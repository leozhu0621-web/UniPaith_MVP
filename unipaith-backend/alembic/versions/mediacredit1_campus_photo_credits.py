"""Backfill campus-photo attribution (school_outcomes.media_credit) on every
enriched institution that leads its media_gallery with a campus photo. The
detail-page hero renders this value as a "Photo: …" caption. Each credit is
VERIFIED via the image's Wikimedia Commons file page (Artist + license) — never
fabricated.

Targeted JSONB backfill (jsonb_set on the single `media_credit` key) so it touches
no profile data module: those are owned and continuously edited by the enrichment
routine, and the enrich-profile skill now requires the routine to set media_credit
itself on future runs. Each profile's apply() shallow-merges
`{**existing, **SCHOOL_OUTCOMES}` (SCHOOL_OUTCOMES carries no media_credit key), so
this backfilled value survives later re-applies. Idempotent; no-ops where an
institution is absent (fresh/CI databases).

Revision ID: mediacredit1
Revises: mitfeeds1
"""

from sqlalchemy import text

from alembic import op
from unipaith.data import (
    berkeley_profile,
    caltech_profile,
    carnegie_mellon_profile,
    chicago_profile,
    columbia_profile,
    cornell_profile,
    duke_profile,
    harvard_profile,
    mit_profile,
    penn_profile,
    princeton_profile,
    rice_profile,
    stanford_profile,
    yale_profile,
)

revision = "mediacredit1"
down_revision = "mitfeeds1"
branch_labels = None
depends_on = None

# module → verified credit (Wikimedia Commons Artist + LicenseShortName, read off
# each file page). The institution name comes from the module so it never drifts.
_CREDITS = {
    berkeley_profile: "Wikimedia Commons / Wil540 art (CC BY-SA 4.0)",
    caltech_profile: "Wikimedia Commons / Antony-22 (CC BY-SA 4.0)",
    carnegie_mellon_profile: "Wikimedia Commons / Jiuguang Wang (CC BY-SA 2.0)",
    chicago_profile: "Wikimedia Commons / Michael Barera (CC BY-SA 4.0)",
    columbia_profile: "Wikimedia Commons / Bitterteayen (CC BY-SA 4.0)",
    cornell_profile: "Wikimedia Commons / Eustress (CC BY-SA 4.0)",
    duke_profile: "Wikimedia Commons / Sdkb (CC BY-SA 4.0)",
    harvard_profile: "Wikimedia Commons / Gunnar Klack (CC BY-SA 4.0)",
    mit_profile: "Wikimedia Commons / Peacearth (CC BY-SA 4.0)",
    penn_profile: "Wikimedia Commons / Detroit Publishing Co. (public domain)",
    princeton_profile: "Wikimedia Commons / Smallbones (CC0)",
    rice_profile: "Wikimedia Commons / Daderot (public domain)",
    stanford_profile: "Wikimedia Commons / Steve Jurvetson (CC BY 2.0)",
    yale_profile: "Wikimedia Commons / ajay_suresh (CC BY 2.0)",
}

_SET = text(
    "UPDATE institutions SET school_outcomes = jsonb_set("
    "coalesce(school_outcomes, '{}'::jsonb), '{media_credit}', "
    "to_jsonb(cast(:cred AS text)), true) "
    "WHERE name = :name"
)
_UNSET = text(
    "UPDATE institutions SET school_outcomes = school_outcomes - 'media_credit' WHERE name = :name"
)


def upgrade() -> None:
    bind = op.get_bind()
    for module, cred in _CREDITS.items():
        bind.execute(_SET, {"cred": cred, "name": module.INSTITUTION_NAME})


def downgrade() -> None:
    bind = op.get_bind()
    for module in _CREDITS:
        bind.execute(_UNSET, {"name": module.INSTITUTION_NAME})
