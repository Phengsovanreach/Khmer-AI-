from __future__ import annotations
import gc
import json
import logging
import os
import subprocess
import threading
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Ensure PyAV >= 15 compatibility with faster-whisper decode_audio
try:
    import av
    _orig_av_open = av.open
    def _compat_av_open(*args, **kwargs):
        kwargs.pop("metadata_errors", None)
        return _orig_av_open(*args, **kwargs)
    av.open = _compat_av_open
except Exception as e:
    logger.warning("Could not patch av.open for faster-whisper compatibility: %s", e)

SUPPORTED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".flac", ".ogg", ".aac", ".opus"}
SUPPORTED_VIDEO_EXTENSIONS = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".m4v"}
ALLOWED_EXTENSIONS = SUPPORTED_AUDIO_EXTENSIONS | SUPPORTED_VIDEO_EXTENSIONS

AVAILABLE_MODELS = [
    {
        "id": "tiny",
        "name": "Tiny (Recommended)",
        "download_size_mb": 75,
        "estimated_ram_mb": 390,
        "description": "Fastest CPU inference, lowest memory footprint (~390 MB RAM). Best for low-memory machines.",
        "is_default": True,
    },
    {
        "id": "base",
        "name": "Base",
        "download_size_mb": 145,
        "estimated_ram_mb": 500,
        "description": "Better recognition accuracy, moderate memory footprint (~500 MB RAM).",
        "is_default": False,
    },
]

_MODEL_CACHE: Any = None
_CACHED_MODEL_ID: str | None = None
_MODEL_LOCK = threading.Lock()


def get_available_models() -> list[dict[str, Any]]:
    return AVAILABLE_MODELS


def get_whisper_model(model_id: str = "tiny", device: str = "cpu", compute_type: str = "int8"):
    global _MODEL_CACHE, _CACHED_MODEL_ID
    valid_ids = {m["id"] for m in AVAILABLE_MODELS}
    if model_id not in valid_ids:
        model_id = "tiny"

    with _MODEL_LOCK:
        if _MODEL_CACHE is not None and _CACHED_MODEL_ID == model_id:
            return _MODEL_CACHE

        # Unload previous model to preserve RAM
        if _MODEL_CACHE is not None:
            del _MODEL_CACHE
            _MODEL_CACHE = None
            _CACHED_MODEL_ID = None
            gc.collect()

        from faster_whisper import WhisperModel
        cpu_threads = max(1, min(os.cpu_count() or 4, 8))
        logger.info("Loading WhisperModel '%s' (device=%s, compute_type=%s, cpu_threads=%d)...", model_id, device, compute_type, cpu_threads)
        model = WhisperModel(model_id, device=device, compute_type=compute_type, cpu_threads=cpu_threads)
        _MODEL_CACHE = model
        _CACHED_MODEL_ID = model_id
        return model


