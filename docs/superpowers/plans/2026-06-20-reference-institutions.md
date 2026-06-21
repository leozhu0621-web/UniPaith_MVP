# Reference Institutions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the College Scorecard institution universe queryable by the backend — a public `reference_institutions` table loaded from a committed distilled seed, exposed by a public read API.

**Architecture:** New `ReferenceInstitution` model (Integer `unitid` PK, separate from claimed `Institution` accounts). Pure ingest helpers in `services/reference_ingest.py` decode Scorecard rows + upsert by unitid; a builder (`Data/tools/build_reference_seed.py`) distills the local 96 MB CSV into a committed ~3-4 MB JSONL; a loader script seeds any environment from that JSONL. A read-only `ReferenceService` + public `/reference/institutions` router serve it.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2 async, PostgreSQL, Alembic, pytest-asyncio.

**Spec:** `docs/superpowers/specs/2026-06-20-reference-institutions-ingestion-design.md`

> **AS-BUILT REVISION (2026-06-20):** discovered current `main` already has the Spec 60 reference
> layer (`models/reference.py`, `ref_*` tables, `ProvenanceMixin`). So the as-built deviates from the
> from-scratch tasks below: `RefInstitution` was **added to `models/reference.py`** (not a new file),
> follows the **`UUIDPrimaryKeyMixin + ProvenanceMixin`** pattern (UUID PK, `unitid` unique, `source='seed'`
> — *not* an Integer PK with bespoke provenance columns), and the migration is **hand-written** (the dev
> DB is `create_all`-polluted so autogenerate is unusable) and also **merges main's pre-existing dual head**
> (`aivisamerge1` + `utaustpercrd1`). The Uni tool stays deferred (slice 1b). Helper/service/API/test
> shapes match the tasks below; the model + migration are the deviations. See the spec's REVISION section.

**Env note (Pre-Work):** the run commands below assume `DATABASE_URL` is exported to the dev Postgres string documented in CLAUDE.md (Testing → "Required env vars"). Before coding, confirm Postgres is up and the suite is green: `make dev-db`, export `DATABASE_URL`, then `cd unipaith-backend && PYTHONPATH=src AI_MOCK_MODE=true .venv/bin/pytest tests/test_health.py -q`. Current single alembic head: `s56a1b2c3d4e`.

---

## File Structure

