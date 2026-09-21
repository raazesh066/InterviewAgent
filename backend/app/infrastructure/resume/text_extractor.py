"""Resume text extraction from PDF/DOCX files."""
from __future__ import annotations

import io

from docx import Document
from pypdf import PdfReader

from app.core.logging import get_logger

logger = get_logger(__name__)


def extract_text_from_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def extract_text_from_docx(file_bytes: bytes) -> str:
    document = Document(io.BytesIO(file_bytes))
    return "\n".join(paragraph.text for paragraph in document.paragraphs)


def extract_resume_text(file_name: str, file_bytes: bytes) -> str:
    lower = file_name.lower()
    if lower.endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)
    if lower.endswith(".docx"):
        return extract_text_from_docx(file_bytes)
    raise ValueError("Unsupported resume file type. Only PDF and DOCX are supported.")
