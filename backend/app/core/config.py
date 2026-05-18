from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_UNSAFE_KEYS = {
    "dev-secret-key-change-in-production",
    "secret",
    "changeme",
    "insecure",
}


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

    # CORS — comma-separated list of allowed origins, or JSON array
    # Example: CORS_ORIGINS=https://ratemyalbum.com,https://www.ratemyalbum.com
    cors_origins: list[str] = ["http://localhost:3000"]

    # Last.fm (optional, for supplementary data)
    lastfm_api_key: str = ""

    # App
    environment: str = "development"
    debug: bool = True

    # CWPR algorithm
    cwpr_lambda: float = 1.0  # Confidence penalty factor

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"  # "json" for production, "text" for development

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        if self.environment == "production":
            if self.secret_key in _UNSAFE_KEYS or self.secret_key.startswith("dev-"):
                raise ValueError(
                    "SECRET_KEY must be set to a strong random value in production. "
                    "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
                )
            if self.debug:
                raise ValueError("DEBUG must be False in production.")
        return self


settings = Settings()
