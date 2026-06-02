"""Spec 12 — backfill School Detail data so the live page renders to spec.

The School Detail page (`/s/institutions/:id`, `/school/:id`) is code-complete
and deployed, but production data is bare: institutions have no sub-school rows
(so the default **Schools** tab — the page's "gateway to programs" purpose,
spec §1/§3.3 — renders empty) and no founding year / size / structured profile
fields (so the header line "Founded … · N students" of spec §2 and the
Overview/About tabs are blank).

This is a **data migration**. Two idempotent steps:

1. GENERIC — for any institution that has **zero** rows in ``schools`` but whose
   programs carry a ``department``, create one ``schools`` row per distinct
   department and point ``programs.school_id`` at it. NYU's programs already
   carry real school names in ``department`` ("Tandon School of Engineering",
   "Stern School of Business", …) so this lights up the Schools tab with real,
   non-invented data, and does the same for any future institution.

2. TARGETED — backfill New York University's public facts (founding year, size,
   campus setting, and the structured ``ranking_data`` / ``school_outcomes`` /
   ``support_services`` / ``policies`` / ``international_info`` JSONB used by the
   Overview + About tabs). Values are public/encyclopedic; spec §2 itself uses
   NYU's real numbers ("Founded 1831 · 51,000 students"). Only fills columns
   that are currently NULL, so an institution that later edits its own profile
   is never overwritten.

Revision ID: b12c0de5f7a9
Revises: r40a1b2c3d4e
Create Date: 2026-06-01

"""

from __future__ import annotations

import json
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b12c0de5f7a9"  # pragma: allowlist secret
down_revision: str | Sequence[str] | None = "r40a1b2c3d4e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_NYU = "New York University"

# NYU's public/encyclopedic structured profile. Kept inline (not a fixture file)
# so the migration is self-contained and reviewable; serialized via json.dumps
# and bound as parameters (no hand-escaped SQL string literals).
_NYU_CAMPUS_DESCRIPTION = (
    "NYU's campus is woven into the streets of Greenwich Village in Lower "
    "Manhattan — there are no walls or gates. The city is the campus: classrooms, "
    "residence halls, libraries, and studios sit among the neighborhood's cafes, "
    "theaters, and startups, with global academic centers in Abu Dhabi and "
    "Shanghai and study-away sites on six continents."
)
_NYU_RANKING = {
    "ownership_type": "private_nonprofit",
    "accreditor": "Middle States Commission on Higher Education",
    "us_news_2025": 30,
    "acceptance_rate": 0.12,
    "graduation_rate": 0.87,
    "median_earnings": 75300,
    "retention_rate": 0.94,
    "tuition_out_of_state": 60438,
    "carnegie_classification": "R1: Doctoral Universities – Very high research activity",
}
_NYU_OUTCOMES = {
    "employed_or_continuing_ed": 0.93,
    "graduation_rate_6yr": 0.87,
    "retention_rate_4yr": 0.94,
    "median_salary": 75300,
    "top_employer_industries": [
        "Financial Services",
        "Technology",
        "Media & Entertainment",
        "Healthcare",
        "Consulting",
    ],
    "_note": (
        "Institution-wide first-destination signal; specific program "
        "outcomes appear on each program page."
    ),
}
_NYU_SUPPORT = {
    "tutoring": {
        "name": "University Learning Center",
        "url": "https://www.nyu.edu/students/academic-services.html",
    },
    "career": {
        "name": "Wasserman Center for Career Development",
        "url": "https://www.nyu.edu/students/career-development.html",
    },
    "counseling": {
        "name": "Counseling and Wellness Services",
        "url": "https://www.nyu.edu/students/health-and-wellness.html",
    },
    "disability": {
        "name": "Moses Center for Student Accessibility",
        "url": "https://www.nyu.edu/students/communities-and-groups/student-accessibility.html",
    },
    "financial_literacy": {
        "name": "Office of Financial Aid",
        "url": "https://www.nyu.edu/admissions/financial-aid-and-scholarships.html",
    },
}
_NYU_POLICIES = {
    "test_optional": {
        "summary": "Test-optional for first-year applicants — SAT/ACT not required.",
        "url": "https://www.nyu.edu/admissions/undergraduate-admissions.html",
    },
    "transfer_credit": {
        "summary": (
            "Accepts transfer credit from accredited institutions; AP/IB credit by department."
        ),
    },
    "deferral": {
        "summary": "Admitted students may request a one-year deferral for approved reasons.",
    },
}
_NYU_INTL = {
    "international_student_count": 21000,
    "supported_visas": ["F-1", "J-1"],
    "english_proficiency": {
        "summary": "TOEFL iBT 100, IELTS 7.5, or Duolingo 125 for most programs.",
        "toefl_ibt_min": 100,
        "ielts_min": 7.5,
        "duolingo_min": 125,
    },
    "office": {
        "summary": (
            "The Office of Global Services supports international students with "
            "visas, work authorization, and orientation."
        ),
    },
    "scholarship_eligibility": (
        "International students are considered for merit-based scholarships; "
        "need-based aid is limited for non-citizens."
    ),
}


