# 43 · Data Rights, Privacy, and Fairness Governance

> The contractual commitments UniPaith makes to students and institutions about how their data is collected, used, retained, and disposed of — and the operational mechanisms (consent levers, audit ledger, fairness auto-halt) that enforce them.
>
> Status: **draft v1.0** · 2026-05-29 · Sources: Master Paper §Risk/Compliance + Appendix A consent block, Landing_MVP `InstitutionFairness.jsx` + brand values, competitor analysis (Element451 + Salesforce Trust Layer norms).

---

## 1. Brand commitments (verbatim from Landing_MVP — these are contractual)

The 4 brand values that govern this entire surface:

1. **Fit, not fame.** "We match students to programs where they'll thrive — not where the brand ranks highest."
2. **Explain everything.** "Every match, every score, every recommendation comes with reasoning." → operationalized in `42-ai-agents-claude.md` rationale agents + `02-design-system.md` §15 (every AI score has a Why affordance).
3. **Partnership, not extraction.** "We exchange value for data — we don't sell it." → operationalized in §3 (no third-party data sale).
4. **Bias-avoidance is a practice.** "It's not a checkbox. Every cohort is audited; flags escalate to humans; decisions are never fully automated." → operationalized in §6 (fairness auto-halt).

These four sentences appear verbatim on the marketing site, in the institution sales deck, and (in slightly compressed form) in the in-app "Why we collect this" tooltips for sensitive fields.

---

## 2. Consent — the 4 levers

Per Master Paper Appendix A output: `consent_usage_mask: {matching, outreach, analytics, training}`. All four are independent boolean toggles per student.

