"""todo 3.2 — the wrong-discipline veto.

Pure CPEF unit tests (no DB): a program in an unrelated discipline (a CS
applicant shown an MBA / law program) must be vetoed and sink in her ranking,
while an adjacent field (CS↔engineering, CS↔data-science) and unlabeled programs
pass untouched. Also pins the onboarding interest-track → canonical-field map.
"""

from unipaith.services.match.field_canon import interest_track_to_field
from unipaith.services.matching import ProgramFeatures, StudentFeatures, score

_CS_STUDENT = StudentFeatures(
    sparse={
        "education_level": "bachelors",
        "geo_must": ["USA"],
        "field_of_study": "computer_science",
    },
    embedding=None,
    profile_completeness=0.8,
)


def _program(pid: str, fields: list[str]) -> ProgramFeatures:
    return ProgramFeatures(
        program_id=pid,
        sparse={
            "target_education_level": "masters",
            "locations": ["USA"],
            "fields_offered": fields,
        },
    )


def _field_dealbreakers(prog: ProgramFeatures) -> list[dict]:
    bd = score(_CS_STUDENT, prog, cpef_enabled=True).fitness_breakdown
    return [d for d in bd["dealbreakers"] if d["key"] == "field"]


def test_unrelated_discipline_is_vetoed_and_buried():
    mba = _program("mba", ["business"])  # CS↔business not in sim table → fit 0.0
    s = score(_CS_STUDENT, mba, cpef_enabled=True)
    assert _field_dealbreakers(mba), "an MBA should trip the field deal-breaker for a CS applicant"
    assert float(s.fitness) < 0.1  # confirmed veto sinks it below clean programs


def test_related_field_is_not_vetoed():
    # CS↔engineering = 0.6 in FIELD_SIM_TABLE → above the 0.35 floor → no veto.
    assert _field_dealbreakers(_program("eng", ["engineering"])) == []
    # CS↔data_science = 0.7 → also passes.
    assert _field_dealbreakers(_program("ds", ["data_science"])) == []


def test_exact_field_passes_and_outranks_unrelated():
    cs = float(score(_CS_STUDENT, _program("cs", ["computer_science"]), cpef_enabled=True).fitness)
    mba = float(score(_CS_STUDENT, _program("mba", ["business"]), cpef_enabled=True).fitness)
    assert _field_dealbreakers(_program("cs", ["computer_science"])) == []
    assert cs > mba


def test_unlabeled_program_is_not_vetoed():
    # No fields_offered → nothing to compare → permissive (never a phantom veto).
    assert _field_dealbreakers(_program("unknown", [])) == []


def test_student_without_a_stated_field_is_not_vetoed():
    blank = StudentFeatures(
        sparse={"education_level": "bachelors"}, embedding=None, profile_completeness=0.5
    )
    bd = score(blank, _program("mba", ["business"]), cpef_enabled=True).fitness_breakdown
    assert [d for d in bd["dealbreakers"] if d["key"] == "field"] == []


def test_interest_track_to_field_mapping():
    assert interest_track_to_field("cs_data_ai") == "computer_science"
    assert interest_track_to_field("comp_engineering_robotics") == "computer_science"
    assert interest_track_to_field("business") == "business"
    assert interest_track_to_field("law_policy") == "political_science"
    assert interest_track_to_field("health") == "public_health"
    # Ambiguous / omitted tracks stay permissive (None → no field token).
    assert interest_track_to_field("arts_design") is None
    assert interest_track_to_field("performing_arts") is None
    assert interest_track_to_field(None) is None
    assert interest_track_to_field("not_a_real_track") is None
