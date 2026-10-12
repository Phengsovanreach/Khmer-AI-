import asyncio
import subprocess
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.dubbing import (
    is_nonverbal_sound_segment,
    get_audio_file_duration,
    fit_speech_audio_to_window,
    extract_original_audio_slice,
    intelligent_mix_soundtrack,
    mix_audio_tracks,
    generate_dubbed_audio_track,
)
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_is_nonverbal_sound_segment():
    # Tagged sound events & nonverbal cues
    is_nv, event = is_nonverbal_sound_segment("[laughter]")
    assert is_nv is True
    assert event == "laughter"

    is_nv, event = is_nonverbal_sound_segment("*gasp*")
    assert is_nv is True
    assert event == "gasp"

    is_nv, event = is_nonverbal_sound_segment("(screaming)")
    assert is_nv is True
    assert event == "screaming"

    is_nv, event = is_nonverbal_sound_segment("[music]")
    assert is_nv is True
    assert event == "music"

    is_nv, event = is_nonverbal_sound_segment("ha ha ha")
    assert is_nv is True
    assert event == "vocalization"

    is_nv, event = is_nonverbal_sound_segment("hmm")
    assert is_nv is True
    assert event == "vocalization"

    # Regular spoken dialogue must NOT be flagged as nonverbal
    is_nv, _ = is_nonverbal_sound_segment("Hello, how are you today?")
    assert is_nv is False

    is_nv, _ = is_nonverbal_sound_segment("ជំរាបសួរអ្នកទាំងអស់គ្នា")
    assert is_nv is False


def test_fit_speech_audio_to_window_normal():
    # Generate 1.0s test audio
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f_in, \
         tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f_out:
        in_p = Path(f_in.name)
        out_p = Path(f_out.name)

    try:
        cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=1.0", "-c:a", "libmp3lame", str(in_p)]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        # Fit into 2.0s window -> fits comfortably, should not stretch
        fitted, dur = fit_speech_audio_to_window(in_p, 2.0, out_p)
        assert fitted.exists()
        assert dur > 0.8 and dur < 1.3
    finally:
        in_p.unlink(missing_ok=True)
        out_p.unlink(missing_ok=True)


def test_fit_speech_audio_to_window_speedup():
    # Generate 2.0s test audio
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f_in, \
         tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f_out:
        in_p = Path(f_in.name)
        out_p = Path(f_out.name)

    try:
        cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=2.0", "-c:a", "libmp3lame", str(in_p)]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        # Target window is 1.6s -> Speech is too long, fit_speech_audio_to_window speeds it up with atempo
        fitted, dur = fit_speech_audio_to_window(in_p, 1.6, out_p, max_tempo=1.25)
        assert fitted.exists()
        assert dur < 1.95  # Successfully compacted so ending syllables aren't cut off
    finally:
        in_p.unlink(missing_ok=True)
        out_p.unlink(missing_ok=True)


def test_extract_original_audio_slice():
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f_media, \
         tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f_slice:
        media_p = Path(f_media.name)
        slice_p = Path(f_slice.name)

    try:
        # Create 3-second media
        cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=300:duration=3.0", "-c:a", "libmp3lame", str(media_p)]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        ok = extract_original_audio_slice(media_p, 0.5, 1.5, slice_p)
        assert ok is True
        assert slice_p.exists() and slice_p.stat().st_size > 500
        dur = get_audio_file_duration(slice_p)
        assert 0.9 <= dur <= 1.2
    finally:
        media_p.unlink(missing_ok=True)
        slice_p.unlink(missing_ok=True)


def test_intelligent_mix_soundtrack_sidechain_ducking():
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f_orig, \
         tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f_voice, \
         tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f_mixed:
        orig_p = Path(f_orig.name)
        voice_p = Path(f_voice.name)
        mixed_p = Path(f_mixed.name)

    try:
        # Original: 4-second background music/effects
        cmd_orig = ["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=220:duration=4.0", "-c:a", "libmp3lame", str(orig_p)]
        subprocess.run(cmd_orig, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        # Voice: 2-second speech starting at t=1s
        cmd_voice = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "sine=frequency=880:duration=2.0",
            "-af", "adelay=1000|1000",
            "-c:a", "libmp3lame",
            str(voice_p),
        ]
        subprocess.run(cmd_voice, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        # Mix with preserve_soundtrack=True
        out = intelligent_mix_soundtrack(
            original_audio_path=orig_p,
            dubbed_audio_path=voice_p,
            output_mixed_path=mixed_p,
            soundtrack_volume=0.85,
            voice_volume=1.0,
            preserve_soundtrack=True,
            ducking_intensity=0.35,
        )

        assert out.exists()
        assert out.stat().st_size > 1000
        dur = get_audio_file_duration(out)
        assert 3.8 <= dur <= 4.2
    finally:
        orig_p.unlink(missing_ok=True)
        voice_p.unlink(missing_ok=True)
        mixed_p.unlink(missing_ok=True)


def test_generate_dubbed_audio_track_with_nonverbal_preservation():
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f_orig, \
         tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f_dub:
        orig_p = Path(f_orig.name)
        dub_p = Path(f_dub.name)

    try:
        # Create 4s original media
        cmd_orig = ["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=330:duration=4.0", "-c:a", "libmp3lame", str(orig_p)]
        subprocess.run(cmd_orig, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        # Segment 0 is laughter (nonverbal), Segment 1 is short text
        segments = [
            {"id": 0, "start": 0.5, "end": 1.5, "text": "[laughter]", "speaker_id": "speaker_1"},
            {"id": 1, "start": 2.0, "end": 3.0, "text": "Yes.", "speaker_id": "speaker_1"},
        ]

        asyncio.run(
            generate_dubbed_audio_track(
                segments=segments,
                voice_id="en-US-GuyNeural",
                total_duration=4.0,
                output_audio_path=dub_p,
                original_media_path=orig_p,
                preserve_nonverbal=True,
            )
        )

        assert dub_p.exists()
        assert dub_p.stat().st_size > 1000
        dur = get_audio_file_duration(dub_p)
        assert 3.8 <= dur <= 4.2
    finally:
        orig_p.unlink(missing_ok=True)
        dub_p.unlink(missing_ok=True)
