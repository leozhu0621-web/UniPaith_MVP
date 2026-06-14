"""Spec 53 — the UX-benchmark & interaction-standards surface, as queryable data.

Spec 53 sets the *experience* bar: each app surface gets a concrete benchmark
(LinkedIn / Handshake / ChatGPT / an ATS), the real page file it lives in, the
interaction contract to build, and an acceptance test. This module turns that
spec into the payload behind ``GET /build/ux-benchmark`` and the
``/goal/experience`` page — the same way ``ai.catalog`` turns spec 45 into
``GET /ai/agents`` and ``transparency.api_contract`` turns spec 50 into a live
route map.

The self-verifying hook: a benchmarked surface is only credible if it's actually
wired. So for each §2 surface we resolve, **live from the running route table**,
the ``/api/v1`` endpoints that back it (matched by path marker). The page then
shows "backed by N live routes" per surface — a number read from the deployed
app, never asserted in prose. The narrative (benchmark, build contract) is
authored from spec 53; the backing count can't drift from what's served.

DB-free and unauthenticated, like its sibling ``/build/*`` modules — it exposes
only build *architecture*, never user data.
"""

from __future__ import annotations

from dataclasses import dataclass

API_PREFIX = "/api/v1"
_SKIP_METHODS = {"HEAD", "OPTIONS"}

# ── §1 · The bar ────────────────────────────────────────────────────────────
THE_BAR: dict = {
    "statement": (
        'A surface is "market-grade" when a user arriving from LinkedIn or '
        "Handshake notices no drop in responsiveness or polish: instant "
        "(optimistic) feedback, no blank states, smooth motion, forgiving "
        "inputs — the app already knew what they wanted."
    ),
    # The two headline competitors named in spec 53; individual surfaces also
    # cite ChatGPT (chat) and Greenhouse/Lever (the ATS pipeline).
    "benchmarks": ("LinkedIn", "Handshake"),
}


# ── §2 · Per-surface build contract ─────────────────────────────────────────
@dataclass(frozen=True)
class Surface:
    key: str
    name: str
    specs: tuple[str, ...]
    files: tuple[str, ...]  # the real frontend page file(s) this surface lives in
    benchmark: str  # display string, verbatim from spec 53 §2
    benchmark_key: str  # filter family: linkedin | handshake | chatgpt | ats
    build_contract: tuple[str, ...]
    # Path substrings used to resolve the live backing endpoints. Grounded
    # against the real route table (see tests) so each surface backs > 0 routes.
    route_markers: tuple[str, ...]


