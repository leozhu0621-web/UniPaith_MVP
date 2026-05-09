"""UniPaith AI package.

Phase A1 ships only the foundations: Anthropic client wrapper, prompt files,
extractor JSON schema, and an eval harness. Agents (orchestrator, extractor,
validator, feature emitter, rationale, workshop coach) land in A2–C2.

All LLM calls in the application MUST go through `unipaith.ai.client.AIClient`.
This is enforced by:
  - the cost ledger (`ai_turns` table) — every call writes a row
  - the per-student cost cap — checked before each call
  - the prompt-cache layout — built into the client, not duplicated per agent

External code imports the singleton:

    from unipaith.ai import get_client
    client = get_client()
    response = await client.message(agent="extractor", ...)
"""

from unipaith.ai.client import AIClient, get_client

__all__ = ["AIClient", "get_client"]
