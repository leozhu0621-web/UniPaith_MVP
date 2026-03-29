"""
Reset dev environment: drop all tables, recreate, and seed.

Usage: python -m scripts.reset_dev
"""
import asyncio

from unipaith.database import async_session, engine
from unipaith.models import Base
from scripts.seed_dev_data import seed


async def main() -> None:
    print("Dropping all tables ...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    print("Creating all tables ...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("Seeding data ...")
    async with async_session() as db:
        await seed(db)

    print("\nDev reset complete!")


if __name__ == "__main__":
    asyncio.run(main())
