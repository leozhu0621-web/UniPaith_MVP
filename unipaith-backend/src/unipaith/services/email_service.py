"""Transactional email sending via Amazon SES.

Small shared utility for direct, user-triggered emails (e.g. the recommender
request email). Follows the existing SES pattern in ``notification_service``
and ``campaign_email_service`` (sync boto3 ``send_email``), but runs the
blocking call off the event loop and RAISES on failure so callers can refuse
to record a send that never happened.

Callers gate on ``settings.email_send_enabled`` before calling.
"""

from __future__ import annotations

import asyncio
import logging

from unipaith.config import settings

logger = logging.getLogger(__name__)


class EmailSendError(Exception):
    """An email send was attempted but failed."""


def _from_address() -> str:
    return settings.email_from_address or (
        f"{settings.ses_sender_name} <{settings.ses_sender_email}>"
    )


def _send_email_sync(*, to_address: str, subject: str, body_text: str) -> None:
    import boto3

    ses = boto3.client("ses", region_name=settings.ses_region)
    ses.send_email(
        Source=_from_address(),
        Destination={"ToAddresses": [to_address]},
        Message={
            "Subject": {"Data": subject, "Charset": "UTF-8"},
            "Body": {
                "Text": {"Data": body_text, "Charset": "UTF-8"},
            },
        },
    )


async def send_email(*, to_address: str, subject: str, body_text: str) -> None:
    """Send a plain-text email via SES, off the event loop.

    Raises :class:`EmailSendError` on any failure — callers must not flip
    "sent" state when this raises.
    """
    try:
        await asyncio.to_thread(
            _send_email_sync,
            to_address=to_address,
            subject=subject,
            body_text=body_text,
        )
    except Exception as exc:
        logger.error("SES send failed for %s: %s", to_address, exc)
        raise EmailSendError(str(exc)) from exc
