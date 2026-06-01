"""JSON schema for CountryRequirementAdvisor (Spec 38 §5).

Given an applicant's country, the agent suggests the extra documents /
attestations / apostille steps that country typically adds to an admissions
file. The calling service has a platform-default pack table to fall back on, so
a malformed/empty tool call is non-fatal. The reviewer confirms every item — the
agent never marks anything received or verified.
"""

SCHEMA_VERSION = 1

SUBMIT_COUNTRY_PACK_TOOL = {
    "name": "submit_country_pack",
    "description": (
        "List the country-specific documents and attestations an international "
        "applicant from this country typically must provide (e.g. apostille, "
        "credential evaluation, certified translation). Keep items operational "
        "and document-focused; suggestions only — a human confirms each."
    ),
    "input_schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["country_name", "requirements"],
        "properties": {
            "country_name": {
                "type": "string",
                "maxLength": 120,
                "description": "Display name of the country.",
            },
            "requirements": {
                "type": "array",
                "maxItems": 12,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["item"],
                    "properties": {
                        "item": {
                            "type": "string",
                            "maxLength": 160,
                            "description": "Short label for the required document/step.",
                        },
                        "description": {
                            "type": "string",
                            "maxLength": 300,
                            "description": "Optional one-line explanation.",
                        },
                    },
                },
            },
        },
    },
}

# ── Changelog ──────────────────────────────────────────────────────────────
# v1 (2026-06-01): initial schema for Spec 38 CountryRequirementAdvisor.
