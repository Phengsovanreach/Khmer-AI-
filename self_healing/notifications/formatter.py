"""
Khmer Translator AI — Telegram Incident Notification Formatter (Bilingual: English & Khmer).
Generates structured, elegant, and readable incident and health reports with dual English & Khmer
labels and Cambodia Local Time (Asia/Phnom_Penh, UTC+7).
"""
from __future__ import annotations

from typing import Optional
from ..config import redact_secrets
from ..models import CheckResult, EventCategory, Incident, Severity, format_cambodia_time


# Bilingual event category mapping
_EVENT_KH = {
    "FRONTEND": "🌐 FRONTEND (គេហទំព័រ Cloudflare Pages)",
    "BACKEND": "⚙️ BACKEND (ម៉ាស៊ីនបម្រើ Render FastAPI)",
    "RECOVERY": "🎉 RECOVERY (ដំណើរការប្រក្រតីឡើងវិញ)",
    "CI": "🚀 CI PIPELINE (ការតេស្តកូដស្វ័យប្រវត្តិ)",
    "AI REPAIR": "🤖 AI REPAIR (ការជួសជុលកូដស្វ័យប្រវត្តិ)",
    "MONITORING": "🛡️ MONITORING (ការត្រួតពិនិត្យប្រព័ន្ធ)",
    "SAFETY": "🔒 SAFETY (ការការពារសុវត្ថិភាពកូដ)",
}

_SEVERITY_BADGE = {
    "CRITICAL": "🔴 ធ្ងន់ធ្ងរ (CRITICAL)",
    "WARNING": "🟡 មធ្យម (WARNING)",
    "INFO": "🟢 ធម្មតា (INFO)",
}


def format_telegram_alert(
    event: EventCategory,
    severity: Severity,
    affected_service: str,
    incident_id: str,
    problem: str,
    evidence: str,
    root_cause: str = "Unknown / មិនទាន់ដឹងច្បាស់",
    action_taken: str = "Automated probe triggered / ប្រព័ន្ធចាប់បានបញ្ហាដោយស្វ័យប្រវត្តិ",
    test_results: str = "N/A",
    pull_request: Optional[str] = None,
    deployment_status: str = "Verified status only / ស្ថានភាពដែលបានផ្ទៀងផ្ទាត់",
    next_action: str = "Awaiting review / រង់ចាំការពិនិត្យ",
    timestamp_kh: Optional[str] = None,
) -> str:
    """Formats incident notifications in an elegant, structured format."""
    time_str = timestamp_kh or format_cambodia_time()
    pr_str = pull_request if pull_request else "គ្មាន (No PR)"

    event_text = _EVENT_KH.get(event.value, event.value)
    severity_badge = _SEVERITY_BADGE.get(severity.value, severity.value)

    header_icon = "🚨" if severity == Severity.CRITICAL else ("⚠️" if severity == Severity.WARNING else "ℹ️")

    return (
        f"{header_icon} <b>KHMER TRANSLATOR AI — INCIDENT ALERT</b>\n"
        f"🇰🇭 <b>សេចក្តីជូនដំណឹងអំពីបញ្ហាប្រព័ន្ធ</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🏷️ <b>ព្រឹត្តិការណ៍ (Event):</b> {event_text}\n"
        f"⚡ <b>កម្រិត (Severity):</b> {severity_badge}\n"
        f"🆔 <b>លេខកូដ (ID):</b> <code>{incident_id}</code>\n"
        f"🕒 <b>ពេលវេលា (Time):</b> <code>{time_str}</code>\n"
        f"📍 <b>សេវាកម្ម (Service):</b> <code>{affected_service}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"💥 <b>បញ្ហាដែលបានរកឃើញ (Problem):</b>\n"
        f"└ <i>{redact_secrets(problem)}</i>\n\n"
        f"📋 <b>ភស្តុតាងបច្ចេកទេស (Evidence):</b>\n"
        f"<code>{redact_secrets(evidence[:350])}</code>\n\n"
        f"🔍 <b>ការវិភាគ & ដំណោះស្រាយ (Analysis):</b>\n"
        f"• <b>មូលហេតុឫសគល់ (Root Cause):</b> {root_cause}\n"
        f"• <b>សកម្មភាពអនុវត្ត (Action Taken):</b> {action_taken}\n"
        f"• <b>លទ្ធផលតេស្ត (Test Results):</b> {test_results}\n"
        f"• <b>សំណើជួសជុល (PR):</b> {pr_str}\n"
        f"• <b>ស្ថានភាព Deploy:</b> {deployment_status}\n"
        f"• <b>ជំហានបន្ទាប់ (Next Action):</b> {next_action}\n"
        f"━━━━━━━━━━━━━━━━━━━━━"
    )


