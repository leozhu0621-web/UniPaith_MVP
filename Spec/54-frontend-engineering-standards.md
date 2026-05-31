# 54 · Frontend Engineering Standards

> The technical foundation that makes `53`'s UX bar actually achievable and maintainable at scale. How the React app is architected, how server state is cached and synced, how it stays fast (Core Web Vitals), and how it's tested — at the level a LinkedIn/Handshake-grade SPA requires. Stack is fixed (`CLAUDE.md`): React 19 + TypeScript + Vite + Tailwind + Zustand + TanStack Query.
>
> Status: **draft v1.0** · 2026-05-30 · Production-parity track. Pairs with `53` (UX), `50` (API contract the client wires to), `02`/`03` (design system).

---

## 1. Architecture layering

```
pages/         route-level screens (per 05 IA); thin — compose features + call hooks
features/      domain UI (match, discover, pipeline, review…) — the real components
api/           one module per backend router (50 §7); typed fns over the Axios client
hooks/         TanStack Query hooks (useMatches, useProfile…) wrapping api/ fns
stores/        Zustand: auth + ephemeral global UI only (NOT server data)
components/ui/  design-system primitives (02) — Button, Card, Sheet, Toast, Skeleton…
types/         TS types mirroring backend Pydantic responses (50 §7)
lib/           cross-cutting (queryClient, realtime, analytics, format)
```
**Rule:** screens call hooks, hooks call api modules, api modules call the client. No `fetch`/`client` calls inside components. No server data in Zustand (that's TanStack Query's job).

---

## 2. State: the three kinds, kept separate

| Kind | Tool | Examples |
|---|---|---|
| **Server state** | TanStack Query | profile, matches, applications, feed, notifications — anything from the API |
| **Global UI state** | Zustand | auth token/role, theme, command-palette open, compare-tray contents |
| **Local UI state** | `useState`/`useReducer` | a modal open, form draft, hover |
| **URL state** | router params/search | tab, filters, search query, compare set (`05` §13) — shareable/bookmarkable |

Never duplicate server data into Zustand — derive from the query cache. This is the single biggest source of stale-UI bugs in SPAs.

---

## 3. TanStack Query patterns (the heart of perceived speed)

- **Query keys**: structured + hierarchical — `['matches', {filters}]`, `['application', id]`. Document the key namespace in `lib/queryKeys.ts` so invalidation is precise.
- **Stale-while-revalidate**: sensible `staleTime` per resource (profile 30s, programs 5m, notifications 0/realtime). Show cached instantly, revalidate in background (`53` §3.2).
- **Optimistic mutations** (powers `53` §3.1): `onMutate` snapshot → patch cache → `onError` rollback → `onSettled` invalidate. Standard wrapper in `lib/optimistic.ts` so every mutation does it consistently.
- **Invalidation map**: mutations invalidate the right keys. Profile edit → invalidate `['matches']` + `['profile']` (mirrors the backend version-bump cache invalidation, `45` §12 / `51` §9). Maintain an explicit "this mutation invalidates these queries" table.
- **Prefetch on intent**: hover/focus a program card → `prefetchQuery(['program', id])` so detail opens instantly (LinkedIn/Handshake do this).
- **Pagination**: `useInfiniteQuery` for feed/search/pipeline/inbox; `getNextPageParam` from the `{total,limit,offset}` or `next_cursor` envelope (`50` §5).
- **Dependent/parallel** queries handled explicitly; avoid waterfalls (fetch in parallel where independent).

---

## 4. Routing & code-splitting

- React Router with **route-level `lazy()` + Suspense** (the app already uses Suspense lazy imports — `CLAUDE.md`). Each top-level route is its own chunk.
- Role-guarded route trees (`05` §3): `RequireAuth` + role check wrap `/s/*` and `/i/*`.
- Preload the next-likely route on idle (e.g., after login, prefetch the role home).
- Keep the initial bundle lean: defer institution-app chunks for students and vice-versa.

---

## 5. Resilience: error boundaries + Suspense

- **Route-level error boundary** (`system/RouteErrorPage` exists) catches render errors → friendly retry, never a white screen.
- **Feature-level boundaries** around risky widgets (AI rationale, charts) so one failure doesn't take the page.
- Suspense fallbacks = the layout-matched skeletons from `53` §3.2.
- Query errors surface via the `50` §3 envelope → inline/toast; 401 → global redirect interceptor.

---

## 6. Performance budgets (Core Web Vitals — LinkedIn/Handshake grade)

