"""Application configuration with multi-tenant support."""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "MedFlow Integration"
    app_env: str = "development"
    debug: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://medflow:medflow_secret@postgres:5432/integration"

    # Redis
    redis_url: str = "redis://redis:6379"

    # Auth
    jwt_secret: str = "change-me-jwt-secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours

    # External Services
    twenty_api_url: str = "http://twenty-server:3000"
    twenty_api_key: str | None = None
    calcom_api_url: str = "http://calcom:3000"
    calcom_api_key: str | None = None
    chatwoot_api_url: str = "http://chatwoot-rails:3000"
    chatwoot_api_key: str | None = None

    # LLM Configuration
    llm_provider: str = "anthropic"  # anthropic, openai, google
    model_smart: str = "claude-sonnet-4-5-20250514"  # For complex reasoning
    model_fast: str = "claude-haiku-4-20250514"  # For routing/simple tasks

    # LLM Keys
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    google_api_key: str | None = None

    # WhatsApp (Evolution API)
    evolution_api_url: str | None = None
    evolution_api_key: str | None = None

    # Image Generation
    replicate_api_key: str | None = None

    # Webhooks
    webhook_secret: str = "change-me-webhook-secret"

    # CORS - Configure properly for production!
    # In dev: ["*"]
    # In prod: ["https://your-domain.com"]
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:3001"]

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
