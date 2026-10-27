"""
Tests for AI Failure Analyzer and Diagnostic Collector.
"""
import json
from unittest.mock import MagicMock, patch

from self_healing.ai.analyzer import FailureAnalyzer
from self_healing.ai.gemini_provider import GeminiProvider
from self_healing.diagnostics.collector import DiagnosticCollector
from self_healing.models import CheckResult, Incident, IncidentStatus, ServiceType


def test_diagnostics_collector():
    inc = Incident(
        incident_id="INC-BE-999",
        service=ServiceType.BACKEND,
        status=IncidentStatus.CONFIRMED_FAILURE,
        consecutive_failures=2,
        first_detected_utc="2026-10-28T00:00:00Z",
        last_detected_utc="2026-10-28T00:02:00Z",
        first_detected_cambodia="2026-10-28 07:00:00 ICT",
        last_detected_cambodia="2026-10-28 07:02:00 ICT",
        error_summary="Failed with token 9125016671:AAEvM_UP5tYvFuBLQfryX_aY6_dzgL9GIII",
    )
    chk = CheckResult(
        service=ServiceType.BACKEND,
        url="https://api.example.com",
        is_healthy=False,
        status_code=500,
        latency_ms=300.0,
        error_message="Internal server error with sk-1234567890abcdef1234567890",
    )

    evidence = DiagnosticCollector.collect_incident_evidence(inc, latest_result=chk)
    assert evidence["incident_id"] == "INC-BE-999"
    assert "9125016671:AAEvM_UP5tYvFuBLQfryX_aY6_dzgL9GIII" not in str(evidence)
    assert "sk-1234567890abcdef1234567890" not in str(evidence)
    assert "[REDACTED_CREDENTIAL]" in evidence["raw_error"]


def test_ai_analyzer_unconfigured():
    analyzer = FailureAnalyzer(provider=None)
    inc = Incident(
        incident_id="INC-BE-999",
        service=ServiceType.BACKEND,
        status=IncidentStatus.CONFIRMED_FAILURE,
        consecutive_failures=2,
        first_detected_utc="2026-10-28T00:00:00Z",
        last_detected_utc="2026-10-28T00:02:00Z",
        first_detected_cambodia="2026-10-28 07:00:00 ICT",
        last_detected_cambodia="2026-10-28 07:02:00 ICT",
        error_summary="Connection timed out after 30 seconds",
    )
    evidence = {"raw_error": "Connection timed out after 30 seconds"}
    report = analyzer.diagnose_incident(inc, evidence)

    assert report.status == "AI_ANALYSIS_NOT_CONFIGURED"
    assert report.failure_category == "TIMEOUT_COLD_START"
    assert report.confidence > 0.5


def test_ai_analyzer_insufficient_evidence():
    analyzer = FailureAnalyzer(provider=None)
    inc = Incident(
        incident_id="INC-BE-999",
        service=ServiceType.BACKEND,
        status=IncidentStatus.CONFIRMED_FAILURE,
        consecutive_failures=2,
        first_detected_utc="2026-10-28T00:00:00Z",
        last_detected_utc="2026-10-28T00:02:00Z",
        first_detected_cambodia="2026-10-28 07:00:00 ICT",
        last_detected_cambodia="2026-10-28 07:02:00 ICT",
        error_summary="",
    )
    evidence = {"raw_error": ""}
    report = analyzer.diagnose_incident(inc, evidence)

    assert report.status == "INSUFFICIENT_EVIDENCE"
    assert report.confidence == 0.1
    assert "Insufficient" in report.probable_root_cause


def test_gemini_provider_mock_success():
    provider = GeminiProvider(api_key="mock_key")
    mock_resp = MagicMock()
    mock_payload = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": json.dumps({
                                "failure_category": "DATABASE_LOCK",
                                "probable_root_cause": "SQLite database was locked by another transaction.",
                                "confidence": 0.9,
                                "proposed_fix": "Enable WAL mode on auth.db connection.",
                                "tests_required": ["test_auth.py"],
                                "safety_risks": ["Verify schema migration compatibility."],
                            })
                        }
                    ]
                }
            }
        ]
    }
    mock_resp.read.return_value = json.dumps(mock_payload).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        res = provider.generate_analysis("Diagnose this failure")
        assert res is not None
        assert res["failure_category"] == "DATABASE_LOCK"
        assert res["confidence"] == 0.9
