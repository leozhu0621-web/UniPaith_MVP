"""Seed ONE real institution — MIT — with REAL, sourced data (no fabrication).

Every numeric fact here comes from an authoritative public source and carries a
``source_url`` in ``field_provenance`` so a catalog fact can answer "sourced from
<domain>" (Spec 60 §4 / 69 §6):

  - U.S. Dept. of Education **College Scorecard** API (IPEDS unit 166683):
    admit rate, cost of attendance, avg net price, 4-yr completion, institution
    median earnings, and FIELD-OF-STUDY (by-CIP) median earnings + degrees
    conferred — the per-program outcome numbers.
  - **MIT Facts** (facts.mit.edu): founding year, campus, enrollment, Nobel
    count, Class-of-2029 admissions funnel, 2025-26 cost-of-attendance breakdown.
  - **MIT Admissions** (mitadmissions.org): EA/RA deadlines + SAT/ACT policy.
  - **MIT Registrar** (registrar.mit.edu): 2025-26 tuition.

Where a real value is not published (e.g. per-program graduate admit rates, or
employer lists MIT doesn't release per major) the field is left NULL rather than
invented — that is the whole point of this script vs. the synthetic generator.

Idempotent: re-running upserts to the same state (Institution by name, programs
by stable external_id via CatalogIngestService). With ONLY_REAL=1 (default) it
also unpublishes any *other* institution's programs so only real data is live.

Run locally:
    cd unipaith-backend
    PYTHONPATH=src DATABASE_URL=... .venv/bin/python -m scripts.seed_real_mit

Run on prod RDS: as a one-off ECS task using the backend image (in-VPC), command
    ["python","-m","scripts.seed_real_mit"]
"""

from __future__ import annotations

import asyncio
import logging
import os
import uuid

from sqlalchemy import select, update

import unipaith.models  # noqa: F401 — registers every table on Base.metadata
from unipaith.database import async_session
from unipaith.models.institution import Institution, Program, School
from unipaith.models.user import User, UserRole
from unipaith.services.catalog import CatalogIngestService
from unipaith.services.outcomes_service import OutcomesService

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("seed_real_mit")

SC = "https://collegescorecard.ed.gov/school/?166683-Massachusetts-Institute-of-Technology"
FACTS = "https://facts.mit.edu/"
ADM = "https://mitadmissions.org/apply/firstyear/deadlines-requirements/"
REG = "https://registrar.mit.edu/registration-academics/tuition-fees/undergraduate"

# ── Institution (all real, sourced) ─────────────────────────────────────────
MIT_NAME = "Massachusetts Institute of Technology"

SCHOOLS = [
    "School of Engineering",
    "School of Science",
    "MIT Sloan School of Management",
    "School of Architecture and Planning",
    "School of Humanities, Arts, and Social Sciences",
    "MIT Schwarzman College of Computing",
]

# Real 2025-26 cost of attendance (facts.mit.edu; tuition split via registrar).
# net_price_service reads: tuition_annual, fees{}, estimated_living_cost,
# book_supplies. Sum = $89,340 = the published total.
COST_DATA = {
    "tuition_annual": 64310,  # $32,155/term x2 (registrar 2025-26)
    "fees": {"student_life_fee": 420},  # tuition+fees 64,730 − tuition 64,310
    "estimated_living_cost": 21264,  # housing + food (facts.mit.edu 2025-26)
    "book_supplies": 3346,  # books + personal allowance (facts.mit.edu)
    "total_cost_of_attendance": 89340,
    "avg_net_price": 20111,  # College Scorecard avg net price (private)
    "currency": "USD",
    "academic_year": "2025-2026",
    "source_url": FACTS,
}

# Institution-wide undergraduate admissions funnel + outcomes (all real).
SCHOOL_OUTCOMES = {
    "admissions": {
        "cycle": "Class of 2029",
        "applicants": 29281,
        "admits": 1334,
        "admit_rate": 0.046,
        "source_url": FACTS,
    },
    "enrollment": {"total": 11816, "undergraduate": 4561, "graduate": 7255, "source_url": FACTS},
    "completion_rate_4yr_150pct": 0.9641,
    "median_earnings_10yr": 143372,
    "median_earnings_6yr": 131633,
    "nobel_laureates": 106,
    "macarthur_fellows": 85,
    "source": "MIT Facts + U.S. Dept. of Education College Scorecard",
    "source_urls": [FACTS, SC],
}

RANKING_DATA = {
    "qs_world_university_rankings": {
        "rank": 1,
        "year": 2025,
        "source_url": "https://www.topuniversities.com/universities/massachusetts-institute-technology-mit",
    },
}

# Real undergraduate application requirements (mitadmissions.org).
UG_APP_REQUIREMENTS = {
    "standardized_testing": "SAT or ACT required (self-reported; verified on enrollment)",
    "essays": True,
    "letters_of_recommendation": "2 teacher evaluations + 1 counselor",
    "interview": "Optional educational counselor interview",
    "application_platform": "MIT first-year application (not the Common App)",
    "source_url": ADM,
}

