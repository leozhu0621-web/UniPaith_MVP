"""Spec 54 — the frontend-engineering build spec, as queryable data.

Spec 54 turns the v1 frontend "standards" into a *build* spec against the real
React 19 + Vite + Tailwind + Zustand + TanStack-Query tree: concrete file
contracts, the state-layering rules, the query-key + optimistic-mutation
conventions, performance budgets, the realtime + analytics clients to build, and
a §12 build-task checklist. This module turns that spec into the payload behind
``GET /build/frontend-standards`` and the ``/goal/frontend`` page — the same way
``transparency.ux_benchmark`` turns spec 53 into ``/goal/experience``.

The self-verifying hook — the §5 *api-module ↔ router parity* contract:
spec 54 §5 says every typed ``api/<domain>.ts`` module maps to a backend router.
The backend half of that contract is **resolved live from the running route
table** (via :func:`build_api_contract`), so the page can show the real
``router_count`` / ``route_count`` it actually serves — never a number asserted
in prose. The frontend half is counted just as honestly: the page reads its own
``import.meta.glob`` of ``api/*.ts`` at build time. Both ends self-count; the
page renders the parity. The narrative (the rules, the budgets, the build-task
*status*) is authored from spec 54 and this PR, and labeled as such.

DB-free and unauthenticated, like its sibling ``/build/*`` modules — it exposes
only build *architecture*, never user data.
"""

from __future__ import annotations

from dataclasses import dataclass

from unipaith.transparency.api_contract import build_api_contract

# Spec 54 §1/§5 was drafted against an earlier tree (2026-05-30). The doc cites
# "37 api modules ↔ 22 routers, 6 stores, 3 hooks"; the live tree has grown
# (the page shows the live counts beside these so the drift is explicit).
DOC_CLAIMED_API_MODULES = 37
DOC_CLAIMED_ROUTERS = 22
DOC_CLAIMED_STORES = 6
DOC_CLAIMED_HOOKS = 3

THE_STANDARD = (
    "A buildable engineering spec for the real frontend, not a principles "
    "overview: typed api modules one-per-router, server state only in TanStack "
    "Query (never Zustand), one query-key factory, one optimistic-mutation "
    "shape, every route lazy + error-boundaried, and enforced Core-Web-Vitals "
    "budgets. The contract is grounded against the actual tree — verify file "
    "lists against frontend/src/ before relying on them."
)


# ── §2 · State-layering rules ───────────────────────────────────────────────
@dataclass(frozen=True)
class StateRule:
    kind: str
    tool: str
    where: str
    rule: str


STATE_RULES: tuple[StateRule, ...] = (
    StateRule(
        "Server state",
        "TanStack Query v5",
        "api/<domain>.ts + useQuery / useMutation in pages",
        "Never copy server data into Zustand.",
    ),
    StateRule(
        "Global UI / auth",
        "Zustand",
        "stores/ (auth · theme · toast · ui · compare · counselor)",
        "Small, synchronous, no async data.",
    ),
    StateRule(
        "URL state",
        "react-router-dom v7",
        "useSearchParams",
        "tab, filters, search q, compare set, open thread.",
    ),
    StateRule(
        "Local",
        "useState",
        "component",
        "Transient toggles only.",
    ),
)

STATE_BUILD_RULE = (
    "A screen reads data only through an api/<domain>.ts function wrapped in a "
    "query hook — no apiClient/fetch in components. CI guards it: "
    "grep -r 'apiClient.' src/pages returns nothing."
)


# ── §3 · Query-key + cache convention ───────────────────────────────────────
QUERY_KEY = {
    "rule": (
        "Keys come from one factory (api/queryKeys.ts), never inline literals. "
        "key = [resource, paramsObject]; the params object carries the FULL "
        "filter set so two filter combinations never collide in the cache."
    ),
    "example": (
        "export const qk = {\n"
        "  matches: (refresh = false) => ['matches', { refresh }] as const,\n"
        "  program: (id: string) => ['program', id] as const,\n"
        "  feed: (params: FeedParams) => ['feed', params] as const,\n"
        "  // …one entry per resource\n"
        "}"
    ),
    "stale_time": (
        "staleTime per resource: reference / program data 5–30 min; "
        "feed / notifications 0–30 s. Filtered lists use "
        "placeholderData: keepPreviousData (no flash on filter change); cursor "
        "lists use useInfiniteQuery with the next_cursor."
    ),
}


