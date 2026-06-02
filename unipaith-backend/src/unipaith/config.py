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

    # Spec 18 §9 / 45 §15 — OutcomeBriefForOfferLetter LLM. When True,
    # ApplicationService routes offer-brief generation through the
    # OutcomeBriefAgent (Sonnet, forced tool-use) at offer-create/record time
    # and caches the structured brief on offer_letters.plain_language_brief.
    # On any failure (parse / API error / mock mode) it falls back to the
    # rule-based _build_structured_brief — the offer flow never 5xxes.
    ai_outcome_brief_v2_enabled: bool = False

    # Spec 17 §7 / 45 §13 — Inbox AI-suggested replies. When True,
    # InboxService.suggested_reply routes a needs_reply / clarification thread
    # through the InboxReplyDrafter agent (Sonnet, forced tool-use, gated on
    # the `outreach` consent lever). Unlike other agents there is NO
    # rule-based fallback: on any failure (consent deny / parse / provider /
    # mock) the endpoint returns null and the UI hides the suggestion card —
    # the student types from scratch. Off (default) → endpoint always returns
    # null, so the card never shows.
    ai_inbox_v2_enabled: bool = False

    # Spec 10 §3 / 45 §12 — Discovery type-first search query interpreter. When
    # True, SearchService.interpret routes a free-text query through the
    # DiscoveryQueryInterpreter agent (Sonnet, forced tool-use) to produce
    # structured constraint chips. On any failure (consent deny / parse /
    # provider error) it falls back to the deterministic rule-based parser
    # (services/query_parser.py), which is also the flag-off default — so the
    # search box always works and never 5xxes.
    ai_discovery_query_v2_enabled: bool = False

    # Spec 20 §8 — ConnectFeedRanker + EventRecommender (Haiku-tier, cheap).
    # When True, the Connect "Most relevant" toggle routes the feed through the
    # ConnectFeedRanker agent and the Events tab through EventRecommender. On
    # any failure (consent deny / parse / provider error) both silently fall
    # back to the deterministic relevance heuristic / reverse-chronological
    # order — the feed never errors (Spec 20 §9 "AI rank failure").
    ai_connect_ranker_v2_enabled: bool = False

    # Spec 25 §10 / 45 §16 — CampaignAudienceCopySuggester. When True, the
    # institution campaign editor's "Draft with AI" button routes through the
    # Sonnet copy agent (forced tool-use). On any failure (parse / provider /
    # mock) it falls back to a deterministic objective-keyed template stub, also
    # the flag-off default — so the button always returns usable copy.
    ai_campaign_copy_v2_enabled: bool = False

    # Spec 20 §6 / §14 — Peers tab (opt-in, privacy-gated). The spec ships
    # Updates + Events for MVP and gates Peers behind this flag as a
    # fast-follow. When False the Peers tab shows the opt-in explainer only and
    # peer endpoints 404/403; no peer data is read or written.
    connect_peers_enabled: bool = True

    # Spec 24 §9 / 45 §19 — DocumentParseTriage on dataset upload. When True the
    # upload validation report is enriched with a Haiku-tier human-readable
    # triage summary; on any failure (parse / provider / guardrail) the
    # deterministic rule-based validation report is returned unchanged — the
    # upload never 5xxes (Plan-2 integration invariant).
    ai_data_parse_triage_v2_enabled: bool = False

    # Spec 26 §6 / 45 §17 — SegmentBuilderNLBridge. When True the "Try AI assist"
    # bar on the segment builder routes the institution's natural-language
    # audience description through the Sonnet agent to draft structured rules;
    # on any failure (parse / provider / mock mode) it falls back to a keyword
    # parser so the institution always gets editable rules (never a 5xx).
    ai_segment_builder_v2_enabled: bool = False

    # Spec 29 §8 / 45 — InstitutionReplyDrafter. When True the institution inbox
    # "AI draft" button routes a thread + applicant context (checklist + reason
    # code) through the Haiku-tier agent. It respects the applicant's `matching`
    # consent for profile context (degrading to thread-text only on denial) and
    # returns null on any failure (parse / provider / mock) — the UI hides the
    # card and staff types from scratch (mirrors the student inbox, spec 17 §7).
    ai_institution_reply_v2_enabled: bool = False

    # Spec 29 §8 / 45 — InboundIntentClassifier (optional). When True a new
    # inbound applicant message gets a Haiku-tier *suggested* reason code +
    # routing hint; suggestion-only (never auto-assigns, §14) and always falls
    # back to no suggestion on failure.
    ai_inbound_intent_v2_enabled: bool = False

    # Spec 33 §9 — interview AI helpers. When True the Propose modal's "AI draft"
    # button routes interview context through the Haiku InterviewInviteDrafter,
    # and the Score modal's "AI prefill" button routes the rubric + transcript
    # through the Sonnet InterviewScorePrefill. Both are institution-initiated,
    # role-gated, and return null on any failure (parse / provider / mock) — the
    # UI simply omits the AI affordance and staff fill in manually.
    ai_interview_v2_enabled: bool = False

    # Spec 35 §6 / 45 — enrollment-yield intelligence (YieldRiskScorer +
    # NextBestActionForYield). When True, NextBestActionForYield (Sonnet) refines
    # the dashboard's ranked actions; YieldRiskScorer stays a deterministic
    # calibrated heuristic either way. Always falls back to deterministic counts
    # on any failure (§6 fairness gate: surfaces disparities, never drives
    # selection). Off in code, enabled per-env via ECS.
    ai_yield_intelligence_v2_enabled: bool = False

    # Spec 09 §4A — probability bands (admit / scholarship / waitlist) on the
    # Match surface + program detail. Rule-based + calibrated heuristic
    # (unipaith.ai.probability); honest ranges, "not enough data yet" when a
    # program lacks historical admit signal or the student isn't match-ready.
    # On by default — pure-Python, no LLM cost, degrades gracefully to null.
    ai_probability_bands_enabled: bool = True

    # Spec 31 §9 / §11 — Intelligence-digest narrator on the institution
    # dashboard. When True a Sonnet-tier agent (45 §11 migrate-to-Claude) writes
    # the plain-English daily digest from a pre-computed, non-PII applicant-
    # landscape stat block; on any failure (flag off / mock / parse / provider)
    # the DashboardIntelligenceService falls back to a deterministic rule-based
    # narrator so the endpoint never 5xxes (the spec 31 integration invariant).
    ai_intelligence_digest_v2_enabled: bool = False

    # Spec 38 §5 — international-admissions processing agents (CredentialNormalizer
    # + CountryRequirementAdvisor). When True, CredentialNormalizer (Haiku) refines
    # the foreign-GPA normalization and CountryRequirementAdvisor (Haiku) proposes
    # a richer country-requirement pack. Both always fall back to deterministic
    # logic (the grading-scale mapper / the platform default pack) on any failure
    # — AI never decides feasibility (§5 / 46 §6) and the endpoint never 5xxes.
    # Off in code, enabled per-env via ECS.
    ai_international_v2_enabled: bool = False

    # Spec 40 §5 — recruitment CRM intelligence (ProspectPrioritizer +
    # TerritoryOptimizer). When True, ProspectPrioritizer ranks prospects by
    # apply-likelihood on list load (deterministic propensity heuristic either
    # way) and TerritoryOptimizer (Sonnet) refines the per-territory travel
    # suggestions. Always falls back to manual sorting / deterministic
    # prior-year-yield ranking on any failure (§5). Prioritization + planning
    # only, never selection (46 §6). Off in code, enabled per-env via ECS.
    ai_recruitment_v2_enabled: bool = False

    # Spec 41 §5 — graduate-admissions intelligence (AdvisorMatcher +
    # SoPInterestExtractor + FundingScenarioHelper). When True the SoP extractor
    # auto-tags research interests, advisor matches carry an AI rationale, and the
    # funding builder surfaces over-commit warnings + re-mix suggestions. The
    # deterministic baseline (advisor alignment ranking + the hard over-commit
    # block, §9) is always on regardless of this flag. Both never decide —
    # matching informs humans, faculty decide (§5 / 46 §6). Off in code, enabled
    # per-env via ECS.
    ai_graduate_v2_enabled: bool = False
    # Spec 42 §4.17 — Prompt Library behavioral coach (PromptCoach). When True,
    # the /students/me/prompt-library/summary endpoint attaches the inference
    # overlay (interview-readiness band+score, competency coverage/gaps,
    # story↔prompt matching, revision priorities, suggested practice plan)
    # computed by the deterministic engine; the tier documents the future LLM
    # swap-in. Off → the summary returns raw counts only. STAR auto-detection on
    # response save is rule-based and always runs (system-derived, §5). The
    # engine never 5xxes either way. Off in code, enabled per-env via ECS.
    ai_prompt_library_v2_enabled: bool = False

    # Spec 43 §4.18 — major-specific readiness coach (MajorTrackCoach). When True,
    # the /students/me/major-specific/{tracks,summary} endpoints attach the §4.18
    # overlay (per-track fit score, readiness band, coverage map, skill-gap
    # severity, specialization tags, suggested artifacts, bridge plan, track
    # recommendation) computed by the deterministic engine; the tier documents the
    # future LLM swap-in. Off → tracks/summary return raw signals + counts only.
    # The engine never 5xxes either way. Off in code, enabled per-env via ECS.
    ai_major_specific_v2_enabled: bool = False

    # Spec 44 §3/§5 — Adaptive Intake Engine LLM path. When True, the intake
    # engine may call an LLM to normalize free text (DiscoveryExtractor) and to
    # triage uploaded documents (DocumentParseTriage); when False, every channel
    # takes the deterministic normalize/validate path. The flag is ANDed with the
    # student's `consent_matching` — no matching consent → no LLM call regardless
    # (§10/§11). The deterministic path is fully functional on its own, so the
    # engine never depends on the LLM to gate the journey. Off in code, enabled
    # per-env via ECS.
    ai_intake_engine_v2_enabled: bool = False

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

    # --- Billing / monetization (Spec 07 §4, 21 §2.7/§3.6) ---
    # Student subscription: $15/mo after a 7-day full-access trial
    # (card-on-file auto-convert), + optional $5/mo ad-free upgrade.
    student_plan_price_usd: int = 15
    student_ad_free_addon_usd: int = 5
    student_trial_days: int = 7
    # Institution usage-based billing: $15 per unique applicant processed.
    institution_per_applicant_usd: int = 15
    # When True, the trial→paywall gate (Spec 05 §9) hard-blocks premium
    # surfaces after the trial lapses without a payment method. Default off so
    # the soft trial banner + upsell ship without locking existing sessions;
    # flip per-environment once Stripe is wired (Spec 39, Phase-2).
    paywall_enforced: bool = False

    # --- Payments / fees (Spec 39 — Fees & Payments) ---
    # Master switch for the applicant-facing transactional layer (application
    # fees + enrollment deposits + waivers + refunds). When False, fee surfaces
    # are hidden and submission is never fee-gated (degrades to the status-only
    # behaviour of Spec 15/35).
    payments_enabled: bool = True
    # Provider behind the PaymentProvider seam (Spec 39 §4): "mock" | "stripe".
    # Default "mock" — a deterministic in-app checkout that moves no real money,
    # so the flow is fully live/demoable without Stripe keys. Flip to "stripe"
    # per-environment once Stripe Connect onboarding + keys are in place.
    payments_provider: str = "mock"
    # Stripe credentials (only read when payments_provider == "stripe").
    stripe_secret_key: str = ""
    stripe_publishable_key: str = ""
    stripe_webhook_secret: str = ""
    # Recurring Price ids for the student subscription (Spec 07 §4.1), created in
    # the Stripe dashboard or by scripts/setup_stripe_products.py. When empty the
    # provider builds an inline price_data from student_plan_price_usd, so Stripe
    # still works without pre-created Prices.
    stripe_price_id: str = ""  # $15/mo Plus
    stripe_adfree_price_id: str = ""  # $5/mo ad-free add-on
    stripe_api_version: str = "2024-06-20"
    # Base URL used to build Stripe Checkout success/cancel return links.
    payments_app_base_url: str = "https://app.unipaith.co"


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
