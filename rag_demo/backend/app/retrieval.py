"""
Retrieval module: Retrieve relevant documents from vector database for a given claim
"""
import logging
import requests
from typing import List, Dict

import chromadb
from chromadb.config import Settings

from app.config import (
    CHROMA_DIR, EMBED_MODEL, OLLAMA_BASE_URL, DEFAULT_TOP_K,
    LLM_PROVIDER, openai_client, EMBED_DIMENSION, is_embedding_dimension_mismatch,
    get_dimension_change_info
)
from app.models import Citation
from app.utils import logger

logger = logging.getLogger(__name__)


def get_embedding(text: str) -> List[float]:
    """Get embedding for text using configured provider (OpenAI or Ollama)"""
    try:
        if LLM_PROVIDER == "openai":
            if not openai_client:
                raise ConnectionError("OpenAI client not initialized. Please set OPENAI_API_KEY.")

            response = openai_client.embeddings.create(
                model=EMBED_MODEL,
                input=text
            )
            embedding = response.data[0].embedding

            if not embedding:
                raise ValueError("OpenAI returned empty embedding")

            return embedding
        else:
            # Ollama API
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
        if LLM_PROVIDER == "openai":
            raise ConnectionError(f"Failed to get embeddings from OpenAI: {e}")
        else:
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

        # Validate embedding dimension compatibility
        collection_metadata = collection.metadata or {}
        stored_dimension = collection_metadata.get("embedding_dimension")

        if stored_dimension is not None:
            if is_embedding_dimension_mismatch(int(stored_dimension)):
                error_msg = get_dimension_change_info(int(stored_dimension), EMBED_DIMENSION)
                logger.error(f"CRITICAL: {error_msg}")
                logger.error(f"ChromaDB collection has incompatible embeddings.")
                logger.error(f"Please run: python -m app.index_internal")
                logger.error(f"Or delete the collection: rm -rf {CHROMA_DIR}")

                # Return empty list to avoid cryptic ChromaDB error
                return []
        else:
            logger.warning("Collection has no embedding_dimension metadata. Attempting retrieval anyway.")
        
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
                # Convert distance to similarity score (lower distance = higher similarity)
                # ChromaDB uses cosine distance, so similarity = 1 - distance
                similarity = max(0.0, min(1.0, 1.0 - distance)) if distance is not None else 0.0
                
                citation = Citation(
                    doc_id=metadata.get('doc_id', doc_id),
                    doc_title=metadata.get('doc_title', 'Unknown'),
                    chunk_id=metadata.get('chunk_id', doc_id),
                    quote=document[:500] if len(document) > 500 else document,  # First 500 chars as quote
                    similarity_score=round(similarity, 4)
                )
                citations.append(citation)
                logger.debug(f"Retrieved: {citation.doc_title} (similarity: {similarity:.4f})")
        
        logger.info(f"Retrieved {len(citations)} relevant documents")
        return citations
        
    except Exception as e:
        error_str = str(e).lower()

        # Check for embedding dimension mismatch error
        if "expecting embedding with dimension of" in error_str:
            logger.error(f"CRITICAL: Embedding dimension mismatch!")
            logger.error(f"Error details: {e}")
            logger.error(f"Solution: Re-index the documents with the current embedding model")
            logger.error(f"Run: python -m app.index_internal")
            logger.error(f"Or manually delete: rm -rf {CHROMA_DIR}")
        else:
            logger.error(f"Error retrieving documents: {e}")

        return []
