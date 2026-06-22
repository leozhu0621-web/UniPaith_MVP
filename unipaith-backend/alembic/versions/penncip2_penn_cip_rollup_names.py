"""Penn: resolve residual federal CIP-rollup TITLE program names → real Penn degrees

REPAIR_BACKLOG #3 (run 79). Three federal CIP rollup/aggregation titles still shipped
verbatim as Penn ``program_name`` values — degrees the institution does NOT confer under
that literal name (miss #2 run-79 tell (b): field part byte-identical to a federal CIP
code→title):

  * CIP 42.27 "Research and Experimental Psychology" (BA/MA/PhD) — Penn's Department of
    Psychology confers one Psychology degree line; the BA + A.M. already ship as the
    42.01 flagships, so the 42.27 BA/MA are duplicates (DROPPED) and the 42.27 PhD fills
    the real doctoral gap → "Doctor of Philosophy in Psychology".
  * CIP 42.28 "Clinical, Counseling and Applied Psychology" (MA/certificate) — Penn's only
    School of Arts & Sciences degree in this CIP is the Master of Applied Positive
    Psychology (MAPP, SAS / LPS, founded by Martin Seligman). The MA resolves to MAPP with
    its real LPS tuition ($59,424 full-time academic year, 2026-27); Penn publishes no
    standalone graduate certificate in this area, so the certificate row is DROPPED.
  * CIP 52.02 "Business Administration, Management and Operations" (PhD, Wharton) — the
    Wharton Management Department doctoral program → "Doctor of Philosophy in Management"
    (the 52.02 BS = the Wharton BS in Economics and the 52.02 master's = the Wharton MBA
    already ship as flagships).

Every name is verified against catalog.upenn.edu / the owning department or LPS page;
no value is guessed (omit-never-guess — the two PhD rows carry tuition omitted-with-reason
as fully-funded research doctorates). The data module's import-time quality gate now also
fails the build on any field part / department equal to a federal CIP rollup title, so the
whole class cannot regress. Idempotent: ``penn_profile.apply`` upserts by slug + drops the
de-fabricated duplicate rows, then re-derives ``program_preferences`` for the catalog.

Revision ID: penncip2
Revises: harvardndmrg1
Create Date: 2026-06-22
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import penn_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "penncip2"
down_revision = "harvardndmrg1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    penn_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == penn_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    # Data-only re-enrichment; the prior catalog is reproduced by the previous migration's
    # apply(). No schema change to reverse.
    pass
