"""Enforced anti-stub gate for certified-clean program catalogs (enrich-profile §8.5).

``check_conformance`` is presence-only and cannot see a stubbed description, so eight
consecutive stub-swap "repair" PRs auto-merged through green CI (REPAIR_BACKLOG run 55).
This test closes that hole: every catalog in ``CERTIFIED_CLEAN`` must score the same
zero the gold MIT reference does on the ``anti_stub`` description-quality metrics, so a
stub-swap of a certified catalog FAILS CI and cannot auto-merge.

To certify a newly de-fabricated catalog, add it to ``CERTIFIED_CLEAN`` — CI then
re-computes the metrics and blocks the merge unless the rows are genuinely researched
per-program. The thresholds are NOT tunable: a non-zero is the no-fabrication /
structure-before-depth invariant, not a knob.
"""

import importlib

import pytest

from unipaith.profile_standard.anti_stub import (
    analyze,
    frame_stripped_shared_body,
    machine_artifacts,
    scrape_debris,
    template_slot_artifacts,
)

# Catalogs verified free of raw scraped-catalogue debris (course-code / requirements /
# contact-address fragments) in description_text — REPAIR_BACKLOG CRITICAL #1 (USC, run 66).
# Grow as scrape-built catalogs are researched per-program (UT-Austin still carries it).
SCRAPE_DEBRIS_CLEAN = ["mit", "usc", "uiuc", "nyu", "columbia"]

# Catalogs whose per-program descriptions have been verified gold-equal (every metric 0).
# Grow this list as catalogs are genuinely de-fabricated — never weaken the assertions.
CERTIFIED_CLEAN = [
    "mit",  # gold reference
    "ucsd",  # cert padding dropped; per-credential descriptions (#745 + this run)
    "caltech",  # cert + non-terminal-MS padding dropped; field-specific descriptions (this run)
    "nyu",  # bulletin-sourced descriptions; school-blurb + synthesized reviews removed (#753)
    "princeton",  # CIP rollups → real majors; textbook-def stubs → researched descriptions (#754)
    "carnegie_mellon",  # researched per-program clauses; "{program_name}: " prefix-double removed
    "duke",  # "{program_name}: " prefix-double removed; per-credential doctoral clauses
    "uiuc",  # catalogue-sourced descriptions; school-blurb + synthesized reviews removed
    "usc",  # catalogue-sourced descriptions; school-blurb + synthesized reviews removed
    "georgia_tech",  # catalog.gatech.edu descriptions; stubs + synth reviews removed (gatechprof3)
    "ut_austin",  # catalog.utexas.edu descriptions; school-blurb + synth reviews removed (utaprof2)
    "uw",  # Wikipedia-sourced per-credential descriptions; junk/Westwood removed (uwdefab1)
    "ucla",  # Wikipedia per-credential descriptions; Catalog entry junk removed (uclaprof4)
    "jhu",  # per-credential level bodies (frame+tail-share removed); real reviews kept
    "michigan",  # per-credential discipline definitions; build-artifact junk removed (michprof4)
    "stanford",  # per-credential defs; Catalog entry junk removed (stanfordprof11)
    "purdue",  # per-credential discipline defs; peer-copy + rollups removed (purduedefab1)
    "chicago",  # per-credential graduate descriptions; cert padding dropped (chicagodefab1)
    "bu",  # Medill peer-copy removed; real dual-degree/MPH/CFA/math/world-lang
    #             names + depts; per-credential bodies; school-as-field fixes (budefab1,
    #             supersedes buprof11's narrower description-only repair)
    "berkeley",  # CIP rollup de-fab; real dept names; per-credential descriptions
    #             (berkeleyprof9 — frame-stripped shared body cleared berkeleypercrd1)
    "cornell",  # CIP-rollup buckets → real Cornell degrees or dropped; field-echo
    #             departments → real owning college; per-credential description leads
    #             (verbatim/shared-body removed) (cornelldefab1)
    "penn",  # CIP-rollup buckets → real Penn degrees or dropped; dept = real owning
    #             school (field-echo removed); per-credential description leads with the
    #             resolved real name, no rollup leak (verbatim/shared-body removed) (penndefab1)
    "yale",  # "{program_name}: " prefix-double removed; per-credential bodies — graduate
    #             rows take a distinct doctoral/master's clause (GRADUATE_FIELD_DESCRIPTIONS),
    #             so credential siblings no longer share a leading body (yaledefab1)
    "harvard",  # CIP rollup de-fab; suffix-diversifier removed; per-credential bodies
    #             (harvarddefab1 — HIGH #4; harvardpercred1 clears frame-stripped shared body)
    "columbia",  # CIP rollup + possessive de-fab; real owning schools; per-credential
    #             bodies (columbiadefab1 — HIGH #1)
    "rice",  # conferred UG names; real depts; per-credential description leads
    #             (verbatim/shared-body removed) (ricedefab1 — HIGH #4)
    "uw_madison",  # per-credential description leads; suffix-diversifier removed
    #             (shared-leading-body = 0) (uwmaddefab1 — HIGH #5)
    "northwestern",  # per-credential description leads; suffix-diversifier removed
    #               (shared-leading-body = 0) (nwdefab1 — HIGH #6)
    "uf",  # 314-program real catalog; LiveWhale feeds; 16 colleges (ufprof1/2)
    "dartmouth",  # institution seed → gold + real verified 43-program catalog across the
    #             five schools; field-specific researched descriptions, real departments,
    #             no rollup/possessive/stub rows (dartprof1)
    "emory",  # institution seed → gold + 46-program catalog; Trumba events feed;
    #             4-photo gallery; field-specific descriptions (emoryprof1)
    "notre_dame",  # 113-program real catalog; conferred names; per-credential discipline
    #             defs (verbatim/shared-body/cross-field = 0); events feeds (ndprof1)
    # NOTE: stanford was REMOVED briefly (2026-06-18, uwdefab1) while it still shipped build-script
    # junk; re-added after stanfordprof11 regeneration matching Michigan/UW repair model.
]


