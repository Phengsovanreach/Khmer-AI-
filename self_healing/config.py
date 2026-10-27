"""
Khmer Translator AI — Self-Healing System Configuration & Security Scrubbing.
Loads settings securely, redacts credentials, and defines operational boundaries.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Optional

# Load local .env if present (safely, without external dotenv dependency)
_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
if _ENV_FILE.exists():
    try:
        for line in _ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip("'\"")
                if k and v:
                    os.environ[k] = v
    except Exception:
        pass


class Config:
    # Service Endpoints
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "https://khmer-ai-16c.pages.dev").rstrip("/")
    BACKEND_HEALTH_URL: str = os.getenv("BACKEND_HEALTH_URL", "https://khmer-ai-1ktp.onrender.com/api/health")
    BACKEND_READY_URL: str = os.getenv("BACKEND_READY_URL", "https://khmer-ai-1ktp.onrender.com/api/ready")

    # Timeouts & Retry Limits
    HTTP_TIMEOUT_SECONDS: int = int(os.getenv("HTTP_TIMEOUT_SECONDS", "30"))
    COLD_START_TIMEOUT_SECONDS: int = int(os.getenv("COLD_START_TIMEOUT_SECONDS", "90"))
    CONFIRMATION_THRESHOLD: int = int(os.getenv("CONFIRMATION_THRESHOLD", "2"))  # 2 consecutive fails
    RECOVERY_THRESHOLD: int = int(os.getenv("RECOVERY_THRESHOLD", "2"))          # 2 consecutive successes
    MAX_REPAIR_ATTEMPTS: int = int(os.getenv("MAX_REPAIR_ATTEMPTS", "2"))
    MAX_DIFF_LINES: int = int(os.getenv("MAX_DIFF_LINES", "150"))

    # GitHub Settings
    GITHUB_TOKEN: Optional[str] = os.getenv("GITHUB_TOKEN")
    GITHUB_REPOSITORY: str = os.getenv("GITHUB_REPOSITORY", "Phengsovanreach/Khmer-AI-")
    PRODUCTION_BRANCH: str = os.getenv("PRODUCTION_BRANCH", "main")
    REPAIR_BRANCH_PREFIX: str = "ai-repair/"

    # Telegram Credentials & Settings
    TELEGRAM_BOT_TOKEN: Optional[str] = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID: Optional[str] = os.getenv("TELEGRAM_CHAT_ID")
    TELEGRAM_API_BASE: str = "https://api.telegram.org"
    ALWAYS_NOTIFY: bool = os.getenv("ALWAYS_NOTIFY", "false").lower() in ("true", "1", "yes")

    # AI Provider Settings
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "auto").lower()  # auto, gemini, openai, mock, none
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    AI_MODEL_NAME: str = os.getenv("AI_MODEL_NAME", "gemini-3.5-flash-lite")

    # Storage Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    STATE_FILE: Path = BASE_DIR / os.getenv("SELF_HEALING_STATE_FILE", "self_healing_state.json")
    AUDIT_LOG_FILE: Path = BASE_DIR / "self_healing_audit.log"

    # Protected paths that automated repairs can NEVER touch
    FORBIDDEN_REPAIR_PATHS: tuple[str, ...] = (
        ".github/workflows",
        "render.yaml",
        "Dockerfile",
        ".env",
        ".env.example",
        ".git",
    )


# Regex patterns for redacting sensitive secrets and non-permitted Thai characters
_THAI_CHAR_PATTERN = re.compile(r"[\u0E00-\u0E7F]+")

_REDACT_PATTERNS = [
    re.compile(r"\b\d{9,10}:[a-zA-Z0-9_-]{35}\b"),              # Telegram bot tokens
    re.compile(r"ghp_[a-zA-Z0-9]{36,255}"),                      # GitHub classic PATs
    re.compile(r"github_pat_[a-zA-Z0-9_]{50,255}"),              # GitHub fine-grained PATs
    re.compile(r"AIza[0-9A-Za-z-_]{35}"),                        # Google API keys
    re.compile(r"sk-[a-zA-Z0-9]{20,64}"),                        # OpenAI API keys
    re.compile(r"(Bearer\s+)[A-Za-z0-9_\-\.]{15,}", re.IGNORECASE),  # Bearer tokens
    re.compile(r"(password[\"']?\s*[:=]\s*[\"'])([^\"']+)([\"'])", re.IGNORECASE),
]


def strip_thai_characters(text: str) -> str:
    """Strictly removes any Thai Unicode characters from text."""
    if not text:
        return text
    return _THAI_CHAR_PATTERN.sub("", text)


def redact_secrets(text: str) -> str:
    """Scrubs all credentials and strictly removes any Thai script from text."""
    if not text:
        return text
    scrubbed = strip_thai_characters(text)
    for pattern in _REDACT_PATTERNS:
        scrubbed = pattern.sub("[REDACTED_CREDENTIAL]", scrubbed)
    # Also explicitly redact configured tokens if present in memory
    for secret in (Config.TELEGRAM_BOT_TOKEN, Config.GITHUB_TOKEN, Config.GEMINI_API_KEY, Config.OPENAI_API_KEY):
        if secret and len(secret) > 8:
            scrubbed = scrubbed.replace(secret, "[REDACTED_TOKEN]")
    return scrubbed
