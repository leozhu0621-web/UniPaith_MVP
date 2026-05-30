# 05 · Platform Architecture & Information Flow

> The system map: module-by-module flow across the student + institution journey, the 3-layer AI engine, the information flow from inputs → inference → outputs, and the service topology. Reconstructed from the founder's architecture-flow diagram (`Misc./UniPaith-Architecture-Flow.png`), the Prompt Map (`Misc./Prompt Map.pdf`), Landing_MVP `AIEngine.jsx`, and the Master Paper.
>
> Status: **draft v1.0** · 2026-05-29 · Foundation doc — referenced by `40`, `41`, `42`, `03`, and every feature spec.

---

## 1. The module flow (canonical)

The founder's architecture diagram organizes the entire platform into **9 sequential stages**, each with three columns: **Student modules** · **Shared flow** · **Institution modules**. This is the authoritative module map; the IA in `04-information-architecture.md` is its routing realization.

```
STAGE                    STUDENT MODULES            INSTITUTION MODULES
──────────────────────────────────────────────────────────────────────────────
0. Institution Setup     —                          Create Institution Profile
                                                     Publish Program Listings
                                                     Upload Outcomes Data
                                                     Define Target Segments
                                                     Launch Inventory Compliance
                                                     Schedule Recruitment Events
                                                     Catalog & Onboarding

1. Student Onboarding     Onboarding Flow            (Institution Profile,
                          Adaptive Intake             Admissions Analytics,
                          Academic Profile            Audience Segments,
                          Test Scores                 Marketing Campaigns,
                          Activities Profile          Outreach Creation feed
                          Document Vault              from setup)
                          Preferences Engine
                          Profile compile + base AI

2. Discovery & Matching   AI Matching Engine         (signals flow to
                          Search & Browse Programs     Funnel Analytics)
                          Discovery Filters
                          Apply Filters & Constraints
                          Program Details
                          Save Program / Shortlist
                          Save to List
                          Compare Tool
                          Monitor Match Engagement

3. Engagement             Calendar                   CRM:
                          Event RSVP                   Event Analytics
                          Unified Inbox                Communication Tools
                            View Events                Funnel Analytics
                            RSVP to Events
                            Attendance History
                            Inquiry per institution
                            Receive & Restart inquiry
                            Respond / Reply
                            Monitor Student Engagement
                            Update Engagement History

4. Preparation            Resume Workshop            —
                          Essay Workshop
                          Test Planning
                          Workshop Check
                          Readiness Check
                          My Application

5. Application            Run The Submission Queue   Admissions Dashboard
                          Review Deadline Alerts
                          Submit & Track
                          Application Lifecycle

6. Institution Admissions Unified Inbox             Review Application Pipeline
                          Document Vault              Organize Application Queue
                          My Applications             Flag Incomplete Applications
                                                      Verify Materials
                                                      Receive Missing-Item Flags
                                                      Collect Materials
                                                      Assign Reviewer
                                                      Reviewer Assignment
                                                      Process & Rank
                                                      Application Queue +
                                                        Cohort Comparison Pane

7. Interview & Comms      Unified Inbox              Communication Tools
                          Calendar                     Interview Night
                            Send Interview Invitation  Rubric Scoring
                            Send Interview Invitation
                            Validate user in school
                            Schedule date & time
                            Confirm & Select Time
                            Receive interview decision
                            Conduct interview
                            Confirm interview schedule
                            Attend interview
                            Record Interview Outcome

8. Decision & Offer       My Applications            Communication Tools
                          Calendar                     Decision Match
                            Send Status Update         Offer Crafting
                            Status update sent         Rubric Decisions
                            Receive Decision           Offer Analytics
                            Configure Offer values
                            Issue Decision & Build
                            Decision notification sent
                            Review Offer Details
                            Compare All Offers
                            Accept / Decline           CRM · Enrollment Confirm
                            Offer Compare              Yield Analytics
                            Enrollment Window
                            Enrollment Confirmed
```

### Mapping to spec docs

| Stage | Student spec | Institution spec |
|---|---|---|
| 0. Institution Setup | — | `20`, `21`, `22` |
| 1. Onboarding | `1B`, `10`, `41` | (segments from `24`) |
| 2. Discovery & Matching | `11`, `12`, `13`, `14`, `15` | (feeds `26`) |
| 3. Engagement | `18`, `19`, (Connect) | `25`, `26`, `30` |
| 4. Preparation | `16`, `17` | — |
| 5. Application | `17` | `30` |
| 6. Admissions | `17`, `19` | `30`, `31` |
| 7. Interview & Comms | `17`, `18`, `19` | `32`, `31` |
| 8. Decision & Offer | `1A` | `33`, `26` |

This confirms the spec set covers every module in the founder's flow.

---

## 2. The 3-layer AI engine

Per Landing_MVP `AIEngine.jsx` + Master Paper "The AI Layer":

