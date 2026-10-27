"""
Khmer Translator AI — Telegram Incident Notification Formatter (Bilingual: English & Khmer).
Generates structured incident reports with dual English & Khmer labels and Cambodia Local Time (Asia/Phnom_Penh, UTC+7).
"""
from __future__ import annotations

from typing import Optional
from ..config import redact_secrets
from ..models import EventCategory, Incident, Severity, format_cambodia_time


# Bilingual mapping dictionaries
_EVENT_KH = {
    "FRONTEND": "FRONTEND (ប្រព័ន្ធវេបសាយ Cloudflare)",
    "BACKEND": "BACKEND (ប្រព័ន្ធម៉ាស៊ីនបម្រើ API Render)",
    "RECOVERY": "RECOVERY (ដំណើរការប្រក្រតីឡើងវិញ)",
    "CI": "CI PIPELINE (ការតេស្តកូដស្វ័យប្រវត្តិ)",
    "AI REPAIR": "AI REPAIR (ការជួសជុលស្វ័យប្រវត្តិដោយ AI)",
    "MONITORING": "MONITORING (ការត្រួតពិនិត្យប្រព័ន្ធ)",
    "SAFETY": "SAFETY (ការការពារសុវត្ថិភាពកូដ)",
}

_SEVERITY_KH = {
    "CRITICAL": "CRITICAL 🔴 (ធ្ងន់ធ្ងរ - សេវាដាច់)",
    "WARNING": "WARNING 🟡 (កម្រិតមធ្យម - គួរប្រុងប្រយ័ត្ន)",
    "INFO": "INFO 🟢 (ព័ត៌មានទូទៅ / ប្រក្រតី)",
}


def format_telegram_alert(
    event: EventCategory,
    severity: Severity,
    affected_service: str,
    incident_id: str,
    problem: str,
    evidence: str,
    root_cause: str = "Unknown / មិនទាន់ដឹងច្បាស់",
    action_taken: str = "Automated health check detected failure / ប្រព័ន្ធចាប់បានបញ្ហាដោយស្វ័យប្រវត្តិ",
    test_results: str = "N/A",
    pull_request: Optional[str] = None,
    deployment_status: str = "Verified status only / ស្ថានភាពដែលបានផ្ទៀងផ្ទាត់",
    next_action: str = "Awaiting human review / រង់ចាំការពិនិត្យ",
    timestamp_kh: Optional[str] = None,
) -> str:
    """Formats incident notifications in both English and Khmer with Cambodia time."""
    time_str = timestamp_kh or format_cambodia_time()
    pr_str = pull_request if pull_request else "None / គ្មាន (មិនទាន់មាន PR)"

    event_text = _EVENT_KH.get(event.value, event.value)
    severity_text = _SEVERITY_KH.get(severity.value, severity.value)

    header_icon = "🚨" if severity == Severity.CRITICAL else ("⚠️" if severity == Severity.WARNING else "ℹ️")

    message = (
        f"{header_icon} <b>[KHMER TRANSLATOR AI — SELF-HEALING]</b>\n"
        f"🇰🇭 <b>ប្រព័ន្ធត្រួតពិនិត្យ និងជួសជុលស្វ័យប្រវត្តិតាមក្លោដ</b>\n\n"
        f"<b>• Event / ព្រឹត្តិការណ៍:</b> {event_text}\n"
        f"<b>• Severity / កម្រិត:</b> {severity_text}\n"
        f"<b>• Timestamp / ពេលវេលា:</b> {time_str}\n"
        f"<b>• Affected Service / សេវាកម្ម:</b> <code>{affected_service}</code>\n"
        f"<b>• Incident ID / លេខកូដបញ្ហា:</b> <code>{incident_id}</code>\n"
        f"<b>• Problem / បញ្ហា:</b> {redact_secrets(problem)}\n"
        f"<b>• Evidence / ភស្តុតាង:</b> <code>{redact_secrets(evidence[:350])}</code>\n"
        f"<b>• Root Cause / មូលហេតុឫសគល់:</b> {root_cause}\n"
        f"<b>• Action Taken / សកម្មភាពអនុវត្ត:</b> {action_taken}\n"
        f"<b>• Test Results / លទ្ធផលតេស្ត:</b> {test_results}\n"
        f"<b>• Pull Request / សំណើកូដជួសជុល:</b> {pr_str}\n"
        f"<b>• Deployment / ស្ថានភាព Deploy:</b> {deployment_status}\n"
        f"<b>• Next Action / ជំហានបន្ទាប់:</b> {next_action}\n"
    )
    return message


def format_recovery_alert(incident: Incident) -> str:
    """Formats verified recovery notifications in both English and Khmer."""
    return format_telegram_alert(
        event=EventCategory.RECOVERY_VERIFIED,
        severity=Severity.INFO,
        affected_service=incident.service.value,
        incident_id=incident.incident_id,
        problem=f"Resolved / បានដោះស្រាយរួចរាល់: {incident.error_summary}",
        evidence=f"Passed {incident.recovery_confirmations} consecutive health verification probes (HTTP 200 OK) / បានឆ្លងកាត់ការផ្ទៀងផ្ទាត់ {incident.recovery_confirmations} ដងជាប់គ្នាដោយជោគជ័យ",
        root_cause="Service Resumed / សេវាកម្មបានដំណើរការឡើងវិញជាប្រក្រតី",
        action_taken="Synthetic probe verified liveness / ប្រព័ន្ធបានផ្ទៀងផ្ទាត់ការឆ្លើយតបឡើងវិញ",
        test_results="100% Passed (HTTP 200)",
        pull_request=incident.pull_request_url,
        deployment_status="Healthy & Active / ដំណើរការល្អ និងសកម្ម",
        next_action="Incident closed automatically; 24/7 monitoring continues / បិទបញ្ហានេះស្វ័យប្រវត្តិ និងបន្តឃ្លាំមើល 24/7",
    )
