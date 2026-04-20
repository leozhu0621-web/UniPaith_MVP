"""add schools table

Revision ID: n4o5p6q7r8s9
Revises: 4c9d6e1a8b3f
Create Date: 2026-04-15 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "n4o5p6q7r8s9"
down_revision = "4c9d6e1a8b3f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create schools table
    op.create_table(
        "schools",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("institution_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description_text", sa.Text, nullable=True),
        sa.Column("media_urls", postgresql.JSONB, nullable=True),
        sa.Column("logo_url", sa.String(1000), nullable=True),
        sa.Column("sort_order", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("institution_id", "name", name="uq_schools_institution_name"),
    )
    op.create_index("ix_schools_institution", "schools", ["institution_id"])

    # Add school_id FK to programs
    op.add_column("programs", sa.Column("school_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_programs_school_id",
        "programs",
        "schools",
        ["school_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_programs_school_id", "programs", ["school_id"])

    # --- Data migration: create School records from existing department strings ---
    conn = op.get_bind()

    # Get all unique institution_id + department pairs
    rows = conn.execute(
        sa.text("""
            SELECT DISTINCT institution_id, department
            FROM programs
            WHERE department IS NOT NULL AND department != ''
            ORDER BY institution_id, department
        """)
    ).fetchall()

    # Create a school for each unique department
    for i, (inst_id, dept_name) in enumerate(rows):
        conn.execute(
            sa.text("""
                INSERT INTO schools (id, institution_id, name, sort_order, created_at, updated_at)
                VALUES (gen_random_uuid(), :inst_id, :name, :sort_order, now(), now())
            """),
            {"inst_id": inst_id, "name": dept_name, "sort_order": i},
        )

    # Link programs to their schools
    conn.execute(
        sa.text("""
            UPDATE programs p
            SET school_id = s.id
            FROM schools s
            WHERE p.institution_id = s.institution_id
              AND p.department = s.name
        """)
    )


def downgrade() -> None:
    op.drop_index("ix_programs_school_id", "programs")
    op.drop_constraint("fk_programs_school_id", "programs", type_="foreignkey")
    op.drop_column("programs", "school_id")
    op.drop_index("ix_schools_institution", "schools")
    op.drop_table("schools")
