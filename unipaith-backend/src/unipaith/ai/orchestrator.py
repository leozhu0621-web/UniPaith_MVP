"""A1 — Orchestrator agent (Discovery mode).

The conversational driver. Reads the current FSM state, the recent
conversation history, and the validator's verdict, then writes a single
turn of warm-but-specific coaching prose.

Cache layout (per `client.py` § "Design / Caching"):

    [1] system_prompt    = orchestrator_discovery.md + frameworks.md
                           (~3.5k tokens, reused across every turn for every
                            user — the highest-leverage cache breakpoint)
    [2] tool definitions = record_artifact + request_layer_advance
    [3] state header     = current_track / layer / completion_pct / next_probe
    [4] message history  = uncached tail

Conventions:

  - The orchestrator NEVER recommends programs in Discovery (frameworks
    rule 4). The system prompt enforces this; we don't post-validate
    output for it in A2 — depth-ladder evals catch regressions.
  - The orchestrator NEVER writes essays/resumes for the student
    (frameworks rule 5). Workshop guardrails (C1) handle this surface.
  - `record_artifact` calls are advisory; the discovery service
    cross-checks with the extractor before persisting. The orchestrator
    is allowed to be optimistic — wrong artifacts get filtered out.

A2 ships streaming-off (single-shot `message()` call). Streaming lands in
A3 alongside the SSE endpoint upgrade.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ai.client import AIClient, get_client
from unipaith.ai.prompt_cache import CACHE_1H
from unipaith.ai.state import Layer, LayerVerdict, Track
from unipaith.ai.tools import RECORD_ARTIFACT_TOOL, REQUEST_LAYER_ADVANCE_TOOL

PROMPTS_DIR = Path(__file__).parent / "prompts"


def _load_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8").rstrip()


# Built once at import; the contents rarely change. If you edit the prompt
# files at runtime (test fixtures), use `Orchestrator(system_prompt=...)`.
_FRAMEWORKS_TEXT = _load_prompt("_shared/frameworks.md")
_DISCOVERY_PROMPT_TEXT = _load_prompt("orchestrator_discovery.md")


def _build_discovery_system_prompt() -> str:
    """Concatenate the discovery prompt with the shared frameworks file.

    Frameworks live at the bottom (where the prompt references them) so
    the cache breakpoint covers both as a single ephemeral block.
    """
    return f"{_DISCOVERY_PROMPT_TEXT}\n\n---\n\n# Frameworks reference\n\n{_FRAMEWORKS_TEXT}"


_DISCOVERY_SYSTEM_PROMPT = _build_discovery_system_prompt()


@dataclass
class TurnContext:
    """Inputs the orchestrator needs to write one turn.

    Built by the discovery service from session state + validator verdict +
    student's known profile snapshot. No DB references inside — the
    orchestrator is pure I/O over Anthropic.
    """

    track: Track
    layer: Layer | None
    completion_pct: float
    verdict: LayerVerdict | None  # None on the very first turn
    known_profile_summary: str  # short text, used to anchor the LLM
    recent_signals_summary: str = ""
    history: list[dict[str, str]] = field(default_factory=list)  # [{role, content}]


@dataclass
class OrchestratorResponse:
    """The orchestrator's structured output for one turn."""

    text: str  # the assistant's prose reply
    record_artifact_calls: list[dict[str, Any]] = field(default_factory=list)
    requested_layer_advance: bool = False
    advance_rationale: str | None = None
    cost_usd: float = 0.0
    latency_ms: int = 0
    raw_blocks: list[dict[str, Any]] = field(default_factory=list)