- Create `unipaith-backend/src/unipaith/models/reference.py` — `ReferenceInstitution` model.
- Modify `unipaith-backend/src/unipaith/models/__init__.py` — export the model (registers it on `Base.metadata` so tests' `create_all` builds it).
- Create `unipaith-backend/src/unipaith/services/reference_ingest.py` — pure helpers: `clean_value`, `decode_control`, `csv_row_to_record`, `upsert_institutions`, plus `SCALAR_MAP`.
- Create `unipaith-backend/src/unipaith/services/reference_service.py` — read-only `ReferenceService`.
- Create `unipaith-backend/src/unipaith/api/reference.py` — public `/reference` router + Pydantic schemas.
- Modify `unipaith-backend/src/unipaith/api/router.py` — register the router.
- Create `Data/tools/build_reference_seed.py` — distills the local CSV → committed JSONL.
- Create `unipaith-backend/data/reference/reference_institutions.jsonl` — committed distilled seed (generated).
- Create `unipaith-backend/scripts/seed_reference_institutions.py` — idempotent loader.
- Create `unipaith-backend/alembic/versions/refinst01_reference_institutions.py` — table migration.
- Create `unipaith-backend/tests/test_reference_institutions.py` — tests.

---

### Task 1: `ReferenceInstitution` model

**Files:**
- Create: `unipaith-backend/src/unipaith/models/reference.py`
- Modify: `unipaith-backend/src/unipaith/models/__init__.py`

- [ ] **Step 1: Write the model**

```python
# unipaith-backend/src/unipaith/models/reference.py
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Integer, Numeric, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from unipaith.models.base import Base, TimestampMixin


class ReferenceInstitution(Base, TimestampMixin):
    """Public U.S. institution directory loaded from College Scorecard.

    Read-only reference data keyed by IPEDS `unitid`. Distinct from the
    `institutions` table, whose rows are claimed accounts (admin_user_id NOT NULL).
    """

    __tablename__ = "reference_institutions"

    unitid: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    opeid: Mapped[str | None] = mapped_column(String(20))
    opeid6: Mapped[str | None] = mapped_column(String(20))
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    alias: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(String(120))
    state: Mapped[str | None] = mapped_column(String(10), index=True)
    zip: Mapped[str | None] = mapped_column(String(20))
    lat: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    lon: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    control_code: Mapped[int | None] = mapped_column(SmallInteger, index=True)
    control: Mapped[str | None] = mapped_column(String(40))
    locale_code: Mapped[int | None] = mapped_column(SmallInteger)
    region_code: Mapped[int | None] = mapped_column(SmallInteger)
    pred_degree: Mapped[int | None] = mapped_column(SmallInteger)
    high_degree: Mapped[int | None] = mapped_column(SmallInteger)
    accreditor: Mapped[str | None] = mapped_column(String(255))
    url: Mapped[str | None] = mapped_column(String(500))
    price_calc_url: Mapped[str | None] = mapped_column(String(500))
    admit_rate: Mapped[Decimal | None] = mapped_column(Numeric(6, 4))
    sat_avg: Mapped[int | None] = mapped_column(Integer)
    act_mid: Mapped[int | None] = mapped_column(Integer)
    size: Mapped[int | None] = mapped_column(Integer)
    cost_attendance: Mapped[int | None] = mapped_column(Integer)
    tuition_in: Mapped[int | None] = mapped_column(Integer)
    tuition_out: Mapped[int | None] = mapped_column(Integer)
    pct_pell: Mapped[Decimal | None] = mapped_column(Numeric(6, 4))
    completion_rate: Mapped[Decimal | None] = mapped_column(Numeric(6, 4))
    retention: Mapped[Decimal | None] = mapped_column(Numeric(6, 4))
    earnings_10yr_median: Mapped[int | None] = mapped_column(Integer)
    median_debt: Mapped[int | None] = mapped_column(Integer)
    carnegie_basic: Mapped[int | None] = mapped_column(SmallInteger)
    program_pct: Mapped[dict | None] = mapped_column(JSONB)
    extra: Mapped[dict | None] = mapped_column(JSONB)
    source: Mapped[str] = mapped_column(String(40), nullable=False, default="college_scorecard")
    source_vintage: Mapped[str | None] = mapped_column(String(40))
    ingested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
```

- [ ] **Step 2: Export it** — add to `unipaith-backend/src/unipaith/models/__init__.py` (follow the existing `from unipaith.models.X import Y` block + `__all__` if present):

```python
from unipaith.models.reference import ReferenceInstitution
```
(If the file has an `__all__` list, add `"ReferenceInstitution"`.)

- [ ] **Step 3: Verify it imports + registers**

Run: `cd unipaith-backend && PYTHONPATH=src python -c "from unipaith.models import ReferenceInstitution; print(ReferenceInstitution.__tablename__)"`
Expected: `reference_institutions`

- [ ] **Step 4: Commit**

```bash
git add unipaith-backend/src/unipaith/models/reference.py unipaith-backend/src/unipaith/models/__init__.py
git commit -m "feat(reference): ReferenceInstitution model"
```

---

### Task 2: Ingest helpers (`clean_value`, `decode_control`, `csv_row_to_record`) — TDD

**Files:**
- Create: `unipaith-backend/src/unipaith/services/reference_ingest.py`
- Test: `unipaith-backend/tests/test_reference_institutions.py`

- [ ] **Step 1: Write failing tests**

```python
# unipaith-backend/tests/test_reference_institutions.py
import pytest

from unipaith.services.reference_ingest import (
    clean_value,
    decode_control,
    csv_row_to_record,
)


def test_clean_value_decodes_sentinels():
    for sentinel in ["NULL", "PrivacySuppressed", "NA", "PS", ""]:
        assert clean_value(sentinel) is None
    assert clean_value("0.1234") == "0.1234"


def test_decode_control():
    assert decode_control(1) == "public"
    assert decode_control(2) == "private nonprofit"
    assert decode_control(3) == "private for-profit"
    assert decode_control(None) is None


def test_csv_row_to_record_maps_and_folds_program_pct():
    row = {
        "UNITID": "166027", "OPEID": "00216500", "OPEID6": "002165",
        "INSTNM": "Harvard University", "CITY": "Cambridge", "STABBR": "MA",
        "CONTROL": "2", "ADM_RATE": "0.0468", "UGDS": "7973",
        "MD_EARN_WNE_P10": "95114", "SAT_AVG": "1520",
        "PCIP11": "0.12", "PCIP14": "PrivacySuppressed", "PCIP52": "0",
    }
    rec = csv_row_to_record(row)
    assert rec["unitid"] == 166027
    assert rec["name"] == "Harvard University"
    assert rec["control_code"] == 2
    assert rec["control"] == "private nonprofit"
    assert rec["admit_rate"] == 0.0468
    assert rec["size"] == 7973
    assert rec["earnings_10yr_median"] == 95114
    # program_pct folds non-null PCIP*, drops sentinels
    assert rec["program_pct"]["PCIP11"] == 0.12
    assert "PCIP14" not in rec["program_pct"]
```

- [ ] **Step 2: Run to verify they fail**

Run: `cd unipaith-backend && PYTHONPATH=src AI_MOCK_MODE=true .venv/bin/pytest tests/test_reference_institutions.py -q`
Expected: FAIL (ImportError: cannot import name 'clean_value')

- [ ] **Step 3: Implement the helpers**

```python
# unipaith-backend/src/unipaith/services/reference_ingest.py
from __future__ import annotations

NULL_SENTINELS = {"NULL", "PrivacySuppressed", "NA", "PS", ""}
CONTROL_LABELS = {1: "public", 2: "private nonprofit", 3: "private for-profit"}

# model_field -> (csv_column, caster)
SCALAR_MAP: dict[str, tuple[str, str]] = {
    "opeid": ("OPEID", "str"), "opeid6": ("OPEID6", "str"),
    "name": ("INSTNM", "str"), "alias": ("ALIAS", "str"),
    "city": ("CITY", "str"), "state": ("STABBR", "str"), "zip": ("ZIP", "str"),
    "lat": ("LATITUDE", "float"), "lon": ("LONGITUDE", "float"),
    "control_code": ("CONTROL", "int"),
    "locale_code": ("LOCALE", "int"), "region_code": ("REGION", "int"),
    "pred_degree": ("PREDDEG", "int"), "high_degree": ("HIGHDEG", "int"),
    "accreditor": ("ACCREDAGENCY", "str"),
    "url": ("INSTURL", "str"), "price_calc_url": ("NPCURL", "str"),
    "admit_rate": ("ADM_RATE", "float"), "sat_avg": ("SAT_AVG", "int"),
    "act_mid": ("ACTCMMID", "int"), "size": ("UGDS", "int"),
    "cost_attendance": ("COSTT4_A", "int"),
    "tuition_in": ("TUITIONFEE_IN", "int"), "tuition_out": ("TUITIONFEE_OUT", "int"),
    "pct_pell": ("PCTPELL", "float"), "completion_rate": ("C150_4", "float"),
    "retention": ("RET_FT4", "float"),
    "earnings_10yr_median": ("MD_EARN_WNE_P10", "int"),
    "median_debt": ("GRAD_DEBT_MDN", "int"),
    "carnegie_basic": ("CCBASIC", "int"),
}


def clean_value(raw):
    if raw is None:
        return None
    s = str(raw).strip()
    return None if s in NULL_SENTINELS else s


def decode_control(code):
    return CONTROL_LABELS.get(code) if code is not None else None


def _cast(value, kind):
    if value is None:
        return None
    try:
        if kind == "int":
            return int(float(value))  # tolerate "12.0"
        if kind == "float":
            return float(value)
        return value  # str
    except (TypeError, ValueError):
        return None


def csv_row_to_record(row: dict) -> dict:
    """Map one Scorecard CSV row (dict of raw strings) to a JSONL-ready record."""
    rec: dict = {"unitid": _cast(clean_value(row.get("UNITID")), "int")}
    for field, (col, kind) in SCALAR_MAP.items():
        rec[field] = _cast(clean_value(row.get(col)), kind)
    rec["control"] = decode_control(rec.get("control_code"))
    program_pct = {}
    for col, val in row.items():
        if col.startswith("PCIP"):
            f = _cast(clean_value(val), "float")
            if f is not None and f > 0:
                program_pct[col] = f
    rec["program_pct"] = program_pct or None
    rec["source"] = "college_scorecard"
    return rec
```

- [ ] **Step 4: Run to verify pass**

Run: `cd unipaith-backend && PYTHONPATH=src AI_MOCK_MODE=true .venv/bin/pytest tests/test_reference_institutions.py -q`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add unipaith-backend/src/unipaith/services/reference_ingest.py unipaith-backend/tests/test_reference_institutions.py
git commit -m "feat(reference): Scorecard row decode helpers + tests"
```

---

### Task 3: `upsert_institutions` (idempotent) — TDD

**Files:**
- Modify: `unipaith-backend/src/unipaith/services/reference_ingest.py`
- Modify: `unipaith-backend/tests/test_reference_institutions.py`

- [ ] **Step 1: Write failing test** (append to the test file)

```python
from datetime import datetime, timezone

from sqlalchemy import select, func
from unipaith.models import ReferenceInstitution
from unipaith.services.reference_ingest import upsert_institutions


@pytest.mark.asyncio
async def test_upsert_is_idempotent(db_session):
    recs = [
        {"unitid": 1, "name": "Alpha U", "state": "CA", "control_code": 1, "control": "public"},
        {"unitid": 2, "name": "Beta College", "state": "NY", "control_code": 2,
         "control": "private nonprofit"},
    ]
    await upsert_institutions(db_session, recs)
    await upsert_institutions(db_session, recs)  # second time must not duplicate
    count = await db_session.scalar(select(func.count()).select_from(ReferenceInstitution))
    assert count == 2
    # update path: change a value, re-upsert
    recs[0]["name"] = "Alpha University"
    await upsert_institutions(db_session, recs)
    row = await db_session.get(ReferenceInstitution, 1)
    assert row.name == "Alpha University"
    assert row.ingested_at is not None
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd unipaith-backend && PYTHONPATH=src AI_MOCK_MODE=true DATABASE_URL="$DATABASE_URL" COGNITO_BYPASS=true S3_LOCAL_MODE=true .venv/bin/pytest tests/test_reference_institutions.py::test_upsert_is_idempotent -q`
Expected: FAIL (ImportError: cannot import name 'upsert_institutions')

- [ ] **Step 3: Implement upsert** (append to `reference_ingest.py`)

```python
from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

# columns the upsert is allowed to write (everything except the PK + server-managed timestamps)
_UPSERT_COLUMNS = [
    "opeid", "opeid6", "name", "alias", "city", "state", "zip", "lat", "lon",
    "control_code", "control", "locale_code", "region_code", "pred_degree", "high_degree",
    "accreditor", "url", "price_calc_url", "admit_rate", "sat_avg", "act_mid", "size",
    "cost_attendance", "tuition_in", "tuition_out", "pct_pell", "completion_rate", "retention",
    "earnings_10yr_median", "median_debt", "carnegie_basic", "program_pct", "extra",
    "source", "source_vintage", "ingested_at",
]


async def upsert_institutions(db: AsyncSession, records: list[dict], batch_size: int = 500) -> int:
    """Upsert reference-institution records by unitid. Idempotent."""
    from unipaith.models import ReferenceInstitution

    now = datetime.now(timezone.utc)
    n = 0
    for start in range(0, len(records), batch_size):
        chunk = records[start : start + batch_size]
        rows = []
        for r in chunk:
            if r.get("unitid") is None:
                continue
            row = {"unitid": r["unitid"], "ingested_at": now}
            for col in _UPSERT_COLUMNS:
                if col in r:
                    row[col] = r[col]
            row.setdefault("source", "college_scorecard")
            rows.append(row)
        if not rows:
            continue
        stmt = pg_insert(ReferenceInstitution).values(rows)
        update_cols = {c: getattr(stmt.excluded, c) for c in _UPSERT_COLUMNS if c in rows[0]}
        stmt = stmt.on_conflict_do_update(index_elements=["unitid"], set_=update_cols)
        await db.execute(stmt)
        n += len(rows)
    await db.commit()
    return n
```

- [ ] **Step 4: Run to verify pass**

Run: same pytest command as Step 2.
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add unipaith-backend/src/unipaith/services/reference_ingest.py unipaith-backend/tests/test_reference_institutions.py
git commit -m "feat(reference): idempotent upsert_institutions"
```

---

### Task 4: Seed builder + generate the committed JSONL

**Files:**
- Create: `Data/tools/build_reference_seed.py`
- Create (generated): `unipaith-backend/data/reference/reference_institutions.jsonl`

- [ ] **Step 1: Write the builder** (reads local CSV, reuses backend helpers via sys.path)

```python
#!/usr/bin/env python3
"""Distill the local College Scorecard institution CSV into a committed JSONL seed.

Run locally (needs the raw CSV under Data/sources/). Idempotent.

    python3 Data/tools/build_reference_seed.py
"""
from __future__ import annotations
import json
import os
import sys
import csv

HERE = os.path.dirname(os.path.abspath(__file__))            # Data/tools
REPO = os.path.dirname(os.path.dirname(HERE))                # repo root
sys.path.insert(0, os.path.join(REPO, "unipaith-backend", "src"))
from unipaith.services.reference_ingest import csv_row_to_record  # noqa: E402

CSV = os.path.join(REPO, "Data/sources/college-scorecard/institution/Most-Recent-Cohorts-Institution.csv")
DICT = os.path.join(REPO, "Data/dictionaries/college-scorecard.fields.json")
OUT = os.path.join(REPO, "unipaith-backend/data/reference/reference_institutions.jsonl")


def vintage() -> str | None:
    try:
        return json.load(open(DICT))["_meta"].get("version")
    except Exception:
        return None


def main() -> int:
    csv.field_size_limit(10_000_000)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    v = vintage()
    n = 0
    with open(CSV, newline="", encoding="utf-8", errors="replace") as fh, open(OUT, "w") as out:
        for row in csv.DictReader(fh):
            rec = csv_row_to_record(row)
            if rec.get("unitid") is None or not rec.get("name"):
                continue
            rec["source_vintage"] = v
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n += 1
    print(f"wrote {n} institutions -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Generate the seed**

Run: `cd "$(git rev-parse --show-toplevel)" && python3 Data/tools/build_reference_seed.py`
Expected: `wrote ~6322 institutions -> .../reference_institutions.jsonl`

- [ ] **Step 3: Sanity-check the seed**

Run: `wc -l unipaith-backend/data/reference/reference_institutions.jsonl && du -h unipaith-backend/data/reference/reference_institutions.jsonl && head -1 unipaith-backend/data/reference/reference_institutions.jsonl | python3 -m json.tool | head -20`
Expected: ~6322 lines, ≤ ~4 MB, first record has unitid/name/control.

- [ ] **Step 4: Confirm the Docker image will ship it** — verify `unipaith-backend/Dockerfile` copies `data/` (grep): `grep -n "COPY .*data" unipaith-backend/Dockerfile`. If `data/` is not copied, add `COPY data/ ./data/` (or adjust) so the seed reaches prod.

- [ ] **Step 5: Commit** (builder + the committed JSONL)

```bash
git add Data/tools/build_reference_seed.py unipaith-backend/data/reference/reference_institutions.jsonl
git commit -m "feat(reference): distilled Scorecard institution seed (JSONL) + builder"
```

---

### Task 5: Loader script

**Files:**
- Create: `unipaith-backend/scripts/seed_reference_institutions.py`

- [ ] **Step 1: Write the loader** (thin wrapper around `upsert_institutions`)

```python
#!/usr/bin/env python3
"""Idempotent loader: upsert reference_institutions from the committed JSONL seed.

    PYTHONPATH=src python scripts/seed_reference_institutions.py

Safe to re-run in any environment (reads the committed seed, no raw CSV needed).
"""
from __future__ import annotations
import asyncio
import json
import os

from unipaith.database import async_session
from unipaith.services.reference_ingest import upsert_institutions

SEED = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "data", "reference", "reference_institutions.jsonl")


