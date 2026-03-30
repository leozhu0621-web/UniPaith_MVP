from fastapi import APIRouter

from unipaith.api.applications import router as applications_router
from unipaith.api.auth import router as auth_router
from unipaith.api.documents import router as documents_router
from unipaith.api.events import router as events_router
from unipaith.api.institutions import router as institutions_router
from unipaith.api.internal import router as internal_router
from unipaith.api.interviews import router as interviews_router
from unipaith.api.messaging import router as messaging_router
from unipaith.api.notifications import router as notifications_router
from unipaith.api.programs import router as programs_router
from unipaith.api.reviews import router as reviews_router
from unipaith.api.saved_lists import router as saved_lists_router
from unipaith.api.students import router as students_router
from unipaith.api.workshops import router as workshops_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(students_router)
api_router.include_router(institutions_router)
api_router.include_router(programs_router)
api_router.include_router(applications_router)
api_router.include_router(documents_router)
api_router.include_router(internal_router)
api_router.include_router(saved_lists_router)
api_router.include_router(workshops_router)
api_router.include_router(messaging_router)
api_router.include_router(events_router)
api_router.include_router(reviews_router)
api_router.include_router(interviews_router)
api_router.include_router(notifications_router)


@api_router.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok", "version": "0.1.0"}
