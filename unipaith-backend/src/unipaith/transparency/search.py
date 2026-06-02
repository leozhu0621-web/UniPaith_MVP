"""Spec 56 — Search, Feed & Recommendations, as queryable data.

Spec 56 is the discovery substrate: full-text + semantic search, faceted
filters, the ranked Connect feed, recommendations, and saved-search alerts. The
spec is explicit that it's *"mostly wiring + extending real modules, plus
building saved-searches"* — so this module turns that honest live/partial/planned
posture into the payload behind ``GET /build/search`` and the ``/goal/search``
page, the same way ``transparency.production`` does for spec 55.

Self-verifying hooks (read live from the running app, never asserted in prose):

- the **backing-route counts** (search / feed / saved-search / events) are
  resolved from the live route table, so the page can only claim a surface the
  deployed app actually serves;
- the **saved-searches table presence** is read from the running SQLAlchemy
  metadata — the page can't claim the feature shipped unless the table is wired;
- the **config knobs** (the NL-interpreter + connect-ranker flags and the new
  saved-search alert caps) are read straight off ``settings``.

The narrative (capabilities, their built/planned split, the §8 checklist, the §9
acceptance, the §10 open questions) is authored from spec 56; each item is
honestly classified ``live`` / ``partial`` / ``planned``. The embedding-dependent
halves (pgvector fusion, Qwen3-Reranker, A/B harness) are marked ``planned`` with
the scaffold that anticipates them as evidence — exactly like the roadmap's
deferred phase. DB-free and unauthenticated.
"""

from __future__ import annotations

from dataclasses import dataclass

from unipaith.config import settings
from unipaith.models.base import Base

API_PREFIX = "/api/v1"
_SKIP_METHODS = {"HEAD", "OPTIONS"}

Status = str  # "live" | "partial" | "planned"


# ── §1 · The bar ────────────────────────────────────────────────────────────
THE_BAR: dict = {
    "statement": (
        "Discovery is good when a student can describe what they want in their "
        "own words and get back relevant programs, refine with live filters, "
        "follow institutions and see what changed, and save a search that keeps "
        "watching for them — with every ranking explainable and fairness-gated."
    ),
    "principle": (
        "Built on the real substrate that already exists — Postgres FTS, the "
        "constraint-chip interpreter, the Connect feed ranker — extended where "
        "the spec calls for it, with saved-search alerts as the net-new payoff."
    ),
}


# ── §2–§7 · Capabilities ─────────────────────────────────────────────────────
@dataclass(frozen=True)
class Capability:
    key: str
    title: str
    section: str  # spec 56 section, e.g. "§2"
    status: Status
    blurb: str
    built: tuple[str, ...]  # what is live today
    planned: tuple[str, ...]  # the gap, honestly named


