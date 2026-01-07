import json
from typing import List, Dict
from pathlib import Path
from datetime import datetime

DATA_DIR = Path("data/chunks")
DATA_DIR.mkdir(parents=True, exist_ok=True)

def save_chunks(
    document_id: str,
    chunks: List[str],
    metadata: Dict
):
    """
    Save document chunks to local JSON storage.
    
    Args:
        document_id: Unique document identifier
        chunks: List of text chunks
        metadata: Document metadata
        
    Returns:
        Number of chunks saved
    """
    # Convert datetime objects to ISO format strings
    serializable_metadata = {}
    for key, value in metadata.items():
        if isinstance(value, datetime):
            serializable_metadata[key] = value.isoformat()
        else:
            serializable_metadata[key] = value
    
    records = []
    for i, chunk in enumerate(chunks):
        records.append({
            "chunk_id": f"{document_id}_chunk_{i}",
            "text": chunk,
            "metadata": serializable_metadata
        })

    with open(DATA_DIR / f"{document_id}.json", "w") as f:
        json.dump(records, f, indent=2)

    return len(records)