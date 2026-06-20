"""AI Structure (Spec 3 §3) — add the 5 deferred typed-fit columns that wire the
last dormant CPEF matcher signals onto real data.

student_preferences gains the student-side constraints:
  - desired_time_to_degree_months (Integer)  → the "time" fit (vs program duration)
  - wants_part_time (Boolean)                 → the "flexibility" fit (hard want)
  - wants_online (Boolean)                    → the "flexibility" fit (hard want)
  - wants_career_support (Boolean)            → the "support" fit (soft want)
programs gains the program-side counterpart:
  - part_time_available (Boolean)             → the "flexibility" fit (program offers)

All net-additive + nullable: an absent preference / unset program attribute
injects no phantom matcher dimension (the matcher gates every signal on a
non-null value). Each add is guarded (`_has_column`) so the migration is a safe
no-op against a dev/test DB built from the models via `create_all` (the conftest
path), and runs incrementally in production from the prior head.

Revision ID: aimig01typedfit
Revises: uwseedmerge1
Create Date: 2026-06-18

"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "aimig01typedfit"  # pragma: allowlist secret
down_revision = "uwseedmerge1"  # pragma: allowlist secret
branch_labels = None
depends_on = None

_PREFERENCE_COLS: list[tuple[str, sa.types.TypeEngine]] = [
    ("desired_time_to_degree_months", sa.Integer()),
    ("wants_part_time", sa.Boolean()),
    ("wants_online", sa.Boolean()),
    ("wants_career_support", sa.Boolean()),
]
_PROGRAM_COLS: list[tuple[str, sa.types.TypeEngine]] = [
    ("part_time_available", sa.Boolean()),
]


def _has_column(table: str, col: str) -> bool:
    return col in {c["name"] for c in sa.inspect(op.get_bind()).get_columns(table)}


def _add_cols(table: str, cols: list[tuple[str, sa.types.TypeEngine]]) -> None:
    for name, typ in cols:
        if not _has_column(table, name):
            op.add_column(table, sa.Column(name, typ, nullable=True))


def upgrade() -> None:
    _add_cols("student_preferences", _PREFERENCE_COLS)
    _add_cols("programs", _PROGRAM_COLS)


def downgrade() -> None:
    for name, _typ in _PROGRAM_COLS:
        if _has_column("programs", name):
            op.drop_column("programs", name)
    for name, _typ in _PREFERENCE_COLS:
        if _has_column("student_preferences", name):
            op.drop_column("student_preferences", name)
