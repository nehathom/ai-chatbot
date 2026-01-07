import json
from pathlib import Path
from typing import List, Dict, Optional
from app.indexing.embeddings import embed_texts
from app.indexing.vector_store import VectorStore
from app.utils.logger import get_logger

logger = get_logger(__name__)

CHUNKS_DIR = Path("data/chunks")

def load_all_chunks(approved_only: bool = True, document_type: Optional[str] = None) -> List[Dict]:
    """
    Load chunks from storage with optional filtering.
    
    Args:
        approved_only: Only load chunks from approved documents
        document_type: Filter by document type (e.g., "Technical", "Policy")
        
    Returns:
        List of filtered chunks
    """
    all_chunks = []
    skipped_count = 0
    
    for chunk_file in CHUNKS_DIR.glob("*.json"):
        with open(chunk_file, "r") as f:
            chunks = json.load(f)
            
            for chunk in chunks:
                metadata = chunk.get("metadata", {})
                
                # Governance: Skip non-approved documents
                if approved_only and not metadata.get("approved", False):
                    skipped_count += 1
                    logger.warning(
                        f"Skipping unapproved chunk from document: {metadata.get('document_id', 'unknown')}"
                    )
                    continue
                
                # Filter by document type if specified
                if document_type and metadata.get("document_type") != document_type:
                    continue
                
                all_chunks.append(chunk)
    
    if skipped_count > 0:
        logger.info(f"Skipped {skipped_count} chunks from unapproved documents")
    
    logger.info(f"Loaded {len(all_chunks)} approved chunks")
    return all_chunks

def build_index(
    store_name: str = "default",
    approved_only: bool = True,
    document_type: Optional[str] = None
) -> VectorStore:
    """
    Build vector index from chunks with governance controls.
    
    Args:
        store_name: Name for the vector store
        approved_only: Only index approved documents
        document_type: Filter by document type
        
    Returns:
        VectorStore with indexed chunks
    """
    logger.info(f"Starting index build (approved_only={approved_only}, document_type={document_type})")
    
    # Load chunks with governance filtering
    chunks = load_all_chunks(approved_only=approved_only, document_type=document_type)
    
    if not chunks:
        logger.warning("No chunks found to index after filtering")
        return VectorStore()
    
    logger.info(f"Processing {len(chunks)} chunks...")
    
    # Extract text
    texts = [chunk["text"] for chunk in chunks]
    
    # Generate embeddings
    logger.info("Generating embeddings with Azure OpenAI...")
    embeddings = embed_texts(texts)
    logger.info(f"Generated {len(embeddings)} embeddings")
    
    # Build index
    logger.info("Building FAISS index...")
    store = VectorStore(dim=len(embeddings[0]))
    store.add(embeddings, chunks)
    
    # Save
    store.save(store_name)
    logger.info(f"Index '{store_name}' saved successfully with {len(chunks)} chunks")
    
    return store

def search_index(
    query: str,
    k: int = 5,
    store_name: str = "default",
    document_type: Optional[str] = None
) -> List[Dict]:
    """
    Search the vector index with optional filtering.
    
    Args:
        query: Search query
        k: Number of results
        store_name: Name of the vector store
        document_type: Filter results by document type
        
    Returns:
        List of matching chunks
    """
    logger.info(f"Searching for: '{query}' (top_k={k}, document_type={document_type})")
    
    store = VectorStore()
    if not store.load(store_name):
        logger.error(f"Vector store '{store_name}' not found")
        raise ValueError(f"Vector store '{store_name}' not found")
    
    query_embedding = embed_texts([query])[0]
    
    # Get more results than needed if filtering by type
    search_k = k * 3 if document_type else k
    results = store.search(query_embedding, search_k)
    
    # Filter by document type if specified
    if document_type:
        results = filter_by_document_type(results, document_type)
        results = results[:k]  # Trim to requested size
    
    logger.info(f"Found {len(results)} relevant chunks")
    return results

def filter_by_document_type(chunks: List[Dict], document_type: str) -> List[Dict]:
    """
    Filter chunks by document type.
    
    Args:
        chunks: List of chunks to filter
        document_type: Document type to filter for
        
    Returns:
        Filtered list of chunks
    """
    filtered = [
        chunk for chunk in chunks 
        if chunk.get("metadata", {}).get("document_type") == document_type
    ]
    logger.info(f"Filtered {len(chunks)} chunks to {len(filtered)} of type '{document_type}'")
    return filtered