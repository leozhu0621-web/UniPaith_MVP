# Enrichment Grader — CHANGELOG

Audit log of the `improve-enrichment` routine: each run grades the live enrichment
output, tightens the `enrich-profile` rulebook against recurring problem CLASSES,
and re-ranks the repair backlog. One squash PR per run.

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