```
┌──────────────────────────────────────────────────────────────────┐
│ LAYER 01 — Online platforms (collect context)                     │
│   The student + institution surfaces capture raw signals:         │
│   chat answers, form fills, uploads, links, platform activity,    │
│   institution datasets.                                            │
│   → writes RAW INPUTS (Prompt Library §3, doc 40)                 │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│ LAYER 02 — LLMs (context → prompts + feature vectors)             │
│   Claude agents (doc 42) normalize, extract, and structure raw    │
│   inputs into canonical signals + embeddings. They also produce   │
│   the human-facing reasoning (rationale, summaries, feedback).    │
│   → writes NORMALIZED + DERIVED signals; emits vectors to L3      │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│ LAYER 03 — ML engine (vectors → matches)                          │
│   Collaborative filtering + pattern recognition + calibrated      │
│   scoring produce fitness/confidence, rankings, risk scores.      │
│   Bias-avoidance is built in (fairness auto-halt, doc 43 §6).     │
│   Trained on permissioned partner data only.                      │
│   → writes OUTPUT FEATURES (Prompt Library §4, doc 40)            │
└──────────────────────────────────────────────────────────────────┘
                              ↓
        LLMs (L2) present ML (L3) outcomes back to the platform
                  with plain-language reasoning.
```

Two hard commitments on this engine (per `43-data-rights-privacy.md`):
- **"We don't sell raw student data. Ever."**
- **Bias-avoidance is a practice** — every cohort audited; auto-halt at disparate-impact Δ > 0.20 for 2 consecutive weeks; decisions never fully automated.

### How LLM (Claude) and ML divide labor

| Task | Layer | Tech |
|---|---|---|
| Extract signals from chat | L2 | Claude Haiku (DiscoveryExtractor) |
| Normalize free text → enum/range | L2 | Claude Haiku |
| Generate match rationale | L2 | Claude Sonnet (MatchRationaleAgent) |
| Compute fitness/confidence scores | L3 | Vector similarity + calibrated classifier |
| Collaborative filtering (students like you applied to…) | L3 | ML (matrix factorization / embeddings) |
| Rank programs for a student | L3 | ML re-ranker + L2 personalization weight |
| Detect fraud / anomaly | L3 | Classical ML + rules |
| Essay authenticity (AI-pattern) | L2 | Claude Haiku (AuthenticityRiskScorer) |
| Strategy narrative | L2 | Claude Sonnet (StrategyAgent) |
| Institution review summary | L2 | Claude Opus (DraftSummarizerForReview) |

The Master Paper line: *"the LLMs will convert the user's context into prompts and feature vectors. The ML engine will convert those prompts and feature vectors into matching recommendations… LLMs will eventually present ML's outcomes back to the platform with adequate reasoning."*

---

## 3. Information flow (inputs → outputs)

Per the Prompt Map (`Misc./Prompt Map.pdf`), the platform has a clean **Incoming Info → Outgoing Info** split that mirrors the Prompt Library's input/output hierarchy (`40-prompt-library-schema.md`).

### Incoming Info (the Prompt Map "left brain")

```
Student                          School / Program
├── Personal Information         ├── School Info (accreditation, location,
├── Academic Background          │     type, enrollment size, calendar,
├── Test                         │     housing, costs, supports, intl office,
├── Activities                   │     diversity data, contacts)
├── Visa                         ├── Program Info (degree & major, modality,
├── Scheduling                   │     length/credits, curriculum, prereqs,
├── Need (housing/support)       │     application components, deadline,
├── Financial                    │     capacity, cost/funding, outcomes,
└── School Preferences           │     experiential, facilities, visa elig.)
                                 ├── Admissions & policy (test policy, scoring,
                                 │     holistic factors, intl docs, scholarship)
                                 ├── History data (admit rate, yield, class
                                 │     profile, scholarship distribution, T2D,
                                 │     outcome trends)
                                 └── Live operational data (application volume,
                                       seat availability, processing time,
                                       event calendar)
```

### Outgoing Info (the Prompt Map "right brain")

```
Student                                  School / Program
├── BEFORE APPLY (discovery & prep)      ├── SHARED-OUTPUT
│   ├── Program match list (ranked,      │   ├── Match Explanation (school: full;
│   │     confidence, top-3 reasons)     │   │     student: redacted, safe)
│   ├── Readiness & Gaps Matrix          │   ├── Engagement Timeline
│   ├── Rigor & trajectory insights      │   ├── Status & SLA Timestamps
│   ├── Net price & scholarship est.     │   └── Messaging Artifacts (templated,
│   ├── Outcome Preview                  │         reason-coded)
│   └── Integrity/Verification Checklist ├── IN-CYCLE OPERATIONS
├── DURING APPLYING (execution)          │   ├── Applicant Reader View (AI rec +
│   ├── Personalized Application Plan    │   │     confidence + evidence link)
│   ├── Requirement Satisfaction Tracker │   ├── Prereq & Policy Engine Output
│   ├── Essay & Interview Guidance       │   ├── Scholarship Optimizer
│   └── Probability Bands                │   ├── Risk & Support Flags
└── AFTER DECISIONS (negotiation/yield)  │   ├── Fraud/Integrity Signals
    ├── Offer Package Explainer          │   └── Yield Probability & Next-Best-Action
    ├── Side-by-Side Comparison          ├── PLANNING (pre-cycle)
    ├── Support Plan Preview             │   ├── Targeting & Capacity Planner
    └── Visa/Housing Readiness           │   ├── Cohort Shaping Simulator
                                         │   └── Pipeline Heatmap
                                         └── POST-CYCLE & COMPLIANCE
                                             ├── Attribution & ROI
                                             ├── Fairness & Bias Dashboard
                                             ├── Audit Ledger
                                             └── Accreditation/Reporting Packs
```

