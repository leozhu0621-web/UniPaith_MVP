# Enrich-profile REPAIR BACKLOG

Ranked **worst-first**. The enricher MUST clear the top open entry before deepening any
other university (repair-first, SKILL.md §2). This is the ONLY file where specific
schools appear. Severity: **critical** (fabricated / cross-contaminated / scraped-debris /
near-duplicate / machine-broken template-slot grammar / wrong-program content shipped live) ·
**high** (real data but materially broken structure OR a matcher-core field STARVED — a whole
master's / professional tier null, a catalog-wide 0%, or a correct repair stranded un-deployed) ·
**medium** (institution-level seed below gold, or dead feed on an otherwise-enriched node).

Evidence is from the live API (`api.unipaith.co/api/v1`), measured this run with
`profile_standard/anti_stub.py` (the enforced CI gate's own functions): `analyze`,
`template_slot_artifacts`, `scrape_debris`, `machine_artifacts`, and
`frame_stripped_shared_body(..., abs_chars=150)` over the fully-paginated `/programs` list of every
program-bearing catalog, plus per-`degree_type` tuition COVERAGE **and per-`degree_type` tuition VALUE
distribution (distinct-value count + undergrad-sticker copy-down)**, plus a campus-photo count on all 300
institutions. Gold MIT (n=65) is the description 0-control — but NOT a tuition control (it ships null
cert/PhD tiers + 9 grad rows at its own undergrad sticker).

_Last graded: 2026-06-22 (grader **run 76**). **FULL-FLEET sweep: all 300 LIVE institutions + all 40
catalogs re-measured via the live API** (≈8,400 programs paginated; per-tier tuition coverage AND value
distribution; campus-photo count on all 300). **1 rule change** — the run-75 copy-down tell (`grad ==
undergrad sticker ⇒ FAIL`) was OVER-BROAD: it false-flagged Boston University's VERIFIED flat full-time
rate ($69,870 for undergrad AND general graduate, 3 cited sources, distinct MD/DMD/SSW professional rows,
funded doctorates omitted). `grad==undergrad` is now a VERIFY-trigger, a copy-down only when the
PROFESSIONAL tier / every funded doctorate carries the undergrad number (the impossible-stamp tell), never
the verified general-graduate flat rate — tightening toward no-fabrication (an unconditional fail would
force a fabricated "different" number). **HEADLINE — STRUCTURE + DESCRIPTIONS are CLEAN fleet-wide and stay
clean:** `template_slot` / `scrape_debris` / `machine_artifacts` = 0 on all 40 catalogs; 0 duplicate /
bare-abbrev / "Programs"-dept / null-dept / CIP-rollup rows on any mature catalog; only benign marginal
`frame_abs` (GT 5, Yale/Duke/Chicago/Northwestern 1) and MIT's known `name_prefixed=1`. **CLEARED since run
75:** BU copy-down (verified flat rate — false positive, NOT a defect), Cornell copy-down (#1068 → distinct
master's + funded-PhD omit), JHU graduate-tier null (#1063 → 98%). **The worst tier now is matcher tuition
STARVATION:** catalog-wide 0% (USC/NYU/UW-Seattle), the CMU deploy-strand (#1073 filled in repo, master's
1/99 live), then master's / professional-tier 0% (~14 catalogs). See CHANGELOG run 76._

## Fleet at a glance (run 76, live `api.unipaith.co/api/v1`)

- **Fleet = 300 institutions LIVE.** **40 carry programs; 260 are bare institution-level stubs**
  (0 programs, dead feed, **33 with ZERO campus photo**). Seeding is **external**; the routine
  ENRICHES + REPAIRS only.
- **🟢 STRUCTURE + DESCRIPTIONS clean fleet-wide (verified LIVE):** every mature catalog scores 0 on
  `template_slot_artifacts` / `scrape_debris` / `machine_artifacts` and on every `analyze` description
  tell; no duplicate / bare-abbreviation / "Programs"-dept / null-dept / CIP-rollup name or department on
  any mature catalog. The run-74/75 tuition HIGH tier landed (BU/Cornell value-correctness, JHU grad-tier).
- **🟢 CLEARED since run 75 (NOT defects — do not re-queue):** **Boston University** — its 154 grad rows at
  $69,870 are BU's VERIFIED flat full-time rate (3 sources; professional MD $72,626 / DMD $99,680 / SSW
  $40,352 DISTINCT; funded doctorates + per-credit certs omitted-with-reason). The run-75 "copy-down HIGH #1"
  was a FALSE POSITIVE — the new rule's class. **Cornell** (#1068 → master's distinct, PhD funded-omit, 5
  residual benign). **JHU** (#1063 → 98%).
- **🔴 catalog-wide 0% tuition (all tiers null — matcher scores budget blind on EVERY program):**
  **USC 511 · NYU 507 · UW-Seattle 360** (entry #1). Tuition is institution-PUBLISHED, so a whole-catalog
  null is a SKIPPED knowable field. Peers prove it knowable: Princeton 100% · UW-Madison 98% · JHU 98% ·
  UT-Austin 95% · UF 92%.
- **🔴 CMU DEPLOY-STRAND:** #1073 fills every program in the repo (cmutuition1), but live reads master's
  1/99 (agg 22%) — its Deploy Backend run FAILED (03:19Z, auto-merge dual-head race); fixup **#1072** was
  in_progress at grade time. Confirm it landed; if so CMU clears; if not re-trigger Deploy Backend — do NOT
  rewrite the already-correct data (§9 merge-is-not-deploy) (entry #2).
- **🔴 master's / professional-tier 0% behind a 100% bachelor's tier (matcher-blind on grad budget):** ~14
  structurally-clean catalogs (entry #3). Master's / professional publish a rate and are rarely funded →
  unambiguous starvation.
- **🟡 PhD-tier null is LARGELY LEGITIMATE (funded research doctorates → omit-with-reason) — do NOT pressure
  fabrication:** Cornell 0/74, UCLA 0/82, Berkeley 0/64, Yale 0/66, Harvard 0/25, Stanford 0/6, etc. The
  run-74 rule exempts funded PhDs. Certificate-tier nulls are similarly often legitimate (per-credit billing,
  no flat annual figure — BU omits its 24 certs with reason). Treat PhD/cert nulls as notes, NOT repair
  priority, UNLESS the institution publishes a non-waived flat rate (UT-Austin PhD 86/86 proves some do).
- **Genuine per-tier fillers to PRESERVE (DISTINCT graduate values — not copy-down):** Michigan (master's
  98/99 distinct), Stanford (master's 67/67), Berkeley (71/74), UCLA (98/146), UF + UT-Austin + JHU +
  UW-Madison (distinct flat graduate rate ≠ undergrad). **Boston University** (general-grad flat $69,870 =
  undergrad BY VERIFIED POLICY, professional distinct). Do NOT "re-uniform" or "re-distinct" these.

⚠️ **FLAG FOR HUMAN (code/workflow, out of grader scope — the grader edits only the 3 skill files):**
1. **The enforced anti-stub gate's `@parametrize` lists DRIFT from `CERTIFIED_CLEAN`** (`anti_stub.py` +
   `test_anti_stub_gate.py`): a catalog can be `CERTIFIED_CLEAN` yet ship a metric live because that metric's
   list excludes it. The durable, drift-proof fix is one change: **parametrize the template-slot / abs-floor /
   debris / artifact tests over `CERTIFIED_CLEAN` ITSELF**, and add `OR lcs >= 150` to
   `frame_stripped_shared_body`'s DEFAULT so the dilution evasion cannot read a false 0 fleet-wide. (No live
   structure breach this run — the drift is still latent.)
2. **`cip_code` is NOT serialized on `/programs/{id}` or the list endpoint** — absent on EVERY program incl.
   gold MIT (re-confirmed run 76), so the matcher-side "flag empty `cip_code` via public API" channel is
   UNUSABLE. The in-repo `PROGRAMS` carry a `cip` key, so it is a serializer gap — expose it or audit via
   DB/git. (`tuition` IS serialized — the tuition gaps are a real DATA gap.)
3. **There is NO enforced gate on tuition VALUE or COVERAGE — `anti_stub` has no tuition metric at all.** Both
   are invisible to CI (the gate is description-only). The durable fix is a `tuition_value_artifacts` metric +
   per-tier coverage in the profile test — **BUT (run-76 refinement) it must NOT fail `grad==undergrad`
   unconditionally** (that false-flags BU's verified flat rate): key the copy-down FAIL on the PROFESSIONAL
   tier carrying the undergrad number / a blanket all-grad-equal stamp, and require a per-institution
   published-rate reference. App/test code the grader does not edit.
4. **A repair PR title can OVERSTATE the live result** — verify the CLAIMED metric live PER TIER **and** for
   value-realness before declaring done (verify-rendered-output). CMU #1073 "graduate-tier tuition backfill"
   reads master's 1/99 live (deploy-strand).
5. **The auto-merge dual-head race RECURRED, badly — a CASCADE of failed deploys this interval** (JHU #1063,
   BU #1066, CMU #1073, merge #1067/#1069 all FAILED Deploy Backend; intervening successes carried JHU/BU/
   Cornell data live; #1072 fixup in_progress for CMU). The §8-step-5 class the rule already documents; the
   durable fix (single-head assertion on the MERGE RESULT, blocking auto-merge) lives in the CI/automerge
   workflow. Schedule one enricher firing per window + dedupe migration-bearing PRs before merge.

---

# HIGH — catalog-wide 0% tuition (all tiers null) — matcher scores EVERY program's budget blind — clear FIRST

## 1. The zero-tuition catalogs — matcher STARVATION — severity: high — first seen run 70 · 2026-06-21
**USC 511 · NYU 507 · UW-Seattle 360** ship 0% `tuition` on every tier (bachelor's INCLUDED — USC ba 0/153,
NYU ba 0/168, UW ba 0/114), so the CPEF matcher scores budget-fit blind on every program. Tuition is
institution-PUBLISHED (one uniform undergraduate sticker; a per-program / per-credit graduate rate for most
graduate programs), so a whole-catalog null is a SKIPPED knowable field, not an honest omission. Peers prove it
knowable: Princeton 100% · UW-Madison 98% · JHU 98% · UT-Austin 95% · UF 92%. **Fix (per university, one PR):**
stamp the published undergraduate sticker (uniform across all majors), then the published per-program /
per-credit graduate + professional rates, citing the bursar/SFS page; omit-with-reason ONLY a genuinely-funded
research PhD or a per-credit certificate with no flat annual figure. Re-measure LIVE per tier.

---

# HIGH — CMU deploy-strand (correct data, failed deploy) — drive the deploy GREEN, do NOT rewrite

## 2. Carnegie Mellon University — graduate tuition filled in repo, 1/99 master's LIVE — severity: high — first seen run 76 · 2026-06-22
180 programs. Repo #1073 (cmutuition1) fills every program with a CMU-published 2026-27 figure (funded
research doctorates stamp tuition 0 with the sticker in the note). But the LIVE API reads master's **1/99**,
PhD 0/41, agg 22% — its Deploy Backend run FAILED at 03:19Z (auto-merge dual-head race, FLAG #5), and fixup
**#1072** was in_progress at grade time. **Fix:** confirm #1072's Deploy Backend went GREEN and CMU now reads
filled live (master's ~99/99, PhD funded-omit); if not, land/reland the merge-only migration and re-trigger
Deploy Backend. The data is CORRECT — do NOT rewrite it (§9 merge-is-not-deploy; rewriting only risks a fresh
dual head). Re-measure LIVE per tier once #1072 deploys.

---

# HIGH — master's / professional-tier 0% behind a 100% bachelor's tier

## 3. The graduate-tier-null catalogs — per-credential matcher STARVATION the aggregate hides — severity: high — first seen run 74 · 2026-06-21
Structurally + description clean catalogs whose bachelor's tier is 100% but whose MASTER'S and/or PROFESSIONAL
tiers ship 0% (matcher scores graduate budget-fit BLIND). These tiers publish a per-program / per-credit rate
and are rarely funded → unambiguous starvation. **PhD nulls are EXCLUDED here (largely funded → legitimate
omit-with-reason — entry "🟡" above; do not pressure fabrication).** Worst-first by null grad rows:
- **Purdue** master's 0/68 + prof 0/2 (ba 97/97)
- **UCSD** master's 0/60 (ba 72/72)
- **Northwestern** master's 0/26 + prof 0/4 (ba 71/71)
- **Notre Dame** master's 0/24 + prof 0/1 (ba 60/60)
- **Harvard** master's 19/110 (mostly null) + cert 0/80 (cert likely per-credit — verify) (ba 64/64)
- **Penn** master's 8/66 (mostly null) + cert 0/16 (ba 55/55)
- **Yale** master's 9/38 (mostly null) + prof 0/2 + cert 0/3 (ba 80/80)
- **Columbia** master's 3/45 (mostly null) + prof 2/8 (ba 70/70)
- **GT** master's 2/55 (mostly null) + prof 0/8 (ba 41/41)
- **Chicago** master's 3/41 (mostly null) + prof 2/2 (ba 48/48)
- **Rice** master's 1/29 (mostly null) + prof 11/38 (ba 61/61)
- **Berkeley** prof 0/20 (master's 71/74 good) (ba 75/75)
- **UCLA** prof 0/4 (master's 98/146 good) (ba 141/141); **Dartmouth** master's 0/6 + prof 0/1;
  **Emory** master's 0/5 + prof 0/2
**Fix (per university, one PR):** group coverage by `degree_type`; stamp the published per-program / per-credit
rate for the null MASTER'S / PROFESSIONAL tier (these publish a rate, rarely funded). For a PhD or per-credit
certificate, record `tuition` in each program's `_standard.omitted` with a reason (funded / per-credit, no flat
annual figure) — never a silent blanket null, and never the undergrad sticker copied onto the professional tier
(the run-76 copy-down tell). Re-measure LIVE per tier.

---

# MEDIUM — flagship seeds · institution-level seeds (seeding is external)

## 4. The flagship seeds (5 programs each) — EMPTY descriptions + null department + 0% tuition + DEAD FEED — severity: medium — first seen run 57 · 2026-06-18
**Brown · Georgetown · UC-Davis · UC-Irvine · UNC-Chapel Hill · UVA · Vanderbilt · Washington U-St Louis** each
ship 5 flagship rows with **null department** and **0% tuition** and a **DEAD FEED** (posts=0). **UC-Davis / UNC
/ Vanderbilt / Washington U-St Louis ship only 3 campus photos (<4)** (Brown / Georgetown / UC-Irvine 4, UVA 5).
**Enrich (per university, one PR):** a full real-named catalog + per-credential researched descriptions + real
departments + published tuition (per credential level — the undergrad sticker uniform across majors, the
published graduate/professional rate per tier, NEVER the undergrad number copied onto the professional tier) +
a working feed + a ≥4-photo verified gallery, then deepen toward the full real catalog.

## 5. The ~260 bulk institution-level seeds (0 programs) — severity: medium — first seen run 59/60
Each entered at institution level with **0 programs, a dead feed**, and **33 with ZERO campus photos** (broken
explore-card gradient header + detail hero — the acute sub-set to clear first; e.g. Air Force Institute of
Technology, Arizona State (Campus & Digital Immersion), Azusa Pacific, Colorado State-Fort Collins, James
Madison, Keiser-Ft Lauderdale, Loyola Marymount, Loyola-Chicago, Miami U-Oxford, Michigan Tech, Montclair
State, Oakland, Oregon State, SUNY-ESF, Sacred Heart, Thomas Jefferson, U Alabama-Birmingham, U Houston, U
Kentucky, U Louisville, UMBC, U Utah, Virginia Commonwealth) plus **~54 more at 1–3 photos**. **Enrich (per
university, one PR):** a full real-named catalog + per-credential field-specific descriptions + real departments
+ published tuition · a working feed · a ≥4-photo verified gallery · reviews on coverable programs ·
`_standard`. Pick a 0-photo seed once the HIGH tier clears.

---

# CLEAN (structure + descriptions + tuition; no action) — verified LIVE run 76
- **Gold (description 0-control):** MIT (n=65, 0 on every description metric; tuition 69% — cert/PhD tiers
  null + 9 grad rows at its own undergrad sticker — MIT is NOT a tuition reference).
- **Tuition-COMPLETE (every published tier filled; PhD/cert omit-with-reason where funded/per-credit):**
  Princeton (43, 100%) · UT-Austin (338, 95% — PhD 86/86 distinct) · UW-Madison (348, 98%) · JHU (244, 98% —
  cleared run 75/76) · UF (314, 92%) · Boston University (402 — verified flat-rate, professional distinct;
  cleared this run) · Cornell (237 — distinct master's, funded-PhD omit; cleared this run).
- **Structure + description clean, master's/prof tuition filled but some tier gaps (entry #3) or PhD funded-
  omit (🟡):** Michigan (379) · Stanford (178) · UCLA (373) · Berkeley (233) · Duke (154) · UIUC (419, 79%) ·
  Caltech (43) · Dartmouth (43) · Emory (46) · Notre Dame (113) · Purdue (172) · UCSD (137) · Northwestern
  (125) · Harvard (279) · Columbia (167) · Yale (189) · Chicago (91) · GT (143) · Rice (159). **"structure
  clean" ≠ "tuition done" — many carry a master's/professional gap (entry #3).**
- **NOT tuition-clean despite structure-clean:** USC / NYU / UW-Seattle (catalog-wide 0% #1) · CMU
  (deploy-strand #2) · all of entry #3.
- **Heuristic over-counts to IGNORE (not defects):** benign marginal `frame_abs` (GT 5, Yale/Duke/Chicago/
  Northwestern 1 — distinct per-credential leads repeating a factual subfield enumeration); MIT's
  `name_prefixed=1` (a real-described row); a verified flat full-time graduate rate EQUAL to undergrad (BU
  $69,870 — confirmed by 3 sources + distinct professional rows, NOT copy-down); a genuine published flat
  academic-graduate rate DISTINCT from undergrad (UT-Austin $12,006, UF $12,740). Treat grad==undergrad as a
  defect ONLY when the PROFESSIONAL tier / every funded doctorate carries the undergrad number (run-76 rule).
