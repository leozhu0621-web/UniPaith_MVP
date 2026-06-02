"""Spec 60 §15 — the no-fabrication contract.

"Extraction never writes a field absent from source (no fabrication), every
domain." The extractor must only emit fields grounded in the source, and the
engine must only persist what the extractor emitted.
"""

from __future__ import annotations

from sqlalchemy import select

from unipaith.models.crawler import EntityEnrichment
from unipaith.models.reference import RefOccupation
from unipaith.services.crawler.engine import KnowledgeEngine
from unipaith.services.crawler.extractor import SourceExtractionAgent
from unipaith.services.crawler.schemas import DOMAIN_SCHEMAS


def test_extractor_emits_only_present_keys_every_domain():
    """For every domain, a structured payload carrying ONLY the key field yields
    only that field — never a fabricated one."""
    ex = SourceExtractionAgent()
    for domain, schema in DOMAIN_SCHEMAS.items():
        key = schema.key_field
        payload = {"format": "structured", "trust_tier": 1, "data": {key: "X-TEST"}}
        result = ex.extract(domain, payload)
        assert set(result.fields).issubset({key}), (
            f"{domain}: extractor fabricated fields {set(result.fields) - {key}}"
        )
        assert ex.verify_grounded(result, payload)


def test_extractor_ignores_unknown_source_keys():
    """A source key not in the schema is never written (schema is the write
    allowlist), and a real schema key IS captured."""
    ex = SourceExtractionAgent()
    payload = {
        "format": "structured",
        "trust_tier": 1,
        "data": {"soc_code": "15-1252", "title": "Software Developers", "totally_made_up": "x"},
    }
    result = ex.extract("occupations", payload)
    assert "totally_made_up" not in result.fields
    assert result.fields["soc_code"].value == "15-1252"
    assert "median_salary" not in result.fields  # absent from source → never emitted


def test_text_path_only_emits_matched_patterns():
    """The free-text path emits a field only when its pattern actually matches the
    source text; an unrelated paragraph yields nothing."""
    ex = SourceExtractionAgent()
    miss = ex.extract(
        "occupations", {"format": "text", "trust_tier": 1, "text": "No numbers here."}
    )
    assert miss.fields == {}
    hit = ex.extract(
        "occupations",
        {"format": "text", "trust_tier": 1, "text": "Median annual pay: $130,160 per year."},
    )
    assert hit.fields["median_salary"].value == 130160
    assert ex.verify_grounded(
        hit, {"format": "text", "text": "Median annual pay: $130,160 per year."}
    )


async def test_engine_persists_only_grounded_fields(db_session):
    """End-to-end: ingest an occupation record missing salary → the row's salary
    stays NULL and no audit row exists for the absent field (no fabrication)."""
    engine = KnowledgeEngine(db_session)
    res = await engine.ingest_record(
        domain="occupations",
        record={"soc_code": "99-0001", "title": "Test Occupation"},
        url="https://www.bls.gov/ooh/#99-0001",
        source="seed",
        trust_tier=1,
    )
    assert res.status == "ingested"
    row = (
        await db_session.execute(select(RefOccupation).where(RefOccupation.soc_code == "99-0001"))
    ).scalar_one()
    assert row.title == "Test Occupation"
    assert row.median_salary is None  # never fabricated
    audits = (
        (
            await db_session.execute(
                select(EntityEnrichment.field_path).where(EntityEnrichment.target_key == "99-0001")
            )
        )
        .scalars()
        .all()
    )
    assert "median_salary" not in audits
    assert "title" in audits
