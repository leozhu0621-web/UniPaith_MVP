# Enrich-profile REPAIR BACKLOG

Ranked **worst-first**. The enricher MUST clear the top open entry before deepening any
other university (repair-first, SKILL.md §2). This is the ONLY file where specific
schools appear. Severity: **critical** (fabricated / cross-contaminated / scraped-debris /
near-duplicate / machine-broken template-slot grammar / wrong-program content shipped live,
**OR the backend deploy pipeline itself blocked** so no repair can land) · **high** (residual
fabricated NAMES on an otherwise-rich catalog, OR a matcher-core field STARVED — a whole
master's / professional tier null, a catalog-wide 0%, or a correct repair stranded
un-deployed in an unmerged PR) · **medium** (institution-level seed below gold, or dead feed
on an otherwise-enriched node).

Evidence is from the live API (`api.unipaith.co/api/v1`), measured this run with
`profile_standard/anti_stub.py` (the enforced CI gate's own functions): `analyze`,
`template_slot_artifacts`, `scrape_debris`, `machine_artifacts`, and
`frame_stripped_shared_body(..., abs_chars=150)` over the fully-paginated `/programs` list of every
program-bearing catalog (≈8,400 programs, all 40 catalogs), plus per-`degree_type` tuition COVERAGE +
value distribution, plus a campus-photo count on all 300 institutions, plus a name-realness scan
(CIP-title tells: the federal "…and Related Sciences/Services" suffix AND any multi-clause field
string equal to a federal CIP rollup title). Gold MIT (n=65) is the description 0-control — but NOT a
tuition control (it ships null cert/PhD tiers + grad rows at its own undergrad sticker). The repo's
alembic head set + the open-PR list (`gh`/MCP) were read direct.

_Last graded: 2026-06-22 (grader **run 79**). **FULL-FLEET sweep: all 300 LIVE institutions + all 40
catalogs re-measured via the live API.** **1 rule change** — miss #2's cross-institution tell (b)
rested on a FALSE premise the live fleet disproves (dozens of REAL degrees are shared verbatim across
peers — "Materials Science and Engineering" ×11, "Electrical and Computer Engineering" ×8); replaced it
with the DETERMINISTIC "field part equals a federal CIP rollup TITLE in the IPEDS table the enricher
holds" check (cross-institution sharing demoted to a lookup HINT). **CLEARED since run 78:** Cornell
"Physiology, Pathology and Related Sciences" name (#1093, live CLEAN); Harvard master's tuition
(#1090 → 102/107 live); Georgia Tech master's tuition (#1091 → 55/55 live). **NEW worst tier =
the DEPLOY PIPELINE is BLOCKED:** a live DUAL ALEMBIC HEAD on `main` (`penntuition1` + `gatechgradtuition1`,
both children of `harvardcip2`, neither with a merge child) fails `test_alembic_has_single_head` and
blocks every Deploy Backend `alembic upgrade head` — Penn's merged tuition (#1097) is stranded
un-deployed (master's 8/64 live) and NOTHING new can deploy until a single merge migration lands
(entry #1). Then a residual federal-CIP-ROLLUP NAME class on Cornell/Penn/Harvard (22 live rows;
Harvard's 11 sit in unmerged PR #1096 — entries #2/#3), then master's/professional-tier tuition
starvation with several repairs stranded in unmerged DRAFT PRs (entry #4), then the seeds. See
CHANGELOG run 79._

## Fleet at a glance (run 79, live `api.unipaith.co/api/v1`)

- **Fleet = 300 institutions LIVE.** **40 carry programs; 260 are bare institution-level stubs**
  (0 programs, dead feed, **33 with ZERO campus photo + 54 at 1–3**). Seeding is **external**; the routine
  ENRICHES + REPAIRS only.
- **🔴 DEPLOY PIPELINE BLOCKED (new worst tier):** `main` has a live DUAL ALEMBIC HEAD —
  `penntuition1` (#1097 Penn) and `gatechgradtuition1` (#1091 GT) BOTH declare `down_revision = "harvardcip2"`
  and NEITHER has a child on `main`. `test_alembic_has_single_head` fails and Deploy Backend's
  `alembic upgrade head` errors `Multiple head revisions`, so **every** merged backend change is stuck until
  one merge migration lands. Penn #1097's tuition is merged but UN-DEPLOYED (Penn master's reads 8/64 live).
  **Three** competing open PRs each try to unify the same two heads — #1098 (dedicated empty merge
  `penngatechmrg1`), #1099 (Yale, via `down_revision=(gatechgradtuition1, penntuition1)`), #1100 (Northwestern,
  `gatepennmerge1`) — so merging more than one re-creates the dual head (the §8-step-5 auto-merge cascade,
  ACTIVE again after being DORMANT at run 78). Entry #1.
- **🟢 STRUCTURE + DESCRIPTIONS clean fleet-wide (verified LIVE):** every mature catalog scores 0 on
  `template_slot_artifacts` / `scrape_debris` / `machine_artifacts`; no duplicate / bare-abbreviation /
  "Programs"-dept / null-dept rows on any mature catalog (only the 8 five-program flagship seeds have null
  dept). Only benign marginal `frame_abs150` (Yale/Duke/Northwestern/Chicago = 1) and MIT's known
  `name_prefixed=1` ("Master in City Planning") — all assessed benign at runs 77–78, unchanged.
- **🔴 Residual federal-CIP-ROLLUP NAME class on Cornell + Penn + Harvard (fabrication, 22 live rows):**
  four federal CIP rollup TITLES no institution confers under that literal name still ship verbatim as
  `program_name` — **CIP 52.02 "Business Administration, Management and Operations"**, **42.28 "Clinical,
  Counseling and Applied Psychology"**, **26.02 "Biochemistry, Biophysics and Molecular Biology"**, **42.27
  "Research and Experimental Psychology"**. Harvard 11 rows (incl. a FABRICATED "Bachelor of Arts in Business
  Administration, Management and Operations" at HBS — a graduate-only school Harvard College awards no business
  bachelor's from); Cornell 5; Penn 6 (incl. a fabricated "Bachelor of Arts in Research and Experimental
  Psychology" — Penn awards a BA in Psychology). Harvard's whole-class clear is DONE in repo but stranded in
  unmerged DRAFT PR #1096 (271→227); Cornell/Penn have NO open PR. The run-78 #1093/#1089/#1095 repairs cleared
  only the "…and Related Sciences" suffix form and left these (the new tell-(b) rule closes the gap). Entries #2/#3.
- **🟢 CLEARED since run 78 (do not re-queue):** Cornell "Physiology, Pathology and Related Sciences" name
  (#1093 — live CLEAN on the name scan); **Harvard** master's tuition (#1090 — now 102/107, was 19/107);
  **Georgia Tech** master's tuition (#1091 — now 55/55, was 2/55).
- **🟢 VERIFIED NOT-A-DEFECT (false-positive avoided — do NOT re-queue / do NOT mangle):** the many
  multi-clause names the naive cross-institution scan flags are VERIFIED REAL conferred degrees shared
  verbatim across peers — "Materials Science and Engineering" (11 catalogs), "Electrical and Computer
  Engineering" (8), "Astronomy and Astrophysics" (4), "Civil and Environmental Engineering" (4), "Ecology and
  Evolutionary Biology" (5), "Slavic / Romance Languages and Literatures", "Computer Science and Engineering",
  "Cinema and Media Studies" — NONE is a CIP rollup title; never resolve/mangle them (the new tell-(b) keys on
  the CIP-title TABLE, not on sharing). Also still real: "Science, Technology, and Society" (MIT/Stanford/
  Chicago), "Speech, Language, and Hearing Sciences", "Russian, East European, and Eurasian Studies",
  "Molecular, Cellular, and Developmental Biology", "Theater, Dance, and Performance Studies". **Boston
  University** Law tier at the flat $69,870 = BU's verified flat full-time rate (MD/DMD distinct); **Georgia
  Tech** "Professional Master's in …" (PMASE) = GT's real conferred designation.
- **🔴 master's / professional-tier 0–low% behind a 100% bachelor's tier (matcher-blind on grad budget):**
  ~10 structurally-clean catalogs (entry #4). Several repairs are DONE but STRANDED in unmerged DRAFT PRs
  (Yale #1099, Northwestern #1100, Rice #1064) or merged-but-deploy-blocked (Penn #1097, behind entry #1).
- **🟡 PhD-tier null is LARGELY LEGITIMATE (funded research doctorates → omit-with-reason) — do NOT pressure
  fabrication:** Columbia phd 0/44, Penn 0/46, Yale 0/66, Berkeley 0/64, UCLA 0/82, Harvard 0/25, etc. The
  run-74 rule exempts funded PhDs; certificate-tier nulls are similarly often per-credit. Treat PhD/cert
  nulls as notes, NOT repair priority, UNLESS the institution publishes a non-waived flat rate (UT-Austin PhD
  86/86, JHU cert 84/84, UF cert 93/93, UW-Madison cert 129/129 prove some do).

⚠️ **FLAG FOR HUMAN (code/workflow, out of grader scope — the grader edits only the 3 skill files):**
1. **The auto-merge DUAL-HEAD race is ACTIVE and blocking ALL backend deploys (was DORMANT run 78).**
   `penntuition1` + `gatechgradtuition1` are concurrent heads on `main`; Deploy Backend is down until ONE
   merge migration lands. **Merge #1098 ALONE** (the minimal empty `penngatechmrg1` merge) to unblock, then
   REBASE #1099 + #1100 onto the resulting single head and DROP their duplicate merges before landing (else a
   third head). The durable fix is the long-standing one: a single-head assertion on the MERGE RESULT that
   BLOCKS auto-merge of a second migration-bearing PR sharing a parent, + dedupe migration-bearing PRs, +
   one enricher firing per window. App/CI-workflow code the grader does not edit.
2. **A wave of correct repairs is STRANDED in unmerged DRAFT PRs (merge-mandatory failures).** #1096 (Harvard
   whole-class CIP-title clear, 271→227), #1099 (Yale grad tuition), #1100 (Northwestern grad tuition), #1064
   (Rice grad tuition) are all OPEN + draft=true and never merged. Draft PRs don't auto-merge, so the work
   never ships (SKILL §9 merge-is-not-deploy / merge-mandatory). Mark ready + land (after the entry-#1
   unblock); verify live, do NOT re-author the already-correct data.
3. **The enforced anti-stub gate is DESCRIPTION-ONLY and never scans NAMES, so verbatim CIP-ROLLUP program
   names ship live undetected** (`anti_stub.py` + `test_anti_stub_gate.py`): the gate scores 0 on the
   Cornell/Penn/Harvard catalogs while 22 federal-CIP-title rows ship. The durable fix is a name-realness
   metric — FAIL any `program_name`/`department` field equal to a federal CIP rollup/aggregation TITLE (the
   IPEDS code→title table) OR carrying the "…and Related Sciences/Services" suffix / a literal `(CIP NN.NN)`
   code, parametrized over `CERTIFIED_CLEAN`, with the verified-real-major carve-out. App/test code.
4. **`cip_code` is serialized as a KEY on `/programs/{id}` but its VALUE is `None` on EVERY program incl.
   gold MIT (re-confirmed run 79)**, so the matcher-side "flag empty `cip_code` via public API" channel is
   UNUSABLE. The in-repo IPEDS catalogs carry a `cip` per row — expose it on the API or audit via DB/git.
   (`tuition` IS serialized with real values — the tuition gaps are a real DATA gap.)
5. **There is NO enforced gate on tuition VALUE or COVERAGE — `anti_stub` has no tuition metric.** Both are
   invisible to CI. The durable fix is a `tuition_value_artifacts` metric + per-tier coverage in the profile
   test — BUT it must NOT fail `grad==undergrad` unconditionally (false-flags BU's verified flat rate incl.
   the Law JD): key the copy-down FAIL on a professional row at the flat sticker ONLY when that professional
   SCHOOL publishes a distinct higher rate, with a per-institution published-rate reference. App/test code.

---

# CRITICAL — the deploy pipeline itself is blocked — clear FIRST (nothing else can land)

## 1. `main` DUAL ALEMBIC HEAD — Deploy Backend blocked, Penn tuition stranded — severity: critical — first seen run 79 · 2026-06-22
`main` carries two live alembic heads: **`penntuition1`** (#1097 Penn graduate tuition) and
**`gatechgradtuition1`** (#1091 GT graduate tuition), BOTH `down_revision = "harvardcip2"`, NEITHER with a
child on `main`. `test_alembic_has_single_head` fails and every Deploy Backend `alembic upgrade head` errors
`Multiple head revisions present` — so **Penn #1097's tuition is merged but cannot deploy** (Penn master's
reads 8/64 live, not the repaired figure) and NO further backend change can ship.
**Fix (one PR, human/enricher — grader flags only):** merge **#1098 ALONE** — the minimal empty merge
migration `penngatechmrg1` (`down_revision=(gatechgradtuition1, penntuition1)`, no DDL/data) — to collapse to
a single head and unblock Deploy Backend. Do **NOT** also merge #1099 (Yale) or #1100 (Northwestern) before
rebasing: each carries its OWN merge of the same two heads, so a second one re-creates the dual head (the
auto-merge cascade). After #1098 lands and deploys green, rebase #1099/#1100/#1096/#1064 onto the new single
head, drop their duplicate merge revisions, and land them. Re-confirm `alembic heads` → single + Penn master's
tuition LIVE before clearing.

---

# HIGH — federal-CIP-ROLLUP NAME residual (fabrication axis) — clear after the deploy unblock

## 2. Harvard — federal CIP-rollup NAMES live, whole-class fix STRANDED in unmerged PR #1096 — severity: high — first seen run 79 · 2026-06-22
Harvard ships **11** rows whose `program_name` is a verbatim federal CIP rollup title it does not confer:
"Business Administration, Management and Operations" (CIP 52.02 — incl. a FABRICATED "Bachelor of Arts in
Business Administration, Management and Operations" at HBS, a graduate-only school), "Clinical, Counseling
and Applied Psychology" (42.28), "Biochemistry, Biophysics and Molecular Biology" (26.02), "Research and
Experimental Psychology" (42.27), across BA/MA/PhD/certificate. PR **#1096** ("repair(harvard): whole-class
CIP-title NAME clear + HBS de-fabrication") resolves the WHOLE class (271→227, re-scan = 0 flags) but is
OPEN + draft=true and never merged (a merge-mandatory failure).
**Fix:** after entry #1 unblocks deploys, mark #1096 ready, rebase onto the single head, land it, and VERIFY
Harvard reads its real degrees LIVE with ZERO CIP-rollup names. Do **NOT** re-author the already-correct PR.

## 3. Cornell · Penn — same federal CIP-rollup NAMES still live, NO open PR — severity: high — first seen run 79 · 2026-06-22
The run-78 #1093 (Cornell) / #1089 (Penn) repairs cleared only the "…and Related Sciences" / Linguistics
suffix forms and left the other federal CIP rollup titles live (a whole-class compliance gap — miss #2):
- **Cornell (5 rows):** PhD + MA "Biochemistry, Biophysics and Molecular Biology" (Arts & Sciences); PhD
  "Business Administration, Management and Operations" (Johnson); PhD + MA "Research and Experimental
  Psychology".
- **Penn (6 rows):** PhD "Business Administration, Management and Operations" (Wharton); MA + Graduate
  Certificate "Clinical, Counseling and Applied Psychology" (SAS); PhD + MA + a FABRICATED "Bachelor of Arts
  in Research and Experimental Psychology" (Penn awards a BA in **Psychology**).
**Fix (per university, one PR each):** resolve each to the institution's real published degree + owning
department per credential level (Johnson PhD = Management; Wharton PhD = the named doctoral field; "Research
and Experimental Psychology" = Psychology; "Biochemistry, Biophysics and Molecular Biology" = the real BMB
concentration), keeping the field-specific descriptions; THEN re-scan the WHOLE catalog with the miss-#2
tells — including **field part equal to a federal CIP rollup TITLE** (the new tell (b)) — and get ZERO. Do
NOT mangle the verified real shared majors (carve-out). Re-measure LIVE.

---

# HIGH — master's / professional-tier 0–low% behind a 100% bachelor's tier — matcher starvation

## 4. The graduate-tier-null catalogs — per-credential matcher STARVATION the aggregate hides — severity: high — first seen run 74 · 2026-06-21
Structurally + description clean catalogs whose bachelor's tier is 100% but whose MASTER'S and/or PROFESSIONAL
tiers ship mostly/all null (matcher scores graduate budget-fit BLIND). These publish a per-program / per-credit
rate and are rarely funded → unambiguous starvation. **PhD nulls EXCLUDED (largely funded → legitimate
omit-with-reason; do not pressure fabrication).** Worst-first by null grad rows (live run 79):
- **Penn** — master's 8/64 + prof 0/2 + cert 0/16 (ba 55/55). **Repair #1097 is MERGED but DEPLOY-BLOCKED by
  entry #1 — verify live after the unblock; do NOT re-author.**
- **Columbia** (agg 45%) master's 3/45 (42 null) + prof 2/8 (ba 70/70)
- **Rice** (agg 47%) master's 1/29 (28 null) + prof 11/38 (27 null) (ba 61/61). **Repair STRANDED in unmerged
  DRAFT PR #1064 — land it (after the entry-#1 unblock), do NOT re-author.**
- **Yale** (agg 47%) master's 9/38 (29 null) + prof 0/2 + cert 0/3 (ba 80/80). **Repair STRANDED in unmerged
  DRAFT PR #1099 — land it; note #1099 also carries a duplicate dual-head merge (rebase per entry #1).**
- **Notre Dame** (agg 53%) master's 0/24 + prof 0/1 (ba 60/60)
- **Northwestern** (agg 57%) master's 0/26 + prof 0/4 (ba 71/71). **Repair STRANDED in unmerged DRAFT PR
  #1100 — land it; #1100 also carries a duplicate dual-head merge (rebase per entry #1).**
- **Chicago** (agg 58%) master's 3/41 (38 null) + prof 2/2 (ba 48/48)
- **Emory** (agg 70%) master's 0/5 + prof 0/2 (ba 32/32)
- **Dartmouth** (agg 72%) master's 0/6 + prof 0/1 (ba 31/31)
- **Duke** (agg 52%) prof 2/9 (7 null) (master's 21/38 ok-ish) (ba 56/56)
- **Berkeley** (agg 63%) prof 0/20 (master's 71/74 good) (ba 75/75)
- **UCLA** (agg 64%) prof 0/4 (master's 98/146) (ba 141/141); **Georgia Tech** prof 3/8 (master's 55/55 — newly cleared)
**Fix (per university, one PR):** group coverage by `degree_type`; stamp the published per-program / per-credit
rate for the null MASTER'S / PROFESSIONAL tier (these publish a rate, rarely funded). For a PhD or per-credit
certificate, record `tuition` in `_standard.omitted` with a reason — never a silent blanket null, and never
the undergrad sticker copied onto a professional school that bills its own higher rate (the run-76 copy-down
tell; BU Law, which genuinely bills the university flat rate, is the verified exception). Re-measure LIVE per
tier. **Land the stranded #1099/#1100/#1064 first — that work is done.**

---

# MEDIUM — flagship seeds · institution-level seeds (seeding is external)

## 5. The flagship seeds (5 programs each) — EMPTY descriptions + null department + 0% tuition + DEAD FEED — severity: medium — first seen run 57 · 2026-06-18
**Brown · Georgetown · UC-Davis · UC-Irvine · UNC-Chapel Hill · UVA · Vanderbilt · Washington U-St Louis** each
ship 5 flagship rows with **null department**, **0% tuition**, and a **DEAD FEED** (posts=0). Several now carry
**3 campus photos** (UC-Davis, UNC, Vanderbilt, WashU — still below the ≥4 gold gate); re-measure per
institution. **Enrich (per university, one PR):** a full real-named catalog + per-credential researched
descriptions + real departments + published tuition (per credential level) + a working feed + a ≥4-photo
verified gallery, then deepen toward the full real catalog.

## 6. The ~260 bulk institution-level seeds (0 programs) — severity: medium — first seen run 59/60
Each entered at institution level with **0 programs, a dead feed**, and **33 with ZERO campus photos** (broken
explore-card gradient header + detail hero — the acute sub-set to clear first): Air Force Institute of
Technology · Arizona State (Campus Immersion) · Arizona State (Digital Immersion) · Azusa Pacific · Colorado
State-Fort Collins · James Madison · Keiser-Ft Lauderdale · Loyola Marymount · Loyola-Chicago · Miami U-Oxford
· Michigan Tech · Montclair State · Northcentral · Oakland · Oregon State · SUNY-ESF · Sacred Heart · Stephen F
Austin State · Texas A&M-Commerce · Texas A&M-Corpus Christi · Thomas Jefferson · Universidad Ana G.
Mendez-Gurabo · U Alabama-Birmingham · U Dayton · U Houston · U Kentucky · U Louisville · UMBC · U Missouri-St
Louis · U Nebraska-Lincoln · U Oklahoma-Norman · U Utah · Virginia Commonwealth — **plus 54 more at 1–3
photos**. **Enrich (per university, one PR):** a full real-named catalog + per-credential field-specific
descriptions + real departments + published tuition · a working feed · a ≥4-photo verified gallery · reviews on
coverable programs · `_standard`. Pick a 0-photo seed once the HIGH tier clears.

---

# CLEAN (structure + descriptions; no name/structure action) — verified LIVE run 79
- **Gold (description 0-control):** MIT (n=65, 0 on every description metric; real "Science, Technology, and
  Society" major; `name_prefixed=1` is the benign real "Master in City Planning"; tuition 69% — cert/PhD tiers
  null + grad rows at its own undergrad sticker, MIT is NOT a tuition reference).
- **Tuition-COMPLETE / near (every published tier filled; PhD/cert omit-with-reason where funded/per-credit):**
  Princeton (43, 100%) · JHU (244, 98% incl. cert 84/84) · UW-Madison (348, 98% incl. cert 129/129) · USC
  (511, 97% — PhD 88/88) · Cornell (233, 97% — but see NAME entry #3) · UW-Seattle (360, 96%) · UCSD (137,
  93%) · UF (314, 92% incl. cert 93/93) · UT-Austin (338, 95% — PhD 86/86) · Purdue (172, 97%) · UIUC (419,
  79%) · CMU (180, 78%).
- **Structure + description clean, tuition mostly filled but some grad-tier gap (entry #4) or PhD funded-omit
  (🟡):** NYU (502, 73%) · BU (402, 72% — verified flat-rate incl. Law; MD/DMD distinct) · Michigan (379,
  61%) · Harvard (270, 61% — master's now 102/107; ALSO the CIP-rollup NAME residual, entry #2) · UCLA
  (373, 64%) · Stanford (178, 66%) · Caltech (43, 63%) · Berkeley (233, 63%) · Emory (46, 70%) · Dartmouth
  (43, 72%) · GT (143, 69%) · Notre Dame (113, 53%) · Northwestern (125, 57%) · Chicago (91, 58%) · Duke
  (154, 52%) · Yale (189, 47%) · Rice (159, 47%) · Columbia (167, 45%) · Penn (183, 34% — master's stuck
  8/64 behind the entry-#1 deploy block; ALSO the CIP-rollup NAME residual, entry #3). **"structure clean" ≠
  "tuition done" — many carry a master's/professional gap (entry #4).**
- **Heuristic over-counts to IGNORE (not defects):** benign marginal `frame_abs150=1` (Yale/Duke/Chicago/
  Northwestern); MIT's `name_prefixed=1`; a verified flat full-time rate EQUAL to undergrad on the general AND
  a genuinely-flat-rate professional school (BU $69,870 incl. Law JD); GT's real "Professional Master's in …"
  (PMASE); real multi-clause MAJOR/department names shared across peers ("Materials Science and Engineering",
  "Electrical and Computer Engineering", "Astronomy and Astrophysics", "Science, Technology, and Society",
  "Molecular, Cellular, and Developmental Biology", "Speech, Language, and Hearing Sciences") — these are
  real, NOT CIP rollups (the new tell-(b) keys on the CIP-title TABLE, not on cross-institution sharing).
