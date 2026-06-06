from __future__ import annotations

import csv
import io
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.dependencies import get_current_user, require_owner, require_system
from unipaith.models.feedback import Feedback
from unipaith.models.user import User
from unipaith.services.feedback_service import FeedbackService

router = APIRouter(prefix="/feedback", tags=["feedback"])


def _feedback_payload(rows: list[Feedback]) -> list[dict]:
    return [
        {
            "id": str(r.id),
            "user_id": str(r.user_id) if r.user_id else None,
            "role": r.role,
            "title": r.title,
            "message": r.message,
            "context": r.context,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


def _feedback_csv(rows: list[Feedback]) -> StreamingResponse:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["created_at", "role", "title", "message"])
    for r in rows:
        writer.writerow([r.created_at.isoformat(), r.role or "", r.title or "", r.message])
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=feedback.csv"},
    )


class FeedbackCreate(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    message: str = Field(min_length=1, max_length=8000)
    context: dict | None = None


class FeedbackOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role: str | None
    title: str | None
    message: str
    created_at: datetime


@router.post("", response_model=FeedbackOut, status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    body: FeedbackCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    user_agent: str | None = Header(default=None, alias="User-Agent"),
):
    """Submit demo feedback (title + message). Auth required so the author's
    id/role are stamped server-side rather than trusted from the client."""
    return await FeedbackService(db).create(
        user_id=user.id,
        role=user.role.value,
        title=body.title,
        message=body.message,
        context=body.context,
        user_agent=user_agent,
    )


@router.get("/inbox")
async def feedback_inbox(
    _: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
    fmt: str | None = Query(default=None, alias="format"),
):
    """Owner-only in-app feedback inbox (newest first). Same data as ``/admin``,
    but gated by the owner email allowlist so it works with the normal login —
    no ops token needed. ``?format=csv`` downloads a spreadsheet."""
    rows = await FeedbackService(db).list_all()
    return _feedback_csv(rows) if fmt == "csv" else _feedback_payload(rows)


@router.get("/admin")
async def list_feedback(
    _: bool = Depends(require_system),
    db: AsyncSession = Depends(get_db),
    fmt: str | None = Query(default=None, alias="format"),
):
    """Collect all feedback. System-guarded (X-Ops-Token, like the crawler ops
    API) for programmatic/ops access. ``?format=csv`` downloads a CSV. The
    in-app owner inbox uses ``/inbox`` instead (user-auth, no token)."""
    rows = await FeedbackService(db).list_all()
    return _feedback_csv(rows) if fmt == "csv" else _feedback_payload(rows)
