"""
Khmer Translator AI — Google Gemini AI Provider.
Communicates directly with the Gemini REST API without requiring external SDK installations.
"""
from __future__ import annotations

import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Optional

from ..config import Config, redact_secrets
from .base import BaseAIProvider

logger = logging.getLogger(__name__)


class GeminiProvider(BaseAIProvider):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or Config.GEMINI_API_KEY
        self.model = model or Config.AI_MODEL_NAME

    def is_available(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def generate_analysis(self, prompt: str) -> Optional[dict[str, Any]]:
        if not self.is_available():
            logger.info("Gemini provider skipped: GEMINI_API_KEY not configured")
            return None

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.1,
                "responseMimeType": "application/json",
            },
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "User-Agent": "KhmerTranslatorSelfHealing/2.0"},
        )

        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        text_response = parts[0].get("text", "")
                        return json.loads(text_response)
        except Exception as exc:
            logger.error("Gemini analysis error: %s", redact_secrets(str(exc)))
        return None
