"""Catalog content expansion — asserts the 23→40 prompt catalog growth.

TDD step 1: WRITE FAILING TEST first.
Verifies:
- After ensure_seeded, load() returns >= 40 entries
- New keys present with correct ask_kind
- Changed keys reflect their new ask_kind
- Essentials list is exactly the original 6 keys
"""

import pytest

from unipaith.services.catalog_service import CatalogService
from unipaith.services.enrichment_planner import CATALOG


@pytest.mark.asyncio
async def test_catalog_has_at_least_40_entries(db_session):
    """After seeding, the catalog must have at least 40 active entries."""
    svc = CatalogService(db_session)
    await svc.ensure_seeded()
    loaded = await svc.load()
    assert len(loaded) >= 40, f"Expected >=40 entries, got {len(loaded)}"


@pytest.mark.asyncio
async def test_new_keys_present_with_correct_ask_kind(db_session):
    """New fields added in the expansion are present with the right ask_kind."""
    svc = CatalogService(db_session)
    await svc.ensure_seeded()
    loaded = await svc.load()
    by_key = {e["key"]: e for e in loaded}

    # Sample of new fields → expected ask_kind
    new_field_ask_kinds = {
        "institution_type": "multi",
        "gpa_scale": "choice",
        "career_goal": "keywords",
        "tests_taken": "multi",
        "first_generation": "choice",
        "current_education_level": "choice",
        "english_proficiency": "choice",
        "strongest_subjects": "keywords",
        "specialization": "keywords",
        "intended_start": "choice",
        "study_mode": "choice",
        "research_experience": "choice",
        "goal_after_degree": "choice",
        "preferred_setting": "multi",
        "school_size": "choice",
        "climate": "choice",
        "distance_from_home": "choice",
    }
    for key, expected_ask_kind in new_field_ask_kinds.items():
        assert key in by_key, f"New key '{key}' missing from seeded catalog"
        assert by_key[key]["ask_kind"] == expected_ask_kind, (
            f"'{key}' expected ask_kind={expected_ask_kind!r}, got {by_key[key]['ask_kind']!r}"
        )


@pytest.mark.asyncio
async def test_changed_fields_reflect_new_ask_kind(db_session):
    """Existing fields updated in the expansion carry their new ask_kind."""
    svc = CatalogService(db_session)
    await svc.ensure_seeded()
    loaded = await svc.load()
    by_key = {e["key"]: e for e in loaded}

    # activities and identity: text→multi, ask_kind→keywords
    assert by_key["activities"]["ask_kind"] == "keywords", (
        "activities should be ask_kind=keywords after expansion"
    )
    assert by_key["identity"]["ask_kind"] == "keywords", (
        "identity should be ask_kind=keywords after expansion"
    )

    # nationality and country_of_residence: ask_kind→typeahead
    assert by_key["nationality"]["ask_kind"] == "typeahead", (
        "nationality should be ask_kind=typeahead after expansion"
    )
    assert by_key["country_of_residence"]["ask_kind"] == "typeahead", (
        "country_of_residence should be ask_kind=typeahead after expansion"
    )


@pytest.mark.asyncio
async def test_essentials_are_exactly_original_six(db_session):
    """The 6 essential keys must remain exactly the original 6, in order."""
    expected_essentials = [
        "gender",
        "nationality",
        "date_of_birth",
        "country_of_residence",
        "target_degree_level",
        "field_of_interest",
    ]
    # Check CATALOG constant
    actual_essentials = [f["key"] for f in CATALOG if f["tier"] == "essential"]
    assert actual_essentials == expected_essentials, (
        f"CATALOG essentials changed: {actual_essentials}"
    )

    # Also check DB-loaded catalog preserves the same essential set
    svc = CatalogService(db_session)
    await svc.ensure_seeded()
    loaded = await svc.load()
    db_essentials = [e["key"] for e in loaded if e["tier"] == "essential"]
    # DB order may differ, but set must match
    assert set(db_essentials) == set(expected_essentials), (
        f"DB catalog essentials differ: {db_essentials}"
    )
    assert len(db_essentials) == 6, f"Expected 6 essentials, got {len(db_essentials)}"
