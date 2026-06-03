# 64 · Frontend Refinement & Public-Release Readiness — Master Plan

> The anchor for the `64`–`70` refinement series: the plan to take the existing student + institution frontend from "works, but reads like a prototype" to a finished product ready for public release. Grounds every downstream spec in the canonical papers (Master Paper, Business Methodology, Brand Visual Guide, Competition Analysis) and in an audit of the real `frontend/src/` tree. Companion to `01`/`02`/`03` (design foundation), `53` (UX bar), `54` (FE engineering), `52` (acceptance gate).
>
> Status: **draft v2.0** · 2026-06-02 · v2 = first issue. This is a planning + sequencing doc; the buildable detail lives in `65`–`70`. Verify every file path against `frontend/src/` before relying on it.

---

## 1. The honest starting point (ground truth — what exists today)

An audit of `frontend/src/` found a **more mature frontend than "prototype" implies**, and that finding shapes this entire plan. What already exists, product-grade:

- A real design-token system in `src/index.css` `@layer base` + `tailwind.config.js`: HSL light/dark variables, the full shadcn semantic set, three documented elevations, `prefers-reduced-motion` + user `data-reduce-motion`, font-size scaling, dyslexia font, 44px coarse-pointer targets.
- 30 primitives in `src/components/ui/` — `Button` (6 variants, `aria-busy`, loading spinner), `Input` (label-above, reserved error region so layout never shifts), `Modal` (focus-trap + ESC + restore-focus + mobile bottom-sheet dock), `Table` (sticky header, zebra, built-in skeleton + empty), `Toast`, `EmptyState`, `Skeleton`, plus domain primitives (`DualRing`, `BandBadge`, `ConfidenceDots`, `AIBadge`, `AIRationalePopover`, `FallbackNote`).
- `showToast` used in 103 files, skeletons in 103 files, mobile bottom-tab + bottom-sheet nav, SSE `NotificationBell`. **Zero `TODO`/`FIXME`/`console.log` in app code.**

**So the gap is not missing scaffolding. The prototype *feel* comes from inconsistency and uneven finish:**

| Symptom | Evidence (from audit) | Reads as |
|---|---|---|
| **Two competing color vocabularies** | `cobalt`/`charcoal`/`slate`/`student-*` legacy tokens in 100+ files alongside semantic `text-foreground`/`bg-card`; worst on the flagship Match surface (`ExplorePage.tsx`, `match/MatchCard.tsx`) | unfinished, off-brand, dark-mode-fragile |
| **Dark-mode leaks** | `bg-white` hardcoded 69× across 28 files; `text-white` 44×; raw hex in `PageLoader.tsx` | half-built theme |
| **Thin error coverage** | only 45 of 137 `useQuery` files handle `isError`; the rest render nothing on failure; no shared error component | brittle, "demo-ware" |
| **Native browser chrome leaks** | 5 `window.confirm` destructive gates; 44 native `<select>` alongside the styled `Select` | not a designed product |
| **No table maturity** | pagination in only 2 institution files; no sort/density/bulk on dense admissions queues | not enterprise-credible |
| **Scattered a11y** | 295 raw `<button>`, only 37 files with `focus-visible`; no keyboard path for the pipeline Kanban | inaccessible, fails review |

The remedy is **consistency, state-coverage, density, accessibility, and a few signature-moment upgrades** — not a rebuild. That is what `65`–`70` deliver.

---

## 2. What "public-release-ready" means here (from the papers)

The canonical sources define the product's promise; the frontend either earns it or undercuts it. Five paper-grounded principles govern every refinement decision in `65`–`70`.

1. **Explainability is the trust surface.** The Master Paper positions UniPaith against "black-box algorithms" — every AI output must carry "plain-language explanations for why each program is suggested, tied directly to the student's stated inputs." Implication: rationale popovers, confidence surfacing, and `FallbackNote` ("Showing rule-based result") are not decoration — they are the product. Refinement must make them consistent and legible, never hide them. (Detail: `67` state copy, `65` AI-surface tokens.)

