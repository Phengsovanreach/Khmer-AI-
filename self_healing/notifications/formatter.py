"""
Khmer Translator AI — Telegram Incident Notification Formatter.
Generates structured incident reports with Cambodia Local Time (Asia/Phnom_Penh, UTC+7).
"""
from __future__ import annotations

from typing import Optional
from ..config import redact_secrets
from ..models import EventCategory, Incident, Severity, format_cambodia_time


def format_telegram_alert(
    event: EventCategory,
    severity: Severity,
    affected_service: str,
    incident_id: str,
    problem: str,
    evidence: str,
    root_cause: str = "Unknown",  # Confirmed / Probable / Unknown
    action_taken: str = "Automated health check detected failure",
    test_results: str = "N/A",
    pull_request: Optional[str] = None,
    deployment_status: str = "Verified status only",
    next_action: str = "Awaiting human review",
    timestamp_kh: Optional[str] = None,
) -> str:
    """Formats incident notifications matching the exact production standard."""
    time_str = timestamp_kh or format_cambodia_time()
    pr_str = pull_request if pull_request else "None (No PR created)"

    message = (
        f"🚨 <b>[KHMER TRANSLATOR AI — SELF-HEALING]</b>\n\n"
        f"<b>Event:</b> {event.value}\n"
        f"<b>Severity:</b> {severity.value}\n"
        f"<b>Timestamp:</b> {time_str}\n"
        f"<b>Affected service:</b> {affected_service}\n"
        f"<b>Incident ID:</b> <code>{incident_id}</code>\n"
        f"<b>Problem:</b> {redact_secrets(problem)}\n"
        f"<b>Evidence:</b> <code>{redact_secrets(evidence[:350])}</code>\n"
        f"<b>Root cause:</b> {root_cause}\n"
        f"<b>Action taken:</b> {action_taken}\n"
        f"<b>Test results:</b> {test_results}\n"
        f"<b>Pull Request:</b> {pr_str}\n"
        f"<b>Deployment status:</b> {deployment_status}\n"
        f"<b>Next action:</b> {next_action}\n"
    )
    return message


def format_recovery_alert(incident: Incident) -> str:
    """Formats verified recovery notifications."""
    return format_telegram_alert(
        event=EventCategory.RECOVERY_VERIFIED,
        severity=Severity.INFO,
        affected_service=incident.service.value,
        incident_id=incident.incident_id,
        problem=f"Previous outage resolved: {incident.error_summary}",
        evidence=f"Service passed {incident.recovery_confirmations} consecutive health verification checks.",
        root_cause="Recovered / Resolved",
        action_taken="Verified service liveness and responsiveness",
        test_results="Passed synthetic health and readiness probes (HTTP 200)",
        pull_request=incident.pull_request_url,
        deployment_status="Active & Responding",
        next_action="Incident closed automatically; normal 24/7 monitoring continues.",
    )
