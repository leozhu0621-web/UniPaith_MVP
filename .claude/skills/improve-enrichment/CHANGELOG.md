# Enrichment Grader — CHANGELOG

Audit log of the `improve-enrichment` routine: each run grades the live enrichment
output, tightens the `enrich-profile` rulebook against recurring problem CLASSES,
and re-ranks the repair backlog. One squash PR per run.

---

## 2026-06-15 — Run 3 (the duplicate-name "repair" was cosmetic — CIP fabrication survives; new concentration-split class; backlog re-ranked)

**Institutions audited:** all 28 in the live DB (`/institutions/search`, full
program pagination per institution). Recently-changed focus on the ~33 PRs merged
since run 2 (#542–#574: Princeton/Duke/Chicago/Caltech/MIT dup-name repairs, 6
campus galleries, 6 reviews-depth passes). Student's-eye pass: Cornell, Berkeley,
Rice (recently changed) + Harvard, Boston U (random/deep-dive).

**Findings (live API evidence):**

1. **The duplicate-name CRITICAL tier is genuinely CLEARED** — 0 duplicate
   `program_name`s fleet-wide (was Princeton 38, Caltech 23, UChicago 27, Yale 36,
   Duke 19 in run 2). Reviews-depth passes are landing (Yale/Rice 11/25, Cornell/CMU
   9/25, up from ~0). Real progress.
2. **NEW PROBLEM CLASS — credential-prefixed CIP-rollup NAME fabrication (the
   dominant fleet defect).** The dup-name "repair" was COSMETIC: it prepended a
   generic credential ("Bachelor's in …"/"Master's in …"/"Doctorate in …") to the
   verbatim federal CIP/IPEDS taxonomy rollup and copied that rollup into
   `department` — so ~3 near-identical rows per field (cert/bachelor's/master's)
   survive with distinct names + a non-null department, evading every prior check
   (bare-abbr, duplicate-name, null/"Programs"/credential-dept). Confirmed at DATA
   level: Harvard `"Bachelor's in Biology, General"`, dept `"Biology, General"`,
   description `"…is an undergraduate program at Harvard's Harvard Faculty of Arts &
   Sciences, offered through the Biology, General."` (broken template), and a
   `"Bachelor's in Intelligence, Command Control and Information Operations"` Harvard
   does not offer. Density by CIP-rollup name share: Northwestern 46%, UCSD/JHU 44%,
   Purdue 43%, Berkeley 41%, **Harvard 40% (run 2 wrongly called it gold)**, Columbia
   40%, Chicago 40%, Stanford 38%, Wisconsin 36%, Cornell 36%, Penn 32%, Princeton
   30%, Caltech 23% — 14 catalogs at 23–46%. The tell survives in the NAME even where
   the department was cleaned (Chicago names 46 / depts 4; Caltech 21/6). Root cause:
   the rename repair de-collided names without de-fabricating.
