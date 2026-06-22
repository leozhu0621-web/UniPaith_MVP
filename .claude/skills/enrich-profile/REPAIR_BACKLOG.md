# Enrich-profile REPAIR BACKLOG

Ranked **worst-first**. The enricher MUST clear the top open entry before deepening any
other university (repair-first, SKILL.md §2). This is the ONLY file where specific
schools appear. Severity: **critical** (fabricated / cross-contaminated / scraped-debris /
near-duplicate / **machine-broken template-slot grammar** / wrong-program content shipped live) ·
**high** (real data but materially broken structure OR a matcher-core field carrying a WRONG
value the coverage metric hides — the undergrad sticker copied onto graduate rows / a whole credential
TIER null / a correct repair stranded un-deployed) · **medium** (institution-level seed below gold, or
dead feed on an otherwise-enriched node).

Evidence is from the live API (`api.unipaith.co/api/v1`), measured this run with
`profile_standard/anti_stub.py` (the enforced CI gate's own functions): `analyze`,
`template_slot_artifacts`, `scrape_debris`, `machine_artifacts`, and
`frame_stripped_shared_body(..., abs_chars=150)` over the fully-paginated `/programs` list of every
program-bearing catalog, plus per-`degree_type` tuition COVERAGE **and per-`degree_type` tuition VALUE
distribution (the new axis: distinct-value count + undergrad-sticker copy-down)**. Gold MIT (n=65) is
the description 0-control — but NOT a tuition control (it ships null cert/PhD tiers + 9 grad rows at the
undergrad sticker).

_Last graded: 2026-06-22 (grader **run 75**). **FULL-FLEET sweep: all 300 LIVE institutions + all 40
catalogs re-measured via the live API** (≈8,400 programs paginated; per-tier tuition coverage AND value
distribution; campus-photo count on all 300). **1 rule change** — the matcher-core tuition rule measured
COVERAGE only (non-null per tier); it now ALSO measures VALUE correctness, because a tier "filled" with one
uniform number — usually the UNDERGRADUATE sticker copied onto the graduate / professional rows — reads
"covered" while the matcher scores the same budget number for a funded PhD, an academic master's, and a
professional Law/MBA/MD. **HEADLINE — STRUCTURE is CLEAN fleet-wide and stays clean:** `template_slot` /
`scrape_debris` / `machine_artifacts` = 0 on all 40 catalogs; 0 duplicate / bare-abbrev / "Programs"-dept /
null-dept / CIP-rollup rows on any mature catalog; only benign marginal `frame_abs` (GT 5, Yale/Duke/
Chicago/Northwestern 1 — distinct per-credential leads repeating a factual subfield enumeration) and MIT's
known `name_prefixed=1`. The run-71→74 template-slot/debris saga is fully resolved + deployed. **The NEW
worst tier is TUITION VALUE-CORRECTNESS** (BU 182 + Cornell 152 grad rows carry the undergrad sticker — both
read "88%/92% covered"), then graduate-tier NULLs (~20 catalogs), then catalog-wide 0% (USC/NYU/UW-Seattle +
UIUC deploy-strand). See CHANGELOG run 75._

## Fleet at a glance (run 75, live `api.unipaith.co/api/v1`)

- **Fleet = 300 institutions LIVE.** **40 carry programs; 260 are bare institution-level stubs**
  (0 programs, dead feed, **33 with ZERO campus photo**). Seeding is **external**; the routine
  ENRICHES + REPAIRS only.
- **🟢 STRUCTURE clean fleet-wide (verified LIVE):** every mature catalog scores 0 on
  `template_slot_artifacts` / `scrape_debris` / `machine_artifacts` and on every `analyze` description
  tell; no duplicate / bare-abbreviation / "Programs"-dept / null-dept / CIP-rollup name or department on
  any mature catalog. The run-74 HIGH tier landed + deployed (BU #1054/#1058, UW-Madison #1057, UIUC #1061).
- **🔴 NEW worst tier — undergrad-sticker COPY-DOWN (reads "covered", ships a WRONG value):**
  **Boston University** stamps its $69,870 undergrad sticker on **182** graduate programs (reads 88%);
  **Cornell** stamps the identical $71,266 on **152 of 153** grad + professional rows — every PhD, every
  professional degree (reads 92%, was in run-74 CLEAN). Both feed the matcher the UNDERGRADUATE number on
  their whole graduate tier. Low-density copy-down on gold MIT (9), Princeton (5/6), Caltech (2/2),
  Harvard (2) — notes, not repair priority.
- **🔴 graduate-TIER tuition NULL behind a 100% bachelor's tier (matcher-blind on grad budget):** ~20
  structurally-clean catalogs (entry #3). Master's / certificate / professional publish a rate and are
  rarely funded → unambiguous starvation; a blanket PhD-tier null beside a peer that fills it (UT-Austin
  PhD 86/86, Cornell PhD 74/74 — though Cornell's are the copy-down) is not the "rare funded-waiver."
- **🔴 catalog-wide 0% tuition (all tiers null):** **USC 511 · NYU 507 · UW-Seattle 360**, plus **UIUC 419
  — a DEPLOY-STRAND** (the repo data IS filled — #1061 — but live reads 0%; the auto-merge dual-head race
  recurred, bunames1+uiuctuition1 → fixup **#1062** was deploying at grade time — confirm it landed).
- **Genuine per-tier fillers to PRESERVE (not copy-down — DISTINCT graduate values):** Michigan (master's
  16 distinct), Stanford (67), Berkeley (71), UCLA (98), UF + UT-Austin (distinct flat graduate rate ≠
  undergrad). Do NOT "re-uniform" these.

⚠️ **FLAG FOR HUMAN (code/workflow, out of grader scope — the grader edits only the 3 skill files):**
1. **The enforced anti-stub gate's `@parametrize` lists DRIFT from `CERTIFIED_CLEAN`** (`anti_stub.py` +
   `test_anti_stub_gate.py`): a catalog can be `CERTIFIED_CLEAN` yet ship a metric live because that metric's
   list excludes it. The durable, drift-proof fix is one change: **parametrize the template-slot / abs-floor /
   debris / artifact tests over `CERTIFIED_CLEAN` ITSELF**, and add `OR lcs >= 150` to
   `frame_stripped_shared_body`'s DEFAULT so the dilution evasion cannot read a false 0 fleet-wide. (No live
   structure breach this run — but the drift is still latent.)
2. **`cip_code` is NOT serialized on `/programs/{id}` or the list endpoint** — absent on EVERY program incl.
   gold MIT (re-confirmed this run), so the matcher-side "flag empty `cip_code` via public API" channel is
   UNUSABLE. The in-repo `PROGRAMS` carry a `cip` key, so it is a serializer gap — expose it or audit via
   DB/git. (`tuition` IS serialized — the tuition gaps are a real DATA gap.)
3. **There is NO enforced gate on tuition VALUE — `anti_stub` has no tuition metric at all.** Coverage and
   the new copy-down defect are both invisible to CI (the gate is description-only). The durable fix is a
   `tuition_value_artifacts` metric in `anti_stub.py` (FAIL a graduate/professional row whose `tuition` ==
   the institution's undergrad sticker; warn on a single distinct value across a whole grad tier) +
   per-tier coverage in the profile test, baselined to a real per-tier reference — app/test code the grader
   does not edit. Flagged so the copy-down cannot recur silently.
4. **A repair PR title can OVERSTATE the live result** — BU/UIUC "full-tier tuition" PRs read 88% / 0% live
   (BU copy-down; UIUC deploy-strand). Verify the CLAIMED metric live PER TIER **and** for value-realness
   before declaring done (verify-rendered-output).
5. **The auto-merge dual-head race RECURRED** — bunames1 (BU) + uiuctuition1 (UIUC) branched off the same
   base, both auto-merged, dual head, Deploy Backend FAILED (23:38Z), fixup **#1062** deploying at grade
   time. This is the §8-step-5 class the rule already documents; the durable fix (single-head assertion on
   the MERGE RESULT, blocking auto-merge) lives in the CI/automerge workflow. Schedule one enricher firing
   per window + dedupe migration-bearing PRs before merge.

---

# HIGH — undergrad-sticker COPY-DOWN (reads "covered", ships a WRONG matcher value) — clear FIRST

## 1. Boston University — $69,870 undergrad sticker copied onto 182 graduate programs — severity: high — first seen run 75 · 2026-06-22
394 programs, reads **88% tuition "covered"** — but **182 of 240 graduate-filled rows carry $69,870, the
undergraduate sticker** (master's 132/160, PhD 15/30, plus certificate/professional), so the matcher scores
the same budget for a funded PhD and a professional master's. PLUS PhD tier only 30/76 filled (the rest
null). **Fix:** stamp BU's published per-credential / per-credit graduate rates (Questrom MBA, MET / GRS /
SPH per-program rates) — never the $69,870 undergrad number on a graduate row — or omit-with-reason for a
genuinely-funded research PhD. Re-measure LIVE per tier AND for distinct values (copy-down count → 0).

## 2. Cornell University — identical $71,266 on 152/153 grad + professional rows — severity: high — first seen run 75 · 2026-06-22
237 programs, reads **92% "covered"** (was in run-74 CLEAN) — but **every** master's (75/76), **every** PhD
(74/74), and **every** professional row (3/3) carries the IDENTICAL $71,266 = the undergraduate endowed
sticker copied wholesale down the tree. Cornell research PhDs are commonly funded, contract-college (CALS /
ILR / Human Ecology) tuition differs from endowed, and the professional schools (Law / Johnson MBA / Vet)
cost far more — none is $71,266. **Fix:** stamp the real published rate per program type (endowed vs
contract/in-state, each professional program's own rate, the per-credit research rate) or omit-with-reason
for funded research degrees; copy-down count → 0 live.

---

# HIGH — graduate-TIER tuition NULL behind a 100% bachelor's tier

## 3. The graduate-tier-null catalogs — per-credential matcher STARVATION the aggregate hides — severity: high — first seen run 74 · 2026-06-21
Structurally clean catalogs whose bachelor's tier is 100% but whose graduate tiers ship 0% (matcher scores
graduate budget-fit BLIND). Worst-first by grad rows null:
- **JHU** agg 25% — cert 0/84, master's 0/95, PhD 0/4, prof 0/1 (ENTIRE grad catalog null, ~184 rows)
- **CMU** agg 22% — master's 1/99, PhD 0/41, cert 0/1 (~140 grad nulls)
- **UCLA** agg 64% — PhD 0/82, prof 0/4 (master's 98/146 distinct — good); **Berkeley** agg 63% — PhD 0/64,
  prof 0/20 (master's 71/74 good)
- **Harvard** agg 30% — cert 0/80, PhD 0/25, master's 19/110; **Penn** agg 34% — cert 0/16, PhD 0/47,
  master's 8/66; **Stanford** agg 66% — cert 0/53, PhD 0/6 (master's 67/67 good)
- **Yale** agg 47% — PhD 0/66, master's 9/38; **Columbia** agg 45% — PhD 0/44, master's 3/45; **Rice**
  agg 47% — PhD 0/29, master's 1/29, prof 11/38; **Duke** agg 52% — PhD 1/51, master's 21/38
- **Purdue** master's 0/68 + PhD 0/5; **UCSD** master's 0/60 + PhD 0/3; **Northwestern** grad 0/54;
  **Notre Dame** grad 0/53; **GT** master's 2/55 + PhD 0/39; **Chicago** master's 3/41; **Emory** grad 0/14;
  **Dartmouth** grad 0/12; **Caltech** PhD 0/16; **Wisconsin** PhD 0/8; **UF** PhD 0/26; **Michigan** PhD 1/148
**Fix (per university):** group coverage by `degree_type`; stamp the published per-program / per-credit rate
for the null master's / certificate / professional tier (these publish a rate, rarely funded — unambiguous
starvation). For the PhD tier, stamp the published sticker (matcher budget input — funding is a separate
signal) or record `tuition` in each genuinely-funded program's `_standard.omitted` with a reason — never a
silent blanket tier null, and never the undergrad sticker copied down (entry #1/#2). Re-measure LIVE per tier.

---

# HIGH — catalog-wide 0% tuition (all tiers null) + a DEPLOY-STRAND

## 4. The zero-tuition catalogs — matcher STARVATION — severity: high — first seen run 70 · 2026-06-21
**USC 511 · NYU 507 · UW-Seattle 360** ship 0% `tuition` on every tier so the CPEF matcher scores budget-fit
blind on every program. **UIUC 419 is a DEPLOY-STRAND** — the repo data IS filled (#1061, 68 published-rate
refs) but the live API reads 0% because the auto-merge dual-head race (bunames1+uiuctuition1) failed the
deploy; fixup **#1062** was deploying at grade time — **confirm it landed live; if so UIUC clears, if not
re-trigger Deploy Backend (do NOT rewrite the already-correct data, §9)**. Tuition is institution-PUBLISHED,
so a whole-catalog null is a SKIPPED knowable field. Peers prove it knowable: Princeton 100% · UW-Madison
98% · UT-Austin 95% · UF 92%.

---

# MEDIUM — flagship seeds · institution-level seeds (seeding is external)

## 5. The flagship seeds (5 programs each) — EMPTY descriptions + null department + 0% tuition + DEAD FEED — severity: medium — first seen run 57 · 2026-06-18
**Brown · Georgetown · UC-Davis · UC-Irvine · UNC-Chapel Hill · UVA · Vanderbilt · Washington U-St Louis** each
ship 5 flagship rows with **EMPTY `description_text`**, **null department**, **0% tuition**, and a **DEAD FEED**
(posts=0). **UC-Davis / UNC / Vanderbilt / Washington U-St Louis ship only 3 campus photos (<4)** (Brown /
Georgetown / UC-Irvine 4, UVA 5). **Enrich (per university, one PR):** a full real-named catalog +
per-credential researched descriptions + real departments + published tuition (per credential level, NOT the
undergrad sticker copied down) + a working feed + a ≥4-photo verified gallery, then deepen toward the full
real catalog.

## 6. The ~260 bulk institution-level seeds (0 programs) — severity: medium — first seen run 59/60
Each entered at institution level with **0 programs, a dead feed**, and **33 with ZERO campus photos** (broken
explore-card gradient header + detail hero — the acute sub-set to clear first; e.g. Air Force Institute of
Technology, Arizona State (Campus & Digital Immersion), Azusa Pacific, Colorado State-Fort Collins, James
Madison, Keiser-Ft Lauderdale, Loyola Marymount, Loyola-Chicago, Miami U-Oxford, Michigan Tech, Montclair
State, Oakland, Oregon State, SUNY-ESF, Sacred Heart) plus **~50 more at 2–3 photos** (Clark Atlanta 2,
Ferris State 2, Fordham 2, Georgia State 2, Auburn 3, Florida State 3, LSU 3, …). **Enrich (per university,
one PR):** a full real-named catalog + per-credential field-specific descriptions + real departments +
published tuition · a working feed · a ≥4-photo verified gallery · reviews on coverable programs ·
`_standard`. Pick a 0-photo seed once the HIGH tier clears.

---

# CLEAN (structure + descriptions; no action) — verified LIVE run 75
- **Gold (description 0-control):** MIT (n=65, 0 on every description metric; tuition 69% but cert/PhD tiers
  null + 9 grad rows at the undergrad sticker — MIT is NOT a tuition reference).
- **Structure + description clean fleet-wide** (0 template_slot / debris / machine / classification /
  verbatim-shared / CIP-rollup; benign marginal `frame_abs` ≤5 only): UT-Austin (338, tuition 95% distinct) ·
  Michigan (379, master's distinct — **PhD 1/148, entry #3**) · UW-Madison (348, 98% — **PhD 0/8, entry #3**) ·
  UF (314, 92% — **PhD 0/26, entry #3**) · Stanford (178 — **cert/PhD null, entry #3**) · UCLA (373 — **PhD
  null, entry #3**) · Berkeley (233 — **PhD/prof null, entry #3**) · Duke (154) · Yale (189) · Chicago (91) ·
  Northwestern (125) · Rice (159) · Purdue (172) · UCSD (137) · Caltech (43) · Princeton (43, 100%) · Harvard
  (279) · Columbia (167) · CMU (180) · Dartmouth (43) · Emory (46) · Notre Dame (113) · GT (143). **Many of
  these carry a graduate-tier tuition gap (entry #3) — "structure clean" ≠ "tuition done".**
- **NOT tuition-clean despite being structure-clean:** Cornell (copy-down #2) · BU (copy-down #1) · USC / NYU /
  UW-Seattle / UIUC (0% #4) · all of entry #3.
- **Heuristic over-counts to IGNORE (not defects):** the benign marginal `frame_abs` (GT 5, Yale/Duke/Chicago/
  Northwestern 1 — distinct per-credential leads repeating a factual subfield enumeration); MIT's
  `name_prefixed=1` (a real-described row); a genuine published flat academic-graduate rate DISTINCT from the
  undergrad sticker (UT-Austin $12,006, UF $12,740 — NOT copy-down). Treat as artifacts UNLESS a grad/prof row
  equals the undergrad sticker or a tier is null.
