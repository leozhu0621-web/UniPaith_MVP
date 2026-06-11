"""Replay all profile DATA migrations onto a seeded scratch DB (schema already
at head, so data migrations were originally no-ops on the empty DB).

Calls each data module's apply() in original migration order, then re-runs the
inline data migrations (feedsbackfill1, instenrich1, instenrich2, and the
post-profile feedsforce1) with a monkeypatched ``op``.
"""

from __future__ import annotations

import importlib.util
import pathlib
import types

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from unipaith.data import (
    berkeley_profile,
    caltech_profile,
    carnegie_mellon_profile,
    chicago_profile,
    columbia_profile,
    cornell_profile,
    harvard_profile,
    mit_profile,
    penn_profile,
    princeton_profile,
    stanford_profile,
    yale_profile,
)

DB = "postgresql+psycopg2://unipaith:unipaith@localhost:5432/unipaith"
VERSIONS = pathlib.Path(__file__).resolve().parent.parent / "alembic" / "versions"

MODULES = [
    mit_profile,
    harvard_profile,
    columbia_profile,
    penn_profile,
    princeton_profile,
    stanford_profile,
    yale_profile,
    berkeley_profile,
    caltech_profile,
    chicago_profile,
]

INLINE = [
    "feedsbackfill1_institution_feeds.py",
    "instenrich1_four_universities.py",
    "instenrich2_remaining_14.py",
]

# Profile data modules whose migrations chain after the INLINE migrations
# (cornellprof1 -> cmuprof1 follow instenrich2).
POST_MODULES = [
    cornell_profile,
    carnegie_mellon_profile,
]

# Inline data migrations that chain after the POST_MODULES profiles. feedsforce1
# (Revises: cornellprof1) force-overwrites content_sources for several
# universities and is not reproduced by any profile apply(), so replay must run
# it to match ``alembic upgrade head``.
POST_INLINE = [
    "feedsforce1_fix_zero_news.py",
]


def run_inline(fname: str, conn) -> None:
    spec = importlib.util.spec_from_file_location(fname[:-3], VERSIONS / fname)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.op = types.SimpleNamespace(get_bind=lambda: conn)
    mod.upgrade()


def main() -> None:
    engine = create_engine(DB)
    with engine.begin() as conn:
        session = Session(bind=conn)
        for m in MODULES:
            m.apply(session)
            session.flush()
            print(f"applied {m.__name__}")
        for fname in INLINE:
            run_inline(fname, conn)
            print(f"applied {fname}")
        for m in POST_MODULES:
            m.apply(session)
            session.flush()
            print(f"applied {m.__name__}")
        for fname in POST_INLINE:
            run_inline(fname, conn)
            print(f"applied {fname}")
        session.flush()
    print("replay complete")


if __name__ == "__main__":
    main()
