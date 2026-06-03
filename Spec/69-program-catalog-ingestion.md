# 69 · Program Catalog Ingestion at Scale — From 9 Programs to a Real Library

> Studyportals carries *"240,000+ programs from 3,700+ universities across 117 countries,"* continuously updated (`Competition Analysis`:2154,2170); Niche and Appily index the U.S. at comparable depth. UniPaith's catalog is **3 institutions, 5 schools, 9 programs — every one a hand-written `Program(...)` literal, every one CS/DS/MBA/policy-flavored** (`scripts/seed_dev_data.py:261` institutions, `:382` programs, zero generators). The `60` crawler seeds *reference* data — institutions-as-knowledge-entities and scholarships (`services/crawler/seed.py:249,309`) — not a browsable program catalog. The `65` matcher embeds and scores **programs**; with nine demo rows there is nothing to embed, nothing to rank, nothing to find. This is the single biggest prototype-vs-product gap, and it is a *data* gap, not an engine gap.
>
> The substrate to close it is already in place and must be **operationalized, not rebuilt**: `60`'s full pipeline (`services/crawler/` — `extractor.py` grounded-never-invents `:6`, `enrichment.py` authority precedence `:51`, `change_detector.py` materiality+consent routing `:75`, `normalizer.py` CIP/SOC/currency `:24-49`, `resolver.py` canonical entity get-or-create `:50`); and Spec 24's institution-direct upload — `services/dataset_upload_service.py` already does column-mapping (`save_mapping_template` `:526`), program-name normalization (`program_lookup` + suggestions `:137,153`), validation (missing/duplicate/invalid-date/unmappable, `validate_dataset_rows` `:122`), replace-vs-append (`replace_or_append_file` `:371`), versioning (`DatasetVersion`), and a usage-scope→consumer map (`USAGE_CONSUMERS` `:44`, `dataset_used_by` `:571`). 69 wires these into *the program catalog itself*: many institutions, many programs, ingested at volume, deduped, normalized, provenance-stamped, first-party-wins, SEO-renderable.
>
> Build anchor: extend `services/dataset_upload_service.py` (usage-scope `training` gate); a new `services/catalog/` ingestion pipeline over `60`'s `services/crawler/` stages; catalog provenance/freshness columns on `programs`/`schools` (`models/institution.py:171,140` — no `cip_code`/`external_id`/`source`/`slug` today); program dedup over the dormant `embeddings` HNSW table (`models/matching.py:119`, entity_type=`program`). Pairs with `60` (crawler), `63` §8 (embeddings/dedup), `62` (extraction eval), `56` (search index), `66`/`67` (admit-history + training consent), `68` (outcomes land here), `65` (real programs to embed), `46` §9 (consent), `22`/`23`/`24` (institution profile/editor/upload).
>
> Status: **draft v1.0** · 2026-06-02 · turns the 9-program demo into a real ingestion pipeline (institution-direct + crawl + editorial) on the `60`/`24` substrate. Deterministic default; LLM extraction stays eval-gated + grounded; rule-based fallback never-5xx (`tests/test_plan2_integration.py`).

---

## 1. What exists vs what to build

| Capability | Real module today | Status |
|---|---|---|
| Institution-direct CSV upload + versioning | `dataset_upload_service.py:280,371` | exists — **extend (not rebuild)** |
| Column-mapping + saved templates | `save_mapping_template` `:526`, `DatasetMappingTemplate` | exists — keep |
| Upload validation (missing/dup/date/unmappable) | `validate_dataset_rows:122` | exists — extend (program-ID norm) |
| Usage-scope consent map | `USAGE_CONSUMERS:44`, `dataset_used_by:571` | exists — **add `training` scope (feeds `66`/`67`)** |
| Program catalog at volume | 9 literals (`seed_dev_data.py:382`) | **NEW (build): ingestion populates programs** |
| Crawl → program fields | `60` crawler seeds *reference* only (`crawler/seed.py`) | **NEW (build): program discover→extract→write** |
| Grounded extractor (never invents) | `crawler/extractor.py:6,138` | exists — reuse for program schema |
| Authority precedence / first-party-wins | `crawler/enrichment.py:51-57` | exists — reuse for catalog writes |
| CIP/SOC/currency normalizers | `crawler/normalizer.py:24-49` | exists — reuse |
| Editorial (curated/manual) ingest path | program editor (`23`); no bulk curate path | **NEW (build): editorial source kind** |
| Program dedup (embeddings) | `embeddings` HNSW unused (`models/matching.py:119`) | **NEW (build): dedup over Vector(1536)** |
| Catalog provenance / per-field freshness | none on `programs` (`institution.py:171`) | **NEW (build): source/provenance/TTL columns** |
| Change-events → alerts routing | `crawler/change_detector.py:75,167` | exists — route program changes through it |
| SEO-indexable program/school records | client-rendered SPA; no canonical server data | **NEW (build): server-renderable canonical record** |