async def main() -> None:
    records = [json.loads(line) for line in open(SEED, encoding="utf-8") if line.strip()]
    async with async_session() as db:
        n = await upsert_institutions(db, records)
    print(f"seeded {n} reference institutions")


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 2: Run it locally against dev DB**

Run: `cd unipaith-backend && PYTHONPATH=src DATABASE_URL="$DATABASE_URL" python scripts/seed_reference_institutions.py`
Expected: `seeded ~6322 reference institutions` (after the migration in Task 7 — or run the migration first; for a quick check the table must exist).

- [ ] **Step 3: Commit**

```bash
git add unipaith-backend/scripts/seed_reference_institutions.py
git commit -m "feat(reference): idempotent JSONL loader script"
```

---

### Task 6: `ReferenceService` + public API + register — TDD

**Files:**
- Create: `unipaith-backend/src/unipaith/services/reference_service.py`
- Create: `unipaith-backend/src/unipaith/api/reference.py`
- Modify: `unipaith-backend/src/unipaith/api/router.py`
- Modify: `unipaith-backend/tests/test_reference_institutions.py`

- [ ] **Step 1: Write failing API tests** (append to the test file)

```python
async def _seed_three(db_session):
    from unipaith.services.reference_ingest import upsert_institutions
    await upsert_institutions(db_session, [
        {"unitid": 166027, "name": "Harvard University", "state": "MA", "control_code": 2,
         "control": "private nonprofit", "size": 7973, "admit_rate": 0.0468,
         "earnings_10yr_median": 95114},
        {"unitid": 110635, "name": "University of California-Berkeley", "state": "CA",
         "control_code": 1, "control": "public", "size": 30980, "admit_rate": 0.1124},
        {"unitid": 243744, "name": "Stanford University", "state": "CA", "control_code": 2,
         "control": "private nonprofit", "size": 7645, "admit_rate": 0.0434},
    ])


@pytest.mark.asyncio
async def test_api_search_and_filter(client, db_session):
    await _seed_three(db_session)
    r = await client.get("/api/v1/reference/institutions", params={"q": "stanford"})
    assert r.status_code == 200
    body = r.json()
    assert any(i["name"] == "Stanford University" for i in body["items"])

    r = await client.get("/api/v1/reference/institutions",
                         params={"state": "CA", "control": "public"})
    names = [i["name"] for i in r.json()["items"]]
    assert names == ["University of California-Berkeley"]


@pytest.mark.asyncio
async def test_api_detail_and_404(client, db_session):
    await _seed_three(db_session)
    r = await client.get("/api/v1/reference/institutions/166027")
    assert r.status_code == 200
    assert r.json()["name"] == "Harvard University"
    assert r.json()["earnings_10yr_median"] == 95114

    r = await client.get("/api/v1/reference/institutions/999999")
    assert r.status_code == 404
```

