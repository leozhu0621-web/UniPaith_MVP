"""Material ingest agent — Uni reads an uploaded file and extracts profile data.

Sends the uploaded document to Claude as a NATIVE content block (PDF + images go
straight to the vision-capable model; Word/text are extracted to text first),
then forces a single tool call that returns structured, confirm-ready profile
signals. It NEVER fabricates — it extracts only what the document actually
contains and omits the rest. On any failure it returns ``None`` so the service
falls back to "enter manually" (never a 5xx).

Cost-ledger slot: this runs under the ``workshop_coach`` agent name — like the
workshop coaches it is user-initiated artifact work (the student uploading their
own file IS the consent signal, so it sits behind no extra consent lever), which
keeps it off the analytics/matching gates and out of the ai_turns CHECK churn.
"""

from __future__ import annotations

import base64
import io
import logging
from typing import Any
from uuid import UUID

from unipaith.ai.client import AIClient, get_client

logger = logging.getLogger(__name__)

# Reuse the user-initiated, consent-free slot (see module docstring).
_AGENT_SLOT = "workshop_coach"

_IMAGE_TYPES = {"image/png", "image/jpeg", "image/gif", "image/webp"}
_DOCX_TYPES = {
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
}
_TEXT_TYPES = {"text/plain", "text/markdown", "text/csv"}

_SYSTEM = (
    "You are Uni, a college counselor reading a document a student uploaded "
    "(a resume, CV, transcript, or similar). Extract ONLY the information the "
    "document actually contains, into the student's profile. Never invent, "
    "guess, or infer beyond what is written — if a field isn't present, omit it. "
    "Prefer the student's own wording. Convert dates to YYYY-MM-DD (or YYYY-MM / "
    "YYYY when only that is given). Map every item to the closest allowed "
    "category. Capture EVERYTHING present: preferred name, email, phone, links "
    "(LinkedIn / portfolio), every school with its honors/scholarships, "
    "concentration (as field_of_study) and relevant coursework, every job and "
    "internship with its quantified achievement bullets and location, languages, "
    "skills, and interests. For an activity or club, `title` is the club's NAME "
    "(e.g. 'Electric Formula Club') and `role` is the position (Member, "
    "President) — never put the role in the title. "
    "Write a one-sentence, warm `summary` of what you picked up, in "
    "the first person ('I picked up your CS degree and two internships'). "
    "Call submit_extracted_profile exactly once."
)

SUBMIT_TOOL: dict[str, Any] = {
    "name": "submit_extracted_profile",
    "description": "Return the structured profile data extracted from the uploaded document.",
    "input_schema": {
        "type": "object",
        "properties": {
            "summary": {
                "type": "string",
                "description": "One warm first-person sentence on what you picked up.",
            },
            "profile": {
                "type": "object",
                "description": "Basic profile fields, only if clearly present.",
                "properties": {
                    "first_name": {"type": "string"},
                    "last_name": {"type": "string"},
                    "preferred_name": {
                        "type": "string",
                        "description": "Name the student goes by, e.g. 'Leo'.",
                    },
                    "email": {"type": "string"},
                    "phone": {"type": "string"},
                    "bio_text": {
                        "type": "string",
                        "description": "A short professional summary if present.",
                    },
                    "country_of_residence": {"type": "string"},
                    "skills": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Hard/technical skills, e.g. Python, SQL, Tableau.",
                    },
                    "interests": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Personal interests/hobbies.",
                    },
                },
            },
            "online_presence": {
                "type": "array",
                "description": "Profile links (LinkedIn, portfolio, GitHub, personal site).",
                "items": {
                    "type": "object",
                    "properties": {
                        "platform_type": {
                            "type": "string",
                            "enum": [
                                "linkedin",
                                "github",
                                "personal_site",
                                "portfolio",
                                "wechat",
                                "twitter",
                                "other",
                            ],
                        },
                        "url": {"type": "string"},
                        "display_name": {"type": "string"},
                    },
                    "required": ["platform_type", "url"],
                },
            },
            "languages": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "language": {"type": "string"},
                        "proficiency_level": {
                            "type": "string",
                            "enum": ["native", "fluent", "advanced", "intermediate", "beginner"],
                            "description": "Map 'conversational' to 'intermediate'.",
                        },
                    },
                    "required": ["language"],
                },
            },
            "academic_records": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "institution_name": {"type": "string"},
                        "degree_type": {
                            "type": "string",
                            "enum": [
                                "high_school",
                                "bachelors",
                                "masters",
                                "phd",
                                "associate",
                                "diploma",
                            ],
                        },
                        "field_of_study": {"type": "string"},
                        "gpa": {"type": "number"},
                        "gpa_scale": {"type": "string", "description": "e.g. '4.0', '100'."},
                        "honors": {"type": "string"},
                        "start_date": {"type": "string"},
                        "end_date": {"type": "string"},
                        "is_current": {"type": "boolean"},
                        "courses": {
                            "type": "array",
                            "description": "Relevant coursework listed for this school.",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "course_name": {"type": "string"},
                                    "subject_area": {"type": "string"},
                                },
                                "required": ["course_name"],
                            },
                        },
                    },
                    "required": ["institution_name", "degree_type"],
                },
            },
            "test_scores": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "test_type": {
                            "type": "string",
                            "enum": [
                                "SAT",
                                "GRE",
                                "GMAT",
                                "TOEFL",
                                "IELTS",
                                "AP",
                                "IB",
                                "ACT",
                                "LSAT",
                                "MCAT",
                                "DUOLINGO",
                            ],
                        },
                        "total_score": {"type": "integer"},
                        "test_date": {"type": "string"},
                    },
                    "required": ["test_type"],
                },
            },
            "activities": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "activity_type": {
                            "type": "string",
                            "enum": [
                                "work_experience",
                                "research",
                                "volunteering",
                                "extracurricular",
                                "leadership",
                                "awards",
                                "publications",
                            ],
                        },
                        "title": {
                            "type": "string",
                            "description": "The club/activity NAME, not the role.",
                        },
                        "role": {
                            "type": "string",
                            "description": "The role, e.g. Member, President.",
                        },
                        "organization": {"type": "string"},
                        "description": {"type": "string"},
                        "start_date": {"type": "string"},
                        "end_date": {"type": "string"},
                        "hours_per_week": {"type": "integer"},
                    },
                    "required": ["activity_type", "title"],
                },
            },
            "work_experiences": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "experience_type": {
                            "type": "string",
                            "enum": ["employment", "internship", "volunteering", "service"],
                        },
                        "organization": {"type": "string"},
                        "role_title": {"type": "string"},
                        "description": {"type": "string"},
                        "key_achievements": {
                            "type": "string",
                            "description": "The quantified achievement bullets, joined.",
                        },
                        "organization_city": {"type": "string"},
                        "organization_country": {"type": "string"},
                        "start_date": {"type": "string"},
                        "end_date": {"type": "string"},
                        "is_current": {"type": "boolean"},
                    },
                    "required": ["experience_type", "organization", "role_title"],
                },
            },
            "goals": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "category": {"type": "string", "enum": ["academic", "social", "personal"]},
                        "specific": {"type": "string"},
                        "measurable": {"type": "string"},
                        "time_bound": {"type": "string"},
                    },
                    "required": ["category", "specific"],
                },
            },
            "needs": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "maslow_level": {
                            "type": "string",
                            "enum": [
                                "physiological",
                                "safety",
                                "social",
                                "self_esteem",
                                "self_actualization",
                            ],
                        },
                        "need_type": {"type": "string"},
                        "signal": {"type": "string"},
                        "severity": {
                            "type": "string",
                            "enum": ["must_have", "strong_preference", "nice_to_have"],
                        },
                    },
                    "required": ["maslow_level", "need_type", "signal", "severity"],
                },
            },
            "identity": {
                "type": "object",
                "description": "Values/beliefs/insights, only if stated.",
                "properties": {
                    "core_values": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "value": {"type": "string"},
                                "evidence": {"type": "string"},
                            },
                            "required": ["value"],
                        },
                    },
                    "worldview": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "belief": {"type": "string"},
                                "context": {"type": "string"},
                            },
                            "required": ["belief"],
                        },
                    },
                    "self_awareness": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {"insight": {"type": "string"}},
                            "required": ["insight"],
                        },
                    },
                },
            },
        },
        "required": ["summary"],
    },
}