# ── §4 · Optimistic-mutation pattern ────────────────────────────────────────
MUTATION = {
    "shape": (
        "useMutation({ mutationFn,\n"
        "  onMutate: async (vars) => { await qc.cancelQueries({ queryKey });\n"
        "    const prev = qc.getQueryData(queryKey);\n"
        "    qc.setQueryData(queryKey, patch(prev, vars)); return { prev } },\n"
        "  onError: (_e,_v,ctx) => qc.setQueryData(queryKey, ctx.prev),\n"
        "  onSettled: () => qc.invalidateQueries({ queryKey }) })"
    ),
    "rule": (
        "Standardized as hooks/useOptimisticMutation.ts so every surface uses "
        "the cancel → snapshot → patch → rollback → invalidate dance "
        "identically."
    ),
    "surfaces": (
        "Saved (13)",
        "Connect react / RSVP (20)",
        "Pipeline stage-move (31)",
        "Inbox mark-read (17)",
        "Notification mark-read (21)",
    ),
}


# ── §6 · Routing, code-split, error boundaries ──────────────────────────────
ROUTING = (
    "Heavy sub-trees are React.lazy + Suspense; the Suspense fallback is that "
    "surface's skeleton, never a global spinner.",
    "Every route carries errorElement = RouteErrorPage; a root AppErrorBoundary "
    "wraps the app — no throw ever yields a white screen.",
    "Guard wrappers (RequireAuth, role guard): 401 → /login?next=, 403 → no-access surface.",
)


# ── §7 · Error + AI-fallback handling ───────────────────────────────────────
ERROR_HANDLING = {
    "interceptor": (
        "client.ts maps status → action: 401 refresh-or-login, 403 no-access, "
        "422 → per-field errors (React Hook Form + Zod), else detail → toast."
    ),
    "ai_fallback": (
        "AI surfaces (50 §6): when a response carries source != 'ai' (rule-based "
        "fallback) the result renders with a subtle 'Showing rule-based result' "
        "note. A chat turn never shows an error bubble on AI failure — it shows "
        "the fallback. Every AI endpoint returns 200, never 5xx."
    ),
}


# ── §8 · Performance budgets (Core Web Vitals) ──────────────────────────────
@dataclass(frozen=True)
class PerfBudget:
    metric: str
    target: str
    note: str


PERF_BUDGETS: tuple[PerfBudget, ...] = (
    PerfBudget("LCP", "< 2.5 s", "Largest Contentful Paint, 4G mid-device."),
    PerfBudget("INP", "< 200 ms", "Interaction to Next Paint."),
    PerfBudget(
        "CLS",
        "< 0.1",
        "Cumulative Layout Shift; Europa via Typekit with font-display: swap + reserved metrics.",
    ),
)

PERF_TACTICS = (
    "Lighthouse-CI in the FE pipeline (budget JSON in lighthouserc.json); "
    "soft-fail first, then hard-gate.",
    "Lazy-load heavy deps (recharts, any editor) via dynamic import — never the main chunk.",
    "Virtualize lists > 50 rows (pipeline 31, feed 20, inbox 17) with @tanstack/react-virtual.",
)


# ── §9 · Realtime client ────────────────────────────────────────────────────
REALTIME = {
    "summary": (
        "One reconnecting client (lib/realtime.ts) with exponential backoff + "
        "jitter, consumed via useRealtime(). On an event it patches the Query "
        "cache (qc.setQueryData) — never a full refetch."
    ),
    "transports": (
        "SSE (EventSource) — notifications bell, feed 'new posts', chat token "
        "streaming (57 §1, 19).",
        "WebSocket — messaging (17 / 29): typing + read receipts.",
    ),
    "status": (
        "Client + useRealtime shipped and unit-tested; inert until spec 57 wires "
        "the endpoints (useRealtime enabled defaults to off)."
    ),
}


# ── §10 · Analytics / instrumentation ───────────────────────────────────────
ANALYTICS = {
    "summary": (
        "A typed event bus (lib/analytics.ts): track(event, props) emitting "
        "funnel events (signup, discover_message_sent, program_saved, "
        "application_started, decision_viewed). Feeds product metrics + the §56 "
        "ranking signals."
    ),
    "rules": (
        "Consent-gated (46): no events while analytics consent is off; revoking "
        "consent drops the buffer.",
        "Batched and best-effort; delivery failures never surface to the user.",
    ),
}


