import asyncio
import os
import subprocess
from pathlib import Path
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from app.main import app, _find_job_media_path
from app.config import UPLOAD_DIR, OUTPUT_DIR
from app.storage import save_job, delete_job
from app.dubbing import (
    verify_audio_is_audible,
    generate_dubbed_audio_track,
    mix_audio_tracks,
    intelligent_mix_soundtrack,
    get_default_voice_for_language,
)
from app.transcription import render_video_with_subtitles, probe_media_file


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def audible_wav(tmp_path) -> Path:
    """Generates a genuinely audible 440 Hz test tone WAV file."""
    wav_path = tmp_path / "audible_tone.wav"
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "sine=frequency=440:duration=1.5",
        "-ar", "24000",
        "-ac", "2",
        str(wav_path)
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return wav_path


@pytest.fixture
def silent_wav(tmp_path) -> Path:
    """Generates a completely silent audio track (anullsrc)."""
    wav_path = tmp_path / "silent_test.wav"
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "anullsrc=r=24000:cl=stereo:d=1.5",
        str(wav_path)
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return wav_path


@pytest.fixture
def sample_video_with_audio(tmp_path) -> Path:
    """Generates a short 720p MP4 test video with an audible audio track."""
    vid_path = tmp_path / "sample_input.mp4"
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "testsrc=size=640x360:rate=24:duration=2.0",
        "-f", "lavfi", "-i", "sine=frequency=880:duration=2.0",
        "-c:v", "libx264", "-preset", "ultrafast",
        "-c:a", "aac", "-b:a", "128k",
        "-shortest",
        str(vid_path)
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return vid_path


def test_verify_audio_is_audible_distinguishes_silence(audible_wav, silent_wav):
    """
    Test 1 & 8: Verify that verify_audio_is_audible accurately recognizes
    audible audio and correctly rejects digital silence.
    """
    assert verify_audio_is_audible(audible_wav) is True
    assert verify_audio_is_audible(silent_wav) is False


def test_get_default_voice_for_language():
    """
    Test: Language-aware voice selection maps to appropriate native voices.
    """
    assert get_default_voice_for_language("km") == "km-KH-PisethNeural"
    assert get_default_voice_for_language("en") == "en-US-GuyNeural"
    assert get_default_voice_for_language("zh") == "zh-CN-YunxiNeural"
    assert get_default_voice_for_language("vi") == "vi-VN-NamMinhNeural"
    assert get_default_voice_for_language("fr") == "fr-FR-HenriNeural"


def test_generate_dubbed_audio_track_with_audible_mock(tmp_path, audible_wav):
    """
    Test 1, 3, 7: Valid segments synthesize and merge into a decodable, audible audio track.
    """
    out_audio = tmp_path / "dubbed_track.mp3"
    segments = [
        {"id": 0, "start": 0.0, "end": 1.2, "text": "សួស្តីកម្ពុជា", "speaker_id": "spk1"}
    ]

    async def mock_save(path):
        import shutil
        shutil.copy(str(audible_wav), str(path))

    async def run_test():
        with patch("edge_tts.Communicate.save", side_effect=mock_save):
            return await generate_dubbed_audio_track(
                segments=segments,
                output_audio_path=out_audio,
                voice_id="km-KH-PisethNeural",
                total_duration=2.0,
            )

    res = asyncio.run(run_test())

    assert res.exists()
    assert res.stat().st_size > 500
    assert verify_audio_is_audible(res) is True

    # Probe decodability
    probe = probe_media_file(res)
    assert probe.get("has_audio") is True
    assert probe.get("audio_codec") in ["mp3", "mp3float"]
    assert float(probe.get("duration", 0.0)) > 1.0


def test_tts_failure_raises_clear_error_and_never_fakes_success(tmp_path):
    """
    Test 2 & 8: When TTS fails completely on spoken segments, raise a clear error
    and DO NOT report success with a silent track.
    """
    out_audio = tmp_path / "dubbed_fail.mp3"
    segments = [
        {"id": 0, "start": 0.0, "end": 1.2, "text": "សួស្តីកម្ពុជា", "speaker_id": "spk1"}
    ]

    async def mock_fail_save(*args, **kwargs):
        raise ConnectionError("TTS service unreachable")

    async def run_test():
        with patch("edge_tts.Communicate.save", side_effect=mock_fail_save):
            await generate_dubbed_audio_track(
                segments=segments,
                output_audio_path=out_audio,
                voice_id="km-KH-PisethNeural",
                total_duration=2.0,
            )

    with pytest.raises(RuntimeError) as exc_info:
        asyncio.run(run_test())
    assert "TTS speech generation failed" in str(exc_info.value)


