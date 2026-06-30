"""Registry + idempotent runner for university *profile* seeders.

Every ``<slug>_profile.py`` module in this package exposes a uniform
``apply(session: Session) -> bool`` that UPSERTs that university's canonical
data and returns whether anything changed.

Historically each profile was invoked from its *own* Alembic migration. With a
heavily parallel workflow that made every data edit a new migration head, so two
PRs touching data routinely produced an Alembic *dual head* that had to be hand-
merged (see git history: dozens of ``fix(alembic): merge dual head ...`` commits).

This registry lets the profiles be seeded as **data** — one idempotent pass over
all of them — instead of as schema *history*. New/edited university data should
go through :func:`seed_all` (run via ``scripts/seed_profiles.py``), **not** a new
per-university migration. See ``docs/DATA_SEEDING.md``.

The functions here take an already-bound sync ``Session`` and never construct an
engine, so they are safe to call from a migration, a management command, or a
test fixture.
"""

from __future__ import annotations

import importlib
import pkgutil
from collections.abc import Callable

from sqlalchemy.orm import Session

from unipaith import data as _data_pkg

#: A profile applier: ``apply(session) -> changed?``
ProfileApplier = Callable[[Session], bool]

_PROFILE_SUFFIX = "_profile"


def discover_profiles() -> dict[str, ProfileApplier]:
    """Return ``{slug: apply}`` for every ``*_profile.py`` in :mod:`unipaith.data`.

    Discovery is filesystem-driven (no hand-maintained list), so adding a new
    ``<slug>_profile.py`` with an ``apply(session)`` automatically registers it.
    """
    appliers: dict[str, ProfileApplier] = {}
    for mod in pkgutil.iter_modules(_data_pkg.__path__):
        if not mod.name.endswith(_PROFILE_SUFFIX):
            continue
        slug = mod.name[: -len(_PROFILE_SUFFIX)]
        module = importlib.import_module(f"{_data_pkg.__name__}.{mod.name}")
        apply = getattr(module, "apply", None)
        if callable(apply):
            appliers[slug] = apply
    return appliers


def profile_slugs() -> list[str]:
    """Sorted list of known university slugs."""
    return sorted(discover_profiles())


def seed_all(session: Session, *, slugs: list[str] | None = None) -> dict[str, bool]:
    """Idempotently apply every (or a selected subset of) university profile.

    Profiles are independent and self-contained (each owns one university), so
    order does not matter; we apply them in a stable, sorted order for
    reproducible logs. Returns ``{slug: changed?}``. Does **not** commit — the
    caller owns the transaction (matching the Alembic-migration convention).
    """
    appliers = discover_profiles()
    if slugs is not None:
        missing = [s for s in slugs if s not in appliers]
        if missing:
            raise KeyError(f"unknown profile slug(s): {', '.join(sorted(missing))}")
        appliers = {s: appliers[s] for s in slugs}

    results: dict[str, bool] = {}
    for slug, apply in sorted(appliers.items()):
        results[slug] = bool(apply(session))
    return results
