"""Spec 41 — Graduate & PhD Admissions API.

Institution surfaces mounted at ``/institutions/me/graduate/*`` (departments,
faculty, advisor matching, funding pools + packages, the two-stage department
review). The student-facing grad intent (§3 flow: the applicant states research
interests + target advisors) lives at ``/students/me/applications/:id/graduate-intent``.

Role model (§8): faculty *and* central admins can read their department's
applicants, score, recommend, and propose funding
(``require_faculty_or_institution_admin``); only central admins can *release* a
decision (``require_institution_admin``) — the two-stage gate (§2.4). Every
endpoint is scoped to the caller's institution; grad features assert the program's
``degree_type`` is graduate (§6).
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.dependencies import (
    require_faculty_or_institution_admin,
    require_institution_admin,
    require_student,
)
from unipaith.models.user import User
from unipaith.services.graduate_service import GraduateService
from unipaith.services.student_service import StudentService

router = APIRouter(tags=["graduate"])

_INST = "/institutions/me/graduate"


def _svc(db: AsyncSession) -> GraduateService:
    return GraduateService(db)


# ── request models (inline, per house convention) ─────────────────────────────


class CreateDepartmentRequest(BaseModel):
    name: str
    code: str | None = None
    description: str | None = None
    notes: str | None = None


class UpdateDepartmentRequest(BaseModel):
    name: str | None = None
    code: str | None = None
    description: str | None = None
    notes: str | None = None


class CreateFacultyRequest(BaseModel):
    name: str
    department_id: UUID | None = None
    user_id: UUID | None = None
    email: str | None = None
    title: str | None = None
    research_areas: list[str] | None = None
    accepting_students: bool | None = None
    openings: int | None = None
    funding_available: bool | None = None
    bio: str | None = None
    homepage_url: str | None = None


class UpdateFacultyRequest(BaseModel):
    name: str | None = None
    department_id: UUID | None = None
    email: str | None = None
    title: str | None = None
    research_areas: list[str] | None = None
    accepting_students: bool | None = None
    openings: int | None = None
    funding_available: bool | None = None
    bio: str | None = None
    homepage_url: str | None = None


class FlagInterestRequest(BaseModel):
    flagged: bool = True


class IntentRequest(BaseModel):
    research_interests: list[str] | None = None
    target_advisor_ids: list[UUID] | None = None
    target_advisor_names: list[str] | None = None
    statement_of_purpose: str | None = None
    funding_required: bool | None = None


class CreateFundingPoolRequest(BaseModel):
    name: str
    kind: str | None = None
    total_budget: float | None = None
    currency: str | None = None
    department_id: UUID | None = None
    notes: str | None = None


class UpdateFundingPoolRequest(BaseModel):
    name: str | None = None
    kind: str | None = None
    total_budget: float | None = None
    currency: str | None = None
    department_id: UUID | None = None
    notes: str | None = None


class FundingComponentInput(BaseModel):
    kind: str
    amount: float
    source_pool_id: UUID | None = None
    years: list[int] | None = None
    label: str | None = None


class BuildFundingPackageRequest(BaseModel):
    status: str | None = None
    currency: str | None = None
    notes: str | None = None
    components: list[FundingComponentInput] = []


class RecommendRequest(BaseModel):
    decision: str
    committee_notes: str | None = None


class ConfirmRequest(BaseModel):
    override_decision: str | None = None
    offer_terms: dict | None = None


# ── summary (admissions Graduate tab) ─────────────────────────────────────────


@router.get(f"{_INST}/summary")
async def graduate_summary(
    user: User = Depends(require_faculty_or_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.resolve_institution(user)
    return await svc.graduate_summary(inst.id)


# ── departments ───────────────────────────────────────────────────────────────


@router.get(f"{_INST}/departments")
async def list_departments(
    user: User = Depends(require_faculty_or_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.resolve_institution(user)
    return await svc.list_departments(inst.id)


@router.post(f"{_INST}/departments", status_code=201)
async def create_department(
    body: CreateDepartmentRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.resolve_institution(user)
    dept = await svc.create_department(inst.id, body.model_dump(exclude_unset=True))
    return svc._department_basic(dept)


@router.get(f"{_INST}/departments/{{department_id}}")
async def get_department(
    department_id: UUID,
    user: User = Depends(require_faculty_or_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.resolve_institution(user)
    dept = await svc.get_department(inst.id, department_id)
    return svc._department_basic(dept)


@router.patch(f"{_INST}/departments/{{department_id}}")
async def update_department(
    department_id: UUID,
    body: UpdateDepartmentRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.resolve_institution(user)
    dept = await svc.update_department(inst.id, department_id, body.model_dump(exclude_unset=True))
    return svc._department_basic(dept)


@router.get(f"{_INST}/departments/{{department_id}}/dashboard")
async def department_dashboard(
    department_id: UUID,
    user: User = Depends(require_faculty_or_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.resolve_institution(user)
    return await svc.department_dashboard(inst.id, department_id)


@router.get(f"{_INST}/departments/{{department_id}}/review")
async def department_review(
    department_id: UUID,
    user: User = Depends(require_faculty_or_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.resolve_institution(user)
    return await svc.list_department_review(inst.id, department_id)


@router.get(f"{_INST}/departments/{{department_id}}/funding-budget")
async def department_funding_budget(
    department_id: UUID,
    user: User = Depends(require_faculty_or_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.resolve_institution(user)
    return await svc.funding_budget(inst.id, department_id=department_id)


# ── faculty ───────────────────────────────────────────────────────────────────


@router.get(f"{_INST}/faculty")
async def list_faculty(
    department_id: UUID | None = Query(None),
    user: User = Depends(require_faculty_or_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.resolve_institution(user)
    faculty = await svc.list_faculty(inst.id, department_id=department_id)
    return [svc._faculty_dict(f) for f in faculty]


@router.post(f"{_INST}/faculty", status_code=201)
async def create_faculty(
    body: CreateFacultyRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.resolve_institution(user)
    fac = await svc.create_faculty(inst.id, body.model_dump(exclude_unset=True))
    return svc._faculty_dict(fac)


@router.get(f"{_INST}/faculty/{{faculty_id}}")
async def get_faculty(
    faculty_id: UUID,
    user: User = Depends(require_faculty_or_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.resolve_institution(user)
    fac = await svc.get_faculty(inst.id, faculty_id)
    return svc._faculty_dict(fac)


@router.patch(f"{_INST}/faculty/{{faculty_id}}")
async def update_faculty(
    faculty_id: UUID,
    body: UpdateFacultyRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.resolve_institution(user)
    fac = await svc.update_faculty(inst.id, faculty_id, body.model_dump(exclude_unset=True))
    return svc._faculty_dict(fac)


# ── advisor matching ──────────────────────────────────────────────────────────


@router.get(f"{_INST}/applications/{{application_id}}/advisor-matches")
async def advisor_matches(
    application_id: UUID,
    user: User = Depends(require_faculty_or_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.resolve_institution(user)
    return await svc.list_advisor_matches(inst.id, application_id)


@router.post(
    f"{_INST}/applications/{{application_id}}/advisor-matches/{{faculty_id}}/flag-interest"
)
async def flag_advisor_interest(
    application_id: UUID,
    faculty_id: UUID,
    body: FlagInterestRequest,
    user: User = Depends(require_faculty_or_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.resolve_institution(user)
    return await svc.flag_advisor_interest(inst.id, application_id, faculty_id, body.flagged)


# ── graduate intent (institution view / edit) ─────────────────────────────────


@router.get(f"{_INST}/applications/{{application_id}}/intent")
async def get_intent(
    application_id: UUID,
    user: User = Depends(require_faculty_or_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.resolve_institution(user)
    await svc._get_application_scoped(inst.id, application_id)
    return svc._intent_dict(await svc.get_intent(application_id))


@router.put(f"{_INST}/applications/{{application_id}}/intent")
async def upsert_intent(
    application_id: UUID,
    body: IntentRequest,
    user: User = Depends(require_faculty_or_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.resolve_institution(user)
    intent = await svc.upsert_intent(inst.id, application_id, body.model_dump(exclude_unset=True))
    return svc._intent_dict(intent)


# ── funding pools + packages ──────────────────────────────────────────────────


@router.get(f"{_INST}/funding/pools")
async def list_funding_pools(
    department_id: UUID | None = Query(None),
    user: User = Depends(require_faculty_or_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.resolve_institution(user)
    pools = await svc.list_funding_pools(inst.id, department_id=department_id)
    return [svc._pool_dict_basic(p) for p in pools]


@router.post(f"{_INST}/funding/pools", status_code=201)
async def create_funding_pool(
    body: CreateFundingPoolRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.resolve_institution(user)
    pool = await svc.create_funding_pool(inst.id, body.model_dump(exclude_unset=True))
    return svc._pool_dict_basic(pool)


@router.patch(f"{_INST}/funding/pools/{{pool_id}}")
async def update_funding_pool(
    pool_id: UUID,
    body: UpdateFundingPoolRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.resolve_institution(user)
    pool = await svc.update_funding_pool(inst.id, pool_id, body.model_dump(exclude_unset=True))
    return svc._pool_dict_basic(pool)


@router.get(f"{_INST}/funding/budget")
async def funding_budget(
    department_id: UUID | None = Query(None),
    user: User = Depends(require_faculty_or_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.resolve_institution(user)
    return await svc.funding_budget(inst.id, department_id=department_id)


@router.get(f"{_INST}/applications/{{application_id}}/funding-package")
async def get_funding_package(
    application_id: UUID,
    user: User = Depends(require_faculty_or_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.resolve_institution(user)
    return await svc.get_funding_package(inst.id, application_id)


@router.put(f"{_INST}/applications/{{application_id}}/funding-package")
async def build_funding_package(
    application_id: UUID,
    body: BuildFundingPackageRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.resolve_institution(user)
    data = body.model_dump(exclude_unset=True)
    return await svc.build_funding_package(inst.id, application_id, data)


# ── two-stage department review ───────────────────────────────────────────────


@router.get(f"{_INST}/applications/{{application_id}}/review")
async def get_application_review(
    application_id: UUID,
    user: User = Depends(require_faculty_or_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.resolve_institution(user)
    return svc._review_dict(await svc.get_department_review(inst.id, application_id))


@router.post(f"{_INST}/applications/{{application_id}}/recommend")
async def recommend(
    application_id: UUID,
    body: RecommendRequest,
    user: User = Depends(require_faculty_or_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Stage 1 — department/faculty recommend a decision (does NOT release)."""
    svc = _svc(db)
    inst = await svc.resolve_institution(user)
    review = await svc.recommend(
        inst.id,
        application_id,
        decision=body.decision,
        committee_notes=body.committee_notes,
        actor_user_id=user.id,
    )
    return svc._review_dict(review)


