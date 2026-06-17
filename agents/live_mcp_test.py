"""End-to-end test: does the live platform agent reach the UniPaith MCP server
and get real data? Creates a session (with the auth vault), asks Uni to find
programs, and reports every agent.mcp_tool_use / agent.mcp_tool_result, the
final reply, and a PASS/FAIL verdict.

Run:
  cd unipaith-backend && \
  ANTHROPIC_API_KEY=$(grep '^ANTHROPIC_API_KEY=sk-' .env | head -1 | cut -d= -f2-) \
  .venv/bin/python ../agents/live_mcp_test.py
"""

from __future__ import annotations

import sys

import anthropic

AGENT = "agent_01Gcox2cnu9zvUCR5Lfb9ymg"  # pragma: allowlist secret
ENV = "env_01N43sA3tmVhij3YYZgWzAP2"  # pragma: allowlist secret
VAULT = "vlt_011Cc3tSSR4f2gHKbZPtUsbL"  # pragma: allowlist secret
PROMPT = "Can you find me a few computer science master's programs? Just search and name a couple."


def main() -> int:
    c = anthropic.Anthropic()
    sess = c.beta.sessions.create(
        agent=AGENT, environment_id=ENV, vault_ids=[VAULT], title="mcp e2e test"
    )
    sid = sess.id
    print(f"session = {sid}", flush=True)

    text: list[str] = []
    tool_uses: list[tuple] = []
    tool_results: list[tuple] = []
    seen = 0
    with c.beta.sessions.events.stream(sid) as stream:
        c.beta.sessions.events.send(
            sid,
            events=[{"type": "user.message", "content": [{"type": "text", "text": PROMPT}]}],
        )
        for ev in stream:
            seen += 1
            if seen > 250:
                print("  [cap] stopping after 250 events", flush=True)
                break
            t = getattr(ev, "type", "")
            if t == "agent.message":
                for b in getattr(ev, "content", []) or []:
                    if getattr(b, "type", "") == "text":
                        text.append(b.text)
            elif t == "agent.mcp_tool_use":
                perm = getattr(ev, "evaluated_permission", None)
                tool_uses.append((ev.mcp_server_name, ev.name, perm))
                print(f"  [mcp_tool_use] {ev.mcp_server_name}.{ev.name} perm={perm}", flush=True)
            elif t == "agent.mcp_tool_result":
                ok = not getattr(ev, "is_error", False)
                snippet = ""
                for b in getattr(ev, "content", None) or []:
                    snippet += getattr(b, "text", "") or ""
                tool_results.append((ok, snippet[:240]))
                print(f"  [mcp_tool_result] ok={ok} :: {snippet[:240]!r}", flush=True)
            elif t == "session.status_idle":
                sr = getattr(getattr(ev, "stop_reason", None), "type", None)
                print(f"  [idle] stop_reason={sr}", flush=True)
                if sr in ("end_turn", "retries_exhausted"):
                    break
            elif t in ("session.status_terminated", "session.deleted"):
                print(f"  [{t}]", flush=True)
                break
            elif t == "session.error":
                print(f"  [session.error] {getattr(ev, 'error', ev)!r}", flush=True)

    reply = "".join(text).strip()
    print("\n=== RESULT ===")
    print("tool calls:", [f"{s}.{n}({p})" for s, n, p in tool_uses])
    print("tool results ok:", [ok for ok, _ in tool_results])
    print("reply:", reply[:700])
    called_mcp = any(s == "unipaith" for s, _, _ in tool_uses)
    got_data = any(ok for ok, _ in tool_results)
    verdict = called_mcp and got_data and bool(reply)
    print("\nMCP E2E", "PASS" if verdict else "FAIL",
          f"(called_unipaith_mcp={called_mcp}, got_data={got_data})")
    return 0 if verdict else 1


if __name__ == "__main__":
    raise SystemExit(main())
