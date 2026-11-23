"""Configuration centralisée, lue depuis les variables d'environnement et `.env`."""

from functools import lru_cache
from typing import Literal

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEV_JWT_SECRET = "change-me-in-production"  # noqa: S105 - valeur de développement uniquement


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Application
    app_name: str = "Enterprise AI Agent"
    environment: Literal["dev", "test", "prod"] = "dev"
    log_level: str = "INFO"
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Base vectorielle
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "documents"

    # Modèles
    embedding_model: str = "BAAI/bge-m3"
    llm_model: str = "gemini-2.5-flash"
    gemini_api_key: SecretStr | None = None

    # Agent
    max_agent_iterations: int = 3
    max_tool_calls: int = 8

    # Sécurité
    jwt_secret: SecretStr = SecretStr(_DEV_JWT_SECRET)
    jwt_expire_minutes: int = 60

    # Stockage
    data_dir: str = "./data"
    max_upload_mb: int = 50

    @model_validator(mode="after")
    def _forbid_dev_secret_in_prod(self) -> "Settings":
        if self.environment == "prod" and self.jwt_secret.get_secret_value() == _DEV_JWT_SECRET:
            msg = "JWT_SECRET doit être défini explicitement en production."
            raise ValueError(msg)
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
