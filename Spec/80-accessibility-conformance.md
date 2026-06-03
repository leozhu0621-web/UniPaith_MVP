# 80 · Accessibility Conformance (WCAG 2.1 AA) — Build Spec

> Consolidate the scattered a11y notes (`02` per-component, `03` §9, the 44px targets) into one conformance target: WCAG 2.1 AA across every route. Strong infra already exists — the work is uniform application: a focus system on the 295 raw buttons, ARIA live regions for optimistic/realtime/streaming, accessible names for the signature score components, a contrast audit of the token pairs, and a keyboard path through the Kanban. Companion to `75`, `76` (tokens/contrast), `77` (reduced-motion), `79` (keyboard tables), `02`/`03`.
>
> Status: **draft v2.0** · 2026-06-02 · v2 = first issue. Counts from the 2026-06-02 audit.

---

## 1. What exists vs what to build (ground truth)

The infrastructure is genuinely good; conformance fails on **uneven application**, not absence.

**Already product-grade:** `aria-*` appears 246×; `Modal`/`Sheet` trap focus + restore on close + ESC; `Input`/`Textarea` fully label-associated with a reserved error region; toasts are `aria-live`; `prefers-reduced-motion` + `data-reduce-motion` honored; 44×44px touch targets on coarse pointers; font-size scaling (`data-font-size`) + dyslexia font (`data-dyslexia`); 7 `<img>` all have `alt`.

**The gaps:**
- **Focus visibility:** `role=` only 35 uses; **295 raw `<button>` elements** in pages bypass the `Button` primitive's built-in gold focus ring; only **37 files** carry `focus-visible`/`focus:ring`. Many bare buttons have **no visible focus state** for keyboard users — a direct 2.4.7 failure.
- **Native controls:** **44 native `<select>`** across 22 files (inconsistent focus styling vs the styled `Select`).
- **No keyboard path** for the pipeline Kanban drag-drop (`79` §4) — a 2.1.1 keyboard failure on a core institution flow.
- **Custom viz without names:** `DualRing`, `ConfidenceDots`, `BandBadge`, `AIRationalePopover` render meaning visually (scores, confidence) with no screen-reader text — the product's signature information is invisible to SR users.
- **Live updates** (optimistic saves, SSE realtime, chat streaming) aren't announced.
- **Contrast** of the token pairs (gold-on-cream, muted-foreground, status colors, dark variants) is unaudited.

**Principle:** accessibility is part of "public-release-ready" and of the mission — "make college information genuinely easy to get… available to everyone" (`75` §2). An inaccessible product excludes exactly the first-gen / under-resourced students the paper centers.

---

## 2. The conformance target

**WCAG 2.1 Level AA, every route.** The criteria most at risk here, with the owning fix:

| Criterion | Risk | Fix (§) |
|---|---|---|
| 1.4.3 Contrast (min) | token pairs unaudited | §7 |
| 1.4.11 Non-text contrast | focus rings, borders, score arcs | §7 |
| 2.1.1 Keyboard | Kanban, native widgets | §5 |
| 2.4.3 Focus order | modals, route changes | §3 |
| 2.4.7 Focus visible | 295 raw buttons | §3 |
| 4.1.2 Name/Role/Value | custom viz, icon buttons | §6 |
| 4.1.3 Status messages | live updates unannounced | §4 |
| 1.4.4 / 1.4.10 Resize/Reflow | 200% zoom, mobile reflow | §8, `03` |
| 2.3.3 Animation from interactions | reduced-motion | `77` §7 |

---

## 3. Focus system

