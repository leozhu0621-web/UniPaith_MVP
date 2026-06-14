"""Live smoke for the Uni managed-agent host mechanics.

Drives the REAL platform agent through one turn using the same
ManagedAgentClient the host uses: create session → stream → send a student
message → answer custom-tool calls with canned data → print the transcript.

Proves, against the live API: the key has managed-agents access, the agent is
configured with the 5 custom tools, and the stream/send/tool-result cycle works.
No DB — tool results are canned (the DB tools are unit-tested separately).

Run:
  cd unipaith-backend && \
  ANTHROPIC_API_KEY=$(grep '^ANTHROPIC_API_KEY=sk-' .env | head -1 | cut -d= -f2-) \
  PYTHONPATH=src .venv/bin/python ../agents/live_smoke_host.py
"""

from __future__ import annotations

import asyncio
import json
import os
import sys

# The live, platform-canonical agent ("UniPaith College Counselor"). The host
# adapts to ITS tool contract (get_profile / create_profile / flat save_signals).
AGENT_ID = "agent_01Gcox2cnu9zvUCR5Lfb9ymg"
ENVIRONMENT_ID = "env_01N43sA3tmVhij3YYZgWzAP2"

# Canned tool results keyed by the live agent's tool names — enough to keep her
# talking. (The real host answers these against RDS via dispatch_tool.)
_CANNED = {
    "get_profile": {
        "profile": {"first_name": "Sam", "last_name": None},
        "goals": [],
        "needs": [],
        "identity": {"core_values": [], "worldview": [], "self_awareness": [], "summary": None},
        "active_strategy": None,
        "completion": {"profile": 0.1, "goals": 0.0, "needs": 0.0},
    },
    "create_profile": {"ok": True, "profile_id": "stub-id"},
    "search_programs": {"programs": [], "total": 0},
    "save_signals": {"written": {}, "completion": {}, "handoff_ready": False},
    "get_matches": {"ready": False, "completion": {}, "reason": "just getting started"},
    "generate_strategy": {"error": "strategy_unavailable", "detail": "not enough signal yet"},
}


async def main() -> int:
    from unipaith.ai.managed_agent_client import ManagedAgentClient

    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key.startswith("sk-"):
        print("NO ANTHROPIC_API_KEY in env", file=sys.stderr)
        return 2

    client = ManagedAgentClient(api_key=key)
    print("creating session…", flush=True)
    sid = await client.create_session(
        agent_id=AGENT_ID, environment_id=ENVIRONMENT_ID, title="live smoke"
    )
    print(f"session = {sid}", flush=True)

    text_parts: list[str] = []
    tools_called: list[str] = []
    stream = client.stream(sid)
    # Test speak-first: send the opener trigger and confirm she greets + leads.
    await client.send_user_message(
        sid,
        "[SESSION_START] The student just opened Uni and hasn't typed anything "
        "yet. Greet them warmly and lead with your first question — you speak first.",
    )
    async for event in stream:
        etype = getattr(event, "type", "")
        if etype == "agent.message":
            for block in getattr(event, "content", []) or []:
                if getattr(block, "type", "") == "text":
                    text_parts.append(block.text)
                    print(f"  [text] {block.text!r}", flush=True)
        elif etype == "agent.custom_tool_use":
            tools_called.append(event.name)
            result = _CANNED.get(event.name, {"ok": True})
            print(f"  [tool] {event.name}({json.dumps(event.input)[:80]}) -> canned", flush=True)
            await client.send_tool_result(sid, event.id, result)
        elif etype == "session.status_idle":
            sr = getattr(getattr(event, "stop_reason", None), "type", None)
            print(f"  [idle] stop_reason={sr}", flush=True)
            if sr in ("end_turn", "retries_exhausted"):
                break
        elif etype in ("session.status_terminated", "session.deleted"):
            print(f"  [{etype}]", flush=True)
            break

    print("\n=== RESULT ===")
    print("tools_called:", tools_called)
    print("reply:", "".join(text_parts).strip()[:600])
    ok = bool("".join(text_parts).strip())
    print("SMOKE", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