SURFACES: tuple[Surface, ...] = (
    Surface(
        "profile",
        "Profile",
        ("08",),
        ("student/ProfilePage.tsx", "profile/*Tab.tsx"),
        "LinkedIn profile",
        "linkedin",
        (
            "Inline-edit per section",
            'Completeness ring + "what\'s next"',
            'Autosave with "saving… / saved" status (54 §4 optimistic)',
            "Reorderable sections",
            "Inline validation on blur",
        ),
        (
            "/students/me/profile",
            "/students/me/goals",
            "/students/me/needs",
            "/students/me/identity",
            "/students/me/strategy",
            "/students/me/completion-map",
        ),
    ),
    Surface(
        "discover",
        "Discover chat",
        ("19",),
        ("student/DiscoverHomePage.tsx", "discover/ChatPanel.tsx", "discover/ArtifactRail.tsx"),
        "ChatGPT / LinkedIn messaging",
        "chatgpt",
        (
            "Token streaming (SSE, 57)",
            "Typing indicator",
            "Retry on a failed turn",
            "Persisted turns",
            "Artifact rail patches live on each extracted signal",
        ),
        ("/students/me/discovery/",),
    ),
    Surface(
        "match",
        "Match / Explore",
        ("09", "10"),
        ("student/ExplorePage.tsx", "match/*", "explore/*"),
        "Handshake search",
        "handshake",
        (
            "Typeahead",
            "Facet filters with live counts",
            "useInfiniteQuery scroll",
            "Saved searches + alerts (56)",
            "Compare tray (compare-store)",
        ),
        (
            "/students/me/matches",
            "/students/me/search/",
            "/programs/search",
            "/students/me/saved",
            "/students/me/compare",
        ),
    ),
    Surface(
        "detail",
        "Program / School detail",
        ("11", "12"),
        ("student/ProgramDetailPage.tsx", "program/*", "student/InstitutionDetailPage.tsx"),
        "LinkedIn company page",
        "linkedin",
        (
            "Sticky section nav",
            "Skeleton load (not a spinner)",
            "Optimistic Save",
            "Related-items rail",
            "Provenance captions (60)",
        ),
        ("/programs/{program_id}", "/institutions/{institution_id}"),
    ),
    Surface(
        "connect",
        "Connect feed",
        ("20",),
        ("student/PostsPage.tsx", "explore/cards/*"),
        "LinkedIn feed",
        "linkedin",
        (
            "Ranked feed (56)",
            "Infinite scroll",
            "Optimistic react / RSVP",
            '"New posts" pill',
            "Seen-state",
        ),
        (
            "/connect/",
            "/students/me/feed",
            "/students/me/follows",
            "/students/me/events",
            "/events/{event_id}/rsvp",
        ),
    ),
    Surface(
        "inbox",
        "Inbox / Messaging",
        ("17", "29"),
        ("student/MessagesPage.tsx", "institution/MessagingPage.tsx"),
        "LinkedIn messaging",
        "linkedin",
        (
            "Real-time delivery (WS, 57)",
            "Unread badges",
            "Typing indicator",
            "Optimistic send",
            "Thread search",
            "List ↔ thread are full screens on mobile (03)",
        ),
        ("/messages/conversations", "/inbox/threads"),
    ),
    Surface(
        "notifications",
        "Notifications",
        ("21", "57"),
        ("Notification bell + center",),
        "LinkedIn notifications",
        "linkedin",
        (
            "Real-time bell (SSE)",
            "Grouped",
            "Mark-all-read (syncs across tabs)",
            "Deep-link",
            "Digest preferences",
        ),
        ("/notifications",),
    ),
    Surface(
        "pipeline",
        "Pipeline / Review",
        ("31", "32"),
        ("institution/PipelinePage.tsx", "institution/StudentDetailPage.tsx"),
        "Greenhouse / Lever ATS",
        "ats",
        (
            "Dense virtualized table (54 §8)",
            "Bulk-select",
            "Keyboard navigation",
            "Saved views",
            "Optimistic stage moves",
            "⌘K palette (institution)",
        ),
        ("/reviews/", "/applications/review/"),
    ),
)


# ── §3 · Interaction standards (apply everywhere) ───────────────────────────
@dataclass(frozen=True)
class Standard:
    title: str
    body: str
    mechanism: str  # the 54 / 56 / 57 mechanism this maps to


INTERACTION_STANDARDS: tuple[Standard, ...] = (
    Standard(
        "Optimistic UI",
        "Save, react, RSVP, stage-move and mark-read apply instantly and reconcile "
        "against the server response.",
        "54 §4 · useOptimisticMutation",
    ),
    Standard(
        "No blank states",
        "Every async region renders skeleton → content / empty / error; empty states "
        "are instructional with a CTA; the Suspense fallback is the skeleton.",
        "02 · 54 §6",
    ),
    Standard(
        "Motion",
        "Enter/exit transitions on lists, sheets and toasts use the 120 / 200 / 360 ms "
        "tokens; prefers-reduced-motion is honored.",
        "02 · motion tokens",
    ),
    Standard(
        "Autosave",
        "Long forms (profile, program editor, essays) autosave with a status indicator — "
        "never a lone Save that can lose work.",
        "23 · 14 · 54 §4",
    ),
    Standard(
        "Infinite scroll + restore position",
        "Any list longer than a page is cursor-paginated and restores scroll position "
        "on back-navigation.",
        "50 §5 · 54 §3",
    ),
    Standard(
        "Typeahead",
        "Search and entity pickers (program, CIP major, country) are debounced 200 ms, "
        "keyboard-navigable and feel ≤150 ms.",
        "54 §7",
    ),
    Standard(
        "Forgiving inputs",
        "Inline validation on blur, scroll-to-first-error, correct inputmode and "
        "paste-friendly fields; 422s map to per-field messages.",
        "54 §7 · 422 mapping",
    ),
    Standard(
        "Completeness gamification",
        'Profile and application show a completeness ring + a "what\'s next" queue.',
        "08 · 15",
    ),
    Standard(
        "Saved searches + alerts",
        "Any filter set is saveable; new matches notify.",
        "56 · 57",
    ),
    Standard(
        "Keyboard",
        "Focus rings, a sane tab order, a ⌘K command palette (institution) and "
        "arrow-key navigation in dense tables.",
        "54 · cmdk",
    ),
)


