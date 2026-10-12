from __future__ import annotations
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings


@pytest.fixture
def client():
    return TestClient(app)


def test_health_endpoint_version(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["version"] == "2.0.0"
    assert "Khmer Translator" in data["app"]


def test_readiness_probe(client):
    res = client.get("/api/ready")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ("ready", "degraded")
    assert "checks" in data
    assert "ffmpeg" in data["checks"]
    assert "storage_writable" in data["checks"]
    assert data["checks"]["storage_writable"] is True


def test_system_diagnostics_sanitized(client):
    res = client.get("/api/system/diagnostics")
    assert res.status_code == 200
    data = res.json()
    assert data["app_version"] == "2.0.0"
    assert data["platform"]
    assert data["cpu_cores"] >= 1
    assert data["memory_total_mb"] > 0
    assert data["storage_free_mb"] > 0
    assert isinstance(data["sanitized_cors_origins"], list)

    # Verify no secrets or sensitive env leaks
    raw_str = res.text.lower()
    for secret_keyword in ("secret", "password", "token", "api_key", "private_key"):
        assert secret_keyword not in raw_str


def test_cors_origins_parsing():
    from app.config import Settings
    custom_cfg = Settings(cors_origins="https://example.com, https://app.example.com")
    assert custom_cfg.cors_origins == ["https://example.com", "https://app.example.com"]
