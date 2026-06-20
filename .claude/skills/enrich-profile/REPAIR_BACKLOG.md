# Enrich-profile REPAIR BACKLOG

Ranked **worst-first**. The enricher MUST clear the top open entry before deepening any
other university (repair-first, SKILL.md §2). This is the ONLY file where specific
schools appear. Severity: **critical** (fabricated / cross-contaminated / scraped-debris /
near-duplicate / wrong-program content shipped live) · **high** (real data but materially
broken structure — credential-frame + ONE shared field body across credential levels /
rollup names / fabricated owning-unit) · **medium** (institution-level seed below gold, or
dead feed on an otherwise-enriched node).

Evidence is from the live API (`api.unipaith.co/api/v1`), measured this run with the
**corrected frame-stripped shared-body scan: longest-common-substring after stripping a
leading credential frame, FAIL ≥80 chars AND (≥50% of shortest OR ≥150 chars ABSOLUTE
regardless of fraction)**. Gold MIT (n=65) is the 0 control; the clean fleet (Duke 132 /
Rice 39 / Purdue 79 / UCSD 71 / USC 148) tops out below the 150-char absolute floor.

_Last graded: 2026-06-20 (grader **run 68** — **FULL-FLEET sweep: all 300 LIVE institutions +
all 40 catalogs (7,200+ programs) re-measured** via the live API across every description +
structure dimension, reusing `profile_standard/anti_stub.py`. **1 rule change** — §8.5 gains
the CERTIFICATION-COVERAGE sub-paragraph: `CERTIFIED_CLEAN` membership gates a catalog only on
`analyze().is_clean`, which EXCLUDES the frame-stripped LCS metric; that metric lives in a
SEPARATE test parametrized over a hardcoded subset that has DRIFTED from `CERTIFIED_CLEAN`, so
nine certified catalogs ship the frame-shared-body defect un-gated. **HEADLINE: the dominant
hole this run is ENFORCEMENT, not new behavior — 9 `CERTIFIED_CLEAN` catalogs (Harvard 68 ·
UCLA 67 · Michigan 67 · Berkeley 64 · Stanford 51 · Penn 51 · Notre Dame 23 · Columbia 14 ·
NYU 5) carry frame-shared bodies the EXISTING un-floored CI metric flags yet were never run
through it.** Plus the run-67 dilution-evasion four (UF 54 · Cornell 44 · BU 23 · JHU 3) which
read 0 on the 50%-floor CI metric. **Enricher WINS this interval (verified live):** UIUC
CRITICAL #1 CLEARED (frame 15→0, scrape-debris 30→0, BSLAS splits collapsed) · JHU 81→3 ·
UW-Seattle 77→0 · UW-Madison 75→0. See CHANGELOG run 68._

## Fleet at a glance (run 68, live `api.unipaith.co/api/v1`)

- **Fleet = 300 institutions LIVE.** **40 carry programs; 260 are bare institution-level stubs**
  (0 programs, dead feed, **33 with ZERO campus photo**). Seeding is **external**; the routine
  ENRICHES + REPAIRS only.
- **🟢 Run-67 backlog CLEARED by the enricher (verified live):** UIUC (#907/#912 — CRITICAL #1:
  frame_abs 15→0, scrape-debris 30→0, BSLAS concentration-splits de-rolled, now CLEAN) · JHU
  (#901/#902 — 81→3 marginal) · UW-Seattle (#914 — 77→0) · UW-Madison (#904 — 75→0).
- **🔴 HEADLINE — ENFORCEMENT hole: 9 `CERTIFIED_CLEAN` catalogs ship frame-shared bodies the
  EXISTING (un-floored) metric flags, never gated.** `analyze().is_clean` (the only gate over
  `CERTIFIED_CLEAN`) excludes `frame_stripped_shared_body`; the LCS-anywhere test parametrizes
  over a hardcoded `[mit, rice, uf, usc, uw_madison, jhu, uiuc, uw]` that has DRIFTED from the
  registry. So Harvard 68 · UCLA 67 · Michigan 67 · Berkeley 64 · Stanford 51 · Penn 51 ·
  Notre Dame 23 · Columbia 14 · NYU 5 are all certified-clean + green-CI while carrying the
  credential-frame + ONE shared field body across BA/MS/PhD (gold MIT 0). New §8.5 rule + FLAG #1.
- **🔴 DILUTION evasion (run-67 four, still live):** UF 54 · Cornell 44 · BU 23 · JHU 3 read **0**
  on the CI 50%-floor metric — a long unique per-credential TAIL dilutes a still-identical
  160–220-char field sentence below 50% of the padded body. Caught only by the absolute-≥150
  floor (new run-67 miss #8 sub-bullet; CI metric still lacks it — FLAG #1).
- **🔴 SCRAPED CATALOG DEBRIS / near-duplicate still LIVE on NYU + UT-Austin (miss #8 scrape-debris).**
  NYU: real colon-truncated requirement intros ("…provides a framework within which students can
  acquire the following training and experience:", PhD History) + the **Chemistry BA & BS share a
  950-char near-identical paragraph** (maxLCS 950 — almost the whole body) + 14 concentration-splits.
  UT-Austin: ~5 colon-truncated rows ("…expected to be able to:"). (NOTE: the CI `scrape_debris`
  ADDRESS tell `\bHall,\s` FALSE-FLAGS researched prose naming a building — "Warren Weaver **Hall,**
  at the heart…" on NYU Math — inflating the raw debris count; real NYU debris is far below 16. FLAG #2.)
- **🟡 Dead feeds on freshly-enriched nodes (compliance gap, miss #1/#9 — flagged runs 65–67, NOT
  fixed):** **Notre Dame, Dartmouth, Emory all STILL ship posts=0** despite being enriched + in
  `CERTIFIED_CLEAN`. A `content_sources` feed counts only if it FETCHES ≥1 item. (Florida's feed
  now fetches, posts=25 ✓; UIUC 36, UW-Seattle 69, Berkeley 19, Purdue 10, UT-Austin 17 all fetch.)
- **Concentration-split over-decomposition (miss #2):** Michigan 32 ("PhD in Conducting: Band/Choral/
  Orchestral" — one DMA split by ensemble) · NYU 14 · BU 7 · UW-Seattle 6 · CMU 13 (borderline —
  joint/option degrees, verify) — collapse genuine concentrations into the base degree's `tracks`.
- **Checklist on the 40 catalogs:** 0 duplicate / 0 bare-abbreviation / 0 "Programs" / 0 null-department
  on the 32 mature catalogs; all mature carry campus_photos. Reviews richly present on coverable
  flagship rows; thin on non-flagship undergraduate majors (lower priority).

⚠️ **FLAG FOR HUMAN (code/workflow, out of grader scope):**
1. **Two compounding gaps in the enforced anti-stub gate (`anti_stub.py` + `test_anti_stub_gate.py`,
   app/test code — not grader-editable):**
   (a) **COVERAGE drift (this run's headline).** `test_certified_catalog_is_anti_stub_clean` asserts
   only `analyze().is_clean`, which has NO frame-stripped metric; `frame_stripped_shared_body` is
   asserted by a SEPARATE test over a hardcoded `[mit, rice, uf, usc, uw_madison, jhu, uiuc, uw]`.
   Make that test (and `scrape_debris` / `machine_artifacts`) parametrize over `CERTIFIED_CLEAN`
   ITSELF so the lists cannot drift — then Harvard/UCLA/Michigan/Berkeley/Stanford/Penn/Columbia/
   Notre Dame/NYU FAIL CI and the certification means something.
   (b) **THRESHOLD undercount (carried run 67).** `frame_stripped_shared_body` uses `min_chars=80
   AND min_fraction=0.5`; add `OR lcs >= 150` (a full stamped sentence, absolute) so the dilution
   evasion (UF/Cornell/BU/JHU) cannot read a false 0.
2. **`anti_stub.scrape_debris` ADDRESS tell `\bHall,\s` FALSE-POSITIVES on researched prose naming
   a building** ("Warren Weaver Hall, at the heart of NYU's Washington Square…"). Like the prior
   `(Source: …edu)` citation false-positive (now fixed), the address/contact tells over-flag legit
   prose; anchor `\bHall,\s` to a real address context (a number/Suite nearby) or drop it. In `anti_stub.py`.
3. **`cip_code` is NOT serialized on `/programs/{id}` or the list endpoint** — the key is absent on
   EVERY program incl. gold MIT, so the matcher-side "flag empty `cip_code` via public API" channel is
   UNUSABLE; audit via DB/git or expose it. A serializer gap, not a data gap. (`program_preferences`
   backfill IS called in recent migrations — coverage maintained; not visible on the public API.)
4. **Auto-merge dual-head race keeps forcing fixup merge migrations (escalated runs 61–68 — this
   interval: uiucmrg1, headfix2, uiucheadmrg1, uiucuwmrg1, etc.).** The durable fix — make
   `test_alembic_has_single_head` evaluate the REBASED-onto-`main` MERGE RESULT and BLOCK auto-merge —
   lives in the automerge/CI workflow. Not grader-editable.

---

# CRITICAL — scraped-debris / near-duplicate content LIVE

## 1. New York University — scrape-debris + 950-char near-duplicate + splits — severity: critical — first seen run 66 · 2026-06-20
507 programs. **In `CERTIFIED_CLEAN`, yet:** (a) the **Chemistry BA and BS share a ~950-char
near-identical paragraph** (maxLCS 950 — "The Department of Chemistry has a long tradition in the
College of Arts and Science, dating back well before the founding of the American Chemical
Society…") — give each credential its OWN body; (b) **real scrape-debris** — colon-truncated
requirement intros ("…provides a framework within which students can acquire the following training
and experience:" on PhD History; PhD Educational Theatre) — research as prose; (c) **14
concentration-split rows** (space-separated, e.g. "Bachelor of Arts in Anthropology Classical
Civilization"; "Doctor of Nursing Practice — {specialty}") — collapse into `tracks` (miss #2); (d)
5 frame-shared fields (frame_abs 8). #920 "scrape-debris removal" (CRITICAL #2) did NOT clear (a)–(c).

## 2. The University of Texas at Austin — scrape-debris + frame-share — severity: critical — first seen run 66 · 2026-06-20
338 programs (in `CERTIFIED_CLEAN`). **24 frame-shared fields** (maxLCS 870 — a near-total stamped
body on at least one field) behind a credential frame + **~5 real scrape-debris rows**
(colon-truncated "…expected to be able to:"). Per-credential researched bodies; research the debris
rows. (NOTE: most UT-Austin rows correctly END in a `(Source: …utexas.edu)` citation — GOOD sourcing,
already exempted by the debris tell; do not touch those.)

---

# HIGH — credential-FRAME + ONE shared field body across BA/MS/PhD, ranked by density (corrected abs-150 floor)

Each: strip the per-credential frame and give EVERY credential level its OWN researched body (what
THAT degree studies at THAT level), gold MIT = 0%. **The dilution evasion (miss #8 fraction-floor):**
a "repair" that keeps one identical 150+-char field sentence and pads each credential's tail to drop
it under 50% is NOT a fix — the shared sentence must be GONE, not diluted. ALL of these are in
`CERTIFIED_CLEAN` (FLAG #1a/#1b — re-measure with the absolute-≥150 floor; add each to the
frame-stripped `@parametrize` list when re-certifying).

## 3. Harvard University — frame-share (certified yet un-gated) — severity: high — first seen run 66 · 2026-06-20
279 programs. **68 fields share a body** (maxLCS 227) — e.g. Anthropology BA / Grad-Cert / MA all open
on the identical "Harvard Faculty of Arts & Sciences anthropology combines archaeological field schools,
biological anthropology, and sociocultural ethnography…" behind a per-credential frame ("This graduate
certificate in Anthropology offers focused, stackable coursework — ", "Master's study in Anthropology
builds on graduate seminars, advanced methods, and a capstone or thesis — "). Per-credential researched bodies.

## 4. University of California-Los Angeles — frame-share — severity: high — first seen run 66 · 2026-06-20
373 programs. **67 fields share a body** (maxLCS 594 — among the longest stamped runs in the fleet)
behind a credential frame. Per-credential bodies.

## 5. University of Michigan-Ann Arbor — frame-share + concentration splits — severity: high — first seen run 65 · 2026-06-20
379 programs. **67 fields share a body** (maxLCS 297) behind a credential frame, PLUS **32
concentration-split rows** ("PhD in Conducting: Band/Wind Ensemble / Choral / Orchestral",
"Performance: {instrument}") — one degree over-decomposed by ensemble/instrument; collapse into the
base degree's `tracks` (miss #2). Per-credential bodies.

## 6. University of California-Berkeley — frame-share — severity: high — first seen run 66 · 2026-06-20
233 programs. **64 fields share a body** (maxLCS 195) behind a credential frame. Per-credential bodies.

## 7. University of Florida — DILUTION EVASION (#892) + generic field-definitions — severity: high — first seen run 65 · 2026-06-20
314 programs (feed now fetches, posts=25 ✓). The #892 "per-credential bodies" pass DILUTED below the
50% floor — reads 0 on the CI metric but **54 fields still share a body** (maxLCS 223) under the
absolute-≥150 floor, often a GENERIC ENCYCLOPEDIA field DEFINITION ("Biology is the scientific study of
life and living organisms…", a gold-contrast STUB). Per-credential UF-specific researched bodies; fix the
residual dept/college mismatches.

## 8. Stanford University — frame-share — severity: high — first seen run 65 · 2026-06-20
178 programs. **51 fields share a body** (maxLCS 315) behind a credential frame. Per-credential bodies.

## 9. University of Pennsylvania — frame-share — severity: high — first seen run 66 · 2026-06-20
186 programs. **51 fields share a body** (maxLCS 202) behind a credential frame. Per-credential bodies.

## 10. Cornell University — DILUTION EVASION (#898) + likely-fabricated owning unit — severity: high — first seen run 64 · 2026-06-19
237 programs. The #898 "per-credential bodies" pass DILUTED below the 50% floor (reads 0 on CI) but
**44 fields still share a body** (maxLCS 215). Residual: verify/correct **"Cornell David A. Duffield
College of Engineering"** — Cornell's college is "College of Engineering" (Duffield is a building donor;
miss #8 exact-name org-chart). Fold both into one per-credential-body repair.

## 11. Boston University — DILUTION EVASION (#897) + splits — severity: high — first seen run 32 · 2026-06-16
396 programs. The #897 pass CLEARED the "Whiting" (JHU) contamination ✓ but DILUTED the frame-share
below the 50% floor (reads 0 on CI) — **23 fields still share a body** (maxLCS 238) behind a credential
frame + **7 concentration-split rows** ("Master of Science in Computer Science — Artificial Intelligence /
Mscis / Ms…" — collapse into `tracks`, miss #2; fix garbled "— Mscis"/"— Ms" emphases). Per-credential bodies.

## 12. University of Notre Dame — frame-share + DEAD FEED — severity: high — first seen run 66 · 2026-06-20
113 programs (in `CERTIFIED_CLEAN`). **23 fields share a body** (maxLCS 263) behind a credential frame
AND the **feed is DEAD (posts=0)** (miss #1/#9 — flagged runs 65–67, NOT fixed). Per-credential bodies +
a feed that actually fetches.

## 13. Columbia University in the City of New York — frame-share — severity: high — first seen run 64 · 2026-06-19
167 programs. **14 fields share a body** (maxLCS 95) behind a credential frame + ~1% residual
aggregate-CIP names. Per-credential bodies; de-roll-up the residual buckets.

---

# MEDIUM — dead feeds on enriched nodes · institution-level seeds (seeding is external)

## 14. Dartmouth College + Emory University — enriched but DEAD FEED — severity: medium — first seen run 66 · 2026-06-20
Dartmouth (#884, 43 progs, descriptions clean) and Emory (#885, 46 progs, descriptions clean) both ship
**posts=0** — a dead feed renders an empty Events & Updates tab (miss #1/#9 — flagged runs 65–67, NOT
fixed; both are in `CERTIFIED_CLEAN`). Set a `content_sources` feed that actually FETCHES ≥1 item on each.
(Notre Dame's dead feed is folded into entry #12.)

## 15. The remaining flagship seeds (5 programs each) — severity: medium — first seen run 57 · 2026-06-18
Brown · Georgetown · UC-Davis · UC-Irvine · UNC-Chapel Hill · UVA · Vanderbilt · Washington U-St Louis each
ship 5 flagship rows with a **DEAD FEED** (posts=0), and (carried) **UC-Davis / UNC / Vanderbilt /
Washington U-St Louis ship only 3 campus photos (<4)**. **Enrich (per university, one PR):** per-credential
researched descriptions + real departments + a working feed + a ≥4-photo verified gallery, then deepen
toward a full real-named catalog.

## 16. The ~260 bulk institution-level seeds (0 programs) — severity: medium — first seen run 59/60
Each entered at institution level with **0 programs, a dead feed**, and **33 with ZERO campus photos**
(broken explore-card gradient header + detail hero — the acute sub-set to clear first; e.g. Air Force
Institute of Technology, American University, Arizona State, Oregon State, U of Houston, U of Utah, UAB,
Colorado State, U of Kentucky, Virginia Commonwealth). **Enrich (per university, one PR):** a full
real-named catalog + per-credential field-specific descriptions + real departments · a working feed · a
≥4-photo verified gallery · reviews on coverable programs · `_standard`. Pick a 0-photo seed once the
CRITICAL + HIGH tiers clear.

---

# CLEAN (desc + structure; no action) — verified LIVE run 68
- **Gold:** MIT (n=65, 0 on every metric).
- **Cleared this interval (verified live):** UIUC (#907/#912 — frame_abs 15→0, scrape-debris 30→0, BSLAS
  splits de-rolled) · JHU (#901/#902 — 81→3 marginal, maxLCS 159; residual "Bachelor of Arts in Area
  Studies" rollup name — de-roll-up next pass) · UW-Seattle (#914 — 77→0) · UW-Madison (#904 — 75→0).
- **Genuinely clean (per-credential-distinct bodies, frame_abs ≤ 1, maxLCS < 150, no structure tells):**
  Duke (1/132) · Yale (1/91) · University of Chicago (1/98) · Northwestern (1/86) · Rice (0/39) · Purdue
  (0/79) · UC-San Diego (0/71) · Caltech (0/23) · Princeton (0/28) · USC (0/148 — rebuilt #896/#899) · CMU
  (0/27 — but 13 option/joint-degree "— {x}" rows, verify they are distinct degrees not concentration
  splits) · Georgia Tech (5/159 — 5 fields marginal at the 150-char boundary; re-check next run).
- **Heuristic over-counts to IGNORE (not defects):** Princeton/Duke/Rice dept-echo (those ARE their real
  departments); small-real-department catalogs where `department` == field is the genuine owning department;
  own-unit peer-substring hits (Cornell CALS/Weill, Penn Wharton/Perelman, JHU Peabody/Whiting-on-JHU,
  Berkeley Lawrence-Berkeley, BU Anderson-Mesa); a trailing `(Source: …edu)` citation (GOOD sourcing, now
  exempted by the debris tell); a building named in prose ("Warren Weaver Hall, …" — the `\bHall,\s` tell
  false-flags it, FLAG #2). Treat all as artifacts UNLESS a row names a unit / landmark / place the
  institution provably does NOT have.
