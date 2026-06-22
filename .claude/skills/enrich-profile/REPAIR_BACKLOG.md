# Enrich-profile REPAIR BACKLOG

Ranked **worst-first**. The enricher MUST clear the top open entry before deepening any
other university (repair-first, SKILL.md §2). This is the ONLY file where specific
schools appear. Severity: **critical** (fabricated / cross-contaminated / scraped-debris /
near-duplicate / machine-broken template-slot grammar / wrong-program content shipped live) ·
**high** (residual fabricated NAMES on an otherwise-rich catalog, OR a matcher-core field
STARVED — a whole master's / professional tier null, a catalog-wide 0%, or a correct repair
stranded un-deployed) · **medium** (institution-level seed below gold, or dead feed on an
otherwise-enriched node).

Evidence is from the live API (`api.unipaith.co/api/v1`), measured this run with
`profile_standard/anti_stub.py` (the enforced CI gate's own functions): `analyze`,
`template_slot_artifacts`, `scrape_debris`, `machine_artifacts`, and
`frame_stripped_shared_body(..., abs_chars=150)` over the fully-paginated `/programs` list of every
program-bearing catalog, plus per-`degree_type` tuition COVERAGE + value distribution, plus a
campus-photo count on all 300 institutions, plus a NEW name-realness scan (multi-clause field
strings shared verbatim across ≥2 institutions = federal CIP titles). Gold MIT (n=65) is the
description 0-control — but NOT a tuition control (it ships null cert/PhD tiers + 9 grad rows at
its own undergrad sticker).

_Last graded: 2026-06-22 (grader **run 77**). **FULL-FLEET sweep: all 300 LIVE institutions + all 40
catalogs re-measured via the live API** (≈8,400 programs paginated; per-tier tuition coverage AND value
distribution; campus-photo count on all 300; cross-institution CIP-title name scan). **1 rule change** —
the comma-and rollup tell (miss #2) was over-broad: applied bluntly it FALSE-FLAGS gold MIT's OWN real
"Science, Technology, and Society" major (the rulebook contradiction), so it now EXCLUDES a verified real
interdisciplinary major and targets only the verbatim federal CIP TITLE the institution does not award.
**CLEARED since run 76:** catalog-wide 0% tuition — USC (now 97%), NYU (72%), UW-Seattle (95%) (#1);
CMU deploy-strand (now 77%, master's filled) (#2). **VERIFIED NOT-A-DEFECT (do NOT re-queue):** Boston
University's professional Law tier (15 JD/LL.M. rows at $69,870) — BU Law JD genuinely bills the BU
university-wide flat full-time rate (2026-27 both $73,024; MD/DMD separately billed + distinct), so this is
BU's verified flat rate, NOT a copy-down (the run-75 false-positive class — confirmed avoided again). **NEW
worst tier = residual fabricated CIP-TITLE NAMES on Cornell/Harvard/Penn (entry #1)**, then matcher tuition
STARVATION: master's / professional-tier 0% behind a 100% bachelor's tier (~14 catalogs, entry #2). Alembic
history is a SINGLE head (`purduetuition1`) — no dual-head deploy block this run. See CHANGELOG run 77._

## Fleet at a glance (run 77, live `api.unipaith.co/api/v1`)

- **Fleet = 300 institutions LIVE.** **40 carry programs; 260 are bare institution-level stubs**
  (0 programs, dead feed, **33 with ZERO campus photo + 54 at 1–3**). Seeding is **external**; the routine
  ENRICHES + REPAIRS only.
- **🟢 STRUCTURE + DESCRIPTIONS still clean fleet-wide (verified LIVE):** every mature catalog scores 0 on
  `template_slot_artifacts` / `scrape_debris` / `machine_artifacts` and on every `analyze` description tell;
  no duplicate / bare-abbreviation / "Programs"-dept / null-dept rows on any mature catalog. Only benign
  marginal `frame_abs` (GT 5, Yale/Duke/Chicago/Northwestern 1) and MIT's known `name_prefixed=1`.
- **🔴 NEW — residual verbatim CIP-TITLE NAMES (fabrication) on otherwise-rich catalogs:** **Cornell 12 ·
  Harvard 11 · Penn 10** ship five verbatim federal CIP taxonomy titles across BA/MA/PhD/cert levels
  (entry #1). Run 76 wrongly read "0 CIP-rollup rows fleet-wide" — the enforced gate is description-only and
  never scanned NAMES (FLAG #1). The identical strings on all three peers = the CIP mint, not three real
  majors.
- **🟢 CLEARED since run 76 (do not re-queue):** catalog-wide 0% tuition — **USC 97% · NYU 72% · UW-Seattle
  95%** (peers proved it knowable; the enricher stamped published rates). **CMU 77%** (deploy-strand landed;
  master's filled).
- **🟢 VERIFIED NOT-A-DEFECT (false-positive avoided — do NOT re-queue):** **Boston University** professional
  Law tier — 15 JD / LL.M. rows at $69,870 are BU's VERIFIED university-wide flat full-time rate (2026-27 BU
  general = BU Law JD = $73,024; the prior-year $69,870 is that same flat rate), with MD ($72,626) / DMD
  ($99,680) separately billed + distinct. BU Law genuinely uses the flat rate (unlike most law schools), so
  professional==flat here is correct, NOT a copy-down.
- **🔴 master's / professional-tier 0% behind a 100% bachelor's tier (matcher-blind on grad budget):** ~14
  structurally-clean catalogs (entry #2). Master's / professional publish a per-program / per-credit rate and
  are rarely funded → unambiguous starvation.
- **🟡 PhD-tier null is LARGELY LEGITIMATE (funded research doctorates → omit-with-reason) — do NOT pressure
  fabrication:** Columbia 0/44, Penn 0/47, Yale 0/66, Berkeley 0/64, UCLA 0/82, Harvard 0/25, etc. The
  run-74 rule exempts funded PhDs; certificate-tier nulls are similarly often per-credit (no flat annual
  figure). Treat PhD/cert nulls as notes, NOT repair priority, UNLESS the institution publishes a non-waived
  flat rate (UT-Austin PhD 86/86 proves some do).
- **Genuine per-tier fillers to PRESERVE (DISTINCT graduate values — not copy-down):** Michigan (master's
  distinct), Stanford, Berkeley (master's 71/74), UCLA (master's 98/146), UF, UT-Austin, JHU, UW-Madison,
  USC, NYU, UW-Seattle, CMU. **Boston University** (general-grad + Law flat $69,870 by VERIFIED policy,
  MD/DMD distinct). Do NOT "re-uniform" or "re-distinct" these.

⚠️ **FLAG FOR HUMAN (code/workflow, out of grader scope — the grader edits only the 3 skill files):**
1. **The enforced anti-stub gate is DESCRIPTION-ONLY and never scans NAMES, so verbatim CIP-TITLE program
   names ship live undetected** (`anti_stub.py` + `test_anti_stub_gate.py`): the gate computes 0 on
   description tells while Cornell/Harvard/Penn carry 10–12 CIP-title NAMES each. The durable fix is a
   name-realness metric (reject the federal "…and Related…Studies and Services" / "…, and {parent}
   Engineering/Biology" suffix AND any multi-clause field string shared verbatim across ≥2 institutions),
   parametrized over `CERTIFIED_CLEAN`. App/test code the grader does not edit.
2. **`cip_code` is NOT serialized on `/programs/{id}` or the list endpoint** — absent on EVERY program incl.
   gold MIT (re-confirmed run 77), so the matcher-side "flag empty `cip_code` via public API" channel is
   UNUSABLE. The in-repo `PROGRAMS` carry a `cip` key — expose it or audit via DB/git. (`tuition` IS
   serialized — the tuition gaps are a real DATA gap.)
3. **There is NO enforced gate on tuition VALUE or COVERAGE — `anti_stub` has no tuition metric at all.** Both
   are invisible to CI (the gate is description-only). The durable fix is a `tuition_value_artifacts` metric +
   per-tier coverage in the profile test — BUT it must NOT fail `grad==undergrad` unconditionally (false-flags
   BU's verified flat rate, incl. the Law JD): key the copy-down FAIL on a professional row at the flat sticker
   ONLY when that professional SCHOOL publishes a distinct higher rate, and require a per-institution
   published-rate reference. App/test code the grader does not edit.
4. **A repair PR title / a prior backlog clear can OVERSTATE the live result** — verify the CLAIMED metric live
   PER TIER and for value-realness before declaring done (verify-rendered-output). Run-76 cleared BU as
   "professional MD/DMD/SSW DISTINCT" — true but incomplete (15 Law rows sit at the flat rate; verified
   correct this run, but the clear should have measured the WHOLE professional tier). Purdue #1082 "clear
   master's/prof 0%" reads master's 0/68 live (deploy lag — see entry #2).
5. **Auto-merge dual-head race — DORMANT this run** (alembic history is a single head `purduetuition1`); the
   recurring cascade of failed Deploy Backend runs did NOT recur this interval. The durable fix (single-head
   assertion on the MERGE RESULT, blocking auto-merge) still belongs in the CI/automerge workflow; schedule one
   enricher firing per window + dedupe migration-bearing PRs before merge.

---

# HIGH — residual fabricated CIP-TITLE NAMES on otherwise-rich catalogs — clear FIRST (fabrication axis)

## 1. Cornell · Harvard · Penn — verbatim federal CIP taxonomy titles as degree NAMES — severity: high — first seen run 77 · 2026-06-22
These three otherwise-gold catalogs (real departments, field-specific descriptions, tuition mostly filled)
ship FIVE verbatim federal CIP taxonomy titles as `program_name` across BA / MA / PhD / certificate levels —
names no institution actually awards (the real degree has a different, usually shorter, published name). The
identical strings on all three peers = the CIP mint (a real major name is institution-specific):
- **Cornell (12 rows)** · **Harvard (11)** · **Penn (10)**, each carrying some subset of:
  - "Linguistic, Comparative, and Related Language Studies and Services" → real: **Linguistics**
  - "Electrical, Electronics, and Communications Engineering" → real: **Electrical Engineering / ECE**
  - "Ecology, Evolution, Systematics, and Population Biology" → real: **Ecology & Evolutionary Biology**
  - "Biomathematics, Bioinformatics, and Computational Biology" → real: **Computational Biology**
  - "Architectural History, Criticism, and Conservation" → real: **Architectural History / Historic Preservation**
**Fix (per university, one PR):** resolve each CIP title to the institution's real published degree name +
owning department per credential level; keep the (already field-specific) descriptions and tuition. **Do NOT
touch verified real multi-clause majors** (gold MIT's "Science, Technology, and Society"; "Molecular, Cellular,
and Developmental Biology"; "Speech, Language, and Hearing Sciences"; "Russian, East European, and Eurasian
Studies"; "Theater, Dance, and Performance Studies"; "Radio/Television/Film") — those are real and must NOT be
mangled (miss #2 comma-and carve-out). Re-measure LIVE.

---

# HIGH — master's / professional-tier 0% behind a 100% bachelor's tier — matcher starvation

## 2. The graduate-tier-null catalogs — per-credential matcher STARVATION the aggregate hides — severity: high — first seen run 74 · 2026-06-21
Structurally + description clean catalogs whose bachelor's tier is 100% but whose MASTER'S and/or PROFESSIONAL
tiers ship mostly/all null (matcher scores graduate budget-fit BLIND). These tiers publish a per-program /
per-credit rate and are rarely funded → unambiguous starvation. **PhD nulls EXCLUDED here (largely funded →
legitimate omit-with-reason — "🟡" above; do not pressure fabrication).** Worst-first by null grad rows (live
run 77):
- **Harvard** (agg 29%) master's 19/110 (91 null) + cert 0/80 (likely per-credit — verify) (ba 64/64)
- **Penn** (agg 33%) master's 8/66 (58 null) + prof 0/2 + cert 0/16 (ba 55/55)
- **Georgia Tech** (agg 30%) master's 2/55 (53 null) + prof 0/8 (ba 41/41)
- **Purdue** (agg 56%) master's 0/68 + prof 0/2 — **PR #1082 (purduetuition1) MERGED to main; reads 0/68
  LIVE = DEPLOY LAG** (single alembic head, merged 07:42Z 2026-06-22). **Verify the Deploy Backend went green
  and Purdue reads filled before any rewrite** (§9 merge-is-not-deploy; do NOT rewrite the correct data).
- **UCSD** (agg 52%) master's 0/60 + prof 0/2 (ba 72/72)
- **Columbia** (agg 44%) master's 3/45 (42 null) + prof 2/8 (6 null) (ba 70/70)
- **Yale** (agg 47%) master's 9/38 (29 null) + prof 0/2 + cert 0/3 (ba 80/80)
- **Rice** (agg 46%) master's 1/29 (28 null) + prof 11/38 (27 null) + cert 1/2 (ba 61/61)
- **Northwestern** (agg 56%) master's 0/26 + prof 0/4 (ba 71/71)
- **Notre Dame** (agg 53%) master's 0/24 + prof 0/1 (ba 60/60)
- **Berkeley** (agg 62%) prof 0/20 (master's 71/74 good) (ba 75/75)
- **Dartmouth** (agg 72%) master's 0/6 + prof 0/1; **Emory** (agg 69%) master's 0/5 + prof 0/2;
  **UCLA** (agg 64%) prof 0/4 (master's 98/146 good)
**Fix (per university, one PR):** group coverage by `degree_type`; stamp the published per-program / per-credit
rate for the null MASTER'S / PROFESSIONAL tier (these publish a rate, rarely funded). For a PhD or per-credit
certificate, record `tuition` in each program's `_standard.omitted` with a reason — never a silent blanket
null, and never the undergrad sticker copied onto a professional school that bills its own higher rate (the
run-76 copy-down tell; BUT a professional school that genuinely bills the university flat rate, e.g. BU Law, is
correct — verify the school's published rate). Re-measure LIVE per tier.

---

# MEDIUM — flagship seeds · institution-level seeds (seeding is external)

## 3. The flagship seeds (5 programs each) — EMPTY descriptions + null department + 0% tuition + DEAD FEED — severity: medium — first seen run 57 · 2026-06-18
**Brown · Georgetown · UC-Davis · UC-Irvine · UNC-Chapel Hill · UVA · Vanderbilt · Washington U-St Louis** each
ship 5 flagship rows with **null department**, **0% tuition**, and a **DEAD FEED** (posts=0). Some still ship
**< 4 campus photos** (re-measure per institution). **Enrich (per university, one PR):** a full real-named
catalog + per-credential researched descriptions + real departments + published tuition (per credential level
— the undergrad sticker uniform across majors, the published graduate/professional rate per tier) + a working
feed + a ≥4-photo verified gallery, then deepen toward the full real catalog.

## 4. The ~260 bulk institution-level seeds (0 programs) — severity: medium — first seen run 59/60
Each entered at institution level with **0 programs, a dead feed**, and **33 with ZERO campus photos** (broken
explore-card gradient header + detail hero — the acute sub-set to clear first; e.g. Air Force Institute of
Technology, Arizona State (Campus & Digital Immersion), Azusa Pacific, Colorado State-Fort Collins, James
Madison, Keiser-Ft Lauderdale, Loyola Marymount, Loyola-Chicago, Miami U-Oxford, Michigan Tech, Montclair
State, Oakland, Oregon State, SUNY-ESF, Sacred Heart, Thomas Jefferson, U Alabama-Birmingham, U Houston, U
Kentucky, U Louisville, UMBC, U Utah, Virginia Commonwealth) plus **54 more at 1–3 photos**. **Enrich (per
university, one PR):** a full real-named catalog + per-credential field-specific descriptions + real departments
+ published tuition · a working feed · a ≥4-photo verified gallery · reviews on coverable programs ·
`_standard`. Pick a 0-photo seed once the HIGH tier clears.

---

# CLEAN (structure + descriptions + tuition; no action) — verified LIVE run 77
- **Gold (description 0-control):** MIT (n=65, 0 on every description metric incl. 0 CIP-title names; tuition
  69% — cert/PhD tiers null + 9 grad rows at its own undergrad sticker — MIT is NOT a tuition reference).
- **Tuition-COMPLETE (every published tier filled; PhD/cert omit-with-reason where funded/per-credit):**
  Princeton (43, 100%) · UW-Madison (348, 97%) · USC (511, 97% — cleared #1) · JHU (244, 98%) · Cornell (237,
  96% — but see NAME entry #1) · UW-Seattle (360, 95% — cleared #1) · UT-Austin (338, 95% — PhD 86/86 distinct)
  · UF (314, 91%) · Boston University (402, 71% agg — verified flat-rate incl. Law; MD/DMD distinct).
- **Structure + description clean, tuition mostly filled but some grad-tier gap (entry #2) or PhD funded-omit
  (🟡):** CMU (180, 77% — cleared #2) · UIUC (419, 78%) · NYU (502, 72% — cleared #1) · Dartmouth (43) · Emory
  (46) · Michigan (379) · UCLA (373) · Berkeley (233) · Caltech (43) · Stanford (178) · Duke (154) · Chicago
  (91) · Columbia (167) · Notre Dame (113) · Northwestern (125) · UCSD (137) · Rice (159) · GT (143) · Yale
  (189). **"structure clean" ≠ "tuition done" — many carry a master's/professional gap (entry #2); Cornell/
  Harvard/Penn ALSO carry the CIP-title NAME residual (entry #1).**
- **Heuristic over-counts to IGNORE (not defects):** benign marginal `frame_abs` (GT 5, Yale/Duke/Chicago/
  Northwestern 1); MIT's `name_prefixed=1`; a verified flat full-time rate EQUAL to undergrad on the general
  AND a genuinely-flat-rate professional school (BU $69,870 incl. Law JD — confirmed BU general = BU Law JD =
  $73,024 in 2026-27); real multi-clause MAJOR names (MIT "Science, Technology, and Society"; "Molecular,
  Cellular, and Developmental Biology"; "Speech, Language, and Hearing Sciences"; "Russian, East European, and
  Eurasian Studies"; "Theater, Dance, and Performance Studies"; "Radio/Television/Film") — these are real, NOT
  CIP rollups (miss #2 carve-out).
