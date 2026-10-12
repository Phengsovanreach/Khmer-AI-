from __future__ import annotations
from typing import Any

# Curated registry of supported languages with native scripts and flags
SUPPORTED_LANGUAGES: list[dict[str, Any]] = [
    {
        "code": "km",
        "name": "Khmer",
        "native_name": "ភាសាខ្មែរ",
        "flag": "🇰🇭",
        "whisper_code": "km",
        "edge_prefix": "km-KH",
        "default_voice": "km-KH-PisethNeural",
        "asr_supported": True,
        "translation_supported": True,
        "tts_supported": True,
    },
    {
        "code": "en",
        "name": "English",
        "native_name": "English",
        "flag": "🇺🇸",
        "whisper_code": "en",
        "edge_prefix": "en-US",
        "default_voice": "en-US-GuyNeural",
        "asr_supported": True,
        "translation_supported": True,
        "tts_supported": True,
    },
    {
        "code": "zh",
        "name": "Chinese (Simplified)",
        "native_name": "简体中文",
        "flag": "🇨🇳",
        "whisper_code": "zh",
        "edge_prefix": "zh-CN",
        "default_voice": "zh-CN-YunxiNeural",
        "asr_supported": True,
        "translation_supported": True,
        "tts_supported": True,
    },
    {
        "code": "zh-TW",
        "name": "Chinese (Traditional)",
        "native_name": "繁體中文",
        "flag": "🇹🇼",
        "whisper_code": "zh",
        "edge_prefix": "zh-TW",
        "default_voice": "zh-TW-YunJheNeural",
        "asr_supported": True,
        "translation_supported": True,
        "tts_supported": True,
    },
    {
        "code": "ja",
        "name": "Japanese",
        "native_name": "日本語",
        "flag": "🇯🇵",
        "whisper_code": "ja",
        "edge_prefix": "ja-JP",
        "default_voice": "ja-JP-KeitaNeural",
        "asr_supported": True,
        "translation_supported": True,
        "tts_supported": True,
    },
    {
        "code": "ko",
        "name": "Korean",
        "native_name": "한국어",
        "flag": "🇰🇷",
        "whisper_code": "ko",
        "edge_prefix": "ko-KR",
        "default_voice": "ko-KR-InJoonNeural",
        "asr_supported": True,
        "translation_supported": True,
        "tts_supported": True,
    },
    {
        "code": "vi",
        "name": "Vietnamese",
        "native_name": "Tiếng Việt",
        "flag": "🇻🇳",
        "whisper_code": "vi",
        "edge_prefix": "vi-VN",
        "default_voice": "vi-VN-NamMinhNeural",
        "asr_supported": True,
        "translation_supported": True,
        "tts_supported": True,
    },
    {
        "code": "fr",
        "name": "French",
        "native_name": "Français",
        "flag": "🇫🇷",
        "whisper_code": "fr",
        "edge_prefix": "fr-FR",
        "default_voice": "fr-FR-HenriNeural",
        "asr_supported": True,
        "translation_supported": True,
        "tts_supported": True,
    },
    {
        "code": "es",
        "name": "Spanish",
        "native_name": "Español",
        "flag": "🇪🇸",
        "whisper_code": "es",
        "edge_prefix": "es-ES",
        "default_voice": "es-ES-AlvaroNeural",
        "asr_supported": True,
        "translation_supported": True,
        "tts_supported": True,
    },
    {
        "code": "pt",
        "name": "Portuguese",
        "native_name": "Português",
        "flag": "🇧🇷",
        "whisper_code": "pt",
        "edge_prefix": "pt-BR",
        "default_voice": "pt-BR-AntonioNeural",
        "asr_supported": True,
        "translation_supported": True,
        "tts_supported": True,
    },
    {
        "code": "de",
        "name": "German",
        "native_name": "Deutsch",
        "flag": "🇩🇪",
        "whisper_code": "de",
        "edge_prefix": "de-DE",
        "default_voice": "de-DE-ConradNeural",
        "asr_supported": True,
        "translation_supported": True,
        "tts_supported": True,
    },
    {
        "code": "it",
        "name": "Italian",
        "native_name": "Italiano",
        "flag": "🇮🇹",
        "whisper_code": "it",
        "edge_prefix": "it-IT",
        "default_voice": "it-IT-DiegoNeural",
        "asr_supported": True,
        "translation_supported": True,
        "tts_supported": True,
    },
    {
        "code": "ru",
        "name": "Russian",
        "native_name": "Русский",
        "flag": "🇷🇺",
        "whisper_code": "ru",
        "edge_prefix": "ru-RU",
        "default_voice": "ru-RU-DmitryNeural",
        "asr_supported": True,
        "translation_supported": True,
        "tts_supported": True,
    },
    {
        "code": "id",
        "name": "Indonesian",
        "native_name": "Bahasa Indonesia",
        "flag": "🇮🇩",
        "whisper_code": "id",
        "edge_prefix": "id-ID",
        "default_voice": "id-ID-ArdiNeural",
        "asr_supported": True,
        "translation_supported": True,
        "tts_supported": True,
    },
    {
        "code": "ms",
        "name": "Malay",
        "native_name": "Bahasa Melayu",
        "flag": "🇲🇾",
        "whisper_code": "ms",
        "edge_prefix": "ms-MY",
        "default_voice": "ms-MY-OsmanNeural",
        "asr_supported": True,
        "translation_supported": True,
        "tts_supported": True,
    },
    {
        "code": "fil",
        "name": "Filipino / Tagalog",
        "native_name": "Filipino",
        "flag": "🇵🇭",
        "whisper_code": "tl",
        "edge_prefix": "fil-PH",
        "default_voice": "fil-PH-AngeloNeural",
        "asr_supported": True,
        "translation_supported": True,
        "tts_supported": True,
    },
    {
        "code": "hi",
        "name": "Hindi",
        "native_name": "हिन्दी",
        "flag": "🇮🇳",
        "whisper_code": "hi",
        "edge_prefix": "hi-IN",
        "default_voice": "hi-IN-MadhurNeural",
        "asr_supported": True,
        "translation_supported": True,
        "tts_supported": True,
    },
    {
        "code": "ar",
        "name": "Arabic",
        "native_name": "العربية",
        "flag": "🇸🇦",
        "whisper_code": "ar",
        "edge_prefix": "ar-SA",
        "default_voice": "ar-SA-HamedNeural",
        "asr_supported": True,
        "translation_supported": True,
        "tts_supported": True,
    },
    {
        "code": "lo",
        "name": "Lao",
        "native_name": "ພາສາລາວ",
        "flag": "🇱🇦",
        "whisper_code": "lo",
        "edge_prefix": "lo-LA",
        "default_voice": "lo-LA-ChanthavongNeural",
        "asr_supported": True,
        "translation_supported": True,
        "tts_supported": True,
    },
    {
        "code": "my",
        "name": "Burmese",
        "native_name": "မြန်မာဘာသာ",
        "flag": "🇲🇲",
        "whisper_code": "my",
        "edge_prefix": "my-MM",
        "default_voice": "my-MM-ThihaNeural",
        "asr_supported": True,
        "translation_supported": True,
        "tts_supported": True,
    },
]

