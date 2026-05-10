"""Phase B1 — Program-side feature builder tests."""

from __future__ import annotations

from unipaith.services.program_features import (
    ProgramRow,
    estimate_data_completeness,
    features_from_row,
)


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
