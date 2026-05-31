# 53 · UX Benchmark & Interaction Standards

> Raises every surface to market-grade by benchmarking against the platforms users already compare us to — **LinkedIn** (profile, feed, messaging, notifications) and **Handshake** (the student↔institution two-sided early-career rail). Companion to `02`/`03` (component + responsive rules) and `54` (the FE engineering that delivers these).
>
> Status: **draft v1.0** · 2026-05-30 · Production-parity track. Sets the *experience bar*; `54` sets the *engineering bar* that meets it.

---

## 1. The bar

A UniPaith surface is "market-grade" when a user coming from LinkedIn/Handshake notices **no drop** in responsiveness, polish, or affordance richness. Concretely: instant feedback (optimistic), no dead/blank states, smooth motion, forgiving inputs, "the app already knew what I wanted."

---

## 2. Per-surface benchmark

| UniPaith surface | Benchmarked against | The bar to hit |
|---|---|---|
| Profile (`08`) | LinkedIn profile | Inline-edit each section, completeness meter + nudges, autosave, reorder, instant validation. |
| Discover chat (`19`) | ChatGPT / LinkedIn msg | Streaming tokens, typing indicator, retry, message persistence, artifact rail updates live. |
| Match / Explore (`09`/`10`) | Handshake job search | Typeahead, faceted filters that update counts live, infinite scroll, saved searches + alerts, compare tray. |
| Program/School detail (`11`/`12`) | LinkedIn company page | Sticky section nav, skeleton load, "save" optimistic, related-items rail. |
| Connect feed (`20`) | LinkedIn feed | Ranked, infinite scroll, optimistic react/RSVP, "new posts" pill, seen-state. |
| Inbox/Messaging (`17`/`29`) | LinkedIn messaging | Real-time delivery, unread badges, typing, optimistic send, thread search. |
| Notifications (`21`/`57`) | LinkedIn notifications | Real-time bell, grouped, mark-all-read, deep-link, digest prefs. |
| Pipeline/Review (`31`/`32`) | Greenhouse/Lever ATS | Dense table, bulk select, keyboard nav, saved views, optimistic stage moves. |

---

## 3. Interaction standards (apply everywhere)

- **Optimistic UI**: mutations reflect instantly; reconcile/rollback on server response (`54` TanStack patterns). Save, react, RSVP, stage-move, mark-read.
- **No blank states**: every async region shows skeleton (load) → content / empty / error. Empty states are instructional with a CTA (`02`).
- **Motion**: `02` tokens; 120/200/360ms; respect `prefers-reduced-motion`. Enter/exit on lists, sheets, toasts; never gratuitous.
- **Autosave** on long forms (profile, program editor, essays) with a "saved ·/saving…" indicator; never a lone "Save" that can lose work.
- **Infinite scroll + "jump to top"** for feeds/lists > one page; cursor-paginated (`50` §5); preserve scroll on back.
- **Typeahead** on search + entity pickers (program, major CIP, country) — debounced 200ms, keyboarded, ≤150ms perceived.
- **Forgiving inputs**: inline validation on blur, scroll-to-first-error on submit, correct `inputmode`/keyboard, paste-friendly.
- **Completeness gamification** (profile, application): ring + "what's next" queue (LinkedIn-style) — drives the activation loop.
- **Saved searches + alerts** (`56`): any filter set is saveable; new matches notify (`57`).
- **Keyboard**: focus rings, tab order, ⌘K command palette (institution power users), table arrow-nav.

---

## 4. Empty / first-run polish

First-run is the highest-churn moment. Each surface defines: an instructional empty state, a seeded "try this" affordance, and a path to value in ≤2 clicks. Student first-run → Discover chat (`19`); institution first-run → setup wizard (`30`).

---

## 5. Acceptance

- [ ] Every mutation is optimistic or shows ≤1 spinner with skeleton, never a blank flash.
- [ ] Every list > 1 page: infinite scroll + restored scroll position.
- [ ] Search + every entity picker has debounced typeahead.
- [ ] Long forms autosave with status.
- [ ] Feeds/messaging/notifications update in real time (`57`).
- [ ] `prefers-reduced-motion` honored; motion uses `02` tokens.
- [ ] Each surface passes its row-3 benchmark in a side-by-side click test vs the named competitor.

---

## 6. Open questions

- ⌘K command palette scope (institution-only vs both) — recommend institution Phase-A, student later.
- Feed ranking ownership lives in `56`; this doc only sets the *interaction* bar.
