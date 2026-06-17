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
     by every rich field being empty and `_standard` unstamped on those rows**) before
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
3. **When NO existing university has a blocking issue (every one gold or
   honestly-omitted), the run's job is GROWTH — actively ADD the next new
   university. Do not idle on the existing set.** Repair-first ORDERS the work; it
   does not CAP the fleet. The platform's value grows with coverage, so a run with
   nothing left to repair is a run that expands the fleet by one.
   - **Where the next university comes from (so you never run dry):** walk the
     **U.S. News & World Report "Best Colleges" → National Universities** ranking in
     rank order (#1, #2, #3, …) and add the highest-ranked university NOT yet in the
     DB. The seeded fleet is already ≈ the top 30, so you continue down the list
     (~#30 onward); **skip any already present** and any without a resolvable UNITID.
     The ranking has hundreds of entries, so there is ALWAYS a next target. Resolve
     the official name + UNITID for that ranked school, then enrich it fully to gold
     (same bar as any existing one) per the steps below. Add ONE new university per
     run. (Optional: a strong real student-demand signal — search / match / view /
     saved-school — may bump a high-demand school ahead of its US-News rank; absent
     a signal, just follow the list one by one.)

Within the repair phase, prioritize by student demand (saved-school / match / view
counts) then by size of gaps. **Adding breadth while existing profiles are broken
is the one thing this routine must NOT do — but once they are whole, refusing to
grow is the second thing it must not do.** Only genuinely stop if every existing
university is gold AND the growth universe is exhausted (it won't be) or the
operator has explicitly paused growth — never stop merely because the originally
seeded set is done.

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

### 9. Ship — and MERGING IS MANDATORY (a run is not done until the work is on `main`)
`ruff check src/<changed> tests/<changed>` (NOT `ruff check .`) + the profile tests +
`npm run build`; branch off `origin/main` → commit → PR → **`gh pr merge --squash`** →
watch Deploy Backend → **verify live** (query the public API for the institution + a
sample school + a sample program; confirm new fields + citations + that the explore-card
eyebrow, updates feed, online programs, and resource links all render).

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
- **Stop condition (rarely reached):** end a run only when every existing university is
  gold at the current `STANDARD_VERSION` AND there is no next university to add. Because
  growth walks the U.S. News National Universities ranking (step 2 item 3), there is
  almost always a next target — so "no repairs left" means **add the next-ranked new
  university**, not stop. Only truly idle if the ranking universe is exhausted or the
  operator has paused growth.

## Using this as a scheduled routine

The human schedules this skill at any cadence they choose; each firing enriches one
whole university (or advances an in-flight one) and ships it. See §11 of the spec for
the exact prompt to schedule. Because every run is whole-tree, idempotent, and verified,
the database grows one complete university at a time, safely, without ever shipping a
fabricated fact.