2. **Restraint signals craft.** Brand Visual Guide: "Sunlit Yellow is brand punctuation, not a fill — hold it back so it feels earned." Color proportion is fixed (paper `55/20/15/10`; implemented `01` §2 `60/25/10/5` — reconcile in `65` §2). "**No decorative images, gradients, or color accents on program detail pages**" (CLAUDE.md, `01` §9, `11`). Over-coloring actively cheapens the brand → `65` enforces the proportion and the earned-gold rule mechanically.

3. **Cross-surface consistency is the polish.** The Master Paper (lines ~1215-1255) makes the **"display card" schema** a product rule: the same program card appears in Discovery results, the compare tray, saved lists, and detail-page headers — "the information students see stays consistent across the platform." Drift between these reads as unfinished → `65` §6 codifies one card.

4. **The product is a calm friend, not a hype machine.** The student voice derives from the counselor-as-"good friend, good listener" model: "self-service, transparency, and instant feedback," lowering admissions anxiety. UX copy voice (`02` §16) = **Plain · Direct · Honest · Brief · Warm**, sentence case, no exclamation marks. Every new empty/error/onboarding string in `67`/`70` ships in this voice.

5. **Human-in-the-loop is a stated guarantee.** On the institution side the paper is explicit: "this stage is intended to have a human in the loop for all decision-making." The UI must make the human's authority visible and never imply autonomous AI decisions → `68` (institution workspace) keeps AI assistive, cobalt-not-gold, with `AIBadge` + final-action affordances owned by the reviewer.

---

## 3. Benchmark synthesis — domain competitors + design-craft leaders

The refinement borrows from two reference sets (the two the user named: "domain competitors at the market" + "design leaders"). Specs `53`/`54` already benchmark **LinkedIn** (profile/feed/messaging) and **Handshake** (the two-sided rail, and the explicit model for `/s/posts` Connect). This series extends that with the rest of the Competition Analysis and a craft bar.

### 3.1 Domain competitors — what to match or beat (from `Competition Analysis.docx`, 18 profiles)

| Competitor | What they own | UX lesson UniPaith must out-execute |
|---|---|---|
| **Element451** | AI-first admissions OS | The paper's sharpest UX rival — "rebuilt its UX around AI agents as primary actors; contemporary, marketer-friendly UI." Our differentiation "must be sharp": match its modern feel **and** beat it on explainability + two-sided reach. The institution workspace (`68`) is graded against it. |
| **Liaison / legacy CAS** | Deepest grad/professional workflow | "Legacy UX feels dated… complex multi-step verification flows, inconsistent UX between CASs, fees visible." The exact failure mode we beat: **consistent, consumer-grade applicant UX** across the full funnel (`65` consistency, `67` states, `70` forms). |
| **Common App** | Application rail, 50-yr trust | Trusted but "has not yet weaponized its data into AI-native experiences." Beat with AI-native, explainable matching surfaced cleanly (not bolted on). |
| **Niche** | Discovery + 140M reviews (SEO moat) | Huge audience, "low AI, rule-based." Beat by turning discovery into *explainable* matching — the dual-score rings + rationale are the wedge. |
| **Unibuddy** | Peer-chat engagement | "AI Buddy constrained to the institution's own content… hallucination-resistant, confidence scoring, conversation summaries." The paper's verdict: **integrate peer engagement, don't rebuild it** — informs `/s/posts` Connect polish, not a new build. |
| **Handshake** | Two-sided early-career network | The named model for Connect (`20`). Match its feed/event/peer ergonomics. |
| **LinkedIn** | Profile / feed / messaging / notifications | The bar `53` already benchmarks for Profile, Inbox, Notifications. |

**The recurring lesson:** incumbents that own the *workflow* have **dated, inconsistent, fee-visible UX**; those with *modern UX* own only a thin slice (Unibuddy) or are AI-velocity rivals to out-execute (Element451). UniPaith's frontend edge = **consumer-grade polish + explainability + cross-surface consistency applied to the *whole* funnel.** That sentence is the brief for `65`–`70`.

### 3.2 Design-craft leaders — the finish bar (patterns to adopt, on-brand)

These set *how finished* it should feel. Borrow the pattern, never the look — everything renders in UniPaith tokens (editorial duotone, no decoration).

