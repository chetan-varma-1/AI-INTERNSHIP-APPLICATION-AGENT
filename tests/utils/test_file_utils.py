"""Tests for uploaded-document validation and extraction."""

from io import BytesIO
from pathlib import Path
from uuid import uuid4

import pytest
from docx import Document

from app.core.exceptions import (
    DocumentTooLargeError,
    InvalidDocumentError,
    UnsupportedDocumentTypeError,
)
from app.utils.file_utils import DocumentFileService


class TestDocumentFileService:
    """Document storage and extraction behavior."""

    @staticmethod
    def _docx_bytes(text: str) -> bytes:
        document = Document()
        document.add_paragraph(text)
        buffer = BytesIO()
        document.save(buffer)
        return buffer.getvalue()

    def test_processes_and_stores_docx(self, tmp_path: Path) -> None:
        service = DocumentFileService(tmp_path, max_size_mb=1)

        result = service.process(
            uuid4(),
            "../../candidate resume.docx",
            self._docx_bytes("Python and FastAPI"),
        )

        assert result.original_name == "candidate_resume.docx"
        assert "Python and FastAPI" in result.text
        assert result.path.exists()
        assert tmp_path in result.path.parents

    def test_rejects_unsupported_extension(self, tmp_path: Path) -> None:
        service = DocumentFileService(tmp_path, max_size_mb=1)

        with pytest.raises(UnsupportedDocumentTypeError):
            service.process(uuid4(), "resume.txt", b"resume")

    def test_rejects_oversized_document(self, tmp_path: Path) -> None:
        service = DocumentFileService(tmp_path, max_size_mb=0)

        with pytest.raises(DocumentTooLargeError):
            service.process(uuid4(), "resume.pdf", b"content")

    def test_rejects_malformed_supported_document(self, tmp_path: Path) -> None:
        service = DocumentFileService(tmp_path, max_size_mb=1)

        with pytest.raises(InvalidDocumentError):
            service.process(uuid4(), "resume.docx", b"not a docx archive")
