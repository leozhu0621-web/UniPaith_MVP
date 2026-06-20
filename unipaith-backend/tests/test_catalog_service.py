"""CatalogService — idempotent seed + load in the planner's shape, and parity
of the DB-driven planner vs the in-code CATALOG constant."""

import pytest
from sqlalchemy import func as safunc
from sqlalchemy import select

from unipaith.models.prompt_catalog import PromptCatalog
from unipaith.services.catalog_service import CatalogService
from unipaith.services.enrichment_planner import CATALOG, essentials_present, plan_next


@pytest.mark.asyncio
async def test_ensure_seeded_then_load_matches_catalog(db_session):
    svc = CatalogService(db_session)
    await svc.ensure_seeded()
    loaded = await svc.load()

    assert {e["key"] for e in loaded} == {f["key"] for f in CATALOG}
    by_key = {e["key"]: e for e in loaded}
    for f in CATALOG:
        e = by_key[f["key"]]
        assert e["type"] == f["type"]
        assert e["tier"] == f["tier"]
        assert e["ask_kind"] == f["ask_kind"]
        assert e["question"] == f["question"]
        assert e["options"] == f.get("options")


@pytest.mark.asyncio
async def test_ensure_seeded_is_idempotent(db_session):
    svc = CatalogService(db_session)
    await svc.ensure_seeded()
    await svc.ensure_seeded()
    n = (await db_session.execute(select(safunc.count()).select_from(PromptCatalog))).scalar()
    assert n == len(CATALOG)


@pytest.mark.asyncio
async def test_db_catalog_drives_planner_identically(db_session):
    """Parity: planner output from the loaded DB catalog == from the constant."""
    svc = CatalogService(db_session)
    await svc.ensure_seeded()
    cat = await svc.load()

    state = {
        "gender": {"value": "Woman", "confidence": 0.9},
        "gpa": {"value": 3.8, "confidence": None},
    }
    assert plan_next(state, limit=5, catalog=cat) == plan_next(state, limit=5)
    assert essentials_present(state, catalog=cat) == essentials_present(state)
