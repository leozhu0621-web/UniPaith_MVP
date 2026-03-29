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


settings = Settings()