def _content_block(mime_type: str, data: bytes) -> dict[str, Any]:
    """Build the right Claude content block for the uploaded file.

    PDFs and images go in natively (Claude reads layout / scans); Word and text
    are extracted to text. Raises ValueError for an unsupported type."""
    mime = (mime_type or "").lower().split(";")[0].strip()
    if mime == "application/pdf":
        return {
            "type": "document",
            "source": {
                "type": "base64",
                "media_type": "application/pdf",
                "data": base64.standard_b64encode(data).decode("ascii"),
            },
        }
    if mime in _IMAGE_TYPES:
        return {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": mime,
                "data": base64.standard_b64encode(data).decode("ascii"),
            },
        }
    if mime in _DOCX_TYPES:
        import docx2txt

        text = docx2txt.process(io.BytesIO(data)) or ""
        return {"type": "text", "text": text[:120_000] or "(empty document)"}
    if mime in _TEXT_TYPES or mime == "":
        return {"type": "text", "text": data.decode("utf-8", errors="replace")[:120_000]}
    raise ValueError(f"unsupported_mime:{mime}")


class MaterialIngestAgent:
    def __init__(self, client: AIClient | None = None) -> None:
        self.client = client or get_client()

    async def read(
        self,
        *,
        filename: str | None,
        mime_type: str | None,
        data: bytes,
        student_id: UUID | None = None,
    ) -> dict[str, Any] | None:
        try:
            block = _content_block(mime_type or "", data)
        except ValueError as exc:
            logger.info("material ingest: %s", exc)
            return None
        instruction = (
            "Read this uploaded file"
            + (f" ({filename})" if filename else "")
            + " and extract the student's profile into submit_extracted_profile. "
            "Extract only what is actually present; omit anything not in the file."
        )
        try:
            resp = await self.client.message(
                agent=_AGENT_SLOT,
                model="sonnet",
                system=[{"type": "text", "text": _SYSTEM}],
                messages=[
                    {"role": "user", "content": [block, {"type": "text", "text": instruction}]}
                ],
                tools=[SUBMIT_TOOL],
                tool_choice={"type": "tool", "name": "submit_extracted_profile"},
                max_tokens=4000,
                temperature=0.0,
                student_id=student_id,
                surface="material_ingest",
                # PDF/image vision + a large structured extraction can take well
                # over the 30s default; give it room so a full resume doesn't
                # time out into the empty-proposal fallback.
                timeout_ms=120_000,
            )
        except Exception as exc:
            logger.warning("material ingest agent call failed: %s", exc)
            return None
        return self._parse(resp.content_blocks)

    @staticmethod
    def _parse(blocks: list[dict[str, Any]]) -> dict[str, Any] | None:
        for b in blocks:
            if b.get("type") == "tool_use" and b.get("name") == "submit_extracted_profile":
                inp = b.get("input")
                return inp if isinstance(inp, dict) else None
        logger.warning("material ingest agent returned no tool_use block")
        return None
