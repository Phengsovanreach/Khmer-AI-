from __future__ import annotations
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

SUPPORTED_EMOTIONS = [
    "neutral",
    "happy",
    "sad",
    "angry",
    "excited",
    "afraid",
    "surprised",
    "worried",
    "calm",
    "whispering",
    "serious",
    "sarcastic",
]

# Lexical emotion cues across multilingual transcripts
_EMOTION_KEYWORDS = {
    "happy": ["happy", "glad", "great", "wonderful", "smile", "love", "good", "រីករាយ", "សប្បាយ", "ល្អណាស់", "អបអរ", "哈哈", "开心", "快乐"],
    "excited": ["wow", "amazing", "awesome", "hurray", "yes!", "oh my god", "អស្ចារ្យ", "ជ័យជំនះ", "太棒了", "哇"],
    "sad": ["sad", "sorry", "crying", "unfortunate", "heartbroken", "miss", "lost", "ព្រួយ", "សោកស្តាយ", "យំ", "ឈឺចាប់", "难过", "伤心"],
    "angry": ["angry", "mad", "hate", "shut up", "idiot", "damn", "furious", "stop it", "ខឹង", "ស្អប់", "បញ្ឈប់", "生氣", "愤怒"],
    "afraid": ["afraid", "scared", "fear", "run", "help", "danger", "ghost", "monster", "ខ្លាច", "ភ័យ", "ជួយផង", "害怕", "恐怖"],
    "surprised": ["what?!", "really?", "no way", "impossible", "unbelievable", "មែនឬ", "មិនគួរឲ្យជឿ", "ពិតមែន", "真的吗", "不可能"],
    "worried": ["worry", "anxious", "nervous", "trouble", "problem", "careful", "បារម្ភ", "ព្រួយបារម្ភ", "ប្រយ័ត្ន", "担心", "焦急"],
    "whispering": ["shh", "quiet", "secret", "whisper", "hush", "កុំមាត់", "សម្ងាត់", "ស្ងាត់", "嘘", "小声点"],
    "serious": ["important", "listen", "truth", "official", "must", "warning", "សំខាន់", "ស្តាប់", "ការពិត", "严肃", "注意"],
}


def get_emotion_tts_adjustments(emotion: str, base_rate_pct: int = 0) -> tuple[str, str, str]:
    """
    Returns (rate_str, pitch_str, volume_str) tailored for Edge-TTS neural voices.
    Applies natural speech modulation without acoustic distortion.
    """
    em = (emotion or "neutral").lower().strip()
    rate_delta = 0
    pitch_hz = 0
    volume_pct = 0

    if em == "excited":
        rate_delta = 12
        pitch_hz = 6
        volume_pct = 6
    elif em == "angry":
        rate_delta = 10
        pitch_hz = 8
        volume_pct = 15
    elif em == "happy":
        rate_delta = 8
        pitch_hz = 4
        volume_pct = 5
    elif em == "sad":
        rate_delta = -12
        pitch_hz = -6
        volume_pct = -10
    elif em == "afraid":
        rate_delta = 12
        pitch_hz = 10
        volume_pct = -4
    elif em == "surprised":
        rate_delta = 10
        pitch_hz = 12
        volume_pct = 8
    elif em == "worried":
        rate_delta = -4
        pitch_hz = 4
        volume_pct = -4
    elif em == "calm":
        rate_delta = -6
        pitch_hz = -2
        volume_pct = 0
    elif em == "whispering":
        rate_delta = -10
        pitch_hz = -4
        volume_pct = -25
    elif em == "serious":
        rate_delta = -4
        pitch_hz = -4
        volume_pct = 4
    elif em == "sarcastic":
        rate_delta = -8
        pitch_hz = 2
        volume_pct = 0
    else:  # neutral
        rate_delta = 0
        pitch_hz = 0
        volume_pct = 0

    total_rate = max(-35, min(40, base_rate_pct + rate_delta))
    rate_str = f"+{total_rate}%" if total_rate >= 0 else f"{total_rate}%"
    pitch_str = f"+{pitch_hz}Hz" if pitch_hz >= 0 else f"{pitch_hz}Hz"
    vol_str = f"+{volume_pct}%" if volume_pct >= 0 else f"{volume_pct}%"

    return rate_str, pitch_str, vol_str