# Source language special options
SOURCE_SPECIAL_OPTIONS = [
    {
        "code": "auto",
        "name": "Auto Detect",
        "native_name": "ស្វែងរកស្វ័យប្រវត្តិ (Auto Detect)",
        "flag": "🌐",
        "whisper_code": None,
        "asr_supported": True,
        "translation_supported": True,
        "tts_supported": False,
    }
]

_LANG_MAP = {lang["code"]: lang for lang in SUPPORTED_LANGUAGES}


def get_supported_languages() -> list[dict[str, Any]]:
    return SUPPORTED_LANGUAGES


def get_source_languages() -> list[dict[str, Any]]:
    return SOURCE_SPECIAL_OPTIONS + SUPPORTED_LANGUAGES


def get_target_languages() -> list[dict[str, Any]]:
    return SUPPORTED_LANGUAGES


def get_language_by_code(code: str | None) -> dict[str, Any] | None:
    if not code:
        return None
    c = code.strip().lower()
    if c == "auto":
        return SOURCE_SPECIAL_OPTIONS[0]
    return _LANG_MAP.get(code) or _LANG_MAP.get(c)


def normalize_whisper_code(code: str | None) -> str | None:
    """Normalizes UI language code to faster-whisper language code."""
    if not code or code.lower() in ("auto", "none"):
        return None
    lang = get_language_by_code(code)
    if lang:
        return lang.get("whisper_code", code)
    return code
