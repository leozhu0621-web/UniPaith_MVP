"""Flatten the live FastAPI route table for transparency introspection.

FastAPI >=0.115 registers ``include_router`` mounts as lazy ``_IncludedRouter``
wrappers — ``app.routes`` no longer lists the nested ``/api/v1/*`` handlers
directly. Transparency surfaces (build-transparency, acceptance, production
health probes) must expand those wrappers so route counts reflect what's deployed.
"""

from __future__ import annotations

from typing import Any


class _PrefixedRoute:
    """Proxy a route with a resolved absolute path (preserves ``dependant`` etc.)."""

    __slots__ = ("_route", "path")

    def __init__(self, route: Any, path: str) -> None:
        object.__setattr__(self, "_route", route)
        object.__setattr__(self, "path", path)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._route, name)

    def __repr__(self) -> str:
        return f"_PrefixedRoute({self.path!r})"


def expand_routes(app_or_routes: Any, *, _prefix: str = "") -> list[Any]:
    """Return route-like objects with resolved ``path`` / ``methods`` / ``tags``.

    Accepts a FastAPI app, an APIRouter, or a plain route sequence (for tests).
    Original route objects are preserved (via :class:`_PrefixedRoute`) so callers
    that inspect ``dependant`` — e.g. auth-guard audits — keep working.
    """
    if hasattr(app_or_routes, "routes") and not isinstance(app_or_routes, list):
        return expand_routes(app_or_routes.routes, _prefix=_prefix)

    out: list[Any] = []
    for route in app_or_routes:
        kind = type(route).__name__
        if kind == "_IncludedRouter":
            prefix = route.include_context.prefix or ""
            out.extend(expand_routes(route.original_router.routes, _prefix=_prefix + prefix))
            continue
        if hasattr(route, "routes") and kind not in {"APIRoute", "Route"}:
            mount_prefix = getattr(route, "path", "") or ""
            out.extend(expand_routes(route.routes, _prefix=_prefix + mount_prefix))
            continue
        path = getattr(route, "path", "") or ""
        full_path = _prefix + path
        out.append(_PrefixedRoute(route, full_path) if _prefix and path else route)
    return out
