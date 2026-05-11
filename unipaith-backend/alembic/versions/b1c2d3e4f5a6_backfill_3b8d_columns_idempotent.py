"""backfill 3b8d4e2f7a1c columns idempotently

Production DB's alembic_version was advanced past 3b8d4e2f7a1c
("Package A: student schema extension") at some point, but the
migration's DDL never actually executed against the live schema —
every signup hit `column "preferred_name" of relation
"student_profiles" does not exist` while alembic happily reported
all migrations complete.

Rather than rewind alembic_version (risky, requires DB access), this
migration runs 3b8d4e2f7a1c's DDL idempotently with CREATE TABLE IF
NOT EXISTS / ADD COLUMN IF NOT EXISTS / CREATE INDEX IF NOT EXISTS so
it's safe whether the prior migration applied or not.

Scope: every table + column 3b8d4e2f7a1c originally added —
student_profiles, student_preferences, test_scores, academic_records,
student_data_consent, student_visa_info, plus the new tables
student_platform_events and student_major_readiness.

Revision ID: b1c2d3e4f5a6
Revises: ac252aa411c3
Create Date: 2026-05-10 20:15:00.000000

"""

from __future__ import annotations

from alembic import op

# revision identifiers
revision = "b1c2d3e4f5a6"
down_revision = "ac252aa411c3"
branch_labels = None
depends_on = None