def probe_media_file(file_path: Path, require_audio: bool = False) -> dict[str, Any]:
    """
    Validates the media file with ffprobe, checks for audio streams,
    and returns duration and stream metadata.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Media file does not exist: {file_path}")

    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration,size,format_name:stream=codec_type,codec_name,channels,sample_rate,width,height",
        "-of", "json",
        str(file_path),
    ]

    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15)
    except Exception as exc:
        raise RuntimeError(f"FFprobe execution failed: {exc}") from exc

    if res.returncode != 0:
        err_msg = res.stderr.strip() or "File is unreadable or corrupted."
        raise ValueError(f"Corrupted or invalid media file: {err_msg}")

    try:
        data = json.loads(res.stdout)
    except Exception as exc:
        raise ValueError(f"Could not parse FFprobe output: {exc}") from exc

    streams = data.get("streams", [])
    audio_streams = [s for s in streams if s.get("codec_type") == "audio"]
    if require_audio and not audio_streams:
        raise ValueError("The uploaded media file does not contain any audio stream to transcribe.")

    fmt_info = data.get("format", {})
    duration_str = fmt_info.get("duration")
    duration = float(duration_str) if duration_str is not None else 0.0

    return {
        "duration": duration,
        "format_name": fmt_info.get("format_name", ""),
        "audio_codec": audio_streams[0].get("codec_name", "") if audio_streams else None,
        "channels": audio_streams[0].get("channels") if audio_streams else None,
        "sample_rate": audio_streams[0].get("sample_rate") if audio_streams else None,
        "has_audio": len(audio_streams) > 0,
        "streams": streams,
    }


def extract_audio_stream(input_file: Path, output_wav: Path) -> Path:
    """
    Extract clean 16kHz mono 16-bit PCM audio WAV using FFmpeg for optimal speech recognition.
    """
    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_file),
        "-vn",
        "-ar", "16000",
        "-ac", "1",
        "-c:a", "pcm_s16le",
        str(output_wav),
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=90)
    if res.returncode != 0:
        err = res.stderr.strip()[:200] or "Unknown ffmpeg error"
        raise RuntimeError(f"FFmpeg audio extraction failed: {err}")
    return output_wav


def transcribe_media(
    file_path: Path,
    model_id: str = "tiny",
    language: str | None = None,
    device: str = "cpu",
    compute_type: str = "int8",
    vad_filter: bool = True,
    progress_callback: Any | None = None,
    cancel_check: Any | None = None,
) -> dict[str, Any]:
    """
    Transcribes media file using faster-whisper with real segment progress tracking.
    Returns detected language, duration, and list of segments.
    Automatically falls back if VAD filter yields 0 segments (e.g. songs, music).
    """
    if cancel_check and cancel_check():
        raise InterruptedError("Transcription cancelled by user")

    model = get_whisper_model(model_id=model_id, device=device, compute_type=compute_type)

    lang_param = None
    if language and language.strip() and language.strip().lower() != "auto":
        lang_param = language.strip().lower()

    try:
        segments_gen, info = model.transcribe(
            str(file_path),
            language=lang_param,
            vad_filter=vad_filter,
            vad_parameters=dict(min_silence_duration_ms=500, speech_pad_ms=400) if vad_filter else None,
            beam_size=1,  # Fast, low-memory beam search
            best_of=1,
            temperature=0.0,
            condition_on_previous_text=False,
        )

        total_duration = float(info.duration) if hasattr(info, "duration") and info.duration else 0.0

        segments: list[dict[str, Any]] = []
        for idx, seg in enumerate(segments_gen, start=1):
            if cancel_check and cancel_check():
                raise InterruptedError("Transcription cancelled by user")

            text = seg.text.strip()
            seg_dict = {
                "id": idx,
                "start": round(float(seg.start), 3),
                "end": round(float(seg.end), 3),
                "text": text,
            }
            if text:
                segments.append(seg_dict)

            if progress_callback:
                progress_callback(float(seg.end), total_duration, seg_dict)

        # Automatic fallback: If VAD filter was on but yielded 0 segments,
        # retry without VAD filter so singing, music, and quiet vocals are recognized!
        if vad_filter and len(segments) == 0:
            if cancel_check and cancel_check():
                raise InterruptedError("Transcription cancelled by user")

            logger.info("VAD filter yielded 0 segments on %s. Retrying without VAD filter...", file_path.name)
            fallback_gen, fallback_info = model.transcribe(
                str(file_path),
                language=lang_param,
                vad_filter=False,
                beam_size=1,
                best_of=1,
                temperature=0.0,
                condition_on_previous_text=False,
            )
            info = fallback_info
            total_duration = float(fallback_info.duration) if hasattr(fallback_info, "duration") and fallback_info.duration else total_duration

            for idx, seg in enumerate(fallback_gen, start=1):
                if cancel_check and cancel_check():
                    raise InterruptedError("Transcription cancelled by user")

                text = seg.text.strip()
                seg_dict = {
                    "id": idx,
                    "start": round(float(seg.start), 3),
                    "end": round(float(seg.end), 3),
                    "text": text,
                }
                if text:
                    segments.append(seg_dict)

                if progress_callback:
                    progress_callback(float(seg.end), total_duration, seg_dict)

        return {
            "source_language": info.language,
            "language_probability": round(float(info.language_probability), 4) if hasattr(info, "language_probability") else 1.0,
            "duration": round(float(info.duration), 2) if hasattr(info, "duration") else total_duration,
            "segments": segments,
            "model_used": model_id,
        }
    except MemoryError as me:
        logger.error("Out of memory during speech recognition: %s", me)
        raise RuntimeError("Insufficient RAM to complete transcription. Try using the 'tiny' model and close background tasks.") from me
    except Exception as exc:
        logger.error("Speech recognition failed: %s", exc)
        raise RuntimeError(f"Transcription failed: {exc}") from exc


def format_srt_timestamp(seconds: float) -> str:
    """Format seconds into SubRip HH:MM:SS,mmm timestamp."""
    if seconds < 0:
        seconds = 0.0
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def build_srt_content(segments: list[dict[str, Any]]) -> str:
    """
    Generates standard compliant SRT subtitles with sequential numbering,
    correct HH:MM:SS,mmm timestamps, and UTF-8 Khmer text preservation.
    """
    entries = []
    idx = 1
    for seg in sorted(segments, key=lambda s: s.get("start", 0.0)):
        text = str(seg.get("text", "")).strip()
        if not text:
            continue
        start_ts = format_srt_timestamp(float(seg.get("start", 0.0)))
        end_ts = format_srt_timestamp(float(seg.get("end", 0.0)))
        entries.append(f"{idx}\n{start_ts} --> {end_ts}\n{text}")
        idx += 1

    return "\n\n".join(entries) + ("\n" if entries else "")


def build_txt_content(segments: list[dict[str, Any]], include_timestamps: bool = True) -> str:
    """Generates plain text transcript with optional timestamp labels."""
    lines = []
    for seg in sorted(segments, key=lambda s: s.get("start", 0.0)):
        text = str(seg.get("text", "")).strip()
        if not text:
            continue
        if include_timestamps:
            start_ts = format_srt_timestamp(float(seg.get("start", 0.0)))
            lines.append(f"[{start_ts}] {text}")
        else:
            lines.append(text)
    return "\n".join(lines) + ("\n" if lines else "")


def format_vtt_timestamp(seconds: float) -> str:
    """Format seconds into WebVTT HH:MM:SS.mmm timestamp."""
    if seconds < 0:
        seconds = 0.0
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


def build_vtt_content(segments: list[dict[str, Any]]) -> str:
    """Generates standard compliant WebVTT subtitles."""
    entries = ["WEBVTT - Khmer Translator Subtitles\n"]
    idx = 1
    for seg in sorted(segments, key=lambda s: s.get("start", 0.0)):
        text = str(seg.get("text", "")).strip()
        if not text:
            continue
        start_ts = format_vtt_timestamp(float(seg.get("start", 0.0)))
        end_ts = format_vtt_timestamp(float(seg.get("end", 0.0)))
        entries.append(f"{idx}\n{start_ts} --> {end_ts}\n{text}\n")
        idx += 1

    return "\n".join(entries)


def escape_ffmpeg_filter_path(path: Path | str) -> str:
    """Escapes special characters in file paths for FFmpeg filtergraph strings."""
    p_str = str(Path(path).resolve()).replace("\\", "/")
    return p_str.replace(":", "\\:").replace("'", "\\'")


def render_video_with_subtitles(
    input_media_path: Path,
    subtitles_srt_path: Path,
    output_mp4_path: Path,
    font_size: int = 22,
    audio_track_path: Path | None = None,
) -> dict[str, Any]:
    """
    Renders video with burned-in (hardsubbed) subtitles using FFmpeg.
    If audio_track_path is provided, uses it as the soundtrack (for Khmer AI dubbed audio).
    If input is video, burns subtitles directly onto video frames.
    If input is audio-only, generates a 720p dark navy background canvas with burned-in subtitles.
    Preserves Khmer typography with Noto Sans Khmer font.
    """
    if not input_media_path.exists():
        raise FileNotFoundError(f"Input media not found: {input_media_path}")
    if not subtitles_srt_path.exists():
        raise FileNotFoundError(f"Subtitles file not found: {subtitles_srt_path}")

    probe = probe_media_file(input_media_path)
    streams = probe.get("streams", [])
    has_video = any(s.get("codec_type") == "video" for s in streams)
    duration = float(probe.get("duration", 0.0) or 5.0)

    escaped_srt = escape_ffmpeg_filter_path(subtitles_srt_path)
    style = f"Fontname=Noto Sans Khmer,Fontsize={font_size},PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BackColour=&H80000000,BorderStyle=4,MarginV=35"

    output_mp4_path.parent.mkdir(parents=True, exist_ok=True)

    if audio_track_path and audio_track_path.exists():
        if has_video:
            cmd = [
                "ffmpeg", "-y",
                "-i", str(input_media_path),
                "-i", str(audio_track_path),
                "-filter_complex", f"[0:v]subtitles='{escaped_srt}':force_style='{style}'[v]",
                "-map", "[v]",
                "-map", "1:a:0",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-threads", "0",
                "-c:a", "aac", "-b:a", "192k",
                "-movflags", "+faststart",
                str(output_mp4_path),
            ]
        else:
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi", "-i", f"color=c=0x080f1d:s=1280x720:r=24:d={duration}",
                "-i", str(audio_track_path),
                "-vf", f"subtitles='{escaped_srt}':force_style='{style}'",
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-c:v", "libx264", "-preset", "ultrafast", "-tune", "stillimage", "-crf", "24", "-threads", "0",
                "-c:a", "aac", "-b:a", "192k",
                "-shortest",
                "-movflags", "+faststart",
                str(output_mp4_path),
            ]
    else:
        orig_has_audio = probe.get("has_audio", False)
        if has_video:
            cmd = [
                "ffmpeg", "-y",
                "-i", str(input_media_path),
                "-vf", f"subtitles='{escaped_srt}':force_style='{style}'",
                "-map", "0:v:0",
            ]
            if orig_has_audio:
                cmd.extend(["-map", "0:a:0", "-c:a", "aac", "-b:a", "192k"])
            cmd.extend([
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-threads", "0",
                "-movflags", "+faststart",
                str(output_mp4_path),
            ])
        else:
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi", "-i", f"color=c=0x080f1d:s=1280x720:r=24:d={duration}",
                "-i", str(input_media_path),
                "-vf", f"subtitles='{escaped_srt}':force_style='{style}'",
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-c:v", "libx264", "-preset", "ultrafast", "-tune", "stillimage", "-crf", "24", "-threads", "0",
                "-c:a", "aac", "-b:a", "192k",
                "-shortest",
                "-movflags", "+faststart",
                str(output_mp4_path),
            ]

    logger.info("Executing FFmpeg subtitle burn-in command on %s -> %s", input_media_path.name, output_mp4_path.name)
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=300)
    if res.returncode != 0:
        err_msg = res.stderr[-500:] if res.stderr else "Unknown FFmpeg error"
        logger.error("FFmpeg video rendering failed: %s", err_msg)
        raise RuntimeError(f"FFmpeg video rendering failed: {err_msg}")

    if not output_mp4_path.exists() or output_mp4_path.stat().st_size == 0:
        raise RuntimeError("Rendered video file is empty or was not created.")

    # Probe resulting output
    out_probe = probe_media_file(output_mp4_path, require_audio=False)
    out_streams = out_probe.get("streams", [])
    video_stream = next((s for s in out_streams if s.get("codec_type") == "video"), {})
    has_audio = out_probe.get("has_audio", False)

    # Strictly validate that audio stream is present if an audio track was provided or original had audio
    expect_audio = bool(audio_track_path and audio_track_path.exists()) or probe.get("has_audio", False)
    if expect_audio and not has_audio:
        raise RuntimeError(
            "Rendered video failed audio validation: no audible audio stream detected in output MP4."
        )

    return {
        "output_path": str(output_mp4_path),
        "size_bytes": output_mp4_path.stat().st_size,
        "duration": float(out_probe.get("duration", duration)),
        "width": int(video_stream.get("width", 1280) or 1280),
        "height": int(video_stream.get("height", 720) or 720),
        "has_audio_track": has_audio,
        "audio_codec": out_probe.get("audio_codec"),
    }

