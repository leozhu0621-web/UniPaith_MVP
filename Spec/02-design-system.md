# 02 · Design System

> Component-level rules built on top of `01-brand-tokens.md`. Every screen in the MVP composes from this library. If you need a component that isn't here, add it to this file before building it.
>
> Status: **draft v1.0** · 2026-05-29 · Depends on `01-brand-tokens.md` · Used by every feature spec (10–35).

---

## 1. How to read this file

Each component section follows the same anatomy:
1. **Use** — when to reach for it.
2. **Anatomy** — labeled regions of the component.
3. **Variants** — distinct shapes the component takes.
4. **States** — interactive states (default / hover / focus / active / disabled / loading).
5. **Tokens** — exact CSS variables and spacing values consumed.
6. **Do / Don't** — paired examples; the Don't always includes a one-line reason.
7. **A11y** — keyboard, screen-reader, contrast notes.

Voice for component rules is **prescriptive**. Imperative voice. "Use X" / "Never do Y."

---

## 2. Buttons

### Use
Primary actions and inline links that need to look like buttons. For navigational text that should look like a link, use the `link` component (§3).

### Anatomy
```
┌─────────────────────────────┐
│  [icon?]   Label   [icon?]  │
└─────────────────────────────┘
```
Icon-left for "back/next" semantics; icon-right for chevrons/expand.

### Variants
| Variant | Background | Text | Border | Use |
|---|---|---|---|---|
| `primary` | `--primary` (gold) | `--on-primary` (ink) | none | The single most important CTA on the surface. Rare. |
| `secondary` | `--secondary` (cobalt) | `--on-secondary` (paper) | none | Most actions: Save, Submit, Continue, Send. |
| `tertiary` | transparent | `--secondary` | `1px solid --border` | Cancel, secondary actions next to a primary/secondary. |
| `ghost` | transparent | `--text` | none | Toolbar buttons, kebab triggers, inline actions in tables. |
| `destructive` | `--error` | `white` | none | Delete, Remove, Withdraw. Always pair with a confirmation pattern (§5). |
| `link` | transparent | `--accent` | none, underline on hover | Inline link inside paragraphs. |

### Sizes
| Size | Height | Padding-x | Type | Use |
|---|---|---|---|---|
| `sm` | 32px | 12px | `label` 13/600 | Toolbar, table-row actions. |
| `md` | 40px | 16px | `label` 13/600 | Default. |
| `lg` | 48px | 24px | `body` 16/600 | Hero CTAs, form-final submits. |

### States
- **default** → resting style above.
- **hover** → background shifts 1 step on the OKLCH lightness axis (gold → `#F5C800`, cobalt → `#1F58B5`). Border-color step for outlined variants.
- **focus-visible** → `0 0 0 2px var(--ring)`, no outline; ring is gold even on cobalt buttons (focus is brand-accented).
- **active** → background shifts another step; subtle 1px translate-y.
- **disabled** → `opacity: 0.5`; cursor not-allowed; no hover state.
- **loading** → spinner replaces icon-left (or appears at center if no label); button text dims to 0.6 opacity but layout doesn't shift. Use `aria-busy`.

### Tokens
Radius `--radius` (12px). Gap between icon and label: 8px. Min-width: none (let content size).

### Do / Don't
- **Do** keep at most **one primary** button per visible surface region.
- **Don't** put two gold buttons next to each other — the brand pair rule says gold is punctuation. *Reason:* it stops feeling earned.
- **Do** use `secondary` (cobalt) for most "main" actions; reserve `primary` (gold) for the single accent moment.
- **Don't** add custom box-shadows; if elevation is needed, the surface holding the button gets `elev-raised`, not the button.

### A11y
- Minimum 44×44px hit target — `sm` buttons get an invisible 12px padding to meet this.
- `<button>` semantics; never a clickable `<div>`.
- Loading buttons set `aria-busy="true"` and `aria-disabled="true"`.

---

## 3. Links

Inline navigation in paragraph copy. Color `--accent`. Underline only on hover. Visited state matches default (no purple). Two patterns:

- **Plain link** — text only.
- **Story link** (existing in `index.css` as `.story-link`) — animated underline that slides on hover. Use on hero/feature cards where the link is the primary affordance.

---

## 4. Inputs

### Use
All text/number/email/password/date entry. Use `textarea` for multi-line, `select` for fixed options, `combobox` for searchable options.

