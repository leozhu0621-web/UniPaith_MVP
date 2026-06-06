# MIT Institution Page — Flagship Overhaul Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the MIT institution page the gold-standard template — complete, real, sourced data (rankings, rich intro, real 6 academic units, real program catalog, depth sections, citations) plus small header/label fixes — and ship it to production.

**Architecture:** A single source of truth for MIT's canonical profile lives in `unipaith/data/mit_profile.py` (data constants + a sync `apply(session)` upserter that's idempotent and FK-safe, and a no-op when MIT is absent). An **idempotent data-only Alembic migration** (DML, no DDL) calls `apply()` so the data ships automatically on the next backend deploy (`docker-entrypoint.sh` runs `alembic upgrade heads` before serving). A standalone `scripts/enrich_mit.py` reuses `apply()` for local runs, and the dev seed imports the same constants. Four surgical frontend edits surface the data.

**Tech Stack:** Python 3.12 · SQLAlchemy 2 (sync Session inside the migration) · Alembic · PostgreSQL 16 (JSONB) · React 19 + TypeScript + Vite + vitest.

---

## Pre-flight recon (Task 0 — investigative, no code)

- [ ] **Step 0.1:** Fetch the live MIT schools & programs to see exactly what the upsert must reconcile.

```bash
# Schools + programs the live API currently serves for MIT
curl -s "https://api.unipaith.co/api/v1/institutions/e885756a-dbf3-4140-879d-fa873dc07973/schools" | python3 -m json.tool
curl -s "https://api.unipaith.co/api/v1/institutions/e885756a-dbf3-4140-879d-fa873dc07973/programs" | python3 -m json.tool
```
(If those paths 404, grep `unipaith-backend/src/unipaith/api/institutions.py` for the schools/programs routes and use the real ones.) Record the legacy school names and program names/slugs — these are what the migration's reconcile step will update-or-remove.

- [ ] **Step 0.2:** Confirm the program/school timestamp columns. Read `unipaith-backend/src/unipaith/models/institution.py` around the `Program` class tail (after line 256) to confirm whether `Program` has `created_at`/`updated_at`. (Using the ORM in `apply()` makes this moot — defaults/timestamps are handled — but confirm before writing tests.)

---

## File Structure

| File | Responsibility | Create/Modify |
|------|----------------|---------------|
| `unipaith-backend/src/unipaith/data/__init__.py` | new package marker | Create |
| `unipaith-backend/src/unipaith/data/mit_profile.py` | Canonical MIT data constants + sync `apply(session)` upserter | Create |
| `unipaith-backend/alembic/versions/<rev>_enrich_mit_profile.py` | Data migration calling `apply(Session(bind=op.get_bind()))` | Create |
| `unipaith-backend/scripts/enrich_mit.py` | CLI wrapper around `apply()` for local/manual runs | Create |
| `unipaith-backend/tests/test_mit_profile.py` | `apply()` idempotency / no-op-absent / shape tests | Create |
| `unipaith-backend/scripts/seed_dev_data.py` | MIT seed imports canonical constants (dev ≈ prod) | Modify |
| `frontend/src/pages/student/institution/InstitutionDetail.tsx` | Remove hero acceptance+students chips; relabel "Students"→"Undergraduates"; add `<SourcesFooter>`; ensure `rankingLabel` maps new keys | Modify |
| `frontend/src/pages/student/institution/InstitutionDetail.test.tsx` | vitest for the four frontend changes | Create (or extend if exists) |

---

## Canonical Data (single source of truth — referenced by tasks)

All figures below are real and traceable. Institution-level numerics come from the prior `seed_mit_flagship.py` (College Scorecard) and the current production record; rankings verified 2026-06-06 against the cited sources.

### Institution `ranking_data` (shallow-merged into existing)
```python
RANKING_DATA = {
    "ownership_type": "private_nonprofit",
    "accreditor": "NECHE",
    "carnegie_classification": "Doctoral Universities: Very High Research Activity",
    "qs_world_university_rankings": {"rank": 1, "year": 2025},          # QS World 2025-26 (MIT News 2025-06-18)
    "times_higher_education": {"rank": 2, "year": 2025},                # THE WUR 2025 (MIT News 2025-03-03; P&Q 2024-10-08)
    "us_news_national": {"rank": 2, "year": 2025},                      # US News 2025-26 (MIT News 2025-09-23)
}
```

### Institution `school_outcomes` (shallow-merged; provides complete sub-objects)
```python
SCHOOL_OUTCOMES = {
    "admit_rate": 0.0455,
    "avg_net_price": 20111,
    "median_earnings_10yr": 143372,
    "completion_rate_4yr_150pct": 0.9641,
    "retention_rate_first_year": 0.9908,
    "test_scores": {"sat_reading_25_75": [740, 780], "sat_math_25_75": [780, 800], "act_25_75": [34, 36]},
    "financial_aid": {"pell_grant_rate": 0.1932, "federal_loan_rate": 0.0669, "median_debt_completers": 14768},
    "demographics": {"white": 0.2126, "black": 0.077, "hispanic": 0.1409, "asian": 0.3517, "women": 0.4816},
    "location": {"lat": 42.3597, "lng": -71.0919},
    "employed_or_continuing_ed": 0.94,
    "graduation_rate_6yr": 0.96,
    "top_employer_industries": ["Technology", "Finance", "Consulting", "Research"],
    "flagship": {
        "nobel_laureates": 106, "macarthur_fellows": 85, "enrollment_total": 11816,
        "admissions_cycle": "Class of 2029", "applicants": 29281, "admits": 1334,
    },
    "sources": [
        {"label": "Costs, outcomes, test scores, demographics", "source": "U.S. Dept. of Education College Scorecard", "year": 2024, "url": "https://collegescorecard.ed.gov/school/?166683-Massachusetts-Institute-of-Technology"},
        {"label": "World ranking", "source": "QS World University Rankings", "year": 2025, "url": "https://www.topuniversities.com/universities/massachusetts-institute-technology-mit"},
        {"label": "World ranking", "source": "Times Higher Education", "year": 2025, "url": "https://www.timeshighereducation.com/world-university-rankings/massachusetts-institute-technology"},
        {"label": "National ranking", "source": "U.S. News Best National Universities", "year": 2025, "url": "https://www.usnews.com/best-colleges/massachusetts-institute-of-technology-2178"},
        {"label": "Schools, distinction, enrollment", "source": "MIT Facts", "year": 2025, "url": "https://web.mit.edu/facts/"},
    ],
}
UNDERGRAD_COUNT = 4535   # student_body_size = undergrad; total (11,816) lives in flagship.enrollment_total
```

### Institution `description_text` (rich intro — replaces the one-liner)
> Founded in 1861 in Cambridge, Massachusetts, the Massachusetts Institute of Technology is a private research university whose motto — *Mens et Manus* ("mind and hand") — captures its founding commitment to advancing knowledge in the service of real-world problems. Its campus stretches more than a mile along the north bank of the Charles River, across from downtown Boston.
>
> MIT is organized into five schools and one college: Engineering; Science; Humanities, Arts, and Social Sciences; the MIT Sloan School of Management; Architecture and Planning; and the Stephen A. Schwarzman College of Computing, opened in 2019 to weave computing and artificial intelligence through every discipline. Roughly 4,500 undergraduates and 7,000 graduate students study across these units, supported by one of the largest research enterprises of any U.S. university.
>
> The Institute ranks among the very best universities in the world — No. 1 globally by QS, and No. 2 in both the Times Higher Education world ranking and the U.S. News national-universities list. Its faculty and alumni include more than 100 Nobel laureates alongside dozens of MacArthur Fellows and Turing Award winners.
>
> MIT is also distinctively entrepreneurial: generations of alumni have founded companies across semiconductors, biotechnology, robotics, aerospace, and the modern internet. A rigorous education in science, engineering, and management — paired with need-based aid that holds the average net price near $20,000 a year — produces graduates with a median income of roughly $143,000 a decade after entry.

### Schools — the real 6 academic units (`SCHOOLS`, in `sort_order`)
```
1. School of Engineering — MIT's largest school; about half of all undergraduates major here. Departments span electrical engineering & computer science, mechanical, aeronautics & astronautics, chemical, materials science, biological, civil & environmental, and nuclear engineering.
2. School of Science — Home to physics, mathematics, biology, chemistry, brain & cognitive sciences, and earth, atmospheric & planetary sciences; a hub of fundamental research and Nobel-winning discovery.
3. School of Humanities, Arts, and Social Sciences (SHASS) — Economics, linguistics & philosophy, political science, comparative media studies/writing and more, ensuring every MIT education is grounded in the humanities and social sciences.
4. MIT Sloan School of Management — One of the world's leading business schools; pioneered modern management science and offers the MBA, Master of Finance, and Master of Business Analytics alongside undergraduate management.
5. School of Architecture and Planning — Home to the oldest architecture program in the United States (founded 1865), urban studies & planning, real estate, and the MIT Media Lab.
6. MIT Stephen A. Schwarzman College of Computing — Opened in 2019 to connect computer science and AI across all of MIT, offering joint and interdisciplinary computing degrees.
```

### Programs — real catalog (`PROGRAMS`). Each: `slug` (idempotency key, e.g. `mit-eecs-sb`), `school` (maps to SCHOOLS name), `program_name`, `degree_type`, `duration_months`, `description` (one real sentence). `is_published=True`. `tuition`/`acceptance_rate` left **null** unless a published per-program figure is verified at build (cite it); PhD programs note "fully funded (tuition + stipend)" in `cost_data`.

