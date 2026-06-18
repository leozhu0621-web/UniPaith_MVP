"""Spec 20 §6 / §12 — Connect Peers (opt-in, privacy-gated).

Covers: nothing shown until consent.peer_connect=true; peer card / model never
carries score/GPA/financial fields (contract test); minor↔adult blocked;
opt-in + discovery by shared programs; request → accept opens a peer thread.
"""

import uuid
from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.engagement import Conversation
from unipaith.models.institution import Institution, Program
from unipaith.models.peer import PeerProfile
from unipaith.models.student import StudentProfile
from unipaith.models.user import User, UserRole
from unipaith.services.peer_service import PeerService
from unipaith.services.saved_list_service import SavedListService

# Fields a peer surface must NEVER expose (Spec 20 §6.2).
_FORBIDDEN = ("score", "gpa", "financ", "decision", "document", "fitness", "confidence", "tuition")


async def _seed_program(db, student_user, institution_user, *, dob=None):
    db.add(student_user)
    db.add(institution_user)
    profile = StudentProfile(
        user_id=student_user.id, first_name="Ada", last_name="Student", date_of_birth=dob
    )
    db.add(profile)
    institution = Institution(
        admin_user_id=institution_user.id,
        name="Foo University",
        type="university",
        country="United States",
    )
    db.add(institution)
    await db.flush()
    program = Program(
        institution_id=institution.id,
        program_name="CS Masters",
        degree_type="masters",
        is_published=True,
        tuition=50000,
    )
    db.add(program)
    await db.commit()
    await db.refresh(program)
    return profile, institution, program


async def _make_peer(db, program_id, *, name="Grace Peer", dob=None) -> StudentProfile:
    u = User(
        id=uuid.uuid4(),
        email=f"peer-{uuid.uuid4().hex[:6]}@example.com",
        cognito_sub=f"dev-{uuid.uuid4().hex[:8]}",
        role=UserRole("student"),
        is_active=True,
    )
    db.add(u)
    p = StudentProfile(
        user_id=u.id, first_name=name.split()[0], last_name="Peer", date_of_birth=dob
    )
    db.add(p)
    await db.flush()
    await db.refresh(p)
    await SavedListService(db).save_program(p.id, program_id)  # shared program
    await PeerService(db).set_opt_in(p.id, True)
    prof = await PeerService(db).get_my_profile(p.id)
    prof.display_name = name
    await db.commit()
    return p


def test_peer_profile_model_excludes_sensitive_fields():
    """Contract: the peer-visibility model structurally has no score/GPA/
    financial column (Spec 20 §6.2) — mirrors the workshop no-generation test."""
    cols = {c.name.lower() for c in PeerProfile.__table__.columns}
    for col in cols:
        assert not any(bad in col for bad in _FORBIDDEN), f"peer profile leaks '{col}'"


