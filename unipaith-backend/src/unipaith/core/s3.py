import os
import uuid
from pathlib import Path

import boto3

from unipaith.config import settings


class S3Client:
    def __init__(self) -> None:
        if settings.s3_local_mode:
            self._local_root = Path(settings.s3_local_path)
            self._local_root.mkdir(parents=True, exist_ok=True)
            self.client = None
        else:
            self.client = boto3.client(
                "s3",
                region_name=settings.aws_region,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
            )
        self.bucket = settings.s3_bucket_name

    def generate_upload_url(
        self, key: str, content_type: str, expires_in: int | None = None
    ) -> str:
        if expires_in is None:
            expires_in = settings.s3_presigned_url_expiry

        if settings.s3_local_mode:
            local_path = self._local_root / key
            local_path.parent.mkdir(parents=True, exist_ok=True)
            return f"file://{local_path.resolve()}"

        return self.client.generate_presigned_url(  # type: ignore[union-attr]
            "put_object",
            Params={"Bucket": self.bucket, "Key": key, "ContentType": content_type},
            ExpiresIn=expires_in,
        )

    def generate_download_url(self, key: str, expires_in: int = 3600) -> str:
        if settings.s3_local_mode:
            local_path = self._local_root / key
            return f"file://{local_path.resolve()}"

        return self.client.generate_presigned_url(  # type: ignore[union-attr]
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=expires_in,
        )

    def delete_object(self, key: str) -> None:
        if settings.s3_local_mode:
            local_path = self._local_root / key
            if local_path.exists():
                local_path.unlink()
            return

        self.client.delete_object(Bucket=self.bucket, Key=key)  # type: ignore[union-attr]

    def head_object(self, key: str) -> bool:
        if settings.s3_local_mode:
            return (self._local_root / key).exists()
        try:
            self.client.head_object(Bucket=self.bucket, Key=key)  # type: ignore[union-attr]
            return True
        except Exception:
            return False

    @staticmethod
    def make_key(student_id: uuid.UUID, document_type: str, file_name: str) -> str:
        ext = os.path.splitext(file_name)[1] or ".bin"
        return f"documents/{student_id}/{document_type}/{uuid.uuid4()}{ext}"


s3_client = S3Client()
