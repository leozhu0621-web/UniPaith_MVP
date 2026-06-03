"""Spec 65 §3 — program dense-embedding columns (revive the matcher cosine term).

Adds ``programs.embedding`` (JSONB, a 1024-d voyage vector stored as a list, like
``student_feature_vectors.embedding``) and ``programs.embedding_version`` (the
``feature_version`` the embedding was built from). The match-recompute path
computes + caches these lazily so the matcher's cosine term — 45% of fitness,
structurally dead until now because no program ever had an embedding — fires.

Guarded so it is a safe no-op against the conftest ``create_all`` test DB.

Revision ID: p65embed1a2b3
Revises: cs69inst1a2b3
Create Date: 2026-06-03

"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "p65embed1a2b3"  # pragma: allowlist secret
down_revision = "cs69inst1a2b3"  # pragma: allowlist secret
branch_labels = None
depends_on = None


def _program_cols() -> set[str]:
    insp = sa.inspect(op.get_bind())
    if "programs" not in insp.get_table_names():
        return set()
    return {c["name"] for c in insp.get_columns("programs")}


def upgrade() -> None:
    cols = _program_cols()
    if not cols:
        return
    if "embedding" not in cols:
        op.add_column("programs", sa.Column("embedding", postgresql.JSONB(), nullable=True))
    if "embedding_version" not in cols:
        op.add_column("programs", sa.Column("embedding_version", sa.Integer(), nullable=True))


def downgrade() -> None:
    cols = _program_cols()
    if "embedding_version" in cols:
        op.drop_column("programs", "embedding_version")
    if "embedding" in cols:
        op.drop_column("programs", "embedding")
