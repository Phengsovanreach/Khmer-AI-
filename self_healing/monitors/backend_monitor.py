"""
Khmer Translator AI — Render FastAPI Backend Health & Readiness Monitor.
Probes backend health and readiness endpoints with intelligent cold-start tolerance.
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Optional

from ..config import Config, redact_secrets
from ..models import CheckResult, ServiceType


def check_backend_health(
    health_url: Optional[str] = None,
    ready_url: Optional[str] = None,
    timeout: Optional[int] = None,
    allow_cold_start_retry: bool = True,
) -> CheckResult:
    """
    Probes the backend API health and readiness probes:
    1. /api/health (Lightweight liveness: {"status": "ok", "app": "...", "version": "2.0.0"})
    2. /api/ready (Deep readiness: checks ffmpeg, faster_whisper, tts, storage)
    Accounts for Render cold starts (handles initial spin-up latency gracefully).
    """
    target_health = health_url or Config.BACKEND_HEALTH_URL
    target_ready = ready_url or Config.BACKEND_READY_URL
    timeout_sec = timeout or Config.HTTP_TIMEOUT_SECONDS

    headers = {
        "User-Agent": "KhmerTranslatorSelfHealing/2.0 (Autonomous Cloud Monitor)",
        "Accept": "application/json",
    }

    start_time = time.perf_counter()
    req = urllib.request.Request(target_health, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            status_code = resp.status
            raw_body = resp.read(16384).decode("utf-8", errors="ignore")

            try:
                data = json.loads(raw_body)
            except Exception:
                data = {}

            is_ok = status_code == 200 and data.get("status") in ("ok", "ready")
            if is_ok:
                # Optionally probe readiness if primary health check succeeded
                readiness_info = _probe_readiness(target_ready, timeout_sec=15)
                return CheckResult(
                    service=ServiceType.BACKEND,
                    url=target_health,
                    is_healthy=True,
                    status_code=status_code,
                    latency_ms=latency_ms,
                    details={
                        "app": data.get("app"),
                        "version": data.get("version"),
                        "readiness": readiness_info,
                        "server_origin": resp.headers.get("x-render-origin-server"),
                        "cf_ray": resp.headers.get("CF-RAY"),
                    },
                )
            else:
                return CheckResult(
                    service=ServiceType.BACKEND,
                    url=target_health,
                    is_healthy=False,
                    status_code=status_code,
                    latency_ms=latency_ms,
                    error_message=f"Backend health check returned invalid payload: {raw_body[:200]}",
                )

    except (urllib.error.HTTPError, urllib.error.URLError) as exc:
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        code = getattr(exc, "code", None)
        reason = getattr(exc, "reason", str(exc))

        # Cold-Start Detection: If Render is spinning up (502/503/504 or timeout > 25s), perform a retry
        if allow_cold_start_retry and (code in (502, 503, 504) or "timed out" in str(reason).lower()):
            time.sleep(5)  # brief grace period for container initialization
            retry_result = check_backend_health(
                health_url=target_health,
                ready_url=target_ready,
                timeout=Config.COLD_START_TIMEOUT_SECONDS,
                allow_cold_start_retry=False,
            )
            if retry_result.is_healthy:
                retry_result.details["cold_start_recovered"] = True
                return retry_result

        err_msg = f"HTTP {code}: {reason}" if code else f"Connection error: {reason}"
        return CheckResult(
            service=ServiceType.BACKEND,
            url=target_health,
            is_healthy=False,
            status_code=code,
            latency_ms=latency_ms,
            error_message=redact_secrets(err_msg),
        )

    except Exception as exc:
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return CheckResult(
            service=ServiceType.BACKEND,
            url=target_health,
            is_healthy=False,
            status_code=None,
            latency_ms=latency_ms,
            error_message=redact_secrets(f"Unexpected backend check error: {exc}"),
        )


def _probe_readiness(ready_url: str, timeout_sec: int = 15) -> dict:
    """Helper to query /api/ready for deep subsystem checks."""
    try:
        req = urllib.request.Request(
            ready_url,
            headers={"User-Agent": "KhmerTranslatorSelfHealing/2.0", "Accept": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8", errors="ignore"))
                return {
                    "status": data.get("status"),
                    "ffmpeg": data.get("ffmpeg"),
                    "faster_whisper": data.get("faster_whisper"),
                    "tts": data.get("tts"),
                    "storage_writable": data.get("storage_writable"),
                }
    except Exception as exc:
        return {"probe_error": redact_secrets(str(exc))}
    return {}