CAPABILITIES: tuple[Capability, ...] = (
    Capability(
        "fts",
        "Full-text search",
        "§2",
        "live",
        "Postgres FTS over programs — cheap, no new infra.",
        (
            "tsvector + plainto_tsquery over program/institution text "
            "(InstitutionService.search_programs)",
            "Constraint chips → additive filter kwargs (SearchService)",
            "Match-aware sort (fitness / confidence) layered over relevance",
            "Sort by relevance / tuition / acceptance / deadline / recency",
        ),
        (
            "pg_trgm fuzzy ranking for typo tolerance",
            "GIN index audit on the search columns (55 §7)",
        ),
    ),
    Capability(
        "nl_interpret",
        "Natural-language query",
        "§2",
        "live",
        "Type a sentence; get structured constraint chips.",
        (
            "Rule-based parser → chips, always on (query_parser.py)",
            "LLM interpreter behind ai_discovery_query_v2_enabled (query_interpreter.py)",
            "Graceful fallback to the rule-based path — never 5xx (50 §6)",
            "POST /students/me/search/interpret",
        ),
        (
            "Qwen3 interpreter served per 63 (today: Claude / rule-based)",
            "Constraint-chip edit handshake refinements (10)",
        ),
    ),
    Capability(
        "facets",
        "Faceted filters",
        "§3",
        "partial",
        "The full filter object exists; live counts are the gap.",
        (
            "Degree / modality / location / cost / duration / selectivity / "
            "outcomes filters (FilterState)",
            "Filter state serializable for the URL (05 §13 / 54 §2)",
            "Panel filters win over chip-derived values",
        ),
        (
            "Live facet counts ({facet: [{value, count}]}) computed alongside results",
            "Toggle-updates-counts handshake bar (53)",
        ),
    ),
    Capability(
        "hybrid",
        "Hybrid semantic fusion",
        "§2B",
        "planned",
        "Semantic recall fused with keyword precision — depends on 63.",
        (
            "Reranker scaffold staged as stage-3 of the matching stack (reranker.py)",
            "pgvector available in the database",
        ),
        (
            "Qwen embeddings + pgvector ANN over the embeddings table (63 §8)",
            "Reciprocal-rank fusion of keyword + semantic in SearchService",
            "Qwen3-Reranker final precision pass",
        ),
    ),
    Capability(
        "feed",
        "Connect feed ranking",
        "§4",
        "live",
        "Reverse-chron or relevance-ranked feed from followed institutions.",
        (
            "Deterministic relevance heuristic: applied > saved > followed > "
            "recency (ConnectService._order_relevant)",
            "Deadline reminders + program-change items + mute (20 / 60 §3B)",
            "Optional AI rerank behind ai_connect_ranker_v2_enabled (connect_ranker.py)",
            "GET /connect/feed?rank=recent|relevant",
        ),
        (
            "Config-tunable weighted blend (recency·w + relevance·w + "
            "materiality·w + engagement·w)",
            "Cursor pagination + “new posts” pill + seen-state (interaction_signals)",
        ),
    ),
    Capability(
        "recs",
        "Recommendations",
        "§5",
        "partial",
        "The rec inputs are live; the explainable rec surface is the gap.",
        (
            "Event recommender (event_recommender.py)",
            "Net-price + match-banding rec inputs (net_price_service / match_banding)",
            "Eligibility-aware scholarship inputs (60 §5.1)",
        ),
        (
            "“Programs like this” + “students with your goals applied to…” endpoints",
            "One-line explainable why per rec (07 §2), fairness-gated (46 §6)",
        ),
    ),
    Capability(
        "saved_search",
        "Saved searches + alerts",
        "§6",
        "live",
        "The net-new build — save a search; it keeps watching.",
        (
            "saved_searches table + model (migration s56a1b2c3d4e)",
            "CRUD + run-now API (/students/me/saved-searches)",
            "Scheduled alert loop on new matches (core/scheduler.py)",
            "Consent-gated (consent_outreach) + per-user-per-day cap + max-per-user",
            "In-app + email delivery via NotificationService (pairs with 57)",
        ),
        (
            "Scholarship / school entity search (program is wired today)",
            "Per-field price / deadline change detection (depends on 60 / 63)",
        ),
    ),
    Capability(
        "experimentation",
        "Relevance experimentation",
        "§7",
        "planned",
        "A/B-test ranking variants and promote on win — depends on 62.",
        ("Ranking variants already gated behind config (no redeploy to flip)",),
        (
            "ab_test_assignments wiring (62 harness)",
            "Measure click / save / apply lift; promote the winner",
        ),
    ),
)


# ── §8 · Build-task checklist ───────────────────────────────────────────────
@dataclass(frozen=True)
class BuildTask:
    section: str
    status: Status
    text: str
    evidence: str


BUILD_TASKS: tuple[BuildTask, ...] = (
    BuildTask(
        "§8",
        "partial",
        "FTS + trgm with facet aggregates + GIN indexes",
        "FTS is live in search_programs; trgm + facet counts + GIN audit are planned.",
    ),
    BuildTask(
        "§8",
        "planned",
        "Hybrid fusion (pgvector + keyword RRF) + reranker → Qwen3-Reranker",
        "Reranker scaffold exists; embeddings + fusion depend on 63.",
    ),
    BuildTask(
        "§8",
        "live",
        "query_interpreter → chips, with query_parser rule-based fallback",
        "Both wired; SearchService.interpret falls back on any AI failure.",
    ),
    BuildTask(
        "§8",
        "partial",
        "Formalize connect_ranker blended score + config weights; cursor feed",
        "Heuristic + optional AI rerank are live; weighted-config + cursor are planned.",
    ),
    BuildTask(
        "§8",
        "partial",
        "Rec endpoints with explainable why + fairness gate",
        "Rec inputs (event/net-price/banding) live; explainable endpoints are planned.",
    ),
    BuildTask(
        "§8",
        "live",
        "saved_searches table/model/service + alert job + endpoints + caps",
        "Built here: model + migration + service + API + scheduler loop + consent/caps.",
    ),
    BuildTask(
        "§8",
        "planned",
        "A/B hooks for ranking variants via 62",
        "Variants are config-gated; the ab_test harness wiring is planned.",
    ),
)


# ── §9 · Acceptance ─────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Acceptance:
    status: Status
    text: str


ACCEPTANCE: tuple[Acceptance, ...] = (
    Acceptance(
        "partial",
        "Search returns results with typeahead + faceted live counts; state in URL.",
    ),
    Acceptance(
        "partial",
        "Feed ranked, infinite-scroll, optimistic react/RSVP, “new posts” pill, seen-state.",
    ),
    Acceptance("partial", "Recs explainable + fairness-gated (46)."),
    Acceptance("live", "Saved searches fire alerts via 57, consent + cap respected."),
    Acceptance("planned", "Ranking changes A/B-gated via 62; no redeploy to flip a variant."),
)


