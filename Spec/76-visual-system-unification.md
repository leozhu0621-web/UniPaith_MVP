# 76 · Visual System Unification & Token Discipline — Build Spec

> The single biggest "finished" lever: collapse the two color vocabularies into one semantic token system, make dark mode survive every route, enforce the brand proportion + earned-gold rule mechanically, document the score-viz family and the one display-card, and add the component→source map. Operationalizes `01` (tokens) and `02` (design system) against the real `frontend/src/` tree. Companion to `75` (plan), `77` (motion), `80` (a11y).
>
> Status: **draft v2.0** · 2026-06-02 · v2 = first issue. Counts are from the 2026-06-02 audit of `frontend/src/`; re-grep before relying on exact numbers.

---

## 1. What exists vs what to build (ground truth)

`src/index.css` `@layer base` + `tailwind.config.js` already define a real system: HSL semantic tokens for light + `.dark` (`background/foreground/card/primary/secondary/muted/accent/destructive/border/ring`), three elevations (`.elev-subtle/.elev-raised/.elev-glow`), `--radius: 0.75rem` with derivations, status colors with `-soft` tints. **The problem is a second, parallel vocabulary living beside it**, and pages mixing both freely.

| Vocabulary | Where | Status |
|---|---|---|
| **Semantic (keep)** | `text-foreground` (154 files), `text-muted-foreground` (174), `bg-card`, `bg-primary`, `bg-secondary`, `border-border` | The source of truth. Dark-mode-safe. |
| **Legacy aliases (retire)** | `tailwind.config.js` maps `student-*`, `school-*`, `gold-*`, `charcoal`, `slate`, `stone`, `cobalt`, `paper`, `cream`, `brand.slate/amber` to brand hexes | `text-cobalt`/`bg-cobalt` in 102 files; `student-*` in 48; `text-charcoal` 27; `text-slate` 20. Many are **dark-mode-unsafe** (fixed hex, no `.dark` swap). |

The flagship Match surface is the worst offender (`pages/student/ExplorePage.tsx:148-150`, `pages/student/match/MatchCard.tsx` — `text-charcoal`/`text-slate`/`bg-cobalt`/`text-student-text` throughout) and so is the first-impression auth screen (`pages/auth/LoginPage.tsx:47,74,76`). This is the highest-ROI visual work in the entire refinement (`75` §1).

**Build = a migration, not a redesign.** The hexes are already correct; we change *which class names* reference them so dark mode and any future re-theme work, and so the brand reads as one system.

---

## 2. The one vocabulary

### 2.1 Token reference (semantic = source of truth, from `01` §2 + `index.css`)

| Role | Token / class | Light | Dark | Use |
|---|---|---|---|---|
| Page bg | `bg-background` | `#FCFAF2` paper cream | `#0A1428` deep ink | app canvas |
| Surface | `bg-card` | `#FFFFFF` | `#122039` | cards, panels, sheets |
| Muted surface | `bg-muted` | `#F2EEE0` | `#1A2C4D` | wells, table stripes |
| Body text | `text-foreground` | `#2A2724` soft ink | `#F5F1E8` | "not pure black" |
| Secondary text | `text-muted-foreground` | `#6B6660` | lifted | captions, meta |
| Workhorse accent | `text-secondary`/`bg-secondary` | `#2A6BD4` cobalt | `#6FA0E8` | links, eyebrows, primary buttons |
| Earned accent | `text-primary`/`bg-primary` | `#FFD60A` gold | `#F2C800` | the one CTA / brand cap / `elev-glow` beat |
| Hairline | `border-border` | `#C9C2A8` | `#3F567C` | dividers |
| Status | `text-success/warning/error` (+ `-soft` bg) | per `01` | brightened | must brighten on dark to hold contrast |

### 2.2 Migration map (legacy class → semantic class)

