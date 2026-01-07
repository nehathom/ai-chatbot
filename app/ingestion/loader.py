import uuid
from pathlib import Path 
from datetime import datetime

from app.ingestion.extractor import extract_text 
from app.ingestion.governance import validate_document 
from app.models.schemas import DocumentMetadata
from app.rag.chunker import chunk_text
from app.rag.store import save_chunks
from app.utils.logger import get_logger

logger = get_logger(__name__)

DOCUMENT_DIR = Path("data/documents")
DOCUMENT_DIR.mkdir(parents=True, exist_ok=True)

def ingest_document(file, metadata: DocumentMetadata):
    """Ingest document with logging and governance."""
    logger.info(f"Starting document ingestion: {file.filename}")
    
    # 1. Governance check
    try:
        validate_document(metadata)
        logger.info(f"Document passed governance checks (approved={metadata.approved})")
    except Exception as e:
        logger.error(f"Governance validation failed: {str(e)}")
        raise
    
    # 2. Generate document ID
    document_id = str(uuid.uuid4())
    metadata.document_id = document_id
    logger.info(f"Assigned document ID: {document_id}")
    
    # 3. Save uploaded file
    file_path = DOCUMENT_DIR / f"{document_id}_{file.filename}"
    with open(file_path, "wb") as f:
        f.write(file.file.read())
    logger.info(f"File saved: {file_path}")
    
    # 4. Extract text
    extracted_text = extract_text(file_path)
    logger.info(f"Text extracted: {len(extracted_text)} characters")
    
    # 5. Chunk the text
    chunks = chunk_text(extracted_text)
    logger.info(f"Created {len(chunks)} chunks")
    
    # 6. Save chunks with metadata
    chunk_count = save_chunks(document_id, chunks, metadata.model_dump())
    logger.info(f"Saved {chunk_count} chunks to storage")
    
    # 7. Return ingestion result
    result = {
        "document_id": document_id,
        "file_path": str(file_path),
        "metadata": metadata.model_dump(),
        "text_length": len(extracted_text),
        "chunk_count": chunk_count,
        "ingested_at": datetime.utcnow().isoformat(),
    }
    
    logger.info(f"Document ingestion completed: {document_id}")
    return result