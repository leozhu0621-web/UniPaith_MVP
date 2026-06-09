# School + Program Events/Updates + Social + Daily Refresh + Tooltip Cleanup — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend channel-sourced Events/Updates to the school (Sloan) + program (MBAn) profiles, scoped by keyword relevance over authoritative MIT channels, surface official social links, refresh daily, and declutter caption notes into hover tooltips.

**Architecture:** Add `school_id` (events + posts) and `program_id` (posts) scoping columns + `content_sources` on schools/programs; a pure `passes_relevance()` gate in the ingest; scope-aware upserts; a 24 h scheduler job; seed via `mit_profile.apply` + a data migration; frontend renders per-scope feeds + social links; tooltips via a shared `withTip` helper.

**Tech Stack:** FastAPI + SQLAlchemy 2 async + Alembic + APScheduler (backend); React 19 + Vite + TanStack Query (frontend).

**Spec:** `docs/superpowers/specs/2026-06-09-school-program-events-updates-design.md`

**Final `content_sources` shape (flat — extends the existing institution shape; no migration of MIT's current config):**
```json
{
  "news_rss": "https://news.mit.edu/rss/topic/sloan-school-management",
  "news_curated": true,
  "events_feed": { "url": "https://calendar.mit.edu/search/events.ics?search=sloan", "type": "ical" },
  "keywords": ["sloan", "mit sloan"],
  "social": { "instagram": "...", "linkedin": "...", "x": "...", "youtube": "...", "facebook": "..." }
}
```
Gate: `news` kept-all if `news_curated` true OR no `keywords`; else keyword-gated. `events` keyword-gated when `keywords` present, else kept-all. MIT institution row keeps its current un-keyworded config → kept-all (unchanged behavior).

---

## Phase 1 — Backend foundation: relevance gate + scoping columns

### Task 1: `passes_relevance()` pure gate

**Files:**
- Modify: `unipaith-backend/src/unipaith/services/content_ingest/base.py`
- Test: `unipaith-backend/tests/test_content_ingest_relevance.py` (create)

- [ ] **Step 1: Write the failing test**
```python
# tests/test_content_ingest_relevance.py
from unipaith.services.content_ingest.base import NormalizedItem, passes_relevance

def _item(title="", body="", location=None):
    return NormalizedItem(kind="event", external_id="x", title=title, body=body, location=location)

def test_curated_keeps_all():
    assert passes_relevance(_item(title="Anything"), [], curated=True) is True

def test_no_keywords_keeps_all():
    assert passes_relevance(_item(title="Anything"), [], curated=False) is True

def test_keyword_in_visible_text_kept():
    assert passes_relevance(_item(title="MIT Sloan info session"), ["sloan"]) is True
    assert passes_relevance(_item(title="Talk", body="Hosted at the Sloan building"), ["sloan"]) is True

def test_keyword_absent_dropped():
    assert passes_relevance(_item(title="Spring into Writing"), ["sloan"]) is False

def test_word_boundary_no_substring_false_positive():
    assert passes_relevance(_item(title="Prof. Sloane speaks"), ["sloan"]) is False

def test_case_insensitive():
    assert passes_relevance(_item(title="SLOAN reunion"), ["sloan"]) is True
```

- [ ] **Step 2: Run it — expect ImportError / fail**
`cd unipaith-backend && PYTHONPATH=src AI_MOCK_MODE=true .venv/bin/pytest tests/test_content_ingest_relevance.py -q`

- [ ] **Step 3: Implement in `base.py`** (append after `clean_text`):
```python
def passes_relevance(item: "NormalizedItem", keywords: list[str], curated: bool = False) -> bool:
    """Keep an item only when it is genuinely relevant to the scope.

    - curated feeds (MIT-authoritative topic feeds) are kept wholesale;
    - with no keywords there is no filter (institution-wide content);
    - otherwise a keyword must appear (case-insensitive, word-boundary) in the
      item's visible text — title + body + location.
    """
    if curated or not keywords:
        return True
    haystack = " ".join(filter(None, [item.title, item.body, item.location or ""])).lower()
    return any(
        re.search(rf"(?<!\w){re.escape(k.lower())}(?!\w)", haystack) for k in keywords
    )
```
(Reuses the module's existing `import re`.)

- [ ] **Step 4: Run tests — expect PASS** (same command).
- [ ] **Step 5: Commit** `git add -A && git commit -m "feat(ingest): keyword relevance gate (passes_relevance)"`

### Task 2: Scoping columns on events + institution_posts (model + migration)

**Files:**
- Modify: `unipaith-backend/src/unipaith/models/institution.py` (Event, InstitutionPost)
- Create migration via `make migration`

- [ ] **Step 1: Add columns to models.**
  - `Event`: after `source_url`, add
    ```python
    school_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="SET NULL"), index=True
    )
    ```
  - `InstitutionPost`: after `source_url`, add
    ```python
    school_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="SET NULL"), index=True
    )
    program_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("programs.id", ondelete="SET NULL"), index=True
    )
    ```
- [ ] **Step 2: Add `content_sources` to `School` and `Program` models** (see Task 3 — do in same edit so one migration captures all).
- [ ] **Step 3: Generate migration**
`cd unipaith-backend && make migration MSG="school/program content scoping (school_id, program_id, content_sources)"`
- [ ] **Step 4: Hand-verify the migration** adds: `events.school_id`, `institution_posts.school_id`, `institution_posts.program_id`, `schools.content_sources`, `programs.content_sources`, with indexes + FKs. Set `down_revision` to current head (`campusinfo1`). Rename revision id to `scope1`.
- [ ] **Step 5: Apply + smoke** `make dev-db` already up; `PYTHONPATH=src .venv/bin/alembic upgrade head` → no error.
- [ ] **Step 6: Commit** `git commit -am "feat(model): school_id/program_id scoping + content_sources on schools/programs"`

### Task 3: `content_sources` on School + Program

Done within Task 2 model edit:
```python
# in class School(...) and class Program(...)
content_sources: Mapped[dict | None] = mapped_column(JSONB)
```
(Same `JSONB` import already used in the file.)

---

## Phase 2 — Ingest extension

### Task 4: Scope-aware, gated ingest + iterate schools/programs + fix event status

**Files:**
- Modify: `unipaith-backend/src/unipaith/services/content_ingest/service.py`
- Modify: `unipaith-backend/src/unipaith/services/content_ingest/__init__.py` (export `passes_relevance`)
- Test: `unipaith-backend/tests/test_content_ingest_scoped.py` (create)

- [ ] **Step 1: Write failing tests** covering: school-scoped post writes `school_id`; program-scoped post writes `program_id`; event written with `status="upcoming"` + future `start_time`; gate drops a non-matching item; dedup keyed by scope (same external_id at institution + school both stored).
```python
# tests/test_content_ingest_scoped.py  (sketch — fill bodies against fixtures)
import pytest, uuid
from datetime import datetime, timedelta, UTC
from unipaith.services.content_ingest.base import NormalizedItem
from unipaith.services.content_ingest.service import ContentIngestService
from unipaith.models.institution import Institution, School, Event, InstitutionPost
pytestmark = pytest.mark.asyncio

async def test_school_scoped_post_tagged(db_session):
    inst = Institution(name="MIT", type="university", country="US", description_text="x", student_body_size=1, admin_user_id=None)
    # ... create inst + school, then:
    svc = ContentIngestService(db_session)
    items=[NormalizedItem(kind="post", external_id="a1", title="MIT Sloan launches", body="...")]
    n = await svc.upsert_posts(inst_id=inst.id, items=items, source="news_rss",
                               school_id=school.id, keywords=["sloan"], curated=True)
    assert n == 1
    row = (await db_session.scalars(select(InstitutionPost))).first()
    assert row.school_id == school.id and row.institution_id == inst.id

async def test_event_status_upcoming_and_gated(db_session):
    svc = ContentIngestService(db_session)
    fut = datetime.now(UTC)+timedelta(days=5)
    items=[NormalizedItem(kind="event", external_id="e1", title="Sloan talk", start_time=fut),
           NormalizedItem(kind="event", external_id="e2", title="Random talk", start_time=fut)]
    n = await svc.upsert_events(inst_id=inst.id, items=items, school_id=school.id, keywords=["sloan"])
    assert n == 1  # only the Sloan one passes the gate
    ev = (await db_session.scalars(select(Event))).first()
    assert ev.status == "upcoming" and ev.school_id == school.id
```

- [ ] **Step 2: Run — expect failures.**

- [ ] **Step 3: Rewrite `service.py`.** Key changes:
  - `upsert_posts(self, inst_id, items, source, *, school_id=None, program_id=None, keywords=None, curated=False)`:
    - filter `items` through `passes_relevance(it, keywords or [], curated)`;
    - dedup query adds `InstitutionPost.school_id == school_id`, `InstitutionPost.program_id == program_id`;
    - new rows set `school_id`, `program_id`.
  - `upsert_events(self, inst_id, items, *, school_id=None, program_id=None, keywords=None)`:
    - gate with `passes_relevance(it, keywords or [], curated=False)`;
    - dedup query adds `Event.school_id == school_id` (program_id already a column — set + match);
    - **new rows set `status="upcoming"`** (was `"live"` — fixes the read-path mismatch with `list_upcoming_events`);
    - set `school_id`, `program_id`.
  - `ingest_institution(inst)`: read `cfg.get("news_curated", False)`, `cfg.get("keywords")`; pass to upserts; pass `school_id=None, program_id=None`.
  - New `_ingest_scope(self, *, inst_id, cfg, school_id=None, program_id=None)` extracting the news/events handling shared by institution/school/program.
  - `ingest_all()`: after institutions, also:
    ```python
    for sch in (await self.session.scalars(select(School).where(School.content_sources.isnot(None)))).all():
        await self._ingest_scope(inst_id=sch.institution_id, cfg=sch.content_sources, school_id=sch.id)
    for prog in (await self.session.scalars(select(Program).where(Program.content_sources.isnot(None)))).all():
        await self._ingest_scope(inst_id=prog.institution_id, cfg=prog.content_sources, program_id=prog.id)
    ```
  - Mirror the gate + scope + `status="upcoming"` in `seed_populate_sync`, and add `seed_populate_sync_scope(session, *, inst_id, cfg, school_id=None, program_id=None)` for the migration to call per school/program.
- [ ] **Step 4: Run tests — expect PASS.**
- [ ] **Step 5: Commit** `git commit -am "feat(ingest): scope-aware gated upserts + iterate schools/programs + status=upcoming"`

---

## Phase 3 — API

### Task 5: events `school_id` filter

**Files:** `unipaith-backend/src/unipaith/services/event_service.py`, `src/unipaith/api/events.py`, `src/unipaith/schemas/event.py`, `frontend/src/api/events.ts`
- [ ] `list_upcoming_events(..., school_id: UUID | None = None)` → `if school_id: query = query.where(Event.school_id == school_id)`.
- [ ] `api/events.py` `list_upcoming_events` route: add `school_id: UUID | None = Query(None)` and pass through.
- [ ] `schemas/event.py` `EventResponse`: add `school_id: UUID | None = None`.
- [ ] `frontend/src/api/events.ts` `listEvents` params type: add `school_id?: string`.
- [ ] Test: `GET /events?school_id=` returns only that school's upcoming events. Commit.

### Task 6: public posts `school_id` / `program_id` filter + fields

**Files:** `src/unipaith/api/institutions.py` (`get_public_posts` route + service), the `InstitutionService.get_public_posts`, `PostResponse` schema (imported at `institutions.py:63`)
- [ ] `get_public_posts(institution_id, school_id: UUID | None = Query(None), program_id: UUID | None = Query(None), db)` → `svc.get_public_posts(institution_id, school_id=school_id, program_id=program_id)`.
- [ ] Service `get_public_posts`: add optional `school_id`/`program_id` filters to the query (and keep `status == "published"`).
- [ ] `PostResponse`: add `school_id: UUID | None = None`, `program_id: UUID | None = None` (already exposes `source`, `source_url`).
- [ ] `frontend/src/api/institutions.ts` `getPublicPosts(institutionId, params?: {school_id?; program_id?})` → pass as query params.
- [ ] Test: `GET /institutions/{id}/posts?school_id=` filters. Commit.

### Task 7: expose `content_sources` on school/program responses

**Files:** `src/unipaith/api/institutions.py` (`get_institution_schools` dict ~1532, `get_school_programs`), program-detail responses (`programs.py` / wherever program detail is serialized), `frontend/src/types/index.ts`
- [ ] Add `"content_sources": s.content_sources` to the `get_institution_schools` dict.
- [ ] Add `content_sources` to the school-programs + program-detail response (find the serializer; add the field).
- [ ] `frontend/src/types/index.ts`: `School.content_sources?` + `Program.content_sources?` typed as `{ social?: Record<string,string|null>; news_rss?: string; events_feed?: {url:string;type:string}; keywords?: string[] } | null`.
- [ ] Commit.

---

## Phase 4 — Daily self-refresh

### Task 8: scheduler job + config flags

**Files:** `src/unipaith/config.py`, `src/unipaith/core/scheduler.py`, `infra/ecs.tf` (env), test `tests/test_scheduler_content_ingest.py`
- [ ] `config.py`: add `content_ingest_refresh_enabled: bool = False` (+ `content_ingest_refresh_hours: int = 24`). (Prod enabled via ECS env, mirroring other flags.)
- [ ] `scheduler.py`: add after the digest block:
```python
if settings.content_ingest_refresh_enabled:
    scheduler.add_job(
        _run_content_ingest_refresh, "interval",
        hours=settings.content_ingest_refresh_hours,
        id="content_ingest_refresh", name="Daily Content Ingest Refresh", **_job_defaults(),
    )
```
and the handler:
```python
async def _run_content_ingest_refresh() -> None:
    from unipaith.database import async_session
    from unipaith.services.content_ingest import ContentIngestService
    try:
        async with async_session() as session:
            totals = await ContentIngestService(session).ingest_all()
            await session.commit()
        logger.info("Content ingest refresh: %s", totals)
    except Exception as exc:  # noqa: BLE001 — never break the scheduler
        logger.warning("Content ingest refresh failed: %s", exc)
```
- [ ] `infra/ecs.tf`: add `CONTENT_INGEST_REFRESH_ENABLED = "true"` to the backend env block.
- [ ] Test: with the flag set, `setup_scheduler()` registers a job named "Daily Content Ingest Refresh"; the handler swallows a raising `ingest_all`. Commit.

---

## Phase 5 — Seeding (real data)

### Task 9: `mit_profile.apply` sets Sloan + MBAn content_sources

**Files:** `src/unipaith/data/mit_profile.py`, `tests/test_mit_profile.py`
- [ ] Define module constants:
```python
_SLOAN_CONTENT = {
    "news_rss": "https://news.mit.edu/rss/topic/sloan-school-management",
    "news_curated": True,
    "events_feed": {"url": "https://calendar.mit.edu/search/events.ics?search=sloan", "type": "ical"},
    "keywords": ["sloan", "mit sloan"],
    "social": {
        "instagram": "https://www.instagram.com/mitsloan/",
        "linkedin": "https://www.linkedin.com/company/mit-sloan-school-of-management",
        "x": "https://twitter.com/mitsloan",
        "youtube": "https://www.youtube.com/user/MITSloan",
        "facebook": "https://www.facebook.com/MITSloan",
    },
}
_MBAN_CONTENT = {
    "news_rss": "https://news.mit.edu/rss/topic/operations-research",
    "news_curated": False,
    "events_feed": {"url": "https://calendar.mit.edu/search/events.ics?search=business+analytics", "type": "ical"},
    "keywords": ["mban", "business analytics", "master of business analytics", "operations research"],
    "social": {  # MBAn inherits Sloan's links + ORC X (no unverified @mit.analytics)
        "instagram": "https://www.instagram.com/mitsloan/",
        "linkedin": "https://www.linkedin.com/company/mit-sloan-school-of-management",
        "x": "https://x.com/orcenter",
        "youtube": "https://www.youtube.com/user/MITSloan",
        "facebook": "https://www.facebook.com/MITSloan",
    },
}
```
- [ ] In `apply()`: after schools are reconciled, set `content_sources` on the Sloan School row (match `name == "MIT Sloan School of Management"`); after programs, set it on the MBAn Program row (`slug == "mit-sloan-mban"`).
- [ ] `tests/test_mit_profile.py`: assert Sloan school row `content_sources["news_curated"] is True` + 5 social keys; MBAn program row `content_sources["keywords"]` contains "business analytics" + social x == orcenter. Commit.

### Task 10: data migration to populate on deploy

**Files:** new `alembic/versions/seedscp1_*.py` (down_revision = `scope1`)
- [ ] `upgrade()`: `mit_profile.apply(session)` (sets content_sources), then for the Sloan School + MBAn Program rows call `seed_populate_sync_scope(session, inst_id=..., cfg=..., school_id=.../program_id=...)`. Fail-soft. `downgrade()` no-op.
- [ ] Verify single head: `PYTHONPATH=src .venv/bin/alembic heads` → one head. Apply locally. Commit.

---

## Phase 6 — Frontend rendering

### Task 11: types
- [ ] `frontend/src/types/index.ts`: `InstitutionPost` += `school_id?`, `program_id?` (source/source_url already added prior); `Event`/event item += `school_id?`. (Done partly in Task 7.) Commit.

### Task 12: SchoolSubunitPage Updates tab + social row
**Files:** `frontend/src/pages/student/SchoolSubunitPage.tsx`
- [ ] Add queries: `listEvents({ school_id: schoolId, limit: 10 })` and `getPublicPosts(institutionId, { school_id: schoolId })`.
- [ ] Replace the empty `tab === 'updates'` placeholder with: Updates list (posts) + Events list, each with `via {host} ↗` attribution when `source !== 'manual'`; honest empty state when both empty.
- [ ] Add a social-links row (Task 14 component) from `school.content_sources?.social`.
- [ ] Commit.

### Task 13: ProgramDetailPage Updates + social row
**Files:** `frontend/src/pages/student/ProgramDetailPage.tsx`
- [ ] Add `getPublicPosts(institutionId, { program_id: programId })` query → render an Updates list (reuse pattern) with attribution. (Events already query `program_id`.)
- [ ] Add social-links row from `program.content_sources?.social`.
- [ ] Commit.

### Task 14: shared SocialLinks + attribution helper
**Files:** `frontend/src/components/SocialLinks.tsx` (create), reuse `sourceHost` from PostCard
- [ ] `SocialLinks({ social }: { social?: Record<string,string|null> | null })` → row of icon links (Instagram/LinkedIn/X/YouTube/Facebook), each `target="_blank" rel="noopener noreferrer"`, skipping null/absent; renders nothing if empty.
- [ ] Export `sourceHost` to a shared util if not already, reuse in both pages.
- [ ] Commit.

---

## Phase 7 — Tooltip cleanup (spec §5 inventory)

### Task 15: shared `withTip` helper
**Files:** `frontend/src/components/ui/withTip.tsx` (create) — a tiny wrapper adding `title` + `aria-label` to a value/heading. Commit.

### Task 16: KeyMetrics — one change covers 22 captions
**Files:** `frontend/src/pages/student/program/KeyMetrics.tsx`
- [ ] At the hero value `<p>` (:515–520, already `title={tile.value}`), set `title={tile.context ? `${tile.value} — ${tile.context}` : tile.value}` and **remove** the printed `{tile.context}` `<p>` at :524. Commit.

### Task 17: InstitutionDetail — render-site hints + per-section headings
**Files:** `frontend/src/pages/student/institution/InstitutionDetail.tsx`
- [ ] Stat hints: at the three render sites (keyStats hint :508, OutcomeStat hint :1160, Fact hint :1172) drop the printed `<p>` and add `title={hint}` to the value `<p>`.
- [ ] Per-section caption→heading title: enrollment (:636→Diversity h2 :628), Carnegie (:657→Quick-facts h2 :647), "Among faculty & alumni" (:777→Recognition h2 :776), research summary (:799→Research h2 :797), sticker cost (:572→net-price value :569), event spots (:1079→event h3).
- [ ] Condense: shorten the net-price sentence (:570). Commit.

### Task 18: remaining files
**Files:** `ProgramDetailPage.tsx` (:476, :848, :1012, :1264, :1289/:1293/:1301, :1367, :1537, :1576, :1583 + condense :1356/:1415/:1495), `program/StatGroup.tsx` (:107/:110/:124/:127 unit→title on value :58), `program/InsightsPanel.tsx` (:236/:364/:405/:316/:471), `program/NetPriceEstimator.tsx` (:56/:58/:95/:114/:183), `program/NextStepsCard.tsx` (:124 hint→button title), `institution/overviewWidgets.tsx` (:142 StatBar hint, :94 funnel cycle), `SchoolSubunitPage.tsx` (:167 "offered", :257 StatTile labels), `SchoolSubunitPage.tsx` footer condense (:358)
- [ ] Apply `title=` conversions per spec §5.2–§5.6. NEVER touch the §5.5 keep list (Source:/Data sources:/via-host/follow-helper/sub-section labels). Commit per file or in 2–3 logical commits.

---

## Phase 8 — Verify + ship

### Task 19: full gate + deploy + verify live
- [ ] Backend: `cd unipaith-backend && PYTHONPATH=src AI_MOCK_MODE=true .venv/bin/ruff check . && PYTHONPATH=src DATABASE_URL=... COGNITO_BYPASS=true AI_MOCK_MODE=true S3_LOCAL_MODE=true .venv/bin/pytest tests/test_content_ingest_relevance.py tests/test_content_ingest_scoped.py tests/test_scheduler_content_ingest.py tests/test_mit_profile.py tests/test_events*.py -q ; echo EXIT=$?` → all green; then full suite.
- [ ] Frontend: `cd frontend && npm run build` (tsc -b + vite) → 0 errors; `npx vitest run` smoke.
- [ ] Confirm single alembic head; clean working tree (purge any iCloud `" 2.*"` dups).
- [ ] PR → merge to `main` → backend + frontend auto-deploy.
- [ ] Verify live: backend deploy runs `scope1` + `seedscp1`; `curl -s https://api.unipaith.co/api/v1/institutions/{MIT_id}/schools` includes Sloan `content_sources`; `GET /events?school_id={sloan}` returns the gated Sloan event(s); Sloan + MBAn pages on app.unipaith.co show Updates + social links; grep live frontend bundle for the new SocialLinks/Updates strings.
- [ ] Confirm scheduler logs "Daily Content Ingest Refresh" registered in ECS logs.

---

## Self-review notes
- **Spec coverage:** §3 manifest → Task 9; §4.1 columns → Task 2/3; §4.2 gate+scope → Task 1/4; §4.3 SocialSource = out-of-scope seam (no live wiring) — flag only, not built this round (acceptable per spec §7); §4.4 API → Task 5/6/7; §4.5 frontend → Task 12/13/14; §4.6 seeding → Task 9/10; §4.7 daily refresh → Task 8; §5 tooltips → Task 15–18; §6 tests → Tasks 1/4/5/6/8/9.
- **SocialSource note:** §4.3 describes a flag-gated adapter interface. This round ships the *links* + the daily refresh; the `SocialSource` post-ingestion class is left as the documented seam (flag `content_social_ingest_enabled` not added until a provider exists) — within spec §7 "out of scope (flag stays off)".
- **Latent bug fixed:** ingest `status="live"` → `"upcoming"` so events surface via `list_upcoming_events` (Task 4).
- **Type consistency:** `passes_relevance(item, keywords, curated)` signature is identical across Tasks 1/4; `content_sources` flat shape identical across Tasks 4/9/7.
