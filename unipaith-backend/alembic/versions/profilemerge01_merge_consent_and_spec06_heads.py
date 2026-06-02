"""merge the consent_training (Universal Profile Data Rights) head with the
spec-06 (program feature_version + ai agents) head.

Both branched off p3q5r7s9t1u3 concurrently; this no-op merge unifies them
into a single Alembic head so the ECS backend-deploy gate
(test_alembic_has_single_head) passes.
"""

revision = "profilemerge01"
down_revision = ("a6c1f0d2e3b4", "e2d4f6a8b0c2")  # pragma: allowlist secret
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
