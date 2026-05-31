# 38 · International Admissions (Institution Processing)

> Institution-side tooling to process international applicants: credential evaluation, English-proficiency verification, country-specific requirements, immigration-document generation (I-20 / DS-2019), and visa-interview coordination. The student-facing side of international (visa fields, readiness) is already in MVP (`42` §3.3, `11`); this doc is the **institution processing** layer.
>
> Status: **draft v1.0 · Phase-2** · 2026-05-29 · Route: `/i/admissions?tab=international` + per-applicant `/i/pipeline/:studentId?tab=international`. Scope: up-market, beyond the launch beachhead (`07` §3); written for completeness, sequenced after MVP.

---

## 1. Purpose

International applicants carry processing steps domestic applicants don't: foreign credentials must be evaluated to a common scale, English proficiency verified, immigration documents issued, and visa timelines tracked. This module gives admissions staff one workspace for all of it, wired to the same review pipeline (`32`) and the student's visa signals (`42` §3.3 / §4.3).

This is the institution counterpart to the student's visa readiness (`42` §4.3 `visa_feasibility_band`, `visa_readiness_checklist`).

---

## 2. Sub-modules

### 2.1 Credential evaluation
- Track third-party evaluation (WES / ECE / SpanTran) status per applicant: `none / requested / in_progress / received / verified`.
- Store the evaluation report (`student-uploaded` or `third-party-verified`, `42` §3.5 `credential_evaluation_*`).
- **GPA normalization**: map foreign grading systems (UK, IB, A-level, Gaokao, 10-point, percentage) to the program's scale → feeds `normalized_gpa` (`42` §4.5). Reviewers see both raw + normalized.
- Country-grading-system reference table maintained per institution (or platform-default).

### 2.2 English-proficiency verification
- Accepted tests + minimum scores per program (TOEFL / IELTS / DET / PTE), configured in the program editor (`23` §3.3 test policy).
- Direct verification request to the testing body (ETS / British Council) — status only in MVP-of-this-module; live API integration is a sub-phase.
- **Waiver rules**: native-English-country list, prior-degree-in-English rule → auto-suggest waiver eligibility; human confirms.

### 2.3 Country-specific requirements
- Per-country requirement packs (extra documents, attestations, apostille needs) that auto-attach to an applicant's checklist (`15` / `31`) based on `nationality` / `country_of_birth`.
- Editable per institution; platform ships sensible defaults.

### 2.4 Immigration document generation (I-20 / DS-2019)
- After admit + enrollment intent (`35`), generate the **I-20** (F-1) or **DS-2019** (J-1) from the applicant record + financial-proof (`42` §3.3 `financial_proof_*`).
- SEVIS-field mapping; export a SEVIS-batch-compatible file (institutions upload to SEVIS themselves — the platform does not connect to SEVIS directly in this phase).
- Document status: `not_started / drafted / issued / sent / received_by_student`.
- Every generation audit-logged (`36`); immigration docs are high-sensitivity (`46`).

### 2.5 Visa-interview coordination
- Track the student's visa appointment (date, consulate, outcome) as surfaced from their side (`42` §4.3).
- Nudge templates for visa-timeline risk (`29` messaging); link to the student's `visa_timeline_risk_score`.

---

## 3. Where it sits in review

International signals appear as a tab on the review packet (`32`): credential-eval status, normalized GPA, English-proficiency result, country-requirement completeness, visa feasibility band. **Visa/immigration status must never be a selection criterion** — it informs feasibility + yield planning only, gated by fairness rules (`46` §6). Surfaced for operational planning, not admit/deny weighting.

---

## 4. Data shape

```ts
type InternationalProcessing = {
  application_id: string;
  credential_eval: { provider: 'WES'|'ECE'|'SpanTran'|'other'|null; status: 'none'|'requested'|'in_progress'|'received'|'verified'; report_ref: string|null; normalized_gpa: number|null };
  english_proficiency: { test: 'TOEFL'|'IELTS'|'DET'|'PTE'|null; score: number|null; meets_minimum: boolean|null; waiver: { eligible: boolean; basis: string|null } };
  country_requirements: Array<{ item: string; status: 'pending'|'received'|'verified'|'waived' }>;
  immigration_doc: { type: 'I-20'|'DS-2019'|null; status: 'not_started'|'drafted'|'issued'|'sent'|'received'; sevis_id: string|null; issued_at: ISO8601|null };
  visa: { appointment_at: ISO8601|null; consulate: string|null; outcome: 'pending'|'approved'|'denied'|null };
};
```
Endpoints: `GET/PATCH /i/applications/:id/international`, `POST /i/applications/:id/immigration-doc/generate`, `GET /i/international/country-requirements`, `PATCH /i/programs/:id/english-policy`.

---

## 5. AI integration

| Agent | Trigger | Output |
|---|---|---|
| `CredentialNormalizer` (extends `DocumentParseTriage` `45` §19) | Credential report uploaded | Parse foreign transcript → normalized GPA + course map |
| `CountryRequirementAdvisor` | Applicant nationality set | Suggests the country-requirement pack |

Falls back to manual entry on failure. AI never decides feasibility — it structures data for a human.

---

## 6. States

- **Domestic applicant:** tab hidden (no international processing needed).
- **Credential eval pending:** banner "Awaiting WES report"; review can proceed with raw GPA + caveat.
- **I-20 blocked:** "Financial proof insufficient" → links to the missing `42` §3.3 fields.
- **Visa denied:** flag + offer-deferral path (`35`).

---

## 7. Brand compliance

- Operational, data-dense; no decorative imagery; no gold (institution operational surface).
- High-sensitivity fields (immigration, financial proof) visually marked + access-gated per `46`.

---

## 8. Gaps / dependencies

- Depends on `23` test policy, `35` enrollment, `42` §3.3 visa fields, `36` audit, `46` sensitivity gating.
- SEVIS + ETS/British Council live integrations are sub-phases; MVP-of-module = status tracking + document export.
- Country-requirement default packs need sourcing (legal review).

---

## 9. Tests

- Foreign GPA normalizes to program scale; reviewer sees raw + normalized.
- I-20 generation blocked until financial proof present; generation audit-logged.
- International tab hidden for domestic applicants.
- Visa/immigration status excluded from any ranking/score input (contract test, `46`).

---

## 10. Copy

- "Awaiting credential evaluation" / "Normalized GPA: 3.6 (from 85/100)".
- "Generate I-20" / "Financial proof required before issuing."
- "English proficiency: waiver eligible (prior degree in English)."

---

## 11. Open questions

- **SEVIS integration depth** — export file vs API. Start with export.
- **Credential-eval partnerships** — official WES/ECE integration vs manual upload. Manual first.
- **Which immigration docs** — F-1/J-1 only in scope; M-1 and others later.