Hard budgets; CI-checkable via Lighthouse:
| Metric | Budget | How |
|---|---|---|
| **LCP** | < 2.5s (4G, mid device) | code-split, skeletons, prefetch, CDN |
| **CLS** | < 0.1 | reserve space for images/cards; no layout-shift on load (`53` §3.3) |
| **INP** | < 200ms | optimistic UI, virtualization, debounce, avoid main-thread blocking |
| **TTI** | < 3s mobile | route chunks, defer non-critical |
| **Initial JS** | < ~250KB gz/route | per-route budget; analyze with `vite-bundle-visualizer` |

- **Virtualize** lists > ~50 rows (`@tanstack/react-virtual`) — feed, pipeline, inbox, search.
- **Images**: responsive `srcset`, lazy-load below fold, explicit dimensions (CLS). Brand uses no decorative imagery (`01`) so payload is mostly type + data — keep it that way.
- **Fonts**: Europa via Typekit (`01` §3); `font-display: swap`; preconnect to `use.typekit.net`; system-ui fallback metrics-matched to avoid FOUT shift.
- **Memoization** where it pays (big lists, expensive derive); don't over-memo.

---

## 7. Realtime client (powers `53` §3.1 messaging/notifications)

- A single `lib/realtime.ts` manages the SSE connection (notifications, live match updates) and the WebSocket (messaging) per `57`.
- On event → update the TanStack Query cache directly (`setQueryData`) so UI reacts without a refetch; fall back to polling if the connection drops.
- Reconnect with backoff; surface connection state subtly (a dot), never a blocking error.

---

## 8. Design-system implementation (`02`/`03`)

- Tailwind config consumes the `01` tokens (no hardcoded hex/px in components).
- `components/ui/` primitives are the ONLY place raw styling lives; features compose primitives.
- Every primitive: keyboard + focus-visible + ARIA baked in (`53` §8) so accessibility is free at the feature level.
- Dark theme via `[data-theme]` (`01` §11); test both.

---

## 9. Analytics & instrumentation (so product/UX decisions are data-driven)

- A typed `lib/analytics.ts` `track(event, props)` — one call site pattern; events defined in a registry (mirror the `44` §8 engagement signals so frontend + backend agree on event names).
- Instrument: page views, key funnel steps (discover→match→save→apply), feature usage, AI-result accept/reject (`50` §6 feedback), errors.
- Respect consent (`46`): no analytics beyond essential without `consent.analytics`.
- Web-vitals reported to the backend/observability (`55`) for real-user monitoring (RUM), not just lab Lighthouse.

---

## 10. Testing (the `52` quality gate, frontend side)

- **Unit/component**: Vitest + Testing Library (`CLAUDE.md`) — every primitive + critical feature component; test states (loading/empty/error/success), not just happy path.
- **Hook tests**: query/mutation hooks with a mock server (MSW) — optimistic + rollback paths.
- **E2E**: Playwright for the two `52` §2 critical journeys (student + institution) — the acceptance core, runnable in CI.
- **Visual regression** (optional, high ROI): snapshot key surfaces to catch unintended UI drift.
- **a11y in CI**: `axe` on key pages fails the build on AA violations.
- Type-check is a gate (`tsc -b`); a missing backend field shows up as a type error (`50` §7).

---

## 11. Code quality & DX

- ESLint + Prettier (`make lint`); strict TS (`noUncheckedIndexedAccess`, no `any` in committed code).
- Conventional file structure (§1); colocate tests with components.
- No prop-drilling deeper than 2 — lift to a hook or context.
- Feature flags read from a typed config (mirror backend flags `50` §6) so AI/experimental UI can ship dark.

---

## 12. Open questions

- **Realtime transport** final call (SSE vs WS split) — defer to `57`; the client wrapper (§7) abstracts it either way.
- **RUM destination** — send web-vitals to the same observability stack as backend (`55`) or a dedicated FE tool? Recommend unified.
- **Bundle budget enforcement** — wire a CI check (size-limit) so budgets in §6 don't silently rot.
- **Component library extraction** — once `components/ui` stabilizes, consider Storybook for the design system (`02`) to keep parity as the team grows.

Sources: [Node/SPA production checklist 2026](https://workforcenext.in/blog/nodejs-performance-scaling-production-checklist-2026/) · [scalable SaaS guide](https://dev.to/thebitforge/building-scalable-saas-products-a-developers-guide-48a7).
