"""Spec 24 — institution dataset upload, validation, templates, versioning."""

from __future__ import annotations

from pathlib import Path

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.institution import Institution
from unipaith.models.user import User

BASE = "/api/v1/institutions/me/datasets"

SAMPLE_CSV = """email,first_name,last_name
alice@example.com,Alice,Smith
bob@example.com,Bob,Jones
"""


async def _ensure_institution(db: AsyncSession, user: User) -> Institution:
    result = await db.execute(select(Institution).where(Institution.admin_user_id == user.id))
    existing = result.scalar_one_or_none()
    if existing:
        return existing
    inst = Institution(
        admin_user_id=user.id,
        name="Dataset Test U",
        type="university",
        country="United States",
    )
    db.add(inst)
    await db.commit()
    await db.refresh(inst)
    return inst


async def _upload_csv(
    client: AsyncClient,
    *,
    name: str = "Prospects 2025",
    mapping: dict | None = None,
    skip_invalid: bool = False,
    scope: str = "marketing",
) -> dict:
    init = await client.post(
        f"{BASE}/upload",
        json={
            "dataset_name": name,
            "dataset_type": "prospect_list",
            "file_name": "prospects.csv",
            "content_type": "text/csv",
            "usage_scope": scope,
        },
    )
    assert init.status_code == 200, init.text
    body = init.json()
    dataset_id = body["dataset_id"]
    upload_url = body["upload_url"]

    if upload_url.startswith("file://"):
        local_path = Path(upload_url.replace("file://", ""))
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_text(SAMPLE_CSV, encoding="utf-8")
    else:
        import httpx

        put = await httpx.AsyncClient().put(
            upload_url,
            content=SAMPLE_CSV.encode(),
            headers={"Content-Type": "text/csv"},
        )
        assert put.status_code in (200, 201, 204), put.text

    confirm_body: dict = {}
    if mapping:
        confirm_body["column_mapping"] = mapping
    if skip_invalid:
        confirm_body["skip_invalid_rows"] = True

    confirm = await client.post(f"{BASE}/{dataset_id}/confirm", json=confirm_body)
    return {"dataset_id": dataset_id, "confirm": confirm}


@pytest.mark.asyncio
async def test_dataset_upload_validate_confirm(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_institution_user: User,
):
    await _ensure_institution(db_session, mock_institution_user)
    out = await _upload_csv(
        institution_client,
        mapping={"email": "email", "first_name": "first_name", "last_name": "last_name"},
    )
    assert out["confirm"].status_code == 200, out["confirm"].text
    data = out["confirm"].json()
    assert data["status"] in ("processed", "active")
    assert data["row_count"] == 2
    assert data["usage_scope"] == "marketing"
    assert data["used_by"] == ["campaigns"]


@pytest.mark.asyncio
async def test_mapping_template_reuse(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_institution_user: User,
):
    await _ensure_institution(db_session, mock_institution_user)
    tpl = await institution_client.post(
        f"{BASE}/mapping-templates",
        json={
            "template_name": "Prospect default",
            "dataset_type": "prospect_list",
            "column_mapping": {"email": "email", "first_name": "first_name"},
        },
    )
    assert tpl.status_code == 200
    listed = await institution_client.get(
        f"{BASE}/mapping-templates", params={"dataset_type": "prospect_list"}
    )
    assert listed.status_code == 200
    assert any(t["template_name"] == "Prospect default" for t in listed.json())


@pytest.mark.asyncio
async def test_validation_blocks_without_skip(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_institution_user: User,
):
    await _ensure_institution(db_session, mock_institution_user)
    out = await _upload_csv(institution_client, mapping={"first_name": "first_name"})
    assert out["confirm"].status_code == 422
    detail = out["confirm"].json()["detail"]
    assert detail["validation_report"]["error_count"] > 0


@pytest.mark.asyncio
async def test_marketing_scope_not_used_for_matching(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_institution_user: User,
):
    await _ensure_institution(db_session, mock_institution_user)
    out = await _upload_csv(
        institution_client,
        scope="marketing",
        mapping={"email": "email", "first_name": "first_name", "last_name": "last_name"},
    )
    assert out["confirm"].status_code == 200
    assert "matching" not in out["confirm"].json()["used_by"]


@pytest.mark.asyncio
async def test_version_history_after_confirm(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_institution_user: User,
):
    await _ensure_institution(db_session, mock_institution_user)
    out = await _upload_csv(
        institution_client,
        mapping={"email": "email", "first_name": "first_name", "last_name": "last_name"},
    )
    dataset_id = out["dataset_id"]
    versions = await institution_client.get(f"{BASE}/{dataset_id}/versions")
    assert versions.status_code == 200
    assert len(versions.json()) >= 1
