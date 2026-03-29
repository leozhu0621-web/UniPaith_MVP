from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.config import settings
from unipaith.core.exceptions import BadRequestException, NotFoundException
from unipaith.core.s3 import s3_client
from unipaith.models.student import StudentDocument
from unipaith.schemas.document import DocumentResponse, UploadResponse


ALLOWED_TYPES: dict[str, list[str]] = {
    "transcript": ["application/pdf", "image/png", "image/jpeg"],
    "essay": [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
    ],
    "resume": [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ],
    "recommendation": ["application/pdf"],
    "portfolio": ["application/pdf", "image/png", "image/jpeg"],
    "certificate": ["application/pdf", "image/png", "image/jpeg"],
}

MAX_FILE_SIZE = 10 * 1024 * 1024


class DocumentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def request_upload(
        self,
        student_id: UUID,
        document_type: str,
        file_name: str,
        content_type: str,
        file_size_bytes: int,
    ) -> UploadResponse:
        allowed = ALLOWED_TYPES.get(document_type)
        if allowed is None:
            raise BadRequestException(f"Unknown document type: {document_type}")
        if content_type not in allowed:
            raise BadRequestException(
                f"Content type {content_type} not allowed for {document_type}"
            )
        if file_size_bytes > MAX_FILE_SIZE:
            raise BadRequestException("File exceeds maximum size of 10 MB")

        key = s3_client.make_key(student_id, document_type, file_name)
        upload_url = s3_client.generate_upload_url(key, content_type)

        doc = StudentDocument(
            student_id=student_id,
            document_type=document_type,
            file_name=file_name,
            file_url=key,
            file_size_bytes=file_size_bytes,
            mime_type=content_type,
        )
        self.db.add(doc)
        await self.db.flush()

        return UploadResponse(
            upload_url=upload_url,
            document_id=doc.id,
            expires_in=settings.s3_presigned_url_expiry,
        )

    async def confirm_upload(
        self, student_id: UUID, document_id: UUID
    ) -> StudentDocument:
        doc = await self._get_document(student_id, document_id)
        if not s3_client.head_object(doc.file_url or ""):
            raise BadRequestException("File not found in storage")
        return doc

    async def list_documents(self, student_id: UUID) -> list[DocumentResponse]:
        result = await self.db.execute(
            select(StudentDocument).where(StudentDocument.student_id == student_id)
        )
        docs = result.scalars().all()
        return [DocumentResponse.model_validate(d) for d in docs]

    async def get_document(
        self, student_id: UUID, document_id: UUID
    ) -> DocumentResponse:
        doc = await self._get_document(student_id, document_id)
        resp = DocumentResponse.model_validate(doc)
        resp.download_url = s3_client.generate_download_url(doc.file_url or "")
        return resp

    async def delete_document(
        self, student_id: UUID, document_id: UUID
    ) -> None:
        doc = await self._get_document(student_id, document_id)
        if doc.file_url:
            s3_client.delete_object(doc.file_url)
        await self.db.delete(doc)
        await self.db.flush()

    async def _get_document(
        self, student_id: UUID, document_id: UUID
    ) -> StudentDocument:
        result = await self.db.execute(
            select(StudentDocument).where(
                StudentDocument.id == document_id,
                StudentDocument.student_id == student_id,
            )
        )
        doc = result.scalar_one_or_none()
        if not doc:
            raise NotFoundException("Document not found")
        return doc
