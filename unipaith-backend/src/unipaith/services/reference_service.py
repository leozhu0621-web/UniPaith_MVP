"""Read-only access to the Spec 60 reference layer (institution directory).

The first public read surface over ``ref_*``. Read-only and public: these are
non-personal, source-cited reference facts (College Scorecard bulk seed).
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models import RefInstitution, RefMajor, RefOccupation


class ReferenceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def search_institutions(
        self,
        *,
        q: str | None = None,
        state: str | None = None,
        control: str | None = None,
        min_size: int | None = None,
        limit: int = 25,
        offset: int = 0,
    ) -> list[RefInstitution]:
        stmt = select(RefInstitution)
        if q:
            stmt = stmt.where(RefInstitution.name.ilike(f"%{q}%"))
        if state:
            stmt = stmt.where(RefInstitution.state == state.upper())
        if control:
            stmt = stmt.where(RefInstitution.control == control)
        if min_size:
            stmt = stmt.where(RefInstitution.size >= min_size)
        stmt = stmt.order_by(RefInstitution.name).limit(min(limit, 100)).offset(offset)
        return list((await self.db.scalars(stmt)).all())

    async def get_institution(self, unitid: int) -> RefInstitution | None:
        return await self.db.scalar(select(RefInstitution).where(RefInstitution.unitid == unitid))

    async def search_majors(
        self, *, q: str | None = None, limit: int = 25, offset: int = 0
    ) -> list[RefMajor]:
        stmt = select(RefMajor)
        if q:
            stmt = stmt.where(RefMajor.title.ilike(f"%{q}%"))
        stmt = stmt.order_by(RefMajor.cip_code).limit(min(limit, 100)).offset(offset)
        return list((await self.db.scalars(stmt)).all())

    async def get_major(self, cip_code: str) -> RefMajor | None:
        return await self.db.scalar(select(RefMajor).where(RefMajor.cip_code == cip_code))

    async def search_occupations(
        self, *, q: str | None = None, limit: int = 25, offset: int = 0
    ) -> list[RefOccupation]:
        stmt = select(RefOccupation)
        if q:
            stmt = stmt.where(RefOccupation.title.ilike(f"%{q}%"))
        stmt = stmt.order_by(RefOccupation.soc_code).limit(min(limit, 100)).offset(offset)
        return list((await self.db.scalars(stmt)).all())

    async def get_occupation(self, soc_code: str) -> RefOccupation | None:
        return await self.db.scalar(select(RefOccupation).where(RefOccupation.soc_code == soc_code))
