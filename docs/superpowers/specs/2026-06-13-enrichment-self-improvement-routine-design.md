# Enrichment Self-Improvement Routine — Design

> A second autonomous routine ("the grader") that examines the results of the
> `enrich-profile` automation (run by Cursor), diagnoses what went wrong, and
> **tightens the `enrich-profile` skill itself** so the same problems stop
> recurring — automating the manual QA→diagnose→fix-the-rulebook loop the founder
> has been doing by hand.
>
> Status: **design v1.0** · 2026-06-13 · Approved direction: Approach A (live-site
> audit + Cursor-PR cross-check), fully-autonomous ship with hard safety rails,
> scope = improve skill + queue repairs (never edits profile data).

---

## 1. Problem & motivation

`enrich-profile` is a Claude Code skill run on a schedule by Cursor automation. It
raises university profiles toward the gold standard one whole university per run.
It keeps shipping the same recurring *classes* of defect that only surface in the
rendered product — for example: programs padded with generic/duplicate names
instead of real field-of-study names; "Events & Updates" tabs that render empty
because a feed was set but never actually produced anything; missing reviews or
campus photos; short or non-conformant catalogs. It also tends to add **new**
universities while earlier ones are still broken — i.e. it does not reliably honor
repair-first.

These are recurring **classes** of problem, not specific schools. Any individual
broken school is transient and belongs in the repair backlog (data), **never baked
into the rulebook** — the skill must stay general so it keeps applying as the fleet
changes.

Today the founder catches these by looking at the live app, diagnoses each, edits
`enrich-profile/SKILL.md` to prevent recurrence of the class (e.g. past manual
fixes added photo-credit, reviews-depth, and ban-stub-program rules), and tells the
enricher what to fix first. **This routine automates that loop.**

The deeper goal is a self-improving system: the grader closes gaps faster than the
enricher opens them, and the rulebook converges toward "can't produce a bad page."

## 2. Goals

- Each run, **find** the defects in the live enrichment output the way a person
  would — both known failure types and **novel** ones not yet codified.
- **Diagnose** each: display bug (code) vs bad data (repair) vs rulebook gap (skill).
- **Tighten `enrich-profile/SKILL.md`** to close rulebook gaps, autonomously.
- **Queue repairs**: a ranked backlog of broken universities the enricher consumes.
- Be **safe to run unattended**: never weaken an invariant, never edit without
  evidence, never touch data/code, fully reversible, fully logged.

## 3. Non-goals (YAGNI / safety)

- Does **not** edit profile data modules, migrations, or app code (it flags those).
- Does **not** run the enrichment itself (separate routine).
- Does **not** relax any invariant or add a rule without an observed live problem.
- Does **not** build a formal scored eval suite in v1 (can fold in `ai/evals` later).

## 4. Architecture

A new skill + a scheduled routine that invokes it. Reads/writes only four files:

| File | Role | Owner |
|---|---|---|
| `.claude/skills/improve-enrichment/SKILL.md` | The grader's own rulebook (this routine's operating manual) | authored once |
| `.claude/skills/enrich-profile/SKILL.md` | The enricher's rulebook — **tightened** by the grader | edited each run |
| `.claude/skills/enrich-profile/REPAIR_BACKLOG.md` | Ranked "fix these first" list the enricher consumes | rewritten each run |
| `.claude/skills/improve-enrichment/CHANGELOG.md` | Append-only log: date · findings · rules changed + evidence · backlog delta | appended each run |

**Trigger:** a daily Claude Code scheduled cloud agent, timed after Cursor's nightly
enrichment window (exact time set at schedule-creation). Daily (not event-driven)
because Claude Code routines are cron-based and daily polling also re-audits older
profiles, not just last night's.

## 5. The run loop (six steps)

### Step 1 — Orient
Read `enrich-profile/SKILL.md` (current rules), the latest `CHANGELOG.md` entry, the
current `REPAIR_BACKLOG.md`, and list the profile PRs/commits Cursor merged since the
last run (`git log origin/main` since the last changelog timestamp; `gh pr list`).

### Step 2 — Grade the live output (two passes)

**(a) Deterministic known-miss checklist** — query the live API
(`https://api.unipaith.co/api/v1`) for each known failure type. Concrete checks:

- **Stub / padded programs:** `/programs?institution_id={id}&page_size=100` (paginate)
  → `Counter(program_name)`. Flag any institution with bare-abbreviation names
  (`BA`/`BS`/`MS`/`MA`/`PhD`…), duplicate names, `department == "Programs"`, or
  boilerplate descriptions (template with the field swapped).
- **Dead feeds:** `/institutions/{id}/posts` returns 0 while the institution is
  enriched (has `_standard` / a campus photo / a full catalog).
- **Missing reviews:** sample programs via `/programs/{id}`; compute % of *coverable*
  programs (MBA/MS-CS/flagship majors/etc.) with non-empty `external_reviews`.
- **Missing/short photo gallery:** `school_outcomes.campus_photos` length < 4.
- **Short catalog / conformance / no `_standard`:** catalog count vs peer; missing
  required fields; missing or stale `_standard` stamp.

**(b) Student's-eye open-ended pass** — pick ~3 recently-changed + ~2 random
institutions and actually read their pages (API payloads, or browser if needed)
*as a prospective student*. Note anything that feels wrong even if it is **not** on
the checklist — wrong-looking numbers, awkward/empty sections, broken links,
mismatched data. This pass is the engine of self-improvement: it is how **new**
problem classes get discovered and become new checklist items + new skill rules.

