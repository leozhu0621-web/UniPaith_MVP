# Task 06: Document Upload — S3 Integration

## Context

You are building document upload for **UniPaith**. Tasks 01-05 set up the full CRUD layer. Now add the ability for students to upload documents (transcripts, essays, resumes, recommendations) to S3 and track them in the database.

**Architecture decision:** We use **presigned URLs** — the backend generates a temporary upload URL, the frontend uploads directly to S3 (no file passes through the API server). This keeps the API lightweight and scales better.

## What to Build

### 1. core/s3.py — S3 Client

```python
import boto3
from unipaith.config import settings

class S3Client:
    def __init__(self):
        self.client = boto3.client(
            "s3",
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )
        self.bucket = settings.s3_bucket_name

    def generate_upload_url(
        self,
        key: str,
        content_type: str,
        expires_in: int = settings.s3_presigned_url_expiry,
    ) -> str:
        """
        Generate a presigned PUT URL for direct upload.
        Key format: documents/{student_id}/{document_type}/{uuid}.{ext}
        """
        return self.client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": self.bucket,
                "Key": key,
                "ContentType": content_type,
            },
            ExpiresIn=expires_in,
        )

    def generate_download_url(self, key: str, expires_in: int = 3600) -> str:
        """Generate a presigned GET URL for downloading."""
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=expires_in,
        )

    def delete_object(self, key: str) -> None:
        """Delete a file from S3."""
        self.client.delete_object(Bucket=self.bucket, Key=key)


# Singleton
s3_client = S3Client()
```

### 2. services/document_service.py

```python
class DocumentService:
    ALLOWED_TYPES = {
        "transcript": ["application/pdf", "image/png", "image/jpeg"],
        "essay": ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain"],
        "resume": ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"],
        "recommendation": ["application/pdf"],
        "portfolio": ["application/pdf", "image/png", "image/jpeg"],
        "certificate": ["application/pdf", "image/png", "image/jpeg"],
    }

    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

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
        """
        1. Validate document_type is known
        2. Validate content_type is allowed for this document_type
        3. Validate file_size_bytes <= MAX_FILE_SIZE
        4. Generate S3 key: documents/{student_id}/{document_type}/{uuid}.{ext}
        5. Generate presigned upload URL
        6. Create StudentDocument record with status pending (file_url set to final S3 path)
        7. Return {upload_url, document_id, expires_in}
        """

    async def confirm_upload(self, student_id: UUID, document_id: UUID) -> StudentDocument:
        """
        Called after frontend successfully uploads to S3.
        1. Verify the file exists in S3 (head_object)
        2. Update document record (mark as confirmed)
        3. Return document record
        """

    async def list_documents(self, student_id: UUID) -> list[StudentDocument]:
        """List all documents for a student."""

    async def get_document(self, student_id: UUID, document_id: UUID) -> StudentDocument:
        """Get single document with download URL."""

    async def get_download_url(self, student_id: UUID, document_id: UUID) -> str:
        """Generate presigned download URL."""

    async def delete_document(self, student_id: UUID, document_id: UUID) -> None:
        """
        1. Verify ownership
        2. Delete from S3
        3. Delete DB record
        """
```

### 3. api/documents.py — Routes

All routes require `require_student` dependency.

```
POST /api/v1/students/me/documents/request-upload
  Body: {document_type, file_name, content_type, file_size_bytes}
  Response: {upload_url, document_id, expires_in}
  Notes: Returns presigned S3 URL. Frontend uploads directly to this URL.

POST /api/v1/students/me/documents/{document_id}/confirm
  Response: Document record
  Notes: Call after successful S3 upload to finalize the record.

GET  /api/v1/students/me/documents
  Response: [Document, ...]

GET  /api/v1/students/me/documents/{document_id}
  Response: Document with download_url

DELETE /api/v1/students/me/documents/{document_id}
  Response: 204
```

### 4. schemas/document.py

```python
class UploadRequest(BaseModel):
    document_type: Literal["transcript", "essay", "resume", "recommendation", "portfolio", "certificate"]
    file_name: str = Field(min_length=1, max_length=255)
    content_type: str
    file_size_bytes: int = Field(gt=0, le=10_485_760)  # Max 10MB

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
    download_url: str | None = None  # Populated on detail view
```

### 5. Upload Flow Diagram

```
Frontend                    Backend API                  S3
   |                            |                        |
   |-- POST /request-upload --> |                        |
   |                            |-- generate presigned ->|
   |   {upload_url, doc_id} <-- |                        |
   |                            |                        |
   |-- PUT upload_url -------->-|----------------------->|
   |   (direct upload)          |                        |-- store file
   |   200 OK <----------------|------------------------|
   |                            |                        |
   |-- POST /confirm ---------->|                        |
   |                            |-- head_object -------->|
   |                            |<-- file exists --------|
   |   {document} <------------ |                        |
```

### 6. S3 Bucket Configuration Script

Create `scripts/setup_s3.py`:

```python
"""
Create S3 bucket with proper configuration for UniPaith document storage.
Run once during infrastructure setup.
"""
```

The script should:
- Create the bucket in the configured region
- Enable server-side encryption (AES-256)
- Set CORS policy to allow PUT from frontend origin
- Set lifecycle rule: delete incomplete multipart uploads after 1 day
- Block all public access (presigned URLs only)

### 7. Tests — test_documents.py

**Upload flow tests:**
- Request upload with valid params → 200 with upload_url
- Request upload with invalid document_type → 422
- Request upload with unsupported content_type for document_type → 400
- Request upload exceeding max file size → 400/422
- Confirm upload → 200 with document record

**Document management tests:**
- List documents returns all for student
- Get document includes download URL
- Delete document removes record (mock S3)
- Cannot access another student's documents → 403/404

**Mock S3 in tests:** Use `moto` library or simply mock the S3Client methods. Tests should NOT require real S3 access.

### 8. Local Development Without S3

For local development, support a `S3_LOCAL_MODE=true` environment variable that:
- Stores files to a local directory (`./uploads/`) instead of S3
- Generates file:// URLs instead of presigned URLs
- Allows development without AWS credentials

Add to config.py:
```python
s3_local_mode: bool = False
s3_local_path: str = "./uploads"
```

## Important Notes

- **Never** pass file contents through the API. The presigned URL pattern keeps files off the API server entirely.
- The `extracted_text` column on `student_documents` is for future use (Phase 2 — OCR/PDF parsing via LLM). Leave it NULL for now.
- S3 key structure (`documents/{student_id}/{type}/{uuid}.{ext}`) makes it easy to list/manage files per student and enforce access control.
- CORS on the S3 bucket must allow PUT from the frontend origin, otherwise direct upload will fail.
- The two-step flow (request → upload → confirm) ensures we only track files that actually made it to S3.
