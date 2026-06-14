"""Spec 50 — the front↔back API contract, with the router map derived LIVE.

The conventions (base, auth, envelope, status taxonomy, AI invariant) are
authored from spec 50 §1–§6. The **router map is built from the running route
table** passed in by the endpoint (``request.app.routes``) — so it is, by
construction, the machine source of truth spec 50 §5 points at, and can never
drift from what's deployed. When this disagrees with the prose in spec 50, the
running code wins (spec 50 §5).
"""

from __future__ import annotations

from collections import defaultdict

from unipaith.transparency.live_routes import expand_routes

# Spec 50 was drafted at 22 routers / ~285 routes (2026-05-30). The live count is
# higher (specs 39–46 landed after). Surfaced so the page shows the correction.
DOC_CLAIMED_ROUTERS = 22
DOC_CLAIMED_ROUTES = 285

API_PREFIX = "/api/v1"
_SKIP_METHODS = {"HEAD", "OPTIONS"}

# Spec 50 §6 — the AI-backed endpoints that must never 5xx (fall back instead).
# Matched as substrings against the live (templated) path so the set tracks the
# real routes precisely — the §6 enumerated surfaces, no more.
_AI_PATH_MARKERS = (
    "/discovery/sessions/{session_id}/messages",
    "/matches/{program_id}/explain",
    "/matches/{program_id}/rationale",
    "/strategy/generate",
    "/workshops/essay/feedback",
    "/workshops/interview/practice",
    "/workshops/interview/feedback",
    "/workshops/test/guidance",
    "/identity/regenerate-summary",
)

# Conservative public classification (spec 50 §2). The authoritative guard is each
# route's dependency; this is a best-effort label noted as such on the page.
_PUBLIC_EXACT = {
    f"{API_PREFIX}/health",
    f"{API_PREFIX}/ready",
    f"{API_PREFIX}/webhooks/stripe",
}
_PUBLIC_PREFIX = (
    f"{API_PREFIX}/ai/agents",
    f"{API_PREFIX}/build",
    f"{API_PREFIX}/t/",
    f"{API_PREFIX}/campaigns/unsubscribe",
)
_PUBLIC_AUTH = {
    f"{API_PREFIX}/auth/login",
    f"{API_PREFIX}/auth/signup",
    f"{API_PREFIX}/auth/google-callback",
}


CONVENTIONS: tuple[dict, ...] = (
    {
        "title": "One prefix, one client",
        "body": "Every route lives under /api/v1. The React app talks to the API "
        "through a single Axios instance (api/client.ts) whose baseURL carries the "
        "prefix — screens call typed per-domain modules, never fetch() ad-hoc.",
    },
    {
        "title": "Bearer auth, three roles",
        "body": "Cognito JWT (or a dev token) on the Authorization header. Roles are "
        "student, institution_admin and admin — no platform-admin tier. 401 redirects "
        "to login; 403 is a wrong-role refusal.",
    },
    {
        "title": "Idiomatic envelope",
        "body": "Success returns the resource (or {items,total,limit,offset} for "
        "lists) directly — no wrapper. Errors are FastAPI's {detail} shape; 422 carries "
        "structured per-field errors the client maps to inline form messages.",
    },
    {
        "title": "AI never 5xxes",
        "body": "Every AI-backed endpoint falls back to a deterministic path on "
        "timeout, parse error or guardrail trip, returning 200 with a source "
        "indicator. The caller always gets a usable answer.",
    },
)

STATUS_TAXONOMY: tuple[dict, ...] = (
    {"code": "200 / 201", "when": "OK / created", "frontend": "Proceed; 201 returns the resource."},
    {"code": "204", "when": "Deleted", "frontend": "Optimistic remove."},
    {"code": "400", "when": "Semantic bad request", "frontend": "Inline detail."},
    {"code": "401", "when": "No / expired token", "frontend": "Redirect /login?next=."},
    {"code": "403", "when": "Wrong role / not owner", "frontend": "No-access state."},
    {"code": "404", "when": "Not found", "frontend": "Not-found state."},
    {"code": "409", "when": "Conflict (dup / state)", "frontend": "Inline (e.g. already applied)."},
    {"code": "422", "when": "Validation", "frontend": "Per-field inline errors."},
    {"code": "429", "when": "Rate limited (AI / bulk)", "frontend": "Backoff + retry."},
    {"code": "5xx", "when": "Server", "frontend": "Toast — but AI endpoints fall back, not 5xx."},
)


