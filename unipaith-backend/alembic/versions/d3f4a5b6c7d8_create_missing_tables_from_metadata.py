"""create missing tables from SQLAlchemy metadata

Prod's alembic_version was advanced through many Phase A migrations
whose CREATE TABLE statements never actually executed (see prior
corrective migrations b1c2d3e4f5a6 and c2e3f4a5b6c7). Missing tables
include discovery_sessions, discovery_messages, student_goals,
student_needs, student_identity, student_strategies,
workshop_feedback_runs, and student_data_consent / student_visa_info.

Rather than re-author each CREATE TABLE statement here, this
migration imports the SQLAlchemy Base and calls
`metadata.create_all(bind, checkfirst=True)`. SQLAlchemy emits
CREATE TABLE IF NOT EXISTS for each declarative model, so:
  - tables that already exist are skipped (no schema drift introduced)
  - tables that are missing are created from the live model definitions
  - indexes / foreign keys defined declaratively come along for free

After this, the c2e3f4a5b6c7 column backfill will have already added
the column-level extensions; together they bring prod's schema into
alignment with the code's model layer.

Revision ID: d3f4a5b6c7d8
Revises: c2e3f4a5b6c7
Create Date: 2026-05-10 20:45:00.000000

"""

from __future__ import annotations

import logging

from alembic import op

# revision identifiers
revision = "d3f4a5b6c7d8"
down_revision = "c2e3f4a5b6c7"
branch_labels = None
depends_on = None

log = logging.getLogger("alembic.runtime.migration")


def upgrade() -> None:
    # Import here, not at module top, so eager alembic collection
    # doesn't load the full app stack (some models depend on settings
    # that aren't present during offline migration generation).
    from unipaith import models  # noqa: F401 — register all model modules
    from unipaith.models.base import Base

    bind = op.get_bind()
    table_count_before = len(Base.metadata.sorted_tables)
    log.info(
        "create_all: %d declarative tables in metadata; "
        "issuing CREATE TABLE IF NOT EXISTS for each",
        table_count_before,
    )
    Base.metadata.create_all(bind=bind, checkfirst=True)


def downgrade() -> None:
    # No-op: this migration only creates missing tables; existing
    # tables are untouched. Rolling back would require dropping
    # potentially-populated user-facing tables, so leave to manual
    # surgery if ever needed.
    pass
