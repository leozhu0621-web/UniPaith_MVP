# Channel-sourced events & updates + campus info on the institution page

**Date:** 2026-06-09
**Status:** Approved design — pending spec review
**Scope of this build:** MIT only (validate with MIT → Sloan → Master of Business
Analytics), RSS-news + events-iCal sourcing, plus the "Campus life" / "Campus &
basics" About sections. Social platforms and other schools are an explicit
fast-follow.

## Problem & context

The institution page already has **Events** and **Updates** tabs (and a student
**Connect** surface) that render real `Event` / `InstitutionPost` rows, and the
institution admin (`EventsPage` / `PostsPage`) already lets a logged-in school
create/edit/pin them. But **seeded** schools like MIT have no logged-in operator,
so those tabs are empty.

Goal: **auto-populate a school's Events/Updates from its own public channels** so
seeded schools look alive, while keeping everything editable by the school. Start
with the rock-solid public feeds (news RSS + events iCal); design the pipeline so
social platforms (X / Instagram / LinkedIn / YouTube) plug in later.

Separately, the **About** tab should carry more institutional substance: a
**Campus life** and a **Campus & basics** section built from data we already
store (`school_outcomes.campus_life` + `scale`). This is a pure frontend addition
(no new data) and is bundled here because it's the same surface.

(Out of band: the campus-photo hero was fixed in PR #376; not part of this spec.)

## Verified MIT public feeds

| Source | URL | Format | Maps to |
|---|---|---|---|
| MIT News | `https://news.mit.edu/rss/feed` | RSS 2.0 | `InstitutionPost` (Updates) |
| MIT Events | `https://calendar.mit.edu/calendar.ics` | iCal (VCALENDAR) | `Event` (Events) |

Both verified live (HTTP 200, correct content-type) at author time.

## Approach (chosen: A — scheduled ingestion into existing tables)

A scheduled job pulls each institution's configured feeds, normalizes them, and
**upserts auto-flagged `Event` / `InstitutionPost` rows** that the existing
student tabs + Connect already render and the existing admin can edit/hide. Live
fetch-at-render (B) was rejected (fragile, no editing, no Connect, no social);
a manual "import" button (C) is folded in as the manual refresh trigger.

## Schema (one migration, off the current head)

- `institutions.content_sources` (JSONB, nullable):
  ```json
  {
    "news_rss": "https://news.mit.edu/rss/feed",
    "events_feed": { "url": "https://calendar.mit.edu/calendar.ics", "type": "ical" },
    "social": { "x": null, "instagram": null, "linkedin": null, "youtube": null }
  }
  ```
  `social` is reserved for Phase 2; `events_feed.type` ∈ {`ical`, `rss`}.
- `institution_posts`: add `source` (String(24), default `'manual'`),
  `external_id` (String(500), nullable), `source_url` (String(1000), nullable).
- `events`: add `source` (String(24), default `'manual'`), `external_id`
  (String(500), nullable), `source_url` (String(1000), nullable).
- Partial-unique index on each: `(institution_id, source, external_id)` where
  `external_id IS NOT NULL` — the idempotency/dedup key.

Existing `status` columns are reused: ingested rows are written `published` and a
school can flip a post to `archived`/`draft` — or an event to `cancelled` (the
status `ConnectService.build_events` already excludes) — to hide it. `published_at`
is set from the feed item's date.

## Ingestion service — `services/content_ingest/`

- `ChannelSource` (ABC): `name: str`; `fetch(session, institution) -> list[NormalizedItem]`.
  `NormalizedItem` = `{kind: 'post'|'event', external_id, title, body/description,
  url, published_at, start_time?, end_time?, location?}`. The `start_time?`/
  `end_time?` fields are optional only for `post` items; for an `event` both are
  **required** (non-null) since the `events` table forbids a null `end_time` (see
  `EventsFeedSource` below for the default).
- `NewsRssSource` — parses `content_sources.news_rss` with **feedparser** → `post`
  items (guid → `external_id`, summary → `body`, link → `source_url`).
- `EventsFeedSource` — parses `content_sources.events_feed` as iCal (**icalendar**)
  or RSS (feedparser) → `event` items (UID → `external_id`, DTSTART/DTEND →
  `start_time`/`end_time`, LOCATION, URL). The `events` table requires a non-null
  `end_time`, but many iCal entries omit `DTEND` or are all-day; the source MUST
  always derive an `end_time` (use `DTEND`/duration when present, else default to
  `start_time + 1h` — all-day → end of that day) so it is never `None` on insert.
- `ContentIngestService.ingest_institution(institution)`:
  - For each configured source: fetch (timeout, fail-soft per source — log and
    continue), cap to the **N most recent** items (e.g. 25 posts / 25 events),
    skip items older than a window (e.g. 180 days) for events keep upcoming + recent.
  - Upsert by `(institution_id, source, external_id)`; set `source`,
    `source_url`, `published_at`, `status='published'`. Never overwrite a row a
    school has manually edited/hidden (respect a `status` that's not `published`,
    or a future `locked` flag — for now: skip re-publishing a post whose status is
    `archived`/`draft`, and skip re-publishing an event whose status is `cancelled`
    (events use `cancelled`, not `archived`/`draft`, to hide — see
    `EventService.cancel_event` / `ConnectService.build_events`)).
  - Governance: **public, non-personal, first-party only** (reuse the Spec 60
    crawler governance posture); store the canonical `source_url`; never fabricate.
- `ingest_all(session)` iterates institutions that have `content_sources`. Because
  this repo's JSONB columns can hold the JSON-null literal (`'null'::jsonb`, which
  passes `IS NOT NULL`/`COALESCE` but deserializes to Python `None`), the selection
  MUST also exclude that case — e.g.
  `WHERE content_sources IS NOT NULL AND jsonb_typeof(content_sources) != 'null'` —
  and the loop must re-check the fetched value for `None`/emptiness before use, so
  schools seeded with a JSON-null placeholder aren't silently skipped or crashed.

