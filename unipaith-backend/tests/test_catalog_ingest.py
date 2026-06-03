"""Spec 69 §3-§6 — deterministic program catalog ingestion.

Covers: create + normalization (§4), stable identity/provenance/freshness (§6),
idempotency (re-ingest updates, never duplicates), authority precedence
(first-party-wins §3/§7), and change-only feature_version bump (§6).
"""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.institution import Institution, Program
from unipaith.models.user import User
from unipaith.services.catalog import (
    CatalogIngestService,
    catalog_authority,
    curated_program_rows,
    normalize_degree_type,
    normalize_modality,
    seed_catalog_for_institution,
)


async def _institution(db: AsyncSession, inst_user: User) -> Institution:
    db.add(inst_user)
    inst = Institution(
        admin_user_id=inst_user.id, name="Test U", type="university", country="United States"
    )
    db.add(inst)
    await db.flush()
    return inst


async def _programs(db: AsyncSession, inst_id) -> list[Program]:
    res = await db.execute(
        select(Program).where(Program.institution_id == inst_id).order_by(Program.program_name)
    )
    return list(res.scalars().all())


# ── Pure normalization (§4) ─────────────────────────────────────────────────


def test_degree_modality_authority_normalization():
    assert normalize_degree_type("M.S.") == "masters"
    assert normalize_degree_type("PhD") == "doctoral"
    assert normalize_modality("On-Campus") == "in_person"
    assert normalize_modality("Remote") == "online"
    assert normalize_modality("teleport") is None
    assert catalog_authority("institution_verified") > catalog_authority("crawled")
    assert catalog_authority("first_party") > catalog_authority("editorial")
    assert catalog_authority("editorial") > catalog_authority("crawled")


# ── Ingest + normalize + provenance (§3/§4/§6) ──────────────────────────────


@pytest.mark.asyncio
async def test_ingest_creates_and_normalizes(db_session: AsyncSession, mock_institution_user):
    inst = await _institution(db_session, mock_institution_user)
    svc = CatalogIngestService(db_session)
    rows = [
        {
            "program_name": "Computer Science",
            "degree_type": "M.S.",
            "delivery_format": "On-Campus",
            "tuition": "52000",
            "cip_code": "11.0701",
            "external_id": "CS-MS",
        },
        {"program_name": "Data Science", "degree_type": "masters", "delivery_format": "online"},
    ]
    summary = await svc.ingest_programs(
        inst.id, rows, source="first_party", source_url="https://u.edu/programs"
    )
    assert summary == {"created": 2, "updated": 0, "skipped": 0}

    cs = next(
        p for p in await _programs(db_session, inst.id) if p.program_name == "Computer Science"
    )
    assert cs.degree_type == "masters"  # "M.S." normalized
    assert cs.delivery_format == "in_person"  # "On-Campus" normalized
    assert cs.tuition == 52000
    assert cs.cip_code == "11.0701"
    assert cs.external_id == "CS-MS"
    assert cs.slug and cs.slug.startswith("computer-science-")  # stable SEO slug (§8)
    assert cs.catalog_source == "first_party"
    assert cs.source_url == "https://u.edu/programs"
    assert cs.last_ingested_at is not None
    assert cs.is_published is True
    assert cs.feature_version == 1


@pytest.mark.asyncio
async def test_ingest_is_idempotent(db_session: AsyncSession, mock_institution_user):
    inst = await _institution(db_session, mock_institution_user)
    svc = CatalogIngestService(db_session)
    rows = [{"program_name": "Computer Science", "degree_type": "MS", "external_id": "CS-MS"}]
    await svc.ingest_programs(inst.id, rows, source="first_party")
    summary2 = await svc.ingest_programs(inst.id, rows, source="first_party")
    assert summary2 == {"created": 0, "updated": 1, "skipped": 0}
    assert len(await _programs(db_session, inst.id)) == 1  # re-ingest never duplicates


# ── Authority precedence — first-party-wins (§3/§7) ─────────────────────────


