"""
Handles resume file validation, storage, and text extraction.
Supports PDF, DOCX, and TXT.
"""
import os
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from pypdf import PdfReader
from docx import Document

from app.config import settings

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}


def _get_extension(filename: str) -> str:
    if "." not in filename:
        return ""
    return filename.rsplit(".", 1)[-1].lower()


async def validate_and_save_resume(file: UploadFile, user_id: int) -> tuple[str, str, str]:
    """
    Validates type/size, saves the file to disk, and returns
    (saved_path, file_type, extracted_text).
    """
    ext = _get_extension(file.filename or "")
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '.{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}.",
        )

    contents = await file.read()
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Max size is {settings.MAX_UPLOAD_MB}MB.",
        )
    if len(contents) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

    safe_name = f"user{user_id}_{uuid.uuid4().hex}.{ext}"
    saved_path = UPLOAD_DIR / safe_name
    with open(saved_path, "wb") as f:
        f.write(contents)

    extracted_text = _extract_text(saved_path, ext)
    if not extracted_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not extract any text from this file. Please upload a text-based resume.",
        )

    return str(saved_path), ext, extracted_text


def _extract_text(path: Path, ext: str) -> str:
    try:
        if ext == "txt":
            return path.read_text(encoding="utf-8", errors="ignore")
        if ext == "pdf":
            reader = PdfReader(str(path))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        if ext == "docx":
            doc = Document(str(path))
            return "\n".join(p.text for p in doc.paragraphs)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read file contents: {exc}",
        ) from exc
    return ""