Note: confirm the `/api/v1` prefix by checking how `main.py` mounts `api_router` (grep `include_router(api_router`); adjust the test path prefix if different.

- [ ] **Step 2: Run to verify they fail**

Run: `cd unipaith-backend && PYTHONPATH=src AI_MOCK_MODE=true DATABASE_URL="$DATABASE_URL" COGNITO_BYPASS=true S3_LOCAL_MODE=true .venv/bin/pytest tests/test_reference_institutions.py -k api -q`
Expected: FAIL (404 for all — router not registered)

- [ ] **Step 3: Implement the service**

```python
# unipaith-backend/src/unipaith/services/reference_service.py
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models import ReferenceInstitution


class ReferenceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def search_institutions(self, *, q=None, state=None, control=None,
                                  min_size=None, limit=25, offset=0):
        stmt = select(ReferenceInstitution)
        if q:
            stmt = stmt.where(ReferenceInstitution.name.ilike(f"%{q}%"))
        if state:
            stmt = stmt.where(ReferenceInstitution.state == state.upper())
        if control:
            stmt = stmt.where(ReferenceInstitution.control == control)
        if min_size:
            stmt = stmt.where(ReferenceInstitution.size >= min_size)
        stmt = stmt.order_by(ReferenceInstitution.name).limit(min(limit, 100)).offset(offset)
        return list((await self.db.scalars(stmt)).all())

    async def get_institution(self, unitid: int):
        return await self.db.get(ReferenceInstitution, unitid)
```

