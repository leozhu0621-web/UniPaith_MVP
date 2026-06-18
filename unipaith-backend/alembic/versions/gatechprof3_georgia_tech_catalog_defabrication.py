"""Georgia Tech catalog de-fabrication — real descriptions, real departments, no synthesized reviews

Re-applies ``georgia_tech_profile.apply()`` after the gatechprof3 de-fabrication:
  • every program description is now a field-specific overview sourced from that program's
    own catalog.gatech.edu page (``georgia_tech_catalog_descriptions``), replacing the
    generated ``"{name} is a … program offered through Georgia Tech's {College}"`` stub;
  • ``department`` is now the real owning GT school/unit, not the field echoed from the name;
  • the 58 machine-synthesized ``DEPTH_REVIEWS`` are removed (re-apply sets external_reviews
    only on the four hand-gathered flagships; the rest are cleared to NULL and recorded in
    ``_standard.omitted``).
Idempotent; no-op when Georgia Tech is absent (fresh/CI databases).

Revision ID: gatechprof3
Revises: uiucprof4
Create Date: 2026-06-18
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import georgia_tech_profile

revision = "gatechprof3"
down_revision = "uiucprof4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    georgia_tech_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass
