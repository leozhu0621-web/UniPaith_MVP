"""A3 — Layer Validator.

For BASIC: deterministic — see `state.evaluate_basic_layer`.
For PERSONALITY and IDENTITY (A3 phase): adds a Haiku-as-judge LLM call to
score soft criteria (depth of value claims, presence of self-awareness
moments). The LLM judge is gated behind `LayerValidator.use_llm_judge`;
when False, the validator returns a deterministic verdict only.

This module is intentionally thin — the heavy lifting lives in `state.py`.
The validator's job is to:

  1. Build a `StudentSnapshot` from the live student profile + recent
     extractions.
  2. Call the right evaluator for the current layer.
  3. Return a `LayerVerdict` for the orchestrator to consume.

A2 ships only the BASIC pathway. PERSONALITY and IDENTITY raise
NotImplementedError so callers know not to expect them yet.
"""

from __future__ import annotations

from typing import Any

from unipaith.ai.state import (
    Layer,
    LayerVerdict,
    StudentSnapshot,
    evaluate_basic_layer,
)


class LayerValidator:
    """Layer-by-layer exit-condition checker.

    No LLM in A2 — this validator is pure Python over a snapshot. A3 adds
    Haiku-as-judge for the personality and identity layers' soft criteria.
    """

    def __init__(self, *, use_llm_judge: bool = False):
        self.use_llm_judge = use_llm_judge

    def validate(
        self,
        *,
        layer: Layer,
        snapshot: StudentSnapshot,
        recent_extractions: list[dict[str, Any]] | None = None,
    ) -> LayerVerdict:
        """Return the verdict for `layer` given the student's current state.

        `recent_extractions` lets the validator look at the freshest
        signals (used in A3 for personality/identity layers). For BASIC
        we read directly off the snapshot.
        """
        if layer == "basic":
            return evaluate_basic_layer(snapshot)

        # PERSONALITY and IDENTITY: A3.
        raise NotImplementedError(
            f"LayerValidator: layer='{layer}' not yet implemented; A2 ships BASIC only."
        )


# Module-level convenience: a default instance for callers that don't need
# to swap config. The orchestration layer uses this.
default_validator = LayerValidator()
