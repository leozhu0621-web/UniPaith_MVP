"""Admin dashboard API — system-wide overview stats."""

from fastapi import APIRouter, Depends
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
