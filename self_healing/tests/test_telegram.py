"""
Tests for Telegram Notification Engine using mocks.
"""
from io import BytesIO
import json
import urllib.error
from unittest.mock import MagicMock, patch

from self_healing.config import Config
from self_healing.models import EventCategory, Severity
from self_healing.notifications.formatter import format_telegram_alert
from self_healing.notifications.telegram import TelegramNotifier


def test_telegram_unconfigured(monkeypatch):
    monkeypatch.setattr(Config, "TELEGRAM_BOT_TOKEN", None)
    monkeypatch.setattr(Config, "TELEGRAM_CHAT_ID", None)
    notifier = TelegramNotifier(token=None, chat_id=None)
    assert notifier.is_configured is False
    res = notifier.send_message("Test message")
    assert res["status"] == "TELEGRAM_NOT_CONFIGURED"
    assert res["delivered"] is False


def test_telegram_successful_delivery():
    notifier = TelegramNotifier(token="mock_token_12345", chat_id="123456789")
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps({"ok": True, "result": {"message_id": 999}}).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        res = notifier.send_message("<b>Alert</b>: Test")
        assert res["status"] == "DELIVERED"
        assert res["delivered"] is True
        assert res["message_id"] == 999


def test_telegram_rate_limit_handled():
    notifier = TelegramNotifier(token="mock_token_12345", chat_id="123456789")
    mock_429 = urllib.error.HTTPError(
        url="https://api.telegram.org",
        code=429,
        msg="Too Many Requests",
        hdrs={},
        fp=BytesIO(b'{"ok": false, "parameters": {"retry_after": 1}}'),
    )
    mock_success = MagicMock()
    mock_success.read.return_value = json.dumps({"ok": True, "result": {"message_id": 1000}}).encode("utf-8")
    mock_success.__enter__.return_value = mock_success

    with patch("urllib.request.urlopen", side_effect=[mock_429, mock_success]), patch("time.sleep"):
        res = notifier.send_message("Rate limited alert")
        assert res["delivered"] is True
        assert res["message_id"] == 1000


def test_telegram_redaction_in_message():
    secret_token = "9125016671:AAEvM_UP5tYvFuBLQfryX_aY6_dzgL9GIII"
    msg = format_telegram_alert(
        event=EventCategory.FRONTEND_OUTAGE,
        severity=Severity.CRITICAL,
        affected_service="FRONTEND",
        incident_id="INC-001",
        problem=f"Failed auth with token {secret_token}",
        evidence="Connection refused",
    )
    assert secret_token not in msg
    assert "[REDACTED_CREDENTIAL]" in msg
    assert "Asia/Phnom_Penh" not in msg  # Ensure proper ICT formatting
    assert "ICT (UTC+7)" in msg


def test_telegram_chunking_large_message():
    notifier = TelegramNotifier(token="mock_token_12345", chat_id="123456789")
    chunks = notifier._chunk_message("A\n" * 2500, max_len=4000)
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk) <= 4000
