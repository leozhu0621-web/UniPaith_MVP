from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.institution import Institution, Program, School
from unipaith.schemas.profile_intelligence import (
    PROFILE_INTELLIGENCE_STANDARD_VERSION,
    validate_profile_intelligence,
)


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _url(*values: Any) -> str | None:
    for value in values:
        if isinstance(value, str) and value.startswith(("http://", "https://")):
            return value
    return None


def _source_blob(blob: dict | None) -> tuple[str | None, str | None]:
    if not isinstance(blob, dict):
        return None, None
    return blob.get("source") or blob.get("label"), _url(blob.get("source_url"), blob.get("url"))


def _entity_evidence(
    entity: Any, *, label: str | None = None, field_path: str | None = None
) -> list[dict]:
    url = _url(getattr(entity, "website_url", None), getattr(entity, "source_url", None))
    if not url:
        return []
    return [
        {
            "label": label
            or getattr(entity, "program_name", None)
            or getattr(entity, "name", "Official profile"),
            "url": url,
            "source_type": "official",
            "field_path": field_path,
            "freshness": {"status": "current", "checked_at": _now()},
        }
    ]


def _blob_evidence(
    blob: dict | None,
    *,
    fallback: list[dict],
    field_path: str,
    default_label: str,
    source_type: str = "official",
) -> list[dict]:
    label, url = _source_blob(blob)
    if url:
        return [
            {
                "label": label or default_label,
                "url": url,
                "source_type": source_type,
                "field_path": field_path,
                "freshness": {"status": "current", "checked_at": _now()},
            }
        ]
    return [dict(e, field_path=field_path) for e in fallback]


def _review_evidence(blob: dict | None, fallback: list[dict], field_path: str) -> list[dict]:
    if not isinstance(blob, dict):
        return fallback
    sources = blob.get("sources")
    if isinstance(sources, list):
        refs = []
        for src in sources:
            if isinstance(src, dict) and _url(src.get("url")):
                refs.append(
                    {
                        "label": src.get("label") or "Review source",
                        "url": src["url"],
                        "source_type": "verified_secondary",
                        "field_path": field_path,
                        "freshness": {"status": "current", "checked_at": _now()},
                    }
                )
        if refs:
            return refs
    return fallback


def _finding(
    statement: str,
    evidence: list[dict],
    *,
    source_type: str = "inferred",
    confidence: float = 0.72,
    time_sensitive: bool = False,
) -> dict | None:
    statement = " ".join((statement or "").split())
    if not statement or not evidence:
        return None
    return {
        "statement": statement[:900],
        "source_type": source_type,
        "confidence": confidence,
        "time_sensitive": time_sensitive,
        "freshness": {"status": "current", "checked_at": _now()},
        "evidence": evidence,
    }


def _add(
    sections: dict[str, dict], key: str, statement: str, evidence: list[dict], **kw: Any
) -> None:
    finding = _finding(statement, evidence, **kw)
    if finding:
        sections.setdefault(key, {"findings": []})["findings"].append(finding)


def _snippet(text: str | None, max_chars: int = 300) -> str | None:
    if not text:
        return None
    s = " ".join(text.split())
    if len(s) <= max_chars:
        return s
    return s[: max_chars - 1].rstrip() + "."


def _contains(text: Any, *terms: str) -> bool:
    if not text:
        return False
    hay = str(text).lower()
    return any(t in hay for t in terms)


