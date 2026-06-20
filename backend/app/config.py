from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    APP_NAME: str = "medical-reports-api"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: str = "change-me"

    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost:5432/medical_reports"
    REDIS_URL: str = "redis://localhost:6379/0"

    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    WHAHA_TOKEN: str = ""
    WHAHA_API_URL: str = "https://api.whaha.com/v1"
    WHAHA_WEBHOOK_SECRET: str = ""

    GOOGLE_CREDENTIALS_JSON: str = "{}"
    SENTRY_DSN: str = ""
    ENCRYPTION_KEY: str = ""

    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60
    JWT_REFRESH_EXPIRATION_DAYS: int = 7


@lru_cache()
def get_settings() -> Settings:
    return Settings()
