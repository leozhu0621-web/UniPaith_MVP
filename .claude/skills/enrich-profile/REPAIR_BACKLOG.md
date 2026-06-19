# Enrich-profile REPAIR BACKLOG

Ranked **worst-first**. The enricher MUST clear the top open entry before deepening any
other university (repair-first, SKILL.md §2). This is the ONLY file where specific
schools appear. Severity: **critical** (fabricated / cross-contaminated / build-junk text
shipped live — peer-signature copies / URL-slug leaks / namesake-scrapes) · **high** (real
data but materially broken structure — rollup names / verbatim-across-levels / prefix-
doubling / field-echo departments) · **medium** (institution-level seed below gold).
Evidence is from the live API (`api.unipaith.co/api/v1`), measured with WORD-BOUNDARY-anchored
structure heuristics (substring matching over-counts — see run-62 correction).

_Last graded: 2026-06-19 (grader **run 62** — **FULL-FLEET sweep: all 300 LIVE institutions
re-measured** via the live API; all 40 catalogs scanned across every description + structure
dimension + a WORD-BOUNDARY peer-signature scan + matcher-side cip_code/reviews spot-checks,
plus campus-photo / feed checks). **0 rule changes** — after a full-fleet sweep every live
defect maps to an EXISTING miss (#2/#8/#9) or is deploy-lag / app-code; no NEW gap-class, so
per the anti-churn + no-edit-without-new-evidence rails the rulebook is unchanged. This run
records REAL enricher PROGRESS (Purdue/USC/Chicago/NYU repaired since run 61) and CORRECTS
run-61's substring-noise peer counts (Purdue peer-copy is now 0, not 31). See CHANGELOG run 62._

## Fleet at a glance (run 62, live `api.unipaith.co/api/v1`)

- **Fleet = 300 institutions LIVE.** **40 carry programs; 260 are bare institution-level
  stubs** (0 programs, dead feed, 33 with ZERO campus photo). Seeding is **external**; the
  routine ENRICHES + REPAIRS only — these 260 stubs are the backlog.
- **🟢 HEADLINE — the enricher is now REPAIRING the top backlog, and it WORKED.** Since run 61
  it merged Purdue #840 (force de-fab live + drop Area Studies rollup), USC #843/#844 (collapse
  concentration splits + remove slug-leak + fix field-echo depts), Chicago #839 (per-credential
  grad descriptions), NYU #845/#846 (strip slug-leak). Verified LIVE: **Purdue peer-copy = 0**
  (word-boundary scan; run-61's "31 peer rows" was substring noise — see correction — AND #840
  cleared it), verbatim 82%→0%, rollup 8%→0%; **USC** dept-echo-field 79%→**5%**, slug-leak
  19%→**0%**, peer-sig clean, n 613→520 (splits collapsed). This is the FIRST interval the
  enricher cleared CRITICAL items instead of shipping single-dimension stub-swaps.
