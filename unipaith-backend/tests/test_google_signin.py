"""GIS-direct Google sign-in endpoint — config + token-validation guards.

A real Google ID token can't be minted in tests, so these cover the wiring +
error paths (no network: malformed tokens fail before the JWKS fetch)."""

from unipaith.config import settings

PREFIX = "/api/v1"


async def test_google_signin_not_configured(client, monkeypatch):
    monkeypatch.setattr(settings, "google_client_id", "")
    resp = await client.post(f"{PREFIX}/auth/google", json={"id_token": "a.b.c"})
    assert resp.status_code == 400
    assert "not configured" in resp.text.lower()


async def test_google_signin_rejects_malformed_token(client, monkeypatch):
    monkeypatch.setattr(settings, "google_client_id", "demo.apps.googleusercontent.com")
    resp = await client.post(f"{PREFIX}/auth/google", json={"id_token": "not-a-jwt"})
    assert resp.status_code == 400
    assert "invalid google token" in resp.text.lower()