def test_ffmpeg_soundtrack_preservation_and_mixing(tmp_path, audible_wav):
    """
    Test 4, 5, 6: FFmpeg sidechain compression mixes background and dubbed voice
    and output contains decodable audio stream.
    """
    mixed_out = tmp_path / "mixed_soundtrack.mp3"
    res = intelligent_mix_soundtrack(
        original_audio_path=audible_wav,
        dubbed_audio_path=audible_wav,
        output_mixed_path=mixed_out,
        voice_volume=1.0,
        soundtrack_volume=0.8,
        preserve_soundtrack=True,
    )

    assert res.exists()
    assert res.stat().st_size > 500
    assert verify_audio_is_audible(res) is True

    probe = probe_media_file(res)
    assert probe.get("has_audio") is True
    assert float(probe.get("duration", 0.0)) > 1.0


def test_render_video_with_subtitles_includes_audio_stream(tmp_path, sample_video_with_audio, audible_wav):
    """
    Test 4, 5, 6: FFmpeg hardsub video rendering properly maps the audio track
    into the final MP4 container and validates its presence.
    """
    srt_path = tmp_path / "test.srt"
    srt_path.write_text("1\n00:00:00,000 --> 00:00:01,500\nសួស្តី\n", encoding="utf-8")
    out_mp4 = tmp_path / "rendered_output.mp4"

    result = render_video_with_subtitles(
        input_media_path=sample_video_with_audio,
        subtitles_srt_path=srt_path,
        output_mp4_path=out_mp4,
        audio_track_path=audible_wav,
    )

    assert out_mp4.exists()
    assert out_mp4.stat().st_size > 1000
    assert result["has_audio_track"] is True
    assert result["duration"] > 1.0

    # Probe resulting MP4 directly
    probe = probe_media_file(out_mp4)
    assert probe.get("has_audio") is True
    audio_stream = next((s for s in probe["streams"] if s.get("codec_type") == "audio"), None)
    assert audio_stream is not None
    assert audio_stream.get("codec_name") == "aac"
    assert float(probe.get("duration", 0.0)) > 1.0


def test_export_rendered_video_rejects_silent_or_missing_audio(client, sample_video_with_audio, silent_wav):
    """
    Test 8: export-video endpoint strictly rejects missing or inaudible audio.
    """
    job_id = "test_silent_export"
    target_media = UPLOAD_DIR / f"{job_id}.mp4"
    target_media.write_bytes(sample_video_with_audio.read_bytes())

    # Put a silent candidate audio in OUTPUT_DIR
    bad_dubbed = OUTPUT_DIR / f"{job_id}_dubbed.mp3"
    bad_dubbed.write_bytes(silent_wav.read_bytes())

    job = {
        "id": job_id,
        "filename": "test.mp4",
        "path": str(target_media),
        "status": "translated",
        "stage": "completed",
        "translation": [
            {"id": 0, "start": 0.0, "end": 1.0, "text": "សួស្តី", "speaker_id": "spk1"}
        ],
        "target_language": "km",
        "duration_seconds": 2.0,
    }
    save_job(job)

    try:
        # Mock TTS to fail so auto-synthesis fails and candidate is caught as inaudible
        with patch("app.main.generate_dubbed_audio_track", side_effect=RuntimeError("TTS failed")):
            res = client.post(
                f"/api/jobs/{job_id}/export-video",
                json={"include_dubbed_audio": True, "audio_mode": "dubbed"}
            )
            # Should fail with 500 error because audio is inaudible / failed, never fake success!
            assert res.status_code == 500
            assert "audible" in res.json()["detail"].lower() or "failed" in res.json()["detail"].lower()
    finally:
        bad_dubbed.unlink(missing_ok=True)
        target_media.unlink(missing_ok=True)
        delete_job(job_id)
