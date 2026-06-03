import sys
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from unipaith.config import settings

# Under pytest, each test case runs on its own event loop; a pooled asyncpg
# connection reused across loops raises "attached to a different loop". NullPool
# hands out a fresh connection per checkout (bound to the current loop) — the same
# choice the conftest test engine makes. Production keeps the real pool.
if "pytest" in sys.modules:
    engine = create_async_engine(settings.database_url, echo=False, poolclass=NullPool)
else:
    engine = create_async_engine(
        settings.database_url,
        echo=settings.debug,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_pool_overflow,
        pool_pre_ping=True,
        pool_recycle=settings.db_pool_recycle,
    )

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
