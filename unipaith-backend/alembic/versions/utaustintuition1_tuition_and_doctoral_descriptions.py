"""UT Austin tuition backfill + 3 researched doctoral descriptions (REPAIR BACKLOG run 72 #3 + #9).

Two matcher-and-editorial repairs, applied as one atomic re-apply of ``ut_austin_profile.apply()``:

1. **Template-slot machine grammar (CRITICAL #3).** Three Ph.D. rows — Anthropology, History,
   and Computer Science — shipped a ``template_slot_artifacts`` description where the field
   anchor's leading clause defeated ``_extract_focus``, slotting a *bachelor's* sentence
   fragment into the doctoral frame ("…advances original research in The Bachelor of Arts in
   Anthropology … introduces the four …"). ``_assign_descriptions`` now uses hand-authored,
   researched doctoral descriptions (``_DOCTORAL_DESCRIPTION_BY_SLUG``) for those three rows —
   each opens on the subject, states the field's real UT Austin doctoral research areas, names
   the real owning department, and shares no body with its siblings — so
   ``template_slot_artifacts`` and ``frame_stripped_shared_body(abs_chars=150)`` reach the
   gold-MIT 0.

2. **Matcher-core tuition null catalog-wide (#9).** The catalog shipped 0% ``tuition`` (every
   ``p.tuition = None``), so the CPEF matcher scored budget-fit blind on all 338 programs.
   Tuition is institution-PUBLISHED, so this was a skipped knowable field, not an honest
   omission. ``apply()`` now stamps the real cited published rate per credential level —
   undergraduate $11,688 (College Scorecard, UNITID 228778); graduate $12,006 (UT Texas One
   Stop per-credit × standard full-time load); the CDSO online master's published ~$10,000
   total; School of Law J.D. $38,236 and Dell Med M.D. $22,074. The three remaining
   professional doctorates (PharmD/AuD/DNP) have no separately-verified annual figure here, so
   their ``cost_data.tuition_usd`` is honestly recorded in ``_standard.omitted`` rather than
   guessed (335/338 = 99% covered).

Re-applies ``ut_austin_profile.apply()`` and re-derives program-preference rows. Chains off
``cornellpercrd2`` (a concurrent session, #1037, landed it as the new single head while this
PR's CI ran), so ``main`` carries exactly one head.

Revision ID: utaustintuition1
Revises: cornellpercrd2
Create Date: 2026-06-21
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import ut_austin_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "utaustintuition1"
down_revision = "cornellpercrd2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    ut_austin_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == ut_austin_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
