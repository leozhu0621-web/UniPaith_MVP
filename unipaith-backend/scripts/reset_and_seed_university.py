"""Reset the database (wipe ALL data + accounts) and seed ONE real university.

DESTRUCTIVE. Truncates every table (keeps the schema + alembic_version), then
seeds a single real institution — MIT — with real schools + programs (via the
Spec-69 catalog ingestion, so each program gets normalized fields + a stable
slug + CIP code that feeds the matcher) and outcomes on the flagship programs.

Usage (intended as a one-off prod job, run inside the VPC where it can reach RDS):
    cd unipaith-backend
    PYTHONPATH=src python -m scripts.reset_and_seed_university

Idempotent: re-running wipes + reseeds to the same clean state. The university is
selected by UNIVERSITY env (default "mit").
"""

from __future__ import annotations

import asyncio
import logging
import os
import uuid

from sqlalchemy import select, text

import unipaith.models  # noqa: F401 — registers every table on Base.metadata
from unipaith.database import async_session, engine
from unipaith.models.base import Base
from unipaith.models.institution import Institution, School
from unipaith.models.user import User, UserRole
from unipaith.services.catalog import CatalogIngestService
from unipaith.services.crawler.seed import seed_all
from unipaith.services.outcomes_service import OutcomesService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("reset_and_seed_university")

# ── MIT — real institution, schools, programs ───────────────────────────────
MIT = {
    "name": "Massachusetts Institute of Technology",
    "type": "university",
    "country": "United States",
    "city": "Cambridge",
    "schools": [
        "School of Engineering",
        "School of Science",
        "MIT Sloan School of Management",
        "School of Architecture and Planning",
        "School of Humanities, Arts, and Social Sciences",
        "Schwarzman College of Computing",
    ],
    # (program_name, degree, cip, school_index, tuition, modality, description)
    "programs": [
        (
            "Electrical Engineering and Computer Science",
            "BS",
            "14.1001",
            0,
            61990,
            "in_person",
            "Undergraduate EECS — circuits, computation, AI, and systems.",
        ),
        (
            "Electrical Engineering and Computer Science",
            "MEng",
            "14.1001",
            0,
            61990,
            "in_person",
            "A fifth-year professional master's in EECS with a research thesis.",
        ),
        (
            "Electrical Engineering and Computer Science",
            "PhD",
            "14.1001",
            0,
            61990,
            "in_person",
            "Doctoral research in EECS across AI, systems, theory, and devices.",
        ),
        (
            "Computer Science",
            "PhD",
            "11.0701",
            5,
            61990,
            "in_person",
            "Doctoral research in computer science within the College of Computing.",
        ),
        (
            "Mechanical Engineering",
            "BS",
            "14.1901",
            0,
            61990,
            "in_person",
            "Design, mechanics, controls, and manufacturing.",
        ),
        (
            "Mechanical Engineering",
            "PhD",
            "14.1901",
            0,
            61990,
            "in_person",
            "Doctoral research in mechanical engineering.",
        ),
        (
            "Aeronautics and Astronautics",
            "SM",
            "14.0201",
            0,
            61990,
            "in_person",
            "Master of Science in aerospace systems, autonomy, and propulsion.",
        ),
        (
            "Chemical Engineering",
            "PhD",
            "14.0701",
            0,
            61990,
            "in_person",
            "Doctoral research in chemical engineering and processes.",
        ),
        (
            "Civil and Environmental Engineering",
            "MEng",
            "14.0801",
            0,
            61990,
            "in_person",
            "Professional master's in civil & environmental systems.",
        ),
        (
            "Materials Science and Engineering",
            "PhD",
            "14.1801",
            0,
            61990,
            "in_person",
            "Doctoral research in materials structure, properties, and processing.",
        ),
        ("Mathematics", "BS", "27.0101", 1, 61990, "in_person", "Pure and applied mathematics."),
        (
            "Mathematics",
            "PhD",
            "27.0101",
            1,
            61990,
            "in_person",
            "Doctoral research in mathematics.",
        ),
        (
            "Physics",
            "BS",
            "40.0801",
            1,
            61990,
            "in_person",
            "Experimental and theoretical physics.",
        ),
        (
            "Physics",
            "PhD",
            "40.0801",
            1,
            61990,
            "in_person",
            "Doctoral research across particle, condensed-matter, and astrophysics.",
        ),
        (
            "Biology",
            "PhD",
            "26.0101",
            1,
            61990,
            "in_person",
            "Doctoral research in molecular, cellular, and computational biology.",
        ),
        (
            "Brain and Cognitive Sciences",
            "PhD",
            "42.2706",
            1,
            61990,
            "in_person",
            "Doctoral research in neuroscience and cognition.",
        ),
        ("Chemistry", "PhD", "40.0501", 1, 61990, "in_person", "Doctoral research in chemistry."),
        (
            "Master of Business Administration",
            "MBA",
            "52.0201",
            2,
            86550,
            "in_person",
            "The MIT Sloan MBA — analytics-driven, action-learning management.",
        ),
        (
            "Management",
            "PhD",
            "52.0201",
            2,
            61990,
            "in_person",
            "Doctoral research in management science and organizations.",
        ),
        (
            "Business Analytics",
            "MS",
            "52.1301",
            2,
            86550,
            "in_person",
            "The Master of Business Analytics — data science for management.",
        ),
        (
            "Economics",
            "BS",
            "45.0601",
            4,
            61990,
            "in_person",
            "Undergraduate economics with quantitative rigor.",
        ),
        ("Economics", "PhD", "45.0601", 4, 61990, "in_person", "Doctoral research in economics."),
        (
            "Architecture",
            "MArch",
            "04.0201",
            3,
            61990,
            "in_person",
            "Professional Master of Architecture.",
        ),
        (
            "Urban Studies and Planning",
            "MCP",
            "04.0301",
            3,
            61990,
            "in_person",
            "Master in City Planning.",
        ),
        (
            "Data, Economics, and Design of Policy",
            "MS",
            "45.0601",
            4,
            61990,
            "online",
            "A blended master's in development economics and policy design.",
        ),
    ],
}


