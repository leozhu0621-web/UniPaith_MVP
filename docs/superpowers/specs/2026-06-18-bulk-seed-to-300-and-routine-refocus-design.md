# Bulk-seed to the US-News top 300 + refocus the routine on enrichment

> Design — 2026-06-18. Two coupled deliverables: (1) manually seed every U.S. News
> National Universities rank 1–300 into the platform at full treatment
> (stats + flagship programs + verified campus photos), and (2) refocus the
> `enrich-profile` routine on enrichment + repair only, dropping the growth/seeding
> responsibility (seeding is now done manually/externally).

## 1. Goal & context

The fleet is at 40 institutions. We want coverage of the **US-News National
Universities ranking 1–300** — roughly **~260 net-new** universities. Until now the
routine grew the fleet one university per run by walking the US-News list; that is
slow and the routine should instead spend its effort *deepening* profiles. So we
bulk-seed 1–300 in one focused effort and re-scope the routine to enrichment.

**The one inviolable rule still holds: never fabricate.** At 260-school scale the
defense is to make the data deterministic wherever possible and to verify the rest,
never to let an agent guess a number, a stat, or a photo credit.

## 2. Non-goals

- Not enriching the 260 to gold here — that is the routine's job afterward (full
  catalogs beyond the flagship few, reviews, feeds, deeper photos).
