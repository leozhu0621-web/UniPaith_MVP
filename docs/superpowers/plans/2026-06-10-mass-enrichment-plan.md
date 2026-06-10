# Mass-Enrichment Plan — raising the whole fleet to the standard

**Status:** plan for review (grounded in the 2026-06-10 audit of gathering mechanisms)

**Goal:** Autonomously raise every institution / school / program profile to the (completed) standard, at fleet scale, with the no-fabrication guarantee — verified-or-omitted, never guessed.

## The reality the plan must respect

The audit found this codebase has a **strong VERIFY half and a near-zero GATHER half**:

- **Reusable (the spine):** `profile_enrichment/engine.py` (conformance-driven `plan()`/`apply_patch()`/`omitted`), `profile_enrichment/gate.py` (the tested no-fabrication verifier), `crawler/extractor.py` (grounded extractor, never-invents), `crawler/normalizer.py` (SOC/CIP/CEFR/currency maps), `content_ingest/service.py` (the **only** live web-fetcher in prod — httpx, polite UA, fail-soft, idempotent upsert, daily scheduler).
- **Missing (the entire acquisition layer):** the engine's `Researcher` is an unimplemented `typing.Protocol` — **no concrete `gather()` exists**, nothing calls `enrich()` outside one unit test, no `/enrich-profile` skill, no scheduled agent. The Spec 60 crawler orchestrator/fetcher/registry/change-detector were **deleted** (only the extractor + normalizer + schemas remain); `crawler_live_fetch_enabled`/`crawler_engine_enabled` are **orphaned flags — do not revive them**. **There is no web-search/web-fetch client in the backend at all.** The playbook is prose, not a machine-readable registry.

So mass enrichment is feasible, but the acquisition layer must be **built**, not merely wired.

## The key insight — a deterministic federal backbone first

The machine-addressable public datasets — **US DoE College Scorecard (keyed on UNITID), IPEDS, O*NET/CIP** — cover, for the *entire US fleet*, via API with **zero LLM and zero fabrication risk**:
- report-card stats (admit rate, net price, completion/graduation, retention, test-score 25–75, demographics),
- financial aid (pell/loan/tuition-free/no-loan/scholarship/median-debt/COA),
- median earnings (10yr) — and Field-of-Study program outcomes,
- institution basics (location, setting, control/type, undergrad majors).

These map directly onto the gate's `first_party` / `authoritative_2x` tiers (Scorecard + IPEDS/CDS agreement). **This single source set moves most institutions from skeleton to substantially-conformant — and needs no web search.** It is the highest-ROI, lowest-risk first move.

## Source map (field group → canonical source → gate tier)

| Field group | Canonical source | Gate tier |
|---|---|---|
| Report-card stats, financial aid, demographics, test scores | College Scorecard (UNITID) + IPEDS; cross-check Common Data Set | `authoritative_2x` (Scorecard+CDS agree) else Scorecard `first_party` |
| Median earnings 10yr; program FOS outcomes | Scorecard (+ institution outcomes page) | `authoritative_2x` / FOS `first_party` |
| Program career outcomes (salary dist, employers, industries, conditions) | Institution **career-office Employment Report** (PDF); FOS fallback | `first_party` cited; fallback `authoritative` |
| Tuition / cost breakdown / fees | Registrar / bursar / financing page | `first_party` cited |
| Rankings (QS / THE / U.S. News) | Each ranking body's own page | `first_party` per body, cited |
| Carnegie / accreditor | Carnegie listing / regional accreditor | `first_party` |
| Admissions (materials, deadlines, recs, test policy, international/visa/OPT) | Official how-to-apply page | `first_party` cited |
| Class profile (cohort, intl%, GPA/GRE/GMAT, work-exp) | Program Class Profile page | `first_party` cited |
| Faculty roster / tracks-curriculum | Faculty directory / curriculum page | `official_or_curated`, verbatim |
| Recognition / scale (Nobel, endowment, ratio, acres) | Institution Facts / news | `first_party` |
| Reviews ("what students say") | ≥2 reputable third-party guides, paraphrased + attributed | `authoritative_2x` / curated |
| Feeds (Updates + Events) | Institution RSS / iCal / social | `first_party` (already live via `content_ingest`) |
| Hero photo | Wikimedia Commons / institution media | structural (`none`) |

## What to build (the acquisition layer)

