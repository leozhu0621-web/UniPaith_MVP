# Channel-sourced Events & Updates + Campus-info Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:executing-plans (inline) — steps use checkbox syntax.

**Goal:** Auto-populate a school's Events/Updates from its public news RSS + events iCal into the existing `Event`/`InstitutionPost` tables (editable by the school), and add Campus-life / Campus & basics sections to the About tab. MIT-first.

**Architecture:** A `content_ingest` service with a pluggable `ChannelSource` interface (news-RSS → posts, events-iCal/RSS → events). Per-institution `content_sources` config (seeded for MIT). A `refresh` ops endpoint + daily schedule. Auto rows are flagged `source`/`source_url`, deduped by `external_id`, render in existing tabs with a "via {source}" link. Campus sections are pure frontend over existing `school_outcomes`.

**Tech Stack:** FastAPI · SQLAlchemy 2 async · Alembic · `feedparser` (RSS) · `icalendar` (iCal) · React/TS.

---

### Task 1: Dependencies
- [ ] Add `feedparser` and `icalendar` to `unipaith-backend/pyproject.toml` deps; install into `.venv`.
- [ ] Verify import: `python -c "import feedparser, icalendar"`.

### Task 2: Model columns
**Files:** Modify `src/unipaith/models/institution.py`
- [ ] `Institution`: `content_sources: Mapped[dict | None] = mapped_column(JSONB)`.
- [ ] `Event` + `InstitutionPost`: `source: Mapped[str] = mapped_column(String(24), default="manual", server_default="manual")`, `external_id: Mapped[str | None] = mapped_column(String(500))`, `source_url: Mapped[str | None] = mapped_column(String(1000))`.

### Task 3: Schema exposure
**Files:** `src/unipaith/api/events.py` (EventResponse), `src/unipaith/api/institutions.py` (PostResponse + post/event list dicts)
- [ ] Add `source`, `source_url` to the Event + Post response models/dicts so the frontend can show attribution.

### Task 4: NormalizedItem + ChannelSource interface
**Files:** Create `src/unipaith/services/content_ingest/__init__.py`, `base.py`
- [ ] `NormalizedItem` dataclass `{kind: 'post'|'event', external_id, title, body, url, published_at, start_time, end_time, location}`.
- [ ] `ChannelSource` ABC: `name`, `fetch(institution) -> list[NormalizedItem]`.

### Task 5: NewsRssSource (TDD)
**Files:** Create `src/unipaith/services/content_ingest/rss.py`; Test `tests/test_content_ingest.py`
- [ ] Test: feed a sample RSS string → returns post items with external_id (guid), title, body, url, published_at.
- [ ] Implement with feedparser (`feedparser.parse(text)`), map entries → NormalizedItem(kind='post'). Cap 25.

### Task 6: EventsFeedSource (TDD)
**Files:** Create `src/unipaith/services/content_ingest/events_feed.py`
- [ ] Test: feed a sample iCal VCALENDAR string → returns event items with UID→external_id, DTSTART/DTEND→start/end, SUMMARY→title, LOCATION, URL. Skip events with no start.
- [ ] Implement with `icalendar.Calendar.from_ical`; for `type=='rss'` fall back to feedparser. Keep upcoming + recent (last 180d). Cap 25.

### Task 7: ContentIngestService (TDD)
**Files:** Create `src/unipaith/services/content_ingest/service.py`
- [ ] Test (async, db_session): institution with content_sources → ingest_institution upserts InstitutionPost + Event with source/source_url/published_at, status='published'.
- [ ] Test: re-run → idempotent (no dupes; dedup by (institution_id, source, external_id)).
- [ ] Test: a row a school set to 'archived' is NOT re-published.
- [ ] Implement: build sources from config (news_rss→NewsRssSource, events_feed→EventsFeedSource), fetch (fail-soft per source, log), upsert with dedup; `ingest_all(session)` over institutions with content_sources.

### Task 8: Refresh endpoint
**Files:** Modify `src/unipaith/api/` (a small admin/ops router) + register
- [ ] `POST /admin/content-ingest/refresh?institution_id=` (system-guarded like other ops endpoints) → runs ingest for one or all; returns counts.

### Task 9: MIT seed
**Files:** Modify `src/unipaith/data/mit_profile.py`
- [ ] In `apply()`, set `inst.content_sources = {news_rss: "https://news.mit.edu/rss/feed", events_feed: {url: "https://calendar.mit.edu/calendar.ics", type: "ical"}, social: {x:null,instagram:null,linkedin:null,youtube:null}}` (idempotent).
- [ ] Test (test_mit_profile): assert `inst.content_sources["news_rss"]` set.

### Task 10: Migration
**Files:** Create `alembic/versions/contentsrc1_*.py` (off current head)
- [ ] add_column content_sources (institutions), source/external_id/source_url (events, institution_posts) + partial-unique indexes; then `mit_profile.apply()` to seed MIT.

### Task 11: Frontend — attribution
**Files:** `frontend/src/types/index.ts` (Event/Post types + source/source_url), `connect/EventsTab.tsx` + `UpdatesTab.tsx` (or InstitutionDetail tabs)
- [ ] When `source && source !== 'manual'`, show "via {sourceLabel}" linking to `source_url`.

### Task 12: Frontend — Campus sections on About
**Files:** `frontend/src/pages/student/institution/InstitutionDetail.tsx` (AboutTab)
- [ ] Add **Campus life** (varsity_sports, athletics_division, arts_groups, residence_halls from `school_outcomes.campus_life`) and **Campus & basics** (founded, setting, campus_acres, student_faculty_ratio, faculty_count, undergrad_majors/minors, endowment from `scale` + inst) — render tiles only when present.

### Task 13: Ship + seed prod + validate
- [ ] tsc -b · ruff · backend tests · single head · build green.
- [ ] Merge → deploy. Migration seeds MIT content_sources; call `refresh?institution_id=MIT` (ops) to populate.
- [ ] Verify: MIT Updates show MIT News (via link), Events show calendar items, About shows Campus sections.
</content>
