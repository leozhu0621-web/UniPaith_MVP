"""Spec 38 §3 / §9 + Spec 46 §6 — fairness contract (the feasibility-vs-selection
asymmetry).

FOUNDER GOVERNANCE DECISION (2026-06-18). Visa / immigration / eligibility IS a
legitimate consideration — but ONLY in the student's OWN direction, and ONLY as
*feasibility*, never as *selection*. The single defensible framing this contract
encodes (and pins so a future code path cannot silently break it):

  • student→program (s→p) FEASIBILITY — ALLOWED. If a student needs a study visa
    AND a program cannot enrol / sponsor an international applicant, that program
    is INFEASIBLE FOR HER. A clearly-labeled, gated, confidence-aware feasibility
    veto sinks it in HER own ranking (she literally cannot attend). This HELPS the
    student avoid a dead end. It lives in matching.py's s→p path and reads exactly
    one derived student key (`needs_visa_sponsorship`) against one program
    capability key (`sponsors_international`). The derived student boolean is
    projected in match_service from the student's OWN StudentVisaInfo.visa_required
    — nothing more of the immigration record is read.

  • program→student (p→s) SELECTION — FORBIDDEN. A program ranking APPLICANTS must
    NEVER use immigration status. The reverse direction (cpef_program_to_student)
    and every applicant-ranking / scoring module must not read any visa /
    immigration / nationality / SEVIS / financial-proof / country-requirement /
    citizenship / prior-refusal field. This is the Spec 38 §3/§9 + Spec 46 §6
    invariant, intact and unchanged.

Why a SOURCE-level contract: it guards the *inputs* to scoring, not a single
computed value, so it can't be bypassed by a new code path that happens to read a
forbidden field. The token checks operate on COMMENT-STRIPPED code (string
literals — i.e. the sparse-dict keys that carry the signal names — are kept), so
this file's own explanatory prose about visas never trips the contract: only what
the matcher actually *reads* counts.
"""

import inspect
import io
import pathlib
import re
import tokenize

import pytest

from unipaith.services import matching
from unipaith.services.international_service import InternationalService

_SRC = pathlib.Path(__file__).resolve().parent.parent / "src" / "unipaith"


def _code_only(text: str) -> str:
    """Return ``text`` with Python comments removed but string literals KEPT.

    The contract guards what the matcher *reads as code* — the sparse-dict keys
    (string literals like ``"needs_visa_sponsorship"``) ARE the signal references,
    so they must stay; only ``# ...`` comments (the explanatory governance prose
    that legitimately discusses visas) are stripped. Lowercased for matching.
    Falls back to the raw text if tokenizing fails (never silently passes a file).
    """
    try:
        parts: list[str] = []
        for tok in tokenize.generate_tokens(io.StringIO(text).readline):
            if tok.type == tokenize.COMMENT:
                continue
            parts.append(tok.string)
        return " ".join(parts).lower()
    except Exception:
        return text.lower()


# Modules that feed the fitness_score / confidence_score / probability bands.
# matching.py + match_service.py are handled with their own targeted assertions
# below (matching.py owns the ALLOWED s→p feasibility veto; match_service.py owns
# the feasibility PROJECTION that derives the single boolean), so a blanket token
# ban would be wrong for those two. Everything here must be visa-free outright.
_RANKING_MODULES = [
    "services/match_banding.py",
    "services/program_features.py",
    "ai/feature_emitter.py",
    "ai/probability.py",
    "ai/rationale.py",
]

# SELECTION-GRADE immigration identifiers — institution-side processing,
# nationality, citizenship, origin, prior refusals, SEVIS, financial-proof,
# country requirements. These are the fields whose use as a matching input would
# turn immigration into a SELECTION criterion. They are forbidden EVERYWHERE in
# the matcher, in BOTH directions and in BOTH the feasibility and projection
# surfaces — even the s→p feasibility path may read NONE of them (it derives a
# single boolean from visa_required and stops). Plain words like "international"
# are intentionally NOT here; these are the concrete field/model names.
_FORBIDDEN_EVERYWHERE = [
    "internationalprocessing",
    "visa_outcome",
    "financial_proof",
    "immigration_doc",
    "sevis",
    "country_requirement",
    "credential_normalized_gpa",
    "nationality",
    "country_of_citizenship",
    "country_of_birth",
    "prior_visa_refusals",
    "current_immigration_status",
    "visa_type_current",
]

