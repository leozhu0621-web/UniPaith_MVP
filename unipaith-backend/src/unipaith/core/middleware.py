import logging
import time
import uuid

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from unipaith.config import settings
from unipaith.core.exceptions import UniPaithException
from unipaith.core.rate_limit import limiter, rate_limit_exceeded_handler

logger = logging.getLogger("unipaith")


async def request_id_middleware(request: Request, call_next):  # noqa: ANN001
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response: Response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


async def logging_middleware(request: Request, call_next):  # noqa: ANN001
    start = time.perf_counter()
    response: Response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "%s %s -> %s (%.1fms)",
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )
    return response


async def security_headers_middleware(request: Request, call_next):  # noqa: ANN001
    response: Response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if settings.environment == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


async def exception_handler(request: Request, exc: UniPaithException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "error_code": exc.error_code,
        },
    )


async def general_exception_handler(
    request: Request,
    exc: Exception,  # noqa: ARG001
) -> JSONResponse:
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error_code": "internal_error",
        },
    )


def setup_middleware(app: FastAPI) -> None:
    # GZip compression for responses > 1KB
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)  # type: ignore[arg-type]

    # Custom middleware stack
    app.middleware("http")(security_headers_middleware)
    app.middleware("http")(request_id_middleware)
    app.middleware("http")(logging_middleware)

    # Exception handlers
    app.add_exception_handler(UniPaithException, exception_handler)  # type: ignore[arg-type]
    if not settings.debug:
        app.add_exception_handler(Exception, general_exception_handler)  # type: ignore[arg-type]
