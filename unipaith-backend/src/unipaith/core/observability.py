"""Spec 55 §2 — structured observability primitives.

The biggest real backend gap was observability. This module formalizes it:

- A ``request_id`` **contextvar** so every log line emitted while handling a
  request carries the id (§2 "every log + error carries the id").
- ``ContextJsonFormatter`` — a ``python-json-logger`` formatter that injects the
  current request id into *every* JSON record, so a downstream error log and the
  access log share one id you can grep across.
- ``log_access`` — one JSON line per request with the §2 field set
  (request_id, method, route, status, latency_ms, client; user_id/role when a
  downstream dependency has populated ``request.state``).

Wired in ``core/middleware.py`` (the single ``observability_middleware``) and
``main.py`` (``_setup_logging`` uses ``ContextJsonFormatter``).
"""

from __future__ import annotations

import contextvars
import logging
from typing import Any

from pythonjsonlogger.json import JsonFormatter

# The id of the in-flight request, or None outside a request. ``default`` keeps
# module-load and background-job logs working without a request scope.
request_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id", default=None
)

# Dedicated logger for the per-request access line so it can be routed/sampled
# independently of application logs if needed.
access_logger = logging.getLogger("unipaith.access")


def bind_request_id(request_id: str) -> contextvars.Token:
    """Bind the request id for the current async context. Returns the reset token."""
    return request_id_ctx.set(request_id)


def reset_request_id(token: contextvars.Token) -> None:
    request_id_ctx.reset(token)


def get_request_id() -> str | None:
    return request_id_ctx.get()


class ContextJsonFormatter(JsonFormatter):
    """JSON formatter that stamps every record with the active request id.

    Subclasses ``python-json-logger`` (already a dependency) so the existing log
    pipeline keeps its shape; we only add ``request_id`` when one is bound.
    """

    def add_fields(
        self,
        log_record: dict[str, Any],
        record: logging.LogRecord,
        message_dict: dict[str, Any],
    ) -> None:
        super().add_fields(log_record, record, message_dict)
        request_id = request_id_ctx.get()
        if request_id is not None and "request_id" not in log_record:
            log_record["request_id"] = request_id


def log_access(
    *,
    request_id: str | None,
    method: str,
    path: str,
    route: str,
    status_code: int,
    latency_ms: float,
    client: str | None,
    user_id: str | None = None,
    role: str | None = None,
) -> None:
    """Emit the structured per-request access log line (§2).

    One JSON object carrying the golden-signal fields (latency, status) keyed by
    request id and route template — the substrate for the §2 dashboards.
    """
    access_logger.info(
        "http_request",
        extra={
            "event": "http_request",
            "request_id": request_id,
            "method": method,
            "path": path,
            "route": route,
            "status": status_code,
            "latency_ms": round(latency_ms, 1),
            "client": client,
            "user_id": user_id,
            "role": role,
        },
    )