### Step 3 — Diagnose each finding
Classify, confirming data-vs-display via the API before deciding (no guessing):
- **Display bug** (the data is fine but the page renders it wrong) → out of scope:
  log it and flag for a human/code fix (e.g. `spawn_task`), do not fix code.
- **Bad data** (a profile is wrong/incomplete) → add to the repair backlog.
- **Rulebook gap** (the skill never forbade/required this) → edit `enrich-profile`.

A single finding can produce both a backlog entry (fix the instance) and a skill edit
(prevent the class) — e.g. a stub-program finding → a backlog entry (repair that
school's stub programs) **and** a general skill rule ("never name a program with a
bare degree abbreviation"). The backlog entry names the school; the skill rule
never does.

### Step 4 — Tighten the rulebook
For each rulebook gap, edit `enrich-profile/SKILL.md` in its existing structure
(numbered "Concrete misses" list; repair-first issue list in step 2; the
verify-rendered-output principle). Adds a new miss or strengthens an existing rule,
with a one-line pointer to the live evidence. Subject to the safety rails (§7).

### Step 5 — Write the repair backlog
Rewrite `REPAIR_BACKLOG.md`: institutions ranked worst-first, each with specific
issues, a severity, and a first-observed date. The enricher's repair-first step reads
this and clears the top entry before creating any new university.

### Step 6 — Ship + log
Run the enricher skill's health check (`pytest tests/test_profile_standard.py
tests/test_profile_enrichment.py -q`; markdown-only so no migration/build gates).
Commit the skill + backlog + changelog on a branch, open a PR, **auto-merge to
`main`** (squash). Append a `CHANGELOG.md` entry: date · findings (with API
evidence) · each rule changed + rationale · backlog delta · or "no new gaps found."

## 6. The two-routine interface (the backlog)

`REPAIR_BACKLOG.md` format (one block per institution, ranked worst-first). The
backlog is **data** — it names real schools transiently and is rewritten every run:

```
## 1. <University Name>  — severity: <high|med|low> — first seen <YYYY-MM-DD>
- <specific issue observed> → <what to fix> (enrich-profile miss #<n>)
- <specific issue observed> → <what to fix> (miss #<n>)
```

`enrich-profile/SKILL.md` step 2 gets one added line: *"Before surveying the DB, read
`REPAIR_BACKLOG.md` — its top entry is your repair target this run; clear it before
adding anything new."* This is the only edit the grader makes to the enricher's
*flow* (vs. its rules); it wires the handoff.

## 7. Safety rails (the core of an unattended self-editing loop)

1. **Immutable invariants.** A hard-coded list the grader may **never weaken or
   remove**, only add to or tighten: no-fabrication (verify or omit), repair-first,
   verify-rendered-output, workshop-feedback-only, the manifest's `required` fields.
   If a finding seems to argue for *loosening* an invariant, the grader **logs it for
   human review and does not act**.
2. **No edit without evidence.** Every rule change must cite a concrete live problem
   observed *this run* (API result / page). A clean fleet → ship nothing, log "no new
   gaps." Never invent a rule to justify a run.
3. **Bounded + anti-churn.** ≤ 3 rule changes per run. Before adding a rule, confirm
   it is not already covered (no duplicates, no cosmetic rewording).
4. **Post-edit self-review.** Re-read the entire `enrich-profile/SKILL.md` after
   editing and confirm it is still coherent: misses numbered sequentially, no
   contradictions, all invariants intact. Abort the edit if not.
5. **Scope fence.** Touches only the four files in §4. Never profile data modules,
   migrations, or app code — those are flagged, not changed.
6. **Reversible + auditable.** One squash PR per run; the `CHANGELOG.md` records every
   change with its rationale and evidence, so any run can be reviewed or reverted.

## 8. Success criteria

- Recurring defect classes **decline** over time (the same miss is not re-found run
  after run once a rule lands).
- The repair backlog **shrinks** as the enricher works it (top entries clear).
- The `CHANGELOG.md` shows every rule was added in response to a **real observed**
  issue, and **no invariant ever weakened**.
- A healthy run reads: "audited N institutions; found X live issues; added Y rules
  (with evidence); queued/updated Z repairs" — or a clean "no new gaps found."

## 9. Components & boundaries (for the implementation plan)

- **`improve-enrichment` skill** — the operating manual: the six-step loop, the
  concrete API audit checklist, the diagnosis taxonomy, the safety rails, the
  ship/log protocol. One self-contained markdown file (+ optional `references/`).
- **`REPAIR_BACKLOG.md`** — data interface to the enricher (format above).
- **`CHANGELOG.md`** — append-only audit trail.
- **One edit to `enrich-profile/SKILL.md`** — the "read the backlog first" line in
  repair-first step 2.
- **The scheduled routine** — created via the schedule mechanism; its prompt simply
  invokes the `improve-enrichment` skill. (Cadence/time set at creation.)

## 10. Testing / validation

- **Dry-run the loop manually** once against the current live fleet before scheduling:
  confirm it finds the fleet's current open issues, proposes sane skill edits, writes
  a sensible backlog, and respects the rails (would refuse to weaken an invariant;
  ships nothing on a clean node).
- **Invariant guard check:** verify the grader, given a (synthetic) finding that
  argues for relaxing no-fabrication, logs-for-review instead of editing.
- **Idempotency:** a second run with no new problems makes no skill edits and logs
  "no new gaps."
- The enricher's existing tests stay green after each grader edit (the ship gate).