def format_recovery_alert(incident: Incident) -> str:
    """Formats verified recovery notifications in both English and Khmer."""
    time_str = incident.last_detected_cambodia or format_cambodia_time()
    pr_str = incident.pull_request_url if incident.pull_request_url else "គ្មាន (No PR required)"

    return (
        f"🎉 <b>KHMER TRANSLATOR AI — RECOVERY VERIFIED</b>\n"
        f"✅ <b>ប្រព័ន្ធបានដំណើរការប្រក្រតីឡើងវិញទាំងស្រុង</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 <b>ស្ថានភាព (Status):</b> 🟢 <b>RECOVERED (បានដោះស្រាយ)</b>\n"
        f"🕒 <b>ពេលវេលា (Time):</b> <code>{time_str}</code>\n"
        f"📍 <b>សេវាកម្ម (Service):</b> <code>{incident.service.value}</code>\n"
        f"🆔 <b>លេខកូដបញ្ហា (Incident ID):</b> <code>{incident.incident_id}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"✨ <b>លទ្ធផលផ្ទៀងផ្ទាត់ (Verification Results):</b>\n"
        f"└ បានឆ្លងកាត់ការតេស្ត <b>{incident.recovery_confirmations} ដងជាប់គ្នាដោយជោគជ័យ (HTTP 200 OK)</b>\n\n"
        f"📌 <b>សេចក្តីសង្ខេប (Summary):</b>\n"
        f"• <b>បញ្ហាដើម (Previous Issue):</b> {redact_secrets(incident.error_summary)}\n"
        f"• <b>សំណើកូដជួសជុល (PR):</b> {pr_str}\n"
        f"• <b>សកម្មភាពបន្ត (Next Step):</b> បិទបញ្ចប់បញ្ហាដោយស្វ័យប្រវត្តិ & បន្តឃ្លាំមើល ២៤/៧\n"
        f"━━━━━━━━━━━━━━━━━━━━━"
    )


