"""
Judge module: Evaluate whether a claim is fully/partially/not addressed by evidence
"""
import logging
import json
import re
from typing import List
import requests

from app.config import OLLAMA_BASE_URL, LLM_MODEL, TEMPERATURE, LLM_PROVIDER
from app.claim_extract import call_llm
from app.models import Claim, ClaimAnalysis, Citation
from app.utils import logger

logger = logging.getLogger(__name__)


JUDGMENT_CRITERIA = """
## Judgment Criteria

### Classification Rules:

1. **Fully Addressed**:
   - Internal evidence directly and clearly refutes or addresses the claim
   - Provides specific, verifiable facts and data
   - Evidence source is reliable and relevant
   - Must cite at least 2 relevant evidence pieces

2. **Partially Addressed**:
   - Internal evidence is partially relevant but incomplete
   - Provides some information but lacks key evidence
   - More information needed to fully address the claim
   - Must cite at least 1 relevant evidence piece

3. **Not Addressed**:
   - Internal evidence is not relevant or very weak
   - No relevant rebuttal evidence found
   - Evidence quality insufficient to support any conclusion
   - If evidence is weak or not relevant, must be classified as "Not Addressed"

### Citation Requirements:
- Must cite all evidence pieces used
- Each citation must include: document name, chunk ID, relevant quote text
- If evidence is insufficient, must clearly specify missing evidence types

### Output Requirements:
- reasoning: 5-10 points of analysis based on evidence
- confidence: confidence score 0-100
- gaps: if not fully addressed, list missing evidence types (e.g., "audit letter", "contract", "invoice sample")
- recommended_actions: recommendations for follow-up steps by IR/Legal/Finance departments
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
            reasoning="No relevant internal evidence found. Further retrieval or document collection required.",
            citations=[],
            confidence=0,
            gaps=["Need to locate internal documents related to claim", "May need audit reports, financial statements, contracts, etc."],
            recommended_actions=["Expand search scope", "Collect relevant internal documents", "Consult relevant departments"]
        )
    
    # Format citations for prompt
    citations_text = "\n\n".join([
        f"[Evidence {i+1}]\n"
        f"Document: {cit.doc_title}\n"
        f"Chunk ID: {cit.chunk_id}\n"
        f"Quote: {cit.quote}\n"
        for i, cit in enumerate(citations)
    ])
    
    prompt = f"""You are a professional financial analyst responsible for evaluating whether short report claims are sufficiently rebutted by internal evidence.

{JUDGMENT_CRITERIA}

## Claim:
ID: {claim.claim_id}
Type: {claim.claim_type}
Content: {claim.claim_text}
Page Numbers: {claim.page_numbers}

## Retrieved Evidence:
{citations_text}

## Task:
Based on the judgment criteria, evaluate the above claim and return results in JSON format.

Output Format (JSON):
{{
  "coverage": "fully_addressed" | "partially_addressed" | "not_addressed",
  "reasoning": "5-10 bullet points of analysis based on evidence",
  "confidence": integer 0-100,
  "gaps": ["missing evidence type 1", "missing evidence type 2"] (if not fully addressed),
  "recommended_actions": ["recommended action 1", "recommended action 2"]
}}

Important Notes:
- Must strictly follow judgment criteria
- If evidence is weak or not relevant, must classify as "not_addressed"
- Must cite all evidence pieces used (mention explicitly in reasoning)
- reasoning must contain 5-10 bullet points
- If coverage is not "fully_addressed", must provide gaps and recommended_actions

Return ONLY valid JSON, do not include other text."""

    try:
        # Call LLM API (OpenAI or Ollama)
        messages = [
            {
                "role": "system",
                "content": "You are a professional financial analyst skilled at evaluating evidence quality. Always return valid JSON format."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        logger.info(f"Calling {LLM_PROVIDER.upper()} API for judgment")
        content = call_llm(messages, temperature=TEMPERATURE, max_tokens=2000)
        
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
        
        reasoning = judgment_data.get("reasoning", "Unable to generate analysis")
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
            recommended_actions = ["Requires further investigation", "Collect more evidence"]
        
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
            reasoning="LLM returned invalid format, unable to perform analysis.",
            citations=citations,
            confidence=0,
            gaps=["Requires manual review"],
            recommended_actions=["Check LLM response format"]
        )
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to call LLM API: {e}")
        if LLM_PROVIDER == "openai":
            raise ConnectionError(f"Failed to connect to OpenAI API: {e}")
        else:
            raise ConnectionError(f"Failed to connect to Ollama: {e}")
    except Exception as e:
        logger.error(f"Error judging claim: {e}")
        # Return default analysis
        return ClaimAnalysis(
            claim_id=claim.claim_id,
            coverage="not_addressed",
            reasoning=f"Error occurred during processing: {str(e)}",
            citations=citations,
            confidence=0,
            gaps=["Requires reprocessing"],
            recommended_actions=["Check system errors"]
        )