| slug | school | program_name | degree | months |
|------|--------|--------------|--------|--------|
| mit-eecs-sb | Engineering | Electrical Engineering & Computer Science (6) | SB | 48 |
| mit-eecs-meng | Engineering | Electrical Engineering & Computer Science (6) | MEng | 12 |
| mit-eecs-phd | Engineering | Electrical Engineering & Computer Science (6) | PhD | 60 |
| mit-meche-sb | Engineering | Mechanical Engineering (2) | SB | 48 |
| mit-meche-phd | Engineering | Mechanical Engineering (2) | PhD | 60 |
| mit-aeroastro-sb | Engineering | Aeronautics & Astronautics (16) | SB | 48 |
| mit-aeroastro-sm | Engineering | Aeronautics & Astronautics (16) | SM | 24 |
| mit-cheme-sb | Engineering | Chemical Engineering (10) | SB | 48 |
| mit-dmse-sb | Engineering | Materials Science & Engineering (3) | SB | 48 |
| mit-be-sb | Engineering | Biological Engineering (20) | SB | 48 |
| mit-cee-sb | Engineering | Civil & Environmental Engineering (1) | SB | 48 |
| mit-nse-sb | Engineering | Nuclear Science & Engineering (22) | SB | 48 |
| mit-physics-sb | Science | Physics (8) | SB | 48 |
| mit-physics-phd | Science | Physics (8) | PhD | 60 |
| mit-math-sb | Science | Mathematics (18) | SB | 48 |
| mit-math-phd | Science | Mathematics (18) | PhD | 60 |
| mit-biology-sb | Science | Biology (7) | SB | 48 |
| mit-chemistry-sb | Science | Chemistry (5) | SB | 48 |
| mit-bcs-sb | Science | Brain & Cognitive Sciences (9) | SB | 48 |
| mit-eaps-sb | Science | Earth, Atmospheric & Planetary Sciences (12) | SB | 48 |
| mit-economics-sb | SHASS | Economics (14) | SB | 48 |
| mit-economics-phd | SHASS | Economics (14) | PhD | 60 |
| mit-linguistics-phil-sb | SHASS | Linguistics & Philosophy (24) | SB | 48 |
| mit-polisci-sb | SHASS | Political Science (17) | SB | 48 |
| mit-cms-writing-sb | SHASS | Comparative Media Studies / Writing (21) | SB | 48 |
| mit-management-sb | Sloan | Management (15) | SB | 48 |
| mit-sloan-mba | Sloan | MBA | MBA | 24 |
| mit-sloan-mfin | Sloan | Master of Finance | SM | 18 |
| mit-sloan-mban | Sloan | Master of Business Analytics | SM | 12 |
| mit-sloan-phd | Sloan | PhD in Management | PhD | 60 |
| mit-arch-sb | Architecture & Planning | Architecture (4) | SB | 48 |
| mit-arch-march | Architecture & Planning | Architecture (4) | MArch | 42 |
| mit-dusp-sb | Architecture & Planning | Urban Studies & Planning (11) | SB | 48 |
| mit-mas-sm | Architecture & Planning | Media Arts & Sciences (Media Lab) | SM | 24 |
| mit-cs-eng-6-3-sb | Computing | Computer Science & Engineering (6-3) | SB | 48 |
| mit-ai-decision-6-4-sb | Computing | Artificial Intelligence & Decision Making (6-4) | SB | 48 |
| mit-cse-phd | Computing | Computational Science & Engineering | PhD | 60 |

Descriptions: write one real, specific sentence per program (department + focus + level). Example for `mit-eecs-sb`: *"MIT's largest undergraduate major (Course 6), spanning circuits and devices, computer systems, AI, and theory — the academic home of the Schwarzman College of Computing's joint degrees."* Keep them factual; no marketing fluff.

`PROGRAM_SLUGS = [p["slug"] for p in PROGRAMS]` is the canonical set used by the reconcile step.

---

## Task 1: Canonical data module + institution-row enrichment

**Files:**
- Create: `unipaith-backend/src/unipaith/data/__init__.py` (empty)
- Create: `unipaith-backend/src/unipaith/data/mit_profile.py`
- Test: `unipaith-backend/tests/test_mit_profile.py`

- [ ] **Step 1.1: Write the failing test** (`tests/test_mit_profile.py`)

```python
import pytest
from sqlalchemy import select
from unipaith.models.institution import Institution
from unipaith.data import mit_profile

pytestmark = pytest.mark.asyncio

async def _make_mit(db_session):
    inst = Institution(name=mit_profile.INSTITUTION_NAME, type="university",
                       country="United States", description_text="stub",
                       student_body_size=1, is_verified=True,
                       ranking_data={"qs_world_university_rankings": {"rank": 1, "year": 2025}},
                       school_outcomes={"employed_or_continuing_ed": 0.94})
    db_session.add(inst)
    await db_session.commit()
    return inst

async def test_apply_enriches_institution(db_session, sync_session_from):
    inst = await _make_mit(db_session)
    # apply() is sync; run it against a sync session bound to the same DB.
    sync_session_from(mit_profile.apply)
    await db_session.refresh(inst)
    assert inst.ranking_data["times_higher_education"]["rank"] == 2
    assert inst.ranking_data["us_news_national"]["rank"] == 2
    assert inst.school_outcomes["avg_net_price"] == 20111
    assert inst.school_outcomes["test_scores"]["act_25_75"] == [34, 36]
    assert inst.school_outcomes["flagship"]["nobel_laureates"] == 106
    assert any(s["source"].startswith("U.S. Dept") for s in inst.school_outcomes["sources"])
    assert inst.student_body_size == 4535
    assert "Mens et Manus" in inst.description_text
```

> **Note on `sync_session_from`:** the migration runs `apply()` synchronously. Add a small fixture in `tests/conftest.py` that opens a **sync** Session against the same test DB URL (swap `+asyncpg` → `+psycopg`/`postgresql`) and runs the passed callable, so the test exercises the exact sync path the migration uses. If the repo already has a sync-session test helper, use it instead.

- [ ] **Step 1.2: Run it, verify it fails**

Run: `cd unipaith-backend && PYTHONPATH=src AI_MOCK_MODE=true .venv/bin/pytest tests/test_mit_profile.py -v --tb=short`
Expected: FAIL (`ModuleNotFoundError: unipaith.data.mit_profile`).

