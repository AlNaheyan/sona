from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    database_url: str = "postgresql+asyncpg://ratemyalbum:ratemyalbum_secret@localhost:5432/ratemyalbum"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Auth
    secret_key: str = "dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Last.fm (optional, for supplementary data)
    lastfm_api_key: str = ""

    # App
    environment: str = "development"
    debug: bool = True

    # CWPR algorithm
    cwpr_lambda: float = 1.0  # Confidence penalty factor

    # Sentry (error tracking)
    sentry_dsn: str = ""  # Leave empty to disable Sentry
    sentry_traces_sample_rate: float = 0.1  # 10% of transactions for performance monitoring
    sentry_profiles_sample_rate: float = 0.1  # 10% of profiled transactions


settings = Settings()
