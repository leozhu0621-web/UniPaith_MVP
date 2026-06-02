from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.api.ai_agents import router as ai_agents_router
from unipaith.api.ai_feedback import router as ai_feedback_router
from unipaith.api.ai_surface import router as ai_surface_router
from unipaith.api.analytics import router as analytics_router
from unipaith.api.applications import router as applications_router
from unipaith.api.auth import router as auth_router
from unipaith.api.billing import router as billing_router
from unipaith.api.build import router as build_router
from unipaith.api.calendar import router as calendar_router
from unipaith.api.connect import router as connect_router
from unipaith.api.discovery import router as discovery_router
from unipaith.api.documents import router as documents_router
from unipaith.api.events import router as events_router
from unipaith.api.goals import router as goals_router
from unipaith.api.governance import router as governance_router
from unipaith.api.graduate import router as graduate_router
from unipaith.api.identity import router as identity_router
from unipaith.api.inbox import router as inbox_router
from unipaith.api.institution_inbox import router as institution_inbox_router
from unipaith.api.institutions import router as institutions_router
from unipaith.api.intake import router as intake_router
from unipaith.api.interviews import router as interviews_router
from unipaith.api.major_specific import router as major_specific_router
from unipaith.api.messaging import router as messaging_router
from unipaith.api.needs import router as needs_router
from unipaith.api.notifications import router as notifications_router
from unipaith.api.payments import router as payments_router
from unipaith.api.programs import router as programs_router
from unipaith.api.prompt_library import router as prompt_library_router
from unipaith.api.recommendations import router as recommendations_router
from unipaith.api.recruitment import router as recruitment_router
from unipaith.api.reviews import router as reviews_router
from unipaith.api.saved_lists import router as saved_lists_router
from unipaith.api.search import router as search_router
from unipaith.api.settings import router as settings_router
from unipaith.api.strategy import router as strategy_router
from unipaith.api.students import router as students_router
from unipaith.api.workshop_feedback import router as workshop_feedback_router
from unipaith.api.workshops import router as workshops_router
from unipaith.database import get_db
from unipaith.models.institution import CampaignLink, CampaignRecipient
from unipaith.services.campaign_email_service import verify_unsubscribe_token
from unipaith.services.institution_service import InstitutionService

api_router = APIRouter()

