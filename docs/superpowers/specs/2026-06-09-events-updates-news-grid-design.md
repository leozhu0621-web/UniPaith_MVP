# Events & Updates — news-magazine grid (all levels) — Design

**Date:** 2026-06-09
**Status:** Approved design (user approved 2026-06-09)
**Reference:** Apple News-style card grid (user-provided)

## 1. Goal

Render **Events & Updates** as a news-magazine **uniform image-card grid** — "small boxes with pics" — on **all three levels** (institution, school, program). News cards show the **real source image**; event cards (no source image) show a clean gradient + date card. Fix the cross-scope duplicate bug surfaced on the institution page along the way.

## 2. Verified facts (no fabrication)

- **News images exist in the feed.** MIT News RSS provides `media:content url="…"` on every item; `feedparser` surfaces it as `entry.media_content[0]["url"]`. No per-article `og:image` fetch needed.
- **Events have no image.** `calendar.mit.edu` iCal exposes only `URL:` (the event link), no `ATTACH`/`IMAGE`. Event cards therefore use a gradient + calendar/date treatment — never a fabricated image.
- **Cross-scope duplicate confirmed.** `GET /institutions/{MIT}/posts` returns 56 posts with 4 duplicated titles — each duplicated title exists once at institution scope (`school_id=NULL`) and once at school scope (`school_id=Sloan`). The institution list returns all scopes, so the same article renders twice. (School/program lists filter by `school_id`/`program_id`, so they're already dupe-free.)

## 3. Architecture

### 3.1 Backend — capture the source image

- `NormalizedItem` gains `image_url: str | None`.
- `rss.py` (`NewsRssSource.parse`): set `image_url` from the first `entry.media_content` entry that has a `url` (fallback to `entry.media_thumbnail` if present); else `None`.
- `events_feed.py` (`EventsFeedSource`): `image_url = None` (iCal has no image). The RSS-fallback path may pick up a media image if present.
- Models: add nullable `image_url` (`String(1000)`) to `Event` and `InstitutionPost` (one migration, no index needed).
- Ingest (`content_ingest/service.py`): `upsert_posts`/`upsert_events` set `image_url` on insert **and** refresh it on the update path (so existing rows backfill on the next run). `_seed_scope_sync` mirrors it.
- Schemas: `EventResponse` and `PostResponse` expose `image_url: str | None = None`; `_enrich_post` passes `post.image_url`.

### 3.2 Backend — fix the cross-scope duplicate (institution scope)

- `InstitutionService.get_public_posts(institution_id, school_id=None, program_id=None, institution_scope=False)`: when `institution_scope=True`, add `school_id IS NULL AND program_id IS NULL`.
- `EventService.list_upcoming_events(..., institution_scope=False)`: same filter.
- API: `GET /institutions/{id}/posts` and `GET /events` accept `institution_scope: bool = Query(False)`.
- The **institution** detail page passes `institution_scope=true` for both its posts and events queries. School/program pages keep filtering by `school_id`/`program_id` (unchanged — already dupe-free). Net: MIT page shows MIT-wide items once; the Sloan-scoped copy shows only on Sloan's page.

### 3.3 Frontend — shared `NewsGrid` component

`frontend/src/components/NewsGrid.tsx` — a responsive uniform card grid (`grid-cols-1 sm:grid-cols-2`, `gap-4`). Input: an array of normalized items built from posts + events, sorted by date descending (events by `start_time`, posts by `published_at`/`created_at`).

- **Update (post) card:** `image_url` photo on top (16:9, `object-cover`); title (2-line clamp); 1-line dek from `body`; footer `via {host} ↗` (from `source_url`) + date. The whole card is an `<a href={source_url}>` (new tab) when `source_url` exists.
- **Event card:** a cream→muted gradient header band with a `Calendar` glyph + a date badge (no fabricated image); title; location line; footer `Add to calendar` + `via {host} ↗`. No RSVP (channel events; consistent with the earlier decision). Manual events with a future date render the same way (RSVP stays out of this grid surface — the grid is the "news" view).
- **Image fallback:** a post lacking `image_url` (rare) uses the same gradient header as events.
- A small `hostOf(url)` helper (shared) powers the `via {host}` label. Reuse the existing `addEventToCalendar` for the event "Add to calendar".

### 3.4 Applied to all three levels

- **Institution** (`InstitutionDetail.tsx`): the merged "Events & Updates" tab renders `<NewsGrid posts={…} events={…} />` instead of the stacked `EventsTab`/`UpdatesTab` sections. Posts/events fetched with `institution_scope=true` (dedup fix). The old `EventsTab`/`UpdatesTab` components are removed if no longer referenced.
- **School** (`SchoolSubunitPage.tsx`): the "Events & Updates" tab renders `<NewsGrid>` (school-scoped) instead of the current inline `EventRow` + `PostCard` lists.
- **Program** (`ProgramDetailPage.tsx`): add an **"Events & Updates" tab** rendering `<NewsGrid>` (program-scoped posts + `listEvents({program_id})`). Remove the program-Updates list previously added to the Overview tab and the "Upcoming Events" block in `RelatedSidebar` (consolidated into the new tab, no duplication).
- Types: `InstitutionPost` and the event item type gain `image_url?: string | null`.

## 4. Seeding / migration

- New migration: add the two `image_url` columns, then re-run the populate (`mit_profile.apply` + `_seed_scope_sync` for MIT/Sloan/MBAn) so existing cards backfill their images immediately. The daily `content_ingest_refresh` job keeps them current thereafter. Fail-soft, single head.

## 5. Testing

- **rss parser:** `image_url` set from a `media_content` fixture; `None` when absent.
- **events parser:** iCal yields `image_url=None`.
- **dedup:** `get_public_posts(institution_scope=True)` returns no duplicate `external_id`s; school/program scoping unaffected.
- **schemas:** `EventResponse`/`PostResponse` expose `image_url`.
- **frontend:** `NewsGrid` renders a post card with an `<img>` when `image_url` present, a gradient event card with date + `Add to calendar` for events, a `via {host}` link, and an honest empty state; institution page shows no duplicate titles.

## 6. Out of scope

- The Apple-News mosaic / featured-hero variants (user chose uniform grid).
- Per-article `og:image` fetching (the feed already supplies images).
- Live social-post ingestion (separate flag-gated `SocialSource` seam).