- [ ] **Step 4: Implement the API**

```python
# unipaith-backend/src/unipaith/api/reference.py
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.services.reference_service import ReferenceService

router = APIRouter(prefix="/reference", tags=["reference"])


class InstitutionCard(BaseModel):
    unitid: int
    name: str
    city: str | None = None
    state: str | None = None
    control: str | None = None
    size: int | None = None
    admit_rate: float | None = None
    earnings_10yr_median: int | None = None

    class Config:
        from_attributes = True


class InstitutionDetail(InstitutionCard):
    opeid6: str | None = None
    zip: str | None = None
    accreditor: str | None = None
    url: str | None = None
    pred_degree: int | None = None
    high_degree: int | None = None
    sat_avg: int | None = None
    act_mid: int | None = None
    cost_attendance: int | None = None
    tuition_in: int | None = None
    tuition_out: int | None = None
    pct_pell: float | None = None
    completion_rate: float | None = None
    retention: float | None = None
    median_debt: int | None = None
    carnegie_basic: int | None = None
    program_pct: dict | None = None
    source: str | None = None
    source_vintage: str | None = None


class InstitutionList(BaseModel):
    items: list[InstitutionCard]


@router.get("/institutions", response_model=InstitutionList,
            summary="Search the public Scorecard institution directory")
async def list_institutions(
    q: str | None = None,
    state: str | None = None,
    control: str | None = None,
    min_size: int | None = None,
    limit: int = Query(25, le=100),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    rows = await ReferenceService(db).search_institutions(
        q=q, state=state, control=control, min_size=min_size, limit=limit, offset=offset)
    return {"items": rows}


@router.get("/institutions/{unitid}", response_model=InstitutionDetail,
            summary="Full reference record for one institution")
async def get_institution(unitid: int, db: AsyncSession = Depends(get_db)):
    row = await ReferenceService(db).get_institution(unitid)
    if row is None:
        raise HTTPException(status_code=404, detail="Institution not found")
    return row
```