api_router.include_router(auth_router)
# Spec 45 — public AI-agent catalog at `/ai/agents` (backs /goal/claude-api).
# No auth, DB-free; exposes only the agent architecture, never user data.
api_router.include_router(ai_agents_router)
# Spec 48/49/50 — public build-transparency surface at `/build/*` (backs the
# /goal hub + roadmap/features/api pages). No auth, DB-free; the api-contract
# map is derived live from the running route table.
api_router.include_router(build_router)
api_router.include_router(billing_router)
# Settings before students/institutions so literal `/institutions/settings` and
# `/students/me/settings` win over param routes like `/institutions/{id}`.
api_router.include_router(settings_router)
# Analytics (Spec 28) before institutions so `/institutions/me/analytics/*` is
# matched ahead of the param route `/institutions/{id}`.
api_router.include_router(analytics_router)
# Spec 42 — Prompt Library under `/students/me/prompt-library/*`; before
# students_router so its literal sub-paths win over any `/students/me/*` route.
api_router.include_router(prompt_library_router)
# Spec 43 — Major-Specific catalog under `/students/me/major-specific/*`; before
# students_router for the same literal-path-precedence reason.
api_router.include_router(major_specific_router)
# Spec 44 — Adaptive Intake Engine under `/students/me/intake/*`; before
# students_router so the literal sub-paths win over `/students/me/*` (and over
# the legacy `/students/me/intake/chat` stub still served by students_router).
api_router.include_router(intake_router)
api_router.include_router(students_router)
api_router.include_router(discovery_router)
api_router.include_router(goals_router)
api_router.include_router(needs_router)
api_router.include_router(identity_router)
api_router.include_router(strategy_router)
# Institution inbox before institutions_router so the literal
# `/institutions/me/inbox/*` paths win over any param route (spec 29).
api_router.include_router(institution_inbox_router)
# Spec 37 — AI edit-diff capture under `/institutions/me/ai-surface/*`; before
# institutions_router so the literal path wins over `/institutions/{id}`.
api_router.include_router(ai_surface_router)
# Spec 40 — recruitment CRM under `/institutions/me/recruitment/*`; before
# institutions_router so the literal path wins over `/institutions/{id}`.
api_router.include_router(recruitment_router)
# Spec 41 — graduate admissions under `/institutions/me/graduate/*` (+ the student
# `/students/me/applications/:id/graduate-intent`); before institutions_router so
# the literal path wins over `/institutions/{id}`.
api_router.include_router(graduate_router)
# Spec 46 §9/§10 — data-governance config + sub-processor list under
# `/institutions/me/data/*`; before institutions_router so the literal paths win
# over `/institutions/{id}`. (§6 fairness endpoints live in institutions.py.)
api_router.include_router(governance_router)
api_router.include_router(institutions_router)
api_router.include_router(programs_router)
api_router.include_router(applications_router)
# Spec 39 — fees & payments (student checkout/waiver + institution config/refunds).
api_router.include_router(payments_router)
api_router.include_router(documents_router)
api_router.include_router(saved_lists_router)
api_router.include_router(search_router)
api_router.include_router(workshops_router)
api_router.include_router(workshop_feedback_router)
api_router.include_router(ai_feedback_router)
api_router.include_router(messaging_router)
api_router.include_router(inbox_router)
api_router.include_router(events_router)
api_router.include_router(reviews_router)
api_router.include_router(interviews_router)
api_router.include_router(notifications_router)
api_router.include_router(recommendations_router)
api_router.include_router(calendar_router)
api_router.include_router(connect_router)


@api_router.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok", "version": "0.1.0"}


@api_router.post("/webhooks/stripe", tags=["payments"])
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    stripe_signature: str | None = Header(None, alias="Stripe-Signature"),
):
    """Public — Stripe posts payment/refund events here (Spec 39 §4).

    Signature-verified in stripe mode; a no-op in mock mode (the in-app confirm
    endpoint drives success instead). Updates fee/deposit status + advances any
    downstream enrollment state. ``get_db`` commits on success.
    """
    from unipaith.config import settings
    from unipaith.core.exceptions import BadRequestException
    from unipaith.services.payment_service import PaymentService

    if settings.payments_provider != "stripe":
        return {"status": "ignored", "reason": "payments_provider is not stripe"}

    payload = await request.body()
    svc = PaymentService(db)
    try:
        event = svc.provider.verify_and_parse_webhook(payload, stripe_signature)
    except Exception as exc:  # noqa: BLE001 — bad signature / malformed payload → 400
        raise BadRequestException("Invalid Stripe webhook signature") from exc
    await svc.handle_provider_event(event)
    # Subscription lifecycle (Spec 07 §4.1) → reconcile the student subscription
    # (renewals, failures, cancellations). Fee/deposit events are a no-op here.
    if event.type in (
        "invoice.payment_succeeded",
        "invoice.payment_failed",
        "customer.subscription.updated",
        "customer.subscription.deleted",
    ):
        from unipaith.services.billing_service import BillingService

        await BillingService(db).handle_subscription_event(event)
    return {"status": "ok", "event": event.type}


@api_router.get("/t/{short_code}", tags=["tracking"])
async def redirect_campaign_link(
    short_code: str,
    sid: UUID | None = Query(None, description="Student profile ID"),
    db: AsyncSession = Depends(get_db),
):
    """Public — redirect trackable campaign link and record click."""
    result = await db.execute(select(CampaignLink).where(CampaignLink.short_code == short_code))
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
        url = f"{base}/school/{link.institution_id}?tab=events&{cid_param}"
    elif link.destination_type == "post" and link.destination_id:
        url = f"{base}/school/{link.institution_id}?tab=posts&{cid_param}"
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
