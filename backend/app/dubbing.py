from __future__ import annotations
import asyncio
import json
import logging
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import edge_tts

logger = logging.getLogger(__name__)

# Curated verified high-quality voices per language for instant offline availability
KHMER_VOICES = [
    {
        "id": "km-KH-PisethNeural",
        "name": "Piseth (ពិសិដ្ឋ) - Male Neural",
        "gender": "Male",
        "language": "km-KH",
        "recommended": True,
        "age_impression": "adult",
    },
    {
        "id": "km-KH-SreymomNeural",
        "name": "Sreymom (ស្រីមុំ) - Female Neural",
        "gender": "Female",
        "language": "km-KH",
        "recommended": False,
        "age_impression": "adult",
    },
]

CURATED_VOICES_BY_LANG: dict[str, list[dict[str, Any]]] = {
    "km": KHMER_VOICES,
    "en": [
        {"id": "en-US-GuyNeural", "name": "Guy (US) - Male Adult", "gender": "Male", "language": "en-US", "recommended": True, "age_impression": "adult"},
        {"id": "en-US-JennyNeural", "name": "Jenny (US) - Female Adult", "gender": "Female", "language": "en-US", "recommended": True, "age_impression": "adult"},
        {"id": "en-US-AriaNeural", "name": "Aria (US) - Female Expressive", "gender": "Female", "language": "en-US", "recommended": False, "age_impression": "young_adult"},
        {"id": "en-US-ChristopherNeural", "name": "Christopher (US) - Male Mature", "gender": "Male", "language": "en-US", "recommended": False, "age_impression": "mature"},
        {"id": "en-US-AnaNeural", "name": "Ana (US) - Youthful / Childlike", "gender": "Female", "language": "en-US", "recommended": False, "age_impression": "childlike"},
        {"id": "en-GB-RyanNeural", "name": "Ryan (UK) - Male British", "gender": "Male", "language": "en-GB", "recommended": False, "age_impression": "adult"},
        {"id": "en-GB-SoniaNeural", "name": "Sonia (UK) - Female British", "gender": "Female", "language": "en-GB", "recommended": False, "age_impression": "adult"},
    ],
    "zh": [
        {"id": "zh-CN-YunxiNeural", "name": "Yunxi (云希) - Male Youthful", "gender": "Male", "language": "zh-CN", "recommended": True, "age_impression": "young_adult"},
        {"id": "zh-CN-XiaoxiaoNeural", "name": "Xiaoxiao (晓晓) - Female Warm", "gender": "Female", "language": "zh-CN", "recommended": True, "age_impression": "adult"},
        {"id": "zh-CN-YunjianNeural", "name": "Yunjian (云健) - Male Mature / Documentary", "gender": "Male", "language": "zh-CN", "recommended": False, "age_impression": "mature"},
        {"id": "zh-CN-XiaoyiNeural", "name": "Xiaoyi (晓伊) - Female Gentle", "gender": "Female", "language": "zh-CN", "recommended": False, "age_impression": "adult"},
    ],
    "zh-tw": [
        {"id": "zh-TW-YunJheNeural", "name": "YunJhe (雲哲) - Male Natural", "gender": "Male", "language": "zh-TW", "recommended": True, "age_impression": "adult"},
        {"id": "zh-TW-HsiaoChenNeural", "name": "HsiaoChen (曉臻) - Female Natural", "gender": "Female", "language": "zh-TW", "recommended": True, "age_impression": "adult"},
    ],
    "ja": [
        {"id": "ja-JP-KeitaNeural", "name": "Keita (圭太) - Male Clear", "gender": "Male", "language": "ja-JP", "recommended": True, "age_impression": "adult"},
        {"id": "ja-JP-NanamiNeural", "name": "Nanami (七海) - Female Warm", "gender": "Female", "language": "ja-JP", "recommended": True, "age_impression": "adult"},
    ],
    "ko": [
        {"id": "ko-KR-InJoonNeural", "name": "InJoon (인준) - Male Natural", "gender": "Male", "language": "ko-KR", "recommended": True, "age_impression": "adult"},
        {"id": "ko-KR-SunHiNeural", "name": "SunHi (선희) - Female Clear", "gender": "Female", "language": "ko-KR", "recommended": True, "age_impression": "adult"},
    ],
    "vi": [
        {"id": "vi-VN-NamMinhNeural", "name": "Nam Minh - Male Northern", "gender": "Male", "language": "vi-VN", "recommended": True, "age_impression": "adult"},
        {"id": "vi-VN-HoaiMyNeural", "name": "Hoài My - Female Clear", "gender": "Female", "language": "vi-VN", "recommended": True, "age_impression": "adult"},
    ],
    "fr": [
        {"id": "fr-FR-HenriNeural", "name": "Henri - Male Natural", "gender": "Male", "language": "fr-FR", "recommended": True, "age_impression": "adult"},
        {"id": "fr-FR-DeniseNeural", "name": "Denise - Female Clear", "gender": "Female", "language": "fr-FR", "recommended": True, "age_impression": "adult"},
    ],
    "es": [
        {"id": "es-ES-AlvaroNeural", "name": "Alvaro - Male Natural", "gender": "Male", "language": "es-ES", "recommended": True, "age_impression": "adult"},
        {"id": "es-ES-ElviraNeural", "name": "Elvira - Female Clear", "gender": "Female", "language": "es-ES", "recommended": True, "age_impression": "adult"},
    ],
    "pt": [
        {"id": "pt-BR-AntonioNeural", "name": "Antonio - Male Brazilian", "gender": "Male", "language": "pt-BR", "recommended": True, "age_impression": "adult"},
        {"id": "pt-BR-FranciscaNeural", "name": "Francisca - Female Brazilian", "gender": "Female", "language": "pt-BR", "recommended": True, "age_impression": "adult"},
    ],
    "de": [
        {"id": "de-DE-ConradNeural", "name": "Conrad - Male Natural", "gender": "Male", "language": "de-DE", "recommended": True, "age_impression": "adult"},
        {"id": "de-DE-KatjaNeural", "name": "Katja - Female Clear", "gender": "Female", "language": "de-DE", "recommended": True, "age_impression": "adult"},
    ],
    "it": [
        {"id": "it-IT-DiegoNeural", "name": "Diego - Male Natural", "gender": "Male", "language": "it-IT", "recommended": True, "age_impression": "adult"},
        {"id": "it-IT-ElsaNeural", "name": "Elsa - Female Clear", "gender": "Female", "language": "it-IT", "recommended": True, "age_impression": "adult"},
    ],
    "ru": [
        {"id": "ru-RU-DmitryNeural", "name": "Dmitry - Male Natural", "gender": "Male", "language": "ru-RU", "recommended": True, "age_impression": "adult"},
        {"id": "ru-RU-SvetlanaNeural", "name": "Svetlana - Female Clear", "gender": "Female", "language": "ru-RU", "recommended": True, "age_impression": "adult"},
    ],
    "id": [
        {"id": "id-ID-ArdiNeural", "name": "Ardi - Male Natural", "gender": "Male", "language": "id-ID", "recommended": True, "age_impression": "adult"},
        {"id": "id-ID-GadisNeural", "name": "Gadis - Female Clear", "gender": "Female", "language": "id-ID", "recommended": True, "age_impression": "adult"},
    ],
    "ms": [
        {"id": "ms-MY-OsmanNeural", "name": "Osman - Male Natural", "gender": "Male", "language": "ms-MY", "recommended": True, "age_impression": "adult"},
        {"id": "ms-MY-YasminNeural", "name": "Yasmin - Female Clear", "gender": "Female", "language": "ms-MY", "recommended": True, "age_impression": "adult"},
    ],
    "fil": [
        {"id": "fil-PH-AngeloNeural", "name": "Angelo - Male Natural", "gender": "Male", "language": "fil-PH", "recommended": True, "age_impression": "adult"},
        {"id": "fil-PH-BlessicaNeural", "name": "Blessica - Female Clear", "gender": "Female", "language": "fil-PH", "recommended": True, "age_impression": "adult"},
    ],
    "hi": [
        {"id": "hi-IN-MadhurNeural", "name": "Madhur - Male Natural", "gender": "Male", "language": "hi-IN", "recommended": True, "age_impression": "adult"},
        {"id": "hi-IN-SwaraNeural", "name": "Swara - Female Clear", "gender": "Female", "language": "hi-IN", "recommended": True, "age_impression": "adult"},
    ],
    "ar": [
        {"id": "ar-SA-HamedNeural", "name": "Hamed - Male Natural", "gender": "Male", "language": "ar-SA", "recommended": True, "age_impression": "adult"},
        {"id": "ar-SA-ZariyahNeural", "name": "Zariyah - Female Clear", "gender": "Female", "language": "ar-SA", "recommended": True, "age_impression": "adult"},
    ],
    "lo": [
        {"id": "lo-LA-ChanthavongNeural", "name": "Chanthavong - Male Natural", "gender": "Male", "language": "lo-LA", "recommended": True, "age_impression": "adult"},
        {"id": "lo-LA-KeomanyNeural", "name": "Keomany - Female Clear", "gender": "Female", "language": "lo-LA", "recommended": True, "age_impression": "adult"},
    ],
    "my": [
        {"id": "my-MM-ThihaNeural", "name": "Thiha - Male Natural", "gender": "Male", "language": "my-MM", "recommended": True, "age_impression": "adult"},
        {"id": "my-MM-NilarNeural", "name": "Nilar - Female Clear", "gender": "Female", "language": "my-MM", "recommended": True, "age_impression": "adult"},
    ],
}


