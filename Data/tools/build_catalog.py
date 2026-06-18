#!/usr/bin/env python3
"""Regenerate Data/catalog.json + Data/dictionaries/ from the local reference archive.

Idempotent. Reads the raw files under Data/sources/, the College Scorecard data.yaml,
and the FAFSA definitions .doc, then writes:

  Data/dictionaries/college-scorecard.fields.json   (raw-column -> {api_name,type,description,value_labels})
  Data/dictionaries/fafsa.fields.json               (term -> definition, extracted from the .doc)
  Data/catalog.json                                 (the machine-readable manifest / contract)

Curated metadata (titles, publishers, URLs, licenses, join keys, key fields, maps_to)
lives in CURATED below; file shapes (size/rows/columns) are computed from disk.

Usage:  python3 Data/tools/build_catalog.py            # run from repo root or Data/
        python3 Data/tools/build_catalog.py --root /path/to/Data
"""
from __future__ import annotations
import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

# --------------------------------------------------------------------------- helpers


def data_root(cli_root: str | None) -> str:
    if cli_root:
        return os.path.abspath(cli_root)
    here = os.path.dirname(os.path.abspath(__file__))  # .../Data/tools
    return os.path.dirname(here)  # .../Data


def file_size(path: str) -> int | None:
    try:
        return os.path.getsize(path)
    except OSError:
        return None


def csv_rows(path: str) -> int | None:
    """Fast data-row count (excludes header) via `wc -l`."""
    if not os.path.exists(path):
        return None
    try:
        out = subprocess.run(["wc", "-l", path], capture_output=True, text=True, check=True)
        total = int(out.stdout.strip().split()[0])
        return max(total - 1, 0)
    except Exception:
        return None


def csv_cols(path: str) -> int | None:
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            header = fh.readline()
        return header.count(",") + 1 if header else None
    except OSError:
        return None


def dir_summary(path: str) -> dict:
    """Total size + file count for a directory of raw files."""
    n, total = 0, 0
    if os.path.isdir(path):
        for name in os.listdir(path):
            fp = os.path.join(path, name)
            if os.path.isfile(fp):
                n += 1
                total += os.path.getsize(fp)
    return {"files": n, "size_bytes": total}


# ----------------------------------------------------------- College Scorecard dictionary


_LABEL_LINE = re.compile(r"^\s*(-?\d+)\s+(.+?)\s*$")


def split_value_labels(description: str) -> tuple[str, dict[str, str] | None]:
    """Pull inline 'N Label' value maps out of a Scorecard description.

    Scorecard encodes categorical value labels inside the description text, e.g.
    'Predominant degree\\n 0 Not classified\\n 1 ...'. Return (clean_description, labels|None).
    """
    if not description or "\n" not in description:
        return description, None
    lines = description.split("\n")
    head = [lines[0]]
    labels: dict[str, str] = {}
    for ln in lines[1:]:
        m = _LABEL_LINE.match(ln)
        if m:
            labels[m.group(1)] = m.group(2)
        else:
            head.append(ln)
    return ("\n".join(head).strip(), labels or None)


def build_scorecard_dict(data_yaml: str) -> dict:
    import yaml  # local import so the script degrades gracefully if pyyaml is absent

    doc = yaml.safe_load(open(data_yaml, encoding="utf-8"))
    dic = doc.get("dictionary", {})
    by_column: dict[str, dict] = {}
    derived = 0
    for api_name, meta in dic.items():
        if not isinstance(meta, dict):
            continue
        col = meta.get("source")
        desc = meta.get("description", "")
        clean, labels = split_value_labels(desc) if isinstance(desc, str) else (desc, None)
        entry = {
            "api_name": api_name,
            "type": meta.get("type"),
            "description": clean,
        }
        if labels:
            entry["value_labels"] = labels
        if col:
            by_column[col] = entry
        else:
            derived += 1
    return {
        "_meta": {
            "source": "College Scorecard data.yaml",
            "version": str(doc.get("version")),
            "keyed_by": "raw CSV column name",
            "api_entries_total": len(dic),
            "columns_with_source": len(by_column),
            "derived_or_calculated_without_column": derived,
            "note": "Value labels for categorical fields are surfaced under 'value_labels' when present.",
        },
        "fields": dict(sorted(by_column.items())),
    }