# Each tuple: (table, column, type_with_default)
_COLUMNS: list[tuple[str, str, str]] = [
    # student_profiles -------------------------------------------------
    ("student_profiles", "preferred_name", "VARCHAR(100)"),
    ("student_profiles", "name_in_native_script", "VARCHAR(255)"),
    ("student_profiles", "preferred_pronouns", "VARCHAR(50)"),
    ("student_profiles", "gender_identity", "VARCHAR(50)"),
    ("student_profiles", "legal_sex", "VARCHAR(20)"),
    ("student_profiles", "place_of_birth", "VARCHAR(255)"),
    ("student_profiles", "passport_issuing_country", "VARCHAR(100)"),
    ("student_profiles", "secondary_email", "VARCHAR(255)"),
    ("student_profiles", "secondary_phone", "VARCHAR(50)"),
    ("student_profiles", "preferred_contact_channel", "VARCHAR(30)"),
    ("student_profiles", "preferred_platform_language", "VARCHAR(30)"),
    ("student_profiles", "preferred_writing_language", "VARCHAR(30)"),
    ("student_profiles", "marital_status", "VARCHAR(30)"),
    ("student_profiles", "residency_status_for_tuition", "VARCHAR(50)"),
    ("student_profiles", "domicile_state", "VARCHAR(50)"),
    ("student_profiles", "duration_of_residency_months", "INTEGER"),
    ("student_profiles", "addresses", "JSONB"),
    ("student_profiles", "emergency_contact", "JSONB"),
    ("student_profiles", "guardian", "JSONB"),
    ("student_profiles", "email_verified", "BOOLEAN DEFAULT FALSE"),
    ("student_profiles", "phone_verified", "BOOLEAN DEFAULT FALSE"),
    ("student_profiles", "id_verification_status", "VARCHAR(20) DEFAULT 'none'"),
    # student_preferences ---------------------------------------------
    ("student_preferences", "weight_cost", "INTEGER"),
    ("student_preferences", "weight_location", "INTEGER"),
    ("student_preferences", "weight_outcomes", "INTEGER"),
    ("student_preferences", "weight_ranking", "INTEGER"),
    ("student_preferences", "weight_flexibility", "INTEGER"),
    ("student_preferences", "weight_support", "INTEGER"),
    ("student_preferences", "weight_time_to_degree", "INTEGER"),
    ("student_preferences", "application_intensity", "VARCHAR(30)"),
    ("student_preferences", "preferred_learning_style", "VARCHAR(30)"),
    ("student_preferences", "preferred_program_style", "VARCHAR(30)"),
    ("student_preferences", "research_interest_level", "VARCHAR(20)"),
    ("student_preferences", "return_home_intent", "VARCHAR(20)"),
    ("student_preferences", "risk_tolerance", "VARCHAR(20)"),
    ("student_preferences", "stretch_target_safety_mix", "VARCHAR(50)"),
    ("student_preferences", "target_degree_level", "VARCHAR(30)"),
    ("student_preferences", "target_start_term", "VARCHAR(30)"),
    ("student_preferences", "thesis_interest", "VARCHAR(20)"),
    ("student_preferences", "career_goal_short_term", "TEXT"),
    # test_scores ------------------------------------------------------
    ("test_scores", "percentile", "NUMERIC(5,2)"),
    ("test_scores", "test_attempt_number", "INTEGER"),
    ("test_scores", "superscore_preference", "BOOLEAN"),
    ("test_scores", "score_expiration_date", "DATE"),
    ("test_scores", "test_waiver_flag", "BOOLEAN"),
    ("test_scores", "test_waiver_basis", "VARCHAR(255)"),
    ("test_scores", "official_score_report_url", "VARCHAR(1000)"),
    ("test_scores", "is_verified", "BOOLEAN DEFAULT FALSE"),
    ("test_scores", "score_normalization_status", "VARCHAR(20) DEFAULT 'unmapped'"),
    # academic_records ------------------------------------------------
    ("academic_records", "attendance_rate", "NUMERIC(5,4)"),
    ("academic_records", "class_rank", "INTEGER"),
    ("academic_records", "class_rank_denominator", "INTEGER"),
    ("academic_records", "percentile_rank", "NUMERIC(5,2)"),
    ("academic_records", "weighted_gpa_flag", "BOOLEAN"),
    ("academic_records", "leave_of_absence_flag", "BOOLEAN"),
    ("academic_records", "withdrawal_incomplete_flag", "BOOLEAN"),
    ("academic_records", "grading_scale_type", "VARCHAR(30)"),
    ("academic_records", "term_system_type", "VARCHAR(30)"),
    ("academic_records", "transcript_upload_url", "VARCHAR(1000)"),
    ("academic_records", "translation_provided_flag", "BOOLEAN"),
    ("academic_records", "school_reported_rigor", "JSONB"),
    ("academic_records", "disruption_details", "TEXT"),
    ("academic_records", "normalized_gpa", "NUMERIC(4,2)"),
    ("academic_records", "transcript_parse_status", "VARCHAR(20) DEFAULT 'not_parsed'"),
    # student_data_consent --------------------------------------------
    ("student_data_consent", "first_generation_status", "BOOLEAN"),
    ("student_data_consent", "first_generation_definition", "VARCHAR(50)"),
    ("student_data_consent", "ferpa_release", "BOOLEAN"),
    ("student_data_consent", "honor_code_ack", "BOOLEAN"),
    ("student_data_consent", "background_check_required", "BOOLEAN"),
    ("student_data_consent", "code_of_conduct_ack", "BOOLEAN"),
    ("student_data_consent", "criminal_history_disclosed", "BOOLEAN"),
    ("student_data_consent", "disciplinary_history_disclosed", "BOOLEAN"),
    ("student_data_consent", "immunization_compliance", "VARCHAR(30)"),
    ("student_data_consent", "health_insurance_waiver_intent", "BOOLEAN"),
    ("student_data_consent", "military_status", "VARCHAR(30)"),
    ("student_data_consent", "veteran_status", "BOOLEAN"),
    ("student_data_consent", "prior_academic_dismissal_flag", "BOOLEAN"),
    ("student_data_consent", "directory_info_release", "BOOLEAN"),
    ("student_data_consent", "third_party_sharing_consent", "BOOLEAN"),
    ("student_data_consent", "marketing_channel_consent", "JSONB"),
    ("student_data_consent", "consent_revocation_timestamps", "JSONB"),
    # student_visa_info -----------------------------------------------
    ("student_visa_info", "current_location_city", "VARCHAR(100)"),
    ("student_visa_info", "current_location_country", "VARCHAR(100)"),
    ("student_visa_info", "dependents_accompanying", "BOOLEAN"),
    ("student_visa_info", "intended_start_term", "VARCHAR(30)"),
    ("student_visa_info", "visa_type_current", "VARCHAR(30)"),
    ("student_visa_info", "country_of_citizenship", "VARCHAR(100)"),
]


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS student_platform_events (
            id UUID PRIMARY KEY,
            student_id UUID NOT NULL REFERENCES student_profiles(id) ON DELETE CASCADE,
            event_type VARCHAR(50) NOT NULL,
            event_metadata JSONB,
            session_id VARCHAR(100),
            device_type VARCHAR(30),
            url_path VARCHAR(500),
            referral_source VARCHAR(100),
            utm_campaign VARCHAR(255),
            ip_country VARCHAR(100),
            occurred_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_student_platform_events_student_id "
        "ON student_platform_events (student_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_platform_events_student_type "
        "ON student_platform_events (student_id, event_type)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_platform_events_occurred_at "
        "ON student_platform_events (occurred_at)"
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS student_major_readiness (
            id UUID PRIMARY KEY,
            student_id UUID NOT NULL REFERENCES student_profiles(id) ON DELETE CASCADE,
            track VARCHAR(30) NOT NULL,
            readiness_data JSONB NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_major_readiness_student_track UNIQUE (student_id, track)
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_student_major_readiness_student_id "
        "ON student_major_readiness (student_id)"
    )

    for table, column, type_def in _COLUMNS:
        op.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {type_def}")


def downgrade() -> None:
    # No-op: this is a corrective migration. Rolling it back would
    # drop columns potentially populated by users; manual review
    # required if a downgrade is ever needed.
    pass
