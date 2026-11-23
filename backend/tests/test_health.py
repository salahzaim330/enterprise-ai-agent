import json
import logging
import sys

import httpx
import pytest
from fastapi.testclient import TestClient

from app.api import health as health_module
from app.main import create_app


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


def _fake_qdrant(up: bool):  # type: ignore[no-untyped-def]
    async def _check(url: str, timeout: float = 2.0) -> bool:  # noqa: ARG001
        return up

    return _check


def test_health_ok_when_qdrant_up(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(health_module, "check_qdrant", _fake_qdrant(True))
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["dependencies"] == {"qdrant": "up"}
    assert body["version"]


def test_health_degraded_when_qdrant_down(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(health_module, "check_qdrant", _fake_qdrant(False))
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "degraded"
    assert response.json()["dependencies"] == {"qdrant": "down"}


def test_request_id_is_generated_and_propagated(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(health_module, "check_qdrant", _fake_qdrant(True))
    generated = client.get("/health").headers["X-Request-ID"]
    assert len(generated) == 32
    echoed = client.get("/health", headers={"X-Request-ID": "abc-123"}).headers["X-Request-ID"]
    assert echoed == "abc-123"


def test_access_log_is_json_with_request_id(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    from app.core.logging import JsonFormatter

    monkeypatch.setattr(health_module, "check_qdrant", _fake_qdrant(True))
    with caplog.at_level(logging.INFO, logger="app.access"):
        client.get("/health", headers={"X-Request-ID": "trace-1"})
    record = next(r for r in caplog.records if r.name == "app.access")
    line = json.loads(JsonFormatter().format(record))
    assert line["message"] == "request"
    assert line["path"] == "/health"
    assert "duration_ms" in line


def test_openapi_is_exposed(client: TestClient) -> None:
    assert client.get("/openapi.json").status_code == 200


def _patch_httpx(monkeypatch: pytest.MonkeyPatch, handler: httpx.MockTransport) -> None:
    real_client = httpx.AsyncClient

    def factory(*args: object, **kwargs: object) -> httpx.AsyncClient:
        kwargs["transport"] = handler
        return real_client(*args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(httpx, "AsyncClient", factory)


async def test_check_qdrant_true_on_200(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(str(request.url))
        return httpx.Response(200, text="healthz check passed")

    _patch_httpx(monkeypatch, httpx.MockTransport(handler))
    assert await health_module.check_qdrant("http://qdrant:6333/") is True
    assert seen == ["http://qdrant:6333/healthz"]


async def test_check_qdrant_false_on_error_status(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_httpx(monkeypatch, httpx.MockTransport(lambda _: httpx.Response(503)))
    assert await health_module.check_qdrant("http://qdrant:6333") is False


async def test_check_qdrant_false_on_connection_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom", request=request)

    _patch_httpx(monkeypatch, httpx.MockTransport(handler))
    assert await health_module.check_qdrant("http://qdrant:6333") is False


def test_lifespan_configures_logging(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(health_module, "check_qdrant", _fake_qdrant(True))
    with TestClient(create_app()) as client:
        assert client.get("/health").status_code == 200


def test_json_formatter_includes_exception() -> None:
    from app.core.logging import JsonFormatter

    try:
        raise ValueError("kaput")
    except ValueError:
        record = logging.LogRecord("t", logging.ERROR, __file__, 1, "failed", None, sys.exc_info())
    line = json.loads(JsonFormatter().format(record))
    assert "ValueError: kaput" in line["exception"]