# ── §10 · Open questions ────────────────────────────────────────────────────
OPEN_QUESTIONS: tuple[dict, ...] = (
    {
        "q": "OpenSearch trigger threshold",
        "a": "Stay on Postgres FTS until program count / query volume measurably "
        "demand faceting at scale.",
    },
    {
        "q": "Cold-start recs (sparse new profile)",
        "a": "Fall back to popularity + stated intent (42 intent signals) until the "
        "profile is rich enough to embed.",
    },
    {
        "q": "Does search compute facet counts yet?",
        "a": "No — SearchService delegates to the FTS engine, which returns results "
        "without per-facet aggregates. Documented as the facets gap (partial).",
    },
)


def _route_buckets(routes) -> dict[str, list[str]]:
    """Resolve the live API paths backing each surface from the running routes —
    so the page can't claim a surface the deployed app doesn't serve. Note
    ``/saved-searches`` contains the substring ``search``; it's bucketed first
    and excluded from the keyword-search bucket."""
    buckets: dict[str, set[str]] = {
        "saved_search": set(),
        "search": set(),
        "feed": set(),
        "events": set(),
    }
    for r in routes:
        path = getattr(r, "path", "")
        methods = getattr(r, "methods", None)
        if not path.startswith(API_PREFIX) or not methods:
            continue
        if all(m in _SKIP_METHODS for m in methods):
            continue
        if "/saved-searches" in path:
            buckets["saved_search"].add(path)
        elif "/search/" in path or path.endswith("/compare") or "/compare/" in path:
            buckets["search"].add(path)
        elif "/connect" in path:
            buckets["feed"].add(path)
        elif path.startswith(f"{API_PREFIX}/events") or "/me/events" in path:
            # Event-discovery surfaces only — not institution-side ai-surface
            # instrumentation that happens to contain the word "events".
            buckets["events"].add(path)
    return {k: sorted(v) for k, v in buckets.items()}


def _config_knobs() -> list[dict]:
    """The live config knobs the page reports, read straight off ``settings``."""
    return [
        {
            "name": "ai_discovery_query_v2_enabled",
            "value": settings.ai_discovery_query_v2_enabled,
            "section": "§2",
        },
        {
            "name": "ai_connect_ranker_v2_enabled",
            "value": settings.ai_connect_ranker_v2_enabled,
            "section": "§4",
        },
        {
            "name": "saved_search_alerts_enabled",
            "value": settings.saved_search_alerts_enabled,
            "section": "§6",
        },
        {
            "name": "saved_search_alert_interval_minutes",
            "value": settings.saved_search_alert_interval_minutes,
            "section": "§6",
        },
        {
            "name": "saved_search_alert_cap_per_day",
            "value": settings.saved_search_alert_cap_per_day,
            "section": "§6",
        },
        {
            "name": "saved_search_max_per_user",
            "value": settings.saved_search_max_per_user,
            "section": "§6",
        },
    ]


def build_search(app_or_routes) -> dict:
    """Assemble the ``GET /build/search`` payload.

    ``app_or_routes`` may be a FastAPI app or its ``.routes`` — the route buckets
    are resolved live so the page mirrors what the deployed app serves. The
    saved-searches table presence is read from the running SQLAlchemy metadata.
    """
    routes = getattr(app_or_routes, "routes", app_or_routes)
    route_buckets = _route_buckets(list(routes))
    config_knobs = _config_knobs()
    saved_searches_table_present = "saved_searches" in Base.metadata.tables

    def _count(status: Status) -> int:
        return sum(1 for c in CAPABILITIES if c.status == status)

    def _task_count(status: Status) -> int:
        return sum(1 for t in BUILD_TASKS if t.status == status)

    def _acc_count(status: Status) -> int:
        return sum(1 for a in ACCEPTANCE if a.status == status)

    backing_route_count = sum(len(v) for v in route_buckets.values())

    return {
        "the_bar": dict(THE_BAR),
        "summary": {
            "capability_count": len(CAPABILITIES),
            "capabilities_live": _count("live"),
            "capabilities_partial": _count("partial"),
            "capabilities_planned": _count("planned"),
            "build_task_count": len(BUILD_TASKS),
            "tasks_live": _task_count("live"),
            "tasks_partial": _task_count("partial"),
            "tasks_planned": _task_count("planned"),
            "acceptance_count": len(ACCEPTANCE),
            "acceptance_live": _acc_count("live"),
            "search_route_count": len(route_buckets["search"]),
            "feed_route_count": len(route_buckets["feed"]),
            "saved_search_route_count": len(route_buckets["saved_search"]),
            "backing_route_count": backing_route_count,
            "saved_searches_table_present": saved_searches_table_present,
            "config_knob_count": len(config_knobs),
            "open_question_count": len(OPEN_QUESTIONS),
            "live_is_source_of_truth": True,
        },
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
        "build_tasks": [
            {"section": t.section, "status": t.status, "text": t.text, "evidence": t.evidence}
            for t in BUILD_TASKS
        ],
        "acceptance": [{"status": a.status, "text": a.text} for a in ACCEPTANCE],
        "config_knobs": config_knobs,
        "routes": route_buckets,
        "saved_searches_table_present": saved_searches_table_present,
        "open_questions": [dict(q) for q in OPEN_QUESTIONS],
    }