| Lever | Default | What it controls | What it does NOT control |
|---|---|---|---|
| `matching` | **true** | Whether profile data feeds the match engine and downstream AI agents that personalize results. | Whether the student can still browse anonymously. |
| `outreach` | **false** | Whether institutions can send the student campaign messages (internal platform or external email). | Whether the student receives system messages from UniPaith. |
| `analytics` | **false** | Whether de-identified, aggregated activity is included in cross-cohort insights and product improvement. | The `audit_log_event_stream` (always recorded for the student's own audit trail). |
| `training` | **false** | Whether the student's data is included in any future training corpus for a UniPaith-tuned model. | Whether their data is sent to LLM providers at inference time (controlled by `matching`). Anthropic does not train on customer data by default; this lever is for our own future fine-tuning pipelines. |

Default rationale:
- `matching=true` because the product is unusable without it; consent is gathered at signup with clear language.
- The other three default to **false** so the student opts in explicitly.

Enforcement points:
- **Inference layer (every Claude call site).** Per `03-llm-claude-migration.md` §11 + `42-ai-agents-claude.md` agent contract.
- **Outbound campaign send.** Per `23-campaigns.md` audience build — `consent.outreach=false` excludes the student.
- **Analytics export pipeline.** Per `26-attribution-funnel-analytics.md` cohort builder — `consent.analytics=false` excludes from cross-cohort aggregates (the student still sees their own data).
- **Training corpus extractor.** Per `41-adaptive-intake-engine.md` provenance — `consent.training=false` excludes from any corpus export.

Consent change UX (Student Profile `?tab=data`):
- Four toggles with one-line explanations.
- Below each toggle: "Last changed: <date>. Change history (audit log)."
- Save button writes `consent_timestamps` array entry + new `consent_version_id` reference.

---

## 3. The "we don't sell raw student data — ever" stance

Strict policy:
- **No raw PII** ever exits UniPaith systems to any third party other than the data subject's chosen recipients (institutions to which they apply, recommenders they invite, verification services they consent to).
- **No raw PII** ever appears in cross-institution analytics. Institutions see their own funnel data + aggregates over consenting students only. No institution sees another institution's applicants.
- **No raw PII** ever feeds a UniPaith-tuned model unless `consent.training=true` AND the student is informed of which model (provider + model_id) at the time of the consent change.
- **No raw PII** is sold, licensed, or rented. UniPaith's revenue is the platform subscription (students) and the per-applicant fee (institutions). There is no data-broker line of business and there never will be.

This is contractual language for the institution MSA and the student Terms of Service.

---

## 4. Regulatory regimes

| Regime | Applies when | Key requirements UniPaith honors |
|---|---|---|
| **FERPA (US)** | Any US college/university student record. | Directory information release preference; school-official exception for institution access; right to inspect; right to correct. |
| **GDPR (EU/EEA)** | Any student domiciled in EU, OR any institution with EU students. | Lawful basis (consent for outreach/analytics/training; contract for matching); right to access; right to erasure (subject to retention exceptions); right to data portability; DPA + sub-processor list. |
| **CCPA / CPRA (California)** | California-resident students. | Notice at collection; right to know; right to delete; right to opt out of sale (always opted out per §3); right to limit use of sensitive PI. |
| **NY Education Law §2-d** | Any student in a NY K-12 or higher-ed institution. | Parents-bill-of-rights for student data; data-security/privacy plan; subcontractor obligations. **Watch BigFuture's $750K 2024 NY AG settlement as the template UniPaith must avoid.** |
| **India DPDP Act (2023)** | Any Indian student. | Notice + consent in plain language; right to correction/erasure; data-fiduciary obligations. |
| **COPPA (US)** | Students under 13 (rare for college apps but possible for early outreach). | Verifiable parental consent; no targeted advertising. |
| **APP (Australia)** | Australian students or institutions. | Standard privacy principles. |
| **HIPAA (US)** | Only if disability / health data crosses the platform — typically only `disability_*` and immunization fields. | Treat health fields as health-pii; restrict access; BAA with sub-processors that touch them. |

UniPaith does not currently hold any of these certifications. Goals:
- **Year 1:** Plain-English privacy notice; in-product privacy controls; vendor diligence on every sub-processor.
- **Year 2:** SOC 2 Type II certification; published Trust page (modeled on Slate, Salesforce Trust Layer).
- **Year 3:** Multi-region data residency (US / Canada / EU).

---

## 5. Data retention

| Data type | Default retention | Notes |
|---|---|---|
| Account (auth) | Indefinite while active; 30-day grace after deletion request, then full purge. | |
| Profile signals (Prompt Library §3) | Indefinite while account active. On deletion request → purge after grace. | |
| Application packets | 7 years after last cycle activity (matches FERPA + audit norms). | Institutions may extend per their own retention contract. |
| Discovery transcripts | 1 year after last activity; archive then auto-purge. | Long-tail data; not load-bearing after one cycle. |
| Engagement telemetry (§3.16) | 18 months rolling. | Aggregated; raw events purged. |
| AI audit ledger | 7 years. | Compliance and fairness audits. |
| Consent change history | Indefinite. Required for regulatory defense. | |
| Documents (transcripts, portfolios) | Same as application packets (7 yr). | |
| Search queries (raw text) | 90 days. Opt-in only. | |
| Disability / health-pii | Same as profile + on deletion: redact, don't archive. | |
| Criminal / disciplinary disclosures | Same as application + lock from any non-essential read after decision. | |

A student-initiated deletion request always wins, subject to:
- A 30-day grace window (during which the request can be reversed).
- Legal hold exceptions (active disputes, regulatory inquiries).
- Aggregated, non-PII analytics retained (consent.analytics doesn't entitle deletion of aggregates that no longer identify the student).

---

## 6. Fairness — the auto-halt commitment (verbatim from Landing_MVP)

> "If disparate-impact Δ exceeds 0.20 for two consecutive weeks, the model stops scoring new applicants for that cohort."

This is the single most concrete commitment in the entire corpus. It is contractual.

### 6.1 Definitions

- **Disparate-impact ratio (DI):** for a binary outcome (e.g., recommended-by-match for a given program) and a protected attribute (e.g., race / gender / first-gen / international), DI = `P(positive | minority) / P(positive | majority)`.
- **Δ:** `|1 - DI|`. So `Δ > 0.20` means the minority's positive rate is more than 20 percentage points different from the majority's.
- **Cohort:** intake_round × program. (e.g., Fall 2026 R1 of "MS CS at U of Foo".)
- **Protected attributes tracked:** race/ethnicity (where institution collects), gender identity, first-generation status, international status, nationality region. Disability and veteran status when sufficient sample size and where institution opt-ed in.
- **Sample size minimum:** 50 scored applicants per cohort per week to compute a statistically meaningful DI. Below threshold → flag as "insufficient sample" not "fair/unfair."

### 6.2 Auto-halt mechanism

```
Every Monday 00:00 UTC:
  for each (program × intake × protected_attribute):
    compute DI for the prior week
    if Δ > 0.20:
      record fairness_signal(severity=high, week_n)
      if previous week also had Δ > 0.20:
        set programs.matching_halted = true
        set fairness_signal(severity=auto_halt, week_n)
        notify institution admin + UniPaith ops
```

Halt scope: only the matching service stops scoring new applicants for that cohort. Existing scores remain. Students whose applications were already scored proceed normally.

### 6.3 Override workflow

- Institution admin can request override at `/i/admissions?tab=fairness-overrides` after reviewing the signal.
- Override requires: (a) institution admin role, (b) a written rationale (≥ 100 chars), (c) acknowledgment that the override is logged.
- Approved override sets `programs.matching_halted=false` and `programs.fairness_override_active=true` with `override_expires_at` (default: 1 week, max: 4).
- Every override is audit-logged with actor + rationale + timestamp + signal context.

### 6.4 Dashboard surface

A `Fairness` panel in `/i/dashboard` shows:
- Current halt status (green / yellow if approaching threshold / red).
- Per-cohort DI trend (4-week sparkline).
- Latest signal events.
- "Open Fairness page" link to the full dashboard with per-attribute breakdown.

A dedicated page at `/i/admissions?tab=fairness` shows:
- Per-cohort × attribute heatmap.
- Halt history with all overrides.
- Threshold configuration (default 0.20, tunable per program with documented justification + audit-logged change).

### 6.5 Data model

```python
class FairnessSignal(Base):
    id: UUID = primary_key
    program_id: UUID = fk
    intake_round_id: UUID = fk
    week_start: date
    protected_attribute: enum<race, gender, first_gen, international, nationality_region, disability, veteran>
    cohort_size: int
    di_ratio: float
    delta: float
    severity: enum<info, warning, high, auto_halt, override_active>
    sample_sufficient: bool
    notes: text
    created_at: datetime

class FairnessOverride(Base):
    id: UUID = primary_key
    fairness_signal_id: UUID = fk
    institution_admin_id: UUID = fk
    rationale: text
    override_expires_at: datetime
    created_at: datetime
    revoked_at: datetime | null
```

### 6.6 Test (G-T3)

Integration test seeds a synthetic cohort with Δ > 0.20 for 2 consecutive weeks; asserts `programs.matching_halted=true` after the second week's compute.

---

## 7. The audit ledger as compliance backbone

Per `03-llm-claude-migration.md` §8 and `40-prompt-library-schema.md` §4.16 output `audit_ledger_entry_bundle`.

Every AI inference writes:
- `provider`, `model_id`, `prompt_version`, request/response timestamps, token counts, cost.
- `student_id`, `consent_mask` at request time, `agent_name`.
- `success`, `failure_reason`.

This ledger is the source for:
- **Cost dashboards** — per-student, per-agent, per-provider.
- **Compliance audits** — proof that every call respected consent at the time of request.
- **Fairness audits** — input to disparate-impact compute.
- **Provider performance** — latency P95, failure rate, cache hit rate.
- **Model drift** — outputs over time for a stable input → flags when behavior shifts unexpectedly.

Retention: 7 years.

---

## 8. Student rights — what they can do

In `/s/profile?tab=data`:

| Right | UX |
|---|---|
| **See what we have** | Portable export button: downloads JSON + PDF of every signal stored for the student. |
| **Correct anything** | Every profile section is editable. Documents replaceable; raw inputs retained per provenance. |
| **Change consent** | Four toggles per §2. |
| **See who saw your data** | View access log: which institutions, when, what fields. |
| **Delete account** | Triggers 30-day grace + full purge (with retention exceptions called out). |
| **Object to AI processing** | If `consent.matching=false`, no AI agent runs against this student's data. UI explains the consequence (no personalized matches, no rationale, no Discovery chat). |
| **Withdraw a specific application** | Per-application; removes from institution's queue per the institution's own retention policy. |

---

## 9. Institution rights — what they can configure

In `/i/settings?tab=data`:

| Configuration | Notes |
|---|---|
| Fairness threshold per program (default 0.20, range 0.05–0.40) | Tightening below 0.10 with sample <100 likely false-positives; warned in UI. |
| Override expiry window default (default 1 week, max 4 weeks) | |
| Protected attributes tracked (default: all available where institution collects them) | Some institutions don't collect race/ethnicity in jurisdiction — disable per attribute. |
| Data residency election | US (default) / Canada / EU — Phase 14 deferred. |
| No-training tier | Override student `consent.training` to ALWAYS false for institution's program data. (Default: respect per-student consent.) |
| Sub-processor list visibility | Institution can view UniPaith's sub-processor list for diligence. |
| Data export (institution's own funnel) | CSV / JSON downloads. |

---

## 10. Sub-processor list

What we use, and what each one touches.

| Sub-processor | What it touches | Data classification | Region |
|---|---|---|---|
| AWS (ECS, RDS, S3, CloudFront) | All production data | All classes including PII | us-east-1 (default) |
| Anthropic API | Inference inputs (student data, application packets) at call time | PII (during inference; not retained per Anthropic policy) | US |
| OpenAI API (parallel fallback) | Same as Anthropic | Same | US |
| AWS Cognito | Auth credentials | PII | us-east-1 |
| AWS SES | Outbound email | PII (recipient address) | us-east-1 |
| Stripe (planned) | Payment card on file | Financial PII | US |
| ACH B2B processor (planned) | Institution payments | Institution billing data | US |
| Sentry (or equivalent) | Error telemetry | Should NOT capture PII (sanitization required) | US |

Each sub-processor agreement: SOC 2 Type II (or audited equivalent); DPA; sub-processor list of their own; uptime SLA; data-residency commitment where available.

A "no model training on UniPaith data" clause is required for every LLM provider.

---

## 11. Disclosure UX — privacy nudges

The Master Paper makes a hard point: **trust is the precondition**. Disclosure UX:

- **At signup:** privacy notice with 4 consent toggles default-correct per §2. Plain language. Required to proceed.
- **Before adding sensitive fields:** inline "Why we ask" tooltip explaining the use and naming the consent lever that controls it. Example, on the disability accommodation form: *"Used to surface accommodation-friendly programs. Stored under your matching consent; never sent to institutions until you apply. Change here →"*.
- **When AI generates content visible to the student:** the `AI assist` badge per `02-design-system.md` §15 + the AI Rationale Popover.
- **When an institution accesses the student's profile:** the access shows up in `/s/profile?tab=data` access log; first-time access from a new institution triggers an in-app notification "U of Foo viewed your application today."

---

## 12. Compliance checklist (cross-cutting)

For any new feature touching student data:

- [ ] Field categorization (core / conditional / program-specific / major-specific) declared.
- [ ] Sensitivity (public / pii / pii-sensitive / policy-gated / health-pii) declared.
- [ ] Consent lever explicitly mapped (matching / outreach / analytics / training).
- [ ] Retention specified per §5.
- [ ] AI agent path declared in `42-ai-agents-claude.md` (if any).
- [ ] Audit ledger row written on every read/write that affects PII.
- [ ] Student visibility: data shows up in the portable export + access log.
- [ ] Institution visibility: data shows up in institution's "applicants you can see" scope only when consent + application both authorize.
- [ ] Sub-processor list updated if a new vendor touches the data.
- [ ] Retention test (purge job removes the data after retention window).

---

## 13. Open questions / known gaps

- **In-product privacy notice review.** The notice text is not yet drafted. Should be reviewed by privacy counsel before MVP launch.
- **Consent-tier inheritance for institutions.** When an institution sets "no-training tier" override (§9), does it propagate retroactively? Recommendation: prospectively only; existing audit rows note the previous policy.
- **Cross-border data flow.** Hosting US-only initially. EU/UK students' data flows to US; need Standard Contractual Clauses in DPAs.
- **Children (COPPA).** Most college applicants are 17+ but the platform may capture some <13 users via early-counselor partnerships. Confirm legal posture and either block under-13 or implement COPPA-compliant parental consent.
- **Right-to-delete vs application archive.** When a student requests full deletion, what happens to applications they've submitted to institutions whose retention contract requires keeping them? Recommendation: hash + anonymize after grace; institution keeps the anonymized record.
- **Fairness threshold per attribute.** Currently one threshold (0.20) applies to all attributes. Some attributes (e.g., first-generation status) may warrant tighter thresholds in selective programs. Defer to product owner.
