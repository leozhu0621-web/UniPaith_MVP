import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pythonjsonlogger.json import JsonFormatter

from unipaith.api.router import api_router
from unipaith.config import settings
from unipaith.core.middleware import setup_middleware
from unipaith.core.scheduler import setup_scheduler, shutdown_scheduler


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


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    setup_scheduler()
    yield
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
