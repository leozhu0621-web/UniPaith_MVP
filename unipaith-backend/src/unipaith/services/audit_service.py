"""Audit trail service (Spec 36) — records who/when/what for every
consequential action and serves the append-only log.

The audit log is "the substrate other surfaces consume": ~25 trigger points
across the admissions pipeline call :meth:`AuditService.log`. Writes infer the
§2 ``category`` and the ``actor_role`` from the action when the caller does not
supply them, so existing call sites need no change.
"""

from __future__ import annotations

import csv
import io
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.audit import AdmissionsAuditLog

# ── Category taxonomy (Spec 36 §2) ───────────────────────────────────────────
# The 13 canonical categories, plus the cross-cutting buckets the audit log
# also captures (message / team_invite / review / other). ``batch_*`` actions
# keep their specific action string as the category (matches the §2 glob).
AUDIT_CATEGORIES: tuple[str, ...] = (
    "status_change",
    "decision_release",
    "reviewer_assigned",
    "checklist_change",
    "document_replaced",
    "waiver_override",
    "ai_generated",
    "consent_change",
    "data_export",
    "data_deletion",
    "fairness_signal_override",
    "integrity_resolution",
)

# Override categories require a free-text reason (Spec 36 §3).
OVERRIDE_CATEGORIES: frozenset[str] = frozenset({"waiver_override", "fairness_signal_override"})


def infer_category(action: str) -> str:
    """Map a specific ``action`` to its §2 category bucket."""
    a = (action or "").lower()
    if a in ("status_change", "submitted", "status_updated"):
        return "status_change"
    if a in ("decision_release", "decision_outcome"):
        return "decision_release"
    if a in ("reviewer_assigned", "reviewer_removed"):
        return "reviewer_assigned"
    if a.startswith("checklist"):
        return "checklist_change"
    if a.startswith("dataset") or a.startswith("document"):
        return "document_replaced"
    if a.startswith("waiver"):
        return "waiver_override"
    if a.startswith("batch_"):
        # Spec 36 §2 treats ``batch_*`` as a single category; the specific
        # batch kind is preserved in ``action``.
        return "batch_action"
    if a.startswith("integrity") or a == "ignore":
        return "integrity_resolution"
    if a.startswith("ai_generated") or a.startswith("ai_artifact"):
        return "ai_generated"
    if a.startswith("consent"):
        return "consent_change"
    if a == "data_export":
        return "data_export"
    if a.startswith("data_deletion") or a.startswith("account_deletion"):
        return "data_deletion"
    if a.startswith("fairness"):
        return "fairness_signal_override"
    if a.startswith("inbox."):
        return "message"
    if a.startswith("team"):
        return "team_invite"
    if a == "blind_review_reveal":
        return "review"
    return "other"


def infer_actor_role(actor_user_id: UUID | None, actor_role: str | None = None) -> str:
    """Best-effort actor-role classification.

    Explicit ``actor_role`` wins (callers pass ``'student'`` / ``'ai_agent'``
    where relevant). Otherwise: no actor → ``system``; an actor → the most
    common case in the admissions pipeline, ``institution_admin``.
    """
    if actor_role:
        return actor_role
    if actor_user_id is None:
        return "system"
    return "institution_admin"


