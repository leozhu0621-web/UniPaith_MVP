"""Profile export helpers (spec 10 §16 — Data Rights tab).

Pure functions over an already-serialized profile dict (the
``StudentProfileResponse.model_dump(mode="json")`` shape), so they are
trivially unit-testable with no DB:

- ``profile_to_pdf`` — a human-readable PDF of every stored signal.
- ``to_external_format`` — maps the Universal Profile onto the Common App /
  Coalition field schema. Read-only (UniPaith → external only; no write-back
  API exists). Anything not mapped is returned in ``unmapped`` so nothing is
  silently dropped.
"""

from __future__ import annotations

from typing import Any

# --- Common App / Coalition mapping ---------------------------------------

# profile scalar field -> external field path. Kept intentionally explicit so
# the `unmapped` list below is honest about what did and didn't carry over.
_SCALAR_MAP: dict[str, str] = {
    "first_name": "personal.legal_name.first",
    "last_name": "personal.legal_name.last",
    "preferred_name": "personal.preferred_name",
    "preferred_pronouns": "personal.pronouns",
    "date_of_birth": "personal.date_of_birth",
    "nationality": "personal.citizenship",
    "country_of_residence": "personal.country_of_residence",
    "secondary_email": "contact.email",
    "secondary_phone": "contact.phone",
    "goals_text": "writing.personal_statement_notes",
    "bio_text": "writing.additional_information",
}

# list sections we transform explicitly (everything else lands in `unmapped`).
_HANDLED_LISTS = {"academic_records", "test_scores", "activities"}

# profile keys that are internal plumbing, never part of an external export.
_META_KEYS = {
    "id",
    "user_id",
    "created_at",
    "updated_at",
    "email_verified",
    "phone_verified",
    "id_verification_status",
    "discovery_completion",
    "strategy_active_id",
    "onboarding",
}


def _is_empty(value: Any) -> bool:
    return value in (None, "", [], {})


def to_external_format(profile: dict, fmt: str = "commonapp") -> dict:
    """Map the Universal Profile onto the Common App / Coalition schema.

    Returns ``{"format", "fields", "unmapped"}``. ``unmapped`` lists the
    populated profile keys that have no destination in the target schema, so
    the student can see exactly what does not carry over.
    """
    fields: dict[str, Any] = {}

    for src, dest in _SCALAR_MAP.items():
        if not _is_empty(profile.get(src)):
            fields[dest] = profile.get(src)

    academics = profile.get("academic_records") or []
    if academics:
        fields["education.colleges"] = [
            {
                "name": a.get("institution_name"),
                "degree": a.get("degree_type"),
                "field_of_study": a.get("field_of_study"),
                "gpa": a.get("gpa"),
                "gpa_scale": a.get("gpa_scale"),
            }
            for a in academics
        ]

    tests = profile.get("test_scores") or []
    if tests:
        fields["testing.scores"] = [
            {
                "type": t.get("test_type"),
                "total": t.get("total_score"),
                "sections": t.get("section_scores"),
                "date": t.get("test_date"),
            }
            for t in tests
        ]

    # Common App caps the activities list at 10.
    activities = (profile.get("activities") or [])[:10]
    if activities:
        fields["activities"] = [
            {
                "type": a.get("activity_type"),
                "name": a.get("title"),
                "organization": a.get("organization"),
                "hours_per_week": a.get("hours_per_week"),
                "description": a.get("description"),
            }
            for a in activities
        ]

    handled = set(_SCALAR_MAP) | _HANDLED_LISTS | _META_KEYS
    unmapped = sorted(
        key for key, value in profile.items() if key not in handled and not _is_empty(value)
    )

    return {"format": fmt, "fields": fields, "unmapped": unmapped}


# --- PDF export ------------------------------------------------------------


def _safe(value: Any) -> str:
    """fpdf2 core fonts are Latin-1; replace anything outside it so a name in
    a non-Latin script never raises mid-render."""
    return str(value).encode("latin-1", "replace").decode("latin-1")


def profile_to_pdf(profile: dict) -> bytes:
    """Render a human-readable PDF of the stored profile signals."""
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 12, "UniPaith - Profile Export", new_x="LMARGIN", new_y="NEXT")

    name = " ".join(x for x in [profile.get("first_name"), profile.get("last_name")] if x)
    pdf.set_font("Helvetica", "", 11)
    if name:
        pdf.cell(0, 7, _safe(name), new_x="LMARGIN", new_y="NEXT")
    meta_line = " · ".join(
        x for x in [profile.get("preferred_pronouns"), profile.get("country_of_residence")] if x
    )
    if meta_line:
        pdf.cell(0, 7, _safe(meta_line), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    def heading(text: str) -> None:
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 9, _safe(text), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)

    def line(label: str, value: Any) -> None:
        if _is_empty(value):
            return
        pdf.multi_cell(0, 6, _safe(f"{label}: {value}"))

    heading("Personal")
    line("Nationality", profile.get("nationality"))
    line("Preferred name", profile.get("preferred_name"))
    line("Goals", profile.get("goals_text"))
    line("Bio", profile.get("bio_text"))
    pdf.ln(2)

    sections: list[tuple[str, str, list[str]]] = [
        (
            "Academics",
            "academic_records",
            ["institution_name", "degree_type", "field_of_study", "gpa"],
        ),
        ("Test Scores", "test_scores", ["test_type", "total_score"]),
        ("Languages", "languages", ["language", "proficiency_level"]),
        ("Research", "research_entries", ["title", "role", "institution_lab"]),
        ("Activities", "activities", ["title", "activity_type", "organization"]),
        ("Work & Service", "work_experiences", ["role_title", "organization", "experience_type"]),
        ("Competitions", "competitions", ["name", "level", "result"]),
        ("Portfolio", "portfolio_items", ["title", "item_type", "url"]),
        ("Online Presence", "online_presence", ["platform_type", "url"]),
    ]
    for title, key, attrs in sections:
        items = profile.get(key) or []
        if not items:
            continue
        heading(title)
        for item in items:
            parts = [str(item.get(a)) for a in attrs if not _is_empty(item.get(a))]
            if parts:
                pdf.multi_cell(0, 6, _safe(" — ".join(parts)))
        pdf.ln(2)

    return bytes(pdf.output())