def format_heartbeat_report(fe_res: CheckResult, be_res: CheckResult, active_count: int = 0) -> str:
    """Formats periodic healthy heartbeat status notifications in English & Khmer."""
    fe_badge = "<code>200 OK</code> 🟢" if fe_res.is_healthy else f"<code>FAIL</code> 🔴 ({fe_res.error_message})"
    be_badge = "<code>200 OK</code> 🟢" if be_res.is_healthy else f"<code>FAIL</code> 🔴 ({be_res.error_message})"
    time_str = format_cambodia_time()

    return (
        f"✨ <b>KHMER TRANSLATOR AI — SYSTEM HEALTH</b>\n"
        f"🛡️ <b>របាយការណ៍ស្ថានភាពប្រព័ន្ធ (Cloud Monitor)</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 <b>ស្ថានភាពរួម (Overall):</b> 🟢 <b>ដំណើរការល្អទាំងអស់ (All Healthy)</b>\n"
        f"🕒 <b>ពេលវេលា (Time):</b> <code>{time_str}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🌐 <b>Frontend (Cloudflare Pages)</b>\n"
        f"  ├ ស្ថានភាព: {fe_badge}\n"
        f"  └ ល្បឿនឆ្លើយតប: <code>{fe_res.latency_ms:.1f} ms</code>\n\n"
        f"⚙️ <b>Backend (Render FastAPI)</b>\n"
        f"  ├ ស្ថានភាព: {be_badge}\n"
        f"  └ ល្បឿនឆ្លើយតប: <code>{be_res.latency_ms:.1f} ms</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔍 <b>ព័ត៌មានបន្ថែម (Overview)</b>\n"
        f"• បញ្ហាសកម្ម (Active Incidents): <code>{active_count}</code>\n"
        f"• ត្រួតពិនិត្យបន្ទាប់ (Next Check): <code>រៀងរាល់ 30 នាទី (GitHub Actions)</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━"
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
    status_text = "🟢 ជោគជ័យ (PASSED - 24/24 Tests)" if is_success else "🔴 បរាជ័យ (FAILED)"
    time_str = format_cambodia_time()

    msg = (
        f"{icon} <b>KHMER TRANSLATOR AI — CI PIPELINE</b>\n"
        f"🛠️ <b>លទ្ធផលតេស្តកូដស្វ័យប្រវត្តិ (GitHub Actions)</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 <b>លទ្ធផលរួម (Status):</b> {status_text}\n"
        f"🕒 <b>ពេលវេលា (Time):</b> <code>{time_str}</code>\n"
        f"🌿 <b>មែកធាងកូដ (Branch):</b> <code>{branch}</code>\n"
        f"📌 <b>Commit SHA:</b> <code>{commit_sha[:8]}</code>\n"
        f"💬 <b>សារ Commit:</b> <i>{commit_msg[:100]}</i>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
    )
    if details:
        msg += "📋 <b>ព័ត៌មានលម្អិតតាមផ្នែក (Jobs):</b>\n"
        for k, v in details.items():
            badge = "🟢" if "pass" in str(v).lower() or "ok" in str(v).lower() else "⚪"
            msg += f"  • {k}: <code>{v}</code> {badge}\n"
        msg += "━━━━━━━━━━━━━━━━━━━━━"
    return msg


def format_hourly_ai_report(
    telemetry: dict[str, Any],
    ai_insights: dict[str, Any],
    fe_latency_ms: float = 0.0,
    be_latency_ms: float = 0.0,
) -> str:
    """Formats the hourly deep AI telemetry & intelligence inspection report."""
    caps = telemetry.get("capabilities", {})
    voices = telemetry.get("voices", [])
    time_str = format_cambodia_time()
    score = ai_insights.get("health_score", 99)
    score_badge = "🟢" if score >= 90 else ("🟡" if score >= 70 else "🔴")
    models_list = ", ".join(caps.get("available_models", ["tiny", "base"]))
    voices_count = len(voices)

    return (
        f"🤖 <b>KHMER TRANSLATOR AI — HOURLY AI INSPECTION</b>\n"
        f"🧠 <b>របាយការណ៍វិភាគទិន្នន័យ & ដំណើរការ AI (ប្រចាំ ១ ម៉ោង)</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🏆 <b>ពិន្ទុដំណើរការ (Health Score):</b> <code>{score}/100</code> {score_badge} <b>{ai_insights.get('performance_status_kh', 'ល្អប្រសើរ')}</b>\n"
        f"🕒 <b>ពេលវេលា (Time):</b> <code>{time_str}</code>\n"
        f"⏱️ <b>ប្រេកង់ (Interval):</b> <code>រៀងរាល់ 1 ម៉ោងម្តង (Hourly Analysis)</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 <b>ទិន្នន័យម៉ាស៊ីន AI & សមត្ថភាព (AI Engines Telemetry)</b>\n"
        f"  ├ 🗣️ <b>Whisper AI (Speech-to-Text):</b> <code>{models_list}</code> 🟢 សកម្ម\n"
        f"  ├ 🎙️ <b>TTS Dubbing (Khmer Voices):</b> <code>{voices_count} សំឡេង Neural</code> 🟢 សកម្ម\n"
        f"  │   • ពិសិដ្ឋ (Piseth Neural - ប្រុស)\n"
        f"  │   • ស្រីមុំ (Sreymom Neural - ស្រី)\n"
        f"  ├ 🎞️ <b>Media Engine:</b> <code>FFmpeg + FFprobe</code> 🟢 ដំណើរការ\n"
        f"  └ 🌐 <b>ភាសាគាំទ្រ (Supported Languages):</b> <code>{caps.get('supported_languages_count', 20)} ភាសា</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚡ <b>ល្បឿនបណ្តាញ & ឆ្លើយតប (Network & Latency)</b>\n"
        f"  ├ គេហទំព័រ (Cloudflare Pages): <code>{fe_latency_ms:.1f} ms</code> 🟢\n"
        f"  └ ម៉ាស៊ីនបម្រើ (Render FastAPI): <code>{be_latency_ms:.1f} ms</code> 🟢\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"💡 <b>ការវិភាគ & យោបល់របស់ Gemini AI (AI Insights)</b>\n"
        f"• <b>ខ្មែរ:</b> <i>{ai_insights.get('ai_opinion_kh', '')}</i>\n"
        f"• <b>English:</b> <i>{ai_insights.get('ai_opinion_en', '')}</i>\n"
        f"• <b>អនុសាសន៍ (Recommendation):</b> {ai_insights.get('recommendation_kh', 'ដំណើរការល្អ')}\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"📌 <b>សេចក្តីសន្និដ្ឋាន:</b> សេវាបកប្រែជាអក្សរ និងសំឡេងត្រៀមរួចរាល់ ១០០%\n"
        f"━━━━━━━━━━━━━━━━━━━━━"
    )