**Key insight from the Prompt Map:** the **Match Explanation is asymmetric** — "school gets the full version; student gets a redacted, safe version." This is a privacy + fairness design choice that belongs in `13-detail-pages-program.md` and `31-review-workspace.md`: the rationale a student sees omits sensitive comparative signals that the institution reviewer sees.

---

## 4. Service topology

Per the Master Paper procurement section + `App_MVP/CLAUDE.md`:

```
                          app.unipaith.co (CloudFront → S3)
                               React 19 + Vite + Tailwind
                                          │
                                          ▼
                          api.unipaith.co (ALB → ECS Fargate)
                               FastAPI + SQLAlchemy 2 (async)
                                          │
                ┌─────────────────────────┼──────────────────────────┐
                ▼                         ▼                          ▼
        PostgreSQL 16 + pgvector   AWS Cognito (auth)         AWS S3 (documents)
        (RDS, in VPC)                                          AWS SES (email)
                                          │
                          ┌───────────────┴───────────────┐
                          ▼                               ▼
              Anthropic API (Claude)            OpenAI API (fallback)
              [L2 LLM agents]                   [parallel failover]
                          │
                          ▼
              In-process ML (L3): pgvector similarity + calibrated
              classifiers + collaborative filtering. (No separate ML
              service in MVP; scale-out candidate for Series A.)
```

Notes:
- **pgvector** in Postgres carries the embedding store (L3 vectors) for MVP — no separate vector DB.
- **L3 ML is in-process** Python in the FastAPI service today (`services/matching.py`, `reranker.py`, `confidence_calibrator.py`, `ml_state.py`). Scale-out (a dedicated ML service / SageMaker) is a Series-A concern.
- **Model-portability** per `03-llm-claude-migration.md` §5 — the provider abstraction means L2 can target Anthropic / OpenAI / Bedrock without touching call sites.
- **SIS/CRM integrations** (Slate, Salesforce Education Cloud, Banner/Workday) reached via published APIs — per the competitor analysis, Slate integration is "must-do day one" (`90` references this).

---

## 5. Data flow invariants

1. **Single source of truth per signal** (`41-adaptive-intake-engine.md` §9). Raw inputs immutable; normalized canonical; derived recomputed on change.
2. **Consent gates every L2 + L3 read** (`43` §2). `consent.matching=false` → no AI processing.
3. **Every L2/L3 output writes an audit ledger row** (`03` §8) with provider+model+tokens+consent_mask.
4. **Cache invalidation** propagates on profile-version / program-version / consent / model / prompt change (`03` §12).
5. **Asymmetric rationale** (Prompt Map): student rationale is the redacted view; institution reviewer sees the full evidence-linked view.

---

## 6. Where the architecture is realized in code

| Layer | Backend location (current) |
|---|---|
| L1 capture | `api/discovery.py`, `api/students.py`, `api/documents.py`, `api/institutions.py` |
| L2 LLM | `services/discovery_service.py`, `match_service.py`, `strategy_service.py`, `workshop_feedback_service.py`, `identity_service.py`, + new `services/ai/providers/` (`03`) |
| L3 ML | `services/matching.py`, `reranker.py`, `confidence_calibrator.py`, `confidence_outcome_service.py`, `ml_state.py`, `program_features.py` |
| Output store | `models/ai_artifacts.py`, `models/matching.py` (extended per `40` §4) |
| Audit | `models/audit.py`, `models/admin_audit_event.py`, + extended `ai_artifacts` (`03` §8) |

---

## 7. Open questions / known gaps

- **L3 ML maturity.** The current ML layer is rule-heavy with calibration. The Master Paper's "collaborative filtering + pattern recognition" implies a learned model trained on partner data — which needs (a) enough partner data, (b) the fairness harness from `43` §6 wired BEFORE training on real cohorts. Sequence: rules → calibrated → learned, gated on data volume.
- **Asymmetric rationale enforcement.** The redaction logic (what the student sees vs the institution) is not yet specified field-by-field. Action: define a redaction map (which matching signals are institution-only) in `13` + `31`.
- **Dedicated vector store.** pgvector suffices < ~1M program-student pairs; beyond that consider a dedicated store. Series-A.
- **ML service extraction.** In-process ML limits independent scaling. Extract when matching latency P95 exceeds budget.
- **Real-time vs batch inference.** Match scores: cached + recomputed on profile change. Engagement-derived scores (apply propensity): nightly. Fairness: real-time. Confirm the cadence per output family.
- **Architecture diagram source.** The founder's `UniPaith-Architecture-Flow.png` (+ `_1/_2/_3` zoom variants) is the authoritative module map; if the product scope changes, update that diagram and this doc together.
