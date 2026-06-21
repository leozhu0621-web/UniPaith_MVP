"""Student-side coverage in soft_align's tag overlaps.

`soft_align` is the s→p (student's-view) signal: "how much of what the student
cares about does this program offer." Its interest/career/value sub-scores
therefore measure STUDENT-SIDE coverage — the fraction of the student's tags
the program covers — NOT symmetric Jaccard. A program that covers ALL of a
student's interests is a full fit on that dimension and must NOT be penalized
for *also* offering themes the student didn't ask about (the old union-
normalized Jaccard penalized exactly that, biasing against broad programs).

This mirrors the social-preference fix (`_pref_satisfaction`): a met preference
is never diluted by the program's unrelated features.

Pure — no DB.
"""

import pytest

from unipaith.services.matching import (
    ProgramFeatures,
    StudentFeatures,
    _tag_coverage,
    soft_align,
)


def test_tag_coverage_full_when_program_covers_all_student_tags() -> None:
    # Every student tag is present in the program → full coverage, regardless of
    # how many extra tags the program lists.
    assert _tag_coverage(["ml"], ["ml"]) == 1.0
    assert _tag_coverage(["ml"], ["ml", "philosophy", "art"]) == 1.0


def test_tag_coverage_partial_when_some_student_tags_unmet() -> None:
    # 1 of the student's 2 tags covered → 0.5 (only the student's tags count).
    assert _tag_coverage(["ml", "philosophy"], ["ml"]) == pytest.approx(0.5)


def test_tag_coverage_zero_when_disjoint_or_no_student_tags() -> None:
    assert _tag_coverage(["ml"], ["biology"]) == 0.0
    assert _tag_coverage([], ["ml"]) == 0.0  # no interest expressed → neutral 0
    assert _tag_coverage([], []) == 0.0


def test_broad_program_not_penalized_vs_narrow_on_covered_interests() -> None:
    # A student interested only in ML, matched against two programs that BOTH
    # fully serve that interest: a narrow ML-only program and a broad program
    # that offers ML plus unrelated themes. The broad program covers 100% of the
    # student's interest, so its themes fit must EQUAL the narrow program's — not
    # be dragged down for being broader (the old Jaccard scored it ~1/3).
    student = StudentFeatures(
        sparse={"interest_themes": ["machine_learning"], "career_arcs": ["ml_research"]}
    )
    narrow = ProgramFeatures(
        program_id="narrow",
        sparse={"interest_themes": ["machine_learning"], "career_arcs": ["ml_research"]},
    )
    broad = ProgramFeatures(
        program_id="broad",
        sparse={
            "interest_themes": ["machine_learning", "philosophy", "art_history"],
            "career_arcs": ["ml_research"],
        },
    )
    assert soft_align(student, broad) == pytest.approx(soft_align(student, narrow))
    # And both fully cover the student's interest + career → a strong score.
    assert soft_align(student, narrow) > 0.5