# ── §11 · Testing ───────────────────────────────────────────────────────────
TESTING = (
    "Vitest + Testing Library + MSW for API mocking. Each surface: a smoke test "
    "asserting render + the four states (loading / empty / error / success) + "
    "the primary action.",
    "Type-parity test catches FE / BE drift (generate from the OpenAPI schema).",
    "Critical journeys → Playwright e2e (post-MVP, high ROI).",
    "Coverage gate: every pages/**/*Page.tsx has ≥ 1 test.",
)


# ── §12 · Build-task checklist (honest status + evidence) ───────────────────
# status ∈ {done, partial, planned}. `fe_verifiable` marks tasks the /goal page
# confirms live by checking import.meta.glob in the running bundle — so the page
# proves the artifact exists rather than trusting this label.
@dataclass(frozen=True)
class BuildTask:
    key: str
    title: str
    status: str
    evidence: str
    artifact: str | None = None  # the file path the FE can glob-check
    fe_verifiable: bool = False


_STATUSES = {"done", "partial", "planned"}

BUILD_TASKS: tuple[BuildTask, ...] = (
    BuildTask(
        "query-keys",
        "api/queryKeys.ts key factory",
        "partial",
        "Factory shipped as the single source of keys; inline keys migrate to it "
        "incrementally (drop-in — roots match the existing literals).",
        "src/api/queryKeys.ts",
        True,
    ),
    BuildTask(
        "optimistic-mutation",
        "hooks/useOptimisticMutation.ts",
        "done",
        "Generic cancel → snapshot → patch → rollback → invalidate helper "
        "shipped and unit-tested; the §4 surfaces adopt it.",
        "src/hooks/useOptimisticMutation.ts",
        True,
    ),
    BuildTask(
        "type-parity",
        "types/api-generated.ts from OpenAPI + assignability CI",
        "planned",
        "Tooling chosen — openapi-typescript (§14): types only, hand modules "
        "kept. Lands with an OpenAPI snapshot + a CI assignability gate.",
        "src/types/api-generated.ts",
        True,
    ),
    BuildTask(
        "error-boundaries",
        "Root + per-route error boundaries via RouteErrorPage",
        "done",
        "AppErrorBoundary wraps the app (root); every route in App.tsx carries "
        "errorElement = RouteErrorPage. No throw yields a white screen.",
        None,
        False,
    ),
    BuildTask(
        "realtime",
        "lib/realtime.ts (SSE + WS) + useRealtime()",
        "done",
        "Reconnecting client (exp-backoff + jitter, cache-patching) + useRealtime "
        "shipped and unit-tested; endpoints land with spec 57.",
        "src/lib/realtime.ts",
        True,
    ),
    BuildTask(
        "analytics",
        "lib/analytics.ts typed event bus, consent-gated",
        "done",
        "Typed, consent-gated, batched track() bus shipped and unit-tested.",
        "src/lib/analytics.ts",
        True,
    ),
    BuildTask(
        "lighthouse",
        "lighthouserc.json + Lighthouse-CI step (soft → hard)",
        "partial",
        "CWV budget JSON shipped; CI runs Lighthouse as a soft (non-blocking) "
        "step first, to be hard-gated once it soaks on staging.",
        None,
        False,
    ),
    BuildTask(
        "virtualize",
        "Virtualize pipeline / feed / inbox lists",
        "planned",
        "Adopt @tanstack/react-virtual on lists > 50 rows (pipeline 31, feed 20, inbox 17).",
        None,
        False,
    ),
    BuildTask(
        "no-stray-files",
        "Delete stray 'api/* 2.ts' iCloud copies + CI filename guard",
        "done",
        "Tree is clean of '* N.*' duplicates; CI rejects any filename matching "
        "the iCloud-copy pattern.",
        None,
        False,
    ),
    BuildTask(
        "guard-api-layer",
        "CI guard: no apiClient. / fetch( in pages/",
        "done",
        "CI greps src/pages for apiClient. and raw fetch(; the two presigned-S3 "
        "PUTs moved to api/uploads.ts so the guard is honest.",
        "src/api/uploads.ts",
        True,
    ),
)


# ── §13 · Acceptance ────────────────────────────────────────────────────────
ACCEPTANCE = (
    "No server data in Zustand; no fetch() / apiClient outside api/.",
    "All §4 surfaces optimistic with rollback; filtered lists keepPreviousData.",
    "Every route lazy / error-boundaried; no white screen on throw.",
    "Query keys come from queryKeys.ts (no inline literals).",
    "Type-parity CI green; CWV budgets met on staging (Lighthouse-CI).",
    "Realtime updates patch the cache (no refetch); analytics consent-gated.",
)


