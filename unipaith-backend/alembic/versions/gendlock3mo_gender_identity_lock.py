"""Basic-info demographics: gender 3-month change-lock (Spec 2026-06-18).

Adds ``student_profiles.gender_identity_updated_at`` (nullable, tz-aware). The
existing free ``gender_identity`` String(50) keeps holding the value; this
timestamp is stamped on every applied change so StudentService.update_profile
can enforce the 90-day (3-month) lock. Additive + nullable, no backfill → safe
to apply online. Guarded so it is a no-op against the conftest ``create_all``
test DB (which already has the column from the model) and runs incrementally in
production from the prior single head ``uwseedmerge1``.

Revision ID: gendlock3mo
Revises: uwseedmerge1
Create Date: 2026-06-18

"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "gendlock3mo"  # pragma: allowlist secret
down_revision = "uwseedmerge1"  # pragma: allowlist secret
branch_labels = None
depends_on = None


def _has_column(table: str, column: str) -> bool:
    insp = sa.inspect(op.get_bind())
    return column in {c["name"] for c in insp.get_columns(table)}


def upgrade() -> None:
    if _has_column("student_profiles", "gender_identity_updated_at"):
        return
    op.add_column(
        "student_profiles",
        sa.Column("gender_identity_updated_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("student_profiles", "gender_identity_updated_at")
