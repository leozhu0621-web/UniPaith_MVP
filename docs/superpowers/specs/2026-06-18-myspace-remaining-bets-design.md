# My Space review — remaining bigger bets (design)

**Date:** 2026-06-18 · **Status:** Approved by founder ("continue to build all features") · **Scope:** frontend-only unless noted

These are the four remaining bigger bets from the My Space subagent review (after the rail single-source-of-truth #776, Documents asset manager #778, deadline radar #783, quick-wins #789, and Planning-that-connects #799 already shipped). Each ships as its own PR via the `/ship` loop.

## 1. Prep readiness header
Prep is five disconnected lists with no answer to "am I ready?". Add a compact readiness strip at the top of `PrepPage` (below the PageHeader, above the tab strip), composing data the room already loads:
- **Recommenders** — `{received}/{requested}` received (`listRecommendations`); warning tone while any are still requested-not-received.
- **Interviews** — `{n} need a response` (`getMyInterviews`, the `RESPOND_STATUSES` bucket InterviewsTab uses); warning tone when > 0, else "all responded".
- **Documents** — `{n} on file` (`listDocuments`).
- **Workshops** — `{n} feedback runs` (`listWorkshopRuns`).
Each tile is a `StatTile`-style cell that deep-links to its tab (`?tab=recommenders|interviews|documents|workshops`). Hide the whole strip on a true cold start (no recs, no interviews, no docs, no runs). Semantic tokens, gold reserved, no manufactured cheer.

## 2. Compare offers — first-class decision table
Decision support is the emotional peak; today comparison is a buried modal (`DecisionComparison`) reached from 4 scattered spots. Promote a side-by-side table into the Offers view (`/s/applications?tab=offers`): one column per offer, rows = key money terms (tuition/COA, funding/aid, net cost), response deadline on a shared line, graduate funding totals inline where present. **Inform + view only** — never a fake Accept/Decline (the real respond action stays in `OfferPanel`, which owns the verified endpoint). Keep the existing modal as a quick peek. Reuse the unified `DeadlinePill` (#783) for response deadlines.

## 3. Recommenders — at-risk nudges + voice migration
Recommendation letters are the highest-anxiety, lowest-control asset. Sort/surface requests by `due_date` with an **at-risk** flag (requested, not received, due soon) and a **Nudge** resend for stale requests (`sendRecommendationRequest`). Migrate the legacy `RecommendationsPage` onto the shared `Select` / `QueryError` / sentence-case voice so it stops being the one tab that breaks the language (Title-Case modal titles, raw `<select>`, bespoke red-text error card).

## 4. Portfolio rowModel + named rail meta
`ApplicationsPage` re-derives bucket + offer state four times (`nextAction` / `rowAction` / `appHref` / `actionScore`), which causes the "card-click lands on the Offer tab but the inline affordance says Open" divergence. Collapse into one `rowModel(app) → { bucket, label, action, href, score, deadlinePill }` computed once per row. Then extend the proven Workspace count badge into **named, child-level** rail meta in `MySpaceShell` (e.g. Recommenders `2/3`, Offers a dot on a new arrival) — each naming its noun to avoid the ambiguous bare `3`.

## Verification (each)
tsc 0 · vite build 0 · eslint 0 errors · vitest green · ship via `/ship` and confirm live.
