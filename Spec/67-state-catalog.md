# 67 · State Catalog — Loading · Empty · Error · Edge — Build Spec

> Close the biggest "demo-ware" gap: every data surface must render all four states (loading → empty / error / success), with a shared error component, real edge-state coverage (offline / 403 / 404 / 500 / partial-failure), styled confirms instead of native dialogs, and exact copy in the brand voice. Operationalizes the "no blank states" principle (`53` §3) and the error/AI-fallback mechanism (`54` §7) into a per-surface catalog. Companion to `64`, `66` (skeletons), `02` §12-13 (empty/loading), `02` §16 (voice).
>
> Status: **draft v2.0** · 2026-06-02 · v2 = first issue. Surface counts from the 2026-06-02 audit; re-grep before relying on them.

---

## 1. What exists vs what to build (ground truth)

Loading and empty are mostly handled; **error and edge are not**.

- **Loading:** 138 files handle `isLoading`; skeletons in 103 (standardized in `66` §4). Good.
- **Empty:** a real `components/ui/EmptyState.tsx` exists and is used. Some surfaces still read as thin/prototype ("Peers — coming soon" in `connect/PeersTab.tsx`; bare empties in `SchoolSubunitPage.tsx:127`).
- **Error — the gap:** only **45 of 137** files using `useQuery` handle `isError`. The other ~92 **render nothing (or a perpetual empty state) on fetch failure** — the clearest "prototype" tell. Where errors *are* handled they're bare one-liners: `analytics/OverviewTab.tsx:80`, `FunnelTab.tsx:55`, `AttributionTab.tsx:31` each render `<p className="text-error">Failed to load X</p>` + a text "Retry". There is **no shared error component** (compare the polished `EmptyState`). A good pattern already exists in one place — `apply/.../TestGuidancePanel.tsx:141` has a reusable `ErrorNote` with retry — but it isn't promoted.
- **Native dialogs:** 5 `window.confirm`/`confirm()` destructive gates (`discover/discoveryConstants.ts:22`, `profile/GoalsTab.tsx:285`, `profile/IdentityTab.tsx:274`, `profile/NeedsTab.tsx:297`, `connect/PeersTab.tsx:122-123` — block/report via OS dialog). A styled `ReleaseConfirmModal` already proves the pattern.
- **Route crashes:** `pages/system/RouteErrorPage.tsx` + `components/system/AppErrorBoundary.tsx` exist (render crashes). The gap is **per-query network failure**, not render crashes.

**Principle:** the product is honest and calm (`64` §2.4). An error never blames the user, always says what happened in plain language, and always offers the next step (retry / go back / contact). A failure that renders blank reads as broken; a failure that's handled gracefully reads as finished.

---

## 2. The four-state contract (every data surface)

Every region backed by a query renders exactly one of four states. This is the `53` §3 "no blank states" rule made mandatory and testable (`54` §11 already requires a test asserting all four).

```
            ┌─ isLoading ──────────→ Skeleton (matches final layout, 66 §4)
query ──────┼─ isError ────────────→ <QueryError> (§3)
            ├─ data && empty ──────→ <EmptyState> (§4)
            └─ data && present ────→ content
```

No surface may fall through to `null`/blank. A "no surface renders blank on failure" test is part of acceptance.

---

## 3. Shared `QueryError` / `ErrorState` component (build)

Promote the `TestGuidancePanel` `ErrorNote` + the analytics retry into one component: `components/ui/QueryError.tsx`.

```tsx
<QueryError
  title?            // default: "We couldn't load this."
  detail?           // plain-language cause, optional
  onRetry?          // → query.refetch(); shows a Retry button
  variant?          // "inline" (in-panel) | "block" (full-region) | "row" (table cell)
/>
```
- Visual: a small warning-tone icon (status color, not gold, never an illustration per `01` §9), the title, optional detail, a `secondary` Retry button (cobalt). `.elev-subtle` block or inline note per `variant`.
- Wire `query.error` → `detail` via the `client.ts` interceptor's mapped message (`54` §7) so the cause is real ("The server is taking too long" / "You're offline"), never a raw stack.
- **Adopt on all ~92 unhandled `useQuery` surfaces.** A `useQueryState` helper (or a `<QueryBoundary query={...}>` wrapper) can collapse the loading/error/empty branching into one call so surfaces can't forget a state.

