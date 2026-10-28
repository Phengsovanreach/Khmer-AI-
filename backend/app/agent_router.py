"""
Khmer Translator AI — Floating AI Agent & Interactive Bug Reporting API Router.
Handles contextual FAQ answering, user bug submissions, incident record tracking,
and automated escalation to Telegram & ChatGPT Crosswalk execution queue.
"""
from __future__ import annotations

import json
import logging
import os
import re
import secrets
import threading
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

try:
    from fastapi import APIRouter, HTTPException, Request, Response, status
except ImportError:
    class APIRouter:
        def __init__(self, *args, **kwargs):
            self.routes = []
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
            super().__init__(detail)
            self.status_code = status_code
            self.detail = detail

    class Request:
        pass

    class Response:
        pass

    class status:
        HTTP_400_BAD_REQUEST = 400
        HTTP_404_NOT_FOUND = 404
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
def report_bug(req: BugReportRequest, request: Request):
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

    # 2. Dispatch Telegram alert & Crosswalk relay (non-blocking in background thread)
    def _dispatch_telemetry():
        if os.getenv("TESTING") == "1":
            return
        try:
            from self_healing.notifications import TelegramNotifier
            from self_healing.models import format_cambodia_time

            notifier = TelegramNotifier()
            if notifier.is_configured:
                err_block = f"\n<b>សារកំហុស (Error Log):</b>\n<code>{clean_error[:350]}</code>" if clean_error else ""
                msg = (
                    f"🐞 <b>KHMER TRANSLATOR AI — របាយការណ៍បញ្ហាពីអ្នកប្រើប្រាស់ (USER BUG REPORT)</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                    f"<b>លេខសម្គាល់បញ្ហា (Incident ID):</b> <code>{incident_id}</code>\n"
                    f"<b>កម្រិតធ្ងន់ធ្ងរ (Severity):</b> {req.severity.upper()}\n"
                    f"<b>ទំព័រជួបបញ្ហា (Page):</b> {clean_url}\n"
                    f"<b>ការពិពណ៌នាអំពីបញ្ហា (Description):</b>\n"
                    f"<i>{clean_desc}</i>{err_block}\n\n"
                    f"<b>ស្ថានភាព (Status):</b> 🟡 បានទទួល (RECEIVED — រង់ចាំការវិភាគស្វ័យប្រវត្តិ)\n"
                    f"<b>ពេលវេលា (Time):</b> <code>{format_cambodia_time()}</code>\n"
                    f"━━━━━━━━━━━━━━━━━━━━━"
                )
                notifier.send_message(msg)
        except Exception as exc:
            logger.warning("Telegram notification failed for bug report: %s", exc)

        try:
            import urllib.request
            from self_healing.config import Config
            cw_key = Config.CROSSWALK_KEY if hasattr(Config, "CROSSWALK_KEY") else None
            if not cw_key:
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

    threading.Thread(target=_dispatch_telemetry, daemon=True).start()

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

            res_notes = None
            if record.diagnostics_json:
                try:
                    diag = json.loads(record.diagnostics_json)
                    res_notes = diag.get("resolution_notes")
                except Exception:
                    pass

            return BugStatusResponse(
                incident_id=record.incident_id,
                status=record.status,
                severity=record.severity,
                created_at=record.first_detected_utc.isoformat() if record.first_detected_utc else "",
                summary=record.error_summary,
                resolution_notes=res_notes,
            )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error retrieving bug status: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving bug status / មិនអាចទាញយកព័ត៌មានបានទេ",
        )


# =============================================================================
# KHMER AI AGENT "ASK" MODE (KNOWLEDGE BASE)
# =============================================================================

