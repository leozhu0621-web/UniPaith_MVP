"""Spec 25 — campaign audience preview and draft copy."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.institution import Institution
from unipaith.models.user import User


async def _ensure_institution(db: AsyncSession, user: User) -> Institution:
    result = await db.execute(select(Institution).where(Institution.admin_user_id == user.id))
    existing = result.scalar_one_or_none()
    if existing:
        return existing
    inst = Institution(
        admin_user_id=user.id,
        name="Test University",
        type="university",
        country="United States",
    )
    db.add(inst)
    await db.commit()
    await db.refresh(inst)
    return inst


@pytest.mark.asyncio
async def test_campaign_audience_preview_empty_without_segment(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_institution_user: User,
):
    await _ensure_institution(db_session, mock_institution_user)
    create = await institution_client.post(
        "/api/v1/institutions/me/campaigns",
        json={"campaign_name": "Preview test", "campaign_type": "in_app"},
    )
    assert create.status_code == 201
    campaign_id = create.json()["id"]

    preview = await institution_client.get(
        f"/api/v1/institutions/me/campaigns/{campaign_id}/audience",
    )
    assert preview.status_code == 200
    data = preview.json()
    assert data["campaign_id"] == campaign_id
    assert "audience_count" in data
    assert isinstance(data["sample"], list)


@pytest.mark.asyncio
async def test_campaign_draft_copy_endpoint(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_institution_user: User,
):
    await _ensure_institution(db_session, mock_institution_user)
    resp = await institution_client.post(
        "/api/v1/institutions/me/campaigns/draft-copy",
        json={
            "objective": "deadline_reminder",
            "cta_type": "start_application",
            "campaign_name": "Fall reminder",
            "program_name": "MBA",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["subject"]
    assert body["body"]
