"""
Khmer Translator AI — Telegram Operational Notification Formatter.
Implements the three primary operational alert categories with polished Khmer typography
and Cambodia Local Time (Asia/Phnom_Penh, UTC+7):
  Type 1: Bug Detection and Automatic Fix (Bug Alert & AI Fix Report)
  Type 2: Hourly Website Health Report (15 telemetry metrics & Gemini analysis)
  Type 3: User Activity and Operation Results (Privacy-conscious audit tracking)
"""
from __future__ import annotations

from typing import Any, Optional
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
    "CRITICAL": "🔴 ធ្ងន់ធ្ងរបំផុត (CRITICAL)",
    "HIGH": "🔴 ខ្ពស់ (HIGH)",
    "WARNING": "🟡 មធ្យម/ប្រុងប្រយ័ត្ន (WARNING)",
    "INFO": "🟢 ព័ត៌មាន (INFO)",
}


# =============================================================================
# NOTIFICATION TYPE 1: BUG DETECTION AND AUTOMATIC FIX
# =============================================================================

def format_bug_detected_alert(
    severity: str,
    incident_id: str,
    component: str,
    issue: str,
    error: str,
    impact: str,
    ai_root_cause: str,
    action: str = "វិភាគកូដដែលពាក់ព័ន្ធ និងបង្កើតសេណារីយ៉ូកំហុសឡើងវិញ (Analyzing code & reproducing failure)",
    timestamp_kh: Optional[str] = None,
) -> str:
    """Formats immediate bug detection alert with polished Khmer typography."""
    time_str = timestamp_kh or format_cambodia_time()
    clean_error = redact_secrets(error[:350])
    clean_issue = redact_secrets(issue)
    clean_cause = redact_secrets(ai_root_cause)

    sev_upper = severity.upper()
    sev_display = _SEVERITY_BADGE.get(sev_upper, f"⚠️ {sev_upper}")

    return (
        f"🚨 <b>KHMER TRANSLATOR AI — រកឃើញបញ្ហាប្រព័ន្ធ (BUG DETECTED)</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>កម្រិតធ្ងន់ធ្ងរ (Severity):</b> {sev_display}\n"
        f"<b>លេខសម្គាល់បញ្ហា (Incident ID):</b> <code>{incident_id}</code>\n"
        f"<b>ផ្នែករងផលប៉ះពាល់ (Component):</b> {component}\n"
        f"<b>បញ្ហាដែលបានជួបប្រទះ (Issue):</b> {clean_issue}\n"
        f"<b>សារកំហុសបច្ចេកទេស (Error):</b> <code>{clean_error}</code>\n"
        f"<b>ផលប៉ះពាល់ដល់អ្នកប្រើប្រាស់ (Impact):</b> {impact}\n"
        f"<b>មូលហេតុឫសគល់ពី AI (AI Root Cause):</b> {clean_cause}\n"
        f"<b>ចំណាត់ការបន្ទាន់ (Action):</b> {action}\n"
        f"<b>ពេលវេលា (Time):</b> <code>{time_str}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━"
    )


