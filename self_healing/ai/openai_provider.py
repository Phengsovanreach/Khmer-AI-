"""
Khmer Translator AI — OpenAI / Compatible Provider.
Supports OpenAI, Groq, Mistral, and local vLLM/Ollama endpoints.
"""
from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from typing import Any, Optional

from ..config import Config, redact_secrets
from .base import BaseAIProvider

logger = logging.getLogger(__name__)


class OpenAICompatibleProvider(BaseAIProvider):
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or Config.OPENAI_API_KEY
        self.base_url = (base_url or "https://api.openai.com/v1").rstrip("/")
        self.model = model

    def is_available(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def generate_analysis(self, prompt: str) -> Optional[dict[str, Any]]:
        if not self.is_available():
            return None

        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a senior site reliability engineer analyzing application incidents. Output only valid JSON."},
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.1,
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "User-Agent": "KhmerTranslatorSelfHealing/2.0",
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                choices = data.get("choices", [])
                if choices:
                    content = choices[0].get("message", {}).get("content", "")
                    return json.loads(content)
        except Exception as exc:
            logger.error("OpenAI provider analysis error: %s", redact_secrets(str(exc)))
        return None
