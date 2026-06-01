"""Spec 24 — Institution Data Upload.

Covers the §13 test list: upload → validate → confirm; mapping-template reuse;
versioning + rollback; usage-scope enforcement (a marketing dataset never feeds
matching); plus the DocumentParseTriage rule-based fallback invariant.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.config import settings
from unipaith.models.institution import Institution, Program
from unipaith.models.user import User
from unipaith.services.dataset_service import DatasetService

API = "/api/v1/institutions"


async def _ensure_institution(db: AsyncSession, user: User) -> Institution:
    inst = Institution(
        admin_user_id=user.id, name="Test University", type="university", country="United States"
    )
    db.add(inst)
    await db.commit()
    return inst


async def _add_program(db: AsyncSession, inst: Institution, name: str) -> Program:
    prog = Program(institution_id=inst.id, program_name=name, degree_type="masters")
    db.add(prog)
    await db.commit()
    return prog


async def _upload(client: AsyncClient, content: str, file_name: str) -> str:
    """Mimic the browser: get a presigned URL, then 'PUT' the file. In
    S3_LOCAL_MODE the URL is a file:// path, so we write the bytes directly."""
    resp = await client.post(
        f"{API}/me/datasets/upload-url",
        json={"file_name": file_name, "content_type": "text/csv"},
    )
    assert resp.status_code == 200, resp.text
    file_ref = resp.json()["file_ref"]
    path = Path(settings.s3_local_path) / file_ref
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return file_ref


PROSPECTS_CSV = "Email,First,Last\na@x.com,Ann,Lee\nb@x.com,Bo,Ng\n"
PROSPECT_MAP = {"Email": "email", "First": "first_name", "Last": "last_name"}


@pytest.mark.asyncio
async def test_upload_validate_confirm_flow(
    institution_client: AsyncClient, db_session: AsyncSession, mock_institution_user: User
):
    await _ensure_institution(db_session, mock_institution_user)
    file_ref = await _upload(institution_client, PROSPECTS_CSV, "prospects.csv")

    # inspect → detected columns
    insp = await institution_client.post(f"{API}/me/datasets/inspect", json={"file_ref": file_ref})
    assert insp.status_code == 200
    assert set(insp.json()["columns"]) == {"Email", "First", "Last"}
    assert insp.json()["total_rows"] == 2

    # validate dry-run → clean
    val = await institution_client.post(
        f"{API}/me/datasets/validate",
        json={"dataset_type": "prospect_list", "mapping": PROSPECT_MAP, "file_ref": file_ref},
    )
    assert val.status_code == 200
    assert val.json()["validation_report"]["valid_rows"] == 2

    # confirm
    conf = await institution_client.post(
        f"{API}/me/datasets/confirm-upload",
        json={
            "name": "Spring prospects",
            "dataset_type": "prospect_list",
            "file_ref": file_ref,
            "file_name": "prospects.csv",
            "mapping": PROSPECT_MAP,
            "usage_scope": "marketing",
            "coverage_start": "2024-01-01",
        },
    )
    assert conf.status_code == 200, conf.text
    body = conf.json()
    assert body["row_count"] == 2
    assert body["version"] == 1
    assert body["status"] == "validated"
    assert body["usage_scope"] == "marketing"
    dataset_id = body["id"]

    # preview → rows + histogram
    prev = await institution_client.get(f"{API}/me/datasets/{dataset_id}/preview")
    assert prev.status_code == 200
    assert prev.json()["total_rows"] == 2
    assert "Email" in prev.json()["histogram"]

    # versions → exactly one
    vers = await institution_client.get(f"{API}/me/datasets/{dataset_id}/versions")
    assert vers.status_code == 200
    assert len(vers.json()) == 1
    assert vers.json()[0]["changes_summary"]["added"] == 2

    # export → CSV round-trip
    exp = await institution_client.get(f"{API}/me/datasets/{dataset_id}/export")
    assert exp.status_code == 200
    assert "a@x.com" in exp.text


