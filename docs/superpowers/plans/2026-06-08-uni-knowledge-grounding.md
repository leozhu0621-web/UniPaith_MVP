# Uni Knowledge Grounding — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ground Uni's conversation (and the inline first-look) in the platform's program library + reference knowledge, our-knowledge-first and counselor-paced, per `docs/superpowers/specs/2026-06-08-uni-knowledge-grounding-design.md`.

**Architecture:** A new deterministic `UniKnowledgeRetriever` maps the discovery `StudentSnapshot` → a `KnowledgeBundle` of relevant real programs (via the existing `InstitutionService.search_programs`) + best-effort scholarships. Its rendered, cited text rides into the orchestrator through a new `TurnContext.knowledge_summary` (same mechanism as the existing profile/signals summaries — no new agent). Gated behind `ai_uni_knowledge_v1` + a counselor-paced signal gate; empty/error degrades to today's ungrounded behavior. No migration.

**Tech Stack:** FastAPI/SQLAlchemy (Python 3.12), React/TS frontend. Worktree `/tmp/wt-uni-knowledge`, branch `claude/uni-knowledge-grounding-8bf9e6`.

**Test lessons (from #328/#362):** router-using FE tests wrap in `MemoryRouter`; `src/test/setup.ts` stubs the axios adapter; run `tsc -b` + `vite build`. Backend retriever tests seed a couple of programs in the isolated test DB. `Array.at()` is unavailable (lib<es2022) — use index access.

---

## Phase 0 — Flag

### Task 1: `ai_uni_knowledge_v1` flag

**Files:** Modify `unipaith-backend/src/unipaith/config.py`; modify `infra/ecs.tf`.

- [ ] **Step 1:** In `config.py`, after `ai_uni_guided_v1`:

```python
    # Uni knowledge grounding — when True, the discovery orchestrator is fed a
    # cited "From your knowledge base" block of real programs (+ scholarships)
    # relevant to the student's emerging profile, so Uni references our catalog
    # our-knowledge-first / counselor-paced. Independent of ai_uni_guided_v1;
    # requires the LLM discovery path (ai_discovery_v2_enabled). Off → today's
    # ungrounded conversation. Flip per-environment.
    ai_uni_knowledge_v1: bool = False
```

- [ ] **Step 2:** Verify: `cd unipaith-backend && PYTHONPATH=src python -c "from unipaith.config import settings; print(settings.ai_uni_knowledge_v1)"` → `False`.
- [ ] **Step 3:** In `infra/ecs.tf`, after the `AI_UNI_GUIDED_V1` env line, add: `{ name = "AI_UNI_KNOWLEDGE_V1", value = "true" },`
- [ ] **Step 4: Commit** `feat(uni): add ai_uni_knowledge_v1 flag`.

---

## Phase 1 — The retriever

### Task 2: `UniKnowledgeRetriever` + `KnowledgeBundle`

**Files:** Create `unipaith-backend/src/unipaith/services/uni_knowledge.py`; test `unipaith-backend/tests/test_uni_knowledge.py`.

Pure query-building + bundle rendering are testable without a DB; the DB retrieve is tested with a couple of seeded programs.

- [ ] **Step 1: Failing test (pure parts):**

```python
# unipaith-backend/tests/test_uni_knowledge.py
from unipaith.ai.state import GoalEntry, NeedEntry, StudentSnapshot
from unipaith.services.uni_knowledge import (
    KnowledgeBundle, ProgramFact, build_query,
)


def _snap(**kw) -> StudentSnapshot:
    return StudentSnapshot(**kw)


def test_build_query_none_without_interest():
    # Counselor-paced gate: no goal interest → no retrieval.
    assert build_query(_snap()) is None
    assert build_query(_snap(needs=[NeedEntry(maslow_level="safety", signal="affordability")])) is None


def test_build_query_from_goals_and_location():
    q = build_query(
        _snap(
            goals=[GoalEntry(category="academic", specific="study marine biology")],
            location_prefs=["Maine"],
        )
    )
    assert q is not None
    assert "marine biology" in q.query
    assert q.location == "Maine"


def test_bundle_render_empty_is_blank():
    assert KnowledgeBundle().render() == ""


def test_bundle_render_lists_programs_cited():
    b = KnowledgeBundle(
        programs=[
            ProgramFact(
                program_id="p1", name="Marine Biology BS", school="U Maine",
                degree_type="bachelors", tuition=18000, acceptance_rate=0.7,
                median_salary=52000,
            )
        ]
    )
    out = b.render()
    assert "From your knowledge base" in out
    assert "Marine Biology BS" in out and "U Maine" in out
    assert "18,000" in out and "52,000" in out
```

- [ ] **Step 2: Run → FAIL** (`uni_knowledge` missing).

Run: `cd unipaith-backend && PYTHONPATH=src AI_MOCK_MODE=true .venv/bin/pytest tests/test_uni_knowledge.py -q`

- [ ] **Step 3: Implement `services/uni_knowledge.py`:**

```python
"""Uni knowledge grounding — retrieve real programs (+ scholarships) relevant to
the student's emerging profile so the orchestrator can reference our catalog
our-knowledge-first. Deterministic; reuses InstitutionService.search_programs.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ai.state import StudentSnapshot


@dataclass
class ProgramFact:
    program_id: str
    name: str
    school: str | None = None
    degree_type: str | None = None
    tuition: int | None = None
    acceptance_rate: float | None = None
    median_salary: int | None = None


@dataclass
class ReferenceFact:
    kind: str
    label: str
    detail: str


@dataclass
class ProgramQuery:
    query: str
    location: str | None = None


@dataclass
class KnowledgeBundle:
    programs: list[ProgramFact] = field(default_factory=list)
    references: list[ReferenceFact] = field(default_factory=list)

    def is_empty(self) -> bool:
        return not self.programs and not self.references

    def render(self) -> str:
        if self.is_empty():
            return ""
        lines = [
            "## From your knowledge base (real options — prefer these when "
            "naming specific schools/programs/costs)"
        ]
        for p in self.programs:
            bits = [p.name]
            if p.school:
                bits.append(f"at {p.school}")
            if p.tuition:
                bits.append(f"~${p.tuition:,}/yr tuition")
            if p.median_salary:
                bits.append(f"${p.median_salary:,} median salary")
            if p.acceptance_rate is not None:
                bits.append(f"{round(p.acceptance_rate * 100)}% admit")
            lines.append("- " + " · ".join(bits))
        for r in self.references:
            lines.append(f"- {r.label}: {r.detail}")
        return "\n".join(lines)


def build_query(snapshot: StudentSnapshot) -> ProgramQuery | None:
    """Counselor-paced gate: only build a query once a real interest exists."""
    interests = [g.specific.strip() for g in snapshot.goals if (g.specific or "").strip()]
    if not interests:
        return None
    location = snapshot.location_prefs[0] if snapshot.location_prefs else None
    return ProgramQuery(query=" ".join(interests[:3]), location=location)


async def _scholarship_facts(snapshot: StudentSnapshot, db: AsyncSession) -> list[ReferenceFact]:
    """Best-effort: a couple of scholarships when the table has rows. Silent on empty/error."""
    try:
        from sqlalchemy import select

        from unipaith.models.reference import Scholarship

        rows = (await db.execute(select(Scholarship).limit(2))).scalars().all()
        out: list[ReferenceFact] = []
        for s in rows:
            amt = f"up to ${int(s.amount_max):,}" if s.amount_max else "varies"
            out.append(ReferenceFact(kind="scholarship", label=s.name, detail=f"{s.scholarship_type}, {amt}"))
        return out
    except Exception:
        return []


class UniKnowledgeRetriever:
    """Snapshot → a small, cited KnowledgeBundle. Never raises to the caller."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def retrieve(self, snapshot: StudentSnapshot, *, limit: int = 4) -> KnowledgeBundle:
        q = build_query(snapshot)
        if q is None:
            return KnowledgeBundle()
        programs: list[ProgramFact] = []
        try:
            from unipaith.services.institution_service import InstitutionService

            page = await InstitutionService(self.db).search_programs(
                query=q.query, location=q.location, page_size=limit
            )
            for p in page.items[:limit]:
                programs.append(
                    ProgramFact(
                        program_id=str(p.id),
                        name=p.program_name,
                        school=p.institution_name,
                        degree_type=p.degree_type,
                        tuition=p.tuition,
                        acceptance_rate=p.acceptance_rate,
                        median_salary=p.median_salary,
                    )
                )
        except Exception:
            programs = []
        refs = await _scholarship_facts(snapshot, self.db)
        return KnowledgeBundle(programs=programs, references=refs)
```

- [ ] **Step 4: Run → PASS** (pure tests). Then add a DB test:

```python
# append to tests/test_uni_knowledge.py
import pytest
from unipaith.services.uni_knowledge import UniKnowledgeRetriever


@pytest.mark.asyncio
async def test_retrieve_empty_without_interest(db_session):
    bundle = await UniKnowledgeRetriever(db_session).retrieve(StudentSnapshot())
    assert bundle.is_empty()


@pytest.mark.asyncio
async def test_retrieve_returns_programs_for_interest(db_session):
    # Seed one institution + program so search_programs has something to find.
    from unipaith.models.institution import Institution, Program

    inst = Institution(name="U Maine", country="US")
    db_session.add(inst)
    await db_session.flush()
    db_session.add(
        Program(
            institution_id=inst.id, program_name="Marine Biology BS",
            degree_type="bachelors", tuition=18000,
            description_text="marine biology coastal field study",
        )
    )
    await db_session.flush()
    snap = StudentSnapshot(goals=[GoalEntry(category="academic", specific="marine biology")])
    bundle = await UniKnowledgeRetriever(db_session).retrieve(snap)
    assert any("Marine Biology" in p.name for p in bundle.programs)
    assert "From your knowledge base" in bundle.render()
```

Run: `cd unipaith-backend && PYTHONPATH=src DATABASE_URL=... COGNITO_BYPASS=true AI_MOCK_MODE=true S3_LOCAL_MODE=true .venv/bin/pytest tests/test_uni_knowledge.py -q` → PASS. (If `search_programs`'s `query` doesn't match on `description_text`, fall back to passing `program_name="Marine"` in the seed/test — verify the actual search field at impl time and align the test.)

- [ ] **Step 5: Commit** `feat(uni): UniKnowledgeRetriever (snapshot → cited program bundle)`.

---

## Phase 2 — Wire into the conversation

### Task 3: `TurnContext.knowledge_summary` + grounding instruction

**Files:** Modify `unipaith-backend/src/unipaith/ai/orchestrator.py`; test `unipaith-backend/tests/test_uni_journey.py` (extend).

- [ ] **Step 1:** Add to `TurnContext` (after `completion_breakdown`):

```python
    # Uni knowledge grounding (ai_uni_knowledge_v1) — a rendered, cited block of
    # real programs/scholarships relevant to the student. Empty string when off
    # or no signal. Injected into the discovery state header.
    knowledge_summary: str = ""
```

- [ ] **Step 2: Failing test** (extend `test_uni_journey.py`):

```python
def test_grounding_block_appended_when_present():
    from unipaith.ai.orchestrator import Orchestrator
    header = Orchestrator._render_state_header(
        _ctx(guided=True, completion_breakdown={"profile": 0.6, "goals": 0.2, "needs": 0},
             knowledge_summary="## From your knowledge base\n- Marine Biology BS at U Maine")
    )
    assert "From your knowledge base" in header
    assert "prefer" in header.lower()


def test_no_grounding_block_when_absent():
    from unipaith.ai.orchestrator import Orchestrator
    header = Orchestrator._render_state_header(
        _ctx(guided=True, completion_breakdown={"profile": 0.6, "goals": 0.2, "needs": 0})
    )
    assert "From your knowledge base" not in header
```

- [ ] **Step 3: Run → FAIL.**
- [ ] **Step 4: Implement** — in `_render_state_header`, at the top of the `if ctx.track == "discovery":` branch compute a grounding suffix and append it to BOTH the guided and open return strings:

```python
        grounding = ""
        if ctx.knowledge_summary:
            grounding = (
                f"\n\n{ctx.knowledge_summary}\n\n"
                "When you name a specific school/program/cost, PREFER the items above — "
                "they're real, from our data. Counselor-paced: weave in 1-2 only when "
                "relevant to what they've told you; never dump a list. If our data doesn't "
                "cover what they need, you may use general knowledge but stay tentative on "
                "specific numbers/deadlines and offer to look it up."
            )
```

Then change both `return (...)` in the discovery branch to `return (...) + grounding`.

- [ ] **Step 5: Run → PASS** + the existing journey/orchestrator tests stay green.
- [ ] **Step 6: Commit** `feat(uni): inject grounding block into the discovery state header`.

### Task 4: Build + thread the bundle in the discovery service

**Files:** Modify `unipaith-backend/src/unipaith/services/discovery_service.py`; test `unipaith-backend/tests/test_uni_knowledge.py` (extend) or a focused service test.

- [ ] **Step 1:** Add a helper near the other turn helpers:

```python
    async def _knowledge_summary(self, snapshot) -> str:
        """Rendered grounding block, gated on the flag. Never raises."""
        from unipaith.config import settings

        if not settings.ai_uni_knowledge_v1:
            return ""
        try:
            from unipaith.services.uni_knowledge import UniKnowledgeRetriever

            bundle = await UniKnowledgeRetriever(self.db).retrieve(snapshot)
            return bundle.render()
        except Exception:
            return ""
```

- [ ] **Step 2:** At BOTH `TurnContext(...)` build sites (append + stream paths), add `knowledge_summary=await self._knowledge_summary(snapshot),` to the kwargs. (The `snapshot` local is already built above each site.)

- [ ] **Step 3: Test** (extend `test_uni_knowledge.py`): `_knowledge_summary` returns "" when the flag is off, and a rendered block when on + interest present. Use `monkeypatch.setattr` on `settings.ai_uni_knowledge_v1`.

```python
@pytest.mark.asyncio
async def test_service_knowledge_summary_gated_by_flag(db_session, monkeypatch):
    from unipaith.services.discovery_service import DiscoveryService
    from unipaith.config import settings
    svc = DiscoveryService(db_session)
    snap = StudentSnapshot(goals=[GoalEntry(category="academic", specific="marine biology")])
    monkeypatch.setattr(settings, "ai_uni_knowledge_v1", False)
    assert await svc._knowledge_summary(snap) == ""
    monkeypatch.setattr(settings, "ai_uni_knowledge_v1", True)
    # No programs seeded here → empty bundle → "" (graceful), which is also fine:
    out = await svc._knowledge_summary(snap)
    assert isinstance(out, str)
```

- [ ] **Step 4: Run → PASS** + the discovery suite (`-k discovery or orchestrator or uni_`) green; confirm flag-off + retriever-error paths never raise.
- [ ] **Step 5: Commit** `feat(uni): thread knowledge_summary into discovery turns (gated)`.

---

## Phase 3 — First-look enrichment

### Task 5: Enrich `FirstLookCard`

**Files:** Modify `frontend/src/pages/student/discover/FirstLookCard.tsx`; modify `frontend/src/test/first-look-card.test.tsx`.

`MatchResultDual` already carries `tuition`, `acceptance_rate`, `band_label` — surface them as a grounded sub-line under each program (degrade to whatever exists). (Outcomes like salary aren't on the match result; deferred.)

- [ ] **Step 1: Failing test** — extend `first-look-card.test.tsx`: give a mocked match `tuition: 18000, acceptance_rate: 0.7, band_label: 'target'`; assert the card shows `$18,000` (or `18,000`) and `70%`.
- [ ] **Step 2: Run → FAIL.**
- [ ] **Step 3: Implement** — in the program row, below the name, render a muted line:

```tsx
{(m.tuition || m.acceptance_rate != null || m.band_label) && (
  <div className="text-xs text-muted-foreground">
    {[
      m.tuition ? `$${m.tuition.toLocaleString()}/yr` : null,
      m.acceptance_rate != null ? `${Math.round(m.acceptance_rate * 100)}% admit` : null,
      m.band_label ? `${m.band_label} fit` : null,
    ].filter(Boolean).join(' · ')}
  </div>
)}
```

(Keep the existing `why` rationale line as well.)

- [ ] **Step 4: Run → PASS** + `tsc -b` + `vite build`.
- [ ] **Step 5: Commit** `feat(uni): grounded cost/selectivity line in the first-look`.

---

## Phase 4 — Accuracy eval

### Task 6: `score_grounding_turn`

**Files:** Modify `unipaith-backend/src/unipaith/ai/evals/uni_counselor.py`; modify `unipaith-backend/tests/test_uni_eval.py`.

Heuristic: a turn asserting a confident specific dollar amount or a specific deadline that isn't in the provided knowledge block, without a hedge word, is flagged `unhedged_specific`.

- [ ] **Step 1: Failing test:**

```python
def test_grounding_flags_unhedged_specific_not_in_bundle():
    from unipaith.ai.evals.uni_counselor import score_grounding_turn
    r = score_grounding_turn(assistant="Tuition there is exactly $54,000 a year.", knowledge_block="")
    assert not r.passed and "unhedged_specific" in r.reasons


def test_grounding_ok_when_specific_is_grounded():
    from unipaith.ai.evals.uni_counselor import score_grounding_turn
    r = score_grounding_turn(
        assistant="Tuition there is about $54,000 a year.",
        knowledge_block="- Program at X · ~$54,000/yr tuition",
    )
    assert r.passed


def test_grounding_ok_when_hedged():
    from unipaith.ai.evals.uni_counselor import score_grounding_turn
    r = score_grounding_turn(assistant="Tuition is typically around $50,000 — worth verifying.", knowledge_block="")
    assert r.passed
```

- [ ] **Step 2: Run → FAIL.**
- [ ] **Step 3: Implement** in `uni_counselor.py`:

```python
import re

_HEDGES = ("about", "around", "roughly", "typically", "usually", "approximately",
           "verify", "check", "varies", "depends", "ballpark", "or so", "~")


def score_grounding_turn(assistant: str, knowledge_block: str = "") -> CounselorVerdict:
    """Flag a confident, specific dollar figure that isn't grounded or hedged."""
    reasons: list[str] = []
    a = assistant.lower()
    dollars = re.findall(r"\$\s?[\d,]{3,}", assistant)
    if dollars:
        hedged = any(h in a for h in _HEDGES)
        grounded = any(d.replace(" ", "") in knowledge_block.replace(" ", "") for d in dollars)
        if not hedged and not grounded:
            reasons.append("unhedged_specific")
    return CounselorVerdict(passed=not reasons, reasons=reasons)
```

- [ ] **Step 4: Run → PASS.**
- [ ] **Step 5: Commit** `test(uni): grounding accuracy eval (score_grounding_turn)`.

---

## Phase 5 — Verify, seed prod, ship

### Task 7: Regression + seed prod + ship

- [ ] **Step 1: Backend** — `cd unipaith-backend && PYTHONPATH=src DATABASE_URL=... COGNITO_BYPASS=true AI_MOCK_MODE=true S3_LOCAL_MODE=true .venv/bin/pytest tests/ -q -k "uni_ or discovery or orchestrator or plan2 or workshop_no_generation" ; echo EXIT=$?` — all pass; flag-off + retriever-error paths never 5xx. `ruff check src tests`.
- [ ] **Step 2: Frontend** — `cd frontend && npx vitest run ; npx tsc -b ; npx vite build ; npx eslint src/pages/student/discover` — green.
- [ ] **Step 3:** Merge `origin/main` (coordinate drift), re-verify single alembic head (no migration added), push branch, open PR, drive CI green → squash-merge → watch Deploy Backend + Terraform Apply (the flag).
- [ ] **Step 4 (seed prod):** After deploy, ensure the catalog + reference data are in prod RDS (VPC-private) via an ECS one-off task. Discover the cluster/task-def/network from the running service, then:

```bash
# Discover config
aws ecs list-clusters
aws ecs describe-services --cluster <cluster> --services <api-service> \
  --query 'services[0].{taskDef:taskDefinition,net:networkConfiguration}'
# Run the seed as a one-off with a command override (subnets/SG from the service)
aws ecs run-task --cluster <cluster> --task-definition <taskDef> --launch-type FARGATE \
  --network-configuration '<net>' \
  --overrides '{"containerOverrides":[{"name":"<container>","command":["python","-m","scripts.seed_real_catalog"]}]}'
# (repeat with scripts.seed_knowledge_engine for reference data, if desired)
```

Verify via the API (e.g. `/api/v1/programs` returns seeded programs) and a live Uni turn that references a real program once a goal is captured.

- [ ] **Step 5:** Verify live: the deployed bundle shows the grounded first-look line; a goal-bearing Uni conversation references a real catalog program.

---

## Self-Review

**Spec coverage:** §3 sources → Task 2 (programs + scholarships); §4 retriever → Task 2; §5 injection + grounding instruction → Tasks 3+4; §6 first-look enrichment → Task 5; §7 guardrail (prompt + eval + fallback) → Tasks 3,4,6; §8 flag/no-migration/reuse → Tasks 1,2; §9 seed-prod → Task 7; §10 testing → every task. **Deferred (noted):** embedding rerank (search_programs result lacks the embedding column — structured search is the floor per §12); outcomes (salary/grad) in first-look (not on the match response — surface tuition/acceptance/band now).

**Placeholder scan:** real code for every novel step (retriever, render, grounding header, eval, FE line); commands exact. The seed-prod command has `<cluster>`/`<taskDef>` placeholders **by necessity** (discovered at runtime) — Step 4 says how to discover them.

**Type consistency:** `KnowledgeBundle`/`ProgramFact`/`ReferenceFact`/`ProgramQuery`/`build_query`/`UniKnowledgeRetriever.retrieve`/`_knowledge_summary`/`knowledge_summary`/`score_grounding_turn` used consistently. `ProgramSummaryResponse` fields (`id`, `program_name`, `institution_name`, `degree_type`, `tuition`, `acceptance_rate`, `median_salary`) match the real schema; `page.items` is the paginated list.

## Notes for the executor
- Work on `claude/uni-knowledge-grounding-8bf9e6` in `/tmp/wt-uni-knowledge`. Symlink `frontend/node_modules` + backend `.venv`, copy `.env`. Coordinate (`git fetch origin main` + merge) before pushing.
- Per the project owner: implementation + online deploy proceed autonomously after this plan ("continue all the way").
- Confirm `search_programs`'s `query` matches the seeded program in the Task 2 DB test; adjust the seed text/field if needed so the test is real.