KHMER_AGENT_KB = [
    {
        "keywords": ["សំឡេង", "dubbing", "voice", "ពិសិដ្ឋ", "ស្រីមុំ", "tts", "edge"],
        "answer": "Khmer Translator គាំទ្រសំឡេងខ្មែរធម្មជាតិកម្រិតខ្ពស់ចំនួន ២ តាមរយៈ Microsoft Edge-TTS:\n1. **កញ្ញា ស្រីមុំ (km-KH-SreymomNeural)** — សំឡេងស្រី ពិរោះរណ្តំ និងច្បាស់ល្អ។\n2. **លោក ពិសិដ្ឋ (km-KH-PisethNeural)** — សំឡេងប្រុស មានអំណាច និងច្បាស់លាស់។\nលោកអ្នកអាចជ្រើសរើសសំឡេងក្នុងផ្ទាំង Dubbing Studio បានភ្លាមៗ!",
        "suggestions": [
            "តើធ្វើដូចម្តេចដើម្បីកំណត់ល្បឿនសំឡេង?",
            "តើប្រព័ន្ធនេះឥតគិតថ្លៃពិតមែនទេ?",
        ],
    },
    {
        "keywords": ["ឥតគិតថ្លៃ", "លុយ", "free", "tier", "ចំណាយ", "ថ្លៃ", "cost"],
        "answer": "Khmer Translator ដំណើរការលើម៉ូដែល **100% Free & Open-Source Tier** ដោយមិនចាំបាច់មាន OpenAI Key ឬ Paid API ឡើយ! រាល់មុខងារបម្លែងសំឡេង Faster-Whisper, ការបកប្រែ, និងការបញ្ចូលសំឡេង Edge-TTS គឺឥតគិតថ្លៃជាអចិន្ត្រៃយ៍។",
        "suggestions": [
            "តើអាចបកប្រែវីដេអូបានកម្រិតណា?",
            "តើមានសំឡេងភាសាខ្មែរអ្វីខ្លះ?",
        ],
    },
    {
        "keywords": ["វីដេអូ", "upload", "video", "ទំហំ", "size", "mp4", "render"],
        "answer": "លោកអ្នកអាច Upload ឯកសារវីដេអូ (MP4, MKV, MOV, WebM) ឬអូឌីយ៉ូ (MP3, WAV, M4A) ដោយផ្ទាល់។ ប្រព័ន្ធមានបច្ចេកវិទ្យា Chunked Resumable Upload ជួយការពារការដាច់កណ្តាលទីពេលអ៊ីនធឺណិតខ្សោយ។",
        "suggestions": [
            "របៀបប្រើប្រាស់ Subtitle Editor Pro",
            "តើអាច Export ជាទម្រង់អ្វីខ្លះ?",
        ],
    },
    {
        "keywords": ["export", "ទាញយក", "srt", "vtt", "txt", "ទម្រង់"],
        "answer": "ក្រោយពេលបកប្រែរួច លោកអ្នកអាច Export បាន ៤ ទម្រង់យ៉ាងងាយស្រួល:\n1. វីដេអូ Dubbed រួចរាល់\n2. ឯកសារ Subtitle SRT (ភាសាខ្មែរ ឬភាសាដើម)\n3. ឯកសារ VTT\n4. អត្ថបទសុទ្ធ TXT ពេញលេញ។",
        "suggestions": [
            "តើធ្វើដូចម្តេចដើម្បីកែសម្រួល Subtitle?",
            "តើមានវចនានុក្រមកែពាក្យខុសទេ?",
        ],
    },
    {
        "keywords": ["វចនានុក្រម", "dictionary", "កែពាក្យ", "proofreading", "អក្ខរាវិរុទ្ធ"],
        "answer": "ប្រព័ន្ធមាន **Khmer Proofreading Studio** និង **Pronunciation Dictionary Studio** ដែលអនុញ្ញាតឱ្យលោកអ្នកកំណត់ពាក្យបច្ចេកទេស និងកែអក្ខរាវិរុទ្ធភាសាខ្មែរឱ្យត្រឹមត្រូវ 100% មុនពេលបង្កើតសំឡេង Dubbing។",
        "suggestions": [
            "តើមានសំឡេងភាសាខ្មែរអ្វីខ្លះ?",
            "របៀប Upload វីដេអូ",
        ],
    },
]

DEFAULT_AGENT_ANSWER = (
    "សូមអរគុណសម្រាប់សំណួរ! ខ្ញុំជា Khmer AI Agent ជំនួយការរបស់លោកអ្នក។ "
    "លោកអ្នកអាចសាកសួរខ្ញុំអំពី៖ ការបញ្ចូលសំឡេង Dubbing (សំឡេងស្រីមុំ និងពិសិដ្ឋ), "
    "ការ Upload វីដេអូ, ការកែសម្រួល Subtitles SRT, ឬការប្រើប្រាស់ 100% Free Tier របស់កម្មវិធី។"
)

DEFAULT_SUGGESTIONS = [
    "តើមានសំឡេងភាសាខ្មែរអ្វីខ្លះ?",
    "តើប្រព័ន្ធនេះឥតគិតថ្លៃពិតមែនទេ?",
    "តើអាច Export ជាទម្រង់អ្វីខ្លះ?",
]


@router.post("/agent/ask", response_model=AskAgentResponse)
def ask_agent(req: AskAgentRequest):
    """
    Answers user questions regarding Khmer Translator AI features, dubbing voices,
    and workflows using an embedded grounded knowledge base.
    """
    q_lower = req.question.strip().lower()

    matched_entry = None
    max_matches = 0

    for item in KHMER_AGENT_KB:
        matches = sum(1 for kw in item["keywords"] if kw in q_lower)
        if matches > max_matches:
            max_matches = matches
            matched_entry = item

    if matched_entry and max_matches > 0:
        return AskAgentResponse(
            answer=matched_entry["answer"],
            suggestions=matched_entry["suggestions"],
            source="khmer_translator_knowledge_base",
        )

    return AskAgentResponse(
        answer=DEFAULT_AGENT_ANSWER,
        suggestions=DEFAULT_SUGGESTIONS,
        source="khmer_translator_fallback",
    )
