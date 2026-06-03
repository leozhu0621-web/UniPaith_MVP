"""Spec 60 — Data Crawler & Knowledge-Base Engine, as queryable data.

Turns spec 60's honest live/partial/planned posture into the payload behind
``GET /build/knowledge`` and the ``/goal/knowledge`` page, the same way
``transparency.search`` does for spec 56.

Self-verifying hooks (read live from the running app, never asserted in prose):

- the **backing-route counts** (reference / crawler-ops / enrichment-review) are
  resolved from the live route table — the page can only claim a surface the
  deployed app serves;
- the **reference-table presence** is read from the running SQLAlchemy metadata —
  the page can't claim a domain whose table isn't wired;
- the **registered-source count** is read from the static §11 allowlist policy;
- the **config knobs** (extraction flag, live-fetch gate, allowlist-only, auto-
  apply floors, change-event cap) are read straight off ``settings``.

The narrative — the Kollegio benchmark (§1A), the reference graph (§3), the 7-stage
pipeline (§6), the change-event taxonomy (§3B), the provenance & authority ladder
(§4/§8), the §14 phasing, the §15 acceptance, the §16 open questions — is authored
from spec 60; each capability is honestly classified ``live`` / ``partial`` /
``planned``. DB-free and unauthenticated.
"""

from __future__ import annotations

from dataclasses import dataclass

from unipaith.config import settings
from unipaith.models.base import Base
from unipaith.services.crawler.sources import REFERENCE_DOMAINS, SOURCE_ALLOWLIST

API_PREFIX = "/api/v1"
_SKIP_METHODS = {"HEAD", "OPTIONS"}
Status = str  # "live" | "partial" | "planned"


# ── §1 · The bar ────────────────────────────────────────────────────────────
THE_BAR: dict = {
    "statement": (
        "The platform should reason against a rich, current, source-cited picture "
        "of the world — real salaries behind a career goal, real score ranges "
        "behind a test, real requirements behind a visa, real cost behind a budget "
        "— not just the sparse data an institution typed in."
    ),
    "principle": (
        "Public, non-personal reference data only. Provenance on every fact; "
        "verified first-party data always wins; nothing is ever fabricated — "
        "not-found stays empty, low-confidence goes to review."
    ),
}


# ── §1A · Competitive benchmark (the asset) ─────────────────────────────────
@dataclass(frozen=True)
class Benchmark:
    dimension: str
    kollegio: str
    gap: str
    unipaith: str


KOLLEGIO_BENCHMARK: tuple[Benchmark, ...] = (
    Benchmark(
        "Provenance",
        "Matches on data points; no published provenance",
        "opaque numbers",
        "Provenance on every fact (§4/§7)",
    ),
    Benchmark(
        "Freshness",
        "Static ~1,650-school snapshot",
        "drifts stale",
        "Scheduled re-crawl + change detection + decay (§10)",
    ),
    Benchmark(
        "Coverage",
        "US undergrad only",
        "no international/grad/career/cost",
        "Full reference graph — careers, tests, visas, cost, majors (§3)",
    ),
    Benchmark(
        "Authority",
        "Student-only, scraped not authoritative",
        "schools can't correct",
        "Two-sided claim & verify; first-party wins (23 / §8/§9)",
    ),
    Benchmark(
        "Depth",
        "Shallow reference numbers",
        "net price / visa / salary thin",
        "World-reference tables feed computed OUTPUT features (§5.2)",
    ),
    Benchmark(
        "Ground truth",
        "Static fine-tuned advice",
        "no live ground truth",
        "A live ground-truth graph the engine reasons against",
    ),
)


# ── §3 · Reference graph ────────────────────────────────────────────────────
@dataclass(frozen=True)
class RefDomain:
    key: str
    title: str
    section: str
    table: str
    sources: str
    feeds: str


