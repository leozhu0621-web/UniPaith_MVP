"""Spec 60 §2 / §11 — the allowlisted source registry.

The allowlist is the governance gate the whole engine hangs off: the frontier
refuses any URL whose domain isn't on it, and the no-personal-data contract test
asserts that every registered source is a public institutional/reference
publisher — never a person or a social/individual surface.

``SOURCE_ALLOWLIST`` is a DB-free constant (the canonical policy) used by the
seeder, the transparency page, and the contract test. ``SourceRegistry`` is the
thin DB service that materializes it into ``crawl_sources`` rows and answers
allow/deny questions at runtime.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.crawler import CrawlSource


@dataclass(frozen=True)
class SourceSpec:
    slug: str
    name: str
    domain: str
    base_url: str
    publisher_kind: str  # official | government | academic | ranking | aggregator
    trust_tier: int  # 1 (highest, official bulk/API) … 4 (lowest, review-only)
    domain_tags: tuple[str, ...]
    volatility_tier: str  # news | in_cycle | watchlisted | standard | slow
    cadence_hours: int
    license: str


# The canonical allowlist (§11): public, non-personal institutional / reference
# publishers only — BLS, O*NET, IPEDS, College Scorecard, immigration agencies,
# CIP, published rankings, public scholarship DBs, .edu catalogs. No social /
# personal / individual sources ever appear here.
SOURCE_ALLOWLIST: tuple[SourceSpec, ...] = (
    SourceSpec(
        "bls",
        "U.S. Bureau of Labor Statistics",
        "bls.gov",
        "https://www.bls.gov/ooh/",
        "government",
        1,
        ("occupations", "outcomes"),
        "slow",
        8760,
        "public-domain",
    ),
    SourceSpec(
        "onet",
        "O*NET OnLine",
        "onetonline.org",
        "https://www.onetonline.org/",
        "government",
        1,
        ("occupations", "majors"),
        "slow",
        8760,
        "CC-BY-4.0",
    ),
    SourceSpec(
        "ipeds",
        "IPEDS — NCES",
        "nces.ed.gov",
        "https://nces.ed.gov/ipeds/",
        "government",
        1,
        ("institutions", "outcomes", "cost"),
        "standard",
        2160,
        "public-domain",
    ),
    SourceSpec(
        "college_scorecard",
        "College Scorecard",
        "collegescorecard.ed.gov",
        "https://collegescorecard.ed.gov/",
        "government",
        1,
        ("institutions", "cost", "outcomes", "aid"),
        "standard",
        2160,
        "public-domain",
    ),
    SourceSpec(
        "cip",
        "CIP — NCES classification",
        "nces.ed.gov",
        "https://nces.ed.gov/ipeds/cipcode/",
        "government",
        1,
        ("majors",),
        "slow",
        8760,
        "public-domain",
    ),
    SourceSpec(
        "uscis",
        "USCIS",
        "uscis.gov",
        "https://www.uscis.gov/",
        "government",
        1,
        ("visas",),
        "in_cycle",
        168,
        "public-domain",
    ),
    SourceSpec(
        "ircc",
        "Immigration, Refugees and Citizenship Canada",
        "canada.ca",
        "https://www.canada.ca/en/immigration-refugees-citizenship.html",
        "government",
        1,
        ("visas",),
        "in_cycle",
        168,
        "open-government-licence-canada",
    ),
    SourceSpec(
        "ukvi",
        "UK Visas and Immigration (GOV.UK)",
        "gov.uk",
        "https://www.gov.uk/browse/visas-immigration",
        "government",
        1,
        ("visas",),
        "in_cycle",
        168,
        "open-government-licence-uk",
    ),
    SourceSpec(
        "ets",
        "ETS (TOEFL / GRE)",
        "ets.org",
        "https://www.ets.org/",
        "official",
        2,
        ("tests",),
        "standard",
        2160,
        "proprietary-public-pages",
    ),
    SourceSpec(
        "collegeboard",
        "College Board (SAT)",
        "collegeboard.org",
        "https://www.collegeboard.org/",
        "official",
        2,
        ("tests",),
        "standard",
        2160,
        "proprietary-public-pages",
    ),
    SourceSpec(
        "ielts",
        "IELTS (British Council)",
        "ielts.org",
        "https://www.ielts.org/",
        "official",
        2,
        ("tests",),
        "standard",
        2160,
        "proprietary-public-pages",
    ),
    SourceSpec(
        "numbeo",
        "Numbeo cost-of-living index",
        "numbeo.com",
        "https://www.numbeo.com/cost-of-living/",
        "aggregator",
        3,
        ("cost",),
        "standard",
        720,
        "attribution-required",
    ),
    SourceSpec(
        "usnews_rankings",
        "U.S. News Best Colleges",
        "usnews.com",
        "https://www.usnews.com/best-colleges",
        "ranking",
        3,
        ("rankings",),
        "standard",
        2160,
        "attribution-required",
    ),
    SourceSpec(
        "qs_rankings",
        "QS World University Rankings",
        "topuniversities.com",
        "https://www.topuniversities.com/",
        "ranking",
        3,
        ("rankings",),
        "standard",
        2160,
        "attribution-required",
    ),
    SourceSpec(
        "che_accreditation",
        "U.S. Dept. of Education — accreditation database",
        "ope.ed.gov",
        "https://ope.ed.gov/dapip/",
        "government",
        1,
        ("accreditation",),
        "standard",
        2160,
        "public-domain",
    ),
    SourceSpec(
        "scholarships_gov",
        "Federal Student Aid (scholarships)",
        "studentaid.gov",
        "https://studentaid.gov/",
        "government",
        1,
        ("scholarships", "aid"),
        "in_cycle",
        336,
        "public-domain",
    ),
)

ALLOWLISTED_DOMAINS: frozenset[str] = frozenset(s.domain for s in SOURCE_ALLOWLIST)

# Domains that must never be crawled — personal / social / individual surfaces.
# The contract test (§8/§11) asserts none of these ever enters the allowlist.
PERSONAL_DOMAIN_DENYLIST: frozenset[str] = frozenset(
    {
        "facebook.com",
        "instagram.com",
        "x.com",
        "twitter.com",
        "linkedin.com",
        "tiktok.com",
        "reddit.com",
    }
)

# Reference domains the engine covers (§3). Drives the transparency page.
REFERENCE_DOMAINS: tuple[str, ...] = (
    "institutions",
    "occupations",
    "tests",
    "visas",
    "cost",
    "majors",
    "rankings",
    "accreditation",
    "outcomes",
    "scholarships",
    "aid",
)


@dataclass
class AllowDecision:
    allowed: bool
    reason: str = ""
    source_slug: str | None = field(default=None)


def domain_of(url: str) -> str:
    """Bare registrable-ish host of a URL (lowercased, no scheme / www / path)."""
    host = url.split("://", 1)[-1].split("/", 1)[0].split("?", 1)[0].lower()
    if host.startswith("www."):
        host = host[4:]
    return host


def _matches(host: str, domain: str) -> bool:
    return host == domain or host.endswith("." + domain)


class SourceRegistry:
    """DB-backed view of the allowlist. Constructed with an ``AsyncSession``."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_sources(self, *, enabled_only: bool = False) -> list[CrawlSource]:
        stmt = select(CrawlSource).order_by(CrawlSource.trust_tier, CrawlSource.name)
        if enabled_only:
            stmt = stmt.where(CrawlSource.enabled.is_(True), CrawlSource.allowlisted.is_(True))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_slug(self, slug: str) -> CrawlSource | None:
        result = await self.db.execute(select(CrawlSource).where(CrawlSource.slug == slug))
        return result.scalar_one_or_none()

    async def is_url_allowed(self, url: str) -> AllowDecision:
        """The frontier gate (§11). A URL is fetchable only if its host maps to a
        registered, enabled, allowlisted source — and never if it's on the
        personal denylist (defense in depth)."""
        host = domain_of(url)
        if any(_matches(host, bad) for bad in PERSONAL_DOMAIN_DENYLIST):
            return AllowDecision(False, "personal/social domain is denylisted")
        sources = await self.list_sources(enabled_only=True)
        for s in sources:
            if _matches(host, s.domain):
                return AllowDecision(True, "allowlisted", s.slug)
        return AllowDecision(False, "host not on the allowlist")

    @staticmethod
    def allowlist_is_clean() -> bool:
        """Static invariant for the contract test: no allowlisted source is a
        personal/social domain."""
        return not (ALLOWLISTED_DOMAINS & PERSONAL_DOMAIN_DENYLIST)