- [ ] **Step 5: Register the router** in `unipaith-backend/src/unipaith/api/router.py` — add the import beside the others and an `api_router.include_router(reference_router)` line near the other public routers:

```python
from unipaith.api.reference import router as reference_router
...
api_router.include_router(reference_router)
```

- [ ] **Step 6: Run to verify pass**

Run: same as Step 2.
Expected: PASS (both api tests)

- [ ] **Step 7: Commit**

```bash
git add unipaith-backend/src/unipaith/services/reference_service.py unipaith-backend/src/unipaith/api/reference.py unipaith-backend/src/unipaith/api/router.py unipaith-backend/tests/test_reference_institutions.py
git commit -m "feat(reference): ReferenceService + public /reference/institutions API"
```

---

### Task 7: Migration + full verification

**Files:**
- Create: `unipaith-backend/alembic/versions/refinst01_reference_institutions.py`

- [ ] **Step 1: Autogenerate the migration** (DB must be at head first)

Run: `cd unipaith-backend && PYTHONPATH=src DATABASE_URL="$DATABASE_URL" .venv/bin/alembic revision --autogenerate -m "reference_institutions"`
Then open the generated file and confirm: `down_revision = "s56a1b2c3d4e"`, it creates `reference_institutions` with all columns + the `name`/`state`/`control_code` indexes, and `op.drop_table` in `downgrade`. Rename the file/revision id to `refinst01_reference_institutions` / `revision = "refinst01"` for a session-unique id. Remove any unrelated autogen noise.

