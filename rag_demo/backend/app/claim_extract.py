"""
Claim extraction module: Extract independent claims from short report using LLM
"""
import logging
import json
import re
from typing import List, Dict, Optional
import requests

from app.config import (
    OLLAMA_BASE_URL, LLM_MODEL, TEMPERATURE, MIN_CLAIMS, MAX_CLAIMS,
    LLM_PROVIDER, openai_client
)
from app.models import Claim
from app.utils import deduplicate_claims, generate_claim_id, logger

logger = logging.getLogger(__name__)


def call_llm(messages: List[Dict], temperature: float = TEMPERATURE, max_tokens: int = 2000) -> str:
    """
    Call LLM API (OpenAI or Ollama) based on configured provider

    Args:
        messages: List of message dicts with 'role' and 'content'
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate

    Returns:
        Generated text content
    """
    if LLM_PROVIDER == "openai":
        if not openai_client:
            raise ConnectionError("OpenAI client not initialized. Please set OPENAI_API_KEY.")

        response = openai_client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content or ""
    else:
        # Ollama API
        url = f"{OLLAMA_BASE_URL}/api/chat"
        payload = {
            "model": LLM_MODEL,
            "messages": messages,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            },
            "stream": False
        }

        response = requests.post(url, json=payload, timeout=120)

        if response.status_code != 200:
            error_msg = response.text
            raise ConnectionError(f"Ollama API returned error {response.status_code}: {error_msg}. Please check if model '{LLM_MODEL}' is available.")

        result = response.json()
        return result.get("message", {}).get("content", "")


def extract_claims_from_text(text: str, pages: List[tuple]) -> List[Claim]:
    """
    Extract independent claims from report text using LLM
    
    Args:
        text: Full text of the report (first 10 pages)
        pages: List of (page_number, page_text) tuples
    
    Returns:
        List of Claim objects
    """
    logger.info("Extracting claims from report text using LLM")
    
    # Build page context for better page number attribution
    page_context = "\n".join([f"Page {pnum}: {ptext[:500]}..." for pnum, ptext in pages[:5]])
    
    prompt = f"""You are an expert financial analyst. Extract independent, testable claims from the following short report.

The report text (first 3 pages):
{text[:8000]}  # Limit context size

Requirements:
1. Extract 8-30 independent, atomic claims (each claim should contain a single allegation)
2. Each claim must be testable and verifiable
3. Claims should be specific and actionable
4. For each claim, identify:
   - The claim text (concise, 1-3 sentences)
   - Page numbers where it appears (from the page context below)
   - Claim type: accounting, business_model, fraud, related_party, guidance, metrics, or other

Page context (first 5 pages):
{page_context}

Output format (JSON array):
[
  {{
    "claim_text": "Specific allegation or claim",
    "page_numbers": [1, 2],
    "claim_type": "accounting"
  }},
  ...
]

Claim types:
- accounting: Accounting irregularities, financial misstatements
- business_model: Business model concerns, sustainability issues
- fraud: Fraud allegations, deception
- related_party: Related party transactions, conflicts of interest
- guidance: Guidance manipulation, forward-looking statements
- metrics: Key metrics manipulation, KPIs
- other: Other types of claims

Return ONLY valid JSON, no additional text."""

    try:
        # Call LLM API (OpenAI or Ollama)
        messages = [
            {
                "role": "system",
                "content": "You are a financial analyst expert at extracting structured claims from reports. Always return valid JSON."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        logger.info(f"Calling {LLM_PROVIDER.upper()} API with model: {LLM_MODEL}")
        content = call_llm(messages, temperature=TEMPERATURE, max_tokens=2000)
        
        if not content:
            raise ValueError("LLM returned empty response")
        
        # Extract JSON from response (handle markdown code blocks)
        json_match = re.search(r'\[[\s\S]*\]', content)
        if json_match:
            json_str = json_match.group(0)
        else:
            json_str = content.strip()
        
        # Parse JSON
        claims_data = json.loads(json_str)
        
        if not isinstance(claims_data, list):
            raise ValueError("LLM did not return a list of claims")
        
        # Validate and clean claims
        validated_claims = []
        for i, claim_data in enumerate(claims_data[:MAX_CLAIMS]):
            if not isinstance(claim_data, dict):
                continue
            
            claim_text = claim_data.get("claim_text", "").strip()
            if not claim_text or len(claim_text) < 10:
                continue
            
            page_numbers = claim_data.get("page_numbers", [])
            if not page_numbers:
                # Try to infer from text if not provided
                page_numbers = [1]
            
            claim_type = claim_data.get("claim_type", "other")
            if claim_type not in ["accounting", "business_model", "fraud", "related_party", "guidance", "metrics", "other"]:
                claim_type = "other"
            
            validated_claims.append({
                "claim_text": claim_text,
                "page_numbers": page_numbers if isinstance(page_numbers, list) else [page_numbers],
                "claim_type": claim_type
            })
        
        # Deduplicate claims
        deduplicated = deduplicate_claims(validated_claims)
        
        # Ensure we have enough claims
        if len(deduplicated) < MIN_CLAIMS:
            logger.warning(f"Only extracted {len(deduplicated)} claims, minimum is {MIN_CLAIMS}")
        
        # Limit to MAX_CLAIMS
        deduplicated = deduplicated[:MAX_CLAIMS]
        
        # Convert to Claim objects
        claims = []
        for i, claim_data in enumerate(deduplicated, start=1):
            claim = Claim(
                claim_id=generate_claim_id(i),
                claim_text=claim_data["claim_text"],
                page_numbers=claim_data["page_numbers"],
                claim_type=claim_data["claim_type"]
            )
            claims.append(claim)
        
        logger.info(f"Successfully extracted {len(claims)} claims")
        return claims
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from LLM response: {e}")
        logger.error(f"LLM response (first 1000 chars): {content[:1000]}")
        # Try to extract JSON from response more aggressively
        # Try to find JSON array in the response
        json_patterns = [
            r'\[[\s\S]*?\]',  # JSON array
            r'\{[\s\S]*?\}',  # JSON object
        ]
        for pattern in json_patterns:
            matches = re.findall(pattern, content)
            if matches:
                try:
                    claims_data = json.loads(matches[0])
                    if isinstance(claims_data, list) and len(claims_data) > 0:
                        logger.info(f"Successfully extracted JSON using pattern matching")
                        # Continue with processing
                        break
                except:
                    continue
        else:
            raise ValueError(f"LLM did not return valid JSON: {e}\nResponse: {content[:500]}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to call LLM API: {e}")
        if LLM_PROVIDER == "openai":
            raise ConnectionError(f"Failed to connect to OpenAI API: {e}")
        else:
            raise ConnectionError(f"Failed to connect to Ollama at {OLLAMA_BASE_URL}. Please ensure Ollama is running and model {LLM_MODEL} is available.")
    except Exception as e:
        import traceback
        logger.error(f"Error extracting claims: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise RuntimeError(f"Failed to extract claims: {e}")