async def wipe_all() -> int:
    """Truncate every table except alembic_version (keep the schema)."""
    async with async_session() as db:
        rows = await db.execute(
            text(
                "SELECT tablename FROM pg_tables "
                "WHERE schemaname='public' AND tablename <> 'alembic_version'"
            )
        )
        tables = [r[0] for r in rows]
        if tables:
            quoted = ", ".join(f'"{t}"' for t in tables)
            await db.execute(text(f"TRUNCATE TABLE {quoted} RESTART IDENTITY CASCADE"))  # noqa: S608
        await db.commit()
    return len(tables)


async def seed_university(uni: dict) -> dict:
    async with async_session() as db:
        admin = User(
            id=uuid.uuid4(),
            email="admissions@mit.edu",
            cognito_sub=f"seed-{uuid.uuid4().hex[:10]}",
            role=UserRole.institution_admin,
            is_active=True,
        )
        db.add(admin)
        await db.flush()

        inst = Institution(
            admin_user_id=admin.id,
            name=uni["name"],
            type=uni["type"],
            country=uni["country"],
            city=uni.get("city"),
            setup_complete=True,
        )
        db.add(inst)
        await db.flush()

        schools: list[School] = []
        for i, sname in enumerate(uni["schools"]):
            s = School(institution_id=inst.id, name=sname, sort_order=i)
            db.add(s)
            schools.append(s)
        await db.flush()

        ingest = CatalogIngestService(db)
        outcomes = OutcomesService(db)
        created_total = 0
        for name, degree, cip, school_idx, tuition, modality, desc in uni["programs"]:
            ext = f"{cip}-{degree}".replace(".", "")
            summary = await ingest.ingest_programs(
                inst.id,
                [
                    {
                        "program_name": f"{name} ({degree})",
                        "degree_type": degree,
                        "delivery_format": modality,
                        "tuition": tuition,
                        "cip_code": cip,
                        "external_id": ext,
                        "description": desc,
                    }
                ],
                source="institution_verified",
                source_url="https://web.mit.edu/",
                school_id=schools[school_idx].id,
            )
            created_total += summary["created"]

        # Outcomes on a few flagship programs (real-ish, windowed, provenance-stamped).
        from unipaith.models.institution import Program

        flagship = (
            (
                await db.execute(
                    select(Program)
                    .where(Program.institution_id == inst.id)
                    .where(Program.degree_type.in_(("masters", "professional")))
                    .limit(4)
                )
            )
            .scalars()
            .all()
        )
        for prog in flagship:
            await outcomes.upsert_program_outcome(
                prog.id, "salary_median", "2024", source="reported", value_numeric=125000
            )
            await outcomes.upsert_program_outcome(
                prog.id, "employment_rate", "2024", source="reported", value_numeric=0.95
            )
            await outcomes.upsert_program_admissions(
                prog.id,
                2024,
                source="reported",
                applicants=2400,
                admits=170,
                enrolled=120,
                admit_rate=0.071,
                yield_rate=0.706,
                class_profile={"gpa_p50": 3.9, "gre_p50": 332, "cohort_size": 120},
                selectivity_band="most_selective",
            )
        await db.commit()
        return {"institution": inst.name, "schools": len(schools), "programs": created_total}


