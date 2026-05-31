from __future__ import annotations

from fastapi import HTTPException


class UniPaithException(HTTPException):
    def __init__(
        self,
        status_code: int,
        detail: str,
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


class PaymentRequiredException(UniPaithException):
    """402 — the caller's plan does not entitle them to a paid feature
    (Spec 06 §4 paywall). The body carries the gated feature so the client
    can render the right upgrade prompt."""

    def __init__(
        self,
        detail: str = "A subscription is required for this feature.",
        *,
        feature: str | None = None,
    ):
        super().__init__(status_code=402, detail=detail, error_code="PAYMENT_REQUIRED")
        self.feature = feature
