---
name: enrich-profile
description: >
  Autonomously develop the UniPaith profile database toward the gold standard,
  ONE COMPLETE UNIVERSITY per run — the institution page + every school + every
  program + all their details — verified and shipped as one atomic unit. Use as a
  scheduled routine that keeps growing the database. Discovers a university's real
  structure, researches every field from authoritative sources, VERIFIES (never
  fabricates — omits if unverifiable), writes the data + an idempotent migration,
  and ships it live. Full spec:
  docs/superpowers/specs/2026-06-10-university-enrichment-routine.md.
---

# Enrich a whole university to the gold standard

You develop the UniPaith profile database so every institution / school / program
reaches the **gold standard** defined by the MIT / Sloan / MBAn reference instance
— with **real, cited data and zero fabrication**. This skill is the complete
operating manual for one run. The human drives it on a schedule and controls the
frequency; you do exactly **one whole university** each run.

**Unit of work = one complete university** = the institution + **all** its schools
+ **all** their programs + every detail, enriched to gold, verified, shipped as one
PR. It is a large job per run, and that is intentional — it satisfies the
cross-level dependencies (schools inherit institution stats; programs inherit the
campus photo) atomically, so you never publish a half-built university or an
orphaned child.

## The one inviolable rule

**Never fabricate. Ever.** A field ships only when verified against authoritative
sources and carrying a citation. If you cannot verify it, **omit it** (record it in
that node's `_standard.omitted`). An honestly-empty field is correct; a guessed one
is a defect. Extra research tokens are acceptable; a wrong fact on a student-facing
page is not.

## Completeness is non-negotiable — verify before you ship

The first routine runs shipped **shallow** universities (only the cheap federal
report-card stats), which broke the pages. Do **not** repeat these misses. A node
is not done until `check_conformance` says so.

**Before shipping any node, run `check_conformance(level, snapshot,
profile_version=)` and only treat it as done when it is gold OR every remaining
required field is recorded in that node's `_standard.omitted` with a real
reason.** Stamp `_standard = {"version": STANDARD_VERSION, "enriched_at": <date>,
"omitted": [...]}` on every node — a node with no `_standard` is treated as
never-enriched and will be redone. **Do not ship a node as "done" with empty
`ranking_data` / `content_sources` / `research` / `campus_life`.**

Concrete misses observed in the first runs — each broke a real page:

1. **Feeds / updates (`content_sources`) — was empty → zero news (issue: no
   updates).** Set `content_sources = {news_rss, events_feed: {url, type:
   "ical"}, social: {instagram, linkedin, x, youtube, facebook}}` on the
   institution **and on every school and every program** (see steps 5–6 — schools
   use their own feed or the institution feed + school `keywords`; programs use the
   institution/school feed + program `keywords`). The daily ingest fills Updates +
   Events FROM these — **a school/program with null `content_sources` shows an empty
   Events & Updates tab, which is the current bug.** Also confirm news posts get a
   cover image (the ingest now reads media/enclosure/inline `<img>`).
2. **Program-set BREADTH — do not curate a flagship subset (issue: too few
   programs).** The standard for a university's program set is the **FULL
   published degree catalog**, not a hand-picked "gold" handful. Penn shipped
   with 18 and Columbia with a "curated catalog" — both wrong. Enumerate EVERY
   substantive degree program across EVERY school: bachelor's / master's / PhD /
   professional, **residential AND online / hybrid / professional / continuing-
   education / extension / part-time**. Cross-check the **IPEDS / College
   Scorecard program list (by CIP for the UNITID)** — if the university offers
   ~100 programs and you've added 18, you are NOT done. The gold reference (MIT)
   carries 65 programs; a peer university with a dozen is incomplete.
   - **Breadth-first, then a MANDATORY depth pass — "defer" is not "abandon".**
     Create EVERY program node with verified *basics* first (full name,
     degree_type, `delivery_format`, department, description, website, tuition —
     all on the official catalog/program pages). Then run the **depth pass over
     the SAME university**: outcomes, class profile, faculty, and
     **`external_reviews` for every program with third-party coverage** (miss #8 +
     step 6). A program that exists with verified basics beats a missing one — so
     never drop a real program over a single unverifiable deep field — **but the
     university is NOT done until the depth pass is complete.** A genuinely huge
     catalog (Columbia ~263) may span runs: stop mid-depth and resume next run,
     BUT repair-first (step 2) forbids starting a NEW university while this one's
     coverable programs still lack reviews. "Omitted-pending until a resume that
     never comes" is the exact bug that left the ENTIRE fleet at ~1 reviewed
     program each — do not repeat it.
   - Set `delivery_format` (`on_campus` / `online` / `hybrid`) on every program.
3. **Links everywhere — were missing (issue: campus resources & others have no
   links).** Whenever you name a lab, institute, research center, campus resource,
   or employer, capture its official URL into the matching links map:
   `school_outcomes.research.lab_links` as `{name: url}`,
   `school_outcomes.campus_life.resources` as `[{name, url}]`, faculty `url`,
   every stat's `source_url`. A named entity without its link is a half-filled
   field — put a link wherever an authoritative one exists.
4. **`ranking_data` — was empty (issue: card has no Private/Public type).**
   Populate `ranking_data.{ownership_type (`private`|`public`),
   carnegie_classification, accreditor}` + the rankings the university actually
   holds (QS / THE / U.S. National, each cited). `ownership_type` +
   `carnegie_classification` drive the explore-card "Private/Public Research"
   eyebrow and the detail-page rankings section.
5. **Lead the description with the institution's character** so the card + filters
   classify it: e.g. *"Harvard University is a private research university in
   Cambridge, MA, founded in 1636…"* (MIT's description does this — that's why its
   card shows the eyebrow). Never bury or omit "private/public research
   university".