def get_available_khmer_voices() -> list[dict[str, Any]]:
    """Returns curated high-quality Khmer neural voices supported by Edge TTS."""
    return KHMER_VOICES


def get_available_voices(target_lang: str | None = None) -> list[dict[str, Any]]:
    """
    Returns available neural voices for the specified target language.
    If target_lang is None or 'km', returns Khmer voices (preserving 100% backward compatibility).
    """
    if not target_lang or target_lang.strip().lower() in ("km", "khmer", "none"):
        return KHMER_VOICES

    lang_code = target_lang.strip().lower()
    if lang_code in CURATED_VOICES_BY_LANG:
        return CURATED_VOICES_BY_LANG[lang_code]

    # Partial prefix match (e.g. 'zh-cn' -> 'zh')
    short_code = lang_code.split("-")[0]
    if short_code in CURATED_VOICES_BY_LANG:
        return CURATED_VOICES_BY_LANG[short_code]

    # Fallback to English or Khmer voices
    return CURATED_VOICES_BY_LANG.get("en", KHMER_VOICES)


async def generate_speech_sample(
    text: str | None = None,
    voice_id: str = "km-KH-PisethNeural",
) -> bytes:
    """Generates a short speech sample for audio preview in browser."""
    sample_text = text
    if not sample_text or not sample_text.strip():
        # Provide natural sample text based on voice language
        vid_lower = voice_id.lower()
        if "km-" in vid_lower:
            sample_text = "សួស្តីកម្ពុជា ស្វាគមន៍មកកាន់ Khmer Translator"
        elif "zh-" in vid_lower:
            sample_text = "您好，欢迎使用智能视频翻译与配音工作室。"
        elif "ja-" in vid_lower:
            sample_text = "こんにちは、AI動画翻訳へようこそ。"
        elif "ko-" in vid_lower:
            sample_text = "안녕하세요, AI 비디오 번역 스튜디오입니다."
        elif "fr-" in vid_lower:
            sample_text = "Bonjour et bienvenue dans le studio de doublage IA."
        elif "es-" in vid_lower:
            sample_text = "Hola, bienvenido al estudio de traducción y doblaje de video."
        elif "th-" in vid_lower:
            sample_text = "สวัสดีครับ ยินดีต้อนรับสู่ระบบแปลและพากย์เสียงวิดีโอ"
        elif "vi-" in vid_lower:
            sample_text = "Xin chào, chào mừng bạn đến với studio lồng tiếng video."
        else:
            sample_text = "Hello, welcome to the Multilingual AI Video Translation Studio."

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        communicate = edge_tts.Communicate(sample_text, voice_id)
        await communicate.save(str(tmp_path))
        return tmp_path.read_bytes()
    finally:
        tmp_path.unlink(missing_ok=True)


