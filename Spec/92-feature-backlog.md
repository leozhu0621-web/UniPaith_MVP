# 92 · Feature Backlog — Feature List V1 Coverage Map

> Every feature in `Misc./Feature List V1.docx`, mapped to the spec that covers it OR flagged net-new. Classifies each as MVP-core, MVP-extend, or defer. Nothing from the founder's feature list is silently dropped.
>
> Status: **draft v1.0** · 2026-05-29 · Source: `Misc./Feature List V1.docx` (+ cross-checked against `Misc./Roadmap.docx`).

---

## 1. How to read

- **Covered** = a current spec already specifies it (named).
- **Net-new** = not in the spec set; needs a spec or a section added.
- **Class:** `core` (in the primary journey, build for MVP) · `extend` (enhancement to a covered surface) · `defer` (Phase 2+ / post-MVP scope).

The Feature List explicitly exceeds a two-sided MVP boundary in places (deposit gateways, I-20 generation, IPEDS). Those are marked `defer` — they're real product scope but not MVP-blocking.

---

## 2. Student-side features

| Feature | Status | Spec | Class |
|---|---|---|---|
| Universal Profile (19 sections) | Covered | `10` | core |
| Program Match (results + reasoning, banded) | Covered | `11` | core |
| Discovery (NLP search, chips, tiles, compare) | Covered | `12` | core |
| Program Detail Page (+ Insights) | Covered | `13` | core |
| School Detail Page | Covered | `14` | core |
| Saved List (reach/target/safer, compare) | Covered | `15` | core |
| Workshops (resume/essay/test, feedback-only) | Covered | `16` | core |
| Applications (adaptive checklist, readiness gate) | Covered | `17` | core |
| Calendar | Covered | `18` | core |
| Inbox (human/system, action labels) | Covered | `19` | core |
| Decisions & Offers (compare, accept/decline) | Covered | `1A` | core |
| Discovery chat (3-track LLM) | Covered | `1B` | core |
| **Probability Bands** (admit/scholarship/waitlist) | ✅ Written | `11` §4A | extend |
| **Net Price Estimator** (program COA + scholarship matches, NPC import, gap analysis) | ✅ Written | `13` §3.3a | extend |
| **Offer Package Explainer** (line-item cost/aid/terms) | Covered (partial) | `1A` §3 + `42` §15 OutcomeBrief | core |
| **Support Plan Preview** (tutoring/disability/writing-center per program, pre-apply) | **Net-new** | new section in `13` | defer |
| **Readiness Tracker w/ peer context** ("top 15% vs school") | ✅ Written | `10` §15 (Analytics) + `40` §4.5 | extend |
| **Thank-You Note Tracker** (recommenders) | **Net-new** | `10` Preparation §11.4 | defer |
| **Letter Request Templates / brag sheets / recommender resume gen** | **Net-new** | `10` §11.4 | defer |
| **Campus Visit Tracker** | **Net-new** | `18` Calendar event type | defer |
| **Student Connect** (Updates/Events/Peers from followed institutions) | ✅ Written | `1C` | core |
| **Alumni Network Connection** (find alumni from your HS, info interviews) | **Net-new** | `1C` §14 (admit-mentor) future | defer |
| **Offline Mode** | **Net-new** | cross-cutting PWA | defer |
| **Voice Input (dictation)** | **Net-new** | `1B` accessibility | defer |
| **Multi-Device Sync w/ conflict resolution** | **Net-new** | infra | defer |
| **Profile Export → Common App / Coalition format** | ✅ Written | `10` §16 (Data) | extend |
| **LinkedIn profile sync** | ✅ Written | `10` §16 + `41` §5.3 | extend |
| **Application Cost Tracker** (fees, waivers, CSS/FAFSA deadlines) | ✅ Written | `17` §2A | extend |

---

## 3. Institution-side features