- [ ] **Step 1.3: Create the data module with constants + institution-row half of `apply()`**

Create `unipaith/data/mit_profile.py` with: `INSTITUTION_NAME = "Massachusetts Institute of Technology"`, the `RANKING_DATA`, `SCHOOL_OUTCOMES`, `UNDERGRAD_COUNT`, `DESCRIPTION` (the rich intro), `SCHOOLS`, `PROGRAMS`, `PROGRAM_SLUGS` constants from the Canonical Data section, and:

```python
from sqlalchemy import select
from sqlalchemy.orm import Session
from unipaith.models.institution import Institution, School, Program

def apply(session: Session) -> bool:
    """Idempotently enrich MIT. No-op (returns False) if MIT is absent.
    Sync — runs inside the Alembic migration and the CLI script."""
    inst = session.scalar(select(Institution).where(Institution.name == INSTITUTION_NAME))
    if inst is None:
        return False
    # Shallow-merge JSONB (we provide complete sub-objects).
    inst.ranking_data = {**(inst.ranking_data or {}), **RANKING_DATA}
    inst.school_outcomes = {**(inst.school_outcomes or {}), **SCHOOL_OUTCOMES}
    inst.description_text = DESCRIPTION
    inst.student_body_size = UNDERGRAD_COUNT
    session.flush()
    _apply_schools(session, inst)    # Task 2
    _apply_programs(session, inst)   # Task 3
    session.commit()
    return True
```

For Task 1, stub `_apply_schools` and `_apply_programs` as `pass` so the institution test passes in isolation.

- [ ] **Step 1.4: Run the test, verify it passes**

Run: `cd unipaith-backend && PYTHONPATH=src AI_MOCK_MODE=true .venv/bin/pytest tests/test_mit_profile.py::test_apply_enriches_institution -v --tb=short`
Expected: PASS.

- [ ] **Step 1.5: Commit**

```bash
git add unipaith-backend/src/unipaith/data/ unipaith-backend/tests/test_mit_profile.py
git commit -m "feat(data): MIT canonical profile module + institution enrichment"
```

---

## Task 2: Schools upsert + legacy-school cleanup

**Files:** Modify `unipaith/data/mit_profile.py`; Test `tests/test_mit_profile.py`

- [ ] **Step 2.1: Write the failing test**

```python
async def test_apply_sets_six_real_schools(db_session, sync_session_from):
    inst = await _make_mit(db_session)
    # seed two legacy schools that should be removed
    db_session.add_all([
        School(institution_id=inst.id, name="Legacy College of Widgets"),
        School(institution_id=inst.id, name="School of Engineering"),  # canonical name, pre-existing
    ])
    await db_session.commit()
    sync_session_from(mit_profile.apply)
    rows = (await db_session.execute(
        select(School).where(School.institution_id == inst.id))).scalars().all()
    names = sorted(s.name for s in rows)
    assert names == sorted(s["name"] for s in mit_profile.SCHOOLS)   # exactly the 6, legacy gone
    assert len(names) == 6
```

- [ ] **Step 2.2: Run it, verify it fails**

Run: `cd unipaith-backend && PYTHONPATH=src AI_MOCK_MODE=true .venv/bin/pytest tests/test_mit_profile.py::test_apply_sets_six_real_schools -v --tb=short`
Expected: FAIL (legacy school still present / canonical missing).

- [ ] **Step 2.3: Implement `_apply_schools`**

```python
def _apply_schools(session: Session, inst: Institution) -> dict[str, "School"]:
    existing = {s.name: s for s in session.scalars(
        select(School).where(School.institution_id == inst.id))}
    canonical_names = {s["name"] for s in SCHOOLS}
    # Upsert the 6 by (institution_id, name)
    by_name: dict[str, School] = {}
    for spec in SCHOOLS:
        sc = existing.get(spec["name"])
        if sc is None:
            sc = School(institution_id=inst.id, name=spec["name"])
            session.add(sc)
        sc.description_text = spec["description"]
        sc.sort_order = spec["sort_order"]
        sc.catalog_source = "curated"
        by_name[spec["name"]] = sc
    # Remove legacy schools (programs.school_id is ON DELETE SET NULL → safe)
    for name, sc in existing.items():
        if name not in canonical_names:
            session.delete(sc)
    session.flush()
    return by_name
```
Have `apply()` keep the returned mapping for Task 3 (`school_by_name = _apply_schools(...)`).

- [ ] **Step 2.4: Run the test, verify it passes** (same command as 2.2). Expected: PASS.

- [ ] **Step 2.5: Commit**

```bash
git add unipaith-backend/src/unipaith/data/mit_profile.py unipaith-backend/tests/test_mit_profile.py
git commit -m "feat(data): upsert MIT's six real academic units + drop legacy schools"
```

---

## Task 3: Programs upsert (by slug) + FK-guarded legacy reconcile

**Files:** Modify `unipaith/data/mit_profile.py`; Test `tests/test_mit_profile.py`

- [ ] **Step 3.1: Write the failing test**

