"""Application configuration and settings."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = Field(default="AI Financial Coach", alias="APP_NAME")
    environment: str = Field(default="local", alias="ENVIRONMENT")
    debug: bool = Field(default=False, alias="DEBUG")
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")
    secret_key: str = Field(
        default="change_me_to_at_least_32_characters_random_secret_key",
        alias="SECRET_KEY",
    )

    # Database (PostgreSQL with pgvector)
    postgres_user: str = Field(default="financial_app", alias="POSTGRES_USER")
    postgres_password: str = Field(
        default="replace_with_secure_postgres_password", alias="POSTGRES_PASSWORD"
    )
    postgres_db: str = Field(default="financial_coach", alias="POSTGRES_DB")
    postgres_host: str = Field(default="postgres", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    database_url: str = Field(
        default="postgresql+asyncpg://financial_app:replace_with_secure_postgres_password@postgres:5432/financial_coach",
        alias="DATABASE_URL",
    )

    # Cache & Queues (Redis)
    redis_host: str = Field(default="redis", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_password: str | None = Field(default=None, alias="REDIS_PASSWORD")
    redis_url: str = Field(default="redis://redis:6379/0", alias="REDIS_URL")

    # Security & Tokens
    access_token_expire_minutes: int = Field(default=15, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, alias="REFRESH_TOKEN_EXPIRE_DAYS")
    algorithm: str = Field(default="HS256", alias="ALGORITHM")

    # CORS
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        alias="CORS_ORIGINS",
    )

    # LLM Settings
    llm_provider: str = Field(default="mock", alias="LLM_PROVIDER")
    llm_api_key: str | None = Field(default=None, alias="LLM_API_KEY")
    llm_model: str = Field(default="gpt-4o-mini", alias="LLM_MODEL")
    llm_temperature: float = Field(default=0.1, alias="LLM_TEMPERATURE")
    llm_timeout_seconds: float = Field(default=10.0, alias="LLM_TIMEOUT_SECONDS")

    # Feature Flags & Kill Switches
    ai_enabled: bool = Field(default=True, alias="AI_ENABLED")
    registration_enabled: bool = Field(default=True, alias="REGISTRATION_ENABLED")
    login_enabled: bool = Field(default=True, alias="LOGIN_ENABLED")
    forecast_enabled: bool = Field(default=True, alias="FORECAST_ENABLED")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
