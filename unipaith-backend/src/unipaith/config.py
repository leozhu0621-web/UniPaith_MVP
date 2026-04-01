from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @model_validator(mode="after")
    def _propagate_api_key(self) -> "Settings":
        """If individual LLM API keys are empty, use the shared openai_api_key."""
        if self.openai_api_key:
            if not self.llm_feature_api_key:
                self.llm_feature_api_key = self.openai_api_key
            if not self.llm_reasoning_api_key:
                self.llm_reasoning_api_key = self.openai_api_key
        return self

    # App
    app_name: str = "UniPaith API"
    debug: bool = False
    environment: str = "development"

    # Database
    database_url: str = "postgresql+asyncpg://unipaith:unipaith@localhost:5432/unipaith"

    # AWS
    aws_region: str = "us-east-1"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""

    # Cognito
    cognito_user_pool_id: str = ""
    cognito_app_client_id: str = ""
    cognito_domain: str = ""
    cognito_bypass: bool = False

    # S3
    s3_bucket_name: str = "unipaith-documents"
    s3_presigned_url_expiry: int = 3600
    s3_local_mode: bool = False
    s3_local_path: str = "./uploads"

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Rate limiting
    rate_limit_per_minute: int = 60
    rate_limit_enabled: bool = True

    # Scheduler
    scheduler_enabled: bool = False
    scheduler_auto_enable_non_test: bool = True
    scheduler_require_leader: bool = False
    scheduler_is_leader: bool = True
    scheduler_misfire_grace_seconds: int = 300
    scheduler_self_driving_enabled: bool = True
    scheduler_self_driving_interval_minutes: int = 30

    # Logging
    log_level: str = "INFO"

    # OpenAI API key (used when gpu_mode is "openai" or "local" with OpenAI)
    openai_api_key: str = ""

    # LLM - Feature Extraction
    llm_feature_base_url: str = "https://api.openai.com/v1"
    llm_feature_model: str = "gpt-4o"
    llm_feature_api_key: str = ""  # auto-filled from openai_api_key
    llm_feature_max_tokens: int = 2048
    llm_feature_temperature: float = 0.1

    # LLM - Reasoning
    llm_reasoning_base_url: str = "https://api.openai.com/v1"
    llm_reasoning_model: str = "gpt-4o"
    llm_reasoning_api_key: str = ""  # auto-filled from openai_api_key
    llm_reasoning_max_tokens: int = 1024
    llm_reasoning_temperature: float = 0.7

    # Embedding (OpenAI's embedding model)
    embedding_base_url: str = "https://api.openai.com/v1"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimension: int = 1536  # OpenAI text-embedding-3-small outputs 1536

    # Matching
    matching_candidate_count: int = 100
    matching_final_count: int = 30
    matching_tier1_threshold: float = 0.80
    matching_tier2_threshold: float = 0.60
    matching_stale_hours: int = 24
    matching_weight_similarity: float = 0.40
    matching_weight_historical: float = 0.25
    matching_weight_institution_pref: float = 0.20
    matching_weight_student_pref: float = 0.15

    # AI dev mode
    ai_mock_mode: bool = False
    ai_refresh_cooldown_seconds: int = 300

    # GPU infrastructure (cloud-first)
    gpu_mode: str = "aws"  # "aws" | "local" | "mock" (mock only for tests)
    gpu_8b_instance_id: str = ""
    gpu_70b_instance_id: str = ""
    gpu_8b_endpoint: str = "http://localhost:8001"
    gpu_70b_endpoint: str = "http://localhost:8002"
    gpu_70b_cold_start_timeout: int = 300
    gpu_health_check_interval: int = 5
    gpu_70b_idle_shutdown_minutes: int = 15
    gpu_70b_max_daily_hours: float = 4.0

    # Cost tracking
    gpu_monthly_budget_cap: float = 2000.0
    gpu_8b_hourly_cost: float = 1.01
    gpu_70b_hourly_cost: float = 5.67

    # --- Self-Improving Loop (Phase 4) ---
    # Outcome collection
    outcome_min_decisions_for_training: int = 50
    outcome_collection_lookback_days: int = 365

    # Evaluation (Person B)
    eval_schedule_hours: int = 24
    eval_accuracy_threshold: float = 0.65
    eval_drift_pvalue_threshold: float = 0.01
    eval_min_predictions_for_eval: int = 30
    eval_retrain_min_new_outcomes: int = 20
    eval_retrain_max_hours_without_training: int = 72

    # Training (Person C)
    training_schedule_hours: int = 168
    training_test_split: float = 0.2
    training_cv_folds: int = 5
    training_optuna_trials: int = 50
    training_max_duration_minutes: int = 60
    training_fast_cv_folds: int = 3
    training_fast_optuna_trials: int = 12
    training_fast_max_duration_minutes: int = 15
    training_default_cycle_mode: str = "fast"
    training_default_manual_mode: str = "full"
    training_recent_outcome_window_days: int = 365
    training_degraded_mode_failure_rate_threshold: float = 0.5
    training_degraded_mode_min_runs: int = 4

    # Model management
    model_promotion_min_improvement: float = 0.02
    model_ab_test_traffic_pct: float = 0.10
    model_ab_test_min_samples: int = 100
    model_rollback_degradation_threshold: float = 0.05

    # Fairness
    fairness_dial: float = 0.5
    fairness_protected_attributes: list[str] = [
        "nationality", "gender", "ethnicity", "first_generation"
    ]
    fairness_max_disparity: float = 0.15
    fairness_check_on_promotion: bool = True

    # Autonomous AI control plane runtime policy
    ai_autonomy_enabled: bool = True
    ai_autonomy_auto_fix: bool = True
    ai_autonomy_emergency_stop: bool = False
    ai_autonomy_max_consecutive_failures: int = 5
    ai_request_timeout_seconds: int = 45
    ai_request_max_retries: int = 3
    ai_request_backoff_seconds: int = 2

    # --- Data Crawler (Phase 5) ---
    crawler_concurrent_requests: int = 4
    crawler_download_delay: float = 2.0
    crawler_max_pages_per_source: int = 500
    crawler_request_timeout: int = 30
    crawler_respect_robots_txt: bool = True
    crawler_user_agent: str = "UniPaith-Bot/1.0 (+https://unipaith.com/bot)"
    crawler_splash_url: str = "http://localhost:8050"

    # LLM extraction
    crawler_extraction_model: str = "mistral"
    crawler_extraction_max_tokens: int = 16000
    crawler_extraction_temperature: float = 0.1
    crawler_max_html_chars: int = 50000

    # Validation & deduplication
    crawler_fuzzy_match_threshold: int = 85
    crawler_confidence_auto_ingest: float = 0.80
    crawler_confidence_review_queue: float = 0.50

    # Enrichment
    crawler_merge_strategy: str = "highest_confidence"
    crawler_ranking_sources: list[str] = ["us_news", "qs", "times_higher_education"]

    # Scheduling
    crawler_default_frequency_hours: int = 168
    crawler_stale_threshold_days: int = 30
    crawler_max_retries: int = 3
    crawler_retry_delay_hours: int = 6

    # Historical outcomes
    crawler_seed_historical_years: int = 3

    # Notifications — Amazon SES
    ses_region: str = "us-east-1"
    ses_sender_email: str = "noreply@unipaith.co"
    ses_sender_name: str = "UniPaith"
    notifications_enabled: bool = False

    # Essay Workshop
    essay_max_drafts: int = 20
    essay_feedback_max_tokens: int = 1500
    essay_feedback_temperature: float = 0.6

    # Resume Workshop
    resume_max_versions: int = 10
    resume_feedback_max_tokens: int = 1200
    resume_score_max_tokens: int = 800

    # Review Pipeline
    review_auto_assign: bool = True
    review_default_due_days: int = 14
    review_min_reviewers: int = 1
    review_max_reviewers: int = 3

    # Messaging
    message_max_length: int = 5000
    message_rate_limit_per_hour: int = 30

    # Events
    event_rsvp_reminder_hours: int = 24

    # Notifications
    notification_retention_days: int = 90


settings = Settings()
