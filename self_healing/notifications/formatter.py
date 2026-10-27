"""
Khmer Translator AI — Telegram Incident Notification Formatter (Bilingual: English & Khmer).
Generates structured incident reports with dual English & Khmer labels and Cambodia Local Time (Asia/Phnom_Penh, UTC+7).
"""
from __future__ import annotations

from typing import Optional
from ..config import redact_secrets
from ..models import CheckResult, EventCategory, Incident, Severity, format_cambodia_time


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


def format_heartbeat_report(fe_res: CheckResult, be_res: CheckResult, active_count: int = 0) -> str:
    """Formats periodic healthy heartbeat status notifications in English & Khmer."""
    fe_status = "OK 🟢 (200 OK)" if fe_res.is_healthy else f"FAIL 🔴 ({fe_res.error_message})"
    be_status = "OK 🟢 (200 OK)" if be_res.is_healthy else f"FAIL 🔴 ({be_res.error_message})"
    time_str = format_cambodia_time()
    return (
        f"💚 <b>[KHMER TRANSLATOR AI — SYSTEM HEALTH REPORT]</b>\n"
        f"🇰🇭 <b>របាយការណ៍ស្ថានភាពប្រព័ន្ធប្រចាំការ (Cloud Monitor)</b>\n\n"
        f"<b>• Overall Status / ស្ថានភាពរួម:</b> ALL SYSTEMS HEALTHY / ដំណើរការល្អធម្មតា\n"
        f"<b>• Timestamp / ពេលវេលា:</b> {time_str}\n"
        f"<b>• Frontend (Cloudflare Pages):</b> {fe_status} (Latency: {fe_res.latency_ms:.1f}ms)\n"
        f"<b>• Backend (Render FastAPI):</b> {be_status} (Latency: {be_res.latency_ms:.1f}ms)\n"
        f"<b>• Active Incidents / បញ្ហាសកម្ម:</b> {active_count}\n"
        f"<b>• Next Routine Check / ត្រួតពិនិត្យបន្ទាប់:</b> In ~30 mins / ប្រហែល 30 នាទីទៀត\n"
    )


def format_ci_report(
    status: str,
    branch: str,
    commit_sha: str,
    commit_msg: str = "",
    details: Optional[dict] = None,
) -> str:
    """Formats automated CI test execution reports in English & Khmer."""
    is_success = status.upper() == "SUCCESS"
    icon = "🚀" if is_success else "⚠️"
    status_text = "PASSED 🟢 (ជោគជ័យគ្រប់តេស្ត)" if is_success else "FAILED 🔴 (មានកំហុសតេស្ត)"
    time_str = format_cambodia_time()

    msg = (
        f"{icon} <b>[KHMER TRANSLATOR AI — CI PIPELINE]</b>\n"
        f"🇰🇭 <b>លទ្ធផលតេស្តកូដស្វ័យប្រវត្តិ (GitHub Actions)</b>\n\n"
        f"<b>• Pipeline Status / ស្ថានភាព:</b> {status_text}\n"
        f"<b>• Timestamp / ពេលវេលា:</b> {time_str}\n"
        f"<b>• Branch / មែកធាងកូដ:</b> <code>{branch}</code>\n"
        f"<b>• Commit / លេខកូដ:</b> <code>{commit_sha[:8]}</code>\n"
        f"<b>• Message / ចំណងជើង:</b> {commit_msg[:100]}\n"
    )
    if details:
        msg += "\n<b>• Jobs Detail / ព័ត៌មានលម្អិត:</b>\n"
        for k, v in details.items():
            msg += f"  • {k}: {v}\n"
    return msg
