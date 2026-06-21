# Enrich-profile REPAIR BACKLOG

Ranked **worst-first**. The enricher MUST clear the top open entry before deepening any
other university (repair-first, SKILL.md §2). This is the ONLY file where specific
schools appear. Severity: **critical** (fabricated / cross-contaminated / scraped-debris /
near-duplicate / **machine-broken template-slot grammar** / wrong-program content shipped live) ·
**high** (real data but materially broken structure — credential-frame + ONE shared field body
across credential levels / a matcher-core field null catalog-wide / a correct repair stranded
un-deployed) · **medium** (institution-level seed below gold, or dead feed on an otherwise-enriched
node).

Evidence is from the live API (`api.unipaith.co/api/v1`), measured this run with
`profile_standard/anti_stub.py` (the enforced CI gate's own functions): `analyze`,
`template_slot_artifacts`, `scrape_debris`, `machine_artifacts`, and
`frame_stripped_shared_body(..., abs_chars=150)`. A **REPO-vs-LIVE diff** ran the same functions
over each in-repo `*_profile.PROGRAMS` (modules are importable here) — the only way to tell a real
repo defect from a deploy-stranded repair. Gold MIT (n=65) is the 0 control.

_Last graded: 2026-06-21 (grader **run 72**). **FULL-FLEET sweep: all 300 LIVE institutions + all 40
catalogs re-measured via the live API, PLUS the repo-vs-live diff.** **1 rule change** — miss #9's
template-slot sub-bullet NOTE was STALE ("the gate has no metric yet — run it by hand"): #1025 ADDED
`template_slot_artifacts` + a parametrized test, so the note now corrects to: a frame-share /
per-credential repair is NOT a clear until `template_slot_artifacts == 0`, and PARKING a still-broken
catalog in the gate's `_TEMPLATE_SLOT_CLEAN` EXCLUSION set (while it stays in `CERTIFIED_CLEAN`) ships
template-slot grammar live under a "certified clean" banner — exclusion is a parking lot, never a
destination. **HEADLINE — the run-71 critical pair FLIPPED: Berkeley (was C1) is now LIVE-CLEAN
(template-slot 107→0, deployed), UCLA (was C2) is repo-fixed (#1027) with its Deploy Backend IN
PROGRESS. The NEW worst-case is STANFORD: its #1021 "per-credential bodies" repair cleared 51
frame-share fields → 0 but MANUFACTURED 51 template-slot machine-grammar rows, REPO-confirmed and LIVE
(Stanford is parked in the gate's exclusion set, so they shipped under CERTIFIED_CLEAN).** **WINS verified
live:** UF (run-71 #1 — frame 54→0 + tuition 28%→92%, DEPLOYED) · Berkeley (template-slot 107→0) ·
Stanford tuition (33%→69%, #1020). **STILL OPEN:** Penn 51 / Cornell 44 / Notre Dame 23 / BU 23
frame-share (repo+live); JHU 3 (deploy-stranded, #984 cancelled & not caught up); 16 zero-tuition
catalogs; UT-Austin 3 + Michigan 1 template-slot (repo). See CHANGELOG run 72._

## Fleet at a glance (run 72, live `api.unipaith.co/api/v1` + repo diff)

- **Fleet = 300 institutions LIVE.** **40 carry programs; 260 are bare institution-level stubs**
  (0 programs, dead feed, ~33 with ZERO campus photo). Seeding is **external**; the routine
  ENRICHES + REPAIRS only.
- **🔴 WORST — template-slot MACHINE-BROKEN GRAMMAR shipped LIVE (miss #9 template-slot sub-bullet):**
  **Stanford 51** (REPO+LIVE — the #1021 regression, NEW), UCLA 13 (repo-fixed #1027, deploy in
  progress — verify), UT-Austin 3 (repo+live), Michigan 1 (repo+live). All four are in `CERTIFIED_CLEAN`
  but EXCLUDED from the gate's `_TEMPLATE_SLOT_CLEAN`, so CI never fails them — they ship live (FLAG #1a).
- **🟢 Cleared + verified LIVE since run 71:** **Berkeley** (template-slot 107→0; was run-71 C1) ·
  **UF** (frame 54→0 + generic-definition openers gone + tuition 28%→92%; was run-71 HIGH #1, deploy
  landed) · **Stanford tuition** 33%→69% (#1020). Debris + machine-artifacts remain **0 across ALL 40
  catalogs**; 0 duplicate / bare-abbreviation / "Programs"-department on the mature catalogs.
- **🔴 Un-repaired credential-FRAME + ONE shared field body across BA/MS/PhD (frame_abs150 > 0, LIVE+REPO):**
  Penn 51 · Cornell 44 · Notre Dame 23 · Boston U 23 (gold MIT 0). Penn/Notre Dame read frame_frac>0 on the
  CI DEFAULT metric YET ship live (CERTIFIED_CLEAN, absent from the abs-floor `@parametrize` list, FLAG #1a/#1b);
  Cornell/BU read 0 on the fraction-only CI metric (DILUTION evasion) and are caught only by the absolute-≥150
  floor (FLAG #1b).
- **🟡 matcher-core TUITION null catalog-wide (16 of 40 catalogs at 0% `tuition` LIVE):** NYU 507 · UIUC 419 ·
  USC 511 · UW-Seattle 360 · UT-Austin 338 · Michigan 379 · BU 396 · UCLA 373 (pending #1027 deploy) + the 8
  flagship 5-program seeds. The matcher scores budget-fit BLIND on these. Tuition is set in `apply()` by
  credential level (NOT in the `PROGRAMS` dict — repo-side tuition reads 0 for everyone and is meaningless;
  the LIVE API is the sole truth). Peers prove it is knowable: Princeton 100% · Cornell 92% · UF 92% · MIT 69%.
- **Per-program "follow the {program} curriculum published on the bulletin" template stub** (unique per row so
  it passes anti-stub, but FAILS the gold contrast — miss #8, NOT a new rule): USC ~20 · NYU 2 · UT-Austin 1.
  Low density; fold into those catalogs' depth passes.
- **Concentration-split over-decomposition (miss #2):** BU 9 ("Master of Science in Computer Science — Artificial
  Intelligence" — collapse into `tracks`). CMU/NYU "— {x}" rows are mostly legit (joint/option degrees) — VERIFY
  before collapsing.
- **Marginal abs-150 over-counts to IGNORE (NOT stubs — distinct per-credential leads that merely repeat a factual
  SUBFIELD-ENUMERATION / department name across levels):** Georgia Tech 5 · Duke 1 · Yale 1 · Chicago 1 ·
  Northwestern 1. Mild redundancy, low priority.

⚠️ **FLAG FOR HUMAN (code/workflow, out of grader scope — the grader edits only the 3 skill files):**
1. **The enforced anti-stub gate has THREE compounding coverage/threshold gaps (`anti_stub.py` +
   `test_anti_stub_gate.py`):**
   (a) **`_TEMPLATE_SLOT_CLEAN` is a SUBSET of `CERTIFIED_CLEAN`** (excludes stanford/ucla/ut_austin/michigan),
   so a catalog can be `CERTIFIED_CLEAN` AND ship template-slot grammar live. Once those four clear, parametrize
   `test_certified_catalog_has_no_template_slot_grammar` over `CERTIFIED_CLEAN` ITSELF so the lists cannot drift.
   (b) **`_ABS_FLOOR_CLEAN` / `_FRAME_STRIPPED_CLEAN` DRIFT from `CERTIFIED_CLEAN`** — Penn / Cornell / Notre Dame /
   BU are `CERTIFIED_CLEAN` but ABSENT from the abs-floor list, so CI never runs `frame_stripped_shared_body(abs_chars=150)`
   on them and they ship frame-share live. Parametrize the abs-floor test over `CERTIFIED_CLEAN` too.
   (c) **THRESHOLD undercount:** `frame_stripped_shared_body` defaults to `min_chars=80 AND min_fraction=0.5`; add
   `OR lcs >= 150` to the DEFAULT so the dilution evasion (Cornell/BU) cannot read a false 0 fleet-wide.
2. **`cip_code` is NOT serialized on `/programs/{id}` or the list endpoint** — absent on EVERY program incl. gold
   MIT, so the matcher-side "flag empty `cip_code` via public API" channel is UNUSABLE. The in-repo `PROGRAMS`
   carry a `cip` key, so it is a serializer gap, not necessarily a data gap — expose it or audit via DB/git.
   (`tuition` IS serialized — the 16 zero-tuition catalogs in entry #7 are a real DATA gap.)
3. **`anti_stub.scrape_debris` ADDRESS tell can FALSE-POSITIVE on researched prose naming a building**
   ("Warren Weaver Hall, at the heart of NYU's…"); anchor it to a real address context or drop it. Debris reads
   0 fleet-wide this run, so latent.
4. **Deploy reliability — NOT resolved.** The LATEST `Deploy Backend` (Berkeley #1025, 11:35Z) **FAILED**; #1026
   (Berkeley) was **CANCELLED**; UCLA #1027's deploy is **IN PROGRESS** (11:51Z) — UCLA's template-slot + tuition
   fix is pending it. **JHU #984** was CANCELLED and, unlike Michigan/Columbia (which self-healed), NO later deploy
   caught it up, so prod permanently serves the old 3 shared-body fields — the non-self-healing stranding from run
   71 FLAG #4 (a deploy cancelled mid-migration leaves the alembic revision marked-applied while its data write
   never completed, so every later deploy SKIPS it; a fresh fixup migration or re-stamp+re-run is then required).
   Durable fixes (deploys QUEUE instead of cancel; data-write migrations re-assert rows idempotently) live in the
   workflow — not grader-editable.

---

# CRITICAL — machine-broken template-slot grammar shipped LIVE — clear FIRST

These render visibly broken machine prose a student reads. They cleared the shared-body count, so they
read CLEAN on `analyze` + `frame_stripped` and a prior grader scored them as wins — but the per-credential
"repair" SLOTTED a field phrase into a fixed template (miss #9 template-slot sub-bullet). REPO-confirmed
(`template_slot_artifacts` over the in-repo `PROGRAMS`), so the fix is to REWRITE each row as researched
per-credential prose — not a deploy.

## 1. Stanford University — template-slot machine-broken grammar (the #1021 regression) — severity: critical — first seen run 72 · 2026-06-21
178 programs. `#1021` "per-credential description bodies" cleared the 51 frame-share fields (frame_abs150 51→0)
but MANUFACTURED **51 `template_slot_artifacts` rows**, REPO-confirmed and LIVE (Stanford is in `CERTIFIED_CLEAN`
but EXCLUDED from `_TEMPLATE_SLOT_CLEAN`, so the gate never failed it). Every one is the fixed template
"Graduate coursework in **the Master of Science in {field}** emphasizes {field-blurb}, with seminars, methods
training, and a culminating thesis or capstone through {School}." — the credential is DOUBLED, a field blurb is
slotted (sometimes broken: "…emphasizes Chemical engineering applies chemistry, physics, with seminars…"), and a
UNIVERSAL field-agnostic tail is appended to every row. Rewrite each credential level as RESEARCHED prose about
what THAT degree studies at THAT level (gold MIT 0); re-scan the WHOLE catalog → `template_slot_artifacts == 0`
AND `frame_stripped(abs_chars=150) == 0`, then GRADUATE Stanford into `_TEMPLATE_SLOT_CLEAN` (do not leave it
parked).

## 2. University of California-Los Angeles — template-slot + 0% tuition — DEPLOY IN PROGRESS (verify) — severity: critical — first seen run 71 · 2026-06-21
373 programs. The in-repo `ucla` `PROGRAMS` are FIXED (`template_slot_artifacts == 0`, tuition backfilled by #1027),
but prod still serves **13 template-slot rows** ("The Doctor of Philosophy in Anthropology at UCLA advances original
research **in for** students interested in an anthropological understanding of **human**.") and **0% tuition**. `#1027`'s
`Deploy Backend` is IN PROGRESS — **DO NOT rewrite; DRIVE/VERIFY THE DEPLOY** (§9), then re-query live for 0
template-slot + non-zero tuition. If #1027's deploy FAILS (the prior Deploy Backend #1025 failed), it is stranded —
a fresh fixup migration is then needed (FLAG #4).

## 3. The University of Texas at Austin — 3 template-slot rows + 0% tuition — severity: critical — first seen run 71 · 2026-06-21
338 programs. REPO+LIVE carry **3 `template_slot_artifacts` rows** where a PhD row slotted a *different credential's*
description into "research in ___": "Doctoral study in Anthropology at UT Austin advances original research in **The
Bachelor of Arts in Anthropology at UT Austin introduces the four**, supported by…" (also History, Computer Science).
Rewrite those 3 PhD rows as researched doctoral prose; re-scan → 0; graduate into `_TEMPLATE_SLOT_CLEAN`. Also 0%
tuition (entry #7) — fix in the same pass.

## 4. University of Michigan-Ann Arbor — 1 template-slot row + 0% tuition — severity: critical — first seen run 71 · 2026-06-21
379 programs (description-clean otherwise). REPO+LIVE carry **1 `template_slot_artifacts` row**: "The Doctor of
Philosophy in Industrial and Operations Engineering at the University of Michigan advances original research **in ,**
analyzes, and improves complex systems…" (empty slot → dangling "research in ,"). Rewrite that one PhD row; re-scan →
0; graduate into `_TEMPLATE_SLOT_CLEAN`. Also 0% tuition (entry #7).

---

# HIGH — credential-FRAME + ONE shared field body across BA/MS/PhD — NOT repaired (LIVE+REPO)

Each: strip the per-credential frame and give EVERY credential level its OWN researched body (what THAT degree
studies at THAT level), gold MIT = 0%. The dilution evasion (miss #8 fraction-floor): a "repair" that keeps one
identical 150+-char field sentence and pads each credential's tail to drop it under 50% is NOT a fix — the shared
sentence must be GONE, not diluted. ALL of these are in `CERTIFIED_CLEAN` but ABSENT from the abs-floor
`@parametrize` list (FLAG #1a/#1b) — add each when re-certifying and re-measure with the absolute-≥150 floor. And
the SAME pass must take `template_slot_artifacts` → 0 (do not trade frame-share for template-slot — entry #1's lesson).

## 5. University of Pennsylvania — frame-share (CI-flagged yet un-gated) — severity: high — first seen run 66 · 2026-06-20
186 programs. **51 fields share a body** (frame_abs150=51, frame_frac=51) behind a per-credential frame. Reads
frame_frac=51 on the CI DEFAULT metric yet ships live (CERTIFIED_CLEAN, absent from the abs-floor list). Per-credential
researched bodies. Tuition 34%.

## 6. Cornell University — DILUTION EVASION + verify owning unit — severity: high — first seen run 64 · 2026-06-19
237 programs (tuition 92% ✓). The "per-credential bodies" pass DILUTED below the 50% floor (frame_frac=0 on CI) but
**44 fields still share a body** (frame_abs150=44). Residual: verify/correct **"Cornell David A. Duffield College of
Engineering"** — Cornell's college is "College of Engineering" (Duffield is a building donor; miss #8 exact-name
org-chart). Fold both into one per-credential-body repair.

## 7. University of Notre Dame — frame-share (CI-flagged yet un-gated) — severity: high — first seen run 66 · 2026-06-20
113 programs (feed fetches, posts=13 ✓). **23 fields share a body** (frame_abs150=23, frame_frac=23) behind a credential
frame; frame_frac=23 on the CI metric yet CERTIFIED_CLEAN. Per-credential researched bodies.

## 8. Boston University — DILUTION EVASION + splits + 0% tuition — severity: high — first seen run 32 · 2026-06-16
396 programs. **23 fields still share a body** (frame_abs150=23, DILUTION — frame_frac=0 on CI) behind a credential frame
+ **9 concentration-split rows** ("Master of Science in Computer Science — Artificial Intelligence" — collapse into
`tracks`, miss #2) + **0% tuition** (entry #7). Per-credential bodies + collapse splits + tuition backfill.

---

# HIGH — matcher-core field null catalog-wide (the matcher scores budget-fit BLIND)

## 9. The 16 zero-tuition catalogs — matcher STARVATION — severity: high — first seen run 70 · 2026-06-21
**16 of 40 enriched catalogs ship 0% `tuition`** so the CPEF matcher scores budget-fit blind on every program:
**NYU 507 · UIUC 419 · USC 511 · UW-Seattle 360 · UT-Austin 338 · Michigan 379 · BU 396 · UCLA 373** (UCLA pending
#1027 deploy) + the **8 flagship 5-program seeds** (entry #11). Tuition is institution-PUBLISHED (uniform undergrad
sticker / published graduate rate), so a whole-catalog null is a SKIPPED knowable field, not an honest omission ("Also
enrich for the MATCH" tuition rule). Stamp the real cited published rate per credential level in `apply()` for each
program; record `_standard.omitted` only for a genuinely-unpublished program (e.g. a fully-funded PhD). Several
(UCLA/Michigan/BU/UT-Austin) overlap entries #2/#4/#8 — fix tuition in the SAME depth pass. Peers prove it is knowable:
Princeton 100% · Cornell 92% · UF 92% · MIT 69%.

## 10. Johns Hopkins University — DEPLOY-STRANDED (repo fixed; prod serves 3 old shared-body fields) — severity: high — first seen run 67 · 2026-06-20
244 programs. The in-repo `jhu` `PROGRAMS` score frame_abs150=0 — the #984 "clear the last 3" repair IS a genuine fix.
But prod still serves **3 shared-body fields** (Anthropology, Chemical Engineering, +1) because #984's `Deploy Backend`
was CANCELLED and (unlike Michigan/Columbia) NO later deploy caught it up — see FLAG #4 (non-self-healing). **DO NOT
rewrite — DRIVE THE DEPLOY** (§9), likely via a fresh fixup migration; re-query live for 0. Low effort, finishes JHU.

---

# MEDIUM — flagship seeds · institution-level seeds (seeding is external)

## 11. The flagship seeds (5 programs each) — EMPTY descriptions + null department + 0% tuition + DEAD FEED — severity: medium — first seen run 57 · 2026-06-18
**Brown · Georgetown · UC-Davis · UC-Irvine · UNC-Chapel Hill · UVA · Vanderbilt · Washington U-St Louis** each ship 5
flagship rows with **EMPTY `description_text`** (all 8, not just Brown — confirmed live this run), **null department**,
**0% tuition**, and a **DEAD FEED** (posts=0). **UC-Davis / UNC / Vanderbilt / Washington U-St Louis ship only 3 campus
photos (<4)** (Brown/Georgetown/UC-Irvine 4, UVA 5). **Enrich (per university, one PR):** a full real-named catalog +
per-credential researched descriptions + real departments + published tuition + a working feed + a ≥4-photo verified
gallery, then deepen toward the full real catalog.

## 12. The ~260 bulk institution-level seeds (0 programs) — severity: medium — first seen run 59/60
Each entered at institution level with **0 programs, a dead feed**, and **~33 with ZERO campus photos** (broken
explore-card gradient header + detail hero — the acute sub-set to clear first; e.g. Air Force Institute of Technology,
Arizona State (Campus & Digital Immersion), Azusa Pacific, Colorado State-Fort Collins, James Madison, Keiser-Ft
Lauderdale, Loyola Marymount, Loyola-Chicago, Miami U-Oxford, Michigan Tech, Montclair State, Oakland, Oregon State,
SUNY-ESF, Sacred Heart). **Enrich (per university, one PR):** a full real-named catalog + per-credential field-specific
descriptions + real departments + published tuition · a working feed · a ≥4-photo verified gallery · reviews on
coverable programs · `_standard`. Pick a 0-photo seed once the HIGH tier clears.

---

# CLEAN (desc + structure; no action) — verified LIVE run 72
- **Gold:** MIT (n=65, 0 on every metric, tuition 69%).
- **Cleared + verified LIVE since run 71:** **Berkeley** (n=233 — template-slot 107→0; was run-71 C1) · **UF**
  (n=314 — frame 54→0 + generic-definition openers gone + tuition 28%→92%; was run-71 HIGH #1).
- **Genuinely clean (per-credential-distinct bodies, frame_abs ≤ 1 marginal, no debris/artifacts/template-slot):**
  Duke (1/154) · Yale (1/189) · Chicago (1/91) · Northwestern (1/125) · Rice (0/159) · Purdue (0/172) ·
  UC-San Diego (0/137) · Caltech (0/43) · Princeton (0/43, tuition 100%) · Harvard (0/279) · Columbia (0/167) ·
  Carnegie Mellon (0/180) · UW-Madison (0/348) · Dartmouth (0/43, feed ok) · Emory (0/46, feed ok) ·
  NYU (0/507 — but **0% tuition** #9 + 2 bulletin-stub rows) · USC (0/511 — **0% tuition** #9 + ~20 bulletin-stub rows) ·
  UIUC (0/419 — **0% tuition** #9) · UW-Seattle (0/360 — **0% tuition** #9) · Georgia Tech (5/143 — 5 fields share a
  SUBFIELD ENUMERATION across levels, each lead distinct; mild redundancy, not a stub).
- **Heuristic over-counts to IGNORE (not defects):** Princeton/Duke/Rice dept-echo (those ARE their real departments);
  own-unit peer-substring hits (Cornell CALS/Weill, Penn Wharton/Perelman, JHU Peabody/Whiting, Berkeley
  Lawrence-Berkeley); a trailing `(Source: …edu)` citation (GOOD sourcing); a building named in prose ("Warren Weaver
  Hall, …" — `\bHall,\s` false-flags it, FLAG #3); a shared SUBFIELD ENUMERATION / department name across credential
  levels when each lead is distinct (the abs-150 marginal over-count — GT/Duke/Yale/Chicago/Northwestern). Treat all as
  artifacts UNLESS a row names a unit / landmark / place the institution provably does NOT have.
