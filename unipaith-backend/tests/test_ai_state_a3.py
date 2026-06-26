"""Phase A3 — Snapshot extension tests for personality + identity.

Verifies that `snapshot_from_extracted_signals_history` correctly builds
PersonalityEntry / IdentityClaim lists from JSONB audit-trail input, with
dedup and defensive handling of malformed entries.
"""

from __future__ import annotations

from unipaith.ai.artifacts import snapshot_from_extracted_signals_history


def test_snapshot_personality_extraction() -> None:
    history = [
        {
            "personality": [
                {"facet": "interest", "value": "ml", "evidence": "I love ml"},
                {"facet": "peer_style", "value": "small", "evidence": "small groups"},
            ]
        }
    ]
    snap = snapshot_from_extracted_signals_history(history)
    assert len(snap.personality) == 2
    facets = {p.facet for p in snap.personality}
    assert facets == {"interest", "peer_style"}


def test_snapshot_personality_dedup_across_turns() -> None:
    """If the extractor restates the same (facet, value) on a later turn,
    the snapshot keeps a single entry."""
    history = [
        {"personality": [{"facet": "interest", "value": "ML", "evidence": "ev1"}]},
        {"personality": [{"facet": "interest", "value": "ml", "evidence": "ev2"}]},
    ]
    snap = snapshot_from_extracted_signals_history(history)
    # Dedup is case-insensitive on value.
    assert len(snap.personality) == 1


def test_snapshot_personality_distinct_values_kept() -> None:
    history = [
        {"personality": [{"facet": "interest", "value": "ml", "evidence": "ev1"}]},
        {"personality": [{"facet": "interest", "value": "philosophy", "evidence": "ev2"}]},
    ]
    snap = snapshot_from_extracted_signals_history(history)
    assert len(snap.personality) == 2


def test_snapshot_identity_extraction() -> None:
    history = [
        {
            "identity": [
                {"facet": "value", "claim": "loyalty", "evidence": "I trust people"},
                {
                    "facet": "self_awareness",
                    "claim": "noticed pattern",
                    "evidence": "I avoid the lab",
                },
            ]
        }
    ]
    snap = snapshot_from_extracted_signals_history(history)
    assert len(snap.identity_claims) == 2
    facets = {c.facet for c in snap.identity_claims}
    assert facets == {"value", "self_awareness"}


def test_snapshot_identity_dedup() -> None:
    history = [
        {"identity": [{"facet": "value", "claim": "loyalty", "evidence": "ev1"}]},
        {"identity": [{"facet": "value", "claim": "loyalty", "evidence": "ev1"}]},
    ]
    snap = snapshot_from_extracted_signals_history(history)
    assert len(snap.identity_claims) == 1


def test_snapshot_identity_user_confirmed_propagates() -> None:
    history = [
        {
            "identity": [
                {
                    "facet": "value",
                    "claim": "loyalty",
                    "evidence": "ev1",
                    "user_confirmed": True,
                }
            ]
        }
    ]
    snap = snapshot_from_extracted_signals_history(history)
    assert snap.identity_claims[0].user_confirmed is True


def test_snapshot_skips_personality_without_facet_or_value() -> None:
    history = [
        {
            "personality": [
                {"facet": "interest", "value": "", "evidence": "x"},
                {"facet": "", "value": "ml", "evidence": "x"},
                {"facet": "interest", "value": "ml", "evidence": "x"},  # only this kept
            ]
        }
    ]
    snap = snapshot_from_extracted_signals_history(history)
    assert len(snap.personality) == 1


def test_snapshot_identity_helpers_match_state() -> None:
    """Spot-check the StudentSnapshot helper methods used by the validator."""
    from unipaith.ai.state import IdentityClaim, StudentSnapshot

    snap = StudentSnapshot(
        identity_claims=[
            IdentityClaim(facet="value", claim="a", evidence="e", user_confirmed=True),
            IdentityClaim(facet="belief", claim="b", evidence="e2"),
            IdentityClaim(facet="self_awareness", claim="c", evidence="e3"),
        ]
    )
    assert snap.identity_value_or_belief_count() == 2
    assert snap.has_self_awareness_moment() is True
    # Evidence-backed claims count as confirmed (user_confirmed was never wired
    # into extraction), so all three evidence-bearing claims here count.
    assert snap.confirmed_identity_claims() == 3
