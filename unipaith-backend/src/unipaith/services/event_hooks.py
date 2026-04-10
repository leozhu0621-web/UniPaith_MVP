"""
Event hooks — standalone async functions that wire notifications and CRM touchpoints
into platform actions. Called by API routes or services after key events.

Every function follows the same pattern:
1. Create NotificationService(db) and call notify()
2. Create CRMService(db) and call log_touchpoint()
3. Catch all exceptions and log them (never fail the parent operation)
"""

from __future__ import annotations

import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ml.outcome_collector import OutcomeCollector
from unipaith.services.crm_service import CRMService
from unipaith.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


async def on_application_submitted(
    db: AsyncSession,
    student_id: UUID,
    student_user_id: UUID,
    application_id: UUID,
    program_id: UUID,
    institution_id: UUID,
    admin_user_id: UUID,
    confirmation_number: str,
) -> None:
    """Notify institution admin and log CRM touchpoint when an application is submitted."""
    try:
        notifications = NotificationService(db)
        await notifications.notify(
            user_id=admin_user_id,
            notification_type="application_submitted",
            title="New Application Received",
            body=f"A new application (#{confirmation_number}) has been submitted.",
            action_url=f"/applications/{application_id}",
            metadata={
                "application_id": str(application_id),
                "program_id": str(program_id),
                "confirmation_number": confirmation_number,
            },
        )

        crm = CRMService(db)
        await crm.log_touchpoint(
            student_id=student_id,
            touchpoint_type="application_submitted",
            institution_id=institution_id,
            program_id=program_id,
            application_id=application_id,
            description=f"Application submitted (#{confirmation_number})",
        )

        # Proactive AI: auto-generate packet summary + integrity scan
        try:
            from unipaith.services.review_pipeline_service import (
                ReviewPipelineService,
            )

            review_svc = ReviewPipelineService(db)
            await review_svc.get_or_generate_packet_summary(
                institution_id, application_id,
            )
            await review_svc.scan_integrity(
                institution_id, application_id,
            )
            logger.info(
                "Auto-generated AI packet + integrity scan for %s",
                application_id,
            )
        except Exception:
            logger.warning(
                "Proactive AI failed for application %s (non-fatal)",
                application_id,
            )
    except Exception:
        logger.exception("Hook on_application_submitted failed for application %s", application_id)


async def on_reviewer_assigned(
    db: AsyncSession,
    reviewer_user_id: UUID,
    application_id: UUID,
    due_date: datetime,
) -> None:
    """Notify a reviewer when they are assigned to review an application."""
    try:
        notifications = NotificationService(db)
        await notifications.notify(
            user_id=reviewer_user_id,
            notification_type="reviewer_assigned",
            title="New Review Assignment",
            body=(
                "You have been assigned to review application."
                f" Due by {due_date.strftime('%B %d, %Y')}."
            ),
            action_url=f"/reviews/applications/{application_id}",
            metadata={
                "application_id": str(application_id),
                "due_date": due_date.isoformat(),
            },
        )
    except Exception:
        logger.exception("Hook on_reviewer_assigned failed for application %s", application_id)


async def on_interview_scheduled(
    db: AsyncSession,
    student_user_id: UUID,
    application_id: UUID,
    interview_id: UUID,
    proposed_times: list[str],
) -> None:
    """Notify a student when an interview is scheduled for their application."""
    try:
        times_text = ", ".join(proposed_times[:3])
        notifications = NotificationService(db)
        await notifications.notify(
            user_id=student_user_id,
            notification_type="interview_scheduled",
            title="Interview Scheduled",
            body=f"An interview has been scheduled. Proposed times: {times_text}.",
            action_url=f"/applications/{application_id}/interviews/{interview_id}",
            metadata={
                "application_id": str(application_id),
                "interview_id": str(interview_id),
                "proposed_times": proposed_times,
            },
        )
    except Exception:
        logger.exception("Hook on_interview_scheduled failed for interview %s", interview_id)


async def on_interview_confirmed(
    db: AsyncSession,
    interviewer_user_id: UUID,
    interview_id: UUID,
    confirmed_time: datetime,
) -> None:
    """Notify an interviewer when the student confirms an interview time."""
    try:
        notifications = NotificationService(db)
        await notifications.notify(
            user_id=interviewer_user_id,
            notification_type="interview_confirmed",
            title="Interview Time Confirmed",
            body=(
                "The interview has been confirmed for"
                f" {confirmed_time.strftime('%B %d, %Y at %I:%M %p')}."
            ),
            action_url=f"/interviews/{interview_id}",
            metadata={
                "interview_id": str(interview_id),
                "confirmed_time": confirmed_time.isoformat(),
            },
        )
    except Exception:
        logger.exception("Hook on_interview_confirmed failed for interview %s", interview_id)