# The ONLY visa-related identifiers the matcher may read, and ONLY in their
# sanctioned places. They are the clearly-labeled feasibility signal — a single
# derived student boolean checked against a single program capability — plus the
# minimal projection plumbing that derives that boolean from the student's OWN
# record. None carries nationality / origin / refusal data.
_ALLOWED_MATCHING_TOKENS = {
    "needs_visa_sponsorship",  # derived student-side feasibility flag (s→p only)
    "sponsors_international",  # program capability the feasibility veto reads
    "visa_feasibility",  # the deal-breaker key label
}
# match_service.py additionally derives the flag from the student's own row, so it
# is permitted these projection-only identifiers on top of the matching tokens.
_ALLOWED_PROJECTION_TOKENS = _ALLOWED_MATCHING_TOKENS | {
    "studentvisainfo",  # the student's OWN visa row (queried to derive the flag)
    "visa_required",  # the single field read off it (the gate for the boolean)
    "visa_info",  # the relationship/local name for that row
    "visa",  # the local variable holding the queried row in the projection
}


def test_selection_grade_immigration_excluded_from_all_matching_inputs():
    """The SELECTION-GRADE immigration fields (institution-side processing,
    nationality, citizenship, origin, prior refusals, SEVIS, financial proof,
    country requirements) must never feed ANY matching module, in EITHER
    direction and on EITHER surface — not the ranking modules, not the matcher,
    not the projection. This is the Spec 38 §3/§9 + Spec 46 §6 invariant, intact.

    Operates on comment-stripped code so the governance prose that names these
    fields only to say "never read them" does not trip the contract."""
    offenders = []
    modules = _RANKING_MODULES + ["services/matching.py", "services/match_service.py"]
    for mod in modules:
        path = _SRC / mod
        if not path.exists():
            continue
        code = _code_only(path.read_text(encoding="utf-8"))
        for token in _FORBIDDEN_EVERYWHERE:
            if token in code:
                offenders.append(f"{mod} references '{token}'")
    assert not offenders, (
        "Selection-grade immigration fields must never feed matching "
        "(Spec 38 §3/§9, 46 §6): " + "; ".join(offenders)
    )


def test_pure_ranking_modules_have_zero_visa_tokens():
    """Belt-and-suspenders: outside matching.py (the ALLOWED s→p feasibility
    veto) and match_service.py (the feasibility PROJECTION), no ranking module may
    reference ANY visa/immigration token — not even the feasibility ones. The
    feasibility signal is confined to those two files; nothing else reasons about
    visas. program_features.py legitimately PROJECTS the program capability
    `sponsors_international` so the s→p veto can read it (feasibility plumbing, not
    selection) — exactly that one token is allowed there, nothing else.

    Comment-stripped so a stray explanatory word never counts."""
    offenders = []
    visa_words = ["visa", "immigration", "sponsor"]
    for mod in _RANKING_MODULES:
        path = _SRC / mod
        if not path.exists():
            continue
        code = _code_only(path.read_text(encoding="utf-8"))
        # remove the one sanctioned program-capability projection token so it does
        # not register as a "sponsor" hit in program_features.py.
        if mod == "services/program_features.py":
            code = code.replace("sponsors_international", "")
        for w in visa_words:
            if w in code:
                offenders.append(f"{mod} references visa word '{w}'")
                break
    assert not offenders, (
        "Only matching.py's s→p path, match_service's projection, and "
        "program_features' sponsors_international projection may mention visas; "
        "found leakage in a pure ranking module: " + "; ".join(offenders)
    )