| Feature | Status | Spec | Class |
|---|---|---|---|
| Institution Profile Page | Covered | `20` | core |
| Program Detail Editor | Covered | `21` | core |
| Data Upload | Covered | `22` | core |
| Campaigns (internal + external SES) | Covered | `23` | core |
| Audience Segmentation | Covered | `24` | core |
| Posts / Updates / Events | Covered | `25` | core |
| Attribution & Funnel Analytics | Covered | `26` | core |
| Admissions Intake (dashboard, batch) | Covered | `30` | core |
| Review Workspace (rubric, cohort compare) | Covered | `31` | core |
| Interviews Module | Covered | `32` | core |
| Decisions & Offers | Covered | `33` | core |
| Audit Log | Covered | `34` | core |
| AI Extensibility | Covered | `35` | core |
| **Institution Messaging / Inbox** (reason-coded threads, AI drafts, bulk send) | ✅ Written | `27` | core |
| **Enrollment Management** (confirmation, intent forms, **waitlist movement**, yield analytics) | ✅ Written | `33b` | extend |
| **Deposit *payment* gateway** (real collection, refunds) | Deferred | `37` (Phase-2) | defer |
| **Blind review mode** | ✅ Written | `31` §7A.1 | extend |
| **Reader calibration tools** (inter-rater reliability) | ✅ Written | `31` §7A.2 | extend |
| **Multi-stage review workflow + workload balancing** | **Net-new** | `31` extend | defer |
| **Committee-review scheduling** | **Net-new** | `31` extend | defer |
| **International tooling** (credential eval WES/ECE tracking, **I-20/DS-2019 generation**, English-proficiency verification, country-specific reqs, visa-interview scheduling) | **Net-new** | new `36-international-admissions.md` | defer |
| **Test-score management** (direct import SAT/ACT/TOEFL, superscoring calc, **test-optional analysis**, verification) | ✅ Written | `21` §3 + `31` §7A.3 | extend |
| **Fee management** (app-fee collection, waiver workflow, deposit gateway, refunds) | **Net-new** | new `37-fees-payments.md` | defer |
| **Alumni Interviewer Network** (portal, geo assignment, training, performance) | **Net-new** | extend `32` | defer |
| **Recruitment / pre-applicant tools** (prospect mgmt before apply, travel calendar, HS-visit scheduling, college-fair reg, **territory management**) | **Net-new** | new `38-recruitment-crm.md` | defer |
| **Transfer-student tools** (credit eval, articulation tracking, transfer-GPA calc) | **Net-new** | extend `30` | defer |
| **Graduate/PhD tooling** (**faculty-advisor matching**, research-interest alignment, **funding-package builder TA/RA/fellowship**, department review portal) | **Net-new** | new `39-graduate-admissions.md` | defer |
| **Holistic-review flags** (first-gen/low-income, **legacy/development tags**, **athletic-recruit tags**, context cards) | ✅ Written | `31` §7A.4 (with `43` fairness) | extend |
| **Compliance** (**IPEDS** reporting, FERPA tools, SIS export Slate/Common App import, API webhooks) | **Net-new** (partial in `43`) | extend `43` + integrations | defer |
| **Transcript Parsing (OCR)** | ✅ Written | `41` §3.1/§5.3 + `42` §19 | extend |
| **Communication channels** (SMS, **WhatsApp**, embedded chat widget, auto-response bot) | **Net-new** | extend `23` / `19` | defer |
| **Mobile App for Reviewers** (offline, push) | **Net-new** | infra | defer |

---

## 4. Net-new spec docs

### ✅ Written this pass (MVP gaps closed)
| Doc | Covers |
|---|---|
| `1C-connect.md` | Student Connect (Stage 3a) — Updates / Events / Peers from followed institutions. |
| `27-institution-messaging.md` | Institution inbox/messaging — mirror of `19`; reason-coded threads, AI drafts, bulk. |
| `33b-enrollment-yield.md` | Enrollment confirmation, intent forms, waitlist movement, yield analytics. |
| `02b-design-system-mobile.md` | Responsive/mobile system. |

### ⏸️ Deferred to Phase-2 (up-market / out of MVP — see `06` §3 beachhead)
| Doc | Covers |
|---|---|
| `36-international-admissions.md` | Credential eval, I-20/DS-2019, English proficiency, visa scheduling (institution-side). |
| `37-fees-payments.md` | Application fees, waivers, deposit gateway, refunds (Stripe/ACH). |
| `38-recruitment-crm.md` | Pre-applicant prospect mgmt, travel/territory, fairs. |
| `39-graduate-admissions.md` | Faculty-advisor matching, funding-package builder, department portal. |

> Student-side international support (visa fields, readiness) IS in MVP (`40` §3.3, `13`); only institution-side international *processing* is deferred.

---

## 5. MVP cut recommendation

**Build for MVP (core + high-value extend):**
- All 13 student core + all 13 institution core (already covered by specs `10`–`35`).
- Extend: Probability Bands, Net Price Estimator, Offer Package Explainer, Profile Export to Common App format, LinkedIn sync, Application Cost Tracker, Readiness peer context, Enrollment/Deposit confirmation (not gateway), blind review + calibration, test-optional analysis, transcript OCR, holistic-review flags.

**Defer (Phase 2+):** international tooling, fee gateways, alumni-interviewer network, recruitment CRM, graduate/PhD tooling, IPEDS, multi-channel comms, mobile reviewer app, offline/voice.

Rationale: the deferred set is largely **enterprise-admissions depth** that matters for up-market institutions but not for the beachhead (community colleges, regional publics — see `06-product-context.md`). Ship the two-sided core + the student-facing decision-support extensions first; layer enterprise depth as institutions demand it.

---

## 6. Roadmap ordering tension (flag for the founder)

Per `Misc./Roadmap.docx`, the founder sequences:
- **Program Match (Phase 2) BEFORE Discovery upgrade (Phase 3).**
- **Conversational/AI intake LAST (Phase 7).**

The **as-built MVP leads with an LLM-led Discover chat at `/s`** — effectively the inverse. This isn't wrong (the chat-first onboarding is a strong hook), but it's a deliberate divergence from the founder's intended sequence. **Decision needed:** keep chat-first (current) or re-sequence to structured-Match-first per the roadmap. Captured in `91-build-sequencing.md` §20.

This spec set assumes **chat-first stays** (matches the shipped IA and CLAUDE.md), but `06-product-context.md` notes the founder's framing treats conversational intake as the capstone.