# ----------------------------------------------------------------- FAFSA dictionary


def build_fafsa_dict(doc_path: str) -> dict:
    """Extract 'Term: definition' pairs from the FAFSA definitions .doc via textutil."""
    fields: dict[str, str] = {}
    text = ""
    if os.path.exists(doc_path):
        try:
            out = subprocess.run(
                ["textutil", "-convert", "txt", "-stdout", doc_path],
                capture_output=True, text=True, check=True,
            )
            text = out.stdout
        except Exception:
            text = ""
    # Headline definitions appear as 'Term: explanation.' lines under a Definitions: header.
    for m in re.finditer(r"^([A-Z][A-Za-z /()]{2,60}):\s+(.+)$", text, flags=re.MULTILINE):
        term, body = m.group(1).strip(), m.group(2).strip()
        if term.lower() in {"general information", "definitions", "general notes"}:
            continue
        if len(body) > 25:
            fields[term] = body
    return {
        "_meta": {
            "source": "FAFSAReportDefinitions.doc",
            "keyed_by": "definition term",
            "extracted_terms": len(fields),
            "note": "Prose definitions; FAFSA tabular files are multi-sheet workbooks (see catalog).",
        },
        "fields": fields,
    }


# ----------------------------------------------- College Scorecard field-of-study dictionary

# The Scorecard data.yaml documents the institution API only — it does NOT cover the
# Field-of-Study CSV's own columns. Those follow a stable naming grammar, decoded here so
# every FoS column gets a description (more useful to an LLM than a flat upstream list).

FOS_IDENTIFIERS = {
    "UNITID": "Institution unit ID (IPEDS)",
    "OPEID6": "6-digit Office of Postsecondary Education ID",
    "INSTNM": "Institution name",
    "CONTROL": "Control of institution (Public / Private nonprofit / Private for-profit)",
    "MAIN": "Main campus flag (1 = main campus)",
    "CIPCODE": "4-digit CIP code identifying the field of study",
    "CIPDESC": "CIP field-of-study description",
    "CREDLEV": "Credential level code (1 UG cert, 2 Associate, 3 Bachelor, 4 Post-bacc cert, "
               "5 Master, 6 Doctoral, 7 First-professional, 8 Grad/prof cert)",
    "CREDDESC": "Credential level description",
    "IPEDSCOUNT1": "Number of awards (IPEDS completions, primary count)",
    "IPEDSCOUNT2": "Number of awards (IPEDS completions, secondary count)",
    "DISTANCE": "Program offered via distance education",
}

FOS_POP = {
    "ALL": "all students", "MALE": "men", "NOTMALE": "women / not-men",
    "NOMALE": "women / not-men", "PELL": "Pell recipients", "NOPELL": "non-Pell students",
}
FOS_LOAN = {"STGP": "Stafford + Grad PLUS loans", "PP": "Parent PLUS loans"}
FOS_FILTER = {"ANY": "any borrowers", "EVAL": "evaluated cohort"}
FOS_STAT = {"N": "count", "MEAN": "mean", "MDN": "median",
            "MDN10YRPAY": "median monthly payment on a 10-year plan"}
FOS_EARN_WORK = {
    "WNE": "working and not enrolled", "NWNE": "not working and not enrolled",
    "NE": "not enrolled",
}
FOS_BBRR_STATUS = {
    "N": "cohort size", "DFLT": "in default", "DLNQ": "delinquent", "FBR": "in forbearance",
    "DFR": "in deferment", "NOPROG": "not making progress", "MAKEPROG": "making progress",
    "PAIDINFULL": "paid in full", "DISCHARGE": "discharged",
}


def _years(tok: str) -> str | None:
    m = re.match(r"(\d+)YR", tok)
    return f"{m.group(1)} year(s) after completion" if m else None


