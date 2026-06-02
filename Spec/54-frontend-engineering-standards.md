# 54 · Frontend Engineering — Build Spec

> Buildable engineering spec for the existing React 19 + Vite + Tailwind + Zustand + TanStack Query frontend (`frontend/src/`). Not a principles overview — concrete file contracts, the real module inventory, query-key conventions, and per-area build tasks grounded in the actual tree. Companion to `02`/`03` (design), `50` (API contract), `53` (UX bar this delivers).
>
> Status: **draft v2.0** · 2026-05-30 · v2 converts the v1 standards into a build spec against the real codebase. Verify file lists against `frontend/src/` before relying on them.

---

## 1. Real frontend tree (ground truth — what exists today)

```
frontend/src/
  api/        37 typed modules, one per backend router (client.ts + <domain>.ts)
  stores/     auth-store, compare-store, counselor-store, theme-store, toast-store, ui-store
  hooks/      useBilling.ts, useDeadlines.ts, usePageTitle.ts
  lib/        utils.ts (cn() etc.)
  types/      TS types mirroring backend Pydantic responses
  components/ shared UI (ui/ primitives + feature components)
  pages/      role-foldered: student/, institution/, public/, auth/, system/
  App.tsx     router + lazy routes + error boundaries
  main.tsx    QueryClient + providers
```

`api/client.ts` already implements: axios instance at `VITE_API_URL || http://localhost:8000/api/v1`, 30s timeout, **token-refresh queue** (`subscribeTokenRefresh`/`onTokenRefreshed`), lazy `auth-store` import to break the circular dep. **Do not replace it** — extend.

> Cleanup task: stray iCloud copies `api/calendar 2.ts`, `api/interviews 2.ts` exist in some working trees (not on `origin/main`). Delete on sight; never import.

---

## 2. State layering — enforced rules (with the real stores)

| Kind | Tool | Where | Rule |
|---|---|---|---|
| Server state | TanStack Query v5 | `api/<domain>.ts` + `useQuery`/`useMutation` in pages | **Never** copy server data into Zustand. |
| Global UI/auth | Zustand | `stores/auth-store.ts`, `theme-store.ts`, `toast-store.ts`, `ui-store.ts`, `compare-store.ts`, `counselor-store.ts` | Small, synchronous, no async data. |
| URL state | react-router-dom v7 | `useSearchParams` | tab, filters, search `q`, compare set, open thread (`05` §13). |
| Local | `useState` | component | transient toggles only. |

**Build rule:** a screen reads data **only** through an `api/<domain>.ts` function wrapped in a query hook. No `apiClient`/`fetch` calls inside components. PR check: `grep -r "apiClient\." src/pages` must return nothing.

---

## 3. Query-key + cache convention (make it a shared file)

Today query keys are inline per page → drift risk. **Build task: add `frontend/src/api/queryKeys.ts`** as the single key factory:
```ts
export const qk = {
  matches: (refresh=false) => ['matches', { refresh }] as const,
  matchProbability: (programId: string) => ['matchProbability', programId] as const,
  program: (id: string) => ['program', id] as const,
  savedList: () => ['savedList'] as const,
  feed: (params: FeedParams) => ['feed', params] as const,
  notifications: () => ['notifications'] as const,
  // …one entry per resource; params object carries the FULL filter set
}
```
Rules: key = `[resource, paramsObject]`; `paramsObject` includes every filter (cache correctness). `staleTime` per resource (reference/program data: 5–30 min; feed/notifications: 0–30 s). Paginated/filtered lists use `placeholderData: keepPreviousData` (no flash on filter change). Cursor lists use `useInfiniteQuery` with the `next_cursor` from `50` §5.

---

## 4. Mutation pattern (optimistic, the `53` bar) — reference implementation

Every save/react/RSVP/stage-move/mark-read uses this exact shape:
```ts
useMutation({
  mutationFn: api.savedLists.save,
  onMutate: async (vars) => {
    await qc.cancelQueries({ queryKey: qk.savedList() })
    const prev = qc.getQueryData(qk.savedList())
    qc.setQueryData(qk.savedList(), patch(prev, vars))   // optimistic
    return { prev }
  },
  onError: (_e, _v, ctx) => qc.setQueryData(qk.savedList(), ctx.prev), // rollback
  onSettled: () => qc.invalidateQueries({ queryKey: qk.savedList() }),
})
```
Standardize as a `useOptimisticMutation` helper in `hooks/` so every surface uses it identically. Surfaces required to be optimistic (`53` §3): Saved (`13`), Connect react/RSVP (`20`), pipeline stage-move (`31`), inbox mark-read (`17`), notification mark-read (`21`).

---

## 5. api-module ↔ router parity (the contract with `50`)

The 37 `api/` modules map 1:1 to the 22 backend routers (`50` §4). Build rules:
- One module per router; export typed functions returning the response type from `types/`.
- TS response type **mirrors the backend Pydantic schema field-for-field** — when a backend field is added, add it to the TS type in the same PR (`CLAUDE.md` "fields invisible otherwise"). 
- **Build task: type-parity test** — generate TS types from `/api/v1/openapi.json` (e.g. `openapi-typescript`) into `types/api-generated.ts` and assert the hand types are assignable; CI fails on drift (`52` §4 "type parity").
- Modules already cite spec sections in comments (e.g. `matching.ts` → "Spec 09 §7"); keep that convention.

