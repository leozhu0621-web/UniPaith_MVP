"""Spec 60 §7 / §8 — the provenance write-path + conflict/authority resolution.

Every crawled field proposed for a reference row becomes a reversible
``entity_enrichments`` audit row, then is applied confidence- and authority-gated:

Precedence (§8): ``institution_verified`` > ``first_party`` > corroborated crawl >
single high-trust crawl > single low-trust crawl (review only). The crawler
**never overwrites verified data** — a lower-authority value that differs from a
higher-authority one is routed to review ("institution says X, source says Y"),
the prior value is preserved. Cross-source corroboration raises confidence and
promotes a single crawl to ``corroborated`` (≥ ``min_sources`` trusted → may
auto-apply).
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.config import settings
from unipaith.models.crawler import EntityEnrichment
from unipaith.models.reference import (
    RefAccreditation,
    ReferenceEntity,
    RefGeoCost,
    RefMajor,
    RefOccupation,
    RefRanking,
    RefTest,
    RefVisa,
    Scholarship,
)
from unipaith.services.crawler.util import to_jsonable

# domain -> (Model, key_field_tuple, audit_target_type)
REF_TARGETS: dict[str, tuple[type, tuple[str, ...], str]] = {
    "occupations": (RefOccupation, ("soc_code",), "ref_occupation"),
    "tests": (RefTest, ("code",), "ref_test"),
    "visas": (RefVisa, ("country", "code"), "ref_visa"),
    "cost": (RefGeoCost, ("country", "locale"), "ref_geo_cost"),
    "majors": (RefMajor, ("cip_code",), "ref_major"),
    "rankings": (RefRanking, ("ranker", "entity_name", "scope", "year"), "ref_ranking"),
    "accreditation": (RefAccreditation, ("body", "entity_name", "scope"), "ref_accreditation"),
    "scholarships": (Scholarship, ("slug",), "scholarship"),
    "reference": (ReferenceEntity, ("ref_type", "ref_key"), "reference_entity"),
}

# §8 authority ranking — higher wins. Verified first-party data is the ceiling.
_AUTHORITY_RANK = {
    "crawled": 2,
    "seed": 2,
    "corroborated": 3,
    "first_party": 4,
    "institution_verified": 5,
}


def authority_rank(source: str) -> int:
    return _AUTHORITY_RANK.get(source, 1)


class UpsertOutcome:
    def __init__(self) -> None:
        self.row = None
        self.created = False
        self.applied_fields: list[str] = []
        self.review_fields: list[str] = []
        self.corroborated_fields: list[str] = []
        # [(field, old, new)] — material value changes for the change detector.
        self.changes: list[tuple[str, object, object]] = []


class EnrichmentWriter:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _is_trusted(self, source: str, confidence: float, source_count: int) -> bool:
        """Auto-apply gate (§7). Seed / corroborated / first-party are trusted.
        A single crawl auto-applies only above the configured confidence AND
        source-count floor; otherwise it's review-only."""
        if source in ("seed", "corroborated", "first_party", "institution_verified"):
            return True
        return (
            confidence >= settings.crawler_auto_apply_min_confidence
            and source_count >= settings.crawler_auto_apply_min_sources
        )

    async def _find_row(self, model: type, keys: tuple[str, ...], values: dict):
        conds = [getattr(model, k) == values.get(k) for k in keys]
        result = await self.db.execute(select(model).where(and_(*conds)))
        return result.scalar_one_or_none()

    async def _audit(
        self,
        *,
        target_type: str,
        target_id: UUID | None,
        target_key: str | None,
        field_path: str,
        proposed,
        current,
        source: str,
        confidence: float,
        source_count: int,
        source_url: str | None,
        source_document_id: UUID | None,
        status: str,
        review_reason: str | None = None,
    ) -> EntityEnrichment:
        row = EntityEnrichment(
            target_type=target_type,
            target_id=target_id,
            target_key=target_key,
            field_path=field_path,
            proposed_value={"value": to_jsonable(proposed)},
            current_value={"value": to_jsonable(current)} if current is not None else None,
            source=source,
            confidence=confidence,
            source_count=source_count,
            source_url=source_url,
            source_document_id=source_document_id,
            status=status,
            review_reason=review_reason,
            applied_at=datetime.now(UTC) if status == "applied" else None,
        )
        self.db.add(row)
        return row

    async def upsert_reference(
        self,
        *,
        domain: str,
        values: dict,
        source: str = "crawled",
        confidence: float = 0.6,
        source_url: str | None = None,
        source_domain: str | None = None,
        source_document_id: UUID | None = None,
    ) -> UpsertOutcome:
        """Create-or-merge a reference row from grounded, normalized values, writing
        an audit row per field and honoring authority precedence."""
        if domain not in REF_TARGETS:
            raise ValueError(f"no reference target for domain {domain!r}")
        model, keys, audit_type = REF_TARGETS[domain]
        outcome = UpsertOutcome()
        key_repr = "|".join(str(values.get(k)) for k in keys)
        data_fields = {k: v for k, v in values.items() if k not in keys}

        existing = await self._find_row(model, keys, values)
        trusted = self._is_trusted(source, confidence, 1)

        if existing is None:
            row_status = "live" if trusted else "review"
            kwargs = {k: values.get(k) for k in keys}
            for f, v in data_fields.items():
                if hasattr(model, f):
                    kwargs[f] = v
            kwargs.update(
                source=source,
                confidence=confidence,
                source_count=1,
                source_url=source_url,
                source_domain=source_domain,
                source_document_id=source_document_id,
                status=row_status,
                fetched_at=datetime.now(UTC),
            )
            row = model(**kwargs)
            self.db.add(row)
            await self.db.flush()
            outcome.row = row
            outcome.created = True
            for f, v in data_fields.items():
                if not hasattr(model, f):
                    continue
                st = "applied" if row_status == "live" else "review"
                await self._audit(
                    target_type=audit_type,
                    target_id=row.id,
                    target_key=key_repr,
                    field_path=f,
                    proposed=v,
                    current=None,
                    source=source,
                    confidence=confidence,
                    source_count=1,
                    source_url=source_url,
                    source_document_id=source_document_id,
                    status=st,
                    review_reason=None if st == "applied" else "low_trust_single_source",
                )
                (outcome.applied_fields if st == "applied" else outcome.review_fields).append(f)
            await self.db.flush()
            return outcome

        # Existing row → merge field by field under authority precedence.
        outcome.row = existing
        incoming_rank = authority_rank(source)
        existing_rank = authority_rank(existing.source or "crawled")
        for f, new in data_fields.items():
            if not hasattr(model, f):
                continue
            old = getattr(existing, f)
            if _equal(old, new):
                # Same value from a distinct trusted source → corroborate (§7).
                if source != existing.source and source in ("crawled", "seed", "corroborated"):
                    existing.source_count = (existing.source_count or 1) + 1
                    existing.confidence = max(existing.confidence or 0, confidence)
                    if existing.source in ("crawled", "seed"):
                        existing.source = "corroborated"
                    existing.status = "live"
                    outcome.corroborated_fields.append(f)
                continue
            if incoming_rank < existing_rank:
                # Lower authority disagrees with verified/stronger data → review.
                reason = (
                    "conflict_with_first_party"
                    if existing.source in ("first_party", "institution_verified")
                    else "lower_authority_conflict"
                )
                await self._audit(
                    target_type=audit_type,
                    target_id=existing.id,
                    target_key=key_repr,
                    field_path=f,
                    proposed=new,
                    current=old,
                    source=source,
                    confidence=confidence,
                    source_count=1,
                    source_url=source_url,
                    source_document_id=source_document_id,
                    status="review",
                    review_reason=reason,
                )
                outcome.review_fields.append(f)
                continue
            # Apply: incoming authority >= existing.
            setattr(existing, f, new)
            outcome.changes.append((f, old, new))
            outcome.applied_fields.append(f)
            await self._audit(
                target_type=audit_type,
                target_id=existing.id,
                target_key=key_repr,
                field_path=f,
                proposed=new,
                current=old,
                source=source,
                confidence=confidence,
                source_count=1,
                source_url=source_url,
                source_document_id=source_document_id,
                status="applied",
            )

        if outcome.applied_fields:
            existing.source = source
            existing.confidence = confidence
            existing.source_url = source_url or existing.source_url
            existing.source_domain = source_domain or existing.source_domain
            existing.source_document_id = source_document_id or existing.source_document_id
            existing.fetched_at = datetime.now(UTC)
            existing.status = (
                "live"
                if self._is_trusted(source, confidence, existing.source_count or 1)
                else existing.status
            )
        await self.db.flush()
        return outcome

    async def propose_for_target(
        self,
        *,
        target_type: str,
        target_id: UUID | None,
        field_path: str,
        proposed,
        current=None,
        source: str = "crawled",
        confidence: float = 0.6,
        source_url: str | None = None,
        source_document_id: UUID | None = None,
    ) -> EntityEnrichment:
        """First-party targets (institution / program) are never mutated by the
        crawler directly — a proposal becomes a ``pending`` audit row surfaced in
        the institution claim & verify queue (§9). Institution confirms/corrects."""
        row = await self._audit(
            target_type=target_type,
            target_id=target_id,
            target_key=None,
            field_path=field_path,
            proposed=proposed,
            current=current,
            source=source,
            confidence=confidence,
            source_count=1,
            source_url=source_url,
            source_document_id=source_document_id,
            status="pending",
        )
        await self.db.flush()
        return row

    async def decide(
        self, enrichment_id: UUID, *, action: str, decided_by: UUID | None
    ) -> EntityEnrichment | None:
        """Institution / ops decision on a queued enrichment (§9). ``approve`` ->
        applied (first-party wins is honored upstream); ``reject`` -> rejected."""
        result = await self.db.execute(
            select(EntityEnrichment).where(EntityEnrichment.id == enrichment_id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        if action == "approve":
            row.status = "applied"
            row.applied_at = datetime.now(UTC)
        elif action == "reject":
            row.status = "rejected"
        row.decided_by = decided_by
        row.decided_at = datetime.now(UTC)
        await self.db.flush()
        return row


def _equal(a, b) -> bool:
    if a is None or b is None:
        return a is b
    try:
        if isinstance(a, (int, float)) or isinstance(b, (int, float)):
            return float(a) == float(b)
    except (TypeError, ValueError):
        pass
    return str(a).strip() == str(b).strip()