async def generate_segment_audio(
    text: str,
    voice_id: str = "km-KH-PisethNeural",
    emotion: str = "neutral",
    rate_pct: int = 0,
) -> bytes:
    """Generates audio bytes for an individual dialogue segment with emotion modulation."""
    from .emotion import get_emotion_tts_adjustments
    em_rate, em_pitch, em_vol = get_emotion_tts_adjustments(emotion, base_rate_pct=rate_pct)
    rate_str = f"+{rate_pct}%" if rate_pct >= 0 else f"{rate_pct}%"

    clean_text = text
    if "km-" in voice_id.lower() or any("\u1780" <= ch <= "\u17d3" for ch in text):
        from .khmer_nlp import normalize_khmer_for_tts
        clean_text = normalize_khmer_for_tts(text) or text

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        try:
            comm = edge_tts.Communicate(clean_text, voice_id, rate=em_rate, pitch=em_pitch, volume=em_vol)
            await comm.save(str(tmp_path))
        except Exception as exc:
            logger.warning("TTS with emotion modulation failed on segment: %s, trying standard rate", exc)
            comm = edge_tts.Communicate(clean_text, voice_id, rate=rate_str)
            await comm.save(str(tmp_path))
        return tmp_path.read_bytes()
    finally:
        tmp_path.unlink(missing_ok=True)


