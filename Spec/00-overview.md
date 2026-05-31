# 00 · UniPaith MVP — Build-Ready Spec Index

> Canonical specification set for the UniPaith MVP. One file per feature/page, plus cross-cutting foundation docs. Each spec is self-contained and build-ready: route, IA, user goal, visual layout, components, data shape, states, edge cases, copy, brand-compliance checklist, AI integration, and current-vs-spec gap.

- **Version:** v2.0 · 2026-05-30 (renumbered contiguous 00–49)
- **Owner:** Leo Zhu — leozjc@unipaith.co
- **Audience:** anyone building the MVP — human engineers, designers, or coding agents.
- **Count:** 53 numbered specs (`00`–`52`) + `ASSETS.md` = 54 docs. Numbering is contiguous — no gaps. (`50`–`52` are build-integration docs derived from the live code.)

---

## 1. Source materials

These are the ground-truth inputs every spec was derived from. If any spec contradicts them, the source wins.

| Source | Location | Purpose |
|---|---|---|
| **Master Paper** | `/Users/leozhu/Desktop/工作/UniPAith/Master Paper.docx` | Canonical product spec — every feature definition. |
| **Business Methodology** | `…/Business Methodology.docx` | Strategic positioning, voice, market thesis. |
| **Brand Visual Guide** (23 pp) | `…/UniPaith_Brand_Visual_Guide.pdf` | Wordmark, monogram, color, typography, tokens. |
| **Brand assets** | `…/Brand Materials/` | SVG wordmarks, favicons, color HTML refs, namecard. |
| **Canonical CSS** | `White-Paper/design_extracted/.../colors_and_type.css` | The single source of truth for tokens (embedded in `01` §11). |
| **Prompt Library / Map** | `Misc./Prompt Library.docx`, `Misc./Prompt Map.pdf` | Signal schema (input + output). |
| **Feature List / Roadmap** | `Misc./Feature List V1.docx`, `Misc./Roadmap.docx` | Feature checklist + founder sequencing. |
| **Competition Analysis** | `…/Competition Analysis.docx` | 18 competitor profiles, moat taxonomy. |
| **Architecture diagram** | `Misc./UniPaith-Architecture-Flow*.png` | 9-stage module flow (transcribed in `06`). |
| **Existing MVP** | `/Users/leozhu/Desktop/工作/UniPAith/App_MVP/` | Current code state (gap audits). |
| **CLAUDE.md** | `App_MVP/CLAUDE.md` | Project conventions, IA decisions, invariants. |

---

## 2. How to use these specs

1. **Start with the foundation docs** (`00`–`07`). Every feature spec assumes you've read brand tokens, design system, IA, architecture, and the LLM migration plan.
2. **Pick a feature doc** matching what you're building. Each lists its own dependencies and downstream consumers.
3. **Honor the brand-compliance checklist** at the end of every feature doc. Stated invariants:
   - No decorative images, gradients, or color accents on program detail pages.
   - Editorial, program-specific aesthetic — not generic marketing.
   - Confirm WHICH component is being changed (explore card vs detail page) before editing.
4. **When implementing**: run the project pre-work checklist first (DB up, Docker running, build green, tests passing — see `CLAUDE.md`).
5. **When LLM work is involved**: route through the Claude provider per `04-llm-claude-migration.md` — swap providers, not call sites.

---

## 3. Spec file map

Naming convention: `NN-slug.md`. Two-digit prefix, **contiguous 00–49** (no gaps). `ASSETS.md` is unnumbered (a catalog, not a spec).

### Foundation & cross-cutting design (00–07)
- `00-overview.md` — this index.
- `01-brand-tokens.md` — colors, type, spacing, elevation, radii, embedded SVGs + canonical CSS, voice. (Europa via Adobe Typekit.)
- `02-design-system.md` — component rules: buttons, inputs, cards, modals, nav, tables, chips, AI-rationale popovers.
- `03-design-system-mobile.md` — responsive/mobile: breakpoints, mobile nav, per-pattern transforms, touch ergonomics.
- `04-llm-claude-migration.md` — agent-by-agent OpenAI→Claude port, model selection, prompt caching, env, cost.
- `05-information-architecture.md` — full route map (student + institution + public + auth), role guards, nav, cross-page links.
- `06-architecture.md` — module-by-module platform flow, the 3-layer AI engine, information flow, service topology.
- `07-product-context.md` — positioning, beachhead/GTM, pricing, competitive moat, market-validated pains, performance targets, funding.
- `ASSETS.md` — embedded brand-asset catalog (SVG/CSS verbatim) + binary-asset paths + source-doc provenance map.

### Student-side features (08–21)
- `08-universal-profile.md` — 19-section profile workspace + completion meter + edit-first UX.
- `09-program-match.md` — guided shortlist with reasoning, dual scores, probability bands, iterative refinement.
- `10-discovery.md` — type-first NL search + LLM query interpretation + constraint chips + filters.
- `11-detail-pages-program.md` — program evaluation page (Insights, costs, net-price estimator). No hero images.
- `12-detail-pages-school.md` — institutional context + program directory gateway.
- `13-saved-list.md` — saved hub, reach/target/safer grouping, compare, one-click application conversion.
- `14-workshops.md` — resume / essay / test workshops, **feedback-only** (no generation — schema-enforced).
- `15-applications.md` — per-application workspace, program-adaptive checklist, readiness gate, app-cost tracker.
- `16-calendar.md` — admissions deadlines + interview events + work blocks, application-linked.
- `17-inbox.md` — application-threaded messages, action labels, attachments, human vs system separation.
- `18-decisions-offers.md` — outcomes tracking, offer capture, side-by-side comparison, post-submission.
- `19-discovery-stage-conversation.md` — Stage-1 LLM-led 3-track journey (Profile / Goals / Needs), chat + artifact rail.
- `20-connect.md` — Stage-3a Connect: Updates / Events / Peers from followed institutions; `/s/posts`.
- `21-settings.md` — settings for **both roles** (account, security, locale, notifications, data-rights entry, deletion).

