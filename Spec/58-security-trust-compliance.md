# 58 · Security, Trust & Compliance — Build Spec

> Buildable security/compliance spec grounded in the real auth + consent + safety modules already in the backend (`core/security.py`, `dependencies.py`, `core/data_safety.py`, `ai/consent.py`, `ai/rationale_redaction.py`, `services/guardrail_service.py`). Not a checklist of principles — concrete controls mapped to real files + gaps to build. Companion to `46` (data rights), `50` (API), `55` (substrate), `36`/`34` (audit log).
>
> Status: **draft v2.0** · 2026-05-30 · v2 converts standards → build tasks against real modules.

---

## 1. What exists vs what to build

| Control | Real module today | Status |
|---|---|---|
| AuthN (Cognito JWT + dev token) | `core/security.py` (`verify_token`, JWKS, `_verify_dev_token`) | exists |
| AuthZ role guards | `dependencies.py` (`get_current_user`, `require_student`, `require_institution_admin`) | exists |
| Core-role coverage / safe deactivate-delete | `core/data_safety.py` | exists |
| AI consent gate | `ai/consent.py` (`get_consent_mask`, `is_call_permitted`) | exists |
| Rationale redaction (asymmetric `05` §3) | `ai/rationale_redaction.py` | exists |
| Generation guardrail (no-essay-gen `14`) | `services/guardrail_service.py` | exists |
| Audit trail | `models/audit.py` + `services/audit_service.py` (`36`) | exists |
| Rate limiting | `core/rate_limit.py` (`55` §5) | exists |
| PII field encryption | — | **NEW (build)** |
| Upload safety (AV/type/size) | partial (`core/s3.py`, `media_urls.py`) | extend |
| Trust & safety / moderation | — | **NEW (build)** |
| Secret scanning / supply chain | partial (`# pragma: allowlist secret` convention) | extend |

This is mostly **hardening + filling gaps**, not greenfield.

---

## 2. AuthN / AuthZ (formalize the real modules)

- **AuthN:** `core/security.py verify_token` validates Cognito JWT against JWKS in prod; `_verify_dev_token` accepts `dev:<uuid>:<role>` only when `cognito_bypass=true`. **Build task:** assert at startup that `cognito_bypass` is **false** in `environment=production` (fail boot otherwise) — prevents the dev bypass shipping to prod (`52` §5 launch blocker).
- **AuthZ:** every router depends on `require_student` / `require_institution_admin` (`dependencies.py`); **plus owner-checks** on user-scoped resources (a student can only read their own application). Build task: an audit script asserting every `/students/me/*` and `/institutions/me/*` route has both a role guard and an owner check; no route relies on obscurity.
- **Token handling:** short-lived access + refresh (the `client.ts` refresh queue, `54` §1); tokens never logged (scrub in `core/logging.py`, `55` §2).

---

## 3. PII protection (build the gap)

- **Classification:** tag PII fields per `42`/`46` sensitivity (`pii`, `pii-sensitive`/FERPA, `policy-gated`, `health-pii`). Build `core/pii.py` registry.
- **Encryption at rest:** RDS encryption (KMS) on by default; **column-level encryption** for the most sensitive fields (government-ID partial, financial-proof, disability/health) via an SQLAlchemy `EncryptedType`. Build task: apply to the `42` §3.2 `policy-gated` + `health-pii` fields.
- **In transit:** TLS everywhere (ALB→ECS, ECS→RDS, ECS→Redis); no plaintext internal hops.
- **Masking:** logs + AI context send masked PII (`ai/consent.py` already produces a consent mask; extend to a PII-mask helper so Claude calls get task-scoped, masked context — `63` §12). Build `core/pii.py mask()`.
- **Minimization:** Qwen processes PII-heavy bulk in-VPC (`63` §12) so less PII reaches the API layer.

---

## 4. Consent enforcement (real `ai/consent.py` — make it the hard gate)

- `get_consent_mask(student)` → `{matching, outreach, analytics, training}`; `is_call_permitted(agent, mask)` already gates AI calls. **Build tasks:**
  - Enforce **before every AI/ML processing call** (advisor, rationale, extraction, scoring) — not just discovery; a decorator on agent entrypoints.
  - **`training=false` is an absolute gate** to any Qwen tuning set (`63` §9, `46` §9) — a filter in the training-data pipeline + a test asserting excluded rows never appear.
  - Consent change → invalidate cached AI artifacts for that student (`ai/cache_invalidation.py`).
- **Asymmetric rationale** (`05` §3): `ai/rationale_redaction.py` already strips institution-only signals from the student-facing rationale — add a contract test asserting redacted fields never appear in the student payload.

---

## 5. Input safety (OWASP, extend real modules)