async def on_decision_made(
    db: AsyncSession,
    student_user_id: UUID,
    application_id: UUID,
    decision: str,
) -> None:
    """Notify a student when a decision has been made on their application."""
    try:
        title_map = {
            "accepted": "Congratulations! You've Been Accepted",
            "rejected": "Application Decision Update",
            "waitlisted": "Application Waitlisted",
        }
        body_map = {
            "accepted": "Great news! Your application has been accepted.",
            "rejected": "After careful review, we were unable to offer admission at this time.",
            "waitlisted": "Your application has been placed on the waitlist.",
        }

        notifications = NotificationService(db)
        await notifications.notify(
            user_id=student_user_id,
            notification_type="decision_made",
            title=title_map.get(decision, "Application Decision Update"),
            body=body_map.get(
                decision, f"A decision ({decision}) has been made on your application."
            ),
            action_url=f"/applications/{application_id}",
            metadata={
                "application_id": str(application_id),
                "decision": decision,
            },
        )
        # Record outcome for ML loop
        try:
            collector = OutcomeCollector(db)
            await collector.record_application_decision(application_id)
        except Exception:
            logger.exception(
                "Hook on_decision_made: outcome collection failed for application %s",
                application_id,
            )
    except Exception:
        logger.exception("Hook on_decision_made failed for application %s", application_id)


async def on_offer_responded(
    db: AsyncSession,
    application_id: UUID,
    offer_id: UUID,
) -> None:
    """Record an outcome when a student responds to an offer letter."""
    try:
        collector = OutcomeCollector(db)
        await collector.record_offer_response(offer_id)
    except Exception:
        logger.exception("Hook on_offer_responded failed for offer %s", offer_id)


async def on_enrollment_confirmed(
    db: AsyncSession,
    enrollment_id: UUID,
) -> None:
    """Record an outcome when an enrollment is confirmed."""
    try:
        collector = OutcomeCollector(db)
        await collector.record_enrollment(enrollment_id)
    except Exception:
        logger.exception("Hook on_enrollment_confirmed failed for enrollment %s", enrollment_id)


async def on_offer_sent(
    db: AsyncSession,
    student_user_id: UUID,
    application_id: UUID,
    offer_id: UUID,
) -> None:
    """Notify a student when an offer letter is sent."""
    try:
        notifications = NotificationService(db)
        await notifications.notify(
            user_id=student_user_id,
            notification_type="offer_sent",
            title="Offer Letter Available",
            body=(
                "Your offer letter is ready."
                " Please review and respond at your earliest convenience."
            ),
            action_url=f"/applications/{application_id}/offers/{offer_id}",
            metadata={
                "application_id": str(application_id),
                "offer_id": str(offer_id),
            },
        )
    except Exception:
        logger.exception("Hook on_offer_sent failed for offer %s", offer_id)


async def on_message_received(
    db: AsyncSession,
    recipient_user_id: UUID,
    conversation_id: UUID,
    sender_name: str,
) -> None:
    """Notify a user when they receive a new message."""
    try:
        notifications = NotificationService(db)
        await notifications.notify(
            user_id=recipient_user_id,
            notification_type="message_received",
            title="New Message",
            body=f"You have a new message from {sender_name}.",
            action_url=f"/messages/{conversation_id}",
            metadata={
                "conversation_id": str(conversation_id),
                "sender_name": sender_name,
            },
        )
    except Exception:
        logger.exception("Hook on_message_received failed for conversation %s", conversation_id)


async def on_event_rsvp(
    db: AsyncSession,
    student_id: UUID,
    student_user_id: UUID,
    event_id: UUID,
    institution_id: UUID,
) -> None:
    """Log a CRM touchpoint when a student RSVPs to an event."""
    try:
        crm = CRMService(db)
        await crm.log_touchpoint(
            student_id=student_id,
            touchpoint_type="event_rsvp",
            institution_id=institution_id,
            description="Student RSVP'd to event",
            metadata={
                "event_id": str(event_id),
            },
        )
    except Exception:
        logger.exception("Hook on_event_rsvp failed for event %s, student %s", event_id, student_id)
