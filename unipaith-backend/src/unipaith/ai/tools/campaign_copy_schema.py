"""JSON schema for the CampaignAudienceCopySuggester agent's tool (45 §16).

Drafts external-email subject + body for an institution Campaign. Shape mirrors
``Spec/45-ai-agents-claude.md §16``:
``{subject, body, alternate_subjects (max 3), preview_text}``.
"""

SCHEMA_VERSION = 1

SUBMIT_CAMPAIGN_COPY_TOOL = {
    "name": "submit_campaign_copy",
    "description": (
        "Return a ready-to-send marketing email draft for a higher-education "
        "institution's outreach campaign. Write warm, specific, second-person "
        "copy aimed at prospective students. Honor the campaign objective and "
        "the call-to-action. Personalization tokens {{first_name}}, "
        "{{program_name}} and {{event_link}} may appear in the body and will be "
        "substituted at send time — use them naturally, never invent other "
        "tokens. No emojis, no ALL-CAPS, no spammy phrasing."
    ),
    "input_schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["subject", "body", "alternate_subjects", "preview_text"],
        "properties": {
            "subject": {
                "type": "string",
                "minLength": 1,
                "maxLength": 120,
                "description": "Primary subject line. Concrete and benefit-led.",
            },
            "body": {
                "type": "string",
                "minLength": 1,
                "maxLength": 1800,
                "description": (
                    "Email body in plain text / light markdown. 2–4 short "
                    "paragraphs ending in the call-to-action."
                ),
            },
            "alternate_subjects": {
                "type": "array",
                "maxItems": 3,
                "description": "Up to 3 alternate subject lines to A/B test.",
                "items": {"type": "string", "maxLength": 120},
            },
            "preview_text": {
                "type": "string",
                "maxLength": 160,
                "description": "Inbox preview / preheader text (one sentence).",
            },
        },
    },
}
