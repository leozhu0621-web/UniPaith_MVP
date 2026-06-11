# Uni Managed Agent — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the in-app `orchestrator.py` conversation brain with "Uni," a managed agent on the Claude platform; the FastAPI backend becomes a thin host that relays the conversation and answers five host-side custom tools against RDS.

**Architecture:** Anthropic runs the agent loop + per-session container. The host (`uni_agent_host.py`) opens each Anthropic session's event stream, relays the student turn, and answers `agent.custom_tool_use` events by calling existing services. It reuses the existing SSE endpoint `/students/me/discovery/sessions/{id}/messages/stream` and its event contract (`student_message` / `delta` / `tool_use` / `assistant_message` / `error` / `done`) so the frontend barely changes. Gated by `ai_uni_managed_agent_v1`; the DB never leaves the VPC.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2 async, Postgres + Alembic, the `anthropic` SDK managed-agents beta (`client.beta.agents/sessions/environments`), pytest-asyncio. Frontend React 19 / TS / Vite.

**Design spec:** [docs/superpowers/specs/2026-06-10-uni-managed-agent-design.md](../specs/2026-06-10-uni-managed-agent-design.md). Verified service surface is in the spec appendix.

**Test command (backend):**
```bash
cd unipaith-backend && PYTHONPATH=src AI_MOCK_MODE=true \
  .venv/bin/pytest tests/<file>.py -v --tb=short
```
conftest sets `AI_MOCK_MODE/COGNITO_BYPASS/S3_LOCAL_MODE=true`. Fixtures: `db_session`, `client`, `student_client`, `mock_student_user`, `monkeypatch`. AI agents are faked with a `_Fake*` class injected via `monkeypatch.setattr("module.get_thing", lambda: _Fake(...))` (see `tests/test_plan2_integration.py`).

**Scope note:** This plan covers **Phases 0–2 (the backend foundation)** in full, bite-sized TDD detail — at the end you have a flag-gated, fully-tested managed-Uni conversation path driven by a faked Anthropic client, plus the agent created on the platform. **Phase 3 (frontend re-point, eval cases, catalog registration, retire orchestrator) is enumerated at the bottom and becomes its own plan** (each produces working software on its own).

---

## File Structure

| File | Responsibility | New/Mod |
|---|---|---|
| `unipaith-backend/pyproject.toml` | bump `anthropic` to a managed-agents-capable version | Mod |
| `unipaith-backend/src/unipaith/config.py` | `ai_uni_managed_agent_v1`, `uni_agent_id`, `uni_environment_id` | Mod |
| `unipaith-backend/src/unipaith/ai/managed_agent_client.py` | thin wrapper around `client.beta.{agents,sessions,environments}` | New |
| `unipaith-backend/src/unipaith/services/uni_tools.py` | the 5 host-side tool functions + dispatcher | New |
| `unipaith-backend/src/unipaith/services/student_service.py` | `get_full_snapshot()` | Mod |
| `unipaith-backend/src/unipaith/services/match_service.py` | `list_matches_for_display()` (factor from `get_my_matches`) | Mod |
| `unipaith-backend/src/unipaith/services/uni_agent_host.py` | session create/resume + stream-first turn loop + graceful envelope | New |
| `unipaith-backend/src/unipaith/models/discovery.py` | `DiscoverySession.agent_session_id` | Mod |
| `unipaith-backend/alembic/versions/uni_agent_sess_*.py` | add column migration | New |
| `unipaith-backend/src/unipaith/api/discovery.py` | route `/messages/stream` through the host when flag on | Mod |
| `unipaith-backend/tests/test_uni_tools.py` | tool + dispatcher tests | New |
| `unipaith-backend/tests/test_uni_agent_host.py` | turn-loop + envelope tests (faked client) | New |

---

## Phase 0 — Prerequisites (SDK + config)

### Task 0.1: Bump the anthropic SDK to a managed-agents-capable version

**Files:**
- Modify: `unipaith-backend/pyproject.toml:20` (`"anthropic>=0.39.0",`)

- [ ] **Step 1: Check the installed SDK for the managed-agents surface**

Run:
```bash
cd unipaith-backend && .venv/bin/python -c "from anthropic import AsyncAnthropic; c=AsyncAnthropic(api_key='x'); print('agents', hasattr(c.beta,'agents'), '| sessions', hasattr(c.beta,'sessions'), '| environments', hasattr(c.beta,'environments'))"
```
Expected on 0.39.0: `agents False | sessions False | environments False`.

- [ ] **Step 2: Upgrade and re-check**

Run:
```bash
cd unipaith-backend && .venv/bin/pip install -U anthropic && .venv/bin/python -c "import anthropic; print(anthropic.__version__)" && .venv/bin/python -c "from anthropic import AsyncAnthropic; c=AsyncAnthropic(api_key='x'); print('agents', hasattr(c.beta,'agents'), '| sessions', hasattr(c.beta,'sessions'))"
```
Expected: a version that prints `agents True | sessions True`. If the latest still lacks them, the managed-agents beta requires a newer release — stop and report; do not proceed.

- [ ] **Step 3: Pin the version in pyproject.toml**

Replace line 20 `"anthropic>=0.39.0",` with the resolved version, e.g. `"anthropic>=0.69.0",` (use the actual installed major.minor from Step 2).

- [ ] **Step 4: Smoke-import the rest of the app**