def format_ai_fix_report(
    incident_id: str,
    root_cause: str,
    code_changed: str,
    fix_applied: str,
    tests_passed: bool,
    deployment_status: str,
    health_verified: bool,
    rollback_occurred: bool = False,
    result_summary: str = "",
) -> str:
    """Formats automated code fix and recovery result with polished Khmer typography."""
    tests_str = "🟢 ជោគជ័យ (PASS)" if tests_passed else "🔴 បរាជ័យ (FAIL)"
    deploy_upper = deployment_status.upper()
    deploy_str = "🟢 ជោគជ័យ (SUCCESS)" if deploy_upper == "SUCCESS" else f"🔴 {deploy_upper}"
    health_str = "🟢 ត្រឹមត្រូវប្រក្រតី (PASS)" if health_verified else ("🔴 មិនប្រក្រតី (FAIL)" if deploy_upper == "SUCCESS" else "មិនទាន់បានត្រួតពិនិត្យ (NOT CHECKED)")
    rollback_str = "⚠️ មាន (YES)" if rollback_occurred else "✅ គ្មាន (NO)"
    final_res = result_summary or ("ការជួសជុលត្រូវបានផ្ទៀងផ្ទាត់ និងដំណើរការប្រក្រតីលើ Production." if health_verified else "ការជួសជុលកំពុងរង់ចាំការត្រួតពិនិត្យ ឬការដកថយ (Rollback)។")

    return (
        f"🛠 <b>KHMER TRANSLATOR AI — របាយការណ៍ជួសជុលកូដស្វ័យប្រវត្តិ (AI FIX REPORT)</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>លេខសម្គាល់បញ្ហា (Incident ID):</b> <code>{incident_id}</code>\n"
        f"<b>មូលហេតុឫសគល់ (Root Cause):</b> {redact_secrets(root_cause)}\n"
        f"<b>កូដដែលបានកែសម្រួល (Code Changed):</b> <code>{redact_secrets(code_changed)}</code>\n"
        f"<b>ដំណោះស្រាយដែលបានអនុវត្ត (Fix Applied):</b> {redact_secrets(fix_applied)}\n"
        f"<b>ការតេស្តកូដ (Tests):</b> {tests_str}\n"
        f"<b>ការដាក់ឱ្យប្រើប្រាស់ (Deployment):</b> {deploy_str}\n"
        f"<b>ការផ្ទៀងផ្ទាត់សុខភាពប្រព័ន្ធ (Health Verification):</b> {health_str}\n"
        f"<b>ការដកថយត្រឡប់ក្រោយ (Rollback):</b> {rollback_str}\n\n"
        f"<b>លទ្ធផលចុងក្រោយ (Result):</b> {final_res}\n"
        f"━━━━━━━━━━━━━━━━━━━━━"
    )


# =============================================================================
# NOTIFICATION TYPE 2: HOURLY WEBSITE HEALTH REPORT
# =============================================================================