def _route_access(path: str, methods: set[str]) -> str:
    """Best-effort public/authenticated label (spec 50 §2)."""
    if path in _PUBLIC_EXACT or path in _PUBLIC_AUTH:
        return "public"
    if any(path.startswith(p) for p in _PUBLIC_PREFIX):
        return "public"
    # Public reads: program browse/detail/search + a single institution by id.
    if "GET" in methods:
        if path == f"{API_PREFIX}/programs" or path.startswith(f"{API_PREFIX}/programs/"):
            return "public"
        if path.startswith(f"{API_PREFIX}/institutions/{{") and "/me" not in path:
            return "public"
    return "authenticated"


def _route_role(path: str, access: str) -> str:
    if access == "public":
        return "public"
    if path.startswith(f"{API_PREFIX}/students") or "/me/" in path or path.endswith("/me"):
        return "student"
    if (
        path.startswith(f"{API_PREFIX}/institutions")
        or path.startswith(f"{API_PREFIX}/applications")
        or path.startswith(f"{API_PREFIX}/reviews")
        or path.startswith(f"{API_PREFIX}/interviews")
    ):
        return "institution"
    return "shared"


def _collect(routes) -> list[dict]:
    """Flatten the live route table to one row per (path, method) under /api/v1."""
    rows: list[dict] = []
    for r in expand_routes(routes):
        path = getattr(r, "path", "")
        methods = getattr(r, "methods", None)
        if not path.startswith(API_PREFIX) or not methods:
            continue
        verbs = sorted(m for m in methods if m not in _SKIP_METHODS)
        if not verbs:
            continue
        tags = list(getattr(r, "tags", None) or [])
        tag = tags[0] if tags else "(untagged)"
        access = _route_access(path, set(verbs))
        role = _route_role(path, access)
        for verb in verbs:
            rows.append(
                {
                    "path": path,
                    "method": verb,
                    "tag": tag,
                    "access": access,
                    "role": role,
                    "is_ai": any(m in path for m in _AI_PATH_MARKERS),
                }
            )
    return rows


def build_api_contract(routes) -> dict:
    """Assemble the ``GET /build/api-contract`` payload from the live route table."""
    rows = _collect(routes)

    by_tag: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_tag[row["tag"]].append(row)

    groups = []
    for tag, tag_rows in by_tag.items():
        method_counts: dict[str, int] = defaultdict(int)
        for r in tag_rows:
            method_counts[r["method"]] += 1
        roles = {r["role"] for r in tag_rows}
        role = next(iter(roles)) if len(roles) == 1 else "mixed"
        accesses = {r["access"] for r in tag_rows}
        access = (
            "public"
            if accesses == {"public"}
            else ("mixed" if "public" in accesses else "authenticated")
        )
        # A few representative paths (deduped, shortest first for readability).
        sample = sorted({r["path"] for r in tag_rows}, key=len)[:4]
        groups.append(
            {
                "tag": tag,
                "route_count": len(tag_rows),
                "methods": dict(sorted(method_counts.items())),
                "role": role,
                "access": access,
                "sample_paths": sample,
            }
        )
    groups.sort(key=lambda g: (-g["route_count"], g["tag"]))

    method_totals: dict[str, int] = defaultdict(int)
    for r in rows:
        method_totals[r["method"]] += 1

    ai_endpoints = sorted({r["path"] for r in rows if r["is_ai"]}, key=len)
    public_count = sum(1 for r in rows if r["access"] == "public")

    return {
        "summary": {
            "route_count": len(rows),
            "router_count": len(groups),
            "public_route_count": public_count,
            "authenticated_route_count": len(rows) - public_count,
            "ai_endpoint_count": len(ai_endpoints),
            "method_totals": dict(sorted(method_totals.items())),
            "prefix": API_PREFIX,
            # Spec 50 §5 — doc-vs-live drift, surfaced for honesty.
            "doc_claimed_routers": DOC_CLAIMED_ROUTERS,
            "doc_claimed_routes": DOC_CLAIMED_ROUTES,
            "live_is_source_of_truth": True,
        },
        "conventions": list(CONVENTIONS),
        "status_taxonomy": list(STATUS_TAXONOMY),
        "groups": groups,
        "ai_endpoints": ai_endpoints,
        "access_note": "Public/authenticated labels are a conservative read of the "
        "route table; the authoritative guard is each route's dependency. The map "
        "is generated live from the running app — it is the source of truth spec 50 "
        "points at.",
    }