| Leader | Pattern we adopt | Lands in |
|---|---|---|
| **Linear** | Keyboard-first density, instant optimistic feedback, ⌘K command surface, restraint, taut motion | `66` motion, `68` tables/keyboard, `69` a11y; ⌘K already noted `53`/`54` |
| **Stripe** | Forms that never punish, inline validation, world-class empty/error states, calm density | `67` states, `70` forms |
| **Airbnb** | Search → card → detail consistency, trust signals, skeletons that match final layout | `65` card schema, `67` skeletons |
| **Notion** | Empty-to-hero ("here's what this becomes"), progressive onboarding, friendly microcopy | `70` onboarding, `67` empty states |
| **Vercel / Geist** | Dark-mode parity as a first-class theme, motion restraint, monochrome + one accent | `65` dark mode, `66` motion |

---

## 4. The cross-cutting gap themes → spec map

Every gap the audit found maps to exactly one downstream spec (no overlap; each extends rather than restates `53`/`54`).

| Theme | Highest-impact evidence | Owner spec |
|---|---|---|
| Color-vocabulary unification, dark-mode parity, proportion/earned-gold, score-viz family, display-card schema, component↔file map | 2 token systems in 100+ files; `bg-white` ×69; flagship Match surface worst | **65** |
| Motion system, choreography, skeleton shimmer spec, optimistic "earned-gold" beat, chat streaming, app-vs-Landing curve seam | hand-rolled `animationDelay`; static typing dots; unresolved curve in `02` §18 | **66** |
| Loading/empty/error/edge catalog, shared `QueryError`, `ConfirmDialog`, exact copy | 92 `useQuery` surfaces with no `isError`; 5 `window.confirm` | **67** |
| Reusable data-table system (sort/paginate/density/bulk/keyboard/export/saved-views); institution operational credibility | pagination in 2 files; unbounded admissions queues | **68** |
| WCAG 2.1 AA conformance: focus system, ARIA live regions, contrast, keyboard Kanban, native→styled controls | 295 raw `<button>`, 37 with focus-visible; 44 native `<select>` | **69** |
| Onboarding/first-run/activation, first impression, setup-wizard polish, forms-at-scale (autosave, upload, inline-edit) | Discover cold-start, `confirm()` deletes, thin "coming soon" states | **70** |

---

## 5. The series (64–70)

- `64-frontend-refinement-public-release.md` — **this doc**: thesis, paper alignment, benchmark synthesis, DoD, sequencing.
- `65-visual-system-unification.md` — one token vocabulary; dark-mode parity; proportion + earned-gold enforcement; the score-viz family; the display-card schema; component→source-file map; lint guards.
- `66-motion-microinteractions.md` — named transition system; enter/exit + stagger choreography; skeleton shimmer; optimistic success beat; Discover chat streaming; reduced-motion matrix; curve reconciliation.
- `67-state-catalog.md` — per-surface loading/empty/error/edge inventory; shared `QueryError` + `ConfirmDialog` + offline/permission/404/403/500; exact copy in brand voice.
- `68-data-tables-institution-workspace.md` — reusable dense-list/table system; institution-side density, operational credibility, and the "system-of-record" finish.
- `69-accessibility-conformance.md` — WCAG 2.1 AA: focus order + focus-visible, ARIA live regions, contrast audit of token pairs, keyboard Kanban, screen-reader naming for AI/score components.
- `70-onboarding-first-run-activation.md` — student cold-start + path-to-value; auth/first-impression; institution setup-wizard polish (`30`); forms-at-scale (autosave, multi-step, upload, inline-edit).

---

## 6. Definition of Done — public-release readiness checklist

The product is release-ready when **all** of the following hold (each item is owned by the cited spec; `52` remains the front+back acceptance gate this complements).

**Visual & brand (`65`)**
- [ ] One color vocabulary: zero legacy `charcoal`/`slate`/`student-*`/raw-`cobalt` class usages in `src/pages/`; everything routes through semantic tokens.
- [ ] Dark mode survives a `.dark` toggle on every route: zero `bg-white`/`text-white`/inline-hex in `className` (lint-enforced); spot-checked per surface.
- [ ] Gold + cobalt ≤ the proportion budget on every light surface; gold appears only on the one earned beat per region.
- [ ] One display-card component across Discovery / compare / saved / detail headers.

