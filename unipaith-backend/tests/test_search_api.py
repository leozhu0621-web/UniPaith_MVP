"""Spec 10 — Discovery type-first search API tests.

Covers: interpret (flag-off rule-based, flag-on agent success, flag-on agent
failure → graceful fallback, never 5xx), search/programs (chip → filter
mapping + sort), and the server-persisted compare set (add/list/remove + cap 4).
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.config import settings
from unipaith.models.institution import Institution, Program
from unipaith.models.student import StudentProfile
from unipaith.models.user import User

INTERPRET = "/api/v1/students/me/search/interpret"
SEARCH = "/api/v1/students/me/search/programs"
COMPARE = "/api/v1/students/me/compare"


async def _seed(db: AsyncSession, student_user: User, inst_user: User):
    db.add(student_user)
    db.add(inst_user)
    db.add(StudentProfile(user_id=student_user.id, first_name="Test", last_name="Student"))
    inst = Institution(
        admin_user_id=inst_user.id,
        name="Test University",
        type="university",
        country="United States",
        region="California",
        city="San Francisco",
    )
    db.add(inst)
    await db.flush()
    progs = {
        "cs_ms": Program(
            institution_id=inst.id,
            program_name="MS in Computer Science",
            degree_type="masters",
            is_published=True,
            tuition=40000,
            delivery_format="online",
            acceptance_rate=0.5,
        ),
        "cs_phd": Program(
            institution_id=inst.id,
            program_name="PhD in Computer Science",
            degree_type="phd",
            is_published=True,
            tuition=30000,
            delivery_format="on_campus",
            acceptance_rate=0.1,
        ),
        "mba": Program(
            institution_id=inst.id,
            program_name="MBA",
            degree_type="masters",
            is_published=True,
            tuition=80000,
            delivery_format="hybrid",
            acceptance_rate=0.3,
        ),
    }
    for p in progs.values():
        db.add(p)
    await db.commit()
    return inst, progs


def _names(body):
    return {r["program_name"] for r in body["results"]}


# ── interpret ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_interpret_flag_off_rule_based(
    student_client: AsyncClient, db_session, mock_student_user, mock_institution_user
):
    await _seed(db_session, mock_student_user, mock_institution_user)
    resp = await student_client.post(
        INTERPRET, json={"query": "MS in Computer Science in California under $50k"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["degraded"] is False
    cats = {c["category"] for c in body["chips"]}
    assert {"degree_level", "location", "budget"} <= cats


@pytest.mark.asyncio
async def test_interpret_flag_on_agent_success(
    student_client, db_session, mock_student_user, mock_institution_user, monkeypatch
):
    await _seed(db_session, mock_student_user, mock_institution_user)
    from unipaith.ai.query_interpreter import QueryInterpretResult
    from unipaith.schemas.search import ConstraintCategory, ConstraintChip

    fake_chips = [
        ConstraintChip(
            category=ConstraintCategory.degree_level,
            value="master",
            display="Master's",
            confidence=95,
        ).with_id()
    ]

    class _FakeAgent:
        async def interpret(self, *, query, profile_summary="", student_id=None, db=None):
            return QueryInterpretResult(chips=fake_chips)

    monkeypatch.setattr(settings, "ai_discovery_query_v2_enabled", True)
    monkeypatch.setattr(
        "unipaith.services.search_service.get_query_interpreter", lambda: _FakeAgent()
    )
    resp = await student_client.post(INTERPRET, json={"query": "anything"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["degraded"] is False
    assert [c["category"] for c in body["chips"]] == ["degree_level"]


@pytest.mark.asyncio
async def test_interpret_flag_on_agent_failure_falls_back(
    student_client, db_session, mock_student_user, mock_institution_user, monkeypatch
):
    """Invariant: LLM failure must never 5xx — fall back to rule-based + degraded."""
    await _seed(db_session, mock_student_user, mock_institution_user)

    class _BoomAgent:
        async def interpret(self, *, query, profile_summary="", student_id=None, db=None):
            raise RuntimeError("LLM timeout")

    monkeypatch.setattr(settings, "ai_discovery_query_v2_enabled", True)
    monkeypatch.setattr(
        "unipaith.services.search_service.get_query_interpreter", lambda: _BoomAgent()
    )
    resp = await student_client.post(
        INTERPRET, json={"query": "online masters in computer science"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["degraded"] is True
    cats = {c["category"] for c in body["chips"]}
    assert "format" in cats and "degree_level" in cats


# ── search/programs ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_search_by_degree_chip(
    student_client, db_session, mock_student_user, mock_institution_user
):
    await _seed(db_session, mock_student_user, mock_institution_user)
    resp = await student_client.post(
        SEARCH,
        json={"chips": [{"category": "degree_level", "value": "master", "display": "Master's"}]},
    )
    assert resp.status_code == 200
    assert _names(resp.json()) == {"MS in Computer Science", "MBA"}


@pytest.mark.asyncio
async def test_search_combined_degree_and_budget(
    student_client, db_session, mock_student_user, mock_institution_user
):
    await _seed(db_session, mock_student_user, mock_institution_user)
    resp = await student_client.post(
        SEARCH,
        json={
            "chips": [
                {"category": "degree_level", "value": "master", "display": "Master's"},
                {"category": "budget", "value": "<=50000", "display": "≤ $50k/yr"},
            ]
        },
    )
    assert resp.status_code == 200
    # masters AND tuition<=50000 → only the CS MS (MBA is $80k).
    assert _names(resp.json()) == {"MS in Computer Science"}


@pytest.mark.asyncio
async def test_search_by_format_online(
    student_client, db_session, mock_student_user, mock_institution_user
):
    await _seed(db_session, mock_student_user, mock_institution_user)
    resp = await student_client.post(
        SEARCH, json={"chips": [{"category": "format", "value": "online", "display": "Online"}]}
    )
    assert resp.status_code == 200
    assert _names(resp.json()) == {"MS in Computer Science"}


@pytest.mark.asyncio
async def test_search_major_fts(
    student_client, db_session, mock_student_user, mock_institution_user
):
    await _seed(db_session, mock_student_user, mock_institution_user)
    resp = await student_client.post(
        SEARCH,
        json={
            "chips": [
                {"category": "major", "value": "computer science", "display": "Computer Science"}
            ]
        },
    )
    assert resp.status_code == 200
    assert _names(resp.json()) == {"MS in Computer Science", "PhD in Computer Science"}


@pytest.mark.asyncio
async def test_search_sort_tuition_asc(
    student_client, db_session, mock_student_user, mock_institution_user
):
    await _seed(db_session, mock_student_user, mock_institution_user)
    resp = await student_client.post(SEARCH, json={"sort": "tuition_asc"})
    assert resp.status_code == 200
    tuitions = [r["tuition"] for r in resp.json()["results"]]
    assert tuitions == sorted(tuitions)
    assert tuitions[0] == 30000


# ── compare set ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_compare_add_list_remove_and_cap(
    student_client, db_session, mock_student_user, mock_institution_user
):
    inst, progs = await _seed(db_session, mock_student_user, mock_institution_user)
    # add 2 more so we have 5 total → exercise the cap-of-4.
    extra = [
        Program(
            institution_id=inst.id,
            program_name=f"Extra {i}",
            degree_type="masters",
            is_published=True,
            tuition=20000 + i,
        )
        for i in range(2)
    ]
    for p in extra:
        db_session.add(p)
    await db_session.commit()
    all_ids = [str(p.id) for p in (*progs.values(), *extra)]

    # starts empty
    resp = await student_client.get(COMPARE)
    assert resp.status_code == 200
    assert resp.json()["items"] == []
    assert resp.json()["max"] == 4

    # add 4 → ok
    for pid in all_ids[:4]:
        r = await student_client.post(COMPARE + "/add", json={"program_id": pid})
        assert r.status_code == 200
    assert len(r.json()["items"]) == 4

    # 5th → 409 (cap)
    r5 = await student_client.post(COMPARE + "/add", json={"program_id": all_ids[4]})
    assert r5.status_code == 409

    # idempotent re-add of an existing one stays at 4
    r_dup = await student_client.post(COMPARE + "/add", json={"program_id": all_ids[0]})
    assert r_dup.status_code == 200
    assert len(r_dup.json()["items"]) == 4

    # remove one → 3
    r_del = await student_client.request("DELETE", f"{COMPARE}/{all_ids[0]}")
    assert r_del.status_code == 200
    assert len(r_del.json()["items"]) == 3
