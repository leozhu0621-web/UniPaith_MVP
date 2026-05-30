"""Spec 03 §3 — Anthropic prompt-cache TTL markers.

The cache layout the migration spec mandates:

    1. System block        ← role + guardrails + output schema + frameworks;
                              rarely changes → cache at 1h
    2. Persona block       ← per-user/session profile snapshot → cache at 5min
    3. Conversation tail   ← the latest user turn / volatile state → uncached

`CACHE_1H` is the high-leverage breakpoint: the long system prompt + tool
schema are identical across every turn for every user, so a 1h TTL keeps them
warm even when a session sits idle longer than the 5-minute default. The 1h
TTL is generally available on the Claude API (no beta header needed) — the
write costs 2x base input vs 1.25x for 5min, but reads stay at 0.1x and the
prompt is reused on the order of thousands of times, so it pays for itself
immediately.

`CACHE_5MIN` is the default ephemeral marker (omitting `ttl` defaults to 5min)
for genuine per-user/session persona blocks that change between sessions but
not within one.

Ordering constraint (Anthropic): within a single request, 1h breakpoints must
appear before 5min breakpoints. Our agents satisfy this naturally — tools and
the system block (both 1h) precede the `messages` array (persona 5min / tail
uncached) in Anthropic's prefix order.
"""

from __future__ import annotations

from typing import Any

# Rarely-changing system / tool-schema blocks. Spec 03 §3 "system block, 1h".
CACHE_1H: dict[str, Any] = {"type": "ephemeral", "ttl": "1h"}

# Per-user/session persona blocks. Spec 03 §3 "persona block, 5min".
# Omitting `ttl` is the 5-minute default — kept explicit for readability.
CACHE_5MIN: dict[str, Any] = {"type": "ephemeral"}

__all__ = ["CACHE_1H", "CACHE_5MIN"]
