"""Spec 57 — realtime & notifications: broker, catalog, service fan-out, digest,
delivery reliability, SSE stream and WS messaging."""

from __future__ import annotations

import asyncio
import json
import uuid

import pytest

from unipaith.api.realtime import (
    _handle_ws_inbound,
    _other_participants,
    ws_messages,
)
from unipaith.config import settings
from unipaith.core.realtime import RealtimeBroker, broker
from unipaith.core.realtime import event as rt_event
from unipaith.models.engagement import Conversation
from unipaith.models.student import StudentProfile
from unipaith.models.user import User, UserRole
from unipaith.services import notification_catalog as catalog
from unipaith.services import notification_delivery as delivery
from unipaith.services.event_hooks import on_message_received
from unipaith.services.notification_service import NotificationService


# ── helpers ──────────────────────────────────────────────────────────────────
async def _make_user(db, role: str = "student") -> User:
    user = User(
        id=uuid.uuid4(),
        email=f"rt-{uuid.uuid4().hex[:8]}@example.com",
        cognito_sub=f"dev-{uuid.uuid4().hex[:8]}",
        role=UserRole(role),
        is_active=True,
    )
    db.add(user)
    await db.flush()
    return user


# ── §2 · broker ──────────────────────────────────────────────────────────────
async def test_broker_publish_subscribe_delivers():
    b = RealtimeBroker()
    uid = uuid.uuid4()
    async with b.subscribe(uid) as q:
        await b.publish(uid, rt_event("ping", {"n": 1}))
        evt = await asyncio.wait_for(q.get(), 1.0)
    assert evt == {"type": "ping", "data": {"n": 1}}
    assert b.stats()["backend"] == "memory"


async def test_broker_isolates_users():
    b = RealtimeBroker()
    a, c = uuid.uuid4(), uuid.uuid4()
    async with b.subscribe(a) as qa, b.subscribe(c) as qc:
        await b.publish(a, rt_event("for_a"))
        got = await asyncio.wait_for(qa.get(), 1.0)
        assert got["type"] == "for_a"
        assert qc.empty()  # c received nothing


async def test_broker_unsubscribe_cleans_up():
    b = RealtimeBroker()
    uid = uuid.uuid4()
    async with b.subscribe(uid):
        assert b.stats()["subscribers"] == 1
    assert b.stats()["subscribers"] == 0
    assert b.stats()["users_connected"] == 0


async def test_broker_drops_oldest_when_full(monkeypatch):
    monkeypatch.setattr(settings, "realtime_queue_maxsize", 2)
    b = RealtimeBroker()
    uid = uuid.uuid4()
    async with b.subscribe(uid) as q:
        for i in range(5):
            await b.publish(uid, rt_event("e", {"i": i}))
        # Queue holds at most 2; the newest survive, oldest dropped.
        assert q.qsize() == 2
        assert b.dropped >= 3


# ── §3 · catalog ─────────────────────────────────────────────────────────────
def test_catalog_resolves_known_event():
    e = catalog.get_entry("decision_made")
    assert e.pref_key == "decisions"
    assert e.urgency == catalog.URGENT
    assert e.silenceable is False  # transactional — not fully silenceable
    assert e.essential is True


def test_catalog_default_for_unknown():
    e = catalog.get_entry("template_acceptance")
    assert e is catalog.DEFAULT_ENTRY
    assert e.pref_key == "messages"
    assert catalog.urgency_of("totally_unknown") == catalog.URGENT


def test_catalog_digest_classification():
    assert catalog.urgency_of("saved_search_alert") == catalog.DIGEST
    assert catalog.is_silenceable("saved_search_alert") is True


def test_catalog_render_fills_deeplink():
    aid = uuid.uuid4()
    title, body, link = catalog.render("decision_made", {"application_id": aid})
    assert link == f"/applications/{aid}"
    assert title and body


def test_catalog_summary_and_count():
    assert catalog.event_type_count() == len(catalog.catalog_summary())
    assert catalog.event_type_count() >= 10


