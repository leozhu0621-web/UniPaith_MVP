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
