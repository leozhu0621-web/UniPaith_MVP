"""Founder governance (2026-06-18) — add ``programs.sponsors_international`` so the
student→program (s→p) FEASIBILITY veto can fire.

A study-visa-needing student literally cannot attend a program that cannot
sponsor an international applicant, so such a program is INFEASIBLE FOR HER and
must sink in HER ranking (it helps her avoid a dead end). This is the ONLY
defensible use of immigration data in the matcher: feasibility in the student's
OWN direction.

Asymmetry pinned elsewhere: the program→student (p→s) SELECTION direction MUST
NEVER read this column — immigration status is not an applicant-selection
criterion (Spec 38 §3/§9, Spec 46 §6). See tests/test_spec38_fairness_contract.py.

Net-additive + nullable: NULL = unknown sponsorship → the veto does NOT fire
(never assume a program cannot sponsor). The add is guarded (`_has_column`) so
this is a safe no-op against a dev/test DB built from the models via
`create_all` (the conftest path), and runs incrementally in production from the
prior head.

Revision ID: aivisamig01
Revises: aimig01typedfit
Create Date: 2026-06-18

"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "aivisamig01"  # pragma: allowlist secret
down_revision = "aimig01typedfit"  # pragma: allowlist secret
branch_labels = None
depends_on = None

_PROGRAM_COLS: list[tuple[str, sa.types.TypeEngine]] = [
    ("sponsors_international", sa.Boolean()),
]


def _has_column(table: str, col: str) -> bool:
    return col in {c["name"] for c in sa.inspect(op.get_bind()).get_columns(table)}


def upgrade() -> None:
    for name, typ in _PROGRAM_COLS:
        if not _has_column("programs", name):
            op.add_column("programs", sa.Column(name, typ, nullable=True))


def downgrade() -> None:
    for name, _typ in _PROGRAM_COLS:
        if _has_column("programs", name):
            op.drop_column("programs", name)
