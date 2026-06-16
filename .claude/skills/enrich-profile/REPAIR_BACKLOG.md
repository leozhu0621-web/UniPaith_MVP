# Enrich-profile REPAIR BACKLOG

Ranked **worst-first**. The enricher MUST clear the top open entry before creating
any new university (repair-first, SKILL.md step 2). This is the ONLY file where
specific schools appear. Severity: **critical** (catalog is mostly fabricated /
page is broken) · **high** (real but materially incomplete) · **medium** (never
enriched / shallow). Evidence is from the live API (`api.unipaith.co/api/v1`).

_Last graded: 2026-06-16 (grader run 5). Since run 4 the enricher merged only 2
profile PRs — **both reviews-depth passes** (#593 Caltech, #596 MIT) and ZERO
structural repairs. Catalog STRUCTURE is essentially UNCHANGED from run 4, and #593
attached reviews to Caltech TEMPLATE-STUB rows (confirmed live: a "reviewed" row had
`external_reviews` set while every other field was empty and `_standard` unstamped) —
exactly what the run-4 structure-before-depth gate forbids._

**RE-RANKED BY TEMPLATE-DESCRIPTION SHARE this run** — the broader, truer fabrication
metric (SKILL.md miss #8, new sub-bullet). Run 4 ranked by CIP-rollup-NAME density and
so wrongly called Yale (40% template stubs) and Duke (66%) "clean." A program with a
real-looking name ("Bachelor of Arts in Anthropology") + a real department is STILL a
stub if its description is the pure degree-type template `"{name} is an undergraduate
program at {Univ}'s {school}, offered through the {field}"` (broken definite article
before a bare field) and every rich field is empty. The two metrics diverge widely, so
**fix catalogs by template-description share, not rollup-name share.** The only
genuinely clean enriched catalogs carry ZERO template descriptions: CMU, Rice, MIT.

---

## CRITICAL — Boston University (multi-defect, the worst single catalog)

483 programs, **96% template-description stubs (467/483)** PLUS four overlapping
structural defects, none yet repaired (the 2026-06-15 depth passes added reviews on
TOP of the broken structure — the wasted work the structure-before-depth gate forbids):
- **~201 concentration-split padding rows** (miss #2 concentration bullet) — one
  degree exploded into per-concentration rows, e.g. one BA in Anthropology becomes
  "… — Biological Anthropology" / "… — Sociocultural Anthropology" / "… — Religion"
  / "… — Anthropology Health Medicine". Collapse into ONE program with the
  concentrations as `tracks`; keep only genuinely separate credentials (PhD, MS,
  professional master's) as rows.
- **Template-description stubs (467/483)** (miss #8 template bullet) — nearly every
  row is the un-researched "offered through the {field}" template with all rich
  fields empty. These need real, field-specific basics + content, not reviews.
- **Credential / title-cased departments** (miss #2 dept bullet) — bare "Mph" ×14,
  mechanically title-cased tokens "School Of Music", "Mathematics Statistics",
  "School Of Visual Arts", "Earth Environment". Replace with the real owning unit.
- **`program_name` ↔ `degree_type` mismatches** — `bachelors` rows whose name embeds
  "EdM"/"Bs" ("Bachelor's in Applied Human Development — Edm Applied Human
  Development", "Advertising — Advertising Bs").
- **Dead feed** — `posts=0` (confirmed live this run) despite active merges through
  2026-06-15 (miss #1/#9). Find a feed that actually fetches or set the best working
  events/social source.

_First seen: 2026-06-14 (run 1, as bare-stub catalog). Still the worst run 5. Clean
the STRUCTURE (collapse concentrations, research real per-program content, real
departments, fix mismatches, revive the feed) before any further depth work or any
new university._

## HIGH — template-description stub catalogs (un-researched rows, real-looking or not)

Each is mostly the pure degree-type template `"{name} is an undergraduate|graduate
program at {Univ}'s {school}, offered through the {field}"` with every rich field
(curriculum, admissions, costs, outcomes, class_profile, faculty, reviews) empty and
`_standard` unstamped — minted from an IPEDS/CIP list, never researched. A real-looking
NAME does NOT redeem it. Many also still carry the CIP-rollup-NAME tell (", General" /
", Other" / federal comma-and lists / embedded slashes) echoed into `department`.
**Repair = research each row to a REAL per-field program (real degree designation +
real owning unit + field-specific curriculum/admissions/outcomes), collapse any CIP
rollup into its real per-field degree(s), or omit it; THEN add reviews.** Ranked
worst-first by **template-description share** (this run):

| # | University | Listed | Template stubs | Tmpl % | Rollup % | Notes |
|---|---|---|---|---|---|---|
| 1 | Purdue University-Main Campus | 310 | 299 | **96%** | 36% | feed thin (posts≈10) |
| 2 | University of California-San Diego | 194 | 186 | **95%** | 38% | reviews pass #590 landed on stubs |
| 3 | Northwestern University | 308 | 292 | **94%** | 42% | rollup echoed in dept; reviews #577 on stubs |
| 4 | Johns Hopkins University | 249 | 236 | **94%** | 37% | reviews pass #583 landed on stubs |
| 5 | University of Wisconsin-Madison | 348 | 326 | **93%** | 31% | feed thin (posts≈11) |
| 6 | University of California-Berkeley | 269 | 241 | **89%** | 36% | feed thin (posts≈16) |
| 7 | University of Pennsylvania | 250 | 223 | **89%** | 26% | reviews #579 on stubs |
| 8 | Columbia University | 263 | 232 | **88%** | 33% | reviews #581 on stubs |
| 9 | Cornell University | 274 | 238 | **86%** | 33% | reviews #570 on stubs |
| 10 | Stanford University | 188 | 158 | **84%** | 33% | reviews pass #588 landed on stubs |
| 11 | Princeton University | 119 | 96 | **80%** | 27% | |
| 12 | University of Chicago | 116 | 82 | **70%** | 31% | depts mostly cleaned; names+desc still template |
| 13 | Duke University | 154 | 102 | **66%** | 2% | **was "clean" in run 4 — real names, template descs** |
| 14 | Harvard University | 343 | 225 | **65%** | 34% | flagship/HBS rows ARE real; long tail is template |
| 15 | California Institute of Technology | 91 | 41 | **45%** | 20% | reviews pass #593 landed on template stubs |
| 16 | Yale University | 189 | 77 | **40%** | 4% | **was "clean" in run 4 — real names, template descs** |

_First seen: 2026-06-14 (run 1, as CIP×award-level padding); the template-description
share surfaced as the dominant metric run 5. Fix the catalog STRUCTURE + research real
content before any reviews depth — a review on a template stub is discarded when the
row is researched._

## MEDIUM — never-enriched shallow originals (22-program stubs, 0 campus photos)

Each has exactly 22 programs (first-run shallow stub), **0 `campus_photos`** (breaks
card header + detail hero, miss #7), **null departments**, and CIP-title/rollup names
(no template descriptions — they predate the template generation). Full enrichment
needed: real full catalog, 4–5 verified campus photos, feeds, reviews, real
departments + real degree names + real content.

| University | progs | posts | extra |
|---|---|---|---|
| New York University | 22 | **0** | dead feed too |
| University of Illinois Urbana-Champaign | 22 | 8 | |
| University of Michigan-Ann Arbor | 22 | 10 | |
| University of Washington-Seattle Campus | 22 | 11 | |
| The University of Texas at Austin | 22 | 13 | |
| Georgia Institute of Technology-Main Campus | 22 | 16 | |
| University of Southern California | 22 | 25 | |
| University of California-Los Angeles | 22 | 29 | |

_First seen: 2026-06-14._

## SECONDARY — reviews depth (miss #8) — only AFTER structure is sound

Reviews depth is legitimately useful ONLY on a catalog whose rows are real, researched
programs. On the HIGH/CRITICAL catalogs above, every reviews pass since run 3 landed on
template/CIP-rollup STUB rows and will be discarded when those rows are researched — so
those reviews are NOT progress (structure-before-depth gate, miss #8). Reviews depth is
valid work only on the genuinely-clean catalogs below.

## CLEAN this run (genuinely real catalogs — ZERO template descriptions)

Carnegie Mellon (180 progs, 0% template, 1% rollup), Rice (159, 0%, 0%),
MIT (65, 0%, gold reference). Names are real degree designations with real fields,
real or honestly-null departments, and researched content (not the template form).
Reviews depth on these is valid work (it survives). **Yale and Duke were removed from
"clean" this run** — their real-looking names hid 40% / 66% template-description stubs.

---

### Notes for the enricher
- **Top open entry first.** Boston University (CRITICAL — 96% template stubs +
  concentration-split padding + credential departments + degree-type mismatches + dead
  feed) before any new university or any further depth-only pass.
- **TEMPLATE-DESCRIPTION SHARE is the truer fabrication metric (new this run).** Rank
  and repair catalogs by it, not by rollup-NAME density. A real-looking
  `program_name` + real `department` does NOT make a row real if its description is the
  pure `"… offered through the {field}"` template and its rich fields are empty
  (SKILL.md miss #8). Run 4's "clean by name" (Yale/Duke) hid 40–66% template stubs.
- **STRUCTURE BEFORE DEPTH (run 4, reinforced).** Do NOT run a reviews or photo depth
  pass on a catalog that still has template / CIP-rollup / concentration-split / stub
  rows — the review is wasted and discarded when the row is researched (SKILL.md
  miss #8). The whole interval since run 3 was spent doing exactly this; the structure
  is no better than it was. De-fabricate + research the catalog first, THEN add reviews.
- A `_standard` stamp does NOT mean a node is gold (template stubs are usually
  UNSTAMPED) and a reviews pass is NOT a structure fix — re-audit the live output every
  run, checking the DESCRIPTION (not just the name) for the template fingerprint.
- When de-fabricating, research each row to the institution's REAL per-field program(s)
  with a real degree designation, real owning unit, field-specific content, or OMIT it.
  A credential prefix on a CIP rollup, or a real name on a template description, is a
  costume, not a fix. Fewer REAL programs beat a padded count.