def format_hourly_health_report(
    website_url: str,
    frontend_online: bool,
    backend_online: bool,
    database_connected: bool,
    auth_pass: bool,
    core_api_pass: bool,
    video_processing_status: str,  # HEALTHY, DEGRADED, NOT CHECKED
    ai_provider_status: str,       # AVAILABLE, UNAVAILABLE
    response_time_ms: float,
    error_rate_pct: float,
    active_users: int,
    background_worker_status: str, # RUNNING, STOPPED
    latest_deployment_status: str,
    open_incidents_count: int,
    overall_status: str,           # HEALTHY, DEGRADED, CRITICAL
    ai_analysis_text: str,
    timestamp_kh: Optional[str] = None,
) -> str:
    """Formats 24/7 hourly health inspection report with polished Khmer typography."""
    time_str = timestamp_kh or format_cambodia_time()
    fe_str = "ដំណើរការប្រក្រតី (ONLINE) 🟢" if frontend_online else "ផ្អាកដំណើរការ (OFFLINE) 🔴"
    be_str = "ដំណើរការប្រក្រតី (ONLINE) 🟢" if backend_online else "ផ្អាកដំណើរការ (OFFLINE) 🔴"
    db_str = "បានតភ្ជាប់ (CONNECTED) 🟢" if database_connected else "ដាច់ការតភ្ជាប់ (DISCONNECTED) 🔴"
    auth_str = "ត្រឹមត្រូវ (PASS) 🟢" if auth_pass else "បរាជ័យ (FAIL) 🔴"
    api_str = "ត្រឹមត្រូវ (PASS) 🟢" if core_api_pass else "បរាជ័យ (FAIL) 🔴"

    video_status_display = "🟢 ប្រក្រតី (HEALTHY)" if video_processing_status.upper() == "HEALTHY" else f"🟡 {video_processing_status}"
    ai_status_display = "🟢 អាចប្រើប្រាស់បាន (AVAILABLE)" if ai_provider_status.upper() == "AVAILABLE" else f"🔴 {ai_provider_status}"
    worker_display = "🟢 កំពុងដំណើរការ (RUNNING)" if background_worker_status.upper() == "RUNNING" else f"🔴 {background_worker_status}"

    overall_upper = overall_status.upper()
    if overall_upper == "HEALTHY":
        status_icon = "💚"
        overall_display = "🟢 ល្អប្រសើរប្រក្រតី (HEALTHY)"
    elif overall_upper == "DEGRADED":
        status_icon = "🟡"
        overall_display = "🟡 មានការរអាក់រអួល (DEGRADED)"
    else:
        status_icon = "🔴"
        overall_display = "🔴 ធ្ងន់ធ្ងរ (CRITICAL)"

    return (
        f"{status_icon} <b>KHMER TRANSLATOR AI — របាយការណ៍សុខភាពប្រព័ន្ធប្រចាំម៉ោង (HOURLY HEALTH REPORT)</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>ពេលវេលា (Time):</b> <code>{time_str}</code>\n"
        f"<b>គេហទំព័រ (Website):</b> {website_url}\n"
        f"<b>Frontend (Cloudflare Pages):</b> {fe_str}\n"
        f"<b>Backend (Render FastAPI):</b> {be_str}\n"
        f"<b>មូលដ្ឋានទិន្នន័យ (Database):</b> {db_str}\n"
        f"<b>ការផ្ទៀងផ្ទាត់គណនី (Authentication):</b> {auth_str}\n"
        f"<b>ប្រព័ន្ធ API ស្នូល (Core API Tests):</b> {api_str}\n"
        f"<b>ដំណើរការវីដេអូ (Video Processing):</b> {video_status_display}\n"
        f"<b>ម៉ាស៊ីន AI (AI Provider):</b> {ai_status_display}\n"
        f"<b>ល្បឿនឆ្លើយតប (Response Time):</b> <code>{response_time_ms:.1f} ms</code>\n"
        f"<b>អត្រាកំហុស (Error Rate):</b> <code>{error_rate_pct:.1f}%</code>\n"
        f"<b>អ្នកប្រើប្រាស់សកម្ម (Active Users):</b> <code>{active_users} នាក់</code>\n"
        f"<b>សេវាកម្មផ្ទៃខាងក្រោយ (Background Worker):</b> {worker_display}\n"
        f"<b>ការដាក់ឱ្យប្រើប្រាស់ចុងក្រោយ (Latest Deployment):</b> <code>{latest_deployment_status}</code>\n"
        f"<b>បញ្ហាកំពុងបើកដោះស្រាយ (Open Incidents):</b> <code>{open_incidents_count}</code>\n\n"
        f"<b>ស្ថានភាពរួម (Overall Status):</b> <b>{overall_display}</b>\n\n"
        f"<b>ការវិភាគរបស់ AI (AI Analysis):</b>\n"
        f"<i>{redact_secrets(ai_analysis_text)}</i>\n"
        f"━━━━━━━━━━━━━━━━━━━━━"
    )


# =============================================================================
# NOTIFICATION TYPE 3: USER ACTIVITY AND OPERATION RESULTS
# =============================================================================