REFERENCE_GRAPH: tuple[RefDomain, ...] = (
    RefDomain(
        "occupations",
        "Careers & occupations",
        "§3.1",
        "ref_occupations",
        "BLS · O*NET",
        "Career alignment + outcome preview",
    ),
    RefDomain(
        "tests",
        "Standardized tests",
        "§3.2",
        "ref_tests",
        "ETS · College Board · IELTS",
        "Test compatibility / superscore",
    ),
    RefDomain(
        "visas",
        "Visa & immigration",
        "§3.3",
        "ref_visas",
        "USCIS · IRCC · UKVI",
        "Visa feasibility band (42 §4.3) · serves 38",
    ),
    RefDomain(
        "cost",
        "Cost of living & geography",
        "§3.4",
        "ref_geo_cost",
        "Numbeo · IPEDS",
        "Net-cost / affordability",
    ),
    RefDomain(
        "majors",
        "Majors & curriculum",
        "§3.5",
        "ref_majors",
        "CIP · catalogs",
        "Major-track fit + prereq gaps",
    ),
    RefDomain(
        "rankings",
        "Rankings",
        "§3.6",
        "ref_rankings",
        "U.S. News · QS",
        "Shown as 'reported by <ranker>, <year>'",
    ),
    RefDomain(
        "accreditation",
        "Accreditation",
        "§3.6",
        "ref_accreditation",
        "USDE DAPIP · ABET · AACSB",
        "Accreditation status by body",
    ),
    RefDomain(
        "scholarships",
        "Scholarships",
        "§5.1",
        "scholarships",
        "Federal Student Aid · external",
        "Aid likelihood band + net price (09/11)",
    ),
)


# ── §6 · Pipeline ───────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Stage:
    n: int
    name: str
    detail: str


PIPELINE_STAGES: tuple[Stage, ...] = (
    Stage(0, "Source registry", "Allowlisted sources + policy (trust tier, cadence, robots)."),
    Stage(1, "Discover", "Frontier — priority from interaction signals; self-expansion."),
    Stage(2, "Fetch", "Robots + delay + conditional GET; unchanged hash → skip (idempotent)."),
    Stage(3, "Extract", "SourceExtractionAgent — grounded, schema-strict, never invents."),
    Stage(4, "Normalize", "Units / SOC / CIP / CEFR / currency / grading scale."),
    Stage(5, "Resolve", "Link facts → canonical knowledge_entities + raw-graph links."),
    Stage(6, "Enrich-write", "Confidence-gated; conflict / low-trust → review (§7/§8)."),
)


# ── §3B · Change-event taxonomy ─────────────────────────────────────────────
CHANGE_EVENT_TYPES: tuple[dict, ...] = (
    {"type": "deadline_moved", "materiality": "high", "routes_to": "notifications + saved-search"},
    {"type": "new_scholarship", "materiality": "high", "routes_to": "Connect feed + notifications"},
    {"type": "policy_change", "materiality": "high", "routes_to": "feed (visa / test-optional)"},
    {"type": "program_added", "materiality": "medium", "routes_to": "Connect feed"},
    {"type": "program_closed", "materiality": "high", "routes_to": "notifications"},
    {"type": "cost_change", "materiality": "medium", "routes_to": "saved-search + feed"},
    {"type": "ranking_update", "materiality": "medium", "routes_to": "feed"},
    {"type": "stat_update", "materiality": "low", "routes_to": "batched / suppressed"},
)


# ── §4 / §8 · Provenance & authority ────────────────────────────────────────
AUTHORITY_LADDER: tuple[dict, ...] = (
    {
        "rank": 1,
        "source": "institution_verified",
        "note": "Institution claim & verify (23) — the ceiling.",
    },
    {"rank": 2, "source": "first_party", "note": "Supplied by the entity itself."},
    {
        "rank": 3,
        "source": "corroborated",
        "note": "≥2 trusted crawled sources agree — may auto-apply.",
    },
    {
        "rank": 4,
        "source": "seed / single high-trust crawl",
        "note": "Official bulk; applies above the confidence floor.",
    },
    {"rank": 5, "source": "single low-trust crawl", "note": "Review only — never auto-applies."},
)


# ── §2–§13 · Capabilities ────────────────────────────────────────────────────
@dataclass(frozen=True)
class Capability:
    key: str
    title: str
    section: str
    status: Status
    blurb: str
    built: tuple[str, ...]
    planned: tuple[str, ...]


