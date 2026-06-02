# 49 · Feature Backlog — Feature List V1 Coverage Map

> Every feature in `Misc./Feature List V1.docx`, mapped to the spec that covers it OR flagged net-new. Classifies each as MVP-core, MVP-extend, or defer. Nothing from the founder's feature list is silently dropped.
>
> Status: **draft v1.1** · 2026-06-02 · Source: `Misc./Feature List V1.docx` (+ cross-checked against `Misc./Roadmap.docx`).
>
> **Now a live surface.** This coverage map is published at **`/goal/features`** (public; `GET /api/v1/build/features`) with a second axis — `delivered` — showing what's actually in the build today. As of 2026-06-02 every **core + extend** feature is delivered, and four items the v1.0 cut marked `defer` (International §38, Fees §39, Recruitment §40, Graduate §41) shipped **ahead of plan** — so the map shows both the plan class and live reality.

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
| Universal Profile (19 sections) | Covered | `08` | core |
| Program Match (results + reasoning, banded) | Covered | `09` | core |
| Discovery (NLP search, chips, tiles, compare) | Covered | `10` | core |
| Program Detail Page (+ Insights) | Covered | `11` | core |
| School Detail Page | Covered | `12` | core |
| Saved List (reach/target/safer, compare) | Covered | `13` | core |
| Workshops (resume/essay/test, feedback-only) | Covered | `14` | core |
| Applications (adaptive checklist, readiness gate) | Covered | `15` | core |
| Calendar | Covered | `16` | core |
| Inbox (human/system, action labels) | Covered | `17` | core |
| Decisions & Offers (compare, accept/decline) | Covered | `18` | core |
| Discovery chat (3-track LLM) | Covered | `19` | core |
| **Probability Bands** (admit/scholarship/waitlist) | ✅ Written | `09` §4A | extend |
| **Net Price Estimator** (program COA + scholarship matches, NPC import, gap analysis) | ✅ Written | `11` §3.3a | extend |
| **Offer Package Explainer** (line-item cost/aid/terms) | Covered (partial) | `18` §3 + `45` §15 OutcomeBrief | core |
| **Support Plan Preview** (tutoring/disability/writing-center per program, pre-apply) | **Net-new** | new section in `11` | defer |
| **Readiness Tracker w/ peer context** ("top 15% vs school") | ✅ Written | `08` §15 (Analytics) + `42` §4.5 | extend |
| **Thank-You Note Tracker** (recommenders) | **Net-new** | `08` Preparation §11.4 | defer |
| **Letter Request Templates / brag sheets / recommender resume gen** | **Net-new** | `08` §11.4 | defer |
| **Campus Visit Tracker** | **Net-new** | `16` Calendar event type | defer |
| **Student Connect** (Updates/Events/Peers from followed institutions) | ✅ Written | `20` | core |
| **Alumni Network Connection** (find alumni from your HS, info interviews) | **Net-new** | `20` §14 (admit-mentor) future | defer |
| **Offline Mode** | **Net-new** | cross-cutting PWA | defer |
| **Voice Input (dictation)** | **Net-new** | `19` accessibility | defer |
| **Multi-Device Sync w/ conflict resolution** | **Net-new** | infra | defer |
| **Profile Export → Common App / Coalition format** | ✅ Written | `08` §16 (Data) | extend |
| **LinkedIn profile sync** | ✅ Written | `08` §16 + `44` §5.3 | extend |
| **Application Cost Tracker** (fees, waivers, CSS/FAFSA deadlines) | ✅ Written | `15` §2A | extend |

---

## 3. Institution-side features