# ── §3/§4 · service emit, idempotency, fan-out ───────────────────────────────
async def test_notify_writes_row_and_sets_urgency(db_session):
    user = await _make_user(db_session)
    svc = NotificationService(db_session)
    n = await svc.notify(
        user_id=user.id,
        notification_type="saved_search_alert",
        title="New matches",
        body="3 new programs",
    )
    assert n.urgency == catalog.DIGEST
    assert n.delivery_status["in_app"] == "sent"
    assert n.delivery_status["email"] == "skipped"  # notifications_enabled=False in tests


async def test_notify_idempotent_on_event_id(db_session):
    user = await _make_user(db_session)
    svc = NotificationService(db_session)
    key = f"decision_made:{uuid.uuid4()}"
    first = await svc.notify(
        user_id=user.id,
        notification_type="decision_made",
        title="Decision",
        body="b",
        event_id=key,
    )
    second = await svc.notify(
        user_id=user.id,
        notification_type="decision_made",
        title="Decision again",
        body="b2",
        event_id=key,
    )
    assert first.id == second.id
    assert (await svc.unread_count(user.id))["count"] == 1


async def test_notify_publishes_to_broker(db_session):
    user = await _make_user(db_session)
    svc = NotificationService(db_session)
    async with broker.subscribe(user.id) as q:
        await svc.notify(
            user_id=user.id,
            notification_type="message_received",
            title="New message",
            body="hi",
        )
        first = await asyncio.wait_for(q.get(), 1.0)
        second = await asyncio.wait_for(q.get(), 1.0)
    types = {first["type"], second["type"]}
    assert "notification.created" in types
    assert "notification.unread_count" in types


async def test_emit_renders_from_catalog(db_session):
    user = await _make_user(db_session)
    svc = NotificationService(db_session)
    aid = uuid.uuid4()
    n = await svc.emit(
        event_type="decision_made",
        user_id=user.id,
        context={"application_id": aid},
        event_id=f"decision_made:{aid}",
    )
    assert n.action_url == f"/applications/{aid}"
    assert n.urgency == catalog.URGENT
    assert n.notification_type == "decision_made"


async def test_mark_read_publishes_read_event(db_session):
    user = await _make_user(db_session)
    svc = NotificationService(db_session)
    n = await svc.notify(user_id=user.id, notification_type="message_received", title="m", body="b")
    async with broker.subscribe(user.id) as q:
        await svc.mark_read(user.id, n.id)
        evt = await asyncio.wait_for(q.get(), 1.0)
    assert evt["type"] == "notification.read"
    assert evt["data"]["id"] == str(n.id)


async def test_mark_all_read_publishes(db_session):
    user = await _make_user(db_session)
    svc = NotificationService(db_session)
    await svc.notify(user_id=user.id, notification_type="message_received", title="m", body="b")
    async with broker.subscribe(user.id) as q:
        await svc.mark_all_read(user.id)
        evt = await asyncio.wait_for(q.get(), 1.0)
    assert evt["type"] == "notification.read_all"


# ── §6 · digest ──────────────────────────────────────────────────────────────
async def test_run_digest_batches_and_marks(db_session, monkeypatch):
    user = await _make_user(db_session)
    svc = NotificationService(db_session)
    # Three digest-class notifications, un-emailed.
    for i in range(3):
        await svc.notify(
            user_id=user.id,
            notification_type="saved_search_alert",
            title=f"alert {i}",
            body="new matches",
        )
    # Enable email + stub the SES send.
    monkeypatch.setattr(settings, "notifications_enabled", True)
    monkeypatch.setattr(settings, "email_notifications_enabled", True)
    sent_emails: list[tuple] = []

    async def _fake_send(uid, subject, body):
        sent_emails.append((uid, subject, body))
        return True

    monkeypatch.setattr(svc, "_send_email", _fake_send)

    sent = await svc.run_digest()
    assert sent == 1  # one batched email for the one user
    assert len(sent_emails) == 1
    assert "3 new updates" in sent_emails[0][1]
    # All folded notifications are now marked emailed → next run is a no-op.
    assert await svc.run_digest() == 0


