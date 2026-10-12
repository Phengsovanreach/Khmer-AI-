import pytest
import subprocess
from pathlib import Path
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from app.main import app, _find_job_media_path
from app.config import UPLOAD_DIR, OUTPUT_DIR
from app.storage import save_job, delete_job


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sample_wav(tmp_path) -> Path:
    wav_path = tmp_path / "valid_test_dub.wav"
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "sine=frequency=1000:duration=2.0",
        "-ar", "24000",
        "-ac", "1",
        str(wav_path)
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return wav_path


def test_media_path_resolution_with_production_paths(tmp_path):
    """Verifies that _find_job_media_path resolves media when job['path'] has an old developer path."""
    job_id = "testres01"
    media_file = UPLOAD_DIR / f"{job_id}.mp4"
    media_file.write_bytes(b"\x00" * 1024)

    try:
        # Simulate a job recorded with a foreign/developer absolute path
        job_foreign = {
            "id": job_id,
            "path": "/home/some_developer/khmer-translator/backend/uploads/testres01.mp4",
            "filename": "testres01.mp4",
        }
        resolved = _find_job_media_path(job_id, job_foreign)
        assert resolved.exists()
        assert resolved.resolve() == media_file.resolve()
    finally:
        media_file.unlink(missing_ok=True)


def test_media_path_traversal_prevention():
    """Verifies that _find_job_media_path rejects path traversal attempts."""
    with pytest.raises(Exception):
        _find_job_media_path("../../../etc/passwd")

    with pytest.raises(Exception):
        _find_job_media_path("job123", {"path": "/etc/passwd"})


def test_dubbing_endpoint_no_unbound_local_error(client, sample_wav):
    """
    Directly tests that /api/jobs/{job_id}/dub executes without raising
    'cannot access local variable media_path where it is not associated with a value'.
    """
    job_id = "dubtest01"
    target_media = UPLOAD_DIR / f"{job_id}.wav"
    target_media.write_bytes(sample_wav.read_bytes())

    job = {
        "id": job_id,
        "filename": "dubtest01.wav",
        "name": "Dub Test",
        "status": "transcribed",
        "stage": "completed",
        "progress": 100,
        "message": "Ready",
        "duration_seconds": 2.0,
        "source_language": "en",
        "target_language": "km",
        "speakers": [
            {
                "speaker_id": "speaker_1",
                "assigned_voice_id": "km-KH-PisethNeural",
                "speech_rate": 0,
            }
        ],
        "transcript": [
            {"id": 0, "start": 0.0, "end": 1.5, "text": "Hello world", "speaker_id": "speaker_1"}
        ],
        "translation": [
            {"id": 0, "start": 0.0, "end": 1.5, "text": "សួស្តីពិភពលោក", "speaker_id": "speaker_1"}
        ],
        "path": str(target_media),
        "stages": {},
    }
    save_job(job)

    try:
        # Mock generate_dubbed_audio_track to quickly write a test audio without external network TTS
        async def mock_generate_dubbed(segments, output_audio_path, **kwargs):
            # Verify original_media_path was passed as a valid Path or None
            assert "original_media_path" in kwargs
            orig_p = kwargs["original_media_path"]
            assert orig_p is not None
            assert Path(orig_p).exists()

            # Create dummy dubbed mp3
            output_audio_path.parent.mkdir(parents=True, exist_ok=True)
            cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=800:duration=1.5", "-c:a", "libmp3lame", str(output_audio_path)]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return output_audio_path

        with patch("app.main.generate_dubbed_audio_track", side_effect=mock_generate_dubbed):
            res = client.post(
                f"/api/jobs/{job_id}/dub",
                json={
                    "voice_id": "km-KH-PisethNeural",
                    "mix_original": True,
                    "voice_volume": 1.0,
                    "original_volume": 0.5,
                },
            )

        assert res.status_code == 200
        data = res.json()
        assert data["has_dubbed_audio"] is True
        assert data["stage"] == "completed"

        out_file = OUTPUT_DIR / f"{job_id}_dubbed.mp3"
        assert out_file.exists()
        assert out_file.stat().st_size > 500
    finally:
        delete_job(job_id)
        target_media.unlink(missing_ok=True)
        (OUTPUT_DIR / f"{job_id}_dubbed.mp3").unlink(missing_ok=True)


def test_dubbing_endpoint_when_media_missing_proceeds_safely(client):
    """
    Verifies that when media_path cannot be located, voice dubbing still synthesizes speech
    safely without UnboundLocalError crash.
    """
    job_id = "dubnomedia01"
    job = {
        "id": job_id,
        "filename": "missing.mp4",
        "name": "Missing Media Test",
        "status": "transcribed",
        "stage": "completed",
        "progress": 100,
        "message": "Ready",
        "duration_seconds": 2.0,
        "source_language": "en",
        "target_language": "km",
        "speakers": [],
        "transcript": [
            {"id": 0, "start": 0.0, "end": 1.5, "text": "Speech only", "speaker_id": "speaker_1"}
        ],
        "translation": [
            {"id": 0, "start": 0.0, "end": 1.5, "text": "និយាយតែប៉ុណ្ណោះ", "speaker_id": "speaker_1"}
        ],
        "path": "/nonexistent/developer/path/missing.mp4",
        "stages": {},
    }
    save_job(job)

    try:
        async def mock_generate_dubbed(segments, output_audio_path, **kwargs):
            # When media is missing, original_media_path is None and preserve_nonverbal is False
            assert kwargs.get("original_media_path") is None
            assert kwargs.get("preserve_nonverbal") is False
            output_audio_path.parent.mkdir(parents=True, exist_ok=True)
            cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=800:duration=1.5", "-c:a", "libmp3lame", str(output_audio_path)]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return output_audio_path

        with patch("app.main.generate_dubbed_audio_track", side_effect=mock_generate_dubbed):
            res = client.post(
                f"/api/jobs/{job_id}/dub",
                json={
                    "voice_id": "km-KH-PisethNeural",
                    "mix_original": True, # requested, but media is missing
                },
            )

        assert res.status_code == 200
        data = res.json()
        assert data["has_dubbed_audio"] is True
        assert data["stage"] == "completed"

        out_file = OUTPUT_DIR / f"{job_id}_dubbed.mp3"
        assert out_file.exists()
        assert out_file.stat().st_size > 500
    finally:
        delete_job(job_id)
        (OUTPUT_DIR / f"{job_id}_dubbed.mp3").unlink(missing_ok=True)
