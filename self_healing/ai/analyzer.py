"""
Khmer Translator AI — Failure Analyzer Engine.
Orchestrates diagnostic evidence synthesis and structured AI root-cause diagnosis.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Optional

from ..config import Config, redact_secrets
from ..models import DiagnosticReport, Incident, format_cambodia_time
from .base import BaseAIProvider
from .gemini_provider import GeminiProvider
from .openai_provider import OpenAICompatibleProvider

logger = logging.getLogger(__name__)


class FailureAnalyzer:
    def __init__(self, provider: Optional[BaseAIProvider] = None):
        self.provider = provider or self._resolve_provider()

    @staticmethod
    def _resolve_provider() -> Optional[BaseAIProvider]:
        """Auto-resolves the best available AI provider based on environment secrets."""
        pref = Config.AI_PROVIDER
        if pref == "gemini" or (pref == "auto" and Config.GEMINI_API_KEY):
            return GeminiProvider()
        elif pref == "openai" or (pref == "auto" and Config.OPENAI_API_KEY):
            return OpenAICompatibleProvider()
        return None

    def diagnose_incident(self, incident: Incident, evidence: dict[str, Any]) -> DiagnosticReport:
        """
        Performs structured diagnosis of an incident:
        1. Checks whether diagnostic evidence is sufficient.
        2. Queries configured AI provider with strict schema constraints.
        3. Falls back gracefully to heuristic classification if AI is unconfigured.
        """
        now_utc = incident.last_detected_utc
        now_kh = incident.last_detected_cambodia

        # Check evidence sufficiency
        err_text = evidence.get("raw_error") or incident.error_summary or ""
        if not err_text or len(err_text.strip()) < 5:
            return DiagnosticReport(
                incident_id=incident.incident_id,
                detected_at_utc=now_utc,
                detected_at_cambodia=now_kh,
                affected_component=incident.service.value,
                failure_category="INSUFFICIENT_EVIDENCE",
                evidence="Empty or minimal diagnostic payload collected.",
                probable_root_cause="Unknown: Insufficient telemetry data to determine failure source.",
                confidence=0.1,
                proposed_fix="Collect detailed application and reverse-proxy logs before retrying.",
                tests_required=["check_frontend_health", "check_backend_health"],
                safety_risks=["Automated code modification without diagnostic evidence is strictly prohibited."],
                status="INSUFFICIENT_EVIDENCE",
            )

        # Check if AI provider is available
        if not self.provider or not self.provider.is_available():
            logger.info("AI provider is not configured. Falling back to heuristic diagnosis.")
            return self._heuristic_diagnosis(incident, evidence)

        prompt = self._build_prompt(incident, evidence)
        ai_response = self.provider.generate_analysis(prompt)

        if not ai_response:
            return self._heuristic_diagnosis(incident, evidence)

        return DiagnosticReport(
            incident_id=incident.incident_id,
            detected_at_utc=now_utc,
            detected_at_cambodia=now_kh,
            affected_component=incident.service.value,
            failure_category=ai_response.get("failure_category", "APPLICATION_ERROR"),
            evidence=redact_secrets(str(evidence.get("raw_error", ""))),
            probable_root_cause=ai_response.get("probable_root_cause", "Undetermined"),
            confidence=float(ai_response.get("confidence", 0.5)),
            proposed_fix=ai_response.get("proposed_fix", "Manual investigation required."),
            tests_required=ai_response.get("tests_required", ["backend-tests", "frontend-build"]),
            safety_risks=ai_response.get("safety_risks", ["Inspect generated changes thoroughly."]),
            status="AI_DIAGNOSED",
        )

    def _heuristic_diagnosis(self, incident: Incident, evidence: dict[str, Any]) -> DiagnosticReport:
        """Deterministic fallback diagnosis when AI API credentials are not set."""
        err_msg = str(evidence.get("raw_error", "")).lower()
        now_utc = incident.last_detected_utc
        now_kh = incident.last_detected_cambodia

        if "timed out" in err_msg or "timeout" in err_msg:
            cat = "TIMEOUT_COLD_START"
            cause = "Application request exceeded timeout threshold (potential Render cold-start or CPU exhaustion)."
            fix = "Verify server process health, review worker concurrency, and adjust wake-up timeouts."
        elif "521" in err_msg or "522" in err_msg or "523" in err_msg or "524" in err_msg:
            cat = "CLOUDFLARE_ORIGIN_DOWN"
            cause = "Cloudflare edge was unable to connect to origin server."
            fix = "Check origin server connectivity, Caddy/Nginx reverse proxy, and DNS routing."
        elif "cors" in err_msg:
            cat = "CORS_MISCONFIGURATION"
            cause = "Cross-Origin Resource Sharing request blocked by backend CORS policy."
            fix = "Verify CORS_ORIGINS environment variable in backend/app/config.py."
        else:
            cat = "GENERIC_HTTP_FAILURE"
            cause = f"Service responded with unexpected error: {evidence.get('raw_error', 'N/A')}"
            fix = "Inspect application logs and restart degraded containers if necessary."

        return DiagnosticReport(
            incident_id=incident.incident_id,
            detected_at_utc=now_utc,
            detected_at_cambodia=now_kh,
            affected_component=incident.service.value,
            failure_category=cat,
            evidence=redact_secrets(str(evidence.get("raw_error", ""))),
            probable_root_cause=cause,
            confidence=0.75,
            proposed_fix=fix,
            tests_required=["backend-tests", "frontend-build"],
            safety_risks=["No AI API key present; diagnosis performed via deterministic heuristics."],
            status="AI_ANALYSIS_NOT_CONFIGURED",
        )

    def _build_prompt(self, incident: Incident, evidence: dict[str, Any]) -> str:
        return f"""You are a Principal SRE diagnosing a failure in Khmer Translator AI (FastAPI backend on Render, React Vite frontend on Cloudflare Pages).
Analyze the following incident telemetry and output ONLY a valid JSON object matching this schema:
{{
  "failure_category": "string (e.g. TIMEOUT, 5XX_ERROR, DEPENDENCY_MISSING, DOM_RENDER_ERROR)",
  "probable_root_cause": "string explaining the likely cause",
  "confidence": 0.0 to 1.0,
  "proposed_fix": "minimal actionable recommendation",
  "tests_required": ["list", "of", "required", "tests"],
  "safety_risks": ["list", "of", "risks"]
}}

INCIDENT DATA:
Service: {incident.service.value}
Incident ID: {incident.incident_id}
Consecutive Failures: {incident.consecutive_failures}
Raw Error: {evidence.get('raw_error')}
Latest Check Details: {json.dumps(evidence.get('latest_check', {}))}
Git Head: {evidence.get('git_context', {}).get('commit')}
"""
