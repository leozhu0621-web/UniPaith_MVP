from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.feedback import Feedback


class FeedbackService:
    """Create + list demo feedback submissions. The request's ``get_db``
    dependency commits on success (repo convention), so this only flushes."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        *,
        user_id: uuid.UUID | None,
        role: str | None,
        title: str | None,
        message: str,
        context: dict | None,
        user_agent: str | None,
    ) -> Feedback:
        fb = Feedback(
            user_id=user_id,
            role=role,
            title=title,
            message=message,
            context=context,
            user_agent=user_agent,
        )
        self.db.add(fb)
        await self.db.flush()
        await self.db.refresh(fb)
        return fb

    async def list_all(self, limit: int = 1000) -> list[Feedback]:
        result = await self.db.execute(
            select(Feedback).order_by(Feedback.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())
