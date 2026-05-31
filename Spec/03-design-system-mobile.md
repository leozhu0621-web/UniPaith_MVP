# 03 · Design System — Mobile & Responsive

> How every surface behaves below desktop width. Breakpoints, mobile navigation, touch ergonomics, and the responsive transform for each complex pattern (chat, rails, compare tray, pipeline, calendar, tables). Companion to `02-design-system.md` (component rules) and `01-brand-tokens.md` (tokens). Recommended by `05` §14.
>
> Status: **draft v1.0** · 2026-05-29 · Applies to both `/s` and `/i`. Mobile-first principle: design the small screen, enhance up.

---

## 1. Why this matters for the MVP

Students are mobile-majority — discovery, deadline checks, RSVP, messaging, and decision moments happen on phones. Institution staff are desktop-majority but need read + quick-reply on mobile. So: **student surfaces must be fully usable on mobile; institution surfaces must be readable + support light actions (reply, assign, nudge) on mobile, with heavy authoring (program editor, rubric, segment builder) acceptable as desktop-first.**

---

## 2. Breakpoints (from `05` §14, canonical here)

| Token | Min width | Primary behavior |
|---|---|---|
| `base` | 0 | Single column. Bottom tab bar. Rails → sheets. |
| `sm` | 640px | Larger type/spacing; still single column; hamburger/bottom-bar nav. |
| `md` | 768px | Two-column layouts begin; rails open as sheets, not docked. |
| `lg` | 1024px | Desktop layout; top nav; docked rails. |
| `xl` | 1280px | Discovery artifact rail docks permanently. |
| `2xl` | 1440px | Pipeline / Applications go full-width. |

Tailwind defaults align with these — use Tailwind's `sm/md/lg/xl/2xl` directly; do not invent custom breakpoints.

---

## 3. Mobile navigation