# ==============================================================================
# NONVERBAL SOUND & VOCALIZATION DETECTION
# ==============================================================================
NONVERBAL_TAG_PATTERN = re.compile(
    r"^[\(\[\*]\s*(laughter|laughing|gasp|groan|sigh|music|applause|cheering|screaming|scream|crying|cry|pant|panting|cough|whisper|gunshot|explosion|fighting|punch|grunt|snicker|chuckle|sob|breath|breathing)\s*[\)\]\*]$",
    re.IGNORECASE,
)
NONVERBAL_INTERJECTION_PATTERN = re.compile(
    r"^(ha(\s*ha)+|he(\s*he)+|uh+|um+|ah+|oh+|hmm+|argh+|gah+|shh+|pfft|sigh|gasp|groan|oof|ouch|grr+)$",
    re.IGNORECASE,
)


def is_nonverbal_sound_segment(text: str) -> tuple[bool, str]:
    """
    Identifies nonverbal expressions, sound effects, or non-lexical vocalizations
    (laughter, crying, gasping, screaming, fighting grunts, background music cues)
    that should preserve authentic original audio instead of synthetic TTS speech.
    """
    t = text.strip()
    if not t:
        return True, "silence"
    tag_match = NONVERBAL_TAG_PATTERN.match(t)
    if tag_match:
        return True, tag_match.group(1).lower()
    if NONVERBAL_INTERJECTION_PATTERN.match(t):
        return True, "vocalization"
    return False, ""


def get_audio_file_duration(file_path: Path) -> float:
    """Returns exact audio stream duration in seconds via ffprobe."""
    if not file_path.exists() or file_path.stat().st_size == 0:
        return 0.0
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(file_path),
    ]
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=10)
        if res.returncode == 0 and res.stdout.strip():
            return float(res.stdout.strip())
    except Exception:
        pass
    return 0.0


