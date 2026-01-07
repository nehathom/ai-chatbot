from typing import List, Dict, Optional
from app.indexing.embeddings import embed_texts
from app.indexing.vector_store import VectorStore
from app.utils.logger import get_logger

logger = get_logger(__name__)

def retrieve_context(
    query: str,
    k: int = 5,
    store_name: str = "default",
    document_type: Optional[str] = None
) -> List[Dict]:
    """
    Retrieve relevant context chunks for a query.
    
    Args:
        query: User's question
        k: Number of chunks to retrieve
        store_name: Name of the vector store
        document_type: Filter by document type
        
    Returns:
        List of relevant chunks with metadata
    """
    logger.info(f"Retrieving context for query: '{query[:50]}...' (k={k}, type={document_type})")
    
    # Load vector store
    store = VectorStore()
    if not store.load(store_name):
        logger.error(f"Vector store '{store_name}' not found")
        raise ValueError(f"Vector store '{store_name}' not found. Build index first.")
    
    # Generate query embedding
    query_embedding = embed_texts([query])[0]
    
    # Get more results if filtering by type
    search_k = k * 3 if document_type else k
    contexts = store.search(query_embedding, search_k)
    
    # Filter by document type if specified
    if document_type:
        contexts = [
            c for c in contexts 
            if c.get("metadata", {}).get("document_type") == document_type
        ][:k]
    
    logger.info(f"Retrieved {len(contexts)} relevant contexts")
    
    # Log which documents were used
    doc_ids = set(c.get("metadata", {}).get("document_id", "unknown") for c in contexts)
    logger.info(f"Context from {len(doc_ids)} unique documents: {list(doc_ids)[:3]}...")
    
    return contexts