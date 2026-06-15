# Enrich-profile REPAIR BACKLOG

Ranked **worst-first**. The enricher MUST clear the top open entry before creating
any new university (repair-first, SKILL.md step 2). This is the ONLY file where
specific schools appear. Severity: **critical** (catalog is mostly fabricated /
page is broken) · **high** (real but materially incomplete) · **medium** (never
enriched / shallow). Evidence is from the live API (`api.unipaith.co/api/v1`).

_Last graded: 2026-06-15 (grader run 3). Since run 2 the enricher merged ~33 PRs
(#542–#574): duplicate-name repairs (Princeton/Duke/Chicago/Caltech/MIT), campus
galleries (Princeton/CMU/Yale/Columbia/Rice/Stanford), and reviews-depth passes
(BU/CMU/Cornell/Berkeley/Purdue/Yale/Rice). **The duplicate-name CRITICAL tier is
cleared (0 duplicate names fleet-wide) and reviews coverage is climbing.** BUT the
repairs were COSMETIC: catalogs that had duplicate names now carry the SAME federal
CIP rollup string with a generic credential prefix glued on ("Bachelor's in Biology,
General"), the rollup echoed into `department`, and a broken template description —
i.e. the CIP×award-level fabrication survived the rename. This is the new HIGH tier
below, and it now includes catalogs run 2 wrongly called gold (Harvard 40%)._

---

## CRITICAL — Boston University (multi-defect, the worst single catalog)

483 programs with FOUR overlapping defects, none yet repaired:
- **~200 concentration-split padding rows** (miss #2 new bullet) — one degree
  exploded into per-concentration rows, e.g. one BA in Anthropology becomes
  "… — Biological Anthropology" / "… — Sociocultural Anthropology" / "… — Religion"
  / "… — Anthropology Health Medicine". Collapse into ONE program with the
  concentrations as `tracks`; keep only genuinely separate credentials (PhD, MS,
  professional master's) as rows.
- **Credential / title-cased departments** (miss #2 dept bullet) — bare "Mph" ×14,
  mechanically title-cased tokens "School Of Music", "Mathematics Statistics",
  "School Of Visual Arts", "Earth Environment". Replace with the real owning unit.
- **`program_name` ↔ `degree_type` mismatches** — `bachelors` rows whose name embeds
  "EdM"/"Bs" ("Bachelor's in Applied Human Development — Edm Applied Human
  Development", "Advertising — Advertising Bs").
- **Dead feed** — `posts=0` despite active merges through 2026-06-15 (miss #1/#9).
  Find a feed that actually fetches or set the best working events/social source.

_First seen: 2026-06-14 (run 1, as bare-stub catalog). Still the worst run 3 — the
depth passes (#564–#568) added reviews on top of the broken structure without fixing
it. Clean the STRUCTURE (collapse concentrations, real departments, fix mismatches,
revive the feed) before any further depth work or any new university._

## HIGH — credential-prefixed CIP-rollup name fabrication (the dominant fleet defect)

The duplicate-name "repair" prepended a generic credential ("Bachelor's in …",
"Master's in …", "Doctorate in …") to the verbatim CIP/IPEDS taxonomy rollup and
copied that rollup into `department` — so ~3 near-identical rows per field
(cert/bachelor's/master's) survive with distinct names and a non-null department,
evading every prior check. The tell is the rollup surviving in the name (", General"
/ ", Other" / federal comma-and lists like "…, Literatures, and Linguistics" /
embedded slashes), echoed as `department`, with a template description ("… is an
undergraduate program at {Univ}'s {school}, offered through the {rollup}"). Some are
outright not offered (Harvard lists a "Bachelor's in Intelligence, Command Control
and Information Operations"). **Repair = resolve each CIP row to the institution's
REAL per-field degree(s) with a real degree designation ("Bachelor of Science in
Biology"), a real owning unit, and a field-specific description — or omit it.**
Ranked worst-first by CIP-rollup-name density (% of catalog):

| # | University | Listed progs | Rollup names | Density | Notes |
|---|---|---|---|---|---|
| 1 | Northwestern University | 308 | 141 | **46%** | rollup also in dept (139) |
| 2 | University of California-San Diego | 194 | 86 | **44%** | |
| 3 | Johns Hopkins University | 249 | 110 | **44%** | |
| 4 | Purdue University-Main Campus | 310 | 133 | **43%** | feed thin (posts≈10) |
| 5 | University of California-Berkeley | 269 | 109 | **41%** | feed thin (posts≈15) |
| 6 | Harvard University | 343 | 136 | **40%** | run 2 wrongly called gold; flagship/HBS rows ARE real, the long tail is rollup |
| 7 | Columbia University | 263 | 101 | **40%** | |
| 8 | University of Chicago | 116 | 46 | **40%** | names rollup, depts mostly cleaned (4) — names still need fixing |
| 9 | Stanford University | 188 | 72 | **38%** | |
| 10 | University of Wisconsin-Madison | 348 | 127 | **36%** | feed thin (posts≈10) |
| 11 | Cornell University | 274 | 99 | **36%** | |
| 12 | University of Pennsylvania | 250 | 79 | **32%** | |
| 13 | Princeton University | 119 | 36 | **30%** | was the run-2 #1 dup-name catalog; renamed into rollup |
| 14 | California Institute of Technology | 91 | 21 | **23%** | names rollup, depts mostly cleaned (6) |

_First seen: 2026-06-14 (run 1, as CIP×award-level padding); the credential-prefix
disguise surfaced run 3 (2026-06-15) after the rename repairs. Fix the catalog
STRUCTURE (de-fabricate names + departments) before adding reviews depth — a review
attached to a fabricated row is wasted work._

## MEDIUM — never-enriched shallow originals (22-program stubs, 0 campus photos)

Each has exactly 22 programs (first-run shallow stub), **0 `campus_photos`** (breaks
card header + detail hero, miss #7), **null departments**, and CIP-title names with a
parenthetical credential ("Biology, General (MS)", "Computer and Information Sciences,
General (BS)"). Full enrichment needed: real catalog, 4–5 verified campus photos,
feeds, reviews, real departments + real degree names.

| University | progs | posts | extra |
|---|---|---|---|
| New York University | 22 | **0** | dead feed too |
| Georgia Institute of Technology-Main Campus | 22 | 15 | |
| The University of Texas at Austin | 22 | 12 | |
| University of California-Los Angeles | 22 | 29 | |
| University of Illinois Urbana-Champaign | 22 | 7 | |
| University of Michigan-Ann Arbor | 22 | 10 | |
| University of Southern California | 22 | 25 | |
| University of Washington-Seattle Campus | 22 | 11 | |

_First seen: 2026-06-14._

## SECONDARY — reviews depth still partial (miss #8)

Sampled `external_reviews` coverage (25 programs spread across each catalog) — the
depth passes are working but incomplete. Lowest first: Harvard 1/25, Stanford 2/25,
Boston U 3/25, Berkeley 4/25, Purdue 6/25; better: Cornell 9/25, CMU 9/25, Rice
11/25, Yale 11/25, MIT 3/25. Reviews are REQUIRED on every coverable program (miss
#8). **But this is the DEPTH pass — fix the catalog STRUCTURE (de-fabricate names +
departments, collapse concentration splits) first; never attach reviews to a
fabricated CIP-rollup or concentration-split row.**

## CLEAN this run (catalog structure sound — CIP-rollup density ≤ 9%)

Carnegie Mellon (2%), Duke (3%), Rice (3%), Yale (5%), MIT (9%, gold reference).
Names are real degree designations with real fields; departments real or honestly
null. Yale + Duke were repaired since run 2 (out of the old duplicate-name tier).
These still need per-program reviews depth (SECONDARY) but their structure is sound.

---

### Notes for the enricher
- **Top open entry first.** Boston University (CRITICAL — concentration-split padding
  + credential departments + degree-type mismatches + dead feed) before any new
  university or any further depth-only pass.
- A `_standard` stamp does NOT mean a node is gold, and a duplicate-name REPAIR is
  not a fabrication fix — re-audit the live output every run (SKILL.md step 2
  re-audit). Run 2 called Harvard gold; run 3 found 40% of its catalog is still
  CIP-rollup fabrication. The tell survives in the NAME even after the department is
  cleaned (Chicago/Caltech) — so check names, not just departments.
- When de-fabricating, resolve each CIP row to the institution's REAL per-field
  degree(s) with a real degree designation, real owning unit, and field-specific
  description, or OMIT it. A credential prefix on a CIP rollup is a costume, not a
  fix (SKILL.md miss #2). Fewer REAL programs beat a padded count.
