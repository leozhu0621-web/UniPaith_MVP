"""Spec 74 §1/§2 — CRM lead export (wrap-around-Slate) + i18n locale. Pure functions."""

from __future__ import annotations

from unipaith.services.interop import (
    SLATE_LEAD_COLUMNS,
    resolve_locale,
    serialize_leads_csv,
    to_slate_lead_row,
)


def test_to_slate_lead_row_maps_and_omits():
    row = to_slate_lead_row(
        {
            "first_name": "Ada",
            "last_name": "Lovelace",
            "email": "ada@example.com",
            "field_of_interest": "Computer Science",
            "unmapped_field": "should be dropped",
        }
    )
    assert row == {
        "first": "Ada",
        "last": "Lovelace",
        "email": "ada@example.com",
        "program": "Computer Science",
    }
    assert "unmapped_field" not in row  # only mapped fields cross the boundary


def test_serialize_leads_csv():
    csv_text = serialize_leads_csv(
        [
            {"first_name": "Ada", "email": "ada@example.com"},
            {"first_name": "Alan", "last_name": "Turing", "country": "UK"},
        ]
    )
    lines = csv_text.strip().splitlines()
    assert lines[0] == ",".join(SLATE_LEAD_COLUMNS)  # stable header
    assert "Ada" in lines[1]
    assert "Turing" in lines[2] and "UK" in lines[2]


def test_resolve_locale():
    supported = ["en", "fr", "es", "zh"]
    assert resolve_locale("fr-FR,fr;q=0.9,en;q=0.8", supported) == "fr"  # base-lang fallback
    assert resolve_locale("es", supported) == "es"  # exact
    assert resolve_locale("de-DE", supported) == "en"  # unsupported → default
    assert resolve_locale(None, supported) == "en"  # no header → default
    assert resolve_locale("zh-CN,zh;q=0.9", supported) == "zh"
