"""Phase D — per-student LLM weekly cost cap (Plan 2 §10).

Verifies enforcement of `settings.ai_per_student_weekly_cost_cap_usd`
across the three modes (off / warn / block) and the helper
`student_cost_in_window`. Uses the real DB session so the ai_turns
window query is exercised end-to-end.
"""

from __future__ import annotations

import datetime as _dt
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ai.client import (
    AIClient,
    CostCapExceededError,
    check_cost_cap,
    student_cost_in_window,
)
from unipaith.config import settings
from unipaith.models.ai_artifacts import AiTurn
from unipaith.models.student import StudentProfile
from unipaith.models.user import User, UserRole

# ── Fixtures ───────────────────────────────────────────────────────────────


async def _seed_student(db: AsyncSession) -> StudentProfile:
    user = User(
        id=uuid4(),
        email=f"cap-{uuid4().hex[:6]}@example.com",
        cognito_sub=f"dev-sub-{uuid4().hex[:8]}",
        role=UserRole.student,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    profile = StudentProfile(user_id=user.id)
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return profile


async def _seed_turn(
    db: AsyncSession,
    student_id,
    *,
    cost: str = "0.10",
    age_hours: float = 0.0,
) -> AiTurn:
    """Insert an ai_turns row with a back-dated created_at."""
    turn = AiTurn(
        student_id=student_id,
        agent="orchestrator",
        role="assistant",
        model="claude-sonnet-4-6",
        input_tokens=100,
        output_tokens=50,
        cost_usd=Decimal(cost),
    )
    db.add(turn)
    await db.flush()
    if age_hours > 0:
        turn.created_at = _dt.datetime.now(_dt.UTC) - _dt.timedelta(hours=age_hours)
        await db.flush()
    await db.commit()
    return turn


def _mock_client() -> AIClient:
    return AIClient(
        anthropic_api_key="",
        voyage_api_key="",
        sonnet_model="claude-sonnet-4-6",
        haiku_model="claude-haiku-4-5",
        embedding_model="voyage-3-large",
        mock_mode=True,
    )


# ── student_cost_in_window ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_student_cost_in_window_zero_when_no_turns(
    db_session: AsyncSession,
):
    student = await _seed_student(db_session)
    total = await student_cost_in_window(db_session, student.id, window_days=7)
    assert total == 0.0


@pytest.mark.asyncio
async def test_student_cost_in_window_sums_recent_turns(
    db_session: AsyncSession,
):
    student = await _seed_student(db_session)
    await _seed_turn(db_session, student.id, cost="0.10", age_hours=1)
    await _seed_turn(db_session, student.id, cost="0.15", age_hours=2)
    await _seed_turn(db_session, student.id, cost="0.05", age_hours=24)
    total = await student_cost_in_window(db_session, student.id, window_days=7)
    assert total == pytest.approx(0.30, abs=1e-6)


@pytest.mark.asyncio
async def test_student_cost_in_window_excludes_old_turns(
    db_session: AsyncSession,
):
    """A turn from 30 days ago should not count in a 7-day window."""
    student = await _seed_student(db_session)
    await _seed_turn(db_session, student.id, cost="0.40", age_hours=24 * 30)
    await _seed_turn(db_session, student.id, cost="0.05", age_hours=1)
    total = await student_cost_in_window(db_session, student.id, window_days=7)
    assert total == pytest.approx(0.05, abs=1e-6)


@pytest.mark.asyncio
async def test_student_cost_in_window_per_student(
    db_session: AsyncSession,
):
    """One student's spend doesn't show up in another's window."""
    a = await _seed_student(db_session)
    b = await _seed_student(db_session)
    await _seed_turn(db_session, a.id, cost="0.30", age_hours=1)
    await _seed_turn(db_session, b.id, cost="0.05", age_hours=1)
    assert await student_cost_in_window(db_session, a.id, window_days=7) == pytest.approx(0.30)
    assert await student_cost_in_window(db_session, b.id, window_days=7) == pytest.approx(0.05)


# ── check_cost_cap (top-level helper) ──────────────────────────────────────


@pytest.mark.asyncio
async def test_check_cost_cap_under_cap_returns_false(
    db_session: AsyncSession,
):
    student = await _seed_student(db_session)
    await _seed_turn(db_session, student.id, cost="0.10", age_hours=1)
    over, spent = await check_cost_cap(
        db_session, student.id, cap_usd=0.5, window_days=7, enforcement="warn"
    )
    assert over is False
    assert spent == pytest.approx(0.10)


@pytest.mark.asyncio
async def test_check_cost_cap_at_cap_returns_true(
    db_session: AsyncSession,
):
    """Exactly at the cap counts as exceeded (>= comparison) — Plan 2 §10
    is about preventing further spend, not about strict overshoot."""
    student = await _seed_student(db_session)
    await _seed_turn(db_session, student.id, cost="0.50", age_hours=1)
    over, spent = await check_cost_cap(
        db_session, student.id, cap_usd=0.5, window_days=7, enforcement="warn"
    )
    assert over is True
    assert spent == pytest.approx(0.5)


@pytest.mark.asyncio
async def test_check_cost_cap_no_db_returns_false(
    db_session: AsyncSession,
):
    """Anonymous calls (eval harness) skip the check."""
    over, spent = await check_cost_cap(
        None, uuid4(), cap_usd=0.01, window_days=7, enforcement="block"
    )
    assert over is False
    assert spent == 0.0


@pytest.mark.asyncio
async def test_check_cost_cap_no_student_returns_false(
    db_session: AsyncSession,
):
    over, spent = await check_cost_cap(
        db_session, None, cap_usd=0.01, window_days=7, enforcement="block"
    )
    assert over is False
    assert spent == 0.0


