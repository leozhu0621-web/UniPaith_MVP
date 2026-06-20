"""AirtableClient — thin async HTTP client for the Airtable REST API.

Wraps the Airtable records endpoint with pagination support.  Built on
``httpx.AsyncClient`` (already a project dependency).

Usage::

    async with AirtableClient(api_key, base_id) as client:
        records = await client.list_records("Prompts")

Each record has the shape::

    {"id": "<airtable record id>", "fields": {<column: value, ...>}}

``is_configured`` returns False when either credential is empty — the sync
service uses this to skip the sync rather than raising.
"""

from __future__ import annotations

from typing import Any

import httpx

_AIRTABLE_API_BASE = "https://api.airtable.com/v0"


class AirtableClient:
    """Async Airtable records client.

    Designed to be used as an async context manager so the underlying
    ``httpx.AsyncClient`` is properly closed::

        async with AirtableClient(api_key, base_id) as client:
            records = await client.list_records("My Table")

    It can also be used without a context manager (e.g. in tests that inject a
    fake); in that case the caller is responsible for cleanup.
    """

    def __init__(self, api_key: str, base_id: str) -> None:
        self._api_key = api_key
        self._base_id = base_id
        self._http: httpx.AsyncClient | None = None

    # ------------------------------------------------------------------
    # Context-manager support
    # ------------------------------------------------------------------

    async def __aenter__(self) -> AirtableClient:
        self._http = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {self._api_key}"},
            timeout=30.0,
        )
        return self

    async def __aexit__(self, *_: object) -> None:
        if self._http is not None:
            await self._http.aclose()
            self._http = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def is_configured(self) -> bool:
        """True when both api_key and base_id are non-empty strings."""
        return bool(self._api_key and self._base_id)

    async def list_records(self, table_name: str) -> list[dict[str, Any]]:
        """Fetch all records from *table_name*, following Airtable pagination.

        Returns a list of ``{"id": str, "fields": dict}`` objects.

        Raises ``RuntimeError`` when the client is not configured.
        Raises ``httpx.HTTPStatusError`` on non-2xx responses.
        """
        if not self.is_configured:
            raise RuntimeError("AirtableClient is not configured: api_key and base_id are required")

        http = self._http
        if http is None:
            # Allow use without async context manager (e.g. one-shot calls).
            http = httpx.AsyncClient(
                headers={"Authorization": f"Bearer {self._api_key}"},
                timeout=30.0,
            )

        url = f"{_AIRTABLE_API_BASE}/{self._base_id}/{table_name}"
        records: list[dict[str, Any]] = []
        params: dict[str, str] = {}

        try:
            while True:
                response = await http.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                records.extend(data.get("records", []))
                offset = data.get("offset")
                if not offset:
                    break
                params = {"offset": offset}
        finally:
            # Only close if we opened it ourselves (not context-manager-owned).
            if self._http is None:
                await http.aclose()

        return records