@pytest.mark.asyncio
async def test_peers_hidden_until_opt_in(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    _, _, program = await _seed_program(db_session, mock_student_user, mock_institution_user)
    await student_client.post("/api/v1/students/me/saved", json={"program_id": str(program.id)})

    status = (await student_client.get("/api/v1/connect/peers/status")).json()
    assert status["enabled"] is True
    assert status["opted_in"] is False

    # No peer data until opted in (Spec 20 §6.1).
    denied = await student_client.get("/api/v1/connect/peers")
    assert denied.status_code == 403


@pytest.mark.asyncio
async def test_opt_in_then_discover_shared_program_peer(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    _, _, program = await _seed_program(db_session, mock_student_user, mock_institution_user)
    await student_client.post("/api/v1/students/me/saved", json={"program_id": str(program.id)})
    await _make_peer(db_session, program.id, name="Grace Peer")

    # Opt in, then discover.
    await student_client.post("/api/v1/connect/peers/opt-in", json={"opted_in": True})
    peers = (await student_client.get("/api/v1/connect/peers")).json()
    assert len(peers) == 1
    card = peers[0]
    assert card["display_name"] == "Grace Peer"
    assert card["connection_state"] == "none"
    assert len(card["shared_programs"]) == 1
    # Contract: the card dict exposes no sensitive key (Spec 20 §6.2).
    for key in card:
        assert not any(bad in key.lower() for bad in _FORBIDDEN)


@pytest.mark.asyncio
async def test_cohort_counts_k_anonymity_floor(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    """The per-program count surfaces only at/above the k-floor (3), and is
    suppressed (omitted) below it. Counts only visible+opted-in peers."""
    profile, _, program = await _seed_program(db_session, mock_student_user, mock_institution_user)
    await student_client.post("/api/v1/students/me/saved", json={"program_id": str(program.id)})
    await student_client.post("/api/v1/connect/peers/opt-in", json={"opted_in": True})

    svc = PeerService(db_session)

    # 2 peers share the program → below the k-floor of 3 → suppressed.
    await _make_peer(db_session, program.id, name="Grace Peer")
    await _make_peer(db_session, program.id, name="Alan Peer")
    assert await svc.cohort_counts(profile.id, [program.id]) == {}

    # A 3rd eligible peer crosses the floor → the count surfaces.
    await _make_peer(db_session, program.id, name="Edsger Peer")
    counts = await svc.cohort_counts(profile.id, [program.id])
    assert counts == {program.id: 3}


@pytest.mark.asyncio
async def test_cohort_counts_empty_when_viewer_not_opted_in(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    """An aggregate over peer profiles is peer data — a non-opted-in viewer gets
    nothing, even with plenty of eligible peers."""
    profile, _, program = await _seed_program(db_session, mock_student_user, mock_institution_user)
    await student_client.post("/api/v1/students/me/saved", json={"program_id": str(program.id)})
    for n in ("A Peer", "B Peer", "C Peer", "D Peer"):
        await _make_peer(db_session, program.id, name=n)
    # Viewer never opted in.
    assert await PeerService(db_session).cohort_counts(profile.id, [program.id]) == {}


@pytest.mark.asyncio
async def test_cohort_counts_endpoint_shape(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    _, _, program = await _seed_program(db_session, mock_student_user, mock_institution_user)
    await student_client.post("/api/v1/students/me/saved", json={"program_id": str(program.id)})
    await student_client.post("/api/v1/connect/peers/opt-in", json={"opted_in": True})
    for n in ("A Peer", "B Peer", "C Peer"):
        await _make_peer(db_session, program.id, name=n)

    resp = await student_client.post(
        "/api/v1/connect/peers/cohort-counts", json={"program_ids": [str(program.id)]}
    )
    assert resp.status_code == 200
    assert resp.json() == {"counts": {str(program.id): 3}}


@pytest.mark.asyncio
async def test_request_and_accept_opens_peer_thread(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    profile, _, program = await _seed_program(db_session, mock_student_user, mock_institution_user)
    await student_client.post("/api/v1/students/me/saved", json={"program_id": str(program.id)})
    peer = await _make_peer(db_session, program.id)
    await student_client.post("/api/v1/connect/peers/opt-in", json={"opted_in": True})

    peers = (await student_client.get("/api/v1/connect/peers")).json()
    peer_id = peers[0]["peer_id"]

    req = await student_client.post(f"/api/v1/connect/peers/{peer_id}/request")
    assert req.status_code == 201
    assert req.json()["connection_state"] == "requested"

    # The peer accepts (service-side, acting as the addressee) → a 'peer' Inbox
    # thread opens with the requester as the other party (Spec 20 §6.3).
    requester_peer_id = await _peer_profile_id(db_session, profile.id)
    conn = await PeerService(db_session).respond(peer.id, requester_peer_id, accept=True)
    await db_session.commit()
    assert conn.status == "connected"
    thread = await db_session.scalar(select(Conversation).where(Conversation.thread_type == "peer"))
    assert thread is not None
    assert thread.peer_student_id == profile.id


@pytest.mark.asyncio
async def test_minor_cannot_receive_adult_request(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    # Client student is an adult.
    adult_dob = date(date.today().year - 25, 1, 1)
    _, _, program = await _seed_program(
        db_session, mock_student_user, mock_institution_user, dob=adult_dob
    )
    await student_client.post("/api/v1/students/me/saved", json={"program_id": str(program.id)})
    # Peer is a minor.
    minor_dob = date(date.today().year - 15, 1, 1)
    await _make_peer(db_session, program.id, name="Young Peer", dob=minor_dob)
    await student_client.post("/api/v1/connect/peers/opt-in", json={"opted_in": True})

    # Minor is filtered out of an adult's discovery (Spec 20 §6.4).
    peers = (await student_client.get("/api/v1/connect/peers")).json()
    assert peers == []


async def _peer_profile_id(db: AsyncSession, student_id) -> uuid.UUID:
    return await db.scalar(select(PeerProfile.id).where(PeerProfile.student_id == student_id))
