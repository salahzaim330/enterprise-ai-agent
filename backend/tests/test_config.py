import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_defaults() -> None:
    settings = Settings(_env_file=None)
    assert settings.environment == "dev"
    assert settings.embedding_model == "BAAI/bge-m3"
    assert settings.max_agent_iterations == 3


def test_environment_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("QDRANT_URL", "http://qdrant:6333")
    monkeypatch.setenv("MAX_AGENT_ITERATIONS", "2")
    settings = Settings(_env_file=None)
    assert settings.qdrant_url == "http://qdrant:6333"
    assert settings.max_agent_iterations == 2


def test_prod_rejects_default_jwt_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "prod")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_prod_accepts_custom_jwt_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "prod")
    monkeypatch.setenv("JWT_SECRET", "a-long-random-secret")
    settings = Settings(_env_file=None)
    assert settings.environment == "prod"
