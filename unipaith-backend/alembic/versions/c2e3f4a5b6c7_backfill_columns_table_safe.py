"""backfill 3b8d columns, table-existence-safe

b1c2d3e4f5a6 was stamped as applied on prod even though its DDL
rolled back: it tried to ALTER a table (student_data_consent) that
didn't exist in prod, which threw, and Postgres transactional DDL
rolled back the whole migration — including every successful
ALTER TABLE student_profiles ADD COLUMN that ran before the failure.

This follow-up wraps every ALTER in a DO $$ block that first checks
information_schema for the target table. Missing tables are skipped
silently; present tables get the column added with IF NOT EXISTS.
The end state is "every column that can be added, is added" without
the all-or-nothing rollback trap.

Revision ID: c2e3f4a5b6c7
Revises: b1c2d3e4f5a6
Create Date: 2026-05-10 20:32:00.000000

"""

from __future__ import annotations

from alembic import op

# revision identifiers
revision = "c2e3f4a5b6c7"
down_revision = "b1c2d3e4f5a6"
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
    # student_data_consent (may not exist in some prod-state snapshots)
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
    # student_visa_info (may not exist in some prod-state snapshots)
    ("student_visa_info", "current_location_city", "VARCHAR(100)"),
    ("student_visa_info", "current_location_country", "VARCHAR(100)"),
    ("student_visa_info", "dependents_accompanying", "BOOLEAN"),
    ("student_visa_info", "intended_start_term", "VARCHAR(30)"),
    ("student_visa_info", "visa_type_current", "VARCHAR(30)"),
    ("student_visa_info", "country_of_citizenship", "VARCHAR(100)"),
]


def upgrade() -> None:
    for table, column, type_def in _COLUMNS:
        # Wrap each ALTER in a DO block that first checks the table
        # exists. PostgreSQL DO blocks are atomic per-block but a
        # caught-and-skipped no-op cannot poison the outer migration
        # transaction. Default value (after DEFAULT) may legitimately
        # contain single quotes ('none' / 'unmapped' / 'not_parsed'),
        # so we double them when nesting inside the EXECUTE string.
        escaped_type = type_def.replace("'", "''")
        op.execute(
            f"""
            DO $$
            BEGIN
              IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = '{table}'
              ) THEN
                EXECUTE 'ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {escaped_type}';
              END IF;
            END $$;
            """
        )


def downgrade() -> None:
    # No-op: corrective migration; downgrade not supported.
    pass
