# 59 · Data Crawler & Knowledge-Base Engine

> The backend system that actively gathers **all the public information the Prompt Library implies** and enriches the UniPaith database — so the platform reasons against a rich, current, source-cited picture of the *world* (schools, programs, scholarships, careers, tests, visas, costs, majors, rankings, outcomes…), not just the sparse data institutions enter and the data students provide. The *what to gather* and *how to present it* come straight from the materials: the **Prompt Map** (`06` §3) and the **Prompt Library** input/output schema (`42`/`43`).
>
> Status: **draft v3.0** · 2026-05-30 · Production track. v2 broadens scope from school/program/scholarship to the **full Prompt-Library reference graph** (per the founder's update); v2.1 adds the **Kollegio competitive benchmark** (§1A); v2.2 adds proactive news/change-monitoring + autonomous discovery (§3B); **v3.0 adds production engineering — official-data-first source strategy (§2A) + crawler engineering, extraction evaluation/cost-control, observability/SLOs, and the worker-fleet stack (§13A–§13D).** Built on an **existing-but-dormant** knowledge skeleton already in the schema (§2). Pairs with `42`/`43` (the field taxonomy this mirrors), `06` (3-layer engine + info flow), `45` (extraction agents), `46` (data rights), `55` (queue/jobs/observability), `51` (data model).

---

## 1. Purpose & scope — the world-side knowledge graph

**The core idea (the symmetry):** the Prompt Library has two halves — what the *student* provides (INPUT, `42` §3) and what the platform *derives* (OUTPUT, `42` §4). Neither is the *world*. To interpret a student's data and produce the OUTPUT features, the engine needs a third thing: **public reference knowledge about the world** — careers, tests, visas, costs of living, majors, institutions, programs, scholarships, rankings, outcomes.

> The crawler's job is to gather a **reference dataset for every domain the Prompt Library touches**, so that:
> - a student's *career goal* (`42` §3.12) can be matched against real occupation salary/demand/outlook data;
> - a *test score* (`42` §3.6) can be read against real program score ranges + policies;
> - a *visa need* (`42` §3.3) can be read against real visa requirements + processing times;
> - a *budget/location constraint* (`42` §3.13) can be read against real cost-of-living data;
> - a *major* (`42` §3.18 / `43`) can be read against real curriculum/prerequisite/career-path data;
> - and the OUTPUT features (`42` §4: net price, outcome preview, visa feasibility band, readiness) have real-world numbers to compute from.

So v2 expands the engine from 3 entity types to the **full reference catalog (§3)** — every public domain in the materials — while keeping one bright line:

**Hard rule — public, non-personal data only.**
- **No crawling of students or any private individual.** The student INPUT half (`42` §3.1, academics, etc.) is *self-provided*, governed by `46` — never crawled. The skeleton's `person_insights`/`advisor_personas` tables stay dormant for this engine (they're conversation-derived, not crawl-fed).
- **Public institutional/reference data only**: government data (BLS, O*NET, IPEDS, immigration agencies), institution `.edu` pages, published rankings, public scholarship databases, public test-provider info. Allowlisted sources only (§11).
- **No platform-admin tier** (`05` §2): governance is institution "claim & verify" (`23`) + an internal ops queue, not a customer admin console. (A prior admin-crawler was removed in the 2026-05-22 pivot; this is the clean, scoped replacement.)

---

## 1A. Competitive benchmark — improving on Kollegio's data method