| Feature | Status | Spec | Class |
|---|---|---|---|
| Institution Profile Page | Covered | `22` | core |
| Program Detail Editor | Covered | `23` | core |
| Data Upload | Covered | `24` | core |
| Campaigns (internal + external SES) | Covered | `25` | core |
| Audience Segmentation | Covered | `26` | core |
| Posts / Updates / Events | Covered | `27` | core |
| Attribution & Funnel Analytics | Covered | `28` | core |
| Admissions Intake (dashboard, batch) | Covered | `31` | core |
| Review Workspace (rubric, cohort compare) | Covered | `32` | core |
| Interviews Module | Covered | `33` | core |
| Decisions & Offers | Covered | `34` | core |
| Audit Log | Covered | `36` | core |
| AI Extensibility | Covered | `37` | core |
| **Institution Messaging / Inbox** (reason-coded threads, AI drafts, bulk send) | ✅ Written | `29` | core |
| **Enrollment Management** (confirmation, intent forms, **waitlist movement**, yield analytics) | ✅ Written | `35` | extend |
| **Deposit *payment* gateway** (real collection, refunds) | Deferred | `39` (Phase-2) | defer |
| **Blind review mode** | ✅ Written | `32` §7A.1 | extend |
| **Reader calibration tools** (inter-rater reliability) | ✅ Written | `32` §7A.2 | extend |
| **Multi-stage review workflow + workload balancing** | **Net-new** | `32` extend | defer |
| **Committee-review scheduling** | **Net-new** | `32` extend | defer |
| **International tooling** (credential eval WES/ECE tracking, **I-20/DS-2019 generation**, English-proficiency verification, country-specific reqs, visa-interview scheduling) | **Net-new** | new `38-international-admissions.md` | defer |
| **Test-score management** (direct import SAT/ACT/TOEFL, superscoring calc, **test-optional analysis**, verification) | ✅ Written | `23` §3 + `32` §7A.3 | extend |
| **Fee management** (app-fee collection, waiver workflow, deposit gateway, refunds) | **Net-new** | new `39-fees-payments.md` | defer |
| **Alumni Interviewer Network** (portal, geo assignment, training, performance) | **Net-new** | extend `33` | defer |
| **Recruitment / pre-applicant tools** (prospect mgmt before apply, travel calendar, HS-visit scheduling, college-fair reg, **territory management**) | **Net-new** | new `40-recruitment-crm.md` | defer |
| **Transfer-student tools** (credit eval, articulation tracking, transfer-GPA calc) | **Net-new** | extend `31` | defer |
| **Graduate/PhD tooling** (**faculty-advisor matching**, research-interest alignment, **funding-package builder TA/RA/fellowship**, department review portal) | **Net-new** | new `41-graduate-admissions.md` | defer |
| **Holistic-review flags** (first-gen/low-income, **legacy/development tags**, **athletic-recruit tags**, context cards) | ✅ Written | `32` §7A.4 (with `46` fairness) | extend |
| **Compliance** (**IPEDS** reporting, FERPA tools, SIS export Slate/Common App import, API webhooks) | **Net-new** (partial in `46`) | extend `46` + integrations | defer |
| **Transcript Parsing (OCR)** | ✅ Written | `44` §3.1/§5.3 + `45` §19 | extend |
| **Communication channels** (SMS, **WhatsApp**, embedded chat widget, auto-response bot) | **Net-new** | extend `25` / `17` | defer |
| **Mobile App for Reviewers** (offline, push) | **Net-new** | infra | defer |

---

## 4. Net-new spec docs

### ✅ Written this pass (MVP gaps closed)
| Doc | Covers |
|---|---|
| `20-connect.md` | Student Connect (Stage 3a) — Updates / Events / Peers from followed institutions. |
| `29-institution-messaging.md` | Institution inbox/messaging — mirror of `17`; reason-coded threads, AI drafts, bulk. |
| `35-enrollment-yield.md` | Enrollment confirmation, intent forms, waitlist movement, yield analytics. |
| `03-design-system-mobile.md` | Responsive/mobile system. |

### ⏸️ Deferred to Phase-2 (up-market / out of MVP — see `07` §3 beachhead)
| Doc | Covers |
|---|---|
| `38-international-admissions.md` | Credential eval, I-20/DS-2019, English proficiency, visa scheduling (institution-side). |
| `39-fees-payments.md` | Application fees, waivers, deposit gateway, refunds (Stripe/ACH). |
| `40-recruitment-crm.md` | Pre-applicant prospect mgmt, travel/territory, fairs. |
| `41-graduate-admissions.md` | Faculty-advisor matching, funding-package builder, department portal. |

> Student-side international support (visa fields, readiness) IS in MVP (`42` §3.3, `11`); only institution-side international *processing* is deferred.

---

## 5. MVP cut recommendation

**Build for MVP (core + high-value extend):**
- All 13 student core + all 13 institution core (already covered by specs `08`–`37`).
- Extend: Probability Bands, Net Price Estimator, Offer Package Explainer, Profile Export to Common App format, LinkedIn sync, Application Cost Tracker, Readiness peer context, Enrollment/Deposit confirmation (not gateway), blind review + calibration, test-optional analysis, transcript OCR, holistic-review flags.

**Defer (Phase 2+):** international tooling, fee gateways, alumni-interviewer network, recruitment CRM, graduate/PhD tooling, IPEDS, multi-channel comms, mobile reviewer app, offline/voice.

Rationale: the deferred set is largely **enterprise-admissions depth** that matters for up-market institutions but not for the beachhead (community colleges, regional publics — see `07-product-context.md`). Ship the two-sided core + the student-facing decision-support extensions first; layer enterprise depth as institutions demand it.

---

## 6. Roadmap ordering tension (flag for the founder)

Per `Misc./Roadmap.docx`, the founder sequences:
- **Program Match (Phase 2) BEFORE Discovery upgrade (Phase 3).**
- **Conversational/AI intake LAST (Phase 7).**

The **as-built MVP leads with an LLM-led Discover chat at `/s`** — effectively the inverse. This isn't wrong (the chat-first onboarding is a strong hook), but it's a deliberate divergence from the founder's intended sequence. **Decision needed:** keep chat-first (current) or re-sequence to structured-Match-first per the roadmap. Captured in `48-build-sequencing.md` §20.

This spec set assumes **chat-first stays** (matches the shipped IA and CLAUDE.md), but `07-product-context.md` notes the founder's framing treats conversational intake as the capstone.
