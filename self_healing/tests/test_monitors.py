"""
Tests for Frontend and Backend Synthetic Health Monitors using mocks.
"""
from io import BytesIO
import urllib.error
from unittest.mock import MagicMock, patch

from self_healing.models import ServiceType
from self_healing.monitors.frontend_monitor import check_frontend_health
from self_healing.monitors.backend_monitor import check_backend_health


def test_frontend_healthy_probe():
    html_content = b"<!DOCTYPE html><html><head><title>Khmer Translator</title></head><body><div id='root'></div></body></html>"
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.headers = {"Content-Type": "text/html; charset=utf-8", "Server": "cloudflare", "CF-RAY": "123456"}
    mock_resp.read.return_value = html_content
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        res = check_frontend_health("https://example.com/mock")
        assert res.is_healthy is True
        assert res.status_code == 200
        assert res.service == ServiceType.FRONTEND
        assert res.details.get("verified_dom") is True


def test_frontend_http_500_failure():
    mock_error = urllib.error.HTTPError(
        url="https://example.com/mock",
        code=500,
        msg="Internal Server Error",
        hdrs={},
        fp=BytesIO(b"Server Crash"),
    )
    with patch("urllib.request.urlopen", side_effect=mock_error):
        res = check_frontend_health("https://example.com/mock")
        assert res.is_healthy is False
        assert res.status_code == 500
        assert "500" in res.error_message


def test_frontend_cloudflare_521_failure():
    mock_error = urllib.error.HTTPError(
        url="https://example.com/mock",
        code=521,
        msg="Web Server Is Down",
        hdrs={},
        fp=BytesIO(b"Cloudflare Error"),
    )
    with patch("urllib.request.urlopen", side_effect=mock_error):
        res = check_frontend_health("https://example.com/mock")
        assert res.is_healthy is False
        assert res.status_code == 521
        assert "Cloudflare Edge Error 521" in res.error_message


def test_frontend_timeout_failure():
    mock_error = urllib.error.URLError("The read operation timed out")
    with patch("urllib.request.urlopen", side_effect=mock_error):
        res = check_frontend_health("https://example.com/mock")
        assert res.is_healthy is False
        assert res.status_code is None
        assert "timed out" in res.error_message.lower()


def test_backend_healthy_probe():
    json_content = b'{"status": "ok", "app": "Khmer Translator API", "version": "2.0.0"}'
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.headers = {"Content-Type": "application/json", "x-render-origin-server": "uvicorn"}
    mock_resp.read.return_value = json_content
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp), \
         patch("self_healing.monitors.backend_monitor._probe_readiness", return_value={"ffmpeg": True}):
        res = check_backend_health("https://example.com/api/health")
        assert res.is_healthy is True
        assert res.status_code == 200
        assert res.service == ServiceType.BACKEND
        assert res.details.get("version") == "2.0.0"


def test_backend_http_502_failure():
    mock_error = urllib.error.HTTPError(
        url="https://example.com/api/health",
        code=502,
        msg="Bad Gateway",
        hdrs={},
        fp=BytesIO(b"Bad Gateway"),
    )
    # allow_cold_start_retry=False to test pure failure path
    with patch("urllib.request.urlopen", side_effect=mock_error):
        res = check_backend_health("https://example.com/api/health", allow_cold_start_retry=False)
        assert res.is_healthy is False
        assert res.status_code == 502
        assert "502" in res.error_message


def test_backend_timeout_failure():
    mock_error = urllib.error.URLError("Connection timed out")
    with patch("urllib.request.urlopen", side_effect=mock_error):
        res = check_backend_health("https://example.com/api/health", allow_cold_start_retry=False)
        assert res.is_healthy is False
        assert res.status_code is None
        assert "timed out" in res.error_message.lower()