# ── §14 · Open questions ────────────────────────────────────────────────────
OPEN_QUESTIONS = (
    {
        "question": "Bearer-token SSE transport",
        "recommendation": "@microsoft/fetch-event-source over native EventSource "
        "(EventSource can't set an Authorization header). The client ships with a "
        "?access_token= seam until the dep is adopted.",
    },
    {
        "question": "OpenAPI type generation",
        "recommendation": "openapi-typescript over orval — types only, no client; "
        "we keep the hand-written api modules.",
    },
    {
        "question": "⌘K command palette",
        "recommendation": "cmdk for the institution side, Phase-A.",
    },
)


def build_frontend_standards(routes) -> dict:
    """Assemble the ``GET /build/frontend-standards`` payload.

    The narrative (rules, budgets, build-task *status*) is authored from spec 54
    and this PR. The §5 parity numbers — ``live_router_count`` /
    ``live_route_count`` — are resolved from ``routes`` (the running route table)
    via :func:`build_api_contract`, so the backend half of the api-module ↔
    router contract is read from the deployed app, never asserted.
    """
    assert all(t.status in _STATUSES for t in BUILD_TASKS)  # internal guard
    contract = build_api_contract(routes)["summary"]

    done = sum(1 for t in BUILD_TASKS if t.status == "done")
    partial = sum(1 for t in BUILD_TASKS if t.status == "partial")
    planned = sum(1 for t in BUILD_TASKS if t.status == "planned")

    return {
        "summary": {
            # §5 — the live backend half of the parity contract.
            "live_router_count": contract["router_count"],
            "live_route_count": contract["route_count"],
            # Spec-doc numbers, surfaced beside the live FE counts for drift.
            "doc_claimed_api_modules": DOC_CLAIMED_API_MODULES,
            "doc_claimed_routers": DOC_CLAIMED_ROUTERS,
            "doc_claimed_stores": DOC_CLAIMED_STORES,
            "doc_claimed_hooks": DOC_CLAIMED_HOOKS,
            "state_rule_count": len(STATE_RULES),
            "build_task_count": len(BUILD_TASKS),
            "build_tasks_done": done,
            "build_tasks_partial": partial,
            "build_tasks_planned": planned,
            "perf_budget_count": len(PERF_BUDGETS),
            "acceptance_count": len(ACCEPTANCE),
            "live_is_source_of_truth": True,
        },
        "the_standard": THE_STANDARD,
        "state_rules": [
            {"kind": r.kind, "tool": r.tool, "where": r.where, "rule": r.rule} for r in STATE_RULES
        ],
        "state_build_rule": STATE_BUILD_RULE,
        "query_key": QUERY_KEY,
        "mutation": {
            "shape": MUTATION["shape"],
            "rule": MUTATION["rule"],
            "surfaces": list(MUTATION["surfaces"]),
        },
        "parity": {
            "statement": (
                "Every typed api/<domain>.ts module maps to a backend router "
                "(50 §4). The backend router / route counts below are read live "
                "from the running route table; the page counts its own api "
                "modules from import.meta.glob — both ends self-count."
            ),
            "live_router_count": contract["router_count"],
            "live_route_count": contract["route_count"],
            "doc_claimed_api_modules": DOC_CLAIMED_API_MODULES,
            "doc_claimed_routers": DOC_CLAIMED_ROUTERS,
        },
        "routing": list(ROUTING),
        "error_handling": ERROR_HANDLING,
        "perf_budgets": [
            {"metric": b.metric, "target": b.target, "note": b.note} for b in PERF_BUDGETS
        ],
        "perf_tactics": list(PERF_TACTICS),
        "realtime": {
            "summary": REALTIME["summary"],
            "transports": list(REALTIME["transports"]),
            "status": REALTIME["status"],
        },
        "analytics": {
            "summary": ANALYTICS["summary"],
            "rules": list(ANALYTICS["rules"]),
        },
        "testing": list(TESTING),
        "build_tasks": [
            {
                "key": t.key,
                "title": t.title,
                "status": t.status,
                "evidence": t.evidence,
                "artifact": t.artifact,
                "fe_verifiable": t.fe_verifiable,
            }
            for t in BUILD_TASKS
        ],
        "acceptance": list(ACCEPTANCE),
        "open_questions": [dict(q) for q in OPEN_QUESTIONS],
    }