def _public_profile(
    *,
    entity: Any,
    name: str,
    description: str | None,
    website_url: str | None,
    outcomes: dict | None = None,
    requirements: dict | None = None,
    tracks: dict | list | None = None,
    reviews: dict | None = None,
    about: dict | None = None,
    who_its_for: str | None = None,
    support: dict | None = None,
) -> dict:
    sections: dict[str, dict] = {}
    omissions: list[dict[str, str]] = []
    fallback = _entity_evidence(entity, label=name, field_path="description_text")

    if description and fallback:
        _add(
            sections,
            "academic_orientation",
            f"{name} presents itself around this academic focus: {_snippet(description)}",
            fallback,
            source_type="inferred",
            confidence=0.76,
        )
        if _contains(description, "theory", "research", "seminar", "dissertation"):
            _add(
                sections,
                "theory_applied_balance",
                f"{name} shows a theory or research-oriented component in its public description.",
                fallback,
                confidence=0.68,
            )
        if _contains(
            description, "applied", "capstone", "project", "practicum", "internship", "employer"
        ):
            _add(
                sections,
                "experiential_learning",
                (
                    f"{name} has public evidence of applied, project, practicum, "
                    "internship, or employer-facing learning."
                ),
                fallback,
                confidence=0.74,
            )
    else:
        omissions.append(
            {"section": "academic_orientation", "reason": "No cited public description available."}
        )

    track_evidence = _blob_evidence(
        tracks if isinstance(tracks, dict) else None,
        fallback=fallback,
        field_path="tracks",
        default_label=f"{name} curriculum",
    )
    if tracks and track_evidence:
        _add(
            sections,
            "learning_experience",
            f"{name} publishes curriculum or track evidence that describes the learning path.",
            track_evidence,
            confidence=0.78,
        )
        if _contains(tracks, "team", "cohort", "collaboration", "collaborative"):
            _add(
                sections,
                "learning_experience",
                f"{name} appears to expect collaborative or cohort-based work.",
                track_evidence,
                confidence=0.7,
            )
        if _contains(tracks, "capstone", "practicum", "internship", "project"):
            _add(
                sections,
                "experiential_learning",
                f"{name} includes an applied project, capstone, practicum, or internship signal.",
                track_evidence,
                confidence=0.8,
            )
    else:
        omissions.append(
            {
                "section": "learning_experience",
                "reason": "Curriculum, pedagogy, or schedule evidence unavailable.",
            }
        )

    outcome_evidence = _blob_evidence(
        outcomes,
        fallback=fallback,
        field_path="outcomes_data",
        default_label=f"{name} outcomes",
        source_type="institution_report",
    )
    if isinstance(outcomes, dict) and outcome_evidence:
        parts = []
        if outcomes.get("median_salary"):
            parts.append(f"published median salary ${int(outcomes['median_salary']):,}")
        if outcomes.get("employment_rate") is not None:
            parts.append(f"employment rate {round(float(outcomes['employment_rate']) * 100)}%")
        industries = outcomes.get("top_industries") or outcomes.get("common_roles") or []
        if industries:
            parts.append("pathways including " + ", ".join(map(str, industries[:4])))
        if parts:
            _add(
                sections,
                "career_pathways",
                f"{name} reports career outcomes or pathways: {'; '.join(parts)}.",
                outcome_evidence,
                source_type="fact",
                confidence=0.86,
                time_sensitive=True,
            )
    else:
        omissions.append(
            {"section": "career_pathways", "reason": "No cited outcomes evidence available."}
        )

    req_evidence = _blob_evidence(
        requirements,
        fallback=fallback,
        field_path="application_requirements",
        default_label=f"{name} admissions",
    )
    evaluation = requirements.get("evaluation") if isinstance(requirements, dict) else None
    if evaluation and req_evidence:
        _add(
            sections,
            "who_thrives",
            (
                f"{name} signals target readiness through admissions evaluation language: "
                f"{_snippet(evaluation, 260)}"
            ),
            req_evidence,
            confidence=0.78,
        )
    elif who_its_for and fallback:
        _add(
            sections,
            "who_thrives",
            f"{name} describes its likely audience this way: {_snippet(who_its_for, 260)}",
            fallback,
            confidence=0.74,
        )
    else:
        omissions.append(
            {"section": "who_thrives", "reason": "No cited target-student evidence available."}
        )

    review_evidence = _review_evidence(reviews, fallback, "external_reviews")
    if isinstance(reviews, dict) and review_evidence and reviews.get("summary"):
        _add(
            sections,
            "student_employer_evidence",
            (
                f"Public student or third-party evidence summarizes {name} as: "
                f"{_snippet(reviews.get('summary'), 300)}"
            ),
            review_evidence,
            source_type="inferred",
            confidence=0.7,
        )
        cautions = []
        for theme in reviews.get("themes") or []:
            if isinstance(theme, dict) and str(theme.get("sentiment", "")).lower() in {
                "caution",
                "mixed",
            }:
                label = theme.get("label") or "Tradeoff"
                detail = theme.get("detail") or ""
                cautions.append(f"{label}: {detail}".strip(": "))
        if cautions:
            _add(
                sections,
                "challenges_tradeoffs",
                f"Common cautions include {'; '.join(cautions[:3])}.",
                review_evidence,
                confidence=0.68,
            )
    else:
        omissions.append(
            {
                "section": "student_employer_evidence",
                "reason": "No cited review or employer evidence available.",
            }
        )

    if isinstance(about, dict) and fallback:
        centers = about.get("research_centers") or []
        faculty = about.get("faculty") or []
        if centers or faculty:
            _add(
                sections,
                "research_employer_exposure",
                (
                    f"{name} has public faculty or research-center evidence tied to "
                    "its academic community."
                ),
                _blob_evidence(
                    about.get("source") if isinstance(about.get("source"), dict) else about,
                    fallback=fallback,
                    field_path="about_detail",
                    default_label=f"{name} about",
                ),
                confidence=0.76,
            )

    if isinstance(support, dict) and fallback:
        _add(
            sections,
            "support_environment",
            f"{name} publishes support resources relevant to student feasibility and belonging.",
            fallback,
            confidence=0.66,
        )
    elif not sections.get("support_environment"):
        omissions.append(
            {
                "section": "support_environment",
                "reason": "Support-service evidence not published at this profile level.",
            }
        )

    payload = {
        "standard_version": PROFILE_INTELLIGENCE_STANDARD_VERSION,
        "profile_version": int(getattr(entity, "profile_intelligence_version", 0) or 0) + 1,
        "generated_at": _now(),
        "sections": sections,
        "omissions": omissions,
    }
    return validate_profile_intelligence(payload)