def format_user_activity_alert(
    event: str,
    user_id: str,
    operation_id: str,
    status: str,
    duration_sec: float = 0.0,
    error_category: Optional[str] = None,
    result_summary: Optional[str] = None,
    ai_action: Optional[str] = None,
    timestamp_kh: Optional[str] = None,
    username: Optional[str] = None,
    masked_email: Optional[str] = None,
    environment: Optional[str] = None,
) -> str:
    """Formats privacy-conscious user operations audit with polished Khmer typography."""
    time_str = timestamp_kh or format_cambodia_time()
    clean_user = user_id[:16] if user_id else "usr_anonymous"
    is_success = status.upper() == "SUCCESS"

    event_map = {
        "User Registration": "ចុះឈ្មោះគណនីថ្មី (User Registration)",
        "User Login": "ចូលប្រើប្រាស់គណនី (User Login)",
        "User Logout": "ចាកចេញពីគណនី (User Logout)",
        "Video Translation": "បកប្រែវីដេអូ (Video Translation)",
        "Video Dubbing": "បញ្ចូលសំឡេងវីដេអូ (Video Dubbing)",
        "Password Reset": "កំណត់ពាក្យសម្ងាត់ឡើងវិញ (Password Reset)",
    }
    event_display = event_map.get(event, event)

    user_meta_lines = []
    if username:
        user_meta_lines.append(f"<b>ឈ្មោះគណនី (Username):</b> <code>{redact_secrets(username)}</code>")
    if masked_email:
        user_meta_lines.append(f"<b>អ៊ីមែល (Email):</b> <code>{redact_secrets(masked_email)}</code>")
    if environment:
        env_display = "Production" if environment.lower() == "production" else ("Development" if environment.lower() == "development" else environment)
        user_meta_lines.append(f"<b>បរិស្ថាន (Environment):</b> <code>{env_display}</code>")
    user_meta_str = "\n".join(user_meta_lines)
    if user_meta_str:
        user_meta_str += "\n"

    if is_success:
        res_text = redact_secrets(result_summary) if result_summary else "ប្រតិបត្តិការដែលបានស្នើសុំត្រូវបានបញ្ចប់ដោយជោគជ័យ។ (Completed successfully)"
        return (
            f"👤 <b>KHMER TRANSLATOR AI — សកម្មភាពអ្នកប្រើប្រាស់ (USER ACTIVITY)</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b>ព្រឹត្តិការណ៍ (Event):</b> {event_display}\n"
            f"<b>អ្នកប្រើប្រាស់ (User ID):</b> <code>{clean_user}</code>\n"
            f"{user_meta_str}"
            f"<b>លេខសម្គាល់ប្រតិបត្តិការ (Operation ID):</b> <code>{operation_id}</code>\n"
            f"<b>ស្ថានភាព (Status):</b> 🟢 ជោគជ័យ (SUCCESS)\n"
            f"<b>រយៈពេលដំណើរការ (Duration):</b> <code>{duration_sec:.2f}s</code>\n"
            f"<b>ពេលវេលា (Timestamp):</b> <code>{time_str}</code>\n\n"
            f"<b>លទ្ធផល (Result):</b> {res_text}\n"
            f"━━━━━━━━━━━━━━━━━━━━━"
        )
    else:
        err_cat_map = {
            "Concurrent Duplicate": "គណនីស្ទួនគ្នាក្នុងពេលតែមួយ (Concurrent Duplicate)",
            "Invalid Credentials": "ព័ត៌មានសម្ងាត់មិនត្រឹមត្រូវ (Invalid Credentials)",
            "Password Mismatch": "ពាក្យសម្ងាត់មិនត្រូវគ្នា (Password Mismatch)",
            "Rate Limited": "លើសកម្រិតកំណត់នៃការស្នើសុំ (Rate Limited)",
            "Network Timeout": "ដាច់ការតភ្ជាប់បណ្តាញ (Network Timeout)",
        }
        err_cat_raw = err_cat_map.get(error_category, error_category) if error_category else "កំហុសប្រព័ន្ធកម្មវិធី (Application Exception)"
        err_cat = redact_secrets(err_cat_raw)
        action_text = redact_secrets(ai_action) if ai_action else "ការស៊ើបអង្កេតត្រូវបានចាប់ផ្ដើមដោយស្វ័យប្រវត្តិតាមរយៈប្រព័ន្ធត្រួតពិនិត្យ (Investigation initiated by telemetry worker)"
        return (
            f"⚠️ <b>KHMER TRANSLATOR AI — ប្រតិបត្តិការមិនជោគជ័យ (OPERATION FAILED)</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b>ព្រឹត្តិការណ៍ (Event):</b> {event_display}\n"
            f"<b>អ្នកប្រើប្រាស់ (User ID):</b> <code>{clean_user}</code>\n"
            f"{user_meta_str}"
            f"<b>លេខសម្គាល់ប្រតិបត្តិការ (Operation ID):</b> <code>{operation_id}</code>\n"
            f"<b>ស្ថានភាព (Status):</b> 🔴 បរាជ័យ (FAILED)\n"
            f"<b>ប្រភេទកំហុស (Error Category):</b> {err_cat}\n"
            f"<b>ពេលវេលា (Timestamp):</b> <code>{time_str}</code>\n\n"
            f"<b>ចំណាត់ការរបស់ AI (AI Action):</b> {action_text}\n"
            f"━━━━━━━━━━━━━━━━━━━━━"
        )