```python
async def test_apply_builds_real_program_catalog_idempotently(db_session, sync_session_from):
    inst = await _make_mit(db_session)
    # legacy program with NO dependents → should be removed
    db_session.add(Program(institution_id=inst.id, program_name="Legacy MS in Widgets",
                           degree_type="SM", is_published=True, slug="mit-legacy-widgets"))
    await db_session.commit()
    sync_session_from(mit_profile.apply)
    sync_session_from(mit_profile.apply)   # run twice → idempotent
    progs = (await db_session.execute(
        select(Program).where(Program.institution_id == inst.id))).scalars().all()
    slugs = sorted(p.slug for p in progs)
    assert slugs == sorted(mit_profile.PROGRAM_SLUGS)        # exactly canonical, no dupes, legacy gone
    assert all(p.is_published for p in progs)
    # programs map to real schools
    eecs = next(p for p in progs if p.slug == "mit-eecs-sb")
    sch = (await db_session.get(School, eecs.school_id))
    assert sch.name == "School of Engineering"
```

- [ ] **Step 3.2: Run it, verify it fails** — Expected: FAIL (programs not built).

- [ ] **Step 3.3: Implement `_apply_programs` with FK-safe reconcile**

```python
from sqlalchemy import text

def _program_has_dependents(session: Session, program_id) -> bool:
    """True if any FK in the DB references this programs row (so deletion is unsafe)."""
    fks = session.execute(text("""
        SELECT tc.table_name, kcu.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage ccu ON tc.constraint_name = ccu.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY' AND ccu.table_name = 'programs'
          AND ccu.column_name = 'id' AND tc.table_name <> 'programs'
    """)).fetchall()
    for table, col in fks:
        n = session.execute(
            text(f'SELECT 1 FROM "{table}" WHERE "{col}" = :pid LIMIT 1'),
            {"pid": program_id}).first()
        if n:
            return True
    return False

def _apply_programs(session: Session, inst: Institution, school_by_name: dict) -> None:
    existing = {p.slug: p for p in session.scalars(
        select(Program).where(Program.institution_id == inst.id)) if p.slug}
    canonical = set(PROGRAM_SLUGS)
    for spec in PROGRAMS:
        p = existing.get(spec["slug"])
        if p is None:
            p = Program(institution_id=inst.id, program_name=spec["program_name"],
                        degree_type=spec["degree_type"], slug=spec["slug"])
            session.add(p)
        p.program_name = spec["program_name"]
        p.degree_type = spec["degree_type"]
        p.duration_months = spec.get("duration_months")
        p.description_text = spec["description"]
        p.school_id = school_by_name[spec["school"]].id
        p.is_published = True
        if spec.get("tuition") is not None:
            p.tuition = spec["tuition"]
        if spec.get("cost_data"):
            p.cost_data = spec["cost_data"]
    session.flush()
    # Reconcile: drop legacy MIT programs not in the canonical set, but only if unreferenced.
    for slug, p in session.execute(
        select(Program.slug, Program).where(Program.institution_id == inst.id)).all() if False else []:
        pass  # (clarity placeholder — real loop below)
    legacy = [p for p in session.scalars(
        select(Program).where(Program.institution_id == inst.id))
        if (p.slug or "") not in canonical]
    for p in legacy:
        if not _program_has_dependents(session, p.id):
            session.delete(p)
        else:
            p.is_published = False   # keep referenced rows but hide from the catalog
    session.flush()
```
Update `apply()` to pass `school_by_name`: `_apply_programs(session, inst, school_by_name)`. Delete the `if False` clarity placeholder line — it must not ship.

- [ ] **Step 3.4: Run the test, verify it passes** — Expected: PASS (both runs → identical canonical set).

- [ ] **Step 3.5: Add the no-op-when-absent test + run the full file**

```python
async def test_apply_is_noop_when_mit_absent(db_session, sync_session_from):
    # fresh DB, no MIT row
    result = {}
    sync_session_from(lambda s: result.__setitem__("ret", mit_profile.apply(s)))
    assert result["ret"] is False
```
Run: `cd unipaith-backend && PYTHONPATH=src AI_MOCK_MODE=true .venv/bin/pytest tests/test_mit_profile.py -v --tb=short`
Expected: ALL PASS.

- [ ] **Step 3.6: Commit**

```bash
git add unipaith-backend/src/unipaith/data/mit_profile.py unipaith-backend/tests/test_mit_profile.py
git commit -m "feat(data): build MIT's real program catalog with FK-safe reconcile"
```

---

## Task 4: Data migration (auto-ships on deploy)

**Files:** Create `unipaith-backend/alembic/versions/<rev>_enrich_mit_profile.py`

- [ ] **Step 4.1: Determine the current head**

Run: `cd unipaith-backend && PYTHONPATH=src .venv/bin/alembic heads`
- If **one** head → that's `down_revision`.
- If **multiple** heads (concurrent sessions) → first create a merge revision: `.venv/bin/alembic merge -m "merge heads before mit enrich" <head1> <head2>`, then chain off that merge.

- [ ] **Step 4.2: Create the migration**

```python
"""enrich MIT institution profile (data-only, no DDL)

Revision ID: <generated>
Revises: <current head from Step 4.1>
"""
from alembic import op
from sqlalchemy.orm import Session
from unipaith.data import mit_profile

revision = "<generated>"
down_revision = "<current head>"
branch_labels = None
depends_on = None

def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    mit_profile.apply(session)   # no-op if MIT absent; commits internally

def downgrade() -> None:
    # Data migration: enrichment is additive/idempotent; no structural rollback.
    pass
```