6. **Use the manifest's EXACT paths.** Ownership goes in
   `ranking_data.ownership_type`, NOT a stray `school_outcomes.ownership`; faculty
   → `faculty_contacts`; reviews → `external_reviews`. The conformance check is
   keyed on these exact dotted paths — run it to confirm every value landed where
   the standard expects, not just "somewhere".
7. **Campus photos + per-photo credit — a GALLERY, not a single shot, and an
   uncredited photo is a defect (issues: pics have no credit/reference; only one
   pic).** Every institution gets `school_outcomes.campus_photos` — a list of
   **4–5** verified `{url, credit}` entries (recognizable OUTDOOR campus scenes:
   named buildings, quads, towers/gates, aerials — no logos/maps/portraits/
   interiors; landscape orientation, ≥1000px wide; use the Commons 1600px
   `thumburl`). The detail-page hero shows `[0]` and opens the rest in a
   click-through lightbox; the explore card uses `[0]` for its gradient header.
   Source from the university's Wikimedia Commons category
   (`action=query&list=categorymembers&cmtitle=Category:<University>&cmtype=file`),
   then **VERIFY each file's author + license via the Commons API extmetadata
   (`Artist` + `LicenseShortName`)** — keep only freely-licensed files (CC BY /
   CC BY-SA / CC0 / public domain / no-restrictions) and write each credit as
   `"Wikimedia Commons / <Author> (<License>)"` — e.g.
   `"Wikimedia Commons / Peacearth (CC BY-SA 4.0)"`, or `"… (public domain)"` /
   `"… (CC0)"`. Also keep `media_gallery` leading with `campus_photos[0].url` and
   `school_outcomes.media_credit` = its credit (legacy single-hero fallback).
   Never invent an author or license; a file you cannot verify gets replaced or
   dropped, and **3 verified photos beat 5 with one guessed credit.**
8. **Reviews (`external_reviews`) — were EMPTY (issue: all reviews are blank).**
   Every program — and any school/institution with third-party coverage — gets an
   `external_reviews` object in the **MBAn shape** (copy the gold example
   `_REVIEWS_BY_SLUG["mit-sloan-mban"]` in `mit_profile.py`):
   `{summary, themes: [{label, sentiment: "positive"|"mixed"|"caution", detail}],
   sources: [{label, url}], disclaimer}`. **GATHER → SUMMARIZE → CITE:** read real
   third-party coverage online (Poets&Quants, BusinessBecause, U.S. News, Niche,
   official employment reports, reputable forum sentiment), distil it into an
   honest paragraph + 4–6 themes that **include the common cautions** (not just
   praise), and attach every source with a resolvable URL. The `disclaimer` must
   say the reviews are aggregated/paraphrased from public sources, not individual
   verbatim quotes. **Never fabricate a quote, rating, or theme**, and never leave
   reviews blank when reputable coverage exists — only record `external_reviews` in
   `_standard.omitted` when a program genuinely has no third-party coverage.
   - **Coverage bar — by program TYPE, not a token count.** Reviews are REQUIRED
     for every program a real applicant would research: MBA / MBAn / MS in
     CS·DS·Analytics·Finance·Engineering / MEng / MPH / MPP / JD / MD / MArch /
     EdM, every flagship undergraduate major, and anything with a Poets&Quants /
     U.S. News / Niche / GradReports / reputable-forum footprint. **Filling 1 of
     60 is the bug;** honest omit-with-reason is only for niche research degrees
     with genuinely no third-party coverage.
   - **Do NOT imitate the gold reference's CURRENT review coverage.** MIT today
     carries `external_reviews` on only the MBAn (1 of 65) — that is a KNOWN GAP,
     not the standard. Copy MBAn's *shape and sourcing quality*, then apply it to
     EVERY coverable program (MIT's own MBA, MFin, etc. are themselves repair
     targets).
   - **The conformance gate already bites:** `external_reviews.summary` is a
     `required` program field in `manifest.py`, so `check_conformance` marks any
     program without it — and without it stamped in `_standard.omitted` — as NOT
     gold. A university with coverable programs missing reviews cannot be "done",
     so run the per-program check before you ship and treat a blank-reviews
     coverable program as a hard failure, not a deferral.

