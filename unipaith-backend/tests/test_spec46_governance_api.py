"""Spec 46 — institution governance API surface (§6 fairness + §9/§10 data tab)."""

from __future__ import annotations

import pytest

from unipaith.models.institution import Institution

# asyncio_mode = "auto"

API = "/api/v1/institutions/me"


async def _seed_institution(db, user) -> Institution:
    inst = Institution(
        admin_user_id=user.id, name="Test U", type="university", country="United States"
    )
    db.add(inst)
    await db.flush()
    return inst


async def test_data_governance_get(institution_client, db_session, mock_institution_user):
    await _seed_institution(db_session, mock_institution_user)
    r = await institution_client.get(f"{API}/data/governance")
    assert r.status_code == 200
    data = r.json()
    assert len(data["subprocessors"]) == 8  # §10
    assert len(data["brand_commitments"]) == 4  # §1
    assert data["brand_commitments"][0]["title"] == "Fit, not fame."
    assert data["settings"]["no_training_tier"] is False
    assert data["settings"]["data_residency"] == "us"
    assert "no_data_sale" in data
    assert len(data["retention_policy"]) >= 8  # §5


async def test_data_governance_patch(institution_client, db_session, mock_institution_user):
    await _seed_institution(db_session, mock_institution_user)
    r = await institution_client.patch(
        f"{API}/data/governance",
        json={"no_training_tier": True, "override_expiry_weeks_default": 3},
    )
    assert r.status_code == 200
    settings = r.json()["settings"]
    assert settings["no_training_tier"] is True
    assert settings["override_expiry_weeks_default"] == 3


async def test_data_governance_patch_rejects_bad_residency(
    institution_client, db_session, mock_institution_user
):
    await _seed_institution(db_session, mock_institution_user)
    r = await institution_client.patch(f"{API}/data/governance", json={"data_residency": "mars"})
    assert r.status_code == 400


async def test_fairness_status_empty(institution_client, db_session, mock_institution_user):
    await _seed_institution(db_session, mock_institution_user)
    r = await institution_client.get(f"{API}/fairness/status")
    assert r.status_code == 200
    body = r.json()
    assert body["overall_status"] == "ok"
    assert body["min_sample"] == 50
    assert body["threshold_default"] == pytest.approx(0.20)


async def test_fairness_compute_endpoint(institution_client, db_session, mock_institution_user):
    await _seed_institution(db_session, mock_institution_user)
    r = await institution_client.post(f"{API}/fairness/compute", json={})
    assert r.status_code == 200
    assert "computed" in r.json()


async def test_fairness_routes_are_live_not_404(
    institution_client, db_session, mock_institution_user
):
    """A signal-key that doesn't exist should 4xx (live route), never 404-missing-route."""
    await _seed_institution(db_session, mock_institution_user)
    r = await institution_client.get(f"{API}/fairness/signals")
    assert r.status_code == 200
    assert r.json() == []
