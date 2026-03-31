"""initial_schema

Revision ID: 0001
Revises:
Create Date: 2026-03-29

Creates all tables with explicit DDL (auto-generated via alembic autogenerate).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.create_table('data_sources',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('source_name', sa.String(length=255), nullable=False),
    sa.Column('source_url', sa.String(length=1000), nullable=True),
    sa.Column('source_type', sa.String(length=20), nullable=True),
    sa.Column('crawl_frequency', sa.String(length=20), nullable=True),
    sa.Column('data_category', sa.String(length=50), nullable=True),
    sa.Column('last_crawled_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('reliability_score', sa.Numeric(precision=3, scale=2), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('drift_snapshots',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('snapshot_type', sa.String(length=30), nullable=False),
    sa.Column('reference_period_start', sa.DateTime(timezone=True), nullable=False),
    sa.Column('reference_period_end', sa.DateTime(timezone=True), nullable=False),
    sa.Column('current_period_start', sa.DateTime(timezone=True), nullable=False),
    sa.Column('current_period_end', sa.DateTime(timezone=True), nullable=False),
    sa.Column('feature_name', sa.String(length=100), nullable=True),
    sa.Column('reference_stats', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('current_stats', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('test_statistic', sa.Numeric(precision=10, scale=6), nullable=True),
    sa.Column('p_value', sa.Numeric(precision=10, scale=8), nullable=True),
    sa.Column('drift_detected', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_drift_snapshots_created', 'drift_snapshots', ['created_at'], unique=False)
    op.create_index('ix_drift_snapshots_type', 'drift_snapshots', ['snapshot_type'], unique=False)
    op.create_table('embeddings',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('entity_type', sa.String(length=20), nullable=False),
    sa.Column('entity_id', sa.UUID(), nullable=False),
    sa.Column('embedding', Vector(dim=1536), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('entity_type', 'entity_id')
    )
    op.create_index('ix_embeddings_hnsw', 'embeddings', ['embedding'], unique=False, postgresql_using='hnsw', postgresql_with={'m': 16, 'ef_construction': 64}, postgresql_ops={'embedding': 'vector_cosine_ops'})
    op.create_table('evaluation_runs',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('model_version', sa.String(length=50), nullable=False),
    sa.Column('evaluation_type', sa.String(length=30), nullable=False),
    sa.Column('dataset_size', sa.Integer(), nullable=False),
    sa.Column('metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('confusion_matrix', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('per_tier_metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('fairness_metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('drift_detected', sa.Boolean(), nullable=False),
    sa.Column('drift_details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('retraining_triggered', sa.Boolean(), nullable=False),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_evaluation_runs_model', 'evaluation_runs', ['model_version'], unique=False)
    op.create_index('ix_evaluation_runs_started', 'evaluation_runs', ['started_at'], unique=False)
    op.create_table('model_registry',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('model_version', sa.String(length=50), nullable=False),
    sa.Column('architecture', sa.Text(), nullable=True),
    sa.Column('hyperparameters', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('training_data_snapshot', sa.String(length=255), nullable=True),
    sa.Column('performance_metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('trained_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('promoted_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('retired_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('model_version')
    )
    op.create_table('users',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('cognito_sub', sa.String(length=255), nullable=True),
    sa.Column('role', sa.Enum('student', 'institution_admin', 'admin', name='user_role'), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_cognito_sub'), 'users', ['cognito_sub'], unique=True)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_table('crawl_jobs',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('source_id', sa.UUID(), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('pages_crawled', sa.Integer(), nullable=False),
    sa.Column('pages_failed', sa.Integer(), nullable=False),
    sa.Column('items_extracted', sa.Integer(), nullable=False),
    sa.Column('items_ingested', sa.Integer(), nullable=False),
    sa.Column('items_queued_for_review', sa.Integer(), nullable=False),
    sa.Column('items_duplicate', sa.Integer(), nullable=False),
    sa.Column('error_log', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['source_id'], ['data_sources.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_crawl_jobs_source_id'), 'crawl_jobs', ['source_id'], unique=False)
    op.create_table('crawl_schedules',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('source_id', sa.UUID(), nullable=False),
    sa.Column('frequency_hours', sa.Integer(), nullable=False),
    sa.Column('next_run_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('last_run_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('is_enabled', sa.Boolean(), nullable=False),
    sa.Column('consecutive_failures', sa.Integer(), nullable=False),
    sa.Column('max_retries', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['source_id'], ['data_sources.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('source_id')
    )
    op.create_table('institutions',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('admin_user_id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('type', sa.String(length=50), nullable=False),
    sa.Column('country', sa.String(length=100), nullable=False),
    sa.Column('region', sa.String(length=100), nullable=True),
    sa.Column('city', sa.String(length=100), nullable=True),
    sa.Column('ranking_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('description_text', sa.Text(), nullable=True),
    sa.Column('logo_url', sa.String(length=1000), nullable=True),
    sa.Column('website_url', sa.String(length=1000), nullable=True),
    sa.Column('is_verified', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['admin_user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('admin_user_id')
    )
    op.create_table('notification_preferences',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('email_enabled', sa.Boolean(), nullable=False),
    sa.Column('preferences', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id')
    )
    op.create_table('notifications',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('notification_type', sa.String(length=100), nullable=False),
    sa.Column('title', sa.String(length=300), nullable=False),
    sa.Column('body', sa.Text(), nullable=False),
    sa.Column('action_url', sa.String(length=500), nullable=True),
    sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('is_read', sa.Boolean(), nullable=False),
    sa.Column('is_emailed', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_notifications_created', 'notifications', ['created_at'], unique=False)
    op.create_index(op.f('ix_notifications_user_id'), 'notifications', ['user_id'], unique=False)
    op.create_index('ix_notifications_user_unread', 'notifications', ['user_id', 'is_read'], unique=False)
    op.create_table('raw_ingested_data',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('source_id', sa.UUID(), nullable=False),
    sa.Column('raw_content', sa.Text(), nullable=True),
    sa.Column('content_hash', sa.String(length=64), nullable=True),
    sa.Column('ingested_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('processed', sa.Boolean(), nullable=False),
    sa.Column('processing_result', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.ForeignKeyConstraint(['source_id'], ['data_sources.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('source_url_patterns',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('source_id', sa.UUID(), nullable=False),
    sa.Column('url_pattern', sa.String(length=1000), nullable=False),
    sa.Column('page_type', sa.String(length=30), nullable=True),
    sa.Column('follow_links', sa.Boolean(), nullable=False),
    sa.Column('link_selector', sa.String(length=500), nullable=True),
    sa.Column('requires_javascript', sa.Boolean(), nullable=False),
    sa.Column('extraction_prompt_override', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['source_id'], ['data_sources.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_source_url_patterns_source_id'), 'source_url_patterns', ['source_id'], unique=False)
    op.create_table('student_profiles',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('first_name', sa.String(length=100), nullable=True),
    sa.Column('last_name', sa.String(length=100), nullable=True),
    sa.Column('date_of_birth', sa.Date(), nullable=True),
    sa.Column('nationality', sa.String(length=100), nullable=True),
    sa.Column('country_of_residence', sa.String(length=100), nullable=True),
    sa.Column('bio_text', sa.Text(), nullable=True),
    sa.Column('goals_text', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id')
    )
    op.create_table('training_runs',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('triggered_by', sa.String(length=30), nullable=False),
    sa.Column('evaluation_run_id', sa.UUID(), nullable=True),
    sa.Column('training_data_size', sa.Integer(), nullable=False),
    sa.Column('test_data_size', sa.Integer(), nullable=False),
    sa.Column('feature_columns', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('algorithm', sa.String(length=50), nullable=False),
    sa.Column('hyperparameters', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('optuna_study_name', sa.String(length=100), nullable=True),
    sa.Column('cv_metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('test_metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('fairness_metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('fairness_passed', sa.Boolean(), nullable=True),
    sa.Column('model_artifact_path', sa.String(length=500), nullable=True),
    sa.Column('resulting_model_version', sa.String(length=50), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('failure_reason', sa.Text(), nullable=True),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['evaluation_run_id'], ['evaluation_runs.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_training_runs_started', 'training_runs', ['started_at'], unique=False)
    op.create_index('ix_training_runs_status', 'training_runs', ['status'], unique=False)
    op.create_table('ab_test_assignments',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('student_id', sa.UUID(), nullable=False),
    sa.Column('experiment_name', sa.String(length=100), nullable=False),
    sa.Column('variant', sa.String(length=20), nullable=False),
    sa.Column('model_version', sa.String(length=50), nullable=False),
    sa.Column('assigned_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('outcome_recorded', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['student_id'], ['student_profiles.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_ab_test_experiment', 'ab_test_assignments', ['experiment_name'], unique=False)
    op.create_index('ix_ab_test_student_experiment', 'ab_test_assignments', ['student_id', 'experiment_name'], unique=True)
    op.create_table('academic_records',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('student_id', sa.UUID(), nullable=False),
    sa.Column('institution_name', sa.String(length=255), nullable=False),
    sa.Column('degree_type', sa.String(length=50), nullable=False),
    sa.Column('field_of_study', sa.String(length=255), nullable=True),
    sa.Column('gpa', sa.Numeric(precision=4, scale=2), nullable=True),
    sa.Column('gpa_scale', sa.String(length=20), nullable=True),
    sa.Column('start_date', sa.Date(), nullable=True),
    sa.Column('end_date', sa.Date(), nullable=True),
    sa.Column('is_current', sa.Boolean(), nullable=False),
    sa.Column('honors', sa.String(length=255), nullable=True),
    sa.Column('thesis_title', sa.String(length=500), nullable=True),
    sa.Column('country', sa.String(length=100), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['student_id'], ['student_profiles.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_academic_records_student_id'), 'academic_records', ['student_id'], unique=False)
    op.create_table('activities',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('student_id', sa.UUID(), nullable=False),
    sa.Column('activity_type', sa.String(length=50), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('organization', sa.String(length=255), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('start_date', sa.Date(), nullable=True),
    sa.Column('end_date', sa.Date(), nullable=True),
    sa.Column('is_current', sa.Boolean(), nullable=False),
    sa.Column('hours_per_week', sa.Integer(), nullable=True),
    sa.Column('impact_description', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['student_id'], ['student_profiles.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activities_student_id'), 'activities', ['student_id'], unique=False)
    op.create_table('crm_records',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('institution_id', sa.UUID(), nullable=False),
    sa.Column('student_id', sa.UUID(), nullable=False),
    sa.Column('touchpoint_type', sa.String(length=50), nullable=True),
    sa.Column('touchpoint_detail', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('occurred_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['institution_id'], ['institutions.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['student_id'], ['student_profiles.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_crm_institution_student', 'crm_records', ['institution_id', 'student_id'], unique=False)
    op.create_index(op.f('ix_crm_records_institution_id'), 'crm_records', ['institution_id'], unique=False)
    op.create_index(op.f('ix_crm_records_student_id'), 'crm_records', ['student_id'], unique=False)
    op.create_table('fairness_reports',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('model_version', sa.String(length=50), nullable=False),
    sa.Column('evaluation_run_id', sa.UUID(), nullable=True),
    sa.Column('training_run_id', sa.UUID(), nullable=True),
    sa.Column('protected_attribute', sa.String(length=50), nullable=False),
    sa.Column('group_metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('demographic_parity_diff', sa.Numeric(precision=5, scale=4), nullable=True),
    sa.Column('equal_opportunity_diff', sa.Numeric(precision=5, scale=4), nullable=True),
    sa.Column('equalized_odds_diff', sa.Numeric(precision=5, scale=4), nullable=True),
    sa.Column('fairness_dial_setting', sa.Numeric(precision=3, scale=2), nullable=False),
    sa.Column('passed', sa.Boolean(), nullable=False),
    sa.Column('violation_details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['evaluation_run_id'], ['evaluation_runs.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['training_run_id'], ['training_runs.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_fairness_reports_attribute', 'fairness_reports', ['protected_attribute'], unique=False)
    op.create_index('ix_fairness_reports_model', 'fairness_reports', ['model_version'], unique=False)
    op.create_table('offer_comparisons',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('student_id', sa.UUID(), nullable=False),
    sa.Column('offer_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('ai_analysis', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['student_id'], ['student_profiles.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('onboarding_progress',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('student_id', sa.UUID(), nullable=False),
    sa.Column('steps_completed', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('completion_percentage', sa.Integer(), nullable=False),
    sa.Column('last_step_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('nudge_sent_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['student_id'], ['student_profiles.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('student_id')
    )
    op.create_table('programs',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('institution_id', sa.UUID(), nullable=False),
    sa.Column('program_name', sa.String(length=255), nullable=False),
    sa.Column('degree_type', sa.String(length=30), nullable=False),
    sa.Column('department', sa.String(length=255), nullable=True),
    sa.Column('duration_months', sa.Integer(), nullable=True),
    sa.Column('tuition', sa.Integer(), nullable=True),
    sa.Column('acceptance_rate', sa.Numeric(precision=5, scale=4), nullable=True),
    sa.Column('requirements', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('description_text', sa.Text(), nullable=True),
    sa.Column('current_preferences_text', sa.Text(), nullable=True),
    sa.Column('is_published', sa.Boolean(), nullable=False),
    sa.Column('application_deadline', sa.Date(), nullable=True),
    sa.Column('program_start_date', sa.Date(), nullable=True),
    sa.Column('page_header_image_url', sa.String(length=1000), nullable=True),
    sa.Column('highlights', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('faculty_contacts', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['institution_id'], ['institutions.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_programs_institution_id'), 'programs', ['institution_id'], unique=False)
    op.create_index('ix_programs_institution_published', 'programs', ['institution_id', 'is_published'], unique=False)
    op.create_table('reviewers',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('institution_id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('department', sa.String(length=255), nullable=True),
    sa.Column('specializations', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('current_workload', sa.Integer(), nullable=False),
    sa.Column('max_workload', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['institution_id'], ['institutions.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('saved_lists',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('student_id', sa.UUID(), nullable=False),
    sa.Column('list_name', sa.String(length=100), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['student_id'], ['student_profiles.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('student_calendar',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('student_id', sa.UUID(), nullable=False),
    sa.Column('entry_type', sa.String(length=20), nullable=True),
    sa.Column('reference_id', sa.UUID(), nullable=True),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
    sa.Column('end_time', sa.DateTime(timezone=True), nullable=True),
    sa.Column('reminder_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['student_id'], ['student_profiles.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_student_calendar_student_id'), 'student_calendar', ['student_id'], unique=False)
    op.create_table('student_documents',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('student_id', sa.UUID(), nullable=False),
    sa.Column('document_type', sa.String(length=50), nullable=False),
    sa.Column('file_name', sa.String(length=255), nullable=False),
    sa.Column('file_url', sa.String(length=1000), nullable=True),
    sa.Column('file_size_bytes', sa.Integer(), nullable=True),
    sa.Column('mime_type', sa.String(length=100), nullable=True),
    sa.Column('extracted_text', sa.Text(), nullable=True),
    sa.Column('uploaded_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['student_id'], ['student_profiles.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_student_documents_student_id'), 'student_documents', ['student_id'], unique=False)
    op.create_table('student_features',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('student_id', sa.UUID(), nullable=False),
    sa.Column('feature_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['student_id'], ['student_profiles.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('student_id')
    )
    op.create_table('student_preferences',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('student_id', sa.UUID(), nullable=False),
    sa.Column('preferred_countries', sa.ARRAY(sa.String()), nullable=True),
    sa.Column('preferred_regions', sa.ARRAY(sa.String()), nullable=True),
    sa.Column('preferred_city_size', sa.String(length=30), nullable=True),
    sa.Column('preferred_climate', sa.String(length=50), nullable=True),
    sa.Column('budget_min', sa.Integer(), nullable=True),
    sa.Column('budget_max', sa.Integer(), nullable=True),
    sa.Column('funding_requirement', sa.String(length=30), nullable=True),
    sa.Column('program_size_preference', sa.String(length=20), nullable=True),
    sa.Column('career_goals', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('values_priorities', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('dealbreakers', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('goals_text', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['student_id'], ['student_profiles.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('student_id')
    )
    op.create_table('test_scores',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('student_id', sa.UUID(), nullable=False),
    sa.Column('test_type', sa.String(length=50), nullable=False),
    sa.Column('total_score', sa.Integer(), nullable=True),
    sa.Column('section_scores', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('test_date', sa.Date(), nullable=True),
    sa.Column('is_official', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['student_id'], ['student_profiles.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_test_scores_student_id'), 'test_scores', ['student_id'], unique=False)
    op.create_table('application_checklists',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('student_id', sa.UUID(), nullable=False),
    sa.Column('program_id', sa.UUID(), nullable=False),
    sa.Column('items', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('completion_percentage', sa.Integer(), nullable=False),
    sa.Column('auto_generated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['program_id'], ['programs.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['student_id'], ['student_profiles.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('applications',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('student_id', sa.UUID(), nullable=False),
    sa.Column('program_id', sa.UUID(), nullable=False),
    sa.Column('status', sa.String(length=30), nullable=True),
    sa.Column('match_score', sa.Numeric(precision=5, scale=4), nullable=True),
    sa.Column('match_reasoning_text', sa.Text(), nullable=True),
    sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('decision', sa.String(length=20), nullable=True),
    sa.Column('decision_by', sa.UUID(), nullable=True),
    sa.Column('decision_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('decision_notes', sa.Text(), nullable=True),
    sa.Column('completeness_status', sa.String(length=30), nullable=True),
    sa.Column('missing_items', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['decision_by'], ['reviewers.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['program_id'], ['programs.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['student_id'], ['student_profiles.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('student_id', 'program_id')
    )
    op.create_index(op.f('ix_applications_program_id'), 'applications', ['program_id'], unique=False)
    op.create_index(op.f('ix_applications_student_id'), 'applications', ['student_id'], unique=False)
    op.create_table('conversations',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('student_id', sa.UUID(), nullable=False),
    sa.Column('institution_id', sa.UUID(), nullable=False),
    sa.Column('program_id', sa.UUID(), nullable=True),
    sa.Column('subject', sa.String(length=500), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('last_message_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['institution_id'], ['institutions.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['program_id'], ['programs.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['student_id'], ['student_profiles.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('enrichment_records',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('program_id', sa.UUID(), nullable=True),
    sa.Column('institution_id', sa.UUID(), nullable=True),
    sa.Column('enrichment_type', sa.String(length=30), nullable=False),
    sa.Column('source_id', sa.UUID(), nullable=False),
    sa.Column('data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('confidence', sa.Numeric(precision=3, scale=2), nullable=True),
    sa.Column('effective_date', sa.Date(), nullable=True),
    sa.Column('expires_at', sa.Date(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['institution_id'], ['institutions.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['program_id'], ['programs.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['source_id'], ['data_sources.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('events',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('institution_id', sa.UUID(), nullable=False),
    sa.Column('program_id', sa.UUID(), nullable=True),
    sa.Column('event_name', sa.String(length=255), nullable=False),
    sa.Column('event_type', sa.String(length=30), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('location', sa.String(length=500), nullable=True),
    sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
    sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),
    sa.Column('capacity', sa.Integer(), nullable=True),
    sa.Column('rsvp_count', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['institution_id'], ['institutions.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['program_id'], ['programs.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('extracted_programs',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('crawl_job_id', sa.UUID(), nullable=False),
    sa.Column('source_id', sa.UUID(), nullable=False),
    sa.Column('raw_data_id', sa.UUID(), nullable=True),
    sa.Column('source_url', sa.String(length=1000), nullable=True),
    sa.Column('institution_name', sa.String(length=255), nullable=True),
    sa.Column('institution_country', sa.String(length=100), nullable=True),
    sa.Column('institution_city', sa.String(length=100), nullable=True),
    sa.Column('institution_type', sa.String(length=50), nullable=True),
    sa.Column('institution_website', sa.String(length=1000), nullable=True),
    sa.Column('program_name', sa.String(length=255), nullable=True),
    sa.Column('degree_type', sa.String(length=30), nullable=True),
    sa.Column('department', sa.String(length=255), nullable=True),
    sa.Column('duration_months', sa.Integer(), nullable=True),
    sa.Column('tuition', sa.Integer(), nullable=True),
    sa.Column('tuition_currency', sa.String(length=10), nullable=True),
    sa.Column('acceptance_rate', sa.Numeric(precision=5, scale=4), nullable=True),
    sa.Column('requirements', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('description_text', sa.Text(), nullable=True),
    sa.Column('application_deadline', sa.Date(), nullable=True),
    sa.Column('program_start_date', sa.Date(), nullable=True),
    sa.Column('highlights', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('faculty_contacts', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('rankings', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('financial_aid_info', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('extraction_confidence', sa.Numeric(precision=3, scale=2), nullable=True),
    sa.Column('field_confidences', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('extraction_model', sa.String(length=50), nullable=True),
    sa.Column('raw_extracted_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('matched_institution_id', sa.UUID(), nullable=True),
    sa.Column('matched_program_id', sa.UUID(), nullable=True),
    sa.Column('match_type', sa.String(length=20), nullable=True),
    sa.Column('review_status', sa.String(length=20), nullable=False),
    sa.Column('reviewed_by', sa.UUID(), nullable=True),
    sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('review_notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['crawl_job_id'], ['crawl_jobs.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['matched_institution_id'], ['institutions.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['matched_program_id'], ['programs.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['raw_data_id'], ['raw_ingested_data.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['source_id'], ['data_sources.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_extracted_programs_crawl_job_id'), 'extracted_programs', ['crawl_job_id'], unique=False)
    op.create_index('ix_extracted_programs_review', 'extracted_programs', ['review_status', 'extraction_confidence'], unique=False)
    op.create_table('historical_outcomes',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('program_id', sa.UUID(), nullable=False),
    sa.Column('year', sa.Integer(), nullable=False),
    sa.Column('applicant_profile_summary', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('outcome', sa.String(length=20), nullable=True),
    sa.Column('enrolled', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['program_id'], ['programs.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_historical_outcomes_program_id'), 'historical_outcomes', ['program_id'], unique=False)
    op.create_table('institution_features',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('program_id', sa.UUID(), nullable=False),
    sa.Column('feature_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['program_id'], ['programs.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('program_id')
    )
    op.create_table('match_results',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('student_id', sa.UUID(), nullable=False),
    sa.Column('program_id', sa.UUID(), nullable=False),
    sa.Column('match_score', sa.Numeric(precision=5, scale=4), nullable=True),
    sa.Column('match_tier', sa.Integer(), nullable=True),
    sa.Column('score_breakdown', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('reasoning_text', sa.Text(), nullable=True),
    sa.Column('model_version', sa.String(length=50), nullable=True),
    sa.Column('computed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('is_stale', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['program_id'], ['programs.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['student_id'], ['student_profiles.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('student_id', 'program_id')
    )
    op.create_index(op.f('ix_match_results_program_id'), 'match_results', ['program_id'], unique=False)
    op.create_index(op.f('ix_match_results_student_id'), 'match_results', ['student_id'], unique=False)
    op.create_table('prediction_logs',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('student_id', sa.UUID(), nullable=False),
    sa.Column('program_id', sa.UUID(), nullable=False),
    sa.Column('predicted_score', sa.Numeric(precision=5, scale=4), nullable=True),
    sa.Column('predicted_tier', sa.Integer(), nullable=True),
    sa.Column('model_version', sa.String(length=50), nullable=True),
    sa.Column('features_used', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('predicted_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('actual_outcome', sa.String(length=20), nullable=True),
    sa.Column('outcome_recorded_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['program_id'], ['programs.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['student_id'], ['student_profiles.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('rubrics',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('institution_id', sa.UUID(), nullable=False),
    sa.Column('program_id', sa.UUID(), nullable=True),
    sa.Column('rubric_name', sa.String(length=255), nullable=False),
    sa.Column('criteria', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['institution_id'], ['institutions.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['program_id'], ['programs.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('saved_list_items',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('list_id', sa.UUID(), nullable=False),
    sa.Column('program_id', sa.UUID(), nullable=False),
    sa.Column('added_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['list_id'], ['saved_lists.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['program_id'], ['programs.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('list_id', 'program_id')
    )
    op.create_table('student_engagement_signals',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('student_id', sa.UUID(), nullable=False),
    sa.Column('program_id', sa.UUID(), nullable=False),
    sa.Column('signal_type', sa.String(length=30), nullable=False),
    sa.Column('signal_value', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['program_id'], ['programs.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['student_id'], ['student_profiles.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_engagement_student_program_type', 'student_engagement_signals', ['student_id', 'program_id', 'signal_type'], unique=False)
    op.create_index(op.f('ix_student_engagement_signals_program_id'), 'student_engagement_signals', ['program_id'], unique=False)
    op.create_index(op.f('ix_student_engagement_signals_student_id'), 'student_engagement_signals', ['student_id'], unique=False)
    op.create_table('student_essays',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('student_id', sa.UUID(), nullable=False),
    sa.Column('program_id', sa.UUID(), nullable=False),
    sa.Column('prompt_text', sa.Text(), nullable=True),
    sa.Column('essay_version', sa.Integer(), nullable=False),
    sa.Column('content', sa.Text(), nullable=True),
    sa.Column('word_count', sa.Integer(), nullable=True),
    sa.Column('ai_feedback', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['program_id'], ['programs.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['student_id'], ['student_profiles.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('student_resumes',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('student_id', sa.UUID(), nullable=False),
    sa.Column('resume_version', sa.Integer(), nullable=False),
    sa.Column('content', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('rendered_pdf_url', sa.String(length=1000), nullable=True),
    sa.Column('ai_suggestions', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('target_program_id', sa.UUID(), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['student_id'], ['student_profiles.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['target_program_id'], ['programs.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('target_segments',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('institution_id', sa.UUID(), nullable=False),
    sa.Column('program_id', sa.UUID(), nullable=True),
    sa.Column('segment_name', sa.String(length=255), nullable=False),
    sa.Column('criteria', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['institution_id'], ['institutions.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['program_id'], ['programs.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('application_scores',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('application_id', sa.UUID(), nullable=False),
    sa.Column('reviewer_id', sa.UUID(), nullable=False),
    sa.Column('rubric_id', sa.UUID(), nullable=False),
    sa.Column('criterion_scores', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('total_weighted_score', sa.Numeric(precision=6, scale=3), nullable=True),
    sa.Column('reviewer_notes', sa.Text(), nullable=True),
    sa.Column('scored_by_type', sa.String(length=20), nullable=True),
    sa.Column('scored_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['application_id'], ['applications.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['reviewer_id'], ['reviewers.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['rubric_id'], ['rubrics.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('application_submissions',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('application_id', sa.UUID(), nullable=False),
    sa.Column('submitted_documents', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('submission_package_url', sa.String(length=1000), nullable=True),
    sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('confirmation_number', sa.String(length=20), nullable=True),
    sa.ForeignKeyConstraint(['application_id'], ['applications.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('application_id'),
    sa.UniqueConstraint('confirmation_number')
    )
    op.create_table('campaigns',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('institution_id', sa.UUID(), nullable=False),
    sa.Column('program_id', sa.UUID(), nullable=True),
    sa.Column('segment_id', sa.UUID(), nullable=True),
    sa.Column('campaign_name', sa.String(length=255), nullable=False),
    sa.Column('campaign_type', sa.String(length=30), nullable=True),
    sa.Column('message_subject', sa.String(length=500), nullable=True),
    sa.Column('message_body', sa.Text(), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('scheduled_send_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['institution_id'], ['institutions.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['program_id'], ['programs.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['segment_id'], ['target_segments.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('enrollment_records',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('application_id', sa.UUID(), nullable=False),
    sa.Column('student_id', sa.UUID(), nullable=False),
    sa.Column('program_id', sa.UUID(), nullable=False),
    sa.Column('enrolled_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('enrollment_status', sa.String(length=20), nullable=True),
    sa.Column('start_term', sa.String(length=20), nullable=True),
    sa.ForeignKeyConstraint(['application_id'], ['applications.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['program_id'], ['programs.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['student_id'], ['student_profiles.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('application_id')
    )
    op.create_table('event_rsvps',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('event_id', sa.UUID(), nullable=False),
    sa.Column('student_id', sa.UUID(), nullable=False),
    sa.Column('rsvp_status', sa.String(length=20), nullable=True),
    sa.Column('registered_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('attended_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['student_id'], ['student_profiles.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('event_id', 'student_id')
    )
    op.create_table('interviews',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('application_id', sa.UUID(), nullable=False),
    sa.Column('interviewer_id', sa.UUID(), nullable=False),
    sa.Column('interview_type', sa.String(length=20), nullable=True),
    sa.Column('proposed_times', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('confirmed_time', sa.DateTime(timezone=True), nullable=True),
    sa.Column('location_or_link', sa.String(length=500), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('duration_minutes', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['application_id'], ['applications.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['interviewer_id'], ['reviewers.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('messages',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('conversation_id', sa.UUID(), nullable=False),
    sa.Column('sender_type', sa.String(length=20), nullable=True),
    sa.Column('sender_id', sa.UUID(), nullable=False),
    sa.Column('message_body', sa.Text(), nullable=False),
    sa.Column('sent_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['sender_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_messages_conversation_id'), 'messages', ['conversation_id'], unique=False)
    op.create_table('offer_letters',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('application_id', sa.UUID(), nullable=False),
    sa.Column('offer_type', sa.String(length=30), nullable=True),
    sa.Column('tuition_amount', sa.Integer(), nullable=True),
    sa.Column('scholarship_amount', sa.Integer(), nullable=False),
    sa.Column('assistantship_details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('financial_package_total', sa.Integer(), nullable=True),
    sa.Column('conditions', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('response_deadline', sa.Date(), nullable=True),
    sa.Column('generated_letter_url', sa.String(length=1000), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('student_response', sa.String(length=20), nullable=True),
    sa.Column('response_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('decline_reason', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['application_id'], ['applications.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('application_id')
    )
    op.create_table('outcome_records',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('prediction_log_id', sa.UUID(), nullable=False),
    sa.Column('student_id', sa.UUID(), nullable=False),
    sa.Column('program_id', sa.UUID(), nullable=False),
    sa.Column('predicted_score', sa.Numeric(precision=5, scale=4), nullable=False),
    sa.Column('predicted_tier', sa.Integer(), nullable=False),
    sa.Column('actual_outcome', sa.String(length=30), nullable=False),
    sa.Column('outcome_source', sa.String(length=30), nullable=False),
    sa.Column('outcome_confidence', sa.Numeric(precision=3, scale=2), nullable=False),
    sa.Column('features_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('outcome_recorded_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['prediction_log_id'], ['prediction_logs.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['program_id'], ['programs.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['student_id'], ['student_profiles.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_outcome_records_outcome', 'outcome_records', ['actual_outcome'], unique=False)
    op.create_index('ix_outcome_records_program', 'outcome_records', ['program_id'], unique=False)
    op.create_index('ix_outcome_records_recorded_at', 'outcome_records', ['outcome_recorded_at'], unique=False)
    op.create_index('ix_outcome_records_student', 'outcome_records', ['student_id'], unique=False)
    op.create_table('review_assignments',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('application_id', sa.UUID(), nullable=False),
    sa.Column('reviewer_id', sa.UUID(), nullable=False),
    sa.Column('assigned_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('due_date', sa.Date(), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.ForeignKeyConstraint(['application_id'], ['applications.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['reviewer_id'], ['reviewers.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('touchpoints',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('student_id', sa.UUID(), nullable=False),
    sa.Column('institution_id', sa.UUID(), nullable=True),
    sa.Column('program_id', sa.UUID(), nullable=True),
    sa.Column('application_id', sa.UUID(), nullable=True),
    sa.Column('touchpoint_type', sa.String(length=100), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['application_id'], ['applications.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['institution_id'], ['institutions.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['program_id'], ['programs.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['student_id'], ['student_profiles.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_touchpoints_application', 'touchpoints', ['application_id'], unique=False)
    op.create_index('ix_touchpoints_created', 'touchpoints', ['created_at'], unique=False)
    op.create_index('ix_touchpoints_institution', 'touchpoints', ['institution_id'], unique=False)
    op.create_index('ix_touchpoints_student', 'touchpoints', ['student_id'], unique=False)
    op.create_index('ix_touchpoints_type', 'touchpoints', ['touchpoint_type'], unique=False)
    op.create_table('campaign_recipients',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('campaign_id', sa.UUID(), nullable=False),
    sa.Column('student_id', sa.UUID(), nullable=False),
    sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('opened_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('clicked_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('responded_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['student_id'], ['student_profiles.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('campaign_id', 'student_id')
    )
    op.create_table('interview_scores',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('interview_id', sa.UUID(), nullable=False),
    sa.Column('interviewer_id', sa.UUID(), nullable=False),
    sa.Column('rubric_id', sa.UUID(), nullable=True),
    sa.Column('criterion_scores', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('total_weighted_score', sa.Numeric(precision=6, scale=3), nullable=True),
    sa.Column('interviewer_notes', sa.Text(), nullable=True),
    sa.Column('recommendation', sa.String(length=20), nullable=True),
    sa.ForeignKeyConstraint(['interview_id'], ['interviews.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['interviewer_id'], ['reviewers.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['rubric_id'], ['rubrics.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('interview_scores')
    op.drop_table('campaign_recipients')
    op.drop_index('ix_touchpoints_type', table_name='touchpoints')
    op.drop_index('ix_touchpoints_student', table_name='touchpoints')
    op.drop_index('ix_touchpoints_institution', table_name='touchpoints')
    op.drop_index('ix_touchpoints_created', table_name='touchpoints')
    op.drop_index('ix_touchpoints_application', table_name='touchpoints')
    op.drop_table('touchpoints')
    op.drop_table('review_assignments')
    op.drop_index('ix_outcome_records_student', table_name='outcome_records')
    op.drop_index('ix_outcome_records_recorded_at', table_name='outcome_records')
    op.drop_index('ix_outcome_records_program', table_name='outcome_records')
    op.drop_index('ix_outcome_records_outcome', table_name='outcome_records')
    op.drop_table('outcome_records')
    op.drop_table('offer_letters')
    op.drop_index(op.f('ix_messages_conversation_id'), table_name='messages')
    op.drop_table('messages')
    op.drop_table('interviews')
    op.drop_table('event_rsvps')
    op.drop_table('enrollment_records')
    op.drop_table('campaigns')
    op.drop_table('application_submissions')
    op.drop_table('application_scores')
    op.drop_table('target_segments')
    op.drop_table('student_resumes')
    op.drop_table('student_essays')
    op.drop_index(op.f('ix_student_engagement_signals_student_id'), table_name='student_engagement_signals')
    op.drop_index(op.f('ix_student_engagement_signals_program_id'), table_name='student_engagement_signals')
    op.drop_index('ix_engagement_student_program_type', table_name='student_engagement_signals')
    op.drop_table('student_engagement_signals')
    op.drop_table('saved_list_items')
    op.drop_table('rubrics')
    op.drop_table('prediction_logs')
    op.drop_index(op.f('ix_match_results_student_id'), table_name='match_results')
    op.drop_index(op.f('ix_match_results_program_id'), table_name='match_results')
    op.drop_table('match_results')
    op.drop_table('institution_features')
    op.drop_index(op.f('ix_historical_outcomes_program_id'), table_name='historical_outcomes')
    op.drop_table('historical_outcomes')
    op.drop_index('ix_extracted_programs_review', table_name='extracted_programs')
    op.drop_index(op.f('ix_extracted_programs_crawl_job_id'), table_name='extracted_programs')
    op.drop_table('extracted_programs')
    op.drop_table('events')
    op.drop_table('enrichment_records')
    op.drop_table('conversations')
    op.drop_index(op.f('ix_applications_student_id'), table_name='applications')
    op.drop_index(op.f('ix_applications_program_id'), table_name='applications')
    op.drop_table('applications')
    op.drop_table('application_checklists')
    op.drop_index(op.f('ix_test_scores_student_id'), table_name='test_scores')
    op.drop_table('test_scores')
    op.drop_table('student_preferences')
    op.drop_table('student_features')
    op.drop_index(op.f('ix_student_documents_student_id'), table_name='student_documents')
    op.drop_table('student_documents')
    op.drop_index(op.f('ix_student_calendar_student_id'), table_name='student_calendar')
    op.drop_table('student_calendar')
    op.drop_table('saved_lists')
    op.drop_table('reviewers')
    op.drop_index('ix_programs_institution_published', table_name='programs')
    op.drop_index(op.f('ix_programs_institution_id'), table_name='programs')
    op.drop_table('programs')
    op.drop_table('onboarding_progress')
    op.drop_table('offer_comparisons')
    op.drop_index('ix_fairness_reports_model', table_name='fairness_reports')
    op.drop_index('ix_fairness_reports_attribute', table_name='fairness_reports')
    op.drop_table('fairness_reports')
    op.drop_index(op.f('ix_crm_records_student_id'), table_name='crm_records')
    op.drop_index(op.f('ix_crm_records_institution_id'), table_name='crm_records')
    op.drop_index('ix_crm_institution_student', table_name='crm_records')
    op.drop_table('crm_records')
    op.drop_index(op.f('ix_activities_student_id'), table_name='activities')
    op.drop_table('activities')
    op.drop_index(op.f('ix_academic_records_student_id'), table_name='academic_records')
    op.drop_table('academic_records')
    op.drop_index('ix_ab_test_student_experiment', table_name='ab_test_assignments')
    op.drop_index('ix_ab_test_experiment', table_name='ab_test_assignments')
    op.drop_table('ab_test_assignments')
    op.drop_index('ix_training_runs_status', table_name='training_runs')
    op.drop_index('ix_training_runs_started', table_name='training_runs')
    op.drop_table('training_runs')
    op.drop_table('student_profiles')
    op.drop_index(op.f('ix_source_url_patterns_source_id'), table_name='source_url_patterns')
    op.drop_table('source_url_patterns')
    op.drop_table('raw_ingested_data')
    op.drop_index('ix_notifications_user_unread', table_name='notifications')
    op.drop_index(op.f('ix_notifications_user_id'), table_name='notifications')
    op.drop_index('ix_notifications_created', table_name='notifications')
    op.drop_table('notifications')
    op.drop_table('notification_preferences')
    op.drop_table('institutions')
    op.drop_table('crawl_schedules')
    op.drop_index(op.f('ix_crawl_jobs_source_id'), table_name='crawl_jobs')
    op.drop_table('crawl_jobs')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_cognito_sub'), table_name='users')
    op.drop_table('users')
    op.drop_table('model_registry')
    op.drop_index('ix_evaluation_runs_started', table_name='evaluation_runs')
    op.drop_index('ix_evaluation_runs_model', table_name='evaluation_runs')
    op.drop_table('evaluation_runs')
    op.drop_index('ix_embeddings_hnsw', table_name='embeddings', postgresql_using='hnsw', postgresql_with={'m': 16, 'ef_construction': 64}, postgresql_ops={'embedding': 'vector_cosine_ops'})
    op.drop_table('embeddings')
    op.drop_index('ix_drift_snapshots_type', table_name='drift_snapshots')
    op.drop_index('ix_drift_snapshots_created', table_name='drift_snapshots')
    op.drop_table('drift_snapshots')
    op.drop_table('data_sources')
    # ### end Alembic commands ###
