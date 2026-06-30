"""The profile registry must cover every ``*_profile.py`` and expose a uniform
``apply(session)`` — this is what lets us seed university data as data (one pass)
instead of one-Alembic-migration-per-edit. See ``unipaith/data/profiles.py``.
"""

from __future__ import annotations

import inspect
from pathlib import Path

from unipaith.data.profiles import discover_profiles, profile_slugs

_DATA_DIR = Path(__file__).resolve().parents[1] / "src" / "unipaith" / "data"


def _slugs_on_disk() -> set[str]:
    return {p.stem[: -len("_profile")] for p in _DATA_DIR.glob("*_profile.py")}


def test_registry_covers_every_profile_module() -> None:
    """Discovery must match the files on disk exactly — no drift, nothing missed."""
    assert set(discover_profiles()) == _slugs_on_disk()


def test_there_are_profiles() -> None:
    # Guards against a discovery bug silently returning an empty registry.
    assert len(profile_slugs()) >= 30


def test_every_apply_is_callable_with_a_session_first_arg() -> None:
    for slug, apply in discover_profiles().items():
        assert callable(apply), f"{slug}.apply is not callable"
        params = list(inspect.signature(apply).parameters.values())
        assert params, f"{slug}.apply takes no arguments"
        assert params[0].name == "session", f"{slug}.apply first arg is not 'session'"
