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

    @model_validator(mode="after")
    def _inject_db_password(self) -> "Settings":
        """Rebuild DATABASE_URL with DB_PASSWORD when the env provides one.

        Production injects DB_PASSWORD from AWS Secrets Manager. Without
        this hook, the password sits in DATABASE_URL too — which means
        any rotation requires a coordinated update of two values. With
        this hook the URL can be `postgresql+asyncpg://user@host:port/db`
        (no password) and we splice DB_PASSWORD in at boot. If the URL
        already has a password, we leave it alone (local dev keeps
        working). If DB_PASSWORD is empty, no-op.
        """
        if not self.db_password:
            return self
        # Avoid clobbering an explicitly-set password in the URL — that's
        # the local-dev path. Detect by looking for `:<something>@` between
        # the scheme and the host.
        from urllib.parse import urlparse, urlunparse

        parsed = urlparse(self.database_url)
        if parsed.password:
            return self  # URL has its own password; respect it
        if not parsed.username:
            return self  # malformed; let it fail loudly elsewhere
        netloc = f"{parsed.username}:{self.db_password}@{parsed.hostname}"
        if parsed.port:
            netloc += f":{parsed.port}"
        self.database_url = urlunparse(parsed._replace(netloc=netloc))
        return self

    # App
    app_name: str = "UniPaith API"
    debug: bool = False
    environment: str = "development"

    # Database
    database_url: str = "postgresql+asyncpg://unipaith:unipaith@localhost:5432/unipaith"
    # Optional — when set, splice into DATABASE_URL at boot (prod ECS task
    # uses this via the DB_PASSWORD secret pulled from AWS Secrets Manager).
    db_password: str = ""
    db_pool_size: int = 30
    db_pool_overflow: int = 20
    db_pool_recycle: int = 1800

    # AWS
    aws_region: str = "us-east-1"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""

    # Cognito
    cognito_user_pool_id: str = ""
    cognito_app_client_id: str = ""
    cognito_domain: str = ""
    cognito_bypass: bool = False
    cognito_redirect_uri: str = ""

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

    # Knowledge engine loop (legacy — replaced by pipeline, kept for backward compat)
    engine_loop_enabled: bool = True
    engine_loop_interval_minutes: int = 5
    engine_loop_default_rpm: int = 10
    engine_bootstrap_enabled: bool = True
    engine_bootstrap_urls: str = ""

    # Continuous pipeline
    pipeline_enabled: bool = True
    pipeline_crawl_rpm: int = 10
    pipeline_crawl_concurrent: int = 10
    pipeline_extract_ollama_url: str = "http://localhost:11434/v1"
    pipeline_extract_ollama_model: str = "qwen2.5:7b"
    pipeline_extract_heartbeat_timeout_seconds: int = 300
    pipeline_extract_budget_per_hour: float = 5.0
    pipeline_extract_cost_per_doc: float = 0.015
    pipeline_extract_idle_seconds: int = 5
    pipeline_ml_check_seconds: int = 60
    pipeline_ml_threshold: int = 30
    pipeline_ml_cooldown_seconds: int = 300

    # Logging
    log_level: str = "INFO"

    # OpenAI API key — optional. User-facing LLM surfaces use Anthropic via
    # `unipaith.ai.client` (see Plan 2); this is retained only for opt-in use.
    openai_api_key: str = ""

    # Anthropic — primary user-facing LLM provider (Plan 2)
    anthropic_api_key: str = ""

    # Voyage — embedding provider paired with Anthropic
    voyage_api_key: str = ""

    # LLM - Feature Extraction (Haiku-class — extractor / validator / emitter)
    llm_feature_base_url: str = "https://api.anthropic.com"
    llm_feature_model: str = "claude-haiku-4-5"
    llm_feature_api_key: str = ""  # auto-filled from openai_api_key for legacy paths
    llm_feature_max_tokens: int = 2048
    llm_feature_temperature: float = 0.1

    # LLM - Reasoning (Sonnet-class — orchestrator / rationale / coach)
    llm_reasoning_base_url: str = "https://api.anthropic.com"
    llm_reasoning_model: str = "claude-sonnet-4-6"
    llm_reasoning_api_key: str = ""  # auto-filled from openai_api_key for legacy paths
    llm_reasoning_max_tokens: int = 1024
    llm_reasoning_temperature: float = 0.7

    # LLM - Flagship (Opus-class — strategy first-pass, packet summary,
    # cohort review summary). Spec 03 §2: used only for "the single
    # defining moment" of a session. Default Opus 4.8.
    anthropic_default_flagship: str = "claude-opus-4-8"
    anthropic_default_workhorse: str = "claude-sonnet-4-6"
    anthropic_default_batch: str = "claude-haiku-4-5-20251001"

    # Spec 03 §5/§6 — provider abstraction. Default provider for all
    # agents unless a per-agent override is set in
    # `ai_provider_per_agent`. Hot-swappable via env.
    ai_provider_default: str = "anthropic"
    # Per-agent overrides. JSON-encoded string in env, e.g.
    # AI_PROVIDER_PER_AGENT='{"match_rationale":"openai"}'. Empty by
    # default — every agent uses `ai_provider_default`.
    ai_provider_per_agent_json: str = ""

    # Spec 03 §9 — failover order. The agent tries providers in this list
    # left-to-right; if all fail, the rule-based fallback runs. Each
    # attempt writes its own audit ledger row. Failover between LLM
    # providers is invisible to the end user.
    ai_provider_failover_csv: str = "anthropic,openai"
    ai_provider_failover_timeout_ms: int = 30000

    # Embedding (Voyage 3-large, paired with Anthropic for the LLM stack.
    # Note: the existing `student_features` table uses 1536-dim OpenAI vectors
    # for legacy matching; the new `student_feature_vectors` table uses 1024-dim
    # voyage-3-large.)
    embedding_base_url: str = "https://api.voyageai.com/v1"
    embedding_model: str = "voyage-3-large"
    embedding_dimension: int = 1024

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
    matching_reasoning_top_k: int = 10

    # AI dev mode
    ai_mock_mode: bool = False
    ai_refresh_cooldown_seconds: int = 300

    # Per-student LLM spend cap (Plan 2 §10).
    # Sums `ai_turns.cost_usd` for the last `window_days` and refuses
    # further calls once the cap is reached. Enforcement mode:
    #   "off"   — no check (cold-start / dev)
    #   "warn"  — log warning + set cost_cap_warning on response, allow call
    #   "block" — raise CostCapExceededError, fail the call
    ai_per_student_weekly_cost_cap_usd: float = 0.50
    ai_cost_cap_window_days: int = 7
    ai_cost_cap_enforcement: str = "warn"

    # Discovery v2 — Phase A2 LLM pipeline. When False (default), the
    # discovery service returns the Phase-A stub assistant reply. When True,
    # the orchestrator + extractor + validator + artifact-writer fire on
    # every student turn. Internal dogfood gate; flip to True per-environment
    # in `.env` once Anthropic + Voyage keys are populated.
    ai_discovery_v2_enabled: bool = False

    # Plan 2 — Workshop coach LLM. When True, WorkshopFeedbackService routes
    # essay/interview/test feedback through the WorkshopCoach agent (with
    # two-layer guardrail: schema-blind heuristics + LLM judge). On coach
    # failure (parse / guardrail trip / API error) the service falls back
    # to the rule-based stub. Internal dogfood gate; flip per-environment.
    ai_workshops_v2_enabled: bool = False

    # Plan 2 — Match rationale LLM. When True, /me/matches/{id}/explain
    # delegates to MatchService.get_match_with_rationale (A5 RationaleAgent
    # + per-(profile_version, program_version) cache). Off → Phase A stub.
    ai_match_rationale_v2_enabled: bool = False

    # Plan 2 — Strategy generator LLM. When True, StrategyService.generate
    # routes through StrategyAgent (Sonnet, forced tool-use). On any
    # failure (parse / well-formed check / API error), falls back to the
    # deterministic rule-based template.
    ai_strategy_v2_enabled: bool = False

    # Plan 2 — Identity summary LLM. When True,
    # IdentityService.regenerate_summary calls IdentitySummaryAgent to
    # synthesize a paragraph from core_values / worldview / self_awareness.
    # Off → returns the hardcoded STUB_IDENTITY_SUMMARY.
    ai_identity_v2_enabled: bool = False

    # --- Billing / Monetization (Spec 06 §4) ---
    # Master Paper model: students get a 7-day full-access trial (card-on-file
    # auto-convert) then $15/mo, with an optional $5/mo ad-free upgrade;
    # institutions pay $15 per unique applicant processed. All gated behind
    # `billing_enabled` so the platform is unchanged until flipped per-env
    # (same dogfood pattern as the AI v2 flags). When False, every entitlement
    # check passes and no trial/charge rows are created — existing flows untouched.
    billing_enabled: bool = False
    # When True (default), the MockBillingProvider services payments in-process
    # (deterministic, no network) — dev/test/demo. Set False + provider="stripe"
    # to route real cards (Spec 43 §10 lists Stripe as planned sub-processor).
    billing_mock_mode: bool = True
    billing_provider: str = "mock"  # "mock" | "stripe"
    # Prices in integer cents (avoid float money).
    billing_student_plan_price_cents: int = 1500  # $15/mo "UniPaith Plus"
    billing_student_adfree_price_cents: int = 500  # $5/mo ad-free upgrade
    billing_institution_per_applicant_cents: int = 1500  # $15 / unique applicant
    billing_trial_days: int = 7
    billing_currency: str = "usd"
    # Stripe credentials (only read when provider="stripe"). Empty in dev.
    stripe_secret_key: str = ""
    stripe_publishable_key: str = ""
    stripe_webhook_secret: str = ""
    # Recurring Price ids created in the Stripe dashboard (or by
    # scripts/setup_stripe_products.py). If stripe_price_id is empty the
    # provider falls back to an inline price_data using the cents config above.
    stripe_price_id: str = ""  # $15/mo Plus
    stripe_adfree_price_id: str = ""  # $5/mo ad-free add-on
    stripe_api_version: str = "2024-06-20"

    # GPU infrastructure (cloud-first)
    gpu_mode: str = "openai"  # "openai" | "aws" | "local" | "mock"
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
    ml_cycle_schedule_minutes: int = 60
    ml_cycle_force_full_every_n_cycles: int = 24
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
    model_promotion_min_composite_improvement: float = 0.01
    model_ab_test_traffic_pct: float = 0.10
    model_ab_test_min_samples: int = 100
    model_rollback_degradation_threshold: float = 0.05

    # Fairness
    fairness_dial: float = 0.5
    fairness_protected_attributes: list[str] = [
        "nationality",
        "gender",
        "ethnicity",
        "first_generation",
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
    crawler_user_agent: str = "UniPaith-Bot/1.0 (+https://app.unipaith.co/bot)"
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
    campaign_unsubscribe_secret: str = "unipaith-campaign-unsub-v1"
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

# Default URLs when ENGINE_BOOTSTRAP_URLS is unset — stable, crawlable education content.
_DEFAULT_ENGINE_BOOTSTRAP_URLS: tuple[str, ...] = (
    "https://www.ed.gov/news/press-releases",
    "https://www.commonapp.org/why-apply-now",
    "https://www.timeshighereducation.com/world-university-rankings",
    "https://www.topuniversities.com/university-rankings/world-university-rankings/2024",
    "https://www.niche.com/colleges/search/best-colleges/",
)


def get_engine_bootstrap_urls() -> list[str]:
    raw = (settings.engine_bootstrap_urls or "").strip()
    if raw:
        return [u.strip() for u in raw.split(",") if u.strip().startswith("http")]
    return list(_DEFAULT_ENGINE_BOOTSTRAP_URLS)