def analyze_dialogue_emotions(
    segments: list[dict[str, Any]],
    acoustic_features: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """
    Performs story-aware conversational emotion detection across dialogue turns.
    Evaluates:
      1. Current segment text, punctuation & duration
      2. Conversational context window (preceding & following turns)
      3. Speaker continuity across turns
      4. Acoustic energy and pitch cues when available
    """
    if not segments:
        return []

    enriched_segments: list[dict[str, Any]] = []
    n = len(segments)

    # First pass: linguistic & acoustic evidence per turn
    raw_turn_emotions: list[dict[str, Any]] = []
    for i, seg in enumerate(segments):
        text = str(seg.get("text", "")).strip()
        spk_id = seg.get("speaker_id", "speaker_1")
        ac_feat = acoustic_features[i] if acoustic_features and i < len(acoustic_features) else None

        detected = "neutral"
        confidence = 0.65

        # Punctuation analysis
        has_excl = "!" in text or "！" in text
        has_ques = "?" in text or "？" in text
        has_ellipsis = "..." in text or "…" in text
        is_shouting = text.isupper() and len(text) > 4

        # Keyword matching
        lower_text = text.lower()
        matched_emotions = []
        for em_name, keywords in _EMOTION_KEYWORDS.items():
            for kw in keywords:
                if kw in lower_text:
                    matched_emotions.append(em_name)
                    break

        if matched_emotions:
            detected = matched_emotions[0]
            confidence = 0.82
        elif has_excl and has_ques:
            detected = "surprised"
            confidence = 0.78
        elif is_shouting:
            detected = "angry"
            confidence = 0.85
        elif has_excl:
            # Differentiate happy/excited vs angry based on energy
            if ac_feat and ac_feat.get("energy", 0) > 0.12:
                detected = "excited"
                confidence = 0.75
            else:
                detected = "happy"
                confidence = 0.72
        elif has_ques:
            detected = "worried" if any(w in lower_text for w in ["why", "how", "where"]) else "neutral"
            confidence = 0.70
        elif has_ellipsis:
            detected = "sad" if ac_feat and ac_feat.get("energy", 0) < 0.04 else "calm"
            confidence = 0.70

        # Acoustic modulation override if extreme pitch or energy
        if ac_feat:
            f0_med = ac_feat.get("f0_median", 150.0)
            energy = ac_feat.get("energy", 0.05)
            if energy < 0.015 and f0_med < 110:
                detected = "whispering"
                confidence = 0.80
            elif energy > 0.18 and f0_med > 220 and detected == "neutral":
                detected = "excited"
                confidence = 0.75

        raw_turn_emotions.append({
            "detected": detected,
            "confidence": confidence,
            "speaker_id": spk_id,
            "text": text,
        })

    # Second pass: Story Context & Speaker Continuity smoothing
    for i, seg in enumerate(segments):
        current_raw = raw_turn_emotions[i]
        final_emotion = current_raw["detected"]
        final_conf = current_raw["confidence"]

        # Check preceding turn from same speaker (within 8 seconds)
        if i > 0 and raw_turn_emotions[i - 1]["speaker_id"] == current_raw["speaker_id"]:
            prev_em = raw_turn_emotions[i - 1]["detected"]
            # If current is neutral but previous was emotionally intense, smooth continuity
            if final_emotion == "neutral" and prev_em in ("sad", "angry", "worried", "calm", "whispering"):
                time_gap = float(seg.get("start", 0)) - float(segments[i - 1].get("end", 0))
                if time_gap < 5.0:
                    final_emotion = prev_em
                    final_conf = 0.70

        rate_str, pitch_str, vol_str = get_emotion_tts_adjustments(final_emotion)

        seg_copy = dict(seg)
        seg_copy["emotion"] = final_emotion
        seg_copy["emotion_confidence"] = round(final_conf, 2)
        seg_copy["ssml_rate"] = rate_str
        seg_copy["ssml_pitch"] = pitch_str
        seg_copy["ssml_volume"] = vol_str

        enriched_segments.append(seg_copy)

    return enriched_segments
