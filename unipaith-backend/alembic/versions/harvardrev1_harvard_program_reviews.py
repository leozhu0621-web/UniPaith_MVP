"""Harvard profile repair — coverable external_reviews depth pass (data-only, no DDL)

Re-applies ``unipaith.data.harvard_profile.apply()`` now that the module carries
verified, cited ``external_reviews`` (MBAn shape) for eleven additional high-demand,
coverable programs that previously had reviews omitted: the Kennedy School MPA and
MPA/ID, the Law School LL.M., the Graduate School of Education Ed.M. and Ed.L.D., the
SEAS S.M. in Data Science, the Graduate School of Design M.Des., the School of Dental
Medicine D.M.D., and three flagship Faculty of Arts & Sciences A.B. concentrations
(Government, Statistics, Mathematics). Each review aggregates and paraphrases public
third-party coverage with two or more resolvable sources and honest cautions — no
fabricated quotes. This lifts Harvard from 8 to 19 reviewed programs.

No schema (DDL) changes. The enrichment is idempotent (programs key off ``slug``) and a
no-op when Harvard is absent, so it is safe on every environment (including CI
databases built with ``create_all``, which never run migrations). It ships to
production automatically: the container entrypoint runs ``alembic upgrade heads``
before serving.

Revision ID: harvardrev1
Revises: campusgallery1
Create Date: 2026-06-12
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import harvard_profile

revision = "harvardrev1"
down_revision = "campusgallery1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # apply() flushes; Alembic commits the surrounding migration transaction.
    session = Session(bind=op.get_bind())
    harvard_profile.apply(session)
    session.flush()


def downgrade() -> None:
    # Data-only enrichment — nothing structural to roll back.
    pass
