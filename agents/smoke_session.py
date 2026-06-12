"""Bounded live smoke test of the Uni managed agent on platform.claude.com.

Starts a session, sends one student message, and watches the event stream until
Uni's first tool call (or she idles) — then archives the session. Confirms the
agent is live and behaving (she should call get_profile_snapshot first, per her
system prompt). She'll idle there because her tools are host-side and no host is
answering — that's expected.

Key from env (ANTHROPIC_API_KEY); never commit it.

Usage:
    ANTHROPIC_API_KEY=sk-ant-... python agents/smoke_session.py
"""

from __future__ import annotations

import anthropic

AGENT_ID = "agent_019QbYB93Ykh8Y58RBHquiQ6"
ENV_ID = "env_01N43sA3tmVhij3YYZgWzAP2"
PROMPT = "Hi, I'm thinking about grad school but honestly I'm overwhelmed."


def main() -> int:
    client = anthropic.Anthropic()
    session = client.beta.sessions.create(agent=AGENT_ID, environment_id=ENV_ID, title="smoke test")
    print("session:", session.id)

    reply: list[str] = []
    tool = None
    seen = 0
    agent_events = 0  # only the agent's own messages/tool calls drive the cap
    with client.beta.sessions.events.stream(session.id) as stream:
        client.beta.sessions.events.send(
            session.id,
            events=[{"type": "user.message", "content": [{"type": "text", "text": PROMPT}]}],
        )
        for event in stream:
            seen += 1
            et = getattr(event, "type", "")
            if et == "agent.message":
                agent_events += 1
                for b in getattr(event, "content", []) or []:
                    if getattr(b, "type", "") == "text":
                        reply.append(b.text)
            elif et == "agent.custom_tool_use":
                tool = {"name": getattr(event, "name", "?"), "input": getattr(event, "input", None)}
                break
            elif et in ("session.status_idle", "session.status_terminated"):
                break
            # Don't let thinking/heartbeat noise trip the cap before Uni acts.
            if agent_events > 60:
                break

    text = "".join(reply).strip()
    print("events seen:", seen)
    print("Uni said:", text[:500] or "(no text before tool call)")
    print("first tool call:", tool)
    ok = True
    if tool is None and not text:
        print("smoke FAILED: Uni produced no reply text and no tool call")
        ok = False
    try:
        client.beta.sessions.archive(session.id)
        print("session archived")
    except Exception as e:  # noqa: BLE001
        print("archive note:", str(e)[:120])
        ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
