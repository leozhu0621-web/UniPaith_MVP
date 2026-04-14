"""Admin dashboard API — system-wide overview stats."""

from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.dependencies import require_admin
from unipaith.models.user import User
from unipaith.services.internal_admin_service import InternalAdminService

router = APIRouter(prefix="/admin/dashboard", tags=["admin-dashboard"])


@router.get("/stats")
async def get_system_stats(
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get system-wide statistics for the admin dashboard."""
    return await InternalAdminService(db).get_dashboard_stats()


class InstitutionPatchRequest(BaseModel):
    logo_url: str | None = None
    media_gallery: list[str] | None = None
    description_text: str | None = None
    campus_description: str | None = None


@router.put("/institutions/{institution_id}")
async def admin_update_institution(
    institution_id: UUID,
    body: InstitutionPatchRequest,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin endpoint to patch any institution's images/descriptions."""
    from unipaith.models.institution import Institution

    result = await db.execute(
        select(Institution).where(Institution.id == institution_id)
    )
    inst = result.scalar_one_or_none()
    if not inst:
        from unipaith.core.exceptions import NotFoundException

        raise NotFoundException("Institution not found")

    if body.logo_url is not None:
        inst.logo_url = body.logo_url
    if body.media_gallery is not None:
        inst.media_gallery = body.media_gallery
    if body.description_text is not None:
        inst.description_text = body.description_text
    if body.campus_description is not None:
        inst.campus_description = body.campus_description

    await db.flush()
    return {"status": "updated", "id": str(inst.id), "name": inst.name}