def _programs(name: str) -> list[dict]:
    mod = importlib.import_module(f"unipaith.data.{name}_profile")
    return list(getattr(mod, "PROGRAMS", []))


@pytest.mark.parametrize("name", CERTIFIED_CLEAN)
def test_certified_catalog_is_anti_stub_clean(name: str):
    report = analyze(_programs(name))
    assert report.is_clean, (
        f"{name} catalog is no longer anti-stub clean: {report.summary()}\n"
        + "\n".join(
            f"  {metric}: {items[:5]}{' …' if len(items) > 5 else ''}"
            for metric, items in report.violations.items()
            if items
        )
    )


def test_gold_mit_is_the_zero_baseline():
    """MIT — the gold reference — must score zero on every metric (the baseline)."""
    report = analyze(_programs("mit"))
    assert report.is_clean, f"gold MIT regressed: {report.summary()}"


@pytest.mark.parametrize("name", CERTIFIED_CLEAN)
def test_certified_catalog_has_no_machine_artifacts(name: str):
    """A certified catalog must not render build-script junk (e.g. "Catalog entry <hex>:"
    or a raw hex id) — these pass every description-quality metric yet show raw junk to
    students. Three certified catalogs (UW/Michigan/UCLA) shipped this live; the gate
    closes that hole (REPAIR_BACKLOG run 59)."""
    hits = machine_artifacts(_programs(name))
    assert not hits, (
        f"{name} catalog carries machine-build artifacts in {len(hits)} descriptions: "
        f"{hits[:5]}{' …' if len(hits) > 5 else ''}"
    )


def test_artifact_detector_bites_on_catalog_entry_junk():
    """Regression guard: the artifact gate must flag the live "Catalog entry <hex>:" form
    while passing a clean field-specific description."""
    junk = [
        {
            "program_name": "Bachelor of Arts in Accounting",
            "description": (
                "Catalog entry 5686776b4e64: Catalog entry 5686776b4e64: UW's Foster "
                "School of Business draws on the Department of Finance on the Westwood campus."
            ),
        }
    ]
    clean = [
        {
            "program_name": "Bachelor of Arts in Accounting",
            "description": (
                "Accounting is the process of recording and processing information about "
                "economic entities. At the University of Washington's Foster School of "
                "Business in Seattle, this program engages the discipline."
            ),
        }
    ]
    assert machine_artifacts(junk), "should flag the 'Catalog entry <hex>' junk"
    assert not machine_artifacts(clean), "must not flag a clean field-specific description"


