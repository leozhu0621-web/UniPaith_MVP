from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

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

    # LLM - Feature Extraction (Mistral 7B)
    llm_feature_base_url: str = "http://localhost:8001/v1"
    llm_feature_model: str = "mistralai/Mistral-7B-Instruct-v0.3"
    llm_feature_api_key: str = "not-needed"
    llm_feature_max_tokens: int = 2048
    llm_feature_temperature: float = 0.1

    # LLM - Reasoning (Llama 70B)
    llm_reasoning_base_url: str = "http://localhost:8002/v1"
    llm_reasoning_model: str = "meta-llama/Llama-3.1-70B-Instruct"
    llm_reasoning_api_key: str = "not-needed"
    llm_reasoning_max_tokens: int = 1024
    llm_reasoning_temperature: float = 0.7

    # Embedding
    embedding_base_url: str = "http://localhost:8001/v1"
    embedding_model: str = "nomic-ai/nomic-embed-text-v1.5"
    embedding_dimension: int = 768

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

    # Notifications — Amazon SES
    ses_region: str = "us-east-1"
    ses_sender_email: str = "noreply@unipaith.com"
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
