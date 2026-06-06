import time
import uuid
from typing import Any

import httpx
from jose import JWTError, jwk, jwt
from pydantic import BaseModel

from unipaith.config import settings
from unipaith.core.exceptions import UnauthorizedException

_jwks_cache: dict[str, Any] = {}
_jwks_fetched_at: float = 0
JWKS_CACHE_TTL = 86400  # 24 hours

# Environments where the dev auth bypass must never be enabled (spec 58 §2).
DEPLOYED_ENVIRONMENTS: frozenset[str] = frozenset({"production", "staging"})


def auth_bypass_safe() -> bool:
    """True unless the dev auth bypass is enabled in a deployed environment.

    ``_verify_dev_token`` accepts ``dev:<uuid>:<role>`` tokens whenever
    ``cognito_bypass`` is true — convenient in dev, catastrophic in prod. This
    predicate is the invariant the ``/goal/security`` surface reports and the
    boot guard enforces.
    """
    deployed = settings.environment.strip().lower() in DEPLOYED_ENVIRONMENTS
    return not (deployed and settings.cognito_bypass)


def assert_secure_auth_config() -> None:
    """Spec 58 §2 — fail boot if the dev auth bypass ships to prod/staging.

    Raises ``RuntimeError`` so the process refuses to serve rather than silently
    accepting forged ``dev:`` tokens — the 52 §5 launch blocker, enforced in
    code. Safe in dev/test, which run ``environment=development``.
    """
    if not auth_bypass_safe():
        raise RuntimeError(
            "SECURITY: cognito_bypass is enabled in a deployed environment "
            f"(environment={settings.environment!r}). The dev auth bypass must "
            "never ship to production/staging — refusing to boot."
        )


class CognitoClaims(BaseModel):
    sub: str
    email: str
    role: str


async def _get_jwks() -> dict[str, Any]:
    global _jwks_cache, _jwks_fetched_at  # noqa: PLW0603
    now = time.time()
    if _jwks_cache and (now - _jwks_fetched_at) < JWKS_CACHE_TTL:
        return _jwks_cache

    url = (
        f"https://cognito-idp.{settings.aws_region}.amazonaws.com"
        f"/{settings.cognito_user_pool_id}/.well-known/jwks.json"
    )
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        _jwks_cache = resp.json()
        _jwks_fetched_at = now
    return _jwks_cache


def _verify_dev_token(token: str) -> CognitoClaims:
    """Parse dev bypass token format: dev:<user_id>:<role>"""
    parts = token.split(":")
    if len(parts) != 3 or parts[0] != "dev":
        raise UnauthorizedException("Invalid dev token format. Expected dev:<user_id>:<role>")
    try:
        uuid.UUID(parts[1])
    except ValueError:
        raise UnauthorizedException("Invalid user_id in dev token")  # noqa: B904
    return CognitoClaims(sub=parts[1], email=f"dev-{parts[1][:8]}@dev.local", role=parts[2])


async def verify_token(token: str) -> CognitoClaims:
    if settings.cognito_bypass:
        return _verify_dev_token(token)

    try:
        jwks_data = await _get_jwks()
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        key = None
        for k in jwks_data.get("keys", []):
            if k["kid"] == kid:
                key = jwk.construct(k)
                break
        if key is None:
            raise UnauthorizedException("Token key not found in JWKS")

        issuer = (
            f"https://cognito-idp.{settings.aws_region}.amazonaws.com"
            f"/{settings.cognito_user_pool_id}"
        )
        payload = jwt.decode(
            token,
            key.to_dict(),
            algorithms=["RS256"],
            audience=settings.cognito_app_client_id,
            issuer=issuer,
        )
        return CognitoClaims(
            sub=payload["sub"],
            email=payload.get("email", ""),
            role=payload.get("custom:role", "student"),
        )
    except JWTError as e:
        # Expired / bad-signature / wrong-audience → 401 (NOT 400) so the web
        # client's interceptor refreshes the token and retries instead of
        # failing every call until manual re-login. See core/exceptions.py.
        raise UnauthorizedException(f"Invalid token: {e}") from e
