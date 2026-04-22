import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env path relative to this file (backend/.env)
_ENV_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env")

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    PROJECT_NAME: str = "Study Abroad API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # ── Database ──────────────────────────────────────────────────────────────
    # If DATABASE_URL is set (Supabase / production), it is used directly.
    # Falls back to building from parts (local dev).
    DATABASE_URL: Optional[str] = None
    DIRECT_DATABASE_URL: Optional[str] = None   # used by Alembic only

    # Legacy local-dev fallback parts
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "study_abroad_db"
    DATABASE_URL: Optional[str] = None

    # ── Security ──────────────────────────────────────────────────────────────
    SECRET_KEY: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # ── Third-party APIs ──────────────────────────────────────────────────────
    ADZUNA_APP_ID: str = "dummy_id"
    ADZUNA_APP_KEY: str = "dummy_key"
    GOOGLE_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    # ── Email / SMTP ──────────────────────────────────────────────────────────
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 465
    EMAILS_FROM_NAME: str = "udaan"

    # ── n8n ───────────────────────────────────────────────────────────────────
    N8N_WEBHOOK_TOKEN: str = ""

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """
        Returns the database URI for SQLAlchemy.
        Priority:
          1. DATABASE_URL from .env  (Supabase / any external DB)
          2. Built from POSTGRES_* parts  (local dev fallback)
        """
        if self.DATABASE_URL:
            # Supabase uses ?sslmode=require — psycopg2 needs it as a connect_arg,
            # but having it in the URL string works fine too.
            return self.DATABASE_URL
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def ALEMBIC_DATABASE_URI(self) -> str:
        """
        Connection URL for Alembic migrations.
        Prefers DIRECT_DATABASE_URL (non-pooler) when available.
        Falls back to SQLALCHEMY_DATABASE_URI (pooler is fine for DDL migrations).
        """
        return self.SQLALCHEMY_DATABASE_URI


settings = Settings()
