# Enrich-profile REPAIR BACKLOG

Ranked **worst-first**. The enricher MUST clear the top open entry before deepening any
other university (repair-first, SKILL.md §2). This is the ONLY file where specific
schools appear. Severity: **critical** (fabricated / cross-contaminated / scraped-debris /
near-duplicate / **machine-broken template-slot grammar** / wrong-program content shipped live) ·
**high** (real data but materially broken structure — credential-frame + ONE shared field body
across credential levels / a research body shipped UN-TERMINATED catalog-wide / a matcher-core field
null catalog-wide / a correct repair stranded un-deployed) · **medium** (institution-level seed below
gold, or dead feed on an otherwise-enriched node).

Evidence is from the live API (`api.unipaith.co/api/v1`), measured this run with
`profile_standard/anti_stub.py` (the enforced CI gate's own functions): `analyze`,
`template_slot_artifacts`, `scrape_debris`, `machine_artifacts`, and
`frame_stripped_shared_body(..., abs_chars=150)` over the fully-paginated `/programs` list of every
program-bearing catalog. Gold MIT (n=65) is the 0 control.

_Last graded: 2026-06-21 (grader **run 73**). **FULL-FLEET sweep: all 300 LIVE institutions + all 40
catalogs re-measured via the live API.** **1 rule change** — the post-repair re-scan checklist (miss #9
template-slot) enumerated only `frame_abs150` + `template_slot_artifacts`; it now ALSO requires
`scrape_debris == 0` (re-run the FULL `anti_stub` suite after ANY body rewrite), because a hand-AUTHORED
per-credential body shipped without terminal punctuation trips the debris TRUNCATION tell exactly like
scraped junk. **HEADLINE — the run-72 CRITICAL/HIGH tier largely CLEARED + deployed: Stanford (template-slot
51→0), UCLA (template-slot 13→0 + tuition 0→64%), Penn (frame 51→0), JHU (frame 3→0 via the #1031 relay) are
all LIVE-CLEAN. The NEW regression is CORNELL: its #1037 "sibling-aware per-credential bodies" cleared 44
frame-share fields → 0 AND template_slot → 0 but shipped 115 of 237 rows (49%) with NO terminal punctuation —
researched, field-specific bodies that fail the debris truncation tell. STILL OPEN: UT-Austin 3 + Michigan 1
template-slot (repairs IN FLIGHT but unmerged — #1038/#1036/#1039); Notre Dame 23 + BU 23 frame-share; 7 large
+ 8 seed zero-tuition catalogs.** See CHANGELOG run 73._

## Fleet at a glance (run 73, live `api.unipaith.co/api/v1`)

- **Fleet = 300 institutions LIVE.** **40 carry programs; 260 are bare institution-level stubs**
  (0 programs, dead feed, **33 with ZERO campus photo**). Seeding is **external**; the routine
  ENRICHES + REPAIRS only.
- **🟢 Cleared + verified LIVE since run 72:** **Stanford** (template_slot 51→0, frame 0; was run-72 C1) ·
  **UCLA** (template_slot 13→0 + tuition 0→64%; was C2) · **Penn** (frame 51→0; was HIGH #5) · **JHU**
  (frame 3→0 via the #1031 relay migration — the run-72 non-self-healing deploy-strand is RESOLVED). Debris +
  machine-artifacts remain **0** on every mature catalog except Cornell (below); 0 duplicate / bare-abbreviation /
  "Programs"-department on the mature catalogs.
- **🔴 template-slot MACHINE-BROKEN GRAMMAR shipped LIVE (miss #9 template-slot sub-bullet):**
  **UT-Austin 3** (a PhD row slots a *bachelor's* description fragment into "research in ___") and
  **Michigan 1** (empty slot → "research in ,"). Both are in `CERTIFIED_CLEAN` but EXCLUDED from the gate's
  `_TEMPLATE_SLOT_CLEAN`, so CI never fails them (FLAG #1a). Repairs are IN FLIGHT but UNMERGED — UT-Austin
  #1038 (tuition + template-slot) and #1036 (template-slot only) are a DUPLICATE pair (concurrent-run
  collision, FLAG #5); both open, neither merged → still live-broken.
- **🔴 NEW — research body shipped UN-TERMINATED catalog-wide (miss #9 debris-after-rewrite, the new rule):**
  **Cornell 115 of 237 (49%)**. The #1037 "sibling-aware per-credential bodies" repair cleared 44 frame-share
  fields → 0 AND template_slot → 0 but left 115 rows with no terminal `.`/`!`/`?` ("…the Dyson School's
  AACSB-accredited undergraduate business degree, grounded in applied economics" — researched, field-specific,
  but cut off / un-punctuated). Content is REAL (not fabrication / not scraped), so HIGH not critical; shipped
  live because Cornell is absent from the gate's debris-clean `@parametrize` list (FLAG #1c).
- **🔴 credential-FRAME + ONE shared field body across BA/MS/PhD (frame_abs150 > 0, LIVE):** Notre Dame 23
  (frame_frac=23 on the CI DEFAULT metric, yet ships live — absent from the abs-floor `@parametrize` list,
  FLAG #1a/#1b; repair #1039 IN FLIGHT but DRAFT/unmerged) · Boston U 23 (DILUTION — frame_frac=0 on the CI
  fraction-only metric, caught only by the absolute-≥150 floor, FLAG #1b). Gold MIT 0.
- **🟡 matcher-core TUITION null catalog-wide (7 large + 8 seed catalogs at 0% `tuition` LIVE):** NYU 507 ·
  UIUC 419 · USC 511 · UW-Seattle 360 · UT-Austin 338 · Michigan 379 · BU 396 + the 8 flagship 5-program seeds.
  The matcher scores budget-fit BLIND on these. Tuition is set in `apply()` by credential level (NOT in the
  `PROGRAMS` dict — the LIVE API is the sole truth). Peers prove it is knowable: Princeton 100% · Cornell 92% ·
  UF 92% · Dartmouth 72% · Emory 70% · Stanford 66% · UCLA 64%. (The 16-catalog set has SHRUNK to 15 — UCLA
  cleared this interval.)
- **Marginal abs-150 over-counts to IGNORE (NOT stubs — distinct per-credential leads that merely repeat a
  factual SUBFIELD-ENUMERATION / department name across levels):** Georgia Tech 5 · Duke 1 · Yale 1 · Chicago 1 ·
  Northwestern 1. Mild redundancy, low priority. (And MIT's single `name_prefixed=1` is a real-described row —
  the 0-control's known benign artifact.)

⚠️ **FLAG FOR HUMAN (code/workflow, out of grader scope — the grader edits only the 3 skill files):**
1. **The enforced anti-stub gate has compounding coverage/threshold gaps (`anti_stub.py` +
   `test_anti_stub_gate.py`) — every interval a repair clears its targeted metric but ships a DIFFERENT metric
   live because that metric's `@parametrize` list DRIFTS from `CERTIFIED_CLEAN`:**
   (a) **`_TEMPLATE_SLOT_CLEAN` is a SUBSET of `CERTIFIED_CLEAN`** (excludes ut_austin/michigan), so a catalog
   can be `CERTIFIED_CLEAN` AND ship template-slot grammar live.
   (b) **`_ABS_FLOOR_CLEAN` / `_FRAME_STRIPPED_CLEAN` DRIFT from `CERTIFIED_CLEAN`** — Notre Dame / BU are
   `CERTIFIED_CLEAN` but absent from the abs-floor list, so CI never runs `frame_stripped_shared_body(abs_chars=150)`
   on them and they ship frame-share live.
   (c) **The debris-clean list ALSO drifts** — Cornell is `CERTIFIED_CLEAN` but absent from the `scrape_debris`
   `@parametrize` list, so CI never failed #1037's 115 un-terminated rows. **The durable, drift-proof fix is one
   change: parametrize the template-slot / abs-floor / debris / artifact tests over `CERTIFIED_CLEAN` ITSELF** so
   a catalog cannot be "certified clean" while any metric is un-checked. Also add `OR lcs >= 150` to
   `frame_stripped_shared_body`'s DEFAULT so the dilution evasion (BU) cannot read a false 0 fleet-wide.
2. **`cip_code` is NOT serialized on `/programs/{id}` or the list endpoint** — absent on EVERY program incl. gold
   MIT, so the matcher-side "flag empty `cip_code` via public API" channel is UNUSABLE. The in-repo `PROGRAMS`
   carry a `cip` key, so it is a serializer gap, not necessarily a data gap — expose it or audit via DB/git.
   (`tuition` IS serialized — the 15 zero-tuition catalogs are a real DATA gap.)
3. **`anti_stub.scrape_debris` ADDRESS tell can FALSE-POSITIVE on researched prose naming a building**
   ("Warren Weaver Hall, at the heart of NYU's…"); anchor it to a real address context or drop it. Debris reads
   0 fleet-wide this run except the Cornell truncation (a real defect, not this false-positive).
4. **Deploy reliability — improving.** The run-72 non-self-healing JHU strand is RESOLVED (#1031 relay migration
   re-asserted the rows idempotently and deployed). No new deploy-strand observed this run. Durable fixes (deploys
   QUEUE instead of cancel; data-write migrations re-assert rows idempotently) live in the workflow.
5. **NEW — concurrent-run PR collision.** UT-Austin has TWO open repair PRs (#1038 tuition+template-slot, #1036
   template-slot-only) and Notre Dame one open DRAFT (#1039) — repairs OPENED but never merged, so the live
   defect persists. Two enricher instances appear to race the same backlog entry; schedule one firing per window
   and dedupe before merge.

---

# CRITICAL — machine-broken template-slot grammar shipped LIVE — clear FIRST

These render visibly broken machine prose a student reads. They cleared the shared-body count, so they read
CLEAN on `analyze` + `frame_stripped` — but the per-credential "repair" SLOTTED a field phrase into a fixed
template (miss #9 template-slot sub-bullet). REPAIRS ARE IN FLIGHT but UNMERGED (so still LIVE): land/dedupe
them, do not start a new university.

## 1. The University of Texas at Austin — 3 template-slot rows + 0% tuition — severity: critical — first seen run 71 · 2026-06-21
338 programs. LIVE carries **3 `template_slot_artifacts` rows** where a PhD row slotted a *bachelor's* description
fragment into "research in ___": "Doctoral study in Anthropology at UT Austin advances original research in **The
Bachelor of Arts in Anthropology at UT Austin introduces the four**, supported by…" (also Computer Science,
History). Rewrite those 3 PhD rows as researched doctoral prose; re-scan the WHOLE catalog → `template_slot_artifacts
== 0` AND `frame_stripped(abs_chars=150) == 0` AND `scrape_debris == 0`, then GRADUATE into `_TEMPLATE_SLOT_CLEAN`.
Also **0% tuition** (entry #6) — fix in the same pass. Two competing PRs are open (#1038 does tuition+template-slot,
#1036 template-slot-only) — DEDUPE and merge ONE; neither has landed (FLAG #5).

## 2. University of Michigan-Ann Arbor — 1 template-slot row + 0% tuition — severity: critical — first seen run 71 · 2026-06-21
379 programs (description-clean otherwise). LIVE carries **1 `template_slot_artifacts` row**: "The Doctor of
Philosophy in Industrial and Operations Engineering at the University of Michigan advances original research **in ,**
analyzes, and improves complex systems…" (empty slot → dangling "research in ,"). Rewrite that one PhD row; re-scan →
0 on the full suite; graduate into `_TEMPLATE_SLOT_CLEAN`. Also **0% tuition** (entry #6).

---

# HIGH — research body shipped UN-TERMINATED catalog-wide (NEW this run)

## 3. Cornell University — 115 un-terminated research bodies (the #1037 regression) — severity: high — first seen run 73 · 2026-06-21
237 programs (frame 44→0 ✓, template_slot 0 ✓, tuition 92% ✓). The #1037 "sibling-aware per-credential bodies"
repair fixed the frame-share dimension but shipped **115 of 237 descriptions (49%) with NO terminal punctuation**,
tripping the `scrape_debris` TRUNCATION tell — e.g. "Applied economics and management — the Dyson School's
AACSB-accredited undergraduate business degree, grounded in applied economics" (no period; reads cut-off). The
CONTENT is real, researched, and field-specific (NOT fabrication, NOT scraped), so this is a mechanical
finish-the-sentence + terminate repair, not a rewrite-from-scratch: give every flagged row a COMPLETE researched
sentence ending in `.`/`!`/`?`. Re-scan the WHOLE catalog → `scrape_debris == 0` (plus the full suite), then add
Cornell to the gate's debris-clean list. Residual from run 72: verify/correct **"Cornell David A. Duffield College of
Engineering"** if still present — Cornell's college is "College of Engineering" (Duffield is a building donor;
miss #8 exact-name org-chart).

---

# HIGH — credential-FRAME + ONE shared field body across BA/MS/PhD — NOT repaired (LIVE)

Each: strip the per-credential frame and give EVERY credential level its OWN researched body (what THAT degree
studies at THAT level), gold MIT = 0%. The dilution evasion (miss #8 fraction-floor): a "repair" that keeps one
identical 150+-char field sentence and pads each credential's tail to drop it under 50% is NOT a fix — the shared
sentence must be GONE, not diluted. Both are `CERTIFIED_CLEAN` but ABSENT from the abs-floor `@parametrize` list
(FLAG #1a/#1b). And the SAME pass must take `template_slot_artifacts` AND `scrape_debris` → 0 (do not trade
frame-share for template-slot or for un-terminated bodies — entries #1–#3's lesson).

## 4. University of Notre Dame — frame-share (CI-flagged yet un-gated) — severity: high — first seen run 66 · 2026-06-20
113 programs (feed fetches, posts=13 ✓, tuition 53% ✓). **23 fields share a body** (frame_abs150=23, frame_frac=23)
behind a credential frame; frame_frac=23 on the CI metric yet CERTIFIED_CLEAN. Per-credential researched bodies.
Repair #1039 is OPEN but DRAFT/unmerged (FLAG #5) — land it (with the full-suite re-scan) or it stays live-broken.

## 5. Boston University — DILUTION EVASION + splits + 0% tuition — severity: high — first seen run 32 · 2026-06-16
396 programs. **23 fields still share a body** (frame_abs150=23, DILUTION — frame_frac=0 on CI) behind a credential
frame + concentration-split rows ("Master of Science in Computer Science — Artificial Intelligence" — collapse into
`tracks`, miss #2) + **0% tuition** (entry #6). Per-credential bodies + collapse splits + tuition backfill.

---

# HIGH — matcher-core field null catalog-wide (the matcher scores budget-fit BLIND)

## 6. The zero-tuition catalogs — matcher STARVATION — severity: high — first seen run 70 · 2026-06-21
**7 large + 8 seed catalogs ship 0% `tuition`** so the CPEF matcher scores budget-fit blind on every program:
**NYU 507 · UIUC 419 · USC 511 · UW-Seattle 360 · UT-Austin 338 · Michigan 379 · BU 396** + the **8 flagship
5-program seeds** (entry #7). Tuition is institution-PUBLISHED (uniform undergrad sticker / published graduate
rate), so a whole-catalog null is a SKIPPED knowable field, not an honest omission ("Also enrich for the MATCH"
tuition rule). Stamp the real cited published rate per credential level in `apply()` for each program; record
`_standard.omitted` only for a genuinely-unpublished program (e.g. a fully-funded PhD). UT-Austin/Michigan/BU
overlap entries #1/#2/#5 — fix tuition in the SAME depth pass. Peers prove it is knowable: Princeton 100% ·
Cornell 92% · UF 92% · Stanford 66% · UCLA 64%.

---

# MEDIUM — flagship seeds · institution-level seeds (seeding is external)

## 7. The flagship seeds (5 programs each) — EMPTY descriptions + null department + 0% tuition + DEAD FEED — severity: medium — first seen run 57 · 2026-06-18
**Brown · Georgetown · UC-Davis · UC-Irvine · UNC-Chapel Hill · UVA · Vanderbilt · Washington U-St Louis** each ship 5
flagship rows with **EMPTY `description_text`**, **null department**, **0% tuition**, and a **DEAD FEED** (posts=0).
**UC-Davis / UNC / Vanderbilt / Washington U-St Louis ship only 3 campus photos (<4)** (Brown/Georgetown/UC-Irvine 4,
UVA 5). **Enrich (per university, one PR):** a full real-named catalog + per-credential researched descriptions + real
departments + published tuition + a working feed + a ≥4-photo verified gallery, then deepen toward the full real catalog.

## 8. The ~260 bulk institution-level seeds (0 programs) — severity: medium — first seen run 59/60
Each entered at institution level with **0 programs, a dead feed**, and **33 with ZERO campus photos** (broken
explore-card gradient header + detail hero — the acute sub-set to clear first; e.g. Air Force Institute of Technology,
Arizona State (Campus & Digital Immersion), Azusa Pacific, Colorado State-Fort Collins, James Madison, Keiser-Ft
Lauderdale, Loyola Marymount, Loyola-Chicago, Miami U-Oxford, Michigan Tech, Montclair State, Oakland, Oregon State,
SUNY-ESF, Sacred Heart). **Enrich (per university, one PR):** a full real-named catalog + per-credential field-specific
descriptions + real departments + published tuition · a working feed · a ≥4-photo verified gallery · reviews on
coverable programs · `_standard`. Pick a 0-photo seed once the HIGH tier clears.

---

# CLEAN (desc + structure; no action) — verified LIVE run 73
- **Gold:** MIT (n=65, 0 on every metric, tuition 69%; the single `name_prefixed=1` is a real-described row).
- **Cleared + verified LIVE since run 72:** **Stanford** (n=178 — template_slot 51→0, tuition 66%) · **UCLA**
  (n=373 — template_slot 13→0, tuition 0→64%) · **Penn** (n=186 — frame 51→0) · **JHU** (n=244 — frame 3→0 via the
  #1031 relay). Earlier-cleared still clean: **Berkeley** (n=233), **UF** (n=314, tuition 92%).
- **Genuinely clean (per-credential-distinct bodies, frame_abs ≤ 1 marginal, no debris/artifacts/template-slot):**
  Duke (1/154) · Yale (1/189) · Chicago (1/91) · Northwestern (1/125) · Rice (0/159) · Purdue (0/172) ·
  UC-San Diego (0/137) · Caltech (0/43) · Princeton (0/43, tuition 100%) · Harvard (0/279) · Columbia (0/167) ·
  Carnegie Mellon (0/180) · UW-Madison (0/348) · Dartmouth (0/43, feed ok) · Emory (0/46, feed ok) ·
  NYU (0/507 — but **0% tuition** #6) · USC (0/511 — **0% tuition** #6) · UIUC (0/419 — **0% tuition** #6) ·
  UW-Seattle (0/360 — **0% tuition** #6) · Georgia Tech (5/143 — 5 fields share a SUBFIELD ENUMERATION across levels,
  each lead distinct; mild redundancy, not a stub).
- **Heuristic over-counts to IGNORE (not defects):** Princeton/Duke/Rice dept-echo (those ARE their real departments);
  own-unit peer-substring hits (Cornell CALS/Weill, Penn Wharton/Perelman, JHU Peabody/Whiting, Berkeley
  Lawrence-Berkeley); a trailing `(Source: …edu)` citation (GOOD sourcing); a building named in prose ("Warren Weaver
  Hall, …" — `\bHall,\s` false-flags it, FLAG #3); a shared SUBFIELD ENUMERATION / department name across credential
  levels when each lead is distinct (the abs-150 marginal over-count — GT/Duke/Yale/Chicago/Northwestern). Treat all as
  artifacts UNLESS a row names a unit / landmark / place the institution provably does NOT have.
