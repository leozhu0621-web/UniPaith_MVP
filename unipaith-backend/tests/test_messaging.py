"""Tests for messaging — conversations and messages."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.institution import Institution, Program
from unipaith.models.student import StudentProfile
from unipaith.models.user import User


async def _seed_student_and_institution(
    db: AsyncSession, student_user: User, institution_user: User
):
    """Create a student profile and institution."""
    db.add(student_user)
    db.add(institution_user)

    profile = StudentProfile(user_id=student_user.id, first_name="Test", last_name="Student")
    db.add(profile)

    institution = Institution(
        admin_user_id=institution_user.id,
        name="Test University",
        type="university",
        country="United States",
    )
    db.add(institution)
    await db.commit()
    return profile, institution


@pytest.mark.asyncio
async def test_create_conversation(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    profile, institution = await _seed_student_and_institution(
        db_session, mock_student_user, mock_institution_user
    )
    resp = await student_client.post(
        "/api/v1/messages/conversations",
        json={
            "institution_id": str(institution.id),
            "student_id": str(profile.id),
            "subject": "Question about CS Masters",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["subject"] == "Question about CS Masters"


@pytest.mark.asyncio
async def test_send_message(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    profile, institution = await _seed_student_and_institution(
        db_session, mock_student_user, mock_institution_user
    )
    # Create conversation first
    convo_resp = await student_client.post(
        "/api/v1/messages/conversations",
        json={
            "institution_id": str(institution.id),
            "student_id": str(profile.id),
            "subject": "Admissions question",
        },
    )
    convo_id = convo_resp.json()["id"]

    # Send a message
    resp = await student_client.post(
        f"/api/v1/messages/conversations/{convo_id}",
        json={"content": "Hello, I have a question about the program."},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["message_body"] == "Hello, I have a question about the program."


@pytest.mark.asyncio
async def test_get_messages(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    profile, institution = await _seed_student_and_institution(
        db_session, mock_student_user, mock_institution_user
    )
    convo_resp = await student_client.post(
        "/api/v1/messages/conversations",
        json={
            "institution_id": str(institution.id),
            "student_id": str(profile.id),
            "subject": "Test conversation",
        },
    )
    convo_id = convo_resp.json()["id"]

    # Send two messages
    await student_client.post(
        f"/api/v1/messages/conversations/{convo_id}",
        json={"content": "First message"},
    )
    await student_client.post(
        f"/api/v1/messages/conversations/{convo_id}",
        json={"content": "Second message"},
    )

    # Get messages
    resp = await student_client.get(f"/api/v1/messages/conversations/{convo_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_list_conversations(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    profile, institution = await _seed_student_and_institution(
        db_session, mock_student_user, mock_institution_user
    )
    # Create two conversations
    await student_client.post(
        "/api/v1/messages/conversations",
        json={
            "institution_id": str(institution.id),
            "student_id": str(profile.id),
            "subject": "Conversation 1",
        },
    )
    await student_client.post(
        "/api/v1/messages/conversations",
        json={
            "institution_id": str(institution.id),
            "student_id": str(profile.id),
            "subject": "Conversation 2",
        },
    )

    resp = await student_client.get("/api/v1/messages/conversations")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
