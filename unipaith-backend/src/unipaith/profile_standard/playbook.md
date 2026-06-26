# Profile sourcing & wording playbook (STANDARD_VERSION 2)

This is the rulebook the enrichment engine (Phase 2) and its verification gate
follow when filling any profile to the standard. It is derived from how the
MIT / Sloan / MBAn reference instance is sourced. **Nothing is fabricated: if a
field cannot be verified per the rules below, it is omitted, never guessed.**

## Definition of done — fully enriched

A node (institution / school / program) is **done only when it is fully
enriched**: every required field is actually present, sourced per the rules
below (`profile_standard.is_fully_enriched` / `enrichment_completeness`).

- **Omitted ≠ done.** A field recorded in `_standard.omitted` is *open work*, not
  a closed gap. The routine re-attempts it every run (the snapshot still shows it
  missing) and must keep trying as new authoritative sources appear. Omission only
  protects the no-fabrication guarantee in the meantime — it never marks the node
  complete, and completeness reporting does not credit it.
- **Target = 100% present.** The self-driving loop selects the node with the most
  remaining required fields (not the lowest omitted-tolerant score) and works it
  until `is_fully_enriched` is true. Stale (`_standard.version` < current) re-opens
  every field.
- **Still no fabrication.** "Fully enriched" raises the *target*, never the
  tolerance: a field is filled only when it clears the verification gate. A node
  that cannot be completed from real sources stays *open*, reported as partial —
  never quietly accepted as done.

## Global rules

- **No fabrication.** A citable fact ships only when verified (see "Verification
  gate"). Otherwise omit it and record it in the profile's `_standard.omitted`.
- **Citations.** Every field whose `sourcing` is `first_party` or
  `authoritative_2x` must carry a resolvable `source` + `source_url` in its
  container blob (and `conditions`/methodology for statistical outcomes).
- **Authority precedence.** A first-party official source is never overwritten
  by a third-party aggregator. Newer official reports supersede older ones.
- **Wording.** Editorial, content-rich, program-specific — never generic
  marketing. Sentence case. Numbers carry their unit and reporting window.

## Verification gate (what may auto-ship)

A field passes only when **all** hold:
1. `first_party` fields: one designated official source (the institution's own
   page/report). `authoritative_2x` fields: **two independent authoritative
   sources agree** within tolerance.
2. A citation (`source` + reachable `source_url`) is attached.
3. Numeric values cross-check across sources within tolerance.
4. An LLM-judge pass (multi-pass; extra tokens are acceptable) finds no
   contradiction between the value and the cited source text.

Otherwise: **omit**.

## Per-field-group sources

| Field group | Authoritative source(s) | Sourcing |
|---|---|---|
| Program **outcomes** (employment rate, salary median/percentiles, signing bonus, top industries/employers, class profile, conditions) | The institution/school's official **career-office employment report** for the most recent class (e.g. MIT Sloan CDO MBAn report). | `first_party` |
| Program **tuition / cost** | The registrar / bursar / program cost-of-attendance page for the current year. | `first_party` |
| Program **admissions** (materials, deadlines, evaluation, fee) | The program's official admissions page. | `first_party` |
| Program **description / website / length / format / degree** | The official program page. | `first_party` / `official_or_curated` |
| Institution **rankings** | The **named ranking body** (QS, Times Higher Education, U.S. News); Carnegie classification from the Carnegie listing; accreditor from the regional accreditor. | `first_party` |
| Institution **report-card stats** (admit rate, net price, retention, graduation, earnings) | IPEDS / College Scorecard for federal stats; the institution's Common Data Set for admit/retention/test scores. Earnings (10yr) require **two** independent sources (Scorecard + institution) to agree → `authoritative_2x`. | `first_party` / `authoritative_2x` |
| Institution **campus resources / research** | Official institution pages (labs/institutes homepages, athletics/arts/housing hubs). | `official_or_curated` |
| School **about** (founded, named-for, leadership, faculty, research centers) | The school's official "about" / leadership / faculty-directory / centers pages. | `first_party` / `official_or_curated` |
| **Reviews** (program insights) | Aggregated from ≥2 reputable published sources with attribution and a disclaimer; never invented. | `authoritative_2x` |
| **Feeds** (news RSS, events calendar, social handles) | The institution/school/program's own published feeds and verified official social accounts. | `first_party` |

## Conditions / methodology

Statistical fields (outcomes especially) must carry the report's own condition
statements (knowledge rate, sample size, base-vs-total comp, reporting window,
reporting standard) so the student sees the data's caveats — as the MBAn
outcomes already do. Copy the report's wording; do not paraphrase a number into
a stronger claim than the source supports.