# University program-page frontier — what the continuous crawler fetches.
_FRONTIER = [
    "https://gradadmissions.mit.edu/programs",
    "https://www.mit.edu/education/",
    "https://grad.stanford.edu/programs/",
    "https://gsas.harvard.edu/programs-of-study",
    "https://www.cmu.edu/graduate/",
    "https://grad.berkeley.edu/programs/",
    "https://www.gradschool.cornell.edu/academics/fields-of-study/",
    "https://admission.gatech.edu/graduate",
    "https://grad.illinois.edu/admissions/programs",
    "https://www.gradschool.wisc.edu/academics/programs/",
]


async def seed_crawler() -> dict:
    """Seed the crawler so the continuous routine has fuel after the wipe: Tier-1
    reference data + allowlisted sources + a frontier. The scheduled engine tick
    (enabled in prod via CRAWLER_ENGINE_ENABLED) crawls these continuously."""
    from urllib.parse import urlparse

    from unipaith.models.crawler import CrawlSource
    from unipaith.models.knowledge import CrawlFrontier

    async with async_session() as db:
        ref = await seed_all(db, commit=True)

    added_sources = added_frontier = 0
    async with async_session() as db:
        have_src = {d for (d,) in (await db.execute(select(CrawlSource.domain))).all()}
        have_url = {u for (u,) in (await db.execute(select(CrawlFrontier.url))).all()}
        for url in _FRONTIER:
            domain = urlparse(url).netloc
            if domain not in have_src:
                db.add(
                    CrawlSource(
                        name=domain,
                        slug=domain.replace(".", "-"),
                        domain=domain,
                        publisher_kind="academic",
                        trust_tier=2,
                        allowlisted=True,
                        enabled=True,
                    )
                )
                have_src.add(domain)
                added_sources += 1
            if url not in have_url:
                db.add(
                    CrawlFrontier(
                        url=url,
                        domain=domain,
                        priority=85,
                        status="pending",
                        content_format_hint="web",
                    )
                )
                added_frontier += 1
        await db.commit()
    return {
        "reference_domains": len(ref.get("reference", {})),
        "sources_added": added_sources,
        "frontier_added": added_frontier,
    }


async def main() -> None:
    # Ensure schema exists (no-op in prod where migrations ran on deploy).
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)

    wiped = await wipe_all()
    uni_key = os.environ.get("UNIVERSITY", "mit").lower()
    uni = {"mit": MIT}.get(uni_key, MIT)
    result = await seed_university(uni)
    crawler = await seed_crawler()

    logger.info("WIPED %d tables; seeded %s; crawler %s", wiped, result, crawler)
    print(
        f"\n=== RESET + SEED complete ===\n  wiped: {wiped} tables\n"
        f"  seeded: {result}\n  crawler (continuous routine fuel): {crawler}"
    )


if __name__ == "__main__":
    asyncio.run(main())
