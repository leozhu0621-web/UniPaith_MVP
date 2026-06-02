"""Spec 46 §9/§10/§1/§5 — institution Data & Privacy governance API.

Counterpart to Spec 46 §6 (fairness auto-halt, tested in test_fairness_governance):
this covers the /institutions/me/data/governance config + sub-processor list +
brand commitments + retention surfaces.
"""

from __future__ import annotations

from unipaith.models.institution import Institution

# asyncio_mode = "auto"

API = "/api/v1/institutions/me/data"


async def _seed_institution(db, user) -> Institution:
    inst = Institution(
        admin_user_id=user.id, name="Test U", type="university", country="United States"
    )
    db.add(inst)
    await db.flush()
    return inst


async def test_data_governance_get(institution_client, db_session, mock_institution_user):
    await _seed_institution(db_session, mock_institution_user)
    r = await institution_client.get(f"{API}/governance")
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
        f"{API}/governance",
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
    r = await institution_client.patch(f"{API}/governance", json={"data_residency": "mars"})
    assert r.status_code == 400


async def test_data_governance_route_is_live_not_404(
    institution_client, db_session, mock_institution_user
):
    await _seed_institution(db_session, mock_institution_user)
    r = await institution_client.get(f"{API}/governance")
    assert r.status_code != 404
