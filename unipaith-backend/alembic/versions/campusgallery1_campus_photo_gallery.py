"""Campus-photo gallery: verified multi-photo school_outcomes.campus_photos.

Data-only backfill for the 14 universities that already carry a verified campus
hero. Each entry is {url, credit} — the credit verified against the Wikimedia
Commons file metadata (extmetadata Artist + LicenseShortName); only freely-
licensed landscape photos. The detail-page hero opens these in a lightbox; the
explore card uses [0]. The existing single hero (media_gallery[0] +
media_credit) is prepended when it isn't already in the list, so the current
hero stays first. Touches ZERO data-module files (jsonb update only) to avoid
conflicting with the enrichment routine's active edits to data/*_profile.py.

Revision ID: campusgallery1
Revises: uni_agent_sess_a1b2c3
"""

import json
import re

import sqlalchemy as sa

from alembic import op

revision = "campusgallery1"
down_revision = "uni_agent_sess_a1b2c3"
branch_labels = None
depends_on = None


CAMPUS_PHOTOS: dict[str, list[dict]] = {
    "Massachusetts Institute of Technology": [
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/MIT_Building_10_and_"
                "the_Great_Dome%2C_Cambridge_MA.jpg/1920px-MIT_Building_10_and_the_Great_Dome%2"
                "C_Cambridge_MA.jpg"
            ),
            "credit": "Wikimedia Commons / John Phelan (CC BY 3.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/9/94/MIT_Killian_Court.jp"
                "g/1920px-MIT_Killian_Court.jpg"
            ),
            "credit": "Wikimedia Commons / Madcoverboy (CC BY-SA 3.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/Great_Dome%2C_Massac"
                "husetts_Institute_of_Technology%2C_Aug_2019_%283_by_2%29.jpg/1920px-Great_Dome"
                "%2C_Massachusetts_Institute_of_Technology%2C_Aug_2019_%283_by_2%29.jpg"
            ),
            "credit": "Wikimedia Commons / Mys 721tx (CC BY-SA 3.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3d/MIT_Main_Campus_Aeri"
                "al.jpg/1920px-MIT_Main_Campus_Aerial.jpg"
            ),
            "credit": "Wikimedia Commons / DrKenneth (CC BY 3.0)",
        },
    ],
    "California Institute of Technology": [
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/1/14/Athenaeum_Caltech_20"
                "20a.jpg/1920px-Athenaeum_Caltech_2020a.jpg"
            ),
            "credit": "Wikimedia Commons / Antony-22 (CC BY-SA 4.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/0/03/Crellin-Gates_Arcade"
                "_Caltech_2022.jpg/1920px-Crellin-Gates_Arcade_Caltech_2022.jpg"
            ),
            "credit": "Wikimedia Commons / Antony-22 (CC BY-SA 4.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d7/Dabney_Hall_Courtyar"
                "d_Caltech_2017.jpg/1920px-Dabney_Hall_Courtyard_Caltech_2017.jpg"
            ),
            "credit": "Wikimedia Commons / Antony-22 (CC BY-SA 4.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/Caltech_Pond.jpg/192"
                "0px-Caltech_Pond.jpg"
            ),
            "credit": "Wikimedia Commons / Boothsift (CC BY-SA 3.0)",
        },
    ],
    "Harvard University": [
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/a/af/Harvard_University_a"
                "erial_20250415.jpg/1920px-Harvard_University_aerial_20250415.jpg"
            ),
            "credit": "Wikimedia Commons / Nickknack00 (CC BY-SA 4.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/c/cf/Harvard_Yard_in_autu"
                "mn%2C_Boston%2C_Massachusetts%2C_2015.jpg/1920px-Harvard_Yard_in_autumn%2C_Bos"
                "ton%2C_Massachusetts%2C_2015.jpg"
            ),
            "credit": "Wikimedia Commons / Nina R (CC BY 2.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/Harvard_Yard_and_Mem"
                "orial_Church_during_a_snowstorm_%2851307020933%29.jpg/1920px-Harvard_Yard_and_"
                "Memorial_Church_during_a_snowstorm_%2851307020933%29.jpg"
            ),
            "credit": "Wikimedia Commons / Chris Rycroft (CC BY 2.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e5/Autumn_Days_in_Harva"
                "rd_Yard_%284092139642%29.jpg/1920px-Autumn_Days_in_Harvard_Yard_%284092139642%"
                "29.jpg"
            ),
            "credit": "Wikimedia Commons / Tim Sackton (CC BY-SA 2.0)",
        },
    ],
    "Columbia University in the City of New York": [
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5f/2014_Columbia_Univer"
                "sity_Low_Memorial_Library.jpg/1920px-2014_Columbia_University_Low_Memorial_Lib"
                "rary.jpg"
            ),
            "credit": "Wikimedia Commons / Beyond My Ken (CC BY-SA 4.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/2014_Columbia_Univer"
                "sity_Low_Memorial_Library_from_front.jpg/1920px-2014_Columbia_University_Low_M"
                "emorial_Library_from_front.jpg"
            ),
            "credit": "Wikimedia Commons / Beyond My Ken (CC BY-SA 4.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/4/40/2014_Columbia_Univer"
                "sity_Morningside_Heights_campus_from_northeast.jpg/1920px-2014_Columbia_Univer"
                "sity_Morningside_Heights_campus_from_northeast.jpg"
            ),
            "credit": "Wikimedia Commons / Beyond My Ken (CC BY-SA 4.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/9/98/2014_Columbia_University_B"
                "utler_Library_from_front.jpg"
            ),
            "credit": "Wikimedia Commons / Beyond My Ken (CC BY-SA 4.0)",
        },
    ],
    "Stanford University": [
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/a/aa/Stanford_main_quad_s"
                "unset.jpg/1920px-Stanford_main_quad_sunset.jpg"
            ),
            "credit": "Wikimedia Commons / Suiren2022 (CC BY-SA 4.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a9/Orange_skies_day_-_S"
                "tanford_Hoover_Tower.jpg/1920px-Orange_skies_day_-_Stanford_Hoover_Tower.jpg"
            ),
            "credit": "Wikimedia Commons / Suiren2022 (CC BY-SA 4.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8c/Hoover_tower_from_Ja"
                "ne_Stanford_Way.jpg/1920px-Hoover_tower_from_Jane_Stanford_Way.jpg"
            ),
            "credit": "Wikimedia Commons / Suiren2022 (CC BY-SA 4.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/9/94/Welcome_banner_at_Pa"
                "lm_Dr_entrance%2C_Stanford_University.jpg/1920px-Welcome_banner_at_Palm_Dr_ent"
                "rance%2C_Stanford_University.jpg"
            ),
            "credit": "Wikimedia Commons / Suiren2022 (CC BY-SA 4.0)",
        },
    ],
    "Yale University": [
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c2/2014-04-17-Yale-Old-"
                "Campus-Courtyard-Harkness-Tower.jpg/1920px-2014-04-17-Yale-Old-Campus-Courtyar"
                "d-Harkness-Tower.jpg"
            ),
            "credit": "Wikimedia Commons / Gunnar Klack (CC BY-SA 4.0)",
        },
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/a/ae/Harkness_Tower_Yale_Fall_2014.jpg",
            "credit": "Wikimedia Commons / Hrichardson (WMF) (CC BY-SA 4.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/6/65/Branford_Court_and_H"
                "arkness_Tower%2C_Yale_University%2C_New_Haven%2C_Conn_%2861775%29.jpg/1920px-B"
                "ranford_Court_and_Harkness_Tower%2C_Yale_University%2C_New_Haven%2C_Conn_%2861"
                "775%29.jpg"
            ),
            "credit": "Wikimedia Commons / Tichnor Brothers (public domain)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f2/Harkness_Tower_-_Yal"
                "e_University_%2854106458290%29.jpg/1920px-Harkness_Tower_-_Yale_University_%28"
                "54106458290%29.jpg"
            ),
            "credit": "Wikimedia Commons / ajay_suresh (CC BY 2.0)",
        },
    ],
    "Princeton University": [
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4f/Nassau_Hall%2C_Princ"
                "eton_University%2C_Princeton_NJ.jpg/1920px-Nassau_Hall%2C_Princeton_University"
                "%2C_Princeton_NJ.jpg"
            ),
            "credit": "Wikimedia Commons / John Phelan (CC BY-SA 3.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/0/07/Cannon_Green_and_Nas"
                "sau_Hall%2C_Princeton_University.jpg/1920px-Cannon_Green_and_Nassau_Hall%2C_Pr"
                "inceton_University.jpg"
            ),
            "credit": "Wikimedia Commons / Ken Lund (CC BY-SA 2.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/b/bb/Nassau_Hall_-_Prince"
                "ton_University_%2855144981395%29.jpg/1920px-Nassau_Hall_-_Princeton_University"
                "_%2855144981395%29.jpg"
            ),
            "credit": "Wikimedia Commons / ajay_suresh (CC BY 4.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/0/04/Princeton_Campus.jpg"
                "/1920px-Princeton_Campus.jpg"
            ),
            "credit": "Wikimedia Commons / Photo: Andreas Praefcke (CC BY 3.0)",
        },
    ],
    "Cornell University": [
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/9/97/Cornell_University_-"
                "_Uris_Library%2C_McGraw_Tower_and_Olin_Library.jpg/1920px-Cornell_University_-"
                "_Uris_Library%2C_McGraw_Tower_and_Olin_Library.jpg"
            ),
            "credit": "Wikimedia Commons / P. Hughes (CC BY 4.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/3/36/Cornell_McGraw_Tower"
                "_and_Uris_Library_March09_1.jpg/1920px-Cornell_McGraw_Tower_and_Uris_Library_M"
                "arch09_1.jpg"
            ),
            "credit": "Wikimedia Commons / Notyourbroom (CC BY 3.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/6/66/Cornell_Arts_Quad.JP"
                "G/1920px-Cornell_Arts_Quad.JPG"
            ),
            "credit": "Wikimedia Commons / Eustress (CC BY-SA 3.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f8/Skyline_of_Cornell_o"
                "ver_Mohawk_Valley%2C_Ithaca_NY.jpg/1920px-Skyline_of_Cornell_over_Mohawk_Valle"
                "y%2C_Ithaca_NY.jpg"
            ),
            "credit": "Wikimedia Commons / Gülməmməd Talk (CC BY-SA 3.0)",
        },
    ],
    "University of Pennsylvania": [
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/5/56/The_Quad_UPenn.jpg/1"
                "920px-The_Quad_UPenn.jpg"
            ),
            "credit": "Wikimedia Commons / Jenkennings (CC0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a9/The_Upper_Quadrangle"
                "_-_University_of_Pennsylvania.jpg/1920px-The_Upper_Quadrangle_-_University_of_"
                "Pennsylvania.jpg"
            ),
            "credit": "Wikimedia Commons / 1a0a2k6 (CC0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2a/Fisher_Fine_Arts_Lib"
                "rary_at_Night.jpg/1920px-Fisher_Fine_Arts_Library_at_Night.jpg"
            ),
            "credit": "Wikimedia Commons / Shirt Vonnegut (CC0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c7/University_of_Pennsy"
                "lvania_in_April.jpg/1920px-University_of_Pennsylvania_in_April.jpg"
            ),
            "credit": "Wikimedia Commons (public domain)",
        },
    ],
    "University of California-Berkeley": [
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5f/UC_Berkeley_campus_a"
                "nd_surroundings_from_Berkeley_Hills_January_2026.jpg/1920px-UC_Berkeley_campus"
                "_and_surroundings_from_Berkeley_Hills_January_2026.jpg"
            ),
            "credit": "Wikimedia Commons / 4300streetcar (CC BY 4.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7d/Doe_library_uc_berke"
                "ley_2023.jpg/1920px-Doe_library_uc_berkeley_2023.jpg"
            ),
            "credit": "Wikimedia Commons / Mizzlbrd (CC BY-SA 4.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/d/df/Berkeley_Sather_Gate"
                "_1_banner.jpg/1920px-Berkeley_Sather_Gate_1_banner.jpg"
            ),
            "credit": "Wikimedia Commons / Bernt Rostad; derivative work Eco84 (CC BY 2.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/7/75/View_of_Sather_Tower%2C_Do"
                "e_Library%2C_and_Memorial_Glade_through_trees_-_U.C._Berkeley_-_The_Daily_Cali"
                "fornian.jpg"
            ),
            "credit": (
                "Wikimedia Commons / Samuel Albillo / Senior Staff for The Daily Californian (0BSD)"
            ),
        },
    ],
    "University of Chicago": [
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7a/Cobb_Gate.jpg/1920px"
                "-Cobb_Gate.jpg"
            ),
            "credit": "Wikimedia Commons / Drsitu (CC BY-SA 4.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d4/University_of_Chicag"
                "o_main_quadrangles.jpg/1920px-University_of_Chicago_main_quadrangles.jpg"
            ),
            "credit": "Wikimedia Commons / Ndshankar (CC BY-SA 4.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/f/fc/Alex_MacLean_2005_campus_w"
                "ith_cityscape.jpg"
            ),
            "credit": "Wikimedia Commons / Ibrahim Old at Arabic Wikipedia (public domain)",
        },
        {
            "url": "https://upload.wikimedia.org/wikipedia/commons/b/bf/University_of_Chicago_at_Fall.jpg",
            "credit": "Wikimedia Commons / Nicomachian (CC BY-SA 4.0)",
        },
    ],
    "Carnegie Mellon University": [
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/5/56/The_Mall%2C_Carnegie"
                "_Mellon_University%2C_2023-04-27%2C_01.jpg/1920px-The_Mall%2C_Carnegie_Mellon_"
                "University%2C_2023-04-27%2C_01.jpg"
            ),
            "credit": "Wikimedia Commons / Cbaile19 (CC0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f4/The_Cut%2C_Carnegie_"
                "Mellon_University.jpg/1920px-The_Cut%2C_Carnegie_Mellon_University.jpg"
            ),
            "credit": "Wikimedia Commons / Sdkb (CC BY-SA 4.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ea/Gates_and_Hillman_Ce"
                "nters%2C_Carnegie_Mellon_University.jpg/1920px-Gates_and_Hillman_Centers%2C_Ca"
                "rnegie_Mellon_University.jpg"
            ),
            "credit": "Wikimedia Commons / Sdkb (CC BY-SA 4.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/2/21/Carnegie_Mellon_Univ"
                "ersity_as_seen_from_the_Cathedral_of_Learning.jpg/1920px-Carnegie_Mellon_Unive"
                "rsity_as_seen_from_the_Cathedral_of_Learning.jpg"
            ),
            "credit": "Wikimedia Commons / Dllu (CC BY-SA 4.0)",
        },
    ],
    "Duke University": [
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/1/12/Duke_University_Chap"
                "el_side_in_July_2025.jpg/1920px-Duke_University_Chapel_side_in_July_2025.jpg"
            ),
            "credit": "Wikimedia Commons / Sdkb (CC BY-SA 4.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/3/36/Duke_University_in_J"
                "uly_2025_West_Campus_photosphere_1.jpg/1920px-Duke_University_in_July_2025_Wes"
                "t_Campus_photosphere_1.jpg"
            ),
            "credit": "Wikimedia Commons / Sdkb (CC BY-SA 4.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/Main_academic_quad_-"
                "_panoramio.jpg/1920px-Main_academic_quad_-_panoramio.jpg"
            ),
            "credit": "Wikimedia Commons / dreid1987 (CC BY 3.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/6/60/Allen_Building%2C_We"
                "st_Campus%2C_Duke_University%2C_Durham%2C_NC_%2848960847232%29.jpg/1920px-Alle"
                "n_Building%2C_West_Campus%2C_Duke_University%2C_Durham%2C_NC_%2848960847232%29"
                ".jpg"
            ),
            "credit": "Wikimedia Commons / Warren LeMay (CC0)",
        },
    ],
    "Rice University": [
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3e/Rice_University_-_Ri"
                "ce_statue_with_Lovett_Hall.JPG/1920px-Rice_University_-_Rice_statue_with_Lovet"
                "t_Hall.JPG"
            ),
            "credit": "Wikimedia Commons / Daderot (public domain)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/2/29/Rice_University_Main"
                "_Entrance.jpg/1920px-Rice_University_Main_Entrance.jpg"
            ),
            "credit": "Wikimedia Commons / Katie Haugland Bowen (CC BY 2.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d9/Rice_University_Camp"
                "us.jpg/1920px-Rice_University_Campus.jpg"
            ),
            "credit": "Wikimedia Commons / AnnaLellis (CC BY 4.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e2/Mcmurtry_college_qua"
                "d_from_roof.jpg/1920px-Mcmurtry_college_quad_from_roof.jpg"
            ),
            "credit": "Wikimedia Commons / Seanharger (CC BY-SA 4.0)",
        },
    ],
}