**Kollegio** ([kollegio.ai](https://www.kollegio.ai/)) is the closest analog to what this engine powers: a free AI college counselor (100k+ users, $2.8M raised) whose matching "blends personality and academic fit to show where you'll *thrive*, not just where you're admitted" — essentially UniPaith's own "fit, not fame" thesis (`07` §2). Its data method (per public sources): it **combines public college data + institutional catalogs + student outcomes + verified scholarship info** across **~1,650 U.S. institutions** (class size, majors, admitted-student profiles, aid packages, deadlines, fees, campus life, rankings, graduate careers), with LLMs (OpenAI + Anthropic) fine-tuned on ~300 counseling documents. ([review](https://www.automateed.com/kollegio-ai-review), [SiliconANGLE](https://siliconangle.com/2025/04/23/startup-kollegio-raises-2-8m-ai-powered-college-counseling-service/))

That validates the approach — and exposes exactly where to beat it. Each gap maps to a capability already in this spec:

| Kollegio's method (observed) | The gap | UniPaith improvement (this engine) |
|---|---|---|
| Matches on college data points; **no published sourcing methodology or per-fact provenance** | Students can't tell where a number came from or trust it; opaque | **Provenance on every fact** — source URL + `fetched_at` + confidence shown inline (§4, §7); "explain everything" (`07` §2) |
| Static snapshot of ~1,650 schools | No visible freshness; data drifts stale | **Scheduled re-crawl + change detection (`content_hash`) + decay/TTL** per domain (§10); "updated N days ago" surfaced |
| **US undergrad** institutional data | No international, graduate, or career/cost reference | **Full reference graph** (§3): careers/BLS, visa/immigration, cost-of-living, tests, majors, grading-scale + language equivalency — powers international (`38`) + graduate (`41`) + real OUTPUT features |
| **Student-only**; scraped data not authoritative | No way for a school to correct/confirm its own data | **Two-sided verification** — institution "claim & verify" (`23`/§9); **first-party data always beats crawl** (§8) |
| Matches on institutional data points | Reference numbers (salary, net price, visa odds) are shallow or absent | **World-reference tables** (§5.2) feed computed OUTPUT features — net price (`11` §3.3a), visa-feasibility band (`42` §4.3), outcome preview, probability bands (`09` §4A) — with real numbers, not vibes |
| Free, US-mass-market, fine-tuned-LLM advice | Advice quality capped by a static doc set; no live ground truth | **Live ground-truth reference graph** the matching engine (`06`) + agents (`45`) reason against — the data moat compounds as it's crawled + verified |

**Net:** Kollegio proves the market and the "thrive not just admit" framing; UniPaith's structural edge is **a transparent, fresh, verified, far broader knowledge graph** (not a static US-undergrad snapshot) feeding a **two-sided, explainable** matching engine. The crawler is how that edge is built. (Also note Kollegio's **direct-admissions** + **counselor recommendation co-pilot** features — our two-sided model is the structural version of direct admissions; the co-pilot analog is the institution-side AI (`37`).)

---

## 2. Build on what already exists (ground truth — verified in code)

The schema **already contains** a knowledge-engine skeleton — `models/knowledge.py` (254 lines), migrated by `c3a7f9e1d502_add_knowledge_engine_tables.py` (+ `data_sources` from `0001_initial_schema.py`). It is **dormant**: no services/API wired. **Reuse it.** Real columns as built:

| Table | Real columns | Role |
|---|---|---|
| `data_sources` (`matching.py`) | source registry + crawl config | Allowlist of approved sources + per-source policy |
| `crawl_frontier` | `url, domain, priority, content_format_hint, discovered_from_id, discovery_method, status, last_crawled_at, next_crawl_after, crawl_count, consecutive_failures, last_error, domain_crawl_delay_seconds, max_depth, respect_robots` | Priority crawl queue — **already has robots + per-domain delay + depth + backoff + dedup** |
| `knowledge_documents` | `source_url, source_domain, content_format, content_type, title, raw_text, extracted_text, summary, extracted_entities {json}, extracted_facts {json}, metadata_json, embedding(1536), quality_score, credibility_score, relevance_score, language, word_count, published_at, ingested_at, processing_status, processing_error, crawl_frontier_id` | Fetched docs: raw + extracted + facts + embedding + **credibility/quality/relevance scoring** |
| `knowledge_links` | `document_id, entity_type, entity_id, entity_name, relationship_type, confidence` | **Generic entity linkage — `entity_type` is free-form, so it already supports ANY domain** (career, test, visa, major…), not just school/program |
| `engine_directives` | `directive_type, directive_key, directive_value {json}, priority, is_active, expires_at` | Work directives ("enrich X", "refresh source Y") |
| `engine_loop_snapshot` | tick metrics (processed/errors/discovered/frontier-pending/…) | Engine run state + metrics (singleton) |
| `interaction_signals` | `user_id, signal_type, entity_type, entity_id, context, value` | Signal log (priority hints for the crawler) |

**Key finding:** the skeleton is domain-agnostic by design — `knowledge_documents.extracted_entities`/`extracted_facts` are JSONB and `knowledge_links.entity_type` is a free string. It can ingest *any* reference domain today. The work is: wire services + jobs + extraction (`45`) + the **normalized reference tables** (§5) + the enrichment write-path. (`knowledge_entities` is referenced in the model but has **no migration** — add it, §16.)

---

## 2A. Source strategy — official data first, scraping last (the production accuracy + legality win)

> **The single biggest production improvement, and the sharpest edge over a scrape-everything competitor (Kollegio, §1A):** for most domains in §3, **authoritative official APIs and bulk datasets already exist.** A production engine prefers them over scraping — they are more accurate, more current, fully legal, and far cheaper than LLM-extracting from HTML. The crawler is the *fallback* for what no official source publishes, not the default.

### 2A.1 The four-tier ingestion ladder (always use the highest tier available for a fact)
| Tier | Method | Trust | Cost | When |
|---|---|---|---|---|
| **1 — Official API** | authenticated REST pull | highest | lowest | the fact is in an official API |
| **2 — Official bulk dataset** | scheduled file download + parse | highest | low | API absent but a published dataset exists |
| **3 — Structured-page selectors** | per-source XPath/CSS templates | medium-high | low | a known site, stable layout, no API/bulk |
| **4 — LLM extraction from HTML** | `45` agent over raw page (§13/§13B) | medium | highest | unstructured prose / long tail / no template |

Rule: **never LLM-extract a fact a Tier-1/2 source already provides.** `data_sources.source_type` tags each source's tier; the resolver (§6 step 5) prefers higher-tier values in the conflict rule (§8).

### 2A.2 Authoritative sources per domain (researched, current)
| Domain (§3) | Tier-1 API | Tier-2 bulk | Notes |
|---|---|---|---|
| Institutions + program core stats (admit rate, cost, outcomes, enrollment, CIP programs, aid) | **College Scorecard API** (`api.data.gov/ed/collegescorecard/v1/schools`; API key; 1,000 req/hr) | **IPEDS** (NCES CSV/Access; back to 1997) + Scorecard bulk files | Covers the bulk of §3.0 + §3.6 history data for ~6,000+ US institutions — far past Kollegio's ~1,650, and *official*. |
| Careers / occupations (§3.1) | **BLS OEWS API** (500 queries/day; Series IDs) · **CareerOneStop API** | **O*NET database download** · BLS OEWS tables (~830 occupations) | Salary/outlook/skills/related occupations — official, not scraped. |
| Education data cross-cut | **Urban Institute Education Data API** | — | Convenience layer over IPEDS/Scorecard. |
| Tests (§3.2), Visa (§3.3) | (mostly none) | some official policy pages | Tier-3 selectors on official test-provider + immigration-agency pages; high source-trust required (§13). |
| Cost-of-living (§3.4) | some open indices | census/BLS regional | License-check (some COL datasets prohibit reuse — §16). |
| Rankings, scholarships, campus-life, curriculum detail | (none) | (none) | **Genuine crawl targets** (Tier 3/4) — this is where the web-crawler earns its keep. |

### 2A.3 API/bulk sync is a *job*, not a crawl
Tier-1/2 ingestion runs as a **scheduled sync** (`55` queue): pull → diff vs last snapshot → upsert via the same normalize→resolve→enrich-write path (§6 steps 4–6) and the same provenance (§7) + change-detection (§3B.3). Operationally distinct from web-crawling (no frontier/robots/politeness needed for an API), but it lands in the same tables with the same audit trail.

### 2A.4 What this leaves for the actual web-crawler
After Tier-1/2 cover institutional stats + careers, the **crawler proper** focuses on: scholarships, rankings, qualitative campus/program detail, events/deadlines, news (§3B), and the long tail of programs not in official datasets. This is a *much* smaller, higher-value crawl surface — which is exactly why the result is more accurate and cheaper to run than scraping everything.

---

## 3. What to gather — full Prompt-Library coverage

Every Prompt Library / Prompt Map domain → its world-reference dataset → the table it enriches. The first block (institutions/programs/scholarships) was v1; everything below it is the v2 expansion.

### 3.0 Institutions / Programs / Scholarships (Prompt Map "School / Program", `06` §3)
As v1: School Info, Program Info, Admissions & policy, History data, Live-ops → `institutions`/`schools`/`programs`/`historical_outcomes`/`events` + the new `scholarships` table (§5.1). (Unchanged; see the field-by-field mapping retained in §3.7.)

### 3.1 Careers & occupations (mirrors `42` §3.12 intent/goals, §3.8 work; feeds OUTPUT §4.11 career-alignment + §4.7 outcomes)
- Source: **BLS Occupational Outlook, O*NET**, industry reports.
- Fields: occupation title + code (SOC), median/range salary, growth outlook, demand, typical entry education, required skills, related occupations, day-to-day, geographic concentration.
- Powers: career-goal realism (`42` §3.24 salary-realism), "outcome preview" (`42` §4), degree→career path mapping, "students with this goal study X."

### 3.2 Standardized tests (mirrors `42` §3.6; feeds OUTPUT §4.6 test policy/superscore)
- Source: ETS/College Board/ACT/British Council public info + program test policies (crawled with programs).
- Fields: test types (SAT/ACT/GRE/GMAT/TOEFL/IELTS/DET/LSAT/MCAT), score scales + percentiles, typical program ranges, test-optional/blind trends, test dates, registration, validity windows, superscore rules.
- Powers: `test_policy_compatibility`, submit-vs-withhold recommendation, "meets typical range" band.

### 3.3 Visa & immigration (mirrors `42` §3.3; feeds OUTPUT §4.3 visa feasibility; serves `38`)
- Source: official immigration agencies (USCIS, IRCC, UKVI, etc.), institution international offices.
- Fields: visa types by destination country (F-1/J-1/Tier-4…), eligibility, financial-proof thresholds, processing times, work-authorization rules (OPT/PGWP), recent policy changes, document checklists.
- Powers: visa feasibility band, timeline risk, readiness checklist (`42` §4.3), feeds the international module (`38`).

### 3.4 Cost of living & geography (mirrors `42` §3.13 constraints; feeds OUTPUT §4.12 net-cost, affordability)
- Source: public cost-of-living indices, BLS/census, city data.
- Fields: by city/region — rent, living-cost index, transport, safety/quality-of-life proxies, climate; distance/relocation context.
- Powers: net-cost scenario, affordability band, geographic feasibility, "true cost to attend here."

### 3.5 Majors, curriculum & fields of study (mirrors `42` §3.18 + `43` 15 tracks)
- Source: institution catalogs, CIP taxonomy, accreditation curricula.
- Fields: CIP major code + name, what the major entails, typical courses, prerequisites, common concentrations, career paths from the major, related majors, per-discipline readiness expectations (the `43` tracks).
- Powers: major-track fit, prerequisite-gap detection (`42` §4.5), "fastest fix path," curriculum-to-goal alignment.

### 3.6 Rankings, accreditation, employer outcomes (mirrors History data + OUTPUT §4.7/§4.13)
- **Rankings**: program/institution rankings (multiple sources, with source + methodology cited) → `institutions.ranking_data`.
- **Accreditation**: accrediting bodies + status + validity → institution policy fields (trust/eligibility signal).
- **Employer outcomes**: where graduates work, hiring employers by program, salary outcomes, placement rates → `historical_outcomes` + `employer_feedback` (`51`).
- Powers: outcome preview, selectivity/access context, employer-fit highlights.

### 3.7 Supporting reference (lighter, as needed)
- **Grading-scale normalization** (mirrors `42` §3.4/§3.5): foreign grading systems (IB, A-level, Gaokao, 10-point) → normalization tables feeding `normalized_gpa` (`42` §4.5) + credential eval (`38`).
- **Language-proficiency equivalency** (mirrors `42` §3.11): CEFR/ACTFL ↔ test-score mapping.
- **Competitions/activities reference** (mirrors `42` §3.9): known competitions + tiers (for activity weighting).
- **Events & deadlines** (Live-ops): public college fairs, info sessions, application deadlines → `events`/`intake_rounds`.

> **What is NOT gathered** (stays student-self-provided per `46`): identity/contact, the student's own academics/tests/work/essays, engagement telemetry, anything personal. The crawler builds the *world*; the student builds *their record*; matching joins them.

---

## 3B. Proactive monitoring — news, changes & autonomous discovery

> The engine is not a one-time scraper or a passive scheduler — `models/knowledge.py` calls it the **"perpetual knowledge engine."** Proactive is the default mode: it continuously watches for **news and changes**, **discovers** new entities/sources on its own, and **pushes** time-sensitive changes to the students they affect. This is the layer that makes the data feel alive, and it's the sharpest edge over a static snapshot (Kollegio, §1A).

### 3B.1 Three proactive behaviors
1. **News & change monitoring** — watch authoritative sources for *new* and *changed* facts, not just re-confirm known ones.
2. **Autonomous discovery** — the engine expands its own coverage (new institutions, programs, scholarships, sources) without a human directive.
3. **Signal-triggered crawling** — student behavior + approaching deadlines + detected gaps raise crawl priority in real time.

### 3B.2 What's monitored (time-sensitive, by domain — mirrors §3)
- **Policy news** — visa/immigration rule changes (`ref_visas`), test-optional/test-policy shifts (`ref_tests`), FAFSA/financial-aid changes, accreditation status changes.
- **Institution news** — new programs launched / programs closed, **deadline changes**, tuition/cost changes, ranking releases, admissions-stat releases, leadership/strategy news, new scholarships posted.
- **Scholarship news** — newly opened scholarships, deadline moves, closed/expired awards (`scholarships`).
- **Sector / market news** — ranking publications, admissions-cycle news, **labor-market & career-outlook updates** (`ref_occupations`).
- Each news item is tied to the entity/domain it affects via `knowledge_links` (already supports any `entity_type`).

### 3B.3 Change-detection & the `change_event` pipeline
Beyond `content_hash` skip (§6 fetch), material changes are detected and emitted as first-class events:
```
re-crawl → content_hash differs → semantic diff (45 agent: old vs new) →
   classify change_type + materiality + confidence → write change_event →
   relevance-route (3B.5) → surface to affected students
```
- A `change_event` captures: target entity, `change_type` (deadline_moved | new_scholarship | policy_change | program_added | program_closed | cost_change | ranking_update | stat_update | new_event), `field_path`, `old_value`→`new_value`, materiality (low/medium/high), source document, confidence, status.
- **Materiality classifier** (`45`): "does this change matter, and to whom?" — a typo fix is material=low (no routing); an applied-program deadline moving is material=high (immediate notify).

### 3B.4 Autonomous discovery (the engine expands itself)
- **Frontier self-expansion** — follow `knowledge_links` to new entities/sources; a crawled program page mentioning a new scholarship → queue it.
- **Search-driven discovery** — for under-covered or newly-relevant entities (a student targets a niche program with no data), the engine issues a web search to find authoritative sources and seeds the frontier. Bounded by the allowlist/trust rules (§11).
- **Gap-filling loop** — each `engine_loop_snapshot` tick scans for sparse or stale entities and self-issues `engine_directives` (no human needed) — sparse records + approaching deadlines + high student interest rank highest.
- **Watchlists** — entities students **save / apply-to / follow** (`interaction_signals`, `student_follows`) get a monitoring watchlist with elevated freshness (3B.6), so the data students depend on is the freshest.
- **Emergence detection** — newly-announced programs/scholarships/events are added as new provisional entities (review-gated, §9).

### 3B.5 Routing changes to the people who care (the proactive payoff)
A `change_event` → relevance match (whose saved / applied / followed / saved-search set it touches) → surfaced, **so students don't have to go looking — relevant news finds them**:
- **Connect feed** (`20`) — "University X extended its CS MS deadline to Jan 15" (the `program_change` feed item already specified in `20` §4.3 is fed from here).
- **Notifications** (`57`) — urgent changes on an **applied/saved** entity (deadline moved, decision-policy change) → immediate push; non-urgent → digest (`57` §5).
- **Saved-search alerts** (`56`) — "a new scholarship matches your saved search" / "a new program fits your filters."
- Gated by materiality + consent (`46`) + per-user alert caps (`56` §9); deduped + batched (`57`).

### 3B.6 Volatility-tiered freshness (extends §10)
Cadence scales with how fast a domain changes:
| Tier | Examples | Cadence |
|---|---|---|
| **News / policy** | visa rules, FAFSA, test-policy, rankings | continuous feeds (hourly–daily) |
| **Deadlines (in-cycle)** | application + scholarship deadlines | daily during the cycle |
| **Watchlisted entities** | programs students saved/applied-to | elevated (e.g., daily–weekly) |
| **Standard reference** | curriculum, cost-of-living | monthly–quarterly |
| **Slow reference** | occupation salary/outlook | annually |

### 3B.7 New table: `change_events` (+ reuse `knowledge_documents` for raw news)
- Raw news docs ride the existing `knowledge_documents` (`content_format='news'`, `published_at` already exists for recency).
- Add **`change_events`**: `id, target_type, target_id, change_type, field_path, old_value, new_value, materiality, source_document_id → knowledge_documents, confidence, detected_at, status(pending|routed|dismissed), routed_at`. This is the routable, auditable record behind every feed item / alert / notification in 3B.5.

### 3B.8 News-specific guardrails (extend §11)
- **Source trust is stricter for news** — prefer primary/official sources (`.gov`, `.edu`, the institution itself, the testing body, the immigration agency); **material claims require corroboration** before high-materiality routing (avoid acting on rumor).
- **Never present unverified news as fact** — "reported by <source>, <date>" framing + provenance + confidence; a single low-trust source is informational, not an alert.
- **Institutional / policy / sector news only — no personal news.** No crawling a person's social posts or news about individuals (reinforces the §1 PII bright line); the engine watches the *world*, not people.
- robots/ToS/rate limits apply to news + feed sources identically (§11).
- **No fabricated urgency** — a change_event's materiality must trace to a real diff in a real source doc; the engine never invents "news" to drive engagement.

---

## 4. How to present it (provisional, sourced, explainable — unchanged from v1, applies to all domains)

Per "explain everything" (`07` §2) + the data invariants (`06` §5):
- **Provenance on every crawled fact**: `source=crawled` + source URL + `fetched_at` + `confidence` (the `42` §5 universal record metadata). UI shows "Sourced from <domain> · updated N days ago."
- **Provisional vs verified**: crawled data is provisional until confidence-gated and/or institution-confirmed (`23`); **verified institution/first-party data always wins** (§8).
- **Never fabricate**: not-found stays empty; low-confidence → review queue (§9), never the live record.
- **Same editorial components**: reference data flows into existing surfaces — careers into the program "Outcomes" + a career-context panel, cost-of-living into the net-price estimator (`11` §3.3a), visa reference into the student's visa readiness (`42` §4.3) and the international module (`38`), test ranges into program admissions (`11`/`23`). No separate "crawled data" UI; no decorative treatment (`01`).
- **Reference vs entity**: world-reference facts (a career's median salary) are shown as context ("typical for this field"), distinct from a specific program's own data — so students never confuse a national average with a program's claim.

---

## 5. New tables

### 5.1 `scholarships` (matchable entity — unchanged from v1)
As specified before: institution/program-linked or external; type, amount, eligibility JSONB, deadline, application, distribution history, provenance, `status: provisional|live|archived`. Feeds `aid_scholarship_likelihood_band` + net-price (`09`/`11`). (Full schema retained from v1 — `scholarship.py`.)

### 5.2 Reference-knowledge tables (the v2 additions)
The normalized, queryable projection of the reference graph. High-value domains get typed tables; the long tail lives in a generic table. All carry provenance (`source_url, confidence, fetched_at, source` + version).

| Table | Domain (§3) | Key fields |
|---|---|---|
| `ref_occupations` | 3.1 careers | soc_code, title, salary_median, salary_range, outlook, demand, entry_education, skills[], related[] |
| `ref_tests` | 3.2 tests | test_code, scale, percentile_table {json}, validity_months, registration_url, typical_ranges {json} |
| `ref_visas` | 3.3 visa | country, visa_type, eligibility {json}, financial_proof_threshold, processing_time, work_auth, updated_at |
| `ref_geo_cost` | 3.4 geo/cost | city, region, country, col_index, rent_band, transport, climate, quality_proxies {json} |
| `ref_majors` | 3.5 majors | cip_code, name, description, typical_courses[], prerequisites[], career_paths[], related_cip[] |
| `ref_rankings` | 3.6 rankings | entity_type, entity_id, source, rank, year, methodology_url |
| `ref_accreditation` | 3.6 accred | body, scope, institution_id, status, valid_until |
| `reference_entities` (generic) | long tail | domain, canonical_key, name, attributes {json}, provenance — for grading scales, language equivalency, competitions, etc. |
| `entity_enrichments` (provenance/audit — from v1) | all | target_type, target_id, field_path, proposed_value, source_document_id, source_url, confidence, status |

> Rationale: the matching engine + OUTPUT features query reference data by structured fields (salary by SOC, COL by city, score range by test) — so the hot domains are typed tables, not JSONB blobs. The generic `reference_entities` keeps the long tail extensible without a migration per domain. `knowledge_documents`/`knowledge_links` remain the raw graph; reference tables are the clean projection.

---

## 6. Pipeline architecture (generalized to all domains)

Six queue stages on the `55` substrate; the engine loop (`engine_loop_snapshot`) orchestrates. **Domain-parameterized** — the same pipeline runs for every §3 domain; only the source set + extraction schema differ.

```
(0) SOURCE REGISTRY   data_sources: approved domains tagged by reference-domain + policy
       │  engine_directive {domain, target}  (e.g. "refresh BLS occupations", "enrich program X")
       ▼
(1) DISCOVER   seed URLs + knowledge_links graph → crawl_frontier (priority/depth/dedup by url)
       ▼
(2) FETCH      robots + domain_crawl_delay + conditional GET; store knowledge_documents (raw + content hash)
       │  unchanged content → skip parse
       ▼
(3) EXTRACT    domain-specific 45 agent reads the page → structured fields per the §3 domain schema
               (occupation / test / visa / cost / major / scholarship / institution / program)
       ▼
(4) NORMALIZE  units/enums/scales (42 §5): currency, SOC/CIP codes, CEFR, dates, grading scales
       ▼
(5) RESOLVE    map facts → existing or new reference/entity rows (knowledge_links + the §5 tables)
       ▼
(6) ENRICH-WRITE  confidence-gated: high → provisional field + provenance; low/conflict → review (§9)
```
Politeness, idempotency (url+content hash), and observability (queue depth, fetch/parse success, fields-enriched, LLM cost via `ai_turns`) exactly as v1 — now reported per-domain.

---

## 7–13 (unchanged from v1, now apply across all domains)

These sections generalize without change — the broadened scope rides the same machinery:
- **§7 Provenance & write-path** — `entity_enrichments` audits every crawled field for *any* target type; reversible.
- **§8 Conflict & authority** — first-party/verified > corroborated crawl > single high-trust > single low-trust; institution-verified never overwritten. Applies to reference data too (e.g., an institution's own salary-outcome figure beats a national average for *that* program).
- **§9 Review & governance** — institution claim-verify (`23`) for their data; internal ops queue + LLM judge (`45`) for reference data; student "report incorrect."
- **§10 Freshness & scheduling** — per-source cadence (rankings yearly, visa policy on-change, deadlines weekly-in-cycle, occupations annually); conditional fetch; priority from `interaction_signals`.
- **§11 Legal, ethical & safety** — allowlist-only sources, robots/ToS, rate-limited + identified UA, **public non-personal data only**, attribution + reversibility, trust scoring, audit (`36`/`55`); ties `58`.
- **§12 Service & API surface** — `services/crawler/` (source_registry, frontier, fetcher, extractor, normalizer, resolver, enrichment_writer, scheduler); internal ops API (system-guarded); institution enrichment-review API (`23` extension); reference data surfaces through existing student endpoints (`50`) with provenance fields added.
- **§13 Extraction agent** — per-domain `SourceExtractionAgent` variants (`45`), forced structured output validated against the §3/§5 schema, **never invents**, cost-tracked, cached by content hash, rule-based fallback per source template.

---

## 13A. Production crawler engineering (the actual web-crawl tier)

For Tier-3/4 sources (§2A) the engine needs real crawler engineering, not a fetch loop.

- **Framework: Scrapy** (Python — fits the async FastAPI stack) for the web-crawl tier, backed by the existing `crawl_frontier` as the durable queue. Not Nutch (Java/Hadoop is web-scale overkill for a curated allowlist). Consider a managed render API (Apify/Firecrawl) for the hard JS long-tail instead of self-hosting headless browsers (§13D / §16).
- **URL canonicalization before dedup**: normalize scheme/host/case, strip tracking params (utm_*, fbclid), resolve relative→absolute, drop fragments, normalize trailing slash — *then* compute `url_hash`. Prevents phantom duplicates ([dedup/canonicalization](https://potentpages.com/web-crawler-development/web-crawlers-and-hedge-funds/deduplication-canonicalization-preventing-double-counts-and-phantom-signals)).
- **Near-duplicate detection**: exact `content_hash` (already, §6) + **SimHash/MinHash shingling** so a reworded or boilerplate-changed page doesn't re-trigger expensive extraction ([SimHash/MinHash](https://grokkingthesystemdesign.com/guides/web-crawler-system-design/)).
- **Politeness budgets** (beyond robots): per-domain req/sec + concurrency cap + crawl-window, honoring `robots` crawl-delay; identified User-Agent + contact URL; the existing `domain_crawl_delay_seconds` + `consecutive_failures` backoff enforce it.
- **Frontier management**: priority queue (existing `crawl_frontier.priority`) with **domain sharding** so one slow domain can't starve others; `max_depth` (existing) bounds discovery; conditional GET (ETag/If-Modified-Since) + `content_hash` skip avoid re-fetching unchanged pages.
- **Rendering tier**: most institutional pages are static — fetch HTML directly. Only escalate to a headless browser (Playwright) when a static fetch yields empty content, gated by a per-source flag (it's ~10–50× the cost).

## 13B. Extraction quality, evaluation & cost control (production LLM discipline)

The §13 extraction agent must be *measured*, not trusted — and run cheaply.

- **Selectors-primary, LLM-fallback**: per-source CSS/XPath templates (deterministic, ~free) run first; the `45` LLM agent runs only when selectors miss or for genuine prose. Research shows keeping selectors primary with AI fallback is the key cost lever ([AI extraction 2026](https://use-apify.com/blog/web-scraping-with-ai-llms-2026)).
- **Schema-strict output**: flat JSON, required fields + types + enums — this minimizes hallucination (flat-JSON extraction hits F1 ≈ 0.957 vs other formats, [NEXT-EVAL](https://arxiv.org/pdf/2505.17125)); validate against the §3/§5 schema before any write; retry-on-validation-failure.
- **Grounding / hallucination guard**: the agent must cite the source span for each fact; an LLM scorer (or rule check) rejects facts not grounded in the page text. "Never invents" (§13) is thus *enforced and measured*, not promised.
- **Golden-set regression**: a labeled gold dataset per domain (known pages → expected fields). CI runs extraction against it and measures **precision/recall/F1 per field**, failing the build on regression — DeepEval/Deepchecks-style ([LLM eval gold sets](https://testquality.com/llm-regression-testing-pipeline/)).
- **Drift detection**: scheduled re-eval against the gold set + comparison to historical baseline catches model drift *and* silent source-layout changes (the selector broke → F1 drops → alert + template-fix directive).
- **Cost control**: track tokens-per-page (`ai_turns`), alert on budget overrun; cache by `content_hash` (no re-extract of unchanged pages); use the cheapest model that passes the domain's gold-set bar (Haiku default per `45`; escalate only where eval demands).

## 13C. Crawler observability, SLOs & failure modes

Rides the `55` observability substrate; `engine_loop_snapshot` already records per-tick metrics — wire it to the dashboard.

- **Metrics**: frontier depth + oldest-pending age; fetch success rate; parse/extraction success + **F1 from the gold set**; fields-enriched/run; `change_events`/run + unrouted-high-materiality count; LLM cost/day; per-domain error rate; **freshness lag per domain** (how stale vs its TTL, §12).
- **SLOs**: ≥95% of watchlisted entities (§3B.4) refreshed within their TTL; extraction F1 ≥ per-domain threshold; **zero high-materiality `change_events` unrouted > N hours**; crawl-error rate < threshold per domain.
- **Failure modes + handling**: source layout change → selectors break → LLM fallback + alert + fix-template directive; source down → backoff, don't thrash; rate-limit/429 → honor Retry-After, slow the domain; bad extraction → gold-set catches it pre-ship; spam/poison source → `trust_score` demotion; robots/ToS change → re-check, stop if now disallowed.
- **Runbook** per alert (F1 drop, frontier stall, cost spike, source-down, DLQ non-empty) — diagnosis + action; ties the `55` §9 + `58` incident process.

## 13D. Stack, deployment & isolation

- **Worker fleet**, separate from the API tasks (bulkhead, `55` §6) so crawling/extraction never competes with serving latency.
- **Components** on the `55` queue (Arq + Redis): Scrapy web-crawl workers (Tier 3/4) · API/bulk **sync** workers (Tier 1/2, §2A.3) · LLM **extraction** workers (`45`) · **scheduler** (engine-loop tick → enqueue due directives, §3B.4 / §12).
- **Storage**: `crawl_frontier`/`knowledge_documents`/`knowledge_links` raw graph + the §5 normalized reference tables + `change_events`; pgvector on `knowledge_documents.embedding` for semantic dedup + retrieval.
- **Secrets**: API keys (data.gov / Scorecard, BLS, CareerOneStop) in AWS Secrets Manager (`58`); per-key rate-limit budgets respected (Scorecard 1,000/hr, BLS 500/day — §2A.2) via the `55` §4 limiter.
- **Idempotent + resumable**: every stage keyed (url_hash/content_hash/directive id) so a worker restart never double-writes (`55` §5).

---

## 14. Phasing (re-sequenced for the broader scope)

- **Phase A — institutional core**: wire services onto the skeleton; schools/programs/scholarships from a few high-trust `.edu` + scholarship sources; review-queue everything. Add `scholarships`, `entity_enrichments`, `knowledge_entities` migration.
- **Phase B — student-facing reference**: the highest-leverage reference domains that power matching + OUTPUT features — **careers (3.1), tests (3.2), visa (3.3), cost-of-living (3.4), majors (3.5)**. These make the match rationale + net-price + visa-feasibility + outcome-preview real.
- **Phase C — depth + long tail**: rankings, accreditation, employer outcomes, grading-scale + language equivalency, competitions; confidence-gated auto-apply; learned extraction templates; priority crawling from engagement.
- Sequenced **after the MVP core** (`48`). Enrichment makes a populated app richer; not a launch blocker, but it's how the database stops being sparse and the AI reasons against the real world.

---

## 15. Acceptance (extends v1)

- [ ] Only `data_sources`-registered, domain-tagged sources fetched; robots/rate honored (verifiable in logs).
- [ ] Each §3 reference domain has: a source set, an extraction schema, a normalized table (§5), and provenance on every row.
- [ ] A crawled fact (career salary, test range, visa requirement, cost-of-living, major prereq) appears as **provisional + source-cited + confidence** in the surface that consumes it.
- [ ] Reference data feeds the OUTPUT features it should (net-price ← cost+aid; outcome preview ← occupations; visa band ← visa ref; test compatibility ← test ref).
- [ ] Institution/first-party data never overwritten by a crawl (conflict → review).
- [ ] Re-crawl of unchanged content = no parse, no write (idempotent).
- [ ] **No personal/individual data gathered** (contract test); only public reference/institutional data; all actions audited.
- [ ] Extraction agent never writes a field absent from the source (no fabrication), across every domain.

---

## 16. Open questions

- **`knowledge_entities` migration** — referenced in the model, no migration found; add before entity-resolve relies on it.
- **Reference source licensing** — BLS/O*NET/IPEDS are open; some rankings + scholarship + cost-of-living datasets prohibit scraping or require licensing. Start with open/government + institution `.edu`; license or API-integrate the rest. Per-source legality recorded in `data_sources`.
- **Typed tables vs generic** — confirm the §5 hot-domain table list; promote from `reference_entities` to a typed table when query/index needs justify it.
- **Reference-data staleness tolerance** — define TTL per domain (salary data annual vs visa policy on-change vs deadlines weekly).
- **People data line** — `advisor_personas`/`person_insights` stay dormant for this engine; if grad advisor-matching (`41`) ever wants public faculty profiles, that's a separate, consent-reviewed decision (`46`), not part of this crawler.
- **Auto-apply threshold** — start review-all; loosen per measured precision per domain.
- **Old removed crawler** — confirm nothing from the pre-pivot admin-crawler is silently re-enabled; this is the clean scoped replacement.

Sources: internal materials — Prompt Map (`Misc./Prompt Map.pdf` → `06` §3), Prompt Library (`42`/`43`), existing `models/knowledge.py` skeleton (verified in code). Competitive: [Kollegio](https://www.kollegio.ai/) · [Kollegio review (automateed)](https://www.automateed.com/kollegio-ai-review) · [SiliconANGLE funding/coverage](https://siliconangle.com/2025/04/23/startup-kollegio-raises-2-8m-ai-powered-college-counseling-service/).