CAPABILITIES: tuple[Capability, ...] = (
    Capability(
        "registry",
        "Allowlisted source registry",
        "§2 · §11",
        "live",
        "Only registered, allowlisted, domain-tagged sources are ever fetched.",
        (
            "crawl_sources registry + policy (trust tier, cadence, robots)",
            "16-source §11 allowlist seeded (BLS / O*NET / IPEDS / USCIS / CIP / …)",
            "Frontier gate refuses any host off the allowlist (+ personal denylist)",
            "GET /crawler/sources · GET /crawler/allowlist (system-guarded)",
        ),
        ("Per-source robots.txt live fetch (only when live-fetch is enabled)",),
    ),
    Capability(
        "skeleton",
        "Knowledge graph (dormant skeleton, now wired)",
        "§2 · §16",
        "live",
        "The previously-dormant knowledge tables are wired; the §16 entity node added.",
        (
            "knowledge_entities added (the §16 missing migration)",
            "knowledge_documents / knowledge_links carry the raw graph",
            "Entity resolver links facts → canonical entity + document",
        ),
        ("Embedding/pgvector indexing of the document graph (depends on 63)",),
    ),
    Capability(
        "reference",
        "Reference projection",
        "§3 · §5.2",
        "live",
        "Typed, normalized, provenance-carrying tables for every hot domain.",
        (
            "8 reference tables: occupations / tests / visas / cost / majors / "
            "rankings / accreditation / scholarships",
            "reference_entities for the generic long-tail",
            "Curated, source-cited seed dataset (Tier-1 structured bulk, §6)",
            "GET /reference/* — public reads with provenance on every row",
        ),
        ("Breadth — seed is a curated core; full-coverage crawl is Phase C",),
    ),
    Capability(
        "extraction",
        "Grounded extraction (never invents)",
        "§13 · §13B",
        "live",
        "Schema-strict, grounded extraction; a field absent from the source is never written.",
        (
            "SourceExtractionAgent — per-domain templates + per-field confidence",
            "Structured (Tier-1) + free-text (Tier-3) paths, both grounding-verified",
            "Deterministic default; verify_grounded enforced before any write",
        ),
        (
            "Qwen/Claude extractor behind ai_crawler_extraction_v2_enabled (63)",
            "Extraction eval harness — precision/recall/F1, CI-gated (62 §13B)",
        ),
    ),
    Capability(
        "provenance",
        "Provenance & authority write-path",
        "§4 · §7 · §8",
        "live",
        "Every crawled field is one reversible audit row; first-party never overwritten.",
        (
            "entity_enrichments — reversible per-field audit (source / confidence)",
            "Authority ladder: institution-verified > first-party > corroborated > "
            "single high-trust > single low-trust (review)",
            "Cross-source corroboration raises confidence; ≥2 trusted → auto-apply",
            "Conflict with verified data → review, prior value preserved",
        ),
        (),
    ),
    Capability(
        "idempotent",
        "Idempotent pipeline",
        "§6",
        "live",
        "Unchanged content does no parse and no write.",
        (
            "Content-hash conditional GET; (source_url, hash) dedup",
            "engine_loop_snapshot tick metrics (queue depth, processed, errors)",
        ),
        ("Per-field semantic diff via the LLM (today: value-equality diff)",),
    ),
    Capability(
        "proactive",
        "Proactive change detection & routing",
        "§3B",
        "live",
        "Detected, materiality-classified changes routed to the students who care.",
        (
            "change_events — change_type + materiality + confidence, traces to a source",
            "Routes to followers/savers/appliers via interaction signals + follows",
            "Consent-gated (consent_outreach) + per-user-per-day cap, deduped",
            "Pairs with the Connect feed (20), notifications (57), saved-search (56)",
        ),
        (
            "Autonomous discovery — frontier self-expansion + gap-fill loop",
            "Volatility-tiered live re-crawl (needs live fetch on)",
        ),
    ),
    Capability(
        "governance",
        "Two-sided governance",
        "§9",
        "live",
        "No platform-admin tier — institution claim & verify + a system ops queue.",
        (
            "Institution enrichment-review at /institutions/me/enrichments (claim & verify)",
            "System-guarded ops review queue (/crawler/review-queue)",
            "All actions auditable; person tables stay dormant (§1/§11)",
        ),
        ("Student 'report incorrect' → re-crawl directive (50 surface hook)",),
    ),
    Capability(
        "scheduling",
        "Freshness & scheduling",
        "§10",
        "partial",
        "Volatility-tiered cadence on the 55 scheduler; live re-crawl needs fetch on.",
        (
            "Per-source volatility tier + cadence_hours in the registry",
            "engine.tick() on the scheduler (flag-gated), writes the snapshot",
        ),
        (
            "Live conditional re-crawl loop (crawler_live_fetch_enabled off by default)",
            "Decay/TTL re-queue of stale entities",
        ),
    ),
    Capability(
        "feeds_output",
        "Feeds the OUTPUT features",
        "§5 · §15",
        "live",
        "The reference projection is consumed by the OUTPUT features, with provenance.",
        (
            "Cost-of-living (ref_geo_cost) feeds net-price COA — a sourced living "
            "figure replaces the hardcoded default (NetPriceService)",
            "Reference reads carry provenance for the editorial components (11/12)",
            "Visa ref + scholarships exposed with provenance for the visa-band (38/42) "
            "and aid-likelihood (09/11) surfaces to consume",
        ),
        ("Deeper per-field wiring (visa-band compute, aid-band corroboration) — incremental",),
    ),
    Capability(
        "chatbot",
        "RAG chatbot over the graph",
        "model note · 61",
        "planned",
        "Claude answers questions about the Qwen-embedded knowledge graph.",
        ("The graph + provenance this RAG needs is built here",),
        ("Retrieval + the conversational layer ship in 61",),
    ),
)


