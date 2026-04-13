from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.api.admin_dashboard import router as admin_dashboard_router
from unipaith.api.applications import router as applications_router
from unipaith.api.auth import router as auth_router
from unipaith.api.conversation import router as conversation_router
from unipaith.api.crawler_admin import router as crawler_admin_router
from unipaith.api.documents import router as documents_router
from unipaith.api.events import router as events_router
from unipaith.api.institutions import router as institutions_router
from unipaith.api.internal import router as internal_router
from unipaith.api.interviews import router as interviews_router
from unipaith.api.knowledge_admin import router as knowledge_admin_router
from unipaith.api.messaging import router as messaging_router
from unipaith.api.ml_admin import router as ml_admin_router
from unipaith.api.notifications import router as notifications_router
from unipaith.api.pipeline import router as pipeline_router
from unipaith.api.programs import router as programs_router
from unipaith.api.recommendations import router as recommendations_router
from unipaith.api.reviews import router as reviews_router
from unipaith.api.saved_lists import router as saved_lists_router
from unipaith.api.students import router as students_router
from unipaith.api.workshops import router as workshops_router
from unipaith.database import get_db
from unipaith.models.institution import CampaignLink, CampaignRecipient
from unipaith.services.campaign_email_service import verify_unsubscribe_token
from unipaith.services.institution_service import InstitutionService

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(students_router)
api_router.include_router(conversation_router)
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
api_router.include_router(recommendations_router)
api_router.include_router(ml_admin_router)
api_router.include_router(crawler_admin_router)
api_router.include_router(admin_dashboard_router)
api_router.include_router(knowledge_admin_router)
api_router.include_router(pipeline_router)


@api_router.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok", "version": "0.1.0"}


@api_router.get("/t/{short_code}", tags=["tracking"])
async def redirect_campaign_link(
    short_code: str,
    sid: UUID | None = Query(None, description="Student profile ID"),
    db: AsyncSession = Depends(get_db),
):
    """Public — redirect trackable campaign link and record click."""
    result = await db.execute(
        select(CampaignLink).where(CampaignLink.short_code == short_code)
    )
    link = result.scalar_one_or_none()
    if not link:
        return RedirectResponse("https://app.unipaith.co", status_code=302)

    svc = InstitutionService(db)
    await svc.record_link_click(short_code, student_id=sid)
    await db.commit()

    # Resolve destination URL
    base = "https://app.unipaith.co"
    cid_param = f"cid={link.campaign_id}"
    if link.destination_type == "custom" and link.custom_url:
        sep = "&" if "?" in link.custom_url else "?"
        url = f"{link.custom_url}{sep}{cid_param}"
    elif link.destination_type == "program" and link.destination_id:
        url = f"{base}/programs/{link.destination_id}?{cid_param}"
    elif link.destination_type == "institution" and link.destination_id:
        url = f"{base}/school/{link.destination_id}?{cid_param}"
    elif link.destination_type == "event" and link.destination_id:
        url = (
            f"{base}/school/{link.institution_id}"
            f"?tab=events&{cid_param}"
        )
    elif link.destination_type == "post" and link.destination_id:
        url = (
            f"{base}/school/{link.institution_id}"
            f"?tab=posts&{cid_param}"
        )
    else:
        url = base

    return RedirectResponse(url, status_code=302)


_UNSUB_PATH = "/campaigns/unsubscribe/{recipient_id}"


@api_router.get(
    _UNSUB_PATH,
    tags=["campaigns"],
    response_class=HTMLResponse,
)
async def unsubscribe_from_campaign(
    recipient_id: UUID,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Public — recipient clicks from email to unsubscribe."""
    if not verify_unsubscribe_token(recipient_id, token):
        return HTMLResponse(
            "<h2>Invalid link</h2><p>Contact support.</p>",
            status_code=400,
        )

    result = await db.execute(
        select(CampaignRecipient).where(
            CampaignRecipient.id == recipient_id,
        )
    )
    recipient = result.scalar_one_or_none()
    if not recipient:
        return HTMLResponse("<h2>Already unsubscribed</h2>")

    await db.delete(recipient)
    await db.commit()

    html = (
        '<div style="font-family:sans-serif;max-width:500px;'
        'margin:80px auto;text-align:center">'
        "<h2>You've been unsubscribed</h2>"
        "<p>You will no longer receive emails from this campaign.</p>"
        '<a href="https://app.unipaith.co">Return to UniPaith</a>'
        "</div>"
    )
    return HTMLResponse(html)
