"""Apply the version-controlled Uni agent config to the managed agent on
platform.claude.com — pushes the current system prompt (agents/uni_system.md) +
tools (agents/uni.agent.yaml) and bumps the agent version. Read-modify-write.

The API key is read from the environment (ANTHROPIC_API_KEY) — never hardcode it
and never commit it.

Usage:
    ANTHROPIC_API_KEY=sk-ant-... python agents/apply_agent.py [agent_id]
"""

from __future__ import annotations

import pathlib
import sys

import anthropic
import yaml

HERE = pathlib.Path(__file__).parent
DEFAULT_AGENT_ID = "agent_019QbYB93Ykh8Y58RBHquiQ6"


def main() -> int:
    agent_id = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_AGENT_ID
    spec = yaml.safe_load((HERE / "uni.agent.yaml").read_text())
    system = (HERE / "uni_system.md").read_text()  # the @./uni_system.md source

    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

    before = client.beta.agents.retrieve(agent_id)
    before_d = before.model_dump() if hasattr(before, "model_dump") else dict(before)
    print(f"before: {before_d.get('name')} version={before_d.get('version')}")

    updated = client.beta.agents.update(
        agent_id,
        version=before_d["version"],  # optimistic lock against the current version
        name=spec["name"],
        model=spec["model"],
        description=spec["description"],
        system=system,
        tools=spec["tools"],
    )
    d = updated.model_dump() if hasattr(updated, "model_dump") else dict(updated)
    print("applied ->", d.get("name"))
    print("new version:", d.get("version"))
    print("system chars:", len(d.get("system") or system))
    print("tools:", [t.get("name") or t.get("type") for t in (d.get("tools") or [])])
    print("system has 'How you talk':", "# How you talk" in (d.get("system") or system))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
