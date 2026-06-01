"""Campaign email delivery via Amazon SES with personalization and unsubscribe."""

from __future__ import annotations

import hashlib
import hmac
import logging
from datetime import UTC, datetime
from uuid import UUID

import boto3
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.config import settings
from unipaith.models.institution import Campaign, CampaignRecipient
from unipaith.models.student import StudentProfile
from unipaith.models.user import User

logger = logging.getLogger("unipaith.campaign_email")


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _generate_unsubscribe_token(recipient_id: UUID) -> str:
    """Generate an HMAC-based unsubscribe token for a recipient."""
    return hmac.new(
        settings.campaign_unsubscribe_secret.encode(),
        str(recipient_id).encode(),
        hashlib.sha256,
    ).hexdigest()[:32]


def verify_unsubscribe_token(recipient_id: UUID, token: str) -> bool:
    """Verify an unsubscribe token is valid."""
    expected = _generate_unsubscribe_token(recipient_id)
    return hmac.compare_digest(expected, token)


_CTA_LABELS = {
    "learn_more": "Learn more",
    "rsvp_event": "RSVP now",
    "request_info": "Request info",
    "start_application": "Start application",
}


def _personalize(template: str, variables: dict[str, str]) -> str:
    """Replace {{variable_name}} placeholders with values."""
    result = template
    for key, value in variables.items():
        result = result.replace(f"{{{{{key}}}}}", value or "")
    return result


class CampaignEmailService:
    """Handles email delivery for outreach campaigns."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def send_campaign_emails(
        self,
        campaign: Campaign,
        institution_name: str,
        program_name: str | None = None,
    ) -> int:
        """
        Send personalized emails to the campaign's external recipients.
        Returns the number of emails successfully sent. Internal-only recipients
        (channel='internal') are skipped — they receive the message in their
        Inbox instead.
        """
        result = await self.db.execute(
            select(CampaignRecipient).where(
                CampaignRecipient.campaign_id == campaign.id,
                CampaignRecipient.channel.in_(("external", "both")),
            )
        )
        recipients = [r for r in result.scalars().all() if r.email]
        if not recipients:
            return 0

        if not settings.notifications_enabled:
            logger.info("Email sending disabled (notifications_enabled=False). Skipping SES.")
            return 0

        sent_count = 0
        for recipient in recipients:
            try:
                success = await self._send_to_recipient(
                    campaign,
                    recipient,
                    institution_name,
                    program_name,
                )
                if success:
                    sent_count += 1
                else:
                    recipient.failed_at = recipient.failed_at or _utcnow()
                    recipient.failure_reason = recipient.failure_reason or "send_failed"
            except Exception:
                logger.exception(
                    "Failed to send campaign email to recipient %s",
                    recipient.id,
                )
                recipient.failed_at = _utcnow()
                recipient.failure_reason = "exception"

        return sent_count

    async def _send_to_recipient(
        self,
        campaign: Campaign,
        recipient: CampaignRecipient,
        institution_name: str,
        program_name: str | None,
    ) -> bool:
        """Send a personalized email to one recipient (platform student or
        uploaded-list contact). Prefers the recipient's own stored email/name;
        falls back to the linked student profile for legacy rows."""
        email = recipient.email
        first_name = recipient.first_name
        last_name = recipient.last_name
        if not email and recipient.student_id:
            profile = (
                await self.db.execute(
                    select(StudentProfile).where(StudentProfile.id == recipient.student_id)
                )
            ).scalar_one_or_none()
            if profile:
                first_name = first_name or profile.first_name
                last_name = last_name or profile.last_name
                user = (
                    await self.db.execute(select(User).where(User.id == profile.user_id))
                ).scalar_one_or_none()
                if user:
                    email = user.email
        if not email:
            return False

        # Build personalization variables
        base_url = "https://app.unipaith.co"
        api_base_url = "https://api.unipaith.co"
        unsub_token = _generate_unsubscribe_token(recipient.id)
        event_link = campaign.destination_url or base_url
        variables = {
            "first_name": first_name or "there",
            "last_name": last_name or "",
            "email": email,
            "institution_name": institution_name,
            "program_name": program_name or "",
            "campaign_name": campaign.campaign_name,
            "event_link": event_link,
            "unsubscribe_url": (
                f"{api_base_url}/api/v1/campaigns/unsubscribe/{recipient.id}?token={unsub_token}"
            ),
            "platform_url": base_url,
        }

        # Personalize subject and body
        subject = _personalize(
            campaign.message_subject or campaign.campaign_name,
            variables,
        )
        body_text = _personalize(
            campaign.message_body or "",
            variables,
        )

        # Build HTML email — UniPaith brand: navy heading, cobalt CTA, cream tile.
        body_html = body_text.replace(chr(10), "<br>")
        unsub_url = variables["unsubscribe_url"]
        cta_label = _CTA_LABELS.get(campaign.cta_type or "", "Learn more")
        html_body = (
            '<div style="font-family:Helvetica,Arial,sans-serif;background:#FCFAF2;'
            'padding:32px 0">'
            '<div style="max-width:600px;margin:0 auto;background:#FFFFFF;'
            'border:1px solid #C9C2A8;border-radius:12px;overflow:hidden">'
            '<div style="background:#0A1428;padding:20px 24px">'
            f'<span style="color:#FFD60A;font-size:20px;font-weight:700;'
            f'letter-spacing:-0.5px">{institution_name}</span></div>'
            '<div style="padding:24px;color:#2B2722;font-size:15px;'
            f'line-height:1.6">{body_html}</div>'
            '<div style="padding:0 24px 24px;text-align:center">'
            f'<a href="{event_link}" style="display:inline-block;'
            "padding:12px 28px;background:#2A6BD4;color:#FFFFFF;"
            "text-decoration:none;border-radius:8px;font-size:14px;"
            f'font-weight:700">{cta_label}</a></div>'
            '<div style="padding:16px 24px;border-top:1px solid #E7E1CF;'
            'text-align:center;font-size:11px;color:#8A857A;background:#FCFAF2">'
            f'<p style="margin:0 0 4px">Sent by {institution_name} via UniPaith</p>'
            f'<a href="{unsub_url}" style="color:#8A857A">'
            "Unsubscribe</a></div></div></div>"
        )

        try:
            ses = boto3.client("ses", region_name=settings.ses_region)
            ses.send_email(
                Source=f"{institution_name} via UniPaith <{settings.ses_sender_email}>",
                Destination={"ToAddresses": [email]},
                Message={
                    "Subject": {"Data": subject, "Charset": "UTF-8"},
                    "Body": {
                        "Text": {"Data": body_text, "Charset": "UTF-8"},
                        "Html": {"Data": html_body, "Charset": "UTF-8"},
                    },
                },
            )
            return True
        except Exception as e:
            logger.error("SES send failed for %s: %s", email, e)
            return False
