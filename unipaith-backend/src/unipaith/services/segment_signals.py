"""Spec 26 §2 — the audience-segmentation signal dictionary.

A single, declarative registry of every field an institution can build a
segment rule on. It is the source of truth for three consumers:

  1. the rule-tree evaluator (`segment_service.SegmentService`) — each signal
     carries an async ``evaluate`` that returns the set of matching
     ``student_profiles.id`` for one leaf rule;
  2. the ``SegmentBuilderNLBridge`` agent (`ai/segment_builder.py`) — the keys +
     operators + options form the "available signal dictionary" the model maps
     natural language onto;
  3. the frontend builder (`GET /institutions/me/segments/signal-dictionary`) —
     the metadata drives the data-driven SignalPicker + plain-language chips.

Every signal is scoped to the institution: activity/fit signals look only at the
institution's own programs/events; profile/intent/constraint signals read the
student's durable record. Protected attributes (e.g. nationality) are flagged
so the preview fairness check (§13 / `46` §6) can warn on skew — they are not
hidden, but international recruitment legitimately targets by region.
"""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.application import Application
from unipaith.models.engagement import (
    SavedList,
    SavedListItem,
    StudentCompareItem,
    StudentEngagementSignal,
)
from unipaith.models.goals import StudentGoal
from unipaith.models.institution import Event, EventRSVP, Inquiry, Program
from unipaith.models.matching import MatchResult
from unipaith.models.student import StudentPreference, StudentProfile

# ── Categories (map to spec §2.1–2.5) ───────────────────────────────────────
CAT_ACTIVITY = "activity"
CAT_INTENT = "intent"
CAT_CONSTRAINT = "constraint"
CAT_FIT = "fit"
CAT_PROFILE = "profile"

CATEGORY_LABELS = {
    CAT_ACTIVITY: "Platform activity",
    CAT_INTENT: "Intent & motivation",
    CAT_CONSTRAINT: "Constraints & readiness",
    CAT_FIT: "Fit & likelihood",
    CAT_PROFILE: "Profile",
}


@dataclass
class EvalContext:
    db: AsyncSession
    institution_id: uuid.UUID
    program_ids: list[uuid.UUID]
    now: datetime
    operator: str
    value: Any


@dataclass
class SignalDef:
    key: str
    label: str
    category: str
    operators: list[str]
    value_type: str  # enum_multi | enum_single | number | band | boolean | days
    plain_language: str  # template with {value}
    evaluate: Callable[[EvalContext], Awaitable[set[uuid.UUID]]]
    options: list[dict[str, str]] | None = None
    protected: bool = False  # surfaced in the fairness skew check
    derived: bool = False  # computed, not a stored column
    help_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "label": self.label,
            "category": self.category,
            "category_label": CATEGORY_LABELS.get(self.category, self.category),
            "operators": self.operators,
            "value_type": self.value_type,
            "options": self.options,
            "plain_language": self.plain_language,
            "protected": self.protected,
            "derived": self.derived,
            "help_text": self.help_text,
        }


# ── small helpers ────────────────────────────────────────────────────────────


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


async def _ids(db: AsyncSession, stmt) -> set[uuid.UUID]:
    rows = await db.execute(stmt)
    return {r[0] for r in rows.all()}


def _fit_band(score: float) -> str:
    if score >= 0.75:
        return "high"
    if score >= 0.50:
        return "medium"
    return "low"


def _likelihood_band(score: float) -> str:
    if score >= 0.70:
        return "high"
    if score >= 0.40:
        return "medium"
    return "low"


def _readiness_band(pct: int) -> str:
    if pct >= 80:
        return "high"
    if pct >= 50:
        return "medium"
    return "low"


def _budget_band(amount: int) -> str:
    if amount < 20000:
        return "under_20k"
    if amount < 40000:
        return "20k_40k"
    if amount < 60000:
        return "40k_60k"
    return "60k_plus"


_WEIGHT_FIELDS = {
    "cost": "weight_cost",
    "location": "weight_location",
    "outcomes": "weight_outcomes",
    "ranking": "weight_ranking",
    "flexibility": "weight_flexibility",
    "support": "weight_support",
}


# ── evaluators ───────────────────────────────────────────────────────────────
# Each returns the set of student_profiles.id matching this one leaf rule.


def _no_programs(ctx: EvalContext) -> bool:
    return not ctx.program_ids


