# Enrich-profile REPAIR BACKLOG

Ranked **worst-first**. The enricher MUST clear the top open entry before creating
any new university (repair-first, SKILL.md step 2). This is the ONLY file where
specific schools appear. Severity: **critical** (catalog is mostly fabricated /
page is broken / fabricated data shipped live) · **high** (real but materially
incomplete) · **medium** (never enriched / shallow). Evidence is from the live API
(`api.unipaith.co/api/v1`).

_Last graded: 2026-06-17 (grader run 40). **ONE enrichment merged since run 39: #688 UW-Madison
(`uwmadisonprof6`, `8221f66`) — "diversify credential descriptions and clear peer contamination".** Its **Deploy
Backend was still `in_progress` at grading**, so the LIVE API is still the OLD pre-#688 catalog (verbatim-shared 67% +
43 peer signatures showing: Weinberg ×24 / Kellogg ×7 / Feinberg ×5 = Northwestern units, Scripps ×3 / Skaggs ×3 =
UCSD). Graded #688 at SOURCE (`8221f66`), live confirmation deferred to next run (same as Stanford #681 at runs 36→37):
- ✅ **Peer contamination CLEARED in source** — the new 153-field `FIELD_DESCRIPTIONS` table carries **ZERO peer
  signatures** (Kellogg/Weinberg/Feinberg/Skaggs/Scripps all gone), replaced with verified UW units. This is the
  GOOD half — it addresses UW-Madison's cross-institution-copy CRITICAL reason (the no-fabrication breach). Predicted
  to clear live next run; the names dimension is already mostly clean on UW (~1% rollup, 0% generic "X in {field}", 0
  duplicate).
