"""Cold-start seed script for the knowledge engine.

Seeds the crawl frontier with high-quality education sources,
auto-approves pending extracted programs, and inserts the default
advisor persona. Run after migration.

Usage:
    cd unipaith-backend
    PYTHONPATH=src python -m scripts.seed_knowledge_engine
"""
from __future__ import annotations

import asyncio
import logging

from sqlalchemy import func, select, update

from unipaith.config import settings
from unipaith.database import async_session
from unipaith.models.crawler import ExtractedProgram
from unipaith.models.knowledge import AdvisorPersona, CrawlFrontier, EngineDirective

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_knowledge_engine")

SEED_FRONTIER_URLS: list[dict] = [
    # University program pages (top schools)
    {"url": "https://www.mit.edu/education/", "priority": 90, "hint": "web"},
    {"url": "https://grad.stanford.edu/programs/", "priority": 90, "hint": "web"},
    {"url": "https://gsas.harvard.edu/programs-of-study", "priority": 90, "hint": "web"},
    {"url": "https://www.cmu.edu/graduate/", "priority": 85, "hint": "web"},
    {"url": "https://grad.berkeley.edu/programs/", "priority": 85, "hint": "web"},
    {"url": "https://www.gradschool.cornell.edu/academics/fields-of-study/", "priority": 85, "hint": "web"},
    {"url": "https://gradadmissions.mit.edu/programs", "priority": 90, "hint": "web"},
    {"url": "https://admission.gatech.edu/graduate", "priority": 80, "hint": "web"},
    {"url": "https://grad.illinois.edu/admissions/programs", "priority": 80, "hint": "web"},
    {"url": "https://www.gradschool.wisc.edu/academics/programs/", "priority": 75, "hint": "web"},

    # Rankings and comparison sites
    {"url": "https://www.usnews.com/best-graduate-schools", "priority": 80, "hint": "web"},
    {"url": "https://www.topuniversities.com/university-rankings", "priority": 80, "hint": "web"},
    {"url": "https://www.timeshighereducation.com/world-university-rankings", "priority": 80, "hint": "web"},
    {"url": "https://www.niche.com/graduate-schools/search/best-graduate-schools/", "priority": 75, "hint": "web"},

    # Student experience and forums
    {"url": "https://www.reddit.com/r/gradadmissions/top/?t=month", "priority": 70, "hint": "social"},
    {"url": "https://www.reddit.com/r/GradSchool/top/?t=month", "priority": 65, "hint": "social"},
    {"url": "https://www.reddit.com/r/MBA/top/?t=month", "priority": 65, "hint": "social"},
    {"url": "https://www.thegradcafe.com/survey/", "priority": 70, "hint": "web"},

    # Government data
    {"url": "https://nces.ed.gov/ipeds/datacenter/InstitutionByName.aspx", "priority": 60, "hint": "web"},
    {"url": "https://collegescorecard.ed.gov/data/", "priority": 70, "hint": "structured"},

    # News and analysis
    {"url": "https://www.insidehighered.com/news", "priority": 55, "hint": "web"},
    {"url": "https://www.chronicle.com/section/news", "priority": 55, "hint": "web"},

    # RSS feeds
    {"url": "https://www.insidehighered.com/rss/news", "priority": 50, "hint": "rss"},
    {"url": "https://www.chronicle.com/section/news/rss", "priority": 50, "hint": "rss"},

    # Financial aid resources
    {"url": "https://studentaid.gov/understand-aid/types", "priority": 60, "hint": "web"},
    {"url": "https://www.fastweb.com/directory/scholarships-for-graduate-students", "priority": 55, "hint": "web"},
]

DEFAULT_DIRECTIVES: list[dict] = [
    {
        "directive_type": "throttle",
        "directive_key": "rpm",
        "directive_value": {"rpm": 10},
        "description": "Default engine speed: 10 requests per minute",
        "priority": 100,
    },
    {
        "directive_type": "steering",
        "directive_key": "default_topics",
        "directive_value": {
            "topics": [
                "graduate admissions",
                "university rankings",
                "scholarship opportunities",
                "student experiences",
                "program requirements",
            ],
        },
        "description": "Default topic steering for knowledge discovery",
        "priority": 50,
    },
    {
        "directive_type": "bias",
        "directive_key": "source_diversity",
        "directive_value": {
            "min_domains_per_cycle": 5,
            "max_documents_per_domain": 50,
            "recency_weight": 0.3,
            "credibility_weight": 0.4,
            "diversity_weight": 0.3,
        },
        "description": "Source diversity and quality bias controls",
        "priority": 50,
    },
]


async def seed() -> None:
    async with async_session() as db:
        existing_frontier = await db.scalar(
            select(func.count()).select_from(CrawlFrontier)
        )
        if existing_frontier and existing_frontier > 0:
            logger.info("Frontier already seeded (%d items), skipping URL seed", existing_frontier)
        else:
            for source in SEED_FRONTIER_URLS:
                existing = await db.execute(
                    select(CrawlFrontier).where(CrawlFrontier.url == source["url"]).limit(1)
                )
                if existing.scalar_one_or_none():
                    continue
                db.add(CrawlFrontier(
                    url=source["url"],
                    domain=source["url"].split("//")[1].split("/")[0],
                    priority=source["priority"],
                    content_format_hint=source["hint"],
                    discovery_method="seed",
                ))
            logger.info("Seeded %d frontier URLs", len(SEED_FRONTIER_URLS))

        for directive_data in DEFAULT_DIRECTIVES:
            existing = await db.execute(
                select(EngineDirective).where(
                    EngineDirective.directive_type == directive_data["directive_type"],
                    EngineDirective.directive_key == directive_data["directive_key"],
                ).limit(1)
            )
            if existing.scalar_one_or_none():
                continue
            db.add(EngineDirective(**directive_data))
        logger.info("Seeded default directives")

        existing_persona = await db.execute(
            select(AdvisorPersona).where(AdvisorPersona.name == "default").limit(1)
        )
        if not existing_persona.scalar_one_or_none():
            db.add(AdvisorPersona(
                name="default",
                is_active=True,
                base_persona_prompt=(
                    "You are a warm, empathetic college advisor. You lead with understanding, "
                    "not data. You help students build self-awareness about what they truly want "
                    "before recommending programs. You remember everything about the student and "
                    "reference previous conversations naturally. You never sound like a search "
                    "engine or a database. When you need to deliver hard truths, you do it with "
                    "care. You are persuasive when it matters."
                ),
            ))
            logger.info("Seeded default advisor persona")

        pending_programs = await db.scalar(
            select(func.count()).select_from(ExtractedProgram).where(
                ExtractedProgram.review_status == "pending",
            )
        )
        if pending_programs and pending_programs > 0:
            await db.execute(
                update(ExtractedProgram)
                .where(ExtractedProgram.review_status == "pending")
                .values(review_status="approved")
            )
            logger.info("Auto-approved %d pending extracted programs", pending_programs)
        else:
            logger.info("No pending programs to auto-approve")

        await db.commit()
        logger.info("Knowledge engine seed complete")


if __name__ == "__main__":
    asyncio.run(seed())
