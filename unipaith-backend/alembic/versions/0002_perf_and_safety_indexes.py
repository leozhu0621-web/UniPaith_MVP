"""perf_and_safety_indexes

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-01

Adds composite indexes for matching and messaging hot paths.
This migration is additive-only and does not remove user data.
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_historical_outcomes_program_outcome",
        "historical_outcomes",
        ["program_id", "outcome"],
        unique=False,
    )
    op.create_index(
        "ix_target_segments_program_active",
        "target_segments",
        ["program_id", "is_active"],
        unique=False,
    )
    op.create_index(
        "ix_messages_conversation_read_sender",
        "messages",
        ["conversation_id", "read_at", "sender_id"],
        unique=False,
    )
    op.create_index(
        "ix_conversations_student_last_message",
        "conversations",
        ["student_id", "last_message_at"],
        unique=False,
    )
    op.create_index(
        "ix_conversations_institution_last_message",
        "conversations",
        ["institution_id", "last_message_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_conversations_institution_last_message", table_name="conversations")
    op.drop_index("ix_conversations_student_last_message", table_name="conversations")
    op.drop_index("ix_messages_conversation_read_sender", table_name="messages")
    op.drop_index("ix_target_segments_program_active", table_name="target_segments")
    op.drop_index("ix_historical_outcomes_program_outcome", table_name="historical_outcomes")