async def test_urgent_not_deferred_to_digest(db_session, monkeypatch):
    """Urgent events email immediately even when the digest is enabled."""
    user = await _make_user(db_session)
    svc = NotificationService(db_session)
    monkeypatch.setattr(settings, "notifications_enabled", True)
    monkeypatch.setattr(settings, "notification_digest_enabled", True)
    monkeypatch.setattr(settings, "email_notifications_enabled", True)

    async def _ok(uid, subject, body):
        return True

    monkeypatch.setattr(svc, "_send_email", _ok)
    n = await svc.notify(
        user_id=user.id, notification_type="decision_made", title="Decision", body="b"
    )
    assert n.delivery_status["email"] == "sent"  # urgent → immediate


async def test_digest_class_deferred_when_digest_enabled(db_session, monkeypatch):
    user = await _make_user(db_session)
    svc = NotificationService(db_session)
    monkeypatch.setattr(settings, "notifications_enabled", True)
    monkeypatch.setattr(settings, "notification_digest_enabled", True)
    monkeypatch.setattr(settings, "email_notifications_enabled", True)
    n = await svc.notify(
        user_id=user.id,
        notification_type="saved_search_alert",
        title="alert",
        body="matches",
    )
    assert n.delivery_status["email"] == "deferred_digest"
    assert n.is_emailed is False


# ── §4 · delivery reliability (retry + DLQ) ──────────────────────────────────
async def test_delivery_retry_succeeds_after_failure():
    delivery.reset()
    calls = {"n": 0}

    async def _flaky():
        calls["n"] += 1
        if calls["n"] < 2:
            raise RuntimeError("transient")
        return True

    ok = await delivery.deliver_with_retry(
        "email",
        _flaky,
        user_id=uuid.uuid4(),
        event_type="x",
        max_retries=3,
        backoff_seconds=0,
    )
    assert ok is True
    assert calls["n"] == 2
    assert delivery.dlq_size() == 0


async def test_delivery_dead_letters_on_terminal_failure():
    delivery.reset()

    async def _always_fail():
        raise RuntimeError("down")

    ok = await delivery.deliver_with_retry(
        "email",
        _always_fail,
        user_id=uuid.uuid4(),
        event_type="decision_made",
        max_retries=2,
        backoff_seconds=0,
    )
    assert ok is False
    assert delivery.dlq_size() == 1
    assert delivery.dead_letters()[0]["channel"] == "email"
    assert delivery.delivery_stats()["failed"] >= 1


# ── §2 · SSE endpoint ────────────────────────────────────────────────────────
async def test_sse_requires_auth(client):
    resp = await client.get("/api/v1/me/stream")
    assert resp.status_code == 403


class _FakeRequest:
    """Drives me_stream's generator without an infinite ASGI client stream."""

    def __init__(self):
        self.disconnected = False

    async def is_disconnected(self):
        return self.disconnected


def _frame_event(frame: str) -> dict:
    assert frame.startswith("data:")
    return json.loads(frame[len("data:") :].strip())


async def test_sse_streams_connected_then_live_event(db_session, monkeypatch):
    from unipaith.api.realtime import me_stream

    monkeypatch.setattr(settings, "realtime_heartbeat_seconds", 1)
    user = await _make_user(db_session)
    await db_session.commit()

    req = _FakeRequest()
    resp = await me_stream(req, user=user)
    it = resp.body_iterator

    connected = _frame_event(await asyncio.wait_for(it.__anext__(), 2.0))
    assert connected["type"] == "connected"
    assert "unread" in connected["data"]

    await broker.publish(user.id, rt_event("notification.unread_count", {"count": 9}))
    live = _frame_event(await asyncio.wait_for(it.__anext__(), 2.0))
    assert live["type"] == "notification.unread_count"
    assert live["data"]["count"] == 9

    # Disconnect → the generator returns on its next loop check.
    req.disconnected = True
    with pytest.raises(StopAsyncIteration):
        await asyncio.wait_for(it.__anext__(), 2.0)


