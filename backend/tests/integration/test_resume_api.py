"""Integration test for resume upload + parsing (Resume Intelligence)."""
import io

import pytest
from pypdf import PdfWriter

pytestmark = pytest.mark.asyncio


def _make_minimal_pdf_bytes() -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


async def test_upload_resume_extracts_structured_data(client):
    from tests.integration.test_interview_flow import _register_and_login

    headers = await _register_and_login(client, email="resume-user@example.com")
    files = {"file": ("resume.pdf", _make_minimal_pdf_bytes(), "application/pdf")}

    response = await client.post("/api/v1/upload-resume", files=files, headers=headers)
    assert response.status_code == 201
    body = response.json()
    assert body["file_name"] == "resume.pdf"
    assert "Azure" in body["parsed"]["skills"]
    assert body["parsed"]["experience_years"] == 6.5


async def test_upload_resume_rejects_unsupported_type(client):
    from tests.integration.test_interview_flow import _register_and_login

    headers = await _register_and_login(client, email="resume-user2@example.com")
    files = {"file": ("resume.txt", b"plain text resume", "text/plain")}

    response = await client.post("/api/v1/upload-resume", files=files, headers=headers)
    assert response.status_code == 400