def test_program_to_student_selection_path_never_reads_visa():
    """p→s SELECTION is FORBIDDEN to read immigration status. Assert the SOURCE of
    cpef_program_to_student — the function a program uses to rank APPLICANTS —
    contains no visa / immigration / nationality / sponsorship token at all (in
    code OR comment; the selection path has no reason to even mention them). A
    program may not select on immigration status (Spec 38 §3/§9, 46 §6)."""
    src = inspect.getsource(matching.cpef_program_to_student).lower()
    forbidden = [
        "visa",
        "immigration",
        "nationality",
        "citizenship",
        "sponsor",
        "needs_visa_sponsorship",
        "sponsors_international",
    ]
    leaks = [tok for tok in forbidden if tok in src]
    assert not leaks, (
        "cpef_program_to_student (the p→s applicant-selection path) must NEVER "
        f"read immigration status — found: {leaks}"
    )


def test_program_pref_overlay_never_loads_visa():
    """The p→s direction is fed by the program-preference overlay
    (_overlay_program_prefs), which builds the program's view of its target
    applicant. Its SOURCE must read only academic/field/level preferences — never
    a visa / immigration / sponsorship / nationality field — so no immigration
    status can leak into the selection direction via the overlay."""
    from unipaith.services.match_service import MatchService

    src = inspect.getsource(MatchService._overlay_program_prefs).lower()
    forbidden = ["visa", "immigration", "nationality", "citizenship", "sponsor"]
    leaks = [tok for tok in forbidden if tok in src]
    assert not leaks, (
        "_overlay_program_prefs (feeds the p→s selection direction) must NEVER "
        f"load immigration status — found: {leaks}"
    )


def test_matching_visa_tokens_are_exactly_the_labeled_feasibility_signal():
    """Inside matching.py, the ONLY visa-related identifiers in CODE are the
    clearly-labeled s→p feasibility tokens. Any other visa/immigration identifier
    appearing in the matcher's code would be un-sanctioned wiring and fails here.

    Comment-stripped (string literals kept, since the sparse-dict keys ARE the
    signal references) so the extensive governance comment block — which discusses
    visas, sponsorship and immigration at length to JUSTIFY the asymmetry — does
    not count. This pins the ALLOWED side precisely: feasibility may use
    `needs_visa_sponsorship` / `sponsors_international` / `visa_feasibility` and
    nothing more."""
    code = _code_only((_SRC / "services" / "matching.py").read_text(encoding="utf-8"))
    candidates = set(re.findall(r"[a-z_][a-z0-9_]*", code))
    stems = ("visa", "immigration", "sponsor", "nationality", "citizenship")
    visa_idents = {c for c in candidates if any(stem in c for stem in stems)}
    unexpected = visa_idents - _ALLOWED_MATCHING_TOKENS
    assert not unexpected, (
        "matching.py code may only use the labeled s→p feasibility tokens "
        f"{sorted(_ALLOWED_MATCHING_TOKENS)}; found unexpected: {sorted(unexpected)}"
    )


def test_match_service_visa_tokens_are_only_the_feasibility_projection():
    """Inside match_service.py, the ONLY visa-related identifiers in CODE are the
    feasibility tokens PLUS the minimal projection plumbing that derives the
    single `needs_visa_sponsorship` boolean from the student's OWN visa row
    (StudentVisaInfo.visa_required). No nationality / refusal / citizenship /
    processing identifier may appear — the projection reads ONE field and stops.

    Comment-stripped so the projection's explanatory prose does not count."""
    code = _code_only((_SRC / "services" / "match_service.py").read_text(encoding="utf-8"))
    candidates = set(re.findall(r"[a-z_][a-z0-9_]*", code))
    stems = ("visa", "immigration", "sponsor", "nationality", "citizenship")
    visa_idents = {c for c in candidates if any(stem in c for stem in stems)}
    unexpected = visa_idents - _ALLOWED_PROJECTION_TOKENS
    assert not unexpected, (
        "match_service.py code may only use the feasibility projection tokens "
        f"{sorted(_ALLOWED_PROJECTION_TOKENS)}; found unexpected: {sorted(unexpected)}"
    )


