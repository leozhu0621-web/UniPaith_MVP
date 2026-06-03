# 72 · Verification & Integrity Intelligence — Transcripts, Credentials, Fraud, Auto-Profiling

> The papers put authentication at the center of the review stage: *"set up student profiles based on their materials using our algorithms (third-party applicants). Then it authenticates the materials using various methods to rule out fraudulent play and introduces manual approval if needed"* (`Master Paper`:90), under the hard rule that this stage *"is intended to have a human in the loop for all decision-making"* (`Master Paper`:88). The `Business Methodology` even types the outputs precisely — *anomaly score, document authenticity confidence band, duplicate identity likelihood score, fraud risk flag, trust band/score, clarification requests* (`Business Methodology`:1927-1936) — and sets the operating SLO: *"a 24–48 hour verification turnaround"* (`Business Methodology`:829). What ships is a thin slice: `scan_integrity` (`review_pipeline_service.py:697`) is **five rule-based checks** — a duplicate-application count, a `gpa > 4.0` guard, static test-score ranges, a missing-name check, and one real agent (`AuthenticityRiskScorer`, essays only). There is **no transcript OCR, no GPA recalculation, no prerequisite check, no tamper-evident hash, no credential/test-score verification, no trust/fraud ML, and no third-party auto-profiling.** `StudentDocument` (`student.py:282`) stores a `file_url` + `extracted_text` but **no content hash** — nothing makes a document tamper-evident; `DocumentParseTriage` (the one upload agent) reads only *aggregate row counts* (`document_parse_triage.py:33`), never a single document, and its flag is **OFF in prod** (`ai_data_parse_triage_v2_enabled=False`, `config.py:331`; absent from `infra/ecs.tf`).
>
> This spec makes application materials trustworthy at scale. It **extends, never duplicates**: the existing `IntegritySignal` table + resolve workflow (`31` §6), the `AuthenticityRiskScorer` agent (`45` §18), `DocumentParseTriage` (`45` §19), and `CredentialNormalizer`'s grading-scale mapper (`38` §2.1) are the foundation — this turns their heuristic scoring into eval-gated ML signals and adds the missing primitives (OCR, tamper-evidence, fraud/trust scoring, auto-profiling) behind them. Every integrity output is **flag-and-score only; a human decides** (the `37` assistive-layer contract, `Master Paper`:88).
>
> Build anchor: extend `services/review_pipeline_service.py:697` (`scan_integrity`) + `models/application.py:405` (`IntegritySignal`); add `student_documents.content_hash` + a `document_verifications` table; new `services/verification/` (OCR → transcript-normalize → prerequisite → tamper-hash → fraud/trust scorer → auto-profiler) on a 24–48h queue; processing models are Qwen (`63` §2, no human contact), Claude only for human-facing clarification prose. Pairs with `31` (IntegritySignal workflow), `37` (assistive-layer/human-in-loop), `38` (`CredentialNormalizer`), `45` §18/§19 (agents), `46`/`58` (document PII), `62` (eval gate), `08`/`42` (canonical profile schema), `36` (audit), `55`/`73` (queue).
>
> Status: **draft v1.0** · 2026-06-02 · turns five rule-based integrity checks into transcript OCR + tamper-evidence + fraud/trust ML + third-party auto-profiling, all human-in-the-loop, on a verification SLO. Rule-based path stays the fallback (`tests/test_plan2_integration.py`).

---

## 1. What exists vs what to build

