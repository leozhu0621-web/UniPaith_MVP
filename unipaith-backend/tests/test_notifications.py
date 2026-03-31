"""Tests for notifications — list, mark read, mark all read."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.user import User
from unipaith.models.workflow import Notification


async def _seed_user(db: AsyncSession, user: User):
    db.add(user)
    await db.commit()


async def _create_notification(
    db: AsyncSession, user_id, title: str = "Test Notification"
) -> Notification:
    notification = Notification(
        user_id=user_id,
        notification_type="test",
        title=title,
        body="This is a test notification.",
    )
    db.add(notification)
    await db.commit()
    return notification


@pytest.mark.asyncio
async def test_list_notifications_empty(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
):
    await _seed_user(db_session, mock_student_user)

    resp = await student_client.get("/api/v1/notifications")
    assert resp.status_code == 200
    data = resp.json()
    assert data == []


@pytest.mark.asyncio
async def test_create_and_list(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
):
    await _seed_user(db_session, mock_student_user)

    # Manually create a notification in the db
    await _create_notification(db_session, mock_student_user.id, "New Application Update")

    resp = await student_client.get("/api/v1/notifications")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["title"] == "New Application Update"


@pytest.mark.asyncio
async def test_mark_read(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
):
    await _seed_user(db_session, mock_student_user)
    notification = await _create_notification(db_session, mock_student_user.id)

    resp = await student_client.post(f"/api/v1/notifications/{notification.id}/read")
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_read"] is True


@pytest.mark.asyncio
async def test_mark_all_read(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
):
    await _seed_user(db_session, mock_student_user)

    # Create multiple notifications
    await _create_notification(db_session, mock_student_user.id, "Notification 1")
    await _create_notification(db_session, mock_student_user.id, "Notification 2")
    await _create_notification(db_session, mock_student_user.id, "Notification 3")

    resp = await student_client.post("/api/v1/notifications/read-all")
    assert resp.status_code == 200

    # Verify all are read
    list_resp = await student_client.get("/api/v1/notifications", params={"unread_only": True})
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 0
