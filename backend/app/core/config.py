"""Application settings loaded from environment variables (.env)."""
from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    app_name: str = "AI Mock Interview Platform"
    environment: str = Field(default="local")
    debug: bool = Field(default=True)
    api_v1_prefix: str = "/api/v1"

    # Security
    jwt_secret_key: str = Field(default="change-me-in-production")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_minutes: int = 60 * 24 * 7

    # CORS
    cors_origins: List[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    # Database - SQL Server / Azure SQL via pyodbc only (no ORM). Schema: docs/api/DATABASE_SCHEMA.sql,
    # applied with backend/scripts/init_db.py. Requires the "ODBC Driver 18 for SQL Server" installed.
    database_backend: str = Field(default="sqlite")
    sqlite_database_path: str = Field(default="./storage/interview.db")
    database_server: str = Field(default="localhost,1433")
    database_name: str = Field(default="interview_db")
    database_user: str = Field(default="sa")
    database_password: str = Field(default="")
    database_driver: str = Field(default="ODBC Driver 18 for SQL Server")
    database_encrypt: bool = Field(default=True)
    database_trust_server_certificate: bool = Field(default=True)
    # Optional full ODBC connection string override (e.g. Azure SQL); built from the fields above if unset.
    database_connection_string: str = Field(default="")

    def build_database_connection_string(self) -> str:
        if self.database_connection_string:
            return self.database_connection_string
        return (
            f"DRIVER={{{self.database_driver}}};"
            f"SERVER={self.database_server};DATABASE={self.database_name};"
            f"UID={self.database_user};PWD={self.database_password};"
            f"Encrypt={'yes' if self.database_encrypt else 'no'};"
            f"TrustServerCertificate={'yes' if self.database_trust_server_certificate else 'no'};"
        )

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0")
    rate_limit_storage_uri: str = Field(default="memory://")
    cache_ttl_seconds: int = 300

    # Rate limiting
    rate_limit_default: str = "100/minute"

    # Azure OpenAI
    azure_openai_endpoint: str = Field(default="https://YOUR-RESOURCE.openai.azure.com/")
    azure_openai_api_key: str = Field(default="")
    azure_openai_api_version: str = Field(default="2024-08-01-preview")
    azure_openai_deployment_gpt4o: str = Field(default="gpt-4o")

    # Azure Speech
    azure_speech_key: str = Field(default="")
    azure_speech_region: str = Field(default="eastus")
    azure_speech_voice: str = Field(default="en-US-JennyNeural")

    # Storage (local filesystem path for uploaded resumes / generated PDFs)
    storage_root: str = Field(default="./storage")

    # OpenTelemetry
    otel_exporter_otlp_endpoint: str = Field(default="")
    otel_enabled: bool = False

    # Interview defaults
    max_questions_per_interview: int = 20


@lru_cache
def get_settings() -> Settings:
    return Settings()
