"""Uni guided-journey helpers — pure, deterministic stage math.

The unified Uni conversation is led stage-by-stage. The current stage is the
first Discovery layer (profile → goals → needs) not yet at the ready threshold,
derived from ``DiscoverySession.completion_breakdown``. No stored stage pointer.
"""

from __future__ import annotations

STAGES: tuple[str, ...] = ("profile", "goals", "needs")
_LABELS = {"profile": "About you", "goals": "your goals", "needs": "what you need"}
_READY = 0.5  # mirrors discovery_service.HANDOFF_THRESHOLD


def current_stage(breakdown: dict[str, float] | None) -> str | None:
    """First Discovery layer below the ready threshold, or None if all are ready."""
    bd = breakdown or {}
    for stage in STAGES:
        if float(bd.get(stage, 0.0) or 0.0) < _READY:
            return stage
    return None


def stage_label(stage: str | None) -> str:
    """Human label for a stage; 'your matches' once the journey is complete."""
    return _LABELS.get(stage or "", "your matches")
