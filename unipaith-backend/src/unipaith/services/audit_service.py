"""Admissions audit trail service — records who/when/what for pipeline actions."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.audit import AdmissionsAuditLog


class AuditService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log(
        self,
        *,
        institution_id: UUID,
        actor_user_id: UUID | None,
        action: str,
        entity_type: str,
        entity_id: str,
        application_id: UUID | None = None,
        description: str | None = None,
        old_value: dict | None = None,
        new_value: dict | None = None,
        metadata_json: dict | None = None,
    ) -> AdmissionsAuditLog:
        entry = AdmissionsAuditLog(
            institution_id=institution_id,
            application_id=application_id,
            actor_user_id=actor_user_id,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id),
            description=description,
            old_value=old_value,
            new_value=new_value,
            metadata_json=metadata_json,
        )
        self.db.add(entry)
        await self.db.flush()
        return entry

    async def list_logs(
        self,
        institution_id: UUID,
        application_id: UUID | None = None,
        action: str | None = None,
        entity_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AdmissionsAuditLog]:
        stmt = (
            select(AdmissionsAuditLog)
            .where(
                AdmissionsAuditLog.institution_id == institution_id,
            )
            .order_by(AdmissionsAuditLog.created_at.desc())
        )
        if application_id:
            stmt = stmt.where(
                AdmissionsAuditLog.application_id == application_id,
            )
        if action:
            stmt = stmt.where(AdmissionsAuditLog.action == action)
        if entity_type:
            stmt = stmt.where(
                AdmissionsAuditLog.entity_type == entity_type,
            )
        stmt = stmt.offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_logs(
        self,
        institution_id: UUID,
        application_id: UUID | None = None,
    ) -> int:
        from sqlalchemy import func

        stmt = select(func.count(AdmissionsAuditLog.id)).where(
            AdmissionsAuditLog.institution_id == institution_id,
        )
        if application_id:
            stmt = stmt.where(
                AdmissionsAuditLog.application_id == application_id,
            )
        result = await self.db.execute(stmt)
        return result.scalar() or 0
