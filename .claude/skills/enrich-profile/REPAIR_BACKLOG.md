# Enrich-profile REPAIR BACKLOG

Ranked **worst-first**. The enricher MUST clear the top open entry before deepening any
other university (repair-first, SKILL.md §2). This is the ONLY file where specific
schools appear. Severity: **critical** (fabricated / cross-contaminated / scraped-debris /
near-duplicate / wrong-program content shipped live) · **high** (real data but materially
broken structure — credential-frame + ONE shared field body across credential levels /
generic encyclopedia field-definition openers / a matcher-core field null catalog-wide) ·
**medium** (institution-level seed below gold, or dead feed on an otherwise-enriched node).

Evidence is from the live API (`api.unipaith.co/api/v1`), measured this run with the
**frame-stripped shared-body scan: longest-common-substring after stripping a leading
credential frame, FAIL ≥80 chars AND (≥50% of shortest OR ≥150 chars ABSOLUTE regardless
of fraction)**, reusing `profile_standard/anti_stub.py` for consistency with the enforced CI
gate. Gold MIT (n=65) is the 0 control; the genuinely clean fleet tops out below the 150-char
absolute floor.

_Last graded: 2026-06-21 (grader **run 70** — **FULL-FLEET sweep: all 300 LIVE institutions +
all 40 catalogs (≈9,600 programs) re-measured** via the live API across every description +
structure + feed + photo + **matcher-core-field** dimension). **1 rule change** — the "Also
enrich for the MATCH" section gains a **TUITION / matcher-core-field-coverage** rule: an
institution-PUBLISHED matcher-core field (`tuition` above all) shipped null CATALOG-WIDE is
matcher STARVATION an editorially-"done" page hides, NOT an honest omission — stamp the real
published rate per credential level, omit-with-reason only for the rare unpublished program.
**HEADLINE — last run's two deploy-stranded CRITICALs are now LIVE + CLEAN:** Michigan (#1012
re-applied live) and Columbia both verify anti-stub-clean on prod this run (frame 0). The
enricher ALSO cleared UCLA 67→0 (#975/#1012) and Berkeley 64→0 (#1015), and the Notre Dame /
Dartmouth / Emory dead feeds have RECOVERED (posts 13 / 24 / 1319). **NEW systemic finding:
16 of 40 catalogs ship 0% tuition** (matcher budget-fit blind) — see entry #7. See CHANGELOG
run 70._

## Fleet at a glance (run 70, live `api.unipaith.co/api/v1`)

- **Fleet = 300 institutions LIVE.** **40 carry programs; 260 are bare institution-level stubs**
  (0 programs, dead feed, **33 with ZERO campus photo**). Seeding is **external**; the routine
  ENRICHES + REPAIRS only.
- **🟢 Cleared by the enricher + DEPLOYED since run 69 (verified live this run):** Michigan
  (#1012 — the run-69 deploy-stranded `michpercrd1` re-applied; frame 67→0) · Columbia (frame
  14→0) · UCLA (#975/#1012 — 67→0) · Berkeley (#1015 — 64→0). Dead feeds RECOVERED on Notre Dame
  (posts 13), Dartmouth (24), Emory (1319). Debris + machine-artifacts remain **0 across ALL 40
  catalogs**; 0 duplicate / bare-abbreviation / "Programs"-department on the 32 mature catalogs.
- **🔴 Un-repaired credential-FRAME + ONE shared field body across BA/MS/PhD (still LIVE):**
  UF 54 · Stanford 51 · Penn 51 · Cornell 44 · BU 23 · Notre Dame 23 (gold MIT 0). UF additionally
  opens every field with a GENERIC ENCYCLOPEDIA DEFINITION ("Anthropology is the scientific study
  of humanity…", "Economics is the social science that studies…") identical across credential
  levels — a gold-contrast STUB on top of the shared body. Entries #1–#6.
- **🔴 DILUTION evasion (frame_abs150 > 0 but reads 0 on the CI 50%-floor metric):** UF 54 · Cornell
  44 · BU 23 · JHU 3 — a long unique per-credential TAIL dilutes a still-identical 150–240-char field
  sentence below 50% of the padded body; caught only by the absolute-≥150 floor (miss #8 fraction-floor;
  the CI metric still lacks it fleet-wide — FLAG #1b).
- **🔴 COVERAGE-DRIFT survivors (CI DEFAULT frac metric flags them, but they are `CERTIFIED_CLEAN` and
  ABSENT from the frame-stripped `@parametrize` list, so CI never runs the frame metric on them):**
  Stanford 51 · Penn 51 · Notre Dame 23 — these read frame_frac=51/51/23 on the un-floored CI metric
  YET ship live (FLAG #1a). Adding them to the parametrized list would FAIL CI and force the repair.
- **🟡 NEW — matcher-core TUITION null catalog-wide (16 of 40 catalogs at 0% `tuition`):** NYU 507 ·
  UCLA 373 · Michigan 379 · UIUC 419 · UW-Seattle 360 · USC 511 · BU 396 · UT-Austin 338 (+8 of the
  5-program flagship seeds). The matcher scores budget-fit BLIND on these. Peers stamp it correctly
  (Princeton 100% · Cornell 92% · MIT 69% · Columbia 44%). New rule + entry #7.
- **🟡 Per-program "follow the {program} curriculum published on the bulletin" template stub** (passes
  the anti-stub metric — unique per row — but FAILS the gold contrast; covered by miss #8 gold-contrast,
  NOT a new rule): USC 20 rows · NYU 2 · UT-Austin 1. Low density; fold into those catalogs' depth passes.
- **Concentration-split over-decomposition (miss #2):** BU 9 ("Master of Science in Computer Science —
  Artificial Intelligence" — collapse into `tracks`). NYU/CMU "— {x}" rows are mostly legit-distinct
  (school suffix / joint-option degrees) — VERIFY before collapsing.
- **Marginal abs-150 over-counts to IGNORE (NOT stubs — distinct per-credential leads that merely repeat
  a factual SUBFIELD-ENUMERATION / department name across levels):** Georgia Tech 5 · Duke 1 · Yale 1 ·
  Chicago 1 · Northwestern 1. Mild redundancy, low priority — deepen if touched, do not prioritize.

⚠️ **FLAG FOR HUMAN (code/workflow, out of grader scope):**
1. **Two compounding gaps in the enforced anti-stub gate (`anti_stub.py` + `test_anti_stub_gate.py`,
   app/test code — not grader-editable):**
   (a) **COVERAGE drift.** `test_certified_catalog_is_anti_stub_clean` asserts only `analyze().is_clean`,
   which has NO frame-stripped metric; `frame_stripped_shared_body` is asserted by a SEPARATE test over a
   hardcoded `_FRAME_STRIPPED_CLEAN` list that DRIFTS from `CERTIFIED_CLEAN`. Make that test (and
   `scrape_debris` / `machine_artifacts`) parametrize over `CERTIFIED_CLEAN` ITSELF so the lists cannot
   drift — then Stanford/Penn/Notre Dame (frame_frac=51/51/23, all `CERTIFIED_CLEAN`) FAIL CI and
   certification means something.
   (b) **THRESHOLD undercount.** `frame_stripped_shared_body` defaults to `min_chars=80 AND min_fraction=0.5`;
   add `OR lcs >= 150` to the DEFAULT so the dilution evasion (UF/Cornell/BU/JHU) cannot read a false 0
   fleet-wide. (Only the NYU/MIT/Columbia tests pass `abs_chars=150` today.)
2. **`cip_code` is NOT serialized on `/programs/{id}` or the list endpoint** — absent on EVERY program incl.
   gold MIT, so the matcher-side "flag empty `cip_code` via public API" channel is UNUSABLE; audit via
   DB/git or expose it. A serializer gap, not necessarily a data gap. (`tuition` IS serialized — the 16
   zero-tuition catalogs in entry #7 are a real DATA gap, not a serializer gap.)
3. **`anti_stub.scrape_debris` ADDRESS tell `\bHall,\s` can FALSE-POSITIVE on researched prose naming a
   building** ("Warren Weaver Hall, at the heart of NYU's…"); anchor it to a real address context (a
   number / Suite nearby) or drop it. In `anti_stub.py`. (Debris reads 0 fleet-wide this run, so latent.)
4. **Auto-merge dual-head race (escalated runs 61–69) appears RESOLVED this interval** — last run's two
   deploy-stranded repairs (Michigan/Columbia) are now LIVE + clean, and #1013/#1014/#1017 landed cleanly.
   Keep watching: the durable fix (make `test_alembic_has_single_head` evaluate the REBASED-onto-`main`
   MERGE RESULT and BLOCK auto-merge) still lives in the automerge/CI workflow, not grader-editable.

---

# HIGH — credential-FRAME / generic field-definition + ONE shared field body across BA/MS/PhD — NOT repaired

Each: strip the per-credential frame and give EVERY credential level its OWN researched body (what THAT
degree studies at THAT level), gold MIT = 0%. **The dilution evasion (miss #8 fraction-floor):** a
"repair" that keeps one identical 150+-char field sentence and pads each credential's tail to drop it
under 50% is NOT a fix — the shared sentence must be GONE, not diluted. ALL of these are in
`CERTIFIED_CLEAN` but ABSENT from the frame-stripped `@parametrize` list (FLAG #1a) — add each to that
list (and to `scrape_debris` / `machine_artifacts`) when re-certifying, and re-measure with the
absolute-≥150 floor.

## 1. University of Florida — frame-share + GENERIC ENCYCLOPEDIA field-definition openers — severity: high — first seen run 65 · 2026-06-20
314 programs (feed fetches, posts=25 ✓). **54 fields share a body** (maxLCS 223, DILUTION — reads 0 on
the CI 50%-floor metric) AND every field opens with a generic encyclopedia DEFINITION identical across
its credential siblings ("Anthropology is the scientific study of humanity…" on the BA + Graduate
Certificate + MS; "Economics is the social science that studies…"). The definition is a gold-contrast
STUB (true of the field at every institution, derivable from the field name) — give each credential level
its OWN UF-specific researched body. Tuition 28% — backfill the rest.

## 2. Stanford University — frame-share (CI-flagged yet un-gated, FLAG #1a) — severity: high — first seen run 65 · 2026-06-20
178 programs. **51 fields share a body** (maxLCS 243) behind a per-credential frame ("Graduate study." /
"Graduate certificate study." + an identical "{Field} is the … study of …" body across the BA/MS). Reads
frame_frac=51 on the CI DEFAULT metric yet ships live (CERTIFIED_CLEAN, absent from the @parametrize list).
Per-credential researched bodies.

## 3. University of Pennsylvania — frame-share (CI-flagged yet un-gated, FLAG #1a) — severity: high — first seen run 66 · 2026-06-20
186 programs. **51 fields share a body** (maxLCS 202) behind a credential frame; frame_frac=51 on CI yet
CERTIFIED_CLEAN. Per-credential bodies. Tuition 33%.

## 4. Cornell University — DILUTION EVASION + likely-fabricated owning unit — severity: high — first seen run 64 · 2026-06-19
237 programs. The "per-credential bodies" pass DILUTED below the 50% floor (reads 0 on CI) but **44 fields
still share a body** (maxLCS 215). Residual: verify/correct **"Cornell David A. Duffield College of
Engineering"** — Cornell's college is "College of Engineering" (Duffield is a building donor; miss #8
exact-name org-chart). Fold both into one per-credential-body repair.

## 5. Boston University — DILUTION EVASION + splits + 0% tuition — severity: high — first seen run 32 · 2026-06-16
396 programs. **23 fields still share a body** (maxLCS 238, DILUTION — reads 0 on CI) behind a credential
frame + **9 concentration-split rows** ("Master of Science in Computer Science — Artificial Intelligence" —
collapse into `tracks`, miss #2) + **0% tuition** (entry #7). Per-credential bodies + tuition backfill.

## 6. University of Notre Dame — frame-share (CI-flagged yet un-gated, FLAG #1a) — severity: high — first seen run 66 · 2026-06-20
113 programs (feed RECOVERED, posts=13 ✓). **23 fields share a body** (maxLCS 263) behind a credential
frame; frame_frac=23 on the CI metric yet CERTIFIED_CLEAN. Per-credential bodies.

---

# HIGH — matcher-core field null catalog-wide (the matcher scores budget-fit BLIND) — NEW this run

## 7. The 16 zero-tuition catalogs — matcher STARVATION — severity: high — first seen run 70 · 2026-06-21
**16 of 40 enriched catalogs ship 0% `tuition`** so the CPEF matcher scores budget-fit blind on every
program: **NYU 507 · UCLA 373 · Michigan 379 · UIUC 419 · UW-Seattle 360 · USC 511 · BU 396 · UT-Austin
338** (+ the 8 flagship 5-program seeds in #9). Tuition is institution-PUBLISHED (uniform undergrad sticker /
published graduate rate), so a whole-catalog null is a SKIPPED knowable field, not an honest omission (new
rule, "Also enrich for the MATCH"). Stamp the real cited published rate per credential level on each program;
record `_standard.omitted` only for a genuinely-unpublished program (e.g. a fully-funded PhD). Several of
these (UCLA/Michigan/BU/UT-Austin) overlap the frame-share entries — fix tuition in the SAME per-credential
depth pass. Peers prove it is knowable: Princeton 100% · Cornell 92% · MIT 69% · Columbia 44%.

## 8. Johns Hopkins University — DILUTION EVASION residual — severity: high — first seen run 67 · 2026-06-20
244 programs. Reads 0 on the CI 50%-floor metric but **3 fields still share a body** under the absolute-≥150
floor (marginal, maxLCS ~159). Give those 3 fields per-credential-distinct bodies; low effort, finishes JHU.

---

# MEDIUM — dead-feed flagship seeds · institution-level seeds (seeding is external)

## 9. The flagship seeds (5 programs each) — DEAD FEED + null department + 0% tuition — severity: medium — first seen run 57 · 2026-06-18
Brown · Georgetown · UC-Davis · UC-Irvine · UNC-Chapel Hill · UVA · Vanderbilt · Washington U-St Louis each
ship 5 flagship rows with **null department**, **0% tuition**, a **DEAD FEED** (posts=0), and Brown's 5 rows
have **EMPTY descriptions**; **UC-Davis / UNC / Vanderbilt / Washington U-St Louis ship only 3 campus photos
(<4)**. **Enrich (per university, one PR):** a full real-named catalog + per-credential researched
descriptions + real departments + published tuition + a working feed + a ≥4-photo verified gallery, then
deepen toward the full real catalog.

## 10. The ~260 bulk institution-level seeds (0 programs) — severity: medium — first seen run 59/60
Each entered at institution level with **0 programs, a dead feed**, and **33 with ZERO campus photos**
(broken explore-card gradient header + detail hero — the acute sub-set to clear first; e.g. Air Force
Institute of Technology, Arizona State (Campus & Digital Immersion), Azusa Pacific, Colorado State-Fort
Collins, James Madison, Keiser-Ft Lauderdale, Loyola Marymount, Loyola-Chicago, Miami U-Oxford, Michigan
Tech, Montclair State, Oakland, Oregon State, SUNY-ESF, Sacred Heart). **Enrich (per university, one PR):**
a full real-named catalog + per-credential field-specific descriptions + real departments + published
tuition · a working feed · a ≥4-photo verified gallery · reviews on coverable programs · `_standard`. Pick
a 0-photo seed once the HIGH tier clears.

---

# CLEAN (desc + structure; no action) — verified LIVE run 70
- **Gold:** MIT (n=65, 0 on every metric, tuition 69%).
- **Cleared + DEPLOYED since run 69 (verified live this run):** Michigan (#1012 — frame 67→0; **0% tuition,
  entry #7**) · Columbia (frame 14→0, tuition 44%) · UCLA (#975/#1012 — 67→0; **0% tuition**) · Berkeley
  (#1015 — 64→0, tuition 32%). (UCLA/Michigan are description-clean but tuition-starved — see #7.)
- **Genuinely clean (per-credential-distinct bodies, frame_abs ≤ 1 marginal, no debris/artifacts):**
  Duke (1/154) · Yale (1/189) · Chicago (1/91) · Northwestern (1/125) · Rice (0/159) · Purdue (0/172) ·
  UC-San Diego (0/137) · Caltech (0/43) · Princeton (0/43, tuition 100%) · Harvard (0/279) · NYU (0/507 —
  but **0% tuition** #7 + 2 bulletin-stub rows) · UT-Austin (0/338 — **0% tuition** #7) · UIUC (0/419 —
  **0% tuition** #7) · UW-Seattle (0/360 — **0% tuition** #7) · UW-Madison (0/348) · USC (0/511 — **0%
  tuition** #7 + 20 bulletin-stub rows) · Dartmouth (0/43, feed recovered) · Emory (0/46, feed recovered) ·
  CMU (0/180 — 17 "— {x}" rows are joint/option degrees, verify) · Georgia Tech (5/143 — 5 fields share a
  SUBFIELD ENUMERATION across levels, each lead distinct; mild redundancy, not a stub).
- **Heuristic over-counts to IGNORE (not defects):** Princeton/Duke/Rice dept-echo (those ARE their real
  departments); own-unit peer-substring hits (Cornell CALS/Weill, Penn Wharton/Perelman, JHU Peabody/Whiting,
  Berkeley Lawrence-Berkeley); a trailing `(Source: …edu)` citation (GOOD sourcing); a building named in
  prose ("Warren Weaver Hall, …" — `\bHall,\s` false-flags it, FLAG #3); a shared SUBFIELD ENUMERATION /
  department name across credential levels when each lead is distinct (the abs-150 marginal over-count —
  GT/Duke/Yale/Chicago/Northwestern). Treat all as artifacts UNLESS a row names a unit / landmark / place
  the institution provably does NOT have.