### Anatomy
```
[ Label ]                              ← `label` token, --text-mut
┌─────────────────────────────────────┐
│ [icon?]  value or placeholder      │← input
└─────────────────────────────────────┘
 ↑ helper text, --text-mut, --small
```

### Variants
- `text` · `email` · `number` · `password` · `search` · `tel` · `url` · `date` · `datetime-local`
- Multi-line: `textarea` (auto-grow up to 8 rows then scroll).
- Selectable: `select` (native) for ≤ 7 options; `combobox` (custom) for searchable lists ≥ 8 or async-fetched.

### States
- **default** → 1px `--border`, `--surface` bg, `--text` color, 12px radius.
- **hover** → border-color steps one notch darker.
- **focus-visible** → 2px `--ring` outline, 0 offset, border becomes `--accent`.
- **filled** → identical to default. Don't change the look once content arrives.
- **disabled** → `--muted` background, `--text-mut` color, no border-color change, cursor not-allowed.
- **error** → border `--error`, `--error-soft` background, helper text `--error`.
- **success** → border `--success`, helper text `--success`. Use only for transient confirmations (saved, verified) — not as a permanent green.

### Sizing
| Size | Height | Type | Use |
|---|---|---|---|
| `sm` | 32px | `small` | Filters, table-row edits. |
| `md` | 40px | `body` | Default. |
| `lg` | 48px | `body` | Hero entries (Discovery search bar). |

### Do / Don't
- **Do** keep labels left-aligned above the input (not placeholder-as-label).
- **Don't** rely on placeholder alone to communicate the field — it disappears the moment the user types. *Reason:* accessibility and recoverability.
- **Do** show the helper text region always (`min-height` for it) so error appearance doesn't shift layout.

### A11y
- Every input has a `<label>` associated by `htmlFor`.
- Errors set `aria-invalid="true"` and `aria-describedby={helperId}`.
- Required fields use `aria-required="true"` and a literal `*` in the label, not red color alone.

---

## 5. Cards

### Use
Group related content. Default container for a program, a school, an application, a message thread, etc.

### Variants
| Variant | Background | Elevation | Border | Use |
|---|---|---|---|---|
| `card` | `--surface` | `elev-subtle` | 1px `--border` | Default. |
| `card-flush` | `--bg` | none | 1px `--border` | Inside a wider card; nested grouping. |
| `card-raised` | `--surface` | `elev-raised` | none | Hovered cards, dropdown menus, modal triggers. |
| `card-accent` | `--surface` | `elev-glow` | 2px `--primary` | The one "this is THE focus" card on the screen. Rare. |

### Anatomy
- **Header** — optional. Eyebrow + H3 + meta row.
- **Body** — primary content.
- **Footer** — actions and metadata.

Padding default: 24px on each side. `sm` cards (e.g., compact program cards in a 4-col grid) use 16px.

### Display card pattern (CRITICAL — used everywhere)

The Master Paper specifies a **single display card schema** for programs and schools, reused across Discovery, Compare, Saved, Detail headers, and institution program directories. Edit the schema once; every surface picks up the change.

**Program display card fields:**
```ts
type ProgramCard = {
  id: string
  name: string
  schoolName: string
  schoolId: string
  location: { city: string; region: string; country: string }
  degreeType: 'certificate' | 'associate' | 'bachelor' | 'master' | 'doctorate' | 'professional'
  deliveryFormat: 'in_person' | 'online' | 'hybrid'
  durationMonths: number | null
  costSignal: { tuitionBand: string; currency: string } | null
  selectivitySignal: 'open' | 'moderate' | 'selective' | 'highly_selective' | null
  outcomesHighlights: string[]      // ≤3 short phrases
  // Match-context (only when rendered inside a match/saved context)
  fitnessScore?: number             // 0-100
  confidenceScore?: number          // 0-100
  bandLabel?: 'reach' | 'target' | 'safer'
}
```

**School display card fields:**
```ts
type SchoolCard = {
  id: string
  name: string
  location: { city: string; region: string; country: string }
  campusSetting: 'urban' | 'suburban' | 'rural'
  size: 'small' | 'medium' | 'large' | 'very_large' | null
  type: 'public' | 'private' | 'community' | 'vocational' | 'for_profit'
  highlights: string[]               // ≤3 short phrases
}
```

