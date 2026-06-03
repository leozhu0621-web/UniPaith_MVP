"""Spec 69 §2 — the `training` usage-scope consent gate + program_catalog type.

The single dataset-level gate `66`/`67` read to decide training eligibility:
training is a strict, explicit opt-in (never folded into `all`), and the
institution's no-training tier (46 §9) hard-blocks it. Pure functions — no DB.
"""

from __future__ import annotations

from unipaith.services.dataset_upload_service import (
    REQUIRED_FIELDS,
    TRAINING_CONSUMER,
    dataset_eligible_for_training,
    dataset_used_by,
)


def test_training_scope_maps_to_model_improvement():
    assert TRAINING_CONSUMER == "model_improvement"
    assert dataset_used_by("training") == ["model_improvement"]


def test_ops_scopes_never_admit_training():
    # Customer-data / model-improvement separation (67 §3): ops scopes — incl.
    # `all` — must NOT silently map to model training.
    for scope in ("marketing", "admissions", "analytics", "all", None, "unknown"):
        assert TRAINING_CONSUMER not in dataset_used_by(scope)


def test_eligible_when_training_scope_and_tier_allows():
    assert dataset_eligible_for_training("training", None) is True
    assert dataset_eligible_for_training("training", {"no_training_tier": False}) is True


def test_no_training_tier_hard_blocks():
    # The institution opted out (46 §9) — even an explicit training scope is denied.
    assert dataset_eligible_for_training("training", {"no_training_tier": True}) is False


def test_ops_scopes_never_eligible_for_training():
    for scope in ("marketing", "admissions", "analytics", "all", None):
        assert dataset_eligible_for_training(scope, None) is False
        assert dataset_eligible_for_training(scope, {"no_training_tier": False}) is False


def test_program_catalog_dataset_type_registered():
    assert "program_catalog" in REQUIRED_FIELDS
    assert REQUIRED_FIELDS["program_catalog"] == ["program_name", "degree_type"]
