# Enrich-profile REPAIR BACKLOG

Ranked **worst-first**. The enricher MUST clear the top open entry before deepening any
other university (repair-first, SKILL.md §2). This is the ONLY file where specific
schools appear. Severity: **critical** (fabricated / cross-contaminated / build-junk text
shipped or about-to-ship live — peer-signature copies / URL-slug leaks / namesake-scrapes) ·
**high** (real data but materially broken structure — rollup names / verbatim-across-levels /
prefix-doubling / per-field stamping / field-echo departments) · **medium** (institution-level
seed below gold). Evidence is from the live API (`api.unipaith.co/api/v1`), measured with
WORD-BOUNDARY-anchored structure heuristics (substring matching over-counts — see run-62
correction) and corroborated against the MERGED source where a deploy is mid-flight.

_Last graded: 2026-06-19 (grader **run 63** — **FULL-FLEET sweep: all 300 LIVE institutions
re-measured** via the live API; all 40 catalogs scanned across every description + structure
dimension + an OWN-UNIT-EXCLUDED word-boundary peer-signature scan + matcher-side
cip_code/reviews spot-checks + campus-photo / feed checks, plus a source-vs-live cross-check of
the mid-deploy Cornell PR). **0 rule changes** — after a full-fleet sweep every live defect maps
to an EXISTING miss (#2/#8/#9), is the external seed backlog, or is deploy-mechanics/app-code; no
NEW gap-class, so per the anti-churn + no-edit-without-new-evidence rails the rulebook is
unchanged. This run records the enricher CLEARING UIUC + NYU slug-leaks, Berkeley + Purdue
structure, and BU peer-copy — and catches a NEW regression: the **Cornell #856 "de-fabrication"
merged carrying cross-institution peer-copy** (Berkeley/Penn units) + rollup names + per-field
stamping. See CHANGELOG run 63._

## Fleet at a glance (run 63, live `api.unipaith.co/api/v1`)

- **Fleet = 300 institutions LIVE.** **40 carry programs; 260 are bare institution-level
  stubs** (0 programs, dead feed, 33 with ZERO campus photo). Seeding is **external**; the
  routine ENRICHES + REPAIRS only — these 260 stubs are the backlog.
- **🟢 HEADLINE — the enricher cleared FOUR backlog tiers this interval (the repair loop is
  working).** Verified LIVE this run: **UIUC slug-leak = 0** (was CRITICAL #2, 33 rows; #849),
  **NYU slug-leak = 0** (was CRITICAL #3, 41 rows; #845/#846 now DEPLOYED), **Berkeley** verbatim
  80%→**0**, rollup 32%→**1%** (was HIGH #4; #854), **Purdue** prefix 16%→**0** (was HIGH #13
  residual; clean), **BU Medill peer-copy = 0** (#851–853). Slug-leak + hex build-artifact tiers
  are now empty fleet-wide.
- **🔴 NEW CRITICAL — Cornell #856 shipped CROSS-INSTITUTION PEER-COPY into source.** The merged
  `cornell_field_descriptions.py` (PR #856 "structural de-fabrication", merged 2026-06-19) carries
  **Berkeley's** "IEOR department serving engineering, Haas, and CDSS students" on Operations
  Research and **Penn's** "Mahoney Institute of Neurological Sciences" + "SAS" on Neurobiology /
  Area Studies — **7 live rows** naming foreign units Cornell does not have (Cornell's dept is
  ORIE, not IEOR; there is no Mahoney Institute at Cornell). The same pass **kept 42 rollup names
  (15%)** and stamps **one description per CIP-field across all credential levels (verbatim 76%)**.
  This is the run-62-flagged risk made live: a "de-fabrication" pass that introduces/retains
  miss-#8 contamination. Deploy Backend was in_progress at grade time, so it is about-to-be-live.
- **🟡 BU repair is IN FLIGHT (open PR #857, NOT merged).** #851–853 removed BU's peer-copy +
  classification stubs but left **216 field-echo departments (56%)** + **9 credential-combo
  name/dept stubs** ("Jdma English", "PhD, MD/PhD"). #857 fixes exactly these (real owning
  colleges + real dual-degree names + 2 regression tests) but is **open, not merged** — an
  unmerged fix is a stranded run (SKILL §9). Land #857.
- **Mature-catalog structure tiers persist (documented classes, no new rule):** genuine
  rollup-name (**Harvard 30 · Cornell 29(crit) · Columbia 29 · Penn 23 %**), verbatim-across-levels
  (**Cornell 76(crit) · Penn 74 · Rice 43 %**), per-field shared-leading-body (**Wisconsin 98f ·
  Harvard 96f · Columbia 67f · Northwestern 63f · Rice 25f**), prefix-doubling (**Yale 70 %**),
  literal "(CIP NN.NN)" (**Penn 28%**).
- **Checklist on the 40 catalogs:** 0 duplicate / 0 bare-abbreviation / 0 "Programs" names on the
  28 mature catalogs; **all 28 carry 5 campus photos + a live posts feed**. The 12 five-program
  seeds remain 5/5 empty-`description_text` + null-`department` + DEAD FEED; **7 of them have <4
  photos** (Florida 1, Emory/Notre Dame 2, Vanderbilt/WashU/UNC/UC-Davis 3 — carried from run 62,
  seeds untouched this interval).

⚠️ **FLAG FOR HUMAN (code/workflow, out of grader scope):**
1. **Auto-merge dual-head race keeps FAILING/forcing fixup deploys (escalated, runs 61–63).** This
   interval alone: NYU #845 Deploy FAILED on a dual head, then #847 (cancelled) + #848 + #855
   ("merge dual heads buprof12 + berkeleyprof9, auto-merge race") were all merge-fixups. The durable
   fix — make `test_alembic_has_single_head` evaluate the REBASED-onto-`main` MERGE RESULT and BLOCK
   auto-merge — lives in the automerge/CI workflow (SKILL §8 step 8.5/5). Not grader-editable.
2. **The enforced anti-stub gate has NO peer-signature allowlist scan — and it just let a
   contaminated de-fab pass auto-merge (Cornell #856).** `anti_stub.analyze` computes description-form
   + (per run 58) structure metrics, but **no allowlist scan of named units against the institution's
   own org chart** (SKILL miss #8 allowlist sub-bullet; carried from runs 58–62 as FLAG #3c). Cornell
   #856 cleared CI and merged while shipping Berkeley/Penn units — direct live proof the missing
   enforced scan now actively passes cross-institution contamination. Add a positive-allowlist
   peer-unit scan to `anti_stub.py` + `test_anti_stub_gate.py`. Not grader-editable.
3. **`cip_code` is NOT serialized on the public `/programs/{id}` or the list endpoint** — it returns
   `None` on EVERY program including gold MIT, so the skill's matcher-side audit channel ("flag empty
   `cip_code` via the public API") is UNUSABLE; audit via DB/git, or expose it in the program schema.
   A serializer gap, not a data gap — out of grader scope.
4. `anti_stub.py` still misses, IN CODE, the **URL-slug `machine_artifacts` pattern**
   (`^[a-z0-9]+(-[a-z0-9]+){2,}\s*[—–-]\s`) — the enricher hand-fixed UIUC/NYU this interval, but the
   gate would not have caught the next one. Not grader-editable.

---

# CRITICAL — fabricated / contaminated content shipped or about-to-ship live (fix before any other deepening)

## 1. Cornell University — cross-institution peer-copy (Berkeley + Penn) shipped by the #856 de-fab — severity: critical — first seen run 63 · 2026-06-19
274 programs. PR #856 ("structural de-fabrication") merged but its `cornell_field_descriptions.py`
ships **7 live rows naming foreign units Cornell does not have:**
- **Berkeley** — "Optimization, stochastic modeling, and analytics in the **IEOR** department serving
  engineering, **Haas**, and **CDSS** students" on *Operations Research* (BS + Master's + PhD). Cornell's
  unit is **ORIE**, not Berkeley's IEOR; Haas + CDSS are Berkeley schools.
- **Penn** — "...across **SAS**, Weill Cornell, and the **Mahoney Institute of Neurological Sciences**"
  on *Neurobiology* (Master's + PhD), and "...in **SAS**" on *Area Studies* (BS/MS/PhD). The Mahoney
  Institute is **Penn's** (Perelman); SAS is Penn's School of Arts and Sciences.

Same pass also left **42 rollup names (15%)** ("Bachelor's in Area Studies", ", General"/", Other"
field titles — miss #2) and stamps **one description per CIP-field across every credential level
(verbatim 76%, miss #8 per-field tell)**. **Repair (miss #8 allowlist + miss #2 + structure-before-depth):**
ALLOWLIST-scan every description against Cornell's OWN org chart and FAIL on any foreign unit (research
each from cornell.edu/department pages, never adapt a peer's blurb); de-roll-up the 42 federal-CIP names
to Cornell's real degree names; give each credential level its OWN researched body (gold MIT = 0% verbatim).

## 2. Boston University — finish the IN-FLIGHT repair (open PR #857, NOT merged) — severity: critical — first seen run 32 · 2026-06-16
399 programs. #851–853 cleared the Medill/Penn/Harvard peer-copy + classification stubs (peer-copy now
0 live — the "Anderson" hits are the real Anderson Mesa AZ observatory, a false positive). **Residual,
fixed in OPEN PR #857:** **216 field-echo departments (56%)** (`_department_for` echoed the program's
field into `department` while the real **College of Arts & Sciences** was known) + **9 credential-combo
name/dept stubs** ("Jdma English", "Jdllm In Finance", "PhD, MD/PhD"). #857 resolves all of this (real
owning colleges + real Law/GMS dual-degree names + 2 regression guards; scratch-DB: 0 field-echo / 0
garbage). **Repair: LAND #857** — head-sync `buprof13` onto current `main`, merge, and verify the 216
rows render their real owning college live. An open-but-unmerged fix is a stranded run (SKILL §9).

---

# HIGH — real data, structurally broken (rollup · verbatim-across-levels · per-field stamping · prefix)

## 3. University of Pennsylvania — severity: high — first seen run 24 · 2026-06-15
250 programs. **23% rollup names + 28% literal "(CIP NN.NN)" in names + 74% verbatim-across-levels +
75 fields sharing a ≥120-char leading body.** Strip the CIP codes (miss #2 CIP-code tell); de-roll-up the
federal-CIP names; give each credential level its OWN researched body; real owning schools in `department`.

## 4. Harvard University — severity: high — first seen ≤run 24 · 2026-06-15
343 programs. **30% rollup names + 96 fields sharing a ≥120-char leading body** (verbatim 0% — a
suffix-diversifier evades the full-string count, miss #8). De-roll-up names; per-credential researched
bodies (gold MIT = 0). Verify the terse "Chemistry"/"Applied Mathematics" depts are the real owning unit
(dept-echo heuristic over-count risk — mostly real).

## 5. Columbia University — severity: high — first seen ≤run 24 · 2026-06-15
263 programs. **29% rollup names + 67 fields sharing a ≥120-char leading body.** De-roll-up names;
per-credential researched bodies; real departments.

## 6. University of Wisconsin-Madison — per-field stamping (shared leading body) — severity: high — first seen run 60 · 2026-06-19
348 programs. **98 fields where credential siblings share a ≥120-char leading body** (verbatim 0%,
rollup 0% — a suffix-diversifier evades the full-string count, miss #8). Give each credential level
(BA/BS/MS/PhD) its OWN researched body (gold MIT = 0).

## 7. Northwestern University — per-field stamping (shared leading body) — severity: high — first seen run 60 · 2026-06-19
308 programs. **63 fields share a ≥120-char leading body** across credential siblings (verbatim 0%,
rollup 2%). Per-credential researched bodies (gold MIT = 0). (The McCormick/Kellogg/Medill mentions are
Northwestern's OWN schools — not contamination.)

## 8. Yale University — severity: high — first seen ≤run 30 · 2026-06-16
189 programs. **70% prefix-doubling (`description_text.startswith(program_name)`).** Strip the name
prefix; open each description on the field fact (gold MIT = 2%); per-credential bodies.

## 9. Rice University — severity: high — first seen run 30 · 2026-06-16
159 programs. **43% verbatim-across-levels + 25 fields sharing a ≥120-char leading body + 8% prefix.**
Per-credential researched bodies; verify departments.

---

# MEDIUM — institution-level seeds: the enrichment backlog (seeding is external)

## 10. The 12 earlier flagship seeds (5 programs each) — severity: medium — first seen run 57 · 2026-06-18
Each ships 5 flagship rows with **5/5 empty `description_text` + null `department`** + a **DEAD FEED**;
**7 have <4 campus photos** (Florida 1, Emory/Notre Dame 2, Vanderbilt/WashU/UNC/UC-Davis 3).
**Enrich (per university, one PR):** researched descriptions + real departments for the flagship rows, a
working feed (`posts`>0), a ≥4-photo verified+credited gallery, then deepen toward a full catalog.
Seeds: Florida · Emory · Notre Dame · Vanderbilt · WashU · UNC-Chapel Hill · UC-Davis · Brown ·
Georgetown · UC-Irvine · Dartmouth · UVA.

## 11. The ~260 bulk institution-level seeds (0 programs) — severity: medium — first seen run 59/60
Each entered at institution level with **0 programs, a dead feed**, and **33 with ZERO campus photos**
(broken explore-card gradient header + detail hero — the acute sub-set to clear first; e.g. Arizona State
(both campuses), Oregon State, U of Houston, U of Utah, UAB, Colorado State, U of Kentucky, Virginia
Commonwealth, Thomas Jefferson, James Madison, Loyola Chicago/Marymount, Michigan Tech).
**Enrich (per university, one PR):** a full real-named catalog + field-specific descriptions + real
departments · a working feed · a ≥4-photo verified gallery · reviews on coverable programs · `_standard`.
Pick the highest-priority (a 0-photo seed) once the CRITICAL/HIGH tiers are clear.

---

# CLEANUP / CLEAN (verify-only)

## Cleared this interval — re-confirmed live run 63 (no data repair needed)
- **UIUC** — slug-leak 33 rows → **0** live (#849). CLEAN.
- **NYU** — slug-leak 41 rows → **0** live (#845/#846 deployed); structure clean (rollup 0). CLEAN.
- **Berkeley** — verbatim 80%→0, rollup 32%→1% (#854). CLEAN.
- **Purdue** — residual prefix-doubling 16%→0; peer-copy/verbatim/rollup already 0. CLEAN.
- **USC** — slug-leak + concentration-splits cleared (#843/#844); dept-echo now **2%** (near-clean residual
  — 30→ a handful of rows still echo the field while Dornsife/Marshall/Viterbi is known; lowest-priority).
- **Build-artifact tier** (UCLA/UW/Michigan/Stanford, run-59 CRITICAL) — `hex_artifact = 0` re-confirmed.

## Genuinely clean (desc + structure; no action) — MIT (gold) · UCSD · Caltech · Princeton · CMU · Duke · UT-Austin · Georgia Tech · JHU · Michigan · UCLA · UW · Stanford
Verified clean on the description + rollup metrics this run. The dept-echo substring heuristic
OVER-counts on small real-department catalogs (Caltech 79% / UChicago 88% / Princeton 74% / Duke 62% —
"Chemistry"/"Anthropology" IS the real owning department, not a field echo) — treat as a heuristic
artifact UNLESS a row's `department` is literally the field copied from the name while a real owning
school is separately known (BU/USC-residual = real defect; Princeton/Caltech = not). Stanford's structure
is clean; prefix-doubling 0% this run.