# Real undergraduate intake rounds (mitadmissions.org). MIT admits to the
# Institute (not by major), so these apply to every undergraduate program.
UG_INTAKE_ROUNDS = [
    {
        "round_name": "Early Action",
        "application_deadline": "2025-11-01",
        "decision_date": "2025-12-15",
        "program_start": "2026-09-01",
    },
    {
        "round_name": "Regular Action",
        "application_deadline": "2026-01-05",
        "decision_date": "2026-03-15",
        "program_start": "2026-09-01",
    },
]

# ── Programs — real catalog with real outcomes ──────────────────────────────
# (name, degree, cip, school_idx, ug?, earn_1yr, earn_4yr, earn_5yr, awards)
# earnings = federal median earnings post-completion, by field of study
# (College Scorecard). awards = IPEDS degrees conferred. None = not published.
PROGRAMS = [
    ("Computer Science and Engineering", "BS", "11.0701", 5, True, 154492, 225141, 220064, 389),
    (
        "Electrical Engineering and Computer Science",
        "BS",
        "14.1001",
        5,
        True,
        117345,
        161118,
        None,
        87,
    ),
    (
        "Electrical Engineering and Computer Science",
        "MEng",
        "14.1001",
        5,
        False,
        149936,
        199245,
        None,
        78,
    ),
    ("Mechanical Engineering", "BS", "14.1901", 0, True, 83957, 131967, None, 141),
    ("Mechanical Engineering", "SM", "14.1901", 0, False, 155889, 200732, None, 149),
    ("Mathematics", "BS", "27.0101", 1, True, 109288, 174951, None, 139),
    ("Mathematics with Computer Science", "BS", "30.0801", 1, True, 126153, None, None, 30),
    ("Physics", "BS", "40.0801", 1, True, 54773, 131025, None, 79),
    ("Chemical Engineering", "BS", "14.0701", 0, True, 80139, 122093, None, 39),
    ("Biological Engineering", "BS", "14.0501", 0, True, 70696, 111738, None, 54),
    ("Materials Science and Engineering", "BS", "14.1801", 0, True, 65919, None, None, 24),
    ("Brain and Cognitive Sciences", "BS", "26.1501", 1, True, 48125, None, None, 16),
    ("Civil and Environmental Engineering", "MEng", "14.0801", 0, False, 88805, None, None, 29),
    ("Management Science", "SM", "52.1301", 2, False, 204731, None, None, 782),
    ("Master in City Planning", "MCP", "04.0301", 3, False, 81382, 100130, None, 43),
    ("Aeronautics and Astronautics", "BS", "14.0201", 0, True, None, None, None, None),
    (
        "Electrical Engineering and Computer Science",
        "PhD",
        "14.1001",
        5,
        False,
        None,
        None,
        None,
        None,
    ),
    ("Biology", "PhD", "26.0101", 1, False, None, None, None, None),
]


def _provenance(fields: list[str], url: str) -> dict:
    return {f: {"source_url": url, "source": "verified_public_source"} for f in fields}