@pytest.mark.asyncio
async def test_validation_detects_missing_and_duplicates(
    institution_client: AsyncClient, db_session: AsyncSession, mock_institution_user: User
):
    await _ensure_institution(db_session, mock_institution_user)
    csv = "Email,First\na@x.com,Ann\n,Bob\na@x.com,Ann2\n"  # row2 missing email, row3 dup
    file_ref = await _upload(institution_client, csv, "p.csv")
    val = await institution_client.post(
        f"{API}/me/datasets/validate",
        json={
            "dataset_type": "prospect_list",
            "mapping": {"Email": "email", "First": "first_name"},
            "file_ref": file_ref,
        },
    )
    report = val.json()["validation_report"]
    assert len(report["missing_required"]) == 1
    assert report["missing_required"][0]["row"] == 2
    assert len(report["duplicates"]) == 1
    assert report["duplicates"][0]["row"] == 3
    assert report["valid_rows"] == 1


@pytest.mark.asyncio
async def test_admissions_invalid_date_and_program_normalization(
    institution_client: AsyncClient, db_session: AsyncSession, mock_institution_user: User
):
    inst = await _ensure_institution(db_session, mock_institution_user)
    await _add_program(db_session, inst, "MSc Data Science")
    csv = (
        "SE,Prog,AppDate,Dec\n"
        "s1@x.com,MSc Data Science,2024-03-01,admit\n"
        "s2@x.com,MSc Data Sciece,not-a-date,reject\n"  # typo program + bad date
    )
    file_ref = await _upload(institution_client, csv, "adm.csv")
    mapping = {
        "SE": "student_email",
        "Prog": "program_name",
        "AppDate": "application_date",
        "Dec": "decision",
    }
    val = await institution_client.post(
        f"{API}/me/datasets/validate",
        json={"dataset_type": "admissions_history", "mapping": mapping, "file_ref": file_ref},
    )
    report = val.json()["validation_report"]
    assert any(e["field"] == "application_date" for e in report["invalid_dates"])
    # the typo'd program is unmappable but gets a close-match suggestion
    assert len(report["unmappable_programs"]) == 1
    assert "MSc Data Science" in report["unmappable_programs"][0]["suggestions"]
    # the correctly-named program normalizes to its id
    assert "MSc Data Science" in val.json()["normalization_map"]


@pytest.mark.asyncio
async def test_mapping_templates_reusable(
    institution_client: AsyncClient, db_session: AsyncSession, mock_institution_user: User
):
    await _ensure_institution(db_session, mock_institution_user)
    create = await institution_client.post(
        f"{API}/me/dataset-mapping-templates",
        json={
            "name": "Standard prospects",
            "dataset_type": "prospect_list",
            "column_mapping": PROSPECT_MAP,
        },
    )
    assert create.status_code == 200, create.text

    listed = await institution_client.get(
        f"{API}/me/dataset-mapping-templates", params={"type": "prospect_list"}
    )
    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert listed.json()[0]["column_mapping"] == PROSPECT_MAP

    # a second upload reuses the saved mapping verbatim
    file_ref = await _upload(institution_client, PROSPECTS_CSV, "again.csv")
    conf = await institution_client.post(
        f"{API}/me/datasets/confirm-upload",
        json={
            "name": "Reused",
            "dataset_type": "prospect_list",
            "file_ref": file_ref,
            "file_name": "again.csv",
            "mapping": listed.json()[0]["column_mapping"],
        },
    )
    assert conf.status_code == 200
    assert conf.json()["column_mapping"] == PROSPECT_MAP

    tpl_id = listed.json()[0]["id"]
    dele = await institution_client.delete(f"{API}/me/dataset-mapping-templates/{tpl_id}")
    assert dele.status_code == 204


@pytest.mark.asyncio
async def test_versioning_and_rollback(
    institution_client: AsyncClient, db_session: AsyncSession, mock_institution_user: User
):
    await _ensure_institution(db_session, mock_institution_user)
    file_ref = await _upload(institution_client, PROSPECTS_CSV, "v1.csv")
    conf = await institution_client.post(
        f"{API}/me/datasets/confirm-upload",
        json={
            "name": "Versioned",
            "dataset_type": "prospect_list",
            "file_ref": file_ref,
            "file_name": "v1.csv",
            "mapping": PROSPECT_MAP,
        },
    )
    dataset_id = conf.json()["id"]
    assert conf.json()["row_count"] == 2

    # replace with a 3-row file
    csv2 = PROSPECTS_CSV + "c@x.com,Cy,Lo\n"
    ref2 = await _upload(institution_client, csv2, "v2.csv")
    rep = await institution_client.post(
        f"{API}/me/datasets/{dataset_id}/replace",
        json={"file_ref": ref2, "file_name": "v2.csv", "mapping": PROSPECT_MAP},
    )
    assert rep.status_code == 200, rep.text
    assert rep.json()["row_count"] == 3
    assert rep.json()["version"] == 2

    vers = await institution_client.get(f"{API}/me/datasets/{dataset_id}/versions")
    assert len(vers.json()) == 2

    # rollback to v1 → 2 rows again, version bumps to 3
    rb = await institution_client.post(f"{API}/me/datasets/{dataset_id}/versions/1/rollback")
    assert rb.status_code == 200, rb.text
    assert rb.json()["row_count"] == 2
    assert rb.json()["version"] == 3


