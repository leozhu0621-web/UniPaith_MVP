# School + Program Events / Updates + Social, and UI tooltip cleanup — Design

**Date:** 2026-06-09
**Status:** Approved design (pending spec review)
**Author:** QA/full-stack session (eager-jemison-98cde6)
**Reference example:** MIT → MIT Sloan School of Management → Master of Business Analytics (MBAn)

## 1. Goal

Extend the channel-sourced **Events & Updates** feature (built for the institution profile in PR #378) down to the **school profile** (Sloan) and **program profile** (MBAn), plus surface each entity's **official social channels**. Bundle a UI decluttering pass that converts scattered small caption notes into **hover-only tooltips**. MIT / Sloan / MBAn set the standard; everything ships with real, sourced data — nothing fabricated.

## 2. Scope decision (confirmed with user)

**School-own + program tagged-only:**

- **Sloan (school)** shows its *own* Sloan-scoped content — never MIT-wide noise.
- **MBAn (program)** shows only content tagged to the MBAn `program_id` — it does **not** inherit Sloan's feed.
- Social channels are shown as **links** on both surfaces.

## 3. Verified channel manifest (the no-fabrication ground truth)

Every URL below was fetched live on 2026-06-09 and adversarially confirmed (parallel verification workflow `wf_0c32505d-ddd`). Confidence and the authoritative source are recorded so seeding is auditable.

### 3.1 Updates — real, populated, correctly-scoped news RSS

| Scope | Feed URL | Items | Scope correctness |
|---|---|---|---|
| Sloan (school) | `https://news.mit.edu/rss/topic/sloan-school-management` | 50 | ✅ Channel title is literally "MIT News - MIT Sloan School of Management" — genuinely Sloan-scoped |
| MBAn (program) | `https://news.mit.edu/rss/topic/operations-research` | 25 | ✅ MBAn's academic home discipline; tagged `program_id`. (`/topic/analytics` (50) is a secondary candidate.) |

### 3.2 Events — **no clean public feed exists** (verified exhaustively)

- `calendar.mit.edu/search/events.ics?search=sloan` and `?search=operations+research+center` are **full-text keyword searches over the MIT-wide calendar**, NOT scoped feeds. Their samples ("Celebrate Juneteenth!", "Spring into Writing", unrelated seminars) prove they are noise — labeling them "Sloan/MBAn events" would be fabrication.
- MIT Sloan does **not** publish a consolidated machine-readable events feed: `mitsloan.mit.edu/events/feed|.xml` → 404; it is not a MIT-wide Localist department or group (Localist only carries Sloan *student clubs*: Design Club, PM Club, Africa Business Club, …).
- ORC's own WordPress feeds (`orc.mit.edu/feed`, `/news/feed`, `/events/feed`) return valid RSS with **0 items** (empty).

**Consequence:** the school/program **Events** area is built as a capability but shows an **honest empty state** until either (a) a clean scoped feed appears, or (b) an institution admin posts events via the existing self-service path. No keyword-search noise is ingested.

### 3.3 Social channels — verified official handles

| Entity | Platform | URL | Confidence | Authority |
|---|---|---|---|---|
| Sloan | Instagram | `https://www.instagram.com/mitsloan/` | high | mitsloan.mit.edu footer |
| Sloan | LinkedIn | `https://www.linkedin.com/company/mit-sloan-school-of-management` | high | mitsloan.mit.edu footer |
| Sloan | X | `https://twitter.com/mitsloan` | high | mitsloan.mit.edu footer |
| Sloan | YouTube | `https://www.youtube.com/user/MITSloan` | high | mitsloan.mit.edu footer |
| Sloan | Facebook | `https://www.facebook.com/MITSloan` | high | mitsloan.mit.edu footer |
| MBAn | Instagram | `https://www.instagram.com/mit.analytics/` | **medium — needs user OK** | ~33K followers, on-brand, but NOT linked from any mit.edu page; confusable student-run `@mitanalytics` (no dot) must never be used |
| MBAn/ORC | X | `https://x.com/orcenter` | medium | bio links orc.mit.edu + matches internal room E40-103; not mit.edu-linked |

MIT (institution) handles were also confirmed (IG `/mit`, LI `/school/mit`, X `/mit`, YT `/mit`, FB `/MITnews`) and may seed the institution row for consistency.

**MBAn social default:** ship **Sloan's confirmed links** on the MBAn page (inherited display) + the ORC X link. `@mit.analytics` is added **only after the user confirms** it (recorded as a follow-up question in the spec-review gate).

**Correction captured:** the earlier assumption that "Bertsimas directs the ORC" is **outdated** — current ORC co-directors are Georgia Perakis & Saurabh Amin (2025–); Bertsimas was co-director 2006–2009 and remains MBAn faculty. The spec/data must not claim he directs the ORC.

## 4. Architecture

### 4.1 Data model (one migration)

- **`events`** += `school_id UUID NULL FK → schools.id` (already has `institution_id`, `program_id`, `source`, `external_id`, `source_url`). Index `(school_id)`.
- **`institution_posts`** += `school_id UUID NULL FK → schools.id`. Index `(school_id)`.
- **`schools`** += `content_sources JSONB NULL` (mirrors the column already on `institutions`).
- **`programs`** += `content_sources JSONB NULL`.

`content_sources` shape (same for institution/school/program):
```json
{
  "news_rss": "https://news.mit.edu/rss/topic/sloan-school-management",
  "events_feed": { "url": "...", "type": "ical" },
  "social": {
    "instagram": "https://www.instagram.com/mitsloan/",
    "linkedin": "https://www.linkedin.com/company/mit-sloan-school-of-management",
    "x": "https://twitter.com/mitsloan",
    "youtube": "https://www.youtube.com/user/MITSloan",
    "facebook": "https://www.facebook.com/MITSloan"
  }
}
```
Any sub-key may be absent/null. `events_feed` is omitted for Sloan/MBAn (no clean feed).

### 4.2 Ingest service (extend, do not replace)

`ContentIngestService` currently walks an institution's feeds. Extend it to also iterate the institution's **schools** and **programs** that carry `content_sources`, tagging each normalized item with the correct scope:

| Source scope | Tag written on Event/InstitutionPost |
|---|---|
| Institution | `institution_id` only |
| School | `institution_id` + `school_id` |
| Program | `institution_id` + `program_id` |

- Dedup key extends to include scope: `(institution_id, school_id|program_id, source, external_id)`.
- Idempotent upsert, fail-soft (one bad feed never breaks others), hidden rows not resurrected — unchanged contract.
- `social` is **not** ingested as posts in this iteration; it is link metadata only (the `SocialSource` adapter below is the flag-gated fast-follow).

### 4.3 `SocialSource` adapter (designed, flag-gated, no fabrication)

Add a `ChannelSource` subclass interface `SocialSource` (e.g. `social_instagram`, `social_linkedin`) so the same pipeline can ingest *real* social posts when a provider/API is wired. It stays **off** until a provider returns real data:

- Behind flag `content_social_ingest_enabled` (default off).
- Produces `InstitutionPost` rows with `source="instagram"|"linkedin"|...` + `source_url` + `external_id`.
- Never emits placeholder/synthetic posts; with no provider configured it yields `[]`.

This is the seam that satisfies "remember social media as well" without inventing content today; the visible social value now is the **links** (§4.5).

### 4.4 API

- `GET /events` (`api/events.py`): add `school_id: UUID | None = Query(None)` → `EventService.list_upcoming_events(..., school_id=...)` filters `Event.school_id == school_id`.
- `EventResponse` schema (`schemas/event.py`): add `school_id: UUID | None = None`.
- Public posts endpoint used by `getPublicPosts`: add a `school_id` filter param so the school Updates tab can request school-scoped posts. `PostResponse` exposes `school_id`, `source`, `source_url` (source/source_url already present).
- School/program response schemas (`getInstitutionSchools`, `getSchoolPrograms`, program detail, public institution schools): add `content_sources` so the frontend can render social links + know which feeds exist. (Per repo rule: new model fields must be added to response schemas in the same change.)

### 4.5 Frontend

**SchoolSubunitPage (`pages/student/SchoolSubunitPage.tsx`) — Updates tab**
- Replace the empty placeholder with the institution page's Events + Updates rendering, scoped by `school_id`:
  - Updates: `getPublicPosts({ school_id })` → list with `via {host} ↗` attribution (reuse `sourceHost` + PostCard pattern).
  - Events: `listEvents({ school_id })` → list; **honest empty state** when none ("No upcoming events published yet").
- Add a **social links row** (icon links) from `school.content_sources.social` — opens in a new tab, `rel="noopener noreferrer"`.

**ProgramDetailPage (`pages/student/ProgramDetailPage.tsx`)**
- Events render already exists (`listEvents({ program_id })` → `RelatedSidebar events`); it lights up once MBAn events are tagged (none now → empty is honest).
- Add an **Updates** list scoped by `program_id` (MBAn → operations-research news) with `via {host}` attribution.
- Add a **social links row** from `program.content_sources.social` (Sloan's links inherited for display + ORC X; `@mit.analytics` only if user-approved).

**Empty states everywhere are honest** — no fabricated filler.

### 4.6 Seeding on production

Same mechanism as MIT (the ops endpoint is locked on prod). `mit_profile.apply()`:
- Sets `content_sources` on the **Sloan School row** (`news_rss` = Sloan topic feed + `social` = 5 confirmed handles; no `events_feed`).
- Sets `content_sources` on the **MBAn Program row** (`news_rss` = operations-research topic feed; `social` = Sloan's links + ORC X; no `events_feed`).
- A new data migration calls `content_ingest` `seed_populate_sync` for the Sloan + MBAn news feeds so Updates populate on deploy (sync, fail-soft, idempotent — same pattern as `contentsrc1`).

## 5. Tooltip cleanup (bundled request "a")

Convert small caption notes into **native hover-only `title` tooltips** (zero-dep, exactly "show on hover") via a tiny shared helper for consistency. Confirmed sites in `InstitutionDetail.tsx`:

| Caption note | Location | Becomes a tooltip on |
|---|---|---|
| `X undergraduate · Y graduate · Z total enrollment` | `:635–641` | the **Diversity** heading |
| Carnegie classification (italic) | `:656–658` | the Quick-facts **Type** value |
| `Among faculty & alumni` | `:777` | that recognition card's heading |
| Stat hints (`per year, after aid`, `10 yrs after entry`) | `:467–468`, `:613` | the corresponding stat label |

The helper is reused for the "lots of small notes everywhere" the user flagged. Tooltips use the `title` attribute (and keep an `aria-label`/`aria-describedby` where the underlying value would otherwise be lost to screen readers).

## 6. Testing

- **Ingest unit tests:** school-scoped tagging (writes `school_id`), program-scoped tagging (writes `program_id`), dedup-with-scope, fail-soft on a bad feed, `SocialSource` yields `[]` when no provider.
- **`mit_profile` test:** Sloan School row gets `content_sources` with the 5 social links + Sloan news feed; MBAn Program row gets `content_sources` with the operations-research feed; assert no `events_feed` key (we don't ship noise).
- **API test:** `GET /events?school_id=` filters; `EventResponse`/`PostResponse` expose `school_id`; school/program responses expose `content_sources`.
- **Frontend:** school Updates tab renders posts/events + social links; program Updates renders; tooltip `title` attributes present on the converted caption sites; empty states render when no data.

## 7. Out of scope / follow-ups

- Live social-post ingestion (needs a provider like Bright Data / platform API) — `SocialSource` is the seam, flag stays off.
- HTML-scraping `mitsloan.mit.edu/events` for real Sloan events (fragile; revisit if a feed never appears).
- Replicating the channel + social + campus data to Harvard and other schools.
- User confirmation of the MBAn `@mit.analytics` Instagram before it is shown as official.

## 8. Open question for spec review

The MBAn `@mit.analytics` Instagram is likely genuine but not strictly confirmable (not linked from any mit.edu page; a confusable impostor exists). **Default: omit it; MBAn shows Sloan's confirmed links + ORC X.** Confirm whether to include `@mit.analytics` anyway.
