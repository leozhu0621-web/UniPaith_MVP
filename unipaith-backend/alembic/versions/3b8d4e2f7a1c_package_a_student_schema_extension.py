"""Package A: student schema extension (appendix prompt-library gap close)

Closes the INPUT-side gap between docs/STUDENT_DATA_STANDARD.md (derived from
Platform_business_plan.docx appendix) and the current student_* schema.

Two new tables:
- student_platform_events: broad analytics events (not program-scoped) -
  login, session, search, page-view, CTA, drop-off, UTM, device. The existing
  student_engagement_signals table is program-scoped and remains as-is.
- student_major_readiness: track-level self-rating rollup
  (cs/engineering/business/health/arts/humanities). One row per student per
  track, with readiness_data as a JSONB blob holding the 50-100 per-track
  fields from the appendix.

Six existing tables get new nullable columns, grouped by concern:
- student_profiles: identity + verification + addresses (JSONB) +
  emergency_contact (JSONB) + guardian (JSONB).
- student_preferences: 7 explicit weight scales (0-10) + categorical
  priorities (application intensity, learning/program style, risk tolerance,
  target degree/term, thesis interest) + short-term career goal.
- test_scores: percentile, attempts, superscore, expiration, waivers,
  verification, score normalization status.
- academic_records: class rank + attendance + percentile, weighted-GPA flag,
  leave-of-absence, withdrawal/incomplete, grading scale type, transcript
  upload + translation, school-reported rigor breakdown, normalized GPA,
  transcript parse status.
- student_data_consent: first-gen, FERPA, honor code, background check,
  military/veteran, disciplinary/prior-dismissal/criminal-history flags,
  directory info release, third-party sharing, marketing channel consent.
- student_visa_info: current location (city/country), dependents, intended
  start term, current visa type, citizenship (when distinct from
  nationality).

Every column is nullable. Every default is null/false so existing rows are
unaffected. Downgrade drops the new tables + columns.

Revision ID: 3b8d4e2f7a1c
Revises: 2a5f8c1d9e3b
Create Date: 2026-04-17 05:00:00.000000

"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "3b8d4e2f7a1c"
down_revision = "2a5f8c1d9e3b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- New table: student_platform_events -----------------------------
    op.create_table(
        "student_platform_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "student_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("student_profiles.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column(
            "event_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("session_id", sa.String(100), nullable=True),
        sa.Column("device_type", sa.String(30), nullable=True),
        sa.Column("url_path", sa.String(500), nullable=True),
        sa.Column("referral_source", sa.String(100), nullable=True),
        sa.Column("utm_campaign", sa.String(255), nullable=True),
        sa.Column("ip_country", sa.String(100), nullable=True),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_platform_events_student_type",
        "student_platform_events",
        ["student_id", "event_type"],
    )
    op.create_index(
        "ix_platform_events_occurred_at",
        "student_platform_events",
        ["occurred_at"],
    )

    # --- New table: student_major_readiness -----------------------------
    op.create_table(
        "student_major_readiness",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "student_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("student_profiles.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("track", sa.String(30), nullable=False),
        sa.Column(
            "readiness_data",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("student_id", "track", name="uq_major_readiness_student_track"),
    )

    # --- student_profiles ------------------------------------------------
    cols_profile = [
        ("preferred_name", sa.String(100)),
        ("name_in_native_script", sa.String(255)),
        ("preferred_pronouns", sa.String(50)),
        ("gender_identity", sa.String(50)),
        ("legal_sex", sa.String(20)),
        ("place_of_birth", sa.String(255)),
        ("passport_issuing_country", sa.String(100)),
        ("secondary_email", sa.String(255)),
        ("secondary_phone", sa.String(50)),
        ("preferred_contact_channel", sa.String(30)),
        ("preferred_platform_language", sa.String(30)),
        ("preferred_writing_language", sa.String(30)),
        ("marital_status", sa.String(30)),
        ("residency_status_for_tuition", sa.String(50)),
        ("domicile_state", sa.String(50)),
        ("duration_of_residency_months", sa.Integer()),
        ("addresses", postgresql.JSONB(astext_type=sa.Text())),
        ("emergency_contact", postgresql.JSONB(astext_type=sa.Text())),
        ("guardian", postgresql.JSONB(astext_type=sa.Text())),
        ("email_verified", sa.Boolean(), False),
        ("phone_verified", sa.Boolean(), False),
        ("id_verification_status", sa.String(20), "none"),
    ]
    for name, type_, *default in cols_profile:
        kwargs = {"nullable": True}
        if default:
            kwargs["server_default"] = (
                sa.text(f"'{default[0]}'") if isinstance(default[0], str)
                else sa.text(str(default[0]).lower())
            )
        op.add_column("student_profiles", sa.Column(name, type_, **kwargs))

    # --- student_preferences --------------------------------------------
    cols_pref = [
        ("weight_cost", sa.Integer()),
        ("weight_location", sa.Integer()),
        ("weight_outcomes", sa.Integer()),
        ("weight_ranking", sa.Integer()),
        ("weight_flexibility", sa.Integer()),
        ("weight_support", sa.Integer()),
        ("weight_time_to_degree", sa.Integer()),
        ("application_intensity", sa.String(30)),
        ("preferred_learning_style", sa.String(30)),
        ("preferred_program_style", sa.String(30)),
        ("research_interest_level", sa.String(20)),
        ("return_home_intent", sa.String(20)),
        ("risk_tolerance", sa.String(20)),
        ("stretch_target_safety_mix", sa.String(50)),
        ("target_degree_level", sa.String(30)),
        ("target_start_term", sa.String(30)),
        ("thesis_interest", sa.String(20)),
        ("career_goal_short_term", sa.Text()),
    ]
    for name, type_ in cols_pref:
        op.add_column("student_preferences", sa.Column(name, type_, nullable=True))

    # --- test_scores ----------------------------------------------------
    cols_test = [
        ("percentile", sa.Numeric(5, 2)),
        ("test_attempt_number", sa.Integer()),
        ("superscore_preference", sa.Boolean()),
        ("score_expiration_date", sa.Date()),
        ("test_waiver_flag", sa.Boolean()),
        ("test_waiver_basis", sa.String(255)),
        ("official_score_report_url", sa.String(1000)),
        ("is_verified", sa.Boolean(), False),
        ("score_normalization_status", sa.String(20), "unmapped"),
    ]
    for name, type_, *default in cols_test:
        kwargs = {"nullable": True}
        if default:
            kwargs["server_default"] = (
                sa.text(f"'{default[0]}'") if isinstance(default[0], str)
                else sa.text(str(default[0]).lower())
            )
        op.add_column("test_scores", sa.Column(name, type_, **kwargs))

    # --- academic_records -----------------------------------------------
    cols_acad = [
        ("attendance_rate", sa.Numeric(5, 4)),
        ("class_rank", sa.Integer()),
        ("class_rank_denominator", sa.Integer()),
        ("percentile_rank", sa.Numeric(5, 2)),
        ("weighted_gpa_flag", sa.Boolean()),
        ("leave_of_absence_flag", sa.Boolean()),
        ("withdrawal_incomplete_flag", sa.Boolean()),
        ("grading_scale_type", sa.String(30)),
        ("term_system_type", sa.String(30)),
        ("transcript_upload_url", sa.String(1000)),
        ("translation_provided_flag", sa.Boolean()),
        ("school_reported_rigor", postgresql.JSONB(astext_type=sa.Text())),
        ("disruption_details", sa.Text()),
        ("normalized_gpa", sa.Numeric(4, 2)),
        ("transcript_parse_status", sa.String(20), "not_parsed"),
    ]
    for name, type_, *default in cols_acad:
        kwargs = {"nullable": True}
        if default:
            kwargs["server_default"] = sa.text(f"'{default[0]}'")
        op.add_column("academic_records", sa.Column(name, type_, **kwargs))

    # --- student_data_consent -------------------------------------------
    cols_consent = [
        ("first_generation_status", sa.Boolean()),
        ("first_generation_definition", sa.String(50)),
        ("ferpa_release", sa.Boolean()),
        ("honor_code_ack", sa.Boolean()),
        ("background_check_required", sa.Boolean()),
        ("code_of_conduct_ack", sa.Boolean()),
        ("criminal_history_disclosed", sa.Boolean()),
        ("disciplinary_history_disclosed", sa.Boolean()),
        ("immunization_compliance", sa.String(30)),
        ("health_insurance_waiver_intent", sa.Boolean()),
        ("military_status", sa.String(30)),
        ("veteran_status", sa.Boolean()),
        ("prior_academic_dismissal_flag", sa.Boolean()),
        ("directory_info_release", sa.Boolean()),
        ("third_party_sharing_consent", sa.Boolean()),
        ("marketing_channel_consent", postgresql.JSONB(astext_type=sa.Text())),
        ("consent_revocation_timestamps", postgresql.JSONB(astext_type=sa.Text())),
    ]
    for name, type_ in cols_consent:
        op.add_column("student_data_consent", sa.Column(name, type_, nullable=True))

    # --- student_visa_info ----------------------------------------------
    cols_visa = [
        ("current_location_city", sa.String(100)),
        ("current_location_country", sa.String(100)),
        ("dependents_accompanying", sa.Boolean()),
        ("intended_start_term", sa.String(30)),
        ("visa_type_current", sa.String(30)),
        ("country_of_citizenship", sa.String(100)),
    ]
    for name, type_ in cols_visa:
        op.add_column("student_visa_info", sa.Column(name, type_, nullable=True))


def downgrade() -> None:
    for col in (
        "current_location_city", "current_location_country", "dependents_accompanying",
        "intended_start_term", "visa_type_current", "country_of_citizenship",
    ):
        op.drop_column("student_visa_info", col)

    for col in (
        "first_generation_status", "first_generation_definition", "ferpa_release",
        "honor_code_ack", "background_check_required", "code_of_conduct_ack",
        "criminal_history_disclosed", "disciplinary_history_disclosed",
        "immunization_compliance", "health_insurance_waiver_intent",
        "military_status", "veteran_status", "prior_academic_dismissal_flag",
        "directory_info_release", "third_party_sharing_consent",
        "marketing_channel_consent", "consent_revocation_timestamps",
    ):
        op.drop_column("student_data_consent", col)

    for col in (
        "attendance_rate", "class_rank", "class_rank_denominator", "percentile_rank",
        "weighted_gpa_flag", "leave_of_absence_flag", "withdrawal_incomplete_flag",
        "grading_scale_type", "term_system_type", "transcript_upload_url",
        "translation_provided_flag", "school_reported_rigor", "disruption_details",
        "normalized_gpa", "transcript_parse_status",
    ):
        op.drop_column("academic_records", col)

    for col in (
        "percentile", "test_attempt_number", "superscore_preference",
        "score_expiration_date", "test_waiver_flag", "test_waiver_basis",
        "official_score_report_url", "is_verified", "score_normalization_status",
    ):
        op.drop_column("test_scores", col)

    for col in (
        "weight_cost", "weight_location", "weight_outcomes", "weight_ranking",
        "weight_flexibility", "weight_support", "weight_time_to_degree",
        "application_intensity", "preferred_learning_style", "preferred_program_style",
        "research_interest_level", "return_home_intent", "risk_tolerance",
        "stretch_target_safety_mix", "target_degree_level", "target_start_term",
        "thesis_interest", "career_goal_short_term",
    ):
        op.drop_column("student_preferences", col)

    for col in (
        "preferred_name", "name_in_native_script", "preferred_pronouns",
        "gender_identity", "legal_sex", "place_of_birth", "passport_issuing_country",
        "secondary_email", "secondary_phone", "preferred_contact_channel",
        "preferred_platform_language", "preferred_writing_language", "marital_status",
        "residency_status_for_tuition", "domicile_state", "duration_of_residency_months",
        "addresses", "emergency_contact", "guardian", "email_verified",
        "phone_verified", "id_verification_status",
    ):
        op.drop_column("student_profiles", col)

    op.drop_table("student_major_readiness")
    op.drop_index("ix_platform_events_occurred_at", table_name="student_platform_events")
    op.drop_index("ix_platform_events_student_type", table_name="student_platform_events")
    op.drop_table("student_platform_events")