- [ ] **Step 4.3: Verify single head + that the file imports**

Run: `cd unipaith-backend && PYTHONPATH=src .venv/bin/alembic heads`
Expected: exactly **one** head (the new revision).
Run: `cd unipaith-backend && PYTHONPATH=src AI_MOCK_MODE=true .venv/bin/pytest tests/ -k "single_head or alembic" -v --tb=short`
Expected: PASS (the single-head guard test stays green).

- [ ] **Step 4.4: Smoke-test the migration against a scratch DB**

```bash
cd unipaith-backend
# Use a throwaway DB so we don't touch the shared dev DB (see CLAUDE.md isolated-DB note).
createdb unipaith_mitmig_test 2>/dev/null || true
# Derive the scratch DSN from your dev DATABASE_URL (no inline credentials):
DATABASE_URL="${DATABASE_URL%/*}/unipaith_mitmig_test" \
  PYTHONPATH=src .venv/bin/alembic upgrade head
# Expected: completes without error (MIT absent in fresh DB → apply() no-ops cleanly).
dropdb unipaith_mitmig_test 2>/dev/null || true
```
Expected: `alembic upgrade head` exits 0.

- [ ] **Step 4.5: Commit**

```bash
git add unipaith-backend/alembic/versions/
git commit -m "feat(migration): data-only MIT profile enrichment (ships on deploy)"
```

---

## Task 5: Standalone CLI (`scripts/enrich_mit.py`)

**Files:** Create `unipaith-backend/scripts/enrich_mit.py`

- [ ] **Step 5.1: Implement** (mirrors how `seed_dev_data.py` builds its engine, but **sync**)

```python
"""One-off: enrich MIT to the canonical profile. Idempotent. `python -m scripts.enrich_mit`."""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from unipaith.data import mit_profile

def main() -> None:
    url = os.environ["DATABASE_URL"].replace("+asyncpg", "+psycopg")
    engine = create_engine(url)
    with Session(engine) as session:
        changed = mit_profile.apply(session)
    print("MIT enriched." if changed else "MIT not found — no-op.")

if __name__ == "__main__":
    main()
```

- [ ] **Step 5.2: Verify it runs against the dev DB** (after `make dev-db` + dev seed has MIT)

Run: `cd unipaith-backend && set -a && . ./.env && set +a && PYTHONPATH=src .venv/bin/python -m scripts.enrich_mit` (sources `DATABASE_URL` from the gitignored `.env` — no inline credentials)
Expected: prints `MIT enriched.`

- [ ] **Step 5.3: Commit**

```bash
git add unipaith-backend/scripts/enrich_mit.py
git commit -m "feat(scripts): enrich_mit CLI reusing the canonical profile apply()"
```

---

## Task 6: Frontend — remove redundant hero chips

**Files:** Modify `frontend/src/pages/student/institution/InstitutionDetail.tsx:243-248`; Test `InstitutionDetail.test.tsx`

- [ ] **Step 6.1: Write the failing test**

