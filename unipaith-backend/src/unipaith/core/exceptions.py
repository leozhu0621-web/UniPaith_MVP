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


class UnauthorizedException(UniPaithException):
    """401 — the request's credentials are missing, invalid, or expired. Distinct
    from 403 (authenticated but not allowed): a 401 tells the client to refresh
    its token and retry, which the web client's axios interceptor does on 401.
    Token verification failures MUST use this (not 400) so expired sessions
    auto-recover instead of failing every call until manual re-login."""

    def __init__(self, detail: str = "Unauthorized"):
        super().__init__(status_code=401, detail=detail, error_code="UNAUTHORIZED")


class ForbiddenException(UniPaithException):
    def __init__(self, detail: str = "Forbidden"):
        super().__init__(status_code=403, detail=detail, error_code="FORBIDDEN")


class BadRequestException(UniPaithException):
    def __init__(self, detail: str = "Bad request"):
        super().__init__(status_code=400, detail=detail, error_code="BAD_REQUEST")


class ConflictException(UniPaithException):
    def __init__(self, detail: str = "Conflict"):
        super().__init__(status_code=409, detail=detail, error_code="CONFLICT")


class PaymentRequiredException(UniPaithException):
    """402 — submission is gated on an unpaid/unwaived application fee (Spec 39
    §2.2/§7). ``detail`` is a structured payload so the UI can route to the pay/
    waiver step: {"message", "amount", "currency", "waiver_allowed"}."""

    def __init__(self, detail: Any):
        super().__init__(status_code=402, detail=detail, error_code="PAYMENT_REQUIRED")


class UnprocessableEntityException(UniPaithException):
    """422 with a structured detail payload. Used by the program-publish
    validator so the editor can list every missing field and scroll to its
    section (Spec 23 §6). `detail` is typically
    {"message": str, "missing_fields": [{"field", "section", "message"}, ...]}.
    """

    def __init__(self, detail: Any):
        super().__init__(status_code=422, detail=detail, error_code="UNPROCESSABLE_ENTITY")
