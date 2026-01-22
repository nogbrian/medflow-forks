"""Application configuration with security validation."""

import secrets
import sys
from functools import lru_cache
from typing import Self

import json

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _generate_dev_secret(name: str) -> str:
    """Generate a random secret for development. Logs a warning."""
    secret = secrets.token_urlsafe(32)
    print(f"⚠️  DEV MODE: Generated random {name}. Set in .env for production.", file=sys.stderr)
    return secret


class Settings(BaseSettings):
    """Application settings with security validation."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "MedFlow Integration"
    app_env: str = "development"
    debug: bool = False

    # Database - NO DEFAULT PASSWORD
    database_url: str = "postgresql+asyncpg://medflow:medflow_secret@postgres:5432/medflow"

    # Redis
    redis_url: str = "redis://redis:6379"

    # Auth - NO DEFAULTS, validated below
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours

    # Webhooks - NO DEFAULTS, validated below
    webhook_secret: str = ""

    # External Services
    twenty_api_url: str = "http://twenty-server:3000"
    twenty_api_key: str | None = None
    calcom_api_url: str = "http://calcom:3000"
    calcom_api_key: str | None = None
    chatwoot_api_url: str = "http://chatwoot-rails:3000"
    chatwoot_api_key: str | None = None

    # LLM Configuration
    llm_provider: str = "anthropic"  # anthropic, openai, google, xai
    model_smart: str = "claude-sonnet-4-5-20250514"
    model_fast: str = "claude-haiku-4-20250514"

    # LLM Keys - at least one required for agents
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    google_api_key: str | None = None
    xai_api_key: str | None = None

    # WhatsApp (Evolution API)
    evolution_api_url: str | None = None
    evolution_api_key: str | None = None

    # Image Generation
    replicate_api_key: str | None = None

    # Scraping (Apify)
    apify_token: str | None = None

    # CORS - stored as string to avoid pydantic-settings JSON parsing issues
    cors_origins_raw: str = "http://localhost:3000,http://localhost:3001"

    @property
    def cors_origins(self) -> list[str]:
        """Parse CORS origins from various formats (handles Coolify escaping issues)."""
        v = self.cors_origins_raw
        if not v:
            return ["http://localhost:3000"]

        # Remove surrounding quotes if present
        v = v.strip().strip("'\"")

        # Handle double-escaped JSON from Coolify
        if v.startswith('[\\') or '\\"' in v:
            v = v.replace('\\"', '"').replace('\\/', '/')

        # Try parsing as JSON array
        if v.startswith('['):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
                return [parsed]
            except json.JSONDecodeError:
                pass

        # Fallback: comma-separated
        return [origin.strip() for origin in v.split(",") if origin.strip()]

    @model_validator(mode="after")
    def validate_security(self) -> Self:
        """Validate security settings based on environment."""
        is_prod = self.app_env == "production"

        # JWT Secret validation
        if not self.jwt_secret or self.jwt_secret.startswith("change-me"):
            if is_prod:
                raise ValueError(
                    "FATAL: JWT_SECRET must be set in production. "
                    "Generate with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
                )
            self.jwt_secret = _generate_dev_secret("JWT_SECRET")

        if len(self.jwt_secret) < 32:
            if is_prod:
                raise ValueError("JWT_SECRET must be at least 32 characters in production")
            print("⚠️  JWT_SECRET is weak (<32 chars). Use longer secret in production.", file=sys.stderr)

        # Webhook Secret validation
        if not self.webhook_secret or self.webhook_secret.startswith("change-me"):
            if is_prod:
                raise ValueError("FATAL: WEBHOOK_SECRET must be set in production")
            self.webhook_secret = _generate_dev_secret("WEBHOOK_SECRET")

        # LLM Key validation - warn if none configured
        has_llm_key = any([
            self.anthropic_api_key,
            self.openai_api_key,
            self.google_api_key,
            self.xai_api_key,
        ])
        if not has_llm_key:
            print("⚠️  No LLM API key configured. Agents will not work.", file=sys.stderr)

        return self

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    def get_llm_api_key(self) -> str | None:
        """Get the API key for the configured LLM provider."""
        provider_keys = {
            "anthropic": self.anthropic_api_key,
            "openai": self.openai_api_key,
            "google": self.google_api_key,
            "xai": self.xai_api_key,
        }
        return provider_keys.get(self.llm_provider)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