async def _ev_viewed(ctx: EvalContext) -> set[uuid.UUID]:
    if _no_programs(ctx):
        return set()
    days = int(ctx.value) if ctx.value not in (None, "") else 30
    cutoff = ctx.now - timedelta(days=days)
    stmt = (
        select(StudentEngagementSignal.student_id)
        .where(
            StudentEngagementSignal.program_id.in_(ctx.program_ids),
            StudentEngagementSignal.signal_type.in_(["view", "view_program", "view_institution"]),
            StudentEngagementSignal.created_at >= cutoff,
        )
        .distinct()
    )
    return await _ids(ctx.db, stmt)


def _saved_base(ctx: EvalContext):
    return (
        select(SavedList.student_id)
        .join(SavedListItem, SavedListItem.list_id == SavedList.id)
        .join(Program, Program.id == SavedListItem.program_id)
        .where(Program.id.in_(ctx.program_ids))
        .distinct()
    )


async def _ev_saved(ctx: EvalContext) -> set[uuid.UUID]:
    if _no_programs(ctx):
        return set()
    return await _ids(ctx.db, _saved_base(ctx))


async def _ev_saved_degree(ctx: EvalContext) -> set[uuid.UUID]:
    if _no_programs(ctx):
        return set()
    vals = [str(v).lower() for v in _as_list(ctx.value)]
    if not vals:
        return set()
    stmt = _saved_base(ctx).where(func.lower(Program.degree_type).in_(vals))
    return await _ids(ctx.db, stmt)


async def _ev_saved_field(ctx: EvalContext) -> set[uuid.UUID]:
    if _no_programs(ctx):
        return set()
    vals = [str(v).lower() for v in _as_list(ctx.value)]
    if not vals:
        return set()
    # substring match on department (the field-of-study proxy)
    conds = [func.lower(Program.department).contains(v) for v in vals]
    from sqlalchemy import or_

    stmt = _saved_base(ctx).where(Program.department.isnot(None), or_(*conds))
    return await _ids(ctx.db, stmt)


async def _ev_compared(ctx: EvalContext) -> set[uuid.UUID]:
    if _no_programs(ctx):
        return set()
    stmt = (
        select(StudentCompareItem.student_id)
        .where(StudentCompareItem.program_id.in_(ctx.program_ids))
        .distinct()
    )
    return await _ids(ctx.db, stmt)


async def _ev_requested_info(ctx: EvalContext) -> set[uuid.UUID]:
    stmt = (
        select(Inquiry.student_id)
        .where(Inquiry.institution_id == ctx.institution_id, Inquiry.student_id.isnot(None))
        .distinct()
    )
    return await _ids(ctx.db, stmt)


async def _ev_event(ctx: EvalContext) -> set[uuid.UUID]:
    states = [str(v) for v in _as_list(ctx.value)] or ["rsvp", "attended"]
    base = (
        select(EventRSVP.student_id)
        .join(Event, Event.id == EventRSVP.event_id)
        .where(Event.institution_id == ctx.institution_id)
    )
    from sqlalchemy import or_

    conds = []
    if "attended" in states:
        conds.append(EventRSVP.attended_at.isnot(None))
    if "waitlisted" in states:
        conds.append(EventRSVP.rsvp_status == "waitlisted")
    if "rsvp" in states:
        conds.append(EventRSVP.rsvp_status.in_(["registered", "confirmed", "going"]))
    if "no_show" in states:
        conds.append(
            (EventRSVP.attended_at.is_(None))
            & (Event.end_time < ctx.now)
            & (EventRSVP.rsvp_status.in_(["registered", "confirmed", "going"]))
        )
    if not conds:
        return set()
    return await _ids(ctx.db, base.where(or_(*conds)).distinct())


async def _ev_started_application(ctx: EvalContext) -> set[uuid.UUID]:
    if _no_programs(ctx):
        return set()
    stmt = (
        select(Application.student_id).where(Application.program_id.in_(ctx.program_ids)).distinct()
    )
    return await _ids(ctx.db, stmt)


async def _ev_started_not_submitted(ctx: EvalContext) -> set[uuid.UUID]:
    if _no_programs(ctx):
        return set()
    stmt = (
        select(Application.student_id)
        .where(
            Application.program_id.in_(ctx.program_ids),
            Application.submitted_at.is_(None),
        )
        .distinct()
    )
    return await _ids(ctx.db, stmt)