def decode_fos_column(col: str) -> str:
    if col in FOS_IDENTIFIERS:
        return FOS_IDENTIFIERS[col]
    parts = col.split("_")
    # DEBT_<pop>_<loan>_<filter>_<stat...>
    if parts[0] == "DEBT" and len(parts) >= 5:
        pop = FOS_POP.get(parts[1], parts[1].lower())
        loan = FOS_LOAN.get(parts[2], parts[2])
        filt = FOS_FILTER.get(parts[3], parts[3].lower())
        stat = FOS_STAT.get("_".join(parts[4:]), "_".join(parts[4:]).lower())
        return f"Debt — {stat} of {loan} for {pop} ({filt})"
    # BBRR<n>_FED_COMP_<status>  (borrower-based repayment rate)
    if parts[0].startswith("BBRR"):
        n = parts[0][4:]
        status = FOS_BBRR_STATUS.get(parts[-1], parts[-1].lower())
        return f"Repayment (federal loans, completers) {n} year(s) out — {status}"
    # EARN_*
    if parts[0] == "EARN":
        yr = next((_years(p) for p in parts if _years(p)), None)
        pop = next((FOS_POP[p] for p in parts if p in FOS_POP), None)
        work = next((FOS_EARN_WORK[p] for p in parts if p in FOS_EARN_WORK), None)
        bits = []
        if "COUNT" in parts or "CNTOVER150" in parts:
            bits.append("count of")
        if "MDN" in parts:
            bits.append("median earnings of")
        if "P25" in parts:
            bits.append("25th-percentile earnings of")
        if "P75" in parts:
            bits.append("75th-percentile earnings of")
        if "GT" in parts and "THRESHOLD" in parts:
            bits.append("count earning above the earnings threshold for")
        lead = " ".join(bits) or "earnings metric for"
        who = pop or "students"
        tail = []
        if work:
            tail.append(work)
        if "HI" in parts:
            tail.append("highest-credential graduates")
        if "IN" in parts and "STATE" in parts:
            tail.append("in-state")
        if "NAT" in parts:
            tail.append("national benchmark")
        suffix = (", " + ", ".join(tail)) if tail else ""
        ystr = f" — {yr}" if yr else ""
        return f"Earnings — {lead} {who}{suffix}{ystr}".strip()
    return "Field-of-study metric (see Scorecard data documentation)"


def build_fos_dict(fos_csv: str) -> dict:
    fields: dict[str, dict] = {}
    if os.path.exists(fos_csv):
        with open(fos_csv, encoding="utf-8", errors="replace") as fh:
            cols = fh.readline().strip().split(",")
        for c in cols:
            c = c.strip()
            if c:
                fields[c] = {"description": decode_fos_column(c)}
    return {
        "_meta": {
            "source": "Decoded from the Field-of-Study CSV naming grammar (data.yaml omits these columns)",
            "keyed_by": "raw CSV column name",
            "columns": len(fields),
            "grammar": {
                "DEBT_<pop>_<loan>_<filter>_<stat>": {
                    "pop": FOS_POP, "loan": FOS_LOAN, "filter": FOS_FILTER, "stat": FOS_STAT,
                },
                "EARN_*": {"work": FOS_EARN_WORK, "pop": FOS_POP,
                           "tokens": "MDN=median, P25/P75=percentiles, HI=highest credential, "
                                     "NAT=national, IN_STATE=in-state, <n>YR=years after completion"},
                "BBRR<n>_FED_COMP_<status>": FOS_BBRR_STATUS,
            },
        },
        "fields": fields,
    }


# --------------------------------------------------------------------------- catalog


# Curated metadata. Shapes (size/rows/columns) are filled from disk at build time.
# license note: U.S. federal data — works of the U.S. Government are not subject to
# domestic copyright (17 U.S.C. 105); treated as public domain for reuse.
US_GOV_PD = "U.S. Government work — public domain (17 U.S.C. 105)"

