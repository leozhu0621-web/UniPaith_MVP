"""UniAgentHost turn loop + ManagedAgentClient facade."""

import pytest

from tests._uni_helpers import ensure_profile


def test_managed_agent_client_importable():
    from unipaith.ai.managed_agent_client import ManagedAgentClient  # noqa: F401


class _Block:
    def __init__(self, text):
        self.type = "text"
        self.text = text


class _Stop:
    def __init__(self, type):
        self.type = type


class _Event:
    def __init__(self, type, **kw):
        self.type = type
        for k, v in kw.items():
            setattr(self, k, v)


class _FakeAgentClient:
    """Scripts an Anthropic session: greets, calls one tool, replies, idles."""

    def __init__(self, *, raise_on_create=False, raise_on_stream=False, chips=False):
        self._raise_create = raise_on_create
        self._raise_stream = raise_on_stream
        self._chips = chips
        self.sent_results = []
        self.sent_messages = []

    async def create_session(self, **kw):
        if self._raise_create:
            raise RuntimeError("platform down")
        return "sesn_fake"

    async def send_user_message(self, session_id, text):
        self.sent_messages.append(text)

    async def send_tool_result(self, session_id, tool_use_id, result, *, is_error=False):
        self.sent_results.append((tool_use_id, result))

    async def stream(self, session_id):
        if self._raise_stream:
            raise RuntimeError("stream blew up")
            yield  # pragma: no cover — makes this an async generator
        yield _Event("agent.message", content=[_Block("Hi there. ")])
        yield _Event("agent.custom_tool_use", id="sevt_1", name="get_profile_snapshot", input={})
        if self._chips:
            yield _Event(
                "agent.custom_tool_use",
                id="sevt_2",
                name="suggest_replies",
                input={"options": ["Research", "Industry"], "kind": "multi"},
            )
        yield _Event("agent.message", content=[_Block("Where are you headed?")])
        yield _Event("session.status_idle", stop_reason=_Stop("end_turn"))


@pytest.mark.asyncio
async def test_stream_turn_relays_and_answers_tool(db_session, mock_student_user):
    from unipaith.services.uni_agent_host import UniAgentHost

    await ensure_profile(db_session, mock_student_user)
    fake = _FakeAgentClient()
    host = UniAgentHost(db_session, client=fake)
    events = [ev async for ev in host.stream_turn(mock_student_user.id, content="hello")]
    names = [n for n, _ in events]
    assert "delta" in names
    assert "assistant_message" in names
    deltas = "".join(p["text"] for n, p in events if n == "delta")
    assert "Hi there" in deltas and "Where are you headed" in deltas
    # The host answered the agent's tool call.
    assert fake.sent_results and fake.sent_results[0][0] == "sevt_1"
    # The student turn was relayed.
    assert fake.sent_messages == ["hello"]


@pytest.mark.asyncio
async def test_suggest_replies_persisted_as_chips(db_session, mock_student_user):
    """A suggest_replies tool call is stamped onto the assistant message's
    extracted_signals so the frontend renders chips — no frontend change."""
    from sqlalchemy import select

    from unipaith.models.discovery import DiscoveryMessage
    from unipaith.services.uni_agent_host import UniAgentHost

    await ensure_profile(db_session, mock_student_user)
    host = UniAgentHost(db_session, client=_FakeAgentClient(chips=True))
    _ = [ev async for ev in host.stream_turn(mock_student_user.id, content="hello")]

    rows = (
        (
            await db_session.execute(
                select(DiscoveryMessage).where(DiscoveryMessage.role == "assistant")
            )
        )
        .scalars()
        .all()
    )
    assert rows, "assistant message was mirrored"
    sig = rows[-1].extracted_signals or {}
    assert sig.get("suggested_options") == ["Research", "Industry"]
    assert sig.get("suggested_input", {}).get("kind") == "multi"


@pytest.mark.asyncio
async def test_stream_opener_speaks_first_without_a_student_message(db_session, mock_student_user):
    """The proactive opener relays Uni's first message but persists NO student
    turn (the student hasn't typed anything)."""
    from sqlalchemy import select

    from unipaith.models.discovery import DiscoveryMessage
    from unipaith.services.uni_agent_host import UniAgentHost

    await ensure_profile(db_session, mock_student_user)
    host = UniAgentHost(db_session, client=_FakeAgentClient())
    events = [ev async for ev in host.stream_opener(mock_student_user.id)]
    names = [n for n, _ in events]
    assert "delta" in names and "assistant_message" in names

    rows = (await db_session.execute(select(DiscoveryMessage))).scalars().all()
    roles = [r.role for r in rows]
    assert "assistant" in roles
    assert "student" not in roles  # opener persists no fake student turn


@pytest.mark.asyncio
async def test_opener_trigger_includes_known_profile(db_session, mock_student_user):
    """todo 2.1 — the opener trigger carries a compact summary of what UniPaith
    already knows (name + goals), so Uni greets by name and won't re-ask."""
    from unipaith.models.goals import StudentGoal
    from unipaith.services.uni_agent_host import UniAgentHost

    profile = await ensure_profile(db_session, mock_student_user)
    profile.first_name = "Ada"
    db_session.add(
        StudentGoal(
            student_id=profile.id,
            category="academic",
            specific="Start a Master's program in computer science",
            source="manual",
            status="active",
        )
    )
    await db_session.commit()

    fake = _FakeAgentClient()
    host = UniAgentHost(db_session, client=fake)
    _ = [ev async for ev in host.stream_opener(mock_student_user.id)]

    trigger = fake.sent_messages[0]
    assert "[SESSION_START]" in trigger
    assert "Ada" in trigger
    assert "computer science" in trigger
    assert "re-ask" in trigger.lower()


@pytest.mark.asyncio
async def test_opener_trigger_generic_for_blank_profile(db_session, mock_student_user):
    """A brand-new student with nothing on file gets the generic opener (fail-soft),
    not an empty 'here's what we know' block."""
    from unipaith.services.uni_agent_host import UniAgentHost

    await ensure_profile(db_session, mock_student_user)
    fake = _FakeAgentClient()
    host = UniAgentHost(db_session, client=fake)
    _ = [ev async for ev in host.stream_opener(mock_student_user.id)]

    trigger = fake.sent_messages[0]
    assert "[SESSION_START]" in trigger
    assert "already knows" not in trigger  # no summary block for an empty profile


@pytest.mark.asyncio
async def test_stream_turn_raises_on_setup_failure(db_session, mock_student_user):
    """Setup failure must propagate so the API can fall back to the orchestrator."""
    from unipaith.services.uni_agent_host import UniAgentHost

    await ensure_profile(db_session, mock_student_user)
    host = UniAgentHost(db_session, client=_FakeAgentClient(raise_on_create=True))
    with pytest.raises(RuntimeError):
        _ = [ev async for ev in host.stream_turn(mock_student_user.id, content="hello")]


@pytest.mark.asyncio
async def test_stream_turn_graceful_on_midstream_failure(db_session, mock_student_user):
    """A failure after setup closes the turn calmly — never a 5xx, no fallback."""
    from unipaith.services.uni_agent_host import UniAgentHost

    await ensure_profile(db_session, mock_student_user)
    host = UniAgentHost(db_session, client=_FakeAgentClient(raise_on_stream=True))
    events = [ev async for ev in host.stream_turn(mock_student_user.id, content="hello")]
    names = [n for n, _ in events]
    assert "assistant_message" in names
    text = next(p["content"] for n, p in events if n == "assistant_message")
    assert "moment" in text.lower() or "breath" in text.lower()
