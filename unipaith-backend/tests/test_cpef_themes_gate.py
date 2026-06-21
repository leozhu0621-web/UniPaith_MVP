"""The CPEF `themes` signal is gated on the student expressing soft preferences.

`themes` (interest/career/value tag overlap + social prefs) used to be appended
unconditionally — so a student who expressed NO soft tags got a phantom themes≈0
dimension injected on EVERY program, depressing fitness and inflating coverage
with a known-and-failed dimension the student never actually expressed. It is now
gated exactly like the other optional signals (field/time/flexibility/support):
absent attribute → no phantom dimension. Pure, no DB.
"""

from unipaith.services.match.params import DEFAULT_PARAMS
from unipaith.services.matching import (
    ProgramFeatures,
    StudentFeatures,
    _build_cpef_signals,
)


def _keys(student: StudentFeatures, program: ProgramFeatures) -> set[str]:
    signals, _db, _w = _build_cpef_signals(student, program, DEFAULT_PARAMS)
    return {s["key"] for s in signals}


def test_themes_gated_when_student_has_no_soft_tags() -> None:
    student = StudentFeatures(sparse={"education_level": "bachelors", "gpa": 3.5})
    program = ProgramFeatures(program_id="p", sparse={"interest_themes": ["ml"]})
    assert "themes" not in _keys(student, program)


def test_themes_present_with_interest_tags() -> None:
    student = StudentFeatures(sparse={"interest_themes": ["ml"]})
    program = ProgramFeatures(program_id="p", sparse={"interest_themes": ["ml"]})
    assert "themes" in _keys(student, program)


def test_themes_present_with_career_or_value_tags() -> None:
    by_career = StudentFeatures(sparse={"career_arcs": ["ml_research"]})
    by_value = StudentFeatures(sparse={"values": ["impact"]})
    program = ProgramFeatures(program_id="p", sparse={"interest_themes": ["ml"]})
    assert "themes" in _keys(by_career, program)
    assert "themes" in _keys(by_value, program)


def test_themes_present_with_only_social_prefs() -> None:
    student = StudentFeatures(sparse={"social_prefs": {"urban": 1.0}})
    program = ProgramFeatures(program_id="p", sparse={"social_features": {"urban": 1.0}})
    assert "themes" in _keys(student, program)
