"""
Unit tests for self-healing models, configuration, and credential redaction.
"""
from datetime import datetime, timezone, timedelta
from self_healing.config import Config, redact_secrets
from self_healing.models import (
    CheckResult,
    EventCategory,
    Incident,
    IncidentStatus,
    ServiceType,
    Severity,
    format_cambodia_time,
    get_cambodia_time,
)


def test_cambodia_time_offset():
    utc_time = datetime(2026, 10, 28, 0, 0, 0, tzinfo=timezone.utc)
    kh_time = get_cambodia_time(utc_time)
    assert kh_time.hour == 7
    assert kh_time.day == 28
    formatted = format_cambodia_time(utc_time)
    assert "2026-10-28 07:00:00" in formatted
    assert "UTC+7" in formatted


def test_secret_redaction():
    telegram_token = "9125016671:AAEvM_UP5tYvFuBLQfryX_aY6_dzgL9GIII"
    github_pat = "ghp_1234567890abcdefghijklmnopqrstuvwxyz"
    bearer_token = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xyz"
    raw_text = f"Error connecting with {telegram_token} and auth {bearer_token} using {github_pat}"

    clean_text = redact_secrets(raw_text)
    assert telegram_token not in clean_text
    assert github_pat not in clean_text
    assert "[REDACTED_CREDENTIAL]" in clean_text


def test_incident_serialization():
    inc = Incident(
        incident_id="INC-BE-001",
        service=ServiceType.BACKEND,
        status=IncidentStatus.CONFIRMED_FAILURE,
        consecutive_failures=3,
        first_detected_utc="2026-10-28T00:00:00Z",
        last_detected_utc="2026-10-28T00:05:00Z",
        first_detected_cambodia="2026-10-28 07:00:00 ICT",
        last_detected_cambodia="2026-10-28 07:05:00 ICT",
        error_summary="HTTP 502 Bad Gateway",
    )
    d = inc.to_dict()
    assert d["service"] == "BACKEND"
    assert d["status"] == "CONFIRMED_FAILURE"

    restored = Incident.from_dict(d)
    assert restored.incident_id == "INC-BE-001"
    assert restored.service == ServiceType.BACKEND
    assert restored.status == IncidentStatus.CONFIRMED_FAILURE
