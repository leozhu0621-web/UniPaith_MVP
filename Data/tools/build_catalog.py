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


# Datasets discovered + adversarially verified by the sourcing workflow (2026-06-18).
# Every download_url was independently fetched and confirmed to resolve from the genuine
# publisher. license_open=False marks sources whose terms restrict redistribution — kept as
# catalog references (look-up the URL), not stored/served. maps_to uses product sections only
# (no backend model names are asserted; ingestion is a deferred spec).
def CC_BY(v):  # noqa: N802 - tiny label helper
    return f"Creative Commons Attribution 4.0 (CC BY 4.0){v}"


SOURCED = [
    # ---- career outcomes: BLS + O*NET + CIP/SOC crosswalk -------------------------------
    {
        "id": "bls-oews-wages-employment",
        "title": "BLS Occupational Employment and Wage Statistics (OEWS), May 2024",
        "publisher": "U.S. Bureau of Labor Statistics (DOL)",
        "category": "career-outcomes",
        "source_url": "https://www.bls.gov/oes/tables.htm",
        "download_url": "https://www.bls.gov/oes/special.requests/oesm24nat.zip  (national; all-areas: oesm24all.zip)",
        "license": US_GOV_PD, "license_open": True,
        "grain": "occupation (SOC) x geography", "entity": "occupation",
        "join_keys": ["soc_code", "area_fips", "naics"],
        "coverage": {"latest": "May 2024", "panel_years": "1997-2024"},
        "dictionary": "https://www.bls.gov/oes/current/oes_tec.htm",
        "format": "zip of xlsx", "est_size": "national ~5-10 MB; all-areas ~76 MB",
        "maps_to": {"unipaith_entity": "program/occupation",
                    "sections": ["program outcomes: typical wages by field", "career-alignment earnings"]},
    },
    {
        "id": "bls-employment-projections",
        "title": "BLS Employment Projections — Occupational Matrix 2024-2034",
        "publisher": "U.S. Bureau of Labor Statistics (DOL)",
        "category": "career-outcomes",
        "source_url": "https://www.bls.gov/emp/data/occupational-data.htm",
        "download_url": "https://www.bls.gov/emp/ind-occ-matrix/occupation.xlsx",
        "license": US_GOV_PD, "license_open": True,
        "grain": "occupation (SOC)", "entity": "occupation",
        "join_keys": ["soc_code"],
        "coverage": {"latest": "2024-2034 projection"},
        "dictionary": "https://www.bls.gov/emp/documentation/",
        "format": "xlsx",
        "path": "sources/bls-onet/EmploymentProjections_occupation_2024-34.xlsx",
        "maps_to": {"unipaith_entity": "program/occupation",
                    "sections": ["career-alignment job outlook (projected growth, openings, typical entry education)"]},
    },
    {
        "id": "onet-database",
        "title": "O*NET Database 30.3 — occupations, skills, knowledge, abilities, tasks",
        "publisher": "O*NET Resource Center (DOL/ETA)",
        "category": "career-outcomes",
        "source_url": "https://www.onetcenter.org/database.html",
        "download_url": "https://www.onetcenter.org/dl_files/database/db_30_3_text.zip",
        "license": CC_BY(""), "license_open": True,
        "grain": "occupation (O*NET-SOC), relational (~45 files)", "entity": "occupation",
        "join_keys": ["onet_soc_code", "soc_code"],
        "coverage": {"latest": "v30.3"},
        "dictionary": "https://www.onetcenter.org/dictionary/30.3/text/",
        "format": "zip of tab-delimited text",
        "path": "sources/bls-onet/onet_db_30_3_text.zip",
        "maps_to": {"unipaith_entity": "program/occupation",
                    "sections": ["career-alignment 'skills you build'", "major -> occupation profiles"]},
    },
    {
        "id": "onet-web-services-api",
        "title": "O*NET Web Services API (v2.0)",
        "publisher": "O*NET Resource Center (DOL/ETA)",
        "category": "career-outcomes",
        "source_url": "https://services.onetcenter.org/",
        "download_url": "https://services.onetcenter.org/  (free API key; REST JSON/XML)",
        "license": CC_BY(" for returned data"), "license_open": True,
        "grain": "occupation (O*NET-SOC)", "entity": "occupation",
        "join_keys": ["onet_soc_code"],
        "coverage": {"latest": "live"},
        "dictionary": "https://services.onetcenter.org/reference/",
        "format": "REST API", "est_size": "API",
        "maps_to": {"unipaith_entity": "occupation", "sections": ["live career-alignment enrichment"]},
    },
    {
        "id": "bls-occupational-outlook-handbook",
        "title": "BLS Occupational Outlook Handbook (OOH) — narrative career profiles",
        "publisher": "U.S. Bureau of Labor Statistics (DOL)",
        "category": "career-outcomes",
        "source_url": "https://www.bls.gov/ooh/",
        "download_url": "https://www.bls.gov/ooh/  (bulk XML feed via OOH developer info)",
        "license": US_GOV_PD, "license_open": True,
        "grain": "occupation", "entity": "occupation",
        "join_keys": ["soc_code"],
        "coverage": {"latest": "current"},
        "dictionary": "https://www.bls.gov/ooh/about/ooh-developer-info.htm",
        "format": "XML/JSON feed", "est_size": "~10-30 MB",
        "maps_to": {"unipaith_entity": "occupation",
                    "sections": ["career-alignment 'how to enter / day-to-day' editorial"]},
    },
    {
        "id": "nces-cip2020-soc2018-crosswalk",
        "title": "NCES CIP 2020 -> SOC 2018 Crosswalk",
        "publisher": "U.S. Dept of Education — NCES",
        "category": "career-outcomes",
        "source_url": "https://nces.ed.gov/ipeds/cipcode/resources.aspx",
        "download_url": "https://nces.ed.gov/ipeds/cipcode/Files/CIP2020_SOC2018_Crosswalk.xlsx",
        "license": US_GOV_PD, "license_open": True,
        "grain": "CIP <-> SOC pair", "entity": "crosswalk",
        "join_keys": ["cip_code", "soc_code"],
        "coverage": {"latest": "2020/2018"},
        "dictionary": "https://nces.ed.gov/ipeds/cipcode/",
        "format": "xlsx",
        "path": "sources/ipeds/CIP2020_SOC2018_Crosswalk.xlsx",
        "maps_to": {"unipaith_entity": "crosswalk",
                    "sections": ["the join glue: 'careers this major leads to' (CIP -> SOC -> wages/outlook)"]},
    },
    {
        "id": "nces-cip2020-dictionary",
        "title": "NCES Classification of Instructional Programs (CIP) 2020 — codes, titles, definitions",
        "publisher": "U.S. Dept of Education — NCES",
        "category": "career-outcomes",
        "source_url": "https://nces.ed.gov/ipeds/cipcode/",
        "download_url": "https://nces.ed.gov/ipeds/cipcode/Files/CIPCode2020.csv",
        "license": US_GOV_PD, "license_open": True,
        "grain": "CIP code", "entity": "major",
        "join_keys": ["cip_code"],
        "coverage": {"latest": "2020"},
        "dictionary": "https://nces.ed.gov/ipeds/cipcode/",
        "format": "csv",
        "path": "sources/ipeds/CIPCode2020.csv",
        "maps_to": {"unipaith_entity": "major",
                    "sections": ["canonical major taxonomy + human-readable field names/definitions"]},
    },
    # ---- IPEDS depth -------------------------------------------------------------------
    {
        "id": "ipeds-complete-data-files",
        "title": "IPEDS Complete Data Files (Directory, Admissions, Enrollment, Completions, Finance, HR)",
        "publisher": "U.S. Dept of Education — NCES",
        "category": "ipeds",
        "source_url": "https://nces.ed.gov/ipeds/use-the-data/download-access-database",
        "download_url": "https://nces.ed.gov/ipeds/datacenter/  (per-survey CSV zips; full-year Access DB: "
                        "tablefiles/zipfiles/IPEDS_YYYY-YY_Final.zip)",
        "license": US_GOV_PD, "license_open": True,
        "grain": "institution (per-survey)", "entity": "institution",
        "join_keys": ["UNITID"],
        "coverage": {"panel_years": "1980-2024"},
        "dictionary": "embedded varlist/Frequencies tables per survey file",
        "format": "zipped CSV / MS Access", "est_size": "per-survey ~1-30 MB; full year ~150-400 MB",
        "maps_to": {"unipaith_entity": "institution",
                    "sections": ["admissions funnel (applied/admitted/enrolled, test bands)",
                                 "report-card stats (selectivity, retention)", "quick facts (enrollment, faculty, finance)"]},
    },
    {
        "id": "urban-education-data-portal-ipeds",
        "title": "Urban Institute Education Data Portal — IPEDS (clean REST API)",
        "publisher": "Urban Institute",
        "category": "ipeds",
        "source_url": "https://educationdata.urban.org/documentation/colleges.html",
        "download_url": "https://educationdata.urban.org/api/v1/college-university/ipeds/  (paginated JSON; CSV export)",
        "license": "Open / free for non-commercial + commercial use with attribution (Urban Institute terms)",
        "license_open": True,
        "grain": "institution / program (harmonized IPEDS)", "entity": "institution",
        "join_keys": ["unitid"],
        "coverage": {"panel_years": "1980-2022"},
        "dictionary": "https://educationdata.urban.org/documentation/colleges.html",
        "format": "REST API + CSV", "est_size": "API (per-slice KB-MB)",
        "maps_to": {"unipaith_entity": "institution",
                    "sections": ["developer-friendly IPEDS ingestion path for admissions/enrollment/completions"]},
    },
    # ---- rankings / classification -----------------------------------------------------
    {
        "id": "carnegie-classification-2025",
        "title": "Carnegie Classifications 2025 — Institutional Classification + Student Access & Earnings",
        "publisher": "American Council on Education (ACE) + Carnegie Foundation",
        "category": "rankings",
        "source_url": "https://carnegieclassifications.acenet.edu/",
        "download_url": "https://carnegieclassifications.acenet.edu/wp-content/uploads/2025/04/2025-Public-Data-File.xlsx",
        "license": "Free public data file; attribution requested (verify reuse terms before redistribution)",
        "license_open": True,
        "grain": "institution", "entity": "institution",
        "join_keys": ["UNITID"],
        "coverage": {"latest": "2025"},
        "dictionary": "https://carnegieclassifications.acenet.edu/",
        "format": "xlsx",
        "path": "sources/rankings/Carnegie2025_Public_Data_File.xlsx",
        "maps_to": {"unipaith_entity": "institution",
                    "sections": ["distinction (Carnegie type, e.g. 'R1: very high research')", "quick facts"]},
    },
    {
        "id": "carnegie-2025-research-activity-designation",
        "title": "Carnegie 2025 Research Activity Designation (RAD)",
        "publisher": "American Council on Education (ACE) + Carnegie Foundation",
        "category": "rankings",
        "source_url": "https://carnegieclassifications.acenet.edu/",
        "download_url": "https://carnegieclassifications.acenet.edu/wp-content/uploads/2025/02/2025-RAD-Public-Data-File.xlsx",
        "license": "Public data file; redistribution terms unclear — treat as reference (verify before storing)",
        "license_open": False,
        "grain": "institution", "entity": "institution",
        "join_keys": ["UNITID"],
        "coverage": {"latest": "2025"},
        "dictionary": "https://carnegieclassifications.acenet.edu/",
        "format": "xlsx", "est_size": "~1-2 MB",
        "maps_to": {"unipaith_entity": "institution", "sections": ["distinction (research-intensity badge)"]},
    },
    {
        "id": "cwur-world-university-rankings",
        "title": "CWUR — Center for World University Rankings (Global 2000)",
        "publisher": "Center for World University Rankings",
        "category": "rankings",
        "source_url": "https://cwur.org/",
        "download_url": "https://cwur.org/2025.php  (HTML table; no official file/API)",
        "license": "Proprietary — display permitted, redistribution NOT permitted without license",
        "license_open": False,
        "grain": "institution (world/national rank)", "entity": "institution",
        "join_keys": ["institution_name"],
        "coverage": {"latest": "2025"},
        "dictionary": None,
        "format": "HTML table", "est_size": "~2000 rows",
        "maps_to": {"unipaith_entity": "institution",
                    "sections": ["rankings section — ONLY under a negotiated license"]},
    },
    # ---- scholarships / aid ------------------------------------------------------------
    {
        "id": "grants-gov-opportunities-api",
        "title": "Grants.gov Opportunities (Search2 + fetchOpportunity REST API)",
        "publisher": "U.S. Grants.gov (HHS)",
        "category": "scholarships",
        "source_url": "https://www.grants.gov/web/grants/s2s/grantor/web-services.html",
        "download_url": "https://api.grants.gov/v1/api/search2  (REST POST; paginated JSON)",
        "license": US_GOV_PD, "license_open": True,
        "grain": "grant opportunity", "entity": "grant",
        "join_keys": ["opportunity_id", "cfda_number"],
        "coverage": {"latest": "live"},
        "dictionary": "https://www.grants.gov/system-to-system/grantor-system-to-system/web-services",
        "format": "REST API", "est_size": "API",
        "maps_to": {"unipaith_entity": "aid", "sections": ["funding catalog (eligibility/award fields)"]},
    },
    {
        "id": "usaspending-assistance-awards",
        "title": "USAspending.gov Federal Financial Assistance Awards",
        "publisher": "U.S. Treasury (USAspending.gov)",
        "category": "scholarships",
        "source_url": "https://www.usaspending.gov/",
        "download_url": "https://api.usaspending.gov/api/v2/search/spending_by_award/  (REST; bulk CSV archive available)",
        "license": US_GOV_PD, "license_open": True,
        "grain": "award (CFDA x recipient)", "entity": "grant",
        "join_keys": ["cfda_number", "recipient_uei"],
        "coverage": {"panel_years": "2008-present"},
        "dictionary": "https://api.usaspending.gov/docs/endpoints",
        "format": "REST API + CSV", "est_size": "filtered by CFDA family = tractable; full = multi-GB",
        "maps_to": {"unipaith_entity": "aid", "sections": ["who-funds-what evidence by institution"]},
    },
    {
        "id": "fsa-title-iv-program-volume",
        "title": "Title IV Program Volume by School (Pell, TEACH, Direct Loan)",
        "publisher": "U.S. Dept of Education — Federal Student Aid",
        "category": "scholarships",
        "source_url": "https://studentaid.gov/data-center/student/title-iv",
        "download_url": "https://studentaid.gov/data-center/student/title-iv  (quarterly XLS/XLSX)",
        "license": US_GOV_PD, "license_open": True,
        "grain": "institution", "entity": "institution",
        "join_keys": ["OPEID"],
        "coverage": {"latest": "quarterly"},
        "dictionary": None,
        "format": "xls/xlsx", "est_size": "few MB per quarter",
        "maps_to": {"unipaith_entity": "institution",
                    "sections": ["affordability/aid context (Pell volume) — joins on OPEID"]},
    },
    {
        "id": "nassgap-state-aid-survey",
        "title": "NASSGAP Annual Survey of State-Sponsored Student Financial Aid",
        "publisher": "NASSGAP",
        "category": "scholarships",
        "source_url": "https://www.nassgapsurvey.com/",
        "download_url": "https://www.nassgapsurvey.com/survey_reports/  (XLSX history tables + annual PDF)",
        "license": "Public survey reports; attribution requested",
        "license_open": True,
        "grain": "state x program", "entity": "aid",
        "join_keys": ["state"],
        "coverage": {"latest": "2023-2024 (55th)"},
        "dictionary": None,
        "format": "xlsx + pdf", "est_size": "<5 MB",
        "maps_to": {"unipaith_entity": "aid", "sections": ["per-state need/merit grant context"]},
    },
    {
        "id": "sam-gov-assistance-listings-cfda",
        "title": "SAM.gov Assistance Listings (formerly CFDA) — federal program catalog",
        "publisher": "U.S. GSA (SAM.gov)",
        "category": "scholarships",
        "source_url": "https://sam.gov/content/assistance-listings",
        "download_url": "https://s3.amazonaws.com/falextracts/Assistance%20Listings/datagov/"
                        "AssistanceListings_DataGov_PUBLIC_CURRENT.csv",
        "license": US_GOV_PD, "license_open": True,
        "grain": "federal assistance program (CFDA)", "entity": "grant",
        "join_keys": ["cfda_number"],
        "coverage": {"latest": "current (~2,300 programs)"},
        "dictionary": "https://sam.gov/content/assistance-listings",
        "format": "csv",
        "path": "sources/scholarships/SAM_AssistanceListings_CFDA.csv",
        "maps_to": {"unipaith_entity": "aid",
                    "sections": ["the CFDA join dictionary: human-readable program objectives/eligibility"]},
    },
    # ---- international -----------------------------------------------------------------
    {
        "id": "ice-sevis-data-mapping-tool",
        "title": "SEVIS by the Numbers — Data Mapping Tool (international student counts)",
        "publisher": "U.S. ICE / DHS (Study in the States)",
        "category": "international",
        "source_url": "https://studyinthestates.dhs.gov/sevis-data-mapping-tool",
        "download_url": "https://studyinthestates.dhs.gov/sevis-data-mapping-tool  (CSV/Excel export per view)",
        "license": US_GOV_PD, "license_open": True,
        "grain": "country x state / field aggregate", "entity": "international_flow",
        "join_keys": ["origin_country", "state"],
        "coverage": {"latest": "2025"},
        "dictionary": None,
        "format": "csv/xlsx + pdf", "est_size": "KB-low MB (aggregates)",
        "maps_to": {"unipaith_entity": "institution",
                    "sections": ["international/diversity context"]},
    },
    {
        "id": "iie-open-doors",
        "title": "IIE Open Doors — international educational exchange",
        "publisher": "Institute of International Education (IIE)",
        "category": "international",
        "source_url": "https://opendoorsdata.org/",
        "download_url": "https://opendoorsdata.org/data/  (XLSX per table)",
        "license": "Proprietary — display/citation permitted; redistribution restricted (verify)",
        "license_open": False,
        "grain": "country / field aggregate", "entity": "international_flow",
        "join_keys": ["origin_country", "field_of_study"],
        "coverage": {"panel_years": "~25 years"},
        "dictionary": None,
        "format": "xlsx", "est_size": "KB-low MB",
        "maps_to": {"unipaith_entity": "program",
                    "sections": ["international students by field — reference under license"]},
    },
    {
        "id": "unesco-uis-education",
        "title": "UNESCO Institute for Statistics (UIS) — Education Bulk Data (SDG4 + OPRI)",
        "publisher": "UNESCO Institute for Statistics",
        "category": "international",
        "source_url": "https://uis.unesco.org/bdds",
        "download_url": "https://download.uis.unesco.org/bdds/  (SDG.zip etc.; also REST + SDMX API)",
        "license": "CC BY-SA 3.0 IGO", "license_open": True,
        "grain": "country x year x indicator", "entity": "country",
        "join_keys": ["iso3_country", "year"],
        "coverage": {"panel_years": "1970-present"},
        "dictionary": "https://uis.unesco.org/",
        "format": "csv bulk + API", "est_size": "tens-hundreds MB bulk",
        "maps_to": {"unipaith_entity": "country",
                    "sections": ["home-country education context for international students"]},
    },
    {
        "id": "worldbank-edstats",
        "title": "World Bank Education Statistics (EdStats) — Data360",
        "publisher": "World Bank",
        "category": "international",
        "source_url": "https://datatopics.worldbank.org/education/",
        "download_url": "https://data360api.worldbank.org/data360/data?DATABASE_ID=WB_EDSTATS  "
                        "(also api.worldbank.org/v2 source 12)",
        "license": CC_BY(""), "license_open": True,
        "grain": "country x year x indicator", "entity": "country",
        "join_keys": ["iso3_country", "year"],
        "coverage": {"panel_years": "1970-present"},
        "dictionary": "https://datacatalog.worldbank.org/search/dataset/0038480",
        "format": "REST API + CSV", "est_size": "indicator CSV tens of MB",
        "maps_to": {"unipaith_entity": "country",
                    "sections": ["home-country education context (preferred open source)"]},
    },
    {
        "id": "world-universities-and-domains",
        "title": "World Universities and Domains List (Hipolabs)",
        "publisher": "Hipolabs (open-source community)",
        "category": "international",
        "source_url": "https://github.com/Hipo/university-domains-list",
        "download_url": "https://raw.githubusercontent.com/Hipo/university-domains-list/master/"
                        "world_universities_and_domains.json",
        "license": "MIT (open)", "license_open": True,
        "grain": "institution (global)", "entity": "institution",
        "join_keys": ["domain", "name", "alpha_two_code"],
        "coverage": {"latest": "rolling (~10k institutions, 200+ countries)"},
        "dictionary": "https://github.com/Hipo/university-domains-list",
        "format": "json",
        "path": "sources/international/world_universities_and_domains.json",
        "maps_to": {"unipaith_entity": "institution",
                    "sections": ["global institution registry; detect prior school/country from email domain"]},
    },
    {
        "id": "wikidata-universities",
        "title": "Wikidata — Global University Registry (SPARQL, IPEDS-keyed)",
        "publisher": "Wikimedia Foundation (Wikidata)",
        "category": "international",
        "source_url": "https://query.wikidata.org/",
        "download_url": "https://query.wikidata.org/sparql  (scoped SPARQL; JSON/CSV)",
        "license": "CC0 1.0 (public domain dedication)", "license_open": True,
        "grain": "institution (global)", "entity": "institution",
        "join_keys": ["wikidata_qid", "ipeds_unitid", "ror_id"],
        "coverage": {"latest": "live (~13k university items)"},
        "dictionary": "https://www.wikidata.org/wiki/Wikidata:List_of_properties",
        "format": "SPARQL (JSON/CSV)", "est_size": "scoped query ~few MB",
        "maps_to": {"unipaith_entity": "institution",
                    "sections": ["non-US institution backbone; UNITID/ROR crosswalk; quick facts (founded, website, logo)"]},
    },
    # ---- other relevant ---------------------------------------------------------------
    {
        "id": "opportunity-insights-mobility-report-cards",
        "title": "Opportunity Insights — College Mobility Report Cards",
        "publisher": "Opportunity Insights (Harvard)",
        "category": "outcomes",
        "source_url": "https://opportunityinsights.org/data/",
        "download_url": "https://opportunityinsights.org/wp-content/uploads/2018/03/mrc_table1.csv",
        "license": "Open for research use with citation (Opportunity Insights terms)",
        "license_open": True,
        "grain": "institution (~2,200 colleges)", "entity": "institution",
        "join_keys": ["super_opeid", "name"],
        "coverage": {"latest": "cohorts ~1980-1991 births"},
        "dictionary": "https://opportunityinsights.org/wp-content/uploads/2018/03/Codebook-MRC-Table-1.pdf",
        "format": "csv",
        "path": "sources/outcomes/OpportunityInsights_mrc_table1.csv",
        "maps_to": {"unipaith_entity": "institution",
                    "sections": ["outcomes/ROI: economic-mobility metric (value-add)"]},
    },
    {
        "id": "census-acs-s1501-educational-attainment",
        "title": "Census ACS Subject Table S1501 — Educational Attainment by geography",
        "publisher": "U.S. Census Bureau",
        "category": "geo",
        "source_url": "https://data.census.gov/",
        "download_url": "https://api.census.gov/data/2022/acs/acs5/subject?get=group(S1501)&for=county:*  (free key)",
        "license": US_GOV_PD, "license_open": True,
        "grain": "geography (state/county/place) x year", "entity": "geo",
        "join_keys": ["fips"],
        "coverage": {"latest": "ACS 5-year 2022"},
        "dictionary": "https://api.census.gov/data/2022/acs/acs5/subject/groups/S1501.html",
        "format": "REST API + flat files", "est_size": "API (per-slice KB-MB)",
        "maps_to": {"unipaith_entity": "geo",
                    "sections": ["institution locale/context; geographic-fit grounding (FIPS join)"]},
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

    # 2) catalog (resident archive + sourced/verified reference datasets)
    datasets = [fill_shapes(root, e) for e in CURATED + SOURCED]
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