async def seed() -> dict:
    only_real = os.getenv("ONLY_REAL", "1") == "1"
    async with async_session() as db:
        # 1) Institution + admin (idempotent by name / email).
        inst = (
            await db.execute(select(Institution).where(Institution.name == MIT_NAME))
        ).scalar_one_or_none()
        if inst is None:
            admin = (
                await db.execute(select(User).where(User.email == "admissions@mit.edu"))
            ).scalar_one_or_none()
            if admin is None:
                admin = User(
                    id=uuid.uuid4(),
                    email="admissions@mit.edu",
                    cognito_sub=f"seed-mit-{uuid.uuid4().hex[:10]}",
                    role=UserRole.institution_admin,
                    is_active=True,
                )
                db.add(admin)
                await db.flush()
            inst = Institution(
                admin_user_id=admin.id, name=MIT_NAME, type="university", country="United States"
            )
            db.add(inst)
            await db.flush()

        # Real institution fields (overwrite — these are the authoritative values).
        inst.region = "Massachusetts"
        inst.city = "Cambridge"
        inst.founded_year = 1861
        inst.student_body_size = 11816
        inst.campus_setting = "urban"
        inst.website_url = "https://web.mit.edu"
        inst.is_verified = True
        inst.setup_complete = True
        inst.description_text = (
            "The Massachusetts Institute of Technology is a private research university in "
            "Cambridge, Massachusetts, founded in 1861. MIT is organized into five schools and "
            "one college and is known for research and education in the physical sciences, "
            "engineering, computing, economics, and management."
        )
        inst.campus_description = (
            "168-acre campus along the Charles River in Cambridge, Massachusetts (urban)."
        )
        inst.ranking_data = RANKING_DATA
        inst.school_outcomes = SCHOOL_OUTCOMES
        await db.flush()

        # 2) Schools (idempotent by institution + name).
        schools: list[School] = []
        for i, sname in enumerate(SCHOOLS):
            s = (
                await db.execute(
                    select(School).where(School.institution_id == inst.id, School.name == sname)
                )
            ).scalar_one_or_none()
            if s is None:
                s = School(institution_id=inst.id, name=sname, sort_order=i)
                db.add(s)
                await db.flush()
            schools.append(s)

        # 3) Programs via CatalogIngestService (idempotent by external_id), then
        #    set the rich real fields directly.
        ingest = CatalogIngestService(db)
        outcomes = OutcomesService(db)
        n_created = 0
        for name, degree, cip, sidx, is_ug, e1, e4, e5, awards in PROGRAMS:
            ext = f"mit-{cip}-{degree}".replace(".", "")
            full_name = f"{name} ({degree})"
            summary = await ingest.ingest_programs(
                inst.id,
                [
                    {
                        "program_name": full_name,
                        "degree_type": degree,
                        "delivery_format": "in_person",
                        "tuition": COST_DATA["tuition_annual"],
                        "cip_code": cip,
                        "external_id": ext,
                        "description": (
                            f"{name} at MIT — a {'undergraduate' if is_ug else 'graduate'} "
                            f"program in the {SCHOOLS[sidx]}."
                        ),
                    }
                ],
                source="institution_verified",
                source_url=FACTS,
                school_id=schools[sidx].id,
            )
            n_created += summary.get("created", 0)

            prog = (
                await db.execute(select(Program).where(Program.external_id == ext))
            ).scalar_one_or_none()
            if prog is None:
                continue

            # Rich real fields.
            prog.is_published = True
            prog.campus_setting = "urban"
            prog.cost_data = COST_DATA
            prog.field_provenance = _provenance(["tuition", "cost_data", "outcomes_data"], SC)
            prog.catalog_source = "scorecard"
            prog.source_url = SC

            if is_ug:
                prog.acceptance_rate = 0.046  # MIT admits to the Institute, not by major
                prog.application_requirements = UG_APP_REQUIREMENTS
                prog.application_deadline = __import__("datetime").date(2026, 1, 5)
                prog.intake_rounds = UG_INTAKE_ROUNDS
                prog.who_its_for = (
                    "Prospective first-year students applying to MIT. Admission is to the "
                    "Institute; students declare a major (course number) at the end of first year."
                )

            # Program-level outcomes JSONB (read by the program detail/editor UI).
            od: dict = {
                "source": "U.S. Dept. of Education College Scorecard (field of study)",
                "source_url": SC,
            }
            if e1 is not None:
                od["median_starting_salary"] = e1
                od["outcome_reporting_window"] = (
                    "Median earnings ~1 year after completion (federal, by field of study)"
                )
                bands = {"p50_1yr": e1}
                if e4 is not None:
                    bands["p50_4yr"] = e4
                if e5 is not None:
                    bands["p50_5yr"] = e5
                od["salary_distribution_bands"] = bands
            if awards is not None:
                od["degrees_conferred_annual"] = awards
            prog.outcomes_data = od

            # Normalized Spec-68 outcomes (read by the matcher's data-completeness
            # + Spec-68 layer). Only real values; salary in USD.
            if e1 is not None:
                await outcomes.upsert_program_outcome(
                    prog.id,
                    "salary_median",
                    "post_completion_1yr",
                    source="licensed",
                    value_numeric=float(e1),
                    confidence=0.9,
                    source_url=SC,
                )
            if e4 is not None:
                await outcomes.upsert_program_outcome(
                    prog.id,
                    "salary_median",
                    "post_completion_4yr",
                    source="licensed",
                    value_numeric=float(e4),
                    confidence=0.9,
                    source_url=SC,
                )
            # Institution-wide undergrad admit rate is real for every UG program.
            if is_ug:
                await outcomes.upsert_program_admissions(
                    prog.id,
                    2025,
                    source="reported",
                    admit_rate=0.046,
                    selectivity_band="most_selective",
                )

        # 4) Make only real data live (optional, default on).
        unpublished = 0
        if only_real:
            res = await db.execute(
                update(Program)
                .where(Program.institution_id != inst.id, Program.is_published.is_(True))
                .values(is_published=False)
            )
            unpublished = res.rowcount or 0

        await db.commit()
        n_progs = (
            (await db.execute(select(Program).where(Program.institution_id == inst.id)))
            .scalars()
            .all()
        )
        return {
            "institution": inst.name,
            "schools": len(schools),
            "programs_total": len(n_progs),
            "programs_created_this_run": n_created,
            "other_programs_unpublished": unpublished,
        }


async def main() -> None:
    result = await seed()
    logger.info("Seeded real MIT data: %s", result)


if __name__ == "__main__":
    asyncio.run(main())