CURATED = [
    {
        "id": "college-scorecard-institution-latest",
        "title": "College Scorecard — Most Recent Cohorts, Institution",
        "publisher": "U.S. Department of Education",
        "source_url": "https://collegescorecard.ed.gov/data/",
        "download_url": "https://collegescorecard.ed.gov/data/  (bulk: College_Scorecard_Raw_Data_*.zip)",
        "api_url": "https://api.data.gov/ed/collegescorecard/v1/schools",
        "license": US_GOV_PD,
        "grain": "institution",
        "entity": "institution",
        "join_keys": ["UNITID", "OPEID", "OPEID6"],
        "coverage": {"latest_cohort": "most-recent", "panel_years": "1996-2025"},
        "path": "sources/college-scorecard/institution/Most-Recent-Cohorts-Institution.csv",
        "format": "csv",
        "dictionary": "dictionaries/college-scorecard.fields.json",
        "key_fields": [
            "INSTNM", "CITY", "STABBR", "ZIP", "INSTURL", "CONTROL", "PREDDEG", "HIGHDEG",
            "CCBASIC", "ADM_RATE", "SAT_AVG", "ACTCMMID", "UGDS", "COSTT4_A",
            "TUITIONFEE_IN", "TUITIONFEE_OUT", "AVGFACSAL", "PCTPELL", "C150_4",
            "RET_FT4", "MD_EARN_WNE_P10", "GRAD_DEBT_MDN", "FTFTPCTPELL",
        ],
        "maps_to": {
            "unipaith_entity": "institution",
            "sections": ["report-card key stats", "admissions funnel", "outcomes/cost", "quick facts"],
        },
    },
    {
        "id": "college-scorecard-field-of-study-latest",
        "title": "College Scorecard — Most Recent Cohorts, Field of Study",
        "publisher": "U.S. Department of Education",
        "source_url": "https://collegescorecard.ed.gov/data/",
        "download_url": "https://collegescorecard.ed.gov/data/  (bulk: College_Scorecard_Raw_Data_*.zip)",
        "api_url": "https://api.data.gov/ed/collegescorecard/v1/fos",
        "license": US_GOV_PD,
        "grain": "program",
        "entity": "program",
        "join_keys": ["UNITID", "CIPCODE", "CREDLEV"],
        "coverage": {"latest_cohort": "most-recent", "panel_years": "2015-2023"},
        "path": "sources/college-scorecard/field-of-study/Most-Recent-Cohorts-Field-of-Study.csv",
        "format": "csv",
        "dictionary": "dictionaries/college-scorecard-field-of-study.fields.json",
        "key_fields": [
            "UNITID", "INSTNM", "CIPCODE", "CIPDESC", "CREDLEV", "CREDDESC",
            "IPEDSCOUNT1", "IPEDSCOUNT2", "DEBT_ALL_STGP_EVAL_MDN",
            "EARN_MDN_HI_1YR", "EARN_MDN_HI_2YR", "EARN_COUNT_WNE_HI_1YR",
        ],
        "maps_to": {
            "unipaith_entity": "program",
            "sections": ["program outcomes: earnings/debt/completion by CIP + credential level"],
        },
    },
    {
        "id": "college-scorecard-panels",
        "title": "College Scorecard — Yearly Panels (institution + field-of-study)",
        "publisher": "U.S. Department of Education",
        "source_url": "https://collegescorecard.ed.gov/data/",
        "download_url": "https://collegescorecard.ed.gov/data/  (bulk archive)",
        "license": US_GOV_PD,
        "grain": "institution+program time series",
        "entity": "institution",
        "join_keys": ["UNITID", "OPEID6", "CIPCODE", "CREDLEV"],
        "coverage": {"panel_years": "1996-2025"},
        "path": "sources/college-scorecard/panels/",
        "format": "csv (directory)",
        "dictionary": "dictionaries/college-scorecard.fields.json",
        "key_fields": [],
        "maps_to": {"unipaith_entity": "institution", "sections": ["historical trends (future)"]},
    },
    {
        "id": "college-scorecard-crosswalks",
        "title": "College Scorecard — CIP/UNITID/OPEID Crosswalks",
        "publisher": "U.S. Department of Education",
        "source_url": "https://collegescorecard.ed.gov/data/",
        "download_url": "https://collegescorecard.ed.gov/data/  (bulk archive)",
        "license": US_GOV_PD,
        "grain": "crosswalk",
        "entity": "institution",
        "join_keys": ["UNITID", "OPEID", "CIPCODE"],
        "coverage": {"panel_years": "2000-2023"},
        "path": "sources/college-scorecard/crosswalks/",
        "format": "xlsx (directory)",
        "dictionary": None,
        "key_fields": [],
        "maps_to": {"unipaith_entity": "institution", "sections": ["id reconciliation across sources"]},
    },
    {
        "id": "fafsa-application-demographics",
        "title": "FAFSA — Application Data by Demographic Characteristics (2023-24)",
        "publisher": "U.S. Department of Education — Federal Student Aid",
        "source_url": "https://studentaid.gov/data-center/student/application-volume/fafsa-school-state",
        "download_url": "https://studentaid.gov/data-center/student/application-volume",
        "license": US_GOV_PD,
        "grain": "national demographic",
        "entity": "aid",
        "join_keys": [],
        "coverage": {"latest_cohort": "2023-2024"},
        "path": "sources/fafsa/2023-2024-application-demographics.xls",
        "format": "xls",
        "dictionary": "dictionaries/fafsa.fields.json",
        "key_fields": ["Gender", "Age", "Grade Level", "Dependency Status", "Pell Eligibility"],
        "maps_to": {"unipaith_entity": "aid", "sections": ["financial-need context"]},
    },
    {
        "id": "fafsa-apps-by-state",
        "title": "FAFSA — Application Data by State (2026-27, quarterly)",
        "publisher": "U.S. Department of Education — Federal Student Aid",
        "source_url": "https://studentaid.gov/data-center/student/application-volume/fafsa-school-state",
        "download_url": "https://studentaid.gov/data-center/student/application-volume",
        "license": US_GOV_PD,
        "grain": "state",
        "entity": "aid",
        "join_keys": ["STATE"],
        "coverage": {"latest_cohort": "2026-2027"},
        "path": "sources/fafsa/2026-2027-app-data-by-state-q1.xlsx",
        "format": "xlsx",
        "dictionary": "dictionaries/fafsa.fields.json",
        "key_fields": ["State", "Applications Submitted", "Applications Completed"],
        "maps_to": {"unipaith_entity": "aid", "sections": ["application-volume context by state"]},
    },
    {
        "id": "fafsa-federal-school-codes",
        "title": "FAFSA — Federal School Code List (2026-27, Q3)",
        "publisher": "U.S. Department of Education — Federal Student Aid",
        "source_url": "https://fsapartners.ed.gov/knowledge-center/library/federal-school-code-lists",
        "download_url": "https://fsapartners.ed.gov/knowledge-center/library/federal-school-code-lists",
        "license": US_GOV_PD,
        "grain": "institution",
        "entity": "institution",
        "join_keys": ["FederalSchoolCode", "OPEID"],
        "coverage": {"latest_cohort": "2026-2027"},
        "path": "sources/fafsa/2627FederalSchoolCodeList3rdQuarter.xlsx",
        "format": "xlsx",
        "dictionary": "dictionaries/fafsa.fields.json",
        "key_fields": ["FederalSchoolCode", "SchoolName", "State"],
        "maps_to": {"unipaith_entity": "institution", "sections": ["aid-eligible school reference / id crosswalk"]},
    },
    {
        "id": "fafsa-portfolio-summary",
        "title": "Federal Student Aid — Portfolio Summary",
        "publisher": "U.S. Department of Education — Federal Student Aid",
        "source_url": "https://studentaid.gov/data-center/student/portfolio",
        "download_url": "https://studentaid.gov/data-center/student/portfolio",
        "license": US_GOV_PD,
        "grain": "national",
        "entity": "aid",
        "join_keys": [],
        "coverage": {},
        "path": "sources/fafsa/PortfolioSummary.xls",
        "format": "xls",
        "dictionary": "dictionaries/fafsa.fields.json",
        "key_fields": ["Outstanding Balance", "Recipients"],
        "maps_to": {"unipaith_entity": "aid", "sections": ["national debt context"]},
    },
    {
        "id": "fafsa-portfolio-by-loan-type",
        "title": "Federal Student Aid — Portfolio by Loan Type",
        "publisher": "U.S. Department of Education — Federal Student Aid",
        "source_url": "https://studentaid.gov/data-center/student/portfolio",
        "download_url": "https://studentaid.gov/data-center/student/portfolio",
        "license": US_GOV_PD,
        "grain": "national",
        "entity": "aid",
        "join_keys": [],
        "coverage": {},
        "path": "sources/fafsa/PortfoliobyLoanType.xls",
        "format": "xls",
        "dictionary": "dictionaries/fafsa.fields.json",
        "key_fields": ["Loan Type", "Outstanding Balance"],
        "maps_to": {"unipaith_entity": "aid", "sections": ["national debt context"]},
    },
]


