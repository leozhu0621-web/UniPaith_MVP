import logging
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pythonjsonlogger.json import JsonFormatter
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.api.router import api_router
from unipaith.config import settings
from unipaith.core.data_safety import assert_core_role_coverage
from unipaith.core.middleware import setup_middleware
from unipaith.core.scheduler import setup_scheduler, shutdown_scheduler
from unipaith.database import async_session


def _setup_logging() -> None:
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        JsonFormatter(
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

    row = await db.execute(text(
        "SELECT 1 FROM information_schema.tables WHERE table_name = 'schools'"
    ))
    if row.scalar():
        return  # Already exists

    log = logging.getLogger("unipaith.startup")
    log.info("Creating schools table and populating from department strings...")

    await db.execute(text("""
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
    """))
    await db.execute(text("CREATE INDEX ix_schools_institution ON schools(institution_id)"))

    # Add school_id column to programs if not exists
    col_check = await db.execute(text(
        "SELECT 1 FROM information_schema.columns "
        "WHERE table_name='programs' AND column_name='school_id'"
    ))
    if not col_check.scalar():
        await db.execute(text(
            "ALTER TABLE programs ADD COLUMN school_id UUID "
            "REFERENCES schools(id) ON DELETE SET NULL"
        ))
        await db.execute(text(
            "CREATE INDEX ix_programs_school_id ON programs(school_id)"
        ))

    # Populate schools from existing department strings
    await db.execute(text("""
        INSERT INTO schools (institution_id, name, sort_order)
        SELECT DISTINCT
            institution_id,
            department,
            ROW_NUMBER() OVER (
                PARTITION BY institution_id ORDER BY department
            )
        FROM programs
        WHERE department IS NOT NULL AND department != ''
        ON CONFLICT DO NOTHING
    """))

    # Link programs to their schools
    await db.execute(text("""
        UPDATE programs p SET school_id = s.id
        FROM schools s
        WHERE p.institution_id = s.institution_id AND p.department = s.name AND p.school_id IS NULL
    """))

    await db.commit()
    log.info("Schools table created and populated successfully.")


async def lifespan(app: FastAPI):  # noqa: ARG001
    from unipaith.services.pipeline import get_pipeline

    # Ensure schools table exists (bypasses broken Alembic chain)
    try:
        async with async_session() as db:
            await _ensure_schools_table(db)
    except Exception:
        logging.getLogger("unipaith.startup").exception(
            "Schools table bootstrap failed"
        )

    if settings.environment.lower() in {"production", "staging"}:
        try:
            async with async_session() as db:
                await assert_core_role_coverage(db)
        except Exception:
            logging.getLogger("unipaith.startup").exception(
                "Core account coverage check failed on startup"
            )

    pipeline = get_pipeline()
    if settings.pipeline_enabled:
        await pipeline.start()

    setup_scheduler()
    yield
    if settings.pipeline_enabled:
        await pipeline.stop()
    shutdown_scheduler()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

setup_middleware(app)

app.include_router(api_router, prefix="/api/v1")

# Admin dashboard
STATIC_DIR = Path(__file__).parent / "static"


@app.get("/admin")
async def admin_dashboard():
    return FileResponse(STATIC_DIR / "admin.html")
