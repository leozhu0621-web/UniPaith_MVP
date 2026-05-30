# UniPaith MVP — Build-Ready Spec Index

> Canonical specification set for the UniPaith MVP. One file per feature/page, plus cross-cutting foundation docs. Each spec is self-contained and build-ready: route, IA, user goal, visual layout, components, data shape, states, edge cases, copy, brand-compliance checklist, AI integration, and current-vs-spec gap.

- **Version:** v1.0 · 2026-05-29
- **Owner:** Leo Zhu — leozjc@unipaith.co
- **Audience:** anyone building the MVP — human engineers, designers, or coding agents.

---

## 1. Source materials

These are the ground-truth inputs every spec was derived from. If any spec contradicts them, the source wins.

| Source | Location | Purpose |
|---|---|---|
| **Master Paper** (4,227 paragraphs) | `/Users/leozhu/Desktop/工作/UniPAith/Master Paper.docx` | Canonical product spec — every feature definition. |
| **Business Methodology** | `/Users/leozhu/Desktop/工作/UniPAith/Business Methodology.docx` | Strategic positioning, voice, market thesis. |
| **Brand Visual Guide** (23 pp PDF) | `/Users/leozhu/Desktop/工作/UniPAith/UniPaith_Brand_Visual_Guide.pdf` | Wordmark, monogram, color, typography, system tokens. |
| **Brand assets** | `/Users/leozhu/Desktop/工作/UniPAith/Brand Materials/` | SVG wordmarks, favicons, color HTML refs, namecard template. |
| **Color CSS refs** | `Brand Materials/color-{palette,light-theme,dark-theme}.html` | CSS variable spec for both themes incl. status colors. |
| **Reference brand guides** | `Brand Materials/example/` | Discord, AmEx, FOLU, GL, Sydney Univ — voice/structure references only; not visual sources. |
| **Existing MVP** | `/Users/leozhu/Desktop/工作/UniPAith/App_MVP/` | Current code state. Used for current-vs-spec gap audits. |
| **CLAUDE.md** | `App_MVP/CLAUDE.md` | Project conventions, IA decisions, deferred work, invariants. |

---

## 2. How to use these specs

1. **Start with the foundation docs** (`00`–`04`). Every feature spec assumes you've read brand tokens, design system, IA, and the LLM migration plan.
2. **Pick a feature doc** matching what you're building. Each doc lists its own dependencies and downstream consumers.
3. **Honor the brand-compliance checklist** at the end of every feature doc. The user's stated invariants:
   - No decorative images, gradients, or color accents on program detail pages.
   - Editorial and program-specific aesthetic — not generic marketing.
   - Always confirm WHICH component is being changed (explore card vs detail page) before editing.
4. **When implementing**: run the project's pre-work checklist first (DB up, Docker running, build green, tests passing — see `CLAUDE.md`). Do not start feature work in a broken environment.
5. **When LLM work is involved**: route through the Claude provider per `03-llm-claude-migration.md`. The existing model-portable interface means you swap providers, not call sites.

---

## 3. Spec file map

Naming convention: `NN-slug.md`. Two-digit prefix groups specs; lower numbers are higher leverage.

