"""Spec 26 — Audience Segmentation rule-tree engine, preview, suppression.

`SegmentService` evaluates a nested include/exclude rule tree over the signal
dictionary (`segment_signals`), scoping every match to the institution's
addressable students, applying the global outreach-suppression list, merging
uploaded prospect lists by email, and producing the audience preview (count +
10-row sample + composition + a lightweight fairness skew warning, §13 / `46`
§6). It also hosts the natural-language → rules bridge (§6, delegates to the
`SegmentBuilderNLBridge` agent with a rule-based fallback).

The rule tree (stored on `target_segments.rules`) has the shape::

    {
      "include": {"op": "AND"|"OR", "rules": [<node>, ...]},
      "exclude": {"op": "AND"|"OR", "rules": [<node>, ...]}
    }

where ``<node>`` is a leaf ``{field, operator, value}`` or a nested group
``{op, rules}`` (op ∈ AND/OR/NOT). Members =
``universe ∩ eval(include) − eval(exclude)``; an empty include is the whole
addressable universe. A bare list or a single group is normalized to an
include branch, so the NL bridge's flat rule list is directly usable.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
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
from unipaith.models.follow import InstitutionFollow
from unipaith.models.institution import (
    Event,
    EventRSVP,
    Inquiry,
    InstitutionDataset,
    Program,
)
from unipaith.models.matching import MatchResult
from unipaith.models.student import StudentDataConsent, StudentProfile
from unipaith.models.user import User
from unipaith.services.segment_signals import (
    SIGNAL_REGISTRY,
    EvalContext,
    render_plain_language,
)

_MAX_DEPTH = 6
_PROTECTED_ATTRS = ("nationality", "gender_identity")
_FAIRNESS_MIN_AUDIENCE = 20
_FAIRNESS_SKEW_THRESHOLD = 0.70


def _utcnow() -> datetime:
    return datetime.now(UTC)


class SegmentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── program scoping ──────────────────────────────────────────────────
    async def _program_ids(
        self, institution_id: uuid.UUID, segment_program_id: uuid.UUID | None = None
    ) -> list[uuid.UUID]:
        if segment_program_id:
            return [segment_program_id]
        rows = await self.db.execute(
            select(Program.id).where(Program.institution_id == institution_id)
        )
        return [r[0] for r in rows.all()]

    # ── addressable universe: students connected to this institution ──────
    async def addressable_universe(
        self, institution_id: uuid.UUID, program_ids: list[uuid.UUID]
    ) -> set[uuid.UUID]:
        ids: set[uuid.UUID] = set()
        # Institution-scoped sources
        inst_sources = [
            select(InstitutionFollow.student_id).where(
                InstitutionFollow.institution_id == institution_id
            ),
            select(Inquiry.student_id).where(
                Inquiry.institution_id == institution_id, Inquiry.student_id.isnot(None)
            ),
            select(EventRSVP.student_id)
            .join(Event, Event.id == EventRSVP.event_id)
            .where(Event.institution_id == institution_id),
        ]
        for stmt in inst_sources:
            rows = await self.db.execute(stmt.distinct())
            ids.update(r[0] for r in rows.all() if r[0] is not None)

        # Program-scoped sources
        if program_ids:
            prog_sources = [
                select(StudentEngagementSignal.student_id).where(
                    StudentEngagementSignal.program_id.in_(program_ids)
                ),
                select(StudentCompareItem.student_id).where(
                    StudentCompareItem.program_id.in_(program_ids)
                ),
                select(Application.student_id).where(Application.program_id.in_(program_ids)),
                select(MatchResult.student_id).where(MatchResult.program_id.in_(program_ids)),
                select(SavedList.student_id)
                .join(SavedListItem, SavedListItem.list_id == SavedList.id)
                .where(SavedListItem.program_id.in_(program_ids)),
            ]
            for stmt in prog_sources:
                rows = await self.db.execute(stmt.distinct())
                ids.update(r[0] for r in rows.all() if r[0] is not None)
        return ids

    # ── rule-tree evaluation ─────────────────────────────────────────────
    @staticmethod
    def _normalize(rules: Any) -> dict[str, Any]:
        """Coerce any accepted rules shape into {include, exclude} branches."""
        empty = {"op": "AND", "rules": []}
        if not rules:
            return {"include": empty, "exclude": dict(empty)}
        if isinstance(rules, list):
            return {"include": {"op": "AND", "rules": rules}, "exclude": dict(empty)}
        if isinstance(rules, dict):
            if "include" in rules or "exclude" in rules:
                return {
                    "include": rules.get("include") or dict(empty),
                    "exclude": rules.get("exclude") or dict(empty),
                }
            if "op" in rules or "rules" in rules:
                return {"include": rules, "exclude": dict(empty)}
        return {"include": empty, "exclude": dict(empty)}

    async def _eval_leaf(
        self,
        institution_id: uuid.UUID,
        program_ids: list[uuid.UUID],
        now: datetime,
        leaf: dict[str, Any],
    ) -> set[uuid.UUID]:
        field = leaf.get("field")
        sig = SIGNAL_REGISTRY.get(field)
        if sig is None:
            return set()
        ctx = EvalContext(
            db=self.db,
            institution_id=institution_id,
            program_ids=program_ids,
            now=now,
            operator=leaf.get("operator") or (sig.operators[0] if sig.operators else "in"),
            value=leaf.get("value"),
        )
        try:
            return await sig.evaluate(ctx)
        except Exception:  # noqa: BLE001 — a bad rule never breaks the whole preview
            return set()

    async def _eval_node(
        self,
        institution_id: uuid.UUID,
        program_ids: list[uuid.UUID],
        now: datetime,
        node: Any,
        universe: set[uuid.UUID],
        depth: int = 0,
    ) -> set[uuid.UUID]:
        if depth > _MAX_DEPTH or not isinstance(node, dict):
            return set()
        # leaf
        if "field" in node:
            return await self._eval_leaf(institution_id, program_ids, now, node)
        # group
        op = str(node.get("op", "AND")).upper()
        children = node.get("rules") or []
        if not children:
            # an empty group matches everything in scope (no constraint)
            return set(universe)
        child_sets: list[set[uuid.UUID]] = []
        for child in children:
            child_sets.append(
                await self._eval_node(institution_id, program_ids, now, child, universe, depth + 1)
            )
        if op == "OR":
            out: set[uuid.UUID] = set()
            for s in child_sets:
                out |= s
            return out
        if op == "NOT":
            negated: set[uuid.UUID] = set()
            for s in child_sets:
                negated |= s
            return universe - negated
        # AND (default)
        out = set(universe)
        for s in child_sets:
            out &= s
        return out

    async def evaluate_rules(
        self,
        institution_id: uuid.UUID,
        rules: Any,
        program_id: uuid.UUID | None = None,
    ) -> set[uuid.UUID]:
        program_ids = await self._program_ids(institution_id, program_id)
        universe = await self.addressable_universe(institution_id, program_ids)
        norm = self._normalize(rules)
        now = _utcnow()

        include = norm["include"]
        if include.get("rules"):
            inc = await self._eval_node(institution_id, program_ids, now, include, universe)
            members = universe & inc
        else:
            members = set(universe)

        exclude = norm["exclude"]
        if exclude.get("rules"):
            exc = await self._eval_node(institution_id, program_ids, now, exclude, universe)
            members -= exc
        return members

    # ── suppression (§5) ─────────────────────────────────────────────────
    async def _suppressed_ids(self, student_ids: set[uuid.UUID]) -> set[uuid.UUID]:
        """Students who have explicitly turned off outreach consent."""
        if not student_ids:
            return set()
        rows = await self.db.execute(
            select(StudentDataConsent.student_id).where(
                StudentDataConsent.student_id.in_(student_ids),
                StudentDataConsent.consent_outreach.is_(False),
            )
        )
        return {r[0] for r in rows.all()}

    async def apply_suppression(
        self, student_ids: set[uuid.UUID], extra_suppression: set[uuid.UUID] | None = None
    ) -> set[uuid.UUID]:
        remaining = set(student_ids)
        remaining -= await self._suppressed_ids(remaining)
        if extra_suppression:
            remaining -= extra_suppression
        return remaining

    # ── uploaded lists (§2.5) — merge/dedupe by email ────────────────────
    async def _uploaded_list_emails(
        self, institution_id: uuid.UUID, uploaded_list_ids: list[str]
    ) -> set[str]:
        """Best-effort extraction of contact emails from prospect-list datasets.

        Reads the dataset's stored CSV via the Spec 24 helpers; on any failure
        (e.g. S3 unavailable in dev) the list silently contributes no emails
        rather than breaking the preview.
        """
        if not uploaded_list_ids:
            return set()
        try:
            ids = [uuid.UUID(str(x)) for x in uploaded_list_ids]
        except (ValueError, TypeError):
            return set()
        rows = await self.db.execute(
            select(InstitutionDataset).where(
                InstitutionDataset.id.in_(ids),
                InstitutionDataset.institution_id == institution_id,
                InstitutionDataset.dataset_type == "prospect_list",
            )
        )
        datasets = list(rows.scalars().all())
        if not datasets:
            return set()
        from unipaith.services import dataset_upload_service as dus

        emails: set[str] = set()
        for ds in datasets:
            try:
                content = dus._read_dataset_content(ds.s3_key)
                _cols, raw_rows = dus._parse_rows(content)
                mapping = ds.column_mapping or {}
                for raw in raw_rows:
                    mapped = dus._mapped_row(raw, mapping) if mapping else raw
                    email = (mapped.get("email") or raw.get("email") or "").strip().lower()
                    if email:
                        emails.add(email)
            except Exception:  # noqa: BLE001
                continue
        return emails

    async def _emails_to_student_ids(self, emails: set[str]) -> dict[str, uuid.UUID]:
        """Resolve uploaded emails to platform student_profile ids (merge by email)."""
        if not emails:
            return {}
        rows = await self.db.execute(
            select(func.lower(User.email), StudentProfile.id)
            .join(StudentProfile, StudentProfile.user_id == User.id)
            .where(func.lower(User.email).in_(list(emails)))
        )
        return {r[0]: r[1] for r in rows.all()}

    # ── preview (§3 / §7) ────────────────────────────────────────────────
    async def preview(
        self,
        institution_id: uuid.UUID,
        rules: Any,
        uploaded_list_ids: list[str] | None = None,
        program_id: uuid.UUID | None = None,
        sample_size: int = 10,
    ) -> dict[str, Any]:
        members = await self.evaluate_rules(institution_id, rules, program_id)
        members = await self.apply_suppression(members)

        # Merge uploaded prospect lists by email.
        uploaded_emails = await self._uploaded_list_emails(institution_id, uploaded_list_ids or [])
        matched = await self._emails_to_student_ids(uploaded_emails)
        # platform users found in the uploaded list join the audience (still
        # honoring suppression for those resolved to a platform student)
        matched_ids = set(matched.values())
        if matched_ids:
            matched_ids = await self.apply_suppression(matched_ids)
            members |= matched_ids
        external_only = len(uploaded_emails) - len(matched)  # emails with no platform user

        platform_count = len(members)
        total_count = platform_count + max(0, external_only)

        sample = await self._student_summaries(list(members)[:sample_size], institution_id)
        composition = await self._composition(members)
        fairness_warning = self._fairness_warning(composition, platform_count)

        return {
            "audience_count": total_count,
            "platform_count": platform_count,
            "uploaded_external_count": max(0, external_only),
            "sample": sample,
            "composition": composition,
            "fairness_warning": fairness_warning,
        }

    async def _student_summaries(
        self, student_ids: list[uuid.UUID], institution_id: uuid.UUID
    ) -> list[dict[str, Any]]:
        if not student_ids:
            return []
        rows = await self.db.execute(
            select(
                StudentProfile.id,
                StudentProfile.first_name,
                StudentProfile.last_name,
                StudentProfile.preferred_name,
                StudentProfile.nationality,
                StudentProfile.country_of_residence,
                User.email,
            )
            .join(User, User.id == StudentProfile.user_id)
            .where(StudentProfile.id.in_(student_ids))
        )
        # fit band per student for this institution
        program_ids = await self._program_ids(institution_id)
        fit_map: dict[uuid.UUID, float] = {}
        if program_ids:
            frows = await self.db.execute(
                select(MatchResult.student_id, func.max(MatchResult.fitness_score))
                .where(
                    MatchResult.student_id.in_(student_ids),
                    MatchResult.program_id.in_(program_ids),
                )
                .group_by(MatchResult.student_id)
            )
            fit_map = {r[0]: float(r[1] or 0) for r in frows.all()}

        out: list[dict[str, Any]] = []
        for r in rows.all():
            sid = r[0]
            fit = fit_map.get(sid)
            band = None
            if fit is not None:
                band = "high" if fit >= 0.75 else "medium" if fit >= 0.50 else "low"
            name = r[3] or " ".join(p for p in [r[1], r[2]] if p) or "Unnamed student"
            out.append(
                {
                    "student_id": str(sid),
                    "name": name,
                    "email": r[6],
                    "nationality": r[4],
                    "country_of_residence": r[5],
                    "fit_band": band,
                }
            )
        return out

    async def _composition(self, student_ids: set[uuid.UUID]) -> dict[str, Any]:
        if not student_ids:
            return {}
        out: dict[str, Any] = {}
        for attr in _PROTECTED_ATTRS:
            col = getattr(StudentProfile, attr)
            rows = await self.db.execute(
                select(col, func.count()).where(StudentProfile.id.in_(student_ids)).group_by(col)
            )
            dist = {(r[0] or "Unknown"): int(r[1]) for r in rows.all()}
            if dist:
                out[attr] = dist
        return out

    def _fairness_warning(self, composition: dict[str, Any], audience_count: int) -> str | None:
        """Spec §13 / `46` §6 — warn when a segment heavily skews on a protected
        attribute. Lightweight pre-send check (not the matching auto-halt)."""
        if audience_count < _FAIRNESS_MIN_AUDIENCE:
            return None
        for attr in _PROTECTED_ATTRS:
            dist = composition.get(attr)
            if not dist:
                continue
            known = {k: v for k, v in dist.items() if k != "Unknown"}
            total = sum(known.values())
            if total < _FAIRNESS_MIN_AUDIENCE:
                continue
            top_key, top_val = max(known.items(), key=lambda kv: kv[1])
            if top_val / total >= _FAIRNESS_SKEW_THRESHOLD:
                pct = round(100 * top_val / total)
                label = attr.replace("_", " ")
                return (
                    f"This audience skews heavily on {label} "
                    f"({pct}% {top_key}). Review for fairness before sending."
                )
        return None

    # ── plain-language rendering helper (§4) ─────────────────────────────
    @staticmethod
    def render_rule(leaf: dict[str, Any]) -> str:
        return render_plain_language(leaf.get("field"), leaf.get("operator"), leaf.get("value"))

    # ── NL bridge (§6) ───────────────────────────────────────────────────
    async def nl_bridge(self, text: str) -> dict[str, Any]:
        from unipaith.ai.segment_builder import SegmentBuilderNLBridge

        agent = SegmentBuilderNLBridge(self.db)
        return await agent.convert(text)
