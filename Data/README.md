# UniPaith Reference Data Archive

Authoritative **public** education datasets, kept resident so the API, the backend LLM (Uni agent +
matching), the `enrich-profile` skill, and the Spec 60 crawler never have to search the web for what
already exists. This folder is the **catalog layer**: it organizes the raw archive and describes it
in machine-readable form. Loading the data into Postgres / the API is a separate, deferred step
(see the follow-up spec).

## What is committed vs. ignored

| | Committed to git | Git-ignored (local / heavy) |
|---|---|---|
| files | `catalog.json`, `dictionaries/*.json`, `tools/build_catalog.py`, this `README.md` | everything under `sources/` (~3.6 GB raw) |

The raw archive is **not** in git (too large) and therefore **not** in production. The small catalog
artifacts are committed and travel with the repo, so any consumer can read *what exists, how it is
shaped, and where to get it* without a download. `.gitignore` enforces this (`Data/sources/`).

## Layout

```
Data/
  catalog.json        # machine-readable manifest — THE contract every consumer reads
  dictionaries/       # normalized field dictionaries (one per source)
    college-scorecard.fields.json                 # institution columns (raw col -> api_name/type/desc/labels)
    college-scorecard-field-of-study.fields.json  # all 178 FoS columns, decoded from the naming grammar
    fafsa.fields.json                             # FAFSA definition terms (from the .doc)
  tools/
    build_catalog.py  # regenerates catalog.json + dictionaries (idempotent)
  sources/            # GIT-IGNORED raw archive
    college-scorecard/{institution,field-of-study,panels,crosswalks}/  + data.yaml
    fafsa/
    bls-onet/  ipeds/  rankings/  scholarships/  international/   # populated by sourcing runs
```

## Sources (current)

| id | publisher | grain | shape |
|---|---|---|---|
| `college-scorecard-institution-latest` | U.S. Dept of Education | institution | 6,322 rows × 3,308 cols |
| `college-scorecard-field-of-study-latest` | U.S. Dept of Education | program (CIP × credential) | 227,980 rows × 178 cols |
| `college-scorecard-panels` | U.S. Dept of Education | yearly time series | 37 files, 1996–2025 |
| `college-scorecard-crosswalks` | U.S. Dept of Education | CIP/UNITID/OPEID crosswalk | 24 files |
| `fafsa-*` (5 datasets) | Federal Student Aid | national / state / institution | xls/xlsx |

All current sources are U.S. federal works — public domain (17 U.S.C. §105). See each entry's
`license` field in `catalog.json`.

## How consumers use this

- **Read `catalog.json`** to discover datasets, their `grain`, `join_keys`, `path`, and `maps_to`
  (which UniPaith entity + detail-page sections each one feeds).
- **Resolve a column** by looking it up in the pointed-to `dictionaries/*.json` (e.g. `MD_EARN_WNE_P10`
  → "Median earnings of students working and not enrolled 10 years after entry"). Categorical fields
  carry inline `value_labels`.
- **Join keys**: `UNITID` (IPEDS) is the spine for institutions; `OPEID`/`OPEID6` bridge to FAFSA and
  federal aid; `CIPCODE` + `CREDLEV` identify a program.

## Refreshing

Re-download the upstream archive (see each entry's `download_url`), drop it under `sources/`, then:

```bash
python3 Data/tools/build_catalog.py
```

The generator recomputes shapes and rebuilds the dictionaries. It is idempotent and never invents
data — datasets not present on disk are marked `status: available` (catalog-only).

## Deferred (follow-up spec)

ETL into Postgres reference tables · API read endpoints · matching-engine wiring · a Uni LLM
reference-lookup tool · S3/prod hosting of the raw archive. `catalog.json` is the blueprint those
will load from.
