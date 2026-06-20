# Enrich-profile REPAIR BACKLOG

Ranked **worst-first**. The enricher MUST clear the top open entry before deepening any
other university (repair-first, SKILL.md §2). This is the ONLY file where specific
schools appear. Severity: **critical** (fabricated / cross-contaminated / scraped-debris /
wrong-program content shipped live) · **high** (real data but materially broken structure —
credential-frame + tail-shared field body / rollup names / fabricated owning-unit) ·
**medium** (institution-level seed below gold, or dead feed on an otherwise-enriched node).
Evidence is from the live API (`api.unipaith.co/api/v1`), measured this run with an
**LCS-anywhere (frame-stripped) shared-body scan** — NOT the leading-prefix count that
run 65 used and that false-cleared most of the mature fleet (see CHANGELOG run 66). Gold
MIT (n=65) is the 0% control.

_Last graded: 2026-06-20 (grader **run 66** — **FULL-FLEET sweep: all 300 LIVE institutions
+ all 40 catalogs re-measured** via the live API across every description + structure
dimension, with the shared-body metric switched to **longest-common-substring measured
ANYWHERE after stripping a leading credential frame** (gold MIT = 0%). **1 rule change** —
miss #8 gains the SCRAPED-CATALOG-DEBRIS sub-bullet (a raw degree-requirements / course-code /
contact-address fragment as `description_text` is an un-researched stub that ZEROES every
share metric and passes the gold contrast). **HEADLINE: run 65 mis-graded the fleet.** Run 65
measured shared-body as a LEADING PREFIX, which the per-credential FRAME zeroes — so it
false-cleared ~12 mature catalogs ("genuinely clean": Harvard / JHU / UCLA / UW-Seattle /
Penn / Berkeley were ALL broken). Measured by LCS-anywhere, **16 catalogs ship a credential
frame over ONE field body stamped across BA/MS/PhD**, and the four LARGEST catalogs ship
SCRAPED CATALOG DEBRIS. The enricher DID clear run-65 CRITICAL #1 (Northwestern rebuilt #888,
0 contamination) + HIGH #2 Purdue (#889) + HIGH #3 Rice (#891), and Florida's feed now
fetches (posts=25). See CHANGELOG run 66._

## Fleet at a glance (run 66, live `api.unipaith.co/api/v1`)

- **Fleet = 300 institutions LIVE.** **40 carry programs; 260 are bare institution-level stubs**
  (0 programs, dead feed, **33 with ZERO campus photo**). Seeding is **external**; the routine
  ENRICHES + REPAIRS only.
