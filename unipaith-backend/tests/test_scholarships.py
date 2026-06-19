"""Scholarships backend — Spec 2026-06-14 (Resources › Financial).

Covers: keyword / level / award-type search; pagination + total; the
``/scholarships`` + ``/scholarships/matches`` endpoint shapes; auth (unauth →
401/403); idempotent seed-upsert by external_id; and ``matches_for_student``
filtering by the student's derived level.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from scripts.seed_scholarships import upsert_rows
from unipaith.models.scholarship import Scholarship
from unipaith.models.strategy import StudentStrategy
from unipaith.models.student import StudentProfile
from unipaith.models.user import User
from unipaith.services.scholarship_service import ScholarshipService


async def _seed_rows(db: AsyncSession) -> None:
    """Four distinct rows spanning levels + award types."""
    db.add_all(
        [
            Scholarship(
                external_id="1001",
                name="Engineering Excellence Award",
                organization="Builders Foundation",
                purpose="Support undergraduate engineering students.",
                level_of_study="Bachelor's Degree",
                award_type="Scholarship",
                award_amount="$1,000 $5,000",
                deadline="November",
                url="https://example.org/1001",
            ),
            Scholarship(
                external_id="1002",
                name="Graduate Research Fellowship",
                organization="Science Trust",
                purpose="Fund graduate research in the sciences.",
                level_of_study="Graduate Degree",
                award_type="Fellowship",
                award_amount="$20,000",
                deadline="March",
                url="https://example.org/1002",
            ),
            Scholarship(
                external_id="1003",
                name="Community Arts Grant",
                organization="Arts Council",
                purpose="Grants for visual and performing arts.",
                level_of_study="Bachelor's Degree Graduate Degree",
                award_type="Grant",
                award_amount="$2,500",
                deadline="June",
                url="https://example.org/1003",
            ),
            Scholarship(
                external_id="1004",
                name="Future Builders Engineering Prize",
                organization="Makers Guild",
                purpose="Recognize engineering capstone projects.",
                level_of_study="Bachelor's Degree",
                award_type="Prize",
                award_amount="$3,000",
                deadline="January",
                url="https://example.org/1004",
            ),
        ]
    )
    await db.commit()


@pytest.mark.asyncio
async def test_search_by_keyword(db_session: AsyncSession):
    await _seed_rows(db_session)
    svc = ScholarshipService(db_session)

    # "engineering" appears in two names/purposes.
    result = await svc.search(q="engineering")
    names = {r.name for r in result["items"]}
    assert result["total"] == 2
    assert names == {"Engineering Excellence Award", "Future Builders Engineering Prize"}

    # Keyword also matches the organization field.
    by_org = await svc.search(q="Science Trust")
    assert by_org["total"] == 1
    assert by_org["items"][0].external_id == "1002"


@pytest.mark.asyncio
async def test_level_filter(db_session: AsyncSession):
    await _seed_rows(db_session)
    svc = ScholarshipService(db_session)

    grad = await svc.search(level="Graduate")
    grad_ids = {r.external_id for r in grad["items"]}
    # Both the pure-graduate row and the combined "Bachelor's … Graduate" row.
    assert grad_ids == {"1002", "1003"}


@pytest.mark.asyncio
async def test_award_type_filter(db_session: AsyncSession):
    await _seed_rows(db_session)
    svc = ScholarshipService(db_session)

    grants = await svc.search(award_type="Grant")
    assert grants["total"] == 1
    assert grants["items"][0].external_id == "1003"

    # Exact match — "Scholarship" does not catch "Fellowship".
    schol = await svc.search(award_type="Scholarship")
    assert schol["total"] == 1
    assert schol["items"][0].external_id == "1001"


@pytest.mark.asyncio
async def test_pagination(db_session: AsyncSession):
    await _seed_rows(db_session)
    svc = ScholarshipService(db_session)

    page1 = await svc.search(limit=2, offset=0)
    page2 = await svc.search(limit=2, offset=2)
    assert page1["total"] == 4
    assert page2["total"] == 4
    assert len(page1["items"]) == 2
    assert len(page2["items"]) == 2
    # Ordered by name, no overlap across pages.
    ids1 = {r.external_id for r in page1["items"]}
    ids2 = {r.external_id for r in page2["items"]}
    assert ids1.isdisjoint(ids2)


@pytest.mark.asyncio
async def test_get_scholarships_endpoint(
    student_client: AsyncClient,
    db_session: AsyncSession,
):
    await _seed_rows(db_session)
    resp = await student_client.get("/api/v1/scholarships?q=engineering&page=1&page_size=10")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    assert body["page"] == 1
    item = body["items"][0]
    # Response mirrors the model fields.
    for field in (
        "id",
        "external_id",
        "name",
        "organization",
        "purpose",
        "level_of_study",
        "award_type",
        "award_amount",
        "deadline",
        "url",
        "source",
    ):
        assert field in item
    assert item["source"] == "careeronestop"


@pytest.mark.asyncio
async def test_matches_endpoint_returns_shape(
    student_client: AsyncClient,
    db_session: AsyncSession,
):
    await _seed_rows(db_session)
    resp = await student_client.get("/api/v1/scholarships/matches?limit=5")
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert isinstance(body["items"], list)
    # With no derivable level, falls back to a general list (real rows, no fake match).
    assert len(body["items"]) == 4


@pytest.mark.asyncio
async def test_matches_for_student_filters_by_level(
    db_session: AsyncSession,
    mock_student_user: User,
):
    await _seed_rows(db_session)
    db_session.add(mock_student_user)
    profile = StudentProfile(user_id=mock_student_user.id, first_name="Ada", last_name="Lovelace")
    db_session.add(profile)
    await db_session.flush()
    # An active strategy targeting a master's → "Graduate" level.
    db_session.add(
        StudentStrategy(
            student_id=profile.id,
            version=1,
            status="active",
            target_degree="Master's in Computer Science",
        )
    )
    await db_session.commit()

    rows = await ScholarshipService(db_session).matches_for_student(mock_student_user.id)
    levels = {r.level_of_study for r in rows}
    ids = {r.external_id for r in rows}
    # Only graduate-eligible awards surface (1002 pure-grad, 1003 bachelor+grad).
    assert ids == {"1002", "1003"}
    assert all("Graduate" in lvl for lvl in levels)


@pytest.mark.asyncio
async def test_non_student_is_rejected(institution_client: AsyncClient):
    """``require_student`` rejects a non-student caller (Spec §Testing)."""
    resp = await institution_client.get("/api/v1/scholarships")
    assert resp.status_code == 403
    matches = await institution_client.get("/api/v1/scholarships/matches")
    assert matches.status_code == 403


@pytest.mark.asyncio
async def test_unauthenticated_is_rejected(client: AsyncClient):
    """No Authorization header → not served (FastAPI returns 422 for the missing
    required header; an invalid bearer returns 403). Either way, never 200."""
    resp = await client.get("/api/v1/scholarships")
    assert resp.status_code in (401, 403, 422)
    invalid = await client.get(
        "/api/v1/scholarships", headers={"Authorization": "Bearer not-a-valid-token"}
    )
    assert invalid.status_code in (401, 403)


@pytest.mark.asyncio
async def test_seed_upsert_is_idempotent(db_session: AsyncSession):
    """Re-running the seed upsert with the same external_id refreshes the row
    rather than inserting a duplicate (spec §Testing)."""
    rows = [
        {
            "external_id": "9999",
            "name": "Idempotent Award",
            "organization": "Org One",
            "purpose": None,
            "level_of_study": "Bachelor's Degree",
            "award_type": "Scholarship",
            "award_amount": "$500",
            "deadline": "May",
            "url": "https://example.org/9999",
            "source": "careeronestop",
        }
    ]

    await upsert_rows(db_session, rows)
    await db_session.commit()

    # Second run with an updated name — should UPDATE in place, not duplicate.
    rows[0]["name"] = "Idempotent Award (revised)"
    await upsert_rows(db_session, rows)
    await db_session.commit()

    count = await db_session.scalar(
        select(func.count()).select_from(Scholarship).where(Scholarship.external_id == "9999")
    )
    assert count == 1
    name = await db_session.scalar(
        select(Scholarship.name).where(Scholarship.external_id == "9999")
    )
    assert name == "Idempotent Award (revised)"


def test_external_scholarships_table_name():
    """The catalog lives on its own table, not Spec 60's ``scholarships`` —
    guards against a future re-collision with the reference model."""
    assert Scholarship.__tablename__ == "external_scholarships"
