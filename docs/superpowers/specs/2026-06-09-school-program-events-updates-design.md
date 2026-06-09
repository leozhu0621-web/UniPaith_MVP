# School + Program Events / Updates + Social, and UI tooltip cleanup — Design

**Date:** 2026-06-09
**Status:** Approved design (pending spec review)
**Author:** QA/full-stack session (eager-jemison-98cde6)
**Reference example:** MIT → MIT Sloan School of Management → Master of Business Analytics (MBAn)

## 1. Goal

Extend the channel-sourced **Events & Updates** feature (built for the institution profile in PR #378) down to the **school profile** (Sloan) and **program profile** (MBAn), plus surface each entity's **official social channels**. Content is scoped by **keyword relevance over authoritative MIT channels** and **refreshes itself daily** so the surfaces stay current with no manual upkeep. Bundle a UI decluttering pass that converts scattered small caption notes into **hover-only tooltips**. MIT / Sloan / MBAn set the standard; everything ships with real, sourced data — nothing fabricated.

## 2. Scope decision (confirmed with user)

**School-own + program tagged-only, scoped by keyword relevance over authoritative channels:**

- **Sloan (school)** shows its *own* Sloan-scoped content — never MIT-wide noise.
- **MBAn (program)** shows only content tagged to the MBAn `program_id` — it does **not** inherit Sloan's feed.
- Social channels are shown as **links** on both surfaces.

**Relevance rule (user direction 2026-06-09):** an item counts for a scope only when it comes **from an authoritative MIT channel** (news.mit.edu, calendar.mit.edu, mitsloan.mit.edu, or the entity's *own* official social account) **AND its visible text actually contains the scope keyword**. "A MIT post that has 'Sloan' in it counts as Sloan-related; a random person mentioning Sloan does not." This is enforced two ways: (1) only official channels are ever configured as sources — never third-party feeds or keyword-mention crawls; (2) a **relevance gate** in the ingest pipeline drops any item whose visible text does not contain a configured keyword.

## 3. Verified channel manifest (the no-fabrication ground truth)

Every URL below was fetched live on 2026-06-09 and adversarially confirmed (parallel verification workflow `wf_0c32505d-ddd`). Confidence and the authoritative source are recorded so seeding is auditable.

### 3.1 Updates — keyword-relevant, from authoritative MIT channels

| Scope | Feed URL | Items | Why authoritative + relevant |
|---|---|---|---|
| Sloan (school) | `https://news.mit.edu/rss/topic/sloan-school-management` | 50 | MIT's OWN editorial Sloan topic feed — every item is MIT-published and MIT-tagged "Sloan". Authoritatively scoped → **relevance gate bypassed** (`curated: true`). |
| MBAn (program) | `https://news.mit.edu/rss/topic/operations-research` (+ `/topic/analytics`, 50) | 25 | MIT-published, tagged to MBAn's home discipline. A program **keyword gate** (`mban`, `business analytics`, `master of business analytics`, `operations research`) keeps only genuinely MBAn-relevant items; tagged `program_id`. |

Curated MIT topic feeds are authoritative by construction (MIT chose the tag) and bypass the relevance gate; keyword-search and general feeds (below) do not.

### 3.2 Events — keyword-relevant from MIT's authoritative calendar, gated for relevance

`calendar.mit.edu` is MIT's official events platform — an authoritative source. But its full-text search is **loose**: of the 15 events `?search=sloan` returns, **only 1 ("Celebrate Juneteenth!") actually contains "Sloan"** (in its DESCRIPTION); the other 14 don't mention Sloan anywhere in the exported event (Localist matched a hidden index field).

Per the user's rule — *"a MIT post that has 'Sloan' in it counts; a random person mentioning Sloan does not"* — the ingest applies a **relevance gate**: keep an event only if a configured keyword appears (case-insensitive, word-boundary) in its **visible text** (`SUMMARY + DESCRIPTION + LOCATION + ORGANIZER + CATEGORIES`). On `?search=sloan` today this keeps the 1 genuine Sloan event and drops the 14 spurious matches.

| Scope | Source URL | Keyword gate | After gate (2026-06-09) |
|---|---|---|---|
| Sloan (school) | `https://calendar.mit.edu/search/events.ics?search=sloan` | `sloan`, `mit sloan` | 1 genuine event (of 15 raw) |
| MBAn (program) | `https://calendar.mit.edu/search/events.ics?search=business+analytics` | `mban`, `business analytics`, `master of business analytics` | gated; tagged `program_id` (may be 0 → honest empty state) |

Result: real, honest, possibly-sparse events that grow over time — no noise is ever shown.

Note: MIT Sloan does not publish its own consolidated events feed (`mitsloan.mit.edu/events/feed` → 404; not a Localist department/group — only Sloan *student clubs* are) and ORC's WordPress feeds are empty. So the **gated MIT calendar is the authoritative events source**; admins may also post events via the existing self-service path.

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
  "updates": { "rss": "https://news.mit.edu/rss/topic/sloan-school-management", "curated": true },
  "events":  { "ical": "https://calendar.mit.edu/search/events.ics?search=sloan" },
  "keywords": ["sloan", "mit sloan"],
  "social": {
    "instagram": "https://www.instagram.com/mitsloan/",
    "linkedin": "https://www.linkedin.com/company/mit-sloan-school-of-management",
    "x": "https://twitter.com/mitsloan",
    "youtube": "https://www.youtube.com/user/MITSloan",
    "facebook": "https://www.facebook.com/MITSloan"
  }
}
```
- `keywords`: the relevance-gate tokens for this scope.
- `updates.curated: true` marks an MIT-authoritative topic feed → relevance gate bypassed (MIT already scoped it). Absent/false → gate applies (MBAn's discipline feed is gated by program keywords).
- `events.ical`: a keyword-search calendar URL whose results are **always** gated by `keywords`.
- Any sub-key may be absent/null.

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

**Relevance gate (encodes the user's rule).** After a source yields `NormalizedItem`s, the service applies `passes_relevance(item, keywords, curated)`:
- `curated == true` (MIT-authoritative topic feed) → keep all (MIT already scoped it);
- otherwise keep the item only if any keyword matches (case-insensitive, word-boundary regex) the item's concatenated visible text — `title + body + location + organizer + categories`. Drop the rest.

This is what makes *"a MIT post that has 'Sloan' counts; a random mention does not"* true at the data layer: only official MIT channels are ever configured as sources, and within them only keyword-matching items survive. A relevance-gate unit test asserts the `?search=sloan` fixture (15 raw) yields exactly the 1 item whose description contains "Sloan".

**Authoritative-source rule.** Sources are restricted to the entity's own / parent institution's OFFICIAL channels (`news.mit.edu`, `calendar.mit.edu`, `mitsloan.mit.edu`, and — when wired — the entity's own official social accounts). Third-party feeds and keyword-mention crawls are never configured. The `SocialSource` adapter, when enabled, ingests posts **authored by** the official account, never third-party mentions of the keyword.

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
  - Events: `listEvents({ school_id })` → the keyword-gated Sloan events; **honest empty state** when none ("No upcoming events published yet").
- Add a **social links row** (icon links) from `school.content_sources.social` — opens in a new tab, `rel="noopener noreferrer"`.

**ProgramDetailPage (`pages/student/ProgramDetailPage.tsx`)**
- Events render already exists (`listEvents({ program_id })` → `RelatedSidebar events`); it shows the keyword-gated MBAn events (may be empty → honest).
- Add an **Updates** list scoped by `program_id` (MBAn → operations-research news) with `via {host}` attribution.
- Add a **social links row** from `program.content_sources.social` (Sloan's links inherited for display + ORC X; `@mit.analytics` only if user-approved).

**Empty states everywhere are honest** — no fabricated filler.

### 4.6 Seeding on production

Same mechanism as MIT (the ops endpoint is locked on prod). `mit_profile.apply()`:
- Sets `content_sources` on the **Sloan School row**: `updates.rss` = Sloan topic feed (`curated: true`), `events.ical` = `?search=sloan`, `keywords` = `["sloan","mit sloan"]`, `social` = the 5 confirmed handles.
- Sets `content_sources` on the **MBAn Program row**: `updates.rss` = operations-research topic feed (`curated: false` → gated), `events.ical` = `?search=business+analytics`, `keywords` = `["mban","business analytics","master of business analytics","operations research"]`, `social` = Sloan's links + ORC X (`@mit.analytics` only if user-approved).
- A new data migration calls `content_ingest` `seed_populate_sync` for the Sloan + MBAn feeds so Updates (and any gated Events) populate on deploy (sync, fail-soft, idempotent — same pattern as `contentsrc1`).

### 4.7 Daily self-refresh (the feature keeps itself current)

The whole Events/Updates pipeline **refreshes itself daily** via the existing APScheduler in `core/scheduler.py` — the same mechanism that already runs the saved-search-alert and notification-digest loops and a `hours=24` "Daily Feature Refresh". Add one job:

- **`_run_content_ingest_refresh()`** — registered with `scheduler.add_job(..., "interval", hours=24, id="content_ingest_refresh", name="Daily Content Ingest Refresh", **_job_defaults())`, gated by a new `settings.content_ingest_refresh_enabled` flag (true in prod, off in `test`).
- Opens its own `async_session`, calls `ContentIngestService(session).ingest_all()` — which walks **every** institution/school/program that has `content_sources`, re-fetches each feed, applies the **relevance gate**, and **idempotently upserts**. Commits once.
- **Fail-soft:** wrapped in `try/except` that logs and is retried next interval — a tick must never crash the scheduler (exactly matching `_run_saved_search_alerts` / `_run_notification_digest`).
- Runs under the existing **leader-only guard** (`scheduler_require_leader` / `scheduler_is_leader`) so multiple ECS tasks don't duplicate the run; the idempotent upsert makes a duplicate harmless regardless.
- Because ingest is idempotent + fail-soft + hidden-rows-not-resurrected, each daily run only **adds genuinely new items and refreshes existing ones** — nothing is duplicated, and admin-hidden rows stay hidden.

So: the deploy-time `seed_populate_sync` migration does the **first** populate; the scheduler keeps it **fresh every 24 h** thereafter; the locked ops endpoint (`/admin/content-ingest/refresh`) remains for manual on-demand refresh. New config: `content_ingest_refresh_enabled` (bool) + optional `content_ingest_refresh_hours` (default 24) in `config.py`, exported to the ECS env block like the other scheduler flags.

## 5. Tooltip cleanup (request "a") — full inventory

The user flagged that small caption notes are "everywhere" and "make the UI look messy." Convert qualifier/explainer captions into **native hover-only `title` tooltips** (zero-dep, exactly "show on hover") via a tiny shared helper. A full sweep of all 11 detail-page files (workflow `wf_b48aaef2-ccc`) classified every small-note site as **tooltip** (hide-on-hover), **keep** (real content / source-trust), or **condense** (shorten — too long for a tooltip).

**Design principle:** the value/heading stays visible; the qualifier moves into its `title=`. Source-citation trust signals and real content are NEVER hidden.

### 5.1 The win: most captions collapse into a few render-site changes

| File | Render site | What it covers |
|---|---|---|
| `program/KeyMetrics.tsx` | `{tile.context}` `<p>` at **:524** (anchor: value `<p>` :515–520, already has `title={tile.value}`) | **all 22** metric-tile captions ("Within 6 months", "Per academic year", "+X% over 4 years", classification words, etc.) — one change |
| `institution/InstitutionDetail.tsx` | keyStats hint `<p>` **:508**; `OutcomeStat` hint **:1160**; `Fact` hint **:1172** | every stat-card hint incl. "per year, after aid" (:467), "10 yrs after entry" (:468/:613) |
| `program/NextStepsCard.tsx` | `step.hint` `<p>` **:124** → `title` on the step button | deadline-countdown (:59), event date/time (:74) qualifiers |
| `program/NetPriceEstimator.tsx` | unit/scale/disclaimer captions **:56, :58, :95, :114, :183** | "/yr", "min–max · estimate", "/ year (expected)", sticker-COA axis, methodology disclaimer |
| `institution/overviewWidgets.tsx` | `StatBar` hint **:142**; `AdmissionsFunnel` cycle **:94** | per-stat hint + funnel scope/period ("Class of 2028") |
| `program/InsightsPanel.tsx` | **:236, :364, :405** (caption labels) + **:316, :471** (date/year stamps) | chip-row lead-in, sentiment-chart label, review date, employer feedback year |
| `program/StatGroup.tsx` | in-label units **:107 (6yr), :110 (10yr), :124 (/yr), :127 (/yr)** | restructure label → unit into `title` on value :58 (borderline; optional) |

### 5.2 Per-section caption → heading-title conversions (InstitutionDetail.tsx)

| Caption | Line | Tooltip anchor |
|---|---|---|
| `X undergraduate · Y graduate · Z total enrollment` | :636 | Diversity `<h2>` (:628) |
| Carnegie classification (italic) | :657 | Quick-facts `<h2>` (:647) |
| `Among faculty & alumni` | :777 | Recognition `<h2>` (:776) |
| `N+ centers, labs & institutes · ~K industry collaborators` | :799 | Research & innovation `<h2>` (:797) |
| `Sticker cost of attendance $X/yr before aid` | :572 | net-price value `<p>` (:569) |
| `{rsvp}/{capacity} spots` | :1079 | event `<h3>` / RSVP control |

### 5.3 ProgramDetailPage.tsx individual sites

`Your match` overline (:476), `N required · M optional` (:848), Admission-Timeline term (:1012), per-line cost note (:1264), the three Estimated-Total-Cost tile captions (:1289/:1293/:1301 → their value `<p>`), income-band `$range` (:1367), outcome reporting window (:1537), `Within {empTimeframe}` (:1576), `Interns → full-time offers` (:1583).

### 5.4 SchoolSubunitPage.tsx

Hero "offered" degree-levels caption (:167) → `title="Degree levels offered"`; quick-facts `StatTile` uppercase labels (:257) → `title` on tile.

### 5.5 KEEP — never convert (source-trust + real content)

All `Source:` lines (e.g. InstitutionDetail :591, InsightsPanel :336, AboutCard source eyebrow), every footer `Data sources:` line, the `via {host}` post/event attribution, the follow-confirmation helper (:320), and real sub-section labels ("Race & ethnicity" :631, "Top industries" :618). `RelatedSidebar.tsx` and `AboutCard.tsx` have **no** tooltip targets — leave unchanged.

### 5.6 CONDENSE — shorten, don't tooltip (too long for a hover)

InstitutionDetail net-price sentence (:570); ProgramDetailPage income-band methodology (:1356), debt-distribution explainer (:1415), outcomes scope+source paragraph (:1495 — keep the `Source:` clause visible, shorten only the scope sentence); SchoolSubunitPage footer trailing clause (:358 — keep the citation, trim "Figures reflect the latest available data…").

### 5.7 Shared helper

A tiny `InfoCaption`/`withTip` helper (or just `title=` + `aria-label` where the value would otherwise be lost to screen readers) keeps the pattern consistent across all sites. `DiversityBar` already uses native `title=` on its segments — that's the model.

## 6. Testing

- **Relevance-gate unit tests:** `curated == true` keeps all; otherwise a `?search=sloan` fixture (15 raw VEVENTs, only 1 with "Sloan" in its description) yields exactly 1; keyword match is case-insensitive + word-boundary (no substring false-positive on "sloane"); a program-keyword fixture drops discipline-feed items lacking the MBAn keywords.
- **Ingest unit tests:** school-scoped tagging (writes `school_id`), program-scoped tagging (writes `program_id`), dedup-with-scope, fail-soft on a bad feed, gate applied per source, `SocialSource` yields `[]` when no provider.
- **Scheduler test:** `setup_scheduler()` registers the `content_ingest_refresh` job (24 h interval) when `content_ingest_refresh_enabled`; `_run_content_ingest_refresh()` is fail-soft (a raising `ingest_all` logs, does not propagate); not registered in `test` env.
- **`mit_profile` test:** Sloan School row gets `content_sources` with the 5 social links, `updates.rss` (Sloan topic, `curated: true`), `events.ical` (`?search=sloan`), and `keywords`; MBAn Program row gets `updates.rss` (operations-research, not curated), `keywords`, and Sloan-inherited social.
- **API test:** `GET /events?school_id=` filters; `EventResponse`/`PostResponse` expose `school_id`; school/program responses expose `content_sources`.
- **Frontend:** school Updates tab renders posts/events + social links; program Updates renders; tooltip `title` attributes present on the converted caption sites; empty states render when no data.

## 7. Out of scope / follow-ups

- Live social-post ingestion (needs a provider like Bright Data / platform API) — `SocialSource` is the seam, flag stays off.
- HTML-scraping `mitsloan.mit.edu/events` for real Sloan events (fragile; revisit if a feed never appears).
- Replicating the channel + social + campus data to Harvard and other schools.
- User confirmation of the MBAn `@mit.analytics` Instagram before it is shown as official.

## 8. Open question for spec review

The MBAn `@mit.analytics` Instagram is likely genuine but not strictly confirmable (not linked from any mit.edu page; a confusable impostor exists). **Default: omit it; MBAn shows Sloan's confirmed links + ORC X.** Confirm whether to include `@mit.analytics` anyway.
