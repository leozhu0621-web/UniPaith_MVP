"""Spec 65 §3 — deterministic program featurizer fills the empty program side.

The fix for the #2 prototype-smell (`64` §1.2): the matcher's program-side
soft features were always empty (phantom `feature_vector_sparse`), so `soft_align`
was dead. These derive vocabulary-aligned tags from a program's real CIP/field/
degree/description — grounded (no fabrication), and proven to make `soft_align`
non-zero for a matched field. Pure functions — no DB.
"""

from __future__ import annotations

from types import SimpleNamespace

from unipaith.ai.tools.feature_schema import (
    CAREER_ARCS,
    INTEREST_THEMES,
    NEED_SIGNAL_TAGS,
    VALUE_TAGS,
)
from unipaith.services.matching import ProgramFeatures, StudentFeatures, soft_align
from unipaith.services.program_features import program_row_from_orm
from unipaith.services.program_featurizer import (
    featurize_program,
    soft_feature_completeness,
)

_VOCAB = {
    "interest_themes": set(INTEREST_THEMES),
    "career_arcs": set(CAREER_ARCS),
    "values": set(VALUE_TAGS),
    "support_signals": set(NEED_SIGNAL_TAGS),
}


def _assert_in_vocab(sparse: dict) -> None:
    for axis, allowed in _VOCAB.items():
        for tag in sparse.get(axis, []):
            assert tag in allowed, f"{tag!r} not in {axis} vocabulary"


def test_featurize_cs_program():
    f = featurize_program(cip_code="11.0701", name="Computer Science", degree_type="masters")
    assert "machine_learning" in f["interest_themes"]
    assert "data_analysis" in f["interest_themes"]
    assert "software_engineering" in f["career_arcs"]
    _assert_in_vocab(f)


def test_featurize_doctoral_implies_research_support():
    f = featurize_program(cip_code="26.0101", name="Biology", degree_type="doctoral")
    # A doctoral program is real evidence of a research opportunity (§3).
    assert f["support_signals"].get("research_opportunities", 0) >= 0.8


def test_featurize_support_signals_are_evidence_based():
    with_career = featurize_program(
        cip_code="52.0201",
        name="MBA",
        degree_type="masters",
        description="Strong career placement.",
    )
    assert "career_services" in with_career["support_signals"]
    # No keyword, no degree evidence → no fabricated support signal.
    without = featurize_program(cip_code="52.0201", name="MBA", degree_type="masters")
    assert without["support_signals"] == {}


def test_featurize_grounded_no_fabrication():
    # No CIP and no keywords → nothing invented.
    f = featurize_program(cip_code=None, name="", description="")
    assert f["interest_themes"] == []
    assert f["career_arcs"] == []
    assert f["support_signals"] == {}
    assert soft_feature_completeness(f) == 0.0


def test_program_row_derives_features_without_stored_vector():
    # An ORM-like program with a real CIP but no feature_vector_sparse column.
    prog = SimpleNamespace(
        id="p1",
        program_name="Computer Science",
        description_text="Machine learning and data systems.",
        degree_type="masters",
        cip_code="11.0701",
        tuition=55000,
        feature_vector_sparse=None,
    )
    row = program_row_from_orm(prog)
    assert "machine_learning" in row.interest_themes  # no longer empty
    assert "software_engineering" in row.career_arcs
    assert row.data_completeness > 0.0


def test_soft_align_nonzero_for_matched_field():
    """The actual fix: a CS student vs a CS program now scores > 0, and beats a
    mismatched field — previously both were 0 (empty program features)."""
    student = StudentFeatures(
        sparse={
            "interest_themes": ["machine_learning", "data_analysis"],
            "career_arcs": ["software_engineering"],
            "values": ["intellectual_rigor"],
            "social_prefs": {},
        }
    )
    cs = ProgramFeatures(
        program_id="cs",
        sparse=featurize_program(
            cip_code="11.0701", name="Computer Science", degree_type="masters"
        ),
    )
    history = ProgramFeatures(
        program_id="hist",
        sparse=featurize_program(cip_code="54.0101", name="History", degree_type="masters"),
    )
    cs_score = soft_align(student, cs)
    hist_score = soft_align(student, history)
    assert cs_score > 0.0  # the dead term is alive
    assert cs_score > hist_score  # and discriminates field fit
