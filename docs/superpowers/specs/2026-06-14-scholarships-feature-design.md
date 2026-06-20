# Scholarships — real-data feature (Resources › Financial)

**Date:** 2026-06-14
**Status:** Approved (user: "Yes — spec + build it"). Data already acquired.
**Unblocks:** the deferred scholarship-matching idea from the Discover review, now on REAL data.

## Data (slice 1 — DONE)

9,500 real scholarships scraped from the CareerOneStop (U.S. DOL) Scholarship Finder,
whose results are server-rendered (no API exists; verified). Acquired by
`Data/fetch_careeronestop_scholarships.py` → normalized JSON committed to the backend at
`unipaith-backend/seed_data/scholarships.json`. Per-record fields (all ~100% filled
except deadline 95%):

`external_id` · `name` · `organization` · `purpose` · `level_of_study` (text, e.g.
"Bachelor's Degree Graduate Degree") · `award_type` (Scholarship/Fellowship/Grant/Prize) ·
`award_amount` (text range, e.g. "$1,000 $5,000") · `deadline` (month, e.g. "November") ·
`url` (official CareerOneStop detail page).

**Honesty:** `award_amount` and `deadline` are verbatim source text — shown as-is, never
parsed into false precision. No eligibility is invented.

## Slice 2 — Backend

- **Model** `models/scholarship.py::Scholarship` (UUIDPrimaryKeyMixin + TimestampMixin):
  `external_id` (String, unique, indexed — the CareerOneStop id, drives idempotent re-seed),
  `name`, `organization`, `purpose` (Text), `level_of_study`, `award_type`, `award_amount`,
  `deadline`, `url`, `source`. A GIN/`pg_trgm`-free simple `ilike` search is enough at 9.5k rows.
- **Migration** — create the `scholarships` table (revision id `schol1a2b3c4d`, down =
  current head `uclaprof5`). Verify single head before/after.
- **Seed** `scripts/seed_scholarships.py` — reads `seed_data/scholarships.json`, upserts by
  `external_id` (idempotent; safe to re-run). Run locally + in prod via the established
  `aws ecs run-task` one-off pattern.
- **Service** `services/scholarship_service.py::ScholarshipService`:
  - `search(q, level, award_type, limit, offset)` — `ilike` over name/org/purpose; optional
    `level` substring filter; `award_type` exact; ordered by name; returns `{items, total}`.
  - `matches_for_student(student_id, limit)` — derive the student's level(s) from their
    profile (target degree / academic records), filter `level_of_study ILIKE %level%`. Real
    signal only; if no level known, fall back to a general list (not a fake "match").
- **API** `api/scholarships.py` (router `/scholarships`, `require_student`):
  - `GET /scholarships?q=&level=&award_type=&page=&page_size=` → paginated list.
  - `GET /scholarships/matches?limit=` → for-your-level list.
  Pydantic `ScholarshipResponse` mirrors the model fields. Register in `api/router.py`.

## Slice 3 — Frontend

- **API** `api/scholarships.ts` — `searchScholarships(params)` + `getScholarshipMatches()`,
  typed `Scholarship`.
- **Resources › Financial** gains a **Scholarships** block above (or beside) the authored
  aid guide:
  - A search box + `level` + `award_type` selects (real option sets derived from the data).
  - A paginated list of `ScholarshipCard`s: name, organization, award type + amount,
    deadline, level, and an **"Apply / details"** external link to the official CareerOneStop
    page (`target=_blank rel=noopener`).
  - Default view = `getScholarshipMatches()` ("for your level"); searching switches to the
    full search. Loading / empty / error states (QueryError + Skeleton).
  - Header note: "Scholarships from the U.S. Dept of Labor's CareerOneStop. Verify amounts
    and deadlines on the official listing." (real attribution + honesty).

## Testing

- **Backend** (`tests/test_scholarships.py`): seed a few rows; search by keyword + level +
  type; pagination; `matches_for_student` filters by level; endpoint shapes + auth (401
  unauth). Idempotent-seed test (re-run doesn't duplicate by external_id).
- **Frontend** (`resources-scholarships.test.tsx`): API maps response; the Scholarships
  block renders a card with name/amount/apply-link; empty + search states.
- Full suites green; `alembic heads` single; ruff + tsc + build clean.

## Ship

- Backend deploy runs the migration; seed prod via ECS run-task (`scripts/seed_scholarships.py`).
- Verify live: `/scholarships?q=engineering` returns real rows; the Resources › Financial
  Scholarships block lists them on app.unipaith.co.

## Out of scope (backlog)

- Field-of-study structured matching (only the keyword/purpose text carries field; defer a
  parsed taxonomy).
- Saving/tracking scholarships to My Space; deadline reminders (a follow-up once the list lands).
- Re-scrape scheduling (the script is idempotent; a cron is a later concern).
