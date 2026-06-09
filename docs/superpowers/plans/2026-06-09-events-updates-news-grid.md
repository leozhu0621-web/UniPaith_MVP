# Events & Updates News Grid — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Render Events & Updates as a uniform image-card news grid (real source images for news, gradient+date for events) on institution/school/program, and fix the cross-scope duplicate.

**Architecture:** Capture `image_url` from the feed (`media:content`) through parser → model → ingest → API response → frontend type; add an `institution_scope` filter to dedup the institution lists; one shared `NewsGrid` React component used at all three levels.

**Tech Stack:** FastAPI + SQLAlchemy + Alembic + feedparser (backend); React 19 + Vite + TanStack Query (frontend).

**Spec:** `docs/superpowers/specs/2026-06-09-events-updates-news-grid-design.md`

---

## Phase 1 — Backend: capture image_url

### Task 1: `image_url` on NormalizedItem + parsers
**Files:** `unipaith-backend/src/unipaith/services/content_ingest/base.py`, `rss.py`, `events_feed.py`; Test: `tests/test_content_ingest_image.py`
- [ ] Add `image_url: str | None = None` to the `NormalizedItem` dataclass (after `location`).
- [ ] `rss.py` `NewsRssSource.parse`: after building title/body, derive
  ```python
  img = None
  mc = getattr(entry, "media_content", None)
  if mc and isinstance(mc, list) and mc and mc[0].get("url"):
      img = mc[0]["url"]
  elif getattr(entry, "media_thumbnail", None):
      mt = entry.media_thumbnail
      img = mt[0].get("url") if mt and mt[0].get("url") else None
  ```
  and pass `image_url=img` into `NormalizedItem`.
- [ ] `events_feed.py`: iCal items pass `image_url=None`; the RSS-fallback path may set it from the shared rss parse (it already delegates to `NewsRssSource`-like fields) — set `image_url=getattr(p, "image_url", None)` where it maps `p`.
- [ ] Test `tests/test_content_ingest_image.py`:
  ```python
  from unipaith.services.content_ingest.rss import NewsRssSource
  RSS_WITH_IMG = '''<rss xmlns:media="http://search.yahoo.com/mrss/"><channel><item>
  <title>AI news</title><link>https://news.mit.edu/x</link><guid>g1</guid>
  <media:content url="https://news.mit.edu/img.jpg"/></item></channel></rss>'''
  def test_rss_extracts_media_content_image():
      items = NewsRssSource().parse(RSS_WITH_IMG)
      assert items[0].image_url == "https://news.mit.edu/img.jpg"
  def test_rss_no_image_is_none():
      items = NewsRssSource().parse('<rss><channel><item><title>t</title><guid>g</guid><link>l</link></item></channel></rss>')
      assert items[0].image_url is None
  ```
- [ ] Run: `PYTHONPATH=src AI_MOCK_MODE=true .venv/bin/pytest tests/test_content_ingest_image.py -v` → PASS. Commit.

## Phase 2 — Backend: persist + expose image_url

### Task 2: columns + models + migration
**Files:** `models/institution.py` (Event, InstitutionPost); migration `imgurl1`
- [ ] Add to both models after `source_url`: `image_url: Mapped[str | None] = mapped_column(String(1000))`.
- [ ] Hand-write migration `alembic/versions/imgurl1_event_post_image_url.py` (down_revision = current head `seedscp1`): `op.add_column("events", sa.Column("image_url", sa.String(1000), nullable=True))` + same for `institution_posts`; downgrade drops both.
- [ ] Verify single head: `.venv/bin/alembic heads` → one head. Validate on scratch DB. Commit.

### Task 3: ingest writes image_url + responses expose it
**Files:** `content_ingest/service.py`, `schemas/event.py`, `schemas/institution.py`, `services/institution_service.py`
- [ ] `upsert_posts`/`upsert_events`: on insert set `image_url=it.image_url`; on the update path set `existing.image_url = it.image_url`. Mirror in `_seed_scope_sync` inserts.
- [ ] `EventResponse` += `image_url: str | None = None`; `PostResponse` += `image_url: str | None = None`; `_enrich_post(...)` passes `image_url=post.image_url`.
- [ ] Extend `tests/test_content_ingest_scoped.py`: a post upserted from an item with `image_url` persists it. Run targeted tests. Commit.

## Phase 3 — Backend: institution-scope dedup

### Task 4: institution_scope filter
**Files:** `services/institution_service.py` (`get_public_posts`), `services/event_service.py` (`list_upcoming_events`), `api/institutions.py`, `api/events.py`; Test: `tests/test_content_ingest_scoped.py`
- [ ] `get_public_posts(self, institution_id, school_id=None, program_id=None, institution_scope=False)`: if `institution_scope`, add `.where(InstitutionPost.school_id.is_(None), InstitutionPost.program_id.is_(None))`.
- [ ] `list_upcoming_events(..., institution_scope: bool = False)`: if set, `.where(Event.school_id.is_(None), Event.program_id.is_(None))`.
- [ ] Routes: `GET /institutions/{id}/posts` + `GET /events` accept `institution_scope: bool = Query(False)`, pass through.
- [ ] Test: seed institution-scope + school-scope copies of same external_id; `get_public_posts(institution_scope=True)` returns 1 (no dupe). Run. Commit.

