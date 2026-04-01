from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.dependencies import require_institution_admin, require_student
from unipaith.models.user import User
from unipaith.schemas.event import (
    CreateEventRequest,
    EventResponse,
    RSVPResponse,
    UpdateEventRequest,
)
from unipaith.services.event_service import EventService
from unipaith.services.institution_service import InstitutionService
from unipaith.services.student_service import StudentService

router = APIRouter(prefix="/events", tags=["events"])


# --- Public / Student ---


@router.get("", response_model=list[EventResponse])
async def list_upcoming_events(
    program_id: UUID | None = Query(None),
    institution_id: UUID | None = Query(None),
    event_type: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    svc = EventService(db)
    return await svc.list_upcoming_events(
        program_id=program_id,
        institution_id=institution_id,
        event_type=event_type,
        limit=limit,
    )


@router.post("/{event_id}/rsvp", response_model=RSVPResponse, status_code=status.HTTP_201_CREATED)
async def rsvp_to_event(
    event_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await StudentService(db)._get_student_profile(user.id)
    svc = EventService(db)
    return await svc.rsvp(profile.id, event_id, user.id)


@router.delete("/{event_id}/rsvp", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_rsvp(
    event_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await StudentService(db)._get_student_profile(user.id)
    svc = EventService(db)
    await svc.cancel_rsvp(profile.id, event_id)


@router.get("/{event_id}/calendar")
async def download_calendar(
    event_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    svc = EventService(db)
    ical_data = await svc.generate_ics(event_id)
    return Response(content=ical_data, media_type="text/calendar")


@router.get("/me/rsvps", response_model=list[RSVPResponse])
async def my_rsvps(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await StudentService(db)._get_student_profile(user.id)
    svc = EventService(db)
    return await svc.list_student_rsvps(profile.id)


# --- Institution Management ---


@router.post("/manage", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    body: CreateEventRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    inst = await InstitutionService(db).get_institution(user.id)
    svc = EventService(db)
    return await svc.create_event(
        institution_id=inst.id,
        event_name=body.event_name,
        event_type=body.event_type,
        start_time=body.start_time,
        end_time=body.end_time,
        description=body.description,
        location=body.location,
        capacity=body.capacity,
        program_id=body.program_id,
    )


@router.get("/manage", response_model=list[EventResponse])
async def list_my_events(
    event_status: str | None = Query(None, alias="status"),
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    inst = await InstitutionService(db).get_institution(user.id)
    svc = EventService(db)
    return await svc.list_institution_events(inst.id, status_filter=event_status)


@router.put("/manage/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: UUID,
    body: UpdateEventRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    inst = await InstitutionService(db).get_institution(user.id)
    svc = EventService(db)
    return await svc.update_event(
        institution_id=inst.id,
        event_id=event_id,
        **body.model_dump(exclude_unset=True),
    )


@router.post("/manage/{event_id}/cancel", response_model=EventResponse)
async def cancel_event(
    event_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    inst = await InstitutionService(db).get_institution(user.id)
    svc = EventService(db)
    return await svc.cancel_event(inst.id, event_id)


@router.get("/manage/{event_id}/attendees", response_model=list[RSVPResponse])
async def get_attendees(
    event_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    inst = await InstitutionService(db).get_institution(user.id)
    svc = EventService(db)
    return await svc.get_event_attendees(inst.id, event_id)
