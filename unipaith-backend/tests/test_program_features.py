"""Phase B1 — Program-side feature builder tests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from unipaith.services.program_features import (
    ProgramRow,
    estimate_data_completeness,
    features_from_row,
    program_row_from_orm,
)


@dataclass
class _StubProgram:
    """Duck-typed stand-in for unipaith.models.institution.Program.

    program_row_from_orm reads attributes with getattr(), so a
    dataclass with the right field names is enough to exercise the
    projection without touching the DB."""

    id: Any
    program_name: str = ""
    description_text: str | None = None
    degree_type: str | None = None
    tuition: int | None = None
    # AI Structure round-3 typed-fit attributes (real Program columns).
    duration_months: int | None = None
    delivery_format: str | None = None
    cip_code: str | None = None
    is_claimed: bool = False
    feature_vector_sparse: dict | None = None
    institution: Any = None


def test_features_from_row_projects_basic_fields() -> None:
    row = ProgramRow(
        id="p1",
        name="MS in Computer Science",
        degree="MS-CS",
        locations=["US-NY", "US-MA"],
        tuition_usd_per_year=55000.0,
        interest_themes=["machine_learning"],
        career_arcs=["ml_research"],
        values=["intellectual_rigor"],
        social_features={"small_cohort": 0.7},
        support_signals={"alumni_network": 0.9},
        data_completeness=0.8,
    )
    f = features_from_row(row, embedding=[0.1] * 1024)
    assert f.program_id == "p1"
    # Education-level mapping: MS prefix → masters
    assert f.sparse["target_education_level"] == "masters"
    assert f.sparse["locations"] == ["US-NY", "US-MA"]
    assert f.sparse["tuition_usd_per_year"] == 55000.0
    assert f.sparse["interest_themes"] == ["machine_learning"]
    assert f.embedding is not None
    assert len(f.embedding) == 1024
    assert f.data_completeness == 0.8


def test_education_level_mapping_md_to_professional() -> None:
    row = ProgramRow(id="p1", degree="MD")
    f = features_from_row(row)
    assert f.sparse["target_education_level"] == "professional"


def test_education_level_mapping_phd_to_doctoral() -> None:
    row = ProgramRow(id="p1", degree="PhD-CS")
    f = features_from_row(row)
    assert f.sparse["target_education_level"] == "doctoral"


def test_education_level_mapping_bfa_to_bachelors() -> None:
    row = ProgramRow(id="p1", degree="BFA")
    f = features_from_row(row)
    assert f.sparse["target_education_level"] == "bachelors"


def test_education_level_mapping_unknown_returns_none() -> None:
    row = ProgramRow(id="p1", degree="Mystery-Degree")
    f = features_from_row(row)
    assert f.sparse["target_education_level"] is None


def test_education_level_mapping_no_degree_returns_none() -> None:
    row = ProgramRow(id="p1", degree=None)
    f = features_from_row(row)
    assert f.sparse["target_education_level"] is None


def test_data_completeness_clamped_to_unit() -> None:
    row = ProgramRow(id="p1", data_completeness=5.0)
    f = features_from_row(row)
    assert f.data_completeness == 1.0


def test_estimate_data_completeness_full_row() -> None:
    row = ProgramRow(
        id="p1",
        degree="MS-CS",
        locations=["US-NY"],
        tuition_usd_per_year=55000,
        interest_themes=["ml"],
        career_arcs=["ml_research"],
        values=["rigor"],
    )
    assert estimate_data_completeness(row) == 1.0


def test_estimate_data_completeness_empty_row() -> None:
    row = ProgramRow(id="p1")
    assert estimate_data_completeness(row) == 0.0


def test_estimate_data_completeness_partial_row() -> None:
    row = ProgramRow(id="p1", degree="MS-CS", locations=["US-NY"])
    assert abs(estimate_data_completeness(row) - 2 / 6) < 1e-9


# ── program_row_from_orm: ORM → ProgramRow projection ──────────────────────


def test_program_row_from_orm_basic_fields() -> None:
    """Maps the documented ORM attributes onto ProgramRow fields."""
    pid = uuid4()
    p = _StubProgram(
        id=pid,
        program_name="MS in CS",
        description_text="A great program.",
        degree_type="MS",
        tuition=55000,
    )
    row = program_row_from_orm(p)
    assert row.id == pid
    assert row.name == "MS in CS"
    assert row.description == "A great program."
    assert row.degree == "MS"
    assert row.tuition_usd_per_year == 55000.0


def test_program_row_from_orm_pulls_soft_features_from_sparse_jsonb() -> None:
    """When `feature_vector_sparse` exists, soft tags + completeness
    flow through verbatim."""
    p = _StubProgram(
        id=uuid4(),
        program_name="x",
        degree_type="MS",
        feature_vector_sparse={
            "interest_themes": ["machine_learning"],
            "career_arcs": ["research"],
            "values": ["impact"],
            "support_signals": {"alumni_network": 0.9},
            "social_features": {"small_cohort": 0.7},
            "tags": ["top10"],
            "data_completeness": 0.8,
            "locations": ["US-NY"],
            "tuition_usd_per_year": 60000.0,
        },
    )
    row = program_row_from_orm(p)
    assert row.interest_themes == ["machine_learning"]
    assert row.career_arcs == ["research"]
    assert row.values == ["impact"]
    assert row.support_signals == {"alumni_network": 0.9}
    assert row.social_features == {"small_cohort": 0.7}
    assert row.tags == ["top10"]
    assert row.data_completeness == 0.8
    # sparse fields win when both present
    assert row.locations == ["US-NY"]
    assert row.tuition_usd_per_year == 60000.0


def test_program_row_from_orm_fallback_location_to_institution_country() -> None:
    """No sparse locations → fall back to institution.country."""

    class _Inst:
        country = "US"

    p = _StubProgram(id=uuid4(), institution=_Inst())
    row = program_row_from_orm(p)
    assert row.locations == ["US"]


def test_program_row_from_orm_empty_when_no_data() -> None:
    """Bare program with no sparse / no institution → defaults."""
    p = _StubProgram(id=uuid4())
    row = program_row_from_orm(p)
    assert row.name == ""
    assert row.description == ""
    assert row.locations == []
    assert row.data_completeness == 0.5  # default


def test_program_row_from_orm_handles_missing_optional_attrs() -> None:
    """The projector should not crash on ORM rows that pre-date the
    feature_vector_sparse column (getattr defaults)."""

    class _MinimalProgram:
        id = uuid4()
        program_name = "minimal"

    row = program_row_from_orm(_MinimalProgram())
    assert row.name == "minimal"
    assert row.data_completeness == 0.5


# ── AI Structure round-3: typed-fit program-side projection (Spec 3 §3) ──────
# These assert the dormant s→p signal keys now get populated FROM REAL ORM
# COLUMNS, and stay gated (absent column → omitted key → no phantom signal).


def test_features_from_row_emits_round3_keys_when_present() -> None:
    row = ProgramRow(
        id="p",
        name="MS Data Science",
        duration_months=24,
        online_available=True,
        fields_offered=["data_science"],
        support_signals={"career_services": 0.6},
    )
    f = features_from_row(row)
    assert f.sparse["duration_months"] == 24
    assert f.sparse["online_available"] is True
    assert f.sparse["fields_offered"] == ["data_science"]
    # career_services derived from the evidence-based support_signals.
    assert f.sparse["career_services"] is True


def test_features_from_row_omits_round3_keys_when_absent() -> None:
    """A bare row injects NO phantom dimension — each gated key stays absent."""
    row = ProgramRow(id="p", name="Mystery Program")
    f = features_from_row(row)
    assert "duration_months" not in f.sparse
    assert "online_available" not in f.sparse
    assert "career_services" not in f.sparse
    # 'Mystery Program' classifies to no canonical field and there is no CIP.
    assert "fields_offered" not in f.sparse


def test_features_from_row_derives_fields_offered_from_name() -> None:
    row = ProgramRow(id="p", name="Master of Public Health")
    f = features_from_row(row)
    assert f.sparse["fields_offered"] == ["public_health"]


def test_program_row_from_orm_reads_duration_delivery_cip() -> None:
    p = _StubProgram(
        id=uuid4(),
        program_name="MS in Data Science",
        degree_type="masters",
        duration_months=24,
        delivery_format="online",
        cip_code="11.07",
    )
    row = program_row_from_orm(p)
    assert row.duration_months == 24
    assert row.online_available is True  # online delivery → available
    assert row.cip_code == "11.07"


def test_program_row_from_orm_in_person_delivery_is_not_online() -> None:
    p = _StubProgram(id=uuid4(), program_name="x", delivery_format="in_person")
    row = program_row_from_orm(p)
    assert row.online_available is False


def test_program_row_from_orm_missing_delivery_leaves_online_none() -> None:
    """No delivery_format → online_available stays None (no fabricated False that
    would falsely fail a student's online want)."""
    p = _StubProgram(id=uuid4(), program_name="x")
    row = program_row_from_orm(p)
    assert row.online_available is None


def test_program_row_from_orm_claimed_program_lifts_completeness() -> None:
    """A claimed (first-party) program gets a higher c_program floor than an
    identical unclaimed one (Spec 2 claim hinge)."""
    claimed = _StubProgram(id=uuid4(), program_name="x", is_claimed=True)
    unclaimed = _StubProgram(id=uuid4(), program_name="x", is_claimed=False)
    assert program_row_from_orm(claimed).data_completeness >= 0.9
    assert program_row_from_orm(unclaimed).data_completeness < 0.9


def test_program_row_from_orm_fields_offered_from_cip_when_name_unclassified() -> None:
    p = _StubProgram(id=uuid4(), program_name="Program 7", cip_code="11.01")
    row = program_row_from_orm(p)
    f = features_from_row(row)
    # name doesn't classify; CIP family 11 → computer_science fallback.
    assert f.sparse["fields_offered"] == ["computer_science"]