## Phase 4 — Backend: seed migration (backfill images)

### Task 5: repopulate migration
**Files:** migration `imgseed1` (down_revision `imgurl1`)
- [ ] `upgrade()`: `mit_profile.apply(session)` then `_seed_scope_sync` is not enough for image backfill on EXISTING rows (seed only inserts new). Instead call the async-equivalent update path: import `ContentIngestService` won't run sync. Simplest: run `seed_populate_sync` + `seed_populate_sync_scope` which on existing rows are skipped — so to backfill images on existing rows, add an UPDATE: for MIT/Sloan/MBAn, re-fetch the news feed and `UPDATE ... SET image_url` by `external_id`. Implement a small sync helper `backfill_images_sync(session, *, inst_id, cfg, school_id, program_id)` in `content_ingest/service.py` that fetches the news feed, and for each item updates the matching row's `image_url` if currently null. Call it for institution + Sloan + MBAn. Fail-soft.
- [ ] Single head check + scratch-DB validate. Commit.

## Phase 5 — Frontend: NewsGrid component

### Task 6: NewsGrid + types
**Files:** Create `frontend/src/components/NewsGrid.tsx`; modify `frontend/src/types/index.ts`
- [ ] Types: `InstitutionPost` += `image_url?: string | null`; the event item type (or `any`) reads `image_url`.
- [ ] `NewsGrid({ posts, events })`: build a unified item list — posts → `{kind:'post', id, title, dek:body, url:source_url, host, image:image_url, date:published_at||created_at, source}`; events → `{kind:'event', id, title, location, url:source_url, host, date:start_time, source, eventId:id, eventName:event_name}`. Sort by date desc. Render `grid grid-cols-1 sm:grid-cols-2 gap-4`.
  - Post card: `<a href={url} target=_blank>` with image (or gradient fallback), title (line-clamp-2), dek (line-clamp-2), footer `via {host} ↗` + date.
  - Event card: gradient header (`bg-gradient-to-br from-secondary/15 to-muted`) with `Calendar` glyph + date badge; title; location; footer `Add to calendar` (calls `addEventToCalendar(eventId, eventName)`) + `via {host} ↗`.
  - Honest empty state when both empty.
  - Shared `hostOf(url)` helper inside the file.
- [ ] Commit.

## Phase 6 — Frontend: wire all three levels

### Task 7: institution
**Files:** `InstitutionDetail.tsx`
- [ ] Posts/events queries pass `institution_scope: true` (`getPublicPosts(id, { institution_scope: true })` — extend the client param; `listEvents({ institution_id, institution_scope: true })`).
- [ ] The `tab === 'events'` block renders `<NewsGrid posts={postList} events={eventList} />` instead of the EventsTab/UpdatesTab sections. Remove now-unused `EventsTab`/`UpdatesTab` if unreferenced (keep if still used elsewhere — grep first).
- [ ] Frontend client: `getPublicPosts` + `listEvents` accept `institution_scope`. Commit.

### Task 8: school
**Files:** `SchoolSubunitPage.tsx`
- [ ] The `tab === 'updates'` block renders `<NewsGrid posts={postList} events={eventList} />` (+ keep the SocialLinks row above it). Remove the inline `EventRow`/PostCard lists. Commit.

### Task 9: program
**Files:** `ProgramDetailPage.tsx`, `program/RelatedSidebar.tsx`
- [ ] Add an `'events_updates'` tab (`{ id, label: 'Events & Updates' }`) to the program tabs; render `<NewsGrid posts={programPosts} events={eventsList} />`.
- [ ] Remove the program-Updates list previously added to the Overview tab.
- [ ] Remove the "Upcoming Events" block from `RelatedSidebar` (now in the tab); drop the now-unused `onRsvp`/`upcomingEvents` wiring if orphaned. Commit.

## Phase 7 — Ship

### Task 10: gate + deploy + verify
- [ ] `ruff check src/ tests/` clean; targeted backend tests green; single alembic head.
- [ ] `npm run build` (tsc -b + vite) clean; `npx vitest run` green (update any test asserting the old list layout).
- [ ] PR → merge to main → backend + frontend deploy → verify: `GET /institutions/{MIT}/posts?institution_scope=true` has no duplicate titles; posts carry `image_url`; the live pages show the image-card grid; bundle grep.

---

## Self-review
- **Spec coverage:** §3.1 image capture → Tasks 1–3; §3.2 dedup → Task 4; §3.3 NewsGrid → Task 6; §3.4 levels → Tasks 7–9; §4 seed → Task 5; §5 tests → Tasks 1/3/4/6/10.
- **Backfill nuance (Task 5):** seed only inserts new rows, so existing rows need an explicit `image_url` UPDATE — captured as `backfill_images_sync`. (Alternatively the daily refresh's update path backfills within 24h; the migration just accelerates it.)
- **Type consistency:** `image_url` (snake) backend, `image_url?` frontend type, `institution_scope` bool param consistent across service/route/client.
- **RSVP:** the grid is RSVP-free by design (Add to calendar only) — consistent across levels.
