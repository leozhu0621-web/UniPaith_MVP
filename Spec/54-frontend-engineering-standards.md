# 54 · Frontend Engineering Standards

> The production-grade FE architecture that delivers the `53` experience bar on the existing React 19 + Vite + Tailwind + Zustand + TanStack Query stack. Companion to `02`/`03` (design) and `50` (API contract).
>
> Status: **draft v1.0** · 2026-05-30 · Production-parity track.

---

## 1. State layering (one rule per kind)

- **Server state → TanStack Query.** All API data. Never mirror server data into Zustand.
- **Global UI/auth state → Zustand** (`auth-store`, theme, command-palette, toast). Small, synchronous.
- **URL state → router** (tab, filters, search, compare set, open thread) — shareable/bookmarkable (`05` §13).
- **Local component state → useState** (transient toggles only).

## 2. TanStack Query patterns

- Query keys = `[resource, params]`, params the full filter object (cache correctness).
- **Optimistic mutations**: `onMutate` snapshot + cache patch → `onError` rollback → `onSettled` invalidate. Standard for save/react/RSVP/stage-move/mark-read (`53` §3).
- `staleTime` per resource (reference data long, feeds short); `placeholderData: keepPreviousData` for paginated/filtered lists (no flash).
- Infinite queries (`useInfiniteQuery`) for feeds/lists; cursor from `50` §5.
- Prefetch on hover/intent for detail pages.

## 3. Code structure

- **Route-level code splitting** (`React.lazy` + Suspense) — already in use; keep per-route chunks.
- `src/api/<domain>.ts` — one module per backend router (`50` §7); screens call modules, never `client` directly.
- `src/types/` — TS types mirror backend Pydantic response field-for-field (`50` §7; CLAUDE.md "fields invisible otherwise").
- Feature-folder layout per `pages/student/<feature>/` (existing convention).

## 4. Resilience

- **Error boundaries** per route + a root boundary → `RouteErrorPage` (exists); never a white screen.
- **Suspense fallbacks** = the surface's skeleton, not a global spinner.
- API errors surfaced via the `50` §3 interceptor → toast/inline; 401→login, 403→no-access, 422→field errors.
- **AI fallback** (`50` §6): render the rule-based result + "showing rule-based" note; never error a chat turn.

## 5. Performance budgets (Core Web Vitals)

- LCP < 2.5s (4G mid-device), INP < 200ms, CLS < 0.1.
- Route JS budget; lazy-load heavy deps (charts, editor). Virtualize lists > 50 rows.
- Images: responsive `srcset`; brand uses no decorative imagery so payload is type+data — keep it lean.
- Typekit (Europa) loaded with `font-display: swap`; reserve space to avoid CLS.

## 6. Realtime client

- SSE for notifications, WebSocket for messaging (`57`); a single reconnecting client with backoff; updates patch the Query cache (no full refetch).

## 7. Analytics & instrumentation

- Typed event bus; emit on key funnel actions (signup, discover-message, save, apply, decision). Feeds product metrics + `56` ranking signals. Respect consent (`46`).

## 8. Testing

- Vitest + Testing Library: each surface has a smoke test (renders, loading/empty/error states, primary action).
- MSW for API mocking in tests; type-level parity test catches FE/BE field drift.
- Critical journeys (`52` §2) → Playwright e2e (post-MVP nicety, high ROI).

## 9. Acceptance

- [ ] No server data in Zustand; no `fetch()` outside api-modules.
- [ ] Mutations optimistic with rollback; lists keepPreviousData.
- [ ] Every route lazy-loaded + error-boundaried; no white screen on throw.
- [ ] CWV budgets met on staging (Lighthouse CI).
- [ ] Realtime updates patch cache, don't refetch.
- [ ] Type-parity check green.

## 10. Open questions

- Lighthouse-CI gate in CI/CD — recommend yes, soft-fail first.
- Command palette lib (cmdk) — adopt for ⌘K (`53`).
