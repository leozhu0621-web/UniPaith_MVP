"""Specs 48/49/50/51/52/53/54/55 — the build-transparency surface.

A read-only metadata layer that turns the build-integration / standards docs into
queryable data, the same way ``ai.catalog`` turns spec 45 into ``GET /ai/agents``:

- ``roadmap`` — spec 48's phased roadmap (current MVP → master-paper spec).
- ``features`` — spec 49's Feature-List V1 coverage map.
- ``api_contract`` — spec 50's front↔back contract, with the router map
  **derived live from the running route table** so it can never drift.
- ``data_model`` — spec 51's table map, **introspected live from the running
  SQLAlchemy metadata** so it equals the deployed schema.
- ``acceptance`` — spec 52's MVP acceptance & runbook, with the readiness summary
  **read from the running system** (routes, agents, schema, feature coverage).
- ``ux_benchmark`` — spec 53's UX bar: each surface's benchmark + build contract,
  the interaction standards, and the count of endpoints backing each surface
  **resolved live from the running route table**.
- ``frontend_standards`` — spec 54's frontend build spec: the state-layering
  rules, query-key + optimistic-mutation conventions, perf budgets, the realtime
  / analytics clients, and the §12 build-task checklist, with the §5 api-module
  ↔ router parity counts **resolved live from the running route table**.
- ``production`` — spec 55's backend production-readiness posture: the pillars
  (observability / cache / queue / rate-limit / resilience / database / health)
  honestly classified live·partial·planned, with the config knobs **read off the
  running ``settings``**, the middleware count off the running app, the health
  probes **resolved from the live route table**, and the read-cache hit-rate from
  the running ``core.cache``.

All back the public ``/build/*`` endpoints and the ``/goal`` hub. They are DB-free
and expose only build *architecture* — never any user data.
"""
