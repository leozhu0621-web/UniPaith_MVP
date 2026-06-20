"""PromptCatalog model — round-trips and column defaults (data-driven catalog)."""

import pytest
from sqlalchemy import select

from unipaith.models.prompt_catalog import PromptCatalog


@pytest.mark.asyncio
async def test_prompt_catalog_roundtrip_and_defaults(db_session):
    row = PromptCatalog(
        key="demo_field",
        section="Basics",
        question="Which best describes you?",
        ask_kind="choice",
        value_type="categorical",
        options=["A", "B"],
        tier="essential",
        saves_to="demo_field",
        sort_order=3,
    )
    db_session.add(row)
    await db_session.flush()

    got = (
        await db_session.execute(select(PromptCatalog).where(PromptCatalog.key == "demo_field"))
    ).scalar_one()
    assert got.options == ["A", "B"]
    assert got.value_type == "categorical"
    assert got.active is True
    assert got.required is False
    assert got.display_logic == []
    assert got.reference_source is None
    assert got.sort_order == 3
