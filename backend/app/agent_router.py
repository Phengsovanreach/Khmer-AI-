"""
Khmer Translator AI — Floating AI Agent & Bug Reporting Router.
Provides endpoints for:
1. ASK Mode: Interactive app Q&A grounded in Khmer Translator AI capabilities.
2. Bug Mode: In-app bug reporting with database persistence and Telegram dispatch.
3. Bug Status: Incident status tracking for reported bugs.
"""
from __future__ import annotations

import json
import logging
import secrets
import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Optional

try:
    from fastapi import APIRouter, HTTPException, Request, status
except ImportError:
    class APIRouter:
        def __init__(self, *args, **kwargs):
            pass
        def post(self, *args, **kwargs):
            def decorator(f):
                return f
            return decorator
        def get(self, *args, **kwargs):
            def decorator(f):
                return f
            return decorator

    class HTTPException(Exception):
        def __init__(self, status_code: int, detail: str = ""):
            self.status_code = status_code
            self.detail = detail
            super().__init__(f"HTTP {status_code}: {detail}")

    class Request:
        pass

    class status:
        HTTP_404_NOT_FOUND = 404
        HTTP_422_UNPROCESSABLE_ENTITY = 422
        HTTP_429_TOO_MANY_REQUESTS = 429
        HTTP_500_INTERNAL_SERVER_ERROR = 500

