"""College Scorecard -> ref_institutions ingestion (spec 2026-06-20).

Pure, testable helpers shared by the seed builder (``Data/tools/build_reference_seed.py``)
and the loader (``scripts/seed_reference_institutions.py``):

- ``csv_row_to_record`` maps one raw Scorecard CSV row to a domain record (no provenance).
- ``upsert_institutions`` upserts those records by ``unitid`` with seed provenance.

``ref_institutions`` joins the Spec 60 reference family (``ProvenanceMixin``), so every row is
``source="seed"`` / ``status="live"`` — the values allowed by ``KNOWLEDGE_SOURCE_CHECK`` /
``KNOWLEDGE_STATUS_CHECK``. A literal like "college_scorecard" would violate that CHECK, so the
source string is fixed here, not derived from the file.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

NULL_SENTINELS = {"NULL", "PrivacySuppressed", "NA", "PS", ""}
CONTROL_LABELS = {1: "public", 2: "private nonprofit", 3: "private for-profit"}

# Seed provenance written on every row (Spec 60 §6 Tier-1 bulk load).
SEED_PROVENANCE = {
    "source": "seed",
    "source_domain": "collegescorecard.ed.gov",
    "source_url": "https://collegescorecard.ed.gov/data/",
    "confidence": 0.9,
    "status": "live",
}

# model_field -> (csv_column, caster)
SCALAR_MAP: dict[str, tuple[str, str]] = {
    "opeid": ("OPEID", "str"),
    "opeid6": ("OPEID6", "str"),
    "name": ("INSTNM", "str"),
    "alias": ("ALIAS", "str"),
    "city": ("CITY", "str"),
    "state": ("STABBR", "str"),
    "zip": ("ZIP", "str"),
    "lat": ("LATITUDE", "float"),
    "lon": ("LONGITUDE", "float"),
    "control_code": ("CONTROL", "int"),
    "locale_code": ("LOCALE", "int"),
    "region_code": ("REGION", "int"),
    "pred_degree": ("PREDDEG", "int"),
    "high_degree": ("HIGHDEG", "int"),
    "accreditor": ("ACCREDAGENCY", "str"),
    "url": ("INSTURL", "str"),
    "price_calc_url": ("NPCURL", "str"),
    "admit_rate": ("ADM_RATE", "float"),
    "sat_avg": ("SAT_AVG", "int"),
    "act_mid": ("ACTCMMID", "int"),
    "size": ("UGDS", "int"),
    "cost_attendance": ("COSTT4_A", "int"),
    "tuition_in": ("TUITIONFEE_IN", "int"),
    "tuition_out": ("TUITIONFEE_OUT", "int"),
    "pct_pell": ("PCTPELL", "float"),
    "completion_rate": ("C150_4", "float"),
    "retention": ("RET_FT4", "float"),
    "earnings_10yr_median": ("MD_EARN_WNE_P10", "int"),
    "median_debt": ("GRAD_DEBT_MDN", "int"),
    "carnegie_basic": ("CCBASIC", "int"),
}

# Domain columns the upsert writes (everything except the UUID PK, timestamps, and the
# provenance/source_vintage envelope, which are added explicitly below).
_DOMAIN_COLUMNS = ["unitid", *SCALAR_MAP.keys(), "control", "program_pct", "extra"]
_PROVENANCE_COLUMNS = [
    "source",
    "source_domain",
    "source_url",
    "confidence",
    "status",
    "fetched_at",
    "source_vintage",
]


def clean_value(raw):
    """Strip + decode Scorecard null sentinels (NULL/PrivacySuppressed/NA/PS/'')."""
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
    """Map one Scorecard CSV row (dict of raw strings) to a domain record (no provenance)."""
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
    return rec


async def upsert_institutions(db: AsyncSession, records: list[dict], batch_size: int = 500) -> int:
    """Upsert domain records into ref_institutions by unitid, stamping seed provenance.

    Idempotent: re-running updates in place (no duplicates). Returns rows written.
    """
    from unipaith.models import RefInstitution

    now = datetime.now(UTC)
    written = 0
    for start in range(0, len(records), batch_size):
        chunk = records[start : start + batch_size]
        rows = []
        for r in chunk:
            if r.get("unitid") is None:
                continue
            # uniform keys across the batch (multi-row VALUES requires it): every
            # domain column present, missing ones None.
            row = {col: r.get(col) for col in _DOMAIN_COLUMNS}
            row.update(SEED_PROVENANCE)
            row["fetched_at"] = now
            row["source_vintage"] = r.get("source_vintage")
            rows.append(row)
        if not rows:
            continue
        update_cols = [c for c in (_DOMAIN_COLUMNS + _PROVENANCE_COLUMNS) if c != "unitid"]
        stmt = pg_insert(RefInstitution).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=["unitid"],
            set_={c: getattr(stmt.excluded, c) for c in update_cols},
        )
        await db.execute(stmt)
        written += len(rows)
    await db.commit()
    return written
