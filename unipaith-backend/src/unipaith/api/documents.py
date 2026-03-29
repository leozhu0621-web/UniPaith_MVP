from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.dependencies import require_student
from unipaith.models.user import User
from unipaith.schemas.document import DocumentResponse, UploadRequest, UploadResponse
from unipaith.services.document_service import DocumentService
from unipaith.services.student_service import StudentService

router = APIRouter(prefix="/students/me/documents", tags=["documents"])


@router.post("/request-upload", response_model=UploadResponse)
async def request_upload(
    body: UploadRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await StudentService(db)._get_student_profile(user.id)
    svc = DocumentService(db)
    return await svc.request_upload(
        student_id=profile.id,
        document_type=body.document_type,
        file_name=body.file_name,
        content_type=body.content_type,
        file_size_bytes=body.file_size_bytes,
    )


@router.post("/{document_id}/confirm", response_model=DocumentResponse)
async def confirm_upload(
    document_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await StudentService(db)._get_student_profile(user.id)
    svc = DocumentService(db)
    return await svc.confirm_upload(profile.id, document_id)


@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await StudentService(db)._get_student_profile(user.id)
    svc = DocumentService(db)
    return await svc.list_documents(profile.id)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await StudentService(db)._get_student_profile(user.id)
    svc = DocumentService(db)
    return await svc.get_document(profile.id, document_id)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await StudentService(db)._get_student_profile(user.id)
    svc = DocumentService(db)
    await svc.delete_document(profile.id, document_id)