- **Visible focus on every interactive element.** Route all interactive elements through `Button`/`Select`/`Link` (which carry the `--ring` gold focus ring), or apply a shared `.focus-ring` utility to the remaining raw `<button>`s. The focus ring is the one always-on use of the ring color; never removed (`77` §5). Target: zero interactive elements without `:focus-visible`.
- **Focus order** follows visual order; no positive `tabindex`. Modals trap focus (done); on close, focus returns to the trigger (done) — verify across all modal/sheet usages.
- **Route-change focus management:** on navigation, move focus to the new page's `<h1>` (or a focus target) so SR/keyboard users land in the right place, not stranded on a stale element.
- **Skip link:** "Skip to content" as the first focusable element in each layout (`StudentLayout`, `InstitutionLayout`), visible on focus.
- **Focus not trapped** anywhere except intentional modals/sheets.

---

## 4. ARIA live regions (announce status — 4.1.3)

Status changes that happen without a page load must be announced:
- **Toasts:** `aria-live="polite"` (assertive for errors) — done; keep.
- **Optimistic actions** (save, react, stage-move): a visually-hidden `aria-live` confirms "Saved to your list" / "Moved to Interview" so SR users get the same feedback sighted users get from the optimistic UI (`54` §4).
- **Realtime** (SSE notifications, new feed posts, `57`): polite announcement of new items; never steal focus.
- **Chat streaming** (`77` §6): the assistant message region is `aria-live="polite"` and `aria-busy` while streaming, so the response is read as it lands; the typing indicator is labeled "Counselor is typing."
- **Loading:** skeleton regions carry `aria-busy`/`aria-live` "Loading…" so a blank-looking region isn't silent.

A single `useAnnounce()` hook + a layout-level visually-hidden live region keeps this consistent.

---

## 5. Keyboard operability (2.1.1)

- **Everything operable by keyboard.** Audit the 295 raw buttons and 44 native selects: native `<select>` is keyboard-fine but inconsistent — replacing with the styled `Select` (`76`/`78`) must preserve full keyboard semantics (type-ahead, arrow nav, ESC) — verify the `Select` implements the listbox pattern, don't regress accessibility for looks.
- **Kanban keyboard DnD** (`79` §4): dnd-kit keyboard sensor — Space to pick up, arrows to move between stages, Space to drop, ESC to cancel, with `aria-live` move announcements. This is the headline keyboard fix.
- **Menus/popovers/dropdowns** implement the correct roving-tabindex / arrow-key patterns (`Dropdown`, `Popover`, `Select`, `Tabs`).
- **⌘K command palette** (`53`/`54`) is itself a keyboard-power feature — ensure it's reachable and escapable.
- **No keyboard trap** anywhere (2.1.2).

---

## 6. Accessible names for the signature components

The dual-score viz is the product's differentiator (`76` §4) and must be perceivable non-visually:

| Component | Accessible treatment |
|---|---|
| `DualRing` | `role="img"` + `aria-label="Fitness 82 out of 100, confidence high"`; the numbers also available as visually-shown text where space allows. |
| `ConfidenceDots` | `aria-label="Confidence: high"` (not "3 of 3 dots"). |
| `BandBadge` | text content "Reach"/"Target"/"Safer" is already textual — ensure it's not icon-only. |
| `AIRationalePopover` | trigger has `aria-haspopup` + `aria-expanded` + a label ("Why this program is suggested"); the popover is a labeled dialog; the rationale text is readable in DOM order. This is the trust surface (`75` §2.1) — it must be reachable by keyboard + SR. |
| `AIBadge`/`FallbackNote` | textual ("Claude" / "Showing a rule-based result"), not a bare colored dot. |
| Icon-only buttons (Pipeline grip, compare, save) | `aria-label` + a `Tooltip` (`76` §7 / new primitive) for sighted discoverability. |

---

## 7. Contrast audit (1.4.3 / 1.4.11)

Audit every token pair from `76` §2.1 against AA (4.5:1 text, 3:1 large/non-text), light **and** dark:
- **`text-muted-foreground` (`#6B6660`) on `bg-card`/`bg-muted`** — the most likely failure; verify ≥ 4.5:1, darken the token if not.
- **Gold (`#FFD60A`) is never a text color on light** (it fails contrast badly) — it's a fill/accent only (`76` §2.4); enforce in the lint allowlist.
- **Status colors** (`success/warning/error`) on their `-soft` backgrounds and as text — verify both themes; status must brighten on dark (`76` §2.1).
- **Focus ring + borders** meet 3:1 non-text contrast.
- **Score-ring arcs** (cobalt fitness, confidence) meet 3:1 against the card.

