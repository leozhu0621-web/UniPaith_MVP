"""Demo feedback survey — submit + system-guarded collect."""

from unipaith.config import settings

PREFIX = "/api/v1"


async def test_student_submits_feedback(student_client):
    resp = await student_client.post(
        f"{PREFIX}/feedback",
        json={"title": "Loved it", "message": "The discovery chat is great."},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["message"] == "The discovery chat is great."
    assert body["title"] == "Loved it"
    assert body["role"] == "student"


async def test_feedback_requires_auth(client):
    resp = await client.post(f"{PREFIX}/feedback", json={"message": "anon"})
    assert resp.status_code >= 400  # missing/!invalid auth — never accepted anonymously


async def test_admin_collect_is_system_guarded(student_client, monkeypatch):
    await student_client.post(f"{PREFIX}/feedback", json={"message": "collect me"})

    monkeypatch.setattr(settings, "crawler_ops_token", "ops-secret")
    # No ops token → forbidden (require_system ignores the student auth).
    forbidden = await student_client.get(f"{PREFIX}/feedback/admin")
    assert forbidden.status_code == 403

    ok = await student_client.get(f"{PREFIX}/feedback/admin", headers={"X-Ops-Token": "ops-secret"})
    assert ok.status_code == 200
    assert "collect me" in [r["message"] for r in ok.json()]


async def test_admin_csv_export(student_client, monkeypatch):
    await student_client.post(f"{PREFIX}/feedback", json={"title": "T", "message": "csv row"})
    monkeypatch.setattr(settings, "crawler_ops_token", "ops-secret")
    resp = await student_client.get(
        f"{PREFIX}/feedback/admin?format=csv", headers={"X-Ops-Token": "ops-secret"}
    )
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    assert "csv row" in resp.text


async def test_owner_inbox_gated_by_email_allowlist(student_client, mock_student_user, monkeypatch):
    """The in-app inbox opens only for accounts on the owner allowlist — no ops
    token, just the logged-in user's email (matched case-insensitively)."""
    await student_client.post(
        f"{PREFIX}/feedback", json={"message": "from the inbox path", "context": {"path": "/s"}}
    )

    # Empty allowlist → nobody is an owner → locked even for an authed student.
    monkeypatch.setattr(settings, "owner_emails", "")
    locked = await student_client.get(f"{PREFIX}/feedback/inbox")
    assert locked.status_code == 403

    # Email on the allowlist (different case, extra entries) → inbox opens.
    allowlist = f"someone@else.com, {mock_student_user.email.upper()}"
    monkeypatch.setattr(settings, "owner_emails", allowlist)
    ok = await student_client.get(f"{PREFIX}/feedback/inbox")
    assert ok.status_code == 200, ok.text
    rows = ok.json()
    assert "from the inbox path" in [r["message"] for r in rows]
    # Context (the page the feedback came from) is preserved for the owner.
    assert any(r.get("context") == {"path": "/s"} for r in rows)


async def test_owner_inbox_csv_export(student_client, mock_student_user, monkeypatch):
    await student_client.post(f"{PREFIX}/feedback", json={"title": "T", "message": "owner csv row"})
    monkeypatch.setattr(settings, "owner_emails", mock_student_user.email)
    resp = await student_client.get(f"{PREFIX}/feedback/inbox?format=csv")
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    assert "owner csv row" in resp.text
