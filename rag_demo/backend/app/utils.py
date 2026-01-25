"""
Utility functions: logging, text chunking, helper functions
"""
import logging
import hashlib
import re
from typing import List, Tuple
from pathlib import Path
import json

from app.config import LOG_LEVEL

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def chunk_text(text: str, chunk_size: int = 512, chunk_overlap: int = 50) -> List[str]:
    """
    Split text into chunks with overlap
    
    Args:
        text: Text to chunk
        chunk_size: Maximum size of each chunk (in characters)
        chunk_overlap: Number of characters to overlap between chunks
    
    Returns:
        List of text chunks
    """
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        
        # Try to break at sentence boundary
        if end < len(text):
            # Look for sentence endings
            last_period = chunk.rfind('.')
            last_newline = chunk.rfind('\n')
            break_point = max(last_period, last_newline)
            
            if break_point > chunk_size * 0.5:  # Only break if we're past halfway
                chunk = chunk[:break_point + 1]
                end = start + break_point + 1
        
        chunks.append(chunk.strip())
        start = end - chunk_overlap
    
    return chunks


def calculate_similarity(text1: str, text2: str) -> float:
    """
    Calculate simple string similarity using Jaccard similarity on words
    
    Args:
        text1: First text
        text2: Second text
    
    Returns:
        Similarity score between 0 and 1
    """
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = len(words1 & words2)
    union = len(words1 | words2)
    
    return intersection / union if union > 0 else 0.0


def deduplicate_claims(claims: List[dict], similarity_threshold: float = 0.7) -> List[dict]:
    """
    Remove duplicate or highly similar claims
    
    Args:
        claims: List of claim dictionaries
        similarity_threshold: Threshold for considering claims as duplicates
    
    Returns:
        Deduplicated list of claims
    """
    if not claims:
        return []
    
    deduplicated = []
    seen_hashes = set()
    
    for claim in claims:
        # Create a hash of the normalized claim text
        normalized_text = re.sub(r'\s+', ' ', claim['claim_text'].lower().strip())
        text_hash = hashlib.md5(normalized_text.encode()).hexdigest()
        
        # Check if we've seen this exact text
        if text_hash in seen_hashes:
            continue
        
        # Check similarity with existing claims
        is_duplicate = False
        for existing in deduplicated:
            similarity = calculate_similarity(claim['claim_text'], existing['claim_text'])
            if similarity >= similarity_threshold:
                # Merge page numbers
                existing['page_numbers'] = sorted(set(existing['page_numbers'] + claim['page_numbers']))
                is_duplicate = True
                break
        
        if not is_duplicate:
            deduplicated.append(claim)
            seen_hashes.add(text_hash)
    
    return deduplicated


def save_json(data: dict, filepath: Path) -> None:
    """Save data to JSON file"""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    logger.info(f"Saved JSON to {filepath}")


def load_json(filepath: Path) -> dict:
    """Load data from JSON file"""
    if not filepath.exists():
        return {}
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_claim_id(index: int) -> str:
    """Generate a claim ID like C001, C002, etc."""
    return f"C{index:03d}"