Record the audit as a table in the spec/PR; fix tokens centrally in `index.css` (one change fixes everywhere — the `76` payoff).

---

## 8. Forms, reflow & zoom

- Forms: every input labeled (Input does this — verify the 44 native selects + any bare inputs); errors associated via `aria-describedby` (Input's reserved region); required marked (not by color alone); related controls in `fieldset`/`legend`.
- **Reflow (1.4.10):** content usable at 320px width and 200% zoom without horizontal scroll — the institution tables are the risk (`79` mobile collapse); verify.
- **Target size:** 44×44px maintained (done on coarse pointers) — verify dense/compact table mode (`79` §2.5) keeps adequate hit areas.

---

## 9. Testing & enforcement

- **Automated:** `jest-axe`/`axe-core` assertion in every `*Page.tsx` test (`54` §11 already requires a per-surface test — add an axe check). CI fails on new violations.
- **Keyboard pass:** a documented manual checklist per critical journey (`52` §2) — tab through, operate everything, nothing trapped, focus always visible.
- **Screen-reader pass:** VoiceOver (Safari) + NVDA (Firefox) spot-check of the signature flows (Discover chat, Match results + rationale, pipeline) before release.
- **Contrast:** the §7 audit table, re-run when tokens change.

---

## 10. Build tasks (checklist)

- [ ] Apply a visible focus ring to all 295 raw buttons (route through `Button` or add `.focus-ring`); target zero unfocusable interactive elements.
- [ ] Replace 44 native `<select>` with the styled `Select`; verify it implements the listbox keyboard pattern (no a11y regression).
- [ ] Add the `useAnnounce()` hook + layout live region; wire optimistic/realtime/streaming/loading announcements.
- [ ] Add accessible names to `DualRing`/`ConfidenceDots`/`AIRationalePopover`/icon buttons; build the `Tooltip` primitive.
- [ ] Keyboard DnD + ARIA for the pipeline Kanban (`79` §4).
- [ ] Add skip links to both layouts; move focus to `<h1>` on route change.
- [ ] Run the §7 contrast audit; fix failing tokens in `index.css`.
- [ ] Add `jest-axe` to the per-surface test suite; CI gate on violations; document the keyboard + SR manual checklists.

---

## 11. Acceptance

- [ ] axe-core clean on every route (CI-gated); zero new violations.
- [ ] Every interactive element has a visible `:focus-visible` state; nothing is keyboard-trapped.
- [ ] The pipeline Kanban is fully keyboard-operable with `aria-live` move announcements.
- [ ] `DualRing`/`ConfidenceDots`/`AIRationalePopover` expose accessible names; the rationale is reachable by keyboard + SR.
- [ ] Optimistic, realtime, streaming, and loading changes are announced to SR users.
- [ ] All token pairs pass AA contrast in light + dark (audit table attached); gold is never light-mode text.
- [ ] Usable at 320px / 200% zoom; VoiceOver + NVDA spot-checks of the signature flows pass.

---

## 12. Open questions

- **Conformance scope for v1.** Full AA on every route (recommended) vs AA on the student critical path + "best-effort" on deep institution admin screens for launch. Recommend full AA on student + the top institution flows (pipeline, review, settings), with the axe gate everywhere.
- **`Select` implementation.** Build an accessible listbox vs adopt a headless one (Radix/Ariakit) for the styled `Select`/`Dropdown`/`Popover`. Recommend a headless primitive library for correctness (these patterns are easy to get subtly wrong) — scope against bundle budget (`54`).
- **Manual SR cadence.** Per-release VoiceOver+NVDA pass (recommended) vs automated-only. Automated catches ~40% of issues; keep a manual pass for the signature flows.