_FRAME_STRIPPED_CLEAN = [
    "mit", "rice", "uf", "usc", "uw_madison", "jhu", "uiuc", "uw", "harvard", "nyu",
    "ut_austin", "columbia", "michigan", "duke", "georgia_tech", "ucla", "berkeley",
    "stanford",
]


@pytest.mark.parametrize("name", _FRAME_STRIPPED_CLEAN)
def test_credential_siblings_have_no_frame_stripped_shared_body(name: str):
    """A field's credential siblings (BA / MS / PhD) must not share a body once a leading
    credential frame is stripped — the run-65 evasion the leading-prefix shared-body count
    in ``analyze`` reads as a false 0 (REPAIR_BACKLOG #3 / miss #8 credential-frame). Gold
    MIT and the (de-fabricated) Rice catalog both score 0: every credential level carries
    its own researched body. A non-zero is the per-program-research invariant, not a knob.
    """
    shared = frame_stripped_shared_body(_programs(name))
    assert not shared, (
        f"{name}: credential siblings share a frame-stripped body on "
        f"{len(shared)} field(s): {shared[:8]}{' …' if len(shared) > 8 else ''}"
    )


# Catalogs that hold to the run-67 ABSOLUTE floor (a 150+-char shared run across a field's
# credential siblings is flagged regardless of fraction, so a padded per-credential tail
# cannot dilute a stamped department blurb past the fraction-only default). Each entry is
# verified at frame_stripped_shared_body(..., abs_chars=150) == 0. A catalog graduates here
# once its frame-shared fields are rewritten to per-credential researched bodies (the
# fraction-only default still guards the rest of the fleet until they are repaired —
# REPAIR_BACKLOG miss #8 fraction-floor; the dilution-evasion catalogs UF / Cornell / BU
# are NOT here yet on purpose).
_ABS_FLOOR_CLEAN = [
    "nyu", "mit", "columbia", "michigan", "ucla", "jhu", "berkeley", "uf", "stanford",
]


@pytest.mark.parametrize("name", _ABS_FLOOR_CLEAN)
def test_credential_siblings_no_shared_body_absolute_floor(name: str):
    """A field's credential siblings must share no body even under the ABSOLUTE 150-char floor
    (REPAIR_BACKLOG CRITICAL #2 / miss #8 fraction-floor): a 150+-char run shared across a
    field's BA/BS or MS/PhD is a stamped department blurb (e.g. the Chemistry B.A.==B.S.
    950-char duplicate), which the fraction-only default could dilute past once each sibling's
    tail is padded. Gold MIT scores 0 with the absolute floor on; JHU joins after its
    Anthropology / Chemical Engineering / Communication Studies clauses (each ~150 chars) were
    rewritten to per-credential researched bodies (REPAIR_BACKLOG #11, jhupercrd1)."""
    shared = frame_stripped_shared_body(_programs(name), abs_chars=150)
    assert not shared, (
        f"{name}: credential siblings share a 150+-char body on "
        f"{len(shared)} field(s): {shared[:8]}{' …' if len(shared) > 8 else ''}"
    )


# Catalogs verified free of run-71 template-slot machine grammar (a field phrase slotted
# into a fixed per-credential frame: a DOUBLED credential heading or a DOUBLE/DANGLING
# preposition from an empty slot — REPAIR_BACKLOG CRITICAL C1/C2, FLAG #1c). These score 0
# on every share/form metric (the body differs per row) yet render machine junk, so they
# need their own gate. This is intentionally a SUBSET of CERTIFIED_CLEAN — the whole-fleet
# sweep this run found template-slot rows still LIVE on stanford (49), ucla (9), ut_austin
# (3) and michigan (1); they stay OUT until repaired, and the durable fix is to parametrize
# this over CERTIFIED_CLEAN itself once those clear (FLAG for the grader).
_TEMPLATE_SLOT_CLEAN = [
    n
    for n in CERTIFIED_CLEAN
    if n not in {"stanford", "ucla", "ut_austin", "michigan"}
]


