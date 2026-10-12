from __future__ import annotations
import asyncio
import json
import logging
import urllib.parse
import urllib.request
from typing import Any

from .languages import get_language_by_code

logger = logging.getLogger(__name__)


def _normalize_lang_code(code: str | None, is_target: bool = False) -> str:
    if not code or code.strip().lower() in ("auto", "none"):
        return "km" if is_target else "auto"
    c = code.strip()
    # Normalize common variations
    c_lower = c.lower()
    if c_lower in ("zh", "chinese", "zh-cn", "zh_cn"):
        return "zh-CN"
    if c_lower in ("zh-tw", "zh_tw"):
        return "zh-TW"
    if c_lower in ("en", "english"):
        return "en"
    if c_lower in ("km", "khmer"):
        return "km"
    return c


def _translate_via_gtx(text: str, source_lang: str, target_lang: str) -> str | None:
    """Translates text via Google Web API (free, fast, no auth)."""
    clean = text.strip()
    if not clean:
        return ""
    sl = "auto" if source_lang in ("auto", None) else source_lang
    tl = target_lang
    url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={sl}&tl={tl}&dt=t&q={urllib.parse.quote(clean)}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data and isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
                translated = "".join(part[0] for part in data[0] if part and part[0])
                if translated.strip():
                    return translated.strip()
    except Exception as exc:
        logger.debug("GTX translation attempt failed: %s", exc)
    return None


def _translate_via_mymemory(text: str, source_lang: str, target_lang: str) -> str | None:
    """Translates text via free MyMemory API."""
    clean = text.strip()
    if not clean:
        return ""
    src = "en" if source_lang in ("auto", None) else source_lang
    url = f"https://api.mymemory.translated.net/get?q={urllib.parse.quote(clean)}&langpair={src}|{target_lang}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (KhmerTranslator/2.0)"})
    try:
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            translated = data.get("responseData", {}).get("translatedText", "")
            if translated and not translated.startswith("MYMEMORY WARNING"):
                return translated.strip()
    except Exception as exc:
        logger.debug("MyMemory translation attempt failed: %s", exc)
    return None


def translate_single_line(text: str, source_lang: str = "auto", target_lang: str = "km") -> str:
    """
    Translates a single line of text from source_lang to target_lang.
    Uses resilient dual-engine fallbacks (Google GTX + MyMemory).
    Does NOT require Ollama or paid APIs.
    """
    clean = text.strip()
    if not clean:
        return ""

    src = _normalize_lang_code(source_lang, is_target=False)
    tgt = _normalize_lang_code(target_lang, is_target=True)

    # If same language, no translation needed
    if src == tgt and src != "auto":
        return clean

    # Try GTX first
    result = _translate_via_gtx(clean, src, tgt)
    if result:
        return result

    # Try MyMemory fallback
    result = _translate_via_mymemory(clean, src, tgt)
    if result:
        return result

    # Return original if all providers unavailable
    return clean


def _translate_single_line_mymemory(text: str, source_lang: str = "en") -> str:
    """Backward compatibility helper for tests."""
    return translate_single_line(text, source_lang=source_lang, target_lang="km")


# Preserved for backward compatibility
translate_text_to_khmer = _translate_single_line_mymemory


async def translate_segments(
    segments: list[dict[str, Any]],
    source_lang: str = "auto",
    target_lang: str = "km",
) -> list[dict[str, Any]]:
    """
    Translates transcript subtitle segments from source_lang to target_lang.
    Preserves exact timing, start, end, IDs, speaker assignments, and order.
    Does NOT require Ollama or heavy local LLMs.
    """
    if not segments:
        return []

    src = _normalize_lang_code(source_lang, is_target=False)
    tgt = _normalize_lang_code(target_lang, is_target=True)

    translated_segments: list[dict[str, Any]] = []

    for seg in sorted(segments, key=lambda s: s.get("start", 0.0)):
        orig_text = str(seg.get("text", "")).strip()
        speaker_id = seg.get("speaker_id")
        seg_id = seg.get("id", len(translated_segments) + 1)
        start_t = round(float(seg.get("start", 0.0)), 3)
        end_t = round(float(seg.get("end", 0.0)), 3)

        if not orig_text:
            out_seg: dict[str, Any] = {
                "id": seg_id,
                "start": start_t,
                "end": end_t,
                "text": "",
            }
            if speaker_id:
                out_seg["speaker_id"] = speaker_id
            translated_segments.append(out_seg)
            continue

        translated_text = await asyncio.to_thread(translate_single_line, orig_text, src, tgt)

        out_seg = {
            "id": seg_id,
            "start": start_t,
            "end": end_t,
            "text": translated_text,
        }
        if speaker_id:
            out_seg["speaker_id"] = speaker_id
        translated_segments.append(out_seg)

        await asyncio.sleep(0.04)

    return translated_segments


async def translate_segments_to_khmer(
    segments: list[dict[str, Any]],
    source_lang: str = "auto",
) -> list[dict[str, Any]]:
    """Backward compatibility wrapper."""
    return await translate_segments(segments, source_lang=source_lang, target_lang="km")
