"""Spec 12 — backfill NYU ranking_data (the one field b12c0de5f7a9 couldn't fill).

The prior backfill (b12c0de5f7a9) set NYU's structured profile but guarded every
column with ``COALESCE(col, …)``. NYU's ``ranking_data`` in prod is stored as a
JSON-null literal (``'null'::jsonb``), which is ``IS NOT NULL`` in Postgres — so
COALESCE kept it and the column still serializes to ``None``. That leaves the
Overview tab's **accreditation** line (spec §3.1) and the ownership/ranking
facts empty.

This revision sets ``ranking_data`` when it is SQL NULL **or** JSON null, so the
Overview tab renders accreditation + ownership. Idempotent: re-running is a
no-op once the value is a real object (the WHERE no longer matches).

Revision ID: c13d1ef6a8b0
Revises: b12c0de5f7a9
Create Date: 2026-06-01

"""

from __future__ import annotations

import json
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c13d1ef6a8b0"  # pragma: allowlist secret
down_revision: str | Sequence[str] | None = "b12c0de5f7a9"  # pragma: allowlist secret
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_NYU = "New York University"
_NYU_RANKING = {
    "ownership_type": "private_nonprofit",
    "accreditor": "Middle States Commission on Higher Education",
    "us_news_2025": 30,
    "acceptance_rate": 0.12,
    "graduation_rate": 0.87,
    "median_earnings": 75300,
    "retention_rate": 0.94,
    "tuition_out_of_state": 60438,
    "carnegie_classification": "R1: Doctoral Universities – Very high research activity",
}


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE institutions
            SET ranking_data = CAST(:ranking AS jsonb)
            WHERE name = :name
              AND (ranking_data IS NULL OR jsonb_typeof(ranking_data) = 'null')
            """
        ).bindparams(ranking=json.dumps(_NYU_RANKING), name=_NYU)
    )


def downgrade() -> None:
    # Reverse only the value we set, leaving a JSON null behind (the prior state).
    op.execute(
        sa.text(
            """
            UPDATE institutions
            SET ranking_data = 'null'::jsonb
            WHERE name = :name
              AND ranking_data = CAST(:ranking AS jsonb)
            """
        ).bindparams(ranking=json.dumps(_NYU_RANKING), name=_NYU)
    )
