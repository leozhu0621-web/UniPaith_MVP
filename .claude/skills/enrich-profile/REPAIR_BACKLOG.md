# Enrich-profile REPAIR BACKLOG

Ranked **worst-first**. The enricher MUST clear the top open entry before deepening any
other university (repair-first, SKILL.md §2). This is the ONLY file where specific
schools appear. Severity: **critical** (fabricated / cross-contaminated content shipped or
about-to-ship live — peer-signature copies / re-labeled peer landmarks / namesake-scrapes /
URL-slug leaks) · **high** (real data but materially broken structure — credential-frame +
tail-shared field body / rollup names / per-field stamping / fabricated owning-unit) ·
**medium** (institution-level seed below gold). Evidence is from the live API
(`api.unipaith.co/api/v1`), measured with WORD-BOUNDARY-anchored structure heuristics
(substring matching over-counts — see run-62 correction, re-confirmed run 65: BU "rollup 8%"
and Cornell/Penn/JHU "peer" hits were joint-degree slashes / own-unit names) and corroborated
against the MERGED source where a deploy is mid-flight.

_Last graded: 2026-06-20 (grader **run 65** — **FULL-FLEET sweep: all 300 LIVE institutions
re-measured** via the live API; all 40 catalogs scanned across every description + structure
dimension + a credential-FRAME-stripped per-field shared-body scan + an OWN-UNIT-EXCLUDED
word-boundary peer-signature scan + name-form measurement + matcher-side cip/reviews spot-checks
+ campus-photo / feed checks; gold MIT (n=65) control. **1 rule change** — miss #8 gains the
credential-FRAME-prepend sub-bullet: a per-credential frame ("{Univ} offers the undergraduate
major in {field}.", "Master's students in {field} complete graduate seminars…—") prepended onto a
field body STILL shared across credential siblings relocates the run-38 stamp into the TAIL, where
the leading-PREFIX shared-body count reads a false 0; strip the frame + measure shared body anywhere
(gold MIT 0%). **HEADLINE: the enricher CLEARED essentially the entire run-64 HIGH tier live** —
possessive names → 0% fleet-wide (Harvard/Cornell/Penn/Duke/Columbia/Yale), Yale prefix 70%→0,
Rice verbatim 43%→0, Columbia rollup 25%→0, UW-Madison/Northwestern leading-body→0. But the
per-credential "repair" passes manufactured the NEW frame+tail-share evasion AND Northwestern #878
shipped CROSS-INSTITUTION CONTAMINATION live. See CHANGELOG run 65._

## Fleet at a glance (run 65, live `api.unipaith.co/api/v1`)

- **Fleet = 300 institutions LIVE.** **41 carry programs (Florida #882 newly enriched to 314);
  259 are bare institution-level stubs** (0 programs, dead feed, ~33 with ZERO campus photo).
  Seeding is **external**; the routine ENRICHES + REPAIRS only.
- **🟢 HEADLINE — the run-64 HIGH backlog was genuinely cleared live (verified, not deploy-lag).**
  **Possessive award-level names → 0% on EVERY catalog** (was Harvard 54 / Columbia 55 / Cornell 54 /
  Penn 53 / Duke 34 / Yale 10 % — #864/#866-872 landed). **Yale prefix-doubling 70%→0** (#864).
  **Rice verbatim-across-levels 43%→0** (#876). **Columbia rollup 25%→0** (#866/#867). **UW-Madison +
  Northwestern shared-LEADING-body → 0** (#877/#878). Columbia · Harvard · Penn · Duke · Yale now
  measure clean on possessive / rollup / prefix / verbatim / leading-body.
- **🔴 CRITICAL REGRESSION — Northwestern #878 (a "per-credential descriptions" repair) shipped
  CROSS-INSTITUTION CONTAMINATION live.** 4 Music/Dance rows carry "Peabody Conservatory … on Chicago's
  **Mount Vernon** campus" (Peabody + Mount Vernon = **Johns Hopkins**, not Northwestern's Bienen School)
  and Materials Sciences carries "**Lawrence** Northwestern facilities" (Lawrence = Berkeley/Livermore
  relabeled). Boston U carries **1** such row ("**Whiting**'s MS in Data Science" — Whiting = JHU). Miss
  #8 cross-institution-copy / re-labeled-peer-landmark — a COMPLIANCE GAP + enforcement gap (FLAG #2).
- **🟡 NEW GAP-CLASS (drives the 1 rule change): credential-FRAME-prepend hides a still-shared field
  body in the description TAIL.** The #876/#877/#878 + Purdue/Florida "per-credential descriptions"
  passes open each row with a credential-keyed frame ("{Univ} offers the undergraduate major in {field}.",
  "Master's students in {field} complete graduate seminars, research methods, and a thesis project —",
  "Doctoral study in {field} at {Univ} centers on dissertation research in", a generic "{Field} is the
  study of …" definition) and then append ONE field body identical across the field's BA/MS/PhD. The
  frames differ by credential, so the leading-PREFIX shared-body count reads 0 (looks fixed) while a
  student still reads the SAME field paragraph on every level. After frame-strip: **Purdue 51/51 ·
  Rice 14/14 · Florida 59/62 · Wisconsin 57/62 · Northwestern 37/42 · Stanford 28/43 · Michigan 16/20 ·
  BU 11/44** multi-credential fields share an ≥80-char body, vs gold MIT 0%.
- **Residual structural classes (documented, no new rule):** a likely-fabricated INTERNAL owning unit
  (**Cornell "David A. Duffield College of Engineering"** on 31 rows — Cornell's college is "College of
  Engineering"; Duffield is a building donor, miss #8); residual aggregate CIP-rollup (**Columbia/UIUC
  ~1%**, near-noise); one literal stub name (**BU "minor"** — flagged run 64, re-check #880); bare-field
  names (**Rice**: English / Religion echoed into department, low). Generic encyclopedia field-DEFINITION
  leads (**Florida**: "Public health is the science and practice of…" + dept/college mismatch, e.g. dept
  "Food Science and Human Nutrition" vs body "College of Liberal Arts and Sciences").
- **Checklist on the 41 catalogs:** 0 duplicate / 0 bare-abbreviation / 0 "Programs" / 0 null-department
  on the 29 mature catalogs; **all carry ≥4 campus photos + a live posts feed** EXCEPT Florida (#882 —
  314 programs but **posts=0 dead feed**, re-check the LiveWhale RSS landed). Reviews richly present on
  coverable flagship rows (Cornell AEM, Penn Wharton = YES). The ~10 five-program seeds remain 5/5
  empty-`description_text` + null-`department` + DEAD FEED; **5 have <4 photos** (Emory/Notre Dame 2,
  Vanderbilt/UNC/UC-Davis 3). **Dartmouth #884 (43-program catalog) is MID-DEPLOY** — live still shows
  the 5-program seed; re-grade next run.

⚠️ **FLAG FOR HUMAN (code/workflow, out of grader scope):**
1. **Auto-merge dual-head race keeps forcing fixup merge migrations (escalated, runs 61–65).** This
   interval alone: `harvardnames1`+`coldukemerge1` (#870/#869 race), `columbiadefab2`+`dukedefab1`,
   `buprof14`+`promptcat1` each needed a reactive merge migration. The durable fix — make
   `test_alembic_has_single_head` evaluate the REBASED-onto-`main` MERGE RESULT and BLOCK auto-merge —
   lives in the automerge/CI workflow (SKILL §8 step 8.5/5). Not grader-editable.
2. **`anti_stub.analyze` lets the run-65 defects through green CI (live proof).** (a) NO cross-institution
   peer-contamination POSITIVE allowlist → Northwestern #878 (Peabody/Mount Vernon/Lawrence) + BU
   (Whiting) auto-merged; the gate must verify each named academic unit / landmark / place-name against
   THIS institution's own org chart + location, not a denylist. (b) NO credential-FRAME-strip in the
   shared-body metric → the #876/#877/#878 frame+tail-share passes scored 0 and joined CERTIFIED_CLEAN;
   `analyze` must strip a leading credential-frame sentence and measure the shared body anywhere (LCS),
   not only as a leading prefix (new miss-#8 sub-bullet). (c) NO exact-name org-chart allowlist → Cornell
   "David A. Duffield College of Engineering" passed. (d) rollup scan still misses bare CIP-bucket titles;
   URL-slug `machine_artifacts` pattern (`^[a-z0-9]+(-[a-z0-9]+){2,}\s*[—–-]\s`) still unimplemented.
   Add to `anti_stub.py` + `test_anti_stub_gate.py`. Not grader-editable.
3. **`cip_code` is NOT serialized on `/programs/{id}` or the list endpoint** — returns `None` on EVERY
   program incl. gold MIT, so the matcher-side "flag empty `cip_code` via public API" channel is UNUSABLE;
   audit via DB/git or expose it. A serializer gap, not a data gap. (program_preferences backfill IS
   called in the recent migrations — coverage maintained.)

---

# CRITICAL — fabricated / cross-contaminated content LIVE

## 1. Northwestern University — cross-institution contamination — severity: critical — first seen run 65 · 2026-06-20
308 programs. Run-64 per-field shared-LEADING-body (56f) was "repaired" by #878, but the pass shipped
CROSS-INSTITUTION CONTAMINATION: **4 Music/Dance rows** (BA/Grad-Cert/MS in Music, BA in Dance) carry
"**Peabody Conservatory** … on Chicago's **Mount Vernon** campus" — Peabody + Mount Vernon are **Johns
Hopkins**, not Northwestern's Bienen School / Evanston campus — and **Materials Sciences** carries
"**Lawrence** Northwestern facilities" (a Berkeley/Livermore landmark relabeled). RESEARCH each from
Northwestern's OWN catalog/department pages and clear the WHOLE class to 0 (miss #8 named-unit-truth +
re-labeled-peer-landmark + geography-lie). THEN fix the frame+tail-share (entry below). Do NOT run any
further depth pass while contaminated rows are live.

---

# HIGH — credential-FRAME + tail-shared field body (the run-65 evasion), ranked by density

## 2. Purdue University-Main Campus — severity: high — first seen run 65 · 2026-06-20
283 programs. **51/51 multi-credential fields share an ≥80-char field body** across credential siblings
after stripping the credential frame (verbatim 0%, leading-prefix 0% — the run-65 evasion, miss #8
credential-frame sub-bullet). Give each credential level (BA/BS/MS/PhD) its OWN researched body (what
THAT degree studies at THAT level); gold MIT = 0%.

## 3. Rice University — severity: high — first seen run 65 · 2026-06-20
159 programs. Verbatim-across-levels 43%→0 cleared (#876), but **14/14 multi-credential fields share an
≥80-char body** behind a "Rice offers the {undergraduate major / master's program} in {field}." frame
(broken splices like "…centers on dissertation research in Rice art history spans…" are the tell). Also
bare-field / dept-echo names (English / Religion). Per-credential researched bodies; drop the redundant
"offers the … in {field}." classification lead.

## 4. University of Florida — newly enriched, structure-incomplete — severity: high — first seen run 65 · 2026-06-20
314 programs (#882 — a real-named catalog with real departments, photos=4 ✓). But **59/62 multi-credential
fields share a body** that is a GENERIC ENCYCLOPEDIA field DEFINITION ("Public health is the science and
practice of protecting populations…", "Cell biology is the study of the structure, function…") + a "{Field}
… At the University of Florida's {College} in Gainesville" classification clause — derivable from the field
name, a gold-contrast STUB. Several **dept/college mismatches** (dept "Food Science and Human Nutrition"
vs body "College of Liberal Arts and Sciences"). **Feed is DEAD (posts=0)** despite the LiveWhale RSS
commit — confirm it fetches. Per-credential RESEARCHED bodies (UF-specific curriculum/centers, not a field
definition); fix the college mismatches; a working feed.

## 5. University of Wisconsin-Madison — severity: high — first seen run 60 · 2026-06-19
348 programs. Run-64 leading-body (75f) "repaired" by #877 → now **57/62 multi-credential fields share a
body** behind a "UW–Madison offers the {…} in {field}." frame (leading-prefix reads 0). Per-credential
researched bodies; gold MIT = 0. (CALS peer hits are UW-Madison's OWN College of Agricultural and Life
Sciences — false positive.)

## 6. Stanford University — severity: high — first seen run 65 · 2026-06-20
178 programs. **28/43 multi-credential fields share an ≥80-char body** behind a credential frame
(leading-prefix / verbatim 0%). Per-credential researched bodies.

## 7. University of Michigan-Ann Arbor — severity: high — first seen run 65 · 2026-06-20
379 programs. **16/20 multi-credential fields share an ≥80-char body** behind a credential frame.
Per-credential researched bodies.

## 8. Boston University — contamination + frame-share + residual — severity: high — first seen run 32 · 2026-06-16
399 programs. **1 contamination row** ("Whiting's MS in Data Science" — Whiting = JHU; clear it, miss #8) +
**11/44 multi-credential fields share a body** behind a credential frame + one literal stub name **"minor"**
(re-check #880's BS-to-MPH fix). ("Anderson" peer hits are the real Anderson Mesa AZ observatory — false
positive; the joint-degree "/" rows are real dual degrees, NOT rollups.)

## 9. Cornell University — likely-fabricated owning unit — severity: high — first seen run 64 · 2026-06-19
237 programs. Possessive names + peer-copy CLEARED (#871). **Residual: "Cornell David A. Duffield College
of Engineering" rides 31 rows** — Cornell's college is "College of Engineering" (Duffield is a building
donor, not the college's name); verify on cornell.edu and correct or drop the donor name (miss #8 exact-name
org-chart). A near-duplicate ORIE pair persists ("…Operations Research" vs "Operations Research and
Information Engineering"). (Cornell also shows the credential frame on its master's rows — fold a
per-credential-body pass into the same repair.)

## 10. UIUC / Columbia residual aggregate-rollup — severity: low — first seen run 64 · 2026-06-19
UIUC 419 + Columbia 167 carry a residual ~1% of federal-CIP aggregate names in conferred form. De-roll-up
the few residual buckets to real degrees or drop them. Lowest priority — near-noise.

---

# MEDIUM — institution-level seeds: the enrichment backlog (seeding is external)

## 11. Dartmouth College — MID-DEPLOY (verify) — severity: medium — first seen run 65 · 2026-06-20
#884 ("real 43-program catalog", dartprof1) merged at grade time; **live still shows the 5-program seed**
(null-dept, dead feed). Re-grade next run — if the deployed 43-program catalog is structurally clean (real
descriptions, departments, ≥4 photos, working feed), CLEAR; else repair per the frame+tail-share gate.

## 12. The remaining ~10 flagship seeds (5 programs each) — severity: medium — first seen run 57 · 2026-06-18
Each ships 5 flagship rows with **5/5 empty `description_text` + null `department`** + a **DEAD FEED**; **5
have <4 campus photos** (Emory/Notre Dame 2, Vanderbilt/UNC-Chapel Hill/UC-Davis 3). **Enrich (per
university, one PR):** researched per-credential descriptions + real departments, a working feed
(`posts`>0), a ≥4-photo verified+credited gallery, then deepen toward a full real-named catalog. Seeds:
Emory · Notre Dame · Vanderbilt · UNC-Chapel Hill · UC-Davis · Brown · Georgetown · UC-Irvine · UVA.

## 13. The ~259 bulk institution-level seeds (0 programs) — severity: medium — first seen run 59/60
Each entered at institution level with **0 programs, a dead feed**, and **~33 with ZERO campus photos**
(broken explore-card gradient header + detail hero — the acute sub-set to clear first; e.g. Arizona State,
Oregon State, U of Houston, U of Utah, UAB, Colorado State, U of Kentucky, Virginia Commonwealth, Thomas
Jefferson, James Madison, Loyola Chicago/Marymount, Michigan Tech). **Enrich (per university, one PR):** a
full real-named catalog + per-credential field-specific descriptions + real departments · a working feed ·
a ≥4-photo verified gallery · reviews on coverable programs · `_standard`. Pick a 0-photo seed once the
CRITICAL + HIGH tiers are clear.

---

# CLEANUP / CLEAN (verify-only)

## Cleared this interval — verified LIVE run 65 (no data repair needed)
- **Possessive award-level names → 0% fleet-wide** — Harvard (#870) · Columbia (#866/#867) · Cornell
  (#871) · Penn (#872) · Duke (#868) · Yale (#864). All now name 85–100% of rows with the conferred
  designation; possessive "Bachelor's in {field}" = 0% on every catalog (gold MIT model).
- **Yale** — prefix-doubling 70%→0 (#864); descriptions field-specific, structure clean.
- **Rice** — verbatim-across-levels 43%→0 (#876) — but frame+tail-share remains (entry #3).
- **Columbia** — rollup 25%→0 (#866/#867); possessive 0; clean on the measured dimensions.

## Genuinely clean (desc + structure; no action) — MIT (gold) · Caltech · Princeton · CMU · UT-Austin · Georgia Tech · JHU · UCLA · UW-Seattle · USC · NYU · Berkeley · UC-San Diego · UChicago · Harvard · Penn · Duke · Yale · Columbia
Verified clean this run on possessive (0%) / rollup (0–1%) / verbatim (0) / prefix-double (~0%) /
credential-frame tail-share (0 of multi-credential fields beyond the gold-MIT baseline). The dept-echo
substring heuristic OVER-counts on small real-department catalogs (CMU "Physics"/"Chemistry", Duke,
Caltech — that IS the real owning department, not a field echo); the peer-signature substring scan
OVER-counts on own units (Cornell CALS/Weill, Penn Wharton/Perelman, JHU Peabody/Whiting, NYU Tandon,
Berkeley Lawrence-Berkeley) — treat both as heuristic artifacts UNLESS a row names a unit/landmark/place
the institution provably does NOT have (the Northwestern + BU contamination above).
