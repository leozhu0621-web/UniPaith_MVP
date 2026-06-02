"""Spec 60 — Data Crawler & Knowledge-Base Engine: the governed engine spine.

These tables wire the previously-dormant ``knowledge.py`` skeleton into a real,
governed enrichment engine. They are **public-non-personal-data-only** by
contract (§1, §11): nothing here stores a student or any private individual —
the student INPUT half is self-provided and governed by spec 46, and the
skeleton's ``person_insights`` / ``advisor_personas`` tables stay dormant.

- ``CrawlSource`` — the allowlisted source registry + policy (trust tier, domain
  tags, volatility-tiered cadence, robots policy). Allowlist membership is the
  gate the no-personal-data contract test asserts against (§11).
- ``KnowledgeEntity`` — the canonical entity node ``knowledge_links.entity_id``
  resolves to (the §16 table the skeleton referenced but never migrated).
- ``EntityEnrichment`` — the provenance / audit write-path (§7): every crawled
  field proposed for a target is one reversible row (source doc + confidence +
  status), applied confidence-gated, conflicts routed to review (§8).
- ``ChangeEvent`` — the §3B proactive payoff: a detected, materiality-classified
  change routed to the students who care (feed / notifications / saved-search).

Provenance rule (§4): every crawled fact carries ``source`` + ``source_url`` +
``fetched_at`` + ``confidence``; verified first-party data always wins (§8).
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from unipaith.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

# ── Provenance envelope (§4 / §7) ───────────────────────────────────────────
# Allowed sources, in ascending authority order (§8): a single low-trust crawl
# is review-only; cross-source corroboration and first-party/institution-verified
# outrank it. ``institution_verified`` / ``first_party`` are the authority floor
# the crawler must never overwrite.
KNOWLEDGE_SOURCES = (
    "seed",  # curated structured bulk-load (Tier-1, §6) — provenance-cited
    "crawled",  # single crawled source
    "corroborated",  # ≥2 trusted crawled sources agree
    "first_party",  # supplied by the entity itself
    "institution_verified",  # institution claim & verify (23 / §9)
)
KNOWLEDGE_SOURCE_CHECK = "source IN (" + ",".join(f"'{s}'" for s in KNOWLEDGE_SOURCES) + ")"

KNOWLEDGE_STATUSES = ("provisional", "live", "review", "superseded", "archived")
KNOWLEDGE_STATUS_CHECK = "status IN (" + ",".join(f"'{s}'" for s in KNOWLEDGE_STATUSES) + ")"


class ProvenanceMixin:
    """Spec 60 §4 — the provenance envelope every crawled/reference fact carries.

    ``source_document_id`` is a soft reference to ``knowledge_documents.id`` (the
    raw graph); we keep it un-FK'd to avoid create_all ordering cycles with the
    knowledge skeleton, matching ``knowledge_links.entity_id``'s soft pattern.
    """

    source: Mapped[str] = mapped_column(String(24), nullable=False, default="crawled")
    source_url: Mapped[str | None] = mapped_column(Text)
    source_domain: Mapped[str | None] = mapped_column(String(255))
    source_document_id: Mapped[UUID | None] = mapped_column()
    # 0.0–1.0 — the spec's per-field confidence (§13). Defaults set by services.
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    # How many trusted sources corroborate the current value (§7 / §8).
    source_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="provisional")


class CrawlSource(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """§2 / §11 — the allowlisted source registry. Only sources with a row here
    (``allowlisted=True`` + ``enabled=True``) may ever be fetched; the frontier
    refuses anything else. ``trust_tier`` 1 = highest (official API/bulk, lands
    structured → skips extraction, §6); 4 = lowest (review-only, §8)."""

    __tablename__ = "crawl_sources"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    domain: Mapped[str] = mapped_column(String(255), nullable=False)
    base_url: Mapped[str | None] = mapped_column(Text)
    publisher_kind: Mapped[str] = mapped_column(String(24), nullable=False, default="official")
    trust_tier: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    # Which §3 reference domains this source feeds, e.g. ["occupations","outcomes"].
    domain_tags: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    # §3B volatility tier → cadence: news | in_cycle | watchlisted | standard | slow.
    volatility_tier: Mapped[str] = mapped_column(String(16), nullable=False, default="standard")
    crawl_config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    cadence_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=720)
    allowlisted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    respect_robots: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    requires_attribution: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    license: Mapped[str | None] = mapped_column(String(120))
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint("trust_tier BETWEEN 1 AND 4", name="ck_crawl_sources_trust_tier"),
        CheckConstraint(
            "publisher_kind IN ('official','government','academic','ranking','aggregator')",
            name="ck_crawl_sources_publisher_kind",
        ),
        Index("ix_crawl_sources_enabled", "enabled", "allowlisted"),
        Index("ix_crawl_sources_domain", "domain"),
    )


class KnowledgeEntity(UUIDPrimaryKeyMixin, TimestampMixin, ProvenanceMixin, Base):
    """§16 — the canonical entity node the dormant ``knowledge_links.entity_id``
    always pointed at but had no table for. One row per resolved world entity
    (an occupation, a test, a visa regime, a major, a ranking subject…), with a
    normalized ``canonical_key`` (SOC / CIP / test code) for dedup."""

    __tablename__ = "knowledge_entities"

    entity_type: Mapped[str] = mapped_column(String(40), nullable=False)
    canonical_name: Mapped[str] = mapped_column(String(500), nullable=False)
    # Normalized identity key (SOC code, CIP code, test code…). Unique per type.
    canonical_key: Mapped[str | None] = mapped_column(String(120))
    domain: Mapped[str | None] = mapped_column(String(40))
    aliases: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    attributes: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    __table_args__ = (
        UniqueConstraint("entity_type", "canonical_key", name="uq_knowledge_entities_type_key"),
        CheckConstraint(KNOWLEDGE_SOURCE_CHECK, name="ck_knowledge_entities_source"),
        CheckConstraint(KNOWLEDGE_STATUS_CHECK, name="ck_knowledge_entities_status"),
        Index("ix_knowledge_entities_type", "entity_type"),
        Index("ix_knowledge_entities_name", "canonical_name"),
    )


class EntityEnrichment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """§7 — the provenance / audit write-path. Every crawled field proposed for a
    target is one reversible row: what was proposed, from which source doc, at
    what confidence, and whether it was applied, queued for review, or rejected.
    Applying writes the field on the target with ``source=crawled``/confidence and
    keeps this row (reversible). Conflict with first-party → ``review`` (§8)."""

    __tablename__ = "entity_enrichments"

    target_type: Mapped[str] = mapped_column(String(40), nullable=False)
    target_id: Mapped[UUID | None] = mapped_column()
    # For reference rows keyed by a code rather than a UUID (e.g. SOC / CIP).
    target_key: Mapped[str | None] = mapped_column(String(120))
    field_path: Mapped[str] = mapped_column(String(120), nullable=False)
    proposed_value: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    current_value: Mapped[dict | None] = mapped_column(JSONB)

    source: Mapped[str] = mapped_column(String(24), nullable=False, default="crawled")
    source_url: Mapped[str | None] = mapped_column(Text)
    source_document_id: Mapped[UUID | None] = mapped_column()
    source_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)

    # pending | applied | review | rejected | superseded
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    review_reason: Mapped[str | None] = mapped_column(String(120))
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decided_by: Mapped[UUID | None] = mapped_column()
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending','applied','review','rejected','superseded')",
            name="ck_entity_enrichments_status",
        ),
        Index("ix_entity_enrichments_target", "target_type", "target_id"),
        Index("ix_entity_enrichments_status", "status"),
        Index("ix_entity_enrichments_target_field", "target_type", "target_key", "field_path"),
    )


class ChangeEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """§3B / §15 — a detected, materiality-classified change in a watched fact,
    routed to the people who care. Distinct from spec 44's ``signal_change_events``
    (student-signal audit ledger): this is the *world*-side change feed.

    News guardrail (§3B): a row must trace to a real diff in a real source
    (``source_document_id``); no fabricated urgency."""

    __tablename__ = "change_events"

    target_type: Mapped[str] = mapped_column(String(40), nullable=False)
    target_id: Mapped[UUID | None] = mapped_column()
    target_name: Mapped[str | None] = mapped_column(String(500))
    # deadline_moved | new_scholarship | policy_change | program_added |
    # program_closed | cost_change | ranking_update | stat_update | new_event
    change_type: Mapped[str] = mapped_column(String(40), nullable=False)
    field_path: Mapped[str | None] = mapped_column(String(120))
    old_value: Mapped[dict | None] = mapped_column(JSONB)
    new_value: Mapped[dict | None] = mapped_column(JSONB)
    materiality: Mapped[str] = mapped_column(String(10), nullable=False, default="low")
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    source_document_id: Mapped[UUID | None] = mapped_column()
    source_url: Mapped[str | None] = mapped_column(Text)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    # pending | routed | dismissed
    status: Mapped[str] = mapped_column(String(12), nullable=False, default="pending")
    routed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # {feed: n, notifications: n, saved_search: n, suppressed_consent: n, recipients: n}
    routing: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    __table_args__ = (
        CheckConstraint(
            "materiality IN ('high','medium','low')", name="ck_change_events_materiality"
        ),
        CheckConstraint(
            "status IN ('pending','routed','dismissed')", name="ck_change_events_status"
        ),
        Index("ix_change_events_target", "target_type", "target_id"),
        Index("ix_change_events_status_materiality", "status", "materiality"),
        Index("ix_change_events_detected_at", "detected_at"),
    )
