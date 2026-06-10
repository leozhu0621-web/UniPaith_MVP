"""POST /students/me/recommendations/{id}/send — real email-send behavior.

The send endpoint must actually contact the recommender (SES) when
``email_send_enabled`` is on, and must not pretend it did when it is off —
``email_sent`` is explicit in the response. A failed send must leave the
request untouched (no status flip) and surface a 502.
"""

from __future__ import annotations

import pytest

from unipaith.config import settings
from unipaith.models.student import StudentProfile

API = "/api/v1/students/me/recommendations"


class _FakeSES:
    """Records send_email calls; stands in for boto3's SES client."""

    def __init__(self) -> None:
        self.calls: list[dict] = []

    def send_email(self, **kwargs):
        self.calls.append(kwargs)
        return {"MessageId": "fake-message-id"}


class _BrokenSES:
    def send_email(self, **kwargs):
        raise RuntimeError("ses unavailable")


@pytest.fixture
async def student_profile(db_session, mock_student_user) -> StudentProfile:
    profile = StudentProfile(
        user_id=mock_student_user.id, first_name="Jo", last_name="Lin"
    )
    db_session.add(profile)
    await db_session.flush()
    return profile


async def _create_rec(student_client, **overrides) -> dict:
    payload = {
        "recommender_name": "Dr. Ada Calc",
        "recommender_email": "ada@example.edu",
        "due_date": "2026-08-01",
    }
    payload.update(overrides)
    resp = await student_client.post(API, json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


async def test_send_disabled_flips_status_but_reports_no_email(
    student_client, student_profile, monkeypatch
):
    monkeypatch.setattr(settings, "email_send_enabled", False)
    fake = _FakeSES()
    monkeypatch.setattr("boto3.client", lambda *a, **k: fake)

    rec = await _create_rec(student_client)
    resp = await student_client.post(f"{API}/{rec['id']}/send")

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "requested"
    assert body["requested_at"] is not None
    assert body["email_sent"] is False
    assert fake.calls == []


async def test_send_enabled_emails_recommender_then_flips_status(
    student_client, student_profile, monkeypatch
):
    monkeypatch.setattr(settings, "email_send_enabled", True)
    fake = _FakeSES()
    monkeypatch.setattr("boto3.client", lambda *a, **k: fake)

    rec = await _create_rec(student_client)
    resp = await student_client.post(f"{API}/{rec['id']}/send")

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["email_sent"] is True
    assert body["status"] == "requested"
    assert body["requested_at"] is not None

    assert len(fake.calls) == 1
    call = fake.calls[0]
    assert call["Destination"]["ToAddresses"] == ["ada@example.edu"]
    assert "Jo Lin" in call["Message"]["Subject"]["Data"]
    text = call["Message"]["Body"]["Text"]["Data"]
    assert "Dr. Ada Calc" in text
    assert "Jo Lin" in text
    assert "2026-08-01" in text
    # Plain student-context request — never an AI-generated letter.
    assert "letter of recommendation" in text


async def test_send_enabled_without_recommender_email_skips_send(
    student_client, student_profile, monkeypatch
):
    monkeypatch.setattr(settings, "email_send_enabled", True)
    fake = _FakeSES()
    monkeypatch.setattr("boto3.client", lambda *a, **k: fake)

    rec = await _create_rec(student_client, recommender_email=None)
    resp = await student_client.post(f"{API}/{rec['id']}/send")

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["email_sent"] is False
    assert body["status"] == "requested"
    assert fake.calls == []


async def test_send_failure_returns_502_and_does_not_flip_status(
    student_client, student_profile, monkeypatch
):
    monkeypatch.setattr(settings, "email_send_enabled", True)
    monkeypatch.setattr("boto3.client", lambda *a, **k: _BrokenSES())

    rec = await _create_rec(student_client)
    resp = await student_client.post(f"{API}/{rec['id']}/send")

    assert resp.status_code == 502, resp.text
    assert "could not be delivered" in resp.json()["detail"]

    # The request must be untouched — the recommender was never contacted.
    after = (await student_client.get(f"{API}/{rec['id']}")).json()
    assert after["status"] == "draft"
    assert after["requested_at"] is None


async def test_list_response_carries_email_sent_default(
    student_client, student_profile
):
    await _create_rec(student_client)
    resp = await student_client.get(API)
    assert resp.status_code == 200
    assert resp.json()[0]["email_sent"] is False