Both cards expose three actions on hover/focus: **Save**, **Add to Compare**, **Open**.

### Do / Don't
- **Do** keep card body content in the same structural order across surfaces — students build muscle memory.
- **Don't** put a decorative image on a program detail card or page. *Reason:* user rule — program detail is editorial, program-specific, not generic marketing.

---

## 6. Modals & Sheets

### Modal
Centered, blocks the rest of the UI. Use for: destructive confirmation, a focused multi-field form, a single decision needing context.

- Max width: `narrow` (640px) for confirmations, `default` (720px) for forms, `wide` (960px) for multi-section editors.
- Backdrop: `rgba(10, 20, 40, 0.45)`. Click-out closes unless the user has unsaved input — then a "Are you sure? Discard changes?" sub-modal.
- Header: H2 + close X. Body. Footer: secondary (Cancel) + primary action right-aligned.
- Focus trap; ESC closes; first focusable element receives focus on open.

### Sheet (side panel)
Slides from the right. Use for: editing a record in context without losing the list (e.g., editing a profile section, replying to a message, scheduling an interview).

- Default width: 480px on desktop; full-width with `safe-area-inset-top` margin on mobile.
- Same header/footer pattern as modal.
- Background: `--surface`. Border-left: 1px `--border`. Shadow: `elev-raised`.

### Popover
Compact, anchored to a trigger. Use for: AI-rationale callouts, quick actions menu, info-tooltip with structured content.

- Max-width: 320px.
- Padding: 16px.
- Background: `--surface`. Border: 1px `--border`. Shadow: `elev-raised`.

### AI Rationale Popover (named pattern — used in match/discovery/decisions)

A popover that explains *why* an AI surfaced something. Three regions:
```
┌──────────────────────────────┐
│ ▸ Why this match              │← H3, body weight 600
│                               │
│ Plain-language reason text…   │← body 14/400
│                               │
│ ─────────────────             │
│ Confidence ●●●○○  Medium      │← inline confidence meter (5 dots)
│ Based on:                     │← eyebrow
│  • Profile completeness       │← signal chips (cobalt outline)
│  • Stated career goal         │
│  • Budget constraint          │
└──────────────────────────────┘
```
The chips are clickable, opening a deeper drill-down. Every AI surface in the app uses this same popover anatomy.

---

## 7. Navigation

### Top nav — student app (`/s/*`)
```
┌────────────────────────────────────────────────────────────────────┐
│  [Wordmark]    Discover  Match  Apply  Connect          [avatar]   │
└────────────────────────────────────────────────────────────────────┘
```
- 64px tall, `--bg` background, 1px bottom border `--border`.
- Wordmark left → home (`/s`).
- 4 main labels matching the spec stages:
  - **Discover** → `/s` (Stage 1 — Discovery)
  - **Match** → `/s/explore` (Stage 2 — Recommendation)
  - **Apply** → `/s/manage` (Stage 3 — Application Management)
  - **Connect** → `/s/posts` (Stage 3 — Connection & Outreach)
- Active label: `--text`, weight 600, 2px bottom underline `--primary` (the one gold accent in the nav).
- Avatar right → dropdown (Profile, Saved, Settings, Sign out).

### Top nav — institution app (`/i/*`)
```
┌────────────────────────────────────────────────────────────────────┐
│  [Wordmark]   Admissions  Outreach  Communications  Programs   ▾   │
└────────────────────────────────────────────────────────────────────┘
```
- Same chrome. Four collapsed groups; each opens a mega-menu of sub-pages.
- Avatar (right `▾`) → Account, Institution settings, Sign out.

### Side nav — admissions queues (within `/i/admissions`)
Optional left rail when filtering large applicant queues. 240px wide. Lists saved filters/views. Hidden on mobile (`< md`), opens as a sheet.

### Breadcrumbs
On every detail page (program, school, application, student record):
```
Discover · Search results · Computer Science MS · ◾  University of Foo
```
Last item not a link. Separators `·` (middle dot), `--text-mut`.

---

## 8. Tables

### Use
Admissions queue, applicant lists, segment members, attribution reports. Heavy data, structured comparison.

