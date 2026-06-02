"""Spec 41 — Graduate & PhD Admissions service.

The graduate-specific business logic layered on top of the shared pipeline
(``31``/``32``/``34``/``35``) without forking it:

- **Faculty-advisor matching** — ranks faculty by deterministic research-interest
  alignment (``AdvisorMatcher``), tracks the applicant-named / advisor-flagged
  interest signals, and surfaces mutual interest to the department (§2.1).
- **Research-interest alignment** — captures the applicant's grad intent and parses
  the statement of purpose into interest tags (``SoPInterestExtractor``, §2.2).
- **Funding-package builder** — builds a TA/RA/fellowship/waiver/stipend package
  against per-source budget pools and **hard-blocks over-commitment** (§2.3 / §9);
  ``FundingScenarioHelper`` advises on viable re-mixes.
- **Department review portal** — scopes review to a department's own applicants and
  runs the two-stage *department recommends → central confirms / releases* flow,
  delegating the actual offer release to ``ApplicationService`` (Spec 34, §2.4).

AI agents (§5) are gated by ``ai_graduate_v2_enabled`` and always fall back to the
deterministic baseline, so no endpoint 5xxes on an AI failure. Matching informs
humans; faculty decide. The over-commit *block* is a business rule, always
enforced regardless of the AI flag.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from unipaith.ai.advisor_matcher import get_advisor_matcher, research_alignment
from unipaith.ai.funding_scenario_helper import get_funding_scenario_helper
from unipaith.ai.sop_interest_extractor import get_sop_interest_extractor
from unipaith.config import settings
from unipaith.core.exceptions import BadRequestException, NotFoundException
from unipaith.models.application import Application
from unipaith.models.graduate import (
    FUNDING_COMPONENT_KINDS,
    FUNDING_PACKAGE_STATUSES,
    FUNDING_POOL_KINDS,
    RECOMMENDED_DECISIONS,
    AdvisorMatch,
    Department,
    DepartmentReview,
    FacultyProfile,
    FundingPackage,
    FundingPackageComponent,
    FundingPool,
    GraduateIntent,
)
from unipaith.models.institution import Institution, Program

logger = logging.getLogger("unipaith.graduate")

# Statuses that consume budget (drafts are tentative and don't count).
_COMMITTING_STATUSES = ("proposed", "finalized")
_EPSILON = 1e-6

# ── degree gating (§6) ────────────────────────────────────────────────────────
_UNDERGRAD_MARKERS = (
    "bachelor",
    "associate",
    "high_school",
    "highschool",
    "high school",
    "undergrad",
    "diploma",
    "certificate",
    "foundation",
)
_GRAD_MARKERS = (
    "master",
    "phd",
    "ph.d",
    "doctor",
    "mba",
    "msc",
    "m.sc",
    "meng",
    "mfa",
    "m.ed",
    "llm",
    "graduate",
    "postgrad",
    "dphil",
    "edd",
    "ed.d",
    "dba",
)
_GRAD_EXACT = {"ms", "ma", "m.s", "m.a", "m.s.", "m.a.", "jd", "j.d", "md", "m.d"}


def is_graduate_degree(degree_type: str | None) -> bool:
    """True when a program's ``degree_type`` denotes a graduate program (§6).

    Conservative: anything not clearly graduate is treated as undergrad so the
    grad-only module stays hidden unless the program is unambiguously graduate.
    """
    if not degree_type:
        return False
    d = degree_type.strip().lower()
    if any(marker in d for marker in _UNDERGRAD_MARKERS):
        return False
    if d in _GRAD_EXACT:
        return True
    return any(marker in d for marker in _GRAD_MARKERS)


def _money(value) -> float:
    try:
        return round(float(value or 0), 2)
    except (TypeError, ValueError):
        return 0.0


class GraduateService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── institution / scoping ─────────────────────────────────────────────────

    async def get_institution(self, user_id: UUID) -> Institution:
        result = await self.db.execute(
            select(Institution).where(Institution.admin_user_id == user_id)
        )
        institution = result.scalar_one_or_none()
        if not institution:
            raise NotFoundException("Institution not found")
        return institution

    async def resolve_institution(self, user) -> Institution:
        """Resolve the caller's institution for both roles (§8): an
        ``institution_admin`` owns the institution row directly; a ``faculty`` user
        is resolved via their FacultyProfile."""
        from unipaith.models.user import UserRole

        if user.role == UserRole.institution_admin:
            return await self.get_institution(user.id)
        fac = (
            (await self.db.execute(select(FacultyProfile).where(FacultyProfile.user_id == user.id)))
            .scalars()
            .first()
        )
        if fac is None:
            raise NotFoundException("No faculty profile is linked to this user")
        inst = await self.db.get(Institution, fac.institution_id)
        if inst is None:
            raise NotFoundException("Institution not found")
        return inst

    async def _get_application_scoped(
        self, institution_id: UUID, application_id: UUID
    ) -> tuple[Application, Program]:
        """Load an application + its program, asserting the program belongs to the
        institution (tenant isolation). Raises 404 otherwise."""
        row = await self.db.execute(
            select(Application, Program)
            .join(Program, Application.program_id == Program.id)
            .where(Application.id == application_id)
            .where(Program.institution_id == institution_id)
        )
        pair = row.first()
        if pair is None:
            raise NotFoundException("Application not found")
        return pair[0], pair[1]

    @staticmethod
    def _assert_graduate(program: Program) -> None:
        if not is_graduate_degree(program.degree_type):
            raise BadRequestException(
                "Graduate-admissions features are only available for graduate programs"
            )

    async def _graduate_program_ids(self, institution_id: UUID) -> list[UUID]:
        progs = (
            await self.db.execute(
                select(Program.id, Program.degree_type).where(
                    Program.institution_id == institution_id
                )
            )
        ).all()
        return [pid for pid, dt in progs if is_graduate_degree(dt)]

    async def graduate_summary(self, institution_id: UUID) -> dict:
        """Institution-wide graduate overview for the admissions Graduate tab:
        departments (with counts), funding totals, and pipeline counts (§2.4)."""
        departments = await self.list_departments(institution_id)
        budget = await self.funding_budget(institution_id)
        faculty_total = (
            await self.db.scalar(
                select(func.count(FacultyProfile.id)).where(
                    FacultyProfile.institution_id == institution_id
                )
            )
        ) or 0
        grad_ids = await self._graduate_program_ids(institution_id)
        grad_app_count = 0
        pending_recs = 0
        if grad_ids:
            grad_app_count = (
                await self.db.scalar(
                    select(func.count(Application.id)).where(Application.program_id.in_(grad_ids))
                )
            ) or 0
            pending_recs = (
                await self.db.scalar(
                    select(func.count(DepartmentReview.id))
                    .select_from(DepartmentReview)
                    .join(Application, DepartmentReview.application_id == Application.id)
                    .where(Application.program_id.in_(grad_ids))
                    .where(DepartmentReview.central_status == "pending")
                )
            ) or 0
        return {
            "departments": departments,
            "department_count": len(departments),
            "faculty_count": int(faculty_total),
            "graduate_application_count": int(grad_app_count),
            "pending_recommendations": int(pending_recs),
            "funding": {
                "total_budget": budget["total_budget"],
                "total_committed": budget["total_committed"],
                "total_remaining": budget["total_remaining"],
            },
        }

    # ── departments ─────────────────────────────────────────────────────────

    async def list_departments(self, institution_id: UUID) -> list[dict]:
        rows = (
            (
                await self.db.execute(
                    select(Department)
                    .where(Department.institution_id == institution_id)
                    .order_by(Department.name)
                )
            )
            .scalars()
            .all()
        )
        # Aggregate counts in one pass each (small N — MVP scale).
        prog_counts = await self._program_counts_by_department(institution_id)
        faculty_counts = await self._faculty_counts_by_department(institution_id)
        budget = await self.funding_budget(institution_id)
        pools_by_dept: dict[str, dict] = {}
        for p in budget["pools"]:
            did = p.get("department_id")
            if did:
                agg = pools_by_dept.setdefault(did, {"budget": 0.0, "committed": 0.0})
                agg["budget"] += p["budget"]
                agg["committed"] += p["committed"]
        return [
            self._department_dict(
                d,
                programs=prog_counts.get(str(d.id), 0),
                faculty=faculty_counts.get(str(d.id), 0),
                funding=pools_by_dept.get(str(d.id), {"budget": 0.0, "committed": 0.0}),
            )
            for d in rows
        ]

    @staticmethod
    def _department_basic(d: Department) -> dict:
        return {
            "id": str(d.id),
            "name": d.name,
            "code": d.code,
            "description": d.description,
            "notes": d.notes,
        }

    @staticmethod
    def _pool_dict_basic(p: FundingPool) -> dict:
        return {
            "id": str(p.id),
            "department_id": str(p.department_id) if p.department_id else None,
            "name": p.name,
            "kind": p.kind,
            "total_budget": _money(p.total_budget),
            "currency": p.currency,
            "notes": p.notes,
        }

    @staticmethod
    def _department_dict(d: Department, *, programs: int, faculty: int, funding: dict) -> dict:
        return {
            "id": str(d.id),
            "name": d.name,
            "code": d.code,
            "description": d.description,
            "notes": d.notes,
            "program_count": programs,
            "faculty_count": faculty,
            "funding_budget": round(funding.get("budget", 0.0), 2),
            "funding_committed": round(funding.get("committed", 0.0), 2),
            "created_at": d.created_at.isoformat() if d.created_at else None,
        }

    async def _program_counts_by_department(self, institution_id: UUID) -> dict[str, int]:
        rows = (
            await self.db.execute(
                select(Program.department_id, func.count(Program.id))
                .where(Program.institution_id == institution_id)
                .where(Program.department_id.isnot(None))
                .group_by(Program.department_id)
            )
        ).all()
        return {str(did): int(n) for did, n in rows}

    async def _faculty_counts_by_department(self, institution_id: UUID) -> dict[str, int]:
        rows = (
            await self.db.execute(
                select(FacultyProfile.department_id, func.count(FacultyProfile.id))
                .where(FacultyProfile.institution_id == institution_id)
                .where(FacultyProfile.department_id.isnot(None))
                .group_by(FacultyProfile.department_id)
            )
        ).all()
        return {str(did): int(n) for did, n in rows}

    async def get_department(self, institution_id: UUID, department_id: UUID) -> Department:
        dept = await self.db.get(Department, department_id)
        if dept is None or dept.institution_id != institution_id:
            raise NotFoundException("Department not found")
        return dept

    async def create_department(self, institution_id: UUID, data: dict) -> Department:
        name = (data.get("name") or "").strip()
        if not name:
            raise BadRequestException("Department name is required")
        dept = Department(
            institution_id=institution_id,
            name=name,
            code=(data.get("code") or None),
            description=data.get("description"),
            notes=data.get("notes"),
        )
        self.db.add(dept)
        await self.db.flush()
        await self.db.refresh(dept)
        return dept

    async def update_department(
        self, institution_id: UUID, department_id: UUID, data: dict
    ) -> Department:
        dept = await self.get_department(institution_id, department_id)
        for field in ("name", "code", "description", "notes"):
            if field in data and data[field] is not None:
                setattr(dept, field, data[field])
        await self.db.flush()
        await self.db.refresh(dept)
        return dept

    async def department_dashboard(self, institution_id: UUID, department_id: UUID) -> dict:
        """Department-portal overview: applicant pool, funding committed-vs-budget,
        yield, and faculty roster summary (§2.4)."""
        dept = await self.get_department(institution_id, department_id)
        review = await self.list_department_review(institution_id, department_id)
        budget = await self.funding_budget(institution_id, department_id=department_id)
        faculty = await self.list_faculty(institution_id, department_id=department_id)
        applicants = review["applicants"]
        # Yield: enrolled / admitted among this department's applicants.
        admitted = sum(
            1 for a in applicants if a.get("decision") in ("admitted", "conditional_admission")
        )
        accepted = sum(1 for a in applicants if a.get("student_decision") == "accepted_by_student")
        return {
            "department": self._department_dict(
                dept,
                programs=(await self._program_counts_by_department(institution_id)).get(
                    str(dept.id), 0
                ),
                faculty=len(faculty),
                funding={"budget": budget["total_budget"], "committed": budget["total_committed"]},
            ),
            "applicant_count": len(applicants),
            "recommended_count": sum(1 for a in applicants if a.get("central_status") == "pending"),
            "admitted_count": admitted,
            "yield": {"admitted": admitted, "accepted": accepted},
            "funding": budget,
            "faculty": [self._faculty_dict(f) for f in faculty],
        }

    # ── faculty ───────────────────────────────────────────────────────────────

    async def list_faculty(
        self, institution_id: UUID, department_id: UUID | None = None
    ) -> list[FacultyProfile]:
        stmt = (
            select(FacultyProfile)
            .where(FacultyProfile.institution_id == institution_id)
            .order_by(FacultyProfile.name)
        )
        if department_id is not None:
            stmt = stmt.where(FacultyProfile.department_id == department_id)
        return list((await self.db.execute(stmt)).scalars().all())

    async def get_faculty(self, institution_id: UUID, faculty_id: UUID) -> FacultyProfile:
        fac = await self.db.get(FacultyProfile, faculty_id)
        if fac is None or fac.institution_id != institution_id:
            raise NotFoundException("Faculty profile not found")
        return fac

    @staticmethod
    def _faculty_dict(f: FacultyProfile) -> dict:
        return {
            "id": str(f.id),
            "department_id": str(f.department_id) if f.department_id else None,
            "user_id": str(f.user_id) if f.user_id else None,
            "name": f.name,
            "email": f.email,
            "title": f.title,
            "research_areas": f.research_areas or [],
            "accepting_students": f.accepting_students,
            "openings": f.openings,
            "funding_available": f.funding_available,
            "bio": f.bio,
            "homepage_url": f.homepage_url,
        }

    async def create_faculty(self, institution_id: UUID, data: dict) -> FacultyProfile:
        name = (data.get("name") or "").strip()
        if not name:
            raise BadRequestException("Faculty name is required")
        dept_id = data.get("department_id")
        if dept_id:
            await self.get_department(institution_id, UUID(str(dept_id)))
        fac = FacultyProfile(
            institution_id=institution_id,
            department_id=UUID(str(dept_id)) if dept_id else None,
            user_id=UUID(str(data["user_id"])) if data.get("user_id") else None,
            name=name,
            email=data.get("email"),
            title=data.get("title"),
            research_areas=data.get("research_areas") or [],
            accepting_students=bool(data.get("accepting_students", False)),
            openings=int(data.get("openings") or 0),
            funding_available=bool(data.get("funding_available", False)),
            bio=data.get("bio"),
            homepage_url=data.get("homepage_url"),
        )
        self.db.add(fac)
        await self.db.flush()
        await self.db.refresh(fac)
        return fac

    async def update_faculty(
        self, institution_id: UUID, faculty_id: UUID, data: dict
    ) -> FacultyProfile:
        fac = await self.get_faculty(institution_id, faculty_id)
        if data.get("department_id"):
            await self.get_department(institution_id, UUID(str(data["department_id"])))
            fac.department_id = UUID(str(data["department_id"]))
        for field in ("name", "email", "title", "bio", "homepage_url", "research_areas"):
            if field in data and data[field] is not None:
                setattr(fac, field, data[field])
        for flag in ("accepting_students", "funding_available"):
            if flag in data and data[flag] is not None:
                setattr(fac, flag, bool(data[flag]))
        if data.get("openings") is not None:
            fac.openings = max(0, int(data["openings"]))
        await self.db.flush()
        await self.db.refresh(fac)
        return fac

    # ── graduate intent + SoP extraction ──────────────────────────────────────

    async def get_intent(self, application_id: UUID) -> GraduateIntent | None:
        return (
            await self.db.execute(
                select(GraduateIntent).where(GraduateIntent.application_id == application_id)
            )
        ).scalar_one_or_none()

    async def _applicant_interests(self, application_id: UUID) -> list[str]:
        intent = await self.get_intent(application_id)
        if intent is None:
            return []
        merged: list[str] = []
        for src in (intent.extracted_interests or [], intent.research_interests or []):
            for v in src:
                if (
                    isinstance(v, str)
                    and v.strip()
                    and v.strip().lower() not in {m.lower() for m in merged}
                ):
                    merged.append(v.strip())
        return merged

    async def _department_vocabulary(self, institution_id: UUID, program: Program) -> list[str]:
        faculty = await self.list_faculty(institution_id, department_id=program.department_id)
        vocab: list[str] = []
        for f in faculty:
            for area in f.research_areas or []:
                if isinstance(area, str) and area.strip():
                    vocab.append(area.strip())
        return vocab

    @staticmethod
    def _apply_intent_fields(intent: GraduateIntent, data: dict) -> None:
        if "research_interests" in data and data["research_interests"] is not None:
            intent.research_interests = [s for s in data["research_interests"] if str(s).strip()]
        if "target_advisor_ids" in data and data["target_advisor_ids"] is not None:
            intent.target_advisor_ids = [str(x) for x in data["target_advisor_ids"]]
        if "target_advisor_names" in data and data["target_advisor_names"] is not None:
            intent.target_advisor_names = [
                s for s in data["target_advisor_names"] if str(s).strip()
            ]
        if "statement_of_purpose" in data:
            intent.statement_of_purpose = data["statement_of_purpose"]
        if data.get("funding_required") is not None:
            intent.funding_required = bool(data["funding_required"])

    async def _get_application_for_student(
        self, student_id: UUID, application_id: UUID
    ) -> tuple[Application, Program]:
        row = await self.db.execute(
            select(Application, Program)
            .join(Program, Application.program_id == Program.id)
            .where(Application.id == application_id)
            .where(Application.student_id == student_id)
        )
        pair = row.first()
        if pair is None:
            raise NotFoundException("Application not found")
        return pair[0], pair[1]

    async def student_get_intent(
        self, student_id: UUID, application_id: UUID
    ) -> tuple[GraduateIntent | None, bool]:
        """Return ``(intent, is_graduate)`` for the student's own application."""
        app, program = await self._get_application_for_student(student_id, application_id)
        return await self.get_intent(application_id), is_graduate_degree(program.degree_type)

    async def student_upsert_intent(
        self, student_id: UUID, application_id: UUID, data: dict
    ) -> GraduateIntent:
        """The applicant states research interests + target advisors + SoP (§3 flow).
        Scoped to the student's own graduate application."""
        app, program = await self._get_application_for_student(student_id, application_id)
        self._assert_graduate(program)
        intent = await self.get_intent(application_id)
        if intent is None:
            intent = GraduateIntent(application_id=application_id)
            self.db.add(intent)
        self._apply_intent_fields(intent, data)
        await self.db.flush()
        await self.db.refresh(intent)
        return intent

    async def upsert_intent(
        self, institution_id: UUID, application_id: UUID, data: dict, *, run_extractor: bool = True
    ) -> GraduateIntent:
        app, program = await self._get_application_scoped(institution_id, application_id)
        self._assert_graduate(program)
        intent = await self.get_intent(application_id)
        if intent is None:
            intent = GraduateIntent(application_id=application_id)
            self.db.add(intent)
        self._apply_intent_fields(intent, data)

        # SoPInterestExtractor (§5) — only when the flag is on; otherwise leave the
        # applicant's stated interests untouched (fall back to manual).
        if run_extractor and settings.ai_graduate_v2_enabled:
            try:
                vocab = await self._department_vocabulary(institution_id, program)
                out = get_sop_interest_extractor().extract(
                    intent.statement_of_purpose,
                    vocabulary=vocab,
                    stated_interests=intent.research_interests or [],
                )
                intent.extracted_interests = out["extracted_interests"]
                intent.alignment_summary = out["alignment_summary"]
            except Exception:  # noqa: BLE001 — extractor is best-effort
                logger.warning(
                    "SoPInterestExtractor failed; leaving stated interests", exc_info=True
                )

        await self.db.flush()
        await self.db.refresh(intent)
        return intent

    @staticmethod
    def _intent_dict(intent: GraduateIntent | None) -> dict | None:
        if intent is None:
            return None
        return {
            "application_id": str(intent.application_id),
            "research_interests": intent.research_interests or [],
            "target_advisor_ids": intent.target_advisor_ids or [],
            "target_advisor_names": intent.target_advisor_names or [],
            "statement_of_purpose": intent.statement_of_purpose,
            "funding_required": intent.funding_required,
            "extracted_interests": intent.extracted_interests or [],
            "alignment_summary": intent.alignment_summary,
        }

    # ── advisor matching ──────────────────────────────────────────────────────

    async def list_advisor_matches(self, institution_id: UUID, application_id: UUID) -> dict:
        """Ranked advisor-fit for an applicant (§2.1). Always computes the
        deterministic alignment baseline; enriches with AI rationale when the flag
        is on. Persists/refreshes the AdvisorMatch rows so the stateful interest
        flags survive between calls."""
        app, program = await self._get_application_scoped(institution_id, application_id)
        self._assert_graduate(program)
        intent = await self.get_intent(application_id)
        interests = await self._applicant_interests(application_id)
        named_ids = {str(x) for x in (intent.target_advisor_ids or [])} if intent else set()
        named_names = (
            {s.lower().strip() for s in (intent.target_advisor_names or [])} if intent else set()
        )

        faculty = await self.list_faculty(institution_id, department_id=program.department_id)
        # Existing rows keyed by faculty id so we preserve advisor_flagged_interest.
        existing = {
            str(m.faculty_id): m
            for m in (
                await self.db.execute(
                    select(AdvisorMatch).where(AdvisorMatch.application_id == application_id)
                )
            )
            .scalars()
            .all()
        }

        use_ai = settings.ai_graduate_v2_enabled
        matcher = get_advisor_matcher()
        results: list[dict] = []
        for f in faculty:
            score, shared = research_alignment(interests, f.research_areas)
            named = str(f.id) in named_ids or (f.name or "").lower().strip() in named_names
            row = existing.get(str(f.id))
            if row is None:
                row = AdvisorMatch(
                    application_id=application_id,
                    faculty_id=f.id,
                    applicant_named_advisor=False,
                    advisor_flagged_interest=False,
                    mutual=False,
                )
                self.db.add(row)
            flagged = bool(row.advisor_flagged_interest)
            row.alignment_score = Decimal(str(score))
            row.applicant_named_advisor = named
            row.mutual = bool(named and flagged)
            rationale = matcher.rationale(score, shared, f.name) if use_ai else None
            row.rationale = rationale
            results.append(
                {
                    "faculty_id": str(f.id),
                    "faculty_name": f.name,
                    "title": f.title,
                    "research_areas": f.research_areas or [],
                    "accepting_students": f.accepting_students,
                    "openings": f.openings,
                    "funding_available": f.funding_available,
                    "alignment_score": score,
                    "shared_interests": shared,
                    "applicant_named_advisor": named,
                    "advisor_flagged_interest": flagged,
                    "mutual": row.mutual,
                    "rationale": rationale,
                }
            )
        await self.db.flush()
        results.sort(key=lambda r: r["alignment_score"], reverse=True)
        return {
            "application_id": str(application_id),
            "applicant_interests": interests,
            "intent": self._intent_dict(intent),
            "matches": results,
            "ai_enabled": use_ai,
        }

    async def flag_advisor_interest(
        self, institution_id: UUID, application_id: UUID, faculty_id: UUID, flagged: bool
    ) -> dict:
        """Faculty (or department, on their behalf) flags interest in an applicant
        (§2.1). Recomputes ``mutual``."""
        app, program = await self._get_application_scoped(institution_id, application_id)
        fac = await self.get_faculty(institution_id, faculty_id)
        row = (
            await self.db.execute(
                select(AdvisorMatch)
                .where(AdvisorMatch.application_id == application_id)
                .where(AdvisorMatch.faculty_id == faculty_id)
            )
        ).scalar_one_or_none()
        if row is None:
            interests = await self._applicant_interests(application_id)
            score, _shared = research_alignment(interests, fac.research_areas)
            row = AdvisorMatch(
                application_id=application_id,
                faculty_id=faculty_id,
                alignment_score=Decimal(str(score)),
                applicant_named_advisor=False,
                advisor_flagged_interest=False,
                mutual=False,
            )
            self.db.add(row)
        row.advisor_flagged_interest = bool(flagged)
        row.mutual = bool(flagged) and bool(row.applicant_named_advisor)
        await self.db.flush()
        await self.db.refresh(row)
        return {
            "faculty_id": str(faculty_id),
            "advisor_flagged_interest": row.advisor_flagged_interest,
            "applicant_named_advisor": row.applicant_named_advisor,
            "mutual": row.mutual,
        }

    # ── funding pools + budget ────────────────────────────────────────────────

    async def list_funding_pools(
        self, institution_id: UUID, department_id: UUID | None = None
    ) -> list[FundingPool]:
        stmt = (
            select(FundingPool)
            .where(FundingPool.institution_id == institution_id)
            .order_by(FundingPool.name)
        )
        if department_id is not None:
            stmt = stmt.where(FundingPool.department_id == department_id)
        return list((await self.db.execute(stmt)).scalars().all())

    async def get_funding_pool(self, institution_id: UUID, pool_id: UUID) -> FundingPool:
        pool = await self.db.get(FundingPool, pool_id)
        if pool is None or pool.institution_id != institution_id:
            raise NotFoundException("Funding pool not found")
        return pool

    async def create_funding_pool(self, institution_id: UUID, data: dict) -> FundingPool:
        name = (data.get("name") or "").strip()
        if not name:
            raise BadRequestException("Funding pool name is required")
        kind = data.get("kind") or "department"
        if kind not in FUNDING_POOL_KINDS:
            raise BadRequestException(f"Invalid pool kind '{kind}'")
        dept_id = data.get("department_id")
        if dept_id:
            await self.get_department(institution_id, UUID(str(dept_id)))
        pool = FundingPool(
            institution_id=institution_id,
            department_id=UUID(str(dept_id)) if dept_id else None,
            name=name,
            kind=kind,
            total_budget=Decimal(str(data.get("total_budget") or 0)),
            currency=data.get("currency") or "USD",
            notes=data.get("notes"),
        )
        self.db.add(pool)
        await self.db.flush()
        await self.db.refresh(pool)
        return pool

    async def update_funding_pool(
        self, institution_id: UUID, pool_id: UUID, data: dict
    ) -> FundingPool:
        pool = await self.get_funding_pool(institution_id, pool_id)
        if data.get("kind") is not None:
            if data["kind"] not in FUNDING_POOL_KINDS:
                raise BadRequestException(f"Invalid pool kind '{data['kind']}'")
            pool.kind = data["kind"]
        for field in ("name", "currency", "notes"):
            if field in data and data[field] is not None:
                setattr(pool, field, data[field])
        if data.get("total_budget") is not None:
            pool.total_budget = Decimal(str(data["total_budget"]))
        if "department_id" in data:
            if data["department_id"]:
                await self.get_department(institution_id, UUID(str(data["department_id"])))
                pool.department_id = UUID(str(data["department_id"]))
            else:
                pool.department_id = None
        await self.db.flush()
        await self.db.refresh(pool)
        return pool

    async def _committed_by_pool(
        self, institution_id: UUID, *, exclude_application_id: UUID | None = None
    ) -> dict[str, float]:
        """Sum of committing (proposed + finalized) component amounts per pool."""
        stmt = (
            select(
                FundingPackageComponent.source_pool_id,
                func.coalesce(func.sum(FundingPackageComponent.amount), 0),
            )
            .select_from(FundingPackageComponent)
            .join(FundingPackage, FundingPackageComponent.package_id == FundingPackage.id)
            .join(FundingPool, FundingPackageComponent.source_pool_id == FundingPool.id)
            .where(FundingPool.institution_id == institution_id)
            .where(FundingPackage.status.in_(_COMMITTING_STATUSES))
            .group_by(FundingPackageComponent.source_pool_id)
        )
        if exclude_application_id is not None:
            stmt = stmt.where(FundingPackage.application_id != exclude_application_id)
        rows = (await self.db.execute(stmt)).all()
        return {str(pid): _money(total) for pid, total in rows if pid is not None}

    async def funding_budget(self, institution_id: UUID, department_id: UUID | None = None) -> dict:
        """Per-pool committed-vs-budget + totals (aggregate-on-read, §2.3/§2.4)."""
        pools = await self.list_funding_pools(institution_id, department_id=department_id)
        committed = await self._committed_by_pool(institution_id)
        pool_rows: list[dict] = []
        total_budget = 0.0
        total_committed = 0.0
        for p in pools:
            c = committed.get(str(p.id), 0.0)
            b = _money(p.total_budget)
            total_budget += b
            total_committed += c
            pool_rows.append(
                {
                    "id": str(p.id),
                    "department_id": str(p.department_id) if p.department_id else None,
                    "name": p.name,
                    "kind": p.kind,
                    "currency": p.currency,
                    "budget": b,
                    "committed": round(c, 2),
                    "remaining": round(b - c, 2),
                    "over": c > b + _EPSILON,
                }
            )
        return {
            "pools": pool_rows,
            "total_budget": round(total_budget, 2),
            "total_committed": round(total_committed, 2),
            "total_remaining": round(total_budget - total_committed, 2),
        }

    # ── funding package builder ───────────────────────────────────────────────

    async def get_funding_package(self, institution_id: UUID, application_id: UUID) -> dict | None:
        await self._get_application_scoped(institution_id, application_id)
        pkg = await self._load_package(application_id)
        if pkg is None:
            return None
        return await self._package_dict(institution_id, pkg)

    async def _load_package(self, application_id: UUID) -> FundingPackage | None:
        return (
            await self.db.execute(
                select(FundingPackage)
                .where(FundingPackage.application_id == application_id)
                .options(selectinload(FundingPackage.components))
            )
        ).scalar_one_or_none()

    async def build_funding_package(
        self, institution_id: UUID, application_id: UUID, data: dict
    ) -> dict:
        """Create/replace the funding package for an application, enforcing the
        per-pool over-commit block (§9). ``data.components`` is the full component
        list; ``data.status`` ∈ draft|proposed|finalized."""
        app, program = await self._get_application_scoped(institution_id, application_id)
        self._assert_graduate(program)

        status = data.get("status") or "draft"
        if status not in FUNDING_PACKAGE_STATUSES:
            raise BadRequestException(f"Invalid package status '{status}'")
        raw_components = data.get("components") or []

        # Validate components + resolve pools (must belong to the institution).
        pools_by_id: dict[str, FundingPool] = {}
        cleaned: list[dict] = []
        draws: dict[str, float] = {}
        for c in raw_components:
            kind = c.get("kind")
            if kind not in FUNDING_COMPONENT_KINDS:
                raise BadRequestException(f"Invalid funding component kind '{kind}'")
            amount = _money(c.get("amount"))
            if amount < 0:
                raise BadRequestException("Funding amount cannot be negative")
            pool_id = c.get("source_pool_id")
            if pool_id:
                pid = str(pool_id)
                if pid not in pools_by_id:
                    pools_by_id[pid] = await self.get_funding_pool(institution_id, UUID(pid))
                draws[pid] = draws.get(pid, 0.0) + amount
            years = c.get("years") or [1]
            years = sorted({int(y) for y in years if int(y) >= 1}) or [1]
            cleaned.append(
                {
                    "kind": kind,
                    "amount": amount,
                    "source_pool_id": str(pool_id) if pool_id else None,
                    "years": years,
                    "label": c.get("label"),
                }
            )

        # HARD over-commit block (§9) — only matters for committing statuses; a
        # draft can be sketched freely, but proposing/finalizing must fit budget.
        if status in _COMMITTING_STATUSES and draws:
            committed_other = await self._committed_by_pool(
                institution_id, exclude_application_id=application_id
            )
            for pid, draw in draws.items():
                pool = pools_by_id[pid]
                projected = committed_other.get(pid, 0.0) + draw
                if projected > _money(pool.total_budget) + _EPSILON:
                    raise BadRequestException(
                        f"Exceeds {pool.name} pool budget "
                        f"(committed {projected:,.0f} of {_money(pool.total_budget):,.0f})"
                    )

        pkg = await self._load_package(application_id)
        if pkg is None:
            pkg = FundingPackage(application_id=application_id)
            self.db.add(pkg)
            await self.db.flush()
        pkg.department_id = program.department_id
        pkg.status = status
        pkg.currency = data.get("currency") or pkg.currency or "USD"
        pkg.notes = data.get("notes", pkg.notes)
        if data.get("proposed_by"):
            pkg.proposed_by = UUID(str(data["proposed_by"]))
        total = round(sum(c["amount"] for c in cleaned), 2)
        pkg.total_value = Decimal(str(total))
        pkg.multi_year = any(any(y > 1 for y in c["years"]) for c in cleaned)
        if status == "finalized":
            pkg.finalized_at = datetime.now(UTC)

        # Replace components — query directly (a freshly-created package has no
        # eager-loaded ``components`` collection; touching the relationship would
        # trigger a lazy load outside the async greenlet).
        existing_components = (
            (
                await self.db.execute(
                    select(FundingPackageComponent).where(
                        FundingPackageComponent.package_id == pkg.id
                    )
                )
            )
            .scalars()
            .all()
        )
        for old in existing_components:
            await self.db.delete(old)
        await self.db.flush()
        for c in cleaned:
            self.db.add(
                FundingPackageComponent(
                    package_id=pkg.id,
                    kind=c["kind"],
                    amount=Decimal(str(c["amount"])),
                    source_pool_id=UUID(c["source_pool_id"]) if c["source_pool_id"] else None,
                    years=c["years"],
                    label=c["label"],
                )
            )
        await self.db.flush()
        pkg = await self._load_package(application_id)
        return await self._package_dict(institution_id, pkg)

    async def _package_dict(self, institution_id: UUID, pkg: FundingPackage) -> dict:
        components = [
            {
                "id": str(c.id),
                "kind": c.kind,
                "amount": _money(c.amount),
                "source_pool_id": str(c.source_pool_id) if c.source_pool_id else None,
                "years": c.years or [1],
                "label": c.label,
            }
            for c in pkg.components
        ]
        # FundingScenarioHelper advisory (§5) — only when flag on.
        analysis = None
        if settings.ai_graduate_v2_enabled:
            try:
                pools = await self.list_funding_pools(institution_id)
                committed_other = await self._committed_by_pool(
                    institution_id, exclude_application_id=pkg.application_id
                )
                pool_payload = [
                    {
                        "id": str(p.id),
                        "name": p.name,
                        "kind": p.kind,
                        "total_budget": _money(p.total_budget),
                        "committed_other": committed_other.get(str(p.id), 0.0),
                        "currency": p.currency,
                    }
                    for p in pools
                ]
                analysis = get_funding_scenario_helper().analyze(components, pool_payload)
            except Exception:  # noqa: BLE001 — advisory only
                logger.warning("FundingScenarioHelper failed", exc_info=True)
        return {
            "application_id": str(pkg.application_id),
            "department_id": str(pkg.department_id) if pkg.department_id else None,
            "status": pkg.status,
            "total_value": _money(pkg.total_value),
            "currency": pkg.currency,
            "multi_year": pkg.multi_year,
            "notes": pkg.notes,
            "finalized_at": pkg.finalized_at.isoformat() if pkg.finalized_at else None,
            "components": components,
            "analysis": analysis,
        }

    @staticmethod
    def _offer_assistantship(pkg: FundingPackage) -> dict:
        """Structured funding summary mirrored into ``OfferLetter.assistantship_details``
        so the Spec 18 student offer view renders the package (§2.3)."""
        return {
            "kind": "graduate_funding_package",
            "total_value": _money(pkg.total_value),
            "currency": pkg.currency,
            "multi_year": pkg.multi_year,
            "components": [
                {
                    "kind": c.kind,
                    "amount": _money(c.amount),
                    "years": c.years or [1],
                    "label": c.label,
                }
                for c in pkg.components
            ],
        }

    # ── department review (two-stage release) ─────────────────────────────────

    async def list_department_review(self, institution_id: UUID, department_id: UUID) -> dict:
        """Applicants scoped to one department + their two-stage review state
        and mutual-advisor flags (§2.4 / §9). Scoped strictly to programs whose
        ``department_id`` is this department."""
        dept = await self.get_department(institution_id, department_id)
        rows = (
            await self.db.execute(
                select(Application, Program)
                .join(Program, Application.program_id == Program.id)
                .where(Program.institution_id == institution_id)
                .where(Program.department_id == department_id)
                .order_by(Application.created_at.desc())
            )
        ).all()
        app_ids = [a.id for a, _ in rows]
        reviews = {
            str(r.application_id): r
            for r in (
                await self.db.execute(
                    select(DepartmentReview).where(
                        DepartmentReview.application_id.in_(app_ids or [None])
                    )
                )
            )
            .scalars()
            .all()
        }
        # Mutual-interest count per application (surfaced to the department, §2.1).
        mutual_counts: dict[str, int] = {}
        if app_ids:
            mrows = (
                await self.db.execute(
                    select(AdvisorMatch.application_id, func.count(AdvisorMatch.id))
                    .where(AdvisorMatch.application_id.in_(app_ids))
                    .where(AdvisorMatch.mutual.is_(True))
                    .group_by(AdvisorMatch.application_id)
                )
            ).all()
            mutual_counts = {str(aid): int(n) for aid, n in mrows}

        applicants: list[dict] = []
        for app, program in rows:
            review = reviews.get(str(app.id))
            applicants.append(
                {
                    "application_id": str(app.id),
                    "program_id": str(program.id),
                    "program_name": program.program_name,
                    "degree_type": program.degree_type,
                    "status": app.status,
                    "decision": app.decision,
                    "student_decision": app.student_decision,
                    "recommended_decision": review.recommended_decision if review else None,
                    "central_status": review.central_status if review else None,
                    "mutual_interest_count": mutual_counts.get(str(app.id), 0),
                }
            )
        return {
            "department": {"id": str(dept.id), "name": dept.name, "code": dept.code},
            "applicants": applicants,
        }

    async def get_department_review(
        self, institution_id: UUID, application_id: UUID
    ) -> DepartmentReview | None:
        await self._get_application_scoped(institution_id, application_id)
        return (
            await self.db.execute(
                select(DepartmentReview).where(DepartmentReview.application_id == application_id)
            )
        ).scalar_one_or_none()

    @staticmethod
    def _review_dict(review: DepartmentReview | None) -> dict | None:
        if review is None:
            return None
        return {
            "application_id": str(review.application_id),
            "department_id": str(review.department_id) if review.department_id else None,
            "recommended_decision": review.recommended_decision,
            "recommended_by": str(review.recommended_by) if review.recommended_by else None,
            "recommended_at": review.recommended_at.isoformat() if review.recommended_at else None,
            "committee_notes": review.committee_notes,
            "funding_package_id": str(review.funding_package_id)
            if review.funding_package_id
            else None,
            "central_status": review.central_status,
            "central_decision": review.central_decision,
            "central_at": review.central_at.isoformat() if review.central_at else None,
        }

    async def recommend(
        self,
        institution_id: UUID,
        application_id: UUID,
        *,
        decision: str,
        committee_notes: str | None,
        actor_user_id: UUID | None,
    ) -> DepartmentReview:
        """Stage 1 — department recommends a decision (§2.4). Faculty/department
        may call this; it does NOT release. Sets ``central_status = 'pending'``."""
        app, program = await self._get_application_scoped(institution_id, application_id)
        self._assert_graduate(program)
        if decision not in RECOMMENDED_DECISIONS:
            raise BadRequestException(f"Invalid recommended decision '{decision}'")
        review = await self.get_department_review(institution_id, application_id)
        if review is None:
            review = DepartmentReview(
                application_id=application_id, department_id=program.department_id
            )
            self.db.add(review)
        review.department_id = program.department_id
        review.recommended_decision = decision
        review.recommended_by = actor_user_id
        review.recommended_at = datetime.now(UTC)
        review.committee_notes = committee_notes
        # Link the finalized funding package if one exists.
        pkg = await self._load_package(application_id)
        if pkg is not None:
            review.funding_package_id = pkg.id
        review.central_status = "pending"
        await self.db.flush()
        await self.db.refresh(review)
        return review

    async def confirm_recommendation(
        self,
        institution_id: UUID,
        application_id: UUID,
        *,
        actor_user_id: UUID | None,
        override_decision: str | None = None,
        offer_terms: dict | None = None,
        notify: bool = True,
    ) -> dict:
        """Stage 2 — central office confirms (or overrides) the department's
        recommendation and releases the decision via Spec 34 (§2.4). Role-gated to
        institution_admin at the API layer (faculty cannot release)."""
        from unipaith.services.application_service import ApplicationService

        app, program = await self._get_application_scoped(institution_id, application_id)
        self._assert_graduate(program)
        review = await self.get_department_review(institution_id, application_id)
        if review is None or review.central_status != "pending":
            raise BadRequestException(
                "No department recommendation is pending central confirmation"
            )
        if override_decision is not None and override_decision not in RECOMMENDED_DECISIONS:
            raise BadRequestException(f"Invalid override decision '{override_decision}'")
        decision = override_decision or review.recommended_decision
        if not decision:
            raise BadRequestException("Department has not recommended a decision")

        # Fold a finalized funding package into the offer terms (Spec 34).
        terms = dict(offer_terms or {})
        pkg = await self._load_package(application_id)
        if pkg is not None and decision in ("admitted", "conditional_admission"):
            terms.setdefault("financial_package_total", int(_money(pkg.total_value)))

        svc = ApplicationService(self.db)
        released_app, offer = await svc.release_decision(
            institution_id,
            application_id,
            decision,
            decision_notes=review.committee_notes,
            actor_user_id=actor_user_id,
            offer=terms,
            notify=notify,
        )
        # Mirror the funding package onto the minted offer so the student sees it.
        if offer is not None and pkg is not None and pkg.components:
            offer.assistantship_details = self._offer_assistantship(pkg)
            if not offer.financial_package_total:
                offer.financial_package_total = int(_money(pkg.total_value))
            await self.db.flush()

        review.central_status = (
            "overridden"
            if (override_decision and override_decision != review.recommended_decision)
            else "confirmed"
        )
        review.central_by = actor_user_id
        review.central_at = datetime.now(UTC)
        review.central_decision = decision
        await self.db.flush()
        await self.db.refresh(review)
        return {
            "department_review": self._review_dict(review),
            "decision": decision,
            "offer_id": str(offer.id) if offer else None,
        }
