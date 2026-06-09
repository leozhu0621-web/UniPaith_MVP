"""seed Sloan + MBAn content_sources and populate their Events/Updates

Re-applies the MIT profile (which sets content_sources on the Sloan School row
and the MBAn Program row), then best-effort populates their keyword-gated
Events/Updates from the configured feeds. Fully fail-soft — a slow/down feed or
an absent MIT (fresh/CI DB) never breaks the migration. The daily scheduler job
keeps these fresh thereafter.

Revision ID: seedscp1
Revises: scope1
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import mit_profile

revision = "seedscp1"
down_revision = "scope1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from unipaith.models.institution import Institution, Program, School
    from unipaith.services.content_ingest.service import (
        seed_populate_sync,
        seed_populate_sync_scope,
    )

    session = Session(bind=op.get_bind())
    # Sets content_sources on the Sloan School + MBAn Program rows. Returns
    # False (no-op) when MIT is absent — safe on fresh/CI databases.
    if not mit_profile.apply(session):
        return
    mit = session.scalar(
        select(Institution).where(Institution.name == mit_profile.INSTITUTION_NAME)
    )
    if mit is None:
        return

    # Institution-wide refresh (idempotent; also re-checks MIT's own feeds).
    seed_populate_sync(session, mit)

    sloan = session.scalar(
        select(School).where(
            School.institution_id == mit.id,
            School.name == "MIT Sloan School of Management",
        )
    )
    if sloan is not None and sloan.content_sources:
        seed_populate_sync_scope(
            session, inst_id=mit.id, cfg=sloan.content_sources, school_id=sloan.id
        )

    mban = session.scalar(
        select(Program).where(
            Program.institution_id == mit.id,
            Program.slug == "mit-sloan-mban",
        )
    )
    if mban is not None and mban.content_sources:
        seed_populate_sync_scope(
            session, inst_id=mit.id, cfg=mban.content_sources, program_id=mban.id
        )


def downgrade() -> None:
    # Data-only, idempotent enrichment; no structural rollback.
    pass
