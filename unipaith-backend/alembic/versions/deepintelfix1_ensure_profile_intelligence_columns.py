"""Recovery — idempotently ensure the ``deepintel1`` (+ ``aivisamig01``) columns
exist on ``institutions`` / ``schools`` / ``programs`` / ``program_preferences`` /
``match_rationales``.

WHY: ``deepintel1_profile_intelligence`` adds those columns with plain
``op.add_column`` (no ``IF NOT EXISTS``) and ends with a Python backfill. If that
migration partially applies and then fails (a transient blip, a racing dual head,
or the backfill raising), the container entrypoint's last-ditch recovery purges
``alembic_version`` and ``alembic stamp heads`` — marking ``deepintel1`` *applied
without running it*. The ORM (``models/institution.py`` etc.) now maps
``profile_intelligence`` / ``is_claimed`` / ``sponsors_international`` / … so EVERY
``SELECT`` against institutions/programs references a column that does not exist,
500-ing the entire public browse + detail surface.

A normal ``alembic upgrade heads`` cannot self-heal that state (the migration is
stamped, so it is skipped). This recovery is a NEW head, so it always runs, and it
is pure ``ADD COLUMN IF NOT EXISTS`` + a guarded FK — safe whether the columns are
already present (no-op) or missing (restores them). No backfill, no service calls,
nothing that can fail and re-trigger the nuclear recovery.

Revision ID: deepintelfix1
Revises: jhupercrd1
Create Date: 2026-06-21

"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "deepintelfix1"  # pragma: allowlist secret
down_revision = "jhupercrd1"  # pragma: allowlist secret
branch_labels = None
depends_on = None


# (table, column DDL) — every column a recent schema migration adds to a table the
# public read paths SELECT. ``IF NOT EXISTS`` makes each a safe no-op when present.
_COLUMNS: list[tuple[str, str]] = [
    # deepintel1 — institutions
    ("institutions", "profile_intelligence JSONB"),
    ("institutions", "profile_intelligence_version INTEGER NOT NULL DEFAULT 0"),
    ("institutions", "profile_intelligence_updated_at TIMESTAMPTZ"),
    ("institutions", "is_claimed BOOLEAN NOT NULL DEFAULT false"),
    ("institutions", "claimed_at TIMESTAMPTZ"),
    ("institutions", "claimed_by_user_id UUID"),
    # deepintel1 — schools
    ("schools", "profile_intelligence JSONB"),
    ("schools", "profile_intelligence_version INTEGER NOT NULL DEFAULT 0"),
    ("schools", "profile_intelligence_updated_at TIMESTAMPTZ"),
    # deepintel1 — programs
    ("programs", "profile_intelligence JSONB"),
    ("programs", "profile_intelligence_version INTEGER NOT NULL DEFAULT 0"),
    ("programs", "profile_intelligence_updated_at TIMESTAMPTZ"),
    # aivisamig01 — programs
    ("programs", "sponsors_international BOOLEAN"),
    # deepintel1 — program_preferences
    ("program_preferences", "target_profile JSONB"),
    ("program_preferences", "preference_weights JSONB"),
    ("program_preferences", "provenance JSONB"),
    ("program_preferences", "standard_version INTEGER NOT NULL DEFAULT 1"),
    ("program_preferences", "derived_at TIMESTAMPTZ"),
    # deepintel1 — match_rationales
    ("match_rationales", "decision_brief JSONB"),
]


def upgrade() -> None:
    for table, column_ddl in _COLUMNS:
        op.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column_ddl}")

    # deepintel1's FK on institutions.claimed_by_user_id — add only if absent.
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'fk_institutions_claimed_by_user_id_users'
            ) THEN
                ALTER TABLE institutions
                ADD CONSTRAINT fk_institutions_claimed_by_user_id_users
                FOREIGN KEY (claimed_by_user_id) REFERENCES users (id)
                ON DELETE SET NULL;
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    # Recovery-only: never drop columns that ``deepintel1`` owns (dropping them
    # would re-break the read paths). Intentionally a no-op.
    pass