Run: `cd unipaith-backend && PYTHONPATH=src AI_MOCK_MODE=true .venv/bin/python -c "import unipaith.main"`
Expected: no import errors (the bump didn't break the Messages-API path).

- [ ] **Step 5: Commit**

```bash
git add unipaith-backend/pyproject.toml
git commit -m "build: bump anthropic SDK to managed-agents-capable version"
```

### Task 0.2: Add config settings

**Files:**
- Modify: `unipaith-backend/src/unipaith/config.py` (flags ~line 225; key ~line 144)
- Test: `unipaith-backend/tests/test_uni_config.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_uni_config.py
from unipaith.config import settings


def test_uni_managed_agent_settings_exist():
    assert settings.ai_uni_managed_agent_v1 is False  # default off
    assert settings.uni_agent_id == ""
    assert settings.uni_environment_id == ""
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd unipaith-backend && PYTHONPATH=src AI_MOCK_MODE=true .venv/bin/pytest tests/test_uni_config.py -v --tb=short`
Expected: FAIL `AttributeError: 'Settings' object has no attribute 'ai_uni_managed_agent_v1'`.

- [ ] **Step 3: Add the settings**

Near line 225 (the `ai_*` flag block) add:
```python
    # Spec: Uni managed agent — route the student discovery conversation to the
    # managed agent on platform.claude.com instead of the in-app orchestrator.
    # When True, /messages/stream is driven by uni_agent_host; on platform
    # failure the host returns a graceful message (never a 5xx). Hard cutover.
    ai_uni_managed_agent_v1: bool = False
    # Managed-agent identifiers (from `ant beta:agents create` / the Console).
    uni_agent_id: str = ""
    uni_environment_id: str = ""
```

- [ ] **Step 4: Run to verify it passes**

Run: `cd unipaith-backend && PYTHONPATH=src AI_MOCK_MODE=true .venv/bin/pytest tests/test_uni_config.py -v --tb=short`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add unipaith-backend/src/unipaith/config.py tests/test_uni_config.py
git commit -m "feat(config): add ai_uni_managed_agent_v1 + uni agent/env ids"
```

---

## Phase 1 — Tools + snapshot + migration (no live platform)

Each tool function has the signature `async def tool_<name>(db: AsyncSession, student_id: UUID, tool_input: dict) -> dict`. They're pure host-side service calls — fully unit-testable.

### Task 1.1: `StudentService.get_full_snapshot()`

**Files:**
- Modify: `unipaith-backend/src/unipaith/services/student_service.py`
- Test: `unipaith-backend/tests/test_uni_snapshot.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_uni_snapshot.py
import pytest
from unipaith.services.student_service import StudentService
from tests.helpers import seed_student_with_goal  # if no helper, inline a profile create


@pytest.mark.asyncio
async def test_get_full_snapshot_shape(db_session, mock_student_user):
    svc = StudentService(db_session)
    snap = await svc.get_full_snapshot(mock_student_user.id)
    assert set(snap.keys()) == {"profile", "goals", "needs", "identity", "active_strategy", "completion"}
    assert isinstance(snap["goals"], list)
    assert isinstance(snap["completion"], dict)
```

(If `tests.helpers.seed_student_with_goal` doesn't exist, replace the import and use the existing `_ensure_profile`-style helper from `tests/test_plan2_integration.py`; the assertion on keys is the point.)

- [ ] **Step 2: Run to verify it fails**

Run: `cd unipaith-backend && PYTHONPATH=src AI_MOCK_MODE=true .venv/bin/pytest tests/test_uni_snapshot.py -v --tb=short`
Expected: FAIL `AttributeError: 'StudentService' object has no attribute 'get_full_snapshot'`.

- [ ] **Step 3: Implement**

Add to `StudentService` (compose the five verified loaders; keep it a plain dict so it serializes straight to the `get_profile_snapshot` tool result):
```python
    async def get_full_snapshot(self, user_id: UUID) -> dict:
        """Consolidated counselor snapshot for the Uni managed agent.

        Composes the existing per-domain loaders. Returns a compact,
        JSON-serializable dict the host hands back from get_profile_snapshot.
        """
        from unipaith.services.goals_service import GoalsService
        from unipaith.services.needs_service import NeedsService
        from unipaith.services.identity_service import IdentityService
        from unipaith.services.strategy_service import StrategyService
        from unipaith.services.discovery_service import DiscoveryService

        profile = await self.get_profile(user_id)
        goals = await GoalsService(self.db).list_goals(user_id)
        needs = await NeedsService(self.db).list_needs(user_id)
        identity = await IdentityService(self.db).get(user_id)
        strategy = await StrategyService(self.db).get_active(user_id)
        completion = await DiscoveryService(self.db).get_completion_map(user_id)

        return {
            "profile": {
                "first_name": profile.first_name,
                "last_name": profile.last_name,
            },
            "goals": [
                {"category": g.category, "specific": g.specific, "status": g.status}
                for g in goals
            ],
            "needs": [
                {"maslow_level": n.maslow_level, "signal": n.signal, "severity": n.severity}
                for n in needs
            ],
            "identity": {
                "core_values": identity.core_values,
                "worldview": identity.worldview,
                "self_awareness": identity.self_awareness,
                "summary": identity.identity_summary,
            },
            "active_strategy": (
                {
                    "career_target": strategy.career_target,
                    "target_degree": strategy.target_degree,
                    "narrative": strategy.narrative,
                }
                if strategy
                else None
            ),
            "completion": {k: float(v) for k, v in completion.items()},
        }
```
Confirm `StudentService.__init__` stores the session as `self.db` (it does — `_get_student_profile` uses it); if it's named differently, match the existing attribute.

- [ ] **Step 4: Run to verify it passes**

Run: `cd unipaith-backend && PYTHONPATH=src AI_MOCK_MODE=true .venv/bin/pytest tests/test_uni_snapshot.py -v --tb=short`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add unipaith-backend/src/unipaith/services/student_service.py tests/test_uni_snapshot.py
git commit -m "feat(student): get_full_snapshot for the Uni counselor session"
```

### Task 1.2: `save_signals` adapter (build ExtractedSignals → persist → completion → handoff)

**Files:**
- Create: `unipaith-backend/src/unipaith/services/uni_tools.py`
- Test: `unipaith-backend/tests/test_uni_tools.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_uni_tools.py
import pytest
from unipaith.services.uni_tools import tool_save_signals


@pytest.mark.asyncio
async def test_save_signals_writes_goal_and_returns_completion(db_session, mock_student_user):
    tool_input = {
        "goals": [{
            "category": "academic",
            "specific": "Earn a funded CS PhD",
            "measurable": "Admitted with full funding",
            "achievable": "Strong research background",
            "relevant": "Career in ML research",
            "time_bound": "2027",
            "completeness": 1.0,
            "evidence": "I want a fully funded CS PhD by 2027.",
        }],
        "confidence": {"goals": 0.9},
    }
    out = await tool_save_signals(db_session, mock_student_user.id, tool_input)
    assert "completion" in out and set(out["completion"]) >= {"profile", "goals", "needs"}
    assert "handoff_ready" in out
    assert out["written"]["goals_written"] >= 0
```

(`mock_student_user.id` is the user id; `tool_save_signals` resolves user→student internally via the existing services, matching `persist_extraction(student_id=...)` which the adapter feeds the student id. If `persist_extraction` needs the *student profile* id rather than the *user* id, resolve it with `StudentService(db)._get_student_profile(user_id)` first — verify against `persist_extraction`'s `student_id` semantics.)

- [ ] **Step 2: Run to verify it fails**

Run: `cd unipaith-backend && PYTHONPATH=src AI_MOCK_MODE=true .venv/bin/pytest tests/test_uni_tools.py::test_save_signals_writes_goal_and_returns_completion -v --tb=short`
Expected: FAIL `ModuleNotFoundError: No module named 'unipaith.services.uni_tools'`.

- [ ] **Step 3: Implement the adapter**

```python
# services/uni_tools.py
"""Host-side custom-tool implementations for the Uni managed agent.

Each tool maps an `agent.custom_tool_use` to an existing UniPaith service and
returns a JSON-serializable dict the host sends back as `user.custom_tool_result`.
The DB never leaves the VPC; the agent only ever sees these results.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ai.artifacts import persist_extraction
from unipaith.ai.extractor import ExtractedSignals
from unipaith.services.discovery_service import DiscoveryService


def _signals_from_tool_input(tool_input: dict[str, Any]) -> ExtractedSignals:
    """Build ExtractedSignals from the save_signals payload (which mirrors
    EXTRACT_SIGNALS_TOOL). The top-level `confidence` block becomes
    confidence_per_key as Decimals; persist_extraction applies its own
    completeness/idempotency gating downstream."""
    conf = tool_input.get("confidence") or {}
    return ExtractedSignals(
        basic=tool_input.get("basic") or {},
        personality=tool_input.get("personality") or [],
        identity=tool_input.get("identity") or [],
        goals=tool_input.get("goals") or [],
        needs=tool_input.get("needs") or [],
        confidence_per_key={k: Decimal(str(v)) for k, v in conf.items()},
        raw_response=tool_input,
    )


async def tool_save_signals(
    db: AsyncSession, user_id: UUID, tool_input: dict[str, Any], *, session_id: UUID | None = None
) -> dict[str, Any]:
    disc = DiscoveryService(db)
    student_id = await disc._student_id_for_user(user_id)  # see note below
    extraction = _signals_from_tool_input(tool_input)
    result = await persist_extraction(
        db=db, student_id=student_id, session_id=session_id, extraction=extraction
    )
    await db.commit()
    completion = await disc.get_completion_map(user_id)
    handoff = await disc.evaluate_handoff(user_id)
    return {
        "written": {
            "goals_written": result.goals_written,
            "needs_written": result.needs_written,
            "identity_added": (
                result.identity_values_added
                + result.identity_worldview_added
                + result.identity_self_awareness_added
            ),
            "basic_fields_written": result.basic_fields_written,
        },
        "completion": {k: float(v) for k, v in completion.items()},
        "handoff_ready": bool(handoff.get("should_handoff")),
    }
```

**Note on `_student_id_for_user`:** `persist_extraction(student_id=...)` expects the **student-profile id**. `DiscoveryService` already resolves user→student internally (its methods take `user_id`). If a public resolver doesn't exist, use `StudentService(db)._get_student_profile(user_id).id`. Pick whichever the existing discovery service uses for `persist_extraction` calls (grep `persist_extraction(` in `discovery_service.py` to copy the exact id it passes) and match it.

`session_id` is optional here — the host passes the mirrored `discovery_sessions.id` so provenance constraints (`source='discovery'` requires `source_session_id`) are satisfied. The test omits it; if `persist_extraction` requires a non-null session for discovery goals, the test should create a discovery session first or the adapter should default `source='inferred'`. Verify `persist_extraction`'s null-session behavior and adjust the test to create a session via `DiscoveryService(db).start_session(...)` if needed.

- [ ] **Step 4: Run to verify it passes**

Run: `cd unipaith-backend && PYTHONPATH=src AI_MOCK_MODE=true .venv/bin/pytest tests/test_uni_tools.py::test_save_signals_writes_goal_and_returns_completion -v --tb=short`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add unipaith-backend/src/unipaith/services/uni_tools.py tests/test_uni_tools.py
git commit -m "feat(uni): save_signals tool — ExtractedSignals adapter + completion/handoff"
```

### Task 1.3: `search_programs` tool

**Files:**
- Modify: `unipaith-backend/src/unipaith/services/uni_tools.py`
- Test: `unipaith-backend/tests/test_uni_tools.py`

- [ ] **Step 1: Write the failing test**

```python
@pytest.mark.asyncio
async def test_search_programs_returns_compact_facts(db_session, mock_student_user, seed_published_program):
    from unipaith.services.uni_tools import tool_search_programs
    out = await tool_search_programs(db_session, mock_student_user.id, {"query": "computer science"})
    assert "programs" in out and isinstance(out["programs"], list)
    if out["programs"]:
        p = out["programs"][0]
        assert {"program_name", "institution_name", "degree_type"} <= set(p)
```

(`seed_published_program` — reuse the catalog seed helper used in matching/search tests, or inline a `Program(is_published=True)` insert. If the test DB is empty the assertion still holds: `programs == []`.)

- [ ] **Step 2: Run to verify it fails**

Run: `cd unipaith-backend && PYTHONPATH=src AI_MOCK_MODE=true .venv/bin/pytest tests/test_uni_tools.py::test_search_programs_returns_compact_facts -v --tb=short`
Expected: FAIL `ImportError: cannot import name 'tool_search_programs'`.

- [ ] **Step 3: Implement (tuition cents→USD conversion happens here, agent speaks USD)**

```python
from unipaith.services.institution_service import InstitutionService


async def tool_search_programs(
    db: AsyncSession, user_id: UUID, tool_input: dict[str, Any]
) -> dict[str, Any]:
    svc = InstitutionService(db)
    page = await svc.search_programs(
        query=tool_input.get("query"),
        country=tool_input.get("country"),
        degree_types=tool_input.get("degree_types"),
        # agent speaks USD; the column is cents → convert filters
        min_tuition=(tool_input["min_tuition"] * 100) if tool_input.get("min_tuition") else None,
        max_tuition=(tool_input["max_tuition"] * 100) if tool_input.get("max_tuition") else None,
        delivery_formats=tool_input.get("delivery_formats"),
        location=tool_input.get("location"),
        page=1,
        page_size=8,
    )
    return {
        "programs": [
            {
                "program_name": p.program_name,
                "institution_name": p.institution_name,
                "country": p.institution_country,
                "city": p.institution_city,
                "degree_type": p.degree_type,
                "tuition_usd": (p.tuition // 100) if p.tuition is not None else None,
                "duration_months": p.duration_months,
                "acceptance_rate": p.acceptance_rate,
                "application_deadline": (
                    p.application_deadline.isoformat() if p.application_deadline else None
                ),
                "median_salary_usd": (p.median_salary // 100) if p.median_salary is not None else None,
                "employment_rate": p.employment_rate,
                "summary": (p.description_text or "")[:280],
            }
            for p in page.items
        ],
        "total": page.total,
    }
```

Confirm `Program.tuition` / `ProgramSummaryResponse.tuition` is in cents (the appendix says cents) — if it's whole USD, drop the `* 100` / `// 100`.

- [ ] **Step 4: Run to verify it passes**

Run: `cd unipaith-backend && PYTHONPATH=src AI_MOCK_MODE=true .venv/bin/pytest tests/test_uni_tools.py::test_search_programs_returns_compact_facts -v --tb=short`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add unipaith-backend/src/unipaith/services/uni_tools.py tests/test_uni_tools.py
git commit -m "feat(uni): search_programs tool bound to InstitutionService"
```

### Task 1.4: `MatchService.list_matches_for_display()` + `get_matches` tool

**Files:**
- Modify: `unipaith-backend/src/unipaith/services/match_service.py` (factor display logic out of the `get_my_matches` endpoint)
- Modify: `unipaith-backend/src/unipaith/services/uni_tools.py`
- Test: `unipaith-backend/tests/test_uni_tools.py`

- [ ] **Step 1: Write the failing test**

```python
@pytest.mark.asyncio
async def test_get_matches_gates_on_handoff(db_session, mock_student_user):
    from unipaith.services.uni_tools import tool_get_matches
    out = await tool_get_matches(db_session, mock_student_user.id, {})
    # Fresh student is not handoff-ready → tool reports not-ready + what's missing.
    assert out["ready"] is False
    assert "completion" in out
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd unipaith-backend && PYTHONPATH=src AI_MOCK_MODE=true .venv/bin/pytest tests/test_uni_tools.py::test_get_matches_gates_on_handoff -v --tb=short`
Expected: FAIL `ImportError: cannot import name 'tool_get_matches'`.

- [ ] **Step 3a: Factor display composition into a service method**

In `get_my_matches` (api/students.py) the endpoint enriches `list_matches` rows with band + program fields. Move that composition into `MatchService.list_matches_for_display(self, student_id: UUID, *, limit: int = 8) -> list[dict]` returning, per match: `{program_id, program_name, institution_name, fitness, confidence, band}`. Have the existing `get_my_matches` endpoint call the new method (no behavior change) so there's one source of truth. Run the existing matches tests to confirm no regression:
Run: `cd unipaith-backend && PYTHONPATH=src AI_MOCK_MODE=true .venv/bin/pytest tests/ -k "match" -q`
Expected: PASS (unchanged behavior).

- [ ] **Step 3b: Implement the tool**

```python
from unipaith.services.match_service import MatchService


async def tool_get_matches(
    db: AsyncSession, user_id: UUID, tool_input: dict[str, Any]
) -> dict[str, Any]:
    disc = DiscoveryService(db)
    handoff = await disc.evaluate_handoff(user_id)
    if not handoff.get("should_handoff"):
        return {
            "ready": False,
            "completion": {k: float(v) for k, v in (handoff.get("completion") or {}).items()},
            "reason": handoff.get("reason"),
        }
    student_id = await disc._student_id_for_user(user_id)  # same resolver as tool_save_signals
    await disc._recompute_matches_for_student(student_id=student_id)
    matches = await MatchService(db).list_matches_for_display(student_id, limit=8)
    return {"ready": True, "matches": matches}
```

- [ ] **Step 4: Run to verify it passes**

Run: `cd unipaith-backend && PYTHONPATH=src AI_MOCK_MODE=true .venv/bin/pytest tests/test_uni_tools.py::test_get_matches_gates_on_handoff -v --tb=short`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add unipaith-backend/src/unipaith/services/match_service.py unipaith-backend/src/unipaith/services/uni_tools.py unipaith-backend/src/unipaith/api/students.py tests/test_uni_tools.py
git commit -m "feat(uni): get_matches tool (handoff-gated) + list_matches_for_display"
```

### Task 1.5: `generate_strategy` tool + dispatcher

**Files:**
- Modify: `unipaith-backend/src/unipaith/services/uni_tools.py`
- Test: `unipaith-backend/tests/test_uni_tools.py`

- [ ] **Step 1: Write the failing test (dispatcher routes by name)**

```python
@pytest.mark.asyncio
async def test_dispatch_unknown_tool_returns_error(db_session, mock_student_user):
    from unipaith.services.uni_tools import dispatch_tool
    out = await dispatch_tool(db_session, mock_student_user.id, "nope", {}, session_id=None)
    assert out["error"]


@pytest.mark.asyncio
async def test_dispatch_get_profile_snapshot(db_session, mock_student_user):
    from unipaith.services.uni_tools import dispatch_tool
    out = await dispatch_tool(db_session, mock_student_user.id, "get_profile_snapshot", {}, session_id=None)
    assert "completion" in out  # snapshot shape
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd unipaith-backend && PYTHONPATH=src AI_MOCK_MODE=true .venv/bin/pytest tests/test_uni_tools.py -k dispatch -v --tb=short`
Expected: FAIL `ImportError: cannot import name 'dispatch_tool'`.

- [ ] **Step 3: Implement strategy tool + snapshot tool + dispatcher**

```python
from unipaith.services.strategy_service import StrategyService
from unipaith.services.student_service import StudentService


async def tool_generate_strategy(
    db: AsyncSession, user_id: UUID, tool_input: dict[str, Any]
) -> dict[str, Any]:
    try:
        strat = await StrategyService(db).generate(user_id)
    except Exception as exc:  # e.g. no active academic goal → 400-equivalent
        return {"error": "strategy_unavailable", "detail": str(exc)[:200]}
    return {
        "career_target": strat.career_target,
        "target_degree": strat.target_degree,
        "academic_path": strat.academic_path,
        "financial_path": strat.financial_path,
        "geographic_path": strat.geographic_path,
        "narrative": strat.narrative,
    }


async def tool_get_profile_snapshot(
    db: AsyncSession, user_id: UUID, tool_input: dict[str, Any]
) -> dict[str, Any]:
    return await StudentService(db).get_full_snapshot(user_id)


_NO_SESSION = {"tool_search_programs", "tool_get_matches", "tool_generate_strategy", "tool_get_profile_snapshot"}

_TOOLS = {
    "get_profile_snapshot": tool_get_profile_snapshot,
    "search_programs": tool_search_programs,
    "save_signals": tool_save_signals,
    "get_matches": tool_get_matches,
    "generate_strategy": tool_generate_strategy,
}


async def dispatch_tool(
    db: AsyncSession, user_id: UUID, name: str, tool_input: dict[str, Any], *, session_id: UUID | None
) -> dict[str, Any]:
    fn = _TOOLS.get(name)
    if fn is None:
        return {"error": f"unknown_tool:{name}"}
    if name == "save_signals":
        return await fn(db, user_id, tool_input, session_id=session_id)
    return await fn(db, user_id, tool_input)
```

- [ ] **Step 4: Run to verify it passes**

Run: `cd unipaith-backend && PYTHONPATH=src AI_MOCK_MODE=true .venv/bin/pytest tests/test_uni_tools.py -v --tb=short`
Expected: PASS (all tool tests).

- [ ] **Step 5: Commit**

```bash
git add unipaith-backend/src/unipaith/services/uni_tools.py tests/test_uni_tools.py
git commit -m "feat(uni): generate_strategy + get_profile_snapshot tools + dispatch_tool"
```

### Task 1.6: Migration — `discovery_sessions.agent_session_id`

**Files:**
- Modify: `unipaith-backend/src/unipaith/models/discovery.py` (add column + index to `DiscoverySession`)
- Create: `unipaith-backend/alembic/versions/uni_agent_sess_a1b2c3.py`
- Test: `unipaith-backend/tests/test_uni_migration.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_uni_migration.py
import pytest
from sqlalchemy import select
from unipaith.models.discovery import DiscoverySession


@pytest.mark.asyncio
async def test_discovery_session_has_agent_session_id(db_session, mock_student_user):
    from unipaith.services.student_service import StudentService
    sp = await StudentService(db_session)._get_student_profile(mock_student_user.id)
    ds = DiscoverySession(student_id=sp.id, track="profile", layer="basic", agent_session_id="sesn_x")
    db_session.add(ds)
    await db_session.flush()
    row = (await db_session.execute(select(DiscoverySession).where(DiscoverySession.id == ds.id))).scalar_one()
    assert row.agent_session_id == "sesn_x"
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd unipaith-backend && PYTHONPATH=src AI_MOCK_MODE=true .venv/bin/pytest tests/test_uni_migration.py -v --tb=short`
Expected: FAIL `TypeError: 'agent_session_id' is an invalid keyword argument for DiscoverySession`.

- [ ] **Step 3a: Add the column to the model**

In `models/discovery.py`, inside `DiscoverySession` after `exit_signal`:
```python
    # Anthropic managed-agent session id (sesn_...) bound to this journey.
    # NULL until the first turn creates the platform session. See uni_agent_host.
    agent_session_id: Mapped[str | None] = mapped_column(String(64))
```
Add an index in `__table_args__`:
```python
        Index("ix_discovery_sessions_agent_session_id", "agent_session_id"),
```

- [ ] **Step 3b: Find the current migration head**

Run: `cd unipaith-backend && ls -1 alembic/versions/ | sort | tail -5` and `cd unipaith-backend && PYTHONPATH=src .venv/bin/alembic heads 2>/dev/null || echo "use the tail output"`
Note the single head revision id — call it `<HEAD>`.

- [ ] **Step 3c: Write the migration (guarded, mirrors p65embed1a2b3)**

```python
# alembic/versions/uni_agent_sess_a1b2c3.py
"""Uni managed agent — discovery_sessions.agent_session_id.

Adds the column that binds a student's discovery journey to its Anthropic
managed-agent session id. Guarded so it is a safe no-op against the conftest
``create_all`` test DB.

Revision ID: uni_agent_sess_a1b2c3
Revises: <HEAD>
Create Date: 2026-06-10
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "uni_agent_sess_a1b2c3"  # pragma: allowlist secret
down_revision = "<HEAD>"  # pragma: allowlist secret  ← set to the id from Step 3b
branch_labels = None
depends_on = None


def _cols() -> set[str]:
    insp = sa.inspect(op.get_bind())
    if "discovery_sessions" not in insp.get_table_names():
        return set()
    return {c["name"] for c in insp.get_columns("discovery_sessions")}


def upgrade() -> None:
    cols = _cols()
    if not cols:
        return
    if "agent_session_id" not in cols:
        op.add_column(
            "discovery_sessions",
            sa.Column("agent_session_id", sa.String(length=64), nullable=True),
        )
        op.create_index(
            "ix_discovery_sessions_agent_session_id",
            "discovery_sessions",
            ["agent_session_id"],
        )


def downgrade() -> None:
    cols = _cols()
    if "agent_session_id" in cols:
        op.drop_index("ix_discovery_sessions_agent_session_id", table_name="discovery_sessions")
        op.drop_column("discovery_sessions", "agent_session_id")
```

- [ ] **Step 4: Run to verify it passes + single head**

Run: `cd unipaith-backend && PYTHONPATH=src AI_MOCK_MODE=true .venv/bin/pytest tests/test_uni_migration.py tests/test_alembic_has_single_head.py -v --tb=short`
Expected: PASS (the model test passes because conftest `create_all` builds the new column; the single-head test confirms `down_revision` chained correctly).

- [ ] **Step 5: Commit**

```bash
git add unipaith-backend/src/unipaith/models/discovery.py "unipaith-backend/alembic/versions/uni_agent_sess_a1b2c3.py" tests/test_uni_migration.py
git commit -m "feat(uni): discovery_sessions.agent_session_id (+ migration)"
```

---

## Phase 2 — Managed-agent client + turn loop + endpoint routing

### Task 2.1: Thin managed-agent client

**Files:**
- Create: `unipaith-backend/src/unipaith/ai/managed_agent_client.py`
- Test: covered indirectly via the host (Task 2.2) with a fake; add one import test.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_uni_agent_host.py
def test_managed_agent_client_importable():
    from unipaith.ai.managed_agent_client import ManagedAgentClient  # noqa: F401
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd unipaith-backend && PYTHONPATH=src AI_MOCK_MODE=true .venv/bin/pytest tests/test_uni_agent_host.py::test_managed_agent_client_importable -v --tb=short`
Expected: FAIL `ModuleNotFoundError`.

- [ ] **Step 3: Implement (interface only — the host depends on this surface, the fake mirrors it)**

```python
# ai/managed_agent_client.py
"""Thin wrapper over the Anthropic managed-agents beta (client.beta.*).

Kept separate from ai/client.py (the Messages-API + cost-ledger singleton) so
the managed-agents surface is isolated and easy to fake in tests.
"""
from __future__ import annotations

from typing import Any, AsyncIterator

from unipaith.config import settings


class ManagedAgentClient:
    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or settings.anthropic_api_key
        self._sdk: Any = None

    def _client(self) -> Any:
        if self._sdk is None:
            from anthropic import AsyncAnthropic

            self._sdk = AsyncAnthropic(api_key=self._api_key)
        return self._sdk

    async def create_session(self, *, agent_id: str, environment_id: str, title: str) -> str:
        sess = await self._client().beta.sessions.create(
            agent=agent_id, environment_id=environment_id, title=title
        )
        return sess.id

    async def stream(self, session_id: str) -> AsyncIterator[Any]:
        async with self._client().beta.sessions.events.stream(session_id) as stream:
            async for event in stream:
                yield event

    async def send_user_message(self, session_id: str, text: str) -> None:
        await self._client().beta.sessions.events.send(
            session_id, events=[{"type": "user.message", "content": [{"type": "text", "text": text}]}]
        )

    async def send_tool_result(self, session_id: str, tool_use_id: str, result: dict) -> None:
        import json

        await self._client().beta.sessions.events.send(
            session_id,
            events=[{
                "type": "user.custom_tool_result",
                "custom_tool_use_id": tool_use_id,
                "content": [{"type": "text", "text": json.dumps(result, default=str)}],
            }],
        )
```

> Verify the exact SDK call shapes (`beta.sessions.events.stream` signature, event attribute names `event.type` / `event.name` / `event.input` / `event.id` / `event.content`, and the `user.custom_tool_result` field name `custom_tool_use_id`) against the installed SDK's managed-agents README before wiring the host. The shapes above are from the claude-api managed-agents reference (Python). If the SDK uses positional vs keyword args differently, adjust here only — the host depends on this wrapper, not the raw SDK.

- [ ] **Step 4: Run to verify it passes**

Run: `cd unipaith-backend && PYTHONPATH=src AI_MOCK_MODE=true .venv/bin/pytest tests/test_uni_agent_host.py::test_managed_agent_client_importable -v --tb=short`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add unipaith-backend/src/unipaith/ai/managed_agent_client.py tests/test_uni_agent_host.py
git commit -m "feat(uni): thin ManagedAgentClient over the anthropic managed-agents beta"
```

### Task 2.2: The host turn loop (stream-first, dispatch, mirror, graceful envelope)

**Files:**
- Create: `unipaith-backend/src/unipaith/services/uni_agent_host.py`
- Test: `unipaith-backend/tests/test_uni_agent_host.py`

The host's `stream_turn` is a drop-in for `DiscoveryService.stream_message`: an async generator yielding `(event_name, payload)` tuples in the existing SSE contract. It takes an injected `client` (real `ManagedAgentClient` in prod, a fake in tests).

- [ ] **Step 1: Write the failing test with a faked client**

```python
# tests/test_uni_agent_host.py (append)
import pytest


class _FakeEvent:
    def __init__(self, type, **kw):
        self.type = type
        for k, v in kw.items():
            setattr(self, k, v)


class _FakeAgentClient:
    """Scripts an Anthropic session: greets, calls one tool, replies, idles."""
    def __init__(self, *, raise_on_create=False):
        self._raise = raise_on_create
        self.sent_results = []
        self._created = "sesn_fake"

    async def create_session(self, **kw):
        if self._raise:
            raise RuntimeError("platform down")
        return self._created

    async def send_user_message(self, session_id, text):
        return None

    async def send_tool_result(self, session_id, tool_use_id, result):
        self.sent_results.append((tool_use_id, result))

    async def stream(self, session_id):
        yield _FakeEvent("agent.message", content=[type("B", (), {"type": "text", "text": "Hi there. "})()])
        yield _FakeEvent("agent.custom_tool_use", id="sevt_1", name="get_profile_snapshot", input={})
        # after we answer the tool, she finishes:
        yield _FakeEvent("agent.message", content=[type("B", (), {"type": "text", "text": "Where are you headed?"})()])
        yield _FakeEvent("session.status_idle", stop_reason=type("S", (), {"type": "end_turn"})())


@pytest.mark.asyncio
async def test_stream_turn_relays_and_answers_tool(db_session, mock_student_user):
    from unipaith.services.uni_agent_host import UniAgentHost
    host = UniAgentHost(db_session, client=_FakeAgentClient())
    events = [
        (name, payload)
        async for name, payload in host.stream_turn(mock_student_user.id, content="hello")
    ]
    names = [n for n, _ in events]
    assert "delta" in names                  # streamed text
    assert "assistant_message" in names       # final persisted reply
    deltas = "".join(p["text"] for n, p in events if n == "delta")
    assert "Hi there" in deltas and "Where are you headed" in deltas


@pytest.mark.asyncio
async def test_stream_turn_graceful_on_platform_down(db_session, mock_student_user):
    from unipaith.services.uni_agent_host import UniAgentHost
    host = UniAgentHost(db_session, client=_FakeAgentClient(raise_on_create=True))
    events = [
        (name, payload)
        async for name, payload in host.stream_turn(mock_student_user.id, content="hello")
    ]
    names = [n for n, _ in events]
    # never raises; emits a friendly message, not an error stack
    assert "assistant_message" in names
    text = next(p["content"] for n, p in events if n == "assistant_message")
    assert "moment" in text.lower() or "breath" in text.lower()
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd unipaith-backend && PYTHONPATH=src AI_MOCK_MODE=true .venv/bin/pytest tests/test_uni_agent_host.py -k stream_turn -v --tb=short`
Expected: FAIL `ModuleNotFoundError: No module named 'unipaith.services.uni_agent_host'`.

- [ ] **Step 3: Implement the host**

```python
# services/uni_agent_host.py
"""Host that drives a student's Uni managed-agent session and relays it to the
existing discovery SSE contract (student_message / delta / tool_use /
assistant_message / error / done). Hard cutover: on platform failure it emits a
graceful message, never a 5xx."""
from __future__ import annotations

from typing import Any, AsyncIterator
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.config import settings
from unipaith.models.discovery import DiscoverySession
from unipaith.services.student_service import StudentService
from unipaith.services.uni_tools import dispatch_tool

_CALM = "Uni is catching her breath for a moment — please try again shortly."


class UniAgentHost:
    def __init__(self, db: AsyncSession, *, client: Any | None = None) -> None:
        self.db = db
        if client is None:
            from unipaith.ai.managed_agent_client import ManagedAgentClient

            client = ManagedAgentClient()
        self.client = client

    async def _get_or_create_session_row(self, user_id: UUID) -> DiscoverySession:
        sp = await StudentService(self.db)._get_student_profile(user_id)
        row = (
            await self.db.execute(
                select(DiscoverySession)
                .where(DiscoverySession.student_id == sp.id, DiscoverySession.track == "profile")
                .order_by(DiscoverySession.created_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        if row is None:
            row = DiscoverySession(student_id=sp.id, track="profile", layer="basic")
            self.db.add(row)
            await self.db.flush()
        return row

    async def stream_turn(self, user_id: UUID, *, content: str) -> AsyncIterator[tuple[str, dict]]:
        try:
            row = await self._get_or_create_session_row(user_id)
            if not row.agent_session_id:
                row.agent_session_id = await self.client.create_session(
                    agent_id=settings.uni_agent_id,
                    environment_id=settings.uni_environment_id,
                    title="Uni discovery",
                )
                await self.db.flush()
            sid = row.agent_session_id

            reply_parts: list[str] = []
            # stream-first, then send
            stream = self.client.stream(sid)
            await self.client.send_user_message(sid, content)
            async for event in stream:
                etype = getattr(event, "type", "")
                if etype == "agent.message":
                    for block in getattr(event, "content", []) or []:
                        if getattr(block, "type", "") == "text":
                            reply_parts.append(block.text)
                            yield ("delta", {"text": block.text})
                elif etype == "agent.custom_tool_use":
                    result = await dispatch_tool(
                        self.db, user_id, event.name, event.input or {}, session_id=row.id
                    )
                    await self.client.send_tool_result(sid, event.id, result)
                    if event.name in ("save_signals", "get_matches"):
                        yield ("tool_use", {"tool": event.name, "result": result})
                elif etype == "session.status_idle":
                    sr = getattr(getattr(event, "stop_reason", None), "type", None)
                    if sr != "requires_action":
                        break
                elif etype == "session.status_terminated":
                    break

            text = "".join(reply_parts).strip() or "…"
            await self._mirror(row, content, text)
            yield ("assistant_message", {"content": text})
        except Exception as exc:  # hard cutover: never 5xx the student mid-conversation
            yield ("error", {"message": str(exc)[:200]})
            yield ("assistant_message", {"content": _CALM})

    async def _mirror(self, row: DiscoverySession, student_text: str, assistant_text: str) -> None:
        """Append the turn to discovery_messages for transcript/audit/eval.

        Uses the existing DiscoveryMessage model (role student/assistant). Best
        effort — a mirror failure must not break the conversation."""
        try:
            from unipaith.models.discovery import DiscoveryMessage

            self.db.add(DiscoveryMessage(session_id=row.id, role="student", content=student_text))
            self.db.add(DiscoveryMessage(session_id=row.id, role="assistant", content=assistant_text))
            await self.db.commit()
        except Exception:
            await self.db.rollback()
```

Verify `DiscoveryMessage`'s required columns (it may need `extracted_signals=None` explicitly or have other NOT NULL fields) against `models/discovery.py`, and confirm `StudentService._get_student_profile` is the right user→profile resolver.

- [ ] **Step 4: Run to verify it passes**

Run: `cd unipaith-backend && PYTHONPATH=src AI_MOCK_MODE=true .venv/bin/pytest tests/test_uni_agent_host.py -v --tb=short`
Expected: PASS (relay + graceful envelope).

- [ ] **Step 5: Commit**

```bash
git add unipaith-backend/src/unipaith/services/uni_agent_host.py tests/test_uni_agent_host.py
git commit -m "feat(uni): UniAgentHost stream-first turn loop + tool dispatch + graceful envelope"
```

### Task 2.3: Route `/messages/stream` through the host when the flag is on

**Files:**
- Modify: `unipaith-backend/src/unipaith/api/discovery.py:129-172`
- Test: `unipaith-backend/tests/test_uni_endpoint.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_uni_endpoint.py
import pytest
from unipaith.config import settings


@pytest.mark.asyncio
async def test_stream_endpoint_uses_host_when_flag_on(
    student_client, db_session, mock_student_user, monkeypatch
):
    monkeypatch.setattr(settings, "ai_uni_managed_agent_v1", True)

    # Fake the host so no live platform is needed.
    from tests.test_uni_agent_host import _FakeAgentClient
    import unipaith.api.discovery as disc_api

    class _Host:
        def __init__(self, db, client=None):
            self._inner = disc_api.UniAgentHost(db, client=_FakeAgentClient())
        def stream_turn(self, user_id, *, content):
            return self._inner.stream_turn(user_id, content=content)

    monkeypatch.setattr(disc_api, "UniAgentHost", _Host)

    # create a session first via the existing endpoint
    s = await student_client.post(
        "/api/students/me/discovery/sessions", json={"track": "profile", "layer": "basic"}
    )
    sid = s.json()["id"]
    resp = await student_client.post(
        f"/api/students/me/discovery/sessions/{sid}/messages/stream",
        json={"role": "student", "content": "hello"},
    )
    assert resp.status_code == 200
    assert "assistant_message" in resp.text
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd unipaith-backend && PYTHONPATH=src AI_MOCK_MODE=true .venv/bin/pytest tests/test_uni_endpoint.py -v --tb=short`
Expected: FAIL (endpoint still calls `_svc(db).stream_message`, the flag does nothing).

- [ ] **Step 3: Branch the endpoint on the flag**

In `api/discovery.py`, add the import and branch inside `append_message_stream`'s `_event_stream`:
```python
from unipaith.config import settings
from unipaith.services.uni_agent_host import UniAgentHost
```
```python
    async def _event_stream():
        if settings.ai_uni_managed_agent_v1:
            host = UniAgentHost(db)
            yield f"event: student_message\ndata: {json.dumps({'content': body.content})}\n\n"
            async for event_name, payload in host.stream_turn(user.id, content=body.content):
                yield f"event: {event_name}\ndata: {json.dumps(payload, default=str)}\n\n"
            yield "event: done\ndata: {}\n\n"
            return
        async for event_name, payload in _svc(db).stream_message(
            user.id, session_id, role=body.role, content=body.content,
            extracted_signals=body.extracted_signals,
        ):
            yield f"event: {event_name}\ndata: {json.dumps(payload, default=str)}\n\n"
        yield "event: done\ndata: {}\n\n"
```

- [ ] **Step 4: Run to verify it passes**

Run: `cd unipaith-backend && PYTHONPATH=src AI_MOCK_MODE=true .venv/bin/pytest tests/test_uni_endpoint.py -v --tb=short`
Expected: PASS.

- [ ] **Step 5: Run the full discovery + tool + host suite for regressions**

Run: `cd unipaith-backend && PYTHONPATH=src AI_MOCK_MODE=true .venv/bin/pytest tests/test_uni_tools.py tests/test_uni_agent_host.py tests/test_uni_endpoint.py tests/test_uni_snapshot.py tests/test_uni_migration.py tests/test_uni_config.py -v --tb=short ; echo EXIT=$?`
Expected: all PASS, `EXIT=0`.

- [ ] **Step 6: Commit**

```bash
git add unipaith-backend/src/unipaith/api/discovery.py tests/test_uni_endpoint.py
git commit -m "feat(uni): route discovery /messages/stream through UniAgentHost behind flag"
```

---

## Phase 3 — Follow-on plan (frontend, eval, registration, retire)

These become their own plan (`docs/superpowers/plans/2026-06-1x-uni-cutover.md`). Enumerated tasks:

1. **Frontend re-point** — point `UniConversation`'s turn at `/messages/stream` (the event contract is unchanged: `student_message`/`delta`/`tool_use`/`assistant_message`/`error`/`done`). Map `tool_use` payloads with `tool==="get_matches"` → inline `FirstLookCard`, `tool==="save_signals"` → `JourneyRail` completion + `LivingProfile` "Noticed" cards. Reuse `useRealtime`/`RealtimeClient` (`frontend/src/hooks/useRealtime.ts`, `frontend/src/lib/realtime.ts`). Vitest smoke for the event mapping.
2. **Confirmation policy** — resolve the deferred `user_confirmed` question: decide whether the host marks discovery `save_signals` as user-confirmed (recommended, since each signal carries the student's verbatim `evidence`) and reconcile with `evaluate_goals_track` / `evaluate_identity_layer`'s "user-confirmed" requirement so handoff can actually unlock.
3. **Eval cases** — add Uni scenarios to the §62 case store; wire the `constitution_student.md` judge; ensure the §61 deterministic floors (crisis, no-fabrication, grounding) run in CI against the host with a faked client.
4. **Catalog registration** — add `"uni_counselor": "flagship"` to `AGENT_TIERS` (agent_registry.py), `"uni_counselor": None` to `AGENT_REQUIRES` (consent.py, like `orchestrator`), and a `uni_counselor` `AgentEntry` to `CATALOG` (catalog.py) so the agent appears on `/goal/claude-api`; `test_spec45_agent_catalog.py` will require all three.
5. **Retire `orchestrator.py` conversation logic** — once the flag is default-on and soaked, delete the orchestrator turn path; keep the extractor/validators/`persist_extraction`/handoff (the host reuses them). Update `tests/test_plan2_integration.py` only if a discovery-fallback test exists (the current essay/workshop tests are unaffected — they keep their own rule-based fallback). Add a host "never 5xx" invariant test (already in Task 2.2) as the discovery analogue.
6. **Create the agent on the platform** — `ant beta:agents create < agents/uni.agent.yaml` (or the Console per `agents/CONFIGURE.md`); set `UNI_AGENT_ID` / `UNI_ENVIRONMENT_ID` / `AI_UNI_MANAGED_AGENT_V1=true` in ECS env; deploy.

---

## Self-Review

**Spec coverage:** persona/system prompt → `agents/uni_system.md` (shipped); the 5 tools → Tasks 1.2–1.5; environment/model → `agents/uni.agent.yaml` + CONFIGURE.md (shipped); session mapping → Task 1.6 + 2.2; turn loop → 2.2; endpoint/frontend → 2.3 + Phase 3.1; graceful envelope → 2.2; "training"/eval + catalog + retire → Phase 3.3–3.5. Covered.

**Placeholder scan:** the only deliberate substitution is the migration `down_revision = "<HEAD>"` (Step 3b gives the exact command to resolve it — migrations are inherently repo-state-dependent). The `_student_id_for_user` / `_get_student_profile` resolver and `Program.tuition` cents-vs-USD are flagged with the exact verification step rather than guessed.

**Type consistency:** tool fns share the `async (db, user_id, tool_input) -> dict` shape; `dispatch_tool` and the host use them consistently; `stream_turn` yields the same `(event_name, payload)` contract the SSE endpoint already serializes; `save_signals` input == `EXTRACT_SIGNALS_TOOL` == `agents/uni.agent.yaml` (single source of truth).
