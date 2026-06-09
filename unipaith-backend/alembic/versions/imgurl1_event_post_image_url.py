"""cover image_url on events + institution_posts (news-grid)

Adds nullable image_url to events + institution_posts (the news-grid card's
cover image, captured from the feed's media:content), then best-effort
backfills it on existing MIT / Sloan / MBAn posts by re-fetching the news feed
and matching by external_id. Fail-soft — a slow/down feed never breaks the
migration; the daily content_ingest_refresh job backfills the rest.

Revision ID: imgurl1
Revises: seedscp1
"""

import sqlalchemy as sa
from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import mit_profile

revision = "imgurl1"
down_revision = "seedscp1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("events", sa.Column("image_url", sa.String(length=1000), nullable=True))
    op.add_column(
        "institution_posts", sa.Column("image_url", sa.String(length=1000), nullable=True)
    )

    from unipaith.models.institution import Institution, Program, School
    from unipaith.services.content_ingest.service import backfill_images_sync

    session = Session(bind=op.get_bind())
    mit = session.scalar(
        select(Institution).where(Institution.name == mit_profile.INSTITUTION_NAME)
    )
    if mit is None:
        return

    if mit.content_sources:
        backfill_images_sync(session, inst_id=mit.id, cfg=mit.content_sources)

    sloan = session.scalar(
        select(School).where(
            School.institution_id == mit.id,
            School.name == "MIT Sloan School of Management",
        )
    )
    if sloan is not None and sloan.content_sources:
        backfill_images_sync(session, inst_id=mit.id, cfg=sloan.content_sources, school_id=sloan.id)

    mban = session.scalar(
        select(Program).where(
            Program.institution_id == mit.id,
            Program.slug == "mit-sloan-mban",
        )
    )
    if mban is not None and mban.content_sources:
        backfill_images_sync(session, inst_id=mit.id, cfg=mban.content_sources, program_id=mban.id)


def downgrade() -> None:
    op.drop_column("institution_posts", "image_url")
    op.drop_column("events", "image_url")