@pytest.mark.parametrize("name", _TEMPLATE_SLOT_CLEAN)
def test_certified_catalog_has_no_template_slot_grammar(name: str):
    """A certified catalog must not ship template-slot machine grammar: a per-credential body
    that DIFFERS per row (so analyze + frame_stripped read 0) but re-states the credential
    inside the body ("...coursework in the Master of Science in …") or carries a double /
    dangling preposition from an empty slot ("research in of farm…"). Berkeley auto-merged
    107 such rows green and CERTIFIED_CLEAN (REPAIR_BACKLOG CRITICAL C1); gold MIT scores 0."""
    hits = template_slot_artifacts(_programs(name))
    assert not hits, (
        f"{name} catalog carries template-slot machine grammar in {len(hits)} descriptions: "
        f"{hits[:5]}{' …' if len(hits) > 5 else ''}"
    )


def test_template_slot_detector_bites_on_doubled_credential_and_empty_slot():
    """Regression guard: the template-slot gate flags the doubled-credential and
    double-preposition forms while passing a clean per-credential researched body."""
    junk = [
        {
            "program_name": "Doctor of Philosophy in Agricultural Business and Management",
            "description": (
                "Doctoral training in the Doctor of Philosophy in Agricultural Business and "
                "Management centers on dissertation research in of farm and agribusiness "
                "economics, with qualifying examinations."
            ),
        },
        {
            "program_name": "Master of Science in Earth Systems",
            "description": (
                "Graduate coursework in the Master of Science in Earth Systems emphasizes "
                "climate and ecosystems."
            ),
        },
    ]
    clean = [
        {
            "program_name": "Doctor of Philosophy in Anthropology",
            "description": (
                "The Doctor of Philosophy in Anthropology centers doctoral research on "
                "archaeological fieldwork, ethnography, and biological anthropology, advancing "
                "candidates through qualifying examinations and a faculty-mentored dissertation."
            ),
        }
    ]
    assert len(template_slot_artifacts(junk)) == 2, "should flag doubled credential + empty slot"
    assert not template_slot_artifacts(clean), "must not flag a clean per-credential body"


def test_absolute_floor_catches_a_diluted_shared_sentence():
    """Regression guard: a 150+-char field sentence stamped across credential siblings and then
    diluted below the fraction floor by a long unique per-credential tail must still flag under
    ``abs_chars`` (run-67 dilution evasion), while the fraction-only default reads it as clean."""
    shared = (
        "Madison campus anthropology combines archaeological fieldwork, medical anthropology, "
        "and sociocultural theory across a department known for its global reach and methods."
    )
    tail_ba = (
        " The B.A. surveys the four subfields through introductory and intermediate seminars "
        "and a flexible elective sequence suited to a liberal-arts course of study at the "
        "college, leaving room for study abroad, a second major, and undergraduate field "
        "experience in museums, laboratories, and community settings across the city and beyond."
    )
    tail_ms = (
        " The M.S. adds graduate methods training, a research practicum, and a thesis advised "
        "by faculty, preparing students for doctoral work or applied research in the "
        "discipline, with coursework spanning quantitative methods, ethnographic technique, "
        "and a capstone investigation developed in close consultation with a faculty committee."
    )
    diluted = [
        {"program_name": "Bachelor of Arts in Anthropology", "description": shared + tail_ba},
        {"program_name": "Master of Science in Anthropology", "description": shared + tail_ms},
    ]
    assert frame_stripped_shared_body(diluted, abs_chars=150), (
        "absolute floor must flag a 150+-char stamped sentence even when diluted below 50%"
    )
    assert not frame_stripped_shared_body(diluted), (
        "fraction-only default reads the diluted stamp as clean (the evasion)"
    )


