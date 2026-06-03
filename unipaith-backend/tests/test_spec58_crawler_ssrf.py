"""Spec 58 §5 — crawler SSRF guard.

Network-free: validates the IP-range classifier and the live ``fetch()`` denial
path for private / link-local hosts (the guard short-circuits before any socket
write, so no real request is made).
"""

from __future__ import annotations

import pytest

from unipaith.config import settings
from unipaith.services.crawler.fetcher import Fetcher, _host_resolves_to_public


@pytest.mark.parametrize(
    "host",
    [
        "127.0.0.1",  # loopback
        "10.0.0.1",  # private (RFC 1918)
        "192.168.1.1",  # private
        "172.16.5.4",  # private
        "169.254.169.254",  # link-local — the AWS/GCP metadata endpoint
        "::1",  # IPv6 loopback
        "0.0.0.0",  # unspecified
        "",  # empty host
    ],
)
def test_private_and_special_hosts_blocked(host: str) -> None:
    assert _host_resolves_to_public(host) is False


@pytest.mark.parametrize("host", ["8.8.8.8", "1.1.1.1"])
def test_public_ips_allowed(host: str) -> None:
    assert _host_resolves_to_public(host) is True


def test_fetch_denies_private_host_before_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """With live fetch ON, a private/link-local host is denied by the SSRF guard
    before any network call (so this test never touches the network)."""
    monkeypatch.setattr(settings, "crawler_live_fetch_enabled", True)
    res = Fetcher().fetch("http://169.254.169.254/latest/meta-data/", respect_robots=False)
    assert res.status == "denied"
    assert "ssrf_blocked" in (res.reason or "")
