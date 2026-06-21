"""Surgical coverage fix (audit Rank 12).

The coverage damp must NOT be capped by PROGRAM authority (c_program): folding
c_program into coverage double-counts confidence (``inner`` already carries the
two-sided product c_student×c_program) and structurally caps derived/unclaimed
programs — the same class as the historic cosine-0.55 cap.

But coverage MUST still rise with how well we know the STUDENT (c_student): that
dependence carries the central "deeper profile → sharper match" property
(test_ai_structure_cohort). So coverage = evidence breadth gated by c_student
ONLY. Pure, no DB.
"""

from unipaith.services.matching import ProgramFeatures, StudentFeatures, cpef


def _cov(student: StudentFeatures, program: ProgramFeatures) -> float:
    return cpef(student, program)[1]["coverage"]


def test_coverage_not_capped_by_program_authority() -> None:
    # Same student, same signals present, different program authority → SAME
    # coverage. Authority belongs in `inner`, not the coverage damp.
    student = StudentFeatures(
        sparse={"interest_themes": ["ml"], "needs_signals": {"funding": 1.0}},
        extractor_quality=0.7,
    )
    attrs = {"interest_themes": ["ml"], "support_signals": {"funding": 1.0}}
    claimed = ProgramFeatures(program_id="c", sparse=attrs, data_completeness=0.9)
    derived = ProgramFeatures(program_id="d", sparse=attrs, data_completeness=0.4)
    assert _cov(student, claimed) == _cov(student, derived)


def test_coverage_still_rises_with_student_depth() -> None:
    # Deeper student profile (higher c_student) → higher coverage for the same
    # present signals. This is what carries "deeper profile → sharper match".
    attrs = {"interest_themes": ["ml"], "support_signals": {"funding": 1.0}}
    program = ProgramFeatures(program_id="p", sparse=attrs, data_completeness=0.5)
    thin = StudentFeatures(
        sparse={"interest_themes": ["ml"], "needs_signals": {"funding": 1.0}},
        extractor_quality=0.45,
    )
    deep = StudentFeatures(
        sparse={"interest_themes": ["ml"], "needs_signals": {"funding": 1.0}},
        extractor_quality=0.93,
    )
    assert _cov(deep, program) > _cov(thin, program)


def test_coverage_rises_with_more_present_dimensions() -> None:
    # Breadth still matters: more present signals → higher coverage.
    student = StudentFeatures(
        sparse={
            "interest_themes": ["ml"],
            "needs_signals": {"funding": 1.0},
            "field_of_study": "data_science",
            "gpa": 3.6,
        },
        extractor_quality=0.7,
    )
    thin_prog = ProgramFeatures(program_id="thin", sparse={"interest_themes": ["ml"]})
    broad_prog = ProgramFeatures(
        program_id="broad",
        sparse={
            "interest_themes": ["ml"],
            "support_signals": {"funding": 1.0},
            "fields_offered": ["data_science"],
            "pref_min_gpa": 3.0,
        },
    )
    assert _cov(student, broad_prog) > _cov(student, thin_prog)


def test_derived_program_fitness_rises_vs_old_cap() -> None:
    # The founder's goal: a derived program (low authority) is no longer
    # structurally capped on coverage, so its CPEF value rises relative to the
    # claimed one shrinking the (coverage-driven) gap — while claimed still leads
    # via `inner` (which keeps the full two-sided confidence).
    student = StudentFeatures(
        sparse={"interest_themes": ["ml"], "needs_signals": {"funding": 1.0}},
        extractor_quality=0.7,
    )
    attrs = {"interest_themes": ["ml"], "support_signals": {"funding": 1.0}}
    claimed = cpef(student, ProgramFeatures(program_id="c", sparse=attrs, data_completeness=0.9))[0]
    derived = cpef(student, ProgramFeatures(program_id="d", sparse=attrs, data_completeness=0.4))[0]
    # claimed still >= derived (inner carries authority), but both are real scores
    assert claimed >= derived > 0.0
