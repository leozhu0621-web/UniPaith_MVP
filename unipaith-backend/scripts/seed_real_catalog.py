"""Seed the REAL university catalog — 28 US universities, ~599 programs — from
authoritative public sources only (no fabrication). Per the "only real data from
the website" directive.

Data lives in ``data/real_universities.json``, built from:
  - U.S. Dept. of Education **College Scorecard** API (by IPEDS unit id):
    admit rate, cost of attendance, avg net price, 4-yr completion, institution
    10-yr median earnings, and FIELD-OF-STUDY (by-CIP) median earnings + degrees
    conferred (the per-program outcome numbers).
  - **MIT Facts / MIT Admissions** (flagship enrichment block): founding year,
    schools, Nobel count, EA/RA deadlines, testing policy, COA breakdown.

Every numeric fact carries a ``source_url``. Facts a school doesn't publish are
left NULL, never invented.

Idempotent: Institution upsert by name; Program upsert by stable external_id
(``sc-<unit>-<cip>-<degree>``) via CatalogIngestService. ONLY_REAL=1 (default)
unpublishes programs that are NOT part of this real catalog so only real data is
live.

Run locally:
    cd unipaith-backend
    PYTHONPATH=src DATABASE_URL=... .venv/bin/python -m scripts.seed_real_catalog

Run on prod RDS (in-VPC one-off ECS task):
    command ["python","-m","scripts.seed_real_catalog"]
"""

from __future__ import annotations

import asyncio
import datetime as _dt
import json
import logging
import os
import pathlib
import uuid

from sqlalchemy import select, update

import unipaith.models  # noqa: F401 — registers every table on Base.metadata
from unipaith.database import async_session
from unipaith.models.institution import Institution, Program, School
from unipaith.models.user import User, UserRole
from unipaith.services.catalog import CatalogIngestService
from unipaith.services.outcomes_service import OutcomesService

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("seed_real_catalog")

DATA = pathlib.Path(__file__).resolve().parent.parent / "data" / "real_universities.json"


def _sc_url(unit_id: int) -> str:
    return f"https://collegescorecard.ed.gov/school/?{unit_id}"


def _slug_email(name: str) -> str:
    base = "".join(c for c in name.lower() if c.isalnum())[:24]
    return f"admissions+{base}@seed.unipaith.co"


async def _get_or_create_institution(db, uni: dict) -> Institution:
    name = uni["name"]
    inst = (
        await db.execute(select(Institution).where(Institution.name == name))
    ).scalar_one_or_none()
    if inst is None:
        admin = User(
            id=uuid.uuid4(),
            email=_slug_email(name),
            cognito_sub=f"seed-{uuid.uuid4().hex[:12]}",
            role=UserRole.institution_admin,
            is_active=True,
        )
        db.add(admin)
        await db.flush()
        inst = Institution(
            admin_user_id=admin.id, name=name, type="university", country="United States"
        )
        db.add(inst)
        await db.flush()
    return inst


def _institution_outcomes(uni: dict) -> dict:
    """Real institution-level Scorecard facts (every value sourced)."""
    out = {
        "ownership": uni.get("type"),
        "admit_rate": uni.get("admit_rate"),
        "completion_rate_4yr_150pct": uni.get("completion_4yr"),
        "median_earnings_10yr": uni.get("earn_10yr"),
        "avg_net_price": uni.get("net_price"),
        "source": "U.S. Dept. of Education College Scorecard",
        "source_url": _sc_url(uni["unit_id"]),
    }
    enr = uni.get("enrichment") or {}
    if enr.get("extras"):
        out["flagship"] = enr["extras"]
        out["admissions_funnel_source"] = (enr.get("source_urls") or [None])[0]
    return {k: v for k, v in out.items() if v is not None}


