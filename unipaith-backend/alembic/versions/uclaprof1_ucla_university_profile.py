"""enrich University of California, Los Angeles (UCLA) profile (data-only, no DDL)

Populates UCLA's canonical profile — rankings (QS #46, THE #18, U.S. News #17 National),
ownership/Carnegie/accreditor classification, school_outcomes depth (report-card stats,
admissions funnel, demographics, scale, research with lab links, campus life with
resource links, location, a verified 5-photo campus gallery, flagship facts, sources),
a character-leading intro, its 13 real degree-granting schools/colleges (the College of
Letters and Science plus the Samueli, Anderson, Law, Geffen Medicine, Dentistry, Fielding
Public Health, Nursing, Luskin, Education & Information Studies, Arts and Architecture,
Theater/Film/Television, and Herb Alpert Music schools — each with sourced About-tab
detail and its own content_sources), and the FULL published degree catalog (373 degree
programs built from the official UCLA General Catalog, each mapped to its owning school,
with delivery_format set on the Samueli online MS tracks). Flagship coverable programs
(Anderson MBA, UCLA Law J.D., plus Computer Science, the M.D., the Master of Financial
Engineering, Business Economics, and Film & Television) carry external_reviews and, for
the MBA and J.D., verified employment outcomes — via ``unipaith.data.ucla_profile.apply()``.

No schema (DDL) changes. The enrichment is idempotent and a no-op when UCLA is absent,
so this migration is safe on every environment (and on CI databases built with
``create_all``, which never run migrations anyway). It ships to production automatically:
the container entrypoint runs ``alembic upgrade heads`` before serving.

Revision ID: uclaprof1
Revises: onboardstate1
Create Date: 2026-06-13
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import ucla_profile

revision = "uclaprof1"
# Chain off the current single head so the migration chain stays single-headed.
down_revision = "onboardstate1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # apply() flushes; Alembic commits the surrounding migration transaction.
    session = Session(bind=op.get_bind())
    ucla_profile.apply(session)
    session.flush()


def downgrade() -> None:
    # Data-only enrichment — nothing structural to roll back.
    pass
