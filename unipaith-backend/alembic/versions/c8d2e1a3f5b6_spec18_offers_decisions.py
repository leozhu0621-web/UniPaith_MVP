"""Spec 18 (Decisions & Offers): extend offer_letters + applications

Spec 18 turns the institution-issued ``offer_letters`` row into the single
student-facing Offer shape (§3/§14): the same row is used whether the offer
was platform-issued or recorded by the student after an off-platform decision
(``received_externally``). Adds the richer fields the per-offer UX (§4) and the
``OutcomeBriefForOfferLetter`` agent (45 §15) need, plus a student-side
``student_decision`` on applications for the §2 decision states
(accepted_by_student / declined_by_student / withdrawn).

Guarded with has_column so it is a safe no-op against a dev DB that was built
from the models via ``create_all``.

Revision ID: c8d2e1a3f5b6
Revises: b7c1d9e2f3a4
Create Date: 2026-05-31

"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "c8d2e1a3f5b6"  # pragma: allowlist secret
down_revision = "b7c1d9e2f3a4"  # pragma: allowlist secret
branch_labels = None
depends_on = None


def _has_column(bind, table: str, column: str) -> bool:
    insp = sa.inspect(bind)
    try:
        return any(c["name"] == column for c in insp.get_columns(table))
    except Exception:
        return False


def upgrade() -> None:
    bind = op.get_bind()

    # ── offer_letters: Spec 18 student-facing Offer shape (§3/§4/§14) ──
    if not _has_column(bind, "offer_letters", "received_externally"):
        op.add_column(
            "offer_letters",
            sa.Column(
                "received_externally",
                sa.Boolean(),
                server_default=sa.text("false"),
                nullable=False,
            ),
        )
    if not _has_column(bind, "offer_letters", "decision_date"):
        op.add_column("offer_letters", sa.Column("decision_date", sa.Date(), nullable=True))
    if not _has_column(bind, "offer_letters", "scholarship_currency"):
        op.add_column(
            "offer_letters", sa.Column("scholarship_currency", sa.String(length=8), nullable=True)
        )
    if not _has_column(bind, "offer_letters", "tuition_estimate"):
        op.add_column("offer_letters", sa.Column("tuition_estimate", sa.Integer(), nullable=True))
    if not _has_column(bind, "offer_letters", "total_cost_estimate"):
        op.add_column(
            "offer_letters", sa.Column("total_cost_estimate", sa.Integer(), nullable=True)
        )
    if not _has_column(bind, "offer_letters", "start_term_season"):
        op.add_column(
            "offer_letters", sa.Column("start_term_season", sa.String(length=16), nullable=True)
        )
    if not _has_column(bind, "offer_letters", "start_term_year"):
        op.add_column("offer_letters", sa.Column("start_term_year", sa.Integer(), nullable=True))
    if not _has_column(bind, "offer_letters", "next_step_actions"):
        op.add_column(
            "offer_letters",
            sa.Column("next_step_actions", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        )
    if not _has_column(bind, "offer_letters", "plain_language_brief"):
        op.add_column(
            "offer_letters",
            sa.Column(
                "plain_language_brief", postgresql.JSONB(astext_type=sa.Text()), nullable=True
            ),
        )

    # ── applications: §2 student-side decision states ──
    if not _has_column(bind, "applications", "student_decision"):
        op.add_column(
            "applications", sa.Column("student_decision", sa.String(length=24), nullable=True)
        )


def downgrade() -> None:
    bind = op.get_bind()
    for col in (
        "plain_language_brief",
        "next_step_actions",
        "start_term_year",
        "start_term_season",
        "total_cost_estimate",
        "tuition_estimate",
        "scholarship_currency",
        "decision_date",
        "received_externally",
    ):
        if _has_column(bind, "offer_letters", col):
            op.drop_column("offer_letters", col)
    if _has_column(bind, "applications", "student_decision"):
        op.drop_column("applications", "student_decision")
