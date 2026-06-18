"""Seed the next 12 US-News National Universities at institution level.

Creates institution + admin user + verified flagship programs + a verified
campus-photo gallery for the universities ranked just below the seeded top-28
(Brown, Dartmouth, Vanderbilt, Notre Dame, WashU, Georgetown, Emory, UVA, UNC,
U-Florida, UC Davis, UC Irvine). Institution level only -- the enrichment routine
deepens each to gold (full catalog, reviews, more photos) on later runs;
intentionally NO _standard stamp so the routine treats them as not-yet-enriched.
Every value verified (College Scorecard / IPEDS / Wikipedia / Wikimedia Commons);
unverifiable fields omitted, never guessed. Data lives in the sibling
seed12univ1_data.json. Idempotent: skips any institution whose name already exists.

Revision ID: seed12univ1
Revises: ucsdprof6
"""

import json
import pathlib
import uuid

import sqlalchemy as sa

from alembic import op

revision = "seed12univ1"
down_revision = "ucsdprof6"
branch_labels = None
depends_on = None

_DATA = pathlib.Path(__file__).with_name("seed12univ1_data.json")
UNIVERSITIES = json.loads(_DATA.read_text(encoding="utf-8"))


def _slug_email(name: str) -> str:
    base = "".join(c for c in name.lower() if c.isalnum())[:24]
    return f"admissions+{base}@seed.unipaith.co"


def upgrade() -> None:
    conn = op.get_bind()
    for u in UNIVERSITIES:
        if conn.execute(
            sa.text("SELECT 1 FROM institutions WHERE name = :n"), {"n": u["name"]}
        ).first():
            continue  # idempotent
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
                "email": _slug_email(u["name"]),
                "cs": "seed-" + uuid.uuid4().hex[:12],
            },
        )
        conn.execute(
            sa.text(
                "INSERT INTO institutions "
                "(id, admin_user_id, name, type, country, city, region, "
                "student_body_size, founded_year, is_verified, setup_complete, "
                "description_text, media_gallery, ranking_data, school_outcomes, "
                "created_at, updated_at) VALUES "
                "(:id, :admin, :name, 'university', 'United States', :city, :region, "
                ":size, :founded, true, true, :descr, CAST(:gallery AS jsonb), "
                "CAST(:ranking AS jsonb), CAST(:outcomes AS jsonb), now(), now())"
            ),
            {
                "id": inst_id,
                "admin": admin_id,
                "name": u["name"],
                "city": u.get("city"),
                "region": u.get("region"),
                "size": u.get("size"),
                "founded": u.get("founded"),
                "descr": u.get("description"),
                "gallery": json.dumps(u.get("media_gallery")),
                "ranking": json.dumps(u.get("ranking_data") or {}),
                "outcomes": json.dumps(u.get("school_outcomes") or {}),
            },
        )
        for p in u.get("programs", []):
            conn.execute(
                sa.text(
                    "INSERT INTO programs "
                    "(id, institution_id, program_name, degree_type, cip_code, "
                    "is_published, catalog_source, source_url, created_at, updated_at) "
                    "VALUES (:id, :inst, :pn, :dt, :cip, true, "
                    "'institution_verified', :src, now(), now())"
                ),
                {
                    "id": str(uuid.uuid4()),
                    "inst": inst_id,
                    "pn": p["name"],
                    "dt": p["degree"],
                    "cip": p.get("cip"),
                    "src": "https://collegescorecard.ed.gov/school/?" + str(u["unit_id"]),
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