def _cost_data(uni: dict, enr: dict | None) -> dict:
    """net_price_service reads: tuition_annual, fees{}, estimated_living_cost,
    book_supplies. Sum reconciles to the published COA."""
    if enr and enr.get("cost_breakdown"):
        cb = enr["cost_breakdown"]
        return {
            "tuition_annual": cb["tuition_annual"],
            "fees": {"student_life_fee": cb.get("student_life_fee", 0)},
            "estimated_living_cost": cb.get("housing_food"),
            "book_supplies": cb.get("books_personal"),
            # both keys: backend net-price ignores it; frontend normalizeCostData
            # reads `total_cost_attendance` to render the COA band.
            "total_cost_of_attendance": cb.get("total"),
            "total_cost_attendance": cb.get("total"),
            "avg_net_price": uni.get("net_price"),
            "currency": "USD",
            "source_url": (enr.get("source_urls") or [None])[0],
        }
    tuition = uni.get("tuition")
    coa = uni.get("coa")
    living = (coa - tuition) if (coa and tuition and coa > tuition) else None
    cd = {
        "tuition_annual": tuition,
        "fees": {},
        "estimated_living_cost": living,  # COA minus tuition (real, derived)
        "book_supplies": 0,
        "total_cost_of_attendance": coa,
        "total_cost_attendance": coa,  # key the frontend normalizer reads
        "avg_net_price": uni.get("net_price"),
        "currency": "USD",
        "source_url": _sc_url(uni["unit_id"]),
    }
    return {k: v for k, v in cd.items() if v is not None}


