#tyring to enforce the only approved documents enter the system

from app.models.schemas import DocumentMetadata

def validate_document(metadata: DocumentMetadata):
    if not metadata.approved:
        raise ValueError("Document is not approved for ingestion")

    if not metadata.approved_by:
        raise ValueError("Approved_by field is required")


    return True

    
