from __future__ import annotations

from typing import Any

from fastapi import HTTPException


class UniPaithException(HTTPException):
    def __init__(
        self,
        status_code: int,
        detail: Any,
        error_code: str | None = None,
    ):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code


class NotFoundException(UniPaithException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=404, detail=detail, error_code="NOT_FOUND")


class ForbiddenException(UniPaithException):
    def __init__(self, detail: str = "Forbidden"):
        super().__init__(status_code=403, detail=detail, error_code="FORBIDDEN")


class BadRequestException(UniPaithException):
    def __init__(self, detail: str = "Bad request"):
        super().__init__(status_code=400, detail=detail, error_code="BAD_REQUEST")


class ConflictException(UniPaithException):
    def __init__(self, detail: str = "Conflict"):
        super().__init__(status_code=409, detail=detail, error_code="CONFLICT")


class UnprocessableEntityException(UniPaithException):
    """422 with a structured detail payload. Used by the program-publish
    validator so the editor can list every missing field and scroll to its
    section (Spec 23 §6). `detail` is typically
    {"message": str, "missing_fields": [{"field", "section", "message"}, ...]}.
    """

    def __init__(self, detail: Any):
        super().__init__(status_code=422, detail=detail, error_code="UNPROCESSABLE_ENTITY")
