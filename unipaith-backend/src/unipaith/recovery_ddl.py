"""Idempotent schema-recovery DDL shared by the ``deepintelfix1`` migration and
``docker-entrypoint.sh``.

WHY THIS EXISTS
---------------
Several recent migrations (``aiclaim01``, ``deepintel1``, ``aivisamig01``) add
columns to the ``institutions`` / ``schools`` / ``programs`` /
``program_preferences`` / ``match_rationales`` tables with plain ``add_column``,
and ``deepintel1`` ends with an ORM-backed Python backfill. If such a migration
partially applies and then fails, the container entrypoint's last-ditch recovery
purges ``alembic_version`` and ``alembic stamp heads`` — marking the migration
*applied without running it*. The ORM maps every one of those columns, so each
``SELECT`` against those tables references a column that does not exist and 500s
the entire public browse + detail surface.

A plain ``alembic upgrade heads`` cannot self-heal that, AND it is unsafe to rely
on a tail migration alone: the intervening per-credential data migrations
(``uclapercrd1`` / ``jhupercrd1`` / …) call ``<univ>_profile.apply(session)`` +
``select(Institution)`` + ``backfill_program_preferences``, which select the
missing columns and FAIL before a tail recovery can run. So the entrypoint runs
this DDL *before* ``alembic upgrade`` — guaranteeing the schema is whole before
any migration or ORM query touches those tables, regardless of the stamped state.

Everything here is ``ADD COLUMN IF NOT EXISTS`` + existence-guarded FKs: a no-op
when present, a restore when missing. Nothing runs application code, so it can
never fail in a way that re-triggers the nuclear recovery.
"""

from __future__ import annotations

# (table, column-DDL) — every column a recent schema migration adds to a table
# the public read paths SELECT. ``IF NOT EXISTS`` makes each a safe no-op.
_COLUMNS: list[tuple[str, str]] = [
    # deepintel1 — institutions
    ("institutions", "profile_intelligence JSONB"),
    ("institutions", "profile_intelligence_version INTEGER NOT NULL DEFAULT 0"),
    ("institutions", "profile_intelligence_updated_at TIMESTAMPTZ"),
    # deepintel1 — institutions claim columns
    ("institutions", "is_claimed BOOLEAN NOT NULL DEFAULT false"),
    ("institutions", "claimed_at TIMESTAMPTZ"),
    ("institutions", "claimed_by_user_id UUID"),
    # deepintel1 — schools
    ("schools", "profile_intelligence JSONB"),
    ("schools", "profile_intelligence_version INTEGER NOT NULL DEFAULT 0"),
    ("schools", "profile_intelligence_updated_at TIMESTAMPTZ"),
    # aiclaim01 — schools claim columns
    ("schools", "is_claimed BOOLEAN NOT NULL DEFAULT false"),
    ("schools", "claimed_at TIMESTAMPTZ"),
    ("schools", "claimed_by_user_id UUID"),
    # deepintel1 — programs
    ("programs", "profile_intelligence JSONB"),
    ("programs", "profile_intelligence_version INTEGER NOT NULL DEFAULT 0"),
    ("programs", "profile_intelligence_updated_at TIMESTAMPTZ"),
    # aivisamig01 — programs
    ("programs", "sponsors_international BOOLEAN"),
    # aiclaim01 — programs claim columns
    ("programs", "is_claimed BOOLEAN NOT NULL DEFAULT false"),
    ("programs", "claimed_at TIMESTAMPTZ"),
    ("programs", "claimed_by_user_id UUID"),
    # deepintel1 — program_preferences
    ("program_preferences", "target_profile JSONB"),
    ("program_preferences", "preference_weights JSONB"),
    ("program_preferences", "provenance JSONB"),
    ("program_preferences", "standard_version INTEGER NOT NULL DEFAULT 1"),
    ("program_preferences", "derived_at TIMESTAMPTZ"),
    # deepintel1 — match_rationales
    ("match_rationales", "decision_brief JSONB"),
]


def _column_statements() -> list[str]:
    return [
        f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column_ddl}"
        for table, column_ddl in _COLUMNS
    ]


def _fk_statement(table: str) -> str:
    # Add a ``claimed_by_user_id`` → ``users(id)`` FK only when the table has no
    # FK on that column yet. Guarded on the column (not a fixed constraint name)
    # because the original constraints were auto-named differently per migration.
    return f"""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON tc.constraint_name = kcu.constraint_name
                 AND tc.table_schema = kcu.table_schema
                WHERE tc.table_name = '{table}'
                  AND tc.constraint_type = 'FOREIGN KEY'
                  AND kcu.column_name = 'claimed_by_user_id'
            ) THEN
                ALTER TABLE {table}
                ADD CONSTRAINT fk_{table}_claimed_by_user_id_users
                FOREIGN KEY (claimed_by_user_id) REFERENCES users (id)
                ON DELETE SET NULL;
            END IF;
        END $$;
    """


# Ordered list of idempotent statements: columns first, then the guarded FKs.
RECOVERY_STATEMENTS: list[str] = _column_statements() + [
    _fk_statement(t) for t in ("institutions", "schools", "programs")
]
