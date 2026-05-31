# 53 · UX Benchmark & Interaction Standards

> The bar: UniPaith's frontend should feel as polished as **LinkedIn** and **Handshake** — the two platforms our users already compare us to. This doc benchmarks each UniPaith surface against its closest analog on those products and defines the **interaction standards** every screen must meet to feel market-grade, not prototype-grade. It raises the quality ceiling; the feature docs (`08`–`41`) own *what* each screen does, this owns *how good it has to feel*.
>
> Status: **draft v1.0** · 2026-05-30 · Production-parity track. Consumes `02` (design system) + `03` (mobile); read alongside `54` (FE engineering) which makes these standards technically achievable.

---

## 1. Why benchmark against these two

- **Handshake** is the direct category analog (students ↔ institutions, two-sided, profile-driven, recommendations, saved searches + alerts, employer/event following). Users will literally A/B us against it. ([Handshake](https://joinhandshake.com/), [saved searches & alerts](https://support.joinhandshake.com/hc/en-us/articles/218693388-Saving-Job-Searches-and-Receiving-Job-Alerts))
- **LinkedIn** is the gold standard for **profile UX, completeness gamification, feed engagement, and notification polish** — patterns students expect by muscle memory. ([profile strength meter](https://www.linkedin.com/help/linkedin/answer/a594698/viewing-your-profile-strength-meter), [gamification analysis](https://blog.captainup.com/analysis-of-linkedin-driving-engagement-with-gamification/))

We borrow their **interaction quality and proven patterns**, not their visual style — UniPaith stays editorial/Europa (`01`), never generic-SaaS-blue.

---

## 2. Surface-by-surface benchmark

Each row: UniPaith surface → closest LinkedIn/Handshake analog → the parity bar (what "as good as them" concretely means here).

| UniPaith surface | Analog | Parity bar |
|---|---|---|
| Universal Profile (`08`) | LinkedIn profile + strength meter | Section-by-section completeness with **levels** (§6); inline edit-in-place (no separate edit page); reorderable entries; "add X to get to next level" nudges; live preview of how institutions see it. |
| Discover chat (`19`) | (novel) + ChatGPT-grade chat UX | Streaming tokens, typing indicator, stop/regenerate, message actions, artifact rail updating live, never a frozen spinner. |
| Match / Explore (`09`,`10`) | Handshake job search + recs | Typeahead search, **saved searches + alerts** (§7 / Handshake), faceted filters that update results live, "why recommended" transparency, infinite scroll + virtualization. |
| Program / School detail (`11`,`12`) | LinkedIn company page / Handshake employer | Sticky section nav, follow button with instant state, related-programs rail, skeleton that matches final layout, share. |
| Saved (`13`) | LinkedIn saved + Handshake saved | Bulk actions, drag-reorder, compare tray persisting across navigation, one-click → application. |
| Connect feed (`20`) | LinkedIn feed | Ranked (not pure-chrono) feed (§ `56`), optimistic reactions/RSVP, pull-to-refresh, "new posts" pill, infinite scroll. |
| Inbox / Messaging (`17`,`29`) | LinkedIn Messaging | Real-time delivery + read receipts + typing (`57`), thread list ↔ conversation, optimistic send, unread badges, attachment preview. |
| Notifications (`21` + bell) | LinkedIn notification bell | Real-time bell with unread count, grouped/categorized center, mark-all-read, deep-link to source, per-type prefs. |
| Applications / Pipeline (`15`,`31`) | Handshake applications tracker / ATS | Status timeline, Kanban-style stages (institution), bulk actions, saved views/filters, optimistic status changes. |
| Institution dashboard (`31`) | Handshake employer dashboard | KPI cards with sparklines, date-range, drill-down, empty-states that teach the next action. |

---

## 3. Interaction standards (every screen)

These are non-negotiable quality gates. They turn "it works" into "it feels professional."

### 3.1 Optimistic UI
Mutations reflect **instantly**, then reconcile with the server. Save, react, RSVP, follow, mark-read, checklist-toggle, status-change → UI updates on click, rolls back with a toast on failure. (TanStack Query optimistic mutations — `54` §3.) No "click → spinner → result" for cheap mutations; that's the prototype tell.

### 3.2 Loading choreography (skeletons, not spinners)
- **Skeleton screens that match the final layout** (LinkedIn/Handshake do this everywhere) — never a centered spinner on a full page.
- Content-aware: profile skeleton looks like a profile, card grid like cards.
- **Stagger** reveal (50–80ms) so content doesn't pop all at once.
- Spinners only for in-button/inline waits (< 1 element).
- Show cached data immediately + revalidate in background (stale-while-revalidate, `54` §3).

### 3.3 Motion & micro-interaction
- Use `01` §4.4 motion tokens (`--ease-out`, `--dur-fast/base/slow`). Every state change animates (enter/exit, expand/collapse, tab switch, sheet).
- Hover/press feedback on every interactive element (`02`); focus-visible rings.
- Respect `prefers-reduced-motion` (`03` §9).
- **No layout shift** on load (reserve space; CLS budget in `54` §6).

### 3.4 Forms: inline validation + autosave
- Validate **on blur**, not just on submit; show success ticks, not only errors (LinkedIn pattern).
- **Autosave** long forms (profile, essays, program editor) with a visible "Saved · 2s ago"; never lose work to a navigation or refresh.
- Correct keyboards/`inputmode` on mobile (`03` §7); searchable selects for long lists (country, CIP major).
- Field-level errors map from the API 422 envelope (`50` §3).

### 3.5 Lists: infinite scroll + virtualization
- Feed, search results, pipeline, inbox, notifications → infinite scroll with a sentinel, **virtualized beyond ~50 rows** (`54`).
- "New items" pill at top instead of auto-jumping (feed/inbox).
- Preserve scroll position on back-navigation.

### 3.6 Search: typeahead everywhere
- Instant typeahead (debounced 150–250ms) on program/school/institution search and any entity picker.
- Recent + suggested queries on focus; keyboard-navigable results; highlight matched substring (Handshake pattern).
- Empty/no-result states that suggest a next action, never a dead end.

### 3.7 Command & speed
- **Global search** in the top bar on every authenticated page (LinkedIn-style) → programs, schools, institutions, your applications.
- Optional command palette (⌘K) for power users (institution staff especially): jump to applicant, program, segment.
- Keyboard shortcuts documented; `j/k` list nav in pipeline/inbox is a nice-to-have.

### 3.8 Feedback: toasts + confirmations
- Toasts for async results (success/error), bottom (mobile) / top-right (desktop), auto-dismiss + manual close, with an action ("Undo", "View").
- **Undo** for destructive/optimistic actions (delete, unsave, decline) rather than a blocking confirm where possible (Gmail pattern).
- Blocking confirm only for truly irreversible (account deletion, decision release) with typed confirmation (`21`,`34`).

### 3.9 Empty / error / offline
- Every list/surface has a **designed empty state** that teaches the next action (per `52` §3 DoD), not blank space.
- Error states offer retry; never a raw stack or white screen (route error boundary, `54` §5).
- Offline/again-online banners (`03` §8 PWA posture).

---

## 4. Profile experience — match LinkedIn specifically

The profile is the spine; it must feel as good as LinkedIn's because students know that one cold.
- **Edit-in-place**: pencil per section → inline form → save → animates back. No separate `/edit` route.
- **Drag-reorder** entries (activities, work, skills); top items weighted (LinkedIn: top 3 skills carry weight — [source](https://gouravdigitalclub.com/blog/linkedin-profile-optimization/)).
- **Live "how institutions see you" preview** toggle.
- **Add-section suggestions** ("Add research to strengthen your profile") driven by completeness gaps (`08` §15 / `42` outputs).
- **Skills with evidence** (our analog to endorsements): each skill links to evidence (`42` §3.23 skill matrix) — trust signal without the social-spam of endorsements.

---

## 5. Two-sided polish (Handshake parity)

- **Following** (institutions/programs/events) with instant toggle + a "Following" management view (`20` §2) — mirrors Handshake employer-follow → closing-window + event alerts ([source](https://support.joinhandshake.com/hc/en-us/articles/218693388-Saving-Job-Searches-and-Receiving-Job-Alerts)).
- **Recommendations** explained ("recommended because…") on Match + feed — Handshake recommends from interests + activity; we add explainability (`09`).
- **Institution-side responsiveness**: bulk actions, saved filter views, and snappy tables in pipeline/review (`31`,`32`) so staff feel an ATS-grade tool, not a form.

---

## 6. Profile-completeness gamification (LinkedIn model)

Adapt LinkedIn's Beginner → Intermediate → All-Star ladder ([source](http://www.samanthafreedman.com/profile-completion)) to UniPaith's journey:

| Level | UniPaith threshold | Unlocks / nudge |
|---|---|---|
| **Started** | account + 1 discovery message | "Add your goals to see matches." |
| **Match-ready** | meets `42` §6.1 minimum | Match unlocks (`09`); badge + confetti-restrained gold moment (`02` §15). |
| **Apply-ready** | core profile + 1 program's requirements | "You're ready to apply to X." |
| **Standout** | all recommended sections (academics, activities, essays, recommenders, identity) | Higher match confidence; "institutions are more likely to find you." |

- Persistent **completeness ring** (`08`) with "X% · next: add Y."
- Each unlock is a designed moment (animation + copy), not a silent flag — this is the single biggest engagement lever LinkedIn proves ([gamification](https://blog.captainup.com/analysis-of-linkedin-driving-engagement-with-gamification/)).
- **Never dark-pattern**: completeness encourages, never blocks core value or shames.

---

## 7. Saved searches & alerts (Handshake model — net-new UX)

Handshake's most-used retention feature; we should match it (ties `09`,`10`,`56`,`57`):
- Save any Match/Discovery search (criteria, not results) with a toggle.
- Per-saved-search **alerts**: frequency (instant/daily/weekly), pause, delete.
- "New programs match your saved search" → notification (`57`) + Connect feed item (`20`).
- Deadline-closing alerts on followed/saved programs (Handshake's "application window closing").
- Managed in `21` Settings → Alerts, surfaced inline where created.

---

## 8. Accessibility as quality (not just compliance)

Market-grade = accessible by default (`03` §9, WCAG AA): full keyboard operability, visible focus, screen-reader labels on every control + live regions for async updates (toasts, new-message), 44px targets, contrast, reduced-motion. LinkedIn/Handshake are AA; we match.

---

## 9. Per-surface UX acceptance (extends `52` DoD)

A surface is "market-grade" when, beyond `52` §3, it also has: optimistic mutations (§3.1), layout-matched skeletons (§3.2), motion on state changes (§3.3), inline-validate + autosave where it has forms (§3.4), virtualized infinite lists where it has long lists (§3.5), designed empty/error states (§3.9), and keyboard + SR support (§8). Add these as checkboxes to each feature doc's brand/DoD checklist when building.

---

## 10. Open questions

- **Command palette scope** — ship ⌘K for institution staff first (higher power-user density) or both roles at once?
- **Feed ranking aggressiveness** (`56`) — how chrono-vs-ranked for Connect; LinkedIn is heavily ranked, but students may distrust a black-box feed. Recommend ranked-with-"why" + a chrono toggle.
- **Endorsements vs evidence** — confirm we use evidence-linked skills (§4) rather than social endorsements, to avoid LinkedIn's endorsement-spam problem.
- **Confetti/celebration frequency** — define the exact 2–3 moments that earn the gold celebration so it stays rare (`02` §15).

Sources: [Handshake](https://joinhandshake.com/) · [Handshake saved searches/alerts](https://support.joinhandshake.com/hc/en-us/articles/218693388-Saving-Job-Searches-and-Receiving-Job-Alerts) · [LinkedIn profile strength](https://www.linkedin.com/help/linkedin/answer/a594698/viewing-your-profile-strength-meter) · [LinkedIn gamification](https://blog.captainup.com/analysis-of-linkedin-driving-engagement-with-gamification/) · [LinkedIn profile completion UX](http://www.samanthafreedman.com/profile-completion).
