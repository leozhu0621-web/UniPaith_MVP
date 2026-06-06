"""Regression — verify_token must accept Cognito ID tokens that carry an
`at_hash` claim (every Google-federated / hosted-UI token does).

python-jose, given an ID token with `at_hash` but no access_token to compare
against, raises "No access_token provided to compare against at_hash claim".
That made `verify_token` 401 on every federated session — the original token
AND every refreshed one — so feedback (and all authed calls) failed in a loop.
The fix passes options={"verify_at_hash": False}; this test would fail without it.
"""

import time

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import jwk, jwt

from unipaith.config import settings
from unipaith.core import security
from unipaith.core.exceptions import UnauthorizedException

_KID = "test-key-1"
_CLIENT = "test-client-id"
_REGION = "us-east-1"
_POOL = "us-east-1_TESTPOOL"
_ISSUER = f"https://cognito-idp.{_REGION}.amazonaws.com/{_POOL}"


def _signing_key() -> tuple[str, dict]:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    priv_pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    pub_pem = (
        key.public_key()
        .public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
        .decode()
    )
    pub_jwk = jwk.construct(pub_pem, algorithm="RS256").to_dict()
    pub_jwk.update({"kid": _KID, "alg": "RS256", "use": "sig"})
    return priv_pem, pub_jwk


def _id_token(priv_pem: str, *, with_at_hash: bool) -> str:
    now = int(time.time())
    claims = {
        "sub": "fed-user-123",
        "email": "leo@example.com",
        "custom:role": "student",
        "token_use": "id",
        "aud": _CLIENT,
        "iss": _ISSUER,
        "exp": now + 3600,
        "iat": now,
    }
    if with_at_hash:
        # A federated ID token includes at_hash; its value is the hash of the
        # paired access token, which the API server never receives. The literal
        # below is a throwaway test placeholder, not a credential.
        claims["at_hash"] = "fake-test-at-hash"  # pragma: allowlist secret
    return jwt.encode(claims, priv_pem, algorithm="RS256", headers={"kid": _KID})


@pytest.fixture
def _cognito_jwt(monkeypatch):
    priv_pem, pub_jwk = _signing_key()
    monkeypatch.setattr(settings, "cognito_bypass", False)
    monkeypatch.setattr(settings, "cognito_app_client_id", _CLIENT)
    monkeypatch.setattr(settings, "cognito_user_pool_id", _POOL)
    monkeypatch.setattr(settings, "aws_region", _REGION)

    async def _fake_jwks():
        return {"keys": [pub_jwk]}

    monkeypatch.setattr(security, "_get_jwks", _fake_jwks)
    return priv_pem


@pytest.mark.asyncio
async def test_verify_token_accepts_federated_id_token_with_at_hash(_cognito_jwt):
    token = _id_token(_cognito_jwt, with_at_hash=True)
    claims = await security.verify_token(token)
    assert claims.sub == "fed-user-123"
    assert claims.role == "student"


@pytest.mark.asyncio
async def test_verify_token_still_rejects_expired_id_token(_cognito_jwt):
    expired = jwt.encode(
        {
            "sub": "u",
            "token_use": "id",
            "aud": _CLIENT,
            "iss": _ISSUER,
            "exp": int(time.time()) - 10,
            "iat": int(time.time()) - 3600,
            "at_hash": "abc",
        },
        _cognito_jwt,
        algorithm="RS256",
        headers={"kid": _KID},
    )
    with pytest.raises(UnauthorizedException):
        await security.verify_token(expired)
