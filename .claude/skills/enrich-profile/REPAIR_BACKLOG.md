# Enrich-profile REPAIR BACKLOG

Ranked **worst-first**. The enricher MUST clear the top open entry before deepening any
other university (repair-first, SKILL.md §2). This is the ONLY file where specific
schools appear. Severity: **critical** (fabricated / cross-contaminated / scraped-debris /
near-duplicate / machine-broken template-slot grammar / **EMPTY description shipped live** /
wrong-program content shipped live, **OR a merged repair STRANDED NOT-LIVE** / the backend deploy
pipeline itself blocked) · **high** (residual fabricated NAMES on an otherwise-rich catalog,
exact-duplicate REAL rows shipped fleet-wide, OR a matcher-core field STARVED / MIS-SIGNALED — a
whole master's / professional tier null, a catalog-wide 0% `tuition` or `cip_code`, a public's
resident-rate scalar the budget veto reads too low) · **medium** (a UNIVERSAL deep field —
`who_its_for` — shipped 0% catalog-wide / type-GAMED to a degree-type template, a generic
degree-TYPE-noun ("Professional program in {field}") / CIP-title-slash / sentence-CASED name on
an otherwise-real catalog, institution-level seed below gold, or dead feed on an otherwise-enriched node).

Evidence is from the live API (`api.unipaith.co/api/v1`), measured THIS run by a direct
full-fleet crawl: all **300 LIVE institutions** fetched (campus-photo gallery length read from
`school_outcomes.campus_photos`; posts-feed count read as a LIST length — the endpoint ignores
`page_size` and returns the full list, so a 0 is a direct read; `?page_size` is capped at 50 on
`/institutions/search`, 100 on `/programs`) + the **40 program-bearing catalogs fully paginated
(8,024 programs)** run through a per-catalog description-NON-EMPTINESS scan, an exact-duplicate
`(program_name, degree_type)` scan, a name-realness scan (CIP-rollup TITLE / "…and Related
Sciences/Services" / ", General/Other" / `(CIP NN.NN)` / possessive "Bachelor's in" /
bare-abbreviation / generic "{DegreeType} program in {field}" placeholder / embedded-slash tells),
a name-CASING scan (mid-name lowercase content word), a duplicate-`description_text` scan, and a
per-`degree_type` tuition COVERAGE **and value** measure (incl. a flat-rate-vs-copy-down
discriminator). Over 20 program DETAILS/catalog (`GET /programs/{id}`, deterministic id-sorted
sample = ~800 detail fetches) I probed `cip_code` / `who_its_for` (coverage AND distinctness) /
`external_reviews` coverage. Gold MIT (n=65) is the description 0-control but is NOT a tuition,
`cip_code`, OR `who_its_for`-distinctness control (it ships null cert/PhD tiers, null `cip_code`,
AND a type-gamed `who_its_for` of 0.25 distinct).