class Orchestrator:
    """A1 — the streaming counselor (streaming-off in A2)."""

    AGENT_NAME = "orchestrator"

    def __init__(
        self,
        client: AIClient | None = None,
        *,
        system_prompt: str | None = None,
        max_tokens: int = 600,
        temperature: float = 0.6,
    ):
        self.client = client or get_client()
        self.system_prompt = system_prompt or _DISCOVERY_SYSTEM_PROMPT
        self.max_tokens = max_tokens
        # 0.6 — warm but not flighty. The framework adherence eval catches
        # drift; if we see refusal-to-redirect failures we'll lower this.
        self.temperature = temperature

    async def respond(
        self,
        *,
        ctx: TurnContext,
        student_id: UUID | None = None,
        discovery_message_id: UUID | None = None,
        db: AsyncSession | None = None,
    ) -> OrchestratorResponse:
        """Generate a single counselor turn. Records to `ai_turns` ledger."""
        system = self._build_system_blocks(ctx)
        tools = [
            {**RECORD_ARTIFACT_TOOL, "cache_control": CACHE_1H},
            {**REQUEST_LAYER_ADVANCE_TOOL},
        ]
        messages = self._build_messages(ctx)

        response = await self.client.message(
            agent=self.AGENT_NAME,
            model="sonnet",
            system=system,
            messages=messages,
            tools=tools,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            student_id=student_id,
            discovery_message_id=discovery_message_id,
            surface="discovery",
            db=db,
        )

        return self._parse_response(response)

    async def stream(
        self,
        *,
        ctx: TurnContext,
        student_id: UUID | None = None,
        discovery_message_id: UUID | None = None,
        db: AsyncSession | None = None,
    ):
        """Streaming variant. Yields the same event tuples as
        `AIClient.stream_message`:

          ('text_delta', str)        — incremental prose chunk
          ('tool_use',   dict)       — completed tool_use block
          ('done',       OrchestratorResponse)  — final aggregated turn

        Callers (the SSE endpoint) typically forward `text_delta` events
        directly to the wire and persist the final response on 'done'.
        """
        system = self._build_system_blocks(ctx)
        tools = [
            {**RECORD_ARTIFACT_TOOL, "cache_control": CACHE_1H},
            {**REQUEST_LAYER_ADVANCE_TOOL},
        ]
        messages = self._build_messages(ctx)

        async for event_type, payload in self.client.stream_message(
            agent=self.AGENT_NAME,
            model="sonnet",
            system=system,
            messages=messages,
            tools=tools,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            student_id=student_id,
            discovery_message_id=discovery_message_id,
            surface="discovery",
            db=db,
        ):
            if event_type == "done":
                # `payload` is an LLMResponse — wrap into an
                # OrchestratorResponse with parsed tool calls.
                yield ("done", self._parse_response(payload))
            else:
                yield (event_type, payload)

    # ── Building the request ─────────────────────────────────────────────

    def _build_system_blocks(self, ctx: TurnContext) -> list[dict[str, Any]]:
        """Three system blocks for the cache layout described above."""
        state_header = self._render_state_header(ctx)
        return [
            # Block 1: the long system prompt + frameworks. Cached at 1h
            # (spec 03 §3) — identical across every turn for every user, so
            # it's the highest-leverage breakpoint.
            {
                "type": "text",
                "text": self.system_prompt,
                "cache_control": CACHE_1H,
            },
            # Block 2: per-turn state header. Not cached — changes every turn
            # (volatile validator state), so it's the uncached tail.
            {
                "type": "text",
                "text": state_header,
            },
        ]

    @staticmethod
    def _render_state_header(ctx: TurnContext) -> str:
        verdict = ctx.verdict
        next_probe = (
            verdict.next_probe_hint
            if verdict and verdict.next_probe_hint
            else "(none — pick the next probe yourself per the framework)"
        )
        missing = ", ".join(verdict.missing_signals) if verdict and verdict.missing_signals else "—"
        return (
            f"## Current state\n\n"
            f"- Track: {ctx.track}\n"
            f"- Layer: {ctx.layer or '—'}\n"
            f"- Completion: {ctx.completion_pct:.0%}\n"
            f"- Validator's missing signals: {missing}\n"
            f"- Validator's next_probe: {next_probe}\n\n"
            f"## What we already know about this student\n\n"
            f"{ctx.known_profile_summary or '(nothing yet)'}\n\n"
            f"## Recently captured signals (this session)\n\n"
            f"{ctx.recent_signals_summary or '(none yet)'}"
        )

    @staticmethod
    def _build_messages(ctx: TurnContext) -> list[dict[str, Any]]:
        """Anthropic messages array. History is pass-through."""
        if ctx.history:
            return list(ctx.history)
        # No history → first turn. Anthropic requires a non-empty messages
        # array starting with `user`; we send a synthetic kickoff so the
        # orchestrator's opener is generated by the model, not hardcoded.
        return [{"role": "user", "content": "(Session starting — please greet me.)"}]

    # ── Parsing the response ─────────────────────────────────────────────

    def _parse_response(self, response) -> OrchestratorResponse:  # type: ignore[no-untyped-def]
        text_chunks: list[str] = []
        record_calls: list[dict[str, Any]] = []
        advance = False
        advance_rationale: str | None = None

        for block in response.content_blocks:
            btype = block.get("type")
            if btype == "text":
                text_chunks.append(block.get("text", ""))
            elif btype == "tool_use":
                tname = block.get("name")
                if tname == "record_artifact":
                    record_calls.append(block.get("input") or {})
                elif tname == "request_layer_advance":
                    advance = True
                    advance_rationale = (block.get("input") or {}).get("rationale")

        return OrchestratorResponse(
            text="".join(text_chunks).strip(),
            record_artifact_calls=record_calls,
            requested_layer_advance=advance,
            advance_rationale=advance_rationale,
            cost_usd=float(response.cost_usd),
            latency_ms=response.latency_ms,
            raw_blocks=response.content_blocks,
        )


# Module-level singleton for the common case.
_default_orchestrator: Orchestrator | None = None


def get_orchestrator() -> Orchestrator:
    global _default_orchestrator
    if _default_orchestrator is None:
        _default_orchestrator = Orchestrator()
    return _default_orchestrator


def reset_orchestrator() -> None:
    """Test helper."""
    global _default_orchestrator
    _default_orchestrator = None
