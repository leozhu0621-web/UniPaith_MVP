# 60 · Data Crawler & Knowledge-Base Engine

> **Model note (per `63`):** the extraction, normalization, entity-resolution, embedding, and display-synthesis steps run on **Qwen** (the self-hosted ML backend — no human interaction). The student-facing **chatbot** that *answers questions about* this knowledge is **Claude**, doing RAG over Qwen's embedded graph. Qwen builds + presents the knowledge; Claude converses about it.

> The backend system that actively gathers **all the public information the Prompt Library implies** and enriches the UniPaith database — so the platform reasons against a rich, current, source-cited picture of the *world* (schools, programs, scholarships, careers, tests, visas, costs, majors, rankings, outcomes…), not just sparse institution-entered data. The *what* and *how to present* come from the **Prompt Map** (`06` §3) and **Prompt Library** I/O schema (`42`/`43`).
>
> Status: **draft v2.2** · 2026-05-30 · v2 broadened scope to the full Prompt-Library reference graph; v2.1 added the Kollegio benchmark (§1A); v2.2 added proactive news/change-monitoring + autonomous discovery (§3B). Built on an existing-but-dormant knowledge skeleton (§2). Pairs with `42`/`43`, `06`, `45`, `46`, `55`, `51`, `63`.

---

## 1. Purpose & scope — the world-side knowledge graph

The Prompt Library has two halves — student INPUT (`42` §3) and platform-derived OUTPUT (`42` §4). Neither is the *world*. To interpret a student and produce OUTPUT features, the engine needs **public reference knowledge** — careers, tests, visas, costs, majors, institutions, programs, scholarships, rankings, outcomes. The crawler gathers a reference dataset for **every domain the Prompt Library touches**, so a career goal reads against real salary/outlook data, a test score against real program ranges, a visa need against real requirements, a budget against real cost-of-living, a major against real curriculum.

**Hard rule — public, non-personal data only.** No crawling of students or any private individual; the student INPUT half is self-provided, governed by `46`. The skeleton's `person_insights`/`advisor_personas` tables stay dormant for this engine. Public institutional/reference sources only (BLS, O*NET, IPEDS, College Scorecard, immigration agencies, `.edu`, published rankings, public scholarship DBs). Allowlisted sources only (§11). **No platform-admin tier** (`05` §2): governance is institution "claim & verify" (`23`) + an internal ops queue.

## 1A. Competitive benchmark — improving on Kollegio

**Kollegio** ([kollegio.ai](https://www.kollegio.ai/)) is the closest analog: a free AI college counselor (100k+ users) combining public college data + catalogs + outcomes + scholarships across **~1,650 U.S. institutions**, LLMs fine-tuned on ~300 counseling docs. Where to beat it:

| Kollegio (observed) | Gap | UniPaith improvement |
|---|---|---|
| Matches on data points; no published provenance | opaque numbers | **provenance on every fact** (§4/§7) |
| Static ~1,650-school snapshot | drifts stale | **scheduled re-crawl + change detection + decay** (§10) |
| US undergrad only | no international/grad/career/cost | **full reference graph** (§3) |
| Student-only, scraped not authoritative | schools can't correct | **two-sided claim & verify** (`23`/§9); first-party wins (§8) |
| Shallow reference numbers | net price/visa/salary thin | **world-reference tables** (§5.2) feed computed OUTPUT features |
| Static fine-tuned advice | no live ground truth | **live ground-truth graph** the engine reasons against |

## 2. Build on what already exists (verified in code)

`models/knowledge.py` (254 lines, migrated by `c3a7f9e1d502`) is dormant — no services/API wired. Reuse it: `data_sources` (registry+policy), `crawl_frontier` (url/domain/priority/depth/status/next_crawl_after/consecutive_failures/domain_crawl_delay_seconds/respect_robots — robots+delay+backoff+dedup already modeled), `knowledge_documents` (raw+extracted+facts+embedding(1536)+quality/credibility/relevance scores+processing_status), `knowledge_links` (generic `entity_type`+`entity_id`+`entity_name`+confidence → links a doc to ANY domain), `engine_directives`, `engine_loop_snapshot` (tick metrics), `interaction_signals`. The skeleton is domain-agnostic by design. `knowledge_entities` is referenced but has **no migration** — add it (§16). Work = wire services + jobs + extraction (`45`/`63`) + the §5 tables + the enrichment write-path.

## 3. What to gather — full Prompt-Library coverage

- **3.0 Institutions/Programs/Scholarships** (Prompt Map "School/Program") → `institutions`/`schools`/`programs`/`historical_outcomes`/`events` + new `scholarships` (§5.1).
- **3.1 Careers/occupations** (BLS, O*NET) → `ref_occupations`; feeds career-alignment + outcome preview.
- **3.2 Standardized tests** (ETS/College Board/ACT/British Council + program policies) → `ref_tests`; feeds test compatibility/superscore.
- **3.3 Visa & immigration** (USCIS/IRCC/UKVI + intl offices) → `ref_visas`; feeds visa feasibility band (`42` §4.3), serves `38`.
- **3.4 Cost of living & geography** → `ref_geo_cost`; feeds net-cost/affordability.
- **3.5 Majors/curriculum** (CIP, catalogs) → `ref_majors`; feeds major-track fit + prereq gaps.
- **3.6 Rankings/accreditation/employer outcomes** → `ref_rankings`/`ref_accreditation` + `historical_outcomes`/`employer_feedback`.
- **3.7 Supporting**: grading-scale normalization, language equivalency, competitions, events/deadlines.

> NOT gathered (self-provided per `46`): identity, the student's own academics/tests/work/essays, telemetry. Crawler builds the *world*; the student builds *their record*; matching joins them.

## 3B. Proactive monitoring — news, changes & autonomous discovery

`knowledge.py` calls this the **"perpetual knowledge engine."** Proactive is the default mode.

**Three behaviors:** (1) news & change monitoring (watch sources for *new/changed* facts), (2) autonomous discovery (engine expands its own coverage), (3) signal-triggered crawling (student behavior + deadlines raise priority).

**Monitored** (time-sensitive): policy news (visa rules, test-optional shifts, FAFSA, accreditation), institution news (programs added/closed, **deadline changes**, tuition, rankings, new scholarships), scholarship news, labor-market updates. Each tied to its entity via `knowledge_links`.

**Change-detection → `change_event` pipeline:** re-crawl → `content_hash` differs → `45` semantic diff (old vs new) → classify `change_type` (deadline_moved | new_scholarship | policy_change | program_added | program_closed | cost_change | ranking_update | stat_update | new_event) + **materiality** + confidence → write `change_event` → relevance-route. A materiality classifier ("does this matter, and to whom?") gates routing.

**Autonomous discovery:** frontier self-expansion via `knowledge_links`; search-driven discovery for under-covered entities (bounded by allowlist/trust); a gap-filling loop where each `engine_loop_snapshot` tick self-issues `engine_directives` for sparse/stale entities; **watchlists** on entities students save/apply/follow (`interaction_signals`/`student_follows`) get elevated freshness; emergence detection adds newly-announced entities (review-gated).

**Routing changes to the people who care** (the proactive payoff): a `change_event` → relevance match (whose saved/applied/followed set it touches) → **Connect feed** (`20`, the `program_change` item), **notifications** (`57`, urgent on applied/saved), **saved-search alerts** (`56`). Gated by materiality + consent (`46`) + per-user caps; deduped/batched.

**Volatility-tiered freshness:** news/policy = hourly–daily; in-cycle deadlines = daily; watchlisted = elevated; standard reference = monthly–quarterly; slow reference (occupations) = annually.

**New table `change_events`:** target_type/id, change_type, field_path, old/new value, materiality, source_document_id → `knowledge_documents`, confidence, detected_at, status(pending|routed|dismissed), routed_at. Raw news rides `knowledge_documents` (`content_format='news'`, `published_at`).

**News guardrails:** stricter source trust (prefer primary/official); material claims require corroboration before high-materiality routing; never present unverified news as fact ("reported by <source>, <date>" + confidence); **institutional/policy news only — no personal news**; robots/rate apply; **no fabricated urgency** — a change_event must trace to a real diff in a real source.

## 4. How to present it (provisional, sourced, explainable)

Provenance on every crawled fact (`source=crawled` + URL + `fetched_at` + confidence; "Sourced from <domain> · updated N days ago"). Provisional until confidence-gated/institution-confirmed; **verified first-party data always wins** (§8). Never fabricate — not-found stays empty; low-confidence → review (§9). Flows into the **same editorial components** (`11`/`12`/etc.), no separate "crawled" UI, no decorative treatment (`01`). Reference facts shown as "typical for this field," distinct from a program's own claim.

## 5. New tables

- **5.1 `scholarships`** — institution/program-linked or external; type, amount, eligibility JSONB, deadline, application, distribution history, provenance, `status: provisional|live|archived`. Feeds `aid_scholarship_likelihood_band` + net-price (`09`/`11`).
- **5.2 Reference tables** (typed for hot domains, generic for the tail; all carry provenance): `ref_occupations`, `ref_tests`, `ref_visas`, `ref_geo_cost`, `ref_majors`, `ref_rankings`, `ref_accreditation`, `reference_entities` (generic long-tail), `entity_enrichments` (provenance/audit: target_type/id, field_path, proposed_value, source_document_id, source_url, confidence, status). `knowledge_documents`/`knowledge_links` stay the raw graph; reference tables are the clean projection.

## 6. Pipeline (Qwen, on the `55` queue)

`(0)` source registry → `(1)` discover (frontier) → `(2)` fetch (robots + delay + conditional GET; unchanged → skip) → `(3)` extract (Qwen `63`, schema-strict, grounded, eval-gated `62`) → `(4)` normalize (units/SOC/CIP/CEFR/currency/grading) → `(5)` resolve (link facts → entities) → `(6)` enrich-write (confidence-gated; low/conflict → review). Two speeds: Tier-1/2 official API/bulk (College Scorecard/IPEDS/BLS/O*NET) land structured → skip extract; Tier-3/4 crawl runs full extraction. Idempotent (url+content hash); observable (queue depth, fetch/parse success, fields-enriched, LLM cost via `ai_turns`).

## 7. Provenance & write-path

`entity_enrichments` audits every crawled field (→ source doc, reversible). Applying writes the field + `source=crawled`/confidence on the target, keeps the audit row. Cross-source corroboration raises confidence (≥2 trusted sources may auto-apply; single low-trust → review).

## 8. Conflict & authority

Precedence: institution-verified > cross-source corroborated crawl > single high-trust > single low-trust (review only). Crawler never overwrites verified data — conflict → review ("institution says X, source says Y"). Freshness tiebreak within tier. Prior values kept (`status=superseded`).

## 9. Review & governance (no platform-admin)

Institution "claim & verify" (`23` extension) for their own data; internal ops queue + LLM judge (`45`) for low-confidence/conflicting reference data; student "report incorrect" → re-crawl directive.

## 10. Freshness & scheduling

Per-source cadence in `data_sources.crawl_config` (volatility-tiered, §3B); priority from `interaction_signals`; conditional fetch; decay/TTL re-queues stale; scheduled via `55` scheduler.

## 11. Legal, ethical & safety

robots/ToS respected; **allowlist-only** sources; rate-limited + identified UA; **public non-personal data only**; attribution + reversibility; trust scoring keeps low-quality sources out of the live record; all actions audited (`36`/`55`). Ties `58`.

## 12. Service & API

`services/crawler/` (source_registry, frontier, fetcher, extractor, normalizer, entity_resolver, enrichment_writer, scheduler); internal ops API (system-guarded); institution enrichment-review API (`23`); reference data surfaces through existing student endpoints (`50`) with provenance fields.

## 13. Extraction agent (Qwen, `63`)

`SourceExtractionAgent` variants per domain: input = cleaned page + target schema; output = structured fields + per-field confidence + source spans. Forced structured output, schema-validated, **never invents**, cost-tracked (`ai_turns`), cached by content hash, rule-based fallback per source template.

### 13B. Extraction eval (→ `62`)
Extraction quality runs through the shared eval harness (`62`) via the extraction adapter: per-field precision/recall/F1, no-fabrication, schema-validity, normalization-correctness; golden set grows from corrections; CI-gated.

## 14. Phasing

A: institutional core (schools/programs/scholarships, few high-trust sources, review-all; add `scholarships`/`entity_enrichments`/`knowledge_entities`). B: student-facing reference (careers/tests/visa/cost/majors). C: rankings/accreditation/employer outcomes + long tail; confidence-gated auto-apply; news/proactive (§3B). After MVP core (`48`).

## 15. Acceptance

- [ ] Only registered/allowlisted, domain-tagged sources fetched; robots/rate honored (logged).
- [ ] Each domain: source set + extraction schema + normalized table + provenance.
- [ ] Crawled facts appear provisional + source-cited + confidence in the consuming surface.
- [ ] Reference data feeds the right OUTPUT features (net-price ← cost+aid; visa band ← visa ref; etc.).
- [ ] First-party never overwritten by crawl (conflict → review).
- [ ] Unchanged content → no parse/write (idempotent).
- [ ] `change_event`s detected, materiality-classified, routed to affected students.
- [ ] **No personal/individual data gathered** (contract test); all actions audited.
- [ ] Extraction never writes a field absent from source (no fabrication), every domain.

## 16. Open questions

`knowledge_entities` migration (add). Reference-source licensing (open/gov first; license rest). Typed vs generic table list. Reference TTL per domain. People-data line (`advisor_personas`/`person_insights` stay dormant). Auto-apply threshold (review-all → loosen on measured precision). Confirm nothing from the pre-pivot admin-crawler is silently re-enabled.

Sources: Prompt Map (`06` §3), Prompt Library (`42`/`43`), `models/knowledge.py`. Competitive: [Kollegio](https://www.kollegio.ai/) · [review](https://www.automateed.com/kollegio-ai-review) · [SiliconANGLE](https://siliconangle.com/2025/04/23/startup-kollegio-raises-2-8m-ai-powered-college-counseling-service/).
