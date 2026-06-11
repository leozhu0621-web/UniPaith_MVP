"""enrich Duke University to the gold standard — full catalog, feeds on every node (data-only)

Applies ``unipaith.data.duke_profile.apply()``, building Duke (previously a shallow,
report-card-only institution) into a full gold-standard profile:
  • the institution gains verified rankings (QS #62 / THE #28 / U.S. News #7), Carnegie R1 +
    SACSCOC + private ownership, founding/scale/endowment, admissions funnel (Class of 2029),
    diversity, outcomes, cost & aid, research institutes WITH links, campus-life resources
    WITH links, a real Duke Chapel hero photo, and a working ``content_sources`` (the Duke
    Today all-topics RSS + the Duke events iCalendar);
  • 10 schools — Trinity College, Pratt Engineering, Fuqua, Law, Medicine, Nursing, the
    Nicholas School, Sanford, Divinity and The Graduate School — each with about_detail
    (founded, dean, faculty where verified, research centers) and its OWN verified Duke Today
    per-school tag RSS + events feed, so every school's Events & Updates tab populates;
  • ~154 programs — every Trinity/Pratt undergraduate major, the professional and master's
    degrees of each school (including the online/hybrid MSQM, DEL-MEM, Pratt MEng and Sanford
    MPA/MNSP programs), and the Graduate School's Ph.D. programs — each with verified basics,
    ``delivery_format``, a school-scoped ``content_sources`` (program keywords), and a
    ``_standard`` stamp recording the deep fields Duke does not publish per program.

No schema (DDL) changes. The enrichment is idempotent (upsert by slug) and a no-op when Duke
is absent, so this migration is safe on every environment (and on CI databases built with
``create_all``, which never run migrations).

Revision ID: dukeprof1
Revises: yaleenrich1
Create Date: 2026-06-11
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import duke_profile

revision = "dukeprof1"
down_revision = "yaleenrich1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # apply() flushes; Alembic commits the surrounding migration transaction.
    session = Session(bind=op.get_bind())
    duke_profile.apply(session)
    session.flush()


def downgrade() -> None:
    # Data-only enrichment — nothing structural to roll back.
    pass