## 2. Institution-direct upload — extend Spec 24, do not rebuild

`dataset_upload_service.py` is the upload spine and already covers most of the papers' "Data Upload" module (`Business Methodology`:498-511). Extend it; the surface is `/i/data` (`24`).

- **`training` usage scope (the consent gate `66`/`67` read).** `USAGE_CONSUMERS` (`:44`) maps `marketing`/`admissions`/`analytics`/`all` → consumers but has **no `training` tier**. Add `"training": ["model_improvement"]` and a stricter explicit-opt-in: a dataset is eligible to *train* a model only when `usage_scope` admits training **and** `consent.training` is set (`46` §9 hard gate). `dataset_used_by()` becomes the single function `66`/`67` call to decide eligibility — they never read raw rows directly. **Customer-data / model-improvement separation** lives here (`67`): admissions-ops use ≠ training use.
- **Program-ID normalization to catalog pages.** Today `validate_dataset_rows` matches `program_name` case-folded against the institution's program names with fuzzy suggestions (`:151-158`). Strengthen to resolve each uploaded row to a **stable `program_id`** (the catalog FK), reusing the `60` resolver pattern (`crawler/resolver.py:50` canonical get-or-create) and the existing fuzzy threshold (`crawler_fuzzy_match_threshold=85`, `config.py:538`). Unmatched rows → review with suggestions, never silently dropped. This is what lets an admit-history upload (`66`) and an outcomes upload (`68`) bind to the *same* program a student browses.
- **Dataset types for the catalog.** `REQUIRED_FIELDS` (`:28`) already declares `admissions_history`, `outcomes_summary`, `prospect_list`. Add a **`program_catalog`** dataset type (bulk program rows for an institution with many programs) with its own required fields (`program_name`, `degree_type`) and date validation — the direct path to "many programs" for a partner that won't hand-enter each in the editor (`23`).
- **Keep as-is:** replace-vs-append (`replace_or_append_file:371`), versioning + rollback (`DatasetVersion`, `:458`), saved mapping templates (`:526`), the best-effort `DocumentParseTriage` note (`:250`). Do not duplicate any of these.

## 3. Crawl ingestion — extend `60`'s pipeline to programs

`60` built the pipeline and pointed it at *reference* data. 69 adds a **program domain** to the same stages — no new crawler, no new fetcher.

- **Discover.** Seed the frontier (`crawl_frontier`, `60` §2) with program-catalog URLs for allowlisted institutions (`.edu` catalog pages, official program directories). Allowlist-only stays the posture (`crawler_allowlist_only=true`, `config.py:564`); `crawler_live_fetch_enabled` (`:563`) remains the hard gate on real fetches.
- **Extract.** Add a program `DomainSchema` to `crawler/extractor.py` (degree_type, duration, tuition, modality, deadlines, requirements, tracks, description). Extraction stays **grounded — never invents** (`extractor.py:6`); `_enforce_grounding` (`:138`) drops any field absent from source. Deterministic template extraction is the default; the LLM path is `ai_crawler_extraction_v2_enabled` (`config.py:447`) and passes through the *same* grounding check. Eval-gated (`62`): per-field precision/recall/F1 + no-fabrication on a program golden set before the crawl path writes.
- **Normalize.** Reuse `crawler/normalizer.py`: CIP for field/major (`normalize_cip:31`), SOC for career arcs (`normalize_soc:24`), currency for tuition/cost (`normalize_currency:39`), plus credential-level + modality maps (small deterministic additions). §4.
- **Dedup → resolve → write.** §5 dedup; resolve to a canonical program node; write through `crawler/enrichment.py` so **authority precedence holds**: `institution_verified` (5) > `first_party` (4) > corroborated crawl > single-trust (`enrichment.py:51-57`). **Institution-reported program data is never overwritten by a crawl** — conflict routes to review ("institution says X, source says Y", `:218`). Provenance (`source=crawled` + URL + `fetched_at` + confidence) on every crawled field, as `60` §4 mandates.

## 4. Normalization — the shared vocabulary that makes rows joinable

Every ingested program (upload / crawl / editorial) passes the **same** normalization so `65` can embed a consistent document and `56` can index one:

- **CIP** (field/major) and **SOC** (career arc) via `normalizer.py:24,31` — the join key to `60`'s `ref_majors`/`ref_occupations` and to `66`'s feature vocabulary.
- **Credential level** (certificate / bachelor / master / doctoral / professional) and **modality** (in_person / online / hybrid) — deterministic maps; `programs.degree_type` + `delivery_format` (`institution.py:189,201`) are the existing target columns.
- **Currency + cost** via `normalize_currency:39` so tuition is comparable across countries (feeds `70` net-price).
- Normalization correctness is itself eval-gated (`62`, `60` §13B): a CIP mis-map silently corrupts every downstream match.

