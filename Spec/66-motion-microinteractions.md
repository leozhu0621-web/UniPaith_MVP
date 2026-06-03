# 66 · Motion, Microinteractions & Feedback — Build Spec

> Turn the existing ad-hoc animations into one named motion system: documented transition tokens, enter/exit + stagger choreography, a skeleton-shimmer spec, the earned-gold success beat, and Discover chat token-streaming — all honoring reduced-motion. Operationalizes the motion tokens in `01` §4.4 and the "no blank states / optimistic" bar in `53` §3. Companion to `64`, `65` (tokens), `67` (states), `69` (a11y).
>
> Status: **draft v2.0** · 2026-06-02 · v2 = first issue. Settles the app-vs-Landing curve seam left open in `02` §18 / `54`.

---

## 1. What exists vs what to build (ground truth)

`src/index.css` already ships **13 named keyframes/animations** — `page-in`, `slide-in-*`, `scale-in`, `page-loader-sweep`, shimmer — and **honors both `prefers-reduced-motion` and a user `data-reduce-motion` toggle**. Tasteful microinteractions exist: hover-lift, story-link underline, button press (`active:translate-y-px`), toast slide-in. This is a real foundation.

Gaps:
- **No documented system.** Animations are applied ad hoc; there's no contract for *which* transition a given interaction uses, durations, or choreography (enter/exit, stagger). New code reinvents.
- **Hand-rolled timing.** Inline `animationDelay` staggers in `discover/ChatPanel.tsx:211,215` and `MiniCounselorPanel.tsx:134-136`; the chat typing-dots are static.
- **No streaming.** Discover chat does a full request→response round-trip then renders the whole message — the flagship "AI counselor" surface feels less alive than ChatGPT/Element451 (`53` benches ChatGPT for chat streaming).
- **The curve seam.** The app uses `--ease-out: cubic-bezier(0.2,0.7,0.2,1)` while the marketing `Landing_MVP` uses `cubic-bezier(0.22,1,0.36,1)`; `02` §18 and `54` both flag this as unresolved. This spec settles it.

**Principle (from the papers):** motion serves *clarity and calm*, never spectacle — the product is "a calm friend," restraint signals craft (`64` §2.2). Motion confirms actions, orients the user across the 3-stage journey, and makes AI feel responsive. It is never decorative.

---

## 2. Motion tokens (the one curve, three durations)

Canonical, in `index.css` (`01` §4.4):

```css
--ease-out:    cubic-bezier(0.2, 0.7, 0.2, 1);   /* default: enter, most transitions */
--ease-in-out: cubic-bezier(0.65, 0.05, 0.36, 1);/* reversible / move transitions   */
--ease-in:     cubic-bezier(0.4, 0, 1, 1);        /* exit only (leaving the screen)  */
--dur-fast:  120ms;  /* hover, focus, press, toggle            */
--dur-base:  200ms;  /* most: cards, popovers, tab change      */
--dur-slow:  360ms;  /* sheets, modals, stage/page transitions */
```

**Curve-seam decision:** the **app keeps `cubic-bezier(0.2,0.7,0.2,1)`**; the Landing curve stays on the marketing site only. Rationale: the app curve is calmer (less overshoot) — correct for an anxiety-lowering product; the Landing curve's spring is marketing energy. Document this in `02` §18 and close the open question. No component imports the Landing curve.

**Usage rule:** enter uses `--ease-out`; exit uses `--ease-in` and is faster (≈0.8×); move/resize uses `--ease-in-out`. Never animate `width`/`height`/`top`/`left` (layout thrash) — animate `transform`/`opacity` (`69` perf + `54` CWV `CLS < 0.1`).

---

## 3. Named transition system & choreography

Define the vocabulary once; every surface picks from it.

