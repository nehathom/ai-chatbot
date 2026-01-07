from pathlib import Path
from pypdf import PdfReader
from docx import Document


def extract_text(file_path: Path) -> str:
    extension = file_path.suffix.lower()

    if extension == ".pdf":
        return _extract_pdf(file_path)
    elif extension == ".docx":
        return _extract_docx(file_path)
    else:
        raise ValueError("Unsupported file type")


def _extract_pdf(file_path: Path) -> str:
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text.strip()


def _extract_docx(file_path: Path) -> str:
    doc = Document(file_path)
    return "\n".join(p.text for p in doc.paragraphs).strip()
