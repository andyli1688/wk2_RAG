"""
Judge module: Evaluate whether a claim is fully/partially/not addressed by evidence
"""
import logging
import json
import re
from typing import List
import requests

from app.config import OLLAMA_BASE_URL, LLM_MODEL, TEMPERATURE
from app.models import Claim, ClaimAnalysis, Citation
from app.utils import logger

logger = logging.getLogger(__name__)


JUDGMENT_CRITERIA = """
## 评判标准 (Judgment Criteria)

### 分类规则 (Classification Rules):

1. **完全解决 (fully_addressed)**:
   - 内部证据直接、明确地反驳或解决了该论点
   - 提供了具体的、可验证的事实和数据
   - 证据来源可靠且相关
   - 必须引用至少2个相关的证据片段

2. **部分解决 (partially_addressed)**:
   - 内部证据部分相关，但不够完整
   - 提供了部分信息，但缺少关键证据
   - 需要更多信息才能完全解决
   - 必须引用至少1个相关的证据片段

3. **未解决 (not_addressed)**:
   - 内部证据不相关或非常薄弱
   - 没有找到相关的反驳证据
   - 证据质量不足以支持任何结论
   - 如果证据薄弱或不相关，必须分类为"未解决"

### 引用要求 (Citation Requirements):
- 必须引用所有使用的证据片段
- 每个引用必须包含：文档名称、分块ID、相关引用文本
- 如果证据不足，必须明确说明缺失的证据类型

### 输出要求 (Output Requirements):
- reasoning: 5-10个要点，基于证据进行分析
- confidence: 0-100的置信度分数
- gaps: 如果未完全解决，列出缺失的证据类型（如"审计师函"、"合同"、"发票样本"等）
- recommended_actions: IR/法律/财务部门的后续步骤建议
"""


def judge_claim(claim: Claim, citations: List[Citation]) -> ClaimAnalysis:
    """
    Judge whether a claim is fully/partially/not addressed by the evidence
    
    Args:
        claim: The claim to judge
        citations: Retrieved evidence citations
    
    Returns:
        ClaimAnalysis object with judgment results
    """
    logger.info(f"Judging claim {claim.claim_id}: {claim.claim_text[:100]}...")
    
    # Build context from citations
    if not citations:
        # No evidence found
        return ClaimAnalysis(
            claim_id=claim.claim_id,
            coverage="not_addressed",
            reasoning="未找到相关内部证据。需要进一步检索或收集相关文档。",
            citations=[],
            confidence=0,
            gaps=["需要查找与论点相关的内部文档", "可能需要审计报告、财务报表、合同等"],
            recommended_actions=["扩大检索范围", "收集相关内部文档", "咨询相关部门"]
        )
    
    # Format citations for prompt
    citations_text = "\n\n".join([
        f"[证据 {i+1}]\n"
        f"文档: {cit.doc_title}\n"
        f"分块ID: {cit.chunk_id}\n"
        f"引用: {cit.quote}\n"
        for i, cit in enumerate(citations)
    ])
    
    prompt = f"""你是一位专业的财务分析师，负责评估空头报告的论点是否被内部证据充分反驳。

{JUDGMENT_CRITERIA}

## 论点 (Claim):
ID: {claim.claim_id}
类型: {claim.claim_type}
内容: {claim.claim_text}
出现页码: {claim.page_numbers}

## 检索到的证据 (Retrieved Evidence):
{citations_text}

## 任务 (Task):
请根据评判标准，对上述论点进行评估，并返回JSON格式的结果。

输出格式 (JSON):
{{
  "coverage": "fully_addressed" | "partially_addressed" | "not_addressed",
  "reasoning": "5-10个要点，基于证据进行分析，使用项目符号格式",
  "confidence": 0-100的整数,
  "gaps": ["缺失的证据类型1", "缺失的证据类型2"] (如果未完全解决),
  "recommended_actions": ["建议行动1", "建议行动2"]
}}

重要提示:
- 必须严格遵循评判标准
- 如果证据薄弱或不相关，必须分类为"not_addressed"
- 必须引用所有使用的证据片段（在reasoning中明确提及）
- reasoning必须包含5-10个要点
- 如果coverage不是"fully_addressed"，必须提供gaps和recommended_actions

返回ONLY有效的JSON，不要包含其他文本。"""

    try:
        # Call Ollama API
        url = f"{OLLAMA_BASE_URL}/api/chat"
        payload = {
            "model": LLM_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一位专业的财务分析师，擅长评估证据质量。总是返回有效的JSON格式。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "options": {
                "temperature": TEMPERATURE,
                "num_predict": 2000
            },
            "stream": False
        }
        
        response = requests.post(url, json=payload, timeout=180)
        response.raise_for_status()
        
        result = response.json()
        content = result.get("message", {}).get("content", "")
        
        if not content:
            raise ValueError("LLM returned empty response")
        
        # Extract JSON from response
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            json_str = json_match.group(0)
        else:
            json_str = content.strip()
        
        # Parse JSON
        judgment_data = json.loads(json_str)
        
        # Validate and create ClaimAnalysis
        coverage = judgment_data.get("coverage", "not_addressed")
        if coverage not in ["fully_addressed", "partially_addressed", "not_addressed"]:
            coverage = "not_addressed"
        
        reasoning = judgment_data.get("reasoning", "无法生成分析")
        # Convert reasoning to string if it's a list
        if isinstance(reasoning, list):
            reasoning = "\n".join([f"• {item}" if not item.startswith("•") else item for item in reasoning])
        elif not isinstance(reasoning, str):
            reasoning = str(reasoning)
        
        confidence = int(judgment_data.get("confidence", 0))
        confidence = max(0, min(100, confidence))  # Clamp to 0-100
        
        gaps = judgment_data.get("gaps", [])
        if coverage == "fully_addressed":
            gaps = None
        
        recommended_actions = judgment_data.get("recommended_actions", [])
        if not recommended_actions and coverage != "fully_addressed":
            recommended_actions = ["需要进一步调查", "收集更多证据"]
        
        # Filter citations to only those actually used (if we can determine)
        # For now, include all citations
        used_citations = citations
        
        analysis = ClaimAnalysis(
            claim_id=claim.claim_id,
            coverage=coverage,
            reasoning=reasoning,
            citations=used_citations,
            confidence=confidence,
            gaps=gaps if gaps else None,
            recommended_actions=recommended_actions if recommended_actions else None
        )
        
        logger.info(f"Judgment for {claim.claim_id}: {coverage} (confidence: {confidence})")
        return analysis
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from LLM response: {e}")
        logger.debug(f"LLM response: {content[:500]}")
        # Return default analysis
        return ClaimAnalysis(
            claim_id=claim.claim_id,
            coverage="not_addressed",
            reasoning="LLM返回格式错误，无法进行分析。",
            citations=citations,
            confidence=0,
            gaps=["需要人工审核"],
            recommended_actions=["检查LLM响应格式"]
        )
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to call Ollama API: {e}")
        raise ConnectionError(f"Failed to connect to Ollama: {e}")
    except Exception as e:
        logger.error(f"Error judging claim: {e}")
        # Return default analysis
        return ClaimAnalysis(
            claim_id=claim.claim_id,
            coverage="not_addressed",
            reasoning=f"处理过程中出现错误: {str(e)}",
            citations=citations,
            confidence=0,
            gaps=["需要重新处理"],
            recommended_actions=["检查系统错误"]
        )
