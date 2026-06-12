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

    def __init__(self, *, raise_on_create=False, raise_on_stream=False):
        self._raise_create = raise_on_create
        self._raise_stream = raise_on_stream
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
