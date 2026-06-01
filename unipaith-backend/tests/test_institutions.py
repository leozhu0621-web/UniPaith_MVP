import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.institution import Institution
from unipaith.models.user import User


async def _ensure_institution(db: AsyncSession, user: User) -> Institution:
    """Idempotent — safe when a prior test in the same session already created one."""
    result = await db.execute(select(Institution).where(Institution.admin_user_id == user.id))
    existing = result.scalar_one_or_none()
    if existing:
        return existing
    inst = Institution(
        admin_user_id=user.id,
        name="Test University",
        type="university",
        country="United States",
    )
    db.add(inst)
    await db.commit()
    await db.refresh(inst)
    return inst


@pytest.mark.asyncio
async def test_create_institution(institution_client: AsyncClient):
    resp = await institution_client.post(
        "/api/v1/institutions/me",
        json={
            "name": "New University",
            "type": "university",
            "country": "United States",
        },
    )
    assert resp.status_code == 201
    assert resp.json()["name"] == "New University"


@pytest.mark.asyncio
async def test_create_institution_duplicate(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_institution_user: User,
):
    await _ensure_institution(db_session, mock_institution_user)
    resp = await institution_client.post(
        "/api/v1/institutions/me",
        json={
            "name": "Another",
            "type": "college",
            "country": "UK",
        },
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_get_institution(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_institution_user: User,
):
    await _ensure_institution(db_session, mock_institution_user)
    resp = await institution_client.get("/api/v1/institutions/me")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Test University"


@pytest.mark.asyncio
async def test_update_institution(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_institution_user: User,
):
    await _ensure_institution(db_session, mock_institution_user)
    resp = await institution_client.put(
        "/api/v1/institutions/me",
        json={
            "city": "Boston",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["city"] == "Boston"
    assert resp.json()["name"] == "Test University"


@pytest.mark.asyncio
async def test_student_cannot_access_institutions(student_client: AsyncClient):
    resp = await student_client.get("/api/v1/institutions/me")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_update_institution_profile_jsonb_roundtrip(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_institution_user: User,
):
    """Spec 22 §3 / G-I1 — the six profile JSONB dicts the guided editor writes
    persist and round-trip exactly through PUT + GET /institutions/me."""
    await _ensure_institution(db_session, mock_institution_user)
    payload = {
        "accreditation": "Middle States Commission on Higher Education",
        "social_links": {"twitter": "https://x.com/foo"},
        "inquiry_routing": {"general": "admissions@foo.edu", "financial_aid": "finaid@foo.edu"},
        "support_services": {"tutoring": {"name": "Tutoring", "url": "https://foo.edu/tutoring"}},
        "policies": {
            "transfer_credit": {"summary": "Up to 60 credits.", "url": "https://foo.edu/transfer"}
        },
        "international_info": {"toefl_min": 100, "supported_visas": ["F-1", "J-1"]},
        "school_outcomes": {"employed_or_continuing_ed": 0.94, "top_employers": ["Google"]},
    }
    resp = await institution_client.put("/api/v1/institutions/me", json=payload)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["ranking_data"]["accreditor"] == payload["accreditation"]
    for key, value in payload.items():
        if key == "accreditation":
            continue
        assert body[key] == value, key

    # Persisted — a fresh GET returns the same nested shapes.
    got = (await institution_client.get("/api/v1/institutions/me")).json()
    assert got["ranking_data"]["accreditor"] == payload["accreditation"]
    assert got["support_services"]["tutoring"]["url"] == "https://foo.edu/tutoring"
    assert got["international_info"]["supported_visas"] == ["F-1", "J-1"]
    assert got["school_outcomes"]["employed_or_continuing_ed"] == 0.94


@pytest.mark.asyncio
async def test_student_submits_institution_level_inquiry(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_institution_user: User,
):
    """Spec 22 §7 — the public/auth "Request info" CTA submits an institution-level
    inquiry (no program_id) via POST /institutions/inquiries."""
    db_session.add(mock_institution_user)
    inst = await _ensure_institution(db_session, mock_institution_user)

    resp = await student_client.post(
        "/api/v1/institutions/inquiries",
        json={
            "institution_id": str(inst.id),
            "subject": "Tell me more",
            "message": "Is there financial aid?",
            "inquiry_type": "general",
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["program_id"] is None
    assert body["inquiry_type"] == "general"
    assert body["subject"] == "Tell me more"


# --- Programs ---


@pytest.mark.asyncio
async def test_create_program_draft(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_institution_user: User,
):
    await _ensure_institution(db_session, mock_institution_user)
    resp = await institution_client.post(
        "/api/v1/institutions/me/programs",
        json={
            "program_name": "MS in CS",
            "degree_type": "masters",
        },
    )
    assert resp.status_code == 201
    assert resp.json()["is_published"] is False


@pytest.mark.asyncio
async def test_publish_program_missing_fields(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_institution_user: User,
):
    await _ensure_institution(db_session, mock_institution_user)
    create_resp = await institution_client.post(
        "/api/v1/institutions/me/programs",
        json={
            "program_name": "MS in CS",
            "degree_type": "masters",
        },
    )
    pid = create_resp.json()["id"]
    resp = await institution_client.post(f"/api/v1/institutions/me/programs/{pid}/publish")
    # Spec 23 §6 — structured 422 so the editor can list missing fields and
    # scroll to each section. (Was a flat 400 before the guided editor.)
    assert resp.status_code == 422
    detail = resp.json()["detail"]
    assert "missing required fields" in detail["message"].lower()
    missing = {m["field"] for m in detail["missing_fields"]}
    # No description and no cost signal → both flagged, each tagged with its section.
    assert "description_text" in missing
    assert all({"field", "section", "message"} <= set(m) for m in detail["missing_fields"])


@pytest.mark.asyncio
async def test_publish_program_success(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_institution_user: User,
):
    await _ensure_institution(db_session, mock_institution_user)
    create_resp = await institution_client.post(
        "/api/v1/institutions/me/programs",
        json={
            "program_name": "MS in CS",
            "degree_type": "masters",
            "description_text": "A great program.",
            "tuition": 40000,
        },
    )
    pid = create_resp.json()["id"]
    resp = await institution_client.post(f"/api/v1/institutions/me/programs/{pid}/publish")
    assert resp.status_code == 200
    assert resp.json()["is_published"] is True


@pytest.mark.asyncio
async def test_unpublish_program(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_institution_user: User,
):
    await _ensure_institution(db_session, mock_institution_user)
    create_resp = await institution_client.post(
        "/api/v1/institutions/me/programs",
        json={
            "program_name": "MS in CS",
            "degree_type": "masters",
            "description_text": "A great program.",
            "tuition": 40000,
        },
    )
    pid = create_resp.json()["id"]
    await institution_client.post(f"/api/v1/institutions/me/programs/{pid}/publish")
    resp = await institution_client.post(f"/api/v1/institutions/me/programs/{pid}/unpublish")
    assert resp.status_code == 200
    assert resp.json()["is_published"] is False


@pytest.mark.asyncio
async def test_delete_program_no_apps(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_institution_user: User,
):
    await _ensure_institution(db_session, mock_institution_user)
    create_resp = await institution_client.post(
        "/api/v1/institutions/me/programs",
        json={
            "program_name": "MS in CS",
            "degree_type": "masters",
        },
    )
    pid = create_resp.json()["id"]
    resp = await institution_client.delete(f"/api/v1/institutions/me/programs/{pid}")
    assert resp.status_code == 204


# --- Public Search ---


@pytest.mark.asyncio
async def test_public_search_only_published(
    institution_client: AsyncClient,
    client: AsyncClient,
    db_session: AsyncSession,
    mock_institution_user: User,
):
    await _ensure_institution(db_session, mock_institution_user)
    await institution_client.post(
        "/api/v1/institutions/me/programs",
        json={
            "program_name": "Draft Program",
            "degree_type": "masters",
        },
    )
    create_resp = await institution_client.post(
        "/api/v1/institutions/me/programs",
        json={
            "program_name": "Published Program",
            "degree_type": "masters",
            "description_text": "Visible.",
            "tuition": 30000,
        },
    )
    pid = create_resp.json()["id"]
    await institution_client.post(f"/api/v1/institutions/me/programs/{pid}/publish")

    resp = await client.get("/api/v1/programs")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    assert items[0]["program_name"] == "Published Program"


@pytest.mark.asyncio
async def test_public_search_filter_by_degree(
    institution_client: AsyncClient,
    client: AsyncClient,
    db_session: AsyncSession,
    mock_institution_user: User,
):
    await _ensure_institution(db_session, mock_institution_user)
    for name, deg in [("MS CS", "masters"), ("PhD CS", "phd")]:
        r = await institution_client.post(
            "/api/v1/institutions/me/programs",
            json={
                "program_name": name,
                "degree_type": deg,
                "description_text": "test",
                "tuition": 10000,
            },
        )
        await institution_client.post(f"/api/v1/institutions/me/programs/{r.json()['id']}/publish")

    resp = await client.get("/api/v1/programs?degree_type=phd")
    assert len(resp.json()["items"]) == 1
    assert resp.json()["items"][0]["degree_type"] == "phd"


# --- Segments ---


@pytest.mark.asyncio
async def test_segment_crud(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_institution_user: User,
):
    await _ensure_institution(db_session, mock_institution_user)

    resp = await institution_client.post(
        "/api/v1/institutions/me/segments",
        json={
            "segment_name": "STEM students",
            "criteria": {"gpa_min": 3.5},
        },
    )
    assert resp.status_code == 201
    sid = resp.json()["id"]

    resp = await institution_client.get("/api/v1/institutions/me/segments")
    assert len(resp.json()) == 1

    resp = await institution_client.put(
        f"/api/v1/institutions/me/segments/{sid}",
        json={
            "segment_name": "Top STEM",
        },
    )
    assert resp.json()["segment_name"] == "Top STEM"

    resp = await institution_client.delete(f"/api/v1/institutions/me/segments/{sid}")
    assert resp.status_code == 204


# --- Spec 23 · Program editor: version, optimistic lock, blast-radius ---


async def _create_min_program(client: AsyncClient, **overrides) -> dict:
    payload = {"program_name": "MS in CS", "degree_type": "masters", **overrides}
    resp = await client.post("/api/v1/institutions/me/programs", json=payload)
    assert resp.status_code == 201
    return resp.json()


@pytest.mark.asyncio
async def test_program_response_exposes_version_and_status(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_institution_user: User,
):
    await _ensure_institution(db_session, mock_institution_user)
    created = await _create_min_program(institution_client)
    # Spec 23 §5 — version + derived status surfaced for the editor.
    assert created["version"] == 1
    assert created["feature_version"] == 1
    assert created["status"] == "draft"
    assert created["applications_count"] == 0


@pytest.mark.asyncio
async def test_program_version_increments_on_save(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_institution_user: User,
):
    await _ensure_institution(db_session, mock_institution_user)
    pid = (await _create_min_program(institution_client))["id"]
    r1 = await institution_client.put(
        f"/api/v1/institutions/me/programs/{pid}",
        json={"description_text": "v2"},
    )
    assert r1.status_code == 200
    assert r1.json()["version"] == 2
    r2 = await institution_client.put(
        f"/api/v1/institutions/me/programs/{pid}",
        json={"description_text": "v3"},
    )
    assert r2.json()["version"] == 3


@pytest.mark.asyncio
async def test_optimistic_lock_conflict(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_institution_user: User,
):
    await _ensure_institution(db_session, mock_institution_user)
    pid = (await _create_min_program(institution_client))["id"]
    # Bump to v2 so a stale expected_version=1 is now out of date.
    await institution_client.put(
        f"/api/v1/institutions/me/programs/{pid}",
        json={"description_text": "v2"},
    )
    stale = await institution_client.put(
        f"/api/v1/institutions/me/programs/{pid}",
        json={"description_text": "from a stale tab", "expected_version": 1},
    )
    assert stale.status_code == 409
    # A correct expected_version (2) succeeds.
    fresh = await institution_client.put(
        f"/api/v1/institutions/me/programs/{pid}",
        json={"description_text": "ok", "expected_version": 2},
    )
    assert fresh.status_code == 200
    assert fresh.json()["version"] == 3


@pytest.mark.asyncio
async def test_publish_then_create_and_publish_flow(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_institution_user: User,
):
    # Spec 23 §10 — create → publish; draft never appears publicly until then.
    await _ensure_institution(db_session, mock_institution_user)
    created = await _create_min_program(
        institution_client, description_text="A great program.", tuition=40000
    )
    pid = created["id"]
    pub = await institution_client.post(f"/api/v1/institutions/me/programs/{pid}/publish")
    assert pub.status_code == 200
    assert pub.json()["status"] == "published"


@pytest.mark.asyncio
async def test_publish_validation_lists_sections(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_institution_user: User,
):
    await _ensure_institution(db_session, mock_institution_user)
    # Has a name+degree (identity ok) but no description and no cost signal.
    pid = (await _create_min_program(institution_client))["id"]
    resp = await institution_client.post(f"/api/v1/institutions/me/programs/{pid}/publish")
    assert resp.status_code == 422
    sections = {m["section"] for m in resp.json()["detail"]["missing_fields"]}
    assert "overview" in sections  # description_text
    assert "costs" in sections  # no tuition/deadline/cost_data/intake_rounds


@pytest.mark.asyncio
async def test_draft_program_not_publicly_visible(
    institution_client: AsyncClient,
    client: AsyncClient,
    db_session: AsyncSession,
    mock_institution_user: User,
):
    # Spec 23 §10 — draft never appears on the public program endpoint.
    await _ensure_institution(db_session, mock_institution_user)
    pid = (await _create_min_program(institution_client))["id"]
    resp = await client.get(f"/api/v1/programs/{pid}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_promotion_categories_round_trip(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_institution_user: User,
):
    await _ensure_institution(db_session, mock_institution_user)
    pid = (await _create_min_program(institution_client))["id"]
    r = await institution_client.put(
        f"/api/v1/institutions/me/programs/{pid}",
        json={"promotion_categories": ["computer_science", "data_science"]},
    )
    assert r.status_code == 200
    assert r.json()["promotion_categories"] == ["computer_science", "data_science"]