def upgrade() -> None:
    # ── Step 1 (generic): synthesize sub-schools from program departments ──
    # For every institution that has no schools yet, create a school per distinct
    # department and link its programs. Idempotent: the INSERT is guarded by a
    # NOT EXISTS on schools for that institution, and the UPDATE only sets
    # school_id where it is still NULL and the name matches a department.
    op.execute(
        """
        INSERT INTO schools (id, institution_id, name, sort_order, created_at, updated_at)
        SELECT gen_random_uuid(), p.institution_id, p.department,
               row_number() OVER (PARTITION BY p.institution_id ORDER BY p.department),
               NOW(), NOW()
        FROM (
            SELECT DISTINCT institution_id, department
            FROM programs
            WHERE department IS NOT NULL AND btrim(department) <> ''
        ) AS p
        WHERE NOT EXISTS (
            SELECT 1 FROM schools s WHERE s.institution_id = p.institution_id
        )
        """
    )

    # Link programs to the school whose name matches their department. Only fills
    # NULL school_id, so it never disturbs explicitly-assigned programs.
    op.execute(
        """
        UPDATE programs p
        SET school_id = s.id
        FROM schools s
        WHERE s.institution_id = p.institution_id
          AND s.name = p.department
          AND p.school_id IS NULL
          AND p.department IS NOT NULL
        """
    )

    # ── Step 2 (targeted): NYU public facts, only where currently NULL ──
    op.execute(
        sa.text(
            """
            UPDATE institutions
            SET founded_year       = COALESCE(founded_year, 1831),
                student_body_size  = COALESCE(student_body_size, 51848),
                campus_setting     = COALESCE(campus_setting, 'urban'),
                campus_description = COALESCE(campus_description, :campus),
                ranking_data       = COALESCE(ranking_data, CAST(:ranking AS jsonb)),
                school_outcomes    = COALESCE(school_outcomes, CAST(:outcomes AS jsonb)),
                support_services   = COALESCE(support_services, CAST(:support AS jsonb)),
                policies           = COALESCE(policies, CAST(:policies AS jsonb)),
                international_info  = COALESCE(international_info, CAST(:intl AS jsonb))
            WHERE name = :name
            """
        ).bindparams(
            campus=_NYU_CAMPUS_DESCRIPTION,
            ranking=json.dumps(_NYU_RANKING),
            outcomes=json.dumps(_NYU_OUTCOMES),
            support=json.dumps(_NYU_SUPPORT),
            policies=json.dumps(_NYU_POLICIES),
            intl=json.dumps(_NYU_INTL),
            name=_NYU,
        )
    )


def downgrade() -> None:
    # Reverse Step 1: detach programs from synthesized schools, then drop the
    # schools whose name still equals a program department (i.e. ones we made).
    op.execute(
        """
        UPDATE programs p
        SET school_id = NULL
        FROM schools s
        WHERE p.school_id = s.id
          AND s.name = p.department
        """
    )
    op.execute(
        """
        DELETE FROM schools s
        WHERE EXISTS (
            SELECT 1 FROM programs p
            WHERE p.institution_id = s.institution_id AND p.department = s.name
        )
        """
    )
    # Reverse Step 2: null out the NYU facts this migration set.
    op.execute(
        sa.text(
            """
            UPDATE institutions
            SET founded_year = NULL,
                student_body_size = NULL,
                campus_setting = NULL,
                campus_description = NULL,
                ranking_data = NULL,
                school_outcomes = NULL,
                support_services = NULL,
                policies = NULL,
                international_info = NULL
            WHERE name = :name
            """
        ).bindparams(name=_NYU)
    )
