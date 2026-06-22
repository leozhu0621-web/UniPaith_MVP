---
name: enrich-profile
description: >
  Autonomously develop the UniPaith profile database toward the gold standard,
  ONE COMPLETE UNIVERSITY per run — the institution page + every school + every
  program + all their details — verified and shipped as one atomic unit. Use as a
  scheduled routine that keeps DEEPENING the database toward gold — enrichment +
  repair only; it never adds universities (seeding is external). Discovers a
  university's real
  structure, researches every field from authoritative sources, VERIFIES (never
  fabricates — omits if unverifiable), writes the data + an idempotent migration,
  and ships it live. Full spec:
  docs/superpowers/specs/2026-06-10-university-enrichment-routine.md (editorial/standard
  axis); the program-side MATCHER contracts are governed by the 2026-06-17 AI-Structure
  specs 2 + 3, which SUPERSEDE the 2026-06-10 doc on the matcher and seeding axes.
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

## Also enrich for the MATCH — Prompt Library + ProgramPreference (AI Structure)

The profile you build is the **program side of the shared Prompt Library** — the
same typed catalog the student side fills (Spec 1) and the deterministic **CPEF
matcher** (Spec 3) sorts students against. Enrichment is therefore not only for the
editorial detail page: the **matcher-relevant attributes below must be populated**
(typed, verified, cited) or the match runs blind on them. Specs:
`docs/superpowers/specs/2026-06-17-ai-structure-2-school-program-profile-design.md`
(see the data map at `docs/superpowers/specs/assets/ai-structure/crawler_data_map.png`)
and `...-3-match-engine-design.md`. (We use **this Claude routine** for program
enrichment — there is no separate crawler service.)

**Authority precedence — never overwrite first-party.** A **claimed** school/program
(a verified institution user owns it) is authoritative. The routine must **not**
overwrite any first-party field — enrich only **unclaimed** profiles, and on a
claimed one fill **only** the gaps the school left empty. First-party always wins.

**Matcher-relevant attributes to fill (each feeds a CPEF fit; omit-never-guess):**
- **outcomes** — salary (median/start) · employment & underemployment · payback ·
  top employers · placement geography (College Scorecard / IPEDS / institution).
- **selectivity & admissions funnel** — applicants→admits→enrolled · admit rate ·
  yield · class profile (GPA & test bands, academic-only) · selectivity band (CDS/IPEDS).
- **full cost** — tuition + fees · total cost of attendance · net price · local living cost.
- **funding** — program-linked scholarships · assistantships · % aid · avg award.
- **format & schedule** — online/hybrid/in-person · campus setting · time-to-degree ·
  start terms · intake rounds · deadlines.
- **requirements** — test policy (test-optional?) · prerequisites · English policy.
- **academic substance** — tracks/specializations · curriculum · faculty/research.
- School **ranking** stays **editorial-only** — shown on cards, **never** a scored value.

**Base match inputs + per-field provenance — the floor the matcher scores on.**
Beyond the enrichment extras above, the matcher reads these *core* fields directly,
so every program MUST carry them: `tuition` (budget fit), location / country (geo
fit), `degree_type` → target level (eligibility veto), `cip_code` + a real,
field-specific `description_text` (these drive the interest/field signals AND the
dense embedding), and support-service signals (needs fit). On **every** field you
write, stamp `field_provenance[field] = {source, source_url, confidence, fetched_at}`
with the authority tier — **claimed › verified-feed › crawler › inferred** — because
that becomes the program-side confidence the matcher trusts (a crawler fact is
believed less than a school-confirmed one). A program missing these core fields is
scored on thin data and will rank poorly for everyone.

**A matcher-core field the institution PUBLISHES (so it is knowable for nearly every
program) is NOT an honest per-field omission when it is null CATALOG-WIDE — that is
matcher STARVATION the editorially-"done" page hides, and `tuition` is the live fleet's
dominant instance.** `tuition` is the budget-fit signal, and it is institution-PUBLISHED —
one uniform undergraduate sticker across all majors, plus a published per-program /
per-credit rate for most graduate programs — so it is knowable for essentially every
program. A catalog that ships 0% (or near-0%) `tuition` has therefore SKIPPED a knowable
matcher-core field, not honestly omitted it; the editorial detail page does not foreground
tuition, so a complete-looking page MASKS the gap and the matcher then scores every
program's budget fit blind. So the matcher pass must measure tuition COVERAGE per catalog
and treat a whole-catalog null as a structural FAILURE (the same bar as a missing
description): stamp the institution's real, cited published rate per credential level (the
undergrad sticker / the graduate tuition), and record `tuition` in `_standard.omitted` with
a reason ONLY for the rare genuinely-unpublished program (e.g. a fully-funded PhD whose
tuition is waived) — never leave the entire catalog null. This TIGHTENS the per-program
"MUST carry" core-field list above; it does NOT weaken omit-never-guess — fill from the
PUBLISHED number, never a guess. The same logic applies to any institution-published
matcher-core field (location/country, `degree_type`) shipped null fleet-wide. Evidence:
live API this run — 16 of the 40 enriched catalogs ship 0% tuition, including editorially-
complete large catalogs (NYU 507 programs, UCLA 373, Michigan 379, UIUC 419, UW-Seattle
360, USC 511, BU 396, UT-Austin 338), while peer catalogs correctly stamp it (Princeton
100%, Cornell 92%, MIT 69%, Columbia 44%).