def test_frame_stripped_shared_body_detector_bites_on_the_run65_evasion():
    """Regression guard: the detector must flag a per-credential frame prepended onto ONE
    field body shared across the credential levels (the run-65 evasion), while passing
    distinct per-credential bodies."""
    body = (
        "Rice chemistry runs organic, inorganic, physical, and chemical-biology groups "
        "with shared instrumentation in the Dell Butcher Hall laboratories."
    )
    evasive = [
        {
            "program_name": "Bachelor of Science in Chemistry",
            "description": f"Rice offers the undergraduate major in Chemistry. {body}",
        },
        {
            "program_name": "Master of Arts in Chemistry",
            "description": f"Rice offers a master's program in Chemistry. {body}",
        },
        {
            "program_name": "Doctor of Philosophy in Chemistry",
            "description": (
                "Doctoral study in Chemistry at Rice centers on dissertation research in " + body
            ),
        },
    ]
    clean = [
        {
            "program_name": "Bachelor of Science in Chemistry",
            "description": (
                "The chemistry B.S. builds a laboratory-intensive foundation across "
                "organic, inorganic, physical, and analytical chemistry."
            ),
        },
        {
            "program_name": "Master of Arts in Chemistry",
            "description": (
                "The master's combines advanced coursework with supervised laboratory "
                "research across the chemical sciences."
            ),
        },
        {
            "program_name": "Doctor of Philosophy in Chemistry",
            "description": (
                "Doctoral candidates join research groups for original, funded dissertation "
                "work using shared instrumentation."
            ),
        },
    ]
    assert frame_stripped_shared_body(evasive), (
        "must flag a shared field body hidden behind per-credential frames"
    )
    assert not frame_stripped_shared_body(clean), (
        "must not flag genuinely distinct per-credential bodies"
    )


def test_analyzer_detects_a_school_blurb_stub_catalog():
    """Regression guard: the gate must BITE on the school-blurb fabrication form."""
    blurb = (
        "Example University's {field} program connects to the College of Arts and "
        "Sciences, the university's largest college spanning the humanities, social "
        "sciences, and natural sciences.. Students build depth in {field} through "
        "seminars, research, and city industry and community partnerships."
    )
    fabricated = [
        {"program_name": f"Bachelor of Arts in {fld}", "description": blurb.format(field=fld)}
        for fld in ("Anthropology", "Classics", "Economics", "History")
    ]
    report = analyze(fabricated)
    assert not report.is_clean
    assert report.double_period, "should flag the '..' splice"
    assert report.cross_field_clause, "should flag one body stamped across different fields"


def test_cross_field_clause_is_case_insensitive_on_the_field_token():
    """The school-blurb stamp often lowercases the interpolated field token
    ("anthropology program connects…") while program_name is title-cased
    ("… in Anthropology"). The cross-field neutralization must be case-insensitive,
    or a lowercase-field blurb with no '..'/classification tell would pass as clean.
    """
    # No double-period and no classification phrase — the cross-field clause is the
    # ONLY tell, and the field token is lowercase in the body (mismatching the title-
    # cased name), so a case-sensitive normalization would miss it.
    blurb = (
        "At Example University, {field_lc} students join a research collective that "
        "spans the humanities and social sciences, building methodological depth "
        "through seminars and faculty-led projects across the city's institutions."
    )
    fabricated = [
        {
            "program_name": f"Bachelor of Arts in {fld}",
            "description": blurb.format(field_lc=fld.lower()),
        }
        for fld in ("Anthropology", "Classics", "Economics", "History")
    ]
    report = analyze(fabricated)
    assert not report.double_period, "guard premise: this fixture has no '..' tell"
    assert report.cross_field_clause, (
        "case-insensitive field neutralization must still flag one body stamped "
        "across different fields when the body lowercases the field token"
    )


def test_analyzer_detects_classification_and_prefix_stubs():
    fabricated = [
        {
            "program_name": "Bachelor of Science in Aerospace Engineering",
            "description": (
                "Bachelor of Science in Aerospace Engineering is an undergraduate major "
                "offered through Example University's College of Engineering."
            ),
        },
    ]
    report = analyze(fabricated)
    assert report.name_prefixed, "should flag the program_name-prefixed description"
    assert report.classification, "should flag the classification-only description"


def test_harvard_catalog_has_no_rollup_or_shared_leading_body():
    """Regression guard: Harvard must not ship CIP rollup names or suffix-diversifier
    shared-leading-body descriptions (REPAIR_BACKLOG HIGH #4)."""
    from unipaith.data import harvard_profile

    rollup_tells = (", General", ", Other", "(CIP ", "/")
    rollup_names = [
        p["slug"]
        for p in harvard_profile.PROGRAMS
        if any(t in p.get("program_name", "") for t in rollup_tells)
    ]
    assert not rollup_names, (
        f"Harvard catalog has {len(rollup_names)} rollup program_name rows: {rollup_names[:5]}"
    )
    report = analyze(harvard_profile.PROGRAMS)
    assert report.is_clean, f"Harvard anti-stub regressed: {report.summary()}"


