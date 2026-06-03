"""Spec 60 §6/§7/§8/§3B/§15 — engine pipeline behaviors.

Covers acceptance: reference rows land provisional + source-cited + confidence
(§4/§15), unchanged content is idempotent (§15 #6), first-party is never
overwritten by crawl (§15 #5), corroboration promotes confidence (§7), and
change_events are detected, classified and routed under consent + cap (§3B/§15 #7).
"""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import func, select

from unipaith.models.crawler import EntityEnrichment, KnowledgeEntity
from unipaith.models.knowledge import InteractionSignal, KnowledgeDocument
from unipaith.models.reference import RefOccupation, Scholarship
from unipaith.models.student import StudentDataConsent, StudentProfile
from unipaith.models.user import User, UserRole
from unipaith.models.workflow import Notification
from unipaith.services.crawler.change_detector import ChangeDetector, classify_change
from unipaith.services.crawler.engine import KnowledgeEngine
from unipaith.services.crawler.enrichment import EnrichmentWriter

_OCC = {
    "soc_code": "15-1252",
    "title": "Software Developers",
    "median_salary": 130160,
    "projected_growth_pct": 17.0,
    "outlook": "Much faster than average",
}
_URL = "https://www.bls.gov/ooh/#15-1252"


async def _make_student(db, *, outreach: bool) -> User:
    user = User(
        id=uuid.uuid4(),
        email=f"s-{uuid.uuid4().hex[:8]}@test.local",
        cognito_sub=str(uuid.uuid4()),
        role=UserRole.student,
    )
    db.add(user)
    await db.flush()
    profile = StudentProfile(user_id=user.id)
    db.add(profile)
    await db.flush()
    db.add(StudentDataConsent(student_id=profile.id, consent_outreach=outreach))
    await db.flush()
    return user


# ── Provenance + resolution (§4/§5/§15 #3) ──────────────────────────────────
async def test_ingest_writes_provenance_and_entity(db_session):
    engine = KnowledgeEngine(db_session)
    res = await engine.ingest_record(
        domain="occupations", record=_OCC, url=_URL, source="seed", trust_tier=1
    )
    assert res.status == "ingested" and res.created

    row = (
        await db_session.execute(select(RefOccupation).where(RefOccupation.soc_code == "15-1252"))
    ).scalar_one()
    assert row.source == "seed"
    assert row.source_url == _URL
    assert row.source_domain == "bls.gov"
    assert row.confidence and row.confidence >= 0.9
    assert row.status == "live"
    assert row.fetched_at is not None

    # canonical entity + raw doc both created
    ent = (
        await db_session.execute(
            select(KnowledgeEntity).where(KnowledgeEntity.canonical_key == "15-1252")
        )
    ).scalar_one()
    assert ent.entity_type == "occupation"
    doc = (
        await db_session.execute(
            select(KnowledgeDocument).where(KnowledgeDocument.source_url == _URL)
        )
    ).scalar_one()
    assert doc.metadata_json["content_hash"]


# ── Idempotency (§15 #6) ────────────────────────────────────────────────────
async def test_unchanged_content_is_idempotent(db_session):
    engine = KnowledgeEngine(db_session)
    first = await engine.ingest_record(
        domain="occupations", record=_OCC, url=_URL, source="seed", trust_tier=1
    )
    second = await engine.ingest_record(
        domain="occupations", record=_OCC, url=_URL, source="seed", trust_tier=1
    )
    assert first.status == "ingested"
    assert second.status == "skipped_unchanged"
    docs = (
        await db_session.execute(
            select(func.count())
            .select_from(KnowledgeDocument)
            .where(KnowledgeDocument.source_url == _URL)
        )
    ).scalar_one()
    assert docs == 1