async def _ev_applied_within(ctx: EvalContext) -> set[uuid.UUID]:
    if _no_programs(ctx):
        return set()
    days = int(ctx.value) if ctx.value not in (None, "") else 30
    cutoff = ctx.now - timedelta(days=days)
    stmt = (
        select(Application.student_id)
        .where(
            Application.program_id.in_(ctx.program_ids),
            Application.submitted_at.isnot(None),
            Application.submitted_at >= cutoff,
        )
        .distinct()
    )
    return await _ids(ctx.db, stmt)


async def _ev_application_status(ctx: EvalContext) -> set[uuid.UUID]:
    if _no_programs(ctx):
        return set()
    vals = [str(v) for v in _as_list(ctx.value)]
    if not vals:
        return set()
    stmt = (
        select(Application.student_id)
        .where(Application.program_id.in_(ctx.program_ids), Application.status.in_(vals))
        .distinct()
    )
    return await _ids(ctx.db, stmt)


async def _ev_application_decision(ctx: EvalContext) -> set[uuid.UUID]:
    if _no_programs(ctx):
        return set()
    vals = [str(v) for v in _as_list(ctx.value)]
    if not vals:
        return set()
    stmt = (
        select(Application.student_id)
        .where(Application.program_id.in_(ctx.program_ids), Application.decision.in_(vals))
        .distinct()
    )
    return await _ids(ctx.db, stmt)


async def _max_match(ctx: EvalContext) -> dict[uuid.UUID, tuple[float, float]]:
    """Per student, the max (fitness, confidence) across this institution's programs."""
    if _no_programs(ctx):
        return {}
    stmt = (
        select(
            MatchResult.student_id,
            func.max(MatchResult.fitness_score),
            func.max(MatchResult.confidence_score),
        )
        .where(MatchResult.program_id.in_(ctx.program_ids), MatchResult.is_stale.is_(False))
        .group_by(MatchResult.student_id)
    )
    rows = await ctx.db.execute(stmt)
    return {r[0]: (float(r[1] or 0), float(r[2] or 0)) for r in rows.all()}


async def _ev_fit_band(ctx: EvalContext) -> set[uuid.UUID]:
    wanted = {str(v) for v in _as_list(ctx.value)}
    if not wanted:
        return set()
    return {sid for sid, (f, _c) in (await _max_match(ctx)).items() if _fit_band(f) in wanted}


async def _ev_likelihood_band(ctx: EvalContext) -> set[uuid.UUID]:
    wanted = {str(v) for v in _as_list(ctx.value)}
    if not wanted:
        return set()
    return {
        sid for sid, (_f, c) in (await _max_match(ctx)).items() if _likelihood_band(c) in wanted
    }


async def _ev_nurture_band(ctx: EvalContext) -> set[uuid.UUID]:
    """Derived: high-fit prospects who have NOT yet started an application need
    the most nurturing; high-fit who applied need the least."""
    wanted = {str(v) for v in _as_list(ctx.value)}
    if not wanted:
        return set()
    match = await _max_match(ctx)
    applied = await _ev_started_application(ctx)
    out: set[uuid.UUID] = set()
    for sid, (f, _c) in match.items():
        if sid in applied:
            band = "low"
        elif f >= 0.75:
            band = "high"
        elif f >= 0.50:
            band = "medium"
        else:
            band = "low"
        if band in wanted:
            out.add(sid)
    return out


async def _ev_match_score(ctx: EvalContext) -> set[uuid.UUID]:
    match = await _max_match(ctx)
    op = ctx.operator
    out: set[uuid.UUID] = set()
    for sid, (f, _c) in match.items():
        pct = f * 100
        if op in ("gt", "gte") and pct >= float(ctx.value):
            out.add(sid)
        elif op in ("lt", "lte") and pct <= float(ctx.value):
            out.add(sid)
        elif op == "between" and isinstance(ctx.value, list) and len(ctx.value) == 2:
            lo, hi = float(ctx.value[0]), float(ctx.value[1])
            if lo <= pct <= hi:
                out.add(sid)
    return out


# --- intent / constraint (StudentPreference + StudentGoal) ---


async def _ev_goal_category(ctx: EvalContext) -> set[uuid.UUID]:
    vals = [str(v) for v in _as_list(ctx.value)]
    if not vals:
        return set()
    stmt = select(StudentGoal.student_id).where(StudentGoal.category.in_(vals)).distinct()
    return await _ids(ctx.db, stmt)


