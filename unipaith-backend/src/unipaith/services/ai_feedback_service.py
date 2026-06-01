"""Phase D1 — AI feedback service + weekly digest queries.

Two surfaces:

  1. **Per-student feedback submission** — students click thumbs /
     regenerate / "this isn't right" on any AI surface; the service
     upserts a row in `ai_turn_feedback`.

  2. **Admin weekly digest** — query helpers that surface low-confidence
     turns + thumbs-down feedback + safety incidents from the last N
     days. Returns structured data the admin UI renders; no LLM in the
     hot path here.

Why no LLM:
  Feedback collection is the *input* to the training flywheel, not part
  of the agent loop. Adding an LLM here would create a circular
  dependency (we'd be using the LLM to evaluate the LLM's own output).
  The digest surfaces raw signal for humans to label; agents only see
  the labeled fixtures via the eval harness.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.ai_artifacts import AiTurn
from unipaith.models.ai_feedback import AiTurnFeedback

logger = logging.getLogger(__name__)


# Allowed values — mirrors the DB CHECK constraints. Exposed for API
# schemas to reference without pulling in SQLAlchemy.
ALLOWED_VOTES = ("up", "down", "regenerate", "not_right")
ALLOWED_SURFACES = (
    "orchestrator_turn",
    "extractor_signal",
    "rationale",
    "workshop_essay",
    "workshop_interview",
    "workshop_test_prep",
    "match_card",
    "other",
)


# ── Output dataclasses for the digest ──────────────────────────────────────


@dataclass
class FeedbackBreakdown:
    """Aggregate counts for a digest section."""

    surface: str
    total: int
    up: int
    down: int
    regenerate: int
    not_right: int

    @property
    def negative_rate(self) -> float:
        bad = self.down + self.regenerate + self.not_right
        return bad / self.total if self.total else 0.0


@dataclass
class WeeklyDigest:
    """The structured payload the admin weekly-review surface consumes."""

    period_start: datetime
    period_end: datetime
    breakdowns: list[FeedbackBreakdown] = field(default_factory=list)
    top_negative_examples: list[dict[str, Any]] = field(default_factory=list)
    safety_incident_count: int = 0
    safety_incident_breakdown: dict[str, int] = field(default_factory=dict)
    low_confidence_turns: int = 0


# ── Service ────────────────────────────────────────────────────────────────


class AiFeedbackService:
    """Stateless — instantiate per-request with the session."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Per-student feedback submission ───────────────────────────────

    async def submit_feedback(
        self,
        *,
        student_id: UUID,
        target_id: UUID,
        surface: str,
        vote: str,
        reason_category: str | None = None,
        free_text: str | None = None,
        context: dict | None = None,
    ) -> AiTurnFeedback:
        """Upsert feedback for (student, target, surface).

        Idempotent — students can change their vote (latest wins) but we
        keep the row so updated_at reflects the latest interaction.
        Repeated submissions on the same target update in place.
        """
        if vote not in ALLOWED_VOTES:
            raise ValueError(f"vote={vote!r} not in {ALLOWED_VOTES} — DB CHECK would reject")
        if surface not in ALLOWED_SURFACES:
            raise ValueError(
                f"surface={surface!r} not in {ALLOWED_SURFACES} — DB CHECK would reject"
            )

        stmt = (
            pg_insert(AiTurnFeedback)
            .values(
                student_id=student_id,
                target_id=target_id,
                surface=surface,
                vote=vote,
                reason_category=reason_category,
                free_text=free_text,
                context=context,
            )
            .on_conflict_do_update(
                constraint="uq_ai_feedback_student_target_surface",
                set_={
                    "vote": vote,
                    "reason_category": reason_category,
                    "free_text": free_text,
                    "context": context,
                    "updated_at": func.now(),
                },
            )
            .returning(AiTurnFeedback)
        )
        result = await self.db.execute(stmt)
        row = result.scalar_one()
        await self.db.flush()

        # Spec 36 §2 — record the human verdict on the AI artifact (accept /
        # reject / regenerate). Append-only; student-scoped.
        from unipaith.services.audit_service import AuditService

        _vote_action = {
            "up": "ai_artifact_accepted",
            "down": "ai_artifact_rejected",
            "not_right": "ai_artifact_rejected",
            "regenerate": "ai_artifact_regenerated",
        }
        await AuditService(self.db).log(
            institution_id=None,
            actor_user_id=None,
            actor_role="student",
            action=_vote_action.get(vote, "ai_artifact_reviewed"),
            category="ai_generated",
            entity_type="ai_artifact",
            entity_id=str(target_id),
            metadata_json={
                "surface": surface,
                "vote": vote,
                "student_profile_id": str(student_id),
            },
        )
        return row

    # ── Read paths ────────────────────────────────────────────────────

    async def list_for_student(self, student_id: UUID, *, limit: int = 50) -> list[AiTurnFeedback]:
        result = await self.db.execute(
            select(AiTurnFeedback)
            .where(AiTurnFeedback.student_id == student_id)
            .order_by(desc(AiTurnFeedback.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    # ── Weekly digest ─────────────────────────────────────────────────

    async def weekly_digest(self, *, days: int = 7, top_n_examples: int = 10) -> WeeklyDigest:
        """Aggregate signal from the last `days` days into a structured
        digest. The admin UI iterates over the breakdowns + examples;
        labelers harvest top-negative turns into the eval fixtures.
        """
        period_end = datetime.now(UTC)
        period_start = period_end - timedelta(days=days)

        # Per-surface vote counts.
        breakdown_rows = await self.db.execute(
            select(
                AiTurnFeedback.surface,
                AiTurnFeedback.vote,
                func.count(AiTurnFeedback.id),
            )
            .where(AiTurnFeedback.created_at >= period_start)
            .group_by(AiTurnFeedback.surface, AiTurnFeedback.vote)
        )
        # Aggregate into FeedbackBreakdown per surface.
        agg: dict[str, dict[str, int]] = {}
        for surface, vote, count in breakdown_rows.all():
            d = agg.setdefault(
                surface,
                {"up": 0, "down": 0, "regenerate": 0, "not_right": 0},
            )
            d[vote] = int(count)
        breakdowns = [
            FeedbackBreakdown(
                surface=s,
                total=sum(d.values()),
                up=d["up"],
                down=d["down"],
                regenerate=d["regenerate"],
                not_right=d["not_right"],
            )
            for s, d in sorted(agg.items())
        ]

        # Top-negative examples — surfaced for labeler review. We pull
        # the most recent down/regenerate/not_right rows; admin UI
        # joins to the target row for context.
        neg_rows = await self.db.execute(
            select(AiTurnFeedback)
            .where(
                AiTurnFeedback.created_at >= period_start,
                AiTurnFeedback.vote.in_(("down", "regenerate", "not_right")),
            )
            .order_by(desc(AiTurnFeedback.created_at))
            .limit(top_n_examples)
        )
        top_negative_examples = [
            {
                "id": str(fb.id),
                "student_id": str(fb.student_id),
                "target_id": str(fb.target_id),
                "surface": fb.surface,
                "vote": fb.vote,
                "reason_category": fb.reason_category,
                "free_text": (fb.free_text or "")[:240],
                "created_at": fb.created_at.isoformat(),
            }
            for fb in neg_rows.scalars().all()
        ]

        # Safety incidents — uses ai_safety_incidents table from the A1
        # migration. Deferred-import the model to avoid a hard dep at
        # service load (the table may not be present in some local DB
        # snapshots that pre-date Phase A1).
        from sqlalchemy import text

        safety_count = 0
        safety_breakdown: dict[str, int] = {}
        try:
            sb = await self.db.execute(
                text(
                    "SELECT kind, count(*) FROM ai_safety_incidents "
                    "WHERE created_at >= :since GROUP BY kind"
                ),
                {"since": period_start},
            )
            for kind, count in sb.all():
                safety_breakdown[str(kind)] = int(count)
                safety_count += int(count)
        except Exception as exc:  # pragma: no cover — defensive
            logger.debug("ai_safety_incidents read failed in digest: %s", exc)

        # Low-confidence turns — extractor turns where downstream
        # confidence was sub-threshold. Proxy: ai_turns rows where the
        # agent is 'extractor' or 'orchestrator' AND cost or latency
        # was anomalously high (a heuristic — full implementation would
        # track per-turn confidence in a separate column).
        # Cold-start: count extractor turns with retries (latency_ms > 3000)
        # as a proxy. Refined in D2 once calibrator data exists.
        low_conf_count = await self.db.scalar(
            select(func.count(AiTurn.id)).where(
                AiTurn.created_at >= period_start,
                AiTurn.agent.in_(("extractor", "orchestrator")),
                AiTurn.latency_ms > 3000,
            )
        )

        return WeeklyDigest(
            period_start=period_start,
            period_end=period_end,
            breakdowns=breakdowns,
            top_negative_examples=top_negative_examples,
            safety_incident_count=safety_count,
            safety_incident_breakdown=safety_breakdown,
            low_confidence_turns=int(low_conf_count or 0),
        )
