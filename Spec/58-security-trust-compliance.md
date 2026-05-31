# 58 · Security, Trust & Compliance

> The controls a real platform handling student PII and admissions decisions must have before launch — not aspirational, table-stakes. Application security (OWASP), data protection (PII/encryption), trust & safety (moderation for peer features), and operational compliance (FERPA/GDPR enforcement, incident response, supply chain). `46` owns the data-rights *policy* + consent model; this owns the *security engineering + enforcement* that makes it real.
>
> Status: **draft v1.0** · 2026-05-30 · Production-parity track. A launch-blocker source for `52` §5. Pairs with `46` (data rights), `50` (auth contract), `55` (rate limiting/infra), `05` (roles).

---

## 1. Why this is non-negotiable

UniPaith holds: government-ID fragments, financial data, transcripts, immigration status, disability/accommodation data, and drives admissions decisions. A breach or a biased/leaky decision is existential. LinkedIn/Handshake-grade means **security is built in, audited, and enforced** — not a checklist done once.

---

## 2. Application security — OWASP Top-10 controls

| Risk | Control in UniPaith |
|---|---|
| **Broken access control** | Every endpoint role-guarded (`50` §2) **+ owner check** (a student can only read their own data; an institution only its applicants). Default-deny. Test with cross-tenant access attempts (§9). |
| **Cryptographic failures** | TLS everywhere (HTTPS only, HSTS); secrets in AWS Secrets Manager (`CLAUDE.md`); PII encrypted at rest (§4). |
| **Injection** | SQLAlchemy parameterized queries (no string SQL); validate/escape any raw query; Pydantic validation on all input. |
| **Insecure design** | Threat-model the sensitive flows (decisions, payments `39`, immigration `38`); consent gates (`46`). |
| **Security misconfig** | `DEBUG=false` in prod (no `/docs` exposed publicly unless intended); least-privilege IAM; locked CORS (`50` §8); security headers (CSP, X-Frame-Options, etc.). |
| **Vulnerable components** | Dependency scanning (§8). |
| **Auth failures** | Cognito (`50` §2); rate-limit + lockout on auth (`55` §4); short-lived tokens + refresh; secure token storage. |
| **Data integrity failures** | Signed/verified uploads; integrity signals (`51` `integrity_signals`); audit log (`36`). |
| **Logging/monitoring failures** | Structured logs + error tracking (`55` §1) without logging secrets/PII (§4). |
| **SSRF** | Validate/allowlist any server-side fetch (link validation `42` §3.17, document URLs). |

---

## 3. AuthN / AuthZ hardening

- **Cognito** as IdP (`50` §2); enforce email verification; offer MFA (`21` §2.2).
- **Token discipline**: short-lived access + refresh; rotate; revoke on logout/"sign out everywhere" (`21`). Validate signature + expiry + audience server-side on every request.
- **RBAC + ownership**: role guard is necessary but not sufficient — every user-scoped query filters by the caller's id. Centralize the ownership check (a dependency) so it can't be forgotten per-endpoint.
- **No platform-admin tier** (`05` §2) — fewer privileged paths to abuse.
- **Brute-force**: progressive backoff + temporary lockout on repeated auth failures (`55` §4).
- **Session**: secure, httpOnly where cookies are used; CSRF protection on any cookie-auth path.

---

## 4. PII & data protection

- **Classification** (per `42` sensitivity tags): `public` / `pii` / `pii-sensitive` (FERPA) / `policy-gated` (criminal, immigration) / `health-pii`. Controls scale with class.
- **Encryption at rest**: RDS + S3 encryption (KMS); encrypt the most-sensitive columns (gov-ID fragments, financial-proof, disability details) at the app layer too (envelope encryption) so a DB dump alone doesn't expose them.
- **Encryption in transit**: TLS 1.2+ everywhere, internal service calls included.
- **Minimization**: collect only what's needed (`42` conditional/policy-gated fields gated by an actual need); don't request gov-ID unless a program requires it.
- **Masking**: logs/analytics/AI prompts carry masked or omitted PII (`55` §1) — never send raw sensitive PII to an AI provider beyond what the agent needs, and record `consent_mask` (`51` `ai_turns`).
- **Retention + deletion**: enforce the `46` retention rules — soft-delete + 30-day grace + hard purge job (`55` §3); honor data-deletion requests (`42` `data_deletion_request_status`).
- **Access logging**: who viewed which student's data (the `21` §2.5 access log) — backed by audit (`36`).

---

## 5. File-upload safety (transcripts, documents, portfolios)

A major attack surface (`44`/`15` uploads):
- Validate type + size server-side (not just client); allowlist extensions/MIME.
- Store in S3 (private, presigned URLs with short expiry, `50`); never serve user files from the app origin (avoids stored-XSS via HTML/SVG).
- **Malware scan** uploads (ClamAV/lambda) before they're processed/served.
- Strip/transcode where feasible; render previews from sanitized derivatives.
- OCR/parse pipeline (`44` §5.3) runs sandboxed; treat extracted text as untrusted.

---

## 6. Trust & safety (the peer/social surfaces)