### Institution-side features (22–30)
- `22-institution-profile-page.md` — public school presence, posts, events, program directory.
- `23-program-detail-page-institution.md` — program editor (deadlines, requirements, cost, outcomes, test policy).
- `24-data-upload.md` — admissions history / prospect lists / outcomes with mapping, versioning, validation.
- `25-campaigns.md` — internal platform messaging + external SES email with trackable links.
- `26-audience-segmentation.md` — reusable segments by activity/intent/readiness/uploaded lists.
- `27-posts-updates-events.md` — unified publishing with promotion controls and performance tracking.
- `28-attribution-funnel-analytics.md` — funnel attribution from impression → application outcome.
- `29-institution-messaging.md` — institution inbox/messaging (mirror of `17`); reason-coded threads, AI drafts, bulk.
- `30-institution-setup.md` — first-run institution wizard (`/i/setup`); orchestrates profile/program/data/team.

### Admissions system (31–41)
- `31-admissions-intake.md` — pipeline + dashboard, queue management, batch actions.
- `32-review-workspace.md` — rubric scoring, side-by-side reviewers, cohort compare, blind review, calibration.
- `33-interviews-module.md` — interview types, scheduling, prep, recording handling.
- `34-decisions-offers-institution.md` — decision release, offer terms, yield management.
- `35-enrollment-yield.md` — enrollment confirmation, intent forms, waitlist movement, yield analytics (Stage 8 tail).
- `36-audit-log.md` — append-only audit trail for compliance.
- `37-ai-extensibility.md` — AI-assistive layer: drafts, summaries, prioritization — humans keep final action.
- `38-international-admissions.md` — credential eval, I-20/DS-2019, English proficiency, visa coordination. *(Phase-2)*
- `39-fees-payments.md` — application fees, waivers, deposit gateway, refunds. *(Phase-2)*
- `40-recruitment-crm.md` — pre-applicant prospect mgmt, travel, territory. *(Phase-2)*
- `41-graduate-admissions.md` — faculty-advisor matching, funding-package builder, department portal. *(Phase-2)*

### Cross-cutting data & AI (42–46)
- `42-prompt-library-schema.md` — enumerated catalog of profile signals (input + output), behavioral layer.
- `43-prompt-library-major-specific.md` — per-discipline readiness field catalog (15 tracks).
- `44-adaptive-intake-engine.md` — multi-source signal population, raw/normalized/derived/engagement, provenance + confidence.
- `45-ai-agents-claude.md` — per-agent system prompts, tool schemas, cache breakpoints, fallback behavior.
- `46-data-rights-privacy.md` — FERPA, consent, no-training tiers, retention, audit, fairness.

### Meta (47–49)
- `47-current-vs-spec-gap-audit.md` — what's in the codebase today, what's missing/mislabeled, what to archive.
- `48-build-sequencing.md` — recommended phase order, dependencies, parallelizable workstreams.
- `49-feature-backlog.md` — every Feature List V1 item, mapped to a spec, classified MVP-core / extend / defer.

### Build integration (50–52) — front↔back readiness, derived from the live code
- `50-api-contract.md` — the front↔back handshake: envelope, auth, errors, pagination + the authoritative router map (26 routers / 276 routes) from real code; OpenAPI at `/docs` is machine truth.
- `51-data-model.md` — consolidated table map (28 live tables) with key columns, FKs, JSONB blobs, and an explicit "spec'd-but-not-built-yet" list.
- `52-mvp-acceptance-runbook.md` — the "ready to use, front+back" gate: two end-to-end critical-path journeys, per-surface DoD, integration gates, launch blockers, seed data, run/deploy verify.

---

## 4. Build order (quick reference)

See `48-build-sequencing.md` for the full plan. TL;DR phase order:

1. **Foundation** — brand tokens + design system + IA + LLM migration (`01`–`05`).
2. **Student spine** — Profile → Discovery chat → Match → Detail → Saved → Applications (`08`,`19`,`09`,`11`,`13`,`15`).
3. **Institution spine** — Profile → Programs → Data → Admissions intake → Review (`22`,`23`,`24`,`31`,`32`).
4. **Cross-cutting** — Prompt Library + Adaptive Intake + AI agents + Data rights (`42`–`46`).
5. **Polish** — Calendar, Inbox, Connect, Workshops, Decisions, Settings, Analytics.
6. **Phase-2** (post-MVP, up-market) — International, Fees/Payments, Recruitment CRM, Graduate (`38`–`41`).

---

## 5. Status

All 53 numbered specs (`00`–`52`) + `ASSETS.md` are written and detailed — no stubs, no numbering gaps. The four Phase-2 docs (`38`–`41`) are full specs but explicitly sequenced after the MVP per the beachhead strategy (`07` §3, `49` §5). Docs `50`–`52` (API contract, data model, acceptance runbook) are build-integration references derived from the live `unipaith-backend`/`frontend` code so a builder can wire front and back to a single contract and verify "ready to use" end-to-end.