1. **`WebResearcher(Researcher)`** — a concrete `gather(level, target, field) -> list[Evidence]` modeled on `content_ingest/service.py`, emitting `Evidence(value, source, source_url, authority)` straight into `gate.verify()`.
2. **Machine-readable `field → source` registry** — turn `playbook.md` prose into concrete fetch targets. **v1 = deterministic gov/standards API clients only** (College Scorecard, IPEDS, O*NET/CIP).
3. **Retrieval capability** — the backend has none today. v1 needs only the federal **API clients** (no search). v2 adds a **search-API/SERP client** (Bright Data SERP/Discover is available in this environment) to discover official institution URLs, then feeds pages to `crawler/extractor.py`.
4. **LLM-judge layer** (design §8, unbuilt) — wraps (never replaces) the deterministic gate for non-deterministic groups (reviews, editorial); contradiction check vs. cited source text. Human-facing → Claude per the boundary policy.
5. **Idempotent emit** — engine patches persist via the existing **idempotent Alembic data-migration** pattern (`mit_profile.apply`-style, `replace=True`/dedup keys), so re-runs are safe and provenance is auditable.
6. **Delivery** — the `/enrich-profile <target>` skill + a scheduled cloud agent, behind a **new** flag (not the orphaned crawler flags).

## Phasing

- **Phase 0 — Standard lock (days):** land the manifest completion (`docs/.../2026-06-10-profile-standard-completion.md`), bump `STANDARD_VERSION` to 2. *Gating prerequisite — nothing keys off the standard until phantom paths are fixed.*
- **Phase 1 — Deterministic federal backbone (highest ROI, no web search):** Scorecard + IPEDS + O*NET/CIP clients behind `WebResearcher`; enrich the **whole US fleet's** report-card / earnings / financial-aid / FOS-outcomes. Gate accepts deterministically; no LLM; no fabrication risk.
- **Phase 2 — Per-institution official-page discovery:** SERP source discovery → `crawler/extractor.py` grounded extraction for admissions / curriculum / faculty / class-profile / rankings; LLM-judge for reviews/editorial.
- **Phase 3 — Feeds at scale:** auto-discover + set `content_sources` per scope so the already-live daily `content_ingest` fills Updates + Events fleet-wide.

## Operating model

**Fleet discovery & prioritization.** All institutions in Postgres, joined to a **UNITID crosswalk** (Scorecard/IPEDS key); no-UNITID → manual-map queue. Prioritize by (a) profiles students actually hit (saved-school / match / page-view counts); (b) lowest conformance first (max gap-closing per unit work); (c) **parent-institution → school → program ordering** — schools inherit institution stats, programs inherit the institution photo, so never enrich a child whose parent is below threshold.

**Throughput / budget.** Phase 1 is **API-bound, ~$0 LLM**, runs the fleet in hours (Scorecard pagination, rate-limit-aware). Phase 2 is **token-bound** only for grounded extraction + judge on already-fetched pages — cap N official pages/institution, Haiku/Sonnet extract, Opus judge only for contested numeric/review fields, batch in waves of ~50–100, cache per `(source_url, STANDARD_VERSION)`.

**Gate at volume.** Every candidate flows through `gate.verify()` unchanged; `authoritative_2x` = ≥2 independent domains within 5%; rejects → `_standard.omitted{reason}`, never guessed.

**Conformance dashboard.** Per profile store `{covered, missing, omitted, last_enriched_at, standard_version}`; aggregate into a fleet view (extend the `/goal` transparency-hub pattern): % at gold per level, top missing fields, omit reasons — the single source of truth for "are we done."

**Scheduling.** Phase 1 monthly (Scorecard annual + new institutions/corrections); Phase 2 quarterly (admissions cycles / class profiles); Feeds daily (existing job). Idempotent so overlapping runs are safe.

**Failure / omit.** Source unreachable → backoff → `omitted{unreachable}`, don't block the worklist (mirror `content_ingest` fail-soft). Gate rejection → `omitted{unverified}` → dashboard manual-research candidate. No grounded value → field stays missing, never fabricated.

**`STANDARD_VERSION` → fleet re-conform.** Each profile stamps the version it conformed to; bumping `STANDARD_VERSION` marks every profile stale; the next scheduled run re-plans only the **newly-added/changed fields** (a diff via `plan()`), not the whole profile. This is how a standard edit propagates fleet-wide without a full re-crawl — and why Phase 0 (fix the manifest) gates everything.

## Bottom line / recommendation
Land Phase 0 (manifest completion + version bump) now, then build **Phase 1 (federal-API backbone)** — it raises most of the fleet with deterministic, citation-backed, zero-fabrication data and no web-search dependency. Phase 2 (official-page discovery + judge) and Phase 3 (feeds) follow. The gate already guarantees no fabrication; the work is the acquisition layer, federal-deterministic-first.
