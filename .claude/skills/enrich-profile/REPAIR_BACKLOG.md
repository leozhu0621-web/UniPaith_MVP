# Enrich-profile REPAIR BACKLOG

Ranked **worst-first**. The enricher MUST clear the top open entry before deepening any
other university (repair-first, SKILL.md §2). This is the ONLY file where specific
schools appear. Severity: **critical** (fabricated / cross-contaminated / build-junk text
shipped or about-to-ship live — peer-signature copies / URL-slug leaks / namesake-scrapes) ·
**high** (real data but materially broken structure — rollup names / verbatim-across-levels /
per-field stamping / prefix-doubling / possessive-mint names / fabricated owning-unit) ·
**medium** (institution-level seed below gold). Evidence is from the live API
(`api.unipaith.co/api/v1`), measured with WORD-BOUNDARY-anchored structure heuristics
(substring matching over-counts — see run-62 correction) and corroborated against the MERGED
source where a deploy is mid-flight.

_Last graded: 2026-06-19 (grader **run 64** — **FULL-FLEET sweep: all 300 LIVE institutions
re-measured** via the live API; all 40 catalogs scanned across every description + structure
dimension + an OWN-UNIT-EXCLUDED word-boundary peer-signature scan + name-form (possessive vs
conferred) measurement + matcher-side cip/reviews spot-checks + campus-photo / feed / dept
checks; gold MIT (n=65) control). **1 rule change** — miss #2 tightened: the possessive
award-level NAME form ("Bachelor's in {field}") is a realness defect even on a REAL field, not
only on a CIP rollup (gold MIT = 0%; the clean fleet = 0%). New live evidence: Penn #863 +
Cornell #861 — DEPLOYED "de-fabrication" passes that fixed descriptions + doctoral names but
ship 53–55% possessive bachelor's/master's names beside conferred doctoral siblings. This run
records the enricher CLEARING three backlog tiers: **Cornell CRITICAL peer-copy** (Berkeley/Penn
units gone, #859/#861), **BU CRITICAL field-echo** (216→0 real owning colleges, #857 landed),
**Penn HIGH** descriptions/rollup-fields/CIP (#863). See CHANGELOG run 64._

## Fleet at a glance (run 64, live `api.unipaith.co/api/v1`)

- **Fleet = 300 institutions LIVE.** **40 carry programs; 260 are bare institution-level
  stubs** (0 programs, dead feed, 33 with ZERO campus photo). Seeding is **external**; the
  routine ENRICHES + REPAIRS only — these 260 stubs are the backlog.
- **🟢 HEADLINE — the enricher cleared THREE more tiers and the run-63 CRITICAL regression.**
  Verified LIVE: **Cornell peer-copy = 0** (no IEOR/Mahoney/Haas/CDSS/Penn-SAS; the lone "Sloan"
  hit is Cornell's OWN Sloan Program in Health Administration — #859/#861, peer-gate added),
  **BU field-echo 216→0** (real owning colleges: Graduate/College of Arts & Sciences, Questrom,
  Goldman, Sargent… — #857 LANDED + deployed), **Penn** verbatim 74%→**0**, shared-body 70f→**0**,
  literal CIP 28%→**0** (#863, deployed). No cross-institution peer-copy anywhere fleet-wide.
- **🟡 NEW GAP-CLASS (drives the 1 rule change): the possessive award-level NAME form survives a
  de-fab.** Penn #863 + Cornell #861 are DEPLOYED "structural de-fabrication" passes that resolved
  the rollup FIELDS + rewrote descriptions but ship the bachelor's/master's rows in possessive mint
  form — **Penn 53% (102 rows), Cornell 54% (129)** "Bachelor's in {field}" — beside the SAME
  field's conferred doctoral sibling ("Doctor of Philosophy in Anthropology" next to "Bachelor's in
  Anthropology"). The possessive form is fleet-anomalous: **0% on gold MIT and 23/28 catalogs**
  (which name 85–100% of rows "Bachelor of Arts/Science in …"); it survives only on the 4–5
  IPEDS-minted catalogs (Harvard/Columbia/Cornell/Penn 53–55%, Duke 34%, Yale 10%). Penn's
  bachelor's rows also still carry federal CIP titles ("Area Studies", "Accounting and Related
  Services", "Biochemistry, Biophysics and Molecular Biology") the pass claimed to drop.
- **🟡 Harvard #862 is MID-DEPLOY.** Deploy Backend on `6bfbb7f` was `in_progress` at grade time
  (343→289 programs pending); live still shows the pre-#862 catalog (25% aggregate-rollup, 54%
  possessive). About-to-be-live — re-grade next run, repair only if the deployed result still
  carries the possessive form / residual rollups.
- **Mature-catalog structure tiers persist (documented classes, no new rule):** aggregate
  CIP-rollup names (**Columbia 25%(65) · Harvard 25%(85, mid-deploy) · BU 8% · UIUC 6%**),
  possessive-mint names (**Columbia 55 · Harvard 54 · Cornell 54 · Penn 53 · Duke 34 · Yale 10 %**),
  prefix-doubling (**Yale 70%**), per-field shared-leading-body (**Wisconsin 75f · Northwestern 56f ·
  BU 31f**), verbatim-across-levels (**Rice 43%**), bare-field / dept-echo names (**Rice**: English,
  Religion, Global Affairs, Operations Research, Sport Analytics/Management), one literal stub name
  (**BU "minor"**), a likely-fabricated owning unit (**Cornell "David A. Duffield College of
  Engineering"**, 31 rows — Cornell's college is "College of Engineering"; Duffield is a building
  donor, not the college's name — miss #8).
- **Checklist on the 40 catalogs:** 0 duplicate / 0 bare-abbreviation / 0 "Programs" names / 0
  null-department on the 28 mature catalogs; **all 28 carry ≥4 campus photos + a live posts feed**.
  Reviews are richly present on coverable flagship programs (Cornell AEM, Penn Wharton). The 12
  five-program seeds remain 5/5 empty-`description_text` + null-`department` + DEAD FEED; **7 have <4
  photos** (Florida 1, Emory/Notre Dame 2, UC-Davis/UNC/Vanderbilt/WashU 3).

⚠️ **FLAG FOR HUMAN (code/workflow, out of grader scope):**
1. **Auto-merge dual-head race keeps forcing fixup deploys (escalated, runs 61–64).** The durable
   fix — make `test_alembic_has_single_head` evaluate the REBASED-onto-`main` MERGE RESULT and BLOCK
   auto-merge — lives in the automerge/CI workflow (SKILL §8 step 8.5/5). Not grader-editable.
2. **The enforced anti-stub gate's rollup scan is punctuation-keyed and lets the possessive form +
   "Area Studies"/"… and Related Services" titles through — Penn #863 asserted "0 rollup live" yet
   shipped them.** `anti_stub.analyze` has (a) no possessive award-level name scan ("Bachelor's in
   {field}" should be ≥-gated to 0% per the new miss-#2 bullet), (b) a rollup scan that misses bare
   CIP-bucket titles without ", General"/"(CIP"/slash punctuation, and (c) no EXACT-NAME org-chart
   allowlist (Cornell "David A. Duffield College of Engineering" — a fabricated INTERNAL unit
   containing "Cornell"/"Engineering" — passed the peer-signature gate). Add these to `anti_stub.py`
   + `test_anti_stub_gate.py`. Not grader-editable.
3. **`cip_code` is NOT serialized on `/programs/{id}` or the list endpoint** — returns `None` on
   EVERY program incl. gold MIT, so the matcher-side "flag empty `cip_code` via public API" channel
   is UNUSABLE; audit via DB/git or expose it. A serializer gap, not a data gap. (program_preferences
   backfill IS called in the recent migrations — coverage maintained.)
4. **`anti_stub.py` still misses the URL-slug `machine_artifacts` pattern**
   (`^[a-z0-9]+(-[a-z0-9]+){2,}\s*[—–-]\s`). Not grader-editable.

---

# HIGH — real data, structurally broken (rollup · possessive-mint names · per-field stamping · prefix · verbatim)

## 1. Columbia University — severity: high — first seen ≤run 24 · 2026-06-15
263 programs. **25% aggregate CIP-rollup names (65 rows) + 55% possessive-mint names** ("Bachelor's
in {field}"). The worst remaining genuine rollup catalog — NOT de-fabbed this interval. De-roll-up the
federal-CIP names to Columbia's real degrees; give every row the conferred designation (possessive
form → 0%, gold MIT model); real owning schools in `department`; per-credential researched bodies.

## 2. Harvard University — severity: high (mid-deploy — verify) — first seen ≤run 24 · 2026-06-15
343→289 programs. **#862 ("de-fabricate CIP rollups + per-credential descriptions") was DEPLOYING at
grade time**; live still shows the pre-#862 catalog (25% aggregate-rollup (85 rows) + 54% possessive
names). **Re-grade next run.** If the deployed result still ships possessive "Bachelor's in {field}"
names or residual rollups, repair to the conferred designation (new miss-#2 bullet); else CLEAR.

## 3. Yale University — severity: high — first seen ≤run 30 · 2026-06-16
189 programs. **70% prefix-doubling (`description_text.startswith(program_name)`)** + 10% possessive
names. Strip the name prefix; open each description on the field fact (gold MIT = 2%); per-credential
bodies; conferred designations.

## 4. Rice University — severity: high — first seen run 30 · 2026-06-16
159 programs. **43% verbatim-across-levels + 25 shared-leading-body fields + bare-field / dept-echo
names** ("English"/dept "English", "Religion"/"Religion", "Global Affairs", "Operations Research",
"Sport Analytics", "Sport Management"). Per-credential researched bodies; real conferred names; real
owning departments (not the field echoed back).

## 5. University of Wisconsin-Madison — per-field stamping — severity: high — first seen run 60 · 2026-06-19
348 programs. **75 fields where credential siblings share a ≥120-char leading body** (verbatim 0%,
rollup 0% — a suffix-diversifier evades the full-string count, miss #8). Give each credential level
(BA/BS/MS/PhD) its OWN researched body (gold MIT = 0).

## 6. Northwestern University — per-field stamping — severity: high — first seen run 60 · 2026-06-19
308 programs. **56 fields share a ≥120-char leading body** across credential siblings (verbatim 0%).
Per-credential researched bodies (gold MIT = 0). (McCormick/Kellogg/Medill are Northwestern's OWN
schools — not contamination.)

## 7. Cornell University — possessive names + likely-fabricated owning unit — severity: high — first seen run 64 · 2026-06-19
239 programs. CRITICAL peer-copy CLEARED (#859/#861 — verified live). **Residual:** **54% possessive
names (129 rows)** "Bachelor's in {field}" beside conferred doctoral siblings (new miss-#2 bullet);
**"Cornell David A. Duffield College of Engineering" on 31 rows appears fabricated** — Cornell's
college is "College of Engineering" (Duffield is a building donor, not the college's name); verify on
cornell.edu and correct or drop the donor name (miss #8); a near-duplicate ORIE pair ("Bachelor's in
Operations Research" vs "Operations Research and Information Engineering"). Resolve names to the
conferred designation; correct the owning-unit name.

## 8. University of Pennsylvania — possessive names + surviving bachelor's rollups — severity: high — first seen run 24 · 2026-06-15
192 programs. HIGH descriptions/CIP/field-echo CLEARED (#863, deployed). **Residual:** **53%
possessive names (102 rows)** beside conferred doctoral siblings, AND the bachelor's rows still carry
federal CIP titles the pass claimed to drop — "Bachelor's in Area Studies", "Bachelor's in Accounting
and Related Services", "Bachelor's in Biochemistry, Biophysics and Molecular Biology". Finish the NAME
dimension: conferred designation on every level (possessive → 0%); resolve/drop the surviving
bachelor's CIP-bucket titles (miss #2 + new bullet).

## 9. Duke University — possessive names — severity: med-high — first seen run 64 · 2026-06-19
154 programs. **34% possessive names (53 rows)** "Bachelor's in {field}" (descriptions/structure
otherwise clean). Resolve to the conferred designation (new miss-#2 bullet).

## 10. Boston University — residual structure — severity: medium — first seen run 32 · 2026-06-16
399 programs. CRITICAL field-echo CLEARED (#857). **Residual:** **31 shared-leading-body fields**
(per-credential bodies needed, miss #8) + one literal stub name **"minor"** (lowercase, dept "Sargent
College") → give it the real program name or drop it. The "Anderson" peer hits are the real Anderson
Mesa AZ observatory (false positive).

## 11. UIUC + BU residual aggregate-rollup — severity: low — first seen run 64 · 2026-06-19
UIUC 419 programs (6% rollup, ~27 rows) and BU (8%, ~33 rows) carry residual federal-CIP aggregate
names in conferred form ("Bachelor of Arts in Area Studies"). De-roll-up the residual buckets to real
degrees or drop them. Lowest priority.

---

# MEDIUM — institution-level seeds: the enrichment backlog (seeding is external)

## 12. The 12 earlier flagship seeds (5 programs each) — severity: medium — first seen run 57 · 2026-06-18
Each ships 5 flagship rows with **5/5 empty `description_text` + null `department`** + a **DEAD FEED**;
**7 have <4 campus photos** (Florida 1, Emory/Notre Dame 2, UC-Davis/UNC/Vanderbilt/WashU 3).
**Enrich (per university, one PR):** researched descriptions + real departments for the flagship rows, a
working feed (`posts`>0), a ≥4-photo verified+credited gallery, then deepen toward a full catalog.
Seeds: Florida · Emory · Notre Dame · Vanderbilt · WashU · UNC-Chapel Hill · UC-Davis · Brown ·
Georgetown · UC-Irvine · Dartmouth · UVA.

## 13. The ~260 bulk institution-level seeds (0 programs) — severity: medium — first seen run 59/60
Each entered at institution level with **0 programs, a dead feed**, and **33 with ZERO campus photos**
(broken explore-card gradient header + detail hero — the acute sub-set to clear first; e.g. Arizona State
(both campuses), Oregon State, U of Houston, U of Utah, UAB, Colorado State, U of Kentucky, Virginia
Commonwealth, Thomas Jefferson, James Madison, Loyola Chicago/Marymount, Michigan Tech).
**Enrich (per university, one PR):** a full real-named catalog + field-specific descriptions + real
departments · a working feed · a ≥4-photo verified gallery · reviews on coverable programs · `_standard`.
Pick the highest-priority (a 0-photo seed) once the HIGH tier is clear.

---

# CLEANUP / CLEAN (verify-only)

## Cleared this interval — re-confirmed live run 64 (no data repair needed)
- **Cornell** — CRITICAL cross-institution peer-copy (Berkeley IEOR/Haas/CDSS + Penn Mahoney/SAS) →
  **0 live** (#859/#861; peer-gate added). Real Cornell colleges in `department`. (Possessive names +
  Duffield unit remain — entry #7.)
- **Boston University** — CRITICAL field-echo departments 216 → **0 live** (#857 landed + deployed);
  real owning colleges. (31 shared-body fields + "minor" remain — entry #10.)
- **University of Pennsylvania** — descriptions verbatim 74%→0, shared-body 70f→0, literal CIP 28%→0
  (#863). (Possessive names + surviving bachelor's rollups remain — entry #8.)

## Genuinely clean (desc + structure; no action) — MIT (gold) · UCSD · Caltech · Princeton · CMU · Stanford · UT-Austin · Georgia Tech · JHU · Michigan · UCLA · UW-Seattle · USC · NYU · Berkeley · Purdue · UChicago
Verified clean on the description + structure metrics this run (0 rollup / 0 possessive / 0 verbatim /
0 shared-body / 0 prefix beyond the gold-MIT ~2% baseline; conferred-designation naming 85–100%). The
dept-echo substring heuristic OVER-counts on small real-department catalogs (Caltech / UChicago /
Princeton / Duke — "Chemistry"/"Anthropology" IS the real owning department, not a field echo) — treat
as a heuristic artifact UNLESS a row's `department` is literally the field copied from the name while a
real owning school is separately known.