## 5. Dedup — one program, one canonical record

A real catalog ingests the same program from multiple sources (institution upload + `.edu` crawl + a directory). Collapse them:

- **Blocking + embedding similarity.** Block on (normalized institution, CIP family, credential level); within a block, embed the program document (`63` §8, Qwen3-Embedding → **1536 dims, no migration**) into the dormant `embeddings` table (`models/matching.py:119`, entity_type=`program`, HNSW) and merge candidates above a cosine threshold. Shares the `56` retrieval index — the same vectors serve search and dedup.
- **Merge under authority.** The surviving canonical record merges fields by `60` precedence (§3); institution-verified values win; provenance is preserved per field. A merge never invents a value not present in some source.
- **Stable identity.** Each canonical program gets an `external_id` (source-scoped) + `slug` so re-crawls update in place (idempotent on url+content-hash, `60` §6) and admit-history/outcomes uploads bind to a durable key (§2).
- **Review on ambiguity.** Below-threshold near-matches do not auto-merge — they queue for the `60` ops review (§9) like a low-confidence enrichment, so a wrong merge (two distinct tracks collapsed) never ships silently. Merge decisions are reversible via the `entity_enrichments` audit trail (`60` §7).

## 6. Freshness, provenance & change routing

- **Per-field provenance + TTL.** `programs`/`schools` carry no provenance or freshness columns today (`institution.py:171,140`). Add catalog-ingestion columns (`source`, `source_url`, `last_ingested_at`, per-field provenance JSONB, `external_id`, `slug`) via Alembic (expand→contract, single head off `s60a1b2c3d4e`). Volatility-tiered TTL (`60` §3B): deadlines daily-in-cycle, tuition per term, descriptions quarterly. Stale → re-queue on the `60` frontier.
- **Recompute on change.** A material program edit/re-crawl bumps `programs.feature_version` — the existing cache key the rationale + match path already key on (`institution_service.py:428`, `match_service.py:659`) — so `65`'s program embedding + rationale invalidate automatically. Mirror that bump in the ingest writer.
- **Route changes to people who care.** A real diff (deadline moved, program closed, tuition change) flows through `crawler/change_detector.py` — `record_change` (`:79`) → materiality classify (`:96`) → `route` (`:167`) → Connect feed / notifications / saved-search alerts (`60` → `57`), gated by outreach consent (`:144`) + per-user/day cap (`:154`). No fabricated urgency: a `change_event` must trace to a real source diff.

## 7. Editorial ingestion — fill the gaps machines miss

Some programs are not on a crawlable page and not in a partner upload. Add a **curated/editorial source kind** (provenance `source=editorial`, authority below `first_party`, above single-low-trust crawl) for ops-entered or licensed-bulk rows. Same normalization (§4), same dedup (§5), same provenance discipline (§6) — editorial is a *source*, not a bypass. Distinct from the per-program editor (`23`, institution self-serve); editorial is platform-side gap-filling, governed like `60`'s ops review queue (§9).

## 8. SEO-indexable program & school records

Niche/Studyportals' acquisition moat is organic search — every program and school is its own indexed landing page (`Competition Analysis`:1781,2170). The app is a client-rendered SPA; ingested programs must also exist as **server-renderable canonical records**:

- A stable public route per program/school keyed by `slug` (§5), emitting canonical server-rendered metadata (title, description, structured-data: degree, field/CIP, institution, location, cost, deadline) + JSON-LD. Provenance shown, first-party-wins (`60` §4) — a crawled fact reads "Sourced from <domain> · updated N days ago", distinct from the institution's own claim.
- Indexability is a property of *real ingested data*: only published, provenance-stamped, deduped programs are exposed (no demo rows, no fabrication). This is the organic-acquisition surface the catalog unlocks once it is real.
- Reuses the editorial component contract (`60` §4) — no separate "crawled" UI, no decorative treatment (`01`), consistent with the program-detail aesthetic. The synthesized factual content is Qwen's (`63` §5, display-synthesis, brand-voice + groundedness eval-gated `62`); the canonical record is what the server renders and a crawler indexes.

## 9. Build tasks (checklist)