### Anatomy
- **Header row**: `--muted` background, sticky on scroll, eyebrow-style labels (12/600/uppercase).
- **Body rows**: alternating `--surface` / very-subtle warm wash. Hover: row gets `--muted` background.
- **Cell padding**: 12px y, 16px x.
- **Numeric columns**: right-aligned, tabular-nums.
- **Selection column**: leftmost; 40px wide.

### Sorting
Click header to sort; sort indicator a small chevron `▴/▾` in `--accent`. Multi-sort with shift-click — chip below table shows the active sort order.

### Empty state
Same surface, body copy "No records match" + a suggested next action (e.g., "Clear filters" link).

### Pagination
Bottom-right: `← Prev` · page chips · `Next →`. Pages-per-row select right-corner.

---

## 9. Chips, Badges, Pills

### Constraint chip (Discovery — critical pattern)
```
┌──────────────────────────┐
│ Degree · Master's      ✕ │
└──────────────────────────┘
```
- Pill radius, 1px `--accent` border, `--surface` background, `--text` label.
- Label format: `Category · Value` separated by middle dot.
- Trailing `✕` removes the chip (and updates the search results live).
- Click the label opens an editor (e.g., dropdown of degree levels) for in-place adjustment.

### Status badge
- Pill, no border, soft-colored.
- `success` chip = `--success-soft` bg + `--success` text.
- Same for `warning` / `error` / `info` (info uses `--secondary` soft tint).

### Reach/Target/Safer band badges
Distinct visual treatment so students recognize them instantly across surfaces.
- **Reach** → `--secondary` 1px outline, `--surface` bg, `--secondary` text.
- **Target** → `--success-soft` bg, `--success` text.
- **Safer** → `--muted` bg, `--text-mut` text.

### Confidence dots (used in AI Rationale Popover and score displays)
Five circular dots. Filled dots = `--primary` (gold). Empty dots = `--border`. Label below: Low (1–2) / Medium (3) / High (4–5).

---

## 10. Forms

### Layout patterns
- **Single-column** for ≤ 8 fields or any focused task (sign-up, application question, message reply).
- **Two-column** for profile sections where pairs naturally group (city + zip, start + end date).
- **Stacked sections** with H3 + 16px gap + form fields inside, separated by 32px between sections.

### Field grouping
Group with `<fieldset>` and a visible H3 legend. Each group has a 1-line description underneath (`--text-mut`, `body small`).

### Form footer
Always pinned-bottom on a long form. Right-aligned: **Cancel** (tertiary) → **Save** (secondary). For multi-step: **Back** (left) and **Continue** (right). Submit button shows `loading` state while in-flight.

### Inline validation
Validate on blur (not on every keystroke). Show error helper text. Don't disable the submit button on errors — submit attempt re-runs validation and focuses the first error.

### Save patterns
- **Explicit save** (default). User edits → button enables → click Save → toast "Saved" or inline check.
- **Autosave** (Profile section editing, Workshops, application drafts). Debounced 800ms after last edit; show small "Saving…" → "Saved at 14:32" indicator near the header. Never block the user.

---

## 11. Toasts & Alerts

### Toast (transient)
Bottom-right stack. 16px gap between toasts. Max 4 visible.
- **Width:** 360px.
- **Anatomy:** icon + title + (optional) body + (optional) action link + dismiss X.
- **Variants:** success (default icon ✓), warning (!), error (✕), info (i).
- **Auto-dismiss:** 5s success/info, 8s warning, sticky for error (manual close only).

### Alert (persistent inline)
Banner inside a page, full-width of its container. Same color variants. Always dismissible. Use for page-level notices ("Your trial ends in 3 days").

---

## 12. Empty states

Use whenever a list, dashboard, or workspace has no data.

```
        [icon — 32px, --text-mut]
                Title (H3)
   One-line body, --text-mut, max 56ch.
        [Primary action button]
```

No illustrations, no marketing tone. The body sentence explains *what would put data here* (e.g., "Save a program from Discovery to see it in your list.").

---

## 13. Loading states

- **Skeleton** for content blocks ≥ 200px tall. Light-gray bars on `--muted` background; animate with a 1.2s shimmer.
- **Spinner** for actions < 1s expected. 16px or 20px size; color `currentColor`.
- **Page-level loader** when the entire route is loading: thin 2px progress bar at the top of the viewport, `--primary` color.

Never block the UI with a centered spinner overlay. Use skeletons and let the user keep navigating.

---

## 14. Charts