| Legacy (retire) | Semantic (use) | Notes |
|---|---|---|
| `text-charcoal`, `text-student-text` | `text-foreground` | body text |
| `text-slate`, `text-stone` | `text-muted-foreground` | secondary/meta |
| `text-cobalt`, `text-student-accent` | `text-secondary` | links, eyebrows |
| `bg-cobalt` | `bg-secondary` | cobalt fills/buttons |
| `bg-gold-*`, `text-gold-*` | `bg-primary`/`text-primary` | only on earned beats (§2.4) |
| `bg-paper`/`bg-cream` | `bg-background` / `bg-card` | pick by layer |
| `border-stone`/`border-slate` | `border-border` | hairlines |
| `student-*`, `school-*` namespaces | semantic equivalents | aligns with `47` G-B6 (delete the aliases) |

**Endgame:** delete the legacy alias namespaces from `tailwind.config.js` entirely (`47` G-B6). A class that no longer resolves becomes a build/lint failure — that is the enforcement.

### 2.3 Proportion rule (reconcile + enforce)

`01` §2 specifies a fixed color budget; the Master Paper states `55/20/15/10` (paper/ink/cobalt/gold) while `01` §2 implements `60/25/10/5`. **Defer to `01` as the implemented source of truth** (recommend updating the paper, not the code — `75` §9). On any **light** surface, **gold + cobalt together ≤ 15% of visual area**; gold alone is the rarest mark. This is a design-review checklist item (`01` §9), not auto-lintable — but the earned-gold rule (§2.4) is partially enforceable.

### 2.4 The earned-gold rule (mechanical where possible)

Gold (`--primary`) is "brand punctuation, not a fill — must feel earned" (Brand Visual Guide). Concretely:
- **At most one `bg-primary` / `elev-glow` element per visual region.** The single most important CTA, the confirmed-enrollment beat (`35`), a brand cap.
- **Never two gold elements adjacent**; never gold on the institution side (cobalt only — `75` §2.5, institution = system-of-record, not delight).
- `Button` default is `secondary` (cobalt). `primary` (gold) is opt-in and rare. (Recurring code trap: the `Button` default has historically rendered gold — audit every `<Button>` with no `variant` and set `secondary` unless it is *the* beat.)

---

## 3. Dark-mode parity (make `.dark` real on every route)

Dark tokens are fully defined but bypassed in practice. Three eradications:

### 3.1 `bg-white` → `bg-card` (69 occurrences, 28 files)
A hardcoded white block on the `#0A1428` canvas is the most visible dark-mode break. Hotspots: `pages/student/CalendarPage.tsx:223,262,271,388` (the entire calendar grid), `SchoolSubunitPage.tsx:94,139`, `connect/PeersTab.tsx:24,37`. Replace with `bg-card` (or `bg-background` for canvas).

### 3.2 `text-white` (44 occurrences) — keep only on fixed-color fills
`text-white` is correct **only** on an element whose background is a fixed color in both themes (e.g. text on a cobalt `bg-secondary` button). Audit each: on `bg-secondary`/`bg-primary` it stays; on anything theme-variable (e.g. `ApplicationDetailPage.tsx:674` `bg-white text-student-text`) it must become `text-primary-foreground` / `text-secondary-foreground` or be re-tokenized.

### 3.3 Raw hex in `className` → tokens
`components/ui/PageLoader.tsx:31,35` hardcodes `bg-[#FFD60A] dark:bg-[#F2C800]` — use `bg-primary` (the token already swaps). General rule: **no `#hex` in any `className` outside `index.css`** (`01` §9).

### 3.4 Scrim token (new)
Modal/sheet/popover backdrops inline `rgba(10,20,40,…)` (`Modal.tsx:84`, `Sheet.tsx:81`, `RationalePopover.tsx:69`, `Paywall.tsx:50`). Add a `--scrim` CSS var (light + dark) in `index.css` and a `bg-scrim` utility; replace the four inline backdrops. One scrim, theme-aware.

---

## 4. The score-viz family (document the signature components)

The dual-score model (Fitness + Confidence) is the product's signature differentiator vs single-score competitors (Master Paper; `09`). Its components exist but are undocumented as a family — codify them so they read consistently and never drift:

| Component | File | Rule |
|---|---|---|
| `DualRing` | `components/ui/DualRing.tsx` | The canonical fitness+confidence ring. **The only** dual-score visual; used on cards + detail + compare. Fitness = cobalt arc, confidence = the dot/secondary ring; never recolor to gold. |
| `ConfidenceDots` | `components/ui/ConfidenceDots.tsx` | Discrete confidence (low/med/high) where a ring is too heavy (list rows). |
| `BandBadge` | `components/ui/BandBadge.tsx` | Reach/Target/Safer probability band; status-tone, not gold. |
| `AIRationalePopover` | `components/ui/AIRationalePopover.tsx` | The "why this program" plain-language rationale (the trust surface, `75` §2.1). Consistent trigger + content shape everywhere a score appears. |

**Honesty rule (from the papers):** the confidence axis exists to avoid false precision — render scores as honest estimates with their rationale reachable in one interaction, never as bare authoritative numbers. **Migration debt:** `SchoolDetailPage` still reads the legacy `match_score` instead of `fitness_score`/`confidence_score` (`47` G-S2 / CLAUDE.md Phase-E) — wire it to `DualRing` here so the legacy column can be dropped.

---

## 5. Elevation, radius & spacing discipline

Already well-defined in `01`; the work is removing violations.
- **Elevation:** exactly three — `.elev-subtle` (resting card), `.elev-raised` (hover/modal/dropdown), `.elev-glow` (the one gold beat). Grep for ad-hoc `shadow-*` Tailwind utilities and `drop-shadow`; replace with one of the three or none. "Drop shadow → ink-tinted only, never gray; no gradients as backgrounds" (`01` §1.6).
- **Radius:** route through the `--radius` scale (`01` §4.3); reconcile the open 12-vs-14px card-radius question (`02` §18) — recommend 14px cards / 10px controls / 6px chips, set once in tokens.
- **Spacing:** every gap/padding/margin a multiple of 4 (`01` §4). Grep for odd arbitrary values (`p-[13px]`, `gap-[7px]`) and snap to the scale.

---

## 6. The display-card schema (one card, everywhere)

The Master Paper makes this a product rule (lines ~1215-1255): the program card is **identical** across Discovery results, the compare tray, saved lists, and detail-page headers — "the information students see stays consistent across the platform." Today the Match surface, saved list, and school pages render visually divergent cards.

**Build:** one `components/program/ProgramCard.tsx` (or promote the strongest existing card) as the single source, with documented slots:
- Header: program + institution name (the canonical names, `32` parity), `DualRing`.
- Body: cost signal (consistent schema per `11`), `BandBadge`, 1-line fit rationale (links to `AIRationalePopover`).
- Footer: save toggle (optimistic, `54` §4), compare checkbox, deep link to detail.
- Density variants: `default` (results grid), `compact` (saved list / compare row), `header` (detail-page hero, no decorative imagery per `11`/`01` §9).

Every results/saved/compare/detail surface consumes this one component. No surface hand-rolls a program card.

---

## 7. Component → source-file map (the missing table)

Both `02` §18 and `47` flag that a mapping from each design-system component to its `frontend/src/` source is missing. Add it here as the canonical index (excerpt; complete it against the real tree):

| Pattern (`02` §) | Source file | Notes |
|---|---|---|
| Button (§2) | `components/ui/Button.tsx` | 6 variants; default → `secondary`. Orphaned `components/shadcn/button.tsx` to be deleted. |
| Input/Textarea (§4) | `components/ui/Input.tsx`, `Textarea.tsx` | reserved error region |
| Select (§4) | `components/ui/Select.tsx` | replaces 44 native `<select>` (`80`) |
| Card (§5) | `components/ui/Card.tsx` + `program/ProgramCard.tsx` | §6 above |
| Modal/Sheet (§6) | `components/ui/Modal.tsx`, `Sheet.tsx` | scrim token §3.4 |
| Table (§8) | `components/ui/Table.tsx` | extended in `79` |
| Chips/Badges (§9) | `components/ui/Badge.tsx`, `BandBadge.tsx` | |
| Toast/Alert (§11) | `components/ui/Toast.tsx`, `Alert.tsx` + `stores/toast-store.ts` | |
| Empty state (§12) | `components/ui/EmptyState.tsx` | extended in `78` |
| Loading (§13) | `components/ui/Skeleton.tsx` (+`SkeletonCard`/`SkeletonTable`) | standardized in `77`/`78` |
| AI surfaces (§15) | `AIBadge.tsx`, `AIRationalePopover.tsx`, `FallbackNote.tsx` | the trust surface |
| Score viz | `DualRing.tsx`, `ConfidenceDots.tsx` | §4 |

