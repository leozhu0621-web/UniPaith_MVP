# Enrich-profile REPAIR BACKLOG

Ranked **worst-first**. The enricher MUST clear the top open entry before deepening any
other university (repair-first, SKILL.md §2). This is the ONLY file where specific
schools appear. Severity: **critical** (fabricated / cross-contaminated / scraped-debris /
near-duplicate / **machine-broken template-slot grammar** / wrong-program content shipped live) ·
**high** (real data but materially broken structure — credential-frame + ONE shared field body
across credential levels / a matcher-core field null catalog-wide OR a whole credential TIER null /
a correct repair stranded un-deployed) · **medium** (institution-level seed below gold, or dead
feed on an otherwise-enriched node).

Evidence is from the live API (`api.unipaith.co/api/v1`), measured this run with
`profile_standard/anti_stub.py` (the enforced CI gate's own functions): `analyze`,
`template_slot_artifacts`, `scrape_debris`, `machine_artifacts`, and
`frame_stripped_shared_body(..., abs_chars=150)` over the fully-paginated `/programs` list of every
program-bearing catalog, plus per-`degree_type` tuition coverage. Gold MIT (n=65) is the 0 control.

_Last graded: 2026-06-21 (grader **run 74**). **FULL-FLEET sweep: all 300 LIVE institutions + all 40
catalogs re-measured via the live API.** **1 rule change** — the matcher-core tuition rule keyed the
FAILURE on a catalog AGGREGATE ("0%/near-0% catalog-wide"); it now ALSO measures coverage PER CREDENTIAL
LEVEL, because the dominant residual starvation is a whole GRADUATE tier at 0% hidden behind a healthy
aggregate %. **HEADLINE — the entire run-73 CRITICAL/HIGH tier CLEARED + deployed: UT-Austin (template-slot
3→0, tuition 0→95%, #1036/#1038), Michigan (template-slot 1→0, #1042), Cornell (115 un-terminated bodies →
debris 0, #1047), Notre Dame (frame 23→0, #1039) are all LIVE-CLEAN. Fleet-wide template_slot/debris/machine
= 0; no fabricated/duplicate/bare-abbrev/"Programs"-dept rows on any mature catalog.** The NEW worst tier
is TUITION: BU ships catalog-wide 0% (even bachelors) + 23 frame-dilution fields (repair #1051 STRANDED as
DRAFT); and ~9 structurally-clean catalogs starve the matcher on a whole GRADUATE tier behind a healthy
aggregate (Wisconsin grad 0%, JHU grad 0%, Harvard/Penn cert+PhD 0%, Michigan PhD 1/148, …). See CHANGELOG run 74._

## Fleet at a glance (run 74, live `api.unipaith.co/api/v1`)

- **Fleet = 300 institutions LIVE.** **40 carry programs; 260 are bare institution-level stubs**
  (0 programs, dead feed, **33 with ZERO campus photo**). Seeding is **external**; the routine
  ENRICHES + REPAIRS only.
- **🟢 Cleared + verified LIVE since run 73:** **UT-Austin** (template_slot 3→0, tuition 0→95%) ·
  **Michigan** (template_slot 1→0; tuition 0→61% — but PhD tier still null, entry #2) · **Cornell**
  (115 un-terminated research bodies → `scrape_debris` 0, #1047 — the run-73 HIGH #3) · **Notre Dame**
  (frame 23→0, #1039). Fleet-wide `template_slot_artifacts` / `scrape_debris` / `machine_artifacts` =
  **0**; 0 duplicate / bare-abbreviation / "Programs"-department / null-department on every mature catalog.
- **🔴 catalog-wide 0% tuition + frame-dilution + a STRANDED repair:** **Boston University** — 0%
  `tuition` on ALL tiers (even bachelors 0/108) + 23 `frame_abs150` dilution fields + concentration-split
  rows. Repair **#1051 is OPEN but DRAFT/unmerged** (stranded enricher work — SKILL §2 / merge-mandatory).
- **🔴 NEW — graduate-TIER tuition starvation behind a healthy aggregate (the new per-credential rule):**
  otherwise structurally-clean catalogs fill the uniform undergrad sticker (bachelor's 100% everywhere)
  but ship a whole GRADUATE tier at 0%, which the catalog aggregate HIDES: **Wisconsin** (cert/master's/PhD/
  prof all 0% — 248 grad rows; agg 29%) · **JHU** (master's 0/95, cert 0/84, PhD 0/4; agg 25%) · **Harvard**
  (cert 0/80, PhD 0/25, master's 17%; agg 30%) · **Penn** (cert 0/16, PhD 0/47, master's 12%; agg 34%) ·
  **CMU** (master's 1/99, PhD 0/41; agg 22%) · **Michigan** (PhD 1/148; agg 61%) · **Yale** (PhD 0/66) ·
  **Columbia** (PhD 0/44, master's 7%) · **Rice** (PhD 0/29, master's 3%). The matcher scores GRADUATE
  budget-fit BLIND. Master's/certificate/professional publish a rate and are rarely funded → unambiguous
  starvation; a blanket PhD-tier null beside a peer that fills it (UT-Austin PhD 86/86) is not the
  "rare funded-waiver" omission.
- **🔴 catalog-wide 0% tuition (aggregate, all tiers null):** **NYU 507 · UIUC 419 · USC 511 ·
  UW-Seattle 360** (+ BU above + the 8 flagship 5-program seeds). The matcher scores budget BLIND on
  every program. Peers prove it knowable: Princeton 100% · Cornell 92% · UF 92% · Stanford 66% · UCLA 64%.
- **Marginal abs-150 over-counts to IGNORE (NOT stubs — distinct per-credential leads that merely repeat a
  factual SUBFIELD-ENUMERATION / department name across levels):** Georgia Tech 5 · Duke 1 · Yale 1 ·
  Chicago 1 · Northwestern 1. Mild redundancy, low priority. (MIT's single `name_prefixed=1` is a
  real-described row — the 0-control's known benign artifact.)

⚠️ **FLAG FOR HUMAN (code/workflow, out of grader scope — the grader edits only the 3 skill files):**
1. **The enforced anti-stub gate's `@parametrize` lists DRIFT from `CERTIFIED_CLEAN`** (`anti_stub.py` +
   `test_anti_stub_gate.py`): a catalog can be `CERTIFIED_CLEAN` yet ship a metric live because that metric's
   list excludes it. Still live this run for the abs-floor list — **BU is structurally registered yet ships
   `frame_abs150=23`** (and `frame_stripped_shared_body`'s DEFAULT reads 0 via the dilution evasion). The
   durable, drift-proof fix is one change: **parametrize the template-slot / abs-floor / debris / artifact
   tests over `CERTIFIED_CLEAN` ITSELF** so a catalog cannot be "certified clean" while any metric is
   un-checked, and add `OR lcs >= 150` to `frame_stripped_shared_body`'s DEFAULT so the dilution evasion
   cannot read a false 0 fleet-wide.
2. **`cip_code` is NOT serialized on `/programs/{id}` or the list endpoint** — absent on EVERY program incl.
   gold MIT (verified again this run), so the matcher-side "flag empty `cip_code` via public API" channel is
   UNUSABLE. The in-repo `PROGRAMS` carry a `cip` key, so it is a serializer gap, not necessarily a data gap —
   expose it or audit via DB/git. (`tuition` IS serialized — the tuition gaps are a real DATA gap.)
3. **`anti_stub.scrape_debris` ADDRESS tell can FALSE-POSITIVE on researched prose naming a building**
   ("Warren Weaver Hall, at the heart of NYU's…"); anchor it to a real address context or drop it. `scrape_debris`
   reads 0 fleet-wide this run (no live instance), so this is a latent note, not a current defect.
4. **A repair's PR title can OVERSTATE the live result** — Michigan #1042 is titled "0%→100%" but the LIVE API
   reads 61% (the PhD tier was never filled). The new per-credential tuition rule (SKILL.md) catches this class
   at the source (measure per `degree_type`, not aggregate); flagged here because the enricher should verify the
   CLAIMED metric live per-tier before declaring done (verify-rendered-output). No deploy-strand observed this run.
5. **Stranded / colliding enrichment PRs.** **#1051 (BU repair) is an OPEN DRAFT** — the live BU defect persists
   because the repair never left draft. Plus a pile-up of stale enrichment drafts opened-but-never-merged-or-closed
   (#769 UCLA — already clean live; #515/#503 Harvard reviews; #499/#489 CMU reviews; #420/#403 gold) clutters the
   queue. Land or close them; schedule one enricher firing per window and dedupe before merge.

---

# HIGH — catalog-wide 0% tuition + frame-dilution + a STRANDED repair — clear FIRST

## 1. Boston University — catalog-wide 0% tuition + 23 frame-dilution fields + splits — severity: high — first seen run 32 · 2026-06-16
396 programs. Ships **0% `tuition` on EVERY tier** (bachelors 0/108, master's 0/161, cert 0/24, PhD 0/76, prof
0/27) — a catalog-wide matcher-budget null (the original aggregate rule) — PLUS **23 fields still share a body**
(`frame_abs150=23`, DILUTION: `frame_frac=0` on the CI fraction-only metric, caught only by the absolute-≥150
floor) behind a credential frame: e.g. MA + PhD Anthropology both open "College of Arts & Sciences anthropology
combines archaeological field schools, biological anthropology, and sociocultural ethnography with the Boston
University Museum collections and global research sites" then diverge only in a generic per-credential tail.
PLUS concentration-split rows ("Master of Science in Computer Science — Artificial Intelligence" — collapse into
`tracks`, miss #2). **Repair #1051 is OPEN but DRAFT** — land it (per-credential researched bodies + collapse
splits + published tuition per credential level), re-scan the FULL `anti_stub` suite → all 0, then merge.

---

# HIGH — graduate-TIER tuition starvation behind a healthy aggregate (NEW this run)

## 2. The graduate-tier-null catalogs — per-credential matcher STARVATION the aggregate hides — severity: high — first seen run 74 · 2026-06-21
Structurally clean catalogs (descriptions/structure pass every metric) that fill the uniform undergrad sticker
(bachelor's tier 100% everywhere) but ship a whole GRADUATE tier at 0%, so the matcher scores graduate budget-fit
BLIND while the catalog AGGREGATE reads "covered":
- **Wisconsin** agg 29% — cert 0/129, master's 0/107, PhD 0/8, prof 0/4 (ENTIRE grad catalog null)
- **JHU** agg 25% — master's 0/95, cert 0/84, PhD 0/4, prof 0/1 (ENTIRE grad catalog null)
- **Harvard** agg 30% — cert 0/80, PhD 0/25, master's 17% (94 grad nulls)
- **Penn** agg 34% — cert 0/16, PhD 0/47, master's 12% (≈73 grad nulls)
- **CMU** agg 22% — master's 1/99, PhD 0/41, cert 0/1 (≈139 grad nulls)
- **Michigan** agg 61% — PhD 1/148 (147 PhD nulls; overlaps the run-73 repair which filled only bach+master's)
- **Yale** agg 47% — PhD 0/66, master's 24%; **Columbia** agg 45% — PhD 0/44, master's 7%; **Rice** agg 47% —
  PhD 0/29, master's 3%
**Fix (per university, one pass):** group coverage by `degree_type`; stamp the published per-program / per-credit
rate for the null master's / certificate / professional tier (these publish a rate and are rarely funded —
unambiguous starvation). For the PhD tier, stamp the published sticker (the matcher's budget input — funding is a
separate signal) or record `tuition` in each genuinely-funded program's `_standard.omitted` with a reason — never a
silent blanket tier null. Re-measure LIVE per tier (not aggregate) before declaring done.

---

# HIGH — catalog-wide 0% tuition (aggregate, all tiers null)

## 3. The zero-tuition catalogs — matcher STARVATION — severity: high — first seen run 70 · 2026-06-21
**4 large + 8 seed catalogs ship 0% `tuition` on every tier** so the CPEF matcher scores budget-fit blind on every
program: **NYU 507 · UIUC 419 · USC 511 · UW-Seattle 360** (BU is entry #1) + the **8 flagship 5-program seeds**
(entry #4). Tuition is institution-PUBLISHED (uniform undergrad sticker / published graduate rate), so a
whole-catalog null is a SKIPPED knowable field, not an honest omission. Stamp the real cited published rate per
credential level in `apply()` for each program; record `_standard.omitted` only for a genuinely-unpublished program.
Peers prove it knowable: Princeton 100% · Cornell 92% · UF 92% · Stanford 66% · UCLA 64%.

---

# MEDIUM — flagship seeds · institution-level seeds (seeding is external)

## 4. The flagship seeds (5 programs each) — EMPTY descriptions + null department + 0% tuition + DEAD FEED — severity: medium — first seen run 57 · 2026-06-18
**Brown · Georgetown · UC-Davis · UC-Irvine · UNC-Chapel Hill · UVA · Vanderbilt · Washington U-St Louis** each ship
5 flagship rows with **EMPTY `description_text`**, **null department**, **0% tuition**, and a **DEAD FEED** (posts=0).
**UC-Davis / UNC / Vanderbilt / Washington U-St Louis ship only 3 campus photos (<4)** (Brown/Georgetown/UC-Irvine 4,
UVA 5). **Enrich (per university, one PR):** a full real-named catalog + per-credential researched descriptions +
real departments + published tuition (per credential level) + a working feed + a ≥4-photo verified gallery, then
deepen toward the full real catalog.

## 5. The ~260 bulk institution-level seeds (0 programs) — severity: medium — first seen run 59/60
Each entered at institution level with **0 programs, a dead feed**, and **33 with ZERO campus photos** (broken
explore-card gradient header + detail hero — the acute sub-set to clear first; e.g. Air Force Institute of
Technology, Arizona State (Campus & Digital Immersion), Azusa Pacific, Colorado State-Fort Collins, James Madison,
Keiser-Ft Lauderdale, Loyola Marymount, Loyola-Chicago, Miami U-Oxford, Michigan Tech, Montclair State, Oakland,
Oregon State, SUNY-ESF, Sacred Heart). **Enrich (per university, one PR):** a full real-named catalog + per-credential
field-specific descriptions + real departments + published tuition · a working feed · a ≥4-photo verified gallery ·
reviews on coverable programs · `_standard`. Pick a 0-photo seed once the HIGH tier clears.

---

# CLEAN (desc + structure; no action) — verified LIVE run 74
- **Gold:** MIT (n=65, 0 on every metric, tuition 69%; the single `name_prefixed=1` is a real-described row).
- **Cleared + verified LIVE since run 73:** **UT-Austin** (n=338 — template_slot 3→0, tuition 95%) · **Michigan**
  (n=379 — template_slot 1→0; **PhD tuition still null, entry #2**) · **Cornell** (n=237 — 115 un-terminated bodies
  → debris 0, tuition 92%) · **Notre Dame** (n=113 — frame 23→0, tuition 53%). Earlier-cleared still clean:
  **Stanford** (n=178), **UCLA** (n=373, tuition 64%), **Penn** (n=186 — but **grad tuition null, entry #2**),
  **JHU** (n=244 — but **grad tuition null, entry #2**), **Berkeley** (n=233, tuition 63%), **UF** (n=314, tuition 92%).
- **Structurally clean (per-credential-distinct bodies, frame_abs ≤ 1 marginal, no debris/artifacts/template-slot):**
  Duke (1/154) · Yale (1/189 — **PhD tuition null, entry #2**) · Chicago (1/91) · Northwestern (1/125) · Rice (0/159
  — **grad tuition null, entry #2**) · Purdue (0/172) · UC-San Diego (0/137) · Caltech (0/43, tuition 63%) ·
  Princeton (0/43, tuition 100%) · Harvard (0/279 — **grad tuition null, entry #2**) · Columbia (0/167 — **grad
  tuition null, entry #2**) · Carnegie Mellon (0/180 — **grad tuition null, entry #2**) · UW-Madison (0/348 — **grad
  tuition null, entry #2**) · Dartmouth (0/43, feed ok, tuition 72%) · Emory (0/46, feed ok, tuition 70%) · NYU
  (0/507 — **0% tuition** #3) · USC (0/511 — **0% tuition** #3) · UIUC (0/419 — **0% tuition** #3) · UW-Seattle
  (0/360 — **0% tuition** #3) · Georgia Tech (5/143 — 5 fields share a SUBFIELD ENUMERATION across levels, each lead
  distinct; mild redundancy, not a stub).
- **Heuristic over-counts to IGNORE (not defects):** Princeton/Duke/Rice dept-echo (those ARE their real
  departments); own-unit peer-substring hits (Cornell CALS/Weill, Penn Wharton/Perelman, JHU Peabody/Whiting,
  Berkeley Lawrence-Berkeley); a trailing `(Source: …edu)` citation (GOOD sourcing); a building named in prose
  ("Warren Weaver Hall, …" — `\bHall,\s` false-flags it, FLAG #3); a shared SUBFIELD ENUMERATION / department name
  across credential levels when each lead is distinct (the abs-150 marginal over-count — GT/Duke/Yale/Chicago/
  Northwestern). Treat all as artifacts UNLESS a row names a unit / landmark / place the institution provably lacks.