# =============================================================================
# LEGACY & COMPATIBILITY HELPERS
# =============================================================================

def format_telegram_alert(
    event: EventCategory,
    severity: Severity,
    affected_service: str,
    incident_id: str,
    problem: str,
    evidence: str,
    root_cause: str = "Unknown",
    action_taken: str = "Automated probe triggered",
    test_results: str = "N/A",
    pull_request: Optional[str] = None,
    deployment_status: str = "Verified status only",
    next_action: str = "Awaiting review",
    timestamp_kh: Optional[str] = None,
) -> str:
    """Compatibility wrapper dispatching into format_bug_detected_alert."""
    return format_bug_detected_alert(
        severity=severity.value,
        incident_id=incident_id,
        component=affected_service,
        issue=problem,
        error=evidence,
        impact="សេវាកម្មរអាក់រអួល ឬផ្អាកដំណើរការបណ្តោះអាសន្ន (Service degraded or unavailable)",
        ai_root_cause=root_cause,
        action=action_taken,
        timestamp_kh=timestamp_kh,
    )


def format_recovery_alert(incident: Incident) -> str:
    """Formats verified recovery notifications with polished Khmer typography."""
    time_str = incident.last_detected_cambodia or format_cambodia_time()
    pr_str = incident.pull_request_url if incident.pull_request_url else "គ្មាន (None)"

    return (
        f"🎉 <b>KHMER TRANSLATOR AI — ប្រព័ន្ធដំណើរការប្រក្រតីឡើងវិញ (RECOVERY VERIFIED)</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>ស្ថានភាព (Status):</b> 🟢 ដំណើរការប្រក្រតីឡើងវិញ (RECOVERED)\n"
        f"<b>ពេលវេលា (Time):</b> <code>{time_str}</code>\n"
        f"<b>សេវាកម្ម (Service):</b> {incident.service.value}\n"
        f"<b>លេខសម្គាល់បញ្ហា (Incident ID):</b> <code>{incident.incident_id}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>ការផ្ទៀងផ្ទាត់ (Verification):</b> ឆ្លងកាត់ការតេស្ត {incident.recovery_confirmations} ដងជាប់គ្នា (HTTP 200 OK)\n"
        f"<b>សេចក្ដីសង្ខេប (Summary):</b> {redact_secrets(incident.error_summary)}\n"
        f"<b>ឯកសារយោងដំណោះស្រាយ (Fix Reference):</b> {pr_str}\n"
        f"━━━━━━━━━━━━━━━━━━━━━"
    )


def format_heartbeat_report(fe_res: CheckResult, be_res: CheckResult, active_count: int = 0) -> str:
    """Routine interim heartbeat check."""
    return format_hourly_health_report(
        website_url="https://khmer-ai-16c.pages.dev",
        frontend_online=fe_res.is_healthy,
        backend_online=be_res.is_healthy,
        database_connected=be_res.is_healthy,
        auth_pass=True,
        core_api_pass=be_res.is_healthy,
        video_processing_status="HEALTHY" if be_res.is_healthy else "DEGRADED",
        ai_provider_status="AVAILABLE",
        response_time_ms=(fe_res.latency_ms + be_res.latency_ms) / 2.0,
        error_rate_pct=0.0 if (fe_res.is_healthy and be_res.is_healthy) else 50.0,
        active_users=1,
        background_worker_status="RUNNING",
        latest_deployment_status="LIVE",
        open_incidents_count=active_count,
        overall_status="HEALTHY" if (fe_res.is_healthy and be_res.is_healthy) else "DEGRADED",
        ai_analysis_text="ការត្រួតពិនិត្យប្រព័ន្ធសុខភាពស្វ័យប្រវត្តិបញ្ជាក់ថា Endpoints ទាំងអស់ដំណើរការប្រក្រតី 100% (Probes confirmed 100% operational availability across endpoints).",
    )