- Not changing the grader (`improve-enrichment`).
- Not re-running `seed_real_catalog.py` (its cleanup unpublishes non-catalog
  programs and would wipe the enricher's deepened catalogs).

## 3. Data sources (authority order)

| Field group | Source | Determinism |
|---|---|---|
| Rank | U.S. News 2025 "Best Colleges → National Universities" 1–300 | one sourced list |
| UNITID, name, city, state, ownership (public/private), enrollment, admit rate, net price, median earnings (10yr), completion (grad) rate, lat/lng | **College Scorecard bulk CSV** (`Most-Recent-Cohorts-Institution.csv`, key-free download) keyed by UNITID | fully deterministic |
| 5 flagship programs (field name + credential + CIP) | **Scorecard `Most-Recent-Cohorts-Field-of-Study.csv`** — top CIPs by completions for that UNITID | fully deterministic |
| Description | **Factual template** from verified fields: `"<Name> is a <public/private> research university in <City>, <ST>."` (same pattern as the existing seed) | deterministic |
| Campus photos | Wikimedia Commons category/search → candidate files → **Commons API `extmetadata` credit verification** (Artist + LicenseShortName) | agent-discovered, deterministically verified |

Stats and programs are **never** agent-authored. Agents are used only to *discover*
candidate Commons photo filenames; every credit is then verified by API and any
file that is not clearly free-licensed, not landscape, or not resolvable is dropped.
A university with no verifiable free campus photo ships **without** a photo (the card
falls back to its text header) — no wrong/uncredited photo ever ships.

## 4. Pipeline

1. **Ranking** — obtain the US-News National Universities 1–300 (name + rank).
2. **Match** — fuzzy-match each ranked name to a Scorecard CSV row → UNITID. Any
   ambiguous/low-confidence match is set aside for manual verification, not guessed.
   Universities already in the DB (the existing 40) are skipped.
3. **Build (deterministic)** — for each matched UNITID, assemble the institution
   record from the CSV fields + 5 top programs from the field-of-study CSV + the
   templated description. Omit any field the CSV leaves null (never impute).
4. **Photos** — a batched photo-discovery workflow (agents return candidate Commons
   filenames per university) → deterministic Commons-API credit verification →
   up to 5 `{url, credit}` per university; omit when none verify.
5. **Assemble & migrate** — write tiered batch migrations (see §5).
6. **Ship & verify** — each batch: scratch-DB validate → single alembic head →
   PR (auto-merges on green) → deploy → verify the live fleet count climbed and a
   sample renders (card photo/stats, detail page).

## 5. Migration structure

Mirror `seed12univ1`: per university create an admin `User`
(`email=admissions+<slug>@seed.unipaith.co`, `role=institution_admin`,
`is_active=true`) + `Institution` (name, type=`university`, country, city, region,
`student_body_size`, `founded_year` when known, `is_verified=true`,
`setup_complete=true`, factual `description_text`, `media_gallery=[photo0]`,
`ranking_data` {ownership_type, carnegie_classification, us_news_2025,
acceptance_rate, earnings_10yr_median, graduation_rate}, `school_outcomes`
{ownership, admit_rate, completion_rate_4yr_150pct, median_earnings_10yr,
avg_net_price, location, campus_photos[{url,credit}], media_credit, source,
source_url}) + the 5 flagship `Program` rows (published, `catalog_source=
institution_verified`). **No `_standard` stamp** — so the routine treats each as
not-yet-enriched and deepens it.

- **Batching:** ~50 universities per migration, by rank tier (e.g. 34–100, 101–150,
  …, 251–300), each with a sibling `<rev>_data.json` (dodges line-length lint on the
  embedded data). Idempotent (skip-if-name-exists); downgrade deletes the batch's
  institutions + admins + programs.
- **Required columns** (verified): `institutions`(admin_user_id, name, type,
  country); `users`(email, role, is_active); `programs`(institution_id,
  program_name, degree_type). `degree_type` is a free String. `admin_user_id` is
  unique → one admin user per institution.

## 6. Coordination (avoid dual-head churn)

The enricher + grader also ship migrations; two migrations off the same alembic head
collide into a dual head and fail the single-head deploy gate. Therefore:
- **Serialize** the seed batches — one at a time, head-sync (`alembic heads` against
  live `origin/main`) immediately before authoring each batch's `down_revision`.
- **Recommended:** the operator pauses the Cursor enricher schedule during the bulk
  seed and resumes after (I cannot pause Cursor from here — it's an external
  automation; I'll flag when to pause/resume). If it is not paused, tolerate
  occasional dual-head self-heals via a merge migration.
- The auto-merge Action will merge each green batch and dispatch the deploy.

## 7. Part 2 — refocus the routine on enrichment

Edit `enrich-profile/SKILL.md` step 2:
- **Remove the growth responsibility** — delete "add the next US-News university"
  and the US-News growth-source bullet; the routine no longer seeds.
- **Re-scope:** the routine's job is **enrichment + repair only** — take the
  seeded institution-level stubs (the 300) to gold: full program catalog (beyond the
  flagship few), reviews, feeds, deeper photos, descriptions, conformance; repair
  acute defects first (repair-first unchanged). Effort-per-run rule unchanged.
- Add a one-line pointer: "Seeding the fleet is done manually/externally (US-News
  1–300 bulk seed); do NOT add brand-new universities — deepen the seeded ones."
- The grader (`improve-enrichment`) is unchanged: it still audits + tightens rules.

## 8. Testing & verification

- Per batch: scratch-DB `alembic upgrade head` from the live head; assert the batch's
  institutions + programs exist with stats/photos; `test_alembic_has_single_head`
  passes; downgrade reverses.
- Live: fleet `total` climbs by the batch size; spot-check 2–3 cards + detail pages
  render (photo/stats/programs).
- Final: fleet `total` reaches ~300 (minus any UNITIDs that could not be matched or
  had no Scorecard row — those are reported, not faked).

## 9. Risks & mitigations

- **Name→UNITID mismatch** → verify ambiguous matches; skip unmatched (report them).
- **Fabrication** → stats/programs CSV-only; photos API-verified or omitted.
- **Thin Commons coverage at lower ranks** → fewer/zero photos for some; acceptable
  (text card; routine deepens later). Never ship a wrong photo to fill the gap.
- **Dual-head/deploy churn** → §6 serialization + optional enricher pause.
- **Scale/time** → tiered waves; report progress + live counts per tier.

## 10. Rollout

Tier-by-tier: ranking+match (once) → then per tier {build → photos → migration →
ship → verify} → finally the Part-2 routine refocus once seeding is complete (or in
parallel, since it only removes growth). Report fleet count after each tier.