# ── §14 · Phasing ───────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Phase:
    key: str
    title: str
    status: Status
    detail: str


PHASES: tuple[Phase, ...] = (
    Phase(
        "A",
        "Institutional core",
        "live",
        "schools/programs/scholarships + entity_enrichments + knowledge_entities; review-all.",
    ),
    Phase(
        "B",
        "Student-facing reference",
        "live",
        "careers / tests / visas / cost / majors — typed tables + provenance reads.",
    ),
    Phase(
        "C",
        "Long tail + auto-apply + proactive",
        "partial",
        "rankings/accreditation + confidence-gated auto-apply + change-event routing (built); "
        "live re-crawl + autonomous discovery gated off until enabled per-env.",
    ),
)


# ── §15 · Acceptance ────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Acceptance:
    status: Status
    text: str


ACCEPTANCE: tuple[Acceptance, ...] = (
    Acceptance(
        "live", "Only registered/allowlisted, domain-tagged sources fetched; robots/rate honored."
    ),
    Acceptance(
        "live", "Each domain: source set + extraction schema + normalized table + provenance."
    ),
    Acceptance(
        "live", "Crawled facts appear provisional + source-cited + confidence in the surface."
    ),
    Acceptance(
        "live", "Reference data feeds the OUTPUT features (cost → net-price; visa/aid exposed)."
    ),
    Acceptance("live", "First-party never overwritten by crawl (conflict → review)."),
    Acceptance("live", "Unchanged content → no parse/write (idempotent)."),
    Acceptance(
        "live", "change_events detected, materiality-classified, routed to affected students."
    ),
    Acceptance(
        "live", "No personal/individual data gathered (contract test); all actions audited."
    ),
    Acceptance(
        "live", "Extraction never writes a field absent from source (no fabrication), every domain."
    ),
)


# ── §16 · Open questions ────────────────────────────────────────────────────
OPEN_QUESTIONS: tuple[dict, ...] = (
    {
        "q": "knowledge_entities migration",
        "a": "Added here — the §16 table the skeleton referenced but never migrated.",
    },
    {
        "q": "Typed vs generic reference tables",
        "a": "Typed for the 8 hot domains; reference_entities for the long tail.",
    },
    {
        "q": "Auto-apply threshold",
        "a": "Review-all for low-trust; ≥2 trusted sources at ≥0.75 confidence "
        "may auto-apply (config-tunable).",
    },
    {
        "q": "Reference TTL per domain",
        "a": "Volatility tier per source: news hourly–daily, standard monthly, "
        "occupations annually.",
    },
    {
        "q": "People-data line",
        "a": "advisor_personas / person_insights stay dormant; a personal-domain "
        "denylist backs the contract test.",
    },
    {
        "q": "Pre-pivot admin crawler",
        "a": "Confirmed not re-enabled — the new engine is built fresh on the "
        "dormant skeleton (§2).",
    },
)


def _route_buckets(routes) -> dict[str, list[str]]:
    buckets: dict[str, set[str]] = {"reference": set(), "crawler_ops": set(), "enrichment": set()}
    for r in routes:
        path = getattr(r, "path", "")
        methods = getattr(r, "methods", None)
        if not path.startswith(API_PREFIX) or not methods:
            continue
        if all(m in _SKIP_METHODS for m in methods):
            continue
        if "/enrichments" in path:
            buckets["enrichment"].add(path)
        elif path.startswith(f"{API_PREFIX}/reference"):
            buckets["reference"].add(path)
        elif path.startswith(f"{API_PREFIX}/crawler"):
            buckets["crawler_ops"].add(path)
    return {k: sorted(v) for k, v in buckets.items()}