async def _ev_top_priority(ctx: EvalContext) -> set[uuid.UUID]:
    wanted = {str(v) for v in _as_list(ctx.value)}
    if not wanted:
        return set()
    cols = [getattr(StudentPreference, c) for c in _WEIGHT_FIELDS.values()]
    stmt = select(StudentPreference.student_id, *cols)
    rows = await ctx.db.execute(stmt)
    out: set[uuid.UUID] = set()
    keys = list(_WEIGHT_FIELDS.keys())
    for row in rows.all():
        sid = row[0]
        weights = [(keys[i], row[i + 1]) for i in range(len(keys)) if row[i + 1] is not None]
        if not weights:
            continue
        top = max(weights, key=lambda kv: kv[1])[0]
        if top in wanted:
            out.add(sid)
    return out


async def _ev_budget_band(ctx: EvalContext) -> set[uuid.UUID]:
    wanted = {str(v) for v in _as_list(ctx.value)}
    if not wanted:
        return set()
    stmt = select(StudentPreference.student_id, StudentPreference.budget_max).where(
        StudentPreference.budget_max.isnot(None)
    )
    rows = await ctx.db.execute(stmt)
    return {r[0] for r in rows.all() if _budget_band(int(r[1])) in wanted}


def _pref_in_eval(field_name: str) -> Callable[[EvalContext], Awaitable[set[uuid.UUID]]]:
    async def _inner(ctx: EvalContext) -> set[uuid.UUID]:
        vals = [str(v) for v in _as_list(ctx.value)]
        if not vals:
            return set()
        col = getattr(StudentPreference, field_name)
        stmt = select(StudentPreference.student_id).where(col.in_(vals)).distinct()
        return await _ids(ctx.db, stmt)

    return _inner


async def _ev_readiness_band(ctx: EvalContext) -> set[uuid.UUID]:
    if _no_programs(ctx):
        return set()
    wanted = {str(v) for v in _as_list(ctx.value)}
    if not wanted:
        return set()
    stmt = (
        select(Application.student_id, func.max(Application.readiness_pct))
        .where(Application.program_id.in_(ctx.program_ids), Application.readiness_pct.isnot(None))
        .group_by(Application.student_id)
    )
    rows = await ctx.db.execute(stmt)
    return {r[0] for r in rows.all() if _readiness_band(int(r[1])) in wanted}


def _profile_in_eval(field_name: str) -> Callable[[EvalContext], Awaitable[set[uuid.UUID]]]:
    async def _inner(ctx: EvalContext) -> set[uuid.UUID]:
        vals = [str(v) for v in _as_list(ctx.value)]
        if not vals:
            return set()
        col = getattr(StudentProfile, field_name)
        stmt = select(StudentProfile.id).where(col.in_(vals)).distinct()
        return await _ids(ctx.db, stmt)

    return _inner


# ── the registry ─────────────────────────────────────────────────────────────

_DEGREE_OPTS = [
    {"value": "bachelor", "label": "Bachelor's"},
    {"value": "master", "label": "Master's"},
    {"value": "phd", "label": "PhD"},
    {"value": "certificate", "label": "Certificate"},
    {"value": "diploma", "label": "Diploma"},
]
_BAND_OPTS = [
    {"value": "high", "label": "High"},
    {"value": "medium", "label": "Medium"},
    {"value": "low", "label": "Low"},
]
_EVENT_OPTS = [
    {"value": "rsvp", "label": "RSVP'd"},
    {"value": "attended", "label": "Attended"},
    {"value": "waitlisted", "label": "Waitlisted"},
    {"value": "no_show", "label": "No-show"},
]
_GOAL_OPTS = [
    {"value": "academic", "label": "Academic"},
    {"value": "social", "label": "Social"},
    {"value": "personal", "label": "Personal"},
]
_PRIORITY_OPTS = [
    {"value": "cost", "label": "Cost"},
    {"value": "location", "label": "Location"},
    {"value": "outcomes", "label": "Outcomes"},
    {"value": "ranking", "label": "Ranking / selectivity"},
    {"value": "flexibility", "label": "Flexibility"},
    {"value": "support", "label": "Support services"},
]
_BUDGET_OPTS = [
    {"value": "under_20k", "label": "Under $20k"},
    {"value": "20k_40k", "label": "$20k–$40k"},
    {"value": "40k_60k", "label": "$40k–$60k"},
    {"value": "60k_plus", "label": "$60k+"},
]
_MODALITY_OPTS = [
    {"value": "online", "label": "Online"},
    {"value": "in_person", "label": "In person"},
    {"value": "hybrid", "label": "Hybrid"},
]
_APP_STATUS_OPTS = [
    {"value": "draft", "label": "Draft"},
    {"value": "submitted", "label": "Submitted"},
    {"value": "under_review", "label": "Under review"},
    {"value": "interview", "label": "Interview"},
    {"value": "decision_made", "label": "Decision made"},
]
_DECISION_OPTS = [
    {"value": "admitted", "label": "Admitted"},
    {"value": "rejected", "label": "Rejected"},
    {"value": "waitlisted", "label": "Waitlisted"},
    {"value": "deferred", "label": "Deferred"},
]