# ── §2 · WS messaging ────────────────────────────────────────────────────────
class FakeWebSocket:
    def __init__(self, headers=None, inbound=None):
        self.headers = headers or {}
        self._inbound = list(inbound or [])
        self.sent: list[dict] = []
        self.closed: int | None = None
        self.accepted = False

    async def accept(self):
        self.accepted = True

    async def close(self, code: int = 1000):
        self.closed = code

    async def send_json(self, data):
        self.sent.append(data)

    async def receive_json(self):
        if self._inbound:
            return self._inbound.pop(0)
        from fastapi import WebSocketDisconnect

        raise WebSocketDisconnect(1000)


async def test_ws_rejects_without_token():
    ws = FakeWebSocket(headers={})
    await ws_messages(ws, access_token=None)
    assert ws.closed == 4401
    assert ws.accepted is False


async def test_ws_ping_pong_and_disconnect(db_session):
    user = await _make_user(db_session)
    await db_session.commit()
    token = f"dev:{user.id}:student"
    ws = FakeWebSocket(inbound=[{"type": "ping"}])
    await ws_messages(ws, access_token=token)
    assert ws.accepted is True
    assert any(s["type"] == "pong" for s in ws.sent)


async def test_ws_handle_inbound_ping():
    ws = FakeWebSocket()
    await _handle_ws_inbound(uuid.uuid4(), {"type": "ping"}, ws)
    assert ws.sent[-1]["type"] == "pong"


async def test_other_participants_resolves_both_sides(db_session):
    student_user = await _make_user(db_session, "student")
    inst_user = await _make_user(db_session, "institution_admin")
    profile = StudentProfile(id=uuid.uuid4(), user_id=student_user.id)
    db_session.add(profile)
    await db_session.flush()
    conv = Conversation(id=uuid.uuid4(), student_id=profile.id, assigned_to=inst_user.id)
    db_session.add(conv)
    await db_session.commit()

    others = await _other_participants(conv.id, student_user.id)
    assert inst_user.id in others
    assert student_user.id not in others


async def test_ws_typing_echoes_to_other_participant(db_session):
    student_user = await _make_user(db_session, "student")
    inst_user = await _make_user(db_session, "institution_admin")
    profile = StudentProfile(id=uuid.uuid4(), user_id=student_user.id)
    db_session.add(profile)
    await db_session.flush()
    conv = Conversation(id=uuid.uuid4(), student_id=profile.id, assigned_to=inst_user.id)
    db_session.add(conv)
    await db_session.commit()

    async with broker.subscribe(inst_user.id) as q:
        await _handle_ws_inbound(
            student_user.id,
            {"type": "typing", "conversation_id": str(conv.id), "is_typing": True},
            FakeWebSocket(),
        )
        evt = await asyncio.wait_for(q.get(), 1.0)
    assert evt["type"] == "messaging.typing"
    assert evt["data"]["user_id"] == str(student_user.id)
    assert evt["data"]["is_typing"] is True


async def test_message_hook_instant_delivery(db_session):
    recipient = await _make_user(db_session)
    await db_session.commit()
    conv_id = uuid.uuid4()
    async with broker.subscribe(recipient.id) as q:
        await on_message_received(db_session, recipient.id, conv_id, "Alex")
        seen = set()
        for _ in range(3):
            evt = await asyncio.wait_for(q.get(), 1.0)
            seen.add(evt["type"])
            if "messaging.message" in seen:
                break
    assert "messaging.message" in seen


@pytest.mark.parametrize("token", ["", "garbage", "dev:not-a-uuid:student"])
async def test_ws_rejects_bad_tokens(token):
    ws = FakeWebSocket()
    await ws_messages(ws, access_token=token or None)
    assert ws.closed == 4401