def _config_knobs() -> list[dict]:
    return [
        {
            "name": "ai_crawler_extraction_v2_enabled",
            "value": settings.ai_crawler_extraction_v2_enabled,
            "section": "§13",
        },
        {
            "name": "crawler_engine_enabled",
            "value": settings.crawler_engine_enabled,
            "section": "§10",
        },
        {
            "name": "crawler_live_fetch_enabled",
            "value": settings.crawler_live_fetch_enabled,
            "section": "§11",
        },
        {
            "name": "crawler_allowlist_only",
            "value": settings.crawler_allowlist_only,
            "section": "§11",
        },
        {
            "name": "crawler_auto_apply_min_sources",
            "value": settings.crawler_auto_apply_min_sources,
            "section": "§7",
        },
        {
            "name": "crawler_auto_apply_min_confidence",
            "value": settings.crawler_auto_apply_min_confidence,
            "section": "§7",
        },
        {
            "name": "change_event_route_cap_per_user_per_day",
            "value": settings.change_event_route_cap_per_user_per_day,
            "section": "§3B",
        },
        {
            "name": "change_event_min_materiality_to_route",
            "value": settings.change_event_min_materiality_to_route,
            "section": "§3B",
        },
    ]


_REF_TABLES = (
    "ref_occupations",
    "ref_tests",
    "ref_visas",
    "ref_geo_cost",
    "ref_majors",
    "ref_rankings",
    "ref_accreditation",
    "scholarships",
    "reference_entities",
)
_ENGINE_TABLES = ("crawl_sources", "knowledge_entities", "entity_enrichments", "change_events")


def build_knowledge(app_or_routes) -> dict:
    """Assemble the ``GET /build/knowledge`` payload. ``app_or_routes`` may be a
    FastAPI app or its ``.routes`` — buckets and table presence resolve live."""
    routes = getattr(app_or_routes, "routes", app_or_routes)
    route_buckets = _route_buckets(list(routes))
    config_knobs = _config_knobs()
    tables = set(Base.metadata.tables)
    ref_tables_present = sum(1 for t in _REF_TABLES if t in tables)
    engine_tables_present = sum(1 for t in _ENGINE_TABLES if t in tables)

    def _count(status: Status) -> int:
        return sum(1 for c in CAPABILITIES if c.status == status)

    def _acc(status: Status) -> int:
        return sum(1 for a in ACCEPTANCE if a.status == status)

    backing_route_count = sum(len(v) for v in route_buckets.values())

    return {
        "the_bar": dict(THE_BAR),
        "summary": {
            "capability_count": len(CAPABILITIES),
            "capabilities_live": _count("live"),
            "capabilities_partial": _count("partial"),
            "capabilities_planned": _count("planned"),
            "acceptance_count": len(ACCEPTANCE),
            "acceptance_live": _acc("live"),
            "acceptance_partial": _acc("partial"),
            "reference_domain_count": len(REFERENCE_GRAPH),
            "registered_source_count": len(SOURCE_ALLOWLIST),
            "reference_tables_present": ref_tables_present,
            "engine_tables_present": engine_tables_present,
            "pipeline_stage_count": len(PIPELINE_STAGES),
            "change_event_type_count": len(CHANGE_EVENT_TYPES),
            "reference_route_count": len(route_buckets["reference"]),
            "ops_route_count": len(route_buckets["crawler_ops"]),
            "backing_route_count": backing_route_count,
            "config_knob_count": len(config_knobs),
            "open_question_count": len(OPEN_QUESTIONS),
            "live_is_source_of_truth": True,
        },
        "benchmark": [
            {"dimension": b.dimension, "kollegio": b.kollegio, "gap": b.gap, "unipaith": b.unipaith}
            for b in KOLLEGIO_BENCHMARK
        ],
        "reference_graph": [
            {
                "key": d.key,
                "title": d.title,
                "section": d.section,
                "table": d.table,
                "sources": d.sources,
                "feeds": d.feeds,
                "table_present": d.table in tables,
            }
            for d in REFERENCE_GRAPH
        ],
        "pipeline": [{"n": s.n, "name": s.name, "detail": s.detail} for s in PIPELINE_STAGES],
        "change_event_types": [dict(c) for c in CHANGE_EVENT_TYPES],
        "authority_ladder": [dict(a) for a in AUTHORITY_LADDER],
        "capabilities": [
            {
                "key": c.key,
                "title": c.title,
                "section": c.section,
                "status": c.status,
                "blurb": c.blurb,
                "built": list(c.built),
                "planned": list(c.planned),
            }
            for c in CAPABILITIES
        ],
        "phases": [
            {"key": p.key, "title": p.title, "status": p.status, "detail": p.detail} for p in PHASES
        ],
        "acceptance": [{"status": a.status, "text": a.text} for a in ACCEPTANCE],
        "config_knobs": config_knobs,
        "routes": route_buckets,
        "reference_domains": list(REFERENCE_DOMAINS),
        "open_questions": [dict(q) for q in OPEN_QUESTIONS],
    }