@router.post(f"{_INST}/applications/{{application_id}}/confirm")
async def confirm_recommendation(
    application_id: UUID,
    body: ConfirmRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Stage 2 — central office confirms/overrides + releases (Spec 34). Only
    institution_admin may release — faculty get a 403 here (the two-stage gate)."""
    svc = _svc(db)
    inst = await svc.resolve_institution(user)
    return await svc.confirm_recommendation(
        inst.id,
        application_id,
        actor_user_id=user.id,
        override_decision=body.override_decision,
        offer_terms=body.offer_terms,
    )


# ── student-facing grad intent (§3 flow) ──────────────────────────────────────


@router.get("/students/me/applications/{application_id}/graduate-intent")
async def student_get_graduate_intent(
    application_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    profile = await StudentService(db)._get_student_profile(user.id)
    intent, is_grad = await svc.student_get_intent(profile.id, application_id)
    return {"is_graduate": is_grad, "intent": svc._intent_dict(intent)}


@router.put("/students/me/applications/{application_id}/graduate-intent")
async def student_put_graduate_intent(
    application_id: UUID,
    body: IntentRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    profile = await StudentService(db)._get_student_profile(user.id)
    intent = await svc.student_upsert_intent(
        profile.id, application_id, body.model_dump(exclude_unset=True)
    )
    return svc._intent_dict(intent)


@router.get("/students/me/applications/{application_id}/advisor-matches")
async def student_advisor_matches(
    application_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Spec 41 §2.1 — "Advisors who fit your research" (student-facing, read-only)."""
    svc = _svc(db)
    profile = await StudentService(db)._get_student_profile(user.id)
    return await svc.student_advisor_matches(profile.id, application_id)