_Last graded: 2026-06-30 (grader **run 94**). **FULL-FLEET sweep: all 300 LIVE institutions + all 40
catalogs (8,024 programs) re-measured via the live API.** **0 rule changes** — after the full-fleet
sweep every live defect maps to an EXISTING rule (compliance gap, queued + logged, NOT re-added), and
the one genuinely-NEW candidate (a master's-tier tuition COPY-DOWN — bulk master's stamped at the
undergrad sticker on USC ×135 / Harvard ×55) was **verified-and-REJECTED**: at both schools the
undergrad sticker ≈ the published STANDARD graduate rate (Harvard GSAS $55,656 vs the $57,328 sticker
= ~3% over; USC standard grad ~$71,515 vs $73,260 = ~2% over), all 55 Harvard at-sticker rows are
standard GSAS/SEAS MA/MS (NO premium professional-school master's masked), and every materially-higher
tier (USC dental $124,923, Harvard $69–79k professional master's, BU's $99,680 professional) was
INDIVIDUALLY researched as a distinct higher value. The ~2–3% delta sits below the matcher budget-bin
granularity → immaterial → no concrete live PROBLEM → no rule (anti-churn; this VALIDATES the run-93
grad==undergrad carve-out and documents WHY). **🟢 NET LIVE DELTA vs run 93 — the matcher-core tuition
picture IMPROVED:** the enricher landed **#1218 Georgetown · #1220 WashU · #1221 UC-Irvine** tuition
backfills, **verified LIVE this run** — **Georgetown master's 6/79→74/79** (73 null → 5), **UC-Irvine
master's 10/21→21/21 + prof 4/4** (FULLY cleared), **WashU master's 4/10→8/10**. The old worst case
(Georgetown 73-null) is GONE. **NEW worst tuition residual = UT-Austin professional 2/5 (3 null = 60%)
+ UVA master's 8/16 (8 null = 50%).** **🟢 EVERYTHING ELSE HELD vs run 93, no regressions:** `cip_code`
null only on gold MIT (39/40 catalogs 100% in-sample); all 15 publics still ship the NON-RESIDENT
scalar; `who_its_for` 0% on the SAME 4 (Georgia Tech · UT-Austin · Notre Dame · UW-Seattle) + type-gamed
on the SAME 9; reviews sparse on the SAME 9 (0/20); structure / descriptions (0/8,024 empty, 0 dup-desc) /
exact-dups (0) / tuition-copy-down (0 MATERIAL) / photos (program-bearing all ≥4) / feeds (all live)
all gold-clean fleet-wide; deploy pipeline healthy (3 repairs live, no programs added → once-backfilled
`program_preferences` intact). **NO critical entries remain.** See CHANGELOG run 94._

## Fleet at a glance (run 94, live `api.unipaith.co/api/v1` + `origin/main`)

- **Fleet = 300 institutions LIVE.** **40 carry programs (8,024 total); 260 are bare institution-level
  stubs** (0 programs, dead feed, **33 with ZERO campus photo**, 50 more at 1–3 photos, the rest at 4+).
  Seeding is **external**; the routine ENRICHES + REPAIRS only.
- **🟢 NO CRITICAL DEFECTS.** 0 empty/whitespace `description_text` across all 8,024 programs; 0 duplicate
  `description_text` within any catalog; 0 exact-duplicate `(program_name, degree_type)` rows on all 40
  catalogs; the FABRICATION name-realness scan returns ZERO CIP-rollup-TITLE / `(CIP NN.NN)` / "…and
  Related Sciences/Services" / ", General/Other" / possessive-mint / bare-abbreviation names (the slash
  rows are VERIFIED REAL joint/dual degrees, combined majors & gender-inclusive names — run-93 carve-out —
  except UW-Madison's CIP-title row, entry #4c); 0 MATERIAL tuition copy-downs (USC/Harvard bulk master's
  at the undergrad sticker = ~2–3% over the standard grad rate, immaterial — see header). Every
  program-bearing node carries a ≥4-photo gallery AND a live feed. Deploy pipeline healthy (single head).
- **🔴 matcher-core master's / professional-tier tuition residual (HIGH — clear FIRST):** bachelor's
  ~100% everywhere, but the MASTER'S (and some PROFESSIONAL) tier ships a material null fraction so the
  matcher scores those programs' budget BLIND. **The run-93 worst case (Georgetown 73-null) is CLEARED.**
  Worst by FRACTION now (live run 94): **UT-Austin professional 2/5 = 3 null (60%)** · **UVA master's
  8/16 = 8 null (50%)** · **Columbia professional 6/8 = 2 null (25%)** · **Georgetown professional 13/17 =
  4 null (24%) + master's 5 null residual** · **UC-Davis master's 15/19 = 4 null (21%)** · **BU
  professional 20/25 = 5 null (20%)** · **WashU master's 8/10 = 2 null (20%)** · **Dartmouth master's
  13/16 = 3 null (19%)**. Low-fraction master's residuals (≤16% null — likely legitimate funded/per-credit
  omits, re-verify before filling): USC 12/261 · UW-Seattle 14/152 · Penn 6/63 · UCSD 5/59 · Cornell 6/85 +
  prof 1 · Harvard 5/90 · NYU 5/232 · Yale 2/38 · UCLA 1 · Michigan 1 · Vanderbilt 1. **PhD nulls EXCLUDED**
  (ship `tuition=0` fleet-wide — funded convention, defensible); **certificate nulls** per-credit →
  omit-with-reason. Entry #1. Rule EXISTS (run 74) → COMPLIANCE GAP.
- **🔴 matcher-core `cip_code` — only MIT null:** `cip_code` (the CIP join key to `ref_majors` + the
  field-66 vocabulary) is NULL only on **MIT** (description control) — 65 programs scored field-blind. The
  other 39 catalogs are 100% in-sample. Entry #2. Rule EXISTS (run 82) → COMPLIANCE GAP; durable enforcement
  is FLAG #2.
