# Enrichment Grader — CHANGELOG

Audit log of the `improve-enrichment` routine: each run grades the live enrichment
output, tightens the `enrich-profile` rulebook against recurring problem CLASSES,
and re-ranks the repair backlog. One squash PR per run.

---

## 2026-06-16 — Run 15 (REAL PROGRESS — Princeton #641 is the FIRST genuinely clean structural de-fabrication, 114→41 real degrees, but its deploy FAILED on a stale `len(PROGRAMS) >= 100` breadth gate frozen to the padded count. NEW class: a count-target breadth GATE fights de-fabrication and blocks the deploy. Added 1 rulebook sub-bullet; moved Princeton out of HIGH)

**Institutions audited:** all 28 in the live DB (`/institutions/search?q=&page_size=50` → total 28,
no sprawl). Recently-changed focus on the ONE new enrichment PR since run 14 — **Princeton #641
"catalog structural repair — field-specific descriptions for 41 programs"** + its follow-up
test-align commit `1057be7`. Read the #641 SOURCE (it is NOT yet live — see deploy finding) via the
data module (`princeton_profile.py` PROGRAMS names/departments, `princeton_field_descriptions.py`
named-unit truth) and the live Princeton catalog (full pagination `page_size=50`, n=114 — the OLD
PRE-#641 padded state, since the deploy failed). Confirmed the failed/in-progress Deploy Backend
runs via GitHub Actions. Re-confirmed the two carried CRITICAL review breaches (Northwestern + Duke)
via `/programs/{id}.external_reviews`; fleet `/institutions/{id}/posts` feed sweep (NYU still dead).

**What merged since run 14:** ONE in-scope profile PR — **Princeton #641** (97978b2) + the test-align
commit `1057be7` (catalog breadth gate). The run-14 grader PR #640 is the prior `origin/main` work;
everything else in range is out of scope. So the other 27 catalogs are byte-identical to run 14.

**Findings (live API + Actions + source evidence):**

1. **REAL PROGRESS — Princeton #641 is the FIRST genuinely CLEAN structural de-fabrication (modulo
   not-yet-live).** It drops 73 federal certificate / incidental-master's padding rows (114→41),
   replaces every CIP-prefix name with a real degree title ("Bachelor of Arts in Anthropology",
   "Master of Public Affairs (MPA)"), gives every row a real owning department, and writes
   field-specific descriptions that name ONLY real Princeton units (PACM, ORFE, SEAS, Frick
   Chemistry Laboratory, Peyton Hall, High Meadows Environmental Institute, Andlinger Center). Source
   scan: ZERO rollup names, ZERO CIP-prefix names, ZERO prefix-doubling, ZERO foreign/mismatched
   units — i.e. it satisfies the dimension-agnostic clear bar on structure AND applies the run-13/14
   named-unit-truth lesson. The first non-MIT catalog to do so. Responsive, correct work.
2. **NEW PROBLEM CLASS — a stale catalog-breadth GATE BLOCKED the de-fabrication deploy (a correct
   repair that never shipped).** Princeton's profile-standard test asserted
   `assert len(PROGRAMS) >= 100` — a row count frozen to the OLD padded catalog. The correct
   de-fabrication to 41 real rows tripped it → **Deploy Backend run 27654099686 FAILED** (the test
   job gates the deploy), so the migration + data NEVER reached production. The LIVE Princeton is
   therefore STILL the old 114-row padded catalog (rollup names, classification-template
   descriptions, empty deep fields) — confirmed live this run. The author self-corrected with
   `1057be7` (drop the `>=100` assertion; assert no-CIP-prefix-names / no-classification-stubs +
   `>=35` instead), and a re-deploy (run 27655035837) was in_progress at grading time. NOT covered
   by any prior rule: miss #2's "count is a CHECK, not a TARGET — NEVER pad it" governs the DATA, not
   a count-target TEST/gate that fights a correct DE-padding and blocks the deploy.