def extract_original_audio_slice(
    media_path: Path,
    start_s: float,
    end_s: float,
    output_slice_path: Path,
) -> bool:
    """
    Extracts an audio slice directly from the original video/media,
    preserving real actor laughter, screams, gasps, crying, or fighting action sounds.
    """
    if not media_path.exists():
        return False
    duration = max(0.1, end_s - start_s)
    fade_d = min(0.04, duration / 4.0)
    fade_st = max(0.0, duration - fade_d)
    cmd = [
        "ffmpeg", "-y",
        "-ss", f"{max(0.0, start_s):.3f}",
        "-t", f"{duration:.3f}",
        "-i", str(media_path),
        "-af", f"afade=t=in:ss=0:d={fade_d:.3f},afade=t=out:st={fade_st:.3f}:d={fade_d:.3f}",
        "-c:a", "libmp3lame",
        "-b:a", "192k",
        str(output_slice_path),
    ]
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return res.returncode == 0 and output_slice_path.exists() and output_slice_path.stat().st_size > 0


def fit_speech_audio_to_window(
    audio_path: Path,
    window_duration: float,
    output_path: Path,
    max_tempo: float = 1.25,
) -> tuple[Path, float]:
    """
    Ensures generated speech audio fits within dialogue duration without cutting off
    sentence endings or trailing syllables. Uses atempo (pitch-neutral) and micro fade-out.
    """
    dur = get_audio_file_duration(audio_path)
    if dur <= 0:
        return audio_path, dur

    target_dur = max(0.4, window_duration)
    # If audio already fits comfortably within window (plus 5% headroom)
    if dur <= target_dur * 1.05:
        fade_d = min(0.04, dur / 6.0)
        fade_st = max(0.0, dur - fade_d)
        cmd = [
            "ffmpeg", "-y",
            "-i", str(audio_path),
            "-af", f"afade=t=out:st={fade_st:.3f}:d={fade_d:.3f}",
            "-c:a", "libmp3lame",
            "-b:a", "192k",
            str(output_path),
        ]
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if res.returncode == 0 and output_path.exists() and output_path.stat().st_size > 0:
            return output_path, dur
        return audio_path, dur

    # Speech is longer than window -> speed up slightly (atempo preserves pitch without distortion)
    ratio = dur / target_dur
    tempo = min(max_tempo, max(1.0, ratio))
    scaled_dur = dur / tempo
    fade_d = min(0.05, scaled_dur / 6.0)
    fade_st = max(0.0, scaled_dur - fade_d)

    cmd = [
        "ffmpeg", "-y",
        "-i", str(audio_path),
        "-af", f"atempo={tempo:.3f},afade=t=out:st={fade_st:.3f}:d={fade_d:.3f}",
        "-c:a", "libmp3lame",
        "-b:a", "192k",
        str(output_path),
    ]
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if res.returncode == 0 and output_path.exists() and output_path.stat().st_size > 0:
        new_dur = get_audio_file_duration(output_path)
        return output_path, new_dur

    return audio_path, dur