@pytest.mark.asyncio
async def test_check_cost_cap_off_mode_returns_false(
    db_session: AsyncSession,
):
    """`"off"` short-circuits to (False, 0.0) without hitting the DB."""
    student = await _seed_student(db_session)
    await _seed_turn(db_session, student.id, cost="999.99", age_hours=1)
    over, spent = await check_cost_cap(
        db_session, student.id, cap_usd=0.5, window_days=7, enforcement="off"
    )
    assert over is False
    assert spent == 0.0


# ── AIClient.message gating ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_message_warn_mode_attaches_warning(
    db_session: AsyncSession,
    monkeypatch,
):
    """Over-cap in warn mode → call succeeds, response carries the
    cost_cap_warning dict for the surface to render a soft banner."""
    monkeypatch.setattr(settings, "ai_cost_cap_enforcement", "warn")
    monkeypatch.setattr(settings, "ai_per_student_weekly_cost_cap_usd", 0.10)
    monkeypatch.setattr(settings, "ai_cost_cap_window_days", 7)
    student = await _seed_student(db_session)
    await _seed_turn(db_session, student.id, cost="0.20", age_hours=1)

    resp = await _mock_client().message(
        agent="orchestrator",
        model="sonnet",
        system="x",
        messages=[{"role": "user", "content": "hi"}],
        student_id=student.id,
        db=db_session,
    )
    assert resp.cost_cap_warning is not None
    assert resp.cost_cap_warning["spent_usd"] == pytest.approx(0.20)
    assert resp.cost_cap_warning["cap_usd"] == pytest.approx(0.10)
    assert resp.cost_cap_warning["mode"] == "warn"


@pytest.mark.asyncio
async def test_message_block_mode_raises_cost_cap_error(
    db_session: AsyncSession,
    monkeypatch,
):
    monkeypatch.setattr(settings, "ai_cost_cap_enforcement", "block")
    monkeypatch.setattr(settings, "ai_per_student_weekly_cost_cap_usd", 0.10)
    student = await _seed_student(db_session)
    await _seed_turn(db_session, student.id, cost="0.50", age_hours=1)

    with pytest.raises(CostCapExceededError) as exc:
        await _mock_client().message(
            agent="orchestrator",
            model="sonnet",
            system="x",
            messages=[{"role": "user", "content": "hi"}],
            student_id=student.id,
            db=db_session,
        )
    assert exc.value.student_id == student.id
    assert exc.value.cap_usd == pytest.approx(0.10)
    assert exc.value.spent_usd == pytest.approx(0.50)


@pytest.mark.asyncio
async def test_message_off_mode_does_not_warn(
    db_session: AsyncSession,
    monkeypatch,
):
    monkeypatch.setattr(settings, "ai_cost_cap_enforcement", "off")
    student = await _seed_student(db_session)
    await _seed_turn(db_session, student.id, cost="100.0", age_hours=1)

    resp = await _mock_client().message(
        agent="orchestrator",
        model="sonnet",
        system="x",
        messages=[{"role": "user", "content": "hi"}],
        student_id=student.id,
        db=db_session,
    )
    assert resp.cost_cap_warning is None


@pytest.mark.asyncio
async def test_message_under_cap_no_warning(
    db_session: AsyncSession,
    monkeypatch,
):
    monkeypatch.setattr(settings, "ai_cost_cap_enforcement", "warn")
    monkeypatch.setattr(settings, "ai_per_student_weekly_cost_cap_usd", 0.50)
    student = await _seed_student(db_session)
    await _seed_turn(db_session, student.id, cost="0.10", age_hours=1)

    resp = await _mock_client().message(
        agent="orchestrator",
        model="sonnet",
        system="x",
        messages=[{"role": "user", "content": "hi"}],
        student_id=student.id,
        db=db_session,
    )
    assert resp.cost_cap_warning is None


# ── stream_message gating ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_stream_message_block_mode_raises_before_yielding(
    db_session: AsyncSession,
    monkeypatch,
):
    """In block mode the generator must raise before yielding any text —
    SSE consumers should not see a partial response when the cap blocks."""
    monkeypatch.setattr(settings, "ai_cost_cap_enforcement", "block")
    monkeypatch.setattr(settings, "ai_per_student_weekly_cost_cap_usd", 0.10)
    student = await _seed_student(db_session)
    await _seed_turn(db_session, student.id, cost="0.50", age_hours=1)

    client = _mock_client()
    chunks: list = []
    with pytest.raises(CostCapExceededError):
        async for evt in client.stream_message(
            agent="orchestrator",
            model="sonnet",
            system="x",
            messages=[{"role": "user", "content": "hi"}],
            student_id=student.id,
            db=db_session,
        ):
            chunks.append(evt)
    assert chunks == []  # no events emitted before the raise


@pytest.mark.asyncio
async def test_stream_message_warn_mode_attaches_to_done_payload(
    db_session: AsyncSession,
    monkeypatch,
):
    monkeypatch.setattr(settings, "ai_cost_cap_enforcement", "warn")
    monkeypatch.setattr(settings, "ai_per_student_weekly_cost_cap_usd", 0.10)
    student = await _seed_student(db_session)
    await _seed_turn(db_session, student.id, cost="0.20", age_hours=1)

    client = _mock_client()
    done_payload = None
    async for event_type, payload in client.stream_message(
        agent="orchestrator",
        model="sonnet",
        system="x",
        messages=[{"role": "user", "content": "hi"}],
        student_id=student.id,
        db=db_session,
    ):
        if event_type == "done":
            done_payload = payload
    assert done_payload is not None
    assert done_payload.cost_cap_warning is not None
    assert done_payload.cost_cap_warning["mode"] == "warn"