### Foundation (00–06)
- `00-overview.md` — this file.
- `01-brand-tokens.md` — colors, type, spacing, elevation, radii, **embedded SVGs + canonical CSS**, voice. (v1.1 — Europa via Adobe Typekit.)
- `02-design-system.md` — component-level rules: buttons, inputs, cards, modals, nav, tables, chips, AI-rationale popovers.
- `02b-design-system-mobile.md` — responsive/mobile: breakpoints, mobile nav, per-pattern transforms, touch ergonomics.
- `03-llm-claude-migration.md` — agent-by-agent OpenAI→Claude port, model selection, prompt caching, env, cost.
- `04-information-architecture.md` — full route map for student + institution + public + auth, role guards, nav hierarchy, cross-page links.
- `05-architecture.md` — module-by-module platform flow, the 3-layer AI engine, information flow (incoming/outgoing), service topology. (From the founder's architecture diagram + Prompt Map.)
- `06-product-context.md` — positioning, beachhead/GTM, pricing, competitive moat, market-validated pains, performance targets, funding. The "why" behind scope tradeoffs.
- `ASSETS.md` — embedded brand-asset catalog (SVG/CSS verbatim) + binary-asset paths + source-doc provenance map.

### Student-side features (10–1C)
- `10-universal-profile.md` — 19-section profile workspace + completion meter + edit-first UX.
- `11-program-match.md` — guided shortlist with reasoning + iterative refinement.
- `12-discovery.md` — type-first NL search + LLM query interpretation + constraint chips + filters.
- `13-detail-pages-program.md` — program-level evaluation page with Insights tab (student/alumni + employer feedback).
- `14-detail-pages-school.md` — institutional context + program directory gateway.
- `15-saved-list.md` — saved hub with reach/target/safer grouping, compare, one-click application conversion.
- `16-workshops.md` — resume / essay / test workshops, general + program-specific modes, **feedback-only** (no generation — schema-enforced).
- `17-applications.md` — per-application workspace with program-adaptive checklist, readiness gate, external vs internal submission.
- `18-calendar.md` — admissions deadlines + interview events + work blocks, application-linked.
- `19-inbox.md` — application-threaded messages, action labels, attachment handling, human vs system separation.
- `1A-decisions-offers.md` — outcomes tracking, offer capture, side-by-side comparison, post-submission workflow.
- `1B-discovery-stage-conversation.md` — Stage-1 LLM-led 3-track journey (Profile / Goals / Needs) with chat + artifact rail.
- `1C-connect.md` — Stage-3a Connect: Updates / Events / Peers from followed institutions; `/s/posts`.
- `1D-settings.md` — account, security, locale, notifications, data-rights entry, deletion (student + institution); `/s/settings`, `/i/settings`.

### Institution-side features (20–27)
- `20-institution-profile-page.md` — public school presence, posts, events, program directory.
- `21-program-detail-page-institution.md` — program-level public page, deadlines, requirements, cost, outcomes, media.
- `22-data-upload.md` — admissions history / prospect lists / outcomes summaries with mapping, versioning, validation.
- `23-campaigns.md` — internal platform messaging + external email with trackable links.
- `24-audience-segmentation.md` — reusable segments by activity/intent/readiness/uploaded lists.
- `25-posts-updates-events.md` — unified publishing with promotion controls and performance tracking.
- `26-attribution-funnel-analytics.md` — funnel attribution from impression → application outcome.
- `27-institution-messaging.md` — institution inbox/messaging (mirror of `19`); reason-coded threads, AI drafts, bulk.
- `28-institution-setup.md` — first-run institution wizard (`/i/setup`); orchestrates profile/program/data/team.

### Cross-role
- `1D-settings.md` — settings for both roles (account, security, locale, notifications, data-rights entry, deletion).

### Admissions System (30–35, 33b)
- `30-admissions-intake.md` — intake dashboard, queue management, batch actions.
- `31-review-workspace.md` — rubric scoring, side-by-side reviewers, cohort comparison.
- `32-interviews-module.md` — interview types, scheduling, prep, recording handling.
- `33-decisions-offers-institution.md` — decision release, offer terms, yield management.
- `33b-enrollment-yield.md` — enrollment confirmation, intent forms, waitlist movement, yield analytics (Stage 8 tail).
- `34-audit-log.md` — append-only audit trail for compliance.
- `35-ai-extensibility.md` — AI-assistive layer: drafts, summaries, prioritization — humans keep final action.

### Cross-cutting (40–43, 90–91)
- `40-prompt-library-schema.md` — enumerated catalog of profile signals (Master Paper Appendix A).
- `41-adaptive-intake-engine.md` — multi-source signal population, raw/normalized/derived/engagement layers, provenance + confidence.
- `42-ai-agents-claude.md` — per-agent system prompts, tool schemas, cache breakpoints, fallback behavior.
- `43-data-rights-privacy.md` — FERPA, consent, no-training tiers, retention, audit.
- `90-current-vs-spec-gap-audit.md` — what's in the codebase today, what's missing, what's mislabeled, what to archive.
- `91-build-sequencing.md` — recommended phase order, dependencies between specs, parallelizable workstreams.
- `92-feature-backlog.md` — every feature in the founder's Feature List V1, mapped to a spec or flagged net-new, classified MVP-core / extend / defer.

---

## 4. Conventions

- **Markdown only.** No images embedded; ASCII layout sketches when helpful.
- **Tokens, not values.** Every color reference uses a token name (e.g., `--primary`, `--ink`, `paper-cream`) defined in `01-brand-tokens.md`. Never hard-code hex outside `01-brand-tokens.md`.
- **Routes are absolute** (`/s/explore`, `/i/admissions`), never relative.
- **Data shapes use TypeScript-ish notation** for frontend types and SQLAlchemy-ish pseudo-code for backend models, with field names matching the existing codebase where the spec extends rather than replaces.
- **States are enumerated.** Every interactive UI must define loading / empty / error / success states explicitly.
- **Copy strings are literal** — sentence case, no marketing voice, no exclamation marks (see voice rules in `01-brand-tokens.md` §6).
- **AI integration sections** describe: agent name, model tier (Sonnet vs Haiku), input shape, output shape, cache key, fallback when the agent fails or `AI_MOCK_MODE=true`.

---

## 5. Glossary

| Term | Meaning |
|---|---|
| **Universal Profile** | The student's single, reusable, modular profile (19 sections — see `10`). |
| **Program Match** | The guided shortlist workflow (see `11`). |
| **Discovery** | The type-first program-search workspace (see `12`). |
| **My Applications** | The student execution hub for the active cycle (see `17`–`1A`). |
| **Workshops** | Feedback-only preparation workspace (resume, essay, test — see `16`). Schema-enforced: no generation. |
| **Prompt Library** | The canonical signal schema for all profile data (see `40`). Master Paper Appendix A. |
| **Adaptive Intake Engine** | The multi-source signal pipeline that populates the Prompt Library (see `41`). |
| **Display card** | A single program/school card schema reused across Discovery, Compare, Saved, Detail, and institution pages. Edited once, reflected everywhere. |
| **Constraint chip** | Editable LLM-extracted filter applied to a search (e.g., `degree: master's`, `location: USA`, `budget: ≤ $40k/yr`). |
| **Fitness score** vs **Confidence score** | Two-dimensional match scoring. Fitness = how well program matches student. Confidence = how reliable that fitness estimate is given data completeness. |
| **Reach / Target / Safer** | Three-band classification for saved programs based on selectivity vs student profile. |
| **Intake / Round** | A single admissions cycle window for one program (e.g., Fall 2026 Round 1). |
| **Internal submission** vs **External submission** | Internal = student submits through UniPaith and the institution receives the packet via UniPaith. External = student tracks the application in UniPaith but submits on the institution's own portal. |
| **Action label** (Inbox) | The state of a message thread: needs reply, document requested, clarification required, interview invite, status update only. |
| **Provenance** (Prompt Library) | Source of a signal value: student-confirmed, student-uploaded, institution-provided, system-derived. |
| **Confidence** (Prompt Library) | Numeric reliability of an extracted/derived signal value; low-confidence values get flagged for student clarification. |
| **AI Extensibility** | The principle that AI generates drafts and suggestions but never autonomously changes status, sends communications, or issues decisions — humans keep the final action. |

---

## 6. Versioning

Each spec doc carries its own `Status:` line. Allowed states:

- **draft v0.x** — in active authoring; expect changes.
- **draft v1.0** — complete first pass; ready for build.
- **stable v1.x** — built once, refined.
- **archived** — superseded; the file says what replaced it.

Index version (this file): bump the top-of-file `v1.x` when a spec is added or significantly restructured. A typo fix in one feature doc does not bump the index.

---

## 7. What this spec set does NOT cover

- **Brand identity definition.** The wordmark, monogram, colors, type, and proportion rules are decided. This spec applies them; it does not redesign them. Source: `UniPaith_Brand_Visual_Guide.pdf`.
- **Business model decisions.** Pricing, financial model, funding strategy are in the Master Paper sections 1–4 and not duplicated here except where they constrain product behavior (e.g., the 7-day trial paywall affects auth flow → see `04`).
- **Marketing site (unipaith.co).** That's a WordPress install — see `CLAUDE.md`. This spec is for the app at `app.unipaith.co`.
- **Terraform / infrastructure.** AWS topology lives in `App_MVP/infra/`. Specs reference env vars and service names but do not redesign infra.