```tsx
it("hero omits acceptance and student-count chips, keeps QS + founded", () => {
  render(<InstitutionDetail institutionId="x" isAuthenticated />, { wrapper })
  const meta = screen.getByTestId("hero-meta") // add data-testid to the heroStats container at :311
  expect(meta).toHaveTextContent(/QS World/)
  expect(meta).toHaveTextContent(/founded/)
  expect(meta).not.toHaveTextContent(/acceptance/)
  expect(meta).not.toHaveTextContent(/students/)
})
```
(Mock the institution query to return MIT-shaped data with `school_outcomes.admit_rate` and `flagship.enrollment_total` set, so the test proves they're intentionally omitted, not just absent.)

- [ ] **Step 6.2: Run it, verify it fails**

Run: `cd frontend && npx vitest run src/pages/student/institution/InstitutionDetail.test.tsx`
Expected: FAIL (chips still rendered).

- [ ] **Step 6.3: Implement** — delete the two `heroStats.push` blocks at `:245` (acceptance) and `:247-248` (students); add `data-testid="hero-meta"` to the container `<div>` at `:311`. Keep the QS (`:244`) and founded (`:246`) pushes.

- [ ] **Step 6.4: Run the test, verify it passes** — Expected: PASS.

- [ ] **Step 6.5: Commit**

```bash
git add frontend/src/pages/student/institution/InstitutionDetail.tsx frontend/src/pages/student/institution/InstitutionDetail.test.tsx
git commit -m "fix(institution): drop redundant acceptance/student chips from hero"
```

---

## Task 7: Frontend — relabel "Students" → "Undergraduates"

**Files:** Modify `InstitutionDetail.tsx:625`; Test `InstitutionDetail.test.tsx`

- [ ] **Step 7.1: Write the failing test**

```tsx
it("labels the undergrad count 'Undergraduates' (total stays in Distinction)", () => {
  render(<InstitutionDetail institutionId="x" isAuthenticated />, { wrapper })
  expect(screen.getByText("Undergraduates")).toBeInTheDocument()
  expect(screen.getByText("Total enrollment")).toBeInTheDocument()
})
```

- [ ] **Step 7.2: Run it, verify it fails** — Expected: FAIL.

- [ ] **Step 7.3: Implement** — at `:625` change `<Fact label="Students" ...>` to `<Fact label="Undergraduates" ...>`.

- [ ] **Step 7.4: Run the test, verify it passes** — Expected: PASS.

- [ ] **Step 7.5: Commit**

```bash
git add frontend/src/pages/student/institution/InstitutionDetail.tsx frontend/src/pages/student/institution/InstitutionDetail.test.tsx
git commit -m "fix(institution): relabel undergrad count, disambiguate from total enrollment"
```

---

## Task 8: Frontend — ranking labels for THE / US News

**Files:** Modify `InstitutionDetail.tsx` (the `rankingLabel` helper); Test `InstitutionDetail.test.tsx`

- [ ] **Step 8.1: Locate `rankingLabel`** — grep `frontend/src/pages/student/institution/InstitutionDetail.tsx` for `function rankingLabel` (or it may be imported). Confirm what it returns for keys `times_higher_education` and `us_news_national`.

- [ ] **Step 8.2: Write the failing test**

```tsx
it("renders all three rankings with clean labels", () => {
  // mock query → ranking_data has qs_world_university_rankings, times_higher_education, us_news_national
  render(<InstitutionDetail institutionId="x" isAuthenticated />, { wrapper })
  expect(screen.getByText(/Times Higher Ed/)).toBeInTheDocument()
  expect(screen.getByText(/US News/)).toBeInTheDocument()
  expect(screen.getByText("#1")).toBeInTheDocument()
})
```

- [ ] **Step 8.3: Run it, verify it fails** — Expected: FAIL (raw key shown or missing).

- [ ] **Step 8.4: Implement** — in `rankingLabel`, map `times_higher_education` → `"Times Higher Ed"`, `us_news_national` → `"US News"`, keep `qs_world_university_rankings` → `"QS World"`. Use a lookup object with a titleized fallback for unknown keys.

- [ ] **Step 8.5: Run the test, verify it passes** — Expected: PASS.

- [ ] **Step 8.6: Commit**

```bash
git add frontend/src/pages/student/institution/InstitutionDetail.tsx frontend/src/pages/student/institution/InstitutionDetail.test.tsx
git commit -m "feat(institution): clean labels for Times Higher Ed + US News rankings"
```

---

## Task 9: Frontend — Sources footer

**Files:** Modify `InstitutionDetail.tsx` (OverviewTab); Test `InstitutionDetail.test.tsx`

- [ ] **Step 9.1: Write the failing test**

```tsx
it("renders a Sources footer from school_outcomes.sources", () => {
  // mock query → school_outcomes.sources = [{label, source, year, url}, ...]
  render(<InstitutionDetail institutionId="x" isAuthenticated />, { wrapper })
  expect(screen.getByRole("heading", { name: /Sources/i })).toBeInTheDocument()
  expect(screen.getByText(/College Scorecard/)).toBeInTheDocument()
})
```

- [ ] **Step 9.2: Run it, verify it fails** — Expected: FAIL.

- [ ] **Step 9.3: Implement** — add a `SourcesFooter` sub-component near the other Overview helpers and render it as the last card in `OverviewTab` (after Quick facts):

```tsx
function SourcesFooter({ sources }: { sources?: { label?: string; source: string; year?: number; url?: string }[] }) {
  if (!sources?.length) return null
  return (
    <Card className="p-5">
      <h2 className="font-semibold text-foreground mb-3 flex items-center gap-2">
        <FileText size={15} className="text-secondary" /> Sources
      </h2>
      <ul className="space-y-1.5">
        {sources.map((s, i) => (
          <li key={i} className="text-[12px] text-muted-foreground">
            {s.label ? <span className="text-foreground/80">{s.label}: </span> : null}
            {s.url ? (
              <a href={s.url} target="_blank" rel="noopener noreferrer" className="text-secondary hover:underline">{s.source}</a>
            ) : <span>{s.source}</span>}
            {s.year ? ` · ${s.year}` : ""}
          </li>
        ))}
      </ul>
    </Card>
  )
}
```
In `OverviewTab`, read `const sources = (inst.school_outcomes as any)?.sources` and render `<SourcesFooter sources={sources} />` as the final child. Import `FileText` from `lucide-react` (match the existing icon import style).

- [ ] **Step 9.4: Run the test, verify it passes** — Expected: PASS.

- [ ] **Step 9.5: Commit**

```bash
git add frontend/src/pages/student/institution/InstitutionDetail.tsx frontend/src/pages/student/institution/InstitutionDetail.test.tsx
git commit -m "feat(institution): sourced-citation footer on the Overview tab"
```

---

## Task 10: Sync the dev seed

**Files:** Modify `unipaith-backend/scripts/seed_dev_data.py:262-290` (MIT entry)

- [ ] **Step 10.1: Implement** — import the canonical constants and use them so dev mirrors prod:

```python
from unipaith.data import mit_profile
# ... when building the MIT Institution(...):
ranking_data={**mit_profile.RANKING_DATA},
school_outcomes={**mit_profile.SCHOOL_OUTCOMES},
description_text=mit_profile.DESCRIPTION,
student_body_size=mit_profile.UNDERGRAD_COUNT,
```
Leave the rest of the dev-seed MIT block (admin_user_id, city, etc.) as-is. (Schools/programs in the dev seed can stay minimal — `enrich_mit.py` / the migration build the full catalog; optionally call `mit_profile.apply(sync_session)` at the end of the seed if a sync session is convenient.)

- [ ] **Step 10.2: Verify the seed still runs**

Run: `cd unipaith-backend && make reset-dev` (or the project's reset+seed target) — confirm it completes and MIT loads.
Expected: seed completes; `curl localhost:8000/api/v1/institutions` shows MIT (after `make dev-backend`).

- [ ] **Step 10.3: Commit**

```bash
git add unipaith-backend/scripts/seed_dev_data.py
git commit -m "chore(seed): MIT dev seed mirrors the canonical profile"
```

---

## Task 11: Full verification + ship to production

- [ ] **Step 11.1: Backend green**

Run: `cd unipaith-backend && PYTHONPATH=src AI_MOCK_MODE=true .venv/bin/pytest tests/test_mit_profile.py -v --tb=short ; echo EXIT=$?`
Then ruff: `cd unipaith-backend && .venv/bin/ruff check src/unipaith/data/ scripts/enrich_mit.py alembic/versions/ ; echo EXIT=$?`
Expected: tests PASS, ruff clean (EXIT=0). Fix any line-length wraps.

- [ ] **Step 11.2: Frontend green**

Run: `cd frontend && npx tsc --noEmit ; echo EXIT=$?`
Run: `cd frontend && npx vitest run src/pages/student/institution/InstitutionDetail.test.tsx ; echo EXIT=$?`
Run: `cd frontend && npm run build ; echo EXIT=$?`
Expected: tsc 0, vitest PASS, build 0.

- [ ] **Step 11.3: Visual check (preview)** — start uvicorn (:8000) + vite (:5173) against the dev DB (after running `enrich_mit.py`), open the MIT page, confirm: hero shows only `#1 QS World · 1861 founded`; three rankings render; depth cards (test scores, financial aid, demographics, campus map) appear; Quick facts says "Undergraduates"; Schools (6); Programs catalog is full; Sources footer present. Screenshot for the summary.

- [ ] **Step 11.4: Merge to main**

```bash
git fetch origin && git rebase origin/main   # resolve any concurrent migration heads (merge revision if needed)
# re-run Step 11.1/11.2 after rebase
git push origin <branch>
gh pr create --title "MIT institution page: flagship data + presentation overhaul" --body "<summary + link to spec/plan>"
gh pr merge --squash
```
(If a concurrent session added an Alembic head during this work, create a merge revision per Task 4.1 and re-point — do NOT force-push.)

- [ ] **Step 11.5: Verify live deploy**

- Backend deploy runs `alembic upgrade heads` on container start → MIT enriched in prod. Watch the deploy (GitHub Actions `deploy-backend.yml`).
- Verify the API: `curl -s https://api.unipaith.co/api/v1/institutions/e885756a-dbf3-4140-879d-fa873dc07973 | python3 -m json.tool` → `ranking_data` has `times_higher_education` + `us_news_national`; `school_outcomes` has `test_scores`/`sources`/etc.; rich `description_text`.
- Verify schools/programs: `curl .../schools` → 6; `curl .../programs` → full catalog.
- Frontend (S3+CloudFront via `deploy-frontend.yml`): load `app.unipaith.co/s/institutions/e885756a-dbf3-4140-879d-fa873dc07973`, confirm hero/rankings/depth/label/sources. Invalidate CloudFront if the bundle looks stale.
- Confirm working tree clean, `main` at the new commit, deploy succeeded.

---

## Self-Review

**1. Spec coverage:**
- Gap 1 (header chips) → Task 6 ✓
- Gap 2 (rankings) → data (RANKING_DATA, Task 1) + labels (Task 8) ✓
- Gap 3 (student labels) → Task 7 (label) + UNDERGRAD_COUNT (Task 1) ✓
- Gap 4 (rich intro) → DESCRIPTION (Task 1) ✓
- Gap 5 (empty depth sections) → SCHOOL_OUTCOMES test_scores/financial_aid/demographics/location (Task 1) ✓
- Gap 6 (schools/programs) → Tasks 2 + 3 ✓
- Gap 7 (sources) → SCHOOL_OUTCOMES.sources (Task 1) + SourcesFooter (Task 9) ✓
- Data contract / provenance → mit_profile constants + sources convention ✓
- Delivery to prod (no schema migration) → data-only migration (Task 4) + entrypoint auto-runs it ✓
- Dev-seed sync → Task 10 ✓
- Testing (contract/idempotency/no-op + frontend) → Tasks 1–3, 6–9 ✓

**2. Placeholder scan:** The `if False` line in Step 3.3 is explicitly flagged for deletion (a clarity marker, not shipped). `tuition`/`acceptance_rate` left null-unless-cited is a deliberate anti-fabrication rule with named sources, not a vague TODO. The migration `down_revision`/`revision` are filled from `alembic heads` at build (correct handling of a moving head, not a placeholder). No "TBD/handle edge cases" remain.

**3. Type consistency:** `apply(session)` (sync) used identically in Tasks 1, 4, 5; `_apply_schools` returns the `school_by_name` map consumed by `_apply_programs` (Task 3); `PROGRAM_SLUGS` defined once and reused in the reconcile + tests; `school_outcomes.sources` shape `{label, source, year, url}` matches between the data (Task 1) and `SourcesFooter` (Task 9); `data-testid="hero-meta"` added in Task 6 and asserted there.
