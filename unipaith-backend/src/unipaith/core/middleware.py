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
from unipaith.core.observability import bind_request_id, log_access, reset_request_id
from unipaith.core.rate_limit import limiter, rate_limit_exceeded_handler

logger = logging.getLogger("unipaith")


async def observability_middleware(request: Request, call_next):  # noqa: ANN001
    """Spec 55 §2 — request id + structured access log in one pass.

    Mints a request id, binds it to the async context (so every log emitted
    while serving this request carries it), times the request, echoes the id on
    ``X-Request-ID``, and emits one JSON access line with the golden-signal
    fields. The ``finally`` block logs even when the handler raises (status 500),
    so an errored request still produces its access record.
    """
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    token = bind_request_id(request_id)
    start = time.perf_counter()
    status_code = 500
    try:
        response: Response = await call_next(request)
        status_code = response.status_code
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        latency_ms = (time.perf_counter() - start) * 1000
        route = request.scope.get("route")
        route_path = getattr(route, "path", None) or request.url.path
        user_id = getattr(request.state, "user_id", None)
        log_access(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            route=route_path,
            status_code=status_code,
            latency_ms=latency_ms,
            client=request.client.host if request.client else None,
            user_id=str(user_id) if user_id else None,
            role=getattr(request.state, "role", None),
        )
        reset_request_id(token)


# Spec 58 §8 — the security headers the app sets on every response. Declared as
# data so the /goal/security transparency surface can introspect the live set
# (it imports SECURITY_HEADERS and reports the names), and so the header policy
# has a single source of truth. HSTS is added separately (production-only).
SECURITY_HEADERS: dict[str, str] = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    # The API serves JSON, so a strict CSP is safe defence-in-depth against
    # clickjacking / injection — `default-src 'none'` allows nothing to load.
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'; base-uri 'none'",
}

# Swagger / Redoc / the OpenAPI JSON load CDN assets, so the strict CSP would
# break them. They are debug-only routes; skip CSP (only) for them.
_CSP_SKIP_PREFIXES = ("/docs", "/redoc", "/openapi.json")


async def security_headers_middleware(request: Request, call_next):  # noqa: ANN001
    response: Response = await call_next(request)
    skip_csp = request.url.path.startswith(_CSP_SKIP_PREFIXES)
    for name, value in SECURITY_HEADERS.items():
        if name == "Content-Security-Policy" and skip_csp:
            continue
        response.headers[name] = value
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
        allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)  # type: ignore[arg-type]

    # Custom middleware stack. observability_middleware is added last so it is
    # the OUTERMOST wrapper — it binds the request id before any other layer
    # runs and times the full request (incl. security-header work).
    app.middleware("http")(security_headers_middleware)
    app.middleware("http")(observability_middleware)

    # Exception handlers
    app.add_exception_handler(UniPaithException, exception_handler)  # type: ignore[arg-type]
    if not settings.debug:
        app.add_exception_handler(Exception, general_exception_handler)  # type: ignore[arg-type]