class AuditService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log(
        self,
        *,
        institution_id: UUID | None,
        actor_user_id: UUID | None,
        action: str,
        entity_type: str,
        entity_id: str,
        application_id: UUID | None = None,
        description: str | None = None,
        old_value: dict | None = None,
        new_value: dict | None = None,
        metadata_json: dict | None = None,
        category: str | None = None,
        actor_role: str | None = None,
        reason: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AdmissionsAuditLog:
        entry = AdmissionsAuditLog(
            institution_id=institution_id,
            application_id=application_id,
            actor_user_id=actor_user_id,
            category=category or infer_category(action),
            actor_role=infer_actor_role(actor_user_id, actor_role),
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id),
            description=description,
            reason=reason,
            old_value=old_value,
            new_value=new_value,
            metadata_json=metadata_json,
            ip_address=ip_address,
            user_agent=(user_agent[:1000] if user_agent else None),
        )
        self.db.add(entry)
        await self.db.flush()
        return entry

    # ── reads ────────────────────────────────────────────────────────────────

    def _apply_filters(
        self,
        stmt,
        *,
        institution_id: UUID | None,
        application_id: UUID | None,
        action: str | None,
        entity_type: str | None,
        category: str | None,
        actor_user_id: UUID | None,
        date_from: datetime | None,
        date_to: datetime | None,
        scope_institution: bool,
    ):
        if scope_institution:
            # Tenant isolation — an institution only ever sees its own events.
            stmt = stmt.where(AdmissionsAuditLog.institution_id == institution_id)
        if application_id:
            stmt = stmt.where(AdmissionsAuditLog.application_id == application_id)
        if action:
            stmt = stmt.where(AdmissionsAuditLog.action == action)
        if entity_type:
            stmt = stmt.where(AdmissionsAuditLog.entity_type == entity_type)
        if category:
            stmt = stmt.where(AdmissionsAuditLog.category == category)
        if actor_user_id:
            stmt = stmt.where(AdmissionsAuditLog.actor_user_id == actor_user_id)
        if date_from:
            stmt = stmt.where(AdmissionsAuditLog.created_at >= date_from)
        if date_to:
            stmt = stmt.where(AdmissionsAuditLog.created_at <= date_to)
        return stmt

    async def list_logs(
        self,
        institution_id: UUID | None,
        application_id: UUID | None = None,
        action: str | None = None,
        entity_type: str | None = None,
        category: str | None = None,
        actor_user_id: UUID | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
        scope_institution: bool = True,
    ) -> list[AdmissionsAuditLog]:
        stmt = self._apply_filters(
            select(AdmissionsAuditLog),
            institution_id=institution_id,
            application_id=application_id,
            action=action,
            entity_type=entity_type,
            category=category,
            actor_user_id=actor_user_id,
            date_from=date_from,
            date_to=date_to,
            scope_institution=scope_institution,
        ).order_by(AdmissionsAuditLog.created_at.desc())
        stmt = stmt.offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_logs(
        self,
        institution_id: UUID | None,
        application_id: UUID | None = None,
        action: str | None = None,
        entity_type: str | None = None,
        category: str | None = None,
        actor_user_id: UUID | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        scope_institution: bool = True,
    ) -> int:
        stmt = self._apply_filters(
            select(func.count(AdmissionsAuditLog.id)),
            institution_id=institution_id,
            application_id=application_id,
            action=action,
            entity_type=entity_type,
            category=category,
            actor_user_id=actor_user_id,
            date_from=date_from,
            date_to=date_to,
            scope_institution=scope_institution,
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def get_event(self, institution_id: UUID, event_id: UUID) -> AdmissionsAuditLog | None:
        """Single event scoped to the institution (tenant-isolated)."""
        stmt = select(AdmissionsAuditLog).where(
            AdmissionsAuditLog.id == event_id,
            AdmissionsAuditLog.institution_id == institution_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def student_events(
        self,
        actor_user_id: UUID,
        application_ids: list[UUID],
        limit: int = 100,
    ) -> list[AdmissionsAuditLog]:
        """Events relevant to a student: their own actions (consent / export /
        deletion) plus institution actions on their applications. Powers the
        Spec 36 §5 student access-log ("who saw your data")."""
        conds = [AdmissionsAuditLog.actor_user_id == actor_user_id]
        if application_ids:
            conds.append(AdmissionsAuditLog.application_id.in_(application_ids))
        stmt = (
            select(AdmissionsAuditLog)
            .where(or_(*conds))
            .order_by(AdmissionsAuditLog.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ── export (Spec 36 §13) ──────────────────────────────────────────────────

    CSV_HEADER = (
        "occurred_at",
        "category",
        "action",
        "actor_role",
        "actor_email",
        "entity_type",
        "entity_id",
        "reason",
        "description",
        "ip_address",
    )

    @classmethod
    def to_csv(cls, rows: list[AdmissionsAuditLog]) -> str:
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(cls.CSV_HEADER)
        for r in rows:
            actor_email = getattr(getattr(r, "actor_user", None), "email", None)
            writer.writerow(
                [
                    r.created_at.isoformat() if r.created_at else "",
                    r.category or "",
                    r.action or "",
                    r.actor_role or "",
                    actor_email or "",
                    r.entity_type or "",
                    r.entity_id or "",
                    r.reason or "",
                    r.description or "",
                    r.ip_address or "",
                ]
            )
        return buf.getvalue()
