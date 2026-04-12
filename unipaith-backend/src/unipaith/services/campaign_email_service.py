"""Campaign email delivery via Amazon SES with personalization and unsubscribe."""
from __future__ import annotations

import hashlib
import hmac
import logging
from uuid import UUID

import boto3
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.config import settings
from unipaith.models.institution import Campaign, CampaignRecipient
from unipaith.models.student import StudentProfile
from unipaith.models.user import User

logger = logging.getLogger("unipaith.campaign_email")

# Shared secret for unsubscribe token generation
_UNSUB_SECRET = "unipaith-campaign-unsub-v1"


def _generate_unsubscribe_token(recipient_id: UUID) -> str:
    """Generate an HMAC-based unsubscribe token for a recipient."""
    return hmac.new(
        _UNSUB_SECRET.encode(),
        str(recipient_id).encode(),
        hashlib.sha256,
    ).hexdigest()[:32]


def verify_unsubscribe_token(recipient_id: UUID, token: str) -> bool:
    """Verify an unsubscribe token is valid."""
    expected = _generate_unsubscribe_token(recipient_id)
    return hmac.compare_digest(expected, token)


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
        Send personalized emails to all campaign recipients.
        Returns the number of emails successfully sent.
        """
        if not settings.notifications_enabled:
            logger.info("Email sending disabled (notifications_enabled=False). Skipping.")
            return 0

        result = await self.db.execute(
            select(CampaignRecipient).where(
                CampaignRecipient.campaign_id == campaign.id,
            )
        )
        recipients = list(result.scalars().all())
        if not recipients:
            return 0

        sent_count = 0
        for recipient in recipients:
            try:
                success = await self._send_to_recipient(
                    campaign, recipient, institution_name, program_name,
                )
                if success:
                    sent_count += 1
            except Exception:
                logger.exception(
                    "Failed to send campaign email to recipient %s", recipient.id,
                )

        return sent_count

    async def _send_to_recipient(
        self,
        campaign: Campaign,
        recipient: CampaignRecipient,
        institution_name: str,
        program_name: str | None,
    ) -> bool:
        """Send a personalized email to one recipient."""
        # Load student profile and user email
        profile_result = await self.db.execute(
            select(StudentProfile).where(StudentProfile.id == recipient.student_id)
        )
        profile = profile_result.scalar_one_or_none()
        if not profile:
            return False

        user_result = await self.db.execute(
            select(User).where(User.id == profile.user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user or not user.email:
            return False

        # Build personalization variables
        base_url = settings.frontend_url
        unsub_token = _generate_unsubscribe_token(recipient.id)
        variables = {
            "first_name": profile.first_name or "Student",
            "last_name": profile.last_name or "",
            "email": user.email,
            "institution_name": institution_name,
            "program_name": program_name or "",
            "campaign_name": campaign.campaign_name,
            "unsubscribe_url": (
                f"{base_url}/api/v1/campaigns/unsubscribe"
                f"/{recipient.id}?token={unsub_token}"
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

        # Build HTML email
        body_html = body_text.replace(chr(10), "<br>")
        unsub_url = variables["unsubscribe_url"]
        html_body = (
            '<div style="font-family:sans-serif;'
            'max-width:600px;margin:0 auto;padding:20px">'
            '<div style="text-align:center;margin-bottom:24px">'
            f'<h2 style="color:#1a1a1a;margin:0">'
            f"{institution_name}</h2></div>"
            '<div style="color:#374151;font-size:14px;'
            f'line-height:1.6">{body_html}</div>'
            '<div style="margin-top:24px;text-align:center">'
            f'<a href="{base_url}" style="display:inline-block;'
            "padding:10px 24px;background:#1a1a1a;color:#fff;"
            'text-decoration:none;border-radius:6px;'
            'font-size:14px">Visit UniPaith</a></div>'
            '<div style="margin-top:32px;padding-top:16px;'
            "border-top:1px solid #e5e7eb;text-align:center;"
            'font-size:11px;color:#9ca3af">'
            f"<p>Sent by {institution_name} via UniPaith</p>"
            f'<a href="{unsub_url}" style="color:#9ca3af">'
            "Unsubscribe</a></div></div>"
        )

        try:
            ses = boto3.client("ses", region_name=settings.ses_region)
            ses.send_email(
                Source=f"{institution_name} via UniPaith <{settings.ses_sender_email}>",
                Destination={"ToAddresses": [user.email]},
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
            logger.error("SES send failed for %s: %s", user.email, e)
            return False