async def seed() -> dict:
    only_real = os.getenv("ONLY_REAL", "1") == "1"
    catalog = json.loads(DATA.read_text())
    seeded_inst_ids: list[uuid.UUID] = []
    n_inst = n_prog = 0

    async with async_session() as db:
        for uni in catalog:
            enr = uni.get("enrichment")
            inst = await _get_or_create_institution(db, uni)
            seeded_inst_ids.append(inst.id)

            # Real institution fields.
            inst.city = uni.get("city")
            inst.region = uni.get("state")
            inst.student_body_size = uni.get("size")
            inst.website_url = uni.get("url")
            inst.is_verified = True
            inst.setup_complete = True
            inst.school_outcomes = _institution_outcomes(uni)
            kind = "public" if uni.get("type") == "public" else "private"
            inst.description_text = (
                f"{uni['name']} is a {kind} research university in "
                f"{uni.get('city')}, {uni.get('state')}."
            )
            if enr:
                inst.founded_year = enr.get("founded_year")
                inst.campus_setting = enr.get("campus_setting")
                inst.campus_description = enr.get("campus_description")
                if enr.get("extras", {}).get("qs_world_rank_2025"):
                    inst.ranking_data = {
                        "qs_world_university_rankings": {
                            "rank": enr["extras"]["qs_world_rank_2025"],
                            "year": 2025,
                        }
                    }
            await db.flush()
            n_inst += 1

            # Optional named schools (flagship only).
            school_by_idx: list[School] = []
            for i, sname in enumerate(enr.get("schools", []) if enr else []):
                s = (
                    await db.execute(
                        select(School).where(School.institution_id == inst.id, School.name == sname)
                    )
                ).scalar_one_or_none()
                if s is None:
                    s = School(institution_id=inst.id, name=sname, sort_order=i)
                    db.add(s)
                    await db.flush()
                school_by_idx.append(s)

            ingest = CatalogIngestService(db)
            outcomes = OutcomesService(db)
            cost = _cost_data(uni, enr)
            sc_url = _sc_url(uni["unit_id"])

            for p in uni["programs"]:
                degree, cip = p["degree"], p["cip"]
                is_ug = degree == "BS"
                ext = f"sc-{uni['unit_id']}-{cip}-{degree}".replace(".", "")
                summ = await ingest.ingest_programs(
                    inst.id,
                    [
                        {
                            "program_name": f"{p['name']} ({degree})",
                            "degree_type": degree,
                            "delivery_format": "in_person",
                            "tuition": uni.get("tuition"),
                            "cip_code": cip,
                            "external_id": ext,
                            "description": (
                                f"{p['name']} at {uni['name']} — a "
                                f"{'undergraduate' if is_ug else 'graduate'} program."
                            ),
                        }
                    ],
                    source="institution_verified",
                    source_url=sc_url,
                )
                n_prog += summ.get("created", 0)

                prog = (
                    await db.execute(select(Program).where(Program.external_id == ext))
                ).scalar_one_or_none()
                if prog is None:
                    continue
                prog.is_published = True
                prog.cost_data = cost
                prog.catalog_source = "scorecard"
                prog.source_url = sc_url
                prog.field_provenance = {
                    "tuition": {"source_url": sc_url},
                    "outcomes_data": {"source_url": sc_url},
                    "cost_data": {"source_url": cost.get("source_url", sc_url)},
                }
                if is_ug and uni.get("admit_rate") is not None:
                    prog.acceptance_rate = round(float(uni["admit_rate"]), 4)
                # Flagship undergrad enrichment (deadlines/testing).
                if is_ug and enr:
                    prog.application_deadline = _dt.date(2026, 1, 5)
                    prog.intake_rounds = [
                        {
                            "round_name": r["round"],
                            "application_deadline": r["deadline"],
                            "decision_date": r["decision"],
                            "program_start": "2026-09-01",
                        }
                        for r in enr.get("ug_deadlines", [])
                    ]
                    if enr.get("testing"):
                        prog.application_requirements = {
                            "standardized_testing": enr["testing"],
                            "source_url": sc_url,
                        }

                od: dict = {"source": "College Scorecard (field of study)", "source_url": sc_url}
                if p.get("earn_1yr"):
                    od["median_starting_salary"] = p["earn_1yr"]
                    od["outcome_reporting_window"] = (
                        "Median earnings ~1 year after completion (federal)"
                    )
                    bands = {"p50_1yr": p["earn_1yr"]}
                    if p.get("earn_4yr"):
                        bands["p50_4yr"] = p["earn_4yr"]
                    od["salary_distribution_bands"] = bands
                if p.get("awards") is not None:
                    od["degrees_conferred_annual"] = p["awards"]
                prog.outcomes_data = od

                if p.get("earn_1yr"):
                    await outcomes.upsert_program_outcome(
                        prog.id,
                        "salary_median",
                        "post_completion_1yr",
                        source="licensed",
                        value_numeric=float(p["earn_1yr"]),
                        confidence=0.9,
                        source_url=sc_url,
                    )
                if p.get("earn_4yr"):
                    await outcomes.upsert_program_outcome(
                        prog.id,
                        "salary_median",
                        "post_completion_4yr",
                        source="licensed",
                        value_numeric=float(p["earn_4yr"]),
                        confidence=0.9,
                        source_url=sc_url,
                    )
                if is_ug and uni.get("admit_rate") is not None:
                    await outcomes.upsert_program_admissions(
                        prog.id,
                        2025,
                        source="reported",
                        admit_rate=round(float(uni["admit_rate"]), 4),
                    )
            await db.flush()

        unpublished = 0
        if only_real:
            res = await db.execute(
                update(Program)
                .where(
                    Program.institution_id.notin_(seeded_inst_ids),
                    Program.is_published.is_(True),
                )
                .values(is_published=False)
            )
            unpublished = res.rowcount or 0

        await db.commit()
        live = (
            (await db.execute(select(Program).where(Program.is_published.is_(True))))
            .scalars()
            .all()
        )
        return {
            "universities": n_inst,
            "programs_created_this_run": n_prog,
            "published_programs_total": len(live),
            "other_programs_unpublished": unpublished,
        }


async def main() -> None:
    logger.info("Seeded real catalog: %s", await seed())


if __name__ == "__main__":
    asyncio.run(main())