**Interaction & motion (`66`)**
- [ ] Every transition uses a named token; honors `prefers-reduced-motion`/`data-reduce-motion`.
- [ ] Discover chat streams tokens; optimistic actions confirm instantly (the `53` bar).

**States (`67`)**
- [ ] Every `useQuery` surface renders all four states (loading / empty / error / success); no surface renders blank on failure.
- [ ] Zero native `window.confirm`/`alert`; destructive actions use `ConfirmDialog`.

**Density & institution (`68`)**
- [ ] Every dense list paginates or virtualizes; admissions tables sort + support bulk actions; no unbounded fetches.

**Accessibility (`69`)**
- [ ] Keyboard-operable end-to-end incl. the pipeline Kanban; visible focus on every interactive element; AA contrast on all token pairs; axe-core clean on every route.

**Activation (`70`)**
- [ ] First-run path-to-value ≤ 2 meaningful actions on both sides; every empty state has a clear next step in brand voice; long forms autosave.

---

## 7. Sequencing & dependencies

Build order maximizes leverage and respects dependencies. `65` is foundational — it unblocks dark mode and removes the single biggest "unfinished" signal, and several other specs assume one token vocabulary.

```
65 (visual/token unification)  ──┬─→ 66 (motion)        ──┐
   ▲ foundational, do first      ├─→ 67 (states)        ──┼─→ 70 (onboarding/forms)
   └──────────────────────────── ├─→ 68 (tables/inst.)  ──┘   (consumes 65 tokens, 67 states)
                                  └─→ 69 (a11y)  ← runs alongside all; final conformance gate
```

1. **`65` first** — token unification + dark-mode parity. Everything else renders in the unified system; doing it last would force rework.
2. **`66` + `67` + `68` in parallel** — independent surfaces (motion, states, tables) once tokens are unified.
3. **`70`** — onboarding/forms layer on top of unified tokens + the state catalog.
4. **`69` continuous, then final gate** — a11y is built in as each spec lands, then a conformance sweep certifies AA before release.

Cleanup coordination: this series also retires the Phase-E frontend debt that blocks polish — the legacy `student-*`/`school-*` Tailwind aliases (`47` G-B6), the dual-score legacy-field reads in `SchoolDetailPage` (`G-S2`), and the dead/mislabeled pages (`47` G-A2…A7). `65`/`68` reference these so cleanup happens in-stream, not as a separate epic.

---

## 8. Acceptance (this master plan)

- [ ] `65`–`70` exist, each in the house build-spec format, each grounded in real `frontend/src/` paths.
- [ ] Every audit-identified gap (§4) maps to exactly one downstream spec, with no duplication of `53`/`54`.
- [ ] The DoD (§6) is the union of the downstream specs' acceptance checklists — a builder can certify "release-ready" by walking it.
- [ ] Paper-grounded principles (§2) and benchmarks (§3) are cited by the specs that operationalize them.

---

## 9. Open questions

- **Scope of "both sides" parity.** The institution side is operationally deep but less consumer-polished; `68` carries most of its load. Is full visual parity with the student side required for v1, or is "credible + consistent" sufficient for the institution audience (who value system-of-record trust over delight)? Recommend the latter for release; revisit post-launch.
- **Proportion-rule source of truth.** Paper says `55/20/15/10` (paper/ink/cobalt/gold); implemented `01` §2 says `60/25/10/5`. `65` §2 must pick one — recommend deferring to `01` (the implemented token doc) and updating the paper, not the code.
- **How hard to gate.** Should the DoD (§6) become CI-enforced (lint rules for tokens/dark-mode, axe-core per route, a "no blank state" test) or a manual release checklist? Recommend CI for the mechanical items (`65`/`69`) per `54`'s precedent, manual sign-off for the judgment items (motion feel, copy voice).
- **Streaming dependency.** Discover chat streaming (`66`) depends on `57` SSE token-streaming being live end-to-end; confirm before scheduling.
