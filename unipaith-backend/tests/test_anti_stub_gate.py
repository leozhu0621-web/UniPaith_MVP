"""CI-enforced anti-stub gates for enriched university catalogs (SKILL.md §8.5)."""

from unipaith.data import nyu_profile as nyu
from unipaith.profile_standard.anti_stub import catalog_anti_stub_violations


def test_nyu_catalog_passes_anti_stub_gates():
    errors = catalog_anti_stub_violations(
        nyu.PROGRAMS, lambda s: nyu._field_key(s["program_name"])
    )
    assert not errors, f"NYU anti-stub violations: {errors}"


def test_nyu_has_no_school_blurb_descriptions():
    blurb = sum(
        1
        for p in nyu.PROGRAMS
        if "connects to" in (p.get("description") or "")
        and "Students build depth" in (p.get("description") or "")
    )
    assert blurb == 0, f"{blurb} school-blurb descriptions remain"


def test_nyu_departments_are_real_schools():
    dept_eq_field = sum(
        1
        for p in nyu.PROGRAMS
        if p.get("department") == nyu._field_key(p["program_name"])
    )
    assert dept_eq_field == 0, f"{dept_eq_field} programs still echo field as department"