New risk introduced by Connect Peers (`20` §6) and messaging (`17`/`29`):
- **Content moderation**: peer profiles + messages screened (automated + reportable) for harassment, PII-fishing, spam. An AI classifier flags; humans review the queue.
- **Reporting & blocking**: every peer card + message has report/block (`20` §6.4); reports route to a moderation queue with action tracking.
- **Rate limits** on connect requests + messages (anti-spam, `55` §4).
- **Minor safety**: no minor↔adult peer matching (`20` §6.4, gate on `adult_minor_status`); extra restraint on minors' data + discoverability.
- **Abuse monitoring**: anomalous behavior (mass-messaging, scraping patterns) flagged via `integrity_signals` (`51`).

---

## 7. Compliance operations (make `46` enforceable)

- **FERPA**: education records access-controlled + logged; directory-info release preference honored (`42` §3.2); DPAs with institutions (`07` §4.3). Reviewer access scoped to assigned applicants.
- **GDPR/CCPA**: consent (`46` §2) as the gate; right-to-access (export, `21`/`46`), right-to-deletion (§4), data-processing records. Lawful-basis tracking per `consent_version_id`.
- **Bias/fairness as compliance** (`46` §6): the disparate-impact monitor + auto-halt isn't just ethics — it's regulatory exposure for automated decisions. Decisions never fully automated (human-in-the-loop, `37`).
- **Data residency**: know where PII lives (RDS region); international students may trigger residency requirements — flag for legal (`07` §10 US-first vs global).
- **Vendor/sub-processor list**: AWS, Anthropic/OpenAI, SES, payment (`39`) — disclosed; DPAs in place; the `consent.training` tier controls what reaches model-training (`46` §9).

---

## 8. Supply chain & secrets

- **Dependency scanning** (Dependabot/Snyk) on Python + npm; fail CI on high-severity CVEs; patch cadence.
- **Secret scanning** (pre-commit + CI, e.g. gitleaks) — no keys in the repo or bundle (`52` §5).
- **SBOM** + pinned dependencies; review transitive additions.
- **IaC security**: Terraform (`CLAUDE.md`) reviewed; least-privilege IAM; the OIDC `AdministratorAccess` role is scoped to this repo's PRs/main only (already noted in `CLAUDE.md`) — keep it tight.
- **CI/CD**: protected main; required reviews; no secrets in logs.

---

## 9. Security testing & verification

- **Authorization tests**: automated cross-tenant/cross-role access attempts must 403 (the highest-value security test for a multi-tenant app) — add to the suite.
- **Input fuzzing** on critical endpoints; Pydantic + schema validation as the first wall.
- **SAST/DAST** in CI; periodic **pen test** before launch + annually.
- **Secret + dependency scan** gates (§8).
- AI-specific: prompt-injection resistance on agents that consume user content (`45`) — the guardrails (`46`/`45`) are security controls too.

---

## 10. Incident response

- **Runbook** per severity (the `engineering:incident-response` discipline): detect → triage → contain → communicate → remediate → blameless postmortem.
- **Breach plan**: notification obligations (FERPA/GDPR/state law) timelines; who/how to notify institutions + students.
- **Alerting** wired (`55` §9) so incidents are detected, not reported by users.
- **Backups + restore drills**: RDS automated backups + tested restore (don't discover backups are broken during an incident).
- Audit log (`36`) is the forensic record — append-only, tamper-evident.

---

## 11. Launch-blocker security gates (feed `52` §5)

- [ ] Every endpoint: role guard **+ ownership filter**; cross-tenant access tests pass.
- [ ] `DEBUG=false` in prod; security headers + locked CORS; HTTPS/HSTS.
- [ ] PII encrypted at rest (KMS + app-layer for most-sensitive); TLS in transit; logs/AI prompts PII-masked.
- [ ] Upload validation + malware scan + private S3 + presigned URLs.
- [ ] Auth: MFA available, rate-limit/lockout, token rotation/revocation.
- [ ] Consent gate enforced on all AI/processing (`46`); deletion + export operational.
- [ ] Trust & safety: report/block + moderation queue live before Peers (`20`) launches; minor safeguards.
- [ ] Dependency + secret scanning green; no secrets in bundle.
- [ ] Fairness monitor + human-in-loop on decisions active (`46` §6).
- [ ] Incident runbook + breach plan + tested backups.

---

## 12. Open questions

- **App-layer field encryption scope** — exactly which columns (gov-ID, financial-proof, disability, immigration) get envelope encryption vs RDS-at-rest only. Recommend the four named.
- **Moderation build vs buy** — automated content moderation in-house vs a service (e.g., for peer messaging). Buy likely faster to launch Peers safely.
- **Pen-test timing/vendor** — schedule before public launch.
- **Data residency** — resolve once US-first-vs-global (`07` §10) is decided; international PII may need regional storage.
- **AI provider data handling** — confirm zero-retention / no-training agreements with Anthropic/OpenAI for the data UniPaith sends (ties `46` §9 training tiers).

Sources: OWASP Top-10 (industry standard) · [SaaS backend security/readiness](https://www.aalpha.net/blog/saas-backend-development/) · [scalable SaaS guide](https://dev.to/thebitforge/building-scalable-saas-products-a-developers-guide-48a7).