@pytest.mark.asyncio
async def test_usage_scope_enforcement_marketing_never_feeds_matching(
    institution_client: AsyncClient, db_session: AsyncSession, mock_institution_user: User
):
    """Spec 24 §13 — a marketing-scope dataset must never be returned for the
    matching purpose. (``institution_client`` persists the admin user.)"""
    inst = await _ensure_institution(db_session, mock_institution_user)
    dsvc = DatasetService(db_session)

    # seed two datasets directly (scope is the thing under test)
    from unipaith.models.institution import InstitutionDataset

    mkt = InstitutionDataset(
        institution_id=inst.id,
        dataset_name="Mkt",
        dataset_type="prospect_list",
        s3_key="k1",
        file_name="m.csv",
        usage_scope="marketing",
        uploaded_by=mock_institution_user.id,
    )
    adm = InstitutionDataset(
        institution_id=inst.id,
        dataset_name="Adm",
        dataset_type="admissions_history",
        s3_key="k2",
        file_name="a.csv",
        usage_scope="admissions",
        uploaded_by=mock_institution_user.id,
    )
    db_session.add_all([mkt, adm])
    await db_session.commit()

    matching = await dsvc.list_for_purpose(inst.id, "matching")
    names = {d.dataset_name for d in matching}
    assert "Adm" in names
    assert "Mkt" not in names  # the invariant
    assert dsvc.scope_allows(adm, "matching") is True
    assert dsvc.scope_allows(mkt, "matching") is False


@pytest.mark.asyncio
async def test_triage_falls_back_to_rule_based(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_institution_user: User,
    monkeypatch,
):
    """With the triage flag on but the agent failing, confirm-upload must still
    succeed with the deterministic rule-based report (never 5xx)."""
    await _ensure_institution(db_session, mock_institution_user)
    monkeypatch.setattr(settings, "ai_data_parse_triage_v2_enabled", True)

    async def _boom(**kwargs):
        raise RuntimeError("provider down")

    monkeypatch.setattr("unipaith.ai.document_parse_triage.triage_parse", _boom)

    file_ref = await _upload(institution_client, PROSPECTS_CSV, "t.csv")
    conf = await institution_client.post(
        f"{API}/me/datasets/confirm-upload",
        json={
            "name": "Triaged",
            "dataset_type": "prospect_list",
            "file_ref": file_ref,
            "file_name": "t.csv",
            "mapping": PROSPECT_MAP,
        },
    )
    assert conf.status_code == 200, conf.text
    assert conf.json()["validation_errors"]["source"] == "rule_based"


@pytest.mark.asyncio
async def test_delete_dataset_with_versions(
    institution_client: AsyncClient, db_session: AsyncSession, mock_institution_user: User
):
    """Deleting a dataset that has version snapshots must not lazy-load the
    versions relationship (async) — it 204s and the dataset is gone."""
    await _ensure_institution(db_session, mock_institution_user)
    file_ref = await _upload(institution_client, PROSPECTS_CSV, "del.csv")
    conf = await institution_client.post(
        f"{API}/me/datasets/confirm-upload",
        json={
            "name": "To delete",
            "dataset_type": "prospect_list",
            "file_ref": file_ref,
            "file_name": "del.csv",
            "mapping": PROSPECT_MAP,
        },
    )
    dataset_id = conf.json()["id"]
    # add a second version so the relationship is non-empty
    ref2 = await _upload(institution_client, PROSPECTS_CSV + "c@x.com,Cy,Lo\n", "del2.csv")
    await institution_client.post(
        f"{API}/me/datasets/{dataset_id}/replace",
        json={"file_ref": ref2, "file_name": "del2.csv", "mapping": PROSPECT_MAP},
    )

    dele = await institution_client.delete(f"{API}/me/datasets/{dataset_id}")
    assert dele.status_code == 204, dele.text
    gone = await institution_client.get(f"{API}/me/datasets/{dataset_id}")
    assert gone.status_code == 404
