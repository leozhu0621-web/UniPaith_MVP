"""Read the Uni agent back from the Claude platform and check it's configured
right — system prompt present, all 5 tools present, and the two tools that need
schemas (search_programs, save_signals) actually kept them. READ-ONLY.

Usage:
    cd unipaith-backend
    ANTHROPIC_API_KEY=sk-ant-... ../agents/verify_agent.py            # default agent id
    ANTHROPIC_API_KEY=sk-ant-... python ../agents/verify_agent.py agent_xxx   # explicit id

Needs the managed-agents SDK surface (anthropic >= ~0.69). The repo venv has it.
"""

from __future__ import annotations

import sys

import anthropic

DEFAULT_AGENT_ID = "agent_019QbYB93Ykh8Y58RBHquiQ6"

EXPECTED: dict[str, list[str]] = {
    "get_profile_snapshot": [],
    "search_programs": [
        "query", "country", "degree_types", "min_tuition",
        "max_tuition", "delivery_formats", "location",
    ],
    "save_signals": ["basic", "personality", "identity", "goals", "needs", "confidence"],
    "get_matches": [],
    "generate_strategy": [],
}


def main() -> int:
    agent_id = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_AGENT_ID
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment
    agent = client.beta.agents.retrieve(agent_id)
    data = agent.model_dump() if hasattr(agent, "model_dump") else dict(agent)

    print(f"agent : {data.get('name')}  (id={agent_id})")
    print(f"model : {data.get('model')}")

    system = data.get("system") or ""
    ok_sys = len(system) > 500
    print(f"system: {len(system)} chars  {'OK' if ok_sys else '!! short — system prompt may be missing'}")

    tools = data.get("tools") or []
    print(f"tools : {len(tools)}")
    seen: set[str] = set()
    all_ok = ok_sys
    for tool in tools:
        name = tool.get("name") or tool.get("type")
        seen.add(name)
        schema = tool.get("input_schema") or {}
        props = sorted((schema.get("properties") or {}).keys())
        flag = "OK"
        want = set(EXPECTED.get(name, []))
        if want and not want.issubset(set(props)):
            flag = f"!! MISSING params: {sorted(want - set(props))}"
            all_ok = False
        print(f"  - {name:22} params={props}  {flag}")

    missing = sorted(set(EXPECTED) - seen)
    if missing:
        print(f"!! MISSING TOOLS: {missing}")
        all_ok = False
    else:
        print("all 5 expected tools present.")

    print("\nRESULT:", "✅ agent looks correctly configured" if all_ok else "❌ fix the items marked !! above")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
