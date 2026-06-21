# Enrich-profile REPAIR BACKLOG

Ranked **worst-first**. The enricher MUST clear the top open entry before deepening any
other university (repair-first, SKILL.md §2). This is the ONLY file where specific
schools appear. Severity: **critical** (fabricated / cross-contaminated / scraped-debris /
near-duplicate / wrong-program content shipped live) · **high** (real data but materially
broken structure — credential-frame + ONE shared field body across credential levels /
rollup names / fabricated owning-unit / a correct repair stranded un-deployed) · **medium**
(institution-level seed below gold, or dead feed on an otherwise-enriched node).

Evidence is from the live API (`api.unipaith.co/api/v1`), measured this run with the
**frame-stripped shared-body scan: longest-common-substring after stripping a leading
credential frame, FAIL ≥80 chars AND (≥50% of shortest OR ≥150 chars ABSOLUTE regardless
of fraction)**, reusing `profile_standard/anti_stub.py` for consistency with the enforced CI
gate. Gold MIT (n=65) is the 0 control; the genuinely clean fleet (Duke/Rice/Purdue/UCSD/USC)
tops out below the 150-char absolute floor.

_Last graded: 2026-06-21 (grader **run 69** — **FULL-FLEET sweep: all 300 LIVE institutions +
all 40 catalogs (≈7,200 programs) re-measured** via the live API across every description +
structure + feed + photo dimension). **1 rule change** — §9 gains the **A-MERGE-IS-NOT-A-DEPLOY**
sub-paragraph: a repair can pass CI + squash-merge yet never reach students when its Deploy
Backend run FAILS/CANCELS (the dual-head race), so the live re-query — not the merge — is the
gate, and a deploy-stranded clean repair is fixed by DRIVING THE DEPLOY, never by rewriting the
already-correct data. **HEADLINE: two correct per-credential repairs are merged-but-NOT-LIVE.**
Michigan (#953) + Columbia (#942) are anti-stub-CLEAN in the repo (frac 0 · abs150 0) and passed
CI, but their Deploy Backend runs were CANCELLED / FAILED (and the #951 dual-head fixup deploy
ALSO failed), so prod STILL serves the old shared-body data — Michigan 67 · Columbia 14 frame-share
fields LIVE. **Enricher WINS this interval (verified LIVE):** Harvard 68→0 (#931 deployed) · NYU
scrape-debris + 950-char Chemistry dup → 0 (#938) · UT-Austin 24 frame + debris → 0 (#943).
See CHANGELOG run 69._

## Fleet at a glance (run 69, live `api.unipaith.co/api/v1`)

- **Fleet = 300 institutions LIVE.** **40 carry programs; 260 are bare institution-level stubs**
  (0 programs, dead feed, **33 with ZERO campus photo**). Seeding is **external**; the routine
  ENRICHES + REPAIRS only.
- **🟢 Cleared by the enricher + DEPLOYED (verified live):** Harvard (#931 — frame 68→0) · NYU
  (#938 — scrape-debris 16→0, Chemistry BA/BS 950-char near-dup gone, frame 8→0) · UT-Austin
  (#943 — frame 24→0, debris ~5→0). Debris + machine-artifacts are now **0 across ALL 40 catalogs**.
- **🔴 HEADLINE — DEPLOY-STRANDED repairs (FLAG #4 bit with a CONFIRMED deploy failure):** Michigan
  #953 + Columbia #942 are anti-stub-CLEAN in the repo and passed CI, but Deploy Backend
  CANCELLED (Michigan 339b1df) / FAILED (Columbia 5792b73), and the #951 dual-head fixup deploy
  also FAILED — so prod still serves the OLD data (Michigan 67 · Columbia 14 frame-share fields
  LIVE). The data is DONE; the fix is to DRIVE THE DEPLOY GREEN (new §9 rule), NOT to rewrite the
  clean catalogs. Entries #1/#2 below.
- **🔴 Un-repaired credential-FRAME + shared body still LIVE (the run-68 enforcement-hole survivors
  the EXISTING un-floored CI metric flags, all `CERTIFIED_CLEAN`, none in the frame-stripped
  `@parametrize` list):** UCLA 67 · Berkeley 64 · Stanford 51 · Penn 51 · Notre Dame 23 (gold MIT 0).
- **🔴 DILUTION evasion still LIVE (frame_abs > 0 but reads 0 on the CI 50%-floor metric):** UF 54 ·
  Cornell 44 · BU 23 · JHU 3 — a long unique per-credential TAIL dilutes a still-identical 160–230-char
  field sentence below 50% of the padded body; caught only by the absolute-≥150 floor (miss #8
  fraction-floor; the CI metric still lacks it fleet-wide — FLAG #1b).
- **🟡 Dead feeds on freshly-enriched full catalogs (compliance gap, miss #1/#9 — flagged runs 65–69,
  NOT fixed):** **Notre Dame (113 progs), Dartmouth (43), Emory (46) all STILL ship posts=0** despite
  being enriched + in `CERTIFIED_CLEAN`. A `content_sources` feed counts only if it FETCHES ≥1 item.
  (Harvard 81 · Purdue 10 · UW-Madison 21 · UT-Austin 17 all fetch ✓.)
- **Concentration-split over-decomposition (miss #2):** Michigan 33 (clearest — "PhD in Conducting:
  Band/Wind Ensemble / Choral / Orchestral", "Performance: {instrument}" — one DMA split by ensemble).
  NYU 22 and CMU 17 are MOSTLY legit-distinct (NYU "— Tisch School of the Arts" is a school suffix;
  "Teaching a World Language 7-12: Chinese/French" are distinct NY-State certs; CMU "AI Engineering —
  Civil/Chemical" are joint programs) — VERIFY before collapsing. BU 9 · Duke/Rice 6 borderline.
- **Checklist on the 40 catalogs:** 0 scrape-debris · 0 machine-artifacts · 0 duplicate · 0 bare-abbreviation ·
  0 "Programs" department · 0 null-department on the 32 mature catalogs; all mature carry campus_photos.
- **Marginal abs-150 over-counts to IGNORE (NOT stubs — distinct per-credential leads that merely repeat
  a factual SUBFIELD-ENUMERATION / department name across levels):** Georgia Tech 5 (Aero/BME/Civil/MSE/ECE —
  each lead distinct, only the subfield list recurs) · Duke 1 (CS) · Yale 1 · Chicago 1 · Northwestern 1.
  Mild redundancy, low priority — deepen if touched, do not prioritize as a stub.

⚠️ **FLAG FOR HUMAN (code/workflow, out of grader scope):**
1. **Two compounding gaps in the enforced anti-stub gate (`anti_stub.py` + `test_anti_stub_gate.py`,
   app/test code — not grader-editable):**
   (a) **COVERAGE drift.** `test_certified_catalog_is_anti_stub_clean` asserts only `analyze().is_clean`,
   which has NO frame-stripped metric; `frame_stripped_shared_body` is asserted by a SEPARATE test over a
   hardcoded `_FRAME_STRIPPED_CLEAN` (now 13 entries — grew this interval to add harvard/nyu/ut_austin/
   columbia/michigan) that still DRIFTS from `CERTIFIED_CLEAN`. Make that test (and `scrape_debris` /
   `machine_artifacts`) parametrize over `CERTIFIED_CLEAN` ITSELF so the lists cannot drift — then
   UCLA/Berkeley/Stanford/Penn/Notre Dame FAIL CI and certification means something.
   (b) **THRESHOLD undercount.** `frame_stripped_shared_body` uses `min_chars=80 AND min_fraction=0.5`; add
   `OR lcs >= 150` to the DEFAULT (only the NYU/MIT/Columbia test passes `abs_chars=150` today) so the
   dilution evasion (UF/Cornell/BU/JHU) cannot read a false 0 fleet-wide.
2. **`anti_stub.scrape_debris` ADDRESS tell `\bHall,\s` can FALSE-POSITIVE on researched prose naming a
   building** ("Warren Weaver Hall, at the heart of NYU's…"); anchor it to a real address context (a
   number / Suite nearby) or drop it. In `anti_stub.py`. (Debris reads 0 fleet-wide this run, so latent.)
3. **`cip_code` is NOT serialized on `/programs/{id}` or the list endpoint** — absent on EVERY program incl.
   gold MIT, so the matcher-side "flag empty `cip_code` via public API" channel is UNUSABLE; audit via
   DB/git or expose it. A serializer gap, not a data gap. (`program_preferences` backfill IS called in
   recent migrations — coverage maintained; not visible on the public API.)
4. **🔴 Auto-merge dual-head race keeps FAILING the prod deploy (escalated runs 61–69 — this run with a
   CONFIRMED deploy failure stranding TWO correct repairs).** Columbia (5792b73) Deploy Backend = FAILURE,
   Michigan (339b1df) = CANCELLED, the #951 merge-heads fixup (2b983e2) deploy = FAILURE — so the
   already-correct Michigan/Columbia data never reached prod. The durable fix — make
   `test_alembic_has_single_head` evaluate the REBASED-onto-`main` MERGE RESULT and BLOCK auto-merge —
   lives in the automerge/CI workflow. Not grader-editable. **This is now the highest-impact infra bug:
   it is silently reverting verified enrichment at the deploy step.**

---

# CRITICAL — correct repair stranded un-deployed (data DONE; DRIVE THE DEPLOY, do NOT rewrite)

## 1. University of Michigan-Ann Arbor — repaired-in-repo, deploy CANCELLED — severity: critical — first seen run 69 · 2026-06-21
379 programs. The per-credential repair #953 (`michpercrd1`) is anti-stub-CLEAN in the repo (frac 0 ·
abs150 0 · `analyze` clean — verified by running `anti_stub` on `michigan_profile.PROGRAMS`), but its
Deploy Backend run was CANCELLED, so **prod STILL serves the OLD shared-body data: 67 frame-share
fields LIVE** (e.g. BA/MS/PhD Chemistry all carry the identical "Chemistry is the scientific study of
matter, its properties, composition, structure…" body behind a 2-word frame "Doctoral research." /
"Graduate study."). **DO NOT rewrite the catalog — it is correct.** Re-drive the deploy green (clear the
dual head, re-trigger Deploy Backend) per the new §9 rule. ALSO collapse the 33 concentration-split rows
("Conducting: Band/Wind Ensemble / Choral / Orchestral", "Performance: {instrument}") into `tracks` (miss
#2) — verify whether that lands in the same data or needs a follow-up.

## 2. Columbia University in the City of New York — repaired-in-repo, deploy FAILED — severity: critical — first seen run 64 · 2026-06-19
167 programs. The per-credential repair #942 (`columbiapercred1`) is anti-stub-CLEAN in the repo (frac 0 ·
abs150 0), but its Deploy Backend run FAILED (and the #951 dual-head fixup deploy also failed), so **prod
STILL serves the OLD shared-body data: 14 frame-share fields LIVE** (maxLCS 95). **DO NOT rewrite the
catalog.** Re-drive the deploy green per §9.

---

# HIGH — credential-FRAME + ONE shared field body across BA/MS/PhD, ranked by density (abs-150 floor) — NOT repaired

Each: strip the per-credential frame and give EVERY credential level its OWN researched body (what THAT
degree studies at THAT level), gold MIT = 0%. **The dilution evasion (miss #8 fraction-floor):** a
"repair" that keeps one identical 150+-char field sentence and pads each credential's tail to drop it
under 50% is NOT a fix — the shared sentence must be GONE, not diluted. ALL of these are in
`CERTIFIED_CLEAN` but ABSENT from the frame-stripped `@parametrize` list (FLAG #1a) — add each to that
list (and to `scrape_debris` / `machine_artifacts`) when re-certifying, and re-measure with the
absolute-≥150 floor.

## 3. University of California-Los Angeles — frame-share (certified yet un-gated) — severity: high — first seen run 66 · 2026-06-20
373 programs. **67 fields share a body** (maxLCS 594 — among the longest stamped runs in the fleet) behind
a per-credential frame. Per-credential researched bodies.

## 4. University of California-Berkeley — frame-share — severity: high — first seen run 66 · 2026-06-20
233 programs. **64 fields share a body** (maxLCS 195) behind a credential frame. Per-credential bodies.

## 5. University of Florida — DILUTION EVASION (#892) + generic field-definitions — severity: high — first seen run 65 · 2026-06-20
314 programs (feed fetches, posts=25 ✓). The #892 "per-credential bodies" pass DILUTED below the 50% floor
— reads 0 on the CI metric but **54 fields still share a body** (maxLCS 223) under the absolute-≥150 floor,
often a GENERIC ENCYCLOPEDIA field DEFINITION ("Biology is the scientific study of life and living
organisms…", a gold-contrast STUB). Per-credential UF-specific researched bodies; fix residual dept/college
mismatches.

## 6. Stanford University — frame-share — severity: high — first seen run 65 · 2026-06-20
178 programs. **51 fields share a body** (maxLCS 315) behind a credential frame. Per-credential bodies.

## 7. University of Pennsylvania — frame-share — severity: high — first seen run 66 · 2026-06-20
186 programs. **51 fields share a body** (maxLCS 202) behind a credential frame. Per-credential bodies.

## 8. Cornell University — DILUTION EVASION (#898) + likely-fabricated owning unit — severity: high — first seen run 64 · 2026-06-19
237 programs. The #898 "per-credential bodies" pass DILUTED below the 50% floor (reads 0 on CI) but
**44 fields still share a body** (maxLCS 215). Residual: verify/correct **"Cornell David A. Duffield
College of Engineering"** — Cornell's college is "College of Engineering" (Duffield is a building donor;
miss #8 exact-name org-chart). Fold both into one per-credential-body repair.

## 9. University of Notre Dame — frame-share + DEAD FEED — severity: high — first seen run 66 · 2026-06-20
113 programs (in `CERTIFIED_CLEAN`). **23 fields share a body** (maxLCS 263) behind a credential frame
AND the **feed is DEAD (posts=0)** (miss #1/#9 — flagged runs 65–69, NOT fixed). Per-credential bodies +
a feed that actually fetches.

## 10. Boston University — DILUTION EVASION (#897) + splits — severity: high — first seen run 32 · 2026-06-16
396 programs. The #897 pass CLEARED the "Whiting" (JHU) contamination ✓ but DILUTED the frame-share below
the 50% floor (reads 0 on CI) — **23 fields still share a body** (maxLCS 238) behind a credential frame +
**9 concentration-split rows** ("Master of Science in Computer Science — Artificial Intelligence" — collapse
into `tracks`, miss #2). Per-credential bodies.

## 11. Johns Hopkins University — DILUTION EVASION residual — severity: high — first seen run 67 · 2026-06-20
244 programs. Reads 0 on the CI 50%-floor metric but **3 fields still share a body** under the absolute-≥150
floor (marginal, maxLCS ~159). Give those 3 fields per-credential-distinct bodies; low effort, finishes JHU.

---

# MEDIUM — dead feeds on enriched catalogs · institution-level seeds (seeding is external)

## 12. Dartmouth College + Emory University — enriched but DEAD FEED — severity: medium — first seen run 66 · 2026-06-20
Dartmouth (#884, 43 progs, descriptions clean) and Emory (#885, 46 progs, descriptions clean) both ship
**posts=0** — a dead feed renders an empty Events & Updates tab (miss #1/#9 — flagged runs 65–69, NOT
fixed; both in `CERTIFIED_CLEAN`). Set a `content_sources` feed that actually FETCHES ≥1 item on each.
(Notre Dame's dead feed is folded into entry #9.)

## 13. The remaining flagship seeds (5 programs each) — severity: medium — first seen run 57 · 2026-06-18
Brown · Georgetown · UC-Davis · UC-Irvine · UNC-Chapel Hill · UVA · Vanderbilt · Washington U-St Louis each
ship 5 flagship rows with a **DEAD FEED** (posts=0), and **UC-Davis / UNC / Vanderbilt / Washington U-St
Louis ship only 3 campus photos (<4)**. **Enrich (per university, one PR):** per-credential researched
descriptions + real departments + a working feed + a ≥4-photo verified gallery, then deepen toward a full
real-named catalog.

## 14. The ~260 bulk institution-level seeds (0 programs) — severity: medium — first seen run 59/60
Each entered at institution level with **0 programs, a dead feed**, and **33 with ZERO campus photos**
(broken explore-card gradient header + detail hero — the acute sub-set to clear first; e.g. Air Force
Institute of Technology, Arizona State (Campus & Digital Immersion), Azusa Pacific, Colorado State-Fort
Collins, James Madison, Keiser-Ft Lauderdale, Loyola Marymount, Loyola-Chicago, Miami U-Oxford, Michigan
Tech, Montclair State). **Enrich (per university, one PR):** a full real-named catalog + per-credential
field-specific descriptions + real departments · a working feed · a ≥4-photo verified gallery · reviews on
coverable programs · `_standard`. Pick a 0-photo seed once the CRITICAL + HIGH tiers clear.

---

# CLEAN (desc + structure; no action) — verified LIVE run 69
- **Gold:** MIT (n=65, 0 on every metric).
- **Cleared + DEPLOYED this interval (verified live):** Harvard (#931 — frame 68→0) · NYU (#938 —
  scrape-debris 16→0, 950-char Chemistry near-dup gone, frame 8→0; 22 "splits" are mostly legit-distinct
  school-suffix / language-cert rows — verify before any collapse) · UT-Austin (#943 — frame 24→0, debris→0).
- **Genuinely clean (per-credential-distinct bodies, frame_abs ≤ 1 marginal, no debris/artifacts):**
  Duke (1/154) · Yale (1/189) · University of Chicago (1/91) · Northwestern (1/125) · Rice (0/159) · Purdue
  (0/172) · UC-San Diego (0/137) · Caltech (0/43) · Princeton (0/43) · USC (0/511) · UIUC (0/419) ·
  UW-Seattle (0/360) · UW-Madison (0/348) · CMU (0/180 — 17 "— {x}" rows are joint/option degrees, verify) ·
  Georgia Tech (5/143 — 5 fields share a SUBFIELD ENUMERATION across levels, each lead distinct; mild
  redundancy, not a stub — deepen if touched).
- **Heuristic over-counts to IGNORE (not defects):** Princeton/Duke/Rice dept-echo (those ARE their real
  departments); small-real-department catalogs where `department` == field is the genuine owning department;
  own-unit peer-substring hits (Cornell CALS/Weill, Penn Wharton/Perelman, JHU Peabody/Whiting-on-JHU,
  Berkeley Lawrence-Berkeley); a trailing `(Source: …edu)` citation (GOOD sourcing, exempted by the debris
  tell); a building named in prose ("Warren Weaver Hall, …" — the `\bHall,\s` tell false-flags it, FLAG #2);
  a shared SUBFIELD ENUMERATION / department name across credential levels when each lead is distinct (the
  abs-150 marginal over-count — GT/Duke/Yale/Chicago/Northwestern). Treat all as artifacts UNLESS a row names
  a unit / landmark / place the institution provably does NOT have.
