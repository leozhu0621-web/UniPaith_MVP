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
