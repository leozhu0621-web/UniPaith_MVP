"""Spec 60 §1 / §8 / §11 / §15 — the no-personal-data contract.

"No personal/individual data gathered (contract test)." The allowlist is public
institutional / reference publishers only; personal / social domains are denied;
the dormant ``person_insights`` / ``advisor_personas`` tables stay empty after a
full seed (the engine builds the *world*, never people).
"""

from __future__ import annotations

from sqlalchemy import func, select

from unipaith.models.knowledge import AdvisorPersona, PersonInsight
from unipaith.services.crawler.seed import seed_all
from unipaith.services.crawler.sources import (
    ALLOWLISTED_DOMAINS,
    PERSONAL_DOMAIN_DENYLIST,
    SOURCE_ALLOWLIST,
    SourceRegistry,
)


def test_allowlist_has_no_personal_domains():
    assert SourceRegistry.allowlist_is_clean()
    assert not (ALLOWLISTED_DOMAINS & PERSONAL_DOMAIN_DENYLIST)
    # Every source declares public-institutional provenance (never 'personal').
    for s in SOURCE_ALLOWLIST:
        assert s.publisher_kind in {"official", "government", "academic", "ranking", "aggregator"}


async def test_registry_denies_personal_and_unlisted_urls(db_session):
    await seed_all(db_session)
    reg = SourceRegistry(db_session)
    # A personal/social URL is denied even though it's a real URL.
    denied = await reg.is_url_allowed("https://www.linkedin.com/in/some-person")
    assert not denied.allowed
    # A random unlisted domain is denied (allowlist-only, §11).
    rand = await reg.is_url_allowed("https://example-random-blog.test/page")
    assert not rand.allowed
    # A real allowlisted source is allowed.
    ok = await reg.is_url_allowed("https://www.bls.gov/ooh/computer/software-developers.htm")
    assert ok.allowed and ok.source_slug == "bls"


async def test_person_tables_stay_dormant_after_seed(db_session):
    """A full seed enriches the world but never writes a single person row."""
    await seed_all(db_session)
    insights = (
        await db_session.execute(select(func.count()).select_from(PersonInsight))
    ).scalar_one()
    personas = (
        await db_session.execute(select(func.count()).select_from(AdvisorPersona))
    ).scalar_one()
    assert insights == 0
    assert personas == 0