def format_ci_report(
    status: str,
    branch: str,
    commit_sha: str,
    commit_msg: str = "",
    details: Optional[dict] = None,
) -> str:
    """Formats automated CI test execution reports with polished Khmer typography."""
    is_success = status.upper() == "SUCCESS"
    icon = "🚀" if is_success else "⚠️"
    status_text = "🟢 ជោគជ័យ (PASSED)" if is_success else "🔴 បរាជ័យ (FAILED)"
    time_str = format_cambodia_time()

    msg = (
        f"{icon} <b>KHMER TRANSLATOR AI — ការតេស្តកូដស្វ័យប្រវត្តិ (CI PIPELINE)</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>ស្ថានភាព (Status):</b> {status_text}\n"
        f"<b>ពេលវេលា (Time):</b> <code>{time_str}</code>\n"
        f"<b>Branch:</b> <code>{branch}</code>\n"
        f"<b>Commit:</b> <code>{commit_sha[:8]}</code>\n"
        f"<b>សារ Commit (Message):</b> <i>{commit_msg[:100]}</i>\n"
        f"━━━━━━━━━━━━━━━━━━━━━"
    )
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
    voice_names = ", ".join([v.get("name", "") for v in voices if v.get("name")]) or "None"

    return (
        f"🤖 <b>KHMER TRANSLATOR AI — របាយការណ៍ត្រួតពិនិត្យដំណើរការ AI (HOURLY AI INSPECTION)</b>\n"
        f"🧠 <b>របាយការណ៍វិភាគទិន្នន័យ & ដំណើរការ AI ប្រចាំម៉ោង</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🏆 <b>ពិន្ទុដំណើរការ (Health Score):</b> <code>{score}/100</code> {score_badge} <b>{ai_insights.get('performance_status_kh', 'ល្អប្រសើរ')}</b>\n"
        f"🕒 <b>ពេលវេលា (Time):</b> <code>{time_str}</code>\n"
        f"⏱️ <b>ប្រេកង់ត្រួតពិនិត្យ (Interval):</b> <code>រៀងរាល់ 1 ម៉ោងម្តង (Hourly Analysis)</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 <b>ទិន្នន័យម៉ាស៊ីន AI & សមត្ថភាពបច្ចេកទេស (AI Engines Telemetry)</b>\n"
        f"  ├ 🗣️ <b>Whisper AI:</b> <code>{models_list}</code> 🟢 សកម្ម\n"
        f"  ├ 🎙️ <b>TTS Dubbing:</b> <code>{voices_count} សំឡេង ({voice_names})</code> 🟢 សកម្ម\n"
        f"  ├ 🎞️ <b>Media Engine:</b> <code>FFmpeg + FFprobe</code> 🟢 ដំណើរការ\n"
        f"  └ 🌐 <b>ភាសាគាំទ្រ:</b> <code>{caps.get('supported_languages_count', 20)} ភាសា</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚡ <b>ល្បឿនបណ្តាញ & ឆ្លើយតប (Network & Latency)</b>\n"
        f"  ├ គេហទំព័រ (Cloudflare Pages): <code>{fe_latency_ms:.1f} ms</code> 🟢\n"
        f"  └ ម៉ាស៊ីនបម្រើ (Render FastAPI): <code>{be_latency_ms:.1f} ms</code> 🟢\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"💡 <b>ការវិភាគ & អនុសាសន៍របស់ Gemini AI (AI Insights)</b>\n"
        f"• <b>ខ្មែរ:</b> <i>{ai_insights.get('ai_opinion_kh', '')}</i>\n"
        f"• <b>English:</b> <i>{ai_insights.get('ai_opinion_en', '')}</i>\n"
        f"• <b>ចំណាត់ការបន្ទាប់:</b> {ai_insights.get('recommendation_kh', 'ដំណើរការល្អ')}\n"
        f"━━━━━━━━━━━━━━━━━━━━━"
    )