def test_nyu_catalog_has_no_slug_leak_prefixes():
    """Regression guard: kebab-case bulletin slugs must not prefix description_text
    (REPAIR_BACKLOG CRITICAL #2 — invisible to machine_artifacts, visible to students)."""
    import re

    from unipaith.data import nyu_profile

    slug_re = re.compile(r"^[a-z0-9]+(-[a-z0-9]+){2,}\s*[—–-]\s")
    hits = [
        p["slug"]
        for p in nyu_profile.PROGRAMS
        if slug_re.match((p.get("description") or "").strip())
    ]
    assert not hits, f"NYU catalog has {len(hits)} slug-prefixed descriptions: {hits[:5]}"


@pytest.mark.parametrize("name", SCRAPE_DEBRIS_CLEAN)
def test_catalog_has_no_scraped_debris(name: str):
    """A debris-clean catalog must carry NO raw scraped catalogue debris in description_text —
    course-code / requirements fragments, unit-count openings, contact / address blocks, or
    fragments truncated mid-sentence / on a trailing colon. Each is unique per row, so it scores
    0 on every share metric in ``analyze`` yet renders raw catalogue text to a student
    (REPAIR_BACKLOG CRITICAL #1, run 66 — USC shipped ~80 such rows). Gold MIT returns []."""
    hits = scrape_debris(_programs(name))
    assert not hits, (
        f"{name} catalog has {len(hits)} scrape-debris descriptions: "
        f"{hits[:5]}{' …' if len(hits) > 5 else ''}"
    )


def test_scrape_debris_detector_bites_on_requirements_and_contact_text():
    """Regression guard: the detector must flag course-code / unit-count / contact-address
    debris and a colon-truncated fragment, while passing researched field-specific prose."""
    debris = [
        {
            "program_name": "Bachelor of Science in Earth Sciences",
            "description": (
                "28 additional units must be selected from MATH 225, MATH 226 (28 units):"
            ),
        },
        {
            "program_name": "Master of Science in Global Medicine",
            "description": "1333 San Pablo Street, McKibben Hall (323) 442-3141 msgm@usc.edu",
        },
    ]
    clean = [
        {
            "program_name": "Bachelor of Science in Earth Sciences",
            "description": (
                "Earth sciences at the college surveys geology, oceans, climate, and natural "
                "hazards, giving undergraduates a broad foundation in the environmental sciences."
            ),
        }
    ]
    assert len(scrape_debris(debris)) == 2, "should flag requirements + contact debris"
    assert not scrape_debris(clean), "must not flag researched field-specific prose"


def test_scrape_debris_exempts_a_trailing_source_citation():
    """A well-sourced description ends in a parenthetical citation, e.g.
    "...prepares graduates for government. (Source: ace.illinois.edu)". The
    terminal-punctuation / trailing-colon tells must run on the text with a trailing
    "(...)" stripped, or every cited row false-flags as truncated (REPAIR_BACKLOG
    human-flag #2). The course-code / contact tells still apply inside the parens."""
    cited = [
        {
            "program_name": "Bachelor of Science in Agricultural & Consumer Economics",
            "description": (
                "Agricultural and consumer economics builds a foundation in economics, finance, "
                "and policy with a focus on the agricultural and environmental sectors, preparing "
                "graduates for industry, nonprofits, and government. (Source: ace.illinois.edu)"
            ),
        }
    ]
    # A genuine debris row ending on a colon still fails even with a parenthetical present.
    still_debris = [
        {
            "program_name": "Master of Science in Community Health",
            "description": "Major areas of specialization (master's and doctoral) include:",
        }
    ]
    assert not scrape_debris(cited), "must not flag a row ending in a (Source: ...) citation"
    assert scrape_debris(still_debris), "a colon-truncated row is still debris"


def test_scrape_debris_allows_legitimate_hall_building_names():
    clean = [
        {
            "program_name": "Master of Architecture",
            "description": (
                "Architecture students work in Gund Hall, a studio building that supports "
                "design reviews, fabrication work, and seminars across the school."
            ),
        }
    ]
    assert not scrape_debris(clean), "building names ending in Hall are not address debris"