def build_institution_profile_intelligence(inst: Institution) -> dict:
    return _public_profile(
        entity=inst,
        name=inst.name,
        description=inst.description_text,
        website_url=inst.website_url,
        outcomes=inst.school_outcomes,
        support=inst.support_services,
    )


def build_school_profile_intelligence(school: School) -> dict:
    return _public_profile(
        entity=school,
        name=school.name,
        description=school.description_text,
        website_url=school.website_url,
        about=school.about_detail,
    )


def build_program_profile_intelligence(program: Program) -> dict:
    return _public_profile(
        entity=program,
        name=program.program_name,
        description=program.description_text,
        website_url=program.website_url,
        outcomes=program.outcomes_data,
        requirements=program.application_requirements or program.requirements,
        tracks=program.tracks,
        reviews=program.external_reviews,
        who_its_for=program.who_its_for,
    )


def _apply_intelligence(entity: Any, payload: dict) -> bool:
    if getattr(entity, "is_claimed", False):
        return False
    entity.profile_intelligence = payload
    entity.profile_intelligence_version = int(payload.get("profile_version") or 1)
    entity.profile_intelligence_updated_at = datetime.now(UTC)
    if hasattr(entity, "feature_version"):
        entity.feature_version = int(getattr(entity, "feature_version", 1) or 1) + 1
    return True


class ProfileIntelligenceService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def enrich_institution(self, institution_id: UUID) -> bool:
        inst = await self.db.get(Institution, institution_id)
        if inst is None:
            return False
        changed = _apply_intelligence(inst, build_institution_profile_intelligence(inst))
        if changed:
            await self.db.flush()
        return changed

    async def enrich_school(self, school_id: UUID) -> bool:
        school = await self.db.get(School, school_id)
        if school is None:
            return False
        changed = _apply_intelligence(school, build_school_profile_intelligence(school))
        if changed:
            await self.db.flush()
        return changed

    async def enrich_program(self, program_id: UUID) -> bool:
        program = await self.db.get(Program, program_id)
        if program is None:
            return False
        changed = _apply_intelligence(program, build_program_profile_intelligence(program))
        if changed:
            await self.db.flush()
        return changed


def backfill_profile_intelligence_sync(session: Any) -> dict[str, int]:
    """Populate profile_intelligence for all unclaimed current rows.

    Sync Session, intended for Alembic data migrations and one-off repair waves.
    """
    counts = {"institutions": 0, "schools": 0, "programs": 0}
    for inst in session.scalars(select(Institution)).all():
        if _apply_intelligence(inst, build_institution_profile_intelligence(inst)):
            counts["institutions"] += 1
    for school in session.scalars(select(School)).all():
        if _apply_intelligence(school, build_school_profile_intelligence(school)):
            counts["schools"] += 1
    for program in session.scalars(select(Program)).all():
        if _apply_intelligence(program, build_program_profile_intelligence(program)):
            counts["programs"] += 1
    session.flush()
    return counts
