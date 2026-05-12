"""
Uygulama ayarları. .env'den okur, eksikse sensible defaults verir.
Pydantic Settings v2 kullanıyoruz — type-safe ve test edilebilir.
"""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Database ---
    # docker-compose'da postgres servis adı "postgres", lokal çalıştırırken "localhost"
    DATABASE_URL: str = (
        "postgresql+asyncpg://agentkobi:changeme@postgres:5432/agentkobi"
    )
    # Alembic senkron sürücü kullanır; asyncpg yerine psycopg2/psycopg kullanır
    DATABASE_URL_SYNC: str = (
        "postgresql+psycopg2://agentkobi:changeme@postgres:5432/agentkobi"
    )

    # --- App ---
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    TZ: str = "Europe/Istanbul"

    # Demo amaçlı sabit business id (seed data ile uyumlu)
    DEMO_BUSINESS_ID: str = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # diğer env değişkenlerini (REDIS_URL vs) görmezden gel
    )


settings = Settings()