---

## 4. Empty / zero states — empty-to-hero (per surface)

`EmptyState` exists; the work is (a) covering every list and (b) upgrading thin ones to "here's what this becomes" (the Notion bar, `64` §3.2). No illustrations (brand rule) — a short heading + one line + one primary action. Copy in brand voice (sentence case, no exclamation marks):

| Surface (file) | Empty heading | Line | Action |
|---|---|---|---|
| Match / Explore results (`ExplorePage.tsx`) | "No matches yet" | "Tell us a bit about your goals and we'll find programs that fit." | "Start with Discover" → `/s` |
| Saved list (`13`) | "Nothing saved yet" | "Save programs from your matches to compare them side by side." | "Browse matches" → `/s/explore` |
| Applications (`15`) | "No applications yet" | "When you're ready, turn a saved program into an application here." | "See saved programs" |
| Connect / Peers (`connect/PeersTab.tsx`) | "No peers to show yet" | "Follow institutions to see students heading the same way." | "Find institutions" |
| Calendar (`16`) | "Nothing scheduled" | "Deadlines and interviews will appear here as you apply." | — |
| Inbox (`17`) | "No messages" | "Messages from institutions about your applications land here." | — |
| Institution pipeline (`31`) | "No applicants in this stage" | "Applicants move here as they progress." | — |
| Institution analytics (`28`) | "Not enough data yet" | "Charts fill in as students engage with your programs." | — |

**Replace the literal "coming soon" strings** (`PeersTab`, `IntegrationsCard`) — if a feature is genuinely not ready, render a disabled state *with context* ("Peer profiles are rolling out — check back soon"), never a bare "coming soon" that reads unfinished.

---

## 5. Edge-state catalog

Beyond the four core states, every app needs these and the audit shows them largely unhandled:

| Edge state | Trigger | Treatment |
|---|---|---|
| **Offline** | `navigator.onLine` false / network error | a thin top banner "You're offline. We'll reconnect automatically." + queries show `QueryError` with an auto-retry on reconnect. |
| **Validation (422)** | form submit | field-level errors via React Hook Form + Zod (`54` §7); `Input`'s reserved error region (no layout shift). Never a toast for field errors. |
| **Permission (403)** | role/guard mismatch | the no-access surface (`05` §3 / `50` §2), not a blank. "You don't have access to this." + a way back. |
| **Not found (404)** | bad id / deleted resource | a real 404 surface, in-app chrome, "We couldn't find that." + primary nav back. Distinct from `RouteErrorPage`. |
| **Server (500)** | unhandled backend error | `QueryError` block with Retry + "If this keeps happening, contact support." |
| **Partial failure** | one of N queries on a page fails | the failed *region* shows `QueryError`; the rest of the page renders. Never blank the whole page for one failed widget (the analytics pages do this well per-chart — generalize it). |
| **Rate-limited (429)** | `55` rate limiting | "You're going a little fast — give it a moment." + auto-retry after the `Retry-After`. |
| **Stale / refetching** | background refetch | keep current data visible (`keepPreviousData`, `54` §3); a subtle inline spinner, never a full skeleton flash. |

Build the 404 (`pages/system/NotFoundPage.tsx`) and 403 (`pages/system/NoAccessPage.tsx`) surfaces if missing; wire the offline banner once at the layout level.

---

## 6. `ConfirmDialog` (replace native dialogs)

Build `components/ui/ConfirmDialog.tsx` (generalize the existing `ReleaseConfirmModal`):
```tsx
<ConfirmDialog
  title destructive?          // destructive → the confirm button is danger-tone
  body confirmLabel cancelLabel
  onConfirm />                // returns a promise; shows loading on the button
```
Replace all 5 native `window.confirm` sites:

| Site | New copy |
|---|---|
| `discover/discoveryConstants.ts:22` (switch track/layer) | "Switch tracks? Your current answers are saved — you can come back anytime." |
| `profile/GoalsTab.tsx:285` (delete goal) | "Delete this goal? You can add it again later." (offer Undo-toast instead where reversible, `66` §5) |
| `profile/IdentityTab.tsx:274` / `NeedsTab.tsx:297` | same delete pattern |
| `connect/PeersTab.tsx:122-123` (block / report) | a proper styled block/report flow — never an OS dialog on a social surface |