3. **Both carried CRITICAL review breaches PERSIST (re-confirmed live).** Northwestern still ships
   the synthesized "Students describe Northwestern's undergraduate program in *Architecture and
   Related Services, Other* within Weinberg…" CIP-rollup review (now runs 9→15); Duke still ships
   the copy-paste Pratt B.S.E. boilerplate ("…a rigorous engineering degree at a selective private
   R1 university…", field swapped across Biomedical/Civil; now runs 10→15).
4. **Feeds healthy** — NYU still the ONLY dead feed (`posts=[]`); Northwestern + others fetch fine.
   28 institutions, no sprawl.

**False alarms caught (diagnosed, not acted on):**
- **The live Princeton 114-row padded catalog is NOT a #641 regression — it is the PRE-#641 state
  because the deploy FAILED.** First read showed clean "Bachelor of Arts in Anthropology" rows AND
  31 surviving CIP-rollup padding rows in one catalog, which looked like a half-applied migration;
  I traced it to the failed Deploy Backend (the upsert never ran). The clean first rows predate
  #641; the migration's reconcile (delete-unreferenced / else-unpublish padding) never executed.
  Do NOT grade #641's content off the live API until the re-deploy lands.
- **`?page_size=100` 422s (server cap 50)** — paginated by 50. The real description field is
  `description_text`; named-unit truth confirmed by reading the source descriptions (all real
  Princeton units) rather than trusting the PR label.
- **The deploy failure is NOT a migration/data defect** — the migration `princetonprof7` is correct
  (idempotent reconcile, single head `down_revision=stanfordprof8`); the failure was a STALE TEST
  assertion, which is the addable class. The fix is already applied (`1057be7`), so a re-deploy
  should land Princeton.

**Rulebook changes: 1 of ≤3 (ADDS/TIGHTENS the completeness/verify gate; loosens nothing):**
- **miss #2 (new sub-bullet):** a catalog-breadth GATE must assert structural REALNESS, not a raw
  row COUNT — a `len(PROGRAMS) >= N` assertion frozen to a PADDED count FIGHTS de-fabrication and
  FAILS the deploy when you correctly drop padding. When de-padding shrinks a catalog toward its
  real published size, a hard high-minimum count gate (calibrated to the padded number) fails on the
  smaller real catalog and blocks the deploy. Write the gate to assert every row is REAL (no
  CIP-prefix / rollup names, no classification stubs, real departments, no concentration splits) and
  a count matching the VERIFIED real catalog — never `>= padded_N`; and update the catalog's breadth
  test in the SAME de-fabrication PR. The full-published-catalog completeness bar still stands,
  enforced by realness not a frozen number. Evidence: live this run — #641's Deploy Backend FAILED on
  `assert len(PROGRAMS) >= 100` after a correct 114→41 de-fabrication; shipped only after `1057be7`
  replaced it with a no-CIP-prefix / no-classification-stub realness gate. (The other 2 reserve
  changes were NOT used — the NW/Duke review breaches and Stanford named-unit fabrications are
  already named, miss #8/#9, so adding rules would be churn.)

**FLAGGED FOR HUMAN REVIEW:**
- **(NEW this run, process)** a CORRECT de-fabrication (Princeton #641) failed to deploy on a stale
  breadth test and required a manual follow-up commit. The rulebook now forbids the count-target
  gate, but a human may want to confirm the re-deploy (run 27655035837) landed and the live Princeton
  now shows 41 real rows — and that no OTHER catalog's profile-standard test carries a `>= padded_N`
  assertion waiting to block its de-fabrication.
- **(carried, urgent — now 7 / 6 intervals)** Northwestern (43+ synthesized reviews, runs 9→15) and
  Duke (~5 Pratt boilerplate reviews, runs 10→15) remain live and unrepaired; the CRITICAL backlog
  top is not being cleared. A human may want to confirm the enricher is working the CRITICAL backlog.
- **(carried, urgent)** Stanford's Sibley-School + Freeman-Spogli fabricated units (run 13/14) remain
  live; the grader does not edit data.
- **(carried from runs 2–14, unreconciled)** miss #9 says "FAIL on null/blank `department`" but gold
  MIT ships null department and `manifest.py` marks `department` `required=False`. Reconciling would
  LOOSEN verify-output → left intact per the rails.
- **(carried from runs 8–14, methodology)** misses #8/#9 cite "`_standard` usually unstamped" as a
  stub tell — valid for the ENRICHER but not API-visible to the grader. Left intact.

**Backlog delta:** Princeton MOVED OUT of HIGH (was run-14 row 3) into a dedicated "REPAIRED IN CODE
(#641), deploy was BLOCKED, verify live once it lands" note — if the re-deploy ALSO failed it returns
to HIGH as a deploy-blocked repair. HIGH table renumbered to 14 entries (otherwise unchanged).
NW/Duke persistence lines bumped to 9→15 / 10→15. Added an enricher note: "A BREADTH GATE CHECKS
REALNESS, NOT A ROW COUNT — when you de-pad a catalog, update its breadth test in the same PR or the
deploy fails." Ranking unchanged: CRITICAL = Boston University (structure) + Stanford (fabricated
units) + Northwestern + Duke (fabricated reviews); HIGH = 14 catalogs worst-first; MEDIUM = the 8
shallow 22-program stubs (NYU = only dead feed); CLEAN = MIT only (Princeton clean-in-code, pending
deploy verification).

**Health check:** the profile pytest could not run in this ephemeral container (no backend venv /
pytest / Postgres) — same constraint as runs 1–14. Changes are markdown-only (SKILL.md +1 sub-bullet
in miss #2, backlog re-write, this changelog; NO Python, no migrations, no app code), so the enricher
code/data state is unaffected and miss numbering remains sequential 1–9.

**Invariants:** all intact; the single edit ADDS/TIGHTENS the completeness + verify-rendered-output
gate (a breadth gate must check per-row realness, and the full-catalog completeness bar is reaffirmed,
not loosened). The findings that could argue for loosening (null-department FAIL vs gold MIT;
`_standard`-as-rendered-signal) remain logged for human review, not acted on.

---

## 2026-06-16 — Run 14 (the enricher's FIRST repair of a grader-flagged fabrication was a WHACK-A-MOLE: Stanford's fa7163e hotfix cleared only the ONE cited field (College of Chemistry) and left sibling fabrications of the SAME class live (Sibley School, FSI mismatches). Closed the gap — promoted the run-13 named-unit-truth check into miss #9's PRE-SHIP PROGRAMMATIC gate + required a whole-class re-scan. 1 rulebook change)

**Institutions audited:** all 28 in the live DB (`/institutions/search?q=&page_size=50` → total 28,
no sprawl). Recently-changed focus on the ONE live-state change since run 13's grading —
**fa7163e "fix(stanford): correct peer-adaptation leaks in field descriptions"** (the Stanford
partial hotfix). Full Stanford program pagination (`page_size=50`, n=188) with a whole-catalog
named-unit scan (`description_text` ⊃ "College of Chemistry"/"Sibley School"/"Freeman Spogli"/
"Harvardsylvania"/"Berkeley"/"Cornell") + rollup-name / prefix-doubling metrics vs gold MIT;
per-program `/programs/{id}.external_reviews` re-confirmation of the two carried breaches
(Northwestern + Duke); fleet-wide `/institutions/{id}/posts` feed sweep; student's-eye detail
integrity check on Rice + Princeton (`campus_photos`, `ranking_data`).

**What merged since run 13:** NO new profile-enrichment PR. The run-13 grader PR #639 is
`origin/main` HEAD. The only profile commit affecting live state is **fa7163e** (Cursor Agent,
2026-06-16 21:34 UTC) — which merged ~8 min BEFORE the run-13 grader PR #639 (21:42 UTC), so
**run 13 graded Stanford's PRE-fix state**; this run grades the POST-fix Stanford. Everything else
is byte-identical to run 13. The other commits in range are out of scope (#637 Import surface).

**Findings (live API evidence):**

1. **PARTIAL REPAIR — fa7163e is the enricher's FIRST attempt at a grader-flagged fabricated-unit
   defect, and it WHACK-A-MOLED only the one field the backlog named verbatim.** ✅ Cleared:
   Berkeley's "College of Chemistry" (the 3 chem-eng rows now correctly cite "Stanford School of
   Engineering's Department of Chemical Engineering") + the "Harvardsylvania" artifact. ❌ STILL
   LIVE (same class, same catalog): Cornell's **"Sibley School"** on 2 Stanford aerospace rows
   (Bachelor's + Graduate Certificate in Aerospace…) — Stanford has no Sibley School; and the
   real-but-international-studies **Freeman Spogli Institute** bolted onto a **systems-engineering**
   row ("Bachelor's in Systems Science and Theory") and a **marketing** row ("Master's in Public
   Relations, Advertising, and Applied Communication"). A no-fabrication breach is not cleared until
   the WHOLE class is — Stanford STAYS CRITICAL.
2. **Stanford's recurring classes unchanged** — n=188, rollup~34% (echoed in `department`,
   single-dimension pass, miss #8), prefix-doubling 85% (miss #9), `class_profile`/
   `faculty_contacts`/`tracks` empty. The hotfix touched only the chem-eng descriptions.
3. **Both carried no-fabrication review breaches PERSIST.** Northwestern still ships the synthesized
   "Students describe Northwestern's undergraduate program in *Architecture and Related Services,
   Other* within Weinberg…" CIP-rollup review (now runs 9→14); Duke still ships the copy-paste Pratt
   B.S.E. boilerplate ("…a rigorous engineering degree at a selective private R1 university…", field
   swapped; now runs 10→14). Re-confirmed live via `/programs/{id}.external_reviews`.
4. **Feeds healthy** — NYU still the ONLY dead feed (`posts=0`); all other 27 fetch ≥8 (UChicago
   1415, Cornell 1270, CMU 1084). No sprawl (28 institutions). Rice + Princeton detail integrity
   fine (5 `campus_photos`, ownership + carnegie present).

**False alarms caught (diagnosed, not acted on):**
- **The Sibley-School / FSI persistence is NOT a NEW defect class** — it is the run-13 named-unit-
  truth class (miss #8) incompletely repaired. Adding a rule for the class itself would be churn.
  The genuinely-new, addable gap is METHODOLOGICAL: that class's check was NOT in miss #9's pre-ship
  PROGRAMMATIC gate (it was only a per-row manual check), so a repair pass running that gate cannot
  catch siblings — that is what I closed.
- `?page_size=100` 422s (server cap 50) — paginated by 50. The real description field is
  `description_text`. Named-unit hits ("Sibley School" = Cornell's, "Freeman Spogli" = international
  studies) confirmed by external knowledge of which institution/field owns each unit; the chem-eng
  control passed (now correctly Stanford's Department of Chemical Engineering), proving the hotfix is
  deployed and the fix is real but field-scoped.
- `campus_photos` reads 0 on the `/institutions/search` LIST endpoint (list-vs-detail artifact, run
  11/12) — used the detail endpoint; Rice + Princeton both carry 5. Not a defect.

**Rulebook changes: 1 of ≤3 (ADDS/TIGHTENS verify-output + no-fabrication; loosens nothing):**
- **miss #9 (new sub-bullet):** scan EVERY description for a named unit that doesn't belong, and a
  REPAIR must clear the WHOLE class, not just the cited row. Promoted the run-13 named-unit-truth
  defect (miss #8) into the PRE-SHIP PROGRAMMATIC gate — before shipping, scan every
  `description_text` and FAIL on any named school/college/department/center/institute/lab this
  institution does not publish OR any real unit cited on a field it does not house. And a pass that
  repairs a flagged fabrication MUST re-scan the whole catalog for EVERY instance of that class and
  get ZERO before shipping; fixing only the named row(s) while siblings survive is a non-repair.
  Evidence: live API this run — the Stanford hotfix cleared the one cited "College of Chemistry"
  instance but a whole-catalog scan still returns "Sibley School" (peer unit) + FSI-on-unrelated-
  fields. (The other 2 reserve changes were NOT used — the Stanford recurrences and the NW/Duke
  review breaches are already named, miss #8/#9, so adding rules would be churn.)

**FLAGGED FOR HUMAN REVIEW:**
- **(carried, urgent)** the enricher's first fabricated-unit repair fixed only the cited example and
  shipped — the Sibley School + FSI fabrications remain in production. A human may want to remove/
  correct the remaining fabricated Stanford descriptions directly (the grader does not edit data).
- **(carried, urgent — now 6 / 5 intervals)** Northwestern (43+ synthesized reviews, runs 9→14) and
  Duke (~5 Pratt boilerplate reviews, runs 10→14) remain live and unrepaired; the CRITICAL backlog
  is not being cleared. A human may want to confirm the enricher is working the CRITICAL backlog top.
- **(carried from runs 2–13, unreconciled)** miss #9 says "FAIL on null/blank `department`" but gold
  MIT ships null department and `manifest.py` marks `department` `required=False`. Reconciling would
  LOOSEN verify-output → left intact per the rails.
- **(carried from runs 8–13, methodology)** misses #8/#9 cite "`_standard` usually unstamped" as a
  stub tell — valid for the ENRICHER but not API-visible to the grader. Left intact.

**Backlog delta:** Stanford KEPT CRITICAL with the entry rewritten to record the partial repair
(College of Chemistry ✅ cleared; Sibley School + FSI ❌ still live) and a whole-catalog-scan repair
instruction. NW/Duke persistence lines bumped to 9→14 / 10→14. HIGH table + MEDIUM unchanged
(nothing else merged). Added an enricher note: "A REPAIR MUST CLEAR THE WHOLE CLASS, NOT THE CITED
ROW." Ranking unchanged: CRITICAL = Boston University (structure) + Stanford (partial-repair,
fabricated units still live) + Northwestern + Duke (fabricated reviews); HIGH = 15 catalogs
worst-first; MEDIUM = the 8 shallow 22-program stubs (NYU = only dead feed); CLEAN = MIT only.

**Health check:** the profile pytest could not run in this ephemeral container (no backend venv /
pytest / Postgres) — same constraint as runs 1–13. Changes are markdown-only (SKILL.md +1
sub-bullet, backlog re-write, this changelog; NO Python, no migrations, no app code), so the
enricher code/data state is unaffected and miss numbering remains sequential 1–9.

**Invariants:** all intact; the single edit ADDS/TIGHTENS verify-output + no-fabrication, weakens
nothing. The findings that could argue for loosening (null-department FAIL vs gold MIT;
`_standard`-as-rendered-signal) remain logged for human review, not acted on.

---

## 2026-06-16 — Run 13 (NEW defect class: the description-depth pass FABRICATES named units to fake specificity — #638 Stanford put Berkeley's "College of Chemistry" and Cornell's "Sibley School" on Stanford rows. A live no-fabrication breach. Added 1 rulebook sub-bullet; promoted Stanford to CRITICAL)

**Institutions audited:** all 28 in the live DB (`/institutions/search` → total 28, no sprawl).
Recently-changed focus on the ONE new enrichment PR since run 12 — **#638 "Stanford description
depth pass" (188 programs)**. Full program pagination (`page_size=50`) + rollup-name / prefix-doubling
/ named-unit-truth metric sweep on Stanford, with gold MIT as the contrast; per-program
`/programs/{id}` deep-field + `external_reviews` deep-checks on Stanford; re-confirmation of the two
carried live breaches (Northwestern + Duke synthesized reviews) via `/programs/{id}.external_reviews`;
fleet-wide `/institutions/{id}/posts` feed sweep.

**What merged since run 12:** ONE in-scope profile PR — **#638 Stanford** (`origin/main` HEAD). The
others are out of scope: #637 Import surface + #633 follow-up app code; #635/#636 are the operator's
skill-growth edits (growth source = U.S. News National Universities ranking, add-don't-idle). So the
other 27 catalogs are byte-identical to run 12.

**Findings (live API evidence):**

1. **REAL PROGRESS — #638 made Stanford descriptions field-specific.** The old generic gloss +
   BA-name/"BS"-desc mismatch run 12's backlog flagged are gone; the clean-named rows pass the gold
   contrast ("Undergraduate economics at Stanford covers micro, macro, econometrics, and policy with
   the Stanford Institute for Economic Policy Research").
2. **NEW PROBLEM CLASS — the description-depth pass FABRICATES named units to fake specificity, a
   live no-fabrication breach.** To make descriptions "specific" #638 attached **another
   institution's** named college/school to Stanford programs: **Berkeley's "College of Chemistry"**
   on all 3 Stanford chemical-engineering rows (cert + bachelor's + master's — the same wrong unit
   copied across credential levels) and **Cornell's "Sibley School"** on 2 Stanford aerospace rows.
   A real Stanford institute (Freeman Spogli/FSI) is also bolted onto an unrelated field ("Master's
   in Public Relations, Advertising, and Applied Communication"). A control passed (FSI is correctly
   named on a political-science row), proving the pass gets some right and INVENTS others — i.e. it
   is generating institutional trivia from a template, not reading the real catalog page. A
   confidently-wrong specific reads authoritative and is WORSE than an honest generic gloss. NOT
   covered by any prior rule: the reviews fabrication-by-synthesis rule (miss #8, run 9) is
   reviews-only, and the gold-contrast rule demands field-SPECIFICITY but never guards its TRUTH.
3. **RECURRENCE (NOT new) — Stanford single-dimension pass (miss #8) + prefix-doubling (miss #9).**
   34% rollup NAMES with the rollup echoed verbatim in `department` ("Bachelor's in Aerospace,
   Aeronautical, and Astronautical/Space Engineering", dept identical), 85% prefix-doubling
   ("Bachelor's in Anthropology: School of Humanities and Sciences anthropology combines …"), and
   `class_profile`/`faculty_contacts`/`tracks` empty. Descriptions-only is not a clear.
4. **PERSIST — both carried live no-fabrication review breaches unrepaired (now runs 9→13 / 10→13).**
   Northwestern still ships "Students describe Northwestern's undergraduate program in *Architecture
   and Related Services, Other* within Weinberg …"; Duke still ships the identical Pratt B.S.E.
   boilerplate ("… a rigorous engineering degree at a selective private R1 university; praise
   includes undergraduate research access and Triangle …", field swapped). Re-confirmed live.
5. **Feeds healthy** — NYU still the ONLY dead feed (`posts=0`); all other 27 fetch ≥33 (Stanford
   234). No sprawl (28 institutions).

**False alarms caught (diagnosed, not acted on):**
- **The "Bachelor → Graduate/master" degree-level scan was mostly a FALSE POSITIVE** — `"graduate "`
  matches inside `"Undergraduate "`. Of 8 hits, 7 were "Undergraduate …" (correct); only "Bachelor's
  in Applied Mathematics: Graduate applied mathematics at Stanford …" is a real level mismatch — a
  single row, already covered by the miss #2/#8 credential/degree-type-disagreement rule, not a new
  class. Re-verified by reading, not by trusting the regex.
- **Stanford's `external_reviews` are NOT the #619/#626 synthesis class** — its BA-Economics review
  is program-specific-ish, names real Stanford units (SIEPR, GSB), and carries no CIP rollup; sources
  mix a program page with a generic Niche page but it is not the institution-level boilerplate. So the
  Stanford breach is the DESCRIPTIONS, not the reviews.
- `?page_size=100` 422s (server cap 50) — paginated by 50. The real description field is
  `description_text`. Rollup/prefix/named-unit heuristics spot-verified against gold MIT (2% prefix,
  6% rollup, true field-specific units) as the contrast before reporting; the foreign-unit hits
  ("College of Chemistry" = Berkeley, "Sibley School" = Cornell) were confirmed by external knowledge
  of which institution owns each unit, with a Stanford-real control (Freeman Spogli) passing.

**Rulebook changes: 1 of ≤3 (ADDS/TIGHTENS no-fabrication + verify-output; loosens nothing):**
- **miss #8 (new sub-bullet):** a field-specific description must be VERIFIED-TRUE, not merely
  specific-SOUNDING — a depth pass that INVENTS a concrete fact (a named school/college/center/
  institute/lab, or a ranking/superlative) to satisfy the gold contrast is fabrication-by-synthesis
  on the DESCRIPTION dimension, and a confidently-wrong specific is worse than an honest generic
  gloss. The gold contrast demands a concrete fact; this rule guards its TRUTH. Operational tells:
  the named unit belongs to a peer institution, or a real same-institution unit is bolted onto an
  unrelated field, or the same wrong unit is copied across every credential level of one field. Any
  named unit MUST be one this institution actually has AND that houses this program (verify against
  the official org/academics page); any ranking/superlative must be cited; else write a true generic
  clause. Evidence: live API this run — a freshly description-passed catalog attached two peer
  institutions' named colleges/schools to its own chemistry- and aerospace-engineering rows and
  repeated each across all three credential levels. (Written generally; the specific school stays
  in the backlog per the GENERAL-NOT-SPECIFIC rail.) The other 2 reserve changes were NOT used —
  the single-dimension + prefix-doubling recurrences are already named (miss #8/#9), so adding rules
  for them would be churn.

**FLAGGED FOR HUMAN REVIEW:**
- **(NEW this run, urgent)** #638 shipped **fabricated unit names to production** (Berkeley's College
  of Chemistry + Cornell's Sibley School on Stanford rows). The rulebook now forbids the class, but a
  human may want to correct/remove the live fabricated descriptions directly (the grader does not edit
  data; queued as the Stanford CRITICAL backlog entry).
- **(carried, urgent — now 5 intervals)** the Northwestern (43+) and Duke (~5 Pratt) synthesized
  reviews remain live and unrepaired across runs 9→13 / 10→13; the CRITICAL backlog is not being
  cleared. A human may want to confirm the enricher is working the CRITICAL backlog top before new
  description passes.
- **(carried from runs 2–12, still unreconciled)** miss #9 says "FAIL on null/blank `department`" but
  gold MIT ships null department and `manifest.py` marks `department` `required=False`. Reconciling
  would LOOSEN the verify-output invariant → left intact per the rails.
- **(carried from runs 8–12, methodology)** misses #8/#9 cite "`_standard` usually unstamped" as a
  stub tell — valid for the ENRICHER but not API-visible to the grader. Left intact; a human may want
  to clarify it is an internal field.

**Backlog delta:** Stanford PROMOTED from HIGH (was row 3) to CRITICAL — a live fabrication breach
outranks incompleteness (same treatment as Northwestern/Duke). HIGH table re-numbered to 15 entries
(unchanged otherwise). Header + methodology updated to add the named-unit-truth grading signal and
the enricher notes warn against inventing named units. Ranking: CRITICAL = Boston University
(structure) + **Stanford (fabricated descriptions, NEW)** + Northwestern + Duke (fabricated reviews);
HIGH = 15 catalogs worst-first; MEDIUM = the 8 shallow 22-program stubs (NYU = only dead feed);
CLEAN = MIT only.

**Health check:** the profile pytest could not run in this ephemeral container (no backend venv /
pytest / Postgres) — same constraint as runs 1–12. Changes are markdown-only (SKILL.md +1 sub-bullet,
backlog re-rank, this changelog; NO Python, no migrations, no app code), so the enricher code/data
state is unaffected and miss numbering remains sequential 1–9.

**Invariants:** all intact; the single edit ADDS/TIGHTENS no-fabrication + verify-output, weakens
nothing. The findings that could argue for loosening (null-department FAIL vs gold MIT;
`_standard`-as-rendered-signal) remain logged for human review, not acted on.

---

## 2026-06-16 — Run 12 (NO new gaps found — THIRD consecutive interval with zero new enrichment work; live fleet byte-identical across runs 10→11→12, both no-fabrication breaches now persisted 9→12. Changed NO rules; updated backlog header + persistence notes only)

**Institutions audited:** all 28 in the live DB (`/institutions/search` → total 28, no sprawl).
Full program pagination (`page_size=50`) + rollup-name / prefix-doubling metric sweep on the
worst/representative catalogs (Northwestern, Duke, Columbia, gold MIT); per-program
`/programs/{id}.external_reviews` deep-checks on Northwestern + Duke (the two live
no-fabrication breaches); fleet-wide `/institutions/{id}/posts` feed sweep + a `campus_photos`
detail-endpoint check.

**What merged since run 11:** NOTHING. The run-11 grader PR (#632) is `origin/main` HEAD with
ZERO commits after it (`git log origin/main`). No profile-enrichment PR has merged since run 10
(the last profile work was the four description passes #620/#622/#626/#628, graded by run 10).
So **no new enrichment output exists to grade** — the enricher has not fired the profile routine
for three intervals running.

**Findings (live API evidence — all identical to runs 10/11 within rounding):**

1. **Fleet metrics unchanged** (computed live this run): Northwestern n=308 rollup=1%
   prefix-dbl=97%; Columbia n=263 34% / 90%; Duke n=154 3% / 66%; gold MIT n=65 6% / **2%**.
   Matches run 11 — confirming no new enrichment landed.
2. **Both live no-fabrication breaches PERSIST (the two top non-BU CRITICAL entries), now FOUR
   grading intervals (9→12) with no repair PR.** Northwestern still ships the synthesized
   "Students describe Northwestern's undergraduate program in *Architecture and Related Services,
   Other* within Weinberg…" CIP-rollup review (now on a row renamed "Bachelor of Arts in
   Architecture Studies" — the rollup survives only in the review summary, proof it was
   synthesized from the original metadata). Duke still ships 5 Pratt B.S.E. rows sharing the
   identical "…a rigorous engineering degree at a selective private R1 university; praise
   includes undergraduate research access and Triangle…" boilerplate, only the field swapped.
3. **Feeds healthy** — NYU still the ONLY dead feed (`posts=0`); all other 27 fetch ≥8. No
   sprawl (still 28 institutions).
4. **Photos** — verified via the DETAIL endpoint (the list endpoint omits them): the 20 enriched
   institutions carry 5 verified `campus_photos` (MIT credit "Wikimedia Commons / Peacearth (CC
   BY-SA 4.0)", Northwestern "… / Madcoverboy (CC BY-SA 3.0)"); the 8 known MEDIUM stubs carry 0
   (already backlog MEDIUM). No new photo class.

**False alarms caught (diagnosed, not acted on):**
- **`campus_photos` reads 0 on the `/institutions/search` LIST endpoint for ALL 28, including
  gold MIT — a list-vs-detail artifact, NOT a regression.** The search listing does not embed
  `school_outcomes.campus_photos`; the detail endpoint `/institutions/{id}` returns the real 5
  (verified above). Do NOT grade photos off the list endpoint. Logged, not ruled.
- `?page_size=100` 422s (server cap 50) — paginated by 50. The real description field is
  `description_text`. Rollup/prefix heuristics spot-verified against gold MIT (2% prefix) as the
  contrast before reporting.

**Rulebook changes: NONE (0 of ≤3).** No new enrichment output existed to grade, and every live
defect is a recurrence of a class the rulebook ALREADY names (prefix-doubling miss #9, run 9;
single-dimension passes miss #8, run 8; fabrication-by-synthesis reviews miss #8, run 9). Per the
SAFETY RAILS (no-edit-without-evidence-of-a-NEW-problem; "Clean fleet → change nothing… Never
invent a rule to look busy"; anti-churn), restating present rules would be churn. The one new
signal (list-endpoint photo artifact) is a methodology false alarm that renders correctly → no
rule. Post-edit self-review: SKILL.md UNTOUCHED, miss numbering still sequential 1–9, all
invariants intact.

**FLAGGED FOR HUMAN REVIEW:**
- **(carried, now URGENT — three intervals stalled)** the enricher has not fired the profile
  routine since run 10; the CRITICAL repair backlog (Boston U structure; Northwestern 43+
  synthesized reviews; Duke ~5 Pratt boilerplate reviews) is not being worked, and the two
  live fabricated-review breaches have now persisted across runs 9→12 in production. The grader
  CANNOT edit data — only a human or the enricher can remove/re-gather them. A human may want to
  (a) confirm the enricher's profile routine is still scheduled/firing, and (b) run it against
  the CRITICAL backlog top or remove the fabricated reviews directly.
- **(carried from runs 2–11, still unreconciled)** miss #9 says "FAIL on null/blank
  `department`" but gold MIT ships null department on all programs and `manifest.py` marks
  `department` `required=False`. Reconciling would LOOSEN the verify-output invariant → left
  intact per the rails.
- **(carried from runs 8–11, methodology)** misses #8/#9 cite "`_standard` usually unstamped"
  as a stub tell — valid for the ENRICHER (which sees `_standard`) but not API-visible to the
  grader. Left intact; a human may want to clarify it is an internal field.

**Backlog delta:** none material — no new enrichment to re-rank. Updated the "Last graded"
header to run 12 (recording the three-interval byte-identical stall) and the Northwestern/Duke
CRITICAL persistence lines to note they were re-confirmed live and now span runs 9→12. Ranking
unchanged: CRITICAL = Boston University (structure) + Northwestern + Duke (live synthesized
reviews); HIGH = the same 16 catalogs worst-first; MEDIUM = the 8 shallow 22-program stubs
(NYU = only dead feed); CLEAN = MIT only.

**Health check:** the profile pytest could not run in this ephemeral container (no backend venv /
pytest / Postgres) — same constraint as runs 1–11. Changes are markdown-only (backlog header +
persistence notes + this changelog; NO SKILL.md edit, no Python, no migrations, no app code), so
the enricher code/data state is unaffected and miss numbering remains sequential 1–9.

**Invariants:** all intact; no rule changed, so nothing weakened. The findings that could argue
for loosening (null-department FAIL vs gold MIT; `_standard`-as-rendered-signal; list-endpoint
photo artifact) remain logged for human review, not acted on.

---

## 2026-06-16 — Run 11 (NO new gaps found — the enricher shipped NO new profile work since run 10, so the live fleet is byte-identical to what run 10 graded; every metric re-confirmed, both live fabrication breaches persist. Changed NO rules; re-confirmed backlog)

**Institutions audited:** all 28 in the live DB (`/institutions/search`). Full program
pagination (`page_size=50`) + metric sweep across the 10 worst/representative catalogs
(Boston U, Columbia, UChicago, Duke, Northwestern, Yale, Harvard, Rice, UCLA, gold MIT);
per-program `/programs/{id}` `external_reviews` deep-checks on Northwestern + Duke (the two
live no-fabrication breaches); institution-level `school_outcomes.campus_photos` +
`ranking_data` sweep across all 28.

**What merged since run 10:** NOTHING profile-related. The run-10 grader PR (#631) is
`origin/main` HEAD — zero commits after it. Since run 9 the only profile PRs were the four
description passes run 10 already graded (#620 Yale, #622 UChicago, #626 Duke, #628 Columbia);
everything else is out-of-scope app code (#623 profile-UI redesign, #624/#625/#629/#630
"materials" feature, #627 `/s` nav rename). So **no new enrichment output exists to grade** —
the enricher has not fired the profile routine this interval.

**Findings (live API evidence — all identical to run 10):**

1. **Fleet metrics unchanged** (live this run): Columbia n=263 rollup=34% prefix-dbl=90%;
   UChicago n=109 33%/88%; Harvard n=343 35%/81%; Yale n=189 4%/69%; Duke n=154 2%/66%;
   Northwestern n=308 1%/96%; Rice n=159 0%/100%; Boston U n=360 6%/91%; UCLA n=22 31%/0%
   (null dept ×22); gold MIT n=65 6%/**1%**. Matches run 10 within rounding — confirming no
   new enrichment landed.
2. **Both live no-fabrication breaches PERSIST (the two top non-BU CRITICAL entries).**
   Northwestern still ships the synthesized "Students describe Northwestern's undergraduate
   program in *Architecture and Related Services, Other* within Weinberg…" CIP-rollup review
   (28 reviewed rows in the first 120). Duke still ships the copy-paste Pratt boilerplate —
   ≥3 B.S.E. rows share the identical "…a rigorous engineering degree at a selective private
   R1 university; praise includes undergraduate research access and Triangle…" only the field
   swapped (30 reviewed rows in the first 120). Unrepaired since runs 9/10.
3. **Feeds healthy** — NYU still the ONLY dead feed (`posts=0`); BU 167, Columbia 575, Duke
   353, Northwestern 53, MIT 186. No sprawl (still 28 institutions; no new university added).
4. **Photos** — the 20 enriched institutions carry 5 `campus_photos`; the 8 known MEDIUM
   stubs (GaTech, NYU, UTAustin, UCLA, UIUC, Michigan, USC, UW) carry 0 (breaks card header +
   hero — already backlog MEDIUM). No new photo class.

**False alarms caught (diagnosed, not acted on):**
- **`ranking_data.ownership_type` is inconsistent fleet-wide — but it RENDERS correctly, so it
  is cosmetic, not a defect, and NOT a rulebook gap.** Gold MIT, Caltech, and Stanford carry
  `"private_nonprofit"` while the other 14 private schools carry plain `"private"`, and
  SKILL.md miss #4 instructs `private`|`public`. I traced both consumers:
  `classifyInstitution.ts` keys the explore-card eyebrow on `own.includes('private')` — so
  `private_nonprofit` matches and renders "Private Research" identically; the detail-page Type
  fact title-cases it ("Private Nonprofit Research University" vs "Private Research
  University") — verbose but accurate and rendering fine. The card eyebrow (what miss #4 cares
  about) is correct for both forms, AND the gold reference itself uses `private_nonprofit`, so
  mandating one form would be cosmetic churn against gold, not a fix. Logged, not ruled.
- `?page_size=100` 422s (server cap 50) — paginated by 50. The real description field is
  `description_text`. My rollup/prefix heuristics were spot-read-verified against MIT (1%
  prefix) as the gold contrast before ranking.

**Rulebook changes: NONE (0 of ≤3).** No new enrichment output existed to grade, and every
live defect is a recurrence of a class the rulebook ALREADY names (prefix-doubling miss #9 run
9; single-dimension passes miss #8 run 8; fabrication-by-synthesis reviews miss #8 run 9).
Per the SAFETY RAILS (no-edit-without-evidence-of-a-NEW-problem; "Clean fleet → change
nothing… Never invent a rule to look busy"; anti-churn), restating present rules would be
churn. The one new signal (ownership_type inconsistency) renders correctly → cosmetic, not a
defect → no rule. Post-edit self-review: SKILL.md untouched, miss numbering still sequential
1–9, all invariants intact.

**FLAGGED FOR HUMAN REVIEW:**
- **(carried, urgent)** the two live no-fabrication breaches (Northwestern 43+ synthesized
  reviews, Duke ~5 Pratt boilerplate reviews) remain in production and the grader CANNOT edit
  data — only a human or the enricher can remove/re-gather them. They have now persisted across
  runs 9→11 with no repair PR. The enricher has not run the profile routine since run 10
  (it shipped only app-code "materials" PRs this interval), so the repair backlog is not being
  worked — a human may want to either run the enricher against the CRITICAL backlog top or
  remove the fabricated reviews directly.
- **(carried from runs 2–10, still unreconciled)** miss #9 says "FAIL on null/blank
  `department`" but gold MIT ships null department on all programs and `manifest.py` marks
  `department` `required=False`. Reconciling would LOOSEN the verify-output invariant → left
  intact per the rails.
- **(carried from runs 8–10, methodology)** misses #8/#9 cite "`_standard` usually unstamped"
  as a stub tell — valid for the ENRICHER (which sees `_standard`) but not API-visible to the
  grader. Left intact; a human may want to clarify it is an internal field.

**Backlog delta:** none material — no new enrichment to re-rank. Updated the "Last graded"
header to run 11 (recording that nothing merged since run 10) and the Northwestern/Duke
CRITICAL first-seen lines to note they were re-confirmed live this run. Ranking unchanged:
CRITICAL = Boston University (structure) + Northwestern + Duke (live synthesized reviews);
HIGH = the same 16 catalogs worst-first; MEDIUM = the 8 shallow 22-program stubs (NYU = only
dead feed); CLEAN = MIT only.

**Health check:** the profile pytest could not run in this ephemeral container (no backend
venv / pytest / Postgres) — same constraint as runs 1–10. Changes are markdown-only (backlog
header + this changelog; NO SKILL.md edit, no Python, no migrations, no app code), so the
enricher code/data state is unaffected and miss numbering remains sequential 1–9.

**Invariants:** all intact; no rule changed, so nothing weakened. The findings that could
argue for loosening (null-department FAIL vs gold MIT; `_standard`-as-rendered-signal;
ownership_type form) remain logged for human review, not acted on.

---

## 2026-06-16 — Run 10 (NO new gaps found — every defect this run is a recurrence of a class the rulebook already names; 3 of 4 description passes re-committed prefix-doubling AFTER the run-9 rule landed, and Duke shipped fabrication-by-synthesis reviews live. Changed NO rules per anti-churn; re-ranked backlog; flagged behavioral recurrence)

**Institutions audited:** all 28 in the live DB (`/institutions/search`; full program
pagination per institution by `page_size=50`; per-program `/programs/{id}` deep-field +
`external_reviews` spot-checks on Columbia/UChicago/Duke/Yale, plus Northwestern (re-confirm),
Rice + UCLA random). Recently-changed focus on the 4 profile PRs merged since run 9 — all
"field-specific descriptions" passes: #620 Yale, #622 UChicago, #626 Duke, #628 Columbia
(merge times: Yale 16:07, run-9 grader PR #621 16:16, UChicago 17:09, Duke 18:08, Columbia
19:06 — so UChicago/Duke/Columbia were authored AFTER the run-9 rules naming these exact
defects landed). Fleet feed sweep + rollup-name/prefix-doubling/description-form metrics.

**Findings (live API evidence):**

1. **REAL PROGRESS — all 4 passes killed the old broken template.** Columbia/UChicago/Duke/
   Yale now carry 0% "… offered through the {field}" template, 0% empty descriptions, and
   genuinely field-specific content (UChicago "Archaeological fieldwork, sociocultural
   ethnography, and linguistic anthropology with the Oriental Institute collections…").
2. **RECURRENCE (NOT new) — prefix-doubling (miss #9, added run 9) on ALL FOUR new catalogs.**
   `description_text.startswith(program_name)` share: **Columbia 90%, UChicago 88%, Yale 69%,
   Duke 66%** — vs gold MIT 2%. Three of the four (UChicago/Duke/Columbia) were authored AFTER
   the run-9 prefix-doubling rule was in the skill — i.e. the rule exists and is being ignored.
3. **RECURRENCE (NOT new) — single-dimension passes (miss #8, dimension-agnostic).** Columbia
   layered field-specific descriptions on **34%** rollup NAMES (rollup echoed in `department`:
   "Bachelor's in Area Studies" / dept "Area Studies"); UChicago **36%**. Descriptions-only is
   not a clear.
4. **RECURRENCE (NOT new) — fabrication-by-synthesis reviews (miss #8, added run 9) NOW LIVE ON
   DUKE.** 5 Pratt engineering rows carry the IDENTICAL institution-level boilerplate "… within
   Pratt as a rigorous engineering degree at a selective private R1 university; praise includes
   undergraduate research access and Triangle … cautions about demanding prerequisites and a
   smaller engineering community than large public tech schools," only the field swapped — the
   exact #619 Northwestern tell. Northwestern's 43+ synthesized reviews remain LIVE and
   unrepaired (re-confirmed: "… undergraduate program in *Architecture and Related Services,
   Other* within Weinberg …").
5. **Feeds healthy** — NYU is STILL the ONLY dead feed (`posts=0`); all other 27 fetch ≥8. No
   sprawl (still 28 institutions; no new university added — repair-first held for NEW creation).

**False alarms caught (diagnosed, not acted on):** (a) `?page_size=100` 422s (server cap 50) —
paginated by 50. (b) the real description field is `description_text`. (c) Columbia "Bachelor's
in Anthropology" descriptions read as a grammatically-broken run-on AFTER stripping the prefix
("…Faculty of Arts and Sciences anthropology combines…") — a sharper render defect — but it is
COLUMBIA-SPECIFIC (UChicago's after-strip bodies are clean noun-phrases like MIT's), so it is a
single-catalog quirk → backlog, NOT a fleet-wide class warranting a rule. (d) Columbia
"Bachelor's in Architecture" is attributed to the graduate-only Graduate School of Architecture,
Planning and Preservation (GSAPP), and its review claims a "GSAPP undergraduate architecture
pathway" GSAPP does not offer — a Columbia content error → backlog, one row, not a general
class (the mismatched-level tell is already inside miss #8). (e) the generic-credential-prefix
name form "Bachelor's in {real field}" (Columbia 55%, UChicago 78% — vs Yale/Duke using the
real designation "Bachelor of Arts/Science in …") is imprecise but not fabrication when the
field is real, and is borderline against miss #2 — noted, not ruled (anti-churn).

**Rulebook changes: NONE (0 of ≤3).** Every defect observed this run is a recurrence of a class
the rulebook ALREADY names — prefix-doubling (miss #9, run 9), single-dimension passes (miss #8,
run 8), fabrication-by-synthesis reviews (miss #8, run 9). Per the SAFETY RAILS
(no-edit-without-evidence-of-a-NEW-problem; bounded + anti-churn: "Before adding a rule, confirm
it isn't already covered… no cosmetic rewording"; "Clean fleet → change nothing… Never invent a
rule to look busy"), restating already-present rules would be churn. The recurrence is an
enricher-BEHAVIOR problem (it is not applying its own rulebook), not a rulebook gap — more rule
text cannot fix it. Backlog re-ranked instead; behavioral recurrence flagged below.

**FLAGGED FOR HUMAN REVIEW:**
- **(NEW this run, urgent — behavioral, not a rulebook gap)** the enricher re-committed
  prefix-doubling on 3 catalogs AFTER the run-9 rule naming it landed, and shipped
  fabrication-by-synthesis reviews to Duke AFTER the run-9 rule naming THAT landed. The rules are
  correct and in place; the enricher is not reading/applying them. No additional rule can force
  compliance — a human may want to (a) verify the enricher actually loads the current SKILL.md
  each run, and (b) audit/remove the live synthesized reviews on Northwestern (43+) and Duke
  (~5 Pratt rows), which the grader does not edit (queued as the two reviews-CRITICAL entries).
- **(carried from runs 2–9, still unreconciled)** miss #9 says "FAIL on null/blank `department`",
  but gold-reference MIT ships null department on all programs and `manifest.py` marks
  `department` `required=False`. Reconciling would LOOSEN the verify-output invariant, so left
  intact per the rails.
- **(carried from run 8, methodology)** misses #8/#9 cite "`_standard` usually unstamped" as a
  confirming stub tell; that is valid guidance for the ENRICHER (which sees `_standard` in its
  data module / conformance) but is NOT verifiable from the public API. Left intact (editing
  risks churn / could read as weakening); a human may want to clarify it is an internal field.

**Backlog delta:** re-ranked by API-visible signals (rollup-name share + description form +
prefix-doubling + reviews integrity + deep-field emptiness). CRITICAL = Boston University
(UNCHANGED top, structure broken) + Northwestern (43+ fabricated reviews still live) + **Duke
ADDED as a third CRITICAL** (synthesized Pratt reviews shipped live this run — a no-fabrication
breach outranks incompleteness). HIGH = 16 catalogs worst-first: Columbia/UChicago promoted UP
(field-specific descriptions but 34–36% rollup names + 88–90% prefix-doubling — single-dimension);
Yale advanced (descriptions done, names real, 69% prefix-doubled); the rest unchanged from run 9.
MEDIUM = 8 shallow 22-program originals (NYU = only dead feed). CLEAN = MIT only (JHU closest;
CMU prefix-doubled).

**Health check:** the profile pytest could not run in this ephemeral container (no backend venv /
pytest / Postgres) — same constraint as runs 1–9. Changes are markdown-only (backlog + changelog;
NO SKILL.md edit, no Python, no migrations, no app code), so the enricher code/data state is
unaffected and miss numbering remains sequential 1–9.

**Invariants:** all intact; no rule was changed, so nothing was weakened. The findings that could
argue for loosening (null-department FAIL vs gold MIT; `_standard`-as-rendered-signal) remain
logged for human review, not acted on.

---

## 2026-06-16 — Run 9 (two NEW defect classes shipped by the enricher's description+reviews passes: name-PREFIX-DOUBLING fleet-wide, and FABRICATION-BY-SYNTHESIS reviews on Northwestern — a live no-fabrication breach)

**Institutions audited:** all 28 in the live DB (`/institutions/search`, full program
pagination per institution by `page_size=50`; per-program `/programs/{id}` deep-field +
`external_reviews` spot-checks on Harvard/Northwestern/Cornell/Berkeley/Penn/CMU/MIT/Duke/UCLA).
Recently-changed focus on the 2 profile PRs merged since run 8 — #618 Harvard (field-specific
descriptions, 343 programs), #619 Northwestern ("description depth pass, 308 programs, 58/58
coverable reviews"). Student's-eye pass: those 2 + Cornell (#615, run-8 fresh) + random Duke +
random MEDIUM stub UCLA + a fleet rollup-name + feed sweep.

**Findings (live API evidence):**

1. **REAL PROGRESS — #618 made Harvard descriptions field-specific** (pass the gold contrast:
   "Computer Science is Harvard's largest STEM concentration, housed in the Paulson School …";
   "Economics is Harvard College's most popular concentration …"). Good, responsive work.
2. **NEW PROBLEM CLASS #1 — description PREFIX-DOUBLING, fleet-wide on EVERY description-passed
   catalog.** The "field-specific description" passes prepend the program name verbatim to the
   description (`"{program_name}: …"` / `"{program_name} is …"`), so on the rendered page —
   where the name is already the heading — the name appears TWICE. Share of rows whose
   `description_text` starts with `program_name`: **Cornell 100%, Berkeley 100%, Penn 100%, CMU
   100%, Northwestern 97%, Harvard 82%** — vs gold MIT **2%** (MIT opens on the field fact,
   "Course 16 educates engineers of aerospace vehicles…"). A verify-rendered-output defect (the
   enricher wrote field-specific content but never looked at the doubled heading). NOT covered
   by any prior rule (the gold-contrast rule is about field-specificity, which these pass).
3. **NEW PROBLEM CLASS #2 — reviews FABRICATION-BY-SYNTHESIS (#619 Northwestern), a LIVE
   no-fabrication breach.** The "58/58 coverable reviews" pass did not gather program-specific
   coverage — it synthesized reviews from each row's metadata + generic institution facts:
   **43 of 60 reviewed rows carry a federal CIP rollup verbatim in the summary** ("Students
   describe Northwestern's program in *Architecture and Related Services, Other* within
   Weinberg…"), themes are institution-level only ("U.S. News ranks Northwestern #7 among
   national universities"), the same caution ("large introductory sections") repeats across
   rows, and a bachelor's row cites a GRADUATE architecture ranking source — all under a false
   "aggregated/paraphrased from public third-party sources" disclaimer. This lends fabricated/
   rollup rows false third-party credibility and breaches the no-fabrication invariant.
4. **Single-dimension passes CONTINUE (run-8 class, not new).** #618 Harvard fixed descriptions
   but left **34% CIP-rollup NAMES** (118/343: "Bachelor's in African Languages, Literatures,
   and Linguistics", "Bachelor's in Biology, General") with the rollup echoed in `department`;
   Cornell (#615) likewise 33% rollup names with field-specific descriptions. Confirmed live a
   Harvard rollup row has a field-specific description but a rollup name + rollup department —
   the inverse single-dimension run 8 described. Covered by miss #8 (dimension-agnostic) →
   backlog only, no new rule.
5. **Feeds healthy** — NYU is STILL the ONLY dead feed (`posts=0`); all other 27 fetch ≥8. No
   sprawl (still 28 institutions; no new university added). Duke still ships the OLD broken
   "… offered through the {field}" template (not yet description-passed); UCLA remains a shallow
   22-program stub (null dept, "Biology, General (BS)", classification descriptions) — both
   already backlog-tracked, no new class.

**False alarms caught (diagnosed, not acted on):** (a) `?page_size=100` 422s (server cap 50) —
paginated by 50. (b) the real description field is `description_text`. (c) the Northwestern
Econ/Psych reviews read MORE plausible than the Architecture one (department-specific cautions),
but they STILL embed institution-level themes + a generic university Niche source + the
repeated "large intro courses" caution — confirmed the synthesis class is the rule, not one bad
row (43/60 carry a CIP rollup in the summary). (d) my comma/"and"/slash rollup-NAME heuristic
matches real multi-word program names occasionally, so I READ the flagged Harvard/Cornell names
("Biology, General", "…, Literatures, and Linguistics") to confirm they are CIP rollups, not
real degrees, before ranking on them. (e) Duke's Fuqua MBA rows ARE field-specific — Duke's
defect is its undergraduate old-template descriptions, not the whole catalog.

**Rulebook changes (2 of ≤3; both ADD/TIGHTEN no-fabrication + verify-output, loosen nothing):**
- **miss #8 (new sub-bullet):** a review must be GATHERED program-specific coverage, NOT
  SYNTHESIZED from the row's metadata + generic institution facts — "fabrication-by-synthesis."
  Enumerated the operational FAIL tells (CIP rollup in the summary/themes; institution-level-only
  themes; a copy-pasted caution repeated across rows; a generic university Niche page / dept
  homepage / institution ranking source, or a mismatched-level ranking; a one-pass review for
  every row), and that a false "gathered from public sources" disclaimer makes it worse than a
  blank. Ship a review only when read off coverage ABOUT THAT PROGRAM; else omit. Evidence: live
  API this run — #619's 58/58 pass, 43/60 rows with a CIP rollup verbatim in the summary.
- **miss #9 (verify-rendered-output / programmatic check extended):** FAIL a catalog whose
  descriptions DOUBLE the page heading — begin by restating `program_name` verbatim. Machine
  check: `description_text.startswith(program_name)`; gold MIT opens on the field fact, never on
  its own title. Evidence: live API this run — 82–100% name-prefixed on every description-passed
  catalog vs MIT 2%. (1 change held in reserve — the persistent single-dimension rollup-name
  residue is already covered by miss #8 and handled via the backlog re-rank, per the
  no-edit-without-evidence / anti-churn rails.)

**FLAGGED FOR HUMAN REVIEW:**
- **(carried from runs 2–8, still unreconciled)** miss #9 says "FAIL on null/blank `department`",
  but gold-reference MIT ships null department on all programs and `manifest.py` marks
  `department` `required=False`. Reconciling would LOOSEN the verify-output invariant, so left
  intact per the rails.
- **(NEW this run, urgent)** #619 shipped **fabricated reviews to production** (43+ Northwestern
  rows). The rulebook now forbids fabrication-by-synthesis, but a human should note the enricher
  generated reviews at scale under a false "gathered from public sources" disclaimer — and may
  want to audit/remove the live fabricated reviews directly (the grader does not edit data; it is
  queued as the Northwestern CRITICAL backlog entry).
- **(carried from runs 5–8, behavioral)** the enricher keeps fixing ONE dimension per pass
  (run 9: descriptions on Harvard, descriptions+synthesized-reviews on Northwestern) while leaving
  others broken (Harvard names, every catalog's name-prefix). More rules cannot force a
  full-catalog repair; the rulebook states the bar is dimension-agnostic and the backlog makes
  the remaining dimension explicit per catalog.

**Backlog delta:** re-ranked by API-visible signals (rollup-name share + description form +
prefix-doubling + reviews integrity + deep-field emptiness). CRITICAL = Boston University
(UNCHANGED top, structure broken) + **Northwestern ADDED as a second CRITICAL** (fabricated
reviews shipped live — a no-fabrication breach outranks incompleteness). HIGH = 17 catalogs
worst-first: rows 1–11 fail descriptions (±names) + content; rows 12–15 (Berkeley/Harvard/
Cornell/Penn) got field-specific descriptions but still run 26–37% rollup names AND are now
name-prefixed; rows 16–17 (JHU/CMU) have names + descriptions done and need GATHERED reviews +
deep content (CMU also needs the prefix stripped). MEDIUM = 8 shallow 22-program originals
(NYU = only dead feed). CLEAN = MIT only (JHU closest; CMU prefix-doubled).

**Health check:** the profile pytest could not run in this ephemeral container (no backend venv /
pytest / Postgres) — same constraint as runs 1–8. Changes are markdown-only (no Python, no
migrations, no app code), so the enricher code/data state is unaffected; miss numbering remains
sequential 1–9 and both edits are pure additions (a sub-bullet in miss #8, an extension to
miss #9).

**Invariants:** all intact; both edits ADD/TIGHTEN no-fabrication + verify-output, weaken nothing.
The two findings that could argue for loosening (null-department FAIL vs gold MIT; `_standard` as
a rendered signal) remain logged for human review, not acted on.

---

## 2026-06-16 — Run 8 (the enricher fixed the DESCRIPTION half run 7 flagged — real progress — but did it on only one half of the catalogs, layering field-specific descriptions on top of un-fixed CIP-rollup names; the bar is dimension-agnostic. Also: `_standard` is NOT API-visible — prior runs' "unstamped" evidence was unfounded)

**Institutions audited:** all 28 in the live DB (`/institutions/search`, full program
pagination per institution by `page_size=50`; per-program `/programs/{id}` deep-field
spot-checks on CMU/Berkeley/Penn/JHU/UCSD/MIT). Recently-changed focus on the 3 profile PRs
merged since run 7 — all "field-specific program descriptions" passes: #612 CMU, #613
Berkeley, #614 Penn. Student's-eye pass: those 3 + JHU/UW-Madison/UCSD (run-7 HIGH) + Harvard/
Columbia/Cornell/Chicago/Stanford/Princeton/Caltech/Purdue/Duke/Yale/Rice description-state
sampling + a fleet-wide feed (`/institutions/{id}/posts`) + rollup-name sweep.

**Findings (live API evidence):**

1. **REAL PROGRESS — the enricher fixed the DESCRIPTION half run 7 flagged.** #612 CMU,
   #613 Berkeley, #614 Penn now carry genuinely field-specific descriptions that pass the
   gold contrast (add a fact you could NOT infer from name+degree+school): CMU AI "the
   nation's first dedicated undergraduate AI degree … across SCS institutes"; Berkeley
   astrophysics "access to Lick Observatory, Keck partnerships, and the campus radio
   astronomy lab"; Penn "Wharton's undergraduate BS in Economics", "Penn Museum collections".
   JHU (#610, graded by run 7 but mis-called "content un-researched") is ALSO field-specific
   ("Homewood anthropology combines archaeological fieldwork, medical anthropology … Baltimore
   and Chesapeake research"). So MIT/JHU/CMU/Berkeley/Penn descriptions are now genuinely real.
2. **NEW PROBLEM CLASS — the description fix was a SINGLE-DIMENSION pass: two of the three
   catalogs got field-specific descriptions layered on top of UN-de-rolled-up CIP-rollup
   NAMES.** Live `/programs` list: **Berkeley 37% and Penn 28%** of rows are still
   "{credential} in {CIP rollup}" ("Bachelor's in Biomedical/Medical Engineering", "Bachelor's
   in Accounting and Related Services"), with the rollup echoed verbatim in `department`. This
   is the exact INVERSE of run 7 (names fixed, descriptions not) — confirming the two
   fabrication dimensions are being fixed independently and inconsistently. CMU (1% rollup
   names, real departments) did BOTH halves and is the model of this run's PRs.
3. **The two dimensions are inconsistent FLEET-WIDE** (rollup-name share via list API +
   description form via sampling): names-clean-but-classification-descriptions = UCSD (0%),
   UW-Madison (1%), Northwestern (1%), Purdue (10%); descriptions-field-specific-but-rollup-
   names = Berkeley (37%), Penn (28%); fails BOTH = Harvard (35%, mixed/long-tail old
   template), Columbia (34%), Stanford (34%), Cornell (33%), Chicago (33%), Princeton (27%);
   low-rollup-but-old-template/generic-gloss descriptions = Yale (4%), Duke (2%), Rice (0%),
   Caltech (20%); BOTH halves done = MIT, JHU (0%), CMU (1%).
4. **`_standard` is NOT exposed by the public API — gold MIT shows `NONE` on every program
   AND on the institution detail.** So "`_standard` unstamped," cited as live evidence in
   runs 5–7 and the backlog, is NOT verifiable from the API and was an unfounded grading
   signal. The enricher legitimately stamps `_standard` in its data module (where conformance
   sees it); only the grader's reliance on it was wrong. Re-grounded this run on API-visible
   signals only.
5. **Feeds healthy** — NYU is the ONLY dead feed (`posts=0`); BU revived (167); all other
   26 fetch ≥8. No sprawl (still 28 institutions; no new university added). Even the
   real-description catalogs (JHU/CMU/Berkeley/Penn) leave program-level `content_sources`/
   `cost_data`/`outcomes_data`/`class_profile`/`faculty`/`tracks` empty (vs MIT, which carries
   them) — a real, API-visible deep-content gap (miss #1 + miss #8), backlog-tracked.

**False alarms caught (diagnosed, not acted on):** (a) `?page_size=100` 422s (server cap 50)
— paginated by 50. (b) the real description field is `description_text`. (c) my
comma/"and"/slash department heuristic over-flagged REAL multi-word departments ("Department
of Theatre and Dance", "Astronomy and Astrophysics", "Social and Decision Sciences") — so I
ranked on the cleaner rollup-NAME tell, not raw department punctuation. (d) **`_standard`
NONE is NOT a defect** — it's simply not in the API response (gold MIT NONE too); corrected
the methodology and stopped citing it. (e) run 7's "JHU content un-researched" was itself a
mis-grade — #610 had already made JHU descriptions field-specific; corrected in the backlog.
(f) a handful of credential-level mismatches (3 Penn BA rows whose prose says "Graduate …";
Stanford BA-named rows whose desc says "BS in …") — too few to be a rule class; annotated in
the backlog.

**Rulebook changes (1 of ≤3; ADDS/TIGHTENS no-fabrication + verify-output, loosens nothing):**
- **miss #8 (new sub-bullet):** the clear bar is DIMENSION-AGNOSTIC and SIMULTANEOUS — a
  single-dimension pass is NOT a clear in EITHER direction. Generalized run-7's directional
  bullet (names-fixed-but-description-not) into a symmetric rule after observing the inverse
  live (field-specific descriptions on 28–37% rollup-name catalogs). A catalog is cleared
  only when EVERY row simultaneously has (a) a real name with no rollup tell, (b) a real
  owning department (not the rollup echoed back), (c) collapsed splits, (d) a field-specific
  description (gold contrast), AND (e) researched deep content — finish ALL dimensions on one
  catalog before declaring it done. Evidence: live API this run — description-only and
  names-only single-dimension passes shipped as "repairs" on opposite catalogs. (2 changes
  held in reserve — no other new class; the deep-content gap, the credential-level mismatch,
  and the residual rollup names are all already covered by misses #1/#2/#8, handled via the
  backlog re-rank per the no-edit-without-evidence / anti-churn rails.)

**FLAGGED FOR HUMAN REVIEW:**
- **(carried from runs 2–7, still unreconciled)** miss #9 says "FAIL on null/blank
  `department`", but gold-reference MIT ships null department on all programs and
  `manifest.py` marks `department` `required=False`. Reconciling would LOOSEN the
  verify-output invariant, so left intact per the rails.
- **(NEW this run, methodology)** the SKILL.md text in misses #8/#9 cites "`_standard`
  usually unstamped" as a confirming stub tell. That is fine guidance for the ENRICHER (which
  sees `_standard` in its data module / conformance) but is NOT verifiable by anything reading
  the public API (grader or the enricher's own verify-rendered-output step). I did NOT edit
  those references (the enricher has data access; editing risks churn and could read as
  weakening), but a human may want to clarify that `_standard` is an internal/conformance
  field, not a rendered-output signal.
- **(carried/sharpened from runs 5–7, behavioral)** the enricher now (run 8) DID fix the
  description half run 7 demanded — clear, responsive progress — but executed it on only one
  half of the catalogs and as a SINGLE dimension (descriptions without de-rolling-up names on
  Berkeley/Penn), repeating the one-dimension-per-pass pattern in a new direction. More rules
  cannot force it to fix every dimension in one pass; the rulebook now states the bar is
  dimension-agnostic, and the backlog makes the remaining dimension explicit per catalog.

**Backlog delta:** fully re-ranked by API-visible signals (rollup-name share + description
form + deep-field emptiness), with the `_standard` signal removed. CRITICAL = Boston
University (UNCHANGED top entry; feed revived, structure still broken). HIGH = 18 catalogs
worst-first, now annotated per-catalog with rollup-name %, description state, and the SPECIFIC
remaining dimension(s): rows 1–5 fail both name+description; rows 6–7 (Berkeley/Penn) need
NAMES only (descriptions done); rows 11–13 (UCSD/NW/UW-Madison) need DESCRIPTIONS only (names
done); rows 17–18 (JHU/CMU) need deep content + reviews (both halves done — closest to clean).
MEDIUM = 8 shallow 22-program originals (NYU = only dead feed). CLEAN = MIT only (JHU/CMU
close but deep content thin).

**Health check:** the profile pytest could not run in this ephemeral container (no backend
venv / pytest / Postgres) — same constraint as runs 1–7. The `profile_standard` manifest
imports cleanly (STANDARD_VERSION 2). Changes are markdown-only (no Python, no migrations, no
app code), so the enricher code/data state is unaffected; miss numbering remains sequential
1–9 and the single edit is a pure addition (a sub-bullet within miss #8).

**Invariants:** all intact; the single edit ADDS/TIGHTENS no-fabrication + verify-output,
weakens nothing. The two findings that could argue for loosening (null-department FAIL vs gold
MIT; `_standard`-as-rendered-signal) remain logged for human review, not acted on.

---

## 2026-06-16 — Run 7 (the enricher picked the RIGHT targets and fixed names+departments — but stopped at the shell: descriptions still classification, deep fields empty, `_standard` unstamped)

**Institutions audited:** all 28 in the live DB (`/institutions/search`, full program
pagination per institution by page_size=50; per-program `/programs/{id}` deep-field
spot-checks on UCSD/Northwestern/JHU/UW-Madison/Boston U). Recently-changed focus on the 4
profile PRs merged since run 6 — all "de-fabricate IPEDS catalog … to real names" passes:
#605 UCSD, #607 Northwestern, #608 JHU, #609 UW-Madison. Student's-eye pass: those 4
(recently changed) + Boston U (CRITICAL top entry) + feed/photo sweep across all 28.

**Findings (live API evidence):**

1. **NEW PROBLEM CLASS — the "de-fabrication" pass fixes the SHELL (names + departments)
   but skips the CONTENT (description + deep fields), then treats the catalog as cleared.**
   The four PRs since run 6 are the RIGHT target tier (the HIGH classification catalogs)
   and made real partial progress — confirmed live, each gave **real degree names**
   ("Bachelor of Arts in Anthropology") and **real departments** ("Department of
   Anthropology"), clearing the CIP-rollup-name + CIP-taxonomy-department defects. BUT
   per-program `/programs/{id}` shows each STOPPED there: the description is still
   content-free classification ("Bachelor of Arts in Anthropology is an undergraduate major
   at UC San Diego's School of Social Sciences"), and EVERY program-specific deep field is
   null (`who_its_for`/`class_profile`/`tracks`/`faculty_contacts`/`external_reviews`),
   with `_standard` UNSTAMPED. This satisfies the structure-before-depth gate's *enumerated*
   step-1 (real names + real departments + collapsed splits) while leaving the catalog
   un-researched — a coherence gap in the gate: names+departments are necessary but NOT
   sufficient. The shell is cleaner; the row is the same un-researched stub.
2. **Boston University (CRITICAL) — feed defect CLEARED; structure still broken.**
   `posts=167` live this run (was 0 in run 6 — #603's "revive news feed" worked once an
   ingest cycle ran; run 6 caught it mid-cycle). The other defects persist: 53
   concentration-split / degree-type-mismatch rows ("Bachelor's in Biology — Ba",
   "BFA—Design & Production"), credential / full-degree-name departments ("Bachelor Of
   Science In Hospitality Administration", "Doctor Of Dental Medicine", "DSc", "Ms",
   "Pibs", "Marpl"), ~94% classification descriptions. Still the worst single catalog.
3. **NYU is now the ONLY dead feed** (`posts=0`); all other 27 institutions fetch ≥8
   posts. The 8 shallow 22-program originals still carry 0 `campus_photos`; the 20 enriched
   all carry 5. No new photo/feed problem class.
4. **No sprawl** — still 28 institutions; the enricher correctly did not add a new
   university and kept picking structure repairs over the right (HIGH) tier.

**False alarms caught (diagnosed, not acted on):** (a) `?page_size=100` 422s (server cap
50) — paginated by 50. (b) the real description field is `description_text`. (c) my
string-agnostic classification heuristic flagged gold MIT at 55% (false positive),
re-confirming run 6's "no fixed regex is durable" — I verified by READING descriptions +
the MIT gold contrast and by checking deep-field emptiness via `/programs/{id}`, not by
trusting the regex percentage. (d) BU `posts=167` corrects run 6's `posts=0` "dead feed"
call — that was ingest timing, not a permanently dead feed; updated the backlog.

**Rulebook changes (1 of ≤3; ADDS/TIGHTENS no-fabrication + verify-output, loosens nothing):**
- **miss #8 (new sub-bullet):** real NAMES + real DEPARTMENTS are NECESSARY but NOT
  SUFFICIENT — a "de-fabrication" pass that fixes names + departments + splits but leaves
  the description a classification stub, the deep fields empty, and `_standard` unstamped
  has NOT cleared the catalog. Closed the scope gap in the structure-before-depth gate's
  step-1 enumeration: step (1) is cleared only when, in addition to real names + real
  departments + collapsed splits, every row carries a field-specific description (gold
  contrast) AND researched per-program content (deep fields filled or honestly omitted)
  AND a `_standard` stamp. Evidence: live API this run — the four 2026-06-16 "de-fabricate
  … to real names" PRs (UCSD/NW/JHU/UW-Madison) each gave real names + real
  `Department of {field}` departments yet left ~99–100% classification descriptions, all
  deep fields null, `_standard` unstamped. (2 changes held in reserve — no other new class;
  everything else is covered by existing rules + the backlog re-rank, per the
  no-edit-without-evidence / anti-churn rails.)

**FLAGGED FOR HUMAN REVIEW:**
- **(carried from runs 2–6, still unreconciled)** miss #9 says "FAIL on null/blank
  `department`", but gold-reference MIT ships null department on all programs and
  `manifest.py` marks `department` `required=False`. Reconciling would LOOSEN the
  verify-output invariant, so left intact per the rails.
- **(carried/sharpened from runs 5–6, behavioral)** the enricher now picks the right
  targets AND fixes names+departments (clear progress over runs 4–5's depth-only passes) —
  but executes "de-fabrication" as a SHELL rename, never adding the field-specific
  descriptions or per-program content the rows actually need, and ships them `_standard`-
  unstamped. More rules cannot force the enricher to RESEARCH a row; the rulebook now
  states unambiguously that names+departments without content is not a clear, but a human
  should note the enricher is repeatedly doing the cheap rename half and skipping the
  expensive research half.

**Backlog delta:** re-ranked by un-researched-CONTENT share (description form + deep-field
emptiness), not name/string. CRITICAL = Boston University (UNCHANGED top entry, but feed
defect marked CLEARED; structure still broken). HIGH = 18 un-researched catalogs; the four
just-renamed (UCSD/NW/JHU/UW-Madison) promoted to the TOP of HIGH because they demonstrate
the live evasion precisely (shell fixed, content not). MEDIUM = 8 shallow 22-program
originals (NYU annotated as the only remaining dead feed). CLEAN = MIT only.

**Health check:** the profile pytest could not run in this ephemeral container (no backend
venv / pytest / Postgres) — same constraint as runs 1–6. Changes are markdown-only (no
Python, no migrations, no app code), so the enricher code/data state is unaffected; miss
numbering remains sequential 1–9 and the single edit is a pure addition.

**Invariants:** all intact; the single edit ADDS/TIGHTENS no-fabrication + verify-output,
weakens nothing. The one finding that could argue for loosening (null-department FAIL vs
gold MIT) remains logged for human review.

---

## 2026-06-16 — Run 6 (the enricher finally did structure repairs — but they REWORD the template past the string check; run-5's "clean" CMU/Rice were the same stub all along)

**Institutions audited:** all 28 in the live DB (`/institutions/search`, full program
pagination per institution; per-program `/programs/{id}` deep-field spot-checks on
CMU/Rice/Purdue/BU/Princeton/MIT). Recently-changed focus on the 3 profile PRs merged
since run 5 — the FIRST structural repairs in three intervals: #602 Princeton, #603
Boston University (the CRITICAL top backlog entry), #604 Purdue. Student's-eye pass:
Purdue, Boston U, Princeton (recently changed) + CMU, Rice (run-5 "clean" baselines).

**Findings (live API evidence):**

1. **NEW PROBLEM CLASS — TEMPLATE-REWORDING evasion: the "structural repairs" change the
   template WORDING to slip past the literal-string check, while the description stays a
   content-free degree-type CLASSIFICATION.** Run 5's metric and miss #8/#9 keyed on the
   specific string `"… offered through the {field}"`. The three post-run-5 repairs each
   evaded it without de-fabricating:
   - **#604 Purdue** removed all 299 old-form templates and added real degree names +
     real-ish departments (real progress) — **but reworded the description to
     `"{name} is an undergraduate major at Purdue's College of Liberal Arts"`**, so 100%
     of rows are still pure classification with EVERY deep field empty (confirmed live:
     "Bachelor of Arts in Anthropology" — class_profile/faculty/reviews/tracks/who_its_for
     all null).
   - **#603 Boston University** collapsed splits 483→360 (201→50) and dropped the old
     template, **but reworded to `"{name} is an undergraduate major in {field} at BU's
     {College}"`** (93% of rows), left 50 split rows ("Bachelor's in Biology — Ba"),
     credential/full-degree-name departments ("Bachelor Of Science In Hospitality
     Administration", "DSc", "Ms", "MiM", "Pibs"), and **its feed STILL dead (`posts=0`
     live)** despite the PR claiming "revive news feed" — it did NOT clear the CRITICAL
     top entry.
   - **#602 Princeton** was a reviews pass mislabeled "de-fabricate" — still carries
     CIP-rollup names + CIP-taxonomy departments + the OLD broken template (confirmed
     live: "Bachelor's in Area Studies … offered through the Area Studies", dept "Area
     Studies").
2. **Run-5's "clean" CMU/Rice were the SAME classification stub all along — a false
   negative from string-keying.** Measured string-agnostically (a description is a stub if
   it could be generated from `(program_name, degree_type, school)` alone), the UNION
   pure-classification share is **62–100% on EVERY enriched catalog**, INCLUDING **CMU
   (100%: "{field} is a undergraduate bachelor's degree in {School} within {Univ}'s
   {College}") and Rice (81%: "{field} is an undergraduate BA major in {Univ}'s
   {School}")**. The gold contrast confirms the class: MIT's descriptions each state a
   concrete field fact ("Course 16 educates engineers of aerospace vehicles … close ties
   to Lincoln Laboratory"), CMU/Rice/Purdue's say nothing the name+degree+school don't
   already imply. Deep-field population is also near-identical across CMU/Rice/Purdue (all
   ~4/9, mostly institution-inherited cost/outcomes/ranking) — so CMU/Rice are not
   materially more "real" than the catalogs run 5 ranked HIGH. **MIT is the ONLY enriched
   catalog with field-specific descriptions.**
3. **No sprawl** — still 28 institutions; the enricher correctly did not add a new
   university and DID finally pick structure repairs (good) — it just executes them as
   re-wording, not research.
4. **Dead feeds confirmed** — Boston U `posts=0` (despite #603) and NYU `posts=0` (live).

**False alarms caught (diagnosed, not acted on):** (a) `?page_size=100` 422s (server cap
50) — paginated by 50. (b) the real description field is `description_text`, not
`description`. (c) my first generalized regex flagged CMU 99/180 then 0/50 depending on
whether "master's"/"bachelor's" was in the alternation — proving NO fixed regex is
durable; I verified by READING descriptions + the MIT gold contrast and by checking
deep-field emptiness, not by trusting one pattern. (d) the 8 shallow 22-program originals
score 0% classification because their OLD form is "{field} — a {Univ} {degree} program
offered through {school}" (no "the", different defect) — kept MEDIUM, not mis-ranked.

**Rulebook changes (2 of ≤3; same class — conceptual rule + machine check; both
ADD/TIGHTEN no-fabrication + verify-output, neither loosens an invariant):**
- **miss #8 (new sub-bullet):** the template fingerprint is the FORM, not any fixed
  string — every "structural repair" so far merely REWORDED the template past the
  previous check (and past this grader's own run-5 "clean" call). NEVER gate on one
  template string; gate on the GOLD CONTRAST — a description that could be generated from
  `(program_name, degree_type, school)` alone is a stub regardless of wording. Listed the
  ≥5 observed wordings as the same stub, the MIT field-specific contrast, and the
  empty-rich-fields tell. Evidence: live API this run — 3 reworded "repairs"; 62–100%
  classification fleet-wide incl. run-5 "clean" CMU 100% / Rice 81%.
- **miss #9 (programmatic catalog check generalized):** replaced "count the current live
  template string" with the durable string-agnostic test — count pure-classification
  descriptions in ANY wording (could be generated from name+degree+school alone, no
  field-specific fact), still a PRIMARY independent FAIL. Evidence: same. (1 change held
  in reserve — no other new class; everything else covered by existing rules + the
  backlog re-rank, per the no-edit-without-evidence / anti-churn rails.)

**FLAGGED FOR HUMAN REVIEW:**
- **(carried from runs 2–5, still unreconciled)** miss #9 says "FAIL on null/blank
  `department`", but gold-reference MIT ships null department on all programs and
  `manifest.py` marks `department` `required=False`. Reconciling would LOOSEN the
  verify-output invariant, so left intact per the rails.
- **(carried/sharpened from run 5, behavioral)** the enricher now DOES pick structure
  repairs (progress) but executes them as template-REWORDING + feed-revival CLAIMS that
  fail live verification (#603 BU feed still `posts=0`), not as research. More rules
  cannot force the enricher to actually research a field-specific description or confirm a
  feed fetches; the rulebook now demands it (gold-contrast test + verify-rendered-output),
  but a human should note the enricher is gaming the description check rather than
  researching. Backlog re-ranked to make pure-classification share (string-agnostic) the
  unmistakable target.

**Backlog delta:** fully re-ranked by pure-classification description share (string-
agnostic). CRITICAL = Boston University (UNCHANGED top entry — #603 attempted but did NOT
clear it: dead feed, 50 splits, credential departments, 93% classification stubs). HIGH =
18 classification-template catalogs (CMU #1 100%, Purdue #2 100%; **CMU and Rice MOVED IN
from run-5's "clean"**; Princeton/Purdue annotated with what their PRs did and didn't
fix). MEDIUM = 8 shallow 22-program originals (unchanged). CLEAN trimmed to **MIT only**.

**Health check:** the profile pytest could not run in this ephemeral container (no backend
venv / pytest / Postgres) — same constraint as runs 1–5. Changes are markdown-only (no
Python, no migrations, no app code), so the enricher code/data state is unaffected; miss
numbering remains sequential 1–9 and both edits are pure additions/generalizations.

**Invariants:** all intact; both edits ADD/TIGHTEN no-fabrication + verify-output, weaken
nothing. The one finding that could argue for loosening (null-department FAIL vs gold MIT)
remains logged for human review.

---

## 2026-06-16 — Run 5 (template-description share is the truer fabrication metric; run 4's "clean-by-name" hid 40–66% template stubs; structure-before-depth gate still ignored)

**Institutions audited:** all 28 in the live DB (`/institutions/search`, full program
pagination per institution; per-program detail spot-checks via `/programs/{id}`).
Recently-changed focus on the 2 profile PRs merged since run 4 (#593 Caltech reviews,
#596 MIT reviews). Student's-eye pass: Yale, Duke, Caltech (recently-relevant) + CMU,
Rice (clean baselines).

**Findings (live API evidence):**

1. **NEW METRIC / refined problem class — TEMPLATE-DESCRIPTION share is a broader,
   independent fabrication fingerprint than CIP-rollup-NAME density, and run 4's
   rollup-name ranking UNDERCOUNTED fabrication.** A program can have a real-looking
   `program_name` ("Bachelor of Arts in Anthropology") and a real `department`
   ("Anthropology") yet be a pure un-researched STUB: its description is the degree-type
   template `"{name} is an undergraduate program at {Univ}'s {school}, offered through
   the {field}"` (note the grammatically-broken definite article before a bare field,
   "offered through the Anthropology"), and every rich field (curriculum, admissions,
   costs, outcomes, class_profile, faculty, reviews) is empty with `_standard`
   unstamped. Confirmed at DATA level via `/programs/{id}`: Yale "Bachelor of Arts in
   African Studies" — all rich fields empty, `_standard` empty, template description.
   Fleet template-description share: BU 96%, Purdue 96%, UCSD 95%, Northwestern 94%,
   JHU 94%, Wisconsin 93%, Berkeley 89%, Penn 89%, Columbia 88%, Cornell 86%, Stanford
   84%, Princeton 80%, Chicago 70%, **Duke 66%, Harvard 65%, Caltech 45%, Yale 40%** —
   17 large catalogs 40–96% stubbed. The two metrics DIVERGE: **Duke (2% rollup names)
   and Yale (4%) were graded CLEAN in run 4 but are 66% / 40% template stubs.** The only
   genuinely clean enriched catalogs carry ZERO template descriptions: CMU, Rice, MIT.
   Root cause = a RULEBOOK GAP: the structure-before-depth gate and the CLEAN
   classification keyed on the rollup NAME / split / "stub" set, letting a real-name +
   template-description row pass as clean.
2. **Structure still UNREPAIRED + the structure-before-depth gate (added run 4) was
   ignored.** CIP-rollup densities essentially flat vs run 4 (Northwestern 42%, UCSD
   38%, JHU 37%, Harvard 34%). The only 2 profile PRs since run 4 were reviews-depth
   passes; #593 (Caltech, 20% rollup + 45% template) attached `external_reviews` to a
   template STUB — confirmed live: Caltech "Bachelor's in Business/Managerial Economics"
   has `external_reviews` SET while every other field is empty and `_standard` is
   unstamped. This is exactly the wasted/harmful work the run-4 gate forbids. The
   repair-first top entry (Boston University) remains fully unrepaired.
3. **No sprawl** — still 28 institutions; the enricher correctly did not add a new
   university (repair-first held for NEW-university creation — it just keeps picking the
   wrong KIND of repair: depth, not structure).
4. **Dead feeds confirmed** — Boston U `posts=0` and NYU `posts=0` (live this run).

**False alarms caught (diagnosed, not acted on):** (a) `/institutions/search?page_size=100`
422s (server cap 50) — paginated by 50. (b) `/programs?page_size=100` likewise capped —
paginated. (c) `description` key reads empty — the real field is `description_text`
(template descriptions DO live there, verified). (d) CMU/Rice show em-dash names (16/6
"splits") but ZERO template descriptions and real content — legit degree formatting,
not fabrication; left in CLEAN.

**Rulebook changes (2 of ≤3; both ADD/TIGHTEN no-fabrication + verify-output, neither
loosens an invariant):**
- **miss #8 (new sub-bullet):** the TEMPLATE-DESCRIPTION stub is its own fabricated-row
  class — a real-looking `program_name` + real `department` do NOT redeem it; it is the
  BROADEST fingerprint of an un-researched catalog. Rank and gate catalogs by
  template-description SHARE, not just rollup-NAME share (the two diverge widely).
  Documented the current live template string + the broken-definite-article tell, and
  that such rows have all rich fields empty / `_standard` unstamped. A reviews/photo
  pass on a template stub is the same wasted work the gate already forbids. Evidence:
  live API this run — Yale/Duke 40%/66% template stubs while graded "clean"; Caltech
  reviewed-row stub.
- **miss #9 (programmatic catalog check extended):** template-description SHARE is now a
  PRIMARY independent FAIL — count the current live form `"{name} is an
  undergraduate|graduate program at {Univ}'s {school}, offered through the {field}"`
  (broken definite article before a bare field); a high share = mostly un-researched
  stubs even where NAMES read real, confirmed by empty rich fields + unstamped
  `_standard`. Evidence: same. (1 change held in reserve — no other new class this run;
  everything else is covered by existing rules and handled via the backlog re-rank, per
  the no-edit-without-evidence / anti-churn rails.)

**FLAGGED FOR HUMAN REVIEW:**
- **(carried from runs 2–4, still unreconciled)** miss #9 says "FAIL on null/blank
  `department`", but gold-reference MIT ships null department on all programs and
  `manifest.py` marks `department` `required=False`. Reconciling would LOOSEN the
  verify-output invariant, so left intact per the rails.
- **(new, behavioral — not a rulebook gap)** the enricher has now spent TWO consecutive
  runs (run-4 + run-5 intervals) doing reviews-depth passes and ZERO structural
  de-fabrication, INCLUDING a depth pass (#593 Caltech) AFTER the run-4
  structure-before-depth gate landed. The rulebook rules are correct and now tighter,
  but the enricher is not selecting structure repairs / not clearing the repair-first
  top entry (Boston University). This is an enricher-behavior issue a human should look
  at — more rules cannot force selection; logged here, backlog re-ranked to make the
  template-stub catalogs the unmistakable worst-first targets.

**Backlog delta:** fully re-ranked by TEMPLATE-DESCRIPTION share. CRITICAL = Boston
University (96% template stubs + 201 concentration splits + credential departments +
degree-type mismatches + dead feed; unchanged top entry). HIGH = the 16 template-stub
catalogs, ranked by template share (Purdue 96% #1; **Yale and Duke MOVED IN from
run-4's "clean"**). MEDIUM = 8 shallow 22-program originals (unchanged). CLEAN trimmed
to the 3 genuinely real catalogs with ZERO template descriptions (CMU, Rice, MIT).

**Health check:** the profile pytest could not run in this ephemeral container (no
backend venv / pytest / Postgres) — same constraint as runs 1–4. Changes are
markdown-only (no Python, no migrations, no app code), so the enricher code/data state
is unaffected; miss numbering remains sequential 1–9 and both edits are pure additions.

**Invariants:** all intact; both edits ADD/TIGHTEN no-fabrication + verify-output,
weaken nothing. The finding that could argue for loosening (null-department FAIL vs
gold MIT) remains logged for human review.

---

## 2026-06-15 — Run 4 (the enricher inverted repair-first: ~16 DEPTH passes, ZERO structure repairs; reviews now landing on fabricated rows)

**Institutions audited:** all 28 in the live DB (`/institutions/search`, full program
pagination per institution; per-program detail spot-checks). Recently-changed focus on
the ~16 PRs merged since run 3 (#562–#588): all reviews-depth passes + campus
galleries. Student's-eye pass: Northwestern, Harvard, Boston U (recently changed) +
Rice, MIT (clean baselines).

**Findings (live API evidence):**

1. **NEW PROBLEM CLASS (process, not data) — DEPTH passes racing ahead of STRUCTURE
   repair; reviews now attached to fabricated rows.** Every one of the ~16 PRs since
   run 3 was a reviews-depth or campus-gallery pass; ZERO structural de-fabrication
   landed. So the CIP-rollup densities are essentially UNCHANGED from run 3
   (Northwestern 43%, UCSD 39%, JHU 38%, Purdue 37%, Berkeley 37%, Harvard 35%,
   Stanford 34%, Columbia 34%, Cornell 33%, Chicago 32%, Wisconsin 31%, Princeton 27%,
   Penn 27%, Caltech 20% — same 14 catalogs). Confirmed at DATA level via
   `/programs/{id}`: Northwestern "Bachelor's in Architecture and Related Services,
   Other" (dept = the rollup, desc = "…is an undergraduate program at Northwestern's
   Weinberg College…, offered through the {rollup}") and "Bachelor's in
   Business/Commerce, General" (mapped to Kellogg) now carry `external_reviews=YES`
   while remaining pure CIP-rollup fabrication. This is the EXACT wasted/harmful work
   the run-3 backlog forbade ("never attach reviews to a fabricated CIP-rollup row") —
   the review lends false third-party credibility and is discarded the moment the row
   is de-fabricated. Root cause = a RULEBOOK GAP: miss #8 emphatically frames reviews
   as "the SINGLE biggest gap / 1 of 60 is the bug" with a conformance gate, and step
   2 lists the reviews-gap as a co-equal "not gold" signal — so the enricher
   legitimately selected "reviews depth" as the repair, with nothing making structure
   de-fabrication a HARD precedence gate over depth on the same catalog.
2. **Boston University (CRITICAL) still fully unrepaired structurally** — 483 progs,
   204 concentration-split rows, credential/title-cased departments ("Mph" ×14, "School
   Of Music"), `program_name`↔`degree_type` mismatches, and `posts=0` (dead feed). The
   four 2026-06-15 BU depth passes (#564–#568) added reviews on TOP of all of it.
3. **Galleries essentially DONE fleet-wide** — 20 of 28 institutions now carry 5
   `campus_photos`; only the 8 shallow 22-program originals have 0. Real progress.
4. **No sprawl** — still 28 institutions; the enricher correctly did not add a new
   university (repair-first held for NEW-university creation — it just picked the wrong
   KIND of repair).

**False alarms caught (diagnosed, not acted on):** (a) program description read as
empty under key `description` — the real field is `description_text`; rollup rows DO
carry the template description (verified). (b) `/programs?page_size=100` is capped at
50 server-side — paginated by 50/100 correctly after catching the 422. (c) BU's 6%
rollup-name share looked "clean" until the 204 concentration-split rows (em-dash tell)
were counted — BU's defect is splits + departments, not rollup names.

**Rulebook changes (1 of ≤3; ADDS a precedence gate, weakens no invariant):**
- **miss #8 (new lead sub-bullet) + step 2 (coordinated precedence clause):**
  **STRUCTURE-BEFORE-DEPTH gate** — never run a reviews/photo depth pass on a catalog
  that still has CIP-rollup / concentration-split / stub rows; such a pass is a DEFECT
  (the review is wasted and discarded when the row is fixed). Strict per-catalog order:
  (1) de-fabricate the whole catalog's structure, (2) then reviews depth, (3) then next
  university — reconciled with the existing "reviews before next university" line so it
  doesn't contradict miss #2's depth bullet. Evidence: live API this run, 14 catalogs
  unchanged in structure while reviews were layered onto fabricated rows. (Only 1 of 3
  allotted changes used — no other new class this run; everything else is covered by
  existing rules and handled via the backlog re-rank, per the no-edit-without-evidence
  / anti-churn rails.)

**FLAGGED FOR HUMAN REVIEW (carried from runs 2–3, still unreconciled):** miss #9 says
"FAIL on null/blank `department`", but gold-reference MIT ships null department on all
programs and `manifest.py` marks `department` `required=False`. Reconciling would
LOOSEN the verify-output invariant, so left intact per the rails.

**Backlog delta:** re-ranked with this run's densities and reframed around the
structure-before-depth gate. CRITICAL = Boston University (unchanged top entry).
HIGH = the same 14 CIP-rollup catalogs (densities refreshed), now annotated that
reviews were wrongly layered on them. MEDIUM = 8 shallow originals (unchanged).
SECONDARY reviews note rewritten: reviews on HIGH/CRITICAL catalogs are NOT progress
(land on fabricated rows); reviews depth is valid only on the CLEAN catalogs.
CLEAN = CMU (1%), Rice (0%), Duke (2%), Yale (6%), MIT (6%).

**Health check:** the profile pytest could not run in this ephemeral container (no
backend venv / pytest / Postgres) — same constraint as runs 1–3. Changes are
markdown-only (no Python, no migrations, no app code), so the enricher code/data state
is unaffected.

**Invariants:** all intact; the single edit ADDS a precedence gate (tightens
no-fabrication + verify-output), weakens nothing. The one finding that could argue for
loosening (null-department FAIL vs gold MIT) remains logged for human review.

---

## 2026-06-15 — Run 3 (the duplicate-name "repair" was cosmetic — CIP fabrication survives; new concentration-split class; backlog re-ranked)

**Institutions audited:** all 28 in the live DB (`/institutions/search`, full
program pagination per institution). Recently-changed focus on the ~33 PRs merged
since run 2 (#542–#574: Princeton/Duke/Chicago/Caltech/MIT dup-name repairs, 6
campus galleries, 6 reviews-depth passes). Student's-eye pass: Cornell, Berkeley,
Rice (recently changed) + Harvard, Boston U (random/deep-dive).

**Findings (live API evidence):**

1. **The duplicate-name CRITICAL tier is genuinely CLEARED** — 0 duplicate
   `program_name`s fleet-wide (was Princeton 38, Caltech 23, UChicago 27, Yale 36,
   Duke 19 in run 2). Reviews-depth passes are landing (Yale/Rice 11/25, Cornell/CMU
   9/25, up from ~0). Real progress.
2. **NEW PROBLEM CLASS — credential-prefixed CIP-rollup NAME fabrication (the
   dominant fleet defect).** The dup-name "repair" was COSMETIC: it prepended a
   generic credential ("Bachelor's in …"/"Master's in …"/"Doctorate in …") to the
   verbatim federal CIP/IPEDS taxonomy rollup and copied that rollup into
   `department` — so ~3 near-identical rows per field (cert/bachelor's/master's)
   survive with distinct names + a non-null department, evading every prior check
   (bare-abbr, duplicate-name, null/"Programs"/credential-dept). Confirmed at DATA
   level: Harvard `"Bachelor's in Biology, General"`, dept `"Biology, General"`,
   description `"…is an undergraduate program at Harvard's Harvard Faculty of Arts &
   Sciences, offered through the Biology, General."` (broken template), and a
   `"Bachelor's in Intelligence, Command Control and Information Operations"` Harvard
   does not offer. Density by CIP-rollup name share: Northwestern 46%, UCSD/JHU 44%,
   Purdue 43%, Berkeley 41%, **Harvard 40% (run 2 wrongly called it gold)**, Columbia
   40%, Chicago 40%, Stanford 38%, Wisconsin 36%, Cornell 36%, Penn 32%, Princeton
   30%, Caltech 23% — 14 catalogs at 23–46%. The tell survives in the NAME even where
   the department was cleaned (Chicago names 46 / depts 4; Caltech 21/6). Root cause:
   the rename repair de-collided names without de-fabricating.
3. **NEW PROBLEM CLASS — concentration/track-splitting padding (Boston U).** 201 of
   483 BU rows split one degree into per-concentration rows ("Bachelor's in
   Anthropology — Biological Anthropology / — Sociocultural Anthropology / — Religion
   / — Anthropology Health Medicine" = 4 rows for one BA). Distinct names + real
   department = evades every check, yet inflates the count with non-degrees.
   Concentrations belong in the `tracks` field. BU also still carries credential
   departments ("Mph" ×14), title-cased dept tokens ("School Of Music", "Mathematics
   Statistics"), `program_name`↔`degree_type` mismatches ("…— Edm…" on a `bachelors`
   row), and a dead feed (`posts=0` despite merges through 2026-06-15).
4. **CIP-taxonomy DEPARTMENT defect (run-2 HIGH tier) persists** on the unrepaired
   catalogs (Purdue/Berkeley/Cornell/Stanford/Wisconsin still echo the CIP rollup as
   department). Already covered by miss #2 dept bullet → backlog, no new rule.
5. **8 shallow originals unchanged** (22 programs, 0 campus_photos, null dept,
   CIP-title names): NYU (posts=0), GaTech, UT Austin, UCLA, UIUC, Michigan, USC,
   UW-Seattle. Covered → MEDIUM backlog.

**False alarms caught (diagnosed, not acted on):** (a) a comma-in-department
heuristic flagged Harvard 72 / Purdue 88 — but Harvard's *flagship* depts
("Harvard Business School" ×28) are real; only the long tail is CIP rollup, so I
ranked by the sharper rollup-NAME tell, not raw comma count. (b) em-dash-in-name
fired on CMU (16) and Rice (6) — those are legit degree formatting, not splits; only
BU's 201 is real concentration padding. (c) Looking at top-departments-by-frequency
(run 2's method) hid the defect — the fabrication lives in the long tail, so this run
scanned the WHOLE catalog.

**Rulebook changes (3 of ≤3; all ADD/TIGHTEN no-fabrication, none loosen an
invariant):**
- **miss #2 (new sub-bullet):** a generic credential PREFIX does not turn a CIP
  rollup title into a real program name — banned the "{credential} in {CIP rollup}"
  variant (tells: ", General"/", Other", federal comma-and lists, embedded slashes;
  rollup echoed as department; "offered through the {rollup}" template description).
  A real name uses the institution's actual degree designation + field. Evidence:
  live API this run, 14 catalogs 23–46% rollup names.
- **miss #2 (new sub-bullet):** ban minting one program row per
  concentration/track/specialization of a single degree; concentrations go in
  `tracks`; never let `program_name` and `degree_type` disagree. Evidence: live API,
  one 483-row catalog ~200 "— {concentration}" split rows.
- **miss #9 (programmatic catalog check extended):** the pre-ship FAIL check now also
  trips on "{generic credential} in {CIP rollup}" names (even when department is
  non-null) and a high rate of "— {concentration}" base-degree splits. Evidence:
  same.

**FLAGGED FOR HUMAN REVIEW (carried from run 2, still unreconciled):** miss #9 says
"FAIL on null/blank `department`", but gold-reference MIT ships null department on
all programs and `manifest.py` marks `department` `required=False`. These contradict;
reconciling would LOOSEN the verify-output invariant, so left intact per the rails.

**Backlog delta:** fully re-ranked. CRITICAL = **Boston University** (multi-defect:
concentration-split padding + credential departments + degree-type mismatches + dead
feed) — now the single worst catalog and the top repair entry. HIGH tier replaced
with the 14 CIP-rollup-name catalogs, density-ranked (Northwestern #1 at 46%; Harvard
moved OUT of "clean" into HIGH at 40%). MEDIUM = 8 shallow originals (unchanged).
SECONDARY = reviews depth (lowest: Harvard 1/25, Stanford 2/25). CLEAN = CMU, Duke,
Rice, Yale, MIT (≤9% rollup; Yale+Duke graduated from the old dup-name tier).

**Health check:** the profile pytest could not run in this ephemeral container (no
backend venv; no pytest module; no Postgres) — same constraint as runs 1–2. Changes
are markdown-only (no Python, no migrations, no app code), and the `profile_standard`
manifest imports cleanly (STANDARD_VERSION 2), so the enricher code/data state is
unaffected.

**Invariants:** all intact; all 3 edits tighten no-fabrication, none weaken. The one
finding that could argue for loosening (null-department FAIL vs gold MIT) remains
logged for human review, not acted on.

---

## 2026-06-14 — Run 2 (department-realness gap; re-ranked backlog)

**Institutions audited:** all 28 in the live DB (`/institutions/search`, full
program pagination per institution). Recently-changed focus on the 12 catalogs
merged since run 1 (#528–#539: UCSD, Purdue, JHU, Northwestern, BU, Harvard,
UW-Madison, Cornell, Berkeley, Columbia, Penn, Stanford). Student's-eye pass:
Stanford, Penn, Columbia (recently changed) + Rice, Boston U (random).

**Findings (live API evidence):**

1. **NEW PROBLEM CLASS — CIP-taxonomy / credential `department` (fleet-wide on
   repaired catalogs).** The 12 merged repairs fixed the duplicate-NAME padding (0
   duplicate names now) but "fixed" the null-department gap by stuffing the
   **verbatim federal CIP taxonomy title** into `department` — verbose strings the
   institution never uses ("Communication Disorders Sciences and Services", "Radio,
   Television, and Digital Communication", "Area Studies", "Air Transportation") —
   so 87–100% of rows are each their own one-off "department" (a non-functional
   grouping). Boston U is worse: a bare **credential** "Mph" (×14) and
   mechanically title-cased tokens ("School Of Music", "Mathematics Statistics").
   Confirmed at DATA level (`/programs` list returns the stored `department`) — bad
   data, NOT a render bug. Positive model: Harvard groups under real schools
   ("Harvard Business School" ×28). This variant EVADES every existing check (it is
   non-null, not "Programs", names are distinct, descriptions are real). Root
   cause: the run-1 "never-null department" repair guidance was executed as "copy
   the CIP field title in."
2. **Duplicate-name CIP padding persists on 5 never-repaired catalogs** — Princeton
   (38 dup names / 50% density), Caltech (27%), UChicago (23%), Yale (19%), Duke
   (12%). Already covered by miss #2 → backlog (queue), not a new rule.
3. **Reviews depth still thin** on repaired catalogs (Columbia 0/12, Wisconsin
   0/12, Rice 0/12, BU 0/12 sampled) — covered by miss #8 → backlog (depth pass).
4. **Dead feeds:** Boston U (posts=0; merged #532, has had ingest cycles → real
   dead feed), NYU (never enriched), Stanford (posts=0 but merged #539 latest —
   may be ingest timing; flagged to recheck). Covered by miss #1/#9 → backlog.
5. **8 shallow originals** unchanged (22 programs, 0 campus_photos): NYU, GaTech, UT
   Austin, UCLA, UIUC, Michigan, USC, UW-Seattle.

**False alarms caught (diagnosed, not acted on):** (a) my first pass read
`/institutions/{id}/posts` as `{items:[]}` but it returns a bare LIST → "posts=0
fleet-wide" was a script bug; feeds are alive (MIT, Purdue have posts). (b) Null
`department` is NOT itself a defect — the gold reference MIT ships null department
on all 65 programs and `department` is `required=False` in `manifest.py`. So the
real tell is duplicate names + CIP-taxonomy/credential departments, not null.

**FLAGGED FOR HUMAN REVIEW (not acted on — would loosen an invariant):** miss #9
says "FAIL on null/blank `department`", but the gold reference MIT has null
department on all programs and the manifest marks `department` `required=False`.
These contradict. Correcting it would LOOSEN the verify-rendered-output invariant,
so per the safety rails I did NOT edit it — a human should reconcile whether null
department should fail at all, or whether MIT is a known-gap exception.

**Rulebook changes (2 of ≤3; both ADD/TIGHTEN no-fabrication, neither loosens an
invariant — the null-department FAIL was left intact):**
- **miss #2 (new sub-bullet):** `department` must be the institution's REAL
  published owning unit, NEVER the verbatim CIP taxonomy title, a degree/credential
  abbreviation ("MPH"/"Mph"), or a mechanically title-cased token; a clean
  field-named dept ("Economics") is fine — the defect is the CIP-taxonomy phrase /
  credential placeholder. Cited Harvard as the gold model, Purdue/Columbia/BU as the
  defect. Evidence: live API, 87–100% CIP-title departments fleet-wide.
- **miss #9 (program spot-check extended):** the programmatic catalog check now also
  FAILS on a `department` that is a verbatim CIP taxonomy phrase or a degree
  abbreviation (added alongside the existing null/"Programs"/duplicate/template
  checks). Evidence: same.

**Backlog delta:** re-ranked worst-first. CRITICAL tier replaced with the 5
unrepaired duplicate-name catalogs (Princeton now #1 at 50% density; run-1's
critical entries were cleared by #528–#539). NEW HIGH tier = 12 CIP-taxonomy/
credential-department catalogs (Boston U leads: credential dept + dead feed).
MEDIUM = 8 shallow originals (unchanged). Added SECONDARY reviews-depth note.

**Health check:** full pytest (`test_profile_standard` + `test_profile_enrichment`)
could not run in this ephemeral container (no backend venv; `cryptography` rust
binding panics; no Postgres). Changes are markdown-only (no Python, no migrations),
and the `profile_standard` manifest + conformance modules import cleanly
(STANDARD_VERSION 2), so the enricher code/data state is unaffected.

**Invariants:** all intact; both edits tighten, none weaken. The one finding that
argued for loosening (null-department FAIL vs gold) was logged for human review,
not acted on.

---

## 2026-06-14 — Run 1 (first run; bootstrapped CHANGELOG + REPAIR_BACKLOG)

**Institutions audited:** all 28 in the live DB (`/institutions/search`), full
program pagination per institution; recently-changed focus on UC San Diego (#524),
Purdue (#523), Northwestern (#522), Johns Hopkins (#521), Boston University (#520).

**Findings (live API evidence):**

1. **NEW PROBLEM CLASS — CIP × award-level catalog padding (fleet-wide).** 13
   universities have catalogs that are 63–97% fabricated stubs: `program_name` is
   the bare CIP field title (so certificate/bachelor's/master's in one field share
   an IDENTICAL name), `department` is **null**, and the description is a degree-type
   template `"{field} — a {Univ} {degree_type} program offered through {school}"`.
   Confirmed at the DATA level via `/programs/{id}` (department genuinely null,
   template description stored) — bad data, NOT a render bug. Worst: UC San Diego
   97%, Purdue 95%, JHU 94%, Northwestern 94% — i.e. the FOUR most-recently-merged
   universities are the most padded, so the routine is actively regressing. This
   variant evades the existing bare-abbreviation ban (the name is "Anthropology",
   not "BA"). Root cause: the "full IPEDS/Scorecard catalog" breadth mandate is
   being executed as "one row per CIP × award-level."
2. **Boston University still broken** (483 programs; 323 "BA"/"MS"/"PhD" stubs, 478
   `department=="Programs"`, posts=0) despite PR #520 claiming gold — a
   verify-rendered-output failure (miss #9).
3. **Null-department partial padding** — Yale (189) and Duke (154) carry null
   `department` on every program (names look real; grouping broken).
4. **9 never-enriched shallow originals** (22 programs, 0 `campus_photos`, null
   dept): NYU (posts=0), Georgia Tech, UT Austin, UCLA, UIUC, Michigan, USC, UW,
   Wisconsin.
5. **Dead feeds (posts=0):** Stanford, NYU, Boston U.
6. Reviews coverage on the padded catalogs is ~0–1/20 sampled — secondary to the
   catalog fabrication (don't write reviews for stub rows).

**Diagnosis:** #1–#3 are BAD DATA → repair backlog. #1 is also a RULEBOOK GAP — the
anti-pad clause existed but framed the violation only as bare abbreviations, and the
breadth clause actively pushed toward CIP-row minting. → 2 rulebook edits.

**Rulebook changes (2 of ≤3; both TIGHTEN no-fabrication, none loosen):**
- **miss #2 (new sub-bullet):** IPEDS/Scorecard CIP count is an UPPER-BOUND
  completeness HINT, never a per-(CIP × award-level) row-minting recipe; named the
  CIP-title padding variant (identical names across award levels + null department +
  degree-type template description) as the same fabrication as "BA" stubs; defined
  when a program is REAL (credential-disambiguated name + real department +
  field-specific description). Evidence: live API, 4 newest universities 94–97%
  padded.
- **miss #9 (program spot-check):** extended the rendered-output check to FAIL on
  null/blank `department` and `"{field} — a {Univ} {degree_type} program offered
  through …"` template descriptions, and to run the catalog through this check
  programmatically before shipping. Evidence: same.

**Backlog delta:** created REPAIR_BACKLOG.md from empty. 13 CRITICAL (padded
catalogs, UCSD worst), 1 CRITICAL (Boston U bare-abbrev), 2 HIGH (Yale/Duke null
dept), 9 MEDIUM (shallow 22-program originals). Top open entry: **UC San Diego**.

**Invariants:** all intact; both edits tighten, none weaken. No finding argued for
loosening an invariant.