@pytest.mark.asyncio
async def test_first_party_wins_over_crawl(db_session: AsyncSession, mock_institution_user):
    inst = await _institution(db_session, mock_institution_user)
    svc = CatalogIngestService(db_session)
    await svc.ingest_programs(
        inst.id,
        [{"program_name": "CS", "degree_type": "masters", "tuition": "50000", "external_id": "CS"}],
        source="first_party",
    )
    # A crawl proposes a different tuition for the same program → must NOT overwrite.
    summary = await svc.ingest_programs(
        inst.id,
        [{"program_name": "CS", "degree_type": "masters", "tuition": "99999", "external_id": "CS"}],
        source="crawled",
    )
    assert summary["skipped"] == 1
    prog = (await _programs(db_session, inst.id))[0]
    assert prog.tuition == 50000  # institution value preserved
    assert prog.catalog_source == "first_party"


@pytest.mark.asyncio
async def test_institution_upgrades_a_crawled_program(
    db_session: AsyncSession, mock_institution_user
):
    inst = await _institution(db_session, mock_institution_user)
    svc = CatalogIngestService(db_session)
    await svc.ingest_programs(
        inst.id,
        [{"program_name": "CS", "degree_type": "masters", "tuition": "40000", "external_id": "CS"}],
        source="crawled",
    )
    # The institution later uploads the same program → higher authority wins.
    summary = await svc.ingest_programs(
        inst.id,
        [{"program_name": "CS", "degree_type": "masters", "tuition": "50000", "external_id": "CS"}],
        source="first_party",
    )
    assert summary["updated"] == 1
    prog = (await _programs(db_session, inst.id))[0]
    assert prog.tuition == 50000  # institution overwrote the crawl
    assert prog.catalog_source == "first_party"


# ── feature_version bumps only on a material change (§6) ─────────────────────


@pytest.mark.asyncio
async def test_feature_version_bumps_only_on_change(
    db_session: AsyncSession, mock_institution_user
):
    inst = await _institution(db_session, mock_institution_user)
    svc = CatalogIngestService(db_session)
    base = [
        {"program_name": "CS", "degree_type": "masters", "tuition": "50000", "external_id": "CS"}
    ]
    await svc.ingest_programs(inst.id, base, source="first_party")
    prog = (await _programs(db_session, inst.id))[0]
    assert prog.feature_version == 1
    # Identical re-ingest → no bump (not a material change).
    await svc.ingest_programs(inst.id, base, source="first_party")
    assert prog.feature_version == 1
    # Changed tuition → bump (cache key invalidates for 65/rationale).
    await svc.ingest_programs(
        inst.id,
        [{"program_name": "CS", "degree_type": "masters", "tuition": "55000", "external_id": "CS"}],
        source="first_party",
    )
    assert prog.feature_version == 2


# ── Catalog at volume (§10 — many programs across fields/levels, deduped) ────


@pytest.mark.asyncio
async def test_curated_catalog_seeds_at_volume(db_session: AsyncSession, mock_institution_user):
    inst = await _institution(db_session, mock_institution_user)
    rows = curated_program_rows()
    assert len(rows) == 36  # 12 CIP fields × 3 degree levels — real breadth to rank
    summary = await seed_catalog_for_institution(db_session, inst.id)
    assert summary["created"] == 36 and summary["skipped"] == 0

    progs = await _programs(db_session, inst.id)
    assert len(progs) == 36
    assert {p.degree_type for p in progs} == {"bachelors", "masters", "doctoral"}
    assert len({p.cip_code for p in progs}) == 12  # 12 distinct fields
    assert all(p.slug and p.is_published for p in progs)

    # Idempotent at volume: re-seed updates in place, never duplicates (§5).
    summary2 = await seed_catalog_for_institution(db_session, inst.id)
    assert summary2["created"] == 0 and summary2["updated"] == 36
    assert len(await _programs(db_session, inst.id)) == 36