Rule: **reversible** destructive actions prefer the Undo-toast (`66` §5); **irreversible** ones use `ConfirmDialog`. Zero `window.confirm`/`alert`/`window.prompt` remain.

---

## 7. AI-fallback states (the trust surface)

Per the papers, every AI output must read honestly (`64` §2.1). Standardize via existing `FallbackNote`/`AIBadge`:
- When a response carries `source != "ai"` (rule-based fallback, `50` §6 / `54` §7), render the result + `FallbackNote` ("Showing a rule-based result") — never an error.
- A chat turn never shows an error bubble on AI failure — it shows the fallback text (`66` §6).
- Low-confidence AI extractions surface a "we weren't sure about this — confirm?" affordance (the paper's "flag low-confidence items for clarification"), not a silent guess.

---

## 8. Copy strings (verbatim, brand voice)

Voice = **Plain · Direct · Honest · Brief · Warm**; sentence case; periods on full sentences; **no exclamation marks** (`02` §16). Reusable strings:

| Key | String |
|---|---|
| `error.generic` | "We couldn't load this." |
| `error.retry` | "Try again" |
| `error.offline` | "You're offline. We'll reconnect automatically." |
| `error.timeout` | "The server is taking too long. Try again in a moment." |
| `error.500` | "Something went wrong on our end. If it keeps happening, contact support." |
| `error.403` | "You don't have access to this." |
| `error.404` | "We couldn't find that." |
| `error.429` | "You're going a little fast — give it a moment." |
| `confirm.delete.generic` | "Delete this? You can't undo it." |
| `loading.aria` | "Loading…" (`aria-live` polite) |

Centralize in a `lib/copy.ts` (or i18n catalog, `70`/future) so strings are consistent and one edit changes them everywhere.

---

## 9. Build tasks (checklist)

- [ ] Build `components/ui/QueryError.tsx` (3 variants) + a `useQueryState`/`<QueryBoundary>` helper; wire the interceptor's message → `detail`.
- [ ] Adopt the four-state contract on all ~92 `useQuery` surfaces missing `isError`; delete the bare "Failed to load" one-liners.
- [ ] Cover every list with `EmptyState`; upgrade thin/"coming soon" empties per §4 with brand-voice copy.
- [ ] Build `NotFoundPage` (404) + `NoAccessPage` (403); add the offline banner at layout level; implement the partial-failure rule.
- [ ] Build `components/ui/ConfirmDialog.tsx`; replace all 5 `window.confirm`; wire Undo-toast for reversible deletes (`66` §5).
- [ ] Standardize AI-fallback rendering via `FallbackNote`; add the low-confidence "confirm?" affordance.
- [ ] Add `lib/copy.ts` with the §8 strings.
- [ ] Add a CI test asserting no `pages/**` query surface can render blank on error (lint for `useQuery` without an `isError`/`QueryBoundary` path).

---

## 10. Acceptance

- [ ] Every `useQuery` surface renders loading / empty / error / success; none render blank on failure.
- [ ] One shared `QueryError`; zero bare "Failed to load X" strings remain.
- [ ] Zero `window.confirm`/`alert`/`prompt`; destructive actions use `ConfirmDialog` or Undo-toast.
- [ ] 404 / 403 / offline / 429 / partial-failure all have designed states.
- [ ] No literal "coming soon" strings; not-ready features show disabled-with-context.
- [ ] All error/empty copy is sentence case, no exclamation marks, from `lib/copy.ts`.
- [ ] `54` §11 per-surface four-state test passes for every `*Page.tsx`.

---

## 11. Open questions

- **`QueryBoundary` vs per-surface branching.** A wrapper component is DRY but can over-abstract surfaces with multiple independent queries (partial-failure). Recommend the wrapper for single-query regions, manual branching for multi-query pages.
- **Offline depth.** Banner + auto-retry (recommended for v1) vs true offline support (service worker / cached reads). Defer real offline to post-launch (`03` PWA-light posture).
- **Undo window length.** 6s default for Undo-toast — confirm it's long enough for the reversible deletes without feeling like a delay.
