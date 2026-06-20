# Reference Data Catalog + Public-Data Sourcing — Design

**Date:** 2026-06-18
**Status:** Approved (founder: "go ahead automatically")
**Scope this round:** Organize + catalog only. ETL / DB / API wiring is deferred to a follow-up spec.

## Problem

The founder downloaded ~3.6 GB of authoritative U.S. public education data into a top-level
`Data/` folder (College Scorecard, FAFSA, an empty Labor-Statistics folder). This is exactly the
data the `enrich-profile` skill and the Spec 60 crawler currently fetch online, one university at a
time. We want it resident and *legible* so the API, the backend LLM (Uni agent + matching), the
enrichment routine, and the crawler stop searching the web for **what exists and how it is shaped**.

Two asks:
1. Arrange the data so both the API and the backend LLM can benefit from it.
2. Source more public data of the same kind.

Constraint that drives everything: production runs on RDS Postgres behind ECS. Local files in a dev
checkout never reach prod. So the *raw* archive cannot help prod directly — but a small, committed,
machine-readable **catalog** can: it is the contract every consumer reads, and the precise blueprint
the deferred ingestion spec will load from.

## Non-goals (deferred to a follow-up spec)

- ETL into Postgres reference tables
- API read endpoints over the data
- Matching-engine wiring
- A Uni LLM "reference lookup" tool
- Hosting the raw archive in S3 / prod

The `catalog.json` produced here is the input to all of the above.

## Approach (chosen: catalog-in-place)

Keep the raw archive in the top-level `Data/` folder, reorganize it into a stable
`sources/<publisher>/<grain>/` taxonomy, and author three small, committed artifacts co-located
with the data: a machine-readable `catalog.json`, a normalized `dictionaries/` set, and a human
`README.md`. One source of truth. The heavy raw files stay git-ignored; only the catalog artifacts
are committed.

Rejected alternatives:
- **Backend-embedded package** (move catalog into `unipaith-backend/src/.../reference/`) — drifts
  toward the ingestion we deferred and risks two-location drift. Revisit in the ETL spec.
- **DuckDB/SQLite queryable index** — that is the "curated + lookup tool" option the founder did not
  pick this round.

## Layout

```
Data/
  README.md                         # committed — human guide, provenance, license, refresh how-to
  catalog.json                      # committed — machine-readable manifest (the contract)
  dictionaries/                     # committed — normalized field dictionaries, one per source
    college-scorecard.fields.json
    fafsa.fields.json
  tools/
    build_catalog.py                # committed — regenerates catalog.json + dictionaries (idempotent)
  sources/                          # git-IGNORED (heavy raw)
    college-scorecard/
      institution/                  # Most-Recent-Cohorts-Institution.csv
      field-of-study/               # Most-Recent-Cohorts-Field-of-Study.csv
      panels/                       # MERGED*_PP.csv, FieldOfStudyData*_PP.csv (yearly)
      crosswalks/                   # CW*.xlsx
      data.yaml                     # raw dictionary (source for the normalized dict)
    fafsa/                          # the .xls/.xlsx + the definitions .doc
    bls-onet/   ipeds/   rankings/   scholarships/   international/   # filled by Part 2
```

## catalog.json schema

Top level: `{ schema_version, generated_at, source_root, datasets: [...] }`.

Each dataset entry:

| field | meaning |
|---|---|
| `id` | stable slug, e.g. `college-scorecard-institution-latest` |
| `title` | human title |
| `publisher` | e.g. "U.S. Department of Education" |
| `source_url` | landing page |
| `download_url` | direct download (so refresh needs no web search) |
| `license` | e.g. "U.S. Government Work — public domain" |
| `grain` | `institution` \| `program` \| `state` \| `occupation` \| ... |
| `entity` | UniPaith entity it describes |
| `join_keys` | e.g. `["UNITID","OPEID","OPEID6"]`, `["CIPCODE","CREDLEV"]`, `["FIPS"]` |
| `coverage` | `{ latest_cohort, panel_years }` |
| `path` | repo-relative path under `Data/` (may be absent locally when `status:available`) |
| `format` | `csv` \| `xlsx` \| `xls` \| ... |
| `size_bytes`, `rows`, `columns` | shape (null when not downloaded) |
| `dictionary` | pointer into `dictionaries/` (or upstream URL) |
| `key_fields` | the high-value subset of columns |
| `maps_to` | `{ unipaith_entity, sections: [...] }` — where it serves the product |
| `status` | `downloaded` \| `available` |
| `committed` | whether the raw file is committed (always false for heavy raw) |

## Normalized dictionaries

`dictionaries/college-scorecard.fields.json` is derived from `data.yaml`'s `dictionary:` block:
`{ RAW_COL: { api_name, type, label, value_labels } }`. This lets any consumer resolve
"what is `MD_EARN_WNE_P10`" without parsing 800 KB of YAML. FAFSA's dictionary is extracted from
`FAFSAReportDefinitions.doc` via `textutil` into prose-keyed definitions.

## The "meaningful arrangement" = the maps_to crosswalk

Every dataset is tied to where it serves UniPaith, so a consumer knows *why* it matters:

| Dataset | maps_to |
|---|---|
| Scorecard · institution | institution detail: report-card stats · admissions funnel · outcomes/cost · quick facts |
| Scorecard · field-of-study | program detail: earnings/debt/completion by CIP + credential level |
| FAFSA | financial-need / aid context; federal school-code reference |
| BLS OES / O*NET (Part 2) | major → career outcomes, salary, projected growth |
| IPEDS (Part 2) | enrollment / faculty / finance depth by demographic |
| Rankings / Carnegie (Part 2) | the "distinction" sections |
| Scholarships (Part 2) | maps to the existing Spec 60 `scholarships` / `ref_*` tables |

## Part 2 — sourcing more public data (subagent-driven, verified)

Fan out parallel research agents (one per category: BLS/O*NET, IPEDS, rankings/Carnegie,
scholarships, international/visa, plus a "what else is relevant" scout) using a Workflow. Each
returns: authoritative source, direct download URL, license, grain, join keys, dictionary URL,
estimated size, and UniPaith relevance — as structured output.

Because subagents can confabulate URLs, every candidate passes an **adversarial verification** stage
(an independent agent fetches the URL and confirms it resolves, is the real publisher, and the
license is genuinely open) before it enters the catalog. Verified-real entries only.

Then, in the main loop: **catalog all** verified datasets, and **download** the high-value,
reasonably-sized, openly-licensed ones (e.g. O*NET database, BLS OES, Carnegie classifications,
select IPEDS surveys) into the taxonomy. Heavy or gated sets stay as `status: available` catalog
entries with their URLs.

## Safety

`.gitignore` ignores `Data/sources/` and heavy globs, with negations so `catalog.json`,
`dictionaries/`, `README.md`, and `tools/` stay committed. Prevents an accidental 3.6 GB commit.

## Verification

- `catalog.json` parses; every `path` with `status:downloaded` exists on disk locally.
- `dictionaries/*.json` parse; Scorecard dict key count matches `data.yaml` dictionary entries.
- `git status` clean after commit; no file > a few hundred KB is tracked.
- Part 2: each cataloged URL was fetched and returned 200 from the stated publisher.

## Follow-up spec (ingestion) will

Define reference tables, an idempotent loader reading `catalog.json`, API endpoints, the matching
seam, the Uni reference tool, and S3/prod hosting of the raw archive.