- [ ] **Step 2: Apply + verify single head**

Run: `cd unipaith-backend && PYTHONPATH=src DATABASE_URL="$DATABASE_URL" .venv/bin/alembic upgrade head && PYTHONPATH=src .venv/bin/alembic heads`
Expected: upgrade OK; `alembic heads` prints exactly one head (`refinst01`).

- [ ] **Step 3: Seed locally end-to-end**

Run: `cd unipaith-backend && PYTHONPATH=src DATABASE_URL="$DATABASE_URL" python scripts/seed_reference_institutions.py`
Expected: `seeded ~6322 reference institutions`. Re-run once → same count (idempotent).

- [ ] **Step 4: Full suite + lint**

Run:
```bash
cd unipaith-backend && PYTHONPATH=src AI_MOCK_MODE=true DATABASE_URL="$DATABASE_URL" COGNITO_BYPASS=true S3_LOCAL_MODE=true .venv/bin/pytest tests/test_reference_institutions.py -q
ruff check src/unipaith/services/reference_ingest.py src/unipaith/services/reference_service.py src/unipaith/api/reference.py src/unipaith/models/reference.py ; echo "EXIT=$?"
```
Then the full backend suite to catch regressions: `make test-backend` (or the documented pytest invocation).
Expected: all green; ruff EXIT=0.

