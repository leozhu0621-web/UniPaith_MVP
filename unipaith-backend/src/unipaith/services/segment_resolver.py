"""Spec 26 — segment membership resolution from rule trees + legacy criteria."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.application import Application
from unipaith.models.engagement import StudentEngagementSignal
from unipaith.models.institution import Event, EventRSVP, InstitutionDataset
from unipaith.models.matching import MatchResult
from unipaith.models.student import StudentDataConsent, StudentProfile
from unipaith.models.user import User
from unipaith.services.dataset_upload_service import _parse_rows, _read_dataset_content

ENGAGEMENT_FIELD_MAP: dict[str, str] = {
    "engagement.viewed_institution": "viewed_program",
    "engagement.saved_program": "saved_program",
    "engagement.compared_program": "compared_program",
    "engagement.requested_info": "request_info",
}

FITNESS_BAND_THRESHOLDS = {
    "high": 0.75,
    "medium": 0.5,
    "low": 0.0,
}

TIER_NAME_TO_INT = {"reach": 1, "target": 2, "safer": 3, "match": 2, "safety": 3}


async def resolve_criteria_members(
    db: AsyncSession,
    *,
    institution_id: UUID,
    program_ids: list[UUID],
    criteria: dict[str, Any],
) -> list[UUID]:
    """Return student IDs matching segment criteria (legacy flat + rule trees)."""
    if not program_ids:
        return []

    include_tree = criteria.get("include")
    exclude_tree = criteria.get("exclude")
    legacy_active = _legacy_has_filters(criteria)

    if include_tree or legacy_active:
        base = await _eval_legacy_criteria(db, program_ids, criteria)
        if include_tree:
            include_ids = await _eval_rule_tree(db, institution_id, program_ids, include_tree)
            base = _intersect(base, include_ids)
    else:
        base = await _all_prospect_pool(db, program_ids)

    if exclude_tree:
        exclude_ids = await _eval_rule_tree(db, institution_id, program_ids, exclude_tree)
        base = [sid for sid in base if sid not in set(exclude_ids)]

    uploaded_ids = criteria.get("uploaded_list_ids") or []
    if uploaded_ids:
        list_ids = await _students_from_uploaded_lists(db, institution_id, uploaded_ids)
        base = _union(base, list_ids)

    base = await _apply_suppression(db, base)
    return base


async def preview_sample_rows(
    db: AsyncSession,
    student_ids: list[UUID],
    *,
    limit: int = 10,
) -> list[dict[str, Any]]:
    if not student_ids:
        return []
    sample_ids = student_ids[:limit]
    result = await db.execute(
        select(
            StudentProfile.id,
            StudentProfile.first_name,
            StudentProfile.last_name,
            StudentProfile.nationality,
        ).where(StudentProfile.id.in_(sample_ids))
    )
    rows = []
    for sid, first, last, nationality in result.all():
        name = " ".join(p for p in (first, last) if p).strip() or None
        rows.append({"id": str(sid), "display_name": name, "nationality": nationality})
    return rows


def _legacy_has_filters(criteria: dict[str, Any]) -> bool:
    keys = (
        "statuses",
        "decisions",
        "min_match_score",
        "max_match_score",
        "match_tiers",
        "min_engagement_signals",
        "engagement_types",
        "nationalities",
        "has_applied",
        "applied_after",
    )
    for k in keys:
        v = criteria.get(k)
        if v is None or v == [] or v == "":
            continue
        return True
    return False


async def _all_prospect_pool(db: AsyncSession, program_ids: list[UUID]) -> list[UUID]:
    """Students with engagement, match, or application touch for institution programs."""
    ids: set[UUID] = set()

    for stmt in (
        select(StudentEngagementSignal.student_id).where(
            StudentEngagementSignal.program_id.in_(program_ids)
        ),
        select(MatchResult.student_id).where(
            MatchResult.program_id.in_(program_ids),
            MatchResult.is_stale.is_(False),
        ),
        select(Application.student_id).where(Application.program_id.in_(program_ids)),
    ):
        result = await db.execute(stmt.distinct())
        ids.update(row[0] for row in result.all())

    return list(ids)


async def _eval_legacy_criteria(
    db: AsyncSession,
    program_ids: list[UUID],
    criteria: dict[str, Any],
) -> list[UUID]:
    """Port of InstitutionService.resolve_segment_members flat-key logic."""
    has_criteria = False
    stmt = select(StudentProfile.id).distinct()

    statuses = criteria.get("statuses")
    decisions = criteria.get("decisions")
    applied_after = criteria.get("applied_after")
    has_applied = criteria.get("has_applied")

    need_app_join = bool(statuses or decisions or applied_after or (has_applied is True))
    if need_app_join:
        has_criteria = True
        app_conditions = [Application.program_id.in_(program_ids)]
        if statuses:
            app_conditions.append(Application.status.in_(statuses))
        if decisions:
            app_conditions.append(Application.decision.in_(decisions))
        if applied_after:
            app_conditions.append(Application.submitted_at >= datetime.fromisoformat(applied_after))
        stmt = stmt.join(Application, Application.student_id == StudentProfile.id).where(
            *app_conditions
        )
    elif has_applied is False:
        has_criteria = True
        app_exists = (
            select(Application.id)
            .where(
                Application.student_id == StudentProfile.id,
                Application.program_id.in_(program_ids),
            )
            .correlate(StudentProfile)
            .exists()
        )
        stmt = stmt.where(~app_exists)

    min_match_score = criteria.get("min_match_score")
    max_match_score = criteria.get("max_match_score")
    match_tiers = criteria.get("match_tiers")
    if min_match_score is not None or max_match_score is not None or match_tiers:
        has_criteria = True
        match_conditions = [
            MatchResult.program_id.in_(program_ids),
            MatchResult.is_stale.is_(False),
        ]
        if min_match_score is not None:
            match_conditions.append(MatchResult.match_score >= min_match_score / 100)
        if max_match_score is not None:
            match_conditions.append(MatchResult.match_score <= max_match_score / 100)
        if match_tiers:
            match_conditions.append(MatchResult.match_tier.in_(match_tiers))
        stmt = stmt.join(MatchResult, MatchResult.student_id == StudentProfile.id).where(
            *match_conditions
        )

    min_engagement = criteria.get("min_engagement_signals")
    engagement_types = criteria.get("engagement_types")
    if min_engagement is not None or engagement_types:
        has_criteria = True
        eng_conditions = [
            StudentEngagementSignal.student_id == StudentProfile.id,
            StudentEngagementSignal.program_id.in_(program_ids),
        ]
        if engagement_types:
            eng_conditions.append(StudentEngagementSignal.signal_type.in_(engagement_types))
        eng_subq = (
            select(StudentEngagementSignal.student_id)
            .where(*eng_conditions)
            .correlate(StudentProfile)
            .group_by(StudentEngagementSignal.student_id)
        )
        if min_engagement is not None:
            eng_subq = eng_subq.having(func.count() >= min_engagement)
        stmt = stmt.where(StudentProfile.id.in_(eng_subq))

    nationalities = criteria.get("nationalities")
    if nationalities:
        has_criteria = True
        stmt = stmt.where(StudentProfile.nationality.in_(nationalities))

    if not has_criteria:
        stmt = stmt.join(Application, Application.student_id == StudentProfile.id).where(
            Application.program_id.in_(program_ids),
            Application.status != "draft",
        )

    result = await db.execute(stmt)
    return [row[0] for row in result.all()]


async def _eval_rule_tree(
    db: AsyncSession,
    institution_id: UUID,
    program_ids: list[UUID],
    tree: dict[str, Any],
) -> list[UUID]:
    op = (tree.get("op") or "AND").upper()
    rules = tree.get("rules") or []
    if not rules:
        return []

    child_sets: list[list[UUID]] = []
    for node in rules:
        if isinstance(node, dict) and node.get("op"):
            child_sets.append(await _eval_rule_tree(db, institution_id, program_ids, node))
        elif isinstance(node, dict) and node.get("field"):
            child_sets.append(await _eval_single_rule(db, institution_id, program_ids, node))

    if op == "OR":
        return _union(*child_sets)
    if op == "NOT":
        pool = await _all_prospect_pool(db, program_ids)
        excluded = _union(*child_sets) if child_sets else []
        ex_set = set(excluded)
        return [sid for sid in pool if sid not in ex_set]
    return _intersect(*child_sets) if child_sets else []


async def _eval_single_rule(
    db: AsyncSession,
    institution_id: UUID,
    program_ids: list[UUID],
    rule: dict[str, Any],
) -> list[UUID]:
    field = rule.get("field", "")
    operator = rule.get("operator", "equals")
    value = rule.get("value")

    if field.startswith("engagement."):
        signal = ENGAGEMENT_FIELD_MAP.get(field)
        if not signal:
            return []
        days = int(value) if operator == "within_days" and value is not None else 90
        since = datetime.now(UTC) - timedelta(days=days)
        result = await db.execute(
            select(StudentEngagementSignal.student_id)
            .where(
                StudentEngagementSignal.program_id.in_(program_ids),
                StudentEngagementSignal.signal_type == signal,
                StudentEngagementSignal.created_at >= since,
            )
            .distinct()
        )
        return [row[0] for row in result.all()]

    if field == "engagement.event_rsvp":
        days = int(value) if operator == "within_days" and value is not None else 180
        since = datetime.now(UTC) - timedelta(days=days)
        result = await db.execute(
            select(EventRSVP.student_id)
            .join(Event, Event.id == EventRSVP.event_id)
            .where(
                Event.institution_id == institution_id,
                EventRSVP.registered_at >= since,
            )
            .distinct()
        )
        return [row[0] for row in result.all()]

    if field == "application.started":
        result = await db.execute(
            select(Application.student_id).where(Application.program_id.in_(program_ids)).distinct()
        )
        return [row[0] for row in result.all()]

    if field == "application.not_submitted":
        result = await db.execute(
            select(Application.student_id)
            .where(
                Application.program_id.in_(program_ids),
                Application.status == "draft",
            )
            .distinct()
        )
        return [row[0] for row in result.all()]

    if field == "application.status" and operator == "in" and value:
        statuses = value if isinstance(value, list) else [value]
        result = await db.execute(
            select(Application.student_id)
            .where(
                Application.program_id.in_(program_ids),
                Application.status.in_(statuses),
            )
            .distinct()
        )
        return [row[0] for row in result.all()]

    if field == "fit.fitness_band" and operator == "has_band":
        band = str(value).lower()
        min_score = FITNESS_BAND_THRESHOLDS.get(band, 0.0)
        max_score = 1.0
        if band == "medium":
            min_score = FITNESS_BAND_THRESHOLDS["medium"]
            max_score = FITNESS_BAND_THRESHOLDS["high"] - 0.001
        elif band == "low":
            max_score = FITNESS_BAND_THRESHOLDS["medium"] - 0.001
        result = await db.execute(
            select(MatchResult.student_id)
            .where(
                MatchResult.program_id.in_(program_ids),
                MatchResult.is_stale.is_(False),
                MatchResult.fitness_score >= min_score,
                MatchResult.fitness_score <= max_score,
            )
            .distinct()
        )
        return [row[0] for row in result.all()]

    if field == "match.tier" and operator == "in" and value:
        tiers = value if isinstance(value, list) else [value]
        tier_ints = [TIER_NAME_TO_INT.get(str(t).lower(), t) for t in tiers]
        result = await db.execute(
            select(MatchResult.student_id)
            .where(
                MatchResult.program_id.in_(program_ids),
                MatchResult.is_stale.is_(False),
                MatchResult.match_tier.in_(tier_ints),
            )
            .distinct()
        )
        return [row[0] for row in result.all()]

    if field == "profile.nationality" and operator == "in" and value:
        nats = value if isinstance(value, list) else [value]
        result = await db.execute(
            select(StudentProfile.id).where(StudentProfile.nationality.in_(nats))
        )
        return [row[0] for row in result.all()]

    if field == "suppression.unsubscribed":
        result = await db.execute(
            select(StudentDataConsent.student_id).where(
                StudentDataConsent.consent_outreach.is_(False)
            )
        )
        return [row[0] for row in result.all()]

    if field == "readiness.modality" and operator == "in" and value:
        from unipaith.models.needs import StudentNeed

        mods = value if isinstance(value, list) else [value]
        patterns = [f"%{m}%" for m in mods]
        result = await db.execute(
            select(StudentNeed.student_id)
            .where(
                StudentNeed.need_type.ilike("%modality%"),
                or_(*[StudentNeed.signal.ilike(p) for p in patterns]),
            )
            .distinct()
        )
        return [row[0] for row in result.all()]

    if field == "readiness.timeline" and operator == "equals" and value:
        from unipaith.models.needs import StudentNeed

        result = await db.execute(
            select(StudentNeed.student_id)
            .where(
                StudentNeed.need_type.ilike("%timeline%"),
                StudentNeed.signal.ilike(f"%{value}%"),
            )
            .distinct()
        )
        return [row[0] for row in result.all()]

    if field == "readiness.budget_band" and operator == "has_band":
        band = str(value).lower()
        stmt = select(StudentProfile.id)
        if band == "high":
            stmt = stmt.where(
                StudentProfile.budget_max.is_not(None), StudentProfile.budget_max <= 30000
            )
        elif band == "medium":
            stmt = stmt.where(
                StudentProfile.budget_max.is_not(None),
                StudentProfile.budget_max > 30000,
                StudentProfile.budget_max <= 60000,
            )
        else:
            stmt = stmt.where(
                StudentProfile.budget_max.is_not(None), StudentProfile.budget_max > 60000
            )
        result = await db.execute(stmt)
        return [row[0] for row in result.all()]

    return []


async def _students_from_uploaded_lists(
    db: AsyncSession,
    institution_id: UUID,
    dataset_ids: list[Any],
) -> list[UUID]:
    emails: set[str] = set()
    for raw_id in dataset_ids:
        try:
            did = UUID(str(raw_id))
        except ValueError:
            continue
        result = await db.execute(
            select(InstitutionDataset).where(
                InstitutionDataset.id == did,
                InstitutionDataset.institution_id == institution_id,
                InstitutionDataset.dataset_type == "prospect_list",
            )
        )
        dataset = result.scalar_one_or_none()
        if not dataset:
            continue
        content = _read_dataset_content(dataset.s3_key)
        _, rows = _parse_rows(content)
        mapping = dataset.column_mapping or {}
        email_col = mapping.get("email", "email")
        for row in rows:
            email = (row.get(email_col) or "").strip().lower()
            if email:
                emails.add(email)

    if not emails:
        return []

    result = await db.execute(
        select(StudentProfile.id)
        .join(User, User.id == StudentProfile.user_id)
        .where(func.lower(User.email).in_(emails))
    )
    return [row[0] for row in result.all()]


async def _apply_suppression(db: AsyncSession, student_ids: list[UUID]) -> list[UUID]:
    if not student_ids:
        return []
    result = await db.execute(
        select(StudentDataConsent.student_id).where(
            StudentDataConsent.student_id.in_(student_ids),
            StudentDataConsent.consent_outreach.is_(False),
        )
    )
    blocked = {row[0] for row in result.all()}
    return [sid for sid in student_ids if sid not in blocked]


def _intersect(*sets: list[UUID]) -> list[UUID]:
    if not sets:
        return []
    common = set(sets[0])
    for s in sets[1:]:
        common &= set(s)
    return list(common)


def _union(*sets: list[UUID]) -> list[UUID]:
    out: set[UUID] = set()
    for s in sets:
        out.update(s)
    return list(out)