- [ ] Extend `USAGE_CONSUMERS` with `training` scope + `dataset_used_by()` training-eligibility gate (`66`/`67`), ANDed with `consent.training` (`46` §9); customer-data/model-improvement separation.
- [ ] Add `program_catalog` dataset type (required fields + date validation) to `dataset_upload_service.py`; bulk-program direct upload.
- [ ] Program-ID normalization: resolve uploaded rows → stable `program_id` (reuse resolver + fuzzy threshold); unmatched → review with suggestions.
- [ ] New `services/catalog/` ingestion pipeline over `60`'s stages; program `DomainSchema` in `crawler/extractor.py` (grounded, `62`-gated).
- [ ] Reuse `crawler/normalizer.py` (CIP/SOC/currency) + add credential-level/modality maps; normalization eval-gated.
- [ ] Program dedup over `embeddings` (entity=`program`, 1536-d, HNSW); block on inst×CIP×credential; merge under authority.
- [ ] Migration: catalog provenance/freshness columns on `programs`/`schools` (`source`, `source_url`, `last_ingested_at`, per-field provenance, `external_id`, `slug`); expand→contract, single head off `s60a1b2c3d4e`.
- [ ] Write path through `crawler/enrichment.py` (first-party-wins); `feature_version` bump on material change; route diffs via `change_detector` → `57`.
- [ ] Editorial source kind (curated/bulk), governed by the `60` ops review queue.
- [ ] SEO: server-renderable canonical program/school record + JSON-LD, slug-keyed, published-only, provenance shown.
- [ ] `ai_catalog_ingestion_v2_enabled` flag (net-new, default off / per-env after eval); rule-based template path is the default; never-5xx fallback (`tests/test_plan2_integration.py`).

## 10. Acceptance

- [ ] In a prod-like env the catalog holds **many institutions and many programs across multiple fields/levels/countries**, populated by ingestion — zero hand-coded `Program(...)` rows in any prod path (closes `seed_dev_data.py:382`).
- [ ] A bulk `program_catalog` upload and a crawl of the same program **converge to one canonical record** (dedup), with per-field provenance and institution-verified values winning over crawled ones.
- [ ] An admit-history upload (`66`) and an outcomes upload (`68`) **bind to the same `program_id`** a student browses (program-ID normalization holds).
- [ ] A dataset trains a model **only** when its `usage_scope` admits `training` *and* `consent.training` is set; test-enforced (`46` §9, `64` §6 release gate).
- [ ] The crawl extractor writes **no field absent from source** (no fabrication), program domain (`62` contract test); LLM path off → identical deterministic rows.
- [ ] A real source diff (deadline/closure/tuition) produces a routed `change_event` to affected students within consent + cap (`57`).
- [ ] Each published program/school exposes a **server-renderable canonical record + JSON-LD** at a stable slug; provenance shown; no demo data indexed.
- [ ] Disabling `ai_catalog_ingestion_v2_enabled` falls back to deterministic template ingestion; no 5xx from any model path.

## 11. Open questions

- **Bulk-source licensing for U.S. coverage** — IPEDS/College Scorecard program lists vs `.edu` crawl vs partner upload for the initial volume seed. *Recommend IPEDS/Scorecard bulk seed (skip-extract structured path, `60` §6 Tier-1) + partner-reported and crawl overlay; first-party-wins.*
- **Catalog size as a goal** — the papers give no UniPaith library-size SLO. *Recommend framing the gate as "ingestion at volume with provenance + dedup," not a row count; measure coverage breadth (fields/levels/countries) and freshness, not headcount.*
- **Program identity across institutions** — same-named programs at different schools, joint/dual degrees, sub-tracks as separate records vs `tracks` JSONB. *Recommend canonical = (institution, CIP family, credential, modality); tracks stay in-record (`programs.tracks`) unless separately admissible.*
- **Editorial authority rank** — where curated/licensed rows sit vs corroborated crawl. *Recommend editorial above single-low-trust crawl, below `first_party`; always reversible via `entity_enrichments` (`60` §7).*
- **Re-crawl cadence for catalog vs reference** — programs change on admissions cycles, not hourly. *Recommend per-field TTL (§6): deadlines daily-in-cycle, tuition per term, descriptions quarterly.*

Sources: internal — `60` §2-13 (crawler/pipeline/provenance/change-routing), `63` §8 (embeddings/dedup, 1536-d), `62` (extraction eval), `56` (search index), `66`/`67` (admit-history + training consent), `68` (outcomes ingest here), `65` (programs to embed), `46` §9 (consent), `22`/`23`/`24` (institution profile/editor/upload). Code — `scripts/seed_dev_data.py:261,382` (9-program demo), `services/dataset_upload_service.py:28,44,122,371,526,571` (Spec-24 upload spine), `services/crawler/{extractor.py:6,138, enrichment.py:51, normalizer.py:24-49, resolver.py:50, change_detector.py:75,167, seed.py:249,309}`, `models/institution.py:140,171` (School/Program, no provenance/slug), `models/matching.py:119` (embeddings HNSW), `config.py:447,538,563,564` (crawler flags), `services/institution_service.py:428` + `services/match_service.py:659` (feature_version cache key). Papers — `Business Methodology`:498-511 (Data Upload). Benchmark — `Competition Analysis`:1781 (SEO moat), 2154,2170 (Studyportals 240K programs / 3,700 universities / 117 countries).