**Measure tuition coverage PER CREDENTIAL LEVEL — a whole credential TIER shipped 0% is the SAME
matcher-starvation as a catalog-wide null, MASKED by a healthy AGGREGATE %.** The catalog-aggregate
bar above (0%/near-0% catalog-wide) is necessary but no longer sufficient: it is BEATEN by a catalog
that fills its cheap-to-cover tiers and skips an expensive one. The undergrad sticker is uniform
across all majors, so bachelor's rows fill to ~100% almost everywhere; the residual null is therefore
concentrated in the GRADUATE tiers, and the catalog AGGREGATE HIDES it — a catalog reads "60% covered,
off the zero-tuition list" while its ENTIRE master's / certificate / PhD tier is matcher-blind on
budget. So the tuition pass must GROUP coverage by `degree_type` and treat any whole tier at 0% (beside
a filled tier in the same catalog, or a peer that fills that tier) as a FAILURE the aggregate cannot
excuse — never declare a catalog's budget signal done off the aggregate alone. Master's / professional /
certificate programs publish a per-program or per-credit rate and are rarely fully funded, so a whole
such tier at 0% is unambiguous starvation: stamp the published rate. A PhD tier publishes a sticker that
is commonly WAIVED by funding, so the genuinely-funded per-program omit-with-reason (above) still applies
— BUT a blanket tier-wide PhD null beside a PEER that fills it is not the "rare funded-waiver" omission;
stamp the published sticker (the matcher's budget input — funding is a SEPARATE signal) or record
`tuition` in that program's `_standard.omitted` with a reason, never a silent blanket tier null. This
TIGHTENS the catalog-aggregate measurement above to a per-credential one; it loosens nothing (the
funded-PhD-waiver exemption is preserved, now per-program-explicit, not tier-wide-silent). Evidence: live
API this run — Michigan reads 61% aggregate yet ships PhD 1/148 (1%); Carnegie Mellon 22% hides master's
1/99 + PhD 0/41; Johns Hopkins 25% hides ALL ~180 graduate programs (master's 0/95, certificate 0/84,
PhD 0/4) at 0% — while a peer (UT-Austin) fills PhD 86/86 and master's 90% and EVERY catalog's bachelor's
tier is already 100%.

**Tuition COVERAGE is NOT tuition CORRECTNESS — a graduate / professional program carrying the
institution's UNDERGRADUATE sticker is a WRONG value the matcher scores, not coverage; the per-credential
coverage rule above (non-null per tier) is BEATEN by stamping one uniform number — usually the undergrad
sticker copied down the tree — across a whole heterogeneous tier.** The per-credential rule fixed "is the
tier non-null"; it does NOT check that the value is RIGHT, so the cheapest way to clear it is to copy the
single undergraduate sticker onto every graduate and professional row: the tier then reads "100% covered"
while the matcher reads the SAME budget number for a funded research PhD, an academic master's, and a
professional Law / MBA / MD — the budget-fit analog of one description stamped across credential levels
(miss #8). Graduate tuition is NOT the undergraduate rate (research degrees are commonly funded or billed
per-credit; endowed vs contract/in-state colleges differ) and a PROFESSIONAL program (JD / MBA / MD / MArch)
publishes its OWN, typically much higher, rate — so a graduate or professional row whose `tuition` EQUALS
the undergraduate sticker is a copy-down DEFECT, a hard FAIL independent of coverage %. So the tuition pass
must measure VALUE-realness, not just non-null: (a) FAIL any graduate / professional program whose `tuition`
equals the institution's undergraduate sticker — stamp that tier's own published rate (the graduate base /
per-credit × typical load, the professional program's published rate) or, for a genuinely-funded research
degree, record `tuition` in `_standard.omitted` with a reason — never the undergrad number copied down;
(b) a single DISTINCT value across an entire graduate tier is a tell to VERIFY (a genuine published flat
academic-graduate rate distinct from undergrad is fine — UT-Austin's $12,006, UF's $12,740 — but the same
value as the undergrad sticker, or one academic rate flattened across the PROFESSIONAL tier, is the
copy-down). This TIGHTENS the per-credential coverage measurement to a per-credential VALUE measurement; it
loosens nothing (omit-never-guess holds — fill from the tier's PUBLISHED number, never a guess, and a
genuinely-unpublished program is omitted-with-reason, never back-filled with the undergrad sticker). **Gold
MIT is the 0-control for the DESCRIPTION metrics, NOT a tuition reference — it ships null cert / PhD tiers
AND 9 graduate rows carrying its own undergrad sticker, so do NOT imitate its tuition; verify against the
institution's published graduate / professional rate.** Evidence: live API this run — Boston University (now
read "88% covered") stamps its $69,870 undergrad sticker on 182 graduate programs; Cornell (read "92%
covered", in the CLEAN tier) stamps the identical $71,266 on 152 of 153 grad + professional rows (every
PhD, every professional degree), so both feed the matcher the undergraduate number on their entire graduate
tier; even gold MIT (9), Princeton (5/6), Caltech (2/2), Harvard (2) carry the undergrad sticker on grad
rows — while the genuine per-tier fillers (Michigan master's = 16 distinct values, Stanford 67, Berkeley
71, UCLA 98) carry DISTINCT graduate rates.

**NEW per-program step — derive the target applicant (`ProgramPreference`).** For
every program, also write a **`program_preferences`** row (model `ProgramPreference`,
table `program_preferences`, added in the AI-Structure build) so the **program →
student** match direction works even before a school claims:
- Set `source = "derived"` and the **inferred** confidence anchor **`0.4`** (§3.6
  authority precedence — NOT 0.6 public-crawl, 0.85 verified-feed, or 1.0 claimed). A
  derived preference is the lowest authority tier, so the matcher reads its `c_program`
  low; only a school's later claim raises it to 1.0.
- From the public **class profile** infer the baseline target applicant —
  `pref_min_gpa` (typical admitted GPA floor), `pref_test_bands` (e.g. `{"GRE": 320}`),
  `pref_fields` (common feeder fields), `pref_levels` (eligible current levels),
  `pref_countries` (recruiting geography).
- **Omit any field you cannot ground** (never guess a cutoff). When a school later
  claims, it overwrites these with `source = "claimed"` — **do not touch a claimed row**.
A program with no `program_preferences` row simply has "no opinion" (the matcher
treats it neutrally), so deriving it from real admit data is a genuine quality win.

**The match-side feed is EXECUTED IN YOUR DATA-MODULE MIGRATION — and `program_preferences`
is now AUTOMATED.** In the migration that calls `<uni>_profile.apply(session)`, add one
line right after it:

```python
from unipaith.services.match.derive_preferences import backfill_program_preferences
backfill_program_preferences(session, institution_id=inst.id)  # derive target-applicant rows
```

That deterministic helper (`services/match/derive_preferences.py`) derives a grounded
target-applicant row for every program of that institution lacking one — `pref_fields`
from the name/CIP, `pref_levels` from the degree, `pref_min_gpa` from a real class
profile (omit-never-guess) — stamping `source="derived"`, `confidence=0.4`, and it
**never touches a claimed/first-party row**. The whole fleet was backfilled once
(migration `progprefbf1`); calling it in your migration keeps each newly-enriched
university covered. `field_provenance` per-attribute stamping is NOT yet automated or
matcher-consumed — stamp it as you populate attributes for future authority-precedence,
but it is not a hard gate today. (The match SCORE math is Spec 3, backend-only; your job
is to feed it typed, grounded data.)

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
   - **The count is a CHECK, not a TARGET — NEVER pad it (issue: Boston U shipped
     483 programs of which 83 were named just "BA", 63 "MS", 61 "PhD", dept
     "Programs", with boilerplate "BA is an undergraduate degree program offered
     through BU's College of Arts & Sciences").** That is fabrication, not breadth,
     and it is WORSE than a short catalog. Every program MUST be a single REAL,
     distinctly-named degree: `program_name` is the field-of-study name —
     **"Bachelor of Arts in Economics", "PhD in Mechanical Engineering"** — NEVER a
     bare degree abbreviation ("BA"/"BS"/"MS"/"PhD"/"MA"), NEVER a generic label.
     **No two programs may share an identical name; `department` must be the real
     owning school/department (never "Programs"); the description must be
     program-SPECIFIC (mention the actual field), never a degree-type template with
     the field swapped out.** If the catalog lists "BA — 47 majors", that is 47
     distinctly-named programs (BA in Economics, BA in History, …) or, if you
     cannot resolve the major names, FEWER real entries — never one stub named "BA"
     per filler row. A duplicate/abbreviation/`"Programs"`-department name is an
     automatic fabrication failure: drop it or give it its real name.
   - **A catalog-breadth GATE must assert structural REALNESS, not a raw row COUNT —
     a `len(PROGRAMS) >= N` assertion frozen to a PADDED count FIGHTS de-fabrication
     and FAILS the deploy when you correctly drop the padding (the live regression
     this run).** When you de-pad a catalog (drop federal certificate / incidental-
     master's / CIP×award-level filler rows), its program count legitimately SHRINKS
     toward the real published catalog — so any test or conformance gate that hard-
     asserts a high MINIMUM row count, calibrated to the OLD padded number, will fail
     on the smaller real catalog and BLOCK the deploy (a correct repair that never
     ships). Write the catalog's own breadth gate to assert that every row is REAL
     (no CIP-prefix / rollup names, no classification-stub descriptions, no
     null/duplicate departments, no concentration-split rows) and that the count
     matches the VERIFIED real catalog — which may be far below the padded count —
     NEVER a raw `>= padded_N`; and when a de-fabrication SHRINKS a catalog, update
     that catalog's breadth test/gate in the SAME PR so the deploy is not blocked.
     The completeness bar still stands (the real FULL published catalog at peer
     count, cf. MIT's 65 — do NOT use this to justify a curated subset), but it is
     enforced by per-row REALNESS, not by a frozen number that mechanically rewards
     padding and punishes a clean de-fabrication. Evidence: live API this run — a
     de-fabrication PR that correctly dropped a catalog from 114 padded rows to 41
     real ones FAILED its Deploy Backend on a stale `assert len(PROGRAMS) >= 100`
     breadth assertion, and shipped only after a follow-up commit replaced the count
     assertion with a no-CIP-prefix / no-classification-stub realness gate.
   - **That realness GATE must scan the rollup tell on the FIELD portion of the name
     CREDENTIAL-FORM-AGNOSTICALLY — a gate keyed only on the generic-credential-PREFIX
     form ("Bachelor's in {rollup}") PASSES a real degree DESIGNATION glued to a
     CIP-rollup FIELD ("Bachelor of Arts in {rollup}"), the live evasion of the prior
     bullet's own realness gate this run.** When you replace a count gate with the
     realness gate above, the rollup-tell scan (trailing ", General"/", Other"; a
     federal multi-clause comma-and list "…, Literatures, and Linguistics"; an embedded
     slash "Religion/Religious Studies"; or a bare CIP rollup like "Area Studies" /
     "Multi/Interdisciplinary Studies, Other") must run on the FIELD part of every
     `program_name` AND its `department` REGARDLESS of the credential designation —
     "Bachelor of Arts in {CIP rollup}" is exactly as fabricated as the generic
     "Bachelor's in {CIP rollup}"; switching to the institution's real credential
     designation does NOT exempt the field. A gate that only rejects the generic
     "Bachelor's in" prefix will pass the real-designation rows and ship the rollup
     live (rollup echoed verbatim into `department`). The fix is unchanged: resolve
     each rollup field to the institution's REAL degree name + owning department
     ("Bachelor of Arts in Classics" / Department of Classics; "Bachelor of Arts in
     Religion" / Department of Religion; "Bachelor of Arts in German" / Department of
     German), never the federal taxonomy title. Evidence: live API this run — a
     freshly-deployed de-fabrication whose realness gate (written to replace a count
     gate per the prior bullet) still passed 8 of 41 "Bachelor of Arts in {CIP rollup}"
     rows — "…Languages, Literatures, and Linguistics" ×3, "Ethnic, Cultural Minority,
     Gender, and Group Studies", "Multi/Interdisciplinary Studies, Other",
     "Religion/Religious Studies", "Area Studies" — each with the rollup echoed
     verbatim into `department`, shipped live (the descriptions were field-specific and
     true, so only the names/departments + the prefix-doubling remained un-de-fabricated).
   - **The realness gate must ALSO reject a literal CIP CODE left in the name or
     department — the naked IPEDS-minting fingerprint the punctuation-keyed rollup scan
     MISSES (the live tell this run).** Every prior rollup-tell bullet keys the scan on
     TITLE punctuation (a trailing ", General"/", Other"; a federal comma-and list; an
     embedded slash; a bare CIP rollup title). But an IPEDS row can be minted into a name
     with the federal CIP NUMBER left attached — "Bachelor's in Psychology (CIP 42.99)",
     "Bachelor's in English Language and Literature (CIP 23.14)", "Bachelor's in Health
     Professions (CIP 51.15)" — and because the field text itself ("Psychology") is a
     CLEAN name with no punctuation tell, the title-keyed scan PASSES it. No real catalog
     prints a CIP code in a degree name, so the realness gate (miss #9) must ALSO scan
     every `program_name` AND `department` for a literal `(CIP <digits>)` (or a bare
     trailing CIP code) and FAIL on any hit: strip the code and resolve the row to the
     institution's real per-credential degree(s). Such a row is the most naked
     IPEDS×award-level mint — it typically also carries the generic "Bachelor's in {field}"
     credential form (resolve to the real "Bachelor of Arts/Science in …" designation) and
     a description written for the field across ALL levels, so a BACHELOR'S row's body
     opens "Graduate {field}…" (a credential-level lie the student sees). Evidence: live
     API this run — a freshly prefix-stripped catalog carried 28 such "(CIP NN.NN)"-suffixed
     names (11%), each invisible to the punctuation-keyed rollup scan; 4 of them bachelor's
     rows whose description opens "Graduate {field}…" (e.g. "Bachelor's in Psychology (CIP
     42.99)" → "Graduate psychology at SAS examines specialized subfields…").
   - **The IPEDS/Scorecard CIP count is an UPPER-BOUND completeness HINT, never a
     row-minting recipe — NEVER mint one program per (CIP × award-level).** A
     second padding variant is now live fleet-wide and EVADES the bare-abbreviation
     ban above: the CIP field title is used verbatim as `program_name`
     ("Anthropology", "Applied Mathematics"), so the certificate, bachelor's, and
     master's in ONE field all carry an IDENTICAL name; `department` is null; and
     the description is a degree-type template ("{field} — a {Univ} {degree_type}
     program offered through {school}"). That is the same fabrication as the "BA"
     stubs wearing a CIP-title costume (live API this run: the four most-recently-
     enriched universities were 94–97% such stubs; ~13 universities ≥60%). A
     program is REAL only when (a) its name disambiguates the credential
     ("Bachelor of Arts in Anthropology", "PhD in Anthropology" — never two rows
     both named "Anthropology"), (b) `department` names the real owning
     school/department (never null, never "Programs"), and (c) the description says
     something field-SPECIFIC beyond the degree label. Resolve each CIP row to its
     real per-degree program(s) or omit it — never emit a null-department,
     template-described, name-colliding stub per CIP×level.
   - **A generic credential PREFIX does NOT turn a CIP rollup title into a real
     program name — the live fleet's DOMINANT evasion this run.** The "repair" that
     cleared the bare-CIP-title and duplicate-name bans simply glued a generic
     credential onto the verbatim CIP/IPEDS taxonomy rollup ("Bachelor's in
     {rollup}", "Master's in {rollup}", "Doctorate in {rollup}") and copied that
     same rollup into `department` — so one field STILL mints ~3 near-identical
     rows (certificate/bachelor's/master's), now with distinct names and a non-null
     department, slipping past every prior check. The tell is the rollup surviving
     verbatim in the name: a trailing ", General" / ", Other", a federal
     multi-clause comma-and list ("…, Literatures, and Linguistics"; "Pharmacy,
     Pharmaceutical Sciences, and Administration"), or an embedded slash
     ("Engineering/Engineering-Related Technologies/Technicians, Other") — strings
     no institution prints on a real degree. A real name uses the institution's
     actual degree designation and field ("Bachelor of Science in Biology", "Master
     of Engineering in Aerospace Engineering"), never the CIP rollup with a
     credential glued on; and the description must NOT be the "{name} is a
     {degree_type} program at {Univ}, offered through the {rollup}" template (a
     grammatically broken "offered through the Biology, General" is the
     fingerprint). This is the SAME CIP×award-level fabrication as the "BA" stubs —
     the credential prefix is a costume, not a fix. Resolve each to the real
     per-field degree(s) or omit it. Evidence: live API this run — most "repaired"
     catalogs carry tens–hundreds of "{credential} in {CIP rollup}" rows with the
     rollup echoed as department and the template description, including one listing
     a "Bachelor's in Intelligence, Command Control and Information Operations" the
     institution does not offer.
   - **The conferred-degree DESIGNATION is itself part of the real name — the
     possessive award-level form ("Bachelor's in {field}" / "Master's in {field}" /
     "Doctorate in {field}") is the IPEDS-mint fingerprint and is a name-realness
     defect EVEN WHEN the field is genuine, not only when the field is a CIP rollup.**
     The prior bullet's tells (", General", federal comma-lists, slashes) catch rollup
     FIELDS; this catches the mint FORM on a legitimate field. Gold MIT and the clean
     fleet name every row with the institution's conferred designation ("Bachelor of
     Science in Biology", "Bachelor of Arts in Anthropology", "Master of Engineering in
     …"); the possessive "Bachelor's in {field}" form is fleet-anomalous — it survives
     only in catalogs minted straight off the IPEDS award-level taxonomy, so its
     presence at ANY density is a tell the rows were never resolved to the real degree.
     A "structural de-fabrication" / "per-credential descriptions" pass that resolves
     the rollup FIELDS and rewrites descriptions but leaves the bachelor's/master's rows
     in possessive form has NOT finished the NAME dimension — most self-evidently when
     the SAME field's doctoral row already ships the conferred form ("Doctor of
     Philosophy in Anthropology" beside "Bachelor's in Anthropology"), which proves the
     enricher knew the real designation and applied it inconsistently across credential
     levels of one field. A de-fab is done only when, per field, every credential row
     uses the institution's conferred designation under ONE convention and the
     possessive award-level form is 0% (gold MIT = 0%). Evidence: live API this run —
     freshly de-fabbed, already-DEPLOYED catalogs ship 53–55% possessive "Bachelor's in
     {field}" rows beside conferred doctoral siblings, with federal CIP titles ("Area
     Studies", "… and Related Services") still riding the surviving bachelor's rows.
   - **Do NOT mint one program row per concentration / track / specialization of a
     single degree (count-padding by over-decomposition).** A degree's
     concentrations belong in that program's `tracks` field (step 6), not as
     separate program nodes. The tell is a base field repeated across rows that
     differ only by a trailing "— {concentration}" — e.g. one "Bachelor's in
     Anthropology" exploded into "… — Biological Anthropology", "… — Sociocultural
     Anthropology", "… — Religion", "… — Health Medicine". These evade the
     duplicate-name and real-department checks (names differ; department is the real
     field) yet inflate the catalog with rows that are not distinct degrees. Collapse
     them into ONE program carrying the concentrations as `tracks`, keeping only
     genuinely separate credentials (a real PhD, MS, professional master's) as their
     own rows. Likewise never let `program_name` and `degree_type` disagree (a
     `bachelors` row whose name embeds "EdM"/"MS"). Evidence: live API this run — one
     483-row catalog had ~200 such "— {concentration}" split rows plus
     credential/degree-type mismatches.
   - **`department` must be the institution's REAL owning unit, NOT the federal
     CIP taxonomy title or a credential (issue: department padding that EVADES the
     null/"Programs"/duplicate-name checks).** A live-fleet repair variant "fixes"
     the null-department gap by copying the verbatim **CIP category name** into
     `department` — verbose federal taxonomy strings the institution never uses,
     e.g. "Communication Disorders Sciences and Services", "Radio, Television, and
     Digital Communication", "Area Studies", "Air Transportation" — producing a
     non-functional grouping where nearly every program is its own one-off
     "department" (live API this run: a repaired 310-program catalog had ~150 such
     CIP-title "departments"; another stored a bare credential "MPH"/"Mph" 14× and
     mechanically title-cased tokens like "School Of Music"/"Mathematics
     Statistics"). `department` must name the real school/college/department the
     institution itself publishes — "Harvard Business School", "College of Liberal
     Arts", "Department of Anthropology" (the gold model this run: one catalog
     correctly grouped 28 programs under "Harvard Business School"). A clean
     real department name that happens to match the field ("Economics",
     "Computer Science") is fine; the defect is the **verbatim CIP taxonomy
     phrase**, a **degree/credential abbreviation** ("MPH"/"MS"/"PhD"), or a
     **mechanically title-cased raw token** standing in for a real unit. If you
     cannot verify the real owning unit, the existing never-null/verify-output
     rule still applies — resolve it, don't paper over it with a CIP/credential
     placeholder, which is the program-name padding wearing a department costume.
     **The field-name blessing above holds ONLY for a genuinely SHARED real
     department — when `department` is set to the row's OWN `program_name`
     VERBATIM on (near-)every row (one-off per program catalog-wide, so no two
     programs share a department) WHILE a real owning school IS known (a
     `school_key`, or the school named in that row's own description), that is NOT
     a real unit: it is the field name standing in for the school, and it EVADES
     every dept check above precisely because it "matches the field." The tell is
     mechanical: `department == program_name` on ~all rows / no two programs share
     a department / a real school is available but unused. Put the institution's
     real published owning school/college/department in `department`, never the
     field echoed from the name. Evidence: live API this run — a freshly-"repaired"
     613-program catalog set `department == program_name` on 98% (601/613), the
     real owning school named ONLY in the description (its build kept the real
     `school_key` but copied the field into `department`).**
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
   - **STRUCTURE-BEFORE-DEPTH gate — NEVER run a reviews (or photo) depth pass on a
     catalog that still carries fabricated rows. This is the dominant regression this
     run.** A review is valuable ONLY on a REAL program. A review attached to a
     CIP-rollup row ("Bachelor's in Business/Commerce, General"), a concentration-split
     row, or a bare stub is wasted AND harmful: it lends a fabricated program false
     third-party credibility, and it is THROWN AWAY the moment that row is
     de-fabricated or dropped (you pay for the same work twice). So within ONE catalog
     the order is strict and non-negotiable: **(1) de-fabricate the whole catalog's
     STRUCTURE first** — real per-field degree names, real owning departments,
     concentration splits collapsed into `tracks` (miss #2), no CIP-rollup names/
     departments left anywhere; **(2) THEN** run the reviews depth pass over the
     now-real programs; **(3) THEN** move to the next university. A reviews/photo pass
     shipped while ANY row in that catalog is still a CIP-rollup / concentration-split /
     stub is itself a **DEFECT** — it does not count as progress and must not be
     shipped. (Repair-first, step 2, still forbids moving to a NEW university while
     this one's real programs lack reviews — structure-then-reviews-then-next is the
     full order, not reviews-skipping-structure.) Evidence: live API this run — every
     one of the ~16 PRs since the prior grading was a reviews-depth or gallery pass on
     catalogs whose CIP-rollup density is UNCHANGED (Northwestern 43%, JHU 38%, UCSD
     39%, Harvard 35%), and fabricated rows like Northwestern's "Bachelor's in
     Architecture and Related Services, Other" now carry `external_reviews` while their
     names/departments/template descriptions remain pure CIP-rollup fabrication.
   - **A review must be GATHERED program-specific coverage, NOT SYNTHESIZED from the
     row's metadata + generic institution facts — "fabrication-by-synthesis" is the
     live reviews-pass defect this run, and the false "aggregated from public sources"
     disclaimer makes it WORSE than an honest blank.** A pass that mints a review for
     EVERY row in one sweep is the tell: the reviews are machine-written from
     `(program_name, school, institution rank)`, not read off real third-party coverage
     of that program. Any one of these fingerprints is a FAIL: the SUMMARY or a theme
     embeds the federal CIP rollup the row was minted from ("Students describe
     Northwestern's program in *Architecture and Related Services, Other*…") — proof it
     was generated from the metadata, not gathered; the THEMES are all institution-level
     ("U.S. News ranks {Univ} #7 among national universities") with nothing
     program-specific; the SAME caution ("large introductory sections") is copy-pasted
     across many rows; a SOURCE is the generic university Niche page / the department
     homepage / an institution ranking rather than program-specific coverage, or is a
     mismatched-level ranking (a GRADUATE architecture ranking cited on a BACHELOR'S
     row). Such a review is fabrication wearing the MBAn shape — it lends the row false
     third-party credibility and is discarded the moment the row is de-fabricated. A
     review ships ONLY when it is read off coverage ABOUT THAT PROGRAM (a program page
     on Poets&Quants / U.S. News / GradReports, program-specific outcomes reports or
     forum threads), is program-specific in summary AND themes AND sources, and carries
     NO CIP-rollup string. If no program-specific coverage exists, OMIT with reason —
     never synthesize one. Evidence: live API this run — a "58/58 coverable reviews"
     one-pass depth had 43 of 60 reviewed rows carrying a CIP rollup verbatim in the
     summary, institution-level-only themes, and a graduate-ranking source on a
     bachelor's row.
   - **The TEMPLATE-DESCRIPTION stub is its own fabricated-row class — a real-looking
     `program_name` and a real `department` do NOT redeem it, and it is the BROADEST
     fingerprint of an un-researched catalog. Rank and gate catalogs by
     template-description SHARE, not just rollup-NAME share.** The gate above keys on
     the CIP-rollup NAME, but the dominant live tell is the DESCRIPTION: a pure
     degree-type template `"{program_name} is an undergraduate|graduate program at
     {Univ}'s {school}, offered through the {field}."` — note the grammatically-broken
     definite article before a bare field ("…offered through the Anthropology") that no
     real catalog prints. A row carrying that description was minted from an IPEDS/CIP
     list, not researched: every rich field is empty (curriculum, admissions, costs,
     outcomes, class_profile, faculty_contacts, external_reviews) and `_standard` is
     usually unstamped — so it is a STUB even when its name is a real degree
     designation ("Bachelor of Arts in Anthropology") and its department is the real
     unit. Rollup-NAME density UNDERCOUNTS this: the two metrics diverge widely, so a
     catalog can read "clean by name" while most of it is template stubs — classify and
     repair by template-description share. A reviews/photo depth pass on a
     template-stub row is the same wasted, harmful work this gate forbids; de-fabricate
     the row (research real field-specific basics + content, or omit it) BEFORE any
     depth pass. Evidence: live API this run — two catalogs with near-zero rollup names
     ran 40% / 66% template stubs yet were graded "clean," and a freshly-"reviewed" row
     carried `external_reviews` while every other field was empty and `_standard` was
     unstamped; the only genuinely clean enriched catalogs carry ZERO template
     descriptions.
   - **The template fingerprint is the FORM, not any fixed string — every "structural
     repair" so far has merely REWORDED the template past the previous check, and the
     reworded form even slipped past this grader's own prior "clean" call. NEVER gate on
     one template string; gate on the GOLD CONTRAST.** A description is a content-free
     stub whenever it only CLASSIFIES the program — states its credential level and its
     owning school/college and swaps in the field name — without a single concrete clause
     about what the program actually studies or does. The exact wording is a moving
     target and chasing it is futile: `"{field} — a {Univ} {degree} program offered
     through {school}"`, `"{name} … offered through the {field}"`, `"{name} is an
     undergraduate major at {Univ}'s {College}"`, `"{name} is an undergraduate major in
     {field} at {Univ}'s {College}"`, and `"{field} is a undergraduate bachelor's degree
     in {School} within {Univ}'s {College}"` are ALL the SAME stub. The durable test is
     the gold contrast: every gold MIT description states something concrete and specific
     about the field ("Course 16 educates engineers of aerospace vehicles, autonomy, and
     space systems … close ties to Lincoln Laboratory"; "Course 4 combines design
     studios, history and theory, and building technology in the oldest architecture
     program in the U.S."), so a description that could be generated from
     `(program_name, degree_type, school)` ALONE — carrying no fact you couldn't infer
     from those three — is a stub regardless of wording. Such a row also has its rich
     fields empty (`tracks`/`who_its_for`/`class_profile`/`faculty_contacts`/
     `external_reviews`) and `_standard` usually unstamped; a depth pass on it is the
     same wasted, harmful work the structure-before-depth gate forbids. Evidence: live
     API this run — the three post-run-5 "structural repairs" each only reworded the
     template or layered reviews while leaving the descriptions pure classification
     (one rewrote 299 old-form rows to a NEW classification form and left every deep
     field empty); the UNION pure-classification share is 62–100% on EVERY enriched
     catalog, INCLUDING the two run-5 flagged "clean" (100% and 81%). MIT is the ONLY
     catalog whose descriptions are field-specific.
   - **Real NAMES + real DEPARTMENTS are NECESSARY but NOT SUFFICIENT — a
     "de-fabrication" pass that fixes the names and the departments but leaves the
     DESCRIPTION a classification stub and the program-specific deep fields empty has
     NOT cleared the catalog. This is the live evasion this run.** The
     structure-before-depth gate above enumerates step (1) as "real per-field degree
     names, real owning departments, concentration splits collapsed" — and the enricher
     now COMPLETES exactly that enumeration (real names like "Bachelor of Arts in
     Anthropology", real departments like "Department of Anthropology", no CIP-rollup
     names left) while STILL shipping content-free classification descriptions, every
     program-specific deep field empty (`who_its_for`/`class_profile`/`tracks`/
     `faculty_contacts`/`external_reviews` all null), and `_standard` UNSTAMPED — then
     treats the catalog as structurally de-fabricated. It is NOT. Step (1) is cleared
     only when, in addition to real names + real departments + collapsed splits, EVERY
     row carries a field-specific description (passes the gold contrast above) AND
     researched per-program content (deep fields filled, or each honestly recorded in
     that row's `_standard.omitted`) AND a `_standard` stamp. Fixing the structural
     SHELL (names/departments) without researching the CONTENT is the same un-researched
     stub wearing a cleaner costume — it does not count as de-fabrication and must not be
     shipped as "done". Evidence: live API this run — four 2026-06-16 "de-fabricate IPEDS
     catalog … to real names" PRs (UCSD, Northwestern, JHU, UW-Madison) each gave real
     degree names + real `Department of {field}` departments yet left ~99–100%
     classification descriptions, all deep fields null, and `_standard` unstamped.
   - **The clear bar is DIMENSION-AGNOSTIC and SIMULTANEOUS — a single-dimension pass is
     NOT a clear in EITHER direction. The recurring root cause across every interval is
     the enricher fixing ONE fabrication dimension per pass and shipping the catalog as
     "repaired."** The prior sub-bullet caught the names+departments-fixed-but-description-
     and-content-NOT direction; the live fleet now shows the INVERSE too — a field-specific-
     DESCRIPTION pass shipped on top of un-de-rolled-up CIP-rollup NAMES with the rollup
     echoed verbatim in `department` (live API this run: two catalogs at 37% and 28%
     "{credential} in {CIP rollup}" rows — names like "Bachelor's in Biomedical/Medical
     Engineering" / "Bachelor's in Accounting and Related Services", dept = the same rollup
     — now wearing genuinely field-specific descriptions on top), while two OTHER catalogs
     are the exact opposite (real de-rolled-up names + real departments, descriptions still
     pure "{name} is an undergraduate major at {Univ}'s {school}" classification). NEITHER
     is a clear. A catalog is cleared ONLY when EVERY row SIMULTANEOUSLY satisfies ALL of:
     (a) a real degree name with NO rollup tell (no ", General"/", Other", no federal
     comma-and list, no embedded slash), (b) a real owning department (NOT the CIP rollup
     echoed back), (c) concentration splits collapsed into `tracks`, (d) a field-specific
     description passing the gold contrast, AND (e) researched per-program deep content
     (cost / outcomes / class_profile / faculty / tracks / reviews filled, or each honestly
     omitted). Fixing whichever single dimension is cheapest and shipping is partial work,
     not a repair — finish ALL dimensions on a catalog before declaring it done. The only
     genuinely real catalogs (beyond gold MIT) are the ones where real names + real
     departments + field-specific descriptions hold ALL TOGETHER, not one without the
     others. Evidence: live API this run — description-only and names-only single-dimension
     passes were each shipped as "repairs" on opposite catalogs; the catalogs clean on
     names still run classification/old-template descriptions, and the catalogs with
     field-specific descriptions still run 28–37% CIP-rollup names.
   - **A field-specific description must be VERIFIED-TRUE, not merely specific-SOUNDING — a
     depth pass that INVENTS a concrete fact (a named school/college/center/institute/lab, or
     a ranking/superlative) to satisfy the gold contrast is fabrication-by-synthesis on the
     DESCRIPTION dimension, and a confidently-WRONG specific is WORSE than an honest generic
     gloss because it reads authoritative. This is the live regression this run.** The
     gold-contrast rule above demands a concrete field-specific fact; this rule guards its
     TRUTH — the two are necessary together. The dominant tell: the named unit belongs to a
     DIFFERENT (peer) institution — a "College of Chemistry"-style college or a named
     aerospace "school" minted onto a program at a university that has NO such unit — OR a
     REAL same-institution unit is bolted onto an UNRELATED field (an international-affairs
     institute cited on a public-relations master's). Both are the SAME defect as the reviews
     fabrication-by-synthesis above: specificity generated from a template + plausible-sounding
     institutional trivia, not read off the program's real catalog/department page. So any
     named school/college/department/center/institute/lab in a description MUST (a) be a unit
     THIS institution actually has (verify against its official org/academics page) and (b)
     actually house THIS program; any ranking/superlative ("the nation's first", "top-ranked")
     MUST be cited. A reliable synthesis tell is the SAME wrong unit copied verbatim across
     every credential level of one field (certificate + bachelor's + master's all naming the
     identical fabricated college). Verify the named entity or write a true generic clause —
     never invent a specific to pass the gold contrast. Evidence: live API this run — a
     freshly description-passed catalog attached two different peer institutions' named
     colleges/schools to its own chemistry- and aerospace-engineering rows (the unit names
     belong to peer universities, not this one) and repeated each across all three credential
     levels of the field.
   - **A "field-specific description" pass that COPIES a PEER (earlier-enriched) institution's
     description and find-replaces only the institution/campus token is
     fabrication-by-cross-institution-templating — and it leaves three tells the named-unit-truth
     scan above MISSES. This is the live regression this run.** When the enricher reuses another
     university's verified description as a template and swaps the campus name but not the body,
     the result reads field-specific and confident yet is FALSE for THIS institution in ways a
     single-unit truth check does not catch: (a) a peer's GEOGRAPHY / place-name survives ("…and
     Chesapeake regional research sites" on a landlocked inland university), which the named-unit
     scan ignores because a region is not an academic unit; (b) a peer's signature UNIT survives
     ("at SAS", "Wharton accounting", "CALS animal science", "the Writing Seminars" on a school
     that has none) — already forbidden by the named-unit-truth rule above, but a CONSTELLATION of
     ONE peer's marks repeated across many rows is the diagnostic that the whole description was
     copied, not merely that one unit was mis-cited; and (c) most deceptively, a real peer
     LANDMARK is mechanically RE-LABELED with this institution's name ("Cornell Lab of
     Ornithology" → "{This} Lab of Ornithology", "Hopkins Review" → "{This} Review", "Weill
     Cornell" → "Weill {This}…academic medical center" on a school with no medical center) — this
     PASSES a naive "is this institution named?" check because the institution IS named, yet the
     entity it is glued to belongs to a peer and does not exist here. So the verified-true gate
     must ALSO (i) scan every description for a GEOGRAPHY / place-name that contradicts the
     institution's real location, (ii) scan for known peer-institution signature strings
     REGARDLESS of whether this institution is also named, and (iii) reject a real peer landmark
     wearing this institution's name. The repair is to RESEARCH each program's description from
     THIS institution's own catalog/department page — never adapt a peer's description by
     find-replace. Evidence: live API this run — a freshly description-passed catalog carried ~11%
     of rows importing another university's signatures (a JHU region + JHU's Writing Seminars,
     Penn's SAS / Wharton / Perelman, Cornell's CALS / Weill, Northwestern's McCormick) plus
     re-labeled peer landmarks ("{This} Lab of Ornithology", "{This} Review"); a second
     description-passed catalog carried ~2% (a peer's observatory + business school + another
     peer's name on unrelated rows), confirming the cross-institution-copy mechanism is a CLASS,
     not one catalog.
   - **ONE field's description STAMPED VERBATIM across every credential-level row of that field is
     field-LEVEL, not program-LEVEL — a per-FIELD generation tell that EVADES both the
     duplicate-NAME check (the names differ — the credential is in the name) AND the gold contrast
     (the prose is genuinely field-specific). This is the live regression this run.** When a
     description is generated once per FIELD (e.g. from a fixed field→description table) and applied
     to every row of that field, the Graduate Certificate, BS, MS, and PhD in ONE field all carry an
     IDENTICAL `description_text` — so a student sees the SAME paragraph on the MS page and the PhD
     page, and the row was minted per-FIELD, never researched per-PROGRAM (the depth pass the
     standard demands). It slips past every prior check because the names are now distinct (the
     credential is IN the name, miss #2) and the prose is field-specific (it passes the gold
     contrast) — yet it is the DESCRIPTION analog of the CIP×award-level / duplicate-name padding:
     one artifact reused across credentials. The gold contrast is decisive — gold MIT gives EVERY
     one of its 65 programs a UNIQUE description (0% shared), because a real BS, MS, and PhD in one
     field study different things (an undergraduate survey vs doctoral research) and a researched
     description says so. So a `description_text` shared verbatim by ≥2 rows is a FAIL: write each
     credential-level row its OWN researched description (what THAT degree studies, at THAT level),
     or recognise the rows as the same minting defect wearing distinct names. Count `description_text`
     shared across rows (gold MIT = 0%); a high share means field-level, not per-program, descriptions.
     Evidence: live API this run — a 348-row catalog had 293 rows (84%) sharing a description verbatim
     across the credential levels of one field (one field's text on its certificate + BS + MS + PhD),
     vs gold MIT 0%.
     - **A PREFIX-STRIP pass is a common SOURCE of this class, NOT a safe isolated fix — when the rows
       of one field differed ONLY by a leading `"{program_name}: "` / `"{program_name} is "` prefix,
       DELETING that prefix collapses their bodies to IDENTICAL across credential levels, trading
       prefix-doubling (miss #9) for identical-across-levels — the enricher's DOMINANT pass keeps
       manufacturing this. This is the live regression this run.** The prefix is often the ONLY per-row
       differentiator on a field-level-generated catalog, so a pass that "fixes" prefix-doubling by
       stripping the name and nothing else converts a prefix-doubled catalog straight into an
       identical-across-levels one — defect-for-defect, no per-program research added. So a prefix-strip
       is NOT done when the prefix is gone: after ANY prefix-strip, RE-COUNT `description_text` shared
       verbatim across ≥2 rows and FAIL on any sharing (gold MIT 0%); a clean prefix-strip must leave
       each credential-level row its OWN distinct researched body (what THAT degree studies at THAT
       level), never one field's text stamped on all its levels. Evidence: live API this run — a 308-row
       catalog whose prefix-strip took name-prefix 97%→0% SIMULTANEOUSLY produced 83% identical-across-
       levels descriptions (one field's Graduate Certificate + MS sharing verbatim text, the MS body even
       reading "undergraduate research in robotics labs" — a credential-level lie copied onto a master's
       row).
     - **The shared-BODY count must catch the SUFFIX-DIVERSIFIER evasion — appending a generic
       per-credential SUFFIX onto a SHARED field body defeats the verbatim-FULL-STRING count above
       (it reads 0%) while the researched body is STILL stamped identically across the credential
       levels. This is the live regression this run, and it evaded BOTH the enricher's build gate AND
       this grader's own verbatim check.** The "diversify + gate" repair (the dominant pass now) keeps
       one field's researched opening identical across its certificate/bachelor's/master's/PhD rows and
       appends a reusable boilerplate sentence keyed only on the CREDENTIAL ("The graduate certificate
       offers focused graduate coursework for working professionals…" / "Master's students complete
       advanced seminars, practica, and professional development…") — so the FULL `description_text`
       strings differ (verbatim-shared = 0%) yet a student reads the SAME field paragraph on the MS and
       the PhD page, with only a generic per-level tag swapped. That generic suffix is NOT per-program
       research: it is field-agnostic (the identical certificate sentence fits every field's certificate),
       so the row was minted per-FIELD, never researched per-PROGRAM — the run-30 defect wearing a
       suffix costume. So the identical-across-levels count must measure the SHARED LEADING BODY across
       a field's credential siblings, NOT just full-string equality: for each field (program_name minus
       its credential designation) with ≥2 rows, compute the common description prefix; FAIL the field
       when that shared prefix is a large fraction of the shortest sibling (e.g. ≥120 chars AND ≥50% of
       the shortest) — gold MIT = 0% of multi-credential fields (its BS-Chemistry "covers organic,
       inorganic, physical, and biological chemistry, with extensive undergraduate research" vs its
       PhD-Chemistry "doctoral research across the chemical sciences. Funded." share NO body). A clean
       diversification gives each credential level its OWN researched body (what THAT degree studies at
       THAT level), not a shared body + a generic credential tag. Evidence: live API this run — the three
       "diversify + gate" passes graded "0% identical-across-levels" by the verbatim count (Columbia #684,
       Stanford #681, Harvard #679) actually share their full researched opening across 81% / 89% / 82%
       of their multi-credential fields, vs gold MIT 0%.
     - **A leading per-CREDENTIAL FRAME sentence prepended onto a shared field body RELOCATES the run-38
       per-field stamp into the description TAIL, where the leading-PREFIX shared-body count (the prior
       sub-bullet) reads 0 — the live evasion this run, manufactured by the very "per-credential
       descriptions" passes meant to FIX the leading-body stamp.** The dominant "repair" pass now OPENS
       each row with a credential-keyed frame generated from `(degree_type, field)` —
       `"{Univ} offers the undergraduate major in {field}."` / `"{Univ} offers a master's program in
       {field}."` / `"Master's students in {field} complete graduate seminars, research methods, and a
       thesis project —"` / `"Doctoral study in {field} at {Univ} centers on dissertation research in"` / a
       bare `"Graduate study."` / `"Graduate certificate."` tag, or a generic textbook DEFINITION of the
       field (`"{Field} is the study/science of …"`) — and then appends ONE field body STILL identical
       across that field's credential siblings (the BA, MS, and PhD in one field share the same researched
       sentence). Because the frames DIFFER by credential, the common LEADING prefix across the siblings is
       tiny, so the prior sub-bullet's prefix count reads 0 and the catalog looks fixed — while a student
       still reads the SAME field paragraph on the bachelor's AND the master's AND the PhD page (gold MIT
       gives every credential level its OWN body, 0% shared even after frame-strip). The frame is the
       run-30 prefix-strip / run-38 suffix-diversifier mechanism wearing a credential-FRAME costume: it is
       field-agnostic boilerplate, not per-program research. So the shared-body count must (a) STRIP a
       leading credential-frame / degree-classification / field-definition sentence from every description
       FIRST, then (b) measure the shared body across a field's credential siblings ANYWHERE in the
       description (longest common substring, NOT only the leading prefix), and FAIL when it is ≥80 chars
       AND ≥50% of the shortest sibling. A "per-credential descriptions" pass is done only when each
       credential level carries its OWN researched body (what THAT degree studies at THAT level), not one
       field body behind a swapped credential frame; a generic field DEFINITION (true of the field at every
       institution, derivable from the field name) is itself a gold-contrast STUB even when paired with a
       real classification clause. Evidence: live API this run — freshly-shipped, already-deployed
       "per-credential descriptions" repair passes that took the run-64 shared-LEADING-body to 0 (and so
       read "fixed") still stamp ONE field body across 88–100% of their multi-credential fields once the
       leading credential frame is stripped (one field's "{field} spans/combines/covers …" sentence on its
       bachelor's AND master's AND PhD), vs gold MIT 0%; the broken splice the frame leaves ("…centers on
       dissertation research in {field} spans …", a bare "{College} foundations in … with …" fragment) is
       the corroborating tell.
     - **The `AND ≥50% of the shortest sibling` FRACTION FLOOR on the shared-body count is ITSELF the next
       loophole — PADDING each credential row with a long UNIQUE per-credential TAIL dilutes a still-IDENTICAL
       leading SENTENCE below 50% of the now-long description, so the LCS-anywhere count reads a false 0 again.
       This is the live evasion this run, manufactured by the very "per-credential bodies" passes meant to FIX
       the frame+tail-share.** A 150+ character identical run across a field's BA / MS / PhD is a STAMPED
       SENTENCE — never a coincidence — so the fraction floor (an anti-coincidence guard meant to spare a short
       shared clause) must NOT exempt it: the "repair" keeps one researched field sentence verbatim across the
       credential siblings and simply appends enough distinct per-credential filler that the shared run, though
       160–220 chars in ABSOLUTE terms, is only ~30% of each padded body — under the 50% floor — and the
       grader/CI metric clears it. A student STILL reads the identical opening sentence on the bachelor's AND
       the master's AND the PhD page (gold MIT 0% — every credential level its OWN body). So the frame-stripped
       shared-body count must FAIL when the longest common substring across a field's credential siblings is
       **≥80 chars AND ≥50% of the shortest sibling, OR ≥150 chars in ABSOLUTE terms regardless of fraction**
       (a full stamped sentence); the clean fleet's per-credential-distinct catalogs top out well below this
       (gold MIT, Duke, Rice, Purdue, UCSD all <150-char max shared run), so the absolute floor separates them
       from the diluted-tail evasion cleanly. A "per-credential bodies" pass is done only when each credential
       level's researched body shares NO sentence with its siblings — not when a padded tail drops the shared
       sentence under an arbitrary fraction. Evidence: live API this run — four freshly-shipped, already-deployed
       "per-credential bodies" repair passes (UW-Madison, Florida, Cornell, Boston U) that took the run-66
       LCS-anywhere ≥50%-floor metric to 0 (and so read "fixed") still stamp ONE field sentence across their
       credential siblings — UW–Madison's Anthropology BA / Graduate Certificate / MS all open on the identical
       162–166-char "Madison campus anthropology combines archaeological fieldwork, medical anthropology, and
       sociocultural theory…" (30% of each ~540–617-char body); Florida's Biology BA / MS share an identical
       160-char generic field-definition sentence (31%) — vs gold MIT 0%, where re-measuring with the absolute
       floor restores 75 / 54 / 44 / 23 flagged fields respectively.
   - **ONE SCHOOL's blurb STAMPED across MANY DIFFERENT FIELDS is the SCHOOL-LEVEL analog of the
     per-field stamping above — and it EVADES the field-keyed shared-body count (which compares only a
     field's credential siblings, NEVER two DIFFERENT fields). This is the live regression this run.**
     When a catalog's descriptions are assembled from a small set of SCHOOL-level blurbs — one paragraph
     per college dropped into a fixed frame, `"{Univ}'s {field} program connects to {SCHOOL blurb}.
     Students build depth in {field} through …"`, whose ONLY per-row token is the field name — every
     program of one school carries the IDENTICAL substantive sentence across DIFFERENT fields (the
     engineering blurb on aerospace AND civil AND computer science; the arts-and-sciences blurb on
     economics AND history AND biology). It passes the classification regex (no "offered through"), the
     prefix-doubling check (it opens on the institution, not the `program_name`), AND the run-38
     field-keyed shared-body count (those rows are different FIELDS, so the field-keyed grouping never
     compares them) — yet it is the SAME not-researched-per-program defect at a COARSER grain: the
     substance is school-level, only the field name is per-row, so it is a gold-contrast STUB (generated
     from `(field, school)` alone). Two tells confirm the machine frame: a UNIVERSAL field-agnostic
     CLOSING sentence appended to every row ("Students build depth in {field} through seminars, research,
     and {city} industry and community partnerships") and GRAMMATICAL breakage from splicing a
     full-sentence blurb into the frame (a double period "..", a "connects to {a complete sentence}"
     splice). So the shared-body count must run CATALOG-WIDE across ALL programs — extract each
     description's substantive clause and FAIL when one clause is shared verbatim across rows of ≥2
     DIFFERENT fields, NOT only within a field's credential siblings (gold MIT = every program uniquely
     described, 0 cross-field sharing). Write each program what THAT program actually studies, never a
     per-school blurb with the field name swapped in. Evidence: live API this run — a 481-field
     description pass used only 18 distinct school-blurbs to cover 461 fields (95%) — one blurb on 124
     different fields, another on 80, another on 38 — with the universal "Students build depth in
     {field}…" closing on 100% of rows and the double-period ".." breakage on 95%.
   - **A description must be RESEARCHED PROSE ABOUT THE PROGRAM — FAIL any description
     that is a BUILD-ARTIFACT ASSEMBLY (a debug/ingest token + a school-division frame
     + scraped namesake text), the live regression this run AND the most dangerous one
     because a per-row id NONCE makes every row's text unique and thereby ZEROES every
     anti_stub verbatim / shared-body / cross-field metric — it evaded BOTH the CI gate
     AND this grader's own prior "win/clean" call.** A "de-fabrication" pass that fails
     to actually research the catalog can emit, instead of one shared stub, a per-row
     MACHINE ASSEMBLY of three parts — and because the id differs per row, no two
     descriptions are byte-equal, so the entire shared-text gate reads 0 (the rows look
     "uniquely described" while not one was researched). Any of these three tells is a
     hard FAIL, independent of every form/share metric:
     (a) a LEADING INTERNAL TOKEN — `"Catalog entry <hex/uuid>:"` (frequently DOUBLED:
       `"Catalog entry 5686…: Catalog entry 5686…:"`), a bare UUID/hash, **a leading
       kebab-case URL SLUG** (`"usc-american-studies-and-ethnicity-ba — …"`,
       `"anthropology-classical-civilization — …"`, `"uiuc-agricultural-biological-
       engineering-bs — …"`), or any ingest/database id. No real catalog prints a row
       id — or its catalog/URL slug — in a degree description; a leading id/slug is a
       build artifact leaked to the live page, and (being a per-row token) it is ALSO
       the gate-evasion that hides parts (b)/(c) from the share count. **The URL-slug
       form is the live tell THIS run, and it is MORE dangerous than the hex nonce
       because it is human-readable and passes the hex-keyed `machine_artifacts` gate
       untouched: it carries no "Catalog entry" string and no a-f+digit hex run, so the
       built `_ARTIFACT_RES` returns 0 on it while it ships live — observed on
       CERTIFIED_CLEAN catalogs (a 19%-of-rows / 8% / 8% slug-prefix leak across three
       certified catalogs, 0 of them caught by `machine_artifacts`). Treat a leading
       kebab slug exactly like the hex nonce: STRIP it before the share counts and FAIL
       on it.**
     (b) a SCHOOL/DIVISION TEMPLATE FRAME — `"{Univ}'s {School} draws on {Department/
       Division of X} for coursework and research on the {city} campus. Published through
       {Univ}'s {School} on the {city} campus."` — pure classification boilerplate (the
       run-43 school-blurb wearing a new costume; it adds no fact you couldn't infer from
       `(school, field)`), and it routinely carries the run-25 GEOGRAPHY lie (every UW row
       ends "on the **Westwood** campus" — Westwood is a PEER's campus, not UW's).
     (c) a NAMESAKE SCRAPE — a paragraph about a DIFFERENT real-world entity that merely
       shares the program's name: a journal ("…is a peer-reviewed scientific journal …
       published by EDP Sciences"), a Wikipedia survey/definition ("Ethnic studies … is
       the study of difference"), or a list article ("The following list features women
       …") — often TRUNCATED MID-WORD ("hly peer-reviewed"), proof it was scraped by name,
       not read off the program page. This is fabrication-by-name-collision: confidently
       WRONG content (an Astronomy M.A.T. described as a journal's editorial board).
     The repair is the same as every de-fabrication: research each description from THIS
     institution's OWN catalog/department page, one paragraph per PROGRAM. The pre-ship
     scan (miss #9) must STRIP any leading id-token/nonce BEFORE recomputing the
     verbatim/shared-body counts (or the nonce hides the stamp) AND fail outright on the
     id-token, the division-frame boilerplate, and a namesake-scrape — none of which the
     description-FORM metrics see. **A catalog carrying this form is NOT clean even at 0
     on every existing anti_stub metric, so it must NOT be trusted as CERTIFIED_CLEAN
     until the analyzer gains a nonce-strip + id-token/division-frame/namesake metric**
     (that lives in `profile_standard/anti_stub.py` + `test_anti_stub_gate.py`, app/test
     code the grader does not edit — FLAG it for a human). Evidence: live API this run —
     three #766/#770/#790 "de-fabricate" PRs that auto-merged green and joined
     CERTIFIED_CLEAN ship this assembly on ~98% of rows (UCLA 364/373, UW 350/365, Michigan
     374/379 carry the "Catalog entry <hex>:" prefix — UW 316 of them DOUBLED — plus the
     division frame and the Westwood-campus geography lie), while UT-Austin #768 / NYU #753
     / UIUC #763 in the SAME interval de-fabricated genuinely (0 artifacts) — so this is one
     broken pass's class, not the only repair model.
   - **A description that is RAW SCRAPED CATALOG DEBRIS — a degree-REQUIREMENTS / course-list
     fragment, a capstone-options list, a unit-count opening, or a CONTACT/ADDRESS block — is an
     un-researched stub EVEN THOUGH it is unique per row (so it ZEROES every share metric, like the
     per-row id nonce) AND field-ish enough to slip past the gold-contrast classification test. This
     is the live regression this run.** A scrape-built catalog that was never researched can fill
     `description_text` not with one shared stub but with whatever text sat on the program's catalog
     page: a degree-requirements excerpt ("28 additional units must be selected from MATH 225, MATH
     226, or any upper-division course…"; "Four MATH courses at the 400-level or above are required,
     chosen from the following list:"), a capstone/option list, a total-unit count as the opening
     clause, or even the department's mailing ADDRESS + phone + email ("… Stonier Hall, Suite 101 …
     (213) 740-1060 Email: …@….edu"). Because each fragment is unique, the verbatim / shared-body /
     cross-field counts ALL read 0 (the exact gate-evasion the per-row nonce uses), and because a
     requirements list is field-ish it also passes the classification / gold-contrast test — yet
     NONE of it is researched prose about what the program STUDIES, and it routinely (a) TRUNCATES
     mid-sentence / mid-list / on a trailing colon (no terminal period), proof it was scraped not
     written, and (b) is MISMATCHED to the WRONG program (an archaeology degree carrying another
     major's course requirements; a row whose body opens on a DIFFERENT field's name than the
     program's), which is confidently-WRONG content the student reads. Any one of these is a hard
     FAIL independent of every share/form metric: a course-code token ("MATH 225"), a unit/credit
     count as the opening clause, a trailing colon or mid-sentence truncation (no terminal "."), an
     address / phone / `@…edu`, or a body whose field does not match the `program_name`. Research
     each description from THIS institution's OWN program page as PROSE about the field; never drop
     the raw catalog-page text into `description_text`. The pre-ship scan (miss #9 / §8.5) must add
     this scrape-debris tell — the form/share metrics are blind to it. Evidence: live API this run —
     the largest scrape-built catalogs ship this on up to ~10% of rows (≥50 on one ~520-program
     catalog, including a raw contact-address row and requirements fragments mismatched to the wrong
     program), every one scoring 0 on every existing description metric.
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
9. **VERIFY THE RENDERED OUTPUT, not just that a value was written — this is the
   common root cause of every miss above.** Writing a field is not the same as the
   field being correct on the page. Boston U's 483 "BA"/"MS" stubs and Stanford's
   dead Events tab both shipped because the routine set a value and moved on
   without looking at the result. Before declaring a node done, CHECK the actual
   output a student would see:
   - **Programs:** spot-check the program list — are names real and distinct (no
     `"BA"`-style stubs, no duplicate names, no `"Programs"` department, **no
     null/blank `department`, no `department` that is a verbatim federal CIP
     taxonomy phrase ("Communication Disorders Sciences and Services", "Area
     Studies") or a degree/credential abbreviation ("MPH"/"MS"), and no
     `"{field} — a {Univ} {degree_type} program offered through …"` template
     descriptions**)? A list with repeated generic names, blank departments, a
     department that is a CIP taxonomy phrase or a credential, or a description
     that only swaps the field into a degree-type sentence = not done — that is
     CIP×award-level padding (miss #2), not breadth. Run the catalog through this
     check programmatically (count duplicate `program_name`s, null `department`s,
     departments matching a CIP taxonomy phrase or a degree abbreviation, template
     descriptions, **`program_name`s of the form "{generic credential} in {CIP
     rollup}" — trailing ", General"/", Other", federal multi-clause comma-and
     lists, or embedded slashes — even when the department is now non-null**, and
     **`program_name`s or `department`s carrying a literal CIP CODE — a `(CIP
     <digits>)` suffix or bare trailing code — which a clean field text ("Psychology
     (CIP 42.99)") slips past the punctuation-keyed rollup scan above (miss #2)**, and
     **a high rate of "— {concentration}" rows that split one base degree**, and
     **the template-description SHARE — count pure-CLASSIFICATION descriptions in
     ANY wording, NOT one fixed string: the live form keeps changing to evade a
     literal-string check (`… offered through the {field}` → `{name} is an
     undergraduate major at {Univ}'s {College}` → `{field} is a undergraduate
     bachelor's degree in {School} within {Univ}'s {College}` are all the same
     stub), so key the count on the durable test instead — a description FAILS if it
     could be generated from `(program_name, degree_type, school)` alone (it only
     states the credential level + owning unit + swapped-in field and adds no
     field-specific fact, cf. gold MIT's "Course 16 educates engineers of aerospace
     vehicles…"). This SHARE is a PRIMARY independent FAIL: a high share means the
     catalog is mostly un-researched stubs even where the NAMES read real, confirmed
     by every rich field being empty and `_standard` unstamped on those rows**, and
     **identical `description_text` shared VERBATIM across ≥2 rows — one field's
     description stamped on every credential level (certificate/BS/MS/PhD), a per-FIELD
     generation tell that EVADES the distinct-NAME and gold-contrast checks (miss #8);
     gold MIT = 0% (every program uniquely described), so any verbatim-shared
     description is a FAIL — AND the count must measure the SHARED LEADING BODY across a
     field's credential siblings, not just full-string equality, or a generic
     per-credential SUFFIX appended onto a shared body evades it (verbatim-shared reads 0%
     while the researched opening is still stamped identically across the levels): for each
     field with ≥2 rows, compute the common description prefix and FAIL when it is ≥120 chars
     AND ≥50% of the shortest sibling (miss #8 suffix-diversifier sub-bullet) — **but FIRST strip a
     leading per-credential FRAME / degree-classification / field-definition sentence ("{Univ} offers
     the {undergraduate major/master's program} in {field}.", "Master's students in {field} complete
     graduate seminars, research methods, and a thesis project —", "Doctoral study in {field} at {Univ}
     centers on dissertation research in", a bare "Graduate study."/"Graduate certificate." tag, "{Field}
     is the study of …") and measure the shared body ANYWHERE in the siblings (longest common substring,
     FAIL at ≥80 chars AND ≥50% of the shortest, OR ≥150 chars in ABSOLUTE terms regardless of fraction — a
     padded unique per-credential TAIL otherwise dilutes a still-identical leading sentence below the 50%
     floor and the count reads a false 0 (miss #8 fraction-floor sub-bullet)), NOT only as a leading prefix —
     or a prepended credential frame pushes the still-shared field body into the TAIL and the prefix count
     reads 0 (miss #8
     credential-frame sub-bullet)**; **AND run that
     shared-body count CATALOG-WIDE across ALL programs, not only within a field — extract each
     description's substantive clause and FAIL when one clause is shared verbatim across rows of
     ≥2 DIFFERENT fields, the SCHOOL-level-blurb stamp that the field-keyed count misses (miss #8
     school-blurb sub-bullet); a universal field-agnostic closing sentence or a double-period ".."
     splice on most rows is the corroborating tell**) before
     shipping — a padded catalog must FAIL the run. **Also FAIL a catalog whose
     descriptions DOUBLE the page heading — i.e. begin by restating the `program_name`
     verbatim (a `"{program_name}: …"` or `"{program_name} is …"` prefix).** The program
     name is already the page heading, so a description that opens with it renders the
     name twice — a mechanical-generation tell that a "field-specific description" pass
     prepended the title rather than opening on a fact. Count
     `description_text.startswith(program_name)`; gold MIT opens on the field fact
     ("Course 16 educates engineers of aerospace vehicles…"), NEVER on its own title.
     Evidence: live API this run — the field-specific-description passes prefix the name
     in 82–100% of rows on every description-passed catalog (Cornell/Berkeley/Penn/CMU
     100%, Northwestern 97%, Harvard 82%), vs gold MIT 2%.
     - **Also FAIL the BUILD-ARTIFACT ASSEMBLY form (miss #8 build-artifact sub-bullet) —
       and STRIP its per-row id NONCE before the verbatim/shared-body counts above, or the
       nonce zeroes them.** Scan every `description_text` and FAIL on (i) a LEADING internal
       token — `"Catalog entry <hex/uuid>:"` (often DOUBLED), a bare UUID/hash, **a leading
       kebab-case URL slug (`^[a-z0-9]+(-[a-z0-9]+){2,}\s*[—–-]\s` — e.g.
       `"usc-american-studies-and-ethnicity-ba — …"`), which the hex-keyed gate MISSES**,
       any ingest id; (ii) the `"{Univ}'s {School} draws on {Dept/Division} for coursework and research
       on the {city} campus. Published through {Univ}'s {School} on the {city} campus."`
       division-frame boilerplate (a classification stub — also re-run the miss-#8 geography
       scan on its "{city} campus" tail); (iii) a NAMESAKE-SCRAPE paragraph (a journal /
       Wikipedia-survey / list about a different entity sharing the name, often truncated
       mid-word like "hly peer-reviewed"); (iv) RAW SCRAPED CATALOG DEBRIS — a degree-requirements /
       course-code list ("28 additional units must be selected from MATH 225…"), a capstone-options
       list, a unit-count opening, or a contact/address block ("… Suite 101 … (213) 740-1060 Email:
       …@….edu"); truncated mid-sentence / on a trailing colon, or MISMATCHED to the wrong program —
       unique per row, so it reads 0 on every share metric yet is an un-researched stub (miss #8
       scrape-debris sub-bullet). Because the leading id is a per-row nonce, the
       verbatim / shared-body / cross-field counts read 0 on this form while NOT ONE row was
       researched — so strip a leading `^Catalog entry [0-9a-f]+:\s*` (and any leading id
       token) from every description FIRST, then recompute those counts. Evidence: live API
       this run — UCLA/UW/Michigan ship this on ~98% of rows yet scored 0 on every existing
       metric and auto-merged into CERTIFIED_CLEAN.
     - **Also FAIL the TEMPLATE-SLOTTED per-credential body (miss #8 template-slot sub-bullet)
       — a per-credential "repair" that CLEARS the shared-body / frame / fraction-floor gate by
       giving each credential its OWN frame but SLOTTING the same field phrase into a fixed
       grammatical template, producing mechanically-assembled, broken prose.** Once siblings stop
       sharing a body, the next evasion is a fixed per-credential TEMPLATE with a variable
       slotted in ("{level-word} in {credential} in {field} centers on dissertation research in
       {field-phrase}, with qualifying examinations …", "Graduate coursework in {credential} in
       {field} emphasizes {field-phrase} …") — each body now DIFFERS, so it scores 0 on every
       share / frame / classification metric, yet renders machine junk. Scan every
       `description_text` and FAIL on the assembly tells, baselined to gold MIT 0: **(i)** the
       CREDENTIAL DOUBLED in the body — `"{level-word} in (the )?(Doctor of Philosophy|Master of
       …|Bachelor of …|Doctorate|Master's) (in|of) {field}"` — the degree designation is already
       the program_name heading, so re-naming it is a template artifact the
       `startswith(program_name)` doubling check (item 9) MISSES, because the body opens on the
       level-word, not the verbatim name; **(ii)** a DOUBLE / DANGLING preposition from an empty
       or mis-typed slot — `"research in of "`, `"research in for "`, `"\bin\s+(of|for|on|in)\s"`,
       `"\b(in|on|of)\s*\."` (preposition then period / comma — the slot came back empty);
       **(iii)** a CAPITALIZED field-FRAGMENT or method list jammed mid-sentence into a singular
       slot — a `[A-Z]`-initial noun phrase / comma list dropped after "research in {topic}"
       ("…research in Archaeological field schools, sociocultural ethnography, with qualifying…"),
       a capitalized phrase lifted from a field list reading ungrammatically where a topic noun
       belongs. A clean per-credential body is RESEARCHED prose about what THAT degree studies at
       THAT level (gold MIT), never a field phrase slotted into a frame. Evidence: live API +
       in-repo `PROGRAMS` this run — two just-merged "per-credential bodies" repairs cleared the
       shared-body count to 0 (the gate read them clean and they auto-merged, and a CONCURRENT
       grader graded them as clean wins) but shipped these tells on ~45% / a handful of rows — the
       natural successor evasion to the credential-frame + fraction-floor sub-bullets, gated the
       same way. **The enforced `anti_stub` gate now HAS this metric — `template_slot_artifacts`
       (the `_TEMPLATE_SLOT_RES` patterns) + a parametrized test — so the "run it by hand" era is
       over: a frame-share / "per-credential bodies" repair is NOT a clear until
       `template_slot_artifacts == 0` on that catalog, and clearing the shared-body count while
       LEAVING template-slot rows is the SAME single-dimension non-clear as every other one-dimension
       pass (miss #8 dimension-agnostic-and-simultaneous): the description repair that fixes the
       frame-share dimension routinely MANUFACTURES the template-slot dimension in the same edit, so
       the SAME pass that takes frame_abs150 → 0 must take `template_slot_artifacts` → 0 — **AND
       `scrape_debris` → 0 (see the next sub-bullet): the re-scan after a body rewrite is the FULL
       `anti_stub` suite, never just the one dimension you targeted** — and only
       then GRADUATE the catalog into the gate's `_TEMPLATE_SLOT_CLEAN` list. The fatal anti-pattern
       is shipping the frame-share fix while PARKING the catalog in the gate's EXCLUSION set
       (`_TEMPLATE_SLOT_CLEAN` is a subset of `CERTIFIED_CLEAN` minus the still-broken catalogs) —
       a parked catalog stays in `CERTIFIED_CLEAN` (so it reads "certified clean") while its
       template-slot rows ship live un-gated. Exclusion is a temporary parking lot for a KNOWN repair
       target, NEVER a destination: never ADD a catalog to the exclusion set to make a frame-share PR
       go green. Evidence: live API + in-repo `PROGRAMS` this run — Stanford's `#1021` "per-credential
       description bodies" repair cleared 51 frame-share fields → 0 but introduced 51
       `template_slot_artifacts` rows ("Graduate coursework in **the Master of Science in** {field}
       emphasizes {field-blurb}, with seminars, methods training, and a culminating thesis or capstone
       through {School}" — credential doubled + a universal field-agnostic tail), shipped live under
       its `CERTIFIED_CLEAN` membership because Stanford sits in the gate's exclusion set;
       UT-Austin (3, one PhD row slotting a *bachelor's* description fragment into "research in ___")
       and Michigan (1, empty slot "research in ,") are the same class still live.)
   - **A per-credential BODY REWRITE is itself a `scrape_debris` source — a hand-AUTHORED
     researched body shipped WITHOUT terminal punctuation (or left cut mid-clause) trips the
     debris TRUNCATION tell exactly like SCRAPED catalogue junk, so the post-rewrite re-scan
     MUST include `scrape_debris == 0`, not only frame + template-slot. This is the live
     regression this run, and it shows the per-credential-bodies pass manufacturing a NEW
     un-rescanned dimension for the THIRD interval running.** `scrape_debris` is wrongly
     assumed to fire only on SCRAPED text (course codes, unit/credit counts, phone/email
     contacts, mailing addresses) — but its terminal-punctuation tell (a description whose
     body, after stripping a trailing `(citation)`, does NOT end in `.`/`!`/`?` or ends on a
     `:`) fires on ANY description that does not END in a sentence terminator, INCLUDING a
     freshly authored per-credential body the enricher wrote by hand and forgot to terminate
     (or truncated mid-clause). So the dimension-agnostic-and-simultaneous rule (miss #8)
     extends to debris: the SAME "per-credential bodies" pass that takes frame_abs150 → 0
     and `template_slot_artifacts` → 0 must ALSO leave `scrape_debris` → 0; after ANY
     description rewrite re-run the FULL suite — `analyze` + `frame_stripped_shared_body
     (abs_chars=150)` + `template_slot_artifacts` + `scrape_debris` + `machine_artifacts` —
     and require EVERY one at 0 before graduating the catalog. Clearing the frame dimension
     while shipping 100+ un-terminated bodies is the same single-dimension non-clear as the
     frame-for-template-slot trade above, just on a different metric. A clean per-credential
     body is a COMPLETE researched sentence about what THAT degree studies at THAT level,
     ending in a terminator (gold MIT `scrape_debris` = 0). Evidence: live API this run — a
     just-merged "sibling-aware per-credential bodies" repair cleared a 237-program catalog's
     44 frame-share fields → 0 AND `template_slot_artifacts` → 0, yet shipped 115 of 237 rows
     (49%) tripping the debris truncation tell — genuinely field-specific bodies ("…the Dyson
     School's AACSB-accredited undergraduate business degree, grounded in applied economics",
     no terminal period), which shipped live because the catalog is absent from the gate's
     debris-clean `@parametrize` list (the same coverage drift as FLAG #1).
   - **Named units — scan EVERY description for a unit that doesn't belong, and a
     REPAIR must clear the WHOLE class, not just the cited row.** The miss-#8
     named-unit-truth defect (a description naming a school/college/department/
     center/institute/lab that is a PEER institution's unit, or a real
     same-institution unit bolted onto an UNRELATED field) must be part of the
     PRE-SHIP PROGRAMMATIC gate, not merely a per-row manual check: before shipping,
     scan every `description_text` and FAIL on any named unit this institution does
     not publish ("College of Chemistry"/"Sibley School" on a school that has
     neither) OR any real unit cited on a field it does not house (an
     international-studies institute on a marketing or systems-engineering row). And
     when a pass REPAIRS a flagged fabrication, it must **re-scan the whole catalog
     for EVERY instance of that class and get ZERO before shipping** — fixing only
     the row(s) the backlog named verbatim while sibling instances of the SAME class
     survive is a non-repair, not progress. Evidence: live API this run — a hotfix
     cleared the one cited "College of Chemistry" instance but a whole-catalog scan
     still returns "Sibley School" (a peer university's unit) on 2 aerospace rows and
     a real international-studies institute bolted onto a systems-engineering and a
     marketing row, all in the same just-"repaired" catalog. **This gate must ALSO
     catch the cross-institution-COPY tells (miss #8): a GEOGRAPHY / place-name that
     contradicts the institution's real location ("Chesapeake" on an inland campus), a
     known PEER signature string even when this institution is also named, and a real
     peer LANDMARK re-labeled with this institution's name ("{This} Lab of
     Ornithology") — a description copied from a peer catalog by find-replace reads
     "field-specific" and slips past the prefix/rollup/classification counts.**
     - **That gate must be a POSITIVE ALLOWLIST — verify each named academic unit
       against the institution's OWN published org chart — NOT a hardcoded DENYLIST of
       enumerated peer-unit strings, which is incomplete BY CONSTRUCTION and PASSES any
       foreign unit it does not list. A green peer-contamination gate / a "0% peer
       contamination" claim is therefore NOT evidence of zero foreign units when the
       gate is a denylist. This is the live evasion this run.** A repair that builds its
       peer gate from the SUBSET of peers a prior backlog happened to name will pass
       every un-enumerated peer unit straight through — including OTHER peer units the
       SAME backlog named elsewhere — so "the build gate is green" certifies only "none
       of the peers I thought to list survived," never "no foreign unit survived." Scan
       every named unit and FAIL unless it is one THIS institution actually publishes
       (the allowlist direction); do not trust a denylist that can only catch the peers
       someone thought to enumerate. Evidence: live API this run — a "clear peer
       contamination" pass whose denylist listed only the peer units earlier runs cited
       shipped THREE OTHER named peer units (a peer's engineering school on a data-science
       row, a peer's medical school on two medical-sciences rows, a peer's journalism
       school on a marketing/PR row — each named verbatim in the PRIOR backlog) into
       source under a "0% peer contamination" PR claim, because its denylist omitted them.
   - **Feeds:** a `content_sources` feed counts only if it actually FETCHES ≥1
     item. **Confirm the feed produces** (the news_rss/events_feed resolves and
     returns entries) before trusting it — set a feed you proved works, not a URL
     you assumed works. If every available feed is gated/empty (e.g. Stanford's
     Cloudflare-gated newsroom), set the best WORKING events/social source and
     accept an honest empty state — never leave a dead feed that just renders
     "hasn't posted anything yet" while claiming to be enriched.
   - **Photos:** each `campus_photos` url must actually load (resolves, not 404).
   - **Stats/reviews:** the value renders where the manifest path expects it.
   The rule: **open the live page (or query the API) for the node you just
   shipped and confirm it looks right. A value that doesn't render correctly is
   not done — it's a defect waiting for the user to find it.**

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
- **Full routine spec (editorial/standard axis):**
  `docs/superpowers/specs/2026-06-10-university-enrichment-routine.md` — note its
  "add a brand-new university" step is **SUPERSEDED** (this routine never adds
  universities; seeding is external). Parent design:
  `docs/superpowers/specs/2026-06-09-profile-standard-and-enrichment-design.md`.
- **Program-side MATCHER contracts (co-authoritative — read for claim hinge, ProgramPreference,
  authority→`c_program`, rankings-display-only):**
  `docs/superpowers/specs/2026-06-17-ai-structure-2-school-program-profile-design.md` +
  `docs/superpowers/specs/2026-06-17-ai-structure-3-match-engine-design.md`.

A node is **gold** when `check_conformance` returns no missing required fields
(except fields legitimately in its `_standard.omitted`). A **university is gold**
when every node in its tree is gold.

## Per-run algorithm (one whole university)

### Effort per run — finish a WHOLE university, not a token gesture
The unit of work is **one university taken ALL the way**, not one cosmetic edit.
Past runs under-delivered by swapping a single dimension (one batch of school
blurbs, one review pass) and stopping — so the same university needed a dozen
shallow runs and the grader kept flagging "Nth consecutive stub-swap." That is a
**failed run**. Each run MUST:
- Take its target through **every dimension to gold in the same run** — full real
  catalog · feeds that actually fetch · `campus_photos` · `external_reviews` on
  every coverable program · field-specific descriptions · conformance — not one
  slice. A repair run clears **every acute defect on that university**, not the one
  the grader happened to cite.
- **Use your full budget.** Keep working until the target is genuinely gold (or
  every remaining field is honestly omitted-with-reason) and the work is MERGED and
  deployed. Do not stop at "made some progress."
- Only a catalog too large to finish in one run (e.g. 300+ programs) may span runs
  (§"Scope & resumption") — and even then, finish a complete *slice* (e.g. a whole
  school's programs to gold), never a one-line edit. If you have budget left after
  the target is gold, move on to the next-priority not-yet-gold university and
  deepen it (§2) rather than ending early. (This routine never adds new
  universities — seeding is external; §2.)

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
   - **stub / generic / padded programs** — bare-abbreviation names ("BA"/"MS"/
     "PhD"), duplicate names, `"Programs"` departments, or boilerplate descriptions
     (miss #2). **Boston U (483 programs, 83 named "BA", 63 "MS") is the #1 repair
     target right now** — a bloated junk catalog is WORSE than a short real one and
     must be cleaned (rename to real field-specific names, or remove the fillers)
     before any new university;
   - **`content_sources` set but producing NOTHING** — an Events & Updates tab that
     renders "hasn't posted anything yet" despite the university being "enriched"
     (e.g. Stanford: gated newsroom + no working events/social feed, posts=0).
     Either find a feed that actually fetches, or set the best working events/
     social source — a dead feed is a miss (miss #9);
   - **schools or programs with no `content_sources`** → their Events & Updates are
     empty (the routine has been setting feeds only on the institution — fix this);
   - news posts with **no cover image** (the feed has images the ingest can now
     capture from media/enclosure/inline `<img>`);
   - **programs lacking `external_reviews` where reputable third-party coverage
     exists** — the SINGLE biggest gap today: the whole fleet has reviews on ~1
     program each (MIT 1/65, Columbia 2/263, Caltech 1/91). A flagship / MBA /
     popular professional or STEM master's with blank reviews is *not gold*
     (miss #8). Repairing this comes before any new university — and MIT itself
     (1/65) is a valid repair target. **But reviews depth on a given catalog ranks
     BELOW de-fabricating that same catalog's STRUCTURE — never pick a reviews/photo
     pass for a catalog that still has CIP-rollup / concentration-split / stub rows
     (structure-before-depth gate, miss #8). A reviews pass on a fabricated catalog is
     a defect, not a repair;**
   - **missing or single-photo `school_outcomes.campus_photos`** — the standard
     is a 4–5 photo verified gallery (miss #7); an institution with no campus
     photo at all (most beyond the original 14) breaks both the card header and
     the detail hero;
   - **no `_standard` stamp**, or stamped at an older `STANDARD_VERSION`.
3. **This routine does NOT add new universities — seeding is done manually/externally.**
   The fleet is bulk-seeded from the U.S. News National Universities ranking by a
   separate operator process (institution-level stubs: verified basics + ranking +
   campus photos). **Your job is ENRICHMENT + REPAIR ONLY** — take those seeded
   stubs to gold. Do NOT walk a ranking, resolve new UNITIDs, or create new
   institutions/admin users. Deepen what is already in the DB.

   Each run, pick the highest-priority NOT-yet-gold existing university (repair-first
   ordering from §2 — clear ACUTE defects before depth) and take it as far toward
   gold as the run allows: full REAL-named catalog (no CIP-rollup/stub rows) · feeds
   that actually fetch · a ≥4-photo verified `campus_photos` gallery · reviews on
   coverable programs · field-specific descriptions · conformance. Use the full
   budget (Effort-per-run rule above) — a freshly-seeded institution is "short
   catalog" + (often) photo-light, so it is an acute target: deepen it fully.

When every existing profile is gold (or honestly-omitted), **report and stop** — do
NOT add new universities; seeding is external. (When the operator adds a new batch of
institution-level seeds, they become the highest-priority enrichment targets on the
next runs.)

**RE-AUDIT — do not trust a prior "done" mark or `_standard` stamp.** Boston U and
Stanford were both shipped as "done" and are both broken (483 stub programs;
empty Events tab). A `_standard` stamp only means "a past run touched this," not
"it's actually gold" — and these misses (#2 stubs, #9 verify-output) post-date
earlier runs. So each run, **actually inspect the live output** of existing
universities (query the API / open the page) against the miss list before
concluding any of them is gold. Trusting your own prior completion is how broken
profiles stay broken.

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
  **Each program needs its REAL field-of-study NAME** ("Bachelor of Arts in
  Economics"), captured from the catalog — never a bare degree abbreviation or a
  generic stub (miss #2). An IPEDS CIP row gives you the *field* (the program
  name), not just the credential level; if you can only see "BA — 47 majors" and
  can't resolve the 47 major names, add the ones you CAN name and resume, rather
  than minting 47 identical "BA" rows.
- Dedupe (by real name, not just slug); assign stable slugs
  (`<univ>-<field>-<degree>`); map each program to its owning school by name. If a
  school/program — or its real name — can't be confirmed officially, **do not add
  it.**

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
5. **Auto-merge changed the timing — step 3 alone is now TOO LATE; PREVENT the dual
   head, don't just react to it.** This routine auto-merges enrichment PRs on green CI
   and auto-dispatches the deploy on merge, so a PR's `test_alembic_has_single_head`
   runs against its OWN base, never the post-merge `main`: two enrichment PRs each
   branched off the SAME base each read as single-head, pass CI, auto-merge, and leave
   `main` with a DUAL head — and the deploy fires on that dual head BEFORE any reactive
   merge-only migration (step 3) can land, so the production deploy FAILS and the work
   never reaches students. (Live this run: #745 `ucsdprof7` + #746 `seed12univ1` both
   branched off the same base and both auto-merged; #745's Deploy Backend FAILED on the
   resulting dual head and neither reached production until a fixup merge migration's
   deploy ran — then #748 + #749 both sat OPEN, each adding a migration off the same
   merged head: the identical collision about to recur.) So: (a) NEVER leave two
   migration-bearing enrichment PRs open against the same base — fold them into one PR,
   or hold the second until the first has merged AND you have re-pointed its
   `down_revision` onto the new head; (b) the durable fix is to make the single-head
   assertion evaluate the MERGE RESULT (rebased onto current `main`) and BLOCK the
   auto-merge, which lives in the automerge / CI workflow (app/infra) — FLAG it for a
   human; the grader does not edit it.

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

**Match-side gate (AI Structure — `check_conformance` does NOT cover this, so enforce it
by hand).** Confirm your migration called `backfill_program_preferences(session,
institution_id=inst.id)` after `apply` — that derives a grounded `program_preferences`
row for every program (skipping claimed rows), so the program -> student match fires.
Verify it ran: each program should have a row (`SELECT count(*) FROM program_preferences
pp JOIN programs p ON p.id=pp.program_id WHERE p.institution_id=...`). `field_provenance`
stamping is encouraged-not-gated today (not matcher-consumed yet; the tier anchors are
claimed 1.0 · verified-feed 0.85 · public-crawl 0.6 · derived/inferred 0.4). (See "Also
enrich for the MATCH" above.)

**Conformance is PRESENCE-only — it does NOT catch stubs, so it must be PAIRED with an
ENFORCED anti-stub gate.** `check_conformance` reports `conformant` from `not
missing_fields and not missing_sections and not stale` — a catalog whose every required
field is PRESENT is "conformant" even when every `description_text` is a school-blurb /
classification / per-field stub. That hole is why a stub-swap PR sails through this gate,
the step-9 "profile tests", and green CI, then **auto-merges** — observed on EIGHT
consecutive "repair" PRs (live full-fleet sweep this run: 22 of 28 catalogs FAIL the
miss #9 shared-leading-body gate, 7 carry the 95–100% double-period school-blurb frame,
one is 100% classification descriptions — all shipped LIVE through green CI). The miss #9
quantitative checks are today only a MANUAL "run it before shipping" pledge that nothing
enforces, so they have been skipped on every one of those PRs. Fix the enforcement, not
the wording: a catalog ships only when, IN ADDITION to `check_conformance`, it PASSES the
miss #9 anti-stub gates computed programmatically over the FULL catalog and baselined to
gold MIT's 0% — **verbatim-shared `description_text` = 0%, per-field shared body
(≥120 chars AND ≥50% of the shortest sibling) = 0% of multi-credential fields — computed AFTER
stripping a leading per-credential FRAME / degree-classification / field-definition sentence and
measured ANYWHERE in the siblings (longest common substring, not only the leading prefix), or a
prepended credential frame relocates the still-shared body into the tail and the count reads a false 0
(miss #8 credential-frame sub-bullet) — catalog-wide
cross-field shared clause = 0%, pure-classification-description share = 0%, double-period
".." / universal field-agnostic closing = 0%, `"{program_name}:"`/`" is "` prefix-double =
0%, `department` echoing the name's field = 0%**. ANY non-zero is a conformance FAIL, not a
warning — go back and research the failing rows per-program before shipping. And because
this routine auto-merges on green CI, the gate is only real once it is ENFORCED by CI: the
shipping change MUST add (or extend) an automated test in the profile test suite that CI
runs — assert these gold-MIT-0% gates for the catalog being shipped — so a stub-swap PR
FAILS CI and CANNOT auto-merge. (Do NOT weaken the thresholds to make a stub pass; a
non-zero means the rows are un-researched, which is the no-fabrication / structure-before-
depth invariant, not a tunable knob.)

**The enforced gate as BUILT is DESCRIPTION-ONLY — `anti_stub.analyze` computes the
description-quality tells (name-prefix, classification, double-period, verbatim /
shared-leading-body, cross-field clause) but has NO STRUCTURE metric, so a catalog joins
`CERTIFIED_CLEAN`, passes CI, and ships LIVE carrying the miss-#2 STRUCTURE defects this
same §8.5 already lists as gold-MIT-0% gates. A green description-only certification is
NOT a clean-catalog certification — and "anti-stub clean" in a PR title certifies only the
descriptions, never the names / departments / decomposition.** The descriptions are the
costume the analyzer sees; the structure is what it is blind to, so a "catalogue
descriptions" repair can clear every description tell, earn `CERTIFIED_CLEAN`, and leave
the field-echo departments and concentration-split rows exactly as they were. So a catalog
may enter `CERTIFIED_CLEAN` only when `anti_stub.analyze` (and the `test_anti_stub_gate`
parametrization) ALSO computes, baselined to gold MIT 0%, the STRUCTURE metrics:
(a) **`department` field-echo** — `department` equal to the name's field on (near-)every
row while a real owning school is known (the precise miss-#2 mechanical tell:
`department == program_name`-field verbatim one-off per row / no two programs share a
department / a `school_key` or the row's own description names the real school — NOT a
naive `dept == field`, which would false-flag a genuinely shared real "Department of
Economics"); (b) **CIP-rollup tells** in `program_name` AND `department` (trailing
", General"/", Other", a federal comma-and list, an embedded slash, a bare CIP rollup
title) — but the **comma-and tell must be ANCHORED to a federal-TAXONOMY ENDING**
(", Literatures, and Linguistics" · ", Pharmaceutical Sciences, and Administration" ·
", and Group Studies" · ", and Technicians/Services") and **NOT any Oxford-comma
"X, Y, and Z" list, which REAL degrees carry** ("Media, Culture, and Communication";
"Hospitality, Travel, and Tourism Management" are real published majors, NOT rollups) —
the same precision caveat (b) needs that (a) already states for `dept == field`, or the
gate FALSE-FLAGS a clean catalog and blocks a correct enrichment from `CERTIFIED_CLEAN`;
(c) a **literal CIP code** (`(CIP NN.NN)` or a bare trailing code) in name or
department; (d) **concentration-split rows** — a base field repeated across rows that
differ only by a trailing "— {concentration}" / ", {emphasis}" (collapse into `tracks`,
keep only genuine separate credentials). ANY non-zero blocks certification, same as a
description tell. (Gold MIT scores 0 on all four, so the baseline holds.) Evidence: live
API this run — a `CERTIFIED_CLEAN` 613-program catalog whose description metrics are
genuinely 0 live still ships ~62% rows whose `department` is the degree's field echoed
verbatim while the real owning school is named only in the description, PLUS one
bachelor's degree decomposed into four "…, {Emphasis}" concentration-split rows (each its
own program, `department` = the emphasis) — none caught, because the enforced gate has no
structure metric and the PR shipped under an "anti-stub clean" claim that covered the
descriptions only.

**`CERTIFIED_CLEAN` membership gates a catalog ONLY on the metrics whose test actually
parametrizes over it — and the frame-stripped shared-body metric is NOT one of them, so a
catalog joins `CERTIFIED_CLEAN`, passes green CI, and ships the fleet's DOMINANT defect (a
per-credential FRAME + ONE shared field body across BA/MS/PhD, miss #8) completely un-gated.
This is the dominant live ENFORCEMENT hole this run, and it is distinct from the abs-150
threshold gap.** The threshold gap (FLAG: the metric UNDERCOUNTS under dilution) is about how
HIGH the bar is; this is about WHICH catalogs the bar is even applied to. `test_certified_
catalog_is_anti_stub_clean` asserts only `analyze().is_clean`, and `analyze` computes the
leading-PREFIX shared-body count — which a prepended credential frame zeroes BY CONSTRUCTION
(miss #8 credential-frame). The LCS-anywhere `frame_stripped_shared_body` lives in a SEPARATE
test (`test_credential_siblings_have_no_frame_stripped_shared_body`) whose `@parametrize` list
is a HAND-MAINTAINED subset, NOT `CERTIFIED_CLEAN`. When those two lists DRIFT apart — and they
have — every certified catalog absent from the frame-stripped list is ungated on the
frame-shared-body defect: "anti-stub clean / `CERTIFIED_CLEAN`" then certifies only the
frame-BLIND `analyze` metric, never the frame-stripped one, so frame-shared bodies the EXISTING
(un-floored) metric would catch ship live as "certified." Therefore, when you certify a catalog
at §8.5/§9 you MUST add it to **EVERY** anti-stub parametrize list — `frame_stripped_shared_body`,
`scrape_debris`, `machine_artifacts` — not only `CERTIFIED_CLEAN`; and the durable fix is to make
those tests parametrize over `CERTIFIED_CLEAN` ITSELF so the lists CANNOT drift (that change lives
in `test_anti_stub_gate.py` — app/test code; FLAG it for a human). A catalog in `CERTIFIED_CLEAN`
but absent from the frame-stripped parametrize list is NOT actually gated and must not be trusted
as clean. Evidence: live API this run — NINE `CERTIFIED_CLEAN` catalogs ship credential-frame +
shared-body fields the EXISTING un-floored metric flags yet were never run through it (Harvard 68 ·
UCLA 67 · Michigan 67 · Berkeley 64 · Stanford 51 · Penn 51 · Notre Dame 23 · Columbia 14 · NYU 5
multi-credential fields share a body, vs gold MIT 0) — all green-CI certified, all absent from the
frame-stripped `@parametrize` list (which holds only mit/rice/uf/usc/uw_madison/jhu/uiuc/uw).

### 9. Ship — and MERGING IS MANDATORY (a run is not done until the work is on `main`)
`ruff check src/<changed> tests/<changed>` (NOT `ruff check .`) + the profile tests +
`npm run build`; branch off `origin/main` → commit → PR → **`gh pr merge --squash`** →
watch Deploy Backend → **verify live** (query the public API for the institution + a
sample school + a sample program; confirm new fields + citations + that the explore-card
eyebrow, updates feed, online programs, and resource links all render).

**A merge is NOT a deploy — `Deploy Backend` GREEN is part of "done," and you must
re-confirm the new data RENDERS LIVE.** A repair can pass CI, squash-merge, and still
never reach students if its Deploy Backend run FAILS or is CANCELLED — most often the
auto-merge dual-head race (step 5 / §8), which fails the prod migration so the live DB
keeps the OLD rows while the repo (and CI) shows the fix. Evidence: live API this run —
two per-credential repairs merged + green CI yet prod kept serving the OLD shared-body
descriptions because their Deploy Backend runs failed/were cancelled (and even the
dual-head fixup deploy failed). So treat the live re-query as the real gate, not the
merge. **If a prior repair is correct in the repo (CI-green) but its defect is still LIVE,
the remaining work is to DRIVE THE DEPLOY GREEN** — land/reland the merge-only migration,
clear the dual head, re-trigger Deploy Backend — and **do NOT rewrite the already-correct
data** (re-pointing or re-authoring a clean catalog only risks a fresh dual head and a
second failed deploy). The data is done; the deploy is the unfinished half.

**An opened-but-unmerged PR is a FAILED run, not a finished one.** Opening a PR and
stopping leaves the whole university invisible to students (the seeded thin profile
still shows) and lets work rot — a batch of fully-enriched universities once sat in
open PRs for days, unmerged, while the live site kept showing their 22-program seed.
So:
- The run is complete only when **`git log origin/main` contains your squash-merge
  commit AND Deploy Backend is green.** Before you write the report, fetch
  `origin/main` and confirm your commit is there. If it isn't, you are not done.
- If you genuinely **cannot** merge (no permission, a REQUIRED check is red), that is a
  **blocking error** — say so loudly at the top of the report with the PR link and the
  exact blocker, and DO NOT start a new university. Never silently end with the work
  stranded in an open PR.
- If older runs left their enrichments in unmerged PRs, treat landing them as repair
  work (step 2): head-sync each migration onto the current head, consolidate if
  several, and merge — before doing anything new.

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
- **Ship every verified unit** (commit → **merge** → deploy → verify live); a run that
  ends with its PR unmerged has FAILED — never block the tree on one unverifiable field
  (omit and continue), and never leave the finished tree stranded in an open PR.
- **Stop condition:** this routine is enrichment-only (it never adds universities —
  seeding is external; step 2 item 3). End a run only when every existing university is
  gold at the current `STANDARD_VERSION`. Until then there is always a next enrichment
  target — the worst-off not-yet-gold university (freshly-seeded institution-level stubs
  rank highest, being "short catalog" acute defects). "No repairs left AND all gold"
  is the only idle state.

## Using this as a scheduled routine

The human schedules this skill at any cadence they choose; each firing takes one
seeded university (or advances an in-flight one) toward gold and ships it. The fleet
is seeded externally (US-News bulk seed); this routine only ENRICHES — it never adds
new universities. Because every run is whole-tree, idempotent, and verified, the
database gains one fully-enriched university at a time, safely, without ever shipping
a fabricated fact.