Delete the orphaned `components/shadcn/{button,accordion}.tsx` copies (dead duplicates of the real primitives).

---

## 8. Enforcement (lint / CI guards)

Make the mechanical rules un-regressable (`54` precedent: CI guards for FE conventions):
- **ESLint rule / `eslint-plugin-tailwindcss` + custom**: ban `bg-white`, `text-white` (except an allowlist of fixed-fill components), and arbitrary `#hex` in `className`.
- **Grep CI check**: fail if `src/pages/` contains any retired legacy token class (`text-charcoal|text-slate|bg-cobalt|student-|school-`). This is the migration's completion gate.
- **Stylelint**: no `box-shadow`/`drop-shadow` outside the three `.elev-*` utilities; no `linear-gradient` background.

---

## 9. Build tasks (checklist)

- [ ] Codemod legacy color classes → semantic per the §2.2 map (script the find-replace; review the Match surface + auth by hand).
- [ ] Delete the `student-*`/`school-*`/`charcoal`/`slate`/`stone`/`cobalt`/`paper`/`cream` alias namespaces from `tailwind.config.js` (`47` G-B6).
- [ ] Replace `bg-white` (69) → `bg-card`/`bg-background`; audit `text-white` (44); fix `PageLoader.tsx` hex → `bg-primary`.
- [ ] Add `--scrim` token + `bg-scrim`; replace the 4 inline backdrops.
- [ ] Audit every `<Button>` with no `variant`; set `secondary` unless it is the one earned beat.
- [ ] Wire `SchoolDetailPage` (and any legacy `match_score` reader) to `DualRing` + `fitness_score`/`confidence_score`; unblock `G-S2`.
- [ ] Build/promote one `program/ProgramCard.tsx`; replace divergent cards on results/saved/compare/detail.
- [ ] Add the component→source map (§7) to `02` (or keep canonical here); delete orphaned `components/shadcn/*`.
- [ ] Add the ESLint/grep/Stylelint guards (§8) to the FE CI.
- [ ] Reconcile the card-radius open question; set radius/elevation tokens once.

---

## 10. Acceptance

- [ ] `grep -rE "text-charcoal|text-slate|bg-cobalt|student-|school-" src/pages` returns nothing.
- [ ] `grep -rE "bg-white|text-white|#[0-9a-fA-F]{3,6}" src/ --include=*.tsx` returns only allowlisted fixed-fill components.
- [ ] Every route renders correctly under a forced `.dark` toggle (manual spot-check matrix per surface).
- [ ] Gold appears at most once per visual region; institution side has zero gold.
- [ ] The same `ProgramCard` renders Discovery / compare / saved / detail headers.
- [ ] `DualRing` is the only dual-score visual; no surface reads legacy `match_score`.
- [ ] FE CI fails on a reintroduced legacy token / `bg-white` / extra shadow.

---

## 11. Open questions

- **Codemod vs hand-migration of the Match surface.** `MatchCard.tsx`/`ExplorePage.tsx` mix tokens with layout logic; a blind codemod risks visual regressions. Recommend codemod the safe 80%, hand-review the flagship surfaces.
- **`text-white` allowlist.** Which components are legitimately fixed-fill (cobalt/gold buttons, status pills)? Enumerate before turning the lint rule to error.
- **Card-radius reconciliation** (`02` §18): 12 (current shadcn default) vs 14 (`01` §4.3 "matches favicon tile"). Recommend 14.
- **Proportion ratio** (`75` §9): `55/20/15/10` (paper) vs `60/25/10/5` (`01`). Pick one; recommend `01`.
