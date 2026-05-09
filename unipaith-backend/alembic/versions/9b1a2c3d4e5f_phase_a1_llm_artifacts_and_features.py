"""Phase A1 — LLM-only storage: feature vectors, AI turn metering, match-result split.

The typed Discovery artifacts (student_goals, student_needs, student_identity)
ship in #113 (revision 9b3c5d7e8f1a). This migration adds only the LLM-side
companions:

  - student_feature_vectors  — voyage-3-large embedding + sparse feature dict
                               (the ML matcher's input, written by the
                               A4 Feature Emitter at end-of-Discovery)
  - ai_turns                 — per-call cost / latency metering ledger;
                               written by `unipaith.ai.client` only
  - match_results extension  — adds fitness, confidence, fitness_components,
                               uncertainty_components, profile_version
                               (the existing single `score` column is kept
                               during cutover; B2 removes it)
  - match_rationales         — cached rationale text keyed by
                               (student, program, profile_version, program_version)
                               for the A5 Rationale agent
  - ai_safety_incidents      — incident log for guardrail breaks, hallucinations,
                               cost-cap hits

Revision ID: 9b1a2c3d4e5f
Revises: 9b3c5d7e8f1a
Create Date: 2026-05-09 16:00:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "9b1a2c3d4e5f"  # pragma: allowlist secret
down_revision = "9b3c5d7e8f1a"  # pragma: allowlist secret
branch_labels = None
depends_on = None


def _has_pgvector(bind) -> bool:
    """Runtime check — production has pgvector; some dev DBs don't."""
    return bool(
        bind.execute(sa.text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")).scalar()
    )


def upgrade() -> None:
    bind = op.get_bind()
    pgvector = _has_pgvector(bind)

    # ── student_feature_vectors ──────────────────────────────────────────
    # Production: VECTOR(1024) (pgvector). Dev/CI without pgvector: JSONB.
    if pgvector:
        op.execute(
            """
            CREATE TABLE student_feature_vectors (
                student_id UUID PRIMARY KEY
                    REFERENCES student_profiles(id) ON DELETE CASCADE,
                profile_version INTEGER NOT NULL DEFAULT 1,
                embedding VECTOR(1024),
                sparse_features JSONB NOT NULL DEFAULT '{}',
                applicant_summary TEXT NOT NULL DEFAULT '',
                emitted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        # ivfflat index — small list count for cold start; tune lists ≈ rows/1000
        # once we have volume.
        op.execute(
            """
            CREATE INDEX ix_student_feature_vectors_embedding
            ON student_feature_vectors
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 32)
            """
        )
    else:
        op.create_table(
            "student_feature_vectors",
            sa.Column(
                "student_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("student_profiles.id", ondelete="CASCADE"),
                primary_key=True,
            ),
            sa.Column("profile_version", sa.Integer, nullable=False, server_default="1"),
            sa.Column("embedding", postgresql.JSONB, nullable=True),
            sa.Column(
                "sparse_features",
                postgresql.JSONB,
                nullable=False,
                server_default="{}",
            ),
            sa.Column("applicant_summary", sa.Text, nullable=False, server_default=""),
            sa.Column(
                "emitted_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
        )

    # ── ai_turns ─────────────────────────────────────────────────────────
    op.create_table(
        "ai_turns",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "student_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("student_profiles.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "discovery_message_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("discovery_messages.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("agent", sa.String(30), nullable=False),
        sa.Column("surface", sa.String(40), nullable=True),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("model", sa.String(60), nullable=False),
        sa.Column("input_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("cache_read_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "cache_creation_tokens",
            sa.Integer,
            nullable=False,
            server_default="0",
        ),
        sa.Column("cost_usd", sa.Numeric(10, 6), nullable=False, server_default="0"),
        sa.Column("latency_ms", sa.Integer, nullable=True),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "role IN ('user','assistant','tool','system')",
            name="ck_ai_turns_role",
        ),
        sa.CheckConstraint(
            "agent IN ('orchestrator','extractor','validator','feature_emitter',"
            "'rationale','workshop_coach','workshop_judge','embedding')",
            name="ck_ai_turns_agent",
        ),
    )
    op.create_index("ix_ai_turns_student_created", "ai_turns", ["student_id", "created_at"])
    op.create_index("ix_ai_turns_agent_created", "ai_turns", ["agent", "created_at"])

    # ── match_results extension ──────────────────────────────────────────
    # Existing `score` is preserved during cutover; B2 removes it after the
    # new scorer is fully wired. New columns are nullable so existing rows
    # survive without backfill.
    insp = sa.inspect(bind)
    if "match_results" in insp.get_table_names():
        existing_cols = {c["name"] for c in insp.get_columns("match_results")}
        with op.batch_alter_table("match_results") as batch:
            if "fitness" not in existing_cols:
                batch.add_column(sa.Column("fitness", sa.Numeric(4, 3), nullable=True))
            if "confidence" not in existing_cols:
                batch.add_column(sa.Column("confidence", sa.Numeric(4, 3), nullable=True))
            if "fitness_components" not in existing_cols:
                batch.add_column(sa.Column("fitness_components", postgresql.JSONB, nullable=True))
            if "uncertainty_components" not in existing_cols:
                batch.add_column(
                    sa.Column("uncertainty_components", postgresql.JSONB, nullable=True)
                )
            if "profile_version" not in existing_cols:
                batch.add_column(sa.Column("profile_version", sa.Integer, nullable=True))

    # ── match_rationales (cache) ─────────────────────────────────────────
    op.create_table(
        "match_rationales",
        sa.Column(
            "student_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("student_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "program_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("programs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("profile_version", sa.Integer, nullable=False),
        sa.Column("program_version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("rationale_text", sa.Text, nullable=False),
        sa.Column("cited_student_fields", postgresql.JSONB, nullable=True),
        sa.Column("cited_program_fields", postgresql.JSONB, nullable=True),
        sa.Column(
            "generated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("student_id", "program_id", "profile_version", "program_version"),
    )

    # ── ai_safety_incidents ──────────────────────────────────────────────
    op.create_table(
        "ai_safety_incidents",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "student_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("student_profiles.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("agent", sa.String(30), nullable=False),
        # kind values: workshop_generation_leak, json_parse_failure,
        # rationale_hallucination, cost_cap_hit, etc.
        sa.Column("kind", sa.String(60), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False, server_default="warn"),
        sa.Column("payload", postgresql.JSONB, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "severity IN ('info','warn','error','blocking')",
            name="ck_ai_safety_severity",
        ),
    )
    op.create_index(
        "ix_ai_safety_incidents_kind_created",
        "ai_safety_incidents",
        ["kind", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_ai_safety_incidents_kind_created", table_name="ai_safety_incidents")
    op.drop_table("ai_safety_incidents")

    op.drop_table("match_rationales")

    bind = op.get_bind()
    insp = sa.inspect(bind)
    if "match_results" in insp.get_table_names():
        existing_cols = {c["name"] for c in insp.get_columns("match_results")}
        with op.batch_alter_table("match_results") as batch:
            for col in (
                "profile_version",
                "uncertainty_components",
                "fitness_components",
                "confidence",
                "fitness",
            ):
                if col in existing_cols:
                    batch.drop_column(col)

    op.drop_index("ix_ai_turns_agent_created", table_name="ai_turns")
    op.drop_index("ix_ai_turns_student_created", table_name="ai_turns")
    op.drop_table("ai_turns")

    op.execute("DROP INDEX IF EXISTS ix_student_feature_vectors_embedding")
    op.execute("DROP TABLE IF EXISTS student_feature_vectors")