Dependencies to add: `feedparser`, `icalendar` (both small, widely used).

## Trigger / freshness

- A daily scheduled task calls `ingest_all` (reuse the project's existing
  scheduler used for alerts/digests; if none fits, a lightweight cron entry).
- A system-guarded ops endpoint `POST /admin/content-ingest/refresh` (and
  `?institution_id=` for one school) for manual/on-demand refresh and seeding.

## Config / self-service (extends "update by themselves")

- The institution admin gains a **Channels** config (the `content_sources` URLs;
  social handle fields shown but disabled/"coming soon" in Phase 1).
- Auto-ingested items appear in the existing Posts/Events admin lists flagged
  **"via your news feed"**, and remain fully editable/hideable (status change).
- **MIT seed:** set `content_sources` for MIT in `mit_profile.apply()` (news_rss
  + events_feed above), so a single re-apply + one `refresh` populates MIT's tabs.

## Frontend

- **Events/Updates tabs** (and Connect cards): when an item has a `source` other
  than `manual`, show a small **"via {source label}"** line linking to
  `source_url` (opens the school's own page). No layout change otherwise.
- **About tab — two new sections** (read existing data; render only when present):
  - **Campus life:** varsity sports, athletics division, arts groups, residence
    halls (`school_outcomes.campus_life`).
  - **Campus & basics:** founded, campus setting, campus acres, student-faculty
    ratio, faculty count, undergrad majors/minors, endowment
    (`school_outcomes.scale` + institution fields).

## Testing

- **Ingestion unit tests** (no network): feed `NewsRssSource`/`EventsFeedSource`
  fixed RSS/iCal fixture strings → assert correct `InstitutionPost`/`Event`
  upserts (fields, `source`, `source_url`, `published_at`); re-run → **idempotent**
  (no duplicates, dedup by `external_id`); a school-hidden row is **not**
  re-published (an `archived`/`draft` post and a `cancelled` event).
- **Governance test:** the ingester only writes public source data; `source_url`
  preserved.
- **Frontend:** Campus life / Campus & basics render from sample
  `school_outcomes`; auto-item shows the "via {source}" attribution + link.

## Validation (the MIT / Sloan / MBAn example)

1. Re-apply MIT (sets `content_sources`) + run `refresh?institution_id=MIT`.
2. MIT institution page → **Updates** shows recent MIT News items (with "via MIT
   News" → news.mit.edu); **Events** shows upcoming MIT calendar events.
3. MIT **About** shows Campus life + Campus & basics.
4. MBAn program page unchanged (program-level; events/updates are institution-level).

## Out of scope (fast-follow)

- **Social platforms** (X / Instagram / LinkedIn / YouTube) via Bright Data — new
  `ChannelSource` adapters + social-handle admin config. The interface + the
  `content_sources.social` config are built to accept them with no schema change.
- **Other schools** (Harvard, etc.) — same pipeline, just seed their feeds.
- **School-unit-level feeds** (e.g. a Sloan-specific feed on the school page).