# ==============================================================================
# DUBBED AUDIO TRACK GENERATION WITH NONVERBAL & TIMING SAFEGUARDS
# ==============================================================================
async def generate_dubbed_audio_track(
    segments: list[dict[str, Any]],
    voice_id: str = "km-KH-PisethNeural",
    speaker_voices: dict[str, str] | None = None,
    speaker_rates: dict[str, int] | None = None,
    total_duration: float = 10.0,
    output_audio_path: Path | None = None,
    original_media_path: Path | None = None,
    preserve_nonverbal: bool = True,
    **kwargs: Any,
) -> Path:
    """
    Generates speech audio for all segments, fits audio to subtitle windows to prevent cut-offs,
    preserves original actor nonverbal vocalizations (laughter, gasps, screams, crying, action sounds),
    and aligns all segments on the timeline matching start timestamps.
    """
    if output_audio_path is None:
        raise ValueError("output_audio_path is required")

    output_audio_path.parent.mkdir(parents=True, exist_ok=True)

    spk_voices = speaker_voices or {}
    spk_rates = speaker_rates or {}

    orig_media = Path(original_media_path) if original_media_path else None
    if not orig_media and kwargs.get("original_audio_path"):
        orig_media = Path(kwargs["original_audio_path"])

    non_empty_segs = [s for s in sorted(segments, key=lambda x: x.get("start", 0.0)) if str(s.get("text", "")).strip()]
    if not non_empty_segs:
        # Create silent track if no segments
        cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", f"anullsrc=r=24000:cl=stereo:d={max(total_duration, 1.0)}", "-c:a", "libmp3lame", str(output_audio_path)]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return output_audio_path

    temp_files: list[Path] = []
    # Input 0 is the base track matching full duration
    inputs: list[str] = ["-f", "lavfi", "-i", f"anullsrc=r=24000:cl=stereo:d={max(total_duration, 1.0)}"]
    filter_parts: list[str] = ["[0:a]aformat=sample_fmts=fltp:sample_rates=24000:channel_layouts=stereo[base]"]

    try:
        filter_idx = 1
        for idx, seg in enumerate(non_empty_segs):
            text = str(seg.get("text", "")).strip()
            start_s = float(seg.get("start", 0.0))
            end_s = float(seg.get("end", 0.0))
            start_ms = max(0, int(round(start_s * 1000)))
            seg_duration = max(0.4, end_s - start_s)

            seg_file = Path(tempfile.mktemp(suffix=f"_seg_{idx}.mp3"))
            temp_files.append(seg_file)

            # Check if this segment is a nonverbal vocalization or sound event
            is_nv, nv_type = is_nonverbal_sound_segment(text)
            if is_nv:
                extracted = False
                if preserve_nonverbal and orig_media and orig_media.exists():
                    extracted = extract_original_audio_slice(orig_media, start_s, end_s, seg_file)
                    if extracted:
                        logger.info("Preserved authentic original %s sound on seg %d (%.2f-%.2f)", nv_type, idx, start_s, end_s)

                if not extracted:
                    # Nonverbal or punctuation without audio slice -> comfortable silence
                    cmd_silence = ["ffmpeg", "-y", "-f", "lavfi", "-i", f"anullsrc=r=24000:cl=stereo:d={seg_duration}", "-c:a", "libmp3lame", str(seg_file)]
                    await asyncio.to_thread(subprocess.run, cmd_silence, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            else:
                # Check if text contains any pronounceable letters or characters
                has_pronounceable = any(c.isalnum() for c in text)
                if not has_pronounceable:
                    cmd_silence = ["ffmpeg", "-y", "-f", "lavfi", "-i", f"anullsrc=r=24000:cl=stereo:d={seg_duration}", "-c:a", "libmp3lame", str(seg_file)]
                    await asyncio.to_thread(subprocess.run, cmd_silence, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                else:
                    # Determine voice for this segment based on speaker
                    spk_id = seg.get("speaker_id")
                    seg_voice = spk_voices.get(spk_id) if spk_id else None
                    if not seg_voice:
                        seg_voice = voice_id or "km-KH-PisethNeural"

                    rate_pct = spk_rates.get(spk_id, 0) if spk_id else 0
                    rate_str = f"+{rate_pct}%" if rate_pct >= 0 else f"{rate_pct}%"

                    # Apply story-aware emotion modulation (pitch, rate, volume)
                    from .emotion import get_emotion_tts_adjustments
                    emotion = seg.get("emotion") or "neutral"
                    em_rate, em_pitch, em_vol = get_emotion_tts_adjustments(emotion, base_rate_pct=rate_pct)

                    clean_text = text
                    if "km-" in seg_voice.lower() or any("\u1780" <= ch <= "\u17d3" for ch in text):
                        from .khmer_nlp import normalize_khmer_for_tts
                        clean_text = normalize_khmer_for_tts(text) or text

                    try:
                        comm = edge_tts.Communicate(clean_text, seg_voice, rate=em_rate, pitch=em_pitch, volume=em_vol)
                        await comm.save(str(seg_file))
                    except Exception as exc:
                        logger.warning("TTS error with emotion modulation on seg %d: %s, falling back to base rate", idx, exc)
                        try:
                            comm = edge_tts.Communicate(clean_text, seg_voice, rate=rate_str)
                            await comm.save(str(seg_file))
                        except Exception as exc2:
                            logger.warning("TTS error on segment %d voice %s: %s, falling back to default voice", idx, seg_voice, exc2)
                            try:
                                comm = edge_tts.Communicate(clean_text, voice_id)
                                await comm.save(str(seg_file))
                            except Exception as exc3:
                                logger.warning("TTS failed on segment %d ('%s'): %s. Using silence fallback.", idx, clean_text[:30], exc3)
                                cmd_silence = ["ffmpeg", "-y", "-f", "lavfi", "-i", f"anullsrc=r=24000:cl=stereo:d={seg_duration}", "-c:a", "libmp3lame", str(seg_file)]
                                await asyncio.to_thread(subprocess.run, cmd_silence, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

                    # Fit speech to dialogue window so sentence endings & last words are never clipped
                    if seg_file.exists() and seg_file.stat().st_size > 0:
                        fitted_file = Path(tempfile.mktemp(suffix=f"_fitted_{idx}.mp3"))
                        temp_files.append(fitted_file)
                        fitted_path, _ = fit_speech_audio_to_window(seg_file, seg_duration, fitted_file)
                        seg_file = fitted_path

            if seg_file.exists() and seg_file.stat().st_size > 0:
                inputs.extend(["-i", str(seg_file)])
                filter_parts.append(f"[{filter_idx}:a]adelay={start_ms}|{start_ms},aformat=sample_fmts=fltp:sample_rates=24000:channel_layouts=stereo[a{filter_idx}]")
                filter_idx += 1

        if filter_idx == 1:
            # Only the base track exists (no speech segments succeeded)
            cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", f"anullsrc=r=24000:cl=stereo:d={max(total_duration, 1.0)}", "-c:a", "libmp3lame", str(output_audio_path)]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            return output_audio_path

        mix_inputs = "[base]" + "".join(f"[a{i}]" for i in range(1, filter_idx))
        filter_str = ";".join(filter_parts) + f";{mix_inputs}amix=inputs={filter_idx}:normalize=0:duration=first[out]"

        cmd = [
            "ffmpeg", "-y",
            *inputs,
            "-filter_complex", filter_str,
            "-map", "[out]",
            "-c:a", "libmp3lame",
            "-b:a", "192k",
            str(output_audio_path),
        ]

        logger.info("Assembling dubbed audio track with %d speech segments into %s", filter_idx - 1, output_audio_path.name)
        res = await asyncio.to_thread(subprocess.run, cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=180)
        if res.returncode != 0:
            err = res.stderr[-500:] if res.stderr else "FFmpeg mixing error"
            raise RuntimeError(f"FFmpeg audio dub assembly failed: {err}")

        if not output_audio_path.exists() or output_audio_path.stat().st_size < 100:
            raise RuntimeError("Generated dubbed audio file is missing or invalid.")

        return output_audio_path
    finally:
        for f in temp_files:
            f.unlink(missing_ok=True)


# ==============================================================================
# SPEECH-AWARE SOUNDTRACK PRESERVATION & INTELLIGENT AUDIO MIXING
# ==============================================================================
def intelligent_mix_soundtrack(
    original_audio_path: Path | None = None,
    dubbed_audio_path: Path | None = None,
    output_mixed_path: Path | None = None,
    voice_volume: float = 1.0,
    soundtrack_volume: float = 0.85,
    preserve_soundtrack: bool = True,
    ducking_intensity: float = 0.35,
    **kwargs: Any,
) -> Path:
    """
    Intelligent speech-aware audio mixing:
    - Preserves background music, fighting sounds, punches, kicks, impacts, explosions, and environmental audio.
    - Where speech is NOT occurring, the original soundtrack plays at 100% full volume.
    - Where speech IS occurring, dynamically ducks the original background audio using sidechain compression
      and gentle vocal formant notch filtering so dialogue is crystal clear while action sounds remain audible.
    """
    orig_path = original_audio_path or kwargs.get("original_media_path")
    dub_path = dubbed_audio_path or kwargs.get("speech_audio_path")
    out_path = output_mixed_path or kwargs.get("output_audio_path")
    v_vol = kwargs.get("voice_volume", kwargs.get("speech_volume", voice_volume))
    st_vol = kwargs.get("soundtrack_volume", kwargs.get("original_volume", soundtrack_volume))

    if not orig_path or not Path(orig_path).exists():
        raise FileNotFoundError(f"Original audio not found: {orig_path}")
    if not dub_path or not Path(dub_path).exists():
        raise FileNotFoundError(f"Dubbed audio not found: {dub_path}")
    if not out_path:
        raise ValueError("output_mixed_path is required")

    orig_p = Path(orig_path)
    dub_p = Path(dub_path)
    out_p = Path(out_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    voice_vol = max(0.0, min(float(v_vol), 3.0))
    orig_vol = max(0.0, min(float(st_vol), 2.0))

    # Probe original media to check if it has an audio stream
    from .transcription import probe_media_file
    probe = probe_media_file(orig_p)
    streams = probe.get("streams", [])
    has_orig_audio = any(s.get("codec_type") == "audio" for s in streams)

    if not has_orig_audio or not preserve_soundtrack or orig_vol <= 0.01:
        # No original audio, or user turned off soundtrack preservation -> encode dubbed speech directly
        cmd = [
            "ffmpeg", "-y",
            "-i", str(dub_p),
            "-c:a", "libmp3lame",
            "-b:a", "192k",
            str(out_p),
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=120)
        if res.returncode != 0:
            err = res.stderr[-500:] if res.stderr else "Audio copy failed"
            raise RuntimeError(f"FFmpeg audio encoding failed: {err}")
        return out_p

    # Speech-aware sidechain compression filter graph:
    # [0:a] is background audio (normalized to soundtrack_volume)
    # [1:a] is dubbed voice (split into mix track and sidechain trigger)
    # sidechaincompress smoothly attenuates background only while voice signal is present.
    # equalizer gently dips 1.4 kHz voice formants on the ducked track to eliminate vocal clashes.
    filter_complex = (
        f"[0:a]volume={orig_vol},aformat=sample_fmts=fltp:sample_rates=24000:channel_layouts=stereo[bg_raw];"
        f"[1:a]volume={voice_vol},aformat=sample_fmts=fltp:sample_rates=24000:channel_layouts=stereo,apad[voice];"
        f"[voice]asplit=2[voice_mix][voice_sc];"
        f"[bg_raw][voice_sc]sidechaincompress=threshold=0.03:ratio=5:attack=35:release=300[ducked_raw];"
        f"[ducked_raw]equalizer=f=1400:t=q:w=1.0:g=-5[ducked_bg];"
        f"[ducked_bg][voice_mix]amix=inputs=2:duration=first:dropout_transition=2[out]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", str(orig_p),
        "-i", str(dub_p),
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-c:a", "libmp3lame",
        "-b:a", "192k",
        str(out_p),
    ]

    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=180)
    if res.returncode != 0:
        err = res.stderr[-500:] if res.stderr else "Audio mix failed"
        raise RuntimeError(f"FFmpeg speech-aware audio mixing failed: {err}")

    if not out_p.exists() or out_p.stat().st_size == 0:
        raise RuntimeError("Mixed audio file is empty or missing.")

    return out_p


def mix_audio_tracks(
    original_audio_path: Path | None = None,
    dubbed_audio_path: Path | None = None,
    output_mixed_path: Path | None = None,
    voice_volume: float = 1.0,
    original_volume: float = 0.85,
    **kwargs: Any,
) -> Path:
    """
    Mixes original background media audio with the dubbed speech.
    Provides 100% backward compatibility for all existing tests while leveraging
    speech-aware dynamic ducking to preserve music and fighting sound effects.
    """
    preserve_st = kwargs.pop("preserve_soundtrack", True)
    duck_int = kwargs.pop("ducking_intensity", 0.35)
    return intelligent_mix_soundtrack(
        original_audio_path=original_audio_path,
        dubbed_audio_path=dubbed_audio_path,
        output_mixed_path=output_mixed_path,
        voice_volume=voice_volume,
        soundtrack_volume=original_volume,
        preserve_soundtrack=preserve_st,
        ducking_intensity=duck_int,
        **kwargs,
    )

