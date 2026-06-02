"""Spec 48/49/50/53 — the build-transparency surface.

A read-only metadata layer that turns the build-integration / standards docs into
queryable data, the same way ``ai.catalog`` turns spec 45 into ``GET /ai/agents``:

- ``roadmap`` — spec 48's phased roadmap (current MVP → master-paper spec).
- ``features`` — spec 49's Feature-List V1 coverage map.
- ``api_contract`` — spec 50's front↔back contract, with the router map
  **derived live from the running route table** so it can never drift.
- ``ux_benchmark`` — spec 53's UX bar: each surface's benchmark + build contract,
  the interaction standards, and the count of endpoints backing each surface
  **resolved live from the running route table**.

All four back the public ``/build/*`` endpoints and the ``/goal`` hub. They are
DB-free and expose only build *architecture* — never any user data.
"""