| Capability | Real module today | Status |
|---|---|---|
| Integrity signal table + resolve workflow | `IntegritySignal` (`application.py:405`); `resolve_integrity_signal` (`review_pipeline_service.py:959`) | exists — **keep, feed richer signals** |
| Integrity scan | `scan_integrity` (`review_pipeline_service.py:697`) — 5 rule checks | exists — **extend with §2–§4 signals** |
| Essay authenticity scorer | `AuthenticityRiskScorer` (`ai/authenticity.py:84`, Haiku) | exists — keep; one of many fraud inputs (§3) |
| Foreign-GPA mapper | `deterministic_normalize` (`credential_normalizer.py:87`) | exists — **OCR feeds it; per-standard recalc (§2)** |
| Document store | `StudentDocument` (`student.py:282`) — `file_url`, `extracted_text` | exists — **add `content_hash`; add `document_verifications`** |
| Transcript OCR + parse | none (`DocumentParseTriage` reads aggregate counts only) | **NEW (build): per-document OCR → structured courses** |
| GPA recalculation (per-standard) + prerequisite check | none | **NEW (build): Liaison's moat** |
| Tamper-evident verification (hash) | none (no doc hash anywhere; `content_hash` at `matching.py:205` is crawler-only) | **NEW (build)** |
| Credential/test-score verification (WES/ECE/ETS/IELTS) | provider **status string only** (`international.py:54`) | **NEW (build): verify-vs-self-reported state** |
| Fraud / anomaly / duplicate-identity / trust ML | none (rule checks only) | **NEW (build): the `1927-1936` outputs** |
| Third-party-applicant auto-profiling | none | **NEW (build): raw materials → canonical profile (`08`/`42`)** |
| 24–48h verification SLO + queue | none | **NEW (build): queue (`55`/`73`) + human-in-loop** |

## 2. Transcript OCR → normalization → prerequisite check (start here)

The deepest incumbent moat: Liaison's CAS does *"automated coursework verification … GPA recalculation per discipline standards, and prerequisite checking"* (`Competition Analysis`:1344). UniPaith has the GPA *mapper* (`credential_normalizer.py:87`) but nothing to feed it — no OCR, no course extraction. Build the pipeline:

- **OCR + structured extraction (Qwen, `63` §2.4 / rule-based fallback).** A transcript document (`StudentDocument`, `document_type='transcript'`) → OCR → `{institution, term, course_code, course_title, credits, grade}[]` + the stated GPA/scale. Schema-strict, **grounded — never invents a course or grade** (`62` extraction gate, mirrors the crawler extractor's "never-invents" contract). PII-heavy, so it runs in-VPC on Qwen (`63` §12), never the API.
- **Per-standard GPA recalculation.** Recompute GPA on the *target program's* scale from the extracted courses — not just map a single number. Reuse `deterministic_normalize`'s bands (`credential_normalizer.py:38-72`: percentage/UK/IB/A-level/Gaokao/10-point) as the per-system table; extend to course-weighted recalculation (credits × grade-points). Reviewer sees **raw stated GPA, extracted-courses GPA, and program-scale GPA** side by side — the existing `38` §2.1 "raw + normalized" pattern, deepened.
- **Prerequisite checker.** Against a program's stated prerequisite list (CIP/SOC-tagged where available, `69`), match extracted coursework → `met / partial / missing` per prerequisite, with the satisfying course cited. Deterministic; the match is evidence-linked, not a black box.
- **Output is advisory.** Recalculated GPA and prerequisite gaps surface in the review packet (`32`) and as `IntegritySignal`s when they **contradict** self-reported data (e.g., stated 3.8 vs recalculated 3.1) — a human reconciles; the engine never overwrites the applicant's record or auto-rejects (`37` rule 1).

## 3. Tamper-evident verification & third-party credential/score checks

ApplyBoard's `ApplyProof` is the benchmark: *"tamper-evident document verification used by institutions and visa offices to validate Letters of Acceptance and other admission documents"* (`Competition Analysis`:454). Today no document carries a hash; verification status is a free-text string.

- **Tamper-evident hash.** On upload, compute and store `student_documents.content_hash` (SHA-256 of the file bytes; `String(64)`, mirrors the crawler's `RawIngestedData.content_hash` at `matching.py:205`). Any later re-fetch / re-submission re-hashes and compares → a `document_modified` integrity signal on mismatch. The hash is recorded in the audit ledger (`36`) so the chain of custody is auditable. (Full cryptographic signing / verifiable-credential issuance is a sub-phase; the hash + audit chain is the v1 tamper-evidence.)
- **Verified-vs-self-reported status.** Add a `document_verifications` table: `document_id` FK, `verification_kind` (`transcript`/`credential_eval`/`test_score`/`identity`), `method` (`self_reported`/`hash_match`/`third_party_api`/`manual`), `status` (`unverified`/`pending`/`verified`/`failed`/`discrepancy`), `provider`, `evidence` JSONB, `verified_by`/`verified_at`, provenance. Every field a reviewer trusts carries a verification state, not a guess.
- **Credential evaluation integration (WES/ECE).** `38` already tracks the provider + status (`international.py:54`); this adds the *verification call seam* — a `CredentialVerifier` port that, given a WES/ECE reference, confirms the report (API where a partnership exists, manual-confirm otherwise) and flips `document_verifications.status` to `verified`. Manual-first per `38` §11; the abstraction lets a live API drop in without touching callers (mirrors `39`'s `PaymentProvider` seam).
- **Test-score verification (ETS/TOEFL, British Council/IELTS).** A `ScoreVerifier` port against the testing body's verification service (ETS `TOEFL`, British Council `IELTS` — both already named in `reference.py:103` / `crawler/sources.py:165`). Until a live integration exists, status stays `self_reported` and **says so** (truthful, `64` §7) — a self-reported score is never silently shown as verified.

## 4. Fraud / integrity intelligence — the `1927-1936` outputs

The papers enumerate the exact integrity outputs (`Business Methodology`:1927-1936). Today only a duplicate-*application* count and range checks exist. Build the scoring layer, all writing into the existing `IntegritySignal` workflow (`31` §6):

- **Anomaly score (cross-field/doc consistency).** A numeric over inconsistencies *across* the profile + documents: stated-vs-recalculated GPA (§2), OCR'd transcript vs self-reported coursework, test scores vs academic record, timeline impossibilities, document metadata anomalies. Deterministic consistency rules first; Qwen/classical scoring once `67` has labels.
- **Document-authenticity confidence band** (categorical). Generalizes today's essay-only `AuthenticityRiskScorer` (`ai/authenticity.py`) across document types (transcript / credential / essay), combining the tamper-hash result (§3), OCR-extraction confidence, and AI-pattern tells. Keeps the agent's **conservative "better silent than false-positive"** posture (`authenticity.py:160`).
- **Duplicate-identity likelihood** (numeric). Beyond same-student-same-program (the existing check at `review_pipeline_service.py:731`): fuzzy cross-account matching on identity signals (name/DOB/email/document-hash collision) → a likelihood score, not an auto-merge. Privacy-bounded (`46`/`58`).
- **Trust band + trust score** (low/med/high; numeric) = **verification coverage × cross-field consistency** — how much of this application is verified and internally coherent. Surfaces in the review packet and feeds review-priority (`31`), **never the admit decision** (§5).
- **Fraud risk flag** (policy-gated, categorical) + **clarification requests list** (what needs explaining). Each writes an `IntegritySignal` (`signal_type` ∈ the above) routed to the existing resolve workflow (`acceptable` / `requires_clarification` / `reject_application`, `application.py:444`). The clarification *prose* (the message to the applicant) is Claude (human-facing, `63` §3); the *scores* are Qwen/classical (`63` §2).

**Human-in-the-loop is the invariant** (`Master Paper`:88, `37` rule 1): every score/flag is advisory; the auto-halt-on-fairness applies (`46` §6) but **no integrity score auto-rejects, auto-merges, or auto-blocks** — a reviewer acts, and the action is audited (`36`).

## 5. Third-party-applicant auto-profiling

The papers' under-built obligation: *"set up student profiles based on their materials using our algorithms (third-party applicants)"* (`Master Paper`:90). For an applicant who arrives via a third-party channel with **raw materials but no UniPaith intake**, algorithmically build a profile:

- **Document parse → canonical profile.** Raw materials (transcript, CV/resume, essays, test reports) → the OCR/extraction pipeline (§2) → mapped into the **canonical student profile schema** (`08` universal profile + `42` signal vocabulary). This is the same taxonomy the in-house intake produces — so a third-party applicant becomes comparable to a UniPaith student for matching (`65`) and review (`32`). Goes **beyond intake forms**: it reconstructs the profile from artifacts.
- **Provenance + confidence per field.** Every auto-derived field carries `source=auto_profiled`, the source document, and an extraction confidence — distinct from student-asserted fields. Low-confidence fields are flagged for human confirmation, never presented as student-verified.
- **Consent + governance.** A third-party-built profile is processed under the institution's DPA and `46` rules; PII-heavy processing stays in-VPC on Qwen (`63` §12); it never enters any training set without the consent tier `67` §3 requires. Auto-profiling **structures data for a human reviewer; it does not decide** (`38` §5 posture, extended).
- **Reuse, don't fork.** This is `DocumentParseTriage`/`CredentialNormalizer` pointed at *per-document content* (today triage sees only aggregate counts, `document_parse_triage.py:33`) and writing the *student* profile, not an institution dataset. Same agents, deeper scope.

## 6. Verification SLO, queue & audit

- **24–48h turnaround** (`Business Methodology`:829). Verification (OCR + credential/score checks + scoring) runs **off the request path** on the async queue (`55` arq / `73`) — never blocking submission. Each document gets a verification task with an SLA clock; a per-institution dashboard shows queue depth and ageing items, and an item nearing 48h escalates (`57` notification).
- **Human-in-loop fallback.** When automated verification is inconclusive (`status='discrepancy'` or low confidence), it routes to **manual approval** — the papers' *"introduces manual approval if needed"* (`Master Paper`:90). The reviewer's decision closes the verification and the linked `IntegritySignal`.
- **Audit.** Every hash, verification state change, score, and manual decision writes to the append-only audit ledger (`36`) with the model version + timestamp (`Business Methodology`:1929 "audit ledger entry bundle (model version + timestamps)").
- **Fallback invariant.** Qwen/OCR/provider unavailable → the deterministic path runs (rule-based consistency checks + self-reported status + manual queue); the endpoint never 5xxes and no document is *blocked* by a verifier outage (`tests/test_plan2_integration.py`, `63` §10).

## 7. Build tasks (checklist)

- [ ] `student_documents.content_hash` (SHA-256, `String(64)`) computed on upload; `document_verifications` table (kind/method/status/provider/evidence/provenance). Migration: Alembic, expand→contract, single head.
- [ ] Transcript OCR + structured extraction (Qwen, `63` §2.4; rule-based fallback), schema-strict + grounded + eval-gated (`62`); per-standard GPA recalculation reusing `credential_normalizer.py` bands; prerequisite checker (evidence-linked `met/partial/missing`).
- [ ] Tamper-evident re-hash compare → `document_modified` signal; chain-of-custody in audit (`36`).
- [ ] `CredentialVerifier` (WES/ECE) + `ScoreVerifier` (ETS/British Council) ports; manual-first, live-API drop-in seam (mirror `39` `PaymentProvider`); self-reported never shown as verified.
- [ ] Fraud/integrity scorer: anomaly score, authenticity band (generalize `AuthenticityRiskScorer` across doc types), duplicate-identity likelihood, trust band/score, fraud flag, clarification list → all write `IntegritySignal` (`31` §6 workflow).
- [ ] Third-party auto-profiler: raw materials → canonical profile (`08`/`42`), `source=auto_profiled` + per-field confidence; consent/PII-gated (`46`/`58`).
- [ ] Verification queue (`55`/`73`) with 24–48h SLA clock + ageing dashboard + escalation (`57`); manual-approval routing on inconclusive.
- [ ] Flag `ai_verification_v2_enabled` (net-new; default off / on-per-env after `62`); ANDs consent; deterministic fallback fully functional. Add to `agent_registry` (batch tier) + `infra/ecs.tf`.
- [ ] Tests: human-in-loop (no score auto-rejects/auto-merges); hash mismatch → signal; recalc-vs-stated discrepancy → signal; verifier outage → deterministic + never-5xx; auto-profiled fields carry provenance; integrity score never enters the admit/rank input (contract test, mirrors `38` §9).

## 8. Acceptance

- [ ] A transcript uploads → OCR extracts courses → GPA recalculated on the program scale → reviewer sees raw + recalculated + per-prerequisite `met/missing`, each course-cited; a stated-vs-recalculated mismatch raises an `IntegritySignal`, not an auto-reject.
- [ ] Every trusted field carries a `document_verifications` state; a self-reported score is **never** displayed as verified; a re-submitted altered document trips `document_modified` via hash compare.
- [ ] `scan_integrity` emits the `Business Methodology`:1927-1936 outputs (anomaly score, authenticity band, duplicate-identity likelihood, trust band/score, fraud flag, clarification list) into the existing resolve workflow.
- [ ] A third-party applicant with only raw materials gets an auto-built profile in the `08`/`42` schema, every auto-derived field tagged `source=auto_profiled` with confidence; low-confidence fields flagged for human confirmation.
- [ ] No integrity/verification output auto-rejects, auto-merges, or auto-blocks — a human acts on every one; the action + model version + timestamp are audited (`36`).
- [ ] Verification runs off the request path within a 24–48h SLA with an ageing/escalation view; a verifier/Qwen outage degrades to deterministic checks + manual queue, never a 5xx and never a blocked submission.
- [ ] Disabling `ai_verification_v2_enabled` returns today's exact rule-based `scan_integrity` behavior (clean fallback, tested); no document data trains a model without the `67` §3 consent tier.

## 9. Open questions

- **Tamper-evidence depth for v1** — content-hash + audit chain now vs cryptographic signing / W3C verifiable credentials. *Recommend hash + audit chain for v1; signed/verifiable-credential issuance as a fast-follow when an institution requires it (the `ApplyProof` parity bar is hash-based validation, `Competition Analysis`:454).*
- **OCR engine** — Qwen-VL self-host (`63` §8, PII in-VPC) vs a managed OCR (Textract/Document AI). *Recommend managed OCR for the pixel→text step + Qwen for structured extraction/normalization initially; self-host the vision model on volume — the win is the pipeline, not the host (mirrors `65` §10's embedder call).*
- **Credential/score verification partnerships** — official WES/ECE/ETS/British Council APIs vs manual-confirm. *Recommend manual-first behind the verifier ports (`38` §11), live API as a partnership lands; status is truthful either way.*
- **Auto-profiling confidence floor** — the per-field confidence below which a field is withheld pending human confirmation rather than auto-populated. *Recommend a conservative floor (silent-over-wrong, matching `AuthenticityRiskScorer`'s posture); tune via `62` once real third-party volume exists.*
- **Duplicate-identity scope** — cross-program within an institution vs cross-institution on the network (privacy-heavier). *Recommend within-institution for v1; cross-network only under explicit consent + `46`/`58` review.*

Sources: internal — `31` §6 (IntegritySignal workflow), `37` (assistive-layer / human-in-loop), `38` §2.1/§5 (`CredentialNormalizer`, WES/ECE), `45` §18/§19 (`AuthenticityRiskScorer`, `DocumentParseTriage`), `46`/`58` (document PII/consent), `62` (eval gate), `08`/`42` (canonical profile schema), `63` §2/§12 (Qwen processing, in-VPC), `36` (audit), `55`/`73` (queue/SLA), `65` (auto-profiled profile feeds matching), `67` §3 (training consent tier); code — `services/review_pipeline_service.py:697,731,959` (`scan_integrity`/resolve), `models/application.py:405` (`IntegritySignal`), `ai/authenticity.py:84,160`, `ai/document_parse_triage.py:33`, `ai/credential_normalizer.py:38,87`, `models/student.py:282` (`StudentDocument`, no hash), `models/matching.py:205` (`content_hash` precedent), `models/international.py:54` (provider status string), `config.py:331` (`ai_data_parse_triage_v2_enabled=False`, absent from `infra/ecs.tf`). Papers — `Master Paper.docx`:88,90; `Business Methodology.docx`:829,1927-1936. Benchmarks — `Competition Analysis.docx`:454 (ApplyBoard `ApplyProof` tamper-evident verification), :1344 (Liaison coursework verification / GPA recalculation / prerequisite checking).
