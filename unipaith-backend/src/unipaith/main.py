import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.api.router import api_router
from unipaith.config import settings
from unipaith.core.data_safety import assert_core_role_coverage
from unipaith.core.middleware import setup_middleware
from unipaith.core.observability import ContextJsonFormatter
from unipaith.core.scheduler import setup_scheduler, shutdown_scheduler
from unipaith.database import async_session


def _setup_logging() -> None:
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    # Spec 55 §2 — ContextJsonFormatter injects the active request id into every
    # JSON record, so an error log and its access line share one greppable id.
    handler.setFormatter(
        ContextJsonFormatter(
            fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
            rename_fields={"asctime": "timestamp", "levelname": "level"},
        )
    )
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(log_level)
    # Quiet down noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


_setup_logging()


async def _ensure_schools_table(db: AsyncSession) -> None:
    """Bootstrap the schools table + school_id FK if they don't exist yet."""
    from sqlalchemy import text

    row = await db.execute(
        text("SELECT 1 FROM information_schema.tables WHERE table_name = 'schools'")
    )
    if row.scalar():
        return  # Already exists

    log = logging.getLogger("unipaith.startup")
    log.info("Creating schools table and populating from department strings...")

    await db.execute(
        text("""
        CREATE TABLE schools (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            institution_id UUID NOT NULL REFERENCES institutions(id) ON DELETE CASCADE,
            name VARCHAR(255) NOT NULL,
            description_text TEXT,
            media_urls JSONB,
            logo_url VARCHAR(1000),
            sort_order INTEGER,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE(institution_id, name)
        )
    """)
    )
    await db.execute(text("CREATE INDEX ix_schools_institution ON schools(institution_id)"))

    # Add school_id column to programs if not exists
    col_check = await db.execute(
        text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name='programs' AND column_name='school_id'"
        )
    )
    if not col_check.scalar():
        await db.execute(
            text(
                "ALTER TABLE programs ADD COLUMN school_id UUID "
                "REFERENCES schools(id) ON DELETE SET NULL"
            )
        )
        await db.execute(text("CREATE INDEX ix_programs_school_id ON programs(school_id)"))

    # Populate schools from existing department strings
    await db.execute(
        text("""
        INSERT INTO schools (institution_id, name, sort_order)
        SELECT DISTINCT institution_id, department,
            ROW_NUMBER() OVER (
                PARTITION BY institution_id ORDER BY department
            )
        FROM programs
        WHERE department IS NOT NULL AND department != ''
        ON CONFLICT DO NOTHING
    """)
    )

    # Link programs to their schools
    await db.execute(
        text("""
        UPDATE programs p SET school_id = s.id
        FROM schools s
        WHERE p.institution_id = s.institution_id AND p.department = s.name AND p.school_id IS NULL
    """)
    )

    await db.commit()
    log.info("Schools table created and populated successfully.")


async def _ensure_follow_schema(db) -> None:
    """Idempotently ensure the Spec-12 School Detail schema exists.

    The Alembic chain has a documented history of divergence (see
    ``_ensure_schools_table``) and the docker entrypoint may stamp heads without
    running a migration after a failed ``upgrade``. To guarantee the "Save
    school" / Follow feature and the institution header render in production
    regardless of Alembic state, we create ``institution_follows`` and the
    ``institutions.founded_year`` column here too. No-op once present.
    """
    from sqlalchemy import text

    log = logging.getLogger("unipaith.startup")

    col = await db.execute(
        text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name='institutions' AND column_name='founded_year'"
        )
    )
    if not col.scalar():
        log.info("Adding institutions.founded_year (Alembic chain bypass)...")
        await db.execute(text("ALTER TABLE institutions ADD COLUMN founded_year INTEGER"))

    tbl = await db.execute(
        text("SELECT 1 FROM information_schema.tables WHERE table_name='institution_follows'")
    )
    if not tbl.scalar():
        log.info("Creating institution_follows table (Alembic chain bypass)...")
        await db.execute(
            text("""
            CREATE TABLE IF NOT EXISTS institution_follows (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                student_id UUID NOT NULL REFERENCES student_profiles(id) ON DELETE CASCADE,
                institution_id UUID NOT NULL REFERENCES institutions(id) ON DELETE CASCADE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                CONSTRAINT uq_institution_follow UNIQUE (student_id, institution_id)
            )
            """)
        )
        await db.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_institution_follows_student "
                "ON institution_follows(student_id)"
            )
        )
        await db.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_institution_follows_institution "
                "ON institution_follows(institution_id)"
            )
        )
    await db.commit()


async def _ensure_saved_list_schema(db) -> None:
    """Spec 13 — priority/tags/status on saved_list_items (Alembic bypass)."""
    from sqlalchemy import text

    log = logging.getLogger("unipaith.startup")
    tbl = await db.execute(
        text("SELECT 1 FROM information_schema.tables WHERE table_name='saved_list_items'")
    )
    if not tbl.scalar():
        return
    for column, ddl in (
        ("priority", "VARCHAR(30) NOT NULL DEFAULT 'considering'"),
        ("status", "VARCHAR(30) NOT NULL DEFAULT 'considering'"),
        ("tags", "JSONB NOT NULL DEFAULT '[]'::jsonb"),
    ):
        exists = await db.execute(
            text(
                "SELECT 1 FROM information_schema.columns "
                "WHERE table_name='saved_list_items' AND column_name=:col"
            ),
            {"col": column},
        )
        if not exists.scalar():
            log.info("Adding saved_list_items.%s (Spec 13 bypass)...", column)
            await db.execute(text(f"ALTER TABLE saved_list_items ADD COLUMN {column} {ddl}"))
    await db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    # Ensure schools table exists (bypasses broken Alembic chain)
    try:
        async with async_session() as db:
            await _ensure_schools_table(db)
    except Exception:
        logging.getLogger("unipaith.startup").exception("Schools table bootstrap failed")

    # Ensure Spec-12 School Detail schema exists (follows + founded_year)
    try:
        async with async_session() as db:
            await _ensure_follow_schema(db)
    except Exception:
        logging.getLogger("unipaith.startup").exception("Follow schema bootstrap failed")

    # Spec 13 — saved list priority/tags/status columns
    try:
        async with async_session() as db:
            await _ensure_saved_list_schema(db)
    except Exception:
        logging.getLogger("unipaith.startup").exception("Saved list schema bootstrap failed")

    # Spec 06 §5.4 — cache-invalidation trigger for prompt/model rolls. After a
    # deploy that bumped RATIONALE_PROMPT_VERSION (also the documented hook for
    # a workhorse-model roll), purge cached rationales generated under an older
    # prompt version. Idempotent: a no-op DELETE on every subsequent boot.
    try:
        from unipaith.ai.cache_invalidation import invalidate_for_prompt_change

        async with async_session() as db:
            removed = await invalidate_for_prompt_change(db)
            await db.commit()
            if removed:
                logging.getLogger("unipaith.startup").info(
                    "Purged %d stale-prompt match_rationale rows on startup", removed
                )
    except Exception:
        logging.getLogger("unipaith.startup").exception("Prompt-cache invalidation failed")

    if settings.environment.lower() in {"production", "staging"}:
        try:
            async with async_session() as db:
                await assert_core_role_coverage(db)
        except Exception:
            logging.getLogger("unipaith.startup").exception(
                "Core account coverage check failed on startup"
            )

    setup_scheduler()
    yield
    shutdown_scheduler()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
)

setup_middleware(app)

app.include_router(api_router, prefix="/api/v1")