- **🟢 PUBLIC resident-tuition scalar — CLEAN fleet-wide:** the CPEF budget feature reads the FLAT
  `program.tuition` scalar; all **15** publics ship the NON-RESIDENT (out-of-state) rate. No public
  mis-signal remains.
- **🟡 `who_its_for` 0% (non-null) on 4 catalogs:** Georgia Tech · UT-Austin · Notre Dame · UW-Seattle.
  Entry #3a. Rule EXISTS (run 84/86) → COMPLIANCE GAP.
- **🟡 `who_its_for` TYPE-GAMING (9 catalogs 100%-filled but program-indistinct):** a DISTINCTNESS pass
  (distinct strings / 20 sampled) shows **Berkeley 0.05 · Penn 0.05 · Caltech 0.10 · Columbia 0.10 ·
  Chicago 0.10 · Princeton 0.15 · UF 0.15 · Michigan 0.15 · MIT 0.25** collapse `who_its_for` to ~one
  template per degree-type, passing the non-null coverage gate while a CS PhD and a Public-Policy PhD read
  identically. Entry #3b. Rule EXISTS (run 89) → COMPLIANCE GAP; FLAG #4.
- **🟢 `who_its_for` FIELD-SPECIFIC (distinct/total ≈1.0) on 25 catalogs** (the model for entry #3).
- **🟡 name-realness on otherwise-real catalogs (3 catalogs):** **(a) Penn ships 2 "Professional program
  in {field}" placeholder rows** (→ real J.D. / V.M.D.). **(b) UT-Austin ships ~52 SENTENCE-CASED names**
  ("Bachelor of Arts in Art history", "… in African and African diaspora studies"). **(c) UW-Madison ships
  the CIP-title slash "Zoology/Animal Biology" on 3 rows** (cert/bachelor's/master's; CIP 26.0701; real
  degree "Zoology"). All verified-REAL-or-resolvable fields in the wrong FORM/title. Entry #4. Rules EXIST
  (placeholder run 91; casing run 90; CIP-title slash miss #2) → COMPLIANCE GAP; FLAG #3.
- **🟡 `external_reviews` sparse fleet-wide (DEPTH-pass priority — do NOT pressure fabrication):** sampled
  20/catalog — thinnest **0/20 on Brown · Georgia Tech · NYU · UC-Davis · UCSD · UF · Michigan · USC ·
  UW-Seattle**, richest Rice 10/20 · Purdue 10/20 · Princeton 9/20 · Caltech 9/20 · MIT 8/20. Coverage-gated
  (even gold MIT is 8/20) → a depth-pass priority on structurally-clean catalogs, NOT a fabrication mandate.
  Entry #5.

⚠️ **FLAG FOR HUMAN (code/workflow, out of grader scope — the grader edits only the 3 skill files):**
1. **The "deploy-safe" self-skipping data migration remains a latent cause of stranded enrichments.**
   A heavy per-program data migration wraps `<uni>_profile.apply(session)` in a `lock_timeout`-bounded
   SAVEPOINT, SKIPS the apply rather than hanging boot, yet records as applied so the chain advances —
   Deploy goes GREEN while the data may never run. No stranded enrichment this run (the 3 tuition repairs
   landed LIVE), but the mechanism is non-deterministic. Durable fix: a prod execution path that ACTUALLY
   RUNS (one-off job / management command, or a migration that retries/blocks and FAILS the deploy if it
   cannot). (carried.)
2. **`cip_code` coverage — ~100% on all mature catalogs but STILL NO enforced gate.** The fleet reached
   parity by repair, not by a gate; gold MIT remains null. Durable fix = a `cip_code` coverage metric in the
   profile test (~100% non-null per mature catalog). (carried.)
3. **The enforced anti-stub gate is DESCRIPTION-PATTERN-only — it never scans NAMES, is BLIND to EMPTY
   descriptions, AND blind to name CASING + the degree-TYPE-noun placeholder + the CIP-title slash.**
   Fabrication + empties clean this run, but UT-Austin's ~52 sentence-cased names, Penn's 2 "Professional
   program in {field}" rows, and UW-Madison's 3 "Zoology/Animal Biology" CIP-title-slash rows shipped
   undetected. Durable fix = a name-realness metric that scans NAMES for fabrication tells (CIP-rollup TITLE,
   `(CIP NN.NN)`, "…and Related", ", General/Other") AND a mid-name lowercase content word (casing) AND a
   leading degree-TYPE-noun placeholder, + a `description_text` NON-EMPTINESS assertion. **The slash sub-check
   MUST carve out a verified real JOINT/DUAL-degree ("MD/PhD"), COMBINED/DOUBLE major ("Mathematics/Economics"),
   and GENDER-INCLUSIVE ethnic-studies name ("Latina/Latino Studies") — flag ONLY a field byte-identical to a
   CIP rollup TITLE (run-93 carve-out), or it false-flags dozens of real degrees.** **The possessive-mint
   sub-metric MUST carve out a verified branded credential (GT's "Professional Master's in {field}" / PMASE) —
   key on the BARE LEADING possessive form (run-92 carve-out).** **The casing sub-check MUST carve out a
   legitimate lowercase parenthetical/abbreviation ("(online)", "(self-designed major)", "(7-year)",
   "(w/Const Mgmt)", branded "(iMBA)") and a foreign proper name ("Institut d'Etudes") — these are NOT casing
   defects; flag a sentence-cased FIELD word, not a parenthetical (run-94 note).** (carried + extended.)
4. **No `who_its_for` distinctness / hard-null regression gate.** The coverage metric asserts NON-NULL only —
   which TYPE-GAMING passes (every program one template). The metric must assert DISTINCTNESS (distinct
   `who_its_for` strings / programs ≈ 1.0, FAIL well under ~0.5) AND a lint/grep gate must FAIL on a literal
   `p.<coverable_field> = None` in an `apply()` loop. App/test code. (carried.)
5. **The catalog build dedups on `slug`, not the rendered `(program_name, degree_type)`, and
   `_catalog_errors` never asserts name uniqueness.** Clean this run (0 dups). Durable fix: dedup the build
   UNION on `(program_name, degree_type)` + a uniqueness assertion in `test_anti_stub_gate.py`. (carried.)
6. **The CPEF budget feature is RESIDENCY-BLIND:** `matching.py` reads the single `program.tuition` scalar
   with no in-state/out-of-state branch on the student's residency. The non-resident-scalar default (all 15
   publics) is the stopgap; the durable fix is residency-aware matching reading `tuition_in_state` vs
   `tuition_out_of_state` by the student's residency/country. (carried.)
7. **No enforced gate on tuition VALUE or COVERAGE.** Durable fix = a `tuition_value_artifacts` metric +
   per-tier coverage; key the copy-down FAIL on a grad/professional row at the flat undergrad sticker ONLY
   when that school **publishes a distinct higher rate AND already ships a higher row on that same catalog**
   (the internal-inconsistency tell) — must NOT fail `grad==undergrad` unconditionally (false-flags BU/MIT's
   verified flat rate AND false-flags USC/Harvard, whose undergrad sticker ≈ the standard grad rate within
   ~3% — run-94 verified-immaterial). A master's/professional COVERAGE sub-check (FAIL a whole
   master's/professional tier shipped >20% null beside a filled peer) makes entry #1 durable, while EXCLUDING
   PhD (ships `tuition=0` funded convention) + per-credit certificate tiers. (carried + refined run 94.)
8. **The `test_alembic_has_single_head` gate asserts single-head on the PR branch, not the post-merge
   `origin/main` result.** Single head clean this run. Durable fix: assert single-head on the rebased merge
   result / `origin/main` POST-MERGE. (carried, lower priority.)
9. **A durable feed-staleness alert is still worth adding** — flag a node whose `content_sources` is set but
   whose post count stays 0 for N days post-ship. No node currently stranded. (carried, low priority.)

---

# HIGH — matcher-core master's / professional-tier tuition residual (clear FIRST — highest matcher leverage)

## 1. UT-Austin · UVA · Columbia · Georgetown(prof) · UC-Davis · BU(prof) · WashU · Dartmouth — partial master's/professional tuition null — severity: high — first seen run 74 — 2026-06-30
Structurally + description clean catalogs whose bachelor's tier is ~100% but whose MASTER'S (and some
PROFESSIONAL) tier ships a material null fraction (the matcher scores those graduate programs' budget-fit
BLIND). **The run-93 dominant case (Georgetown master's 73-null) + UC-Irvine + WashU are CLEARED LIVE this
run** (#1218 / #1221 / #1220 — Georgetown master's now 74/79, UC-Irvine 21/21 + prof 4/4, WashU 8/10).
Worst by null FRACTION now (live run 94): **UT-Austin professional 2/5 = 3 null (60%, professional publishes
a rate → FAIL)** · **UVA master's 8/16 = 8 null (50%)** · **Columbia professional 6/8 = 2 null (25%)** ·
**Georgetown professional 13/17 = 4 null (24%) + master's 5 null residual** · **UC-Davis master's 15/19 =
4 null (21%)** · **BU professional 20/25 = 5 null (20%)** · **WashU master's 8/10 = 2 null (20%)** ·
**Dartmouth master's 13/16 = 3 null (19%)**. **Fix (per university):** group coverage by `degree_type`;
stamp the published per-program / per-credit rate for the null MASTER'S / PROFESSIONAL tier (these publish a
rate, rarely funded). For a PhD or per-credit certificate, record `tuition` in `_standard.omitted` with a
reason — never a silent blanket null, and never the undergrad sticker copied onto a professional school that
bills its own higher rate. **PhD nulls EXCLUDED** (ship `tuition=0` fleet-wide — funded convention);
certificate per-credit → omit-with-reason. Low-fraction (≤16% null) master's residuals on USC · UW-Seattle ·
Penn · UCSD · Cornell · Harvard · NYU · Yale · UCLA · Michigan · Vanderbilt are likely legitimate per-program
funded/per-credit omits — re-verify each before filling, never fabricate. Re-measure LIVE per tier. Rule
EXISTS (run 74) → compliance/repair. Durable enforcement = FLAG #7.

---

# HIGH — matcher-core `cip_code` (lone residual)

## 2. MIT — the last catalog shipping `cip_code` null — severity: high — first seen run 82 — 2026-06-30
`cip_code` is the CIP join key the CPEF matcher uses to resolve a program's field to `ref_majors` + the
field-66 vocabulary. NULL remains only on **MIT** — 65 programs scored field-blind (the other 39 catalogs are
100% in-sample). **Fix:** stamp `p.cip_code = spec.get("cip")` (the IPEDS CIP already used for the breadth
cross-check), exactly as the 39 other catalogs do — never a guess, omit-with-reason only for a genuinely
uncodeable program. MIT is the DESCRIPTION 0-control, NOT a `cip_code` reference — its null must be repaired,
not imitated. Re-measure LIVE to ~100%. Rule EXISTS (run 82) → compliance/repair. Durable enforcement = FLAG #2.

---

# MEDIUM — `who_its_for` (0% + type-gamed) · name realness (placeholder + casing + CIP-title slash) · reviews · bulk seeds

## 3. `who_its_for` — 4 catalogs 0% (un-done) AND 9 catalogs TYPE-GAMED (coverage-passing, indistinct) — severity: medium — first seen run 84 (0%) / run 89 (type-gaming) — 2026-06-30
`who_its_for` ("Who it's for", a manifest field) is derivable for EVERY program from its own published
audience/fit material, so both failure modes below are un-done depth, not honest omission.
**(a) 0% (non-null) on 4 catalogs** — Georgia Tech · UT-Austin · Notre Dame · UW-Seattle.
**(b) TYPE-GAMED on 9 catalogs (100% non-null but ONE degree-type template per tier)** — Berkeley 0.05 · Penn
0.05 · Caltech 0.10 · Columbia 0.10 · Chicago 0.10 · Princeton 0.15 · UF 0.15 · Michigan 0.15 · MIT 0.25
(distinct strings / 20 sampled).
**Fix (per catalog, in the SAME pass as tuition):** build a `_WHO_BY_SLUG` dict of field-specific 1–2 sentence
statements (subject, methods, who it fits, next step) — the bar the 25 field-specific catalogs already meet
(distinct/total ≈1.0). The `_WHO_BY_TYPE` fallback is a narrow last resort, never the primary fill; never
`= None`. Re-measure LIVE for BOTH coverage (~100%) AND distinctness (≈1.0). Rule EXISTS run 84/86 (0%) + run
89 (distinctness) → compliance/repair. Durable enforcement = FLAG #4.

## 4. Name-realness on otherwise-real catalogs — (a) Penn degree-TYPE-noun placeholder · (b) UT-Austin sentence-casing · (c) UW-Madison CIP-title slash — severity: medium — first seen run 91 (placeholder) / run 90 (casing) / run 93 (CIP-title slash) — 2026-06-30
**(a) Penn degree-TYPE-noun placeholder NAMES (2 rows).** Penn ships "Professional program in Law" +
"Professional program in Veterinary Medicine" — the `degree_type` value ("professional") title-cased AS the
program name in place of Penn's published conferred designation. **Fix:** resolve each to the real conferred
designation — Penn "Professional program in Law" → "Juris Doctor (J.D.)", Penn "Professional program in
Veterinary Medicine" → "Veterinary Medical Doctor (V.M.D.)" — verify each against Penn's catalog; never the
degree_type label, never invent a degree. Baked into `penn_profile.py`. Re-measure LIVE: 0 "{DegreeType}
program in {field}" names. Rule EXISTS (run 91) → compliance/repair. **NOTE — Georgia Tech's 3 "Professional
Master's in {field}" rows are VERIFIED REAL (PMASE etc.), NOT this defect; do NOT "resolve" them (run-92
carve-out).**
**(b) UT-Austin sentence-casing (~52/338, un-repaired since run 90).** Bachelor's rows ship the field part
SENTENCE-CASED — "Bachelor of Arts in Art history", "… in African and African diaspora studies", "… in Asian
cultures and languages", "… in Classical languages", "… in Behavioral and social data science". Verified-REAL
degrees in the WRONG CASE — the form the student reads on the explore card + detail page. **Fix:** re-case
every `program_name` (and any matching `department`) to UT-Austin's PUBLISHED title-case ("Bachelor of Arts in
Art History"), PRESERVING legitimate lowercase (parentheticals, post-positives, acronyms) — only its
capitalization, never a word. Baked into `ut_austin_profile.py`. Re-measure LIVE: 0 mid-name lowercase content
words. Rule EXISTS (run 90) → compliance/repair. Durable enforcement = FLAG #3. **NOTE — a lowercase
PARENTHETICAL/abbreviation ("(online)", "(self-designed major)", "(7-year)", "(w/Const Mgmt)", "(iMBA)") and a
foreign proper name ("Institut d'Etudes") are NOT casing defects — Duke/NYU/UCLA/UIUC/UW-Seattle's handful are
false positives; do NOT "fix" them (run-94 note).**
**(c) UW-Madison CIP-title slash "Zoology/Animal Biology" (3 rows: cert/bachelor's/master's).** Byte-
identical to federal CIP 26.0701 "Zoology/Animal Biology", minted across three award levels of one field (the
IPEDS×award-level fingerprint); UW-Madison's real degree is "Zoology" (Department of Integrative Biology).
**Fix:** resolve the field to the real published degree name ("Bachelor of Science in Zoology", "Master of
Science in Zoology", "Graduate Certificate in Zoology") — never the CIP title. Baked into the UW-Madison
profile module. Re-measure LIVE: 0 CIP-rollup-title slashes. Rule EXISTS (miss #2 CIP-title) → compliance/repair.
**NOTE — the BU/NYU/UCLA/Duke/Cornell slash rows (MD/PhD, JD/LLM, B.A./M.S. combined, Mathematics/Economics),
the Latina/o & Chicana/o majors across ≥6 catalogs, UC-Davis "Middle East/South Asia Studies", UCI
"Biology/Education", and Northwestern/UW-Madison "Radio/Television/Film" (real RTVF/Comm-Arts unit) are VERIFIED
REAL joint/dual/combined/inclusive/cross-listed degrees, NOT this defect; do NOT "resolve" them (run-93
carve-out). Only a slash byte-identical to a federal CIP rollup TITLE fails.**

## 5. `external_reviews` depth pass on the (structurally-clean) mature catalogs — severity: medium — first seen run 65 — 2026-06-30
Structure is clean fleet-wide, so the miss-#8 STRUCTURE-BEFORE-DEPTH order unblocks the reviews depth pass.
Sampled 20/catalog: 0/20 on Brown · Georgia Tech · NYU · UC-Davis · UCSD · UF · Michigan · USC · UW-Seattle;
richest Rice 10/20 · Purdue 10/20 · Princeton 9/20 · Caltech 9/20 · MIT 8/20. **Calibrate — reviews are
coverage-gated; do NOT fabricate (even gold MIT is 8/20).** **Enrich:** on a structurally-clean catalog, run
the reviews depth pass over programs WITH real third-party coverage (Poets&Quants / U.S. News / GradReports /
program outcomes reports) — program-specific summary + themes + resolvable sources, no synthesized-from-metadata
reviews (miss #8) — and record `external_reviews` in `_standard.omitted` with a reason where a program genuinely
has no coverage.

## 6. The ~254 bulk institution-level seeds (0 programs) — severity: medium — first seen run 59/60
Each entered at institution level with **0 programs, a dead feed**, and **33 with ZERO campus photos**
(broken explore-card gradient header + detail hero — the acute sub-set to clear first), plus 50 more at 1–3
photos. **Enrich (per university — after the HIGH tier clears):** a full real-named, TITLE-CASED catalog with
**field-specific `description_text` on every program** + the real conferred degree designation (never
"{DegreeType} program in {field}", never a CIP-title slash) + PROGRAM-DISTINCT `who_its_for` (never a
degree-type template, never `= None`) + real departments + published tuition (non-resident scalar for publics;
the master's/professional tier filled, not just bachelor's) + `cip_code` · a working feed · a ≥4-photo verified
gallery · reviews on coverable programs · `_standard`. Pick a 0-photo seed once the higher tiers clear.

---

# CLEAN (structure + descriptions(pattern + NON-EMPTINESS + no-dup) + names(fabrication) + tuition-value-copy-down + exact-dup + photos + feeds + public-scalar + cip_code(39/40) + deploy; no action) — verified LIVE run 94
- **Gold (description 0-control):** MIT (n=65, real "Science, Technology, and Society" major; but type-gamed
  `who_its_for` 0.25 + null cert/PhD tiers + null `cip_code` — MIT is a description control ONLY, not a
  tuition / `cip_code` / who-distinctness reference; its `cip_code` null is entry #2, not a model).
- **CLEARED LIVE this run (matcher-core tuition):** Georgetown master's (73 null → 5; #1218) · UC-Irvine
  master's 21/21 + prof 4/4 (fully; #1221) · WashU master's 8/10 (#1220) — verified live by direct crawl.
- **`cip_code`-COMPLETE (39 of 40, the model for entry #2):** every mature catalog EXCEPT MIT (100% in-sample).
- **`who_its_for` FIELD-SPECIFIC (the distinctness model for entry #3b — distinct/total ≈1.0, 25 catalogs):**
  Brown · Emory · Purdue · Dartmouth · Georgetown · Vanderbilt · UC-Davis · UCLA · UC-Irvine · UNC · UVA ·
  WashU · Rice · UIUC · UW-Madison · CMU · Duke · JHU · Northwestern · BU · NYU · USC · UCSD · Stanford · Yale.
- **PUBLIC non-resident scalar CORRECT (all 15):** Georgia Tech · UT-Austin · Berkeley · UCLA · UC-Davis ·
  UC-Irvine · UCSD · UNC · UVA · UW-Seattle · Michigan · Purdue · UF · UIUC · UW-Madison.
- **TUITION COPY-DOWN — 0 MATERIAL fleet-wide (run-94 verified):** BU/MIT/Princeton bill a verified flat
  rate (premium exceptions correctly captured); USC's 135 + Harvard's 55 bulk master's at the undergrad
  sticker are within ~2–3% of the published STANDARD grad rate (Harvard GSAS $55,656; USC ~$71,515) with NO
  premium professional-school master's masked (those were individually researched) → below matcher budget-bin
  granularity → not a defect. PhD `tuition=0` is a defensible funded convention, uniform fleet-wide.
- **EXACT-DUPLICATE / DUP-DESC / NAME-FABRICATION / EMPTY-DESC / PHOTO / FEED classes CLEAN fleet-wide:**
  0 raw `(program_name, degree_type)` repeats, 0 duplicate `description_text`, 0 fabricated names (slash rows
  VERIFIED REAL except UW-Madison's 3 CIP-title rows in entry #4c), 0 empty descriptions (0/8,024), every
  program-bearing node ≥4 campus photos AND a live feed.
- **DEPLOY PIPELINE HEALTHY:** single head, migrations applying in prod; 3 tuition repairs landed LIVE this
  window with no programs added (once-backfilled `program_preferences` intact).
