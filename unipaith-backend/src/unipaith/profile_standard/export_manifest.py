"""Serialize the manifest to ``frontend/src/generated/profile-manifest.json`` so
the frontend reads the same single source of truth (drives the render-parity
test now, and optional declarative widgets later).

Run: ``python -m unipaith.profile_standard.export_manifest``
"""

from __future__ import annotations

import json
from pathlib import Path

from .manifest import MANIFEST, STANDARD_VERSION


def build() -> dict:
    return {
        "version": STANDARD_VERSION,
        "levels": {
            level: [
                {
                    "id": s.id,
                    "title": s.title,
                    "order": s.order,
                    "required": s.required,
                    "widget": s.widget,
                    "fields": [f.key for f in s.fields],
                }
                for s in secs
            ]
            for level, secs in MANIFEST.items()
        },
    }


def _repo_root() -> Path:
    # .../unipaith-backend/src/unipaith/profile_standard/export_manifest.py
    # parents: [profile_standard, unipaith, src, unipaith-backend, <repo root>]
    return Path(__file__).resolve().parents[4]


def main() -> None:
    out = _repo_root() / "frontend" / "src" / "generated" / "profile-manifest.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(build(), indent=2) + "\n")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