## What "the standard" is (read these first)

- **`unipaith-backend/src/unipaith/profile_standard/manifest.py`** — `STANDARD_VERSION`
  + the ordered `Section`/`Field` blueprint per level (`institution`, `school`,
  `program`); each `Field` has a dotted `path`, a `required` flag, a `sourcing`
  rule, and an `enrich` flag (`False` = inherited-from-parent or render-only).
- **`profile_standard/conformance.py`** — `check_conformance(level, snapshot,
  profile_version=)` → `{missing_sections, missing_fields, stale}`.
- **`profile_standard/playbook.md`** — the per-field authoritative-source + gate rules.
- **`services/profile_enrichment/gate.py`** — the deterministic verify rules.
- **`unipaith-backend/src/unipaith/data/mit_profile.py`** — the gold reference and the
  data-module template (copy its *shape*, never its values).
- **Full routine spec:** `docs/superpowers/specs/2026-06-10-university-enrichment-routine.md`.
  Parent design: `docs/superpowers/specs/2026-06-09-profile-standard-and-enrichment-design.md`.

A node is **gold** when `check_conformance` returns no missing required fields
(except fields legitimately in its `_standard.omitted`). A **university is gold**
when every node in its tree is gold.

## Per-run algorithm (one whole university)

### 1. Health check
```bash
cd unipaith-backend && PYTHONPATH=src AI_MOCK_MODE=true .venv/bin/pytest tests/test_profile_standard.py tests/test_profile_enrichment.py -q
cd ../frontend && npm run build >/dev/null 2>&1 && echo FE_OK
```
Confirm the working tree is clean and `main` is healthy.

### 2. Select the target university — REPAIR EXISTING BEFORE ADDING NEW
**Never create or import a new university while any existing one has issues.**
Otherwise the fleet sprawls and the same gaps recur forever. Each run, in this
STRICT order:

1. **Finish any university a prior run left partial** (in-flight) first.
2. **Then repair the worst-off EXISTING university that is not fully gold.** Survey
   the institutions already in the DB and treat a university as *not gold* if ANY
   node has an issue:
   - `check_conformance` reports a missing required field at the institution, **any
     school**, or **any program**;
   - a **short program catalog** — missing online / professional / continuing-ed /
     extension programs, or a school showing far fewer programs than it really has;
   - **schools or programs with no `content_sources`** → their Events & Updates are
     empty (the routine has been setting feeds only on the institution — fix this);
   - news posts with **no cover image** (the feed has images the ingest can now
     capture from media/enclosure/inline `<img>`);
   - **programs lacking `external_reviews` where reputable third-party coverage
     exists** — the SINGLE biggest gap today: the whole fleet has reviews on ~1
     program each (MIT 1/65, Columbia 2/263, Caltech 1/91). A flagship / MBA /
     popular professional or STEM master's with blank reviews is *not gold*
     (miss #8). Repairing this comes before any new university — and MIT itself
     (1/65) is a valid repair target;
   - **missing or single-photo `school_outcomes.campus_photos`** — the standard
     is a 4–5 photo verified gallery (miss #7); an institution with no campus
     photo at all (most beyond the original 14) breaks both the card header and
     the detail hero;
   - **no `_standard` stamp**, or stamped at an older `STANDARD_VERSION`.
3. **Only when EVERY existing university is fully gold** (institution + all schools
   + all programs, each conformant or honestly-omitted) may you add a brand-new
   university.

Within that order, prioritize by student demand (saved-school / match / view counts)
then by size of gaps. If every existing university is gold and no new target is
requested, report and stop. **Adding breadth while existing profiles are broken is
the one thing this routine must NOT do.**

### 3. Discover the university's real structure (never invent it)
- Resolve the official name + **UNITID** (College Scorecard / IPEDS key). No UNITID →
  flag for manual mapping and skip.
- **Schools/colleges:** the university's official "Schools & Colleges" / "Academics"
  page; cross-check IPEDS.
- **Programs (FULL catalog — not a flagship subset):** enumerate **every**
  substantive degree program per school from the official catalog **and** the
  IPEDS / College Scorecard program list (by CIP for that UNITID), including
  online / professional / continuing-ed / extension. Treat the IPEDS/Scorecard
  program count as the target completeness check — getting ~15-20 when the
  university offers ~100 means structure discovery is incomplete; keep going (or
  resume next run) until the set is the real catalog (peer count, cf. MIT's 65).
- Dedupe; assign stable slugs (`<univ>-<program>-<degree>`); map each program to its
  owning school by name. If a school/program can't be confirmed officially, **do not
  add it.**

### 4. Enrich the institution FIRST (parent before children)
Fill every required institution-level field (rankings · report-card · admissions
funnel · diversity · recognition · scale · outcomes · cost & aid · location · campus
resources · **`campus_photos` gallery (4–5, each with verified credit) +
`media_credit`** (completeness item 7) · feeds ·
sources) from authoritative sources. Verify each (§Verify); cite;
omit-if-unverifiable. The institution must reach gold first so schools/programs
inherit its stats + photo.

### 5. Enrich every school
For each school: `about_detail` (founded, leadership, faculty, research centers,
named-for) + **`content_sources` (REQUIRED — this is why school Events & Updates are
empty today)**. Set the school's `content_sources` to its OWN official feeds when it
has them (e.g. `news.hbs.edu`, a school events calendar, the school's social
accounts); otherwise set the institution's `news_rss`/`events_feed` **plus
`keywords`** naming the school (e.g. `["Harvard Business School","HBS"]`) so the
shared feed is filtered to school-relevant items. Verify; cite; omit-if-unverifiable.

### 6. Enrich every program
For each program: basics, curriculum/tracks, admissions (incl. international / recs /
fee), costs (breakdown), outcomes (salary distribution + employment + top industries
/ employers + **conditions/methodology verbatim** + source), insights (class profile,
faculty, **reviews — `external_reviews` in the MBAn shape, completeness item 8,
gathered→summarized→cited, never left blank when coverage exists**), and
**`content_sources` (so the program's Events &
Updates populate — empty today because the routine only set institution feeds)**. A
program rarely has its own news site, so use the school's/institution's `news_rss` +
`events_feed` **plus `keywords`** naming the program/department (the MBAn pattern in
`_MBAN_CONTENT`) so the shared feed is filtered to program-relevant items — never
leave program `content_sources` null. Verify each; cite; omit-if-unverifiable.

### Verify (the gate — every value, every level)
Ships only if: `first_party` = one official source; `authoritative_2x` = **≥2
independent (distinct-domain) sources agreeing** within ~5%; a **citation** (`source`
+ resolvable `source_url`) is attached; numbers cross-check; and a careful re-read of
the cited text confirms it (multi-pass for contested numbers — extra tokens are fine).
Else → **omit** (add the path to that node's `_standard.omitted`). Never guess, infer,
or round into a stronger claim. Capture stats' conditions verbatim.

### 7. Write the data module
Author/extend `unipaith-backend/src/unipaith/data/<university>_profile.py`, mirroring
`mit_profile.py`: per-university constants (`RANKING_DATA`, `SCHOOL_OUTCOMES`,
`SCHOOLS[]`, `PROGRAMS[]`) + per-slug dicts (`_OUTCOMES_BY_SLUG`, `_COST_BY_SLUG`,
`_REQ_*`, `_TRACKS_BY_SLUG`, `_CLASS_PROFILE_BY_SLUG`, `_FACULTY_BY_SLUG` →
`faculty_contacts`, `_REVIEWS_BY_SLUG` → `external_reviews`, school `about_detail` /
`content_sources`) + an idempotent `apply(session)`. Stamp every node's `_standard =
{"version": STANDARD_VERSION, "enriched_at": <date>, "omitted": [...]}`.

### 8. Migration + scratch-DB validation
Add an Alembic data migration whose `upgrade()` calls
`<university>_profile.apply(Session(bind=op.get_bind()))` (idempotent, flush-not-
commit, `replace=True`/dedup). Validate the full chain on a fresh scratch DB
(CREATE EXTENSION vector,pgcrypto → `alembic upgrade head`). Single head.

**Head-sync protocol (MANDATORY — a dual-head once blocked ALL deploys for hours):**
other sessions ship migrations concurrently, so never trust a stale checkout.
1. **Immediately before authoring** the migration: `git fetch origin main` and
   branch off fresh `origin/main`; set `down_revision` to the CURRENT head of
   that fresh tree (`alembic heads`), not whatever your older checkout had.
2. **Right before opening the PR:** re-fetch `origin/main`, merge it in, re-run
   `alembic heads`. If a concurrent migration landed and you now see TWO heads,
   re-point your `down_revision` onto the new head (or add a merge-only
   migration) so your PR carries exactly ONE head.
3. **Right after your PR squash-merges:** fetch the merged `origin/main` and run
   `alembic heads` one final time. If a racing merge created a dual head, ship a
   merge-only migration IMMEDIATELY (tiny PR, `down_revision = (headA, headB)`,
   empty upgrade/downgrade) before ending the run. Never leave `main` with two
   heads — `test_alembic_has_single_head` fails CI and every deploy is blocked
   until someone fixes it.
   **Anti-fix-race:** before authoring that merge migration, RE-FETCH
   `origin/main` and check both the tree and the OPEN PRs for an existing merge
   migration covering the same head pair — two sessions once both shipped merges
   for the same pair, which itself created a new dual head. If one already
   exists/is open, do NOT author a duplicate; wait for it to land, re-fetch, and
   re-run `alembic heads`. If your merge still lands second and creates a new
   dual pair anyway, ship a merge-of-merges (`down_revision = (mergeA, mergeB)`).
4. Use READABLE revision ids (e.g. `nyuprof1`, `feedspennmerge1`) — auto-generated
   hex ids trip the repo's detect-secrets pre-commit hook as false positives.

### 8.5 Conformance gate (do NOT skip — this is what the first runs missed)
For the institution and **every** school and program in the tree, build its
snapshot and run `check_conformance`. A node may ship only when it is **gold**
(no missing required fields) OR every remaining required field is in its
`_standard.omitted` with a real reason. If a node is neither, it is **not done** —
go back and fill it (or omit-with-reason). Confirm `ranking_data`,
institution **and every school and every program** `content_sources` (so their
Events & Updates aren't empty), `research`/`campus_life` (with links), the FULL
program catalog (cross-checked against the IPEDS/Scorecard count), and program
`delivery_format` are all populated. Stamp `_standard` on every node.

### 9. Ship
`ruff check src/<changed> tests/<changed>` (NOT `ruff check .`) + the profile tests +
`npm run build`; branch off `origin/main` → commit → PR → squash-merge → watch Deploy
Backend → **verify live** (query the public API for the institution + a sample school
+ a sample program; confirm new fields + citations + that the explore-card eyebrow,
updates feed, online programs, and resource links all render).

### 10. Report
University name · #schools · #programs · per-level fields filled (with sources) vs
omitted (with reasons) · conformance before/after · PR link.

## Scope & resumption for very large universities

The unit is the whole tree, but a giant (100+ programs) may exceed one run. Each field
is independently verified-or-omitted, so a partial tree is always consistent and
shippable. If a run can't finish, **ship the verified partial**; because step 2 prefers
finishing in-flight universities, the next run **resumes the SAME university** (re-plans
only what's missing — conformance-driven) until its whole tree is gold, *then* moves on.
Idempotent migrations make resumption and overlap safe.

## Guardrails (every run)

- **Never fabricate. Omit if unverifiable. Cite everything.**
- **One whole university per run** (or finish an in-flight one) — atomic + shippable.
- **Institution before its schools/programs.**
- **Idempotent migrations** (`replace=True` / dedup).
- **Editorial standard:** content-rich, program-specific, sentence case, numbers with
  units + reporting window — never generic marketing.
- **Never expose secrets / API keys.**
- **Ship every verified unit** (commit → merge → deploy → verify live); never block the
  tree on one unverifiable field — omit and continue.
- **Stop condition:** all universities gold at the current `STANDARD_VERSION` → report
  and end.

## Using this as a scheduled routine

The human schedules this skill at any cadence they choose; each firing enriches one
whole university (or advances an in-flight one) and ships it. See §11 of the spec for
the exact prompt to schedule. Because every run is whole-tree, idempotent, and verified,
the database grows one complete university at a time, safely, without ever shipping a
fabricated fact.
