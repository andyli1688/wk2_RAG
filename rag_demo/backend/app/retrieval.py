"""
Retrieval module: Retrieve relevant documents from vector database for a given claim
"""
import logging
import requests
from typing import List, Dict

import chromadb
from chromadb.config import Settings

from app.config import CHROMA_DIR, EMBED_MODEL, OLLAMA_BASE_URL, DEFAULT_TOP_K
from app.models import Citation
from app.utils import logger

logger = logging.getLogger(__name__)


def get_embedding(text: str) -> List[float]:
    """Get embedding for text using Ollama"""
    try:
        url = f"{OLLAMA_BASE_URL}/api/embeddings"
        payload = {
            "model": EMBED_MODEL,
            "prompt": text
        }
        
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        embedding = result.get("embedding", [])
        
        if not embedding:
            raise ValueError("Ollama returned empty embedding")
        
        return embedding
        
    except Exception as e:
        logger.error(f"Failed to get embedding: {e}")
        raise ConnectionError(f"Failed to connect to Ollama for embeddings: {e}")


def retrieve_relevant_documents(claim_text: str, top_k: int = DEFAULT_TOP_K) -> List[Citation]:
    """
    Retrieve relevant documents for a given claim
    
    Args:
        claim_text: The claim text to search for
        top_k: Number of documents to retrieve
    
    Returns:
        List of Citation objects
    """
    logger.info(f"Retrieving documents for claim: {claim_text[:100]}...")
    
    try:
        # Initialize ChromaDB
        client = chromadb.PersistentClient(
            path=str(CHROMA_DIR),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get collection
        try:
            collection = client.get_collection("internal_documents")
        except Exception:
            logger.error("ChromaDB collection 'internal_documents' not found. Please run index_internal.py first.")
            return []
        
        # Get embedding for claim
        query_embedding = get_embedding(claim_text)
        
        # Search
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        # Convert to Citation objects
        citations = []
        
        if results['ids'] and len(results['ids'][0]) > 0:
            for i, (doc_id, metadata, document, distance) in enumerate(zip(
                results['ids'][0],
                results['metadatas'][0],
                results['documents'][0],
                results['distances'][0] if 'distances' in results else [0.0] * len(results['ids'][0])
            )):
                citation = Citation(
                    doc_id=metadata.get('doc_id', doc_id),
                    doc_title=metadata.get('doc_title', 'Unknown'),
                    chunk_id=metadata.get('chunk_id', doc_id),
                    quote=document[:500]  # First 500 chars as quote
                )
                citations.append(citation)
                logger.debug(f"Retrieved: {citation.doc_title} (distance: {distance:.4f})")
        
        logger.info(f"Retrieved {len(citations)} relevant documents")
        return citations
        
    except Exception as e:
        logger.error(f"Error retrieving documents: {e}")
        return []
