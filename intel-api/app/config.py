from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str
    debug: bool = False

    # Apify
    apify_token: str = ""

    # Scraping limits
    max_posts_per_scrape: int = 100
    max_reels_per_scrape: int = 50

    # Meta Ad Library API
    meta_access_token: str = ""
    meta_api_version: str = "v18.0"
    meta_ads_per_request: int = 50

    # Google Ads Transparency
    google_ads_max_results: int = 100

    # AI Providers
    gemini_api_key: str = ""
    openai_api_key: str = ""
    xai_api_key: str = ""
    anthropic_api_key: str = ""
    default_ai_provider: str = "openai"

    # AI Settings
    ai_temperature: float = 0.7
    ai_max_tokens: int = 4096

    # Server
    host: str = "0.0.0.0"
    port: int = 8001

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
