"""Connect API — Spec 20 (Student Stage 3a: Connection & Outreach).

The demand-side endpoint of the institution Outreach module. Read/respond,
not authoring:
- Updates feed (posts + deadline + program_change), recent | relevant.
- Events (upcoming | past | mine) with RSVP / waitlist.
- Manage following (mute / unfollow, blocked while an application is active).
- Peers (opt-in, consent + privacy gated; behind ``connect_peers_enabled``).

Routes mount under ``/api/v1/connect``.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.config import settings
from unipaith.database import get_db
from unipaith.dependencies import require_student
from unipaith.models.user import User
from unipaith.services.connect_service import ConnectService
from unipaith.services.follow_service import FollowService
from unipaith.services.peer_service import PeerService
from unipaith.services.student_service import StudentService

router = APIRouter(prefix="/connect", tags=["connect"])


async def _profile_id(user: User, db: AsyncSession) -> UUID:
    profile = await StudentService(db)._get_student_profile(user.id)
    return profile.id


def _require_peers_enabled() -> None:
    """Spec 20 §14 — Peers ships behind ``connect_peers_enabled``. When off the
    surface is invisible (404), the Updates + Events MVP is unaffected."""
    if not settings.connect_peers_enabled:
        raise HTTPException(status_code=404, detail="Peers is not enabled")


# ════════════════════════════════════════════════════════════════════════
# Updates feed (Spec 20 §4)
# ════════════════════════════════════════════════════════════════════════


@router.get("/feed")
async def get_feed(
    tab: str = Query("updates"),
    rank: str = Query("recent", pattern="^(recent|relevant)$"),
    limit: int = Query(50, ge=1, le=100),
    cursor: str | None = Query(None),
    kinds: str | None = Query(None, description="Comma-list of item kinds to include"),
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Updates feed (Spec 20 §4). Posts + system deadline reminders + program
    changes from followed institutions. ``rank=recent`` (reverse-chronological)
    or ``rank=relevant`` (relevance heuristic, optionally AI-refined). Muted
    institutions are suppressed except for ``program_change`` items. ``kinds``
    optionally restricts item kinds (Spec 2026-06-12 §5.1 — rail teasers).
    ``cursor`` pages forward (Spec 56 §4); the response carries ``next_cursor``."""
    pid = await _profile_id(user, db)
    kind_set = {k.strip() for k in kinds.split(",") if k.strip()} if kinds else None
    return await ConnectService(db).build_updates_feed(
        pid, rank=rank, limit=limit, cursor=cursor, kinds=kind_set
    )


# ════════════════════════════════════════════════════════════════════════
# Events tab (Spec 20 §5)
# ════════════════════════════════════════════════════════════════════════


