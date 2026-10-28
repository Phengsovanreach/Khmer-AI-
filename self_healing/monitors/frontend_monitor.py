"""
Khmer Translator AI — Cloudflare Pages Frontend Health Monitor.
Performs non-intrusive synthetic health probes against the production web frontend.
"""
from __future__ import annotations

import time
import urllib.error
import urllib.request
from typing import Optional

from ..config import Config, redact_secrets
from ..models import CheckResult, ServiceType


def check_frontend_health(url: Optional[str] = None, timeout: Optional[int] = None) -> CheckResult:
    """
    Probes the frontend public deployment URL and validates:
    1. HTTP status code is 200.
    2. Response Content-Type is HTML.
    3. HTML payload contains valid application root markup (#root or Khmer Translator branding).
    """
    target_url = url or Config.FRONTEND_URL
    timeout_sec = timeout or Config.HTTP_TIMEOUT_SECONDS
    start_time = time.perf_counter()

    headers = {
        "User-Agent": "KhmerTranslatorSelfHealing/2.0 (Autonomous Cloud Monitor)",
        "Accept": "text/html,application/xhtml+xml",
    }

    req = urllib.request.Request(target_url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            status_code = resp.status
            content_type = resp.headers.get("Content-Type", "").lower()
            body = resp.read(65536).decode("utf-8", errors="ignore")

            # Validation checks
            is_html = "text/html" in content_type
            has_app_root = ("id=\"root\"" in body) or ("id='root'" in body) or ("Khmer Translator" in body)
            is_cloudflare = "cloudflare" in resp.headers.get("Server", "").lower() or "cf-ray" in resp.headers

            if status_code == 200 and is_html and has_app_root:
                return CheckResult(
                    service=ServiceType.FRONTEND,
                    url=target_url,
                    is_healthy=True,
                    status_code=status_code,
                    latency_ms=latency_ms,
                    details={
                        "server": resp.headers.get("Server", "Unknown"),
                        "cf_ray": resp.headers.get("CF-RAY"),
                        "content_length": len(body),
                        "verified_dom": True,
                    },
                )
            else:
                err_reasons = []
                if status_code != 200:
                    err_reasons.append(f"HTTP status {status_code} != 200")
                if not is_html:
                    err_reasons.append(f"Content-Type '{content_type}' is not HTML")
                if not has_app_root:
                    err_reasons.append("Missing application root DOM or title markup")

                return CheckResult(
                    service=ServiceType.FRONTEND,
                    url=target_url,
                    is_healthy=False,
                    status_code=status_code,
                    latency_ms=latency_ms,
                    error_message=f"Frontend validation failed: {', '.join(err_reasons)}",
                    details={"body_snippet": redact_secrets(body[:500])},
                )

    except urllib.error.HTTPError as exc:
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        err_msg = f"HTTP {exc.code}: {exc.reason}"
        if exc.code in (520, 521, 522, 523, 524):
            err_msg += f" (Cloudflare Edge Error {exc.code})"
        return CheckResult(
            service=ServiceType.FRONTEND,
            url=target_url,
            is_healthy=False,
            status_code=exc.code,
            latency_ms=latency_ms,
            error_message=err_msg,
        )

    except urllib.error.URLError as exc:
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        reason_str = str(exc.reason)
        is_timeout = "timed out" in reason_str.lower()
        err_msg = "Request timed out" if is_timeout else f"Network connection failed: {reason_str}"
        return CheckResult(
            service=ServiceType.FRONTEND,
            url=target_url,
            is_healthy=False,
            status_code=None,
            latency_ms=latency_ms,
            error_message=redact_secrets(err_msg),
        )

    except Exception as exc:
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return CheckResult(
            service=ServiceType.FRONTEND,
            url=target_url,
            is_healthy=False,
            status_code=None,
            latency_ms=latency_ms,
            error_message=redact_secrets(f"Unexpected monitor failure: {exc}"),
        )