def fill_shapes(root: str, entry: dict) -> dict:
    e = dict(entry)
    rel = e.get("path")
    if not rel:
        e["status"] = "available"
        e["size_bytes"] = None
        return e
    abspath = os.path.join(root, rel)
    if rel.endswith("/") or os.path.isdir(abspath):
        summ = dir_summary(abspath)
        e["size_bytes"] = summ["size_bytes"]
        e["files"] = summ["files"]
        e["status"] = "downloaded" if summ["files"] else "available"
    elif os.path.isfile(abspath):
        e["size_bytes"] = file_size(abspath)
        if e.get("format") == "csv":
            e["rows"] = csv_rows(abspath)
            e["columns"] = csv_cols(abspath)
        e["status"] = "downloaded"
    else:
        e["size_bytes"] = None
        e["status"] = "available"
    e["committed"] = False  # heavy raw is never committed
    return e


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=None, help="path to the Data/ folder")
    args = ap.parse_args()
    root = data_root(args.root)

    os.makedirs(os.path.join(root, "dictionaries"), exist_ok=True)

    # 1) dictionaries
    sc_yaml = os.path.join(root, "sources/college-scorecard/data.yaml")
    if os.path.exists(sc_yaml):
        sc_dict = build_scorecard_dict(sc_yaml)
        with open(os.path.join(root, "dictionaries/college-scorecard.fields.json"), "w") as fh:
            json.dump(sc_dict, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        print(f"college-scorecard.fields.json: {len(sc_dict['fields'])} columns")
    else:
        print("WARN: scorecard data.yaml not found; skipping its dictionary", file=sys.stderr)

    fos_csv = os.path.join(
        root, "sources/college-scorecard/field-of-study/Most-Recent-Cohorts-Field-of-Study.csv"
    )
    fos_dict = build_fos_dict(fos_csv)
    with open(os.path.join(root, "dictionaries/college-scorecard-field-of-study.fields.json"), "w") as fh:
        json.dump(fos_dict, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    print(f"college-scorecard-field-of-study.fields.json: {len(fos_dict['fields'])} columns")

    fafsa_doc = os.path.join(root, "sources/fafsa/FAFSAReportDefinitions.doc")
    fafsa_dict = build_fafsa_dict(fafsa_doc)
    with open(os.path.join(root, "dictionaries/fafsa.fields.json"), "w") as fh:
        json.dump(fafsa_dict, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    print(f"fafsa.fields.json: {len(fafsa_dict['fields'])} terms")

    # 2) catalog
    datasets = [fill_shapes(root, e) for e in CURATED]
    catalog = {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_root": "Data/sources/",
        "note": (
            "Machine-readable catalog of local reference data. Raw files are git-ignored; "
            "this catalog + dictionaries are committed. status=downloaded means the file is "
            "present in the local archive; status=available means catalog-only (fetch via download_url)."
        ),
        "datasets": datasets,
    }
    with open(os.path.join(root, "catalog.json"), "w") as fh:
        json.dump(catalog, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    dl = sum(1 for d in datasets if d.get("status") == "downloaded")
    print(f"catalog.json: {len(datasets)} datasets ({dl} downloaded)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