@router.get("/events")
async def get_events(
    scope: str = Query("upcoming", pattern="^(upcoming|past|mine)$"),
    limit: int = Query(50, ge=1, le=100),
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Events from followed institutions (Spec 20 §5). ``scope`` ∈
    {upcoming, past, mine}. Each event carries rsvp_state / counts /
    recommended / a near-start meeting link. RSVP itself stays on
    ``POST /events/{id}/rsvp`` (waitlist + Calendar + Inbox confirmation)."""
    pid = await _profile_id(user, db)
    return await ConnectService(db).build_events(pid, scope=scope, limit=limit)


# ════════════════════════════════════════════════════════════════════════
# Manage following (Spec 20 §2)
# ════════════════════════════════════════════════════════════════════════


class FollowDetail(BaseModel):
    institution_id: UUID
    name: str
    followed_at: object | None = None
    country: str | None = None
    city: str | None = None
    logo_url: str | None = None
    type: str | None = None
    source: str
    muted: bool
    program_count: int = 0
    can_unfollow: bool = True


class MuteRequest(BaseModel):
    muted: bool


@router.get("/follows", response_model=list[FollowDetail])
async def list_following(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Followed institutions for the Manage-Following panel (Spec 20 §3).

    Each row carries ``muted`` / ``source`` / ``can_unfollow`` (always true —
    following is reversible even while an application is active).
    """
    pid = await _profile_id(user, db)
    rows = await FollowService(db).list_detailed(pid)
    return [FollowDetail(**r) for r in rows]


@router.post("/follows/{institution_id}", status_code=status.HTTP_201_CREATED)
async def follow(
    institution_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Explicit follow from a school/program page (Spec 20 §2). Idempotent."""
    pid = await _profile_id(user, db)
    await FollowService(db).ensure_follow(pid, institution_id, source="explicit")
    await db.commit()
    return {"institution_id": str(institution_id), "following": True}


@router.patch("/follows/{institution_id}")
async def mute_following(
    institution_id: UUID,
    body: MuteRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Mute / unmute an institution (Spec 20 §2). Muting suppresses feed items
    but keeps the follow so application context survives. ``program_change``
    items are never suppressed (enforced in the feed builder)."""
    pid = await _profile_id(user, db)
    follow = await FollowService(db).set_muted(pid, institution_id, body.muted)
    await db.commit()
    return {"institution_id": str(institution_id), "muted": follow.muted}


@router.delete("/follows/{institution_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unfollow(
    institution_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Unfollow. Always available; idempotent when not following (Spec 20 §2)."""
    pid = await _profile_id(user, db)
    await FollowService(db).unfollow(pid, institution_id)
    await db.commit()


# ════════════════════════════════════════════════════════════════════════
# Peers tab (Spec 20 §6) — opt-in, privacy-gated, behind connect_peers_enabled
# ════════════════════════════════════════════════════════════════════════


class OptInRequest(BaseModel):
    opted_in: bool = True


class PeerProfileUpdate(BaseModel):
    display_name: str | None = None
    use_alias: bool | None = None
    intended_major: str | None = None
    region: str | None = None
    bio: str | None = None
    share_targets: bool | None = None
    visible: bool | None = None


class ReportRequest(BaseModel):
    reason: str | None = None
    detail: str | None = None


class RespondRequest(BaseModel):
    accept: bool


def _peer_profile_dict(p) -> dict:
    return {
        "id": str(p.id),
        "display_name": p.display_name,
        "use_alias": p.use_alias,
        "intended_major": p.intended_major,
        "region": p.region,
        "bio": p.bio,
        "share_targets": p.share_targets,
        "visible": p.visible,
    }


@router.get("/peers/status")
async def peers_status(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Whether Peers is enabled and whether the student has opted in (Spec 20
    §6.1). Always 200 so the tab can render the opt-in explainer."""
    if not settings.connect_peers_enabled:
        return {"enabled": False, "opted_in": False}
    pid = await _profile_id(user, db)
    return {"enabled": True, "opted_in": await PeerService(db).is_opted_in(pid)}


@router.post("/peers/opt-in")
async def peers_opt_in(
    body: OptInRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Set ``consent.peer_connect`` (Spec 20 §6.1). Revocable."""
    _require_peers_enabled()
    pid = await _profile_id(user, db)
    opted = await PeerService(db).set_opt_in(pid, body.opted_in)
    await db.commit()
    return {"opted_in": opted}


@router.get("/peers/me")
async def get_my_peer_profile(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """The student's self-curated peer-visibility profile (Spec 20 §6.2)."""
    _require_peers_enabled()
    pid = await _profile_id(user, db)
    svc = PeerService(db)
    await svc.require_opted_in(pid)
    profile = await svc.get_my_profile(pid)
    await db.commit()
    return _peer_profile_dict(profile)


@router.put("/peers/me")
async def update_my_peer_profile(
    body: PeerProfileUpdate,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    _require_peers_enabled()
    pid = await _profile_id(user, db)
    svc = PeerService(db)
    await svc.require_opted_in(pid)
    profile = await svc.update_my_profile(pid, **body.model_dump(exclude_unset=True))
    await db.commit()
    return _peer_profile_dict(profile)


@router.get("/peers")
async def discover_peers(
    program_id: UUID | None = Query(None),
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Discover peers by shared programs (Spec 20 §6.3). Returns nothing until
    the student opts in; cards never expose scores/GPA/financials (§6.2)."""
    _require_peers_enabled()
    pid = await _profile_id(user, db)
    return await PeerService(db).discover(pid, program_id=program_id)


@router.post("/peers/{peer_id}/request", status_code=status.HTTP_201_CREATED)
async def request_peer(
    peer_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Send a connect request (Spec 20 §6.3). Rate-limited; minor↔adult blocked."""
    _require_peers_enabled()
    pid = await _profile_id(user, db)
    conn = await PeerService(db).request(pid, peer_id)
    await db.commit()
    return {"peer_id": str(peer_id), "connection_state": conn.status}


@router.post("/peers/{peer_id}/respond")
async def respond_peer(
    peer_id: UUID,
    body: RespondRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Accept/decline an incoming request. On accept a peer Inbox thread opens."""
    _require_peers_enabled()
    pid = await _profile_id(user, db)
    conn = await PeerService(db).respond(pid, peer_id, accept=body.accept)
    await db.commit()
    return {"peer_id": str(peer_id), "connection_state": conn.status}


@router.post("/peers/{peer_id}/block")
async def block_peer(
    peer_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    _require_peers_enabled()
    pid = await _profile_id(user, db)
    await PeerService(db).block(pid, peer_id)
    await db.commit()
    return {"peer_id": str(peer_id), "connection_state": "blocked"}


@router.post("/peers/{peer_id}/report", status_code=status.HTTP_201_CREATED)
async def report_peer(
    peer_id: UUID,
    body: ReportRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Report a peer → moderation queue (Spec 20 §6.3)."""
    _require_peers_enabled()
    pid = await _profile_id(user, db)
    await PeerService(db).report(pid, peer_id, reason=body.reason, detail=body.detail)
    await db.commit()
    return {"peer_id": str(peer_id), "reported": True}
