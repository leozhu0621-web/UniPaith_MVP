"""Carnegie Mellon matcher-core enrichment (REPAIR_BACKLOG #1 / #4a).

Re-applies ``carnegie_mellon_profile.apply()`` after wiring two matcher-core dimensions the
live catalog (180 real, field-specific programs) was missing:
  * #1 ``cip_code`` — a verified NCES CIP-2020 6-digit code is now stamped on every
    ``Program.cip_code`` (``carnegie_mellon_cip_who.CIP6_BY_SLUG``). The base ``apply()`` never
    assigned it, so the matcher scored every CMU program field-blind; the CPEF field signal
    resolves on the CIP code + program-name aliases. The 2020-new / less-common codes were
    verified against the NCES CIP user site + DHS STEM list (AI 11.0102, Robotics 14.4201,
    Data Science 30.7001, Business Analytics 30.7102, Music Technology 50.0913, Language
    Interpretation and Translation 16.0103, Rhetoric and Composition 23.1304, Financial
    Mathematics 27.0305, Medical Informatics 51.2706) — no guesses.
  * #4a ``who_its_for`` filled on every program with a PROGRAM-DISTINCT (distinct/total = 1.0)
    field-specific statement derived from each program's own field + credential level
    (``carnegie_mellon_cip_who.WHO_BY_SLUG``) — never a degree-type template. The base
    ``apply()`` previously left the field null catalog-wide. (CMU's module never hard-nulled it,
    so there is no ``= None`` to remove.)

CMU is private, so the public non-resident-tuition scalar (#2) does not apply; its bachelor's
and master's tuition tiers are already ~100% covered and its Ph.D. / per-credit-certificate
nulls are funded-research / per-credit rows honestly omitted with reason (#3 n/a). Because
``progprefbf1`` derived program-preference rows while ``cip_code`` was still null, and
``backfill_program_preferences`` only fills EMPTY fields on existing rows, the corrected CIP
would not reach the program -> student field signal. So this DELETES unclaimed
``source="derived"`` preference rows for CMU, then re-derives — the same recompute the
Duke / Northwestern / Rice / UW-Madison CIP repairs use. Direct apply (no lock-bounded skip)
so the data actually lands; verify-live on content.

Revision ID: cmucipwho1
Revises: dukecipwho1
Create Date: 2026-06-26
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import carnegie_mellon_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "cmucipwho1"
down_revision = "dukecipwho1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    carnegie_mellon_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == carnegie_mellon_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        # Only clear DERIVED rows for UNCLAIMED programs — backfill skips claimed
        # programs, so deleting a claimed row would strand first-party data.
        prog_ids = session.scalars(
            select(Program.id).where(
                Program.institution_id == inst.id,
                Program.is_claimed.is_(False),
            )
        ).all()
        if prog_ids:
            session.execute(
                delete(ProgramPreference).where(
                    ProgramPreference.program_id.in_(prog_ids),
                    ProgramPreference.source == "derived",
                )
            )
            session.flush()
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
