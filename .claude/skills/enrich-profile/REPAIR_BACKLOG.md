# Enrich-profile REPAIR BACKLOG

Ranked **worst-first**. The enricher MUST clear the top open entry before deepening any
other university (repair-first, SKILL.md §2). This is the ONLY file where specific
schools appear. Severity: **critical** (fabricated / cross-contaminated / scraped-debris /
near-duplicate / machine-broken template-slot grammar / wrong-program content shipped live) ·
**high** (residual fabricated NAMES on an otherwise-rich catalog, OR a matcher-core field
STARVED — a whole master's / professional tier null, a catalog-wide 0%, or a correct repair
stranded un-deployed) · **medium** (institution-level seed below gold, or dead feed on an
otherwise-enriched node).

Evidence is from the live API (`api.unipaith.co/api/v1`), measured this run with
`profile_standard/anti_stub.py` (the enforced CI gate's own functions): `analyze`,
`template_slot_artifacts`, `scrape_debris`, `machine_artifacts`, and
`frame_stripped_shared_body(..., abs_chars=150)` over the fully-paginated `/programs` list of every
program-bearing catalog, plus per-`degree_type` tuition COVERAGE + value distribution, plus a
campus-photo count on all 300 institutions, plus a name-realness scan (CIP-title tells: the federal
"…and Related Sciences/Services" suffix AND multi-clause field strings shared verbatim across ≥2
institutions). Gold MIT (n=65) is the description 0-control — but NOT a tuition control (it ships
null cert/PhD tiers + grad rows at its own undergrad sticker).

_Last graded: 2026-06-22 (grader **run 78**). **FULL-FLEET sweep: all 300 LIVE institutions + all 40
catalogs re-measured via the live API** (≈8,400 programs paginated; per-tier tuition coverage AND value
distribution; campus-photo count on all 300; cross-institution CIP-title NAME scan). **1 rule change** —
miss #2 now requires a CIP-title repair to clear the WHOLE class (re-scan with the tells, get ZERO),
because the backlog enumerates a SAMPLE not the exhaustive set (run-77 backlog #1 was 5 enumerated
strings; the repairs fixed exactly those and left a 6th same-class title live). **CLEARED since run 77:**
Cornell/Harvard/Penn 5 enumerated CIP-title names (#1085/#1088/#1089 — Penn deploy in-progress);
UCSD master's/prof tuition (#1083, now mast 53/60 + prof 2/2); Purdue tuition (#1082, now 100% all
tiers). **NEW worst tier = the UN-ENUMERATED CIP-title residual "Physiology, Pathology and Related
Sciences" still LIVE on Cornell + Harvard (entry #1)**, then Penn name deploy-lag (#1089 in-progress —
verify, do NOT rewrite — entry #2), then master's/professional-tier tuition STARVATION (~13 catalogs,
entry #3). Alembic history is a single linear head (recent deploys green; #1089 deploying) — no dual-head
block this run. See CHANGELOG run 78._

## Fleet at a glance (run 78, live `api.unipaith.co/api/v1`)

- **Fleet = 300 institutions LIVE.** **40 carry programs; 260 are bare institution-level stubs**
  (0 programs, dead feed, **33 with ZERO campus photo + 54 at 1–3**). Seeding is **external**; the routine
  ENRICHES + REPAIRS only.
- **🟢 STRUCTURE + DESCRIPTIONS still clean fleet-wide (verified LIVE):** every mature catalog scores 0 on
  `template_slot_artifacts` / `scrape_debris` / `machine_artifacts` and on every `analyze` description tell;
  no duplicate / bare-abbreviation / "Programs"-dept / null-dept rows on any mature catalog. Only benign
  marginal `frame_abs150` (GT 5 — engineering MS/PhD share a specialization clause; Yale/Duke/Chicago/
  Northwestern 1) and MIT's known `name_prefixed=1` — all assessed benign at run 77, unchanged this run.
- **🔴 NEW — UN-ENUMERATED CIP-TITLE NAME residual (fabrication) on otherwise-rich catalogs:** **Cornell +
  Harvard** each still ship **"Physiology, Pathology and Related Sciences"** (federal CIP 26.09 — the "…and
  Related Sciences" suffix form, identical on both = the CIP mint) verbatim as a PhD / certificate name
  (entry #1). The run-77 repairs fixed exactly the 5 backlog-enumerated strings and left this 6th same-class
  title because neither `_ROLLUP_RESOLVE` map gained a key for it (the new miss-#2 whole-class rule).
- **🟡 Penn name DEPLOY LAG (not a data defect):** Penn live still shows "Linguistic, Comparative, and
  Related Language Studies and Services" ×3, but `penn_profile._ROLLUP_RESOLVE` ALREADY maps it →
  "Linguistics" (#1089). #1089's Deploy Backend is **in-progress** (started 11:49Z) → the names will
  resolve on deploy. **Verify it lands; do NOT rewrite the already-correct map** (§9 merge-is-not-deploy).
- **🟢 CLEARED since run 77 (do not re-queue):** Cornell/Harvard/Penn 5 enumerated CIP-title names
  (#1085/#1088/#1089); **UCSD** master's/prof tuition (#1083 — now master's 53/60 + prof 2/2); **Purdue**
  tuition (#1082 — now 100% across bach/master's/prof, PhD funded-omit).
- **🟢 VERIFIED NOT-A-DEFECT (false-positive avoided — do NOT re-queue):** all the multi-clause names the
  naive scan flags are VERIFIED real majors the institution awards (run-77 carve-out): "Science, Technology,
  and Society" (MIT/Stanford/Chicago), "Speech, Language, and Hearing Sciences" (Purdue/UT-Austin/UF),
  "Russian, East European, and Eurasian Studies", "Molecular, Cellular, and Developmental Biology",
  "Theater, Dance, and Performance Studies", "Radio/Television/Film", "Latina/Latino Studies" — NOT CIP
  titles. **Boston University** professional Law tier (15 JD/LL.M. rows at the flat $69,870) = BU's verified
  university-wide flat full-time rate, NOT a copy-down. **Georgia Tech "Professional Master's in …"** (PMASE
  etc.) is GT's REAL conferred designation, NOT the IPEDS possessive mint — do not mangle it.
- **🔴 master's / professional-tier 0–low% behind a 100% bachelor's tier (matcher-blind on grad budget):**
  ~13 structurally-clean catalogs (entry #3). Master's / professional publish a per-program / per-credit rate
  and are rarely funded → unambiguous starvation.
- **🟡 PhD-tier null is LARGELY LEGITIMATE (funded research doctorates → omit-with-reason) — do NOT pressure
  fabrication:** Columbia phd 0/44, Penn 0/47, Yale 0/66, Berkeley 0/64, UCLA 0/82, Harvard, etc. The
  run-74 rule exempts funded PhDs; certificate-tier nulls are similarly often per-credit. Treat PhD/cert
  nulls as notes, NOT repair priority, UNLESS the institution publishes a non-waived flat rate (UT-Austin PhD
  86/86, JHU cert 84/84, UF cert 93/93, UW-Madison cert 129/129 prove some do).
- **Genuine per-tier fillers to PRESERVE (DISTINCT graduate values — not copy-down):** Michigan, Stanford,
  Berkeley (master's 71/74), UCLA (master's 98/146), UF, UT-Austin, JHU, UW-Madison, USC, NYU, UW-Seattle,
  CMU, UCSD (newly filled), Purdue (newly 100%). **Boston University** (general-grad + Law flat $69,870 by
  VERIFIED policy, MD/DMD distinct). Do NOT "re-uniform" or "re-distinct" these.

⚠️ **FLAG FOR HUMAN (code/workflow, out of grader scope — the grader edits only the 3 skill files):**
1. **The enforced anti-stub gate is DESCRIPTION-ONLY and never scans NAMES, so verbatim CIP-TITLE program
   names ship live undetected** (`anti_stub.py` + `test_anti_stub_gate.py`): the gate computes 0 on
   description tells while Cornell/Harvard ship the "Physiology, Pathology and Related Sciences" CIP title
   un-flagged. The durable fix is a name-realness metric (reject the federal "…and Related…Sciences/Services"
   / "…, and {parent} Engineering/Biology" suffix AND any multi-clause field string shared verbatim across ≥2
   institutions, with the run-77 verified-real-major carve-out), parametrized over `CERTIFIED_CLEAN`. App/test
   code the grader does not edit.
2. **`cip_code` is serialized as a KEY on `/programs/{id}` but its VALUE is `None` on EVERY program incl.
   gold MIT (re-confirmed run 78)**, so the matcher-side "flag empty `cip_code` via public API" channel is
   UNUSABLE. The in-repo IPEDS catalogs carry a `cip` per row — expose it on the API or audit via DB/git.
   (`tuition` IS serialized with real values — the tuition gaps are a real DATA gap.)
3. **There is NO enforced gate on tuition VALUE or COVERAGE — `anti_stub` has no tuition metric at all.** Both
   are invisible to CI (the gate is description-only). The durable fix is a `tuition_value_artifacts` metric +
   per-tier coverage in the profile test — BUT it must NOT fail `grad==undergrad` unconditionally (false-flags
   BU's verified flat rate, incl. the Law JD): key the copy-down FAIL on a professional row at the flat sticker
   ONLY when that professional SCHOOL publishes a distinct higher rate, and require a per-institution
   published-rate reference. App/test code the grader does not edit.
4. **A repair PR title / a prior backlog clear can OVERSTATE the live result** — verify the CLAIMED metric live
   PER TIER and for whole-CLASS realness before declaring done (verify-rendered-output). Run-77 cleared
   Cornell/Harvard/Penn CIP-title names as repaired, but the repairs only cleared the 5 ENUMERATED strings and
   left "Physiology, Pathology and Related Sciences" live on both (entry #1). A name repair must re-scan the
   whole catalog with the tells and get ZERO, not fix the backlog's sample (new miss-#2 rule).
5. **Auto-merge dual-head race — DORMANT this run** (alembic history is a single linear head; recent Deploy
   Backend runs are green and #1089 is deploying). The recurring cascade of failed Deploy Backend runs did NOT
   recur this interval (one Harvard #1088 deploy failed but the later #1087 deploy succeeded and the names
   landed). The durable fix (single-head assertion on the MERGE RESULT, blocking auto-merge) still belongs in
   the CI/automerge workflow; schedule one enricher firing per window + dedupe migration-bearing PRs.

---

# HIGH — UN-ENUMERATED residual CIP-TITLE NAME — clear FIRST (fabrication axis)

## 1. Cornell · Harvard — "Physiology, Pathology and Related Sciences" still LIVE — severity: high — first seen run 78 · 2026-06-22
Both catalogs are otherwise gold (real departments, field-specific de-fabbed descriptions, tuition mostly
filled), but each still ships the verbatim federal CIP taxonomy title **"Physiology, Pathology and Related
Sciences"** (CIP 26.09 — the "…and Related Sciences" suffix form, identical on both = the CIP mint, a string
no institution awards) as a `program_name`:
- **Cornell:** "Doctor of Philosophy in Physiology, Pathology and Related Sciences" (dept "Cornell University
  College of Arts and Sciences"; description already field-specific + true — only the NAME is the CIP title).
- **Harvard:** "Graduate Certificate in Physiology, Pathology and Related Sciences" (Harvard Faculty of Arts
  & Sciences).
The run-77 CIP-title repairs (#1085 Cornell, #1088 Harvard) added `_ROLLUP_RESOLVE` keys for exactly the 5
backlog-enumerated strings and shipped; neither map gained a key for this 6th same-class title, so it falls
through `_ROLLUP_RESOLVE.get(field, field)` verbatim.
**Fix (per university, one PR):** resolve "Physiology, Pathology and Related Sciences" to the institution's
real published degree name + owning department per credential level (Cornell PhD / Harvard certificate),
keeping the (already field-specific) description + tuition; THEN re-scan the WHOLE catalog with the miss-#2
CIP-title tells (federal "…and Related Sciences/Services" suffix, ", General"/", Other", bare CIP rollup,
embedded slash, `(CIP NN.NN)`, any field string shared verbatim across ≥2 institutions) and get ZERO before
shipping — do NOT stop at this one cited string (new miss #2 whole-class rule). **Do NOT touch the verified
real majors** (run-77 carve-out). Re-measure LIVE.

---

# HIGH — correct repair stranded in deploy (verify, do NOT rewrite)

## 2. Penn — CIP-title NAME fix correct in repo, stale LIVE (deploy lag) — severity: high — first seen run 78 · 2026-06-22
Penn live still shows "Bachelor of Arts / Master of Arts / Doctor of Philosophy in Linguistic, Comparative,
and Related Language Studies and Services" ×3, but `penn_profile._ROLLUP_RESOLVE` ALREADY maps it →
"Linguistics" (plus "Electrical, Electronics, and Communications Engineering" → "Electrical Engineering",
"Biomathematics…" → "Genomics and Computational Biology"), shipped in #1089. **#1089's Deploy Backend is
in-progress (started 11:49Z 2026-06-22)** — the data is correct; the deploy is the unfinished half (§9
merge-is-not-deploy). **Fix:** verify the Deploy Backend goes GREEN and Penn reads "Bachelor of Arts in
Linguistics" etc. LIVE; if the deploy failed, re-trigger it / clear any dual head. **Do NOT rewrite the
already-correct map** (re-authoring only risks a fresh dual head + a second failed deploy). After it lands,
re-scan Penn for any un-enumerated same-class CIP title (entry #1 whole-class rule) before declaring clear.

---

# HIGH — master's / professional-tier 0–low% behind a 100% bachelor's tier — matcher starvation

## 3. The graduate-tier-null catalogs — per-credential matcher STARVATION the aggregate hides — severity: high — first seen run 74 · 2026-06-21
Structurally + description clean catalogs whose bachelor's tier is 100% but whose MASTER'S and/or PROFESSIONAL
tiers ship mostly/all null (matcher scores graduate budget-fit BLIND). These tiers publish a per-program /
per-credit rate and are rarely funded → unambiguous starvation. **PhD nulls EXCLUDED here (largely funded →
legitimate omit-with-reason — "🟡" above; do not pressure fabrication).** Worst-first by null grad rows (live
run 78):
- **Harvard** (agg 39%) master's 19/107 (88 null) + cert 0/76 (likely per-credit — verify) (ba 63/63)
- **Penn** (agg 34%) master's 8/66 (58 null) + cert 0/16 + prof 0/2 (ba 55/55) — tuition gap is SEPARATE from
  the name deploy-lag (#2); fix both
- **Georgia Tech** (agg 30%) master's 2/55 (53 null) + prof 0/8 (ba 41/41)
- **Columbia** (agg 45%) master's 3/45 (42 null) + prof 2/8 (6 null) (ba 70/70)
- **Yale** (agg 48%) master's 10/38 (28 null) + prof 0/2 + cert 0/3 (ba 80/80)
- **Rice** (agg 47%) master's 1/29 (28 null) + prof 11/38 (27 null) + cert 1/2 (ba 61/61)
- **Duke** (agg 52%) master's 21/38 (17 null) + prof 2/9 (7 null) (ba 56/56)
- **Northwestern** (agg 76%) master's 0/26 + prof 0/4 (ba 71/71)
- **Notre Dame** (agg 78%) master's 0/24 + prof 0/1 (ba 60/60)
- **Berkeley** (agg 90%) prof 0/20 (master's 71/74 good) (ba 75/75)
- **UCLA** (agg 85%) prof 0/4 + master's 98/146 (48 null) (ba 141/141)
- **Dartmouth** (agg 72%) master's 0/6 + prof 0/1; **Emory** (agg 70%) master's 0/5 + prof 0/2
**Fix (per university, one PR):** group coverage by `degree_type`; stamp the published per-program / per-credit
rate for the null MASTER'S / PROFESSIONAL tier (these publish a rate, rarely funded). For a PhD or per-credit
certificate, record `tuition` in each program's `_standard.omitted` with a reason — never a silent blanket
null, and never the undergrad sticker copied onto a professional school that bills its own higher rate (the
run-76 copy-down tell; BUT a professional school that genuinely bills the university flat rate, e.g. BU Law, is
correct — verify the school's published rate). Re-measure LIVE per tier.

---

# MEDIUM — flagship seeds · institution-level seeds (seeding is external)

## 4. The flagship seeds (5 programs each) — EMPTY descriptions + null department + 0% tuition + DEAD FEED — severity: medium — first seen run 57 · 2026-06-18
**Brown · Georgetown · UC-Davis · UC-Irvine · UNC-Chapel Hill · UVA · Vanderbilt · Washington U-St Louis** each
ship 5 flagship rows with **null department**, **0% tuition**, and a **DEAD FEED** (posts=0). Some still ship
**< 4 campus photos** (re-measure per institution). **Enrich (per university, one PR):** a full real-named
catalog + per-credential researched descriptions + real departments + published tuition (per credential level
— the undergrad sticker uniform across majors, the published graduate/professional rate per tier) + a working
feed + a ≥4-photo verified gallery, then deepen toward the full real catalog.

## 5. The ~260 bulk institution-level seeds (0 programs) — severity: medium — first seen run 59/60
Each entered at institution level with **0 programs, a dead feed**, and **33 with ZERO campus photos** (broken
explore-card gradient header + detail hero — the acute sub-set to clear first): Air Force Institute of
Technology · Arizona State (Campus Immersion) · Arizona State (Digital Immersion) · Azusa Pacific · Colorado
State-Fort Collins · James Madison · Keiser-Ft Lauderdale · Loyola Marymount · Loyola-Chicago · Miami U-Oxford
· Michigan Tech · Montclair State · Northcentral · Oakland · Oregon State · SUNY-ESF · Sacred Heart · Stephen F
Austin State · Texas A&M-Commerce · Texas A&M-Corpus Christi · Thomas Jefferson · Universidad Ana G.
Mendez-Gurabo · U Alabama-Birmingham · U Dayton · U Houston · U Kentucky · U Louisville · UMBC · U Missouri-St
Louis · U Nebraska-Lincoln · U Oklahoma-Norman · U Utah · Virginia Commonwealth — **plus 54 more at 1–3
photos**. **Enrich (per university, one PR):** a full real-named catalog + per-credential field-specific
descriptions + real departments + published tuition · a working feed · a ≥4-photo verified gallery · reviews on
coverable programs · `_standard`. Pick a 0-photo seed once the HIGH tier clears.

---

# CLEAN (structure + descriptions + tuition; no action) — verified LIVE run 78
- **Gold (description 0-control):** MIT (n=65, 0 on every description metric; carries its real "Science,
  Technology, and Society" major; tuition 85% — cert/PhD tiers null + grad rows at its own undergrad sticker,
  MIT is NOT a tuition reference).
- **Tuition-COMPLETE (every published tier filled; PhD/cert omit-with-reason where funded/per-credit):**
  Princeton (43, 100%) · Caltech (43, 100%) · JHU (244, 100% incl. cert 84/84) · UF (314, 100% incl. cert
  93/93) · UW-Madison (348, 100% incl. cert 129/129) · UIUC (419, 100%) · Purdue (172, 100% — cleared #1082)
  · CMU (180, 99%) · Michigan (379, 99%) · USC (511, 97%) · Cornell (237, 97% — but see NAME entry #1) ·
  UW-Seattle (360, 96%) · UCSD (137, 95% — cleared #1083) · UT-Austin (338, 95% — PhD 86/86 distinct).
- **Structure + description clean, tuition mostly filled but some grad-tier gap (entry #3) or PhD funded-omit
  (🟡):** Berkeley (233, 90%) · UCLA (373, 85%) · Notre Dame (113, 78%) · Northwestern (125, 76%) · NYU
  (502, 73%) · Dartmouth (43, 72%) · Emory (46, 70%) · Stanford (178, 69%) · BU (402, 72% agg — verified
  flat-rate incl. Law; MD/DMD distinct) · Chicago (91, 58%) · Duke (154, 52%) · Yale (189, 48%) · Columbia
  (167, 45%) · Harvard (271, 39% — ALSO carries the CIP-title NAME residual, entry #1) · Penn (186, 34% —
  ALSO the name deploy-lag, entry #2) · Rice (159, 47%). **"structure clean" ≠ "tuition done" — many carry a
  master's/professional gap (entry #3).**
- **Heuristic over-counts to IGNORE (not defects):** benign marginal `frame_abs150` (GT 5 — engineering
  MS/PhD share a specialization clause; Yale/Duke/Chicago/Northwestern 1); MIT's `name_prefixed=1`; a verified
  flat full-time rate EQUAL to undergrad on the general AND a genuinely-flat-rate professional school (BU
  $69,870 incl. Law JD); GT's real "Professional Master's in …" (PMASE) conferred designation; real
  multi-clause MAJOR names (MIT "Science, Technology, and Society"; "Molecular, Cellular, and Developmental
  Biology"; "Speech, Language, and Hearing Sciences"; "Russian, East European, and Eurasian Studies";
  "Theater, Dance, and Performance Studies"; "Radio/Television/Film"; "Latina/Latino Studies") — these are
  real, NOT CIP rollups (miss #2 carve-out).
