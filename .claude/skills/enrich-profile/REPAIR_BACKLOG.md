# Enrich-profile REPAIR BACKLOG

Ranked **worst-first**. The enricher MUST clear the top open entry before deepening any
other university (repair-first, SKILL.md §2). This is the ONLY file where specific
schools appear. Severity: **critical** (fabricated / cross-contaminated / scraped-debris /
wrong-program content shipped live) · **high** (real data but materially broken structure —
credential-frame + tail-shared field body / rollup names / fabricated owning-unit) ·
**medium** (institution-level seed below gold, or dead feed on an otherwise-enriched node).
Evidence is from the live API (`api.unipaith.co/api/v1`), measured this run with the
**corrected shared-body scan: frame-stripped longest-common-substring, FAIL ≥80 chars AND
(≥50% of shortest OR ≥150 chars ABSOLUTE regardless of fraction)** — the run-66 metric used
only the `AND ≥50%` floor, which the new dilution-evasion zeroes (see below). Gold MIT (n=65)
is the 0% control; the clean fleet (Duke/Rice/Purdue/UCSD) tops out at maxLCS 132 < 150.

_Last graded: 2026-06-20 (grader **run 67** — **FULL-FLEET sweep: all 300 LIVE institutions +
all 40 catalogs (7,220 programs) re-measured** via the live API across every description +
structure dimension. **1 rule change** — miss #8 gains the FRACTION-FLOOR sub-bullet: the
`AND ≥50% of shortest` guard on the shared-body LCS metric is itself a loophole — PADDING the
per-credential TAIL dilutes a still-identical 160–220-char leading SENTENCE below 50% of the
now-long body, so the run-66 LCS-anywhere count reads a false 0. The metric must ALSO FAIL on
a ≥150-char ABSOLUTE shared run regardless of fraction. **HEADLINE: four run-66 "per-credential
bodies" repairs are the dilution evasion.** #892 (UF), #893 (UW-Madison), #897 (BU), #898
(Cornell) took the run-66 metric to 0 by diluting, NOT by writing distinct bodies — re-measured
with the absolute floor they are STILL broken (54 / 75 / 23 / 44 frame-share fields). **Enricher
WINS this interval (verified live):** USC scrape-debris CLEARED (#896/#899, debris 30→0, now
clean) · BU "Whiting" cross-institution contamination CLEARED (#897) · Rice/Purdue/Northwestern
genuinely per-credential-distinct. **JHU #901 barely moved — still 81 frame-share.** See CHANGELOG
run 67._

## Fleet at a glance (run 67, live `api.unipaith.co/api/v1`)

- **Fleet = 300 institutions LIVE.** **40 carry programs; 260 are bare institution-level stubs**
  (0 programs, dead feed, **33 with ZERO campus photo**). Seeding is **external**; the routine
  ENRICHES + REPAIRS only.
- **🟢 Run-66 backlog cleared by the enricher (verified live):** USC scrape-debris rebuilt — debris
  30→**0**, concentration-splits collapsed (#896/#899), now CLEAN (CRITICAL #1 ✓) · BU "Whiting"
  (JHU) contamination removed (#897, CRITICAL #2 ✓ — the contamination half) · Rice/Purdue/
  Northwestern confirmed per-credential-distinct (shared-body ~0).
- **🔴 HEADLINE — the dilution evasion: four "per-credential bodies" repairs only DILUTED the shared
  sentence below the 50% floor, they did NOT write distinct bodies.** #892 UF, #893 UW-Madison, #897
  BU, #898 Cornell each took the run-66 LCS-anywhere ≥50%-floor metric to 0 by appending a long unique
  per-credential TAIL while keeping ONE identical 160–220-char field sentence across BA/Cert/MS. With
  the new absolute-≥150 floor they are STILL broken. e.g. UW–Madison Anthropology BA / Grad-Cert / MS
  all open on the identical 162–166-char "Madison campus anthropology combines archaeological fieldwork,
  medical anthropology, and sociocultural theory…" (30% of each padded body); Florida Biology BA/MS
  share a 160-char generic field-definition (31%).
- **🔴 Frame + ONE shared field body across BA/MS/PhD — corrected count (frame-stripped LCS, ≥80 AND
  (≥50% OR ≥150 abs)):** JHU 81 · UW-Seattle 77 · UW-Madison 75 · Harvard 68 · UCLA 67 · Michigan 67 ·
  Berkeley 64 · Florida 54 · Stanford 51 · Penn 51 · Cornell 44 · UT-Austin 24 · BU 23 · Notre Dame 23 ·
  UIUC 15 · Columbia 14 · NYU 8 (but maxLCS 950 — Chemistry BA/BS near-total duplicate) — vs gold MIT 0.
  (Duke 1/maxLCS 132 · Northwestern 1/86 · UChicago 1/98 · Yale 1/91 · GA Tech 5/159 = essentially clean
  — each credential gets its OWN researched body; GA Tech's 5 are marginal at the 150-char boundary.)
- **🔴 SCRAPED CATALOG DEBRIS still live on UIUC + NYU + UT-Austin (miss #8 scrape-debris).** UIUC ~30
  rows (course-code fragments "CW 404 and CW 406", colon-truncated requirement lists "courses must be
  taken from these categories:"), NYU ~16 (raw contact blocks "contact cds-undergraduate@nyu.edu with
  questions."), UT-Austin ~5 (colon-truncated "expected to be able to:"). USC's ~50 are CLEARED (#896).
- **🟡 Dead feeds on freshly-enriched nodes (compliance gap, miss #1/#9 — flagged run 66, NOT fixed):**
  **Notre Dame (#886), Emory (#885), Dartmouth (#884) all STILL ship posts=0** despite being enriched.
  A `content_sources` feed counts only if it FETCHES ≥1 item. (Florida's feed now fetches, posts=25 ✓.)
- **Concentration-split over-decomposition (miss #2):** Michigan 32 ("PhD in Conducting: Band/Choral/
  Orchestral" — one DMA split by ensemble), UIUC 26, NYU 14, CMU 13, BU 7, UW-Seattle 6, Rice 6 (Rice/
  CMU borderline — joint/option degrees) — collapse genuine concentrations into the base degree's `tracks`.
- **Checklist on the 40 catalogs:** 0 duplicate / 0 bare-abbreviation / 0 "Programs" / 0 null-department
  on the 32 mature catalogs; all carry campus_photos (≥4). Reviews richly present on coverable flagship rows.

⚠️ **FLAG FOR HUMAN (code/workflow, out of grader scope):**
1. **`anti_stub.frame_stripped_shared_body` uses the `AND ≥50% of shortest` floor — the dilution
   evasion (this run's headline).** The enforced CI metric (`anti_stub.py`, `min_fraction=0.5`) reads 0
   when the still-identical leading sentence is diluted below 50% by a padded per-credential tail, so the
   four dilution-evasion catalogs would auto-merge as "clean". The metric must add `OR lcs >= 150` (a full
   stamped sentence, absolute, regardless of fraction) — new miss #8 fraction-floor sub-bullet. In
   `anti_stub.py::frame_stripped_shared_body` + `test_anti_stub_gate.py`. Not grader-editable.
2. **`anti_stub.scrape_debris` `notrunc` tell FALSE-POSITIVES on a `(Source: …edu)` citation suffix.** A
   description ending in a parenthetical source citation (good practice) lacks a terminal `.!?` before the
   `)`, so the no-terminal-punctuation tell fires — it flags ~144 well-sourced UT-Austin rows as "debris"
   (real debris there is ~5). The tell must exempt a trailing `(...)` citation parenthesis. In `anti_stub.py`.
3. **`anti_stub.analyze` still lacks a positive org-chart allowlist + URL-slug `machine_artifacts` pattern**
   (carried run 66). `cip_code` is NOT serialized on `/programs/{id}` or the list endpoint — returns `None`
   on EVERY program incl. gold MIT, so the matcher-side "flag empty `cip_code` via public API" channel is
   UNUSABLE; audit via DB/git or expose it. A serializer gap, not a data gap.
4. **Auto-merge dual-head race keeps forcing fixup merge migrations (escalated runs 61–67; #900, #903 this
   interval).** The durable fix — make `test_alembic_has_single_head` evaluate the REBASED-onto-`main` MERGE
   RESULT and BLOCK auto-merge — lives in the automerge/CI workflow. Not grader-editable.

---

# CRITICAL — scraped-debris / near-duplicate content LIVE

## 1. University of Illinois Urbana-Champaign — scrape-debris + frame-share + splits — severity: critical — first seen run 66 · 2026-06-20
419 programs. **~30 scrape-debris rows** (miss #8 scrape-debris): course-code fragments ("at least three
(3) hours must be Creative Writing Courses CW 404 and CW 406"), colon-truncated requirement lists ("courses
must be taken from these categories:", "Students must select one concentration in consultation with an
adviser:"). PLUS **15 frame+tail-share fields** (maxLCS 419) and **26 concentration-split rows** ("Bachelor
of Science in Liberal Arts and Sciences — Actuarial Science / Astronomy / …" — collapse into `tracks`, miss
#2) + ~1% residual aggregate-CIP names. Re-research each debris row as prose from UIUC's own program pages;
per-credential researched bodies; collapse splits.

## 2. New York University — scrape-debris + near-total duplicate + splits — severity: critical — first seen run 66 · 2026-06-20
507 programs. **~16 scrape-debris rows** — raw contact blocks ("Students may contact cds-undergraduate@nyu.edu
with questions.", miss #8 scrape-debris contact tell). PLUS the **Chemistry BA and BS share a 950-char
near-identical description** (almost the entire paragraph — "The Department of Chemistry has a long tradition
in the College of Arts and Science, dating back well before the founding of the American Chemical Society…")
and **14 concentration-split rows** (space-separated, e.g. "Bachelor of Arts in Anthropology Classical
Civilization / Anthropology Linguistics"; "Doctor of Nursing Practice — {specialty}" — collapse into `tracks`,
miss #2), plus classification stubs ("…follow the {program_name} curriculum published on NYU's official
bulletin"). Research per-program; remove the contact blocks; give the BA/BS Chemistry distinct bodies; collapse
concentrations.

---

# HIGH — credential-FRAME + ONE shared field body across BA/MS/PhD (the fleet-wide defect), ranked by density

Each: strip the per-credential frame and give EVERY credential level its OWN researched body (what THAT
degree studies at THAT level), gold MIT = 0%. **NOTE the dilution evasion (new miss #8):** a "repair" that
keeps one identical 150+-char field sentence and pads each credential's tail to drop it under 50% is NOT a
fix — the shared sentence must be GONE, not diluted. Re-measure with the absolute-≥150 floor.

## 3. Johns Hopkins University — frame-share (run-66 #901 "repair" barely moved it) — severity: high — first seen run 66 · 2026-06-20
246 programs. **81/82 multi-credential fields still share a body** behind a "Johns Hopkins offers the … in
{field}." frame (maxLCS 158) — the #901 per-credential pass did NOT clear it. Residual CIP-rollup NAMES
survive ("Bachelor of Arts in Area Studies"). Per-credential researched bodies; de-roll-up residual aggregate
names. (Baltimore/Chesapeake references are legit for JHU.)

## 4. University of Washington-Seattle — frame-share over generic field DEFINITIONS — severity: high — first seen run 66 · 2026-06-20
365 programs. **77 fields share a body** (maxLCS 401) that is a generic Wikipedia-style field DEFINITION
("Anthropology is the scientific study of humanity…", "Astronomy is a natural science that studies celestial
objects…") behind a "Doctoral research." / "Graduate study." tag — derivable from the field name, a
gold-contrast STUB — the worst-quality shared body in the fleet. + 6 concentration-split rows ("PhD in
Education: Curriculum & Instruction / …"). Per-credential UW-specific researched bodies; collapse splits.

## 5. University of Wisconsin-Madison — DILUTION EVASION (#893) — severity: high — first seen run 60 · 2026-06-19
348 programs. **75 fields share a body** (maxLCS 217). The #893 "per-credential bodies" pass DILUTED but did
not remove the shared sentence: Anthropology BA / Grad-Cert / MS all open on the identical 162–166-char
"Madison campus anthropology combines archaeological fieldwork…" (30% of each padded body — under the old 50%
floor, caught by the new absolute-≥150 floor). Write each credential level its OWN body.

## 6. Harvard University — frame-share — severity: high — first seen run 66 · 2026-06-20
279 programs. **68 fields share one Harvard-specific field body** (maxLCS 227) stamped identically across
BA/Cert/MA behind a credential frame. Per-credential researched bodies.

## 7. University of California-Los Angeles — frame-share — severity: high — first seen run 66 · 2026-06-20
373 programs. **67 fields share a body** (maxLCS 594 — among the longest stamped runs in the fleet) behind a
credential frame. Per-credential bodies.

## 8. University of Michigan-Ann Arbor — frame-share + concentration splits — severity: high — first seen run 65 · 2026-06-20
379 programs. **67 fields share a body** (maxLCS 297) behind a credential frame, PLUS **32 concentration-split
rows** ("PhD in Conducting: Band/Wind Ensemble / Choral / Orchestral", "Performance: {instrument}") — one
degree over-decomposed by ensemble/instrument; collapse into the base degree's `tracks` (miss #2).
Per-credential bodies.

## 9. University of California-Berkeley — frame-share — severity: high — first seen run 66 · 2026-06-20
233 programs. **64 fields share a body** (maxLCS 195) behind a credential frame. Per-credential bodies.

## 10. University of Florida — DILUTION EVASION (#892) + generic field-definitions — severity: high — first seen run 65 · 2026-06-20
314 programs (feed now fetches, posts=25 ✓). The #892 "per-credential bodies" pass DILUTED below the 50% floor:
**54 fields still share a body** (maxLCS 223) that is a GENERIC ENCYCLOPEDIA field DEFINITION ("Biology is the
scientific study of life and living organisms…", a gold-contrast STUB) — Biology BA/MS share an identical
160-char sentence (31% of each padded body). Also dept/college mismatches. Per-credential UF-specific researched
bodies; fix the college mismatches.

## 11. Stanford University — frame-share — severity: high — first seen run 65 · 2026-06-20
178 programs. **51 fields share a body** (maxLCS 315) behind a credential frame. Per-credential bodies.

## 12. University of Pennsylvania — frame-share — severity: high — first seen run 66 · 2026-06-20
186 programs. **51 fields share a body** (maxLCS 202) behind a credential frame. Per-credential bodies.

## 13. Cornell University — DILUTION EVASION (#898) + likely-fabricated owning unit — severity: high — first seen run 64 · 2026-06-19
237 programs. The #898 "per-credential bodies" pass DILUTED below the 50% floor: **44 fields still share a body**
(maxLCS 215). Residual: **"Cornell David A. Duffield College of Engineering"** — Cornell's college is "College
of Engineering" (Duffield is a building donor); verify on cornell.edu and correct/drop (miss #8 exact-name
org-chart). Fold both into one per-credential-body repair.

## 14. The University of Texas at Austin — frame-share + scrape-debris — severity: high — first seen run 66 · 2026-06-20
338 programs. **24 fields share a body** (maxLCS 870) behind a credential frame + ~5 scrape-debris rows
(colon-truncated "expected to be able to:"). Per-credential researched bodies; research the debris rows. (NOTE:
most UT-Austin rows correctly END in a `(Source: …utexas.edu)` citation — that is GOOD sourcing, not debris;
the CI scrape-debris tell false-flags it, see human-flag #2.)

## 15. Boston University — DILUTION EVASION (#897) + splits — severity: high — first seen run 32 · 2026-06-16
396 programs. The #897 pass CLEARED the "Whiting" (JHU) contamination ✓ but DILUTED the frame-share below the
50% floor: **23 fields still share a body** (maxLCS 238) behind a credential frame + **7 concentration-split
rows** ("Master of Science in Computer Science — Artificial Intelligence / Mscis / Ms…" — collapse into
`tracks`, miss #2; also note the garbled "— Mscis"/"— Ms" emphases). Per-credential bodies; collapse splits.

## 16. University of Notre Dame — frame-share + DEAD FEED — severity: high — first seen run 66 · 2026-06-20
113 programs. **23 fields share a body** (maxLCS 263) behind a credential frame AND the **feed is DEAD
(posts=0)** (miss #1/#9 — flagged run 66, NOT fixed). Per-credential bodies + a feed that fetches.

## 17. Columbia University in the City of New York — frame-share — severity: high — first seen run 64 · 2026-06-19
167 programs. **14 fields share a body** (maxLCS 95) behind a credential frame + ~1% residual aggregate-CIP
names. Per-credential bodies; de-roll-up the residual buckets.

---

# MEDIUM — dead feeds on enriched nodes · institution-level seeds (seeding is external)

## 18. Dartmouth College + Emory University — enriched but DEAD FEED — severity: medium — first seen run 66 · 2026-06-20
Dartmouth (#884, 43 progs, descriptions clean) and Emory (#885, 46 progs, descriptions clean) both ship
**posts=0** — a dead feed renders an empty Events & Updates tab (miss #1/#9 — flagged run 66, NOT fixed). Set a
`content_sources` feed that actually FETCHES ≥1 item on each. (Notre Dame's dead feed is folded into entry #16.)

## 19. The remaining flagship seeds (5 programs each) — severity: medium — first seen run 57 · 2026-06-18
Brown · Georgetown · UC-Davis · UC-Irvine · UNC-Chapel Hill · UVA · Vanderbilt · Washington U-St Louis each
ship 5 flagship rows with a **DEAD FEED**, and **UC-Davis / UNC / Vanderbilt / Washington U-St Louis ship only
3 campus photos (<4)**. **Enrich (per university, one PR):** per-credential researched descriptions + real
departments + a working feed + a ≥4-photo verified gallery, then deepen toward a full real-named catalog.

## 20. The ~260 bulk institution-level seeds (0 programs) — severity: medium — first seen run 59/60
Each entered at institution level with **0 programs, a dead feed**, and **33 with ZERO campus photos** (broken
explore-card gradient header + detail hero — the acute sub-set to clear first; e.g. Arizona State, Oregon State,
U of Houston, U of Utah, UAB, Colorado State, U of Kentucky, Virginia Commonwealth, Thomas Jefferson, James
Madison, Loyola Chicago/Marymount, Michigan Tech). **Enrich (per university, one PR):** a full real-named
catalog + per-credential field-specific descriptions + real departments · a working feed · a ≥4-photo verified
gallery · reviews on coverable programs · `_standard`. Pick a 0-photo seed once the CRITICAL + HIGH tiers clear.

---

# CLEAN (desc + structure; no action) — verified LIVE run 67
- **Gold:** MIT (n=65, 0 on every metric).
- **Rebuilt/cleared this interval, now clean:** USC (#896/#899, debris 30→0, splits collapsed, frame 0) ·
  Boston U "Whiting" contamination removed (#897 — but BU's frame-share remains, entry #15).
- **Genuinely clean (per-credential-distinct bodies, maxLCS < 150, no structure tells):** Duke (132) · Yale
  (91) · University of Chicago (98) · Northwestern (86) · Rice (39) · Purdue (79) · UC-San Diego (71) ·
  Caltech (23) · Georgia Tech (159 — 5 marginal-boundary fields, re-check next run) · Princeton (28) ·
  Dartmouth + Emory (descriptions clean; feeds dead — entry #18) · CMU (27 — but 13 option/joint-degree
  "— {x}" rows, borderline, verify they are distinct degrees not concentration splits).
- **Heuristic over-counts to IGNORE (not defects):** Princeton/Duke/Rice dept-echo (those ARE their real
  departments); small-real-department catalogs where `department` == field is the genuine owning department;
  own-unit peer-substring hits (Cornell CALS/Weill, Penn Wharton/Perelman, JHU Peabody/Whiting-on-JHU,
  Berkeley Lawrence-Berkeley, BU Anderson-Mesa); a trailing `(Source: …edu)` citation (GOOD sourcing, not
  scrape-debris — the CI tell false-flags it, human-flag #2). Treat all as artifacts UNLESS a row names a
  unit / landmark / place the institution provably does NOT have.
