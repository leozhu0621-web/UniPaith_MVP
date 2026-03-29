import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.student import StudentProfile
from unipaith.models.user import User


async def _ensure_profile(db: AsyncSession, user: User) -> None:
    db.add(user)
    db.add(StudentProfile(user_id=user.id))
    await db.commit()


@pytest.mark.asyncio
async def test_request_upload_valid(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User,
):
    await _ensure_profile(db_session, mock_student_user)
    resp = await student_client.post("/api/v1/students/me/documents/request-upload", json={
        "document_type": "transcript",
        "file_name": "transcript.pdf",
        "content_type": "application/pdf",
        "file_size_bytes": 1_000_000,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "upload_url" in data
    assert "document_id" in data
    assert "expires_in" in data


@pytest.mark.asyncio
async def test_request_upload_invalid_type(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User,
):
    await _ensure_profile(db_session, mock_student_user)
    resp = await student_client.post("/api/v1/students/me/documents/request-upload", json={
        "document_type": "invalid_doc",
        "file_name": "test.pdf",
        "content_type": "application/pdf",
        "file_size_bytes": 100,
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_request_upload_wrong_mime(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User,
):
    await _ensure_profile(db_session, mock_student_user)
    resp = await student_client.post("/api/v1/students/me/documents/request-upload", json={
        "document_type": "recommendation",
        "file_name": "rec.docx",
        "content_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "file_size_bytes": 100,
    })
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_request_upload_too_large(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User,
):
    await _ensure_profile(db_session, mock_student_user)
    resp = await student_client.post("/api/v1/students/me/documents/request-upload", json={
        "document_type": "transcript",
        "file_name": "big.pdf",
        "content_type": "application/pdf",
        "file_size_bytes": 20_000_000,
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_list_documents(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User,
):
    await _ensure_profile(db_session, mock_student_user)
    await student_client.post("/api/v1/students/me/documents/request-upload", json={
        "document_type": "resume",
        "file_name": "resume.pdf",
        "content_type": "application/pdf",
        "file_size_bytes": 500_000,
    })
    resp = await student_client.get("/api/v1/students/me/documents")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["document_type"] == "resume"


@pytest.mark.asyncio
async def test_delete_document(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User,
):
    await _ensure_profile(db_session, mock_student_user)
    upload_resp = await student_client.post("/api/v1/students/me/documents/request-upload", json={
        "document_type": "essay",
        "file_name": "essay.pdf",
        "content_type": "application/pdf",
        "file_size_bytes": 100_000,
    })
    doc_id = upload_resp.json()["document_id"]
    resp = await student_client.delete(f"/api/v1/students/me/documents/{doc_id}")
    assert resp.status_code == 204

    resp = await student_client.get("/api/v1/students/me/documents")
    assert len(resp.json()) == 0