| Transition | Tokens | Where |
|---|---|---|
| **fade** | opacity, `--dur-fast`, `--ease-out` | tooltips, hover reveals |
| **scale-in** | opacity+scale(0.96→1), `--dur-base` | popovers, dropdowns, `AIRationalePopover` |
| **slide-up sheet** | translateY, `--dur-slow`, `--ease-out` | mobile bottom-sheet, modals |
| **page-in** | opacity+translateY(8px), `--dur-base` | route entrance (exists; standardize) |
| **stagger-list** | children `page-in`, +40ms each, cap 6 | results grid, feed, message list |
| **collapse/expand** | height via grid-rows trick or `transform`, `--ease-in-out` | accordions, filter panels |
| **cross-stage** | `--dur-slow` directional slide | Discover track switch, stage transitions |

**Choreography rules:** one primary motion per interaction (don't animate five things at once); stagger caps at 6 items then the rest appear instantly (no long cascades); list **enter** animates, list **reorder** uses `--ease-in-out` move, list **exit** is a quick fade so removals feel decisive (optimistic deletes, `53`/`54`). Replace the inline `animationDelay` staggers (`ChatPanel.tsx`, `MiniCounselorPanel.tsx`) with the `stagger-list` utility.

---

## 4. Skeleton shimmer spec

Skeletons exist in 103 files but are inconsistent — some use the nice `Skeleton`/`up-skeleton` shimmer, others ad-hoc `bg-card animate-pulse` blocks (`ExplorePage.tsx:201`, `SchoolSubunitPage.tsx:139`, `PeersTab.tsx:24`). Standardize:
- **One shimmer**: a single `--shimmer` keyframe (subtle, ink-tinted, ~1.4s, respects reduced-motion → falls back to a static muted block).
- **Skeletons mirror final layout** (Airbnb rule, `64` §3.2): a `SkeletonCard` matches `ProgramCard`'s real dimensions so there's no layout shift when content arrives (`CLS < 0.1`). Build `SkeletonCard`/`SkeletonTable`/`SkeletonRing` variants that match their real counterparts.
- **Retire** all ad-hoc `animate-pulse` divs → `Skeleton`/`SkeletonCard`.

---

## 5. Microinteractions & feedback

| Interaction | Treatment |
|---|---|
| **Hover** | `--dur-fast` lift (`translateY(-1px)` + `.elev-raised`) on cards; underline-grow on story links. Pointer-fine only (skip on touch). |
| **Press** | `active:translate-y-px` + slight scale on buttons (exists). |
| **Focus** | the gold focus ring (`--ring`) — see `69`; never removed, never replaced by motion. |
| **Drag** | pipeline cards lift + `.elev-raised` + cursor; drop target gets a `--ring` outline. Keyboard equivalent in `69`. |
| **Optimistic success (the earned beat)** | a save/confirm that succeeds gets a brief `.elev-glow` pulse on the affected element — gold, ~`--dur-base`, **once**. This is the one place motion uses gold (`65` §2.4). The student "Confirm enrollment" (`35`) is the canonical example. Never on the institution side. |
| **Copy-to-clipboard** | inline "Copied" affordance (icon → check, `--dur-fast`), not a toast, for inline copies. |
| **Undo** | destructive optimistic actions (delete a goal, remove from saved) show a toast with an **Undo** action for ~6s before commit, instead of an upfront confirm where reversible (pairs with `67`'s `ConfirmDialog` for the irreversible ones). |

---

## 6. Discover chat token-streaming (flagship upgrade)

The Discovery chat (`19`, `pages/student/discover/ChatPanel.tsx`) is the product's signature "AI counselor" moment and currently round-trips then dumps the full reply. Stream it.

- **Transport:** consume the SSE token stream from `57` §1 via `lib/realtime.ts` (`54` §9). The endpoint is `POST /me/discovery/sessions/{id}/messages` (Plan-2 orchestrator, already wired per CLAUDE.md).
- **UX:** tokens append into the assistant bubble as they arrive (cobalt caret while streaming); the typing-dots indicator shows only during the pre-first-token latency, then yields to streamed text. The live **artifact rail** (GoalStack / NeedsMap / IdentitySignals) updates when the turn's `extracted_signals` land — a visible "the counselor understood you" beat (the emotional job, `64` §2).
- **Fallbacks (`54` §7):** on AI failure the chat shows the rule-based fallback text (never an error bubble); on stream interruption it falls back to the buffered full response. `FallbackNote` if `source != "ai"`.
- **Reduced-motion:** streaming still streams (it's information, not decoration) but the caret blink is disabled.

This is the single highest perceived-intelligence upgrade in the refinement; it depends on `57` SSE being live end-to-end (`64` §9).

---

## 7. Reduced-motion matrix

`prefers-reduced-motion` and `data-reduce-motion` already gate animations; make the policy explicit (`69` cross-ref):

| Motion | Full | Reduced |
|---|---|---|
| page-in / stagger | animate | instant (opacity only, no translate) |
| hover lift / press | animate | static (no transform) |
| skeleton shimmer | shimmer | static muted block |
| scale-in popovers | scale+fade | fade only |
| chat streaming | stream + caret blink | stream, no blink |
| earned-gold glow | pulse | static gold ring (still marks the success, no motion) |

Rule: reduced-motion **never** removes *information* (streaming, state changes, the success mark) — only the decorative delta.

---

## 8. Feedback & notifications (already strong — keep, standardize)

`showToast` (`stores/toast-store.ts`) is product-grade: variant-aware auto-dismiss (errors sticky), `aria-live`, used in 103 files; `NotificationBell` streams via SSE. Keep. Standardize: errors → sticky toast with a retry/Undo action where applicable; success → transient; never use a toast for inline feedback that belongs in place (copy, field save → §5).

---

## 9. Build tasks (checklist)

- [ ] Add the named-transition utilities (§3) + the single `--shimmer` keyframe (§4) to `index.css`; document the vocabulary in `02` §18.
- [ ] Close the curve seam: keep the app curve, document the decision, ensure no component imports the Landing curve.
- [ ] Build `SkeletonCard`/`SkeletonTable`/`SkeletonRing` mirroring real layouts; retire ad-hoc `animate-pulse` blocks.
- [ ] Replace inline `animationDelay` staggers (`ChatPanel.tsx`, `MiniCounselorPanel.tsx`) with `stagger-list`.
- [ ] Build the optimistic earned-gold success pulse helper; wire to Confirm-enrollment (`35`) and other earned beats.
- [ ] Add inline copy-to-clipboard + the Undo-toast pattern; reserve `ConfirmDialog` (`67`) for irreversible actions.
- [ ] Stream Discover chat via `57` SSE; live artifact-rail update on `extracted_signals`; fallback behavior per `54` §7.
- [ ] Implement the reduced-motion matrix (§7) and verify every entry.

---

## 10. Acceptance

- [ ] Every animation uses a named token (no inline `cubic-bezier`/`animationDelay` in components).
- [ ] One shimmer; skeletons match their final layout (no CLS on content swap).
- [ ] Discover chat streams tokens; artifact rail updates mid-conversation; AI failure shows fallback, not an error bubble.
- [ ] The earned-gold success pulse fires once, only on earned beats, only student-side.
- [ ] Reduced-motion removes decoration but never information; verified against the §7 matrix.
- [ ] No layout-animating properties (`width`/`top`/etc.) in transitions; `CLS < 0.1` holds (`54` §8).

---

## 11. Open questions

- **Streaming readiness.** Confirm `57` SSE token-streaming is live for `POST /me/discovery/.../messages` before scheduling §6; otherwise ship the artifact-rail-on-completion upgrade first and stream second.
- **Motion library vs CSS.** Hand-rolled CSS keyframes (current) vs a small library (e.g. Framer Motion) for the stagger/exit choreography. Recommend staying CSS-first for bundle size (`54` CWV); adopt a library only if exit-animation orchestration proves painful.
- **Undo vs confirm boundary.** Which destructive actions get Undo-toast (reversible) vs `ConfirmDialog` (irreversible)? Enumerate with `67`.