from .db.database import db_session_scope
from .db.models import IncidentRecord
from .schemas import (
    AskAgentRequest,
    AskAgentResponse,
    BugReportRequest,
    BugReportResponse,
    BugStatusResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Agent & Bug Reporting"])

# Rate limit tracking: IP -> list of timestamps
_BUG_RATE_LIMITS: dict[str, list[float]] = defaultdict(list)
_MAX_BUG_REPORTS_PER_5MIN = 5


def _is_rate_limited(ip: str) -> bool:
    now = time.time()
    cutoff = now - 300  # 5 minutes window
    _BUG_RATE_LIMITS[ip] = [t for t in _BUG_RATE_LIMITS[ip] if t > cutoff]
    if len(_BUG_RATE_LIMITS[ip]) >= _MAX_BUG_REPORTS_PER_5MIN:
        return True
    _BUG_RATE_LIMITS[ip].append(now)
    return False


def _redact(text: str) -> str:
    try:
        from self_healing.config import redact_secrets
        return redact_secrets(text)
    except Exception:
        return text


# =============================================================================
# BUG REPORTING ENDPOINTS
# =============================================================================

@router.post("/bugs/report", response_model=BugReportResponse)
async def report_bug(req: BugReportRequest, request: Request):
    """
    Submits a user-reported bug or exception directly to the engineering telemetry pipeline.
    Persists report in database and dispatches a sanitized alert to the project Telegram bot.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"

    if _is_rate_limited(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many bug reports submitted. Please wait a few minutes / សូមរង់ចាំបន្តិចសិនមុននឹងផ្ញើរបាយការណ៍ម្តងទៀត",
        )

    clean_desc = _redact(req.description.strip())
    clean_error = _redact(req.error_text.strip()) if req.error_text else None
    clean_url = req.page_url.strip() if req.page_url else "/"
    incident_id = f"BUG-{secrets.token_hex(4).upper()}"
    now_utc = datetime.now(timezone.utc)

    # 1. Persist to database
    try:
        with db_session_scope() as session:
            record = IncidentRecord(
                incident_id=incident_id,
                service="USER_REPORT",
                status="RECEIVED",
                severity=req.severity.upper(),
                consecutive_failures=1,
                error_summary=clean_desc[:500],
                first_detected_utc=now_utc,
                last_detected_utc=now_utc,
                diagnostics_json=json.dumps({
                    "page_url": clean_url,
                    "error_text": clean_error,
                    "user_contact": req.user_contact,
                    "source": "floating_agent_widget",
                }),
                repair_attempts=0,
                recovery_confirmations=0,
            )
            session.add(record)
    except Exception as exc:
        logger.error("Failed to save user bug report to database: %s", exc)

    # 2. Dispatch Telegram alert
    try:
        from self_healing.notifications import TelegramNotifier
        from self_healing.models import format_cambodia_time

        notifier = TelegramNotifier()
        if notifier.is_configured:
            err_block = f"\n<b>Error Log:</b>\n<code>{clean_error[:350]}</code>" if clean_error else ""
            msg = (
                f"🐞 <b>KHMER TRANSLATOR AI — USER BUG REPORT</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"<b>Incident ID:</b> <code>{incident_id}</code>\n"
                f"<b>Severity:</b> {req.severity.upper()}\n"
                f"<b>Page:</b> {clean_url}\n"
                f"<b>Description:</b>\n"
                f"<i>{clean_desc}</i>{err_block}\n\n"
                f"<b>Status:</b> 🟡 RECEIVED (Queued for Autonomous Analysis)\n"
                f"<b>Time:</b> <code>{format_cambodia_time()}</code>\n"
                f"━━━━━━━━━━━━━━━━━━━━━"
            )
            notifier.send_message(msg)
    except Exception as exc:
        logger.warning("Telegram notification failed for bug report: %s", exc)

    # 3. Relay to Crosswalk (best effort)
    try:
        import urllib.request
        from self_healing.config import Config
        # If Crosswalk key is present in environment
        cw_key = Config.CROSSWALK_KEY if hasattr(Config, "CROSSWALK_KEY") else None
        if not cw_key:
            import os
            cw_key = os.getenv("CROSSWALK_KEY")
        if cw_key:
            payload = {
                "crosswalk": "chatgptantigravity2",
                "brief": f"User Bug Report: {incident_id} — {clean_desc[:50]}",
                "body": f"New user bug report received via floating widget:\n\nIncident ID: {incident_id}\nSeverity: {req.severity}\nPage: {clean_url}\nDescription: {clean_desc}",
            }
            req_cw = urllib.request.Request(
                "https://mcp.crosswalk.to/v1/post",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Authorization": f"Bearer {cw_key}", "Content-Type": "application/json"},
            )
            urllib.request.urlopen(req_cw, timeout=5)
    except Exception:
        pass

    return BugReportResponse(
        success=True,
        incident_id=incident_id,
        status="RECEIVED",
        message="របាយការណ៍ត្រូវបានបញ្ជូនទៅកាន់ក្រុមបច្ចេកទេសដោយជោគជ័យ។ លេខយោង៖ " + incident_id,
        created_at=now_utc.isoformat(),
    )


@router.get("/bugs/status/{incident_id}", response_model=BugStatusResponse)
def get_bug_status(incident_id: str):
    """Retrieves current status of a user-submitted bug report."""
    clean_id = incident_id.strip()
    try:
        with db_session_scope() as session:
            record = session.query(IncidentRecord).filter(IncidentRecord.incident_id == clean_id).first()
            if not record:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Bug report '{clean_id}' not found / រកមិនឃើញរបាយការណ៍នេះទេ",
                )
            return BugStatusResponse(
                incident_id=record.incident_id,
                status=record.status,
                severity=record.severity,
                summary=record.error_summary,
                created_at=record.first_detected_utc.isoformat() if record.first_detected_utc else "",
            )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error looking up bug report %s: %s", clean_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database lookup error",
        )


# =============================================================================
# ASK MODE ENDPOINT
# =============================================================================

# Comprehensive Knowledge Base grounded strictly in Khmer Translator AI
_KHMER_KNOWLEDGE_BASE = [
    {
        "keywords": ["dubbing", "សំឡេង", "voice", "voiceover", "បញ្ចូលសំឡេង"],
        "answer": (
            "ប្រព័ន្ធ Khmer Translator AI ប្រើប្រាស់បច្ចេកវិទ្យា Microsoft Edge Neural TTS សម្រាប់សំយោគសំឡេងជាភាសាខ្មែរធម្មជាតិ៖\n\n"
            "• **km-KH-SreymomNeural**: សំឡេងស្រី សំឡេងស្រទន់ ច្បាស់ និងសមរម្យសម្រាប់ព័ត៌មាន ឬឯកសារ\n"
            "• **km-KH-PisethNeural**: សំឡេងប្រុស ច្បាស់ រឹងមាំ និងមានថាមពល\n\n"
            "អ្នកអាចកំណត់ល្បឿន (Rate) និងកម្រិតសំឡេង (Pitch) ព្រមទាំងប្រើមុខងារ Audio Ducking ដើម្បីកាត់បន្ថយសំឡេងដើមនៃវីដេអូដោយស្វ័យប្រវត្តិ។"
        ),
        "suggestions": ["តើមានសំឡេងភាសាខ្មែរប៉ុន្មាន?", "តើ Audio Ducking ដំណើរការដូចម្តេច?", "តើភាសាអ្វីខ្លះត្រូវបានគាំទ្រ?"],
    },
    {
        "keywords": ["ភាសា", "language", "languages", "គាំទ្រ"],
        "answer": (
            "Khmer Translator AI គាំទ្រការបកប្រែពហុភាសាជាង ៥០ ភាសាជុំវិញពិភពលោក មកកាន់ភាសាខ្មែរ ឬពីខ្មែរទៅភាសាដទៃ រួមមាន៖\n\n"
            "• អង់គ្លេស (English), ចិន (Chinese), ជប៉ុន (Japanese), កូរ៉េ (Korean)\n"
            "• បារាំង (French), ថៃ (Thai), វៀតណាម (Vietnamese)\n\n"
            "ការបកប្រែប្រើប្រាស់ម៉ូដែល AI កម្រិតខ្ពស់ដែលយល់ពីវេយ្យាករណ៍ និងបរិបទនៃភាសាខ្មែរយ៉ាងច្បាស់លាស់។"
        ),
        "suggestions": ["តើបកប្រែពីវីដេអូ YouTube បានទេ?", "តើការបកប្រែចំណាយពេលប៉ុន្មាន?", "តើទាញយកឯកសារ Subtitle យ៉ាងដូចម្តេច?"],
    },
    {
        "keywords": ["free", "ថ្លៃ", "លុយ", "price", "pricing", "cost", "គិតថ្លៃ"],
        "answer": (
            "Khmer Translator AI ដំណើរការលើហេដ្ឋារចនាសម្ព័ន្ធ **ឥតគិតថ្លៃ ១០០% អចិន្ត្រៃយ៍ ($0.00/ខែ)** ដោយមិនតម្រូវឱ្យមានកាតធនាគារ (Credit Card) ឡើយ៖\n\n"
            "• គេហទំព័រ Frontend ដំណើរការលើ **Cloudflare Pages** (Free Tier)\n"
            "• ម៉ាស៊ីនបម្រើ Backend ដំណើរការលើ **Render Web Service** (Free Tier)\n"
            "• មូលដ្ឋានទិន្នន័យ Postgres ដំណើរការលើ **Neon Serverless PostgreSQL** (Free Tier)\n\n"
            "អ្នកអាចប្រើប្រាស់មុខងារទាំងអស់ដោយឥតគិតថ្លៃ!"
        ),
        "suggestions": ["តើធ្វើដូចម្តេចដើម្បីចុះឈ្មោះ?", "តើទិន្នន័យមានសុវត្ថិភាពឬទេ?", "តើមានដែនកំណត់ទំហំវីដេអូទេ?"],
    },
    {
        "keywords": ["វចនានុក្រម", "dictionary", "បញ្ចេញសំឡេង", "pronunciation", "កែ"],
        "answer": (
            "Khmer Translator AI មានមុខងារ **វចនានុក្រមបញ្ចេញសំឡេងផ្ទាល់ខ្លួន (Pronunciation Dictionary Studio)**៖\n\n"
            "• អនុញ្ញាតឱ្យអ្នកកំណត់ពាក្យបច្ចេកទេស ឈ្មោះមនុស្ស ឬពាក្យកម្ចីភាសាបរទេស\n"
            "• កំណត់របៀបអានជាភាសាខ្មែរឱ្យបានត្រឹមត្រូវ ១០០% មុនពេលសំយោគសំឡេង Dubbing\n"
            "• ពាក្យក្នុងវចនានុក្រមនឹងត្រូវយកទៅអនុវត្តលើរាល់គម្រោងរបស់អ្នកដោយស្វ័យប្រវត្តិ។"
        ),
        "suggestions": ["តើបញ្ចូលពាក្យថ្មីក្នុងវចនានុក្រមយ៉ាងដូចម្តេច?", "តើ export subtitle ជា SRT បានទេ?", "របៀបប្តូរសំឡេងតួអង្គ"],
    },
    {
        "keywords": ["export", "subtitle", "srt", "vtt", "ទាញយក", "download"],
        "answer": (
            "បន្ទាប់ពីការបកប្រែ និង Dubbing រួចរាល់ អ្នកអាចទាញយក (Export) បានជាច្រើនទម្រង់៖\n\n"
            "1. **ឯកសារ Subtitle**: ទាញយកជា `.SRT`, `.VTT`, ឬ `.TXT`\n"
            "2. **ឯកសារសំឡេង**: ទាញយកសំឡេង Dubbed Audio Track ជា `.WAV` ឬ `.MP3`\n"
            "3. **វីដេអូសម្រេច**: វីដេអូដែលបានបញ្ចូលសំឡេងខ្មែរ និង Subtitle ជាប់វីដេអូ (Hardcoded Burn-in) ក្នុងកម្រិតច្បាស់ HD។"
        ),
        "suggestions": ["តើកែសម្រួល Subtitle ដោយដៃបានទេ?", "តើធ្វើដូចម្តេចដើម្បីចាប់ផ្តើម?", "តើមាន AI ជំនួយការឆ្លើយតបឬទេ?"],
    },
]


@router.post("/agent/ask", response_model=AskAgentResponse)
async def ask_agent(req: AskAgentRequest):
    """
    Answers user queries about Khmer Translator AI features, capabilities, and guidance.
    Uses Gemini AI if configured, with an accurate, pre-grounded fallback knowledge base.
    """
    q = req.question.strip().lower()

    # Try Gemini AI first if configured
    try:
        from self_healing.ai.gemini_provider import GeminiProvider
        provider = GeminiProvider()
        if provider.is_available():
            system_prompt = (
                "You are the official Khmer Translator AI assistant. Answer user queries in natural, polite Khmer. "
                "The app provides AI speech-to-text with Faster-Whisper, multilingual translation into Khmer, "
                "and Edge TTS Khmer voice dubbing (voices: km-KH-SreymomNeural and km-KH-PisethNeural). "
                "The service runs 100% free permanently ($0.00/month, zero credit card) on Cloudflare Pages, Render, and Neon PostgreSQL. "
                "Keep answers concise, direct, helpful, and formatted with markdown."
            )
            ai_ans = provider.generate_text(f"{system_prompt}\n\nUser Question: {req.question}")
            if ai_ans and len(ai_ans.strip()) > 10:
                return AskAgentResponse(
                    answer=ai_ans.strip(),
                    source="ai",
                    suggestions=[
                        "តើមានសំឡេងភាសាខ្មែរប៉ុន្មាន?",
                        "តើធ្វើដូចម្តេចដើម្បីបញ្ចូលសំឡេង dubbing?",
                        "តើប្រព័ន្ធនេះឥតគិតថ្លៃពិតមែនទេ?",
                    ],
                )
    except Exception as exc:
        logger.debug("Gemini query fallback to knowledge base: %s", exc)

    # Intelligent Knowledge Base Grounding
    for item in _KHMER_KNOWLEDGE_BASE:
        if any(kw in q for kw in item["keywords"]):
            return AskAgentResponse(
                answer=item["answer"],
                source="knowledge_base",
                suggestions=item["suggestions"],
            )

    # Default friendly Khmer response with key features
    default_ans = (
        "សូមស្វាគមន៍មកកាន់ **Khmer Translator AI (ជំនួយការឆ្លាតវៃ)**! 🙏\n\n"
        "ខ្ញុំអាចជួយអ្នកលើបញ្ហា និងមុខងារសំខាន់ៗដូចជា៖\n"
        "• **ការបកប្រែវីដេអូ & សំឡេង**: បំប្លែងសំឡេងនិយាយជាអក្សរ និងបកប្រែមកជាភាសាខ្មែរ\n"
        "• **សំឡេង Dubbing ភាសាខ្មែរ**: ប្រើប្រាស់សំឡេង Sreymom និង Piseth ជាមួយ Audio Ducking\n"
        "• **វចនានុក្រមបញ្ចេញសំឡេង**: កំណត់ពាក្យពិបាកអាន ឬពាក្យបច្ចេកទេសឱ្យអានបានត្រឹមត្រូវ\n"
        "• **ការទាញយក**: Export ជាវីដេអូសម្រេច, MP3 Audio, ឬ Subtitle (SRT/VTT)\n\n"
        "ប្រសិនបើអ្នកជួបបញ្ហាបច្ចេកទេស អ្នកអាចប្តូរទៅកាន់ **Bug Mode (រាយការណ៍បញ្ហា)** ដើម្បីផ្ញើកំហុសទៅកាន់ក្រុមវិស្វករបានភ្លាមៗ!"
    )
    return AskAgentResponse(
        answer=default_ans,
        source="knowledge_base",
        suggestions=[
            "តើធ្វើដូចម្តេចដើម្បីបញ្ចូលសំឡេង dubbing?",
            "តើភាសាអ្វីខ្លះត្រូវបានគាំទ្រ?",
            "តើប្រព័ន្ធនេះឥតគិតថ្លៃពិតមែនទេ?",
        ],
    )