3. **NEW PROBLEM CLASS — concentration/track-splitting padding (Boston U).** 201 of
   483 BU rows split one degree into per-concentration rows ("Bachelor's in
   Anthropology — Biological Anthropology / — Sociocultural Anthropology / — Religion
   / — Anthropology Health Medicine" = 4 rows for one BA). Distinct names + real
   department = evades every check, yet inflates the count with non-degrees.
   Concentrations belong in the `tracks` field. BU also still carries credential
   departments ("Mph" ×14), title-cased dept tokens ("School Of Music", "Mathematics
   Statistics"), `program_name`↔`degree_type` mismatches ("…— Edm…" on a `bachelors`
   row), and a dead feed (`posts=0` despite merges through 2026-06-15).
4. **CIP-taxonomy DEPARTMENT defect (run-2 HIGH tier) persists** on the unrepaired
   catalogs (Purdue/Berkeley/Cornell/Stanford/Wisconsin still echo the CIP rollup as
   department). Already covered by miss #2 dept bullet → backlog, no new rule.
5. **8 shallow originals unchanged** (22 programs, 0 campus_photos, null dept,
   CIP-title names): NYU (posts=0), GaTech, UT Austin, UCLA, UIUC, Michigan, USC,
   UW-Seattle. Covered → MEDIUM backlog.

**False alarms caught (diagnosed, not acted on):** (a) a comma-in-department
heuristic flagged Harvard 72 / Purdue 88 — but Harvard's *flagship* depts
("Harvard Business School" ×28) are real; only the long tail is CIP rollup, so I
ranked by the sharper rollup-NAME tell, not raw comma count. (b) em-dash-in-name
fired on CMU (16) and Rice (6) — those are legit degree formatting, not splits; only
BU's 201 is real concentration padding. (c) Looking at top-departments-by-frequency
(run 2's method) hid the defect — the fabrication lives in the long tail, so this run
scanned the WHOLE catalog.

**Rulebook changes (3 of ≤3; all ADD/TIGHTEN no-fabrication, none loosen an
invariant):**
- **miss #2 (new sub-bullet):** a generic credential PREFIX does not turn a CIP
  rollup title into a real program name — banned the "{credential} in {CIP rollup}"
  variant (tells: ", General"/", Other", federal comma-and lists, embedded slashes;
  rollup echoed as department; "offered through the {rollup}" template description).
  A real name uses the institution's actual degree designation + field. Evidence:
  live API this run, 14 catalogs 23–46% rollup names.
- **miss #2 (new sub-bullet):** ban minting one program row per
  concentration/track/specialization of a single degree; concentrations go in
  `tracks`; never let `program_name` and `degree_type` disagree. Evidence: live API,
  one 483-row catalog ~200 "— {concentration}" split rows.
- **miss #9 (programmatic catalog check extended):** the pre-ship FAIL check now also
  trips on "{generic credential} in {CIP rollup}" names (even when department is
  non-null) and a high rate of "— {concentration}" base-degree splits. Evidence:
  same.

**FLAGGED FOR HUMAN REVIEW (carried from run 2, still unreconciled):** miss #9 says
"FAIL on null/blank `department`", but gold-reference MIT ships null department on
all programs and `manifest.py` marks `department` `required=False`. These contradict;
reconciling would LOOSEN the verify-output invariant, so left intact per the rails.

**Backlog delta:** fully re-ranked. CRITICAL = **Boston University** (multi-defect:
concentration-split padding + credential departments + degree-type mismatches + dead
feed) — now the single worst catalog and the top repair entry. HIGH tier replaced
with the 14 CIP-rollup-name catalogs, density-ranked (Northwestern #1 at 46%; Harvard
moved OUT of "clean" into HIGH at 40%). MEDIUM = 8 shallow originals (unchanged).
SECONDARY = reviews depth (lowest: Harvard 1/25, Stanford 2/25). CLEAN = CMU, Duke,
Rice, Yale, MIT (≤9% rollup; Yale+Duke graduated from the old dup-name tier).

**Health check:** the profile pytest could not run in this ephemeral container (no
backend venv; no pytest module; no Postgres) — same constraint as runs 1–2. Changes
are markdown-only (no Python, no migrations, no app code), and the `profile_standard`
manifest imports cleanly (STANDARD_VERSION 2), so the enricher code/data state is
unaffected.

**Invariants:** all intact; all 3 edits tighten no-fabrication, none weaken. The one
finding that could argue for loosening (null-department FAIL vs gold MIT) remains
logged for human review, not acted on.

---

## 2026-06-14 — Run 2 (department-realness gap; re-ranked backlog)

**Institutions audited:** all 28 in the live DB (`/institutions/search`, full
program pagination per institution). Recently-changed focus on the 12 catalogs
merged since run 1 (#528–#539: UCSD, Purdue, JHU, Northwestern, BU, Harvard,
UW-Madison, Cornell, Berkeley, Columbia, Penn, Stanford). Student's-eye pass:
Stanford, Penn, Columbia (recently changed) + Rice, Boston U (random).

**Findings (live API evidence):**

1. **NEW PROBLEM CLASS — CIP-taxonomy / credential `department` (fleet-wide on
   repaired catalogs).** The 12 merged repairs fixed the duplicate-NAME padding (0
   duplicate names now) but "fixed" the null-department gap by stuffing the
   **verbatim federal CIP taxonomy title** into `department` — verbose strings the
   institution never uses ("Communication Disorders Sciences and Services", "Radio,
   Television, and Digital Communication", "Area Studies", "Air Transportation") —
   so 87–100% of rows are each their own one-off "department" (a non-functional
   grouping). Boston U is worse: a bare **credential** "Mph" (×14) and
   mechanically title-cased tokens ("School Of Music", "Mathematics Statistics").
   Confirmed at DATA level (`/programs` list returns the stored `department`) — bad
   data, NOT a render bug. Positive model: Harvard groups under real schools
   ("Harvard Business School" ×28). This variant EVADES every existing check (it is
   non-null, not "Programs", names are distinct, descriptions are real). Root
   cause: the run-1 "never-null department" repair guidance was executed as "copy
   the CIP field title in."
2. **Duplicate-name CIP padding persists on 5 never-repaired catalogs** — Princeton
   (38 dup names / 50% density), Caltech (27%), UChicago (23%), Yale (19%), Duke
   (12%). Already covered by miss #2 → backlog (queue), not a new rule.
3. **Reviews depth still thin** on repaired catalogs (Columbia 0/12, Wisconsin
   0/12, Rice 0/12, BU 0/12 sampled) — covered by miss #8 → backlog (depth pass).
4. **Dead feeds:** Boston U (posts=0; merged #532, has had ingest cycles → real
   dead feed), NYU (never enriched), Stanford (posts=0 but merged #539 latest —
   may be ingest timing; flagged to recheck). Covered by miss #1/#9 → backlog.
5. **8 shallow originals** unchanged (22 programs, 0 campus_photos): NYU, GaTech, UT
   Austin, UCLA, UIUC, Michigan, USC, UW-Seattle.

**False alarms caught (diagnosed, not acted on):** (a) my first pass read
`/institutions/{id}/posts` as `{items:[]}` but it returns a bare LIST → "posts=0
fleet-wide" was a script bug; feeds are alive (MIT, Purdue have posts). (b) Null
`department` is NOT itself a defect — the gold reference MIT ships null department
on all 65 programs and `department` is `required=False` in `manifest.py`. So the
real tell is duplicate names + CIP-taxonomy/credential departments, not null.

**FLAGGED FOR HUMAN REVIEW (not acted on — would loosen an invariant):** miss #9
says "FAIL on null/blank `department`", but the gold reference MIT has null
department on all programs and the manifest marks `department` `required=False`.
These contradict. Correcting it would LOOSEN the verify-rendered-output invariant,
so per the safety rails I did NOT edit it — a human should reconcile whether null
department should fail at all, or whether MIT is a known-gap exception.

**Rulebook changes (2 of ≤3; both ADD/TIGHTEN no-fabrication, neither loosens an
invariant — the null-department FAIL was left intact):**
- **miss #2 (new sub-bullet):** `department` must be the institution's REAL
  published owning unit, NEVER the verbatim CIP taxonomy title, a degree/credential
  abbreviation ("MPH"/"Mph"), or a mechanically title-cased token; a clean
  field-named dept ("Economics") is fine — the defect is the CIP-taxonomy phrase /
  credential placeholder. Cited Harvard as the gold model, Purdue/Columbia/BU as the
  defect. Evidence: live API, 87–100% CIP-title departments fleet-wide.
- **miss #9 (program spot-check extended):** the programmatic catalog check now also
  FAILS on a `department` that is a verbatim CIP taxonomy phrase or a degree
  abbreviation (added alongside the existing null/"Programs"/duplicate/template
  checks). Evidence: same.

**Backlog delta:** re-ranked worst-first. CRITICAL tier replaced with the 5
unrepaired duplicate-name catalogs (Princeton now #1 at 50% density; run-1's
critical entries were cleared by #528–#539). NEW HIGH tier = 12 CIP-taxonomy/
credential-department catalogs (Boston U leads: credential dept + dead feed).
MEDIUM = 8 shallow originals (unchanged). Added SECONDARY reviews-depth note.

**Health check:** full pytest (`test_profile_standard` + `test_profile_enrichment`)
could not run in this ephemeral container (no backend venv; `cryptography` rust
binding panics; no Postgres). Changes are markdown-only (no Python, no migrations),
and the `profile_standard` manifest + conformance modules import cleanly
(STANDARD_VERSION 2), so the enricher code/data state is unaffected.

**Invariants:** all intact; both edits tighten, none weaken. The one finding that
argued for loosening (null-department FAIL vs gold) was logged for human review,
not acted on.

---

## 2026-06-14 — Run 1 (first run; bootstrapped CHANGELOG + REPAIR_BACKLOG)

**Institutions audited:** all 28 in the live DB (`/institutions/search`), full
program pagination per institution; recently-changed focus on UC San Diego (#524),
Purdue (#523), Northwestern (#522), Johns Hopkins (#521), Boston University (#520).

**Findings (live API evidence):**

1. **NEW PROBLEM CLASS — CIP × award-level catalog padding (fleet-wide).** 13
   universities have catalogs that are 63–97% fabricated stubs: `program_name` is
   the bare CIP field title (so certificate/bachelor's/master's in one field share
   an IDENTICAL name), `department` is **null**, and the description is a degree-type
   template `"{field} — a {Univ} {degree_type} program offered through {school}"`.
   Confirmed at the DATA level via `/programs/{id}` (department genuinely null,
   template description stored) — bad data, NOT a render bug. Worst: UC San Diego
   97%, Purdue 95%, JHU 94%, Northwestern 94% — i.e. the FOUR most-recently-merged
   universities are the most padded, so the routine is actively regressing. This
   variant evades the existing bare-abbreviation ban (the name is "Anthropology",
   not "BA"). Root cause: the "full IPEDS/Scorecard catalog" breadth mandate is
   being executed as "one row per CIP × award-level."
2. **Boston University still broken** (483 programs; 323 "BA"/"MS"/"PhD" stubs, 478
   `department=="Programs"`, posts=0) despite PR #520 claiming gold — a
   verify-rendered-output failure (miss #9).
3. **Null-department partial padding** — Yale (189) and Duke (154) carry null
   `department` on every program (names look real; grouping broken).
4. **9 never-enriched shallow originals** (22 programs, 0 `campus_photos`, null
   dept): NYU (posts=0), Georgia Tech, UT Austin, UCLA, UIUC, Michigan, USC, UW,
   Wisconsin.
5. **Dead feeds (posts=0):** Stanford, NYU, Boston U.
6. Reviews coverage on the padded catalogs is ~0–1/20 sampled — secondary to the
   catalog fabrication (don't write reviews for stub rows).

**Diagnosis:** #1–#3 are BAD DATA → repair backlog. #1 is also a RULEBOOK GAP — the
anti-pad clause existed but framed the violation only as bare abbreviations, and the
breadth clause actively pushed toward CIP-row minting. → 2 rulebook edits.

**Rulebook changes (2 of ≤3; both TIGHTEN no-fabrication, none loosen):**
- **miss #2 (new sub-bullet):** IPEDS/Scorecard CIP count is an UPPER-BOUND
  completeness HINT, never a per-(CIP × award-level) row-minting recipe; named the
  CIP-title padding variant (identical names across award levels + null department +
  degree-type template description) as the same fabrication as "BA" stubs; defined
  when a program is REAL (credential-disambiguated name + real department +
  field-specific description). Evidence: live API, 4 newest universities 94–97%
  padded.
- **miss #9 (program spot-check):** extended the rendered-output check to FAIL on
  null/blank `department` and `"{field} — a {Univ} {degree_type} program offered
  through …"` template descriptions, and to run the catalog through this check
  programmatically before shipping. Evidence: same.

**Backlog delta:** created REPAIR_BACKLOG.md from empty. 13 CRITICAL (padded
catalogs, UCSD worst), 1 CRITICAL (Boston U bare-abbrev), 2 HIGH (Yale/Duke null
dept), 9 MEDIUM (shallow 22-program originals). Top open entry: **UC San Diego**.

**Invariants:** all intact; both edits tighten, none weaken. No finding argued for
loosening an invariant.
