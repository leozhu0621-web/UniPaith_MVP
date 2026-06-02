# 53 · UX Benchmark & Interaction — Build Spec

> Buildable interaction spec: each surface gets a concrete benchmark, the real page file it lives in, the interaction contract to implement, and acceptance. Benchmarked against **LinkedIn** (profile, feed, messaging, notifications) and **Handshake** (two-sided early-career rail). Companion to `02`/`03` (components/responsive), `54` (the FE engineering that delivers these).
>
> Status: **draft v2.0** · 2026-05-30 · v2 ties the experience bar to real page files + build contracts. Sets the *experience* bar; `54` sets the *engineering* bar.

---

## 1. The bar

A surface is "market-grade" when a user from LinkedIn/Handshake notices **no drop** in responsiveness or polish: instant (optimistic) feedback, no blank states, smooth motion, forgiving inputs, "the app already knew what I wanted."

---

## 2. Per-surface build contract (real files)

Each row: the real page file (`frontend/src/pages/...`), the benchmark, and the concrete interaction work.

| Surface | Real file(s) | Benchmark | Build contract |
|---|---|---|---|
| Profile (`08`) | `student/ProfilePage.tsx`, `profile/*Tab.tsx` | LinkedIn profile | Inline-edit per section; completeness ring + "what's next"; **autosave** w/ "saving…/saved" (`54` §4 optimistic); reorder; inline validation. |
| Discover chat (`19`) | `student/DiscoverHomePage.tsx`, `discover/ChatPanel.tsx`, `ArtifactRail.tsx` | ChatGPT / LinkedIn msg | **Token streaming** (SSE `57`); typing indicator; retry; persisted turns; artifact rail patches live on each extracted signal. |
| Match / Explore (`09`/`10`) | `student/ExplorePage.tsx`, `match/*`, `explore/*` | Handshake search | Typeahead; facet filters w/ **live counts**; `useInfiniteQuery` scroll; saved searches+alerts (`56`); compare tray (`compare-store`). |
| Program/School detail (`11`/`12`) | `student/ProgramDetailPage.tsx`, `program/*`, `InstitutionDetailPage.tsx` | LinkedIn company page | Sticky section nav; **skeleton** load (not spinner); optimistic Save; related-items rail; provenance captions (`60`). |
| Connect feed (`20`) | `student/PostsPage.tsx`, `explore/cards/*` | LinkedIn feed | Ranked (`56`), infinite scroll, **optimistic react/RSVP**, "new posts" pill, seen-state. |
| Inbox / Messaging (`17`/`29`) | `student/MessagesPage.tsx`, `institution/MessagingPage.tsx` | LinkedIn messaging | **Real-time** delivery (WS `57`), unread badges, typing, optimistic send, thread search; list↔thread are full-screens on mobile (`03`). |
| Notifications (`21`/`57`) | bell component + center | LinkedIn notifications | Real-time bell (SSE), grouped, mark-all-read (syncs tabs), deep-link, digest prefs. |
| Pipeline / Review (`31`/`32`) | `institution/PipelinePage.tsx`, `StudentDetailPage.tsx` | Greenhouse/Lever ATS | Dense **virtualized** table (`54` §8), bulk-select, keyboard nav, saved views, **optimistic stage moves**, ⌘K (institution). |

---

## 3. Interaction standards (apply everywhere — each is a `54` mechanism)

- **Optimistic UI** → `54` §4 `useOptimisticMutation` (save, react, RSVP, stage-move, mark-read).
- **No blank states** → every async region: skeleton → content/empty/error; empty states instructional w/ CTA (`02`). Suspense fallback = the skeleton (`54` §6).
- **Motion** → `02` tokens (120/200/360ms), `prefers-reduced-motion` honored; enter/exit on lists/sheets/toasts.
- **Autosave** on long forms (profile, program editor `23`, essays `14`) w/ status indicator; never a lone Save that can lose work.
- **Infinite scroll + restore position** for any list > 1 page; cursor-paginated (`50` §5, `54` §3).
- **Typeahead** on search + entity pickers (program, CIP major, country) — debounced 200ms, keyboarded, ≤150ms perceived.
- **Forgiving inputs** — inline validation on blur, scroll-to-first-error, correct `inputmode`, paste-friendly (`54` §7 422 mapping).
- **Completeness gamification** (profile, application) — ring + "what's next" queue.
- **Saved searches + alerts** (`56`) — any filter set saveable; new matches notify (`57`).
- **Keyboard** — focus rings, tab order, ⌘K palette (institution; `cmdk`), table arrow-nav.

---

## 4. Empty / first-run polish (highest-churn moment)

Each surface defines: an instructional empty state, a seeded "try this" affordance, path to value in ≤2 clicks. Student first-run → Discover chat (`19`); institution first-run → setup wizard (`30`, `institution/SetupPage.tsx`). Build task: an empty-state component per surface, not a generic "no data".

---

## 5. Acceptance (side-by-side click test vs the named competitor)

- [ ] Every mutation optimistic or ≤1 skeleton, never a blank flash.
- [ ] Every list > 1 page: infinite scroll + restored scroll on back.
- [ ] Search + every entity picker has debounced typeahead.
- [ ] Long forms autosave with status.
- [ ] Feeds/messaging/notifications update in real time (`57`).
- [ ] `prefers-reduced-motion` honored; motion uses `02` tokens.
- [ ] Each §2 surface passes its benchmark in a side-by-side click test vs the named competitor.

---

## 6. Open questions

- ⌘K scope (institution-only vs both) — institution Phase-A.
- Feed ranking lives in `56`; this doc sets only the interaction bar.