def _build_registry() -> dict[str, SignalDef]:
    defs: list[SignalDef] = [
        # ── Platform activity (§2.1) ──
        SignalDef(
            "viewed_institution",
            "Viewed our institution",
            CAT_ACTIVITY,
            ["within_days"],
            "days",
            "Viewed our institution or a program in the last {value} days",
            _ev_viewed,
        ),
        SignalDef(
            "saved_program",
            "Saved any of our programs",
            CAT_ACTIVITY,
            ["exists"],
            "boolean",
            "Saved one of our programs",
            _ev_saved,
        ),
        SignalDef(
            "saved_program_degree",
            "Saved a program by degree type",
            CAT_ACTIVITY,
            ["in"],
            "enum_multi",
            "Saved one of our {value} programs",
            _ev_saved_degree,
            options=_DEGREE_OPTS,
        ),
        SignalDef(
            "saved_program_field",
            "Saved a program in a field",
            CAT_ACTIVITY,
            ["in"],
            "enum_multi",
            "Saved one of our programs in {value}",
            _ev_saved_field,
            options=None,
            help_text="Matches the program department / field of study.",
        ),
        SignalDef(
            "compared_program",
            "Compared our programs",
            CAT_ACTIVITY,
            ["exists"],
            "boolean",
            "Compared one of our programs",
            _ev_compared,
        ),
        SignalDef(
            "requested_info",
            "Requested information",
            CAT_ACTIVITY,
            ["exists"],
            "boolean",
            "Requested information from us",
            _ev_requested_info,
        ),
        SignalDef(
            "event_engagement",
            "Event engagement",
            CAT_ACTIVITY,
            ["in"],
            "enum_multi",
            "Event status: {value}",
            _ev_event,
            options=_EVENT_OPTS,
        ),
        SignalDef(
            "started_application",
            "Started an application",
            CAT_ACTIVITY,
            ["exists"],
            "boolean",
            "Started an application with us",
            _ev_started_application,
        ),
        SignalDef(
            "started_not_submitted",
            "Started but not submitted",
            CAT_ACTIVITY,
            ["exists"],
            "boolean",
            "Started an application but hasn't submitted it",
            _ev_started_not_submitted,
        ),
        SignalDef(
            "applied_within",
            "Applied recently",
            CAT_ACTIVITY,
            ["within_days"],
            "days",
            "Applied in the last {value} days",
            _ev_applied_within,
        ),
        SignalDef(
            "application_status",
            "Application status",
            CAT_ACTIVITY,
            ["in"],
            "enum_multi",
            "Application status is {value}",
            _ev_application_status,
            options=_APP_STATUS_OPTS,
        ),
        SignalDef(
            "application_decision",
            "Application decision",
            CAT_ACTIVITY,
            ["in"],
            "enum_multi",
            "Decision is {value}",
            _ev_application_decision,
            options=_DECISION_OPTS,
        ),
        # ── Fit & likelihood (§2.4) ──
        SignalDef(
            "fit_band",
            "Fit-to-program band",
            CAT_FIT,
            ["in"],
            "band",
            "Fit band is {value}",
            _ev_fit_band,
            options=_BAND_OPTS,
            help_text="Computed from the platform match (fitness) score.",
        ),
        SignalDef(
            "likelihood_band",
            "Likelihood-to-apply band",
            CAT_FIT,
            ["in"],
            "band",
            "Likelihood-to-apply band is {value}",
            _ev_likelihood_band,
            options=_BAND_OPTS,
            help_text="Computed from the match confidence score.",
        ),
        SignalDef(
            "nurture_band",
            "Nurture-needed band",
            CAT_FIT,
            ["in"],
            "band",
            "Nurture-needed band is {value}",
            _ev_nurture_band,
            options=_BAND_OPTS,
            derived=True,
            help_text="High-fit prospects who haven't applied need the most nurturing.",
        ),
        SignalDef(
            "match_score",
            "Match score (0–100)",
            CAT_FIT,
            ["gt", "lt", "between"],
            "number",
            "Match score is {operator} {value}",
            _ev_match_score,
        ),
        # ── Intent & motivation (§2.2) ──
        SignalDef(
            "goal_category",
            "Has a goal in category",
            CAT_INTENT,
            ["in"],
            "enum_multi",
            "Has a(n) {value} goal",
            _ev_goal_category,
            options=_GOAL_OPTS,
        ),
        SignalDef(
            "top_priority",
            "Top tradeoff priority",
            CAT_INTENT,
            ["in"],
            "enum_multi",
            "Prioritizes {value}",
            _ev_top_priority,
            options=_PRIORITY_OPTS,
            derived=True,
        ),
        # ── Constraints & readiness (§2.3) ──
        SignalDef(
            "budget_band",
            "Budget band",
            CAT_CONSTRAINT,
            ["in"],
            "band",
            "Budget band is {value}",
            _ev_budget_band,
            options=_BUDGET_OPTS,
        ),
        SignalDef(
            "modality_pref",
            "Modality preference",
            CAT_CONSTRAINT,
            ["in"],
            "enum_multi",
            "Prefers {value} programs",
            _pref_in_eval("preferred_learning_style"),
            options=_MODALITY_OPTS,
        ),
        SignalDef(
            "target_degree_level",
            "Target degree level",
            CAT_CONSTRAINT,
            ["in"],
            "enum_multi",
            "Targeting a {value} degree",
            _pref_in_eval("target_degree_level"),
            options=_DEGREE_OPTS,
        ),
        SignalDef(
            "readiness_band",
            "Document readiness band",
            CAT_CONSTRAINT,
            ["in"],
            "band",
            "Document readiness is {value}",
            _ev_readiness_band,
            options=_BAND_OPTS,
        ),
        # ── Profile (§ demographic; nationality flagged protected) ──
        SignalDef(
            "nationality",
            "Nationality",
            CAT_PROFILE,
            ["in"],
            "enum_multi",
            "Nationality is {value}",
            _profile_in_eval("nationality"),
            protected=True,
            help_text="Protected attribute — segments skewing on it trigger a fairness warning.",
        ),
        SignalDef(
            "country_of_residence",
            "Country of residence",
            CAT_PROFILE,
            ["in"],
            "enum_multi",
            "Resides in {value}",
            _profile_in_eval("country_of_residence"),
        ),
    ]
    return {d.key: d for d in defs}