- **Injection:** SQLAlchemy parameterized only (no string SQL); Pydantic v2 validates every body (`50` §3 422). 
- **Upload safety** (`core/s3.py`, `media_urls.py` + `/documents`): enforce content-type allowlist, size cap, extension check, and **AV scan** (build: S3 event → ClamAV/Lambda or a scan service → quarantine on hit) before a document is marked `parse_status=ready` (`51`).
- **Prompt injection** (crawler `60` + advisor RAG): page content is **data, not instructions** — the extraction agent (`63`) + advisor system prompt isolate retrieved text; red-team battery (`61` §6 / `62` §7) tests injection-via-page-content. Build task: a structural test that crawled text can't alter agent system instructions.
- **XSS/CSRF:** React escapes by default; sanitize any markdown render (posts `27`, essays); SameSite cookies / bearer-token model avoids classic CSRF; CORS allowlist (`50` §8).
- **SSRF** (crawler fetches arbitrary URLs `60`): allowlist-only sources + block private IP ranges + no redirects to internal hosts. Build into the crawler fetcher.

---

## 6. Trust & safety / moderation (build the gap)

- **User-generated content** (posts `27`, peer connect `20` §6, messages `17`/`29`, essays): a moderation pass (rules + LLM classifier) flags abuse/harassment/PII-leak; report→queue→action; block minors↔adults peer matching (`20` §6.4).
- **AI safety / crisis** (`61` §3): crisis-signal detection → empathetic response + human/crisis-resource escalation; hard-floor in `62`. 
- **Abuse rate-limits** (`core/rate_limit.py`): connect-request caps, message-spam caps.

---

## 7. Compliance (FERPA / GDPR ops — wire to real audit + data-safety)

- **FERPA:** education records access-logged (`audit_service.py` `36`); directory-info release preference honored (`42` §3.2); institution sees only its own applicants (owner-check §2).
- **GDPR/CCPA:** consent (`46` §2, `ai/consent.py`), data export (Profile Data tab `21`), deletion + 30-day grace via `core/data_safety.py ensure_can_delete_user` (extend to full purge across tables + audit). Build: a `data_export_service` producing the portable bundle (`21`).
- **Retention:** per-class TTL (`46`); audit + financial rows never hard-deleted; PII soft-delete + purge after grace.
- **Audit everything sensitive:** consent change, data export/deletion, AI-generated content, decision release, fairness override, integrity action — all append-only (`36`, `audit_service.py`).

---

## 8. Supply chain / secrets / infra

- **Secrets:** AWS Secrets Manager only; none in the bundle or repo; the `# pragma: allowlist secret` + a secret-scanner (e.g. `detect-secrets`/gitleaks) in pre-commit + CI (CLAUDE.md). Build task: add the scanner to CI.
- **Deps:** Dependabot/`pip-audit` + `npm audit` in CI; pin + lockfiles.
- **Infra (`infra/` Terraform):** RDS in private subnet + SG (CLAUDE.md), least-privilege IAM, no public S3, WAF on CloudFront/ALB (rate + common-rule set).
- **Headers:** HSTS, CSP, X-Content-Type-Options, Referrer-Policy via `core/middleware.py`.

---

## 9. Incident response

- Sev classification + on-call + runbook (ties `55` §1 alerts); breach → contain → assess (audit log scope) → notify per legal timelines → blameless postmortem. Build `infra/runbooks/incident.md`.

---

## 10. Build tasks (checklist)

- [ ] Startup assert: `cognito_bypass=false` in production (fail boot).
- [ ] Route audit: every me-scoped route has role guard + owner check.
- [ ] `core/pii.py` (classification + `mask()`); column encryption on policy-gated/health fields.
- [ ] Consent decorator on **all** AI/ML entrypoints; training-set consent filter + test; redaction contract test.
- [ ] Upload AV scan (S3→scan→quarantine) before `parse_status=ready`; content-type/size allowlist.
- [ ] Crawler SSRF guard (allowlist + private-IP block + no internal redirects); prompt-injection structural test.
- [ ] Moderation pass for UGC + minors↔adults block; crisis escalation (`61` §3) as `62` hard-floor.
- [ ] `data_export_service` + full-purge-after-grace extension of `data_safety.py`.
- [ ] Secret scanner + `pip-audit`/`npm audit` in CI; WAF + security headers in `infra`.
- [ ] `infra/runbooks/incident.md`.

---

## 11. Acceptance

- [ ] Prod refuses to boot with auth bypass on; every me-route role+owner guarded.
- [ ] Policy-gated/health PII encrypted at rest; PII masked in logs + AI context.
- [ ] No AI/ML call runs without a passing consent mask; `training=false` rows never in a tuning set (test).
- [ ] Uploads AV-scanned + type/size-capped; crawler SSRF-guarded; injection red-team passes (`62`).
- [ ] UGC moderated; crisis escalation hard-floored; deletion purges + audits.
- [ ] Secrets only in Secrets Manager; scanner + dep-audit + WAF + headers live.

---

## 12. Open questions

- Column-encryption lib (`sqlalchemy-utils EncryptedType` vs app-layer KMS envelope) — recommend KMS envelope for the few highest-sensitivity fields.
- AV: ClamAV-on-Lambda vs a managed scan API — start ClamAV (cost), revisit.
- Moderation model: rules-only MVP vs LLM classifier — rules + a cheap classifier; full model fast-follow.