Used in Analytics, Attribution, Cohort Comparison, profile Analytics tab.

- **Library:** existing in codebase (likely `recharts`).
- **Color palette for series:** in order — `--secondary` (cobalt), `--primary` (gold), `--success`, `--warning`, then `--text-mut`. Never use more than 5 colors at once.
- **Axes:** `--text-mut` 12px labels; gridlines `--border` at 0.5 opacity.
- **Tooltip:** popover styling (§6); shows the data point's date/label, value, and series name.
- **Empty state:** "Not enough data to plot yet" plus a one-line hint about what produces this chart.

---

## 15. AI surfaces — common patterns

Any UI region that surfaces AI-generated content must follow these conventions:

1. **Visible attribution.** A small badge `AI assist` or `AI suggestion`, `--accent` outline, `--surface` bg. Never hide that AI produced it.
2. **Reasoning available.** Every score, ranking, or recommendation has a "Why" affordance opening the AI Rationale Popover (§6).
3. **Editable, not authoritative.** The user can always reject, edit, or refresh. Display the timestamp of the last AI run.
4. **Confidence shown.** Confidence dots (§9) on every AI-derived value with a numeric score.
5. **Failure is graceful.** When the agent fails (timeout, parse error, guardrail trip), show the rule-based fallback with a small note "Showing rule-based result" — the caller never sees a 5xx.
6. **Generation vs feedback.** Workshops are **feedback-only**. The schema mechanically excludes any field that could carry a generated essay or model answer. Other AI surfaces may suggest content (e.g., a drafted reply in Inbox), but the user must accept/edit before it sends.

---

## 16. Voice (UX copy)

Five adjectives govern all UX copy and component microcopy:

1. **Plain.** No jargon. "Save to my list" not "Bookmark this program."
2. **Direct.** Imperative when an action is expected. "Add a recommender." Not "You might want to add a recommender."
3. **Honest.** Say what's true, including when something failed. "We couldn't reach the matching service. Showing your last saved shortlist." Not "Oops, something went wrong."
4. **Brief.** Tightest sentence that holds the meaning. Cut adverbs.
5. **Warm.** Sentence case (not Title Case). Periods on full sentences. No exclamation marks.

### Standard phrasings (reuse verbatim across surfaces)
| Use | Phrasing |
|---|---|
| Save | `Save to my list` (student); `Save` (institution) |
| Remove from list | `Remove` |
| Compare | `Add to compare` / `Open compare` |
| AI feedback | `Get feedback` (never `Get review` or `Generate`) |
| Submit application | `Submit application` |
| Mark ready | `Mark as ready to submit` |
| Cancel | `Cancel` |
| Delete | `Delete` (destructive variant button only) |
| Loading | `Loading…` / `Saving…` / `Sending…` |
| Empty list | `Nothing here yet` |
| Error | `Something didn't work. Try again.` (toast) or specific cause |

---

## 17. Scale of flexibility

Some elements are **templated** (engineers do not deviate); some are **bespoke** (designers compose). This file documents what's templated.

- **Templated (no deviation):** colors, type scale, spacing scale, radii, elevation, button/input/card variants, table chrome, navigation chrome, AI Rationale Popover anatomy, display-card schemas, voice rules.
- **Bespoke (per surface, follow tokens):** layout composition within a page, illustrative diagrams in AI/architecture contexts (e.g., the 3-layer AI engine diagram from Landing_MVP), specific copy on hero/empty states, animation timing for stage transitions.

If a designer wants to deviate from a templated rule, the rule changes here first — then propagates downstream.

---

## 18. Open questions / known gaps

- **Specific component implementations.** The current codebase uses shadcn primitives + custom components in `frontend/src/components/ui/`. A mapping table from each spec component → existing source file should be added once the audit subagent's output is in (`90-current-vs-spec-gap-audit.md`).
- **Animation tokens.** Not yet specified. Recommend the Landing_MVP convention: cubic-bezier(0.22, 1, 0.36, 1) at 200/300/700 ms for ui/ux/page transitions respectively.
- **Dark theme audit.** Need to spot-check every component variant on dark to confirm contrast. Specifically the `--primary` on `--secondary` button hover is suspicious.
- **Mobile spec.** This document defines desktop-first. A mobile breakpoints + touch-target audit doc should be added (proposed as `02b-design-system-mobile.md`).
