"""Seed US-News National Universities ranks 76-109 (batch 2) at institution level.

Institution-level seed of the next US-News national universities (verified
deterministic data: IPEDS / Urban Institute directory + admissions + grad rates;
factual templated description). NO programs / earnings / _standard stamp -- the
enrichment routine deepens each to gold (full catalog, reviews, earnings, more
photos). Campus photos are verified Wikimedia Commons files (credit checked) or
omitted. Data in the sibling seed300b2_data.json. Idempotent: skips existing names.

Revision ID: seed300b2
Revises: seed300b1
"""

import json
import pathlib
import uuid

import sqlalchemy as sa

from alembic import op

revision = "seed300b2"
down_revision = "seed300b1"
branch_labels = None
depends_on = None

_DATA = pathlib.Path(__file__).with_name("seed300b2_data.json")
UNIVERSITIES = json.loads(_DATA.read_text(encoding="utf-8"))


def _slug_email(name: str, unit_id: int) -> str:
    # Include the UNITID so similarly-named institutions (e.g. the UC campuses,
    # which share the same 24-char prefix) never collide on the unique email.
    base = "".join(c for c in name.lower() if c.isalnum())[:24]
    return f"admissions+{base}-{unit_id}@seed.unipaith.co"


def upgrade() -> None:
    conn = op.get_bind()
    for u in UNIVERSITIES:
        if conn.execute(
            sa.text("SELECT 1 FROM institutions WHERE name = :n"), {"n": u["name"]}
        ).first():
            continue
        admin_id = str(uuid.uuid4())
        inst_id = str(uuid.uuid4())
        conn.execute(
            sa.text(
                "INSERT INTO users "
                "(id, email, cognito_sub, role, is_active, created_at, updated_at) "
                "VALUES (:id, :email, :cs, 'institution_admin', true, now(), now())"
            ),
            {
                "id": admin_id,
                "email": _slug_email(u["name"], u["unit_id"]),
                "cs": "seed-" + uuid.uuid4().hex[:12],
            },
        )
        conn.execute(
            sa.text(
                "INSERT INTO institutions "
                "(id, admin_user_id, name, type, country, city, region, "
                "student_body_size, is_verified, setup_complete, description_text, "
                "media_gallery, ranking_data, school_outcomes, created_at, updated_at) "
                "VALUES (:id, :admin, :name, 'university', 'United States', :city, "
                ":region, :size, true, true, :descr, CAST(:gallery AS jsonb), "
                "CAST(:ranking AS jsonb), CAST(:outcomes AS jsonb), now(), now())"
            ),
            {
                "id": inst_id,
                "admin": admin_id,
                "name": u["name"],
                "city": u.get("city"),
                "region": u.get("region"),
                "size": u.get("size"),
                "descr": u.get("description"),
                "gallery": json.dumps(u.get("media_gallery")),
                "ranking": json.dumps(u.get("ranking_data") or {}),
                "outcomes": json.dumps(u.get("school_outcomes") or {}),
            },
        )


def downgrade() -> None:
    conn = op.get_bind()
    for u in UNIVERSITIES:
        row = conn.execute(
            sa.text("SELECT id, admin_user_id FROM institutions WHERE name = :n"),
            {"n": u["name"]},
        ).first()
        if not row:
            continue
        conn.execute(sa.text("DELETE FROM programs WHERE institution_id = :i"), {"i": row[0]})
        conn.execute(sa.text("DELETE FROM institutions WHERE id = :i"), {"i": row[0]})
        conn.execute(sa.text("DELETE FROM users WHERE id = :a"), {"a": row[1]})
