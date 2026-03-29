import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from unipaith.api.router import api_router
from unipaith.config import settings
from unipaith.core.middleware import setup_middleware

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

setup_middleware(app)

app.include_router(api_router, prefix="/api/v1")