# ── §4 · Empty / first-run polish ───────────────────────────────────────────
EMPTY_STATE_POLICY: dict = {
    "rule": (
        'Every surface ships an instructional empty state with a seeded "try this" '
        "affordance and a path to value in ≤2 clicks — a real empty-state component "
        'per surface, never a generic "no data".'
    ),
    "first_run": (
        {"side": "student", "to": "Discover chat (19)", "file": "student/DiscoverHomePage.tsx"},
        {"side": "institution", "to": "Setup wizard (30)", "file": "institution/SetupPage.tsx"},
    ),
}


# ── §5 · Acceptance (side-by-side click test vs the named competitor) ────────
ACCEPTANCE: tuple[str, ...] = (
    "Every mutation is optimistic or shows ≤1 skeleton — never a blank flash.",
    "Every list longer than a page has infinite scroll + restored scroll on back.",
    "Search and every entity picker has debounced typeahead.",
    "Long forms autosave with a status indicator.",
    "Feeds, messaging and notifications update in real time (57).",
    "prefers-reduced-motion is honored; motion uses the 02 tokens.",
    "Each surface passes its benchmark in a side-by-side click test vs the named competitor.",
)


def _iter_api_routes(routes):
    """Yield ``(path, method)`` for each live ``/api/v1`` route (skip HEAD/OPTIONS).

    Same flattening the api-contract surface uses — one row per (path, method),
    so "backed by N live routes" counts the same way the /goal/api page does.
    """
    from unipaith.transparency.live_routes import expand_routes

    for r in expand_routes(routes):
        path = getattr(r, "path", "")
        methods = getattr(r, "methods", None)
        if not path.startswith(API_PREFIX) or not methods:
            continue
        for method in sorted(methods):
            if method not in _SKIP_METHODS:
                yield path, method


def build_ux_benchmark(routes) -> dict:
    """Assemble the ``GET /build/ux-benchmark`` payload.

    The narrative (benchmark + build contract per surface, the standards, the
    acceptance list) is authored from spec 53. The per-surface ``backed_route_count``
    is resolved from ``routes`` — the running route table — so it can't claim a
    surface the deployed app doesn't actually serve.
    """
    rows = list(_iter_api_routes(routes))

    surfaces_out: list[dict] = []
    backed_union: set[tuple[str, str]] = set()
    for s in SURFACES:
        matched = [(p, m) for (p, m) in rows if any(mk in p for mk in s.route_markers)]
        backed_union.update(matched)
        sample = sorted({p for (p, _) in matched}, key=len)[:4]
        surfaces_out.append(
            {
                "key": s.key,
                "name": s.name,
                "specs": list(s.specs),
                "files": list(s.files),
                "benchmark": s.benchmark,
                "benchmark_key": s.benchmark_key,
                "build_contract": list(s.build_contract),
                "backed_route_count": len(matched),
                "sample_paths": sample,
            }
        )

    return {
        "the_bar": {"statement": THE_BAR["statement"], "benchmarks": list(THE_BAR["benchmarks"])},
        "summary": {
            "surface_count": len(SURFACES),
            "standard_count": len(INTERACTION_STANDARDS),
            "acceptance_count": len(ACCEPTANCE),
            "benchmarks": list(THE_BAR["benchmarks"]),
            "benchmark_keys": sorted({s.benchmark_key for s in SURFACES}),
            "backed_route_total": len(backed_union),
            "surfaces_backed": sum(1 for s in surfaces_out if s["backed_route_count"] > 0),
        },
        "surfaces": surfaces_out,
        "standards": [
            {"title": x.title, "body": x.body, "mechanism": x.mechanism}
            for x in INTERACTION_STANDARDS
        ],
        "empty_state": {
            "rule": EMPTY_STATE_POLICY["rule"],
            "first_run": [dict(x) for x in EMPTY_STATE_POLICY["first_run"]],
        },
        "acceptance": list(ACCEPTANCE),
    }
