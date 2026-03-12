"""Application settings loaded from environment variables / .env file."""

from __future__ import annotations

import secrets

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ------------------------------------------------------------------ #
    # Database — individual components (optional convenience)             #
    # ------------------------------------------------------------------ #
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "tenantrix"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    # Can be set directly OR will be assembled from the components above
    DATABASE_URL: str = ""

    @model_validator(mode="after")
    def assemble_db_url(self) -> Settings:
        """Build DATABASE_URL from parts if not explicitly provided."""
        if not self.DATABASE_URL:
            self.DATABASE_URL = (
                f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )
        return self

    # ------------------------------------------------------------------ #
    # Security                                                             #
    # ------------------------------------------------------------------ #
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    @model_validator(mode="after")
    def ensure_secret_key(self) -> Settings:
        """Generate a SECRET_KEY when not provided (convenience for local/dev)."""
        if not self.SECRET_KEY:
            self.SECRET_KEY = secrets.token_urlsafe(32)
        return self

    # ------------------------------------------------------------------ #
    # Application                                                          #
    # ------------------------------------------------------------------ #
    ENVIRONMENT: str = "development"
    VERSION: str = "0.1.0"
    DEBUG: bool = False

    # ------------------------------------------------------------------ #
    # Rate limiting                                                        #
    # ------------------------------------------------------------------ #
    RATE_LIMIT_PER_MINUTE: int = 60

    # ------------------------------------------------------------------ #
    # SMTP / Email                                                         #
    # ------------------------------------------------------------------ #
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_USE_TLS: bool = False
    MAIL_FROM_EMAIL: str = "noreply@tenantrix.io"
    MAIL_FROM_NAME: str = "Tenantrix"
    FRONTEND_URL: str = "http://localhost:5173"

    # ------------------------------------------------------------------ #
    # S3 / MinIO (object storage for attachments)                          #
    # ------------------------------------------------------------------ #
    S3_ENDPOINT: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET: str = "tenantrix-attachments"

    # ------------------------------------------------------------------ #
    # CORS                                                                 #
    # ------------------------------------------------------------------ #
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://localhost:5174,http://localhost:5175"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