### 3.1 Student — bottom tab bar (base–md)
The four stages become a fixed bottom tab bar (thumb-reachable), replacing the desktop top nav:
```
┌──────────────────────────────────────────────┐
│                  (page content)               │
│                                               │
├──────────────────────────────────────────────┤
│  ◎        ◇         ▣         ⬡       ⦿       │
│ Discover  Match    Apply    Connect  (avatar) │
└──────────────────────────────────────────────┘
```
- 56px tall, `--bg` + top hairline `--border-hair`.
- Active tab: `--secondary` icon + label; inactive `--fg-muted`.
- The avatar tab opens a sheet: Profile · Saved · Settings · Sign out.
- No gold in the bar (it's chrome). Badge dots use `--secondary` (or `--warning` for action-needed).

### 3.2 Institution — hamburger + section sheet (base–md)
Institution has more top-level surfaces and is desktop-leaning, so mobile uses a top bar + hamburger that opens a full-height nav sheet (Admissions / Outreach / Communications / Programs + their sub-tabs as an accordion).

### 3.3 Sub-tabs on mobile
Desktop sub-tabs (`?tab=`) become a horizontally scrollable segmented control under the page title, or a select dropdown when >4 tabs. Selection still writes `?tab=` (deep-linkable).

---

## 4. Touch ergonomics

- **Minimum touch target 44×44px** (also an accessibility requirement — see `design:accessibility-review` / WCAG 2.5.5). Applies to icon buttons, chips, tab targets, calendar cells.
- **Spacing** between adjacent tappable targets ≥ 8px (`--space-2`).
- **Primary action reachable** in the thumb zone (bottom third) — sticky action bars for multi-step forms.
- **Hover-only affordances must have a tap equivalent** — e.g., the AI Rationale Popover (`02` §6) opens on tap (not hover) on touch devices; "Why this match" is a tappable link, not a hover reveal.
- **No drag-only interactions** without a tap fallback (the compare tray "drag to add" must also have an "Add" button).

---

## 5. Responsive transforms per pattern

The hard part — what each complex desktop pattern becomes on mobile:

| Desktop pattern | Mobile (base–md) |
|---|---|
| **Discover: chat + artifact rail** (`19`) | Chat is full-screen. Artifact rail → a "Your profile so far" **bottom sheet** with a peek handle; pull up to see live extractions. A badge on the handle pulses when a new artifact is written. |
| **Match: strategy + results grid** (`09`/`10`) | Strategy card collapses to a one-line summary (tap to expand sheet). Results grid → single-column cards. Filters → full-screen filter sheet via a "Filters (3)" button. |
| **Compare tray** (`10`/`13`) | Persistent bottom pill "Compare (3)"; tap → full-screen compare table that scrolls horizontally, first column (criteria) pinned. |
| **Program/School detail** (`11`/`12`) | Single column; the sticky right-rail summary (cost/deadline/match) becomes a **sticky bottom action bar** (Save · Apply · key stat). Sections stack; in-page jump via a sticky section chip-scroller. |
| **Applications workspace** (`15`) | Tabs → segmented scroller; checklist full-width; document actions in a sheet. |
| **Calendar** (`16`) | Default to **agenda/list view** on mobile (month grid is unusable small); month grid available via toggle but read-only-ish (tap a day → that day's agenda). |
| **Inbox / Messaging** (`17`/`29`) | List ↔ thread are **separate full screens** (list → tap → thread → back). Context panel (`29`) becomes a collapsible accordion above the reply box. Reply box sticky at bottom above the keyboard. |
| **Connect** (`20`) | Tabs as segmented scroller; single-column feed; event RSVP inline; peer cards single column. |
| **Institution Pipeline** (`31`) | Table → **stacked cards** (applicant name, stage, key flags, one-tap open). Filters/saved-views in a sheet. Bulk-select via long-press → action bar. |
| **Review workspace** (`32`) | Read packet + rubric stack vertically; rubric scoring as a sticky bottom mini-form. Heavy committee compare = desktop-recommended (show a "best on larger screen" hint). |
| **Program editor / Segment builder / Data upload** (`23`/`26`/`24`) | Functional but desktop-recommended; on mobile, render as long single-column forms with section accordions; show a non-blocking "easier on desktop" hint. |
| **Dashboards / analytics** (`28`/`35`) | KPI cards stack 1-up; charts become horizontally scrollable or swap to a compact sparkline + tap-for-detail. |
| **Tables (generic, `02` §10)** | Either horizontal scroll with a pinned first column, OR card-per-row. Prefer card-per-row for student-facing; scroll for dense institution data. |

---

## 6. Sheets vs modals

- **Bottom sheet** is the mobile default for: filters, artifact rail, compare, event detail, day agenda, action menus. Drag-to-dismiss + backdrop tap.
- **Full-screen modal** for: focused creation flows, AI rationale on small screens if content is long, image/portfolio viewers.
- **Avoid desktop center-modals on mobile** — they get cramped; promote to full-screen or bottom sheet.
- Respect `--dur-base` (200ms) `--ease-out` for sheet transitions (`01` §4.4); `--dur-slow` (360ms) for full-screen.

---

## 7. Forms on mobile

- One column always; labels above inputs.
- Correct input types/`inputmode` (email, tel, numeric) to get the right keyboard.
- Sticky "Save"/"Continue" bar; show validation inline, scroll-to-first-error on submit.
- Long pickers (country, major CIP) → searchable full-screen select.
- File upload supports camera capture (transcript photo → OCR path, `44`/`45`).
- Autosave drafts (profile, essays) so keyboard interruptions/app-switches don't lose work.

---

## 8. Performance & PWA posture

- Mobile budget: first meaningful paint < 2.5s on a mid-tier device / 4G; route-level code splitting (the app already uses Suspense lazy imports).
- Images: responsive `srcset`; the brand uses no decorative imagery (project rule) so payload is mostly type + data — keep it that way.
- Lists virtualize beyond ~50 rows (feed, pipeline, inbox).
- **PWA (light):** installable manifest + offline shell for already-loaded data is a reasonable fast-follow; full offline mode is deferred (`49`). Add the manifest + theme-color (`01` §7.3) now; service-worker caching later.

---

## 9. Accessibility on mobile (cross-ref)

- 44px targets (§4) double as WCAG 2.5.5.
- Respect `prefers-reduced-motion` — disable the artifact-rail pulse + sheet spring.
- Dynamic type: layouts must not break at 200% text zoom; avoid fixed-height text containers.
- Focus management when sheets/modals open/close (trap + restore).
- Full audit via the `design:accessibility-review` skill before launch.

---

## 10. Brand compliance on mobile

- Wordmark: below 80px wide, switch to the **UP monogram** (`01` §7.4) — the mobile top bar / splash uses the monogram, not the full wordmark.
- Type scale steps down one notch on `base` (Display 72→48, H1 48→32) to avoid overflow; tracking unchanged.
- Gold stays rare (caps/celebration/one earned accent per view) — even scarcer on small screens.
- Dark theme parity: all mobile transforms work in `[data-theme="dark"]`.

---

## 11. Gaps (relative to current code)

- No mobile nav (bottom tab bar / hamburger sheet) implemented — current app is desktop-first.
- Calendar lacks a mobile agenda default.
- Inbox/Pipeline are not yet card-collapsing on mobile.
- PWA manifest + theme-color not yet added (`01` §7.3).
- Add to `47` as a mobile-readiness workstream (parallelizable, post-core).

---

## 12. Tests

- Each student route usable at 360px width (no horizontal scroll except intended compare/table).
- Bottom tab bar navigates + preserves `?tab=` deep links.
- Artifact rail → bottom sheet on `base`; docks at `xl`.
- Calendar defaults to agenda on mobile.
- Inbox list↔thread as separate screens; reply bar sticky above keyboard.
- All tap targets ≥ 44px (automated audit).
- `prefers-reduced-motion` disables pulses/springs.
- Layouts hold at 200% zoom + dark theme.

---

## 13. Open questions

- **Native app vs PWA.** `49` defers a native reviewer app. For students, a PWA likely suffices for MVP; revisit if push-notification reliability demands native.
- **Institution mobile depth.** How much authoring to support on mobile vs gate to desktop? Recommend: read+reply+assign+nudge on mobile; full authoring desktop-first with graceful (if cramped) mobile fallback.
- **Offline scope.** Which data is cached offline first? Likely: saved programs, application checklists, calendar agenda. Sequence in the PWA fast-follow.