def test_feasibility_veto_fires_only_in_student_direction_and_is_gated():
    """Behavioural pin of the asymmetry. A confirmed-ineligible program (student
    needs sponsorship, program known-cannot-sponsor) is BURIED in the STUDENT's
    s→p ranking; the same pair, scored p→s, is byte-identical regardless of the
    visa keys — the program's view of the applicant cannot see them. Unknown
    sponsorship never vetoes (gated); a domestic student never vetoes (gated)."""
    from unipaith.services.match.params import DEFAULT_PARAMS
    from unipaith.services.matching import (
        ProgramFeatures,
        StudentFeatures,
        cpef,
        cpef_program_to_student,
    )

    # Identical fit on both sides; the only difference is the visa keys.
    base_student = {"field_of_study": "data_science", "education_level": "bachelors", "gpa": 3.6}
    base_program = {"fields_offered": ["data_science"], "pref_min_gpa": 3.0}

    visa_student = StudentFeatures(
        sparse={**base_student, "needs_visa_sponsorship": True}, extractor_quality=0.95
    )
    no_visa_student = StudentFeatures(sparse=dict(base_student), extractor_quality=0.95)

    cant_sponsor = ProgramFeatures(
        program_id="x", sparse={**base_program, "sponsors_international": False}
    )
    unknown_sponsor = ProgramFeatures(program_id="x", sparse=dict(base_program))

    # s→p: a visa-needing student facing a known-cannot-sponsor program is buried.
    buried, buried_bd = cpef(visa_student, cant_sponsor, params=DEFAULT_PARAMS)
    clean, _ = cpef(visa_student, unknown_sponsor, params=DEFAULT_PARAMS)
    assert buried < clean, "the infeasible program must sink in HER ranking"
    assert buried_bd["hard_floor"] is True
    assert any(db["key"] == "visa_feasibility" for db in buried_bd["dealbreakers"])

    # Gated: an unknown-sponsorship program is NOT vetoed (no assumption that an
    # unknown program cannot sponsor).
    _, clean_bd = cpef(visa_student, unknown_sponsor, params=DEFAULT_PARAMS)
    assert all(db["key"] != "visa_feasibility" for db in clean_bd["dealbreakers"])

    # Gated: a domestic student (no visa need) is never vetoed, even by a
    # known-cannot-sponsor program.
    _, dom_bd = cpef(no_visa_student, cant_sponsor, params=DEFAULT_PARAMS)
    assert all(db["key"] != "visa_feasibility" for db in dom_bd["dealbreakers"])

    # p→s SELECTION: the program's view of the applicant is BYTE-IDENTICAL whether
    # or not the student needs a visa and whether or not the program sponsors —
    # immigration status simply does not exist in the selection direction.
    ps_visa, ps_visa_bd = cpef_program_to_student(visa_student, cant_sponsor, params=DEFAULT_PARAMS)
    ps_novisa, ps_novisa_bd = cpef_program_to_student(
        no_visa_student, unknown_sponsor, params=DEFAULT_PARAMS
    )
    assert ps_visa == ps_novisa, "p→s selection must not change with visa status"
    assert ps_visa_bd == ps_novisa_bd, "p→s breakdown must be identical regardless of visa"


def test_international_processing_model_not_imported_by_matcher():
    """Belt-and-suspenders: the matcher must not import the institution-side
    international-PROCESSING model. (The student-side feasibility flag is a derived
    boolean projected in match_service from StudentVisaInfo.visa_required — never
    the processing model.)"""
    for mod in ("services/matching.py", "services/match_service.py"):
        path = _SRC / mod
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8").lower()
        assert "internationalprocessing" not in text, (
            f"{mod} references InternationalProcessing — keep institution-side "
            "international processing out of matching."
        )


@pytest.mark.asyncio
async def test_feasibility_band_is_labelled_operational_only():
    """The feasibility band the INSTITUTION sees is explicitly operational — the
    packet block carries the fairness note so the UI can render it (§3). Distinct
    from the student-side s→p feasibility veto above."""
    result = InternationalService._feasibility_band(None, {"financial_proof_available": True})
    assert set(result.keys()) == {"band", "reasons"}
    assert "score" not in result
    assert result["band"] in {"blocked", "at_risk", "moderate", "strong"}
