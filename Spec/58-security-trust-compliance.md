# 58 · Security, Trust & Compliance

> Production security posture: OWASP controls, authn/authz hardening, PII protection, upload safety, trust & safety / moderation, FERPA/GDPR operations, supply chain, incident response. Companion to `46` (data rights/consent policy) and `55` (the ops substrate).
>
> Status: **draft v1.0** · 2026-05-30 · Production-parity track. Several items are launch blockers (`52` §5).

---

## 1. AuthN / AuthZ

- Cognito (prod) / dev bypass (`50` §2); JWT verified server-side every request.
- **Role guards + owner checks** on every endpoint — a student can only read/write their own records; institution scoped to its tenant (`50` §2). Test the negative paths (403).
- MFA available (`21` §2.2); session revocation; password reset path (launch blocker if absent).

## 2. OWASP Top-10 controls

- **Injection**: parameterized SQLAlchemy only; no string-built SQL. Pydantic validation on all input (422).
- **Broken access control**: deny-by-default; owner/tenant check helper used everywhere; audit access to sensitive records.
- **SSRF**: the crawler (`60`) fetches only allowlisted domains; no user-supplied URL fetched server-side without validation.
- **XSS**: React escaping; sanitize any rendered markdown (posts, essays); CSP header.
- **CSRF**: token auth (not cookies) mitigates; if cookies used, CSRF tokens.
- Security headers: CSP, HSTS, X-Content-Type-Options, Referrer-Policy.

## 3. PII protection

- Encrypt at rest (RDS/S3 KMS) + in transit (TLS).
- **PII minimization to AI**: human-facing Claude calls get only consented, task-scoped, **masked** context (`45` `consent_mask`); Qwen processes PII in-VPC (`63` §12).
- Field-level sensitivity per `42` (pii / pii-sensitive / policy-gated); access-logged.
- Retention + soft-delete + 30-day purge (`46`); right-to-export + right-to-delete.

## 4. Upload safety (`08`/`15` documents)

- Type + size validation; virus scan; store in S3 (private, signed URLs); never execute; strip metadata where needed; OCR/parse in a sandboxed worker (`60`/`63`).

## 5. Trust & safety / moderation

- Peer connection + messaging (`20`/`17`) content moderation; report/block; rate-limit to curb spam/abuse.
- No minor↔adult peer matching (`20` §6.4).
- Integrity signals on applications (`32` §7); fraud/anomaly scoring (Qwen `63`).

## 6. Compliance operations

- **FERPA**: education-record handling, directory-info release prefs, audit trail (`36`/`46`).
- **GDPR/CCPA**: consent ledger (`46` §2), DSAR (export/delete) workflow, lawful-basis records, DPAs with institutions (`46` §9).
- **Fairness/bias** as compliance: cohort audits + auto-halt (`46` §6) — disparate-impact monitoring is a governance control, not just ML.

## 7. Supply chain + secrets

- Secrets via AWS Secrets Manager; never in bundle/repo (launch blocker).
- Dependency scanning (Dependabot/audit); pin + review; SBOM.
- Least-privilege IAM; the OIDC CI role scoped (CLAUDE.md).

## 8. Incident response

- Runbook: detect (alerts `55`) → triage severity → contain → communicate → postmortem (blameless).
- Breach notification process (regulatory timelines); audit log immutability (`36`).

## 9. Launch blockers (subset, see `52` §5)

- [ ] No secrets in bundle; Secrets Manager wired.
- [ ] Role + owner checks on every endpoint (negative tests green).
- [ ] PII encrypted at rest+transit; AI gets masked/consented context only.
- [ ] Consent gate enforced on AI processing (`46` §2).
- [ ] Upload scanning + private storage.
- [ ] Security headers + CSP set.

## 10. Open questions

- WAF (AWS WAF on CloudFront/ALB) — recommend yes at launch.
- Pen-test before GA — schedule once feature-complete.
- Moderation: automated (LLM classifier) vs queue — start queue + cheap classifier.