- [ ] **Step 5: Commit the migration**

```bash
git add unipaith-backend/alembic/versions/refinst01_reference_institutions.py
git commit -m "feat(reference): migration for reference_institutions"
```

---

### Task 8: Ship

- [ ] **Step 1:** Push branch, open PR to `main`, ensure CI green.
- [ ] **Step 2:** Confirm `alembic heads` singular on the branch; if a concurrent migration created a second head, add a merge migration (session-unique id) and re-run the suite.
- [ ] **Step 3:** Merge (squash). Verify `origin/main` advanced and the committed seed (≤ ~4 MB) is the only new data file.
- [ ] **Step 4:** After deploy, run the seed once in prod: `aws ecs run-task` invoking `scripts/seed_reference_institutions.py`.
- [ ] **Step 5:** Verify live: `curl 'https://api.unipaith.co/api/v1/reference/institutions?q=stanford'` returns a row; `curl 'https://api.unipaith.co/api/v1/reference/institutions/243744'` returns Stanford. Report the live URL.

---

## Self-Review

- **Spec coverage:** table (T1+T7) · committed distilled seed (T4) · idempotent loader (T3+T5) · sentinel + control decoding (T2) · public read API search/detail/404 (T6) · prod seed + live verify (T8). Uni tool is explicitly deferred (slice 1b) — no task, matches the spec's Non-goals. ✓
- **Placeholders:** none — every code step shows complete code; commands have expected output. ✓
- **Type consistency:** `csv_row_to_record`/`upsert_institutions`/`ReferenceInstitution`/`ReferenceService.search_institutions` signatures match across tasks; JSONL record keys == model columns == `_UPSERT_COLUMNS`. ✓
- **Open risks flagged inline:** `/api/v1` prefix to confirm against `main.py` (T6 S1); Dockerfile `data/` copy to confirm (T4 S4); autogen down_revision to confirm `s56a1b2c3d4e` (T7 S1).
