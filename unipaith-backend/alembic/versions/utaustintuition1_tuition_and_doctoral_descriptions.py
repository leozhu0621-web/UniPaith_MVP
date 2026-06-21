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
   omission. ``apply()`` now stamps the real cited published ANNUAL rate per credential level —
   undergraduate $11,688 (College Scorecard, UNITID 228778); standard academic graduate
   $12,006 (UT Texas One Stop per-credit × standard full-time load); School of Law J.D.
   $38,236; Dell Med M.D. $22,074; and the McCombs Full-Time MBA $55,196 (its school-published
   premium first-year rate, NOT the generic graduate figure). ``program.tuition`` is consumed
   as ANNUAL, so programs without a verified annual rate omit the scalar rather than ship a
   misleading number: the 3 online CDSO master's publish only a ~$10,000 TOTAL (kept in
   ``cost_data.total_program_tuition``, annual omitted); the other specialized McCombs master's
   carry an unverified premium rate; and PharmD/AuD/DNP bill per their own schedules — each
   records ``cost_data.tuition_usd`` in ``_standard.omitted`` (322/338 = 95% carry a verified
   annual figure; the 16 omissions are honest, not guesses).

Re-applies ``ut_austin_profile.apply()``, refreshes the DERIVED ``program_preferences`` rows
(deleted first so backfill re-derives them from the repaired descriptions — claimed/first-party
rows are never touched). Chains off
``cornellpercrd2`` (a concurrent session, #1037, landed it as the new single head while this
PR's CI ran), so ``main`` carries exactly one head.

Revision ID: utaustintuition1
Revises: cornellpercrd2
Create Date: 2026-06-21
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import ut_austin_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
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
        # backfill_program_preferences only FILLS empty fields on an existing derived row;
        # it does not refresh a stale target_profile. The three repaired Ph.D. descriptions
        # (and the corrected tuition) feed the derived target applicant, so on a DB that
        # already ran the fleet backfill those rows would keep signals derived from the old
        # template-slot prose. Delete the DERIVED rows for this institution first so backfill
        # re-derives them from the repaired data. source="claimed"/first-party rows are NEVER
        # touched (authority-safe).
        session.execute(
            delete(ProgramPreference).where(
                ProgramPreference.source == "derived",
                ProgramPreference.program_id.in_(
                    select(Program.id).where(Program.institution_id == inst.id)
                ),
            )
        )
        session.flush()
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