---

## 6. Routing, code-split, error boundaries (real `App.tsx`)

- Every route is `React.lazy` + `Suspense` (already in use) → keep per-route chunks; Suspense fallback = that surface's **skeleton**, not a global spinner.
- **Build task: route-level error boundary** wrapping each lazy route → `pages/system/RouteErrorPage.tsx` (exists); plus a root boundary. No throw ever yields a white screen.
- Guard wrappers (`RequireAuth`, role guard) per `05` §3 / `50` §2; 401→`/login?next=`, 403→no-access surface.

---

## 7. Error + AI-fallback handling (wire to `50` §3/§6)

- `client.ts` response interceptor maps status → action: 401 refresh-or-login, 403 no-access, 422 → field errors (React Hook Form + Zod), else `detail` → toast (`toast-store`).
- **AI surfaces (`50` §6):** when a response carries `source != "ai"` (rule-based fallback), render the result + a subtle "Showing rule-based result" note (copy per feature doc). A chat turn never shows an error bubble on AI failure — it shows the fallback.

---

## 8. Performance budgets (enforced, not aspirational)

- Targets: **LCP < 2.5s** (4G mid-device), **INP < 200ms**, **CLS < 0.1**.
- **Build task: Lighthouse-CI** in the FE pipeline, soft-fail first then hard-gate; budget JSON in `frontend/lighthouserc.json`.
- Lazy-load heavy deps: `recharts` (analytics `28`/`35`), any editor — dynamic import, never in the main chunk.
- Virtualize lists > 50 rows (pipeline `31`, feed `20`, inbox `17`) — adopt `@tanstack/react-virtual`.
- Europa via Typekit with `font-display: swap` + reserved metrics to avoid CLS (`01` §3).

---

## 9. Realtime client (NEW — does not exist yet; build it)

No realtime dep is installed today. Build `frontend/src/lib/realtime.ts`:
- **SSE** (`EventSource` or `@microsoft/fetch-event-source` for auth headers) for notifications bell + feed "new posts" + chat token streaming (`57` §1, `19`).
- **WebSocket** for messaging (`17`/`29`) — typing, read receipts.
- One reconnecting client with exponential backoff; on event, **patch the Query cache** (`qc.setQueryData`) — never full refetch. Consumed via a `useRealtime()` hook. Full contract in `57`.

---

## 10. Analytics / instrumentation (NEW — build a typed event bus)

Build `frontend/src/lib/analytics.ts`: typed `track(event, props)` emitting funnel events (signup, discover_message_sent, program_saved, application_started, decision_viewed). Feeds product metrics + `56` ranking signals. Consent-gated (`46`): no events when analytics consent is off. Batched + sent to the backend events endpoint (or a provider).

---

## 11. Testing (extend existing vitest setup)

- Vitest + Testing Library + **MSW** for API mocking. Each surface: a smoke test asserting render + the four states (loading/empty/error/success) + the primary action (`53` §5).
- Type-parity test (§5) catches FE/BE drift.
- Critical journeys (`52` §2) → Playwright e2e (post-MVP, high ROI).
- Coverage gate: every `pages/**/*Page.tsx` has ≥1 test.

---

## 12. Build tasks (checklist — what to actually create/change)

- [ ] `api/queryKeys.ts` key factory; migrate inline keys to it.
- [ ] `hooks/useOptimisticMutation.ts`; adopt on the §4 surfaces.
- [ ] `types/api-generated.ts` from OpenAPI + assignability test in CI.
- [ ] Root + per-route error boundaries via `RouteErrorPage`.
- [ ] `lib/realtime.ts` (SSE+WS) + `useRealtime()` (contract in `57`).
- [ ] `lib/analytics.ts` typed event bus, consent-gated.
- [ ] `lighthouserc.json` + Lighthouse-CI step (soft→hard).
- [ ] Virtualize pipeline/feed/inbox lists.
- [ ] Delete stray `api/*\ 2.ts` iCloud copies; add a lint/CI check rejecting filenames matching `* [0-9].*`.
- [ ] `grep` guard in CI: no `apiClient.`/`fetch(` in `pages/`.

---

## 13. Acceptance

- [ ] No server data in Zustand; no `fetch()`/`apiClient` outside `api/`.
- [ ] All §4 surfaces optimistic with rollback; filtered lists `keepPreviousData`.
- [ ] Every route lazy + error-boundaried; no white screen on throw.
- [ ] Query keys come from `queryKeys.ts` (no inline literals).
- [ ] Type-parity CI green; CWV budgets met on staging (Lighthouse-CI).
- [ ] Realtime updates patch cache (no refetch); analytics consent-gated.

---

## 14. Open questions

- `@microsoft/fetch-event-source` vs native `EventSource` (auth header support) — recommend the former for bearer-token SSE.
- `openapi-typescript` vs `orval` for type generation — recommend `openapi-typescript` (types only, no client; we keep hand modules).
- Command palette (`cmdk`) for ⌘K (`53`) — institution Phase-A.