def _file_key(url: str) -> str:
    """Normalize a Commons URL to its file name (strip size prefix) for dedupe."""
    last = url.rsplit("/", 1)[-1]
    return re.sub(r"^\d+px-", "", last).lower()


def upgrade() -> None:
    conn = op.get_bind()
    for name, photos in CAMPUS_PHOTOS.items():
        row = conn.execute(
            sa.text("SELECT media_gallery, school_outcomes FROM institutions WHERE name = :n"),
            {"n": name},
        ).fetchone()
        if row is None:
            continue  # idempotent on fresh/CI databases
        gallery = row[0] or []
        outcomes = row[1] or {}
        hero = next(
            (u for u in gallery if re.search(r"\.(jpe?g|png|webp|avif)($|\?)", u, re.I)),
            None,
        )
        merged = list(photos)
        if hero and outcomes.get("media_credit"):
            keys = {_file_key(p["url"]) for p in merged}
            if _file_key(hero) not in keys:
                merged = [{"url": hero, "credit": outcomes["media_credit"]}, *merged]
        merged = merged[:5]
        conn.execute(
            sa.text(
                "UPDATE institutions SET school_outcomes = jsonb_set("
                "COALESCE(school_outcomes, '{}'::jsonb), '{campus_photos}', "
                "CAST(:v AS jsonb), true) WHERE name = :n"
            ),
            {"v": json.dumps(merged), "n": name},
        )


def downgrade() -> None:
    conn = op.get_bind()
    for name in CAMPUS_PHOTOS:
        conn.execute(
            sa.text(
                "UPDATE institutions SET school_outcomes = "
                "school_outcomes - 'campus_photos' WHERE name = :n"
            ),
            {"n": name},
        )