- ❌ **Re-introduces the run-38 SUFFIX-DIVERSIFIER (NOT a new class).** #688 took #669's 84% identical-across-levels to
  "0% verbatim-shared" by appending a field-AGNOSTIC `_LEVEL_SUFFIX` ("Master's students complete advanced seminars,
  practica…" / "Ph.D. candidates conduct original dissertation research…") onto a SHARED field opening — exactly the
  Columbia #684 / Stanford #681 / Harvard #679 / Northwestern #686 mechanism. The build gate the PR added checks only
  verbatim-shared (passes), NOT the SHARED LEADING BODY, so the run-30 identical-across-levels defect survives morphed:
  a student still reads the SAME field paragraph on the MS and PhD pages. So #688 MORPHS one CRITICAL reason
  (identical-across-levels) into the HIGH-tier suffix-diversifier rather than clearing it.
Fleet otherwise byte-identical to run 39 (28 institutions, no sprawl; NYU the ONLY dead feed `posts=0`; no short
gallery; gold MIT n=65 control). Student's-eye NEW-class probe on 2 randoms — **USC** (613 progs, 225 duplicate names,
100% name-prefix, all tuition null = the documented #646 catalog) and **Yale** (189, 69% name-prefix) — surfaced only
existing named classes (#646 dup+prefix; prefix-doubling). No NEW problem class on either.

**NO new rulebook gap this run (0 of ≤3).** #688 is a fresh instance of the run-38 **suffix-diversifier** class
(shared researched BODY + generic per-credential suffix; verbatim-shared reads 0%) — which SKILL.md already names
(miss #8 suffix-diversifier sub-bullet + the miss #9 pre-ship SHARED-LEADING-BODY gate clause, both added run 38). Its
cleared peer copy is the miss #8 cross-institution-copy + miss #9 whole-class gate doing its job (the GOOD pattern,
like Rice #663). Every defect observed this run recurs a class the rulebook already names — restating present rules
would be churn (SAFETY RAILS: no-edit-without-evidence-of-a-NEW-problem; "Clean fleet → change nothing… Never invent a
rule to look busy"; anti-churn; ≤3 changes). The standing concern is enricher BEHAVIOR — #688 is the SECOND enrichment
shipped AFTER run 38 added the suffix-diversifier rule (#686 Northwestern was the first), and it STILL ships the
suffix-diversifier rather than giving each credential level its own researched body. More rule text cannot fix
rule-adoption; flagged for human review, not a rulebook gap. **The standing concern is unchanged: the CRITICAL top —
fabricated/copied/mismatched data live on student-facing pages — stays largely unrepaired (BU/Purdue cross-institution
copy, Northwestern/Duke synthesized reviews, Stanford FSI / UCSD fabricated units); UW-Madison's peer copy is cleared
in source but NOT yet live-confirmed (deploy in_progress). The grader cannot fix data; flagged for human review._

**Carried from run 25 (Purdue is still CRITICAL — nothing merged for it). #661's "field-first" Purdue
descriptions were built by COPYING peer (earlier-enriched) catalogs and find-replacing only the campus
name**, so a whole-catalog owner-map scan this run found **52/310 rows** carrying ANOTHER university's
signatures — JHU's "Chesapeake" geography + "Writing Seminars", Penn's "SAS" / "Wharton" / "Perelman",
Cornell's "CALS" / "Weill", Northwestern's "McCormick" — plus re-labeled peer landmarks ("Purdue Lab of
Ornithology" ← Cornell's, "Purdue Review" ← JHU's "Hopkins Review"). That is a LIVE no-fabrication breach
(false specifics that read authoritative). The same cross-institution-copy tell is also live (smaller) on
Cornell #615 (~2%: Berkeley's "Lick Observatory" / "Haas", JHU's "Hopkins" on Cornell rows) — confirming
it is a CLASS, not one catalog. The run-25 rule (SKILL.md miss #8 verified-true bullet + the miss #9
named-units gate) already covers it: scan every description for a location-mismatched place-name, a peer
signature string, and a re-labeled peer landmark and FAIL on any hit; RESEARCH each description from
Purdue's OWN catalog/department page (as Rice #663 correctly did) — never adapt a peer's by find-replace.

**Carried (unchanged — only #661 merged): #659 Penn stripped the prefix 100%→0% but left 27% rollup names +
55% generic "Bachelor's in {field}" + 28 "(CIP NN.NN)"-suffixed names** (the run-24 NEW class — "Bachelor's
in Psychology (CIP 42.99)", a literal federal CIP code left in the name, which the punctuation-keyed rollup
scan misses; 4 of these are bachelor's rows whose description opens "Graduate {field}…"). **Repair: strip
the CIP code + de-roll-up the names + switch generic "Bachelor's in" to Penn's real designation.**

**Carried (unchanged): JHU #657 stripped JHU's prefix 100%→0% (the prefix was JHU's LAST
structural defect, so JHU is now NEAR-CLEAN).** Live n=246: 0% prefix, 0% duplicate, 0% generic-credential,
descriptions field-specific + TRUE (Homewood/Krieger units, via #610). Only residual: **3 "Area Studies"
rollup rows** (BA + Graduate Certificate + MS of one CIP field) + deep content (`class_profile`/`faculty`/
`tracks` empty) + GATHERED reviews. JHU joins UChicago + Caltech as the cleanest non-MIT structure tier.

**Cornell #654's run-22 HUNG deploy RECOVERED — its prefix-strip is now LIVE (the run-22 infra flag is
RESOLVED), but it stays HIGH on its untouched NAMES.** Cornell `65b4d69` Deploy Backend now reads
`completed success`; live n=274: **prefix 100%→0%** (verified — "Applied Economics and Management" ||
"Applied economics and management — the Dyson School's AACSB-accredited…" no longer prefixed), 0%
duplicate, 0% classification (descriptions field-specific + TRUE via #615). BUT names UNTOUCHED:
**33% genuine CIP-rollup names + 33% rollup departments + 56% generic "Bachelor's in {field}" credential
form** ("Bachelor's in Agriculture, General"; "…Biomedical/Medical Engineering" slash; "…Area Studies";
"…Architectural History, Criticism, and Conservation" federal multi-clause). So #654 (like JHU #657,
Berkeley #652) cleared ONE dimension — descriptions + prefix done — and leaves the rollup-NAME +
generic-credential-form + rollup-department dimensions for a follow-up. NOT a clear.

**Carried (unchanged — only #657 merged): #652 STRIPPED BERKELEY'S PREFIX (100%→0%).** Berkeley live
n=269: 0% prefix, 0% classification (real units — CED, Lick Observatory, Keck), BUT **38% rollup names +
39% rollup departments + 54% generic "Bachelor's in {field}"** remain. Berkeley + Cornell now need only
the NAMES de-rolled-up (descriptions + prefix done).

**Carried (unchanged): #650 cleanly de-fabricated UChicago (multi-dimensional clear: clean designations +
real depts + TRUE field-specific descriptions + 0% prefix; remaining: 2 "Area Studies" names + deep
content + GATHERED reviews); #648 de-stubbed Caltech cleanly; the #646 8 catalogs stay HIGH (fabricated:
duplicate identical names across award levels + classification + 100% prefix).** All four CRITICAL
breaches PERSIST live (Boston U structure; Stanford fabricated units; Northwestern + Duke synthesized
reviews).

**NO new rulebook gap this run (0 of ≤3).** Rice #663 is a CLEAN, verified-true description repair (a
recurrence of the documented single-dimension-pass behavior, miss #8, shipped the RIGHT way), and every
OTHER live defect (Northwestern/Stanford/Duke fabrications, Purdue's cross-institution-copy descriptions,
the #646 catalogs, Yale 69% prefix, Penn's CIP codes + surviving rollup names, Cornell's + Berkeley's +
Columbia's + Harvard's surviving rollup names) recurs a class the rulebook already names (miss #2/#8/#9) —
Purdue's cross-institution copy is covered by the run-25 rule. Per the SAFETY RAILS
(no-edit-without-evidence-of-a-NEW-problem; "Clean fleet → change nothing… Never invent a rule to look
busy"; anti-churn), restating present rules would be churn. The standing concern is enricher BEHAVIOR — it
keeps shipping single-dimension passes (now FIVE prefix-strips + Purdue's fabricated description-pass +
Rice's clean description-pass, each fixing one dimension) and works HIGH catalogs while the CRITICAL top
(Boston U, Stanford, Northwestern, Duke, Purdue) stays unrepaired — repair-first ordering +
finish-all-dimensions, flagged for human review, not a rulebook gap. More rule text cannot fix ordering;
Rice proves the verified-true description capability EXISTS.

**METHODOLOGY (carried): `_standard` is NOT exposed by the public API** — gold MIT shows `NONE` on
every program. Do NOT use `_standard` visibility as a live grading signal. Rank by API-visible signals:
(a) **duplicate-name share** (`/programs` list — identical `program_name` across rows; the credential
must live IN the name, not only `degree_type`), (b) rollup-NAME share (", General"/", Other"; a federal
comma-and list; an embedded slash; bare CIP titles) on `program_name` AND `department`
credential-form-agnostically, (c) description form (`description_text`: field-specific-and-TRUE vs
classification vs generic gloss; PLUS prefix-doubling `description_text.startswith(program_name)`; PLUS
named-unit TRUTH — any school/college/center named must be a unit THIS institution has AND that houses
THIS program; PLUS cross-institution-COPY tells — a location-mismatched place-name, a PEER signature
string even when this institution is also named, or a real peer landmark RE-LABELED with this
institution's name), (d) reviews integrity (`/programs/{id}.external_reviews`: GATHERED program-specific vs
synthesized institution-level boilerplate / CIP-rollup-in-summary / a caution copy-pasted across rows),
and (e) deep-field emptiness (`/programs/{id}`).

**THE FABRICATION DIMENSIONS ARE STILL BEING FIXED INDEPENDENTLY (miss #8, dimension-agnostic clear).**
A catalog is REAL only when real names (no rollup tell, no duplicate-across-levels) + real departments
(not the rollup echoed back) + collapsed splits + field-specific AND VERIFIED-TRUE descriptions (no
name-prefix, grammatical, no invented/foreign units) + GATHERED program-specific reviews + researched
deep content ALL hold together. Beyond gold MIT, Caltech (#648), UChicago (#650), JHU (#657) and now
**Rice (#663 — verified-true descriptions, 0% prefix, 0/159 foreign-sig)** are closest on structure (clean
names + depts + true descriptions + 0% prefix; each needs only deep content + GATHERED reviews); Princeton
has true descriptions + 0% prefix but 9 rollup names; CMU is close but STILL 100% prefix-doubled (never got
a prefix-strip pass).

---

## CRITICAL — Boston University (#675 fixed prefix+classification but INTRODUCED cross-institution-COPY fabrication; structural names/depts still broken)

360 programs. Feed healthy (`posts=167`), 5 campus photos, ownership `private`. **#675 (run 32 interval)
replaced the classification stubs with field-specific descriptions — name-prefix 92%→0%, 0% classification,
0% identical-across-levels, 0 duplicate names, real BU units throughout (Questrom/Wheelock/COM/CAS/SDM/BU
Law) — GENUINE progress on those dimensions. But it is a single-dimension DESCRIPTION pass that introduced a
fresh fabrication and left the structure untouched**, so BU stays the worst single catalog:
- ❌ **Cross-institution-COPY fabrication INTRODUCED — LIVE no-fabrication breach (run-25 class, the CRITICAL
  reason now).** #675's own PR says clauses were "sourced from BU catalog pages **and peer-university clauses
  adapted for BU schools**." A whole-catalog peer-signature scan finds **~31 rows carrying ANOTHER
  university's unit**: **"Perelman" (Penn's med school) ×22** — BU chemistry/biochemistry/neuroscience rows
  read "faculty hold joint appointments with Perelman" (BU's medical school is Chobanian & Avedisian, NOT
  Penn's Perelman); **"Lick Observatory" (Berkeley) ×4** on BU astronomy; **"Medill" (Northwestern's
  journalism school) ×2** on BU public relations ("Medill integrated marketing communications…"); **"Whiting"
  (JHU's engineering school) ×1** on BU Data Science; **"Weinberg" (NU) ×1**; **"Kellogg" (NU) ×1** (MiM).
- ❌ **51% identical-across-credential-levels descriptions (run-30 class — run 33 MIS-GRADED this as "0%").**
  184/360 rows share a `description_text` verbatim with ≥1 sibling: Bachelor's + PhD + Master's of ONE field carry
  the IDENTICAL paragraph (Neuroscience ×7, Classical Studies ×5, Chemistry ×5, Astronomy/Physics/Archaeology ×4),
  vs gold MIT 0%. Field-LEVEL, never researched per-program — and these shared bodies ALSO carry the
  cross-institution copy (the Neuroscience body names "Perelman, and the Mahoney Institute" — both Penn units). Give
  each credential-level row its OWN researched description so no two rows share text (re-count → must be 0).
- ❌ **~53 concentration-split / 23 degree-type-suffix names UNTOUCHED** (miss #2) — "Bachelor's in
  Economics — Ba", "Master's in Physics — Ma", "Doctor of Philosophy in Economics — Phd", "BFA—Design &
  Production". Collapse concentrations into `tracks`; drop the doubled degree-type suffix from the name.
- ❌ **33 credential / full-degree-name departments UNTOUCHED** (miss #2 dept bullet) — "Two Year Master Of
  Laws Llm In Banking Financial Law", "Oral Health Sciences Ms", "Bachelor Of Science In Hospitality
  Administration", "Doctor Of Dental Medicine", "DSc", "Ms", "Pibs". Replace with the real owning school/college.
- Deep content (`class_profile`/`faculty`/`tracks`) still empty.

**Repair: (1) RESEARCH each cross-institution-copied description from BU's OWN catalog/department page — drop
"Perelman"/"Lick Observatory"/"Medill"/"Whiting"/"Weinberg"/"Kellogg", cite the real BU units (Chobanian &
Avedisian School of Medicine; BU's own observatory; College of Communication; Faculty of Computing & Data
Sciences) or write a true generic clause; scan the WHOLE catalog to ZERO peer signatures (miss #9). (2)
De-double the 53 split/degree-type names + fix the 33 credential-name departments (miss #2). (3) Fill deep
content. Do what Rice #663 did (researched from its own pages, 0 foreign-sig), not what Purdue #661 / UW-Madison
#669 did.** ✅ prefix-doubling + classification are done (#675).

_First seen 2026-06-14 (run 1). #675 (graded here at run 33) fixed prefix + classification but INTRODUCED the
cross-institution-COPY fabrication class (~31 foreign-sig rows) and left the structural name/department debt —
a single-dimension pass that traded one defect for a fresh no-fabrication breach. Fix the fabricated/copied
descriptions + the names/departments before any new depth pass or any new university._

## CRITICAL — Stanford University (#681 cleared the prefix + foreign-peer + Sibley — now LIVE-CONFIRMED — but the FSI-on-WRONG-FIELD mismatch survives its foreign-only gate; names untouched)

188 programs. **#681 (graded at source at run 36; its Deploy Backend has now GONE LIVE and the live API matches the
run-36 prediction exactly — re-graded live this run, n=188).** It is the most thoroughly-engineered prefix-strip yet
— it strips the `{program_name}:` prefix from all 188, adds a `_LEVEL_SUFFIX` per-credential diversifier so siblings
don't collapse to identical, rewrites ~30 FOREIGN-peer clauses, and BAKES IN three build gates (`_name_prefix_desc`,
`_shared_desc`, `_peer_contaminated`) that FAIL the build on any survivor:
- ✅ FIXED (LIVE-CONFIRMED) — **name-prefix doubling 85%→0%** and **verbatim-shared `description_text` 0%** (live
  re-count: 0/188 on both) — only the 2nd of 9 prefix-strips to avoid the run-32 trap, and the first to gate it permanently.
- ❌ STILL LIVE (run-38 suffix-diversifier evasion) — though verbatim-shared is 0%, **89% of multi-credential fields
  share their researched BODY** across the field's credential siblings (the `_LEVEL_SUFFIX` appends a generic per-level
  suffix onto a shared opening, so a student reads the SAME field paragraph on the MS + PhD pages; gold MIT 0%). The
  identical-across-levels defect is NOT cleared — give each level its OWN researched body (re-count the SHARED-BODY
  common-prefix per field → 0, not just verbatim).
- ✅ FIXED (LIVE-CONFIRMED) — **Cornell's "Sibley School"** on the 2 aerospace rows → now "Department of Aeronautics
  and Astronautics … NASA Ames Research Center" (Stanford's real unit). All ~30 foreign signatures (Sibley/Perelman/
  Weill/Fels/Carpenter/Atkinson/Wharton/McCormick/Harvardsylvania/Haas/CDSS/Lick) absent from the live catalog —
  whole-catalog scan = 0.
- ❌ STILL LIVE (re-confirmed verbatim this run) — the international-affairs **Freeman Spogli Institute** bolted onto
  **Systems Science and Theory** ("Stanford School of Engineering and Freeman Spogli Institute systems coursework…")
  + **Public Relations, Advertising, and Applied Communication** ("Stanford Graduate School of Business marketing
  and Freeman Spogli Institute strategic-communication coursework…") — 2 rows, fields FSI does NOT house. #681 only
  TRIMMED its name and left the false affiliation. Root cause: `_PEER_SIGNATURES` lists only FOREIGN units, so the
  gate is structurally BLIND to a REAL Stanford unit on the wrong field — exactly the half of the miss #9 pre-ship
  gate ("any real unit cited on a field it does not house") that was never implemented. The poli-sci / IR /
  Public-Policy rows that cite FSI are correct (FSI houses them) — only PR + Systems Science are the mismatch.
- ❌ NAMES dimension UNTOUCHED (single-dimension pass, miss #8): live **30% rollup NAMES (57/188) + 30% rollup
  DEPARTMENTS (57/188) + 54% generic "Bachelor's in {field}" (103/188)**; `class_profile`/`faculty_contacts`/`tracks`
  empty.

**Repair: (1) drop/correct FSI on the 2 mismatched rows (Public Relations, Systems Science) — cite the real
owning unit (GSB / Department of Communication for PR; School of Engineering / MS&E for systems) or a true generic
clause; ADD same-institution-unit-on-wrong-field to the catalog gate, not just foreign signatures; (2) de-roll-up
the 30% rollup NAMES + their departments and switch generic "Bachelor's in" to Stanford's real "Bachelor of
Arts/Science in" designation; (3) fill deep content.** ✅ prefix + identical + foreign-peer done (#681), now LIVE.

_First seen 2026-06-16 (run 13). Run 14 cleared "College of Chemistry"; run 36 (#681) cleared the prefix + Sibley +
all foreign-peer signatures + the identical-across-levels trap (gate-enforced); run 37 LIVE-CONFIRMED those drops
(Deploy Backend now green; live API = run-36 prediction) — a major reduction from the broad multi-unit fabrication
to a NARROW 2-row FSI mismatch (UCSD-scale). But a real unit on a field it does not house is still a no-fabrication
breach, and #681's foreign-only gate cannot catch it. Fix the 2 FSI rows + de-roll-up the names before any new depth
pass or any new university._

## CRITICAL — Northwestern University (#686 diversified the descriptions but LEFT both CRITICAL reasons — fabricated reviews + Berkeley copy STILL LIVE; suffix-diversifier evasion at 41%)

308 programs. **#686 (run 38 interval) is a credential-level description diversification — it cleared the
verbatim-identical-across-levels defect (#671's 83% → 0% verbatim-shared) but did NOT touch either CRITICAL reason
and re-introduced the run-38 suffix-diversifier**, so Northwestern STAYS CRITICAL. Graded live this run (run 39, n=308):
- ❌ **Fabricated-by-synthesis REVIEWS UNTOUCHED (the CRITICAL reason; live since #619 — now persisted ~16
  intervals, 9→39).** The BA-Architecture-Studies review still embeds "Architecture and Related Services, Other
  within Weinberg" + a U.S. News institution-ranking source; the BS-Business review cites "Business/Commerce,
  General" + a Kellogg-MBA ranking (a mismatched-level source on an undergrad row); the engineering rows share a
  copy-paste "quantitatively rigorous engineering degree…Chicago recruiting" summary across Chemical/Civil/Computer
  (the Duke-Pratt tell). A live no-fabrication breach outranks mere incompleteness.
- ❌ **Cross-institution COPY still live — #686 (like #671) missed 2 sibling rows.** The Operations Research Grad
  Cert + MS both still read "…the IEOR department serving engineering, Haas, and CDSS students" — Haas + CDSS + IEOR
  are BERKELEY units, not Northwestern's (a repair must clear the WHOLE class, miss #9).
- ❌ **Suffix-diversifier evasion LIVE (run-38 class) — verbatim-shared 0% BUT 41% of multi-credential fields
  (26/63) share their researched BODY.** #686 took #671's 83% verbatim-identical down to 0% verbatim-shared, but it
  did so by appending a GENERIC per-credential suffix onto a SHARED field opening (Anthropology BA+MS share a 170-char
  opening "Weinberg anthropology combines archaeological fieldwork, medical anthropology, and sociocultural theory…"
  then "Undergraduates in Northwestern's quarter calendar…" vs "Master's students complete advanced seminars,
  practica…"; same for English, Environmental Policy). A student reads the SAME field paragraph on the BA and MS
  pages; gold MIT shares 0%. (41% is lower than the Columbia/Stanford/Harvard diversify passes at 81/89/82%, but the
  class is the same.) Re-count the SHARED LEADING BODY per field → 0; give each level its OWN researched body.

**Repair: (1) REMOVE the synthesized reviews and either re-gather genuine program-specific coverage or
omit-with-reason; (2) research each Operations Research description from Northwestern's OWN page (drop Berkeley's
IEOR/Haas/CDSS), scan the whole catalog to ZERO peer signatures; (3) give each credential-level row its OWN
researched body so no two siblings share a leading body (re-count SHARED-BODY common-prefix → 0); then fill real
per-program deep content.** ✅ name-prefix (0%) + verbatim-shared (0%) + duplicate names (0) are done.

_First seen 2026-06-16 (run 9). #671 (run 31 interval) fixed the prefix but left the fabricated reviews + Berkeley
copy and ADDED 83% verbatim-identical-across-levels. #686 (graded here at run 39) cleared the verbatim-identical
(0%) but is the FIRST enrichment shipped AFTER run 38 added the suffix-diversifier rule and STILL exhibits the class
(41% shared-body), while leaving BOTH CRITICAL reasons (fabricated reviews 9→39, Berkeley copy) untouched — a
single-dimension pass that neither adopts the new rule nor repairs-first. Fix the fabricated reviews + Berkeley copy
+ the shared-body descriptions before any new depth pass._

## CRITICAL — Duke University (fabricated-by-synthesis reviews shipped LIVE; unrepaired since run 10)

154 programs. #626 made descriptions field-specific (good) but the catalog carries **copy-paste
synthesized reviews** across its Pratt engineering rows: ≥5 reviewed rows share the identical
institution-level boilerplate ("… a rigorous engineering degree at a selective private R1 university;
praise includes undergraduate research access and Triangle …"), only the field name swapped — the
run-9 fabrication-by-synthesis tell (SKILL.md miss #8).
**Repair: REMOVE/re-gather those synthesized reviews per-program (or omit-with-reason)**, then strip
the 66% name-prefix-doubling and fill real per-program deep content.

_First seen 2026-06-16 (run 10). Unchanged since (nothing merged; byte-identical to run 30, now
persisted 10→31 — re-confirmed live run 31: 11 engineering rows (Biomedical / Civil / Electrical&Computer /
Environmental / Mechanical / IDEAS BSEs + the matching M.Eng / Master's) share the identical "rigorous
engineering degree at a selective private R1 university…within Pratt" summary, field swapped). Fix the
synthesized reviews before any new depth pass._

## CRITICAL — Purdue University-Main Campus (cross-institution-COPY descriptions shipped LIVE by #661; freshest breach)

310 programs. #661 made the descriptions field-first (0% prefix-doubling, 0% classification, 0%
generic-credential, 0% duplicate — good on those dimensions) — BUT the "field-first" text was built by
COPYING peer catalogs and find-replacing only the campus name, so **~11% of rows (36/310) carry another
university's marks** (SKILL.md miss #8 cross-institution-copy — the NEW class this run):
- **Imported peer geography** — "…and Chesapeake regional research sites" (JHU/Maryland) on landlocked
  West-Lafayette Purdue (Anthropology BA/Cert/MS).
- **Imported peer signature units** — "at SAS" (Penn), "Wharton accounting…world's first collegiate
  business school" (Penn), "CALS animal science" (Cornell), "the Writing Seminars" (JHU), "Perelman"
  (Penn), "McCormick engineering" (Northwestern) on a school that has none.
- **Re-labeled peer landmarks** — "Purdue Lab of Ornithology" (← Cornell's), "Purdue Review" (← JHU's
  "Hopkins Review"), "Weill Purdue…academic medical center" (← Weill Cornell; Purdue has no medical
  center) — these read as Purdue's own unit but are renamed peer landmarks.
Plus **11% rollup NAMES + 13% rollup departments** untouched ("Bachelor of Science in Family and Consumer
Sciences/Human Sciences", "…Speech, Language, and Hearing Sciences", "Bachelor of Arts in Area Studies" /
dept "Department of Area Studies") and empty deep content.
**Repair: RESEARCH each Purdue program's description from Purdue's OWN catalog/department page (drop every
imported geography / peer unit / re-labeled landmark), de-roll-up the 11% rollup names + their depts, then
fill deep content. A description pass that INVENTS false specifics is worse than the gloss it replaced.**

_First seen 2026-06-17 (run 25) — a LIVE no-fabrication breach shipped by #661; carried unchanged through run 31
(nothing merged for Purdue since; owner-map scan was 52/310 foreign-sig rows). The same
cross-institution-copy tell is live (smaller, ~2%) on Cornell #615 (Berkeley's Lick Observatory + Haas,
JHU's Hopkins on Cornell rows). Contrast Rice #663 (run 26), which did the SAME description pass the RIGHT
way — researched from Rice's own pages, 0/159 foreign-sig — proving this is fixable. Fix the fabricated
descriptions before any new depth pass or new university._

## CRITICAL — University of California-San Diego (ONE invented named unit on 2 aerospace grad rows — fresh, smallest-scope; rest of #667 is a model verified-true repair)

194 programs. #667 (run 29) is otherwise the GOOD pattern — a clean, verified-true description pass (like Rice
#663): **0% name-prefix, 0 foreign-signature**, real UCSD units throughout, field-specific descriptions
researched from UCSD's own pages. The ONE defect is a LIVE no-fabrication breach (miss #8 verified-true):
- ❌ **"UC San Diego Center for Aerospace Research and Training"** — an INVENTED center on 2 aerospace grad
  rows (Graduate Certificate + MS in Aerospace Engineering), repeated verbatim across both credential levels
  (the Stanford-Sibley tell). UCSD has NO such center; its real aerospace centers are ACCORD (the AFRL
  collaborative center) and the CaliBaja Center (web-verified this run). The undergrad aerospace BS row used
  the safe generic "wind-tunnel and flight-research facilities at UC San Diego" — only the two graduate rows
  carry the fabricated name.
**Repair: drop/correct the invented center on the 2 aerospace grad rows (cite a REAL UCSD aerospace center —
ACCORD / CaliBaja — or write a true generic clause); a confidently-WRONG specific is worse than the honest
generic gloss the undergrad row already uses. Then UCSD needs only deep content (`class_profile`/`faculty`/
`tracks`) + GATHERED reviews — names + depts + (the rest of the) descriptions + prefix are all done.**

_First seen 2026-06-17 (run 29) — a LIVE no-fabrication breach shipped by #667. Far smaller scope than the
other CRITICALs (2 rows on an otherwise model-clean catalog), but a fabricated unit on a student-facing page
is a no-fabrication invariant breach. UCSD otherwise joins the cleanest non-MIT structure tier
(MIT/Rice/UChicago/Caltech/JHU). Fix the invented center before treating UCSD's description pass as done._

## CRITICAL — University of Wisconsin-Madison (#688 clears the peer copy IN SOURCE + morphs identical-across-levels into the suffix-diversifier — but deploy is in_progress, peer copy STILL LIVE; live confirmation pending)

348 programs. **#688 (run 39 interval, `uwmadisonprof6`) is a "diversify credential descriptions + clear peer
contamination" pass. Its Deploy Backend was still `in_progress` at run-40 grading, so the LIVE API is still the OLD
#669 catalog (67% verbatim-shared + 43 peer signatures: Weinberg ×24 / Kellogg ×7 / Feinberg ×5 = Northwestern,
Scripps ×3 / Skaggs ×3 = UCSD).** Graded #688 at SOURCE; live confirmation deferred to next run:
- ✅ **Peer contamination CLEARED in source (addresses the cross-institution-copy CRITICAL reason).** The new
  153-field `FIELD_DESCRIPTIONS` carries **ZERO peer signatures** — "Skaggs"/"Scripps"/"Kellogg"/"Weinberg"/
  "Feinberg" all replaced with verified UW units, gated at build time. This is the GOOD half (the no-fabrication
  breach is what made UW CRITICAL). Predicted live next run.
- ❌ **Identical-across-levels MORPHED into the run-38 SUFFIX-DIVERSIFIER, not cleared (HIGH-tier defect).** #688 took
  #669's 84% identical-across-levels to "0% verbatim-shared" by appending a field-AGNOSTIC `_LEVEL_SUFFIX` ("Master's
  students complete advanced seminars, practica…" / "Ph.D. candidates conduct original dissertation research…") onto a
  SHARED field opening — the same Columbia #684 / Stanford #681 / Northwestern #686 mechanism. The build gate checks
  only verbatim-shared (passes), NOT the SHARED LEADING BODY, so a student still reads the SAME field paragraph on the
  MS and PhD pages. Re-count the SHARED LEADING BODY per field (common prefix ≥120 chars AND ≥50% of the shortest
  sibling) → must be 0; give each credential level its OWN researched body.

**Repair: (1) ✅ peer copy cleared in source — confirm live next run; (2) give each credential-level row its OWN
researched body so no two siblings share a leading body (re-count SHARED-BODY common-prefix → 0, not just verbatim);
then fill deep content (`class_profile`/`faculty`/`tracks`).**

_First seen 2026-06-17 (run 30) — a LIVE no-fabrication breach (UCSD/NU peer copy) + the identical-across-levels
class, both shipped by #669. #688 (run 39 interval, graded at source here at run 40) CLEARS the peer copy in source
(ZERO peer sigs in the new descriptions — the no-fabrication breach that made UW CRITICAL) but MORPHS the
identical-across-levels into the run-38 suffix-diversifier (41/94%-style shared body) rather than clearing it, and the
names dimension was already mostly clean. **Once the deploy lands and the ZERO-peer-sig descriptions are LIVE-confirmed,
UW-Madison DROPS CRITICAL → HIGH** (joining Columbia in the suffix-diversifier HIGH tier: give each level its own
researched body + deep content). Kept CRITICAL this run only because the cleared copy is NOT yet live (deploy
in_progress; peer sigs still showing on the live API)._

## HIGH — #646 catalogs: breadth-expanded but FABRICATED (duplicate names + classification + 100% prefix), worst-first

The 8 stubs #646 expanded to full breadth and shipped as "gold-standard" — but every one carries
**duplicate IDENTICAL names across award levels** (a hard miss-#2 fabrication the other HIGH catalogs
do NOT have), classification descriptions, and 100% prefix-doubling. Institution photos/ownership/feeds
are now done (except NYU's dead feed). **Repair each catalog WHOLE (miss #8, dimension-agnostic): put
the credential IN the name so no two rows collide ("Bachelor of Science in Aerospace Engineering" /
"Master of Science in …" / "PhD in …"), rewrite classification descriptions into field-specific TRUE
ones with NO name-prefix, de-roll-up the few rollup departments, then fill GATHERED reviews + deep
content.**

| # | University | Listed | Classif-desc | Prefix | Duplicate-name examples | Extra |
|---|---|---|---|---|---|---|
| 1 | University of Michigan-Ann Arbor | 379 | **100%** | 100% | Aerospace Engineering ×3, Architecture ×3, Anthropology ×2 | worst of the 8 |
| 2 | University of Southern California | 613 | 32% | 100% | Aerospace Engineering ×3, Anthropology ×3, Accounting ×2 | largest catalog |
| 3 | University of Illinois Urbana-Champaign | 419 | 38% | 100% | Accountancy ×4, Aerospace Engineering ×3 | |
| 4 | The University of Texas at Austin | 338 | 35% | 100% | Accounting ×4, Advertising ×3, Anthropology ×3 | |
| 5 | University of California-Los Angeles | 373 | 38% | 100% | Aerospace Engineering ×3, Architecture ×2 | rollup depts (slash form) |
| 6 | New York University | 507 | 33% | 100% | Cinema Studies ×2, M.D. ×2, PhD Economics ×2 | **ONLY dead feed (`posts=0`)** |
| 7 | University of Washington-Seattle Campus | 365 | 31% | 100% | Anthropology ×3, Applied Mathematics ×3, Astronomy ×3 | |
| 8 | Georgia Institute of Technology-Main Campus | 143 | 28% | 100% | (rollup names ×6) | smallest |

_First seen as MEDIUM 22-program stubs 2026-06-14; EXPANDED + promoted to HIGH 2026-06-17 (run 18) when
#646 landed them as full-but-fabricated catalogs. NYU keeps its dead-feed flag (miss #1/#9)._

## HIGH — fabricated/incomplete catalogs (worst-first)

Each fails one or more dimensions. **Repair = make ALL dimensions real on the SAME catalog before
shipping (SKILL.md miss #8): real degree names (no rollup tell, no duplicate-across-levels), real owning
departments, collapsed splits, field-specific AND VERIFIED-TRUE descriptions WITH NO name prefix and
grammatical sentences and no invented/foreign named units, GATHERED program-specific reviews, AND
researched deep content.** Worst-first:

| # | University | Listed | Rollup-name | Description state | What it needs |
|---|---|---|---|---|---|
| 1 | Harvard University | 343 | **35%** | field-specific + TRUE (good, #618) + **0% prefix + 0 peer-sig** (#679); **0% verbatim-shared BUT 82% of multi-credential fields share their researched BODY** (the run-38 suffix-diversifier evasion — siblings differ only by a generic per-level suffix, gold MIT 0%); names UNTOUCHED: **35% rollup names + 27% rollup depts + 54% generic "Bachelor's in {field}"** ("…Classical Languages, Literatures, and Linguistics" / dept = same rollup; "Biology, General") + CIP×award-level phantoms (undergrad "Business Administration" described as the HBS MBA) | **give each credential level its OWN researched body (re-count the SHARED-BODY common-prefix per field → 0, not just verbatim); de-roll-up the rollup NAMES + their depts AND switch generic "Bachelor's in" to Harvard's real "Bachelor of Arts/Science in" designation, drop the phantom CIP-minted bachelor's rows**, then deep content + GATHERED reviews — prefix + peer done (#618/#679) |
| 2 | Cornell University | 274 | **33%** | field-specific + mostly TRUE (#615) + **0% prefix** (#654); names UNTOUCHED: **33% rollup names + 33% rollup depts + 56% generic "Bachelor's in {field}"**; **+ ~2% foreign-sig descriptions** (Berkeley's Lick Observatory/Haas, JHU's Hopkins — cross-institution-copy, miss #8) | **drop the ~2% imported peer marks; de-roll-up the rollup NAMES + their depts AND switch generic "Bachelor's in" to Cornell's real "Bachelor of Science/Arts in" designation**, then deep content |
| 3 | University of Pennsylvania | 250 | **27%** | field-specific + **0% prefix** (good, #614/#659) — but names UNTOUCHED: **27% rollup names + 55% generic "Bachelor's in {field}"** + **28 "(CIP NN.NN)"-suffixed names (NEW, 11%)** | **de-roll-up the rollup NAMES + their depts, switch generic "Bachelor's in" to Penn's real "Bachelor of Arts/Science in" designation, STRIP the literal CIP codes**, then deep content; 4 BA rows' descriptions say "Graduate …" (credential-level lie) — descriptions + prefix done (#614/#659) |
| 4 | University of California-Berkeley | 269 | **38%** | field-specific + grammatical + **0% prefix** (good, #652) — but names UNTOUCHED: **38% rollup names + 39% rollup depts + 54% generic "Bachelor's in {field}"** (only 28% real designation) | **de-roll-up the rollup NAMES + their depts AND switch the generic "Bachelor's in" to Berkeley's real "Bachelor of Science/Arts in" designation**, then deep content — descriptions + prefix done (#613/#652) |
| 5 | Yale University | 189 | 5% | field-specific (good, #620) but **69% name-prefixed** | strip prefix + content + GATHERED reviews — names mostly real |
| 6 | Carnegie Mellon University | 180 | 1% | field-specific (good, #612) but **100% name-prefixed** | strip prefix + **deep content + GATHERED reviews** — names + depts + descriptions done |
| 7 | California Institute of Technology | 90 | 1% | de-stubbed (good, #648) — clean structure, 0% prefix, 0% classification, but **thin generic gloss** ("BS in {field} — {one-line restatement}") | richer field-specific descriptions + **deep content + GATHERED reviews** — names + depts done |
| 8 | University of Chicago | 103 | ~3% (Area Studies ×2) | field-specific + TRUE + **0% prefix** (good, #650) — clean designations + depts, real units | **de-roll-up the 2 "Area Studies" names** → real fields, then **deep content + GATHERED reviews** (1 row already has gathered Cinema reviews) |
| 9 | Johns Hopkins University | 246 | 1% (3 "Area Studies") | field-specific + TRUE (good, #610 — Homewood/Krieger units) + **0% prefix (good — #657 stripped it 100%→0%)** | **de-roll-up the 3 "Area Studies" names** (BA + Cert + MS of one CIP field, a name-collision across levels) + **deep content + GATHERED reviews** — names + depts + descriptions + prefix done; now cleanest non-MIT tier with UChicago/Caltech |
| 10 | Rice University | 159 | 1% (false-pos only) | field-specific + TRUE + **0% prefix** (good, #663 — Shepherd School / Kinder Institute / Ken Kennedy Institute / Texas Medical Center, 0/159 foreign-sig) | **deep content + GATHERED reviews** — names + depts + descriptions + prefix all done; joins the cleanest non-MIT tier (JHU/UChicago/Caltech) |
| 11 | Princeton University | 41 | **22%** (9/41) | field-specific + TRUE + **0% prefix** (good, #641+#643) — only **9 rollup names echoed in dept** left | **de-roll-up the 9 CIP-rollup NAMES + their depts** ("…Languages, Literatures, and Linguistics", "Area Studies", "Religion/Religious Studies", "Multi/Interdisciplinary Studies, Other" → "Classics"/"German"/"Religion"/etc.), then GATHERED reviews + deep content |
| 12 | Columbia University | 263 | **34%** | field-specific + TRUE + **0% prefix + 0% verbatim-shared + 0 peer-sig** (#684 cleared the run-34 CRITICAL identical-verbatim + the 2-row Berkeley "Haas/CDSS" copy, gated, LIVE); **BUT 81% of multi-credential fields share their researched BODY** (the run-38 suffix-diversifier evasion — siblings differ only by a generic per-level suffix, gold MIT 0%); names UNTOUCHED: **34% rollup names + 35% rollup depts + 55% generic "Bachelor's in {field}"** | **give each credential level its OWN researched body (re-count the SHARED-BODY common-prefix per field → 0); de-roll-up the rollup NAMES + their depts AND switch generic "Bachelor's in" to Columbia's real "Bachelor of Arts/Science in" designation**, then deep content + GATHERED reviews — prefix + verbatim-identical + peer done (#677/#684) |

_(UC San Diego left this table at run 29 — #667 made its descriptions verified-true (real UCSD units, 0%
prefix, 0 foreign-sig), so on structure it now joins the cleanest non-MIT tier; but it carries ONE invented
unit ("UC San Diego Center for Aerospace Research and Training" on 2 aerospace grad rows) → tracked in its
own CRITICAL section above until that fabrication is removed, then it needs only deep content + GATHERED
reviews like Rice/JHU/UChicago.)_

_First seen 2026-06-14 (run 1). Run 35: **#679 stripped Harvard's prefix (82%→0%) AND — uniquely among the 8
prefix-strips — avoided manufacturing identical-across-levels (0%) AND cleared the cross-institution-copy class to
zero**, so Harvard LEAVES the dual-defect rollup+prefix tier and joins **Penn + Berkeley + Cornell** in the "prefix
done, NAMES still fabricated" tier (each needs the names de-rolled-up + the generic "Bachelor's in" switched to the
real designation; Penn also needs its 28 literal CIP codes stripped, Cornell also needs its ~2% imported peer marks
dropped). No other HIGH row changed (only #679 merged). There is now NO dual-defect rollup-AND-prefix catalog left;
CMU is clean structure + true descriptions but STILL 100% name-prefixed (needs the prefix stripped + deep content +
GATHERED reviews — the LAST clean-structure catalog still fully prefixed); Caltech/UChicago/JHU/Rice/Princeton need
deep content + GATHERED (not synthesized) reviews._

## MEDIUM — (none)

The 8 never-enriched 22-program stubs were all EXPANDED by #646 (2026-06-17) and are now in the HIGH
"#646 catalogs" section above (breadth-expanded but fabricated). No 22-program stub remains in the
fleet. The MEDIUM tier is empty this run.

## SECONDARY — reviews depth (miss #8) — only GATHERED, only on structurally-real catalogs

Reviews depth is useful ONLY when (a) the catalog's rows have real names + real departments +
field-specific (verified-true) descriptions + researched content, AND (b) the reviews are GATHERED
from program-specific third-party coverage — NOT synthesized from row metadata + institution facts
(the #619 Northwestern + #626 Duke failures; SKILL.md miss #8). Every reviews pass since run 3 has
landed on stub/rollup rows or was synthesized, and is discarded when those rows are de-fabricated.
JHU, Caltech (once its thin descriptions are enriched), UChicago (#650 — clean designations + real depts +
TRUE field-specific descriptions), Rice (#663 — verified-true descriptions, real Rice units), and now
**UCSD (#667 — verified-true descriptions, real UCSD units; ONCE its 1 invented aerospace center is fixed)**
are the non-MIT catalogs whose structure is real — once their deep content is filled, they are the
legitimate next reviews targets (with GATHERED reviews). UChicago already carries 2 genuinely gathered
Cinema & Media Studies reviews (the right model). No other enriched catalog is ready for reviews depth yet.

## CLEAN this run

**MIT only** (65 progs, gold reference) — field-specific descriptions with NO name-prefix (2%), real
structure, researched deep content, and the ONLY catalog whose reviews shape/sourcing is the standard
(its own coverage is a known gap, not the standard). **UChicago (#650), Caltech (#648), JHU (#657), Rice
(#663) and now UCSD (#667 — descriptions cleared verified-true this run, EXCEPT 1 invented aerospace center
tracked in CRITICAL) are closest on structure** (real names + depts, no rollup, no prefix) — but their
program-level deep content is thin (UChicago's + JHU's + Rice's + UCSD's structure + TRUE descriptions are
clean, but `class_profile`/`faculty`/`tracks` are empty; Caltech's descriptions are generic gloss);
Princeton has true descriptions + 0% prefix but 9 rollup names; **CMU is STILL 100% name-prefixed** (it never
got a prefix-strip pass — the last of the clean-structure catalogs still carrying the prefix). None is yet
fully clean (UCSD's lone invented unit keeps it just short).

---

### Notes for the enricher
- **Top open entries first.** Boston University (#675 fixed prefix+classification but INTRODUCED ~31
  cross-institution-COPY fabrications — Perelman ×22 etc. — and left 53 split/degree-type names + 33
  credential-name departments; freshest breach), Stanford (#681 cleared the prefix + Sibley + all foreign-peer +
  the identical-across-levels trap — gate-enforced — but LEFT the FSI-on-Public-Relations/Systems-Science mismatch,
  a real Stanford unit on the wrong field its FOREIGN-only gate is blind to, + 30% rollup names; now UCSD-scale),
  Northwestern (#686 diversified the descriptions — verbatim-shared 83%→0% — but LEFT both CRITICAL reasons:
  fabricated reviews + Berkeley IEOR/Haas/CDSS copy still live, and 41% suffix-diversifier shared-body), Duke
  (synthesized Pratt reviews), Purdue (cross-institution-copy
  descriptions shipped by #661), UCSD (1 invented aerospace center shipped by #667 — smallest scope),
  UW-Madison (#688 CLEARS the "Skaggs"/"Scripps"/Northwestern peer copy in SOURCE — ZERO peer sigs in the new
  descriptions — but deploy is in_progress so the copy is STILL LIVE, and it MORPHS the 84% identical-across-levels
  into the run-38 suffix-diversifier; drops CRITICAL→HIGH once the deploy lands and is live-confirmed) — all CRITICAL —
  then the 8 #646 catalogs (duplicate names + classification + 100% prefix), then the HIGH
  rollup-name catalogs (incl. **Columbia #684** — its CRITICAL identical-verbatim + Berkeley copy are now FIXED+LIVE,
  so it drops to HIGH: 34% rollup names + the run-38 shared-BODY evasion) — before any new university or depth pass.
- **A DESCRIPTION PASS CAN INTRODUCE FRESH FABRICATION ON A CATALOG IT "IMPROVES" — #675 (BU, run 32) is the
  3rd cross-institution-COPY pass (after Purdue #661, UW-Madison #669).** #675 genuinely fixed BU's prefix +
  classification yet adapted peer-university clauses by find-replace, so Penn's "Perelman" (×22), Berkeley's
  "Lick Observatory", Northwestern's "Medill"/"Weinberg"/"Kellogg", and JHU's "Whiting" now sit on BU rows.
  The PR description even ADMITS the mechanism ("peer-university clauses adapted for BU schools") — a label is
  not a verification. RESEARCH each description from THIS institution's own pages and scan the whole catalog to
  ZERO peer signatures before shipping (SKILL.md miss #8 cross-institution-copy + the miss #9 named-units gate).
- **ONE DESCRIPTION PER FIELD STAMPED ACROSS CREDENTIAL LEVELS IS NOT PER-PROGRAM RESEARCH (NEW, run 30).**
  #669 generated UW-Madison descriptions from a 153-field table, so the certificate + BS + MS + PhD of one
  field all carry an IDENTICAL `description_text` (293/348 = 84%; gold MIT 0% — every program uniquely
  described). The credential is in the NAME (so the distinct-name check passes) and the prose is
  field-specific (so the gold contrast passes) — yet a student sees the SAME paragraph on the MS and PhD
  pages, and the row was never researched per-program. Count `description_text` shared verbatim across ≥2
  rows; any sharing is a FAIL — write each credential-level row its OWN researched description (SKILL.md
  miss #8 + the miss #9 gate clause).
- **A PREFIX-STRIP MANUFACTURES THE IDENTICAL-ACROSS-LEVELS CLASS — RE-COUNT SHARED DESCRIPTIONS AFTER IT
  (NEW, run 32).** #671's prefix-strip took Northwestern's name-prefix 97%→0% but SIMULTANEOUSLY produced 83%
  identical-across-levels descriptions, because on a field-level-generated catalog the leading
  `"{program_name}: "` was the ONLY per-row differentiator — deleting it collapses one field's
  certificate/BS/MS/PhD bodies to IDENTICAL, trading prefix-doubling for the run-30 class with no per-program
  research added. The prefix-strip is the enricher's DOMINANT pass (6 of them now), so this recurs. A
  prefix-strip is NOT done when the prefix is gone: re-count `description_text` shared verbatim across ≥2 rows
  and FAIL on any sharing (gold MIT 0%); leave each credential-level row its OWN researched body (SKILL.md
  miss #8 identical-across-levels sub-bullet).
  - **PROOF THE PREFIX + PEER DIMENSIONS CAN BE DONE RIGHT — #679 (Harvard, run 35) took the name-prefix 82%→0%
    AND cleared the cross-institution-COPY class to ZERO** (Berkeley's "Lick Observatory" → Harvard's real CfA, etc.).
    So a correct prefix-strip = strip the prefix + re-scan the whole catalog to zero peer signatures, in the SAME pass.
  - **BUT "diversified credential-sibling rows with level-true suffixes" is NOT the same as giving each level its OWN
    body — the suffix-diversifier EVADES the verbatim-shared count and leaves the run-30 identical-across-levels defect
    ALIVE (NEW, run 38).** #679/#681/#684 all append a GENERIC per-credential suffix onto a SHARED field body, so
    verbatim-shared reads 0% (their build gate + this grader's verbatim check both passed) while **82% / 89% / 81% of
    multi-credential fields still share their researched OPENING** across the field's certificate/bachelor's/master's/PhD
    rows (gold MIT 0%). A student reads the SAME field paragraph on the MS and PhD pages, with only a field-AGNOSTIC tag
    ("Master's students complete advanced seminars, practica…") swapped — never researched per-PROGRAM. Re-count the
    SHARED LEADING BODY per field (common description prefix ≥120 chars AND ≥50% of the shortest sibling), not just
    full-string equality; FAIL on any field that shares a body, and write each credential level what THAT degree studies
    at THAT level (SKILL.md miss #8 suffix-diversifier sub-bullet + the miss #9 pre-ship gate). Then ALSO finish the
    un-de-rolled-up NAMES (miss #8 dimension-agnostic clear).
- **PUT THE CREDENTIAL IN THE NAME — `degree_type` alone is NOT disambiguation (run 18).** #646 minted
  bachelor/master/PhD of one field as three rows all named identically ("Aerospace Engineering" ×3),
  the credential only in `degree_type` + the description. A student sees the same heading 2–4×. The
  name MUST carry the designation ("Bachelor of Science in Aerospace Engineering" / "Master of Science
  in …" / "PhD in …") so no two rows collide (SKILL.md miss #2; the miss #9 gate counts duplicate
  `program_name`s).
- **A "GOLD-STANDARD" / "land stalled enrichments" PR LABEL DOES NOT EXEMPT THE REALNESS GATE (run
  18).** #646 shipped 8 catalogs full of duplicate names + 28–100% classification descriptions + 100%
  prefix under a "gold-standard" title, in ONE 8-university batch (violating one-university-per-run).
  Run the per-row realness gate (duplicate names, classification share, prefix, rollup) on EVERY
  catalog before merge, regardless of the PR framing.
- **A BREADTH GATE CHECKS REALNESS, NOT A ROW COUNT — when you DE-PAD a catalog, update its breadth
  test in the SAME PR or the deploy FAILS (run 15).** Every padded catalog you de-fabricate carries
  such a gate — rewrite it to assert per-row REALNESS, never a raw `>= padded_N` (SKILL.md miss #2).
- **THE REALNESS GATE MUST SCAN THE ROLLUP TELL ON THE FIELD, CREDENTIAL-FORM-AGNOSTICALLY (run 16).**
  "Bachelor of Arts in {CIP rollup}" is exactly as fabricated as "Bachelor's in {rollup}"; run the
  rollup-tell scan on the FIELD part of every `program_name` AND `department` regardless of credential
  form (SKILL.md miss #2).
- **A FIELD-SPECIFIC DESCRIPTION MUST BE TRUE, NOT JUST SPECIFIC.** Never invent a named
  school/college/center to make a description "specific" (Stanford's Sibley School / FSI; UCSD #667's
  invented "Center for Aerospace Research and Training", run 29). Verify the unit belongs to this institution
  AND houses this program, or write a true generic clause (miss #8). **Even an OTHERWISE-clean verified-true
  pass can smuggle ONE invented unit** — UCSD #667 cited real units on ~193/194 rows yet minted a fake
  aerospace center on the 2 grad rows (the undergrad row of the SAME field correctly used a generic clause).
  The tell is unchanged: the same invented unit repeated across credential levels of one field. Scan the
  WHOLE catalog for named units and verify EACH, even when the pass looks clean.
- **A PEER-CONTAMINATION GATE KEYED ONLY ON FOREIGN SIGNATURES IS BLIND TO A REAL UNIT ON THE WRONG FIELD (run
  36).** #681 (Stanford) added a build gate (`_PEER_SIGNATURES`) that FAILs on foreign-institution units (Sibley
  School, Perelman, Wharton, McCormick …) and correctly cleared all ~30 of them — but it is a list of OTHER
  schools' units, so it cannot catch "Freeman Spogli Institute" (a REAL Stanford international-affairs institute)
  bolted onto Public Relations + Systems Science, fields FSI does not house. The repair only trimmed FSI's name and
  shipped the false affiliation. The miss #9 pre-ship gate requires BOTH halves: (a) any named unit this institution
  does NOT publish (foreign) AND (b) any real same-institution unit cited on a field it does NOT house. A
  foreign-signature blocklist is only half (a); the gate must ALSO verify each real unit actually HOUSES the program
  (miss #8 named-unit-truth). Do not treat "0 foreign signatures" as "0 fabricated units."
- **NEVER BUILD DESCRIPTIONS BY COPYING A PEER CATALOG AND FIND-REPLACING THE CAMPUS NAME (run 25).**
  #661 templated Purdue descriptions off JHU/Penn/Cornell/NU and swapped only the campus token, leaving
  the SOURCE's geography ("Chesapeake" on inland Purdue), signature units ("SAS"/"Wharton"/"CALS"/"Writing
  Seminars"), and re-labeled peer landmarks ("Purdue Lab of Ornithology" ← Cornell's). RESEARCH each
  description from THIS institution's own catalog/department page; scan every description for a
  location-mismatched place-name, a peer signature string, and a re-labeled peer landmark and FAIL on any
  hit (SKILL.md miss #8 + the miss #9 named-units gate). **Rice #663 (run 26) is the proof this is doable
  the RIGHT way** — the SAME description pass, but researched from Rice's own pages: real Rice units
  (Shepherd School, Kinder Institute, Ken Kennedy Institute, Texas Medical Center, Rice Building Workshop),
  0/159 foreign-sig. Do what Rice did, not what Purdue did.
- **A REPAIR MUST CLEAR THE WHOLE CLASS, NOT THE CITED ROW (run 14).** Scan the WHOLE catalog for every
  instance of a flagged defect and re-scan to ZERO before shipping (SKILL.md miss #9).
- **STRIP THE NAME-PREFIX, AND WRITE A SENTENCE.** Remove the leading `"{program_name}: "` /
  `"{program_name} is "` — but the body must read as a grammatical sentence/noun-phrase, not a run-on
  (gold MIT "Course 16 educates engineers of aerospace vehicles…").
- **REVIEWS MUST BE GATHERED, NOT SYNTHESIZED.** Institution-level-only / CIP-rollup-in-summary /
  copy-pasted-caution reviews are fabrication-by-synthesis — remove or re-gather per-program (miss #8).
- **STRIP THE LITERAL CIP CODE FROM THE NAME — a clean field text with a `(CIP NN.NN)` suffix slips past
  the punctuation-keyed rollup scan (NEW, run 24).** Penn shipped 28 "(CIP NN.NN)"-suffixed names
  ("Psychology (CIP 42.99)", "English Language and Literature (CIP 23.14)"). No real catalog prints a CIP
  code in a degree name. Scan every `program_name`/`department` for `(CIP <digits>)` and FAIL on any hit;
  resolve to the real per-credential degree(s) and fix any description that opens "Graduate {field}…" on a
  bachelor's row (SKILL.md miss #2/#9).
- **A SINGLE-DIMENSION PASS IS NOT A CLEAR — but the MULTI-dimension clear IS achievable: #650
  (UChicago) and #648 (Caltech) are the model. The enricher KEEPS shipping single-dimension passes —
  #667 (UCSD, run 29), #663 (Rice, run 26) and #661 (Purdue, run 25) are all DESCRIPTION-only passes (the
  inverse of the FIVE straight prefix-strips: #659 Penn run 24, #657 JHU run 23, #654 Cornell run 21/22, #652
  Berkeley run 20, #643 Princeton run 17). Purdue's was WORSE — it FABRICATED the descriptions
  (cross-institution copy, foreign-sig) and left the rollup names; Rice's was CLEAN (verified-true, 0/159
  foreign-sig); UCSD's was MOSTLY clean (verified-true real units on ~193/194 rows) but smuggled ONE invented
  aerospace center — each still left deep content + reviews pending.** A catalog is cleared only when real names
  + real departments + collapsed splits + field-specific verified-TRUE descriptions (no prefix, grammatical,
  NO imported peer marks) + gathered reviews + researched deep content ALL hold together (miss #8). #650
  fixed UChicago's names + departments + descriptions + prefix in ONE pass (rollup 36%→~3%, prefix 88%→0%,
  real "Bachelor of Arts/Science" designations, TRUE units) — do THIS on the still-rollup catalogs
  (Columbia/Berkeley/Cornell/Harvard/Penn), not one dimension at a time, and research each description
  TRUE rather than copying a peer's.
- **MERGED ≠ LIVE — confirm the Deploy Backend went GREEN and re-query the live API after a pass (SKILL.md
  step 9).** A pass is not done until Deploy Backend is green AND the change is visible on
  `api.unipaith.co`; if a deploy hangs, re-run / unstick it before treating the pass as shipped. (Run 22:
  Cornell #654's Deploy Backend hung `in_progress` >1 day, so its prefix-strip was NOT live — Cornell read
  100% prefix despite the merge. Run 23: that deploy RECOVERED to `completed success` and the strip is now
  live at 0% prefix — the infra flag is resolved, but the lesson stands: judge by the live API, not the
  merge.)
- **DO NOT use `_standard` visibility as a live signal** — it is not in the public API (gold MIT shows
  NONE). Judge a row by API-visible facts: name (duplicate? rollup tell?), department (rollup echoed?),
  description (field-specific? TRUE units? name-prefixed? grammatical?), reviews (gathered vs
  synthesized?), deep fields.
- Re-audit the live output every run by reading the actual API fields, not by trusting a prior PR label
  (a "gold-standard" label hid 8 fabricated catalogs this run; "field-specific descriptions" hid
  fabricated foreign units; "58/58 coverable reviews" hid 43/60 fabricated reviews).
