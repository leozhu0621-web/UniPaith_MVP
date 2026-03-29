from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UploadRequest(BaseModel):
    document_type: Literal[
        "transcript", "essay", "resume", "recommendation", "portfolio", "certificate"
    ]
    file_name: str = Field(min_length=1, max_length=255)
    content_type: str
    file_size_bytes: int = Field(gt=0, le=10_485_760)


class UploadResponse(BaseModel):
    upload_url: str
    document_id: UUID
    expires_in: int


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    student_id: UUID
    document_type: str
    file_name: str
    file_size_bytes: int | None
    mime_type: str | None
    uploaded_at: datetime
    download_url: str | None = None