- **🟢 Run-65 backlog cleared by the enricher (verified live):** Northwestern rebuilt 308→125 with
  **0 contamination** (#888, CRITICAL #1 ✓) · Purdue rebuilt to per-credential bodies, shared-body
  0 (#889, #2 ✓) · Rice per-credential bodies, shared-body 0 (#891, #3 ✓) · Florida feed now
  fetches (posts=25, #883). Emory (#885, 46 progs) shipped CLEAN descriptions (shared-body 0).
- **🔴 HEADLINE REGRESSION — run 65's "genuinely clean" list was wrong; the credential-FRAME +
  ONE-shared-field-body defect is FLEET-WIDE, hidden from run 65's leading-prefix count.** Measured
  by LCS-anywhere (frame-stripped, ≥80 chars AND ≥50% of the shortest sibling), the count of
  multi-credential fields whose BA/MS/PhD share one field body: **UW-Madison 109/111 · Florida
  102/102 · JHU 81/82 · UW-Seattle 77/77 · Harvard 75/77 · Michigan 71/74 · UCLA 70/77 · Penn
  55/56 · Stanford 51/58 · BU 46/79 · Berkeley 40/68 · Cornell 38/71 · Notre Dame 25/28 · UT-Austin
  21/88 · UIUC 17/96 · Columbia 14/42**, vs gold MIT 0. (Duke 2, Yale 1, UChicago 1, Georgia Tech 5,
  Purdue/Rice/Northwestern/MIT/Emory/Caltech/UCSD/Dartmouth/Princeton 0 = the genuinely-clean
  per-credential model: each credential gets its OWN researched body, e.g. Duke "biology majors
  explore… field work at the Duke Forest" (BA) vs "biology doctoral students pursue dissertation
  research…" (PhD).)
- **🔴 SCRAPED CATALOG DEBRIS on the four LARGEST catalogs (new rule, miss #8).** USC ships ~50/520
  rows whose `description_text` is a raw degree-requirements / course-code fragment ("28 additional
  units must be selected from MATH 225, MATH 226…"; "Four MATH courses at the 400-level…, chosen
  from the following list:"), a capstone-options list, or even a CONTACT/ADDRESS block ("…Stonier
  Hall, Suite 101… (213) 740-1060 Email:…@…edu") — frequently truncated mid-sentence and sometimes
  MISMATCHED to the wrong program (an Archaeology degree carrying American-Studies requirements).
  UIUC 18, NYU 11, UT-Austin 2 carry the same class. Each is unique per row → it scores 0 on every
  share metric, so run 65 graded these "clean."
- **🔴 Residual cross-institution contamination LIVE — Boston University.** "Master of Science in
  Data Science… **Whiting's** MS in Data…" — Whiting = JHU's engineering school (flagged run 65,
  NOT fixed). Clear it (miss #8 named-unit-truth + positive allowlist).
- **🟡 Dead feeds on freshly-enriched nodes (compliance gap, miss #1/#9 verify-feed-fetches):**
  **Notre Dame (#886), Emory (#885), Dartmouth (#884) all ship posts=0** despite being enriched
  this interval. A `content_sources` feed counts only if it FETCHES ≥1 item.
- **Concentration-split over-decomposition (miss #2):** Michigan 33 ("PhD in Performance: Bassoon /
  Cello / Flute / French Horn…" — one DMA split by instrument), UIUC 26, NYU 17 (space-separated:
  "Anthropology Classical Civilization", "Anthropology Linguistics"), CMU 15, USC 8, Rice 6 — collapse
  into the base degree's `tracks`.
- **Checklist on the 40 catalogs:** 0 duplicate / 0 bare-abbreviation / 0 "Programs" / 0 null-department
  on the 32 mature catalogs; **all carry a campus_photos[0]** (≥4 not individually re-counted this run —
  re-verify the 5 run-65 photo-light seeds). Reviews richly present on coverable flagship rows.

⚠️ **FLAG FOR HUMAN (code/workflow, out of grader scope):**
1. **Auto-merge dual-head race keeps forcing fixup merge migrations (escalated runs 61–66).** The
   durable fix — make `test_alembic_has_single_head` evaluate the REBASED-onto-`main` MERGE RESULT and
   BLOCK auto-merge — lives in the automerge/CI workflow (SKILL §8 step 5). Not grader-editable.
2. **`anti_stub.analyze` lets the run-66 defects through green CI (live proof).** (a) **NO LCS-anywhere
   frame-stripped shared-body metric** — it measures the leading PREFIX, so the 16-catalog credential-
   frame + tail-share passes all score 0 and join CERTIFIED_CLEAN; `analyze` must strip a leading
   credential frame and measure the shared body ANYWHERE (longest common substring), not as a leading
   prefix. (b) **NO scrape-debris metric** — a requirements/course-code/contact-address fragment is
   unique per row, so the share/form metrics read 0 (new miss #8 scrape-debris sub-bullet); add a tell
   for course-code tokens, unit-count openings, trailing-colon / mid-sentence truncation, address/email,
   and program/field mismatch. (c) **NO positive org-chart allowlist** for named units → BU "Whiting"
   (JHU) auto-merged. (d) URL-slug `machine_artifacts` pattern still unimplemented. All in `anti_stub.py`
   + `test_anti_stub_gate.py`. Not grader-editable.
3. **`cip_code` is NOT serialized on `/programs/{id}` or the list endpoint** — returns `None` on EVERY
   program incl. gold MIT, so the matcher-side "flag empty `cip_code` via public API" channel is UNUSABLE;
   audit via DB/git or expose it. A serializer gap, not a data gap.

---

# CRITICAL — scraped-debris / cross-contaminated content LIVE

## 1. University of Southern California — scraped catalog debris + wrong-program content — severity: critical — first seen run 66 · 2026-06-20
520 programs. ~50/520 `description_text` are RAW SCRAPED CATALOG DEBRIS (miss #8 scrape-debris): degree-
requirements / course-code fragments ("28 additional units must be selected from MATH 225, MATH 226…",
"Four MATH courses at the 400-level or above are required, chosen from the following list:"), capstone-
option lists ending on a colon, and a raw CONTACT/ADDRESS block ("…Stonier Hall, Suite 101… (213)
740-1060 Email:…@…edu"). Several are TRUNCATED mid-sentence and at least two are MISMATCHED to the wrong
program (Archaeology row → American-Studies requirements; "American Studies and Ethnicity" row opens on
"African American Studies is a multidisciplinary program…"). Re-RESEARCH each as prose about the field
from USC's own program pages; never drop raw catalog text into `description_text`. Also 8 concentration-
split rows (miss #2). (Unique-per-row, so it scored 0 on every share metric — run 65 graded USC "clean".)

## 2. Boston University — cross-institution contamination + frame-share — severity: critical — first seen run 32 · 2026-06-16
399 programs. **1 contamination row LIVE** (flagged run 65, NOT fixed): "Master of Science in Data
Science… **Whiting's** MS in Data…" — Whiting = Johns Hopkins' engineering school. Research from BU's own
page and clear it (miss #8 named-unit-truth; verify against BU's org chart, not a denylist). THEN the
frame+tail-share: **46/79 multi-credential fields share one field body** behind a credential frame; give
each credential its own researched body. + 11 concentration-split rows. (The earlier "minor" stub —
re-check #880's fix.)

---

# HIGH — credential-FRAME + ONE shared field body across BA/MS/PhD (the fleet-wide defect), ranked by density

Each: strip the per-credential frame and give EVERY credential level its OWN researched body (what THAT
degree studies at THAT level), gold MIT = 0%. Frame forms seen: "{Univ} offers the undergraduate major
in {field}.", "Master's study in {field} builds on graduate seminars, advanced methods, and a capstone or
thesis —", "This graduate certificate in {field} offers focused, stackable coursework —", a bare
"Doctoral research." / "Graduate study." tag.

## 3. University of Wisconsin-Madison — severity: high — first seen run 60 · 2026-06-19
348 programs. **109/111 multi-credential fields share one field body** behind a "UW–Madison offers the
{…} in {field}." frame (leading-prefix reads 0 — the run-66 evasion). Per-credential researched bodies.

## 4. University of Florida — frame-share + generic field-definition bodies — severity: high — first seen run 65 · 2026-06-20
314 programs (feed now fetches, posts=25 ✓). **102/102 multi-credential fields share a body** that is a
GENERIC ENCYCLOPEDIA field DEFINITION ("Public health is the science and practice of protecting
populations…", "Cell biology is the study of the structure, function…") — derivable from the field name, a
gold-contrast STUB — plus dept/college mismatches (dept "Food Science and Human Nutrition" vs body "College
of Liberal Arts and Sciences"). Per-credential UF-specific researched bodies; fix the college mismatches.

## 5. Johns Hopkins University — frame-share + residual rollup — severity: high — first seen run 66 · 2026-06-20
246 programs. **81/82 multi-credential fields share a body** behind a "Johns Hopkins offers the … in
{field}." frame. Residual CIP-rollup NAMES survive ("Bachelor of Arts in Area Studies"). Per-credential
bodies; de-roll-up the residual aggregate names. (Baltimore/Chesapeake references are legit for JHU.)

## 6. University of Washington-Seattle — frame-share over generic field definitions — severity: high — first seen run 66 · 2026-06-20
365 programs. **77/77 multi-credential fields share a body** that is a generic Wikipedia-style field
DEFINITION ("Anthropology is the scientific study of humanity…", "Astronomy is a natural science that
studies celestial objects…") behind a "Doctoral research." / "Graduate study." tag — the worst-quality
shared body in the fleet. Per-credential UW-specific researched bodies.

## 7. Harvard University — severity: high — first seen run 66 · 2026-06-20
279 programs. **75/77 multi-credential fields share one field body** (real Harvard-specific, but stamped
identically across BA/Cert/MA behind a credential frame). Per-credential researched bodies.

## 8. University of Michigan-Ann Arbor — frame-share + concentration splits — severity: high — first seen run 65 · 2026-06-20
379 programs. **71/74 multi-credential fields share a body** behind a credential frame, PLUS **33
concentration-split rows** ("PhD in Performance: Bassoon / Cello / Flute / French Horn…", "Conducting:
Choral/Orchestral", "Musicology: Ethnomusicology/History") — one degree over-decomposed by instrument/
ensemble; collapse into the base degree's `tracks` (miss #2). Per-credential bodies.

## 9. University of California-Los Angeles — severity: high — first seen run 66 · 2026-06-20
373 programs. **70/77 multi-credential fields share a body** behind a credential frame. Per-credential bodies.

## 10. University of Pennsylvania — severity: high — first seen run 66 · 2026-06-20
186 programs. **55/56 multi-credential fields share a body** behind a credential frame. Per-credential bodies.

## 11. Stanford University — severity: high — first seen run 65 · 2026-06-20
178 programs. **51/58 multi-credential fields share a body** behind a credential frame. Per-credential bodies.

## 12. University of California-Berkeley — severity: high — first seen run 66 · 2026-06-20
233 programs. **40/68 multi-credential fields share a body** behind a credential frame. Per-credential bodies.

## 13. Cornell University — frame-share + likely-fabricated owning unit — severity: high — first seen run 64 · 2026-06-19
237 programs. **38/71 multi-credential fields share a body** behind a credential frame. Residual: **"Cornell
David A. Duffield College of Engineering" on 4 rows** — Cornell's college is "College of Engineering"
(Duffield is a building donor); verify on cornell.edu and correct/drop (miss #8 exact-name org-chart). Fold
both into one per-credential-body repair.

## 14. University of Notre Dame — fresh enrichment, frame-share + dead feed — severity: high — first seen run 66 · 2026-06-20
113 programs (#886, real names + departments). But **25/28 multi-credential fields share a body** behind a
credential frame AND the **feed is DEAD (posts=0)** (miss #1/#9). Per-credential bodies + a feed that fetches.

## 15. The University of Texas at Austin — frame-share + scrape-debris — severity: high — first seen run 66 · 2026-06-20
338 programs. **21/88 multi-credential fields share a body** behind a credential frame + 2 scrape-debris
rows. Per-credential researched bodies.

## 16. University of Illinois Urbana-Champaign — frame-share + scrape-debris + concentration — severity: high — first seen run 66 · 2026-06-20
419 programs. **17/96 multi-credential fields share a body** + **18 scrape-debris rows** (miss #8) + **26
concentration-split rows** (miss #2) + ~1% residual aggregate-CIP names. Per-credential bodies; collapse
splits; research the scrape-debris rows; de-roll-up residuals.

## 17. New York University — concentration + classification stubs + scrape — severity: high — first seen run 66 · 2026-06-20
507 programs. Low frame-share (5) but **17 concentration-split rows** (space-separated, e.g. "Bachelor of
Arts in Anthropology Classical Civilization / Anthropology Linguistics" — collapse into `tracks`, miss #2),
**classification stubs** ("…follow the {program_name} curriculum published on NYU's official bulletin" — a
gold-contrast STUB), a Department-of-Anthropology blurb stamped across the Anthropology rows (cross-field,
miss #8), and 11 scrape-debris rows. Research per-program; collapse concentrations.

## 18. Columbia University in the City of New York — severity: high — first seen run 64 · 2026-06-19
167 programs. **14/42 multi-credential fields share a body** behind a credential frame + ~1% residual
aggregate-CIP names. Per-credential bodies; de-roll-up the residual buckets.

---

# MEDIUM — dead feeds on enriched nodes · institution-level seeds (seeding is external)

## 19. Dartmouth College + Emory University — enriched but DEAD FEED — severity: medium — first seen run 66 · 2026-06-20
Dartmouth (#884, 43 progs, descriptions clean) and Emory (#885, 46 progs, descriptions clean) both ship
**posts=0** — a dead feed renders an empty Events & Updates tab (miss #1/#9). Set a `content_sources` feed
that actually FETCHES ≥1 item on each. (Notre Dame's dead feed is folded into entry #14.)

## 20. The remaining flagship seeds (5 programs each) — severity: medium — first seen run 57 · 2026-06-18
Brown · Georgetown · UC-Davis · UC-Irvine · UNC-Chapel Hill · UVA · Vanderbilt · Washington U-St Louis each
ship 5 flagship rows with **5/5 empty `description_text` + null `department`** + a **DEAD FEED**; re-verify
photo count (run 65: Vanderbilt/UNC/UC-Davis had 3 <4). **Enrich (per university, one PR):** per-credential
researched descriptions + real departments + a working feed + a ≥4-photo verified gallery, then deepen
toward a full real-named catalog.

## 21. The ~260 bulk institution-level seeds (0 programs) — severity: medium — first seen run 59/60
Each entered at institution level with **0 programs, a dead feed**, and **33 with ZERO campus photos**
(broken explore-card gradient header + detail hero — the acute sub-set to clear first; e.g. Arizona State,
Oregon State, U of Houston, U of Utah, UAB, Colorado State, U of Kentucky, Virginia Commonwealth, Thomas
Jefferson, James Madison, Loyola Chicago/Marymount, Michigan Tech). **Enrich (per university, one PR):** a
full real-named catalog + per-credential field-specific descriptions + real departments · a working feed ·
a ≥4-photo verified gallery · reviews on coverable programs · `_standard`. Pick a 0-photo seed once the
CRITICAL + HIGH tiers are clear.

---

# CLEAN (desc + structure; no action) — verified LIVE run 66
- **Gold:** MIT (n=65, 0 on every metric).
- **Rebuilt/repaired this interval, now clean:** Northwestern (#888, 308→125, 0 contamination, shared-body
  1) · Purdue (#889, shared-body 0) · Rice (#891, shared-body 0).
- **Genuinely clean (per-credential-distinct bodies, ~0 shared-body, no structure tells):** Duke ·
  Yale · University of Chicago · UC-San Diego · Caltech · Georgia Tech · Princeton · Dartmouth (descriptions;
  feed dead — entry #19).
- **Heuristic over-counts to IGNORE (not defects):** Princeton dept-echo (40/43 — those ARE Princeton's real
  departments: Anthropology, Chemistry, Classics); small-real-department catalogs where `department` == field
  is the genuine owning department; own-unit peer-substring hits (Cornell CALS/Weill, Penn Wharton/Perelman,
  JHU Peabody/Whiting-on-JHU, Berkeley Lawrence-Berkeley, BU Anderson-Mesa). Treat both as artifacts UNLESS a
  row names a unit / landmark / place the institution provably does NOT have (the BU "Whiting" + USC mismatch).
