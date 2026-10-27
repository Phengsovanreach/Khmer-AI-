"""
Khmer Translator AI — Telegram Bot Notification Client.
Implements resilient, credential-scrubbed alert delivery via the Telegram Bot API.
"""
from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Optional

from ..config import Config, redact_secrets

logger = logging.getLogger(__name__)


class TelegramNotifier:
    def __init__(self, token: Optional[str] = None, chat_id: Optional[str] = None):
        self._token = token or Config.TELEGRAM_BOT_TOKEN
        self._chat_id = chat_id or Config.TELEGRAM_CHAT_ID

    @property
    def is_configured(self) -> bool:
        """Returns True only if both bot token and chat ID are available."""
        return bool(self._token and self._chat_id and self._token.strip() and self._chat_id.strip())

    def send_message(
        self,
        text: str,
        parse_mode: str = "HTML",
        disable_web_page_preview: bool = True,
        max_retries: int = 3,
    ) -> dict[str, Any]:
        """
        Sends an alert message to the configured Telegram chat.
        Safely handles missing credentials, message length limits, and API rate limits.
        """
        if not self.is_configured:
            logger.info("Telegram notification skipped: TELEGRAM_NOT_CONFIGURED")
            return {"status": "TELEGRAM_NOT_CONFIGURED", "delivered": False}

        scrubbed_text = redact_secrets(text)

        # Telegram message length limit is 4096 characters
        chunks = self._chunk_message(scrubbed_text, max_len=4000)
        last_result = {}

        for chunk in chunks:
            last_result = self._send_chunk_with_retry(
                chunk,
                parse_mode=parse_mode,
                disable_web_page_preview=disable_web_page_preview,
                max_retries=max_retries,
            )
            if not last_result.get("delivered"):
                break

        return last_result

    def _send_chunk_with_retry(
        self,
        chunk: str,
        parse_mode: str,
        disable_web_page_preview: bool,
        max_retries: int,
    ) -> dict[str, Any]:
        """Sends a single chunk with exponential backoff on HTTP 429 rate limits."""
        url = f"{Config.TELEGRAM_API_BASE}/bot{self._token}/sendMessage"
        payload = {
            "chat_id": self._chat_id,
            "text": chunk,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_web_page_preview,
        }
        data = json.dumps(payload).encode("utf-8")

        for attempt in range(1, max_retries + 1):
            req = urllib.request.Request(
                url,
                data=data,
                headers={"Content-Type": "application/json", "User-Agent": "KhmerTranslatorSelfHealing/2.0"},
            )
            try:
                with urllib.request.urlopen(req, timeout=15) as resp:
                    resp_data = json.loads(resp.read().decode("utf-8"))
                    if resp_data.get("ok"):
                        return {"status": "DELIVERED", "delivered": True, "message_id": resp_data.get("result", {}).get("message_id")}
                    return {"status": "API_ERROR", "delivered": False, "error": redact_secrets(str(resp_data))}

            except urllib.error.HTTPError as exc:
                raw_err = exc.read().decode("utf-8", errors="ignore")
                # Handle rate limit 429
                if exc.code == 429:
                    retry_after = 5
                    try:
                        err_json = json.loads(raw_err)
                        retry_after = int(err_json.get("parameters", {}).get("retry_after", 5))
                    except Exception:
                        pass
                    if attempt < max_retries:
                        time.sleep(retry_after)
                        continue
                logger.error("Telegram API HTTP %s: %s", exc.code, redact_secrets(raw_err))
                return {"status": f"HTTP_{exc.code}", "delivered": False, "error": redact_secrets(raw_err)}

            except Exception as exc:
                if attempt < max_retries:
                    time.sleep(2 * attempt)
                    continue
                logger.error("Telegram send error: %s", redact_secrets(str(exc)))
                return {"status": "NETWORK_ERROR", "delivered": False, "error": redact_secrets(str(exc))}

        return {"status": "MAX_RETRIES_EXCEEDED", "delivered": False}

    @staticmethod
    def _chunk_message(text: str, max_len: int = 4000) -> list[str]:
        """Splits text into chunks at line breaks if possible."""
        if len(text) <= max_len:
            return [text]
        lines = text.split("\n")
        chunks = []
        current = ""
        for line in lines:
            if len(current) + len(line) + 1 > max_len:
                if current:
                    chunks.append(current.strip())
                current = line + "\n"
            else:
                current += line + "\n"
        if current.strip():
            chunks.append(current.strip())
        return chunks
