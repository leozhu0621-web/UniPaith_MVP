"""backfill chat folders + name existing discovery threads

Idempotent. Seeds the 8 preset folders per student and names each existing
discovery thread as a chat_session filed under the matching topic folder.

Revision ID: chatsessbf1
Revises: chatsess1
Create Date: 2026-06-19

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "chatsessbf1"  # pragma: allowlist secret
down_revision: str | None = "chatsess1"  # pragma: allowlist secret
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_PRESETS = [
    ("profile", "Profile", "discovery", 0),
    ("goals", "Goals", "discovery", 1),
    ("needs", "Needs", "discovery", 2),
    ("strategy", "Strategy", "recommendation", 3),
    ("schools", "Schools", "recommendation", 4),
    ("connect", "Connect", "application", 5),
    ("prepare", "Prepare", "application", 6),
    ("manage", "Manage", "application", 7),
]
_TRACK_TITLE = {
    "profile": "Your story",
    "goals": "Your goals",
    "needs": "What you need",
    "discovery": "Getting to know you",
}


def upgrade() -> None:
    bind = op.get_bind()
    sids = [r[0] for r in bind.execute(sa.text("SELECT id FROM student_profiles"))]
    for sid in sids:
        for key, name, stage, order in _PRESETS:
            bind.execute(
                sa.text(
                    "INSERT INTO chat_folders"
                    " (id, student_id, name, kind, topic_key, stage, sort_order)"
                    " VALUES (gen_random_uuid(), :sid, :n, 'preset', :k, :st, :o)"
                    " ON CONFLICT (student_id, topic_key) DO NOTHING"
                ),
                {"sid": sid, "n": name, "k": key, "st": stage, "o": order},
            )
    rows = list(
        bind.execute(
            sa.text("SELECT id, student_id, track, agent_session_id FROM discovery_sessions")
        )
    )
    for _did, sid, track, agent_sid in rows:
        topic = (
            track if track in ("profile", "goals", "needs") else "profile"
        )  # 'discovery' → profile
        title = _TRACK_TITLE.get(track, "Session")
        fid = bind.execute(
            sa.text("SELECT id FROM chat_folders WHERE student_id=:sid AND topic_key=:k"),
            {"sid": sid, "k": topic},
        ).scalar()
        if fid is None:
            continue
        exists = bind.execute(
            sa.text(
                "SELECT 1 FROM chat_sessions WHERE student_id=:sid"
                " AND agent_session_id IS NOT DISTINCT FROM :a AND title=:t"
            ),
            {"sid": sid, "a": agent_sid, "t": title},
        ).scalar()
        if exists:
            continue
        bind.execute(
            sa.text(
                "INSERT INTO chat_sessions"
                " (id, student_id, folder_id, title, origin_kind, agent_session_id)"
                " VALUES (gen_random_uuid(), :sid, :fid, :t, 'manual', :a)"
            ),
            {"sid": sid, "fid": fid, "t": title, "a": agent_sid},
        )


def downgrade() -> None:
    pass  # data backfill — non-reversible