- **🔴 DEPLOY-MECHANICS is now the bottleneck, NOT missing rules.** The dual-head auto-merge
  race (SKILL §8 step 8.5/5, flagged-for-human) is ACTIVELY FAILING deploys this interval:
  **Chicago #839 Deploy Backend FAILED** (dual head), **NYU #845 Deploy Backend FAILED** (dual
  head), then a cascade of merge-fixups (#842, #847 cancelled, b30d6ec6 merge-of-merges pending).
  So **NYU's slug-leak fix is MERGED IN SOURCE but NOT LIVE** — stranded mid-deploy, not a false
  repair. The fix-the-deploy work outweighs the fix-the-data work right now.
- **🟡 GRADER-ACCURACY CORRECTION — run-61 peer-signature counts were substring noise.** A
  naive `"CALS" in desc` matches "chemi**cals**"; `"Stern"` matches "we**stern**/ea**stern**".
  Run 61's "Purdue 31 peer rows / BU Perelman+Lick+Medill" were inflated by this. The
  WORD-BOUNDARY (`\bSIG\b`) scan this run returns: **Purdue 0, USC 0, UIUC 0, NYU 0 peer sigs**;
  the ONLY surviving real peer signature fleet-wide is **Boston U "Medill" ×2** (Northwestern's
  journalism school on a Public-Relations row). The peer-copy CRITICAL tier has collapsed from
  "3 catalogs" to "BU ×2 rows."
- **Mature-catalog structure tiers persist (documented classes, no new rule):** field-echo dept
  (BU 81%, plus the substring-heuristic over-counts on small real-dept catalogs — Caltech/
  Princeton/UChicago "Chemistry" IS the real dept), genuine rollup-name (**Berkeley 32 · Harvard
  29 · Cornell 28 · Columbia 27 · Penn 22 %**), verbatim-across-levels (**Berkeley 80 · Cornell
  76 · Penn 74 · Rice 42 %**), shared-leading-body / per-field stamping (**Wisconsin 94f ·
  Harvard 82f · Cornell 78f · Penn 72f · Columbia 60f · Northwestern 59f · Rice 25f**),
  prefix-doubling (**Yale 69 · Stanford 19 · Purdue 16 %**), literal "(CIP NN.NN)" (**Penn 11%**).
- **Checklist on the 40 catalogs:** 0 duplicate / 0 bare-abbreviation / 0 "Programs" names on
  the 28 mature catalogs; **all 28 carry 5 campus photos + a live posts feed**. The 12
  five-program seeds remain 5/5 empty-`description_text` + null-`department` + DEAD FEED;
  **7 of them have <4 photos** (Florida 1, Emory/Notre Dame 2, Vanderbilt/WashU/UNC/UC-Davis 3).

⚠️ **FLAG FOR HUMAN (code/workflow, out of grader scope):**
1. **Auto-merge dual-head race is FAILING PRODUCTION DEPLOYS (escalated from run 61).** Two
   data-PR deploys FAILED on dual heads this interval (Chicago #839, NYU #845), stranding the
   NYU slug-leak fix off-prod despite a green-CI merge, and spawning a merge-of-merges cascade
   (#842/#847/b30d6ec6). The durable fix — make `test_alembic_has_single_head` evaluate the
   REBASED-onto-`main` MERGE RESULT and BLOCK auto-merge — lives in the automerge/CI workflow
   (SKILL §8 step 8.5/5). Not grader-editable. **This is now the single highest-leverage fix in
   the system: good repairs are being merged but not reaching students.**
2. **`cip_code` is NOT serialized on the public `/programs/{id}`** — it returns `None` on EVERY
   program including gold MIT (whose data module certainly sets it), so the skill's matcher-side
   audit channel ("flag empty `cip_code` via the public API") is UNUSABLE; the field must be
   audited via DB/git, or the public program schema must expose it. A serializer gap, not a data
   gap — out of grader scope.
3. `anti_stub.py` is description-FORM-only and still misses, IN CODE, what the rulebook
   prescribes (carried from runs 58–61): (a) the **URL-slug pattern** in `machine_artifacts`
   (`^[a-z0-9]+(-[a-z0-9]+){2,}\s*[—–-]\s`) — NYU + UIUC ship it live while otherwise passing;
   (b) the §8.5 **STRUCTURE metrics** (dept-echo, rollup, CIP-code, concentration-split, anchored
   to the run-61 federal-taxonomy-ending tell, NOT a naive comma-and); (c) a **peer-signature
   WORD-BOUNDARY allowlist scan** (Purdue #832 once shipped peer rows green). None grader-editable.

---

# CRITICAL — fabricated / contaminated / build-junk content shipped live (fix before any other deepening)

## 1. Boston University — peer-signature copy + field-echo dept + classification — severity: critical — first seen run 32 · 2026-06-16
376 programs, UNREPAIRED. WORD-BOUNDARY scan: **"Medill" (Northwestern's journalism school) ×2**
e.g. on BS Public Relations ("…Medill integrated marketing communications…"). Plus structure:
**dept-echo-field 81% (308/376, ~one-off per program), classification descriptions 15% (58),
rollup 6% (24), shared-body 10f.** **Repair:** ALLOWLIST-scan every description against BU's OWN
org chart and FAIL on any foreign unit (miss #8 allowlist, NOT a denylist) — research each
description from BU's catalog; put the real BU school/college in `department` (not the field
echoed from the name); de-roll-up the 24 names; replace the 58 classification stubs with
field-specific prose.

## 2. University of Illinois Urbana-Champaign — URL-slug-leak (UNREPAIRED, no PR) — severity: critical — first seen run 60 · 2026-06-19
419 programs. A leading kebab-case catalog/URL slug bled into `description_text` LIVE on **33 rows
(8%)** — e.g. `"uiuc-agricultural-biological-engineering-bs — Agricultural and Biological Engineers
apply…"`, `"uiuc-chemistry-bs — …"`. Invisible to the built `machine_artifacts` gate (carries no
hex / "Catalog entry" token). **No repair PR has been opened** — this is genuinely unrepaired work.
**Repair:** strip the leading `^[a-z0-9]+(-[a-z0-9]+){2,}\s*[—–-]\s` slug from every description and
open on the field fact (miss #8 build-artifact / §9). The slug is in the source data module.

## 3. New York University — URL-slug-leak: fix MERGED but DEPLOY-STRANDED — severity: critical — first seen run 60 · 2026-06-19
507 programs. **41 rows (8%)** still carry a leading kebab slug LIVE — e.g.
`"anthropology-classical-civilization — The Department of Anthropology…"`,
`"global-public-health-anthropology — …"` (cross-field joint-major slugs). #845/#846
("strip slug-leak / remove slug-leak prefixes (41 rows)") ARE merged to `main`, but **#845's
Deploy Backend FAILED on a dual head** and #846 is still deploying — so the fix is in SOURCE but
NOT yet live. **Repair (verify-don't-rebuild):** confirm the slug is stripped in the source module,
then drive the deploy green (clear the dual head per SKILL §8) and **re-query the live API until the
41 rows render slug-free** — a merged fix that never deployed is a FAILED run (§9), not a clear.

---

# HIGH — real data, structurally broken (rollup · verbatim-across-levels · per-field stamping · field-echo dept · prefix)

## 4. University of California-Berkeley — severity: high — first seen run 22 · 2026-06-15
269 programs. **32% rollup names + 80% verbatim-across-levels + 89% field-echo dept + 18% (50f)
shared-body.** De-roll-up the federal-CIP names; per-credential researched bodies; real owning
schools in `department`.

## 5. Cornell University — severity: high — first seen run 22 · 2026-06-15
274 programs. **28% rollup + 76% verbatim + 86% dept-echo (dept echoes the CIP rollup) + 28% (78f)
shared-body + 3% prefix.** De-roll-up; per-credential bodies; real departments.

## 6. University of Pennsylvania — severity: high — first seen run 24 · 2026-06-15
250 programs. **22% rollup + 11% literal "(CIP NN.NN)" in names + 74% verbatim + 89% dept-echo +
28% (72f) shared-body.** Strip the CIP codes (miss #2 CIP-code tell); de-roll-up; per-credential
bodies; real departments.

## 7. Columbia University — severity: high — first seen ≤run 24 · 2026-06-15
263 programs. **27% rollup + 88% dept-echo + 22% (60f) shared-body.** De-roll-up names;
per-credential bodies; real departments.

## 8. Harvard University — severity: high — first seen ≤run 24 · 2026-06-15
343 programs. **29% rollup + 23% (82f) shared-body + 67% dept-echo.** De-roll-up names;
per-credential bodies; verify the terse "Chemistry"/"Applied Mathematics" depts are the real owning
unit (dept-echo heuristic over-count risk — mostly real) vs a field echo.

## 9. University of Wisconsin-Madison — per-field stamping (shared leading body) — severity: high — first seen run 60 · 2026-06-19
348 programs. **94 fields where credential siblings share a ≥120-char leading body** (verbatim 0%,
rollup 1% — a suffix-diversifier evades the full-string count, miss #8). Give each credential level
(BA/BS/MS/PhD) its OWN researched body (gold MIT = 0).

## 10. Northwestern University — per-field stamping (shared leading body) — severity: high — first seen run 60 · 2026-06-19
308 programs. **59 fields share a ≥120-char leading body** across credential siblings (verbatim 0%,
rollup 1%). Per-credential researched bodies (gold MIT = 0).

## 11. Yale University — severity: high — first seen ≤run 30 · 2026-06-16
189 programs. **69% prefix-doubling (`description_text.startswith(program_name)`) + 75% dept-echo.**
Strip the name prefix; open on the field fact; per-credential bodies; real departments.

## 12. Rice University — severity: high — first seen run 30 · 2026-06-16
159 programs. **42% verbatim + 62% dept-echo + 15% (25f) shared-body + 8% prefix.** Per-credential
bodies; verify departments.

## 13. Purdue University-Main Campus — residual prefix-doubling (peer-copy + verbatim RESOLVED) — severity: high — first seen run 25 · 2026-06-15
283 programs. #840 RESOLVED the peer-copy (word-boundary = 0) and verbatim-across-levels (82%→0%) and
rollup (8%→0%) — a real repair. **Residual: 47 rows (16%) prefix-doubling** (`description_text`
restates the `program_name`). Strip the name prefix; open each on the field fact (miss #9). Demoted
from CRITICAL #1 to HIGH residual.

## 14. University of Southern California — residual field-echo dept (peer + slug + splits RESOLVED) — severity: high — first seen run 58 · 2026-06-18
520 programs. #843/#844 RESOLVED the slug-leak (19%→0%), collapsed the concentration splits (n
613→520), and cut dept-echo 79%→**5% (30 rows)**. **Residual: 30 rows still set `department` to the
field echoed from the name** while the real USC school (Dornsife/Marshall/Viterbi) is known. Put the
real owning school in those 30 rows' `department` (miss #2). Demoted from HIGH to near-clean residual.

---

# MEDIUM — institution-level seeds: the enrichment backlog (seeding is external)

## 15. The 12 earlier flagship seeds (5 programs each) — severity: medium — first seen run 57 · 2026-06-18
Each ships 5 flagship rows with **5/5 empty `description_text` + null `department`** + a **DEAD FEED**;
**7 have <4 campus photos** (Florida 1, Emory/Notre Dame 2, Vanderbilt/WashU/UNC/UC-Davis 3).
**Enrich (per university, one PR):** researched descriptions + real departments for the flagship rows,
a working feed (`posts`>0), a ≥4-photo verified+credited gallery, then deepen toward a full catalog.
Seeds: Florida · Emory · Notre Dame · Vanderbilt · WashU · UNC-Chapel Hill · UC-Davis · Brown ·
Georgetown · UC-Irvine · Dartmouth · UVA.

## 16. The ~260 bulk institution-level seeds (0 programs) — severity: medium — first seen run 59/60
Each entered at institution level with **0 programs, a dead feed**, and **33 with ZERO campus photos**
(broken explore-card gradient header + detail hero — the acute sub-set to clear first; e.g. Arizona
State (both campuses), Oregon State, U of Houston, U of Utah, UAB, Colorado State, U of Kentucky,
Virginia Commonwealth, Thomas Jefferson, James Madison, Loyola Chicago/Marymount, Michigan Tech).
**Enrich (per university, one PR):** a full real-named catalog + field-specific descriptions + real
departments · a working feed · a ≥4-photo verified gallery · reviews on coverable programs · `_standard`.
Pick the highest-priority (a 0-photo seed) once the CRITICAL/HIGH tiers are clear.

---

# CLEANUP / CLEAN (verify-only)

## Repaired this interval — re-confirmed live run 62 (no data repair needed)
- **Purdue** — peer-copy + verbatim + rollup cleared by #840 (residual prefix → HIGH #13).
- **USC** — slug-leak + concentration-splits cleared by #843/#844; dept-echo 79%→5% (residual → HIGH #14).
- **Chicago** (#839), **build-artifact tier** (UCLA/UW/Michigan/Stanford, run-59 CRITICAL) — STAY clean;
  `hex_artifact = 0` re-confirmed on every catalog this run.

## Genuinely clean (desc + structure; no action) — MIT (gold) · UCSD · Caltech · Princeton · CMU · Duke · UT-Austin · Georgia Tech · JHU · NYU(structure) · Michigan · UCLA · UW · Stanford(structure)
Verified clean on the description + rollup metrics this run. The dept-echo substring heuristic
OVER-counts on small real-department catalogs (Caltech 88% / UChicago 87% / Princeton 74% / Harvard
67% / Duke 65% — "Chemistry"/"Anthropology" IS the real owning department, not a field echo) — treat
as a heuristic artifact UNLESS a row's `department` is literally the field copied from the name while a
real owning school is separately known (BU/USC-residual = real defect; Princeton/Caltech = not). NYU's
STRUCTURE is clean (rollup 0%); its only residual is the slug-leak in CRITICAL #3 (deploy-stranded).
Stanford's structure is clean; prefix-doubling 19% is its only residual (below the HIGH threshold).
