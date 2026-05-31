"""Peer service — Spec 20 §6 (opt-in, privacy-gated Peers).

Connect students with shared application context. Off by default — every read
requires ``consent.peer_connect`` (Spec 20 §6.1). Discovery is by shared
programs; admit-mentor matching is deferred (Spec 20 §14). Safety: minor↔adult
matching is blocked (§6.4), connect requests are rate-limited, and block/report
route to a moderation record.

Privacy: a peer is referenced by the opaque ``PeerProfile.id`` (never the
student_id), and a peer card NEVER carries scores / GPA / documents / decisions
/ financials (§6.2).
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.core.exceptions import (
    BadRequestException,
    ForbiddenException,
    NotFoundException,
)
from unipaith.models.application import Application
from unipaith.models.engagement import Conversation, SavedList, SavedListItem
from unipaith.models.peer import PeerConnection, PeerProfile, PeerReport
from unipaith.models.student import StudentDataConsent, StudentProfile

logger = logging.getLogger(__name__)

PEER_REQUEST_DAILY_LIMIT = 20  # anti-spam (Spec 20 §6.4)


class PeerService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # Consent (Spec 20 §6.1)
    # ------------------------------------------------------------------

    async def is_opted_in(self, student_id: UUID) -> bool:
        row = await self.db.scalar(
            select(StudentDataConsent.consent_peer_connect).where(
                StudentDataConsent.student_id == student_id
            )
        )
        return bool(row)

    async def set_opt_in(self, student_id: UUID, opted_in: bool) -> bool:
        consent = await self.db.scalar(
            select(StudentDataConsent).where(StudentDataConsent.student_id == student_id)
        )
        if consent is None:
            consent = StudentDataConsent(student_id=student_id, consent_peer_connect=opted_in)
            self.db.add(consent)
        else:
            consent.consent_peer_connect = opted_in
        # Opting in seeds a default visibility profile (revocable, editable).
        if opted_in:
            await self._get_or_create_profile(student_id)
        await self.db.flush()
        return opted_in

    async def require_opted_in(self, student_id: UUID) -> None:
        if not await self.is_opted_in(student_id):
            raise ForbiddenException(
                "Opt in to Peers first — others can find you by shared programs and "
                "see only what you choose to share."
            )

    # ------------------------------------------------------------------
    # Visibility profile (Spec 20 §6.2)
    # ------------------------------------------------------------------

    async def _get_or_create_profile(self, student_id: UUID) -> PeerProfile:
        profile = await self.db.scalar(
            select(PeerProfile).where(PeerProfile.student_id == student_id)
        )
        if profile is None:
            sp = await self.db.get(StudentProfile, student_id)
            display = None
            if sp and (sp.first_name or sp.last_name):
                display = " ".join(p for p in [sp.first_name, sp.last_name] if p)
            profile = PeerProfile(student_id=student_id, display_name=display)
            self.db.add(profile)
            await self.db.flush()
        return profile

    async def get_my_profile(self, student_id: UUID) -> PeerProfile:
        return await self._get_or_create_profile(student_id)

    async def update_my_profile(self, student_id: UUID, **fields) -> PeerProfile:
        profile = await self._get_or_create_profile(student_id)
        allowed = {
            "display_name",
            "use_alias",
            "intended_major",
            "region",
            "bio",
            "share_targets",
            "visible",
        }
        for key, value in fields.items():
            if key in allowed and value is not None:
                setattr(profile, key, value)
        await self.db.flush()
        return profile

    # ------------------------------------------------------------------
    # Discovery (Spec 20 §6.3) — by shared programs
    # ------------------------------------------------------------------

    async def discover(self, student_id: UUID, *, program_id: UUID | None = None) -> list[dict]:
        await self.require_opted_in(student_id)

        my_progs = await self._engaged_program_ids(student_id)
        if program_id is not None:
            my_progs = {program_id} & my_progs
        if not my_progs:
            return []

        my_bucket = await self._age_bucket(student_id)
        blocked = await self._blocked_student_ids(student_id)

        # Candidate students who engage with the same programs (excluding me/blocked).
        cand_rows = await self.db.execute(
            select(SavedListItem.program_id, SavedList.student_id)
            .join(SavedList, SavedList.id == SavedListItem.list_id)
            .where(SavedListItem.program_id.in_(my_progs), SavedList.student_id != student_id)
        )
        applied_rows = await self.db.execute(
            select(Application.program_id, Application.student_id).where(
                Application.program_id.in_(my_progs), Application.student_id != student_id
            )
        )
        shared: dict[UUID, set[UUID]] = {}
        for prog_id, other_id in list(cand_rows.all()) + list(applied_rows.all()):
            if other_id in blocked:
                continue
            shared.setdefault(other_id, set()).add(prog_id)
        if not shared:
            return []

        # Load visible, opted-in peer profiles for the candidates.
        prof_rows = await self.db.execute(
            select(PeerProfile)
            .join(StudentDataConsent, StudentDataConsent.student_id == PeerProfile.student_id)
            .where(
                PeerProfile.student_id.in_(shared.keys()),
                PeerProfile.visible.is_(True),
                StudentDataConsent.consent_peer_connect.is_(True),
            )
        )
        profiles = list(prof_rows.scalars().all())
        if not profiles:
            return []

        prog_names = await self._program_names({p for s in shared.values() for p in s})
        conn_states = await self._connection_states(student_id, [p.student_id for p in profiles])

        cards: list[dict] = []
        for prof in profiles:
            # Minor↔adult matching is blocked (§6.4).
            if await self._age_bucket(prof.student_id) != my_bucket:
                continue
            shared_progs = shared.get(prof.student_id, set())
            cards.append(self._to_card(prof, shared_progs, prog_names, conn_states))
        return cards

    def _to_card(
        self,
        prof: PeerProfile,
        shared_progs: set[UUID],
        prog_names: dict[UUID, str],
        conn_states: dict[UUID, str],
    ) -> dict:
        """Build a privacy-safe peer card. NEVER includes scores / GPA /
        financials (Spec 20 §6.2) — only the self-curated fields."""
        name = prof.display_name or "Applicant"
        return {
            "peer_id": str(prof.id),  # opaque — not the student_id (§7)
            "display_name": name,
            "shared_programs": (
                [{"id": str(pid), "name": prog_names.get(pid, "Program")} for pid in shared_progs]
                if prof.share_targets
                else []
            ),
            "intended_major": prof.intended_major,
            "region": prof.region,
            "bio": prof.bio,
            "connection_state": conn_states.get(prof.student_id, "none"),
        }

    # ------------------------------------------------------------------
    # Connection actions (Spec 20 §6.3 / §6.4)
    # ------------------------------------------------------------------

    async def request(self, student_id: UUID, peer_id: UUID) -> PeerConnection:
        await self.require_opted_in(student_id)
        target = await self._resolve_peer(peer_id)
        if target == student_id:
            raise BadRequestException("You can't connect with yourself")

        if await self._is_blocked_between(student_id, target):
            raise ForbiddenException("Cannot connect with this peer")
        if await self._age_bucket(student_id) != await self._age_bucket(target):
            raise ForbiddenException("For safety, applicants under 18 and adults can't connect.")

        existing = await self._connection(student_id, target)
        if existing and existing.status in ("requested", "connected"):
            return existing

        await self._enforce_rate_limit(student_id)

        if existing is not None:
            existing.status = "requested"
            await self.db.flush()
            return existing
        conn = PeerConnection(requester_id=student_id, addressee_id=target, status="requested")
        self.db.add(conn)
        await self.db.flush()
        return conn

    async def respond(self, student_id: UUID, peer_id: UUID, *, accept: bool) -> PeerConnection:
        """Accept/decline a request the peer sent to me. On accept a peer Inbox
        thread opens (Spec 20 §6.3)."""
        await self.require_opted_in(student_id)
        requester = await self._resolve_peer(peer_id)
        conn = await self.db.scalar(
            select(PeerConnection).where(
                PeerConnection.requester_id == requester,
                PeerConnection.addressee_id == student_id,
                PeerConnection.status == "requested",
            )
        )
        if conn is None:
            raise NotFoundException("No pending request from this peer")
        if not accept:
            conn.status = "declined"
            await self.db.flush()
            return conn

        conn.status = "connected"
        # Open a peer Inbox thread (Spec 20 §6.3 — NEW 'peer' thread type).
        now = datetime.now(UTC)
        conv = Conversation(
            student_id=student_id,
            institution_id=None,
            subject="Peer connection",
            status="active",
            thread_type="peer",
            peer_student_id=requester,
            started_at=now,
            last_message_at=now,
        )
        self.db.add(conv)
        await self.db.flush()
        conn.conversation_id = conv.id
        await self.db.flush()
        return conn

    async def block(self, student_id: UUID, peer_id: UUID) -> None:
        await self.require_opted_in(student_id)
        target = await self._resolve_peer(peer_id)
        conn = await self._connection(student_id, target)
        if conn is None:
            conn = PeerConnection(requester_id=student_id, addressee_id=target, status="blocked")
            self.db.add(conn)
        else:
            conn.status = "blocked"
        await self.db.flush()

    async def report(
        self, student_id: UUID, peer_id: UUID, *, reason: str | None, detail: str | None
    ) -> PeerReport:
        await self.require_opted_in(student_id)
        target = await self._resolve_peer(peer_id)
        report = PeerReport(
            reporter_id=student_id, reported_id=target, reason=reason, detail=detail, status="open"
        )
        self.db.add(report)
        await self.db.flush()
        return report

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _resolve_peer(self, peer_id: UUID) -> UUID:
        sid = await self.db.scalar(select(PeerProfile.student_id).where(PeerProfile.id == peer_id))
        if sid is None:
            raise NotFoundException("Peer not found")
        return sid

    async def _connection(self, a: UUID, b: UUID) -> PeerConnection | None:
        return await self.db.scalar(
            select(PeerConnection).where(
                PeerConnection.requester_id == a, PeerConnection.addressee_id == b
            )
        )

    async def _is_blocked_between(self, a: UUID, b: UUID) -> bool:
        row = await self.db.scalar(
            select(PeerConnection.id).where(
                PeerConnection.status == "blocked",
                or_(
                    and_(PeerConnection.requester_id == a, PeerConnection.addressee_id == b),
                    and_(PeerConnection.requester_id == b, PeerConnection.addressee_id == a),
                ),
            )
        )
        return row is not None

    async def _blocked_student_ids(self, student_id: UUID) -> set[UUID]:
        rows = await self.db.execute(
            select(PeerConnection.requester_id, PeerConnection.addressee_id).where(
                PeerConnection.status == "blocked",
                or_(
                    PeerConnection.requester_id == student_id,
                    PeerConnection.addressee_id == student_id,
                ),
            )
        )
        out: set[UUID] = set()
        for req, addr in rows.all():
            out.add(addr if req == student_id else req)
        return out

    async def _connection_states(self, student_id: UUID, others: list[UUID]) -> dict[UUID, str]:
        """Map each other student → connection_state from my perspective."""
        if not others:
            return {}
        rows = await self.db.execute(
            select(PeerConnection).where(
                or_(
                    and_(
                        PeerConnection.requester_id == student_id,
                        PeerConnection.addressee_id.in_(others),
                    ),
                    and_(
                        PeerConnection.addressee_id == student_id,
                        PeerConnection.requester_id.in_(others),
                    ),
                )
            )
        )
        states: dict[UUID, str] = {}
        for c in rows.scalars().all():
            other = c.addressee_id if c.requester_id == student_id else c.requester_id
            if c.status == "connected":
                states[other] = "connected"
            elif c.status == "blocked":
                states[other] = "blocked"
            elif c.status == "requested":
                # Distinguish a request I sent vs one I received.
                states[other] = "requested" if c.requester_id == student_id else "incoming"
            else:
                states.setdefault(other, "none")
        return states

    async def _enforce_rate_limit(self, student_id: UUID) -> None:
        since = datetime.now(UTC) - timedelta(hours=24)
        count = await self.db.scalar(
            select(func.count())
            .select_from(PeerConnection)
            .where(
                PeerConnection.requester_id == student_id,
                PeerConnection.created_at >= since,
            )
        )
        if (count or 0) >= PEER_REQUEST_DAILY_LIMIT:
            raise BadRequestException(
                "You've reached the daily limit for connection requests. Try again tomorrow."
            )

    async def _age_bucket(self, student_id: UUID) -> str:
        """'minor' if under 18, else 'adult'. Unknown DOB → 'adult' (a real
        minor has a DOB; unknowns can only match other adults/unknowns)."""
        dob: date | None = await self.db.scalar(
            select(StudentProfile.date_of_birth).where(StudentProfile.id == student_id)
        )
        if dob is None:
            return "adult"
        today = date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return "minor" if age < 18 else "adult"

    async def _engaged_program_ids(self, student_id: UUID) -> set[UUID]:
        saved = await self.db.execute(
            select(SavedListItem.program_id)
            .join(SavedList, SavedList.id == SavedListItem.list_id)
            .where(SavedList.student_id == student_id)
        )
        applied = await self.db.execute(
            select(Application.program_id).where(Application.student_id == student_id)
        )
        return {r[0] for r in saved.all()} | {r[0] for r in applied.all()}

    async def _program_names(self, ids: set[UUID]) -> dict[UUID, str]:
        from unipaith.models.institution import Program

        ids = {i for i in ids if i}
        if not ids:
            return {}
        rows = await self.db.execute(
            select(Program.id, Program.program_name).where(Program.id.in_(ids))
        )
        return {r[0]: r[1] for r in rows.all()}
