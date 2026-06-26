"""Public universities — matcher tuition scalar = NON-RESIDENT (out-of-state) rate

Clears REPAIR_BACKLOG entry #4 (HIGH) for six public flagships that shipped the IN-STATE
resident rate as the flat ``program.tuition`` scalar the CPEF budget feature reads
(``fits.py`` ``fit_range`` + the ``matching.py`` budget breaker ``p_tuition > s_budget``).
The scalar is residency-blind, so an out-of-state or international applicant — the MAJORITY of
the applicant pool at a flagship public, and ALL international applicants pay non-resident — was
scored as comfortably affordable at 2.5-3.5x too low a tuition, so the over-budget veto never
fired and the affordability fit over-scored.

The fix is a choice between two ALREADY-PUBLISHED numbers, never a guess: every affected
bachelor row already carries BOTH ``cost_data.breakdown.tuition_in_state`` AND
``cost_data.breakdown.tuition_out_of_state`` (verified, sourced). This migration stamps each
row's OWN published non-resident rate (read from its breakdown) into the MATCHER SCALAR
``programs.tuition`` ONLY, leaving ``cost_data`` untouched on the RESIDENT basis (the Berkeley
pattern, berkeleycip1): ``cost_data.tuition_usd`` + ``total_cost_of_attendance`` stay internally
consistent and the breakdown keeps both rates, so the cost card never shows tuition > total cost,
while the matcher reads the conservative, broadly-correct non-resident figure for a
national/international pool. Reading the value per-row from each row's own breakdown correctly
handles the per-school undergraduate differentials at Michigan and UW-Madison (no single
campus-wide figure to hardcode).

The six affected institutions (live API this run): University of California-Los Angeles
(15,202 -> 49,402), University of California-San Diego (16,758 -> 50,958), University of
Michigan-Ann Arbor (per-school, e.g. 17,864 -> 63,480), University of Florida (6,381 -> 28,659),
University of Wisconsin-Madison (per-school, 12,186 -> 44,210), and Purdue University-Main Campus
(9,992 -> 28,794). Their ``*_profile.py`` modules are edited in the same change so a future full
re-apply keeps the non-resident scalar (the bachelor branch now returns the out-of-state rate);
this migration is the deterministic live backfill (no heavy full-catalog re-apply, so it cannot
self-skip at boot). The durable fix is residency-aware budget matching in ``matching.py`` (CODE,
flagged for a human — FLAG #6); until it lands, the non-resident scalar is the matcher-correct
default.

UIUC is intentionally NOT included here: its breakdown carries no
``tuition_out_of_state`` value to read, so its non-resident sticker requires fresh research
rather than a breakdown read — left for a follow-up so this PR stays a pure no-fabrication
backfill.

Revision ID: pubtuitscalar1
Revises: uciprof1
Create Date: 2026-06-26
"""

from __future__ import annotations

from sqlalchemy import text

from alembic import op

revision = "pubtuitscalar1"
down_revision = "uciprof1"
branch_labels = None
depends_on = None

_INSTITUTIONS = [
    "University of California-Los Angeles",
    "University of California-San Diego",
    "University of Michigan-Ann Arbor",
    "University of Florida",
    "University of Wisconsin-Madison",
    "Purdue University-Main Campus",
]


def upgrade() -> None:
    bind = op.get_bind()
    # Stamp each published bachelor row's OWN verified non-resident rate (already in its
    # breakdown) into the MATCHER SCALAR `programs.tuition` ONLY. cost_data is left untouched on
    # the RESIDENT basis (tuition_usd + total_cost_of_attendance stay internally consistent; the
    # breakdown already carries both rates) — the Berkeley pattern (berkeleycip1): only the
    # exposed matcher scalar is the non-resident rate, so the cost card never shows
    # tuition > total cost. Only touches rows that actually carry a numeric tuition_out_of_state
    # in the breakdown, so it is a no-op on a fresh/CI database (and idempotent).
    bind.execute(
        text(
            """
            UPDATE programs p
            SET tuition = (p.cost_data->'breakdown'->>'tuition_out_of_state')::int
            FROM institutions i
            WHERE p.institution_id = i.id
              AND i.name = ANY(:names)
              AND p.degree_type = 'bachelors'
              AND jsonb_typeof(p.cost_data->'breakdown'->'tuition_out_of_state') = 'number'
            """
        ),
        {"names": _INSTITUTIONS},
    )


def downgrade() -> None:
    pass
