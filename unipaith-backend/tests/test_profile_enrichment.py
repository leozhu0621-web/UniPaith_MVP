"""Phase 2 — the verification gate never fabricates, and the engine fills only
verified fields, omitting the rest."""

from unipaith.profile_standard.manifest import Field
from unipaith.services.profile_enrichment import (
    Evidence,
    apply_patch,
    enrich,
    plan,
    verify,
)

FP = "first_party"
AUTH = "authoritative"


def _ev(value, url, authority="authoritative", source="Src"):
    return Evidence(value=value, source=source, source_url=url, authority=authority)


# --- gate: per-rule behavior ---


def test_authoritative_2x_rejects_single_source():
    d = verify("authoritative_2x", [_ev(100, "https://a.org")])
    assert d.accept is False
    assert "independent" in d.reason


def test_authoritative_2x_rejects_disagreement():
    d = verify("authoritative_2x", [_ev(100, "https://a.org"), _ev(200, "https://b.org")])
    assert d.accept is False
    assert "disagree" in d.reason


def test_authoritative_2x_accepts_two_independent_agreeing():
    d = verify("authoritative_2x", [_ev(100, "https://a.org"), _ev(102, "https://b.org")])
    assert d.accept is True
    assert d.value == 100
    assert d.source_url == "https://a.org"


def test_authoritative_2x_two_items_same_domain_not_independent():
    d = verify(
        "authoritative_2x",
        [_ev(100, "https://a.org/x"), _ev(100, "https://www.a.org/y")],
    )
    assert d.accept is False  # same domain → not 2 independent sources


def test_first_party_requires_first_party_authority():
    d = verify("first_party", [_ev(5, "https://agg.com", authority=AUTH)])
    assert d.accept is False
    d2 = verify("first_party", [_ev(5, "https://official.edu", authority=FP)])
    assert d2.accept is True
    assert d2.value == 5


def test_official_or_curated_accepts_single_cited():
    d = verify("official_or_curated", [_ev("Hello", "https://x.edu")])
    assert d.accept is True


def test_cited_rule_rejects_when_no_citation():
    d = verify("first_party", [Evidence(value=5, source="", source_url="", authority=FP)])
    assert d.accept is False
    assert "cited" in d.reason


def test_none_accepts_uncited_value():
    d = verify("none", [Evidence(value="MIT report", source="", source_url="")])
    assert d.accept is True
    assert d.value == "MIT report"


def test_numeric_tolerance_boundary():
    # within 5%
    assert verify("authoritative_2x", [_ev(100, "https://a.org"), _ev(104, "https://b.org")]).accept
    # beyond 5%
    assert not verify(
        "authoritative_2x", [_ev(100, "https://a.org"), _ev(120, "https://b.org")]
    ).accept


# --- gate: no-fabrication contract (property over many cases) ---


def test_no_fabrication_contract():
    rules = ["first_party", "authoritative_2x", "official_or_curated", "none"]
    cases: list[list[Evidence]] = [
        [],
        [_ev(None, "https://a.org")],
        [_ev(1, "", authority=FP)],
        [_ev(1, "https://a.org", authority=FP)],
        [_ev(1, "https://a.org"), _ev(1, "https://b.org")],
        [_ev(1, "https://a.org"), _ev(9, "https://b.org")],
        [Evidence(value="x", source="", source_url="")],
    ]
    for rule in rules:
        for ev in cases:
            d = verify(rule, ev)
            if d.accept and rule != "none":
                # An accepted CITED field must carry a value and a resolvable url.
                assert d.value is not None and d.source_url, (rule, ev, d)


# --- engine: planning + orchestration ---


def test_plan_empty_program_includes_required_fields():
    paths = plan("program", {})
    assert "outcomes_data.median_salary" in paths
    assert "application_requirements.materials" in paths


def test_plan_stale_returns_all_fields():
    # Even a full snapshot, if stale (older version), re-plans everything.
    snap = {"program_name": "X", "outcomes_data": {"median_salary": 1}}
    paths = plan("program", snap, profile_version=0)
    assert "cost_data.tuition_usd" in paths  # a field not in the snapshot, included because stale


class _FixtureResearcher:
    def __init__(self, by_path: dict[str, list[Evidence]]):
        self.by_path = by_path

    def gather(self, level: str, target: str, field: Field) -> list[Evidence]:
        return self.by_path.get(field.path, [])


def test_enrich_fills_verified_omits_unverifiable():
    researcher = _FixtureResearcher(
        {
            # verifiable first-party field
            "outcomes_data.median_salary": [
                _ev(143000, "https://mitsloan.mit.edu/report", authority=FP)
            ],
            # unverifiable: authoritative_2x with only one source
            "outcomes_data.median_earnings_10yr": [_ev(150000, "https://a.org")],
        }
    )
    res = enrich("program", "mit-sloan-mban", {}, researcher)
    assert "outcomes_data.median_salary" in res.filled
    assert apply_patch({}, res.patch)["outcomes_data"]["median_salary"] == 143000
    # the version stamp is written
    assert res.patch["_standard"]["version"] >= 1
    # fields with no/weak evidence are omitted, never invented
    assert any(o["path"] == "application_requirements.materials" for o in res.omitted)
