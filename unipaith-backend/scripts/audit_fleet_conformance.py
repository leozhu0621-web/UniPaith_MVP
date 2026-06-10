"""Fleet-wide conformance audit: for every institution + school + program,
build the manifest snapshot from the DB and run check_conformance.

Usage: PYTHONPATH=src .venv/bin/python scripts/audit_fleet_conformance.py [--detail "Name"]
"""

from __future__ import annotations

import asyncio
import sys

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard.conformance import check_conformance

DB = "postgresql+asyncpg://unipaith:unipaith@localhost:5432/unipaith"


def inst_snapshot(i: Institution) -> dict:
    return {
        "description_text": i.description_text,
        "student_body_size": i.student_body_size,
        "media_gallery": i.media_gallery,
        "website_url": i.website_url,
        "type": i.type,
        "campus_setting": i.campus_setting,
        "founded_year": i.founded_year,
        "social_links": i.social_links,
        "ranking_data": i.ranking_data,
        "school_outcomes": i.school_outcomes,
        "content_sources": i.content_sources,
    }


def school_snapshot(s: School) -> dict:
    return {
        "name": s.name,
        "description_text": s.description_text,
        "website_url": s.website_url,
        "about_detail": s.about_detail,
        "content_sources": s.content_sources,
    }


def prog_snapshot(p: Program) -> dict:
    return {
        "program_name": p.program_name,
        "degree_type": p.degree_type,
        "duration_months": p.duration_months,
        "delivery_format": p.delivery_format,
        "description_text": p.description_text,
        "website_url": p.website_url,
        "department": p.department,
        "highlights": getattr(p, "highlights", None),
        "who_its_for": getattr(p, "who_its_for", None),
        "tracks": p.tracks,
        "application_requirements": p.application_requirements,
        "cost_data": p.cost_data,
        "outcomes_data": p.outcomes_data,
        "class_profile": p.class_profile,
        "faculty_contacts": p.faculty_contacts,
        "external_reviews": p.external_reviews,
        "content_sources": p.content_sources,
    }


def node_standard(blob: dict | None) -> dict | None:
    return (blob or {}).get("_standard")


def effective_missing(result, std: dict | None) -> list[str]:
    omitted = set((std or {}).get("omitted", []))
    return [f for f in result.missing_fields if f not in omitted]


async def main() -> None:
    detail = None
    if "--detail" in sys.argv:
        detail = sys.argv[sys.argv.index("--detail") + 1]
    engine = create_async_engine(DB)
    Sess = async_sessionmaker(engine)
    async with Sess() as session:
        insts = (await session.execute(select(Institution).order_by(Institution.name))).scalars().all()
        rows = []
        for i in insts:
            snap = inst_snapshot(i)
            res = check_conformance("institution", snap)
            std = node_standard(i.school_outcomes)
            inst_missing = effective_missing(res, std)
            schools = (
                (await session.execute(select(School).where(School.institution_id == i.id)))
                .scalars()
                .all()
            )
            progs = (
                (
                    await session.execute(
                        select(Program).where(
                            Program.institution_id == i.id,
                            Program.is_published.is_(True),
                        )
                    )
                )
                .scalars()
                .all()
            )
            s_bad = 0
            s_nostamp = 0
            for s in schools:
                sres = check_conformance("school", school_snapshot(s))
                sstd = node_standard(s.about_detail)
                if sstd is None:
                    s_nostamp += 1
                if effective_missing(sres, sstd):
                    s_bad += 1
            p_bad = 0
            p_nostamp = 0
            for p in progs:
                pres = check_conformance("program", prog_snapshot(p))
                pstd = node_standard(p.outcomes_data)
                if pstd is None:
                    p_nostamp += 1
                if effective_missing(pres, pstd):
                    p_bad += 1
            gold = (
                not inst_missing
                and std is not None
                and s_bad == 0
                and s_nostamp == 0
                and p_bad == 0
                and p_nostamp == 0
                and len(schools) > 0
                and len(progs) > 0
            )
            rows.append(
                (
                    i.name,
                    "GOLD" if gold else "----",
                    len(inst_missing),
                    "Y" if std else "n",
                    f"{len(schools) - s_bad}/{len(schools)}",
                    f"{len(progs) - p_bad}/{len(progs)}",
                    s_nostamp,
                    p_nostamp,
                )
            )
            if detail and detail.lower() in i.name.lower():
                print(f"\n=== {i.name} (institution) ===")
                print("  missing (after omitted):", inst_missing)
                print("  missing_sections:", res.missing_sections)
                print("  _standard:", std)
                for s in schools:
                    sres = check_conformance("school", school_snapshot(s))
                    sstd = node_standard(s.about_detail)
                    miss = effective_missing(sres, sstd)
                    if miss or sstd is None:
                        print(f"  [school] {s.name}: stamp={'Y' if sstd else 'NO'} missing={miss}")
                for p in progs:
                    pres = check_conformance("program", prog_snapshot(p))
                    pstd = node_standard(p.outcomes_data)
                    miss = effective_missing(pres, pstd)
                    if miss or pstd is None:
                        print(
                            f"  [program] {p.slug or p.program_name}: "
                            f"stamp={'Y' if pstd else 'NO'} missing={miss}"
                        )
        print(
            f"\n{'University':44} {'gold':4} {'inst-miss':9} {'stamp':5} "
            f"{'schools-ok':10} {'progs-ok':9} {'s-nostamp':9} {'p-nostamp':9}"
        )
        for r in rows:
            print(f"{r[0]:44.44} {r[1]:4} {r[2]:<9} {r[3]:5} {r[4]:10} {r[5]:9} {r[6]:<9} {r[7]:<9}")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
