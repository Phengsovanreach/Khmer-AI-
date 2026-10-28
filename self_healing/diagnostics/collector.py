"""
Khmer Translator AI — Incident Diagnostic Evidence Collector.
Gathers runtime diagnostics, HTTP error responses, Git metadata, and sanitizes sensitive data.
"""
from __future__ import annotations

import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any, Optional

from ..config import Config, redact_secrets
from ..models import CheckResult, Incident, format_cambodia_time


class DiagnosticCollector:
    @staticmethod
    def collect_incident_evidence(
        incident: Incident,
        latest_result: Optional[CheckResult] = None,
        extra_logs: Optional[str] = None,
    ) -> dict[str, Any]:
        """Gathers comprehensive, sanitized diagnostic evidence for AI analysis."""
        now_utc = datetime.now(timezone.utc).isoformat()
        now_kh = format_cambodia_time()

        git_info = DiagnosticCollector._get_git_metadata()

        evidence = {
            "incident_id": incident.incident_id,
            "service": incident.service.value,
            "timestamp_utc": now_utc,
            "timestamp_cambodia": now_kh,
            "consecutive_failures": incident.consecutive_failures,
            "error_summary": redact_secrets(incident.error_summary),
            "git_context": git_info,
            "runtime_environment": {
                "python_version": sys.version.split()[0],
                "platform": platform.platform(),
                "node_name": platform.node(),
            },
            "latest_check": latest_result.details if latest_result else {},
            "raw_error": redact_secrets(latest_result.error_message if latest_result else incident.error_summary),
            "extra_logs": redact_secrets(extra_logs) if extra_logs else None,
        }
        return evidence

    @staticmethod
    def _get_git_metadata() -> dict[str, str]:
        """Safely captures current Git HEAD and branch info."""
        meta = {"branch": "unknown", "commit": "unknown", "commit_msg": "unknown"}
        try:
            head_sha = subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=str(Config.BASE_DIR),
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
            meta["commit"] = head_sha[:10]

            branch = subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=str(Config.BASE_DIR),
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
            meta["branch"] = branch

            msg = subprocess.check_output(
                ["git", "log", "-1", "--pretty=%s"],
                cwd=str(Config.BASE_DIR),
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
            meta["commit_msg"] = redact_secrets(msg)
        except Exception:
            pass
        return meta
