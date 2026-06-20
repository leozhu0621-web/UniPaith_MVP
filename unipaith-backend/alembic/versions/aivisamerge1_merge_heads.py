"""merge concurrent heads: AI-structure visa migration + Stanford enrichment

Two migrations landed concurrently on main — ``aivisamig01`` (the AI-Structure
visa-feasibility ``programs.sponsors_international`` column) and ``stanfordprof11``
(a profile-enrichment data migration). This is a no-op merge migration that
unifies them into a single head; it adds no schema (both parents already applied
their own DDL).

Revision ID: aivisamerge1
Revises: aivisamig01, stanfordprof11
Create Date: 2026-06-19
"""

from __future__ import annotations

# revision identifiers, used by Alembic.
revision = "aivisamerge1"  # pragma: allowlist secret
down_revision = ("aivisamig01", "stanfordprof11")
branch_labels = None
depends_on = None


def upgrade() -> None:
    """No-op: a merge of two already-applied heads."""
    pass


def downgrade() -> None:
    """No-op: splitting back into two heads requires no schema change."""
    pass
