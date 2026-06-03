# 74 · Interoperability, i18n & Compliance-Ops — Wrap-Around-Slate, Multilingual, Audit-Ready

> *"Institutions don't switch off Slate; they extend it. UniPaith must integrate with Slate or accept the cost of asking institutions to replace their core operating system"* (`Competition_Analysis`:2175). The integration bar is concrete: Niche is a *"Slate Platinum Preferred Partner — direct, automated weekly SFTP integration that pushes lead/prospect data into Slate, and pulls weekly enrollment-funnel snapshots back"* (`Competition_Analysis`:1759); Slate's own surface is *"scheduled web services, batched SFTP/XML file transfers, and a documented REST API"* (`Competition_Analysis`:2263). Two other procurement walls stand beside it: international students are the growth segment and the #1 incumbent weakness is being *"U.S.-only"* (`Competition_Analysis`:1789) while Studyportals' Sophia advises *"in 20+ languages … students from 100+ countries"* (`Competition_Analysis`:2095, `Feature_List_V1`:171 Multi-language Support); and there is **no formal FERPA+GDPR+CCPA review, no SOC 2 Type II readiness, no Trust page** — `47` G-C1 calls this *"block for institution sales"* — with the College Board NY-AG consent settlement (*"$750,000 … 237,000+ NY students … a template other state AGs will follow"*, `Competition_Analysis`:631) as the precedent to pre-empt. Today none of this exists: no connector lives anywhere in `src/` (the only webhook is `POST /webhooks/stripe`, `api/router.py:147`); i18n stops at two dormant columns (`student_profiles.preferred_platform_language`, `student.py:50`) with no translation path; and `data_residency` is validated three ways but stamped *"Phase 14 deferred, US only"* (`services/data_governance.py:149,182`).
>
> This spec makes UniPaith **interoperable, multilingual, and procurement-ready** — the last detail spec of the public-release block (`64`). It is deliberately **wrap-around, not rip-replace**: it adds a CRM sync seam over the *real* attribution + recruitment data already built, a translation layer over the *real* discovery/rationale agents, and a compliance-ops register over the *real* security/consent/audit controls already shipped (`58`/`46`/`36`). It builds almost nothing greenfield in the brain — it makes the product **sellable**.
>
> Build anchor: new `services/interop/` (Slate/Salesforce/CommonApp connectors) consuming `attribution_service.export_csv` (`attribution_service.py:980`) + recruitment `import_prospects`/`convert_prospect` (`recruitment_service.py:251,330`); new `services/i18n/` translation gateway over `ai/` agents; extend `services/data_governance.py` (residency routing), `transparency/security.py` (compliance register, `security.py:418` `ComplianceItem`), `core/data_safety.py` (purge completeness). Pairs with `58` (security/PII), `46` (consent/governance/sub-processors), `36` (audit), `28` (export), `40` (recruitment), `62` (translation eval-gate), `73` (the surge/queue infra translation jobs ride). Closes `47` G-C1, G-C2, G-C3.
>
> Status: **draft v1.0** · 2026-06-02 · turns a closed prototype into an interoperable, multilingual, audit-ready product; closes the institution-sales compliance block. Translation is AI → rule-based fallback, never 5xx (`tests/test_plan2_integration.py`); legal/consent text is never machine-translated without human review.

---

## 1. What exists vs what to build

| Capability | Real module today | Status |
|---|---|---|
| Funnel/attribution export (CSV) | `attribution_service.py:980` `export_csv` | exists — **wrap as connector source** |
| Prospect import + convert-to-applicant | `recruitment_service.py:251,330` (`import_prospects`, `convert_prospect`) | exists — **wrap as connector sink** |
| Outbound webhook precedent | `POST /webhooks/stripe` (`api/router.py:147`), `require_system` X-Ops-Token (`api/crawler.py:4`) | exists — **generalize to webhooks** |
| Slate / Salesforce / Common App connectors | none anywhere in `src/` | **NEW (build): bidirectional sync** |
| i18n persistence | `student_profiles.preferred_platform_language` (`student.py:50`), `preferred_writing_language` (:51), `StudentLanguage` (:108) | exists — **dormant; wire** |
| UI string catalog + translated advisor | none | **NEW (build): i18n catalog + translation gateway** |
| Data residency per institution | `data_governance.py:149` (validated `us/canada/eu`, *deferred*) | exists — **make region routing real** |
| Sub-processor / DPA surface | `data_governance.py:101` `SUBPROCESSOR_NOTE`, `46` §10 list | exists — **DPA surface + per-jurisdiction** |
| Compliance-controls register | `transparency/security.py:418` `ComplianceItem`, `CONTROLS` (:78) | exists — **map controls→evidence (SOC 2)** |
| Public Trust page | none (`46` §4 plans it; `47` G-C1 blocks on it) | **NEW (build): `/trust` surface** |
| Audit/export/purge completeness | `audit_service` (`36`), `core/data_safety.py:63` `ensure_can_delete_user` | exists — **finish purge + G-C3 events** |

This is **integration + governance**, not core ML. It depends on nothing in R1/R2 and can run continuously (`64` §4); only `73`'s queue is a hard dependency for the async sync/translation jobs.

## 2. CRM interoperability — wrap around Slate, never replace it

The hard constraint (`Competition_Analysis`:2175): the institution's CRM is its operating system; UniPaith is an **adjacent lead/funnel source**, not a CRM. The mechanism mirrors Niche's Platinum-Preferred posture (`:1759`) — push leads in, pull funnel snapshots back — built on the two real data layers already shipped (`28` attribution, `40` recruitment), so this is a **seam, not a second pipeline**.

- **New `services/interop/` package** + `integration_connectors` table (`institution_id` FK, `kind ∈ {slate, salesforce, common_app, coalition, webhook}`, `direction`, `transport ∈ {sftp, rest, webhook}`, encrypted `credentials_ref` → Secrets Manager not the row (`58` §8), `schedule`, `field_mapping` JSONB, `last_run_at`, `last_status`, provenance). Migration: Alembic expand→contract, single head.
- **Lead/prospect export (push, the Niche bar).** A scheduled job serializes consented prospects + funnel state to **SFTP/XML** (Slate's batch format, `:2263`) — reusing `attribution_service.export_csv`'s aggregation (`attribution_service.py:980`) and the recruitment prospect graph (`40`). `consent.outreach=false` excludes the row (`46` §2, same gate `28`/`25` already apply); export is **de-identified to the institution's own applicants only** — no cross-institution leakage (`46` §3).
- **Funnel-snapshot import (pull).** Weekly enrollment-funnel snapshots from the CRM (the reverse leg of `:1759`) land via SFTP/REST → normalized → `attribution_events` (`28`) so UniPaith's analytics reflect downstream CRM outcomes (and feed `67`'s yield labels). First-party-wins on conflict (`60` precedence rule).
- **Documented REST API + webhooks.** A versioned `/integrations/*` REST surface (Slate's third transport) for institutions that pull rather than receive SFTP, plus **outbound webhooks** on lead/decision/funnel events — generalizing the single `POST /webhooks/stripe` precedent (`api/router.py:147`) into a signed, retried, DLQ'd delivery (reuse `57`'s delivery DLQ + `73` idempotency). Webhook endpoints system-guarded by the `require_system` X-Ops-Token pattern already in `api/crawler.py:4`.
- **Salesforce Education Cloud connector.** Same `integration_connectors` row, `transport=rest`, OAuth credentials in Secrets Manager; maps prospects/funnel to Education Cloud objects. Salesforce localizes + has a Trust Layer (`46` §4) — parity is the procurement expectation.
- **Common App / Coalition application IMPORT (one-profile → our system).** Ingest a submitted Common App / Coalition application as a **read-only source** that auto-populates a UniPaith profile (the `72` third-party-auto-profiling consumer) — *import only*, never a submission channel back (Niche itself is "not an integrated submission channel", `:1759`); the apply-once fan-out that *submits* is `73`'s scope. Usage-scope consent applies (`66` §2 / `46`).

**Invariant:** a connector failure (SFTP down, bad mapping, auth expiry) **never blocks the request path** — it queues, retries, and surfaces `last_status` on the institution dashboard; the sync is best-effort and audited (`36`), never a 5xx.

## 3. Internationalization & the multilingual advisor

International students are the growth segment and the incumbents' blind spot (`:1789`); the bar is Sophia's *"20+ languages … 100+ countries"* (`:2095`). UniPaith already persists language *preference* (`student.py:50,51`, `StudentLanguage` :108) but does nothing with it. Build the two halves — static UI strings and the live AI advisor — with translation as an **eval-gated AI path with a fallback**.

- **Static UI / content i18n.** A string catalog (locale → key → text), `Accept-Language` + `preferred_platform_language` resolution, locale-aware dates/numbers/currency (reuse the normalizers `63` §5 already defines). Frontend `react-i18next`-style catalog; English is the source-of-truth fallback for any missing key (never a blank string).
- **Multilingual AI advisor.** The discovery orchestrator (`61`/`19`) and the match rationale (`45` §6) — both Claude, both human-facing (`63` §3) — gain a **translation gateway** (`services/i18n/`): respond in the student's locale either by prompting the agent natively in-language or by a translate-after-generate pass, behind a net-new **`ai_i18n_v2_enabled`** flag. Per `63`, translation/synthesis is processing (Qwen-eligible) but the *conversation* stays Claude — the gateway translates Claude's output; it does not move the advisor to Qwen.
- **Eval-gated + fallback (the `62` contract).** A translated response ships only if it passes a `62` translation-quality + safety + groundedness check (no meaning drift in a *match rationale*, no crisis-floor regression `61` §3 across languages). On failure or timeout → **serve the English original with a "translation unavailable" note**, never a 5xx (`tests/test_plan2_integration.py`). The crisis/safety floor (`61`) is evaluated **per target language**, not assumed to transfer.
- **Legal & consent text is never machine-translated.** Privacy notice, consent levers (`46` §2), Terms, DPA, sub-processor list — these are human-reviewed translations only (a `locale_status ∈ {human_reviewed, machine_draft, untranslated}` on each legal string); the consent UI refuses to render a `machine_draft` legal string as authoritative. This is the i18n analog of the §1 "never overwrite first-party" rule and directly pre-empts a mistranslated-consent regulatory exposure (`:631`).
- **Multilingual document handling.** Transcript/credential language (`student.py:158` `transcript_language`) routes `72`'s parsing to the right normalizer; foreign-language essays are workshop-fed in-language (feedback-only contract preserved, `14`).

## 4. Compliance-ops & procurement-readiness (closes `47` G-C1)

G-C1 is a **sales block**: no formal FERPA+GDPR+CCPA review, no SOC 2 Type II readiness, no Trust page. The controls largely *exist* (`58`); what's missing is the **register that maps each control to its evidence** and the **public surface** that lets a procurement team self-serve. Build on the live introspection already in `transparency/security.py` (`CONTROLS` :78, `ComplianceItem` :418, `build_security` :491) rather than a static doc.

- **Compliance-controls register.** Extend `transparency/security.py` so each control names its **regime mapping** (FERPA §99.x / GDPR Art. / CCPA §1798.x / SOC 2 TSC) and its **evidence pointer** (the live module enforcing it, the audit query proving it, the test asserting it). SOC 2 Type II readiness = this register + the operational-evidence trail (audit ledger `46` §7, retention jobs `46` §5) demonstrably running over a period — not a one-time attestation. Year-1/2/3 goals already staged (`46` §4); this makes Year-2 SOC 2 *mechanically trackable*.
- **Public Trust page (`/trust`).** A DB-free public surface (the `/goal` / `/build/*` pattern, `transparency/__init__`) — modeled on Slate / Salesforce Trust Layer (`46` §4) — exposing: the controls register (live status), the sub-processor list (`46` §10, `data_governance.py:101`), data-residency options, retention schedule (`46` §5), the fairness auto-halt commitment (`46` §6), and the "we never sell raw student data" stance (`46` §3). Backed by `build_security` (`security.py:491`), so it **cannot drift** from the deployed controls. This is the artifact `47` G-C1 names ("publish a Trust page").
- **DPA / sub-processor surface.** Make the institution-facing sub-processor list (`46` §9 already wires `/i/settings?tab=data`) a procurement deliverable: machine-readable sub-processor list + each one's classification/region (`data_governance.py` `SUBPROCESSOR_NOTE` :101), a downloadable DPA template, and the "no model training on UniPaith data" clause status per LLM provider (`46` §10) — the diligence a CISO asks for before signing the MSA.

## 5. Per-institution data residency (closes `47` G-C2)

`data_governance.py:149` already *stores and validates* `data_residency ∈ {us, canada, eu}` — but it's inert ("Phase 14 deferred, US only", `:182`). G-C2 (`major`, procurement) makes it **real region routing**, the request Slate (US/Canada/EU) and Salesforce already answer (`46` §4, §9 "Data residency election").

- **Region routing.** Resolve an institution's `data_residency` to a regional data plane (RDS + S3 + the Qwen processing fleet `63` §10) so that institution's applicants' PII is stored and processed in-region. PII-heavy processing stays in-VPC on Qwen (`63` §12) — residency makes that VPC the *right region*. Cross-region replication is metadata/non-PII only.
- **Cross-border flow controls.** EU/UK student data to a US plane requires SCCs in the DPA (`46` §13 open item); residency election + the §4 DPA surface together discharge it. The consent levers (`46` §2) and the residency choice are **independent** — a US institution with EU students still honors per-student GDPR rights regardless of plane.
- **Scope honesty.** Full multi-region infra is `46` §4 "Year 3" / 30+-day Terraform work (`47` G-C2). `74` lands the **routing seam + the election surface + the documented commitment** (the procurement-blocker), with the regional plane stood up per-deal; it does not pretend a turnkey three-region deployment exists on day one.

## 6. Audit / export / purge completeness (closes `47` G-C3) + per-jurisdiction consent

The audit log already covers most events (`36`) but `47` G-C3 names gaps; and the College Board precedent (`:631`) makes **per-jurisdiction consent governance** the thing to pre-empt, not just react to.

- **G-C3 event coverage.** Extend `audit_service` (`36`) to log the named-missing events — *AI-generated artifact accepted/edited/rejected, consent change, data export, account-deletion request* — plus the new `74` events: connector sync run, residency change, translation-override. Append-only, actor-attributed (`36`).
- **Export + purge completeness.** The portable export (`46` §8) and the 30-day-grace full purge (`core/data_safety.py:63` `ensure_can_delete_user`, `58` §7) must now also reach the `74`-introduced surfaces — connector mirrors (a purged student is purged from queued exports), translation caches, and any regional plane (§5). A purge that misses a region is a breach; the purge test asserts cross-region completeness.
- **Per-jurisdiction consent governance.** The College Board settlement (`:631`) was a *consent/sale* failure under NY Education Law §2-d (`46` §4); pre-empt it by resolving the **applicable jurisdiction(s)** for each student (residence + institution region) and applying the **strictest** consent/retention defaults (FERPA / GDPR / CCPA / §2-d / DPDP / COPPA, the `46` §4 matrix) — never the loosest. The "we never sell raw student data" stance (`46` §3) is already absolute; this makes the *consent and retention posture* jurisdiction-correct by construction, and every jurisdiction resolution is auditable.

## 7. How it fits the rest

- **`28`/`40`** are the data the §2 connectors serialize; `74` adds the sync seam, not a new funnel.
- **`46`** owns consent/governance/sub-processors/residency-storage; `74` *operationalizes* them (routing, DPA surface, jurisdiction resolution, Trust page).
- **`58`** owns the controls; `74` adds the regime-mapped register + evidence pointers (SOC 2) and the public Trust surface over `transparency/security.py`.
- **`36`** owns the ledger; `74` adds the G-C3 + connector/residency/translation events.
- **`62`** gates the translation path exactly as it gates every other AI surface; **`73`** provides the queue/idempotency the async sync + translation jobs ride.
- **`64` §6 release gate** — "It interoperates and complies": `74` is the spec that satisfies it.

## 8. Build tasks (checklist)

- [ ] `integration_connectors` table + `services/interop/` (Slate SFTP/XML + REST, Salesforce REST, webhook); credentials in Secrets Manager, never in-row (`58` §8). Migration: expand→contract, single head.
- [ ] Lead/prospect export (push) over `attribution_service.export_csv` + recruitment graph; `consent.outreach` gate; own-applicants-only de-identification.
- [ ] Funnel-snapshot import (pull) → `attribution_events`; first-party-wins; feeds `67` yield labels.
- [ ] Documented `/integrations/*` REST + signed/retried/DLQ'd outbound webhooks (generalize `POST /webhooks/stripe`); `require_system` guard.
- [ ] Common App / Coalition application IMPORT → auto-profile (`72`); import-only, usage-scope consent; no submission-back.
- [ ] i18n string catalog + `Accept-Language`/`preferred_platform_language` resolution + locale-aware formats; English fallback for missing keys.
- [ ] `services/i18n/` translation gateway over the discovery orchestrator + rationale (Claude); `ai_i18n_v2_enabled` flag; `62` translation/safety/groundedness gate; English-original fallback on fail.
- [ ] Legal/consent strings: `locale_status` (human_reviewed/machine_draft/untranslated); consent UI refuses `machine_draft` as authoritative; crisis floor evaluated per language.
- [ ] Compliance-controls register in `transparency/security.py`: regime mapping (FERPA/GDPR/CCPA/SOC 2 TSC) + evidence pointer per control.
- [ ] Public `/trust` surface (DB-free, over `build_security`) — controls, sub-processors, residency, retention, fairness, no-sale stance.
- [ ] DPA / sub-processor procurement surface (machine-readable list + DPA template + per-provider no-training clause status).
- [ ] Data-residency region routing (RDS/S3/Qwen in-region) + election surface; SCC linkage for cross-border; scope-honest (seam now, regional plane per-deal).
- [ ] Audit G-C3 events + connector/residency/translation events; export+purge completeness across connectors/caches/regions (cross-region purge test).
- [ ] Per-jurisdiction consent/retention resolution (strictest-wins) + audit.
- [ ] Fallbacks: connector fail → queue/retry/surface, never 5xx; translation fail → English original; both tested (`tests/test_plan2_integration.py`).

## 9. Acceptance

- [ ] A prospect export lands in a Slate-shaped SFTP/XML fixture and a funnel snapshot imports back into `attribution_events`, end-to-end against fixtures — proving wrap-around sync (`64` §6 "Slate/Common App import-export proven against fixtures").
- [ ] A connector failure (bad mapping / auth expiry / SFTP down) surfaces `last_status` and queues a retry; it never returns a 5xx and never blocks a user request (tested).
- [ ] A Common App application imports into a populated UniPaith profile; no submission path back exists (import-only asserted).
- [ ] The advisor and a match rationale render in a non-English locale behind `ai_i18n_v2_enabled`; disabling it returns English; a translation failure falls back to the English original (tested).
- [ ] A legal/consent string with `locale_status=machine_draft` is **not** rendered as authoritative consent text (tested); the crisis floor passes in each enabled language (`62`).
- [ ] `/trust` renders the live controls register, sub-processor list, residency options, retention, and fairness commitment — and changes when the deployed controls change (drift-proof via `build_security`).
- [ ] The controls register maps every control to a regime + evidence pointer; the SOC 2 readiness view enumerates the operational evidence trail (`46` §7 ledger + §5 retention running).
- [ ] An institution set to `data_residency=eu` routes its applicants' PII storage/processing in-region; a deletion purges across every region (cross-region purge test) — closing G-C2.
- [ ] G-C3 events (AI-artifact accept/edit/reject, consent change, export, deletion request) + connector/residency/translation events are append-only audited.
- [ ] Per-jurisdiction resolution applies the strictest consent/retention defaults (test over a GDPR-vs-CCPA-vs-§2-d matrix), pre-empting the `:631` consent-settlement failure mode.

## 10. Open questions

- **Slate transport for v1** — SFTP/XML (the Niche Platinum bar, `:1759`) vs Slate's REST first. *Recommend SFTP/XML first (it's the documented Platinum-Preferred path institutions already run); REST as the pull-mode fast-follow.*
- **Translate-after-generate vs native-in-language** — prompt Claude in-language vs translate its English output. *Recommend native-in-language for the advisor (preserves voice/safety), translate-after for static synthesized facts; both `62`-gated.*
- **Residency depth for v1 public release** — routing seam + per-deal regional plane vs full turnkey three-region infra (`46` §4 Year 3, `47` G-C2 30+ days). *Recommend seam + election + commitment now (unblocks procurement), regional plane stood up per signed EU/Canada deal; do not over-build ahead of demand.*
- **R3/R4 GTM sequencing** — `74` full CRM interop may be fast-follow if launch is student-discovery-first (`64` §7). *Recommend ship the export/Trust/compliance half for the first institution sale; Salesforce + Common App import as the second-deal fast-follow, gated by GTM.*
- **Machine-readable compliance format** — bespoke `/trust` JSON vs an OpenChain / vendor-assessment standard (CAIQ/SIG) export. *Recommend bespoke now, add a CAIQ-lite export when a procurement team first asks.*

Sources: internal — `64` §3/§6 (release block + gate), `46` §2/§3/§4/§5/§6/§9/§10/§13 (consent/no-sale/regimes/retention/fairness/governance/sub-processors/SCC), `58` §3/§7/§8 (PII/purge/secrets), `36` (audit), `28` (attribution export), `40` (recruitment), `60` (first-party-wins, X-Ops-Token), `57` (delivery DLQ), `62` (translation eval-gate), `63` §3/§5/§10/§12 (Claude-faces-humans, normalizers, serving, in-VPC PII), `72` (auto-profiling from imported apps), `73` (queue/idempotency); code — `services/data_governance.py:149,182,101`, `services/attribution_service.py:980`, `services/recruitment_service.py:251,330,658`, `transparency/security.py:78,418,491`, `models/student.py:50,51,108,158`, `models/institution.py:99`, `core/data_safety.py:63`, `api/router.py:147`, `api/crawler.py:4`. Benchmarks — `Competition_Analysis.docx`:631 (NY-AG settlement), 1759 (Niche Slate Platinum SFTP), 1789 (US-only weakness), 2095 (Sophia 20+ languages), 2175 (Slate switching cost), 2263 (Slate integration transports). Papers — `Feature_List_V1`:171 (Multi-language Support).