SIGNAL_REGISTRY: dict[str, SignalDef] = _build_registry()


def signal_dictionary_json() -> dict[str, Any]:
    """Payload for the frontend builder + the NL-bridge prompt."""
    return {
        "categories": [{"key": k, "label": v} for k, v in CATEGORY_LABELS.items()],
        "signals": [d.to_dict() for d in SIGNAL_REGISTRY.values()],
    }


def render_plain_language(field_key: str, operator: str, value: Any) -> str:
    """Render one rule as a plain sentence (spec §4)."""
    sig = SIGNAL_REGISTRY.get(field_key)
    if sig is None:
        return f"{field_key} {operator} {value}"
    rendered_value = value
    if isinstance(value, list):
        # map enum option values to labels where possible
        if sig.options:
            label_map = {o["value"]: o["label"] for o in sig.options}
            rendered_value = ", ".join(str(label_map.get(v, v)) for v in value)
        else:
            rendered_value = ", ".join(str(v) for v in value)
    elif sig.options:
        label_map = {o["value"]: o["label"] for o in sig.options}
        rendered_value = label_map.get(str(value), value)
    op_label = {"gt": "≥", "lt": "≤", "gte": "≥", "lte": "≤", "between": "between"}.get(
        operator, operator
    )
    try:
        return sig.plain_language.format(value=rendered_value, operator=op_label)
    except (KeyError, IndexError):
        return sig.plain_language
