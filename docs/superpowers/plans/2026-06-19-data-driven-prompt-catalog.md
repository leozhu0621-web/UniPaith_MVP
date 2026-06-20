# Data-Driven Prompt Catalog (foundation) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:test-driven-development. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Move the prompt catalog out of the hard-coded `enrichment_planner.CATALOG` Python list into a `prompt_catalog` DB table read through a loader, **behavior-identical** on day one, so the catalog can later be driven by Airtable.

**Architecture:** New `PromptCatalog` model + migration. `CatalogService.load(db)` returns the catalog in the exact shape the planner consumes; `ensure_seeded(db)` idempotently inserts the in-code `CATALOG` snapshot (INSERT … ON CONFLICT(key) DO NOTHING, so future Airtable edits aren't clobbered). The pure planner functions gain an optional `catalog=` param (default = the module constant) so existing pure tests are unchanged; `enrichment_service` loads from the DB and passes it in. Parity test proves DB-seeded == constant.

**Tech Stack:** Python 3.12 · SQLAlchemy 2 async · Alembic (hand-written) · pytest-asyncio.

**Scope (this plan = Plan 1a, foundation only):** table + loader + seed + planner refactor + parity. NOT in scope: the comprehensive catalog expansion (new fields/sources), new scored-weight columns, Airtable sync, widgets, templates — those are later plans.

---

### Task 1: `PromptCatalog` model + migration

**Files:**
- Create: `unipaith-backend/src/unipaith/models/prompt_catalog.py`
- Modify: `unipaith-backend/src/unipaith/models/__init__.py` (export)
- Create: `unipaith-backend/alembic/versions/promptcat1_prompt_catalog.py`
- Test: `unipaith-backend/tests/test_prompt_catalog_model.py`

- [ ] **Step 1 — failing test** (`test_prompt_catalog_model.py`): insert a `PromptCatalog` row and read it back; assert columns round-trip and `active` defaults True, `display_logic` defaults `[]`.
- [ ] **Step 2 — run, expect fail** (`ModuleNotFoundError`/no table).
- [ ] **Step 3 — model** mirroring `chat_session.py` conventions:

```python
class PromptCatalog(Base):
    __tablename__ = "prompt_catalog"
    __table_args__ = (
        UniqueConstraint("key", name="uq_prompt_catalog_key"),
        Index("ix_prompt_catalog_active_sort", "active", "sort_order"),
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(String(60), nullable=False)
    section: Mapped[str] = mapped_column(String(40), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    ask_kind: Mapped[str] = mapped_column(String(20), nullable=False)
    value_type: Mapped[str] = mapped_column(String(20), nullable=False)
    options: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    tier: Mapped[str] = mapped_column(String(20), nullable=False)
    required: Mapped[bool] = mapped_column(Boolean, server_default=text("false"), nullable=False)
    display_logic: Mapped[list] = mapped_column(JSONB, server_default=text("'[]'::jsonb"), nullable=False)
    saves_to: Mapped[str] = mapped_column(String(60), nullable=False)
    reference_source: Mapped[str | None] = mapped_column(String(40), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, server_default=text("0"), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"), nullable=False)
    airtable_record_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at / updated_at: DateTime(timezone=True), server_default=func.now()
```

- [ ] **Step 4** — export in `models/__init__.py`.
- [ ] **Step 5** — migration `promptcat1` (down_revision `chatsessbf1`), `_has("prompt_catalog")`-guarded `create_table` mirroring the columns, `# pragma: allowlist secret` on revision lines if flagged.
- [ ] **Step 6** — run the test (conftest `create_all` builds the table); expect PASS.
- [ ] **Step 7** — `alembic heads` shows single head `promptcat1`. Commit.

---

### Task 2: `CatalogService` — load + ensure_seeded

**Files:**
- Create: `unipaith-backend/src/unipaith/services/catalog_service.py`
- Test: `unipaith-backend/tests/test_catalog_service.py`

- [ ] **Step 1 — failing test:** `ensure_seeded(db)` then `load(db)` returns a list whose `{key}` set equals `{f["key"] for f in CATALOG}`, and each entry has keys `key,type,tier,ask_kind,question,options` with values equal to the matching `CATALOG` entry. Second `ensure_seeded` is a no-op (still N rows).
- [ ] **Step 2 — run, expect fail.**
- [ ] **Step 3 — implement:**

```python
_SECTION_BY_KEY = { ...key -> "Basics"/"Academics"/... per spec §3.1 for the existing 23 keys... }
_REFSRC = {"nationality": "countries", "country_of_residence": "countries"}

class CatalogService:
    def __init__(self, db): self.db = db
    async def ensure_seeded(self):
        for i, f in enumerate(CATALOG):
            await self.db.execute(pg_insert(PromptCatalog).values(
                key=f["key"], section=_SECTION_BY_KEY[f["key"]], question=f["question"],
                ask_kind=f["ask_kind"], value_type=f["type"], options=f.get("options"),
                tier=f["tier"], saves_to=f["key"], reference_source=_REFSRC.get(f["key"]),
                sort_order=i,
            ).on_conflict_do_nothing(index_elements=["key"]))
        await self.db.flush()
    async def load(self):
        rows = (await self.db.execute(
            select(PromptCatalog).where(PromptCatalog.active).order_by(PromptCatalog.sort_order)
        )).scalars().all()
        return [{"key": r.key, "type": r.value_type, "tier": r.tier, "ask_kind": r.ask_kind,
                 "question": r.question, "options": r.options} for r in rows]
```

- [ ] **Step 4 — run, expect PASS. Commit.**

---

### Task 3: planner takes an optional `catalog`

**Files:**
- Modify: `unipaith-backend/src/unipaith/services/enrichment_planner.py`
- Test: `unipaith-backend/tests/test_enrichment_planner.py` (add a case; existing cases must stay green)

- [ ] **Step 1 — failing test:** `plan_next(state, catalog=CATALOG)` equals `plan_next(state)`; `essentials_present(state, catalog=CATALOG)` equals `essentials_present(state)`. (Drives the new param.)
- [ ] **Step 2 — run, expect fail** (unexpected kwarg).
- [ ] **Step 3 — implement:** add `catalog: list[dict] | None = None` to `plan_next` and `essentials_present`; inside, `cat = catalog if catalog is not None else CATALOG`; derive `essential_keys`, `catalog_order` from `cat` (helper `_derive(cat)`); keep `SECTION_FIELDS`, `_TIER_RANK`, `_ACTION_RANK` as-is. `action_for` unchanged.
- [ ] **Step 4 — run full `test_enrichment_planner.py`, expect all PASS. Commit.**

---

### Task 4: `enrichment_service` reads from the DB catalog

**Files:**
- Modify: `unipaith-backend/src/unipaith/services/enrichment_service.py`
- Test: `unipaith-backend/tests/test_enrichment_write_typing.py` (existing; must stay green) + a parity test in `test_catalog_service.py`

- [ ] **Step 1 — failing parity test:** with a seeded DB, `EnrichmentService(db).next_signals(student)` returns the same `items`/`essentials_present` as the constant-driven planner for a fixed signal state. And `set_value` still types weight/taxonomy correctly (existing typing tests).
- [ ] **Step 2 — run, expect fail** (service still uses module constant only — actually passes today; the test pins behavior before refactor, so write it to assert against `plan_next(state)` constant path → should pass, then refactor must keep it green).
- [ ] **Step 3 — implement:** in `next_signals`, `cat = await CatalogService(self.db).load()` and pass `catalog=cat` to `plan_next`/`essentials_present`; in `set_value`, build `by_key = {e["key"]: e for e in cat}` from the loaded catalog instead of the module-level `_CATALOG_BY_KEY`. Keep `_coerce_weight_0_5`/`_validate_taxonomy` unchanged.
- [ ] **Step 4 — run both test files, expect PASS. Commit.**

---

### Task 5: seed at startup + seed script

**Files:**
- Modify: `unipaith-backend/src/unipaith/main.py` (lifespan: call `ensure_seeded` best-effort) OR the existing seed entrypoint
- Test: covered by Task 2/4 (idempotency)

- [ ] **Step 1** — call `CatalogService(db).ensure_seeded()` in the startup seed path (same place other reference seeds run), guarded so a fresh prod DB self-seeds; idempotent.
- [ ] **Step 2** — `make test-backend` targeted: run `test_prompt_catalog_model.py test_catalog_service.py test_enrichment_planner.py test_enrichment_write_typing.py test_ai_structure_simulation.py`; all green.
- [ ] **Step 3** — ruff + tsc not needed (backend only). Commit, open PR, merge, deploy, verify live (`/me/enrichment/next` still 200/422 as before).

---

## Self-review
- **Spec coverage:** §5 (loader + planner-takes-catalog), §6 (`prompt_catalog` table + seed-from-CATALOG behavior-identical). The comprehensive assembly (§3) and Airtable (§7) are explicitly later plans.
- **Type consistency:** loader returns `type` (not `value_type`) to match the planner's expected dict shape; `set_value` reads `entry["type"]`/`entry.get("options")` — preserved.
- **Behavior-identical:** seed maps every existing CATALOG field 1:1; parity test enforces identical planner output.