# ── Authority: first-party never overwritten (§8/§15 #5) ────────────────────
async def test_first_party_not_overwritten_by_crawl(db_session):
    writer = EnrichmentWriter(db_session)
    # Institution-verified value lands first (the authority ceiling).
    await writer.upsert_reference(
        domain="scholarships",
        values={"slug": "x-award", "name": "X Award", "amount_max": 50000},
        source="institution_verified",
        confidence=0.99,
    )
    # A crawl proposes a DIFFERENT amount → review, not overwrite.
    outcome = await writer.upsert_reference(
        domain="scholarships",
        values={"slug": "x-award", "name": "X Award", "amount_max": 9999},
        source="crawled",
        confidence=0.9,
    )
    assert "amount_max" in outcome.review_fields
    assert "amount_max" not in outcome.applied_fields
    row = (
        await db_session.execute(select(Scholarship).where(Scholarship.slug == "x-award"))
    ).scalar_one()
    assert float(row.amount_max) == 50000  # untouched
    review = (
        (
            await db_session.execute(
                select(EntityEnrichment).where(
                    EntityEnrichment.field_path == "amount_max", EntityEnrichment.status == "review"
                )
            )
        )
        .scalars()
        .all()
    )
    assert review and review[0].review_reason == "conflict_with_first_party"


# ── Authority: corroboration promotes confidence (§7) ───────────────────────
async def test_corroboration_promotes_source(db_session):
    writer = EnrichmentWriter(db_session)
    await writer.upsert_reference(
        domain="occupations", values=dict(_OCC), source="seed", confidence=0.9
    )
    # A second, distinct trusted source agreeing on the same value corroborates.
    outcome = await writer.upsert_reference(
        domain="occupations", values=dict(_OCC), source="crawled", confidence=0.8
    )
    assert "median_salary" in outcome.corroborated_fields
    row = (
        await db_session.execute(select(RefOccupation).where(RefOccupation.soc_code == "15-1252"))
    ).scalar_one()
    assert row.source == "corroborated"
    assert (row.source_count or 1) >= 2


# ── Change detection + classification (§3B) ─────────────────────────────────
def test_classify_change_taxonomy():
    assert classify_change("scholarships", "deadline", "a", "b")[0] == "deadline_moved"
    assert classify_change("scholarships", None, None, "New", created=True)[0] == "new_scholarship"
    assert classify_change("visas", "work_rights", "a", "b")[0] == "policy_change"
    assert classify_change("rankings", "rank", 2, 1)[0] == "ranking_update"
    assert classify_change("occupations", "median_salary", 100, 110)[0] == "stat_update"


async def test_change_event_routes_to_consenting_followers_under_cap(db_session):
    # A scholarship the students track.
    sch = Scholarship(slug="route-award", name="Route Award", source="seed", status="live")
    db_session.add(sch)
    await db_session.flush()

    yes = await _make_student(db_session, outreach=True)
    no = await _make_student(db_session, outreach=False)
    for u in (yes, no):
        db_session.add(
            InteractionSignal(
                user_id=u.id, signal_type="save", entity_type="scholarship", entity_id=sch.id
            )
        )
    await db_session.flush()

    detector = ChangeDetector(db_session)
    event = await detector.record_change(
        domain="scholarships",
        target_type="scholarship",
        target_id=sch.id,
        target_name="Route Award",
        field="deadline",
        old=str(date(2026, 10, 1)),
        new=str(date(2026, 11, 1)),
        confidence=0.9,
        source_url="https://studentaid.gov/",
    )
    assert event.change_type == "deadline_moved"
    assert event.materiality == "high"

    summary = await detector.route(event)
    assert summary["recipients"] == 2
    assert summary["notifications"] == 1  # only the consenting student
    assert summary["suppressed_consent"] == 1
    assert event.status == "routed"

    notes = (
        (
            await db_session.execute(
                select(Notification).where(
                    Notification.user_id == yes.id,
                    Notification.notification_type == "program_change",
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(notes) == 1


async def test_low_materiality_change_is_not_routed(db_session):
    detector = ChangeDetector(db_session)
    event = await detector.record_change(
        domain="occupations",
        target_type="ref_occupation",
        target_id=uuid.uuid4(),
        target_name="Software Developers",
        field="employment",
        old=1000,
        new=1003,
        confidence=0.8,
        source_url="https://www.bls.gov/",
    )
    assert event.materiality == "low"
    summary = await detector.route(event)
    assert summary["notifications"] == 0
    assert event.status == "dismissed"
