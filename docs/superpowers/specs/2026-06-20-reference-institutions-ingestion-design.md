# Reference Institutions — Ingestion Slice 1 (Design)

**Date:** 2026-06-20
**Status:** Approved (founder: "continue plz")
**Parent:** `2026-06-18-reference-data-catalog-design.md` (the catalog this loads from)
**Slice:** Institution directory — the first ingestion slice. Backend-only.

## REVISION (2026-06-20) — fit the existing Spec 60 reference layer

Current `origin/main` (advanced to #948) already has a **Spec 60 reference/knowledge layer**:
`models/reference.py` defines `ref_occupations`, `ref_majors`, `ref_tests`, `ref_visas`,
`ref_geo_cost`, `ref_rankings`, `ref_accreditation`, the generic `reference_entities`, and
`scholarships` — every one on `UUIDPrimaryKeyMixin + TimestampMixin + ProvenanceMixin` with
`KNOWLEDGE_SOURCE_CHECK` / `KNOWLEDGE_STATUS_CHECK`. There is **no typed `ref_institutions` table**
(institutions only land in the generic `reference_entities`), the typed tables are **not bulk-populated
from authoritative data**, and there is **no public reference read API**.

So this slice is revised: add **`RefInstitution`** (`__tablename__ = "ref_institutions"`) to
`models/reference.py` following that exact pattern — UUID PK, `unitid` unique natural key,
`ProvenanceMixin` (`source="seed"`, `status="live"`, `confidence≈0.9`,
`source_domain="collegescorecard.ed.gov"`) — loaded from the committed Scorecard seed, and served by a
new public reference router (the first one). Everything below is read with this revision in force:
"separate table" now means "a new typed `ref_*` table in the Spec 60 family," not a standalone
Integer-PK table; provenance columns come from `ProvenanceMixin` (replacing the old
`source`/`source_vintage`/`ingested_at` trio, except `source_vintage` is kept as an extra column).

## Problem

The reference-data **catalog** (PR #818) made the College Scorecard / FAFSA / BLS / O*NET archive
*discoverable* — the backend knows what exists and how it is shaped. It is not yet *queryable at
runtime*: the API and the Uni agent still cannot read a single Scorecard number from Postgres. The
founder's goal is "the public data available for the backend so they don't have to go search online."

This slice makes the **institution** universe queryable: a public, UNITID-keyed directory loaded
from College Scorecard, readable by the API and grounded into the Uni agent.

## Goal

A `reference_institutions` table populated from College Scorecard, exposed by a public read API and a
Uni host tool, so the backend grounds institution facts (admit rate, cost, earnings, completion) from
resident data instead of searching the web.

## Non-goals (later slices)

- **Uni LLM tool** (`lookup_institution`) — deferred to slice 1b. CLAUDE.md documents the managed-agent
  tool wiring at `services/uni_tools.py` / `services/uni_agent_host.py`, but those files do **not**
  exist in current `main` (the agent layer changed). Building a tool now means coding against an
  undocumented, moving target. The read API already makes the data queryable; the tool is a thin
  fast-follow once the live agent-host dispatch is mapped.
- Matching-engine wiring (CPEF scoring off reference data).
- Crosswalk that links a *claimed* `Institution` account to its reference row.
- Frontend browse / detail-page rendering (the immediate next slice).
- `reference_program_outcomes` (field-of-study) and the careers layer.

## Why a separate table (not the `Institution` model)

`Institution` rows are **claimed accounts**: `admin_user_id` is `NOT NULL UNIQUE`. A 6,322-row public
directory cannot become `Institution` rows without inventing 6,322 users. `reference_institutions` is
a distinct, read-only, public directory keyed by `unitid`. A future slice adds an optional crosswalk
(`Institution.reference_unitid`) — out of scope here.

## Data flow

```
Data/sources/college-scorecard/institution/Most-Recent-Cohorts-Institution.csv   (96 MB, local-only)
        │  Data/tools/build_reference_seed.py   (distill ~35 columns x 6,322 rows; decode sentinels)
        ▼
unipaith-backend/data/reference/reference_institutions.jsonl   (~3-4 MB, COMMITTED, public-domain)
        │  alembic migration (create table)  +  scripts/seed_reference_institutions.py (upsert by unitid)
        ▼
reference_institutions ──► GET /reference/institutions[/{unitid}]   (public read API)
                       └─► (slice 1b) Uni host tool  lookup_institution(name | unitid)
```

**Why a committed distilled seed** (not download-at-seed / S3): the bulk Scorecard download is a
~700 MB zip with no stable per-file URL; a ~3-4 MB public-domain subset commits cleanly, ships in the
Docker image (which copies `data/`), and makes the prod loader a one-liner. The catalog keeps the
full `download_url` for refresh. JSONL is the seed format — line-oriented, nests `program_pct`/`extra`
cleanly, streams.

## Table: `reference_institutions`

Hybrid — typed, indexable high-value columns + JSONB long tail + provenance. `unitid` is the PK.
Source column in parentheses (resolved via `Data/dictionaries/college-scorecard.fields.json`).

| column | type | source |
|---|---|---|
| `unitid` | Integer PK | UNITID |
| `opeid`, `opeid6` | String | OPEID, OPEID6 |
| `name` | String, indexed | INSTNM |
| `alias` | Text | ALIAS |
| `city`, `state`, `zip` | String | CITY, STABBR, ZIP |
| `lat`, `lon` | Numeric | LATITUDE, LONGITUDE |
| `control_code` | SmallInt | CONTROL |
| `control` | String | decoded: 1→public, 2→private nonprofit, 3→private for-profit |
| `locale_code` | SmallInt | LOCALE |
| `region_code` | SmallInt | REGION |
| `pred_degree`, `high_degree` | SmallInt | PREDDEG, HIGHDEG |
| `accreditor` | String | ACCREDAGENCY |
| `url`, `price_calc_url` | String | INSTURL, NPCURL |
| `admit_rate` | Numeric(5,4) | ADM_RATE |
| `sat_avg` | Integer | SAT_AVG |
| `act_mid` | Integer | ACTCMMID |
| `size` | Integer | UGDS |
| `cost_attendance` | Integer | COSTT4_A |
| `tuition_in`, `tuition_out` | Integer | TUITIONFEE_IN, TUITIONFEE_OUT |
| `pct_pell` | Numeric(5,4) | PCTPELL |
| `completion_rate` | Numeric(5,4) | C150_4 |
| `retention` | Numeric(5,4) | RET_FT4 |
| `earnings_10yr_median` | Integer | MD_EARN_WNE_P10 |
| `median_debt` | Integer | GRAD_DEBT_MDN |
| `carnegie_basic` | SmallInt | CCBASIC |
| `program_pct` | JSONB | {PCIPxx → pct} (program mix) |
| `extra` | JSONB | reserved long tail |
| `source` | String | const "college_scorecard" |
| `source_vintage` | String | data.yaml version (e.g. "2026-03-15") |
| `ingested_at` | DateTime(tz) | load time |

Indexes: `name`, `state`, `control_code`. Migration uses an explicit `op.create_table` (never
`metadata.create_all`), session-unique revision id; check `alembic heads` is single before deploy.

## ETL

- **`Data/tools/build_reference_seed.py`** — reads the local institution CSV + the committed
  dictionary, selects the columns above, decodes Scorecard null sentinels
  (`NULL` / `PrivacySuppressed` / `NA` / `PS` / `""` → `None`), decodes `control`, folds `PCIP*`
  into `program_pct`, and writes the committed JSONL. Idempotent. Run locally (needs the raw CSV).
- **`scripts/seed_reference_institutions.py`** — reads the committed JSONL, upserts by `unitid`
  (PostgreSQL `INSERT ... ON CONFLICT (unitid) DO UPDATE`), sets `ingested_at`. Idempotent; safe to
  re-run in any environment. No raw CSV needed (reads the committed seed) → runs in prod via
  `aws ecs run-task`.

## API — public read (no auth; public reference data)

New thin router `api/reference.py`, registered in `api/router.py`:
- `GET /reference/institutions?q=&state=&control=&min_size=&limit=&offset=` — search/filter; returns
  a compact card projection (name, city, state, control, size, admit_rate, earnings_10yr_median).
- `GET /reference/institutions/{unitid}` — the full record.
Pydantic response schemas inline. Read-only `ReferenceService` (constructor takes `AsyncSession`).

## Uni LLM tool — deferred to slice 1b

`lookup_institution` against `reference_institutions` is a thin fast-follow once the live managed-agent
tool dispatch is located (see Non-goals). Not part of this slice.

## Testing (backend pytest, `AI_MOCK_MODE=true`)

1. **Loader idempotency** — seed twice → row count stable, values updated not duplicated.
2. **Sentinel decoding** — `PrivacySuppressed`/`NULL`/`PS` values load as `None`, not literals.
3. **Control decoding** — code 1/2/3 → correct labels.
4. **API** — search by `q`, filter by `state`+`control`, `{unitid}` detail, 404 for unknown unitid.
A tiny fixture JSONL (3–5 institutions) seeds the test DB — tests never depend on the full file.

## Prod / deploy

- Migration applies on deploy; then seed once via `aws ecs run-task` running
  `scripts/seed_reference_institutions.py` (the committed JSONL is in the image under `data/`).
- Verify live: `GET https://api.unipaith.co/api/v1/reference/institutions?q=stanford` returns a row.
- Check `alembic heads` is singular before deploy (resolve dual heads with a merge migration if not).

## Verification before "done"

`tsc`/build N/A (backend-only). `ruff` clean · full `pytest` green · `alembic heads` singular ·
seed runs idempotently locally · API returns real records · committed seed ~6 MB (6,322 institutions,
public domain; the only new tracked data file). Then commit → PR → merge → deploy → seed in prod →
confirm live URL.
