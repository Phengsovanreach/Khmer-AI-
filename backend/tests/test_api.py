from __future__ import annotations
import io
import subprocess
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.transcription import (
    build_srt_content,
    build_txt_content,
    format_srt_timestamp,
    AVAILABLE_MODELS,
)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sample_wav(tmp_path) -> Path:
    """Generate a real 1-second valid WAV audio file using ffmpeg."""
    wav_path = tmp_path / "valid_test.wav"
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "sine=frequency=1000:duration=1.0",
        "-ar", "16000",
        "-ac", "1",
        str(wav_path)
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return wav_path


# 1. Health endpoint test
def test_health_endpoint(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "app" in data


# 2. Model listing endpoint test
def test_transcription_models_endpoint(client):
    res = client.get("/api/transcription/models")
    assert res.status_code == 200
    data = res.json()
    assert "models" in data
    assert data["default_model"] == "tiny"
    model_ids = [m["id"] for m in data["models"]]
    assert "tiny" in model_ids
    assert "base" in model_ids
    # Verify RAM metadata
    tiny_model = next(m for m in data["models"] if m["id"] == "tiny")
    assert tiny_model["estimated_ram_mb"] <= 500


# 3. Capabilities endpoint test
def test_capabilities_endpoint(client):
    res = client.get("/api/capabilities")
    assert res.status_code == 200
    data = res.json()
    assert data["ffmpeg"] is True
    assert data["ffprobe"] is True
    assert data["faster_whisper"] is True
    assert "tiny" in data["available_models"]


# 4. Missing upload test
def test_missing_upload(client):
    res = client.post("/api/jobs")
    assert res.status_code in (400, 422)


# 5. Empty upload (0 bytes) test
def test_empty_upload(client):
    files = {"video": ("empty.wav", io.BytesIO(b""), "audio/wav")}
    res = client.post("/api/jobs", files=files)
    assert res.status_code == 400
    assert "empty" in res.json()["detail"].lower()


# 6. Unsupported extension test
def test_unsupported_extension(client):
    files = {"video": ("test.txt", io.BytesIO(b"hello world"), "text/plain")}
    res = client.post("/api/jobs", files=files)
    assert res.status_code == 400
    assert "unsupported" in res.json()["detail"].lower()


# 7. Corrupted media test (ffprobe rejection)
def test_corrupted_media_upload(client):
    files = {"video": ("corrupted.mp4", io.BytesIO(b"not a real video file content"), "video/mp4")}
    res = client.post("/api/jobs", files=files)
    assert res.status_code == 400
    assert "validation failed" in res.json()["detail"].lower()


# 8. Successful upload with real audio fixture
def test_successful_media_upload(client, sample_wav):
    with sample_wav.open("rb") as f:
        res = client.post("/api/jobs", files={"video": ("test.wav", f, "audio/wav")})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "uploaded"
    assert data["filename"] == "test.wav"
    assert data["duration_seconds"] is not None
    assert round(data["duration_seconds"], 1) == 1.0
    job_id = data["id"]

    # Verify retrieval
    res_get = client.get(f"/api/jobs/{job_id}")
    assert res_get.status_code == 200
    assert res_get.json()["id"] == job_id

    # Clean up
    del_res = client.delete(f"/api/jobs/{job_id}")
    assert del_res.status_code == 200


# 9. Real transcription integration test
def test_real_transcription_integration(client, sample_wav):
    with sample_wav.open("rb") as f:
        res_upload = client.post("/api/jobs", files={"video": ("speech_test.wav", f, "audio/wav")})
    assert res_upload.status_code == 200
    job_id = res_upload.json()["id"]

    try:
        # Transcribe with tiny model
        res_transcribe = client.post(f"/api/jobs/{job_id}/transcribe?model=tiny&language=en")
        assert res_transcribe.status_code == 200
        data = res_transcribe.json()
        assert data["status"] == "transcribed"
        assert data["model_used"] == "tiny"
        assert data["source_language"] == "en"
        assert isinstance(data["transcript"], list)

        # Check job result endpoint
        res_result = client.get(f"/api/transcription/jobs/{job_id}/result")
        assert res_result.status_code == 200
        assert res_result.json()["status"] == "transcribed"
    finally:
        client.delete(f"/api/jobs/{job_id}")


# 10. SRT formatting unit tests with Khmer Unicode
def test_srt_formatting():
    # Test timestamp converter
    assert format_srt_timestamp(0.0) == "00:00:00,000"
    assert format_srt_timestamp(65.123) == "00:01:05,123"
    assert format_srt_timestamp(3661.045) == "01:01:01,045"

    # Test segments with Khmer text
    segments = [
        {"id": 1, "start": 0.5, "end": 2.75, "text": "សួស្តីបងប្អូនទាំងអស់គ្នា"},
        {"id": 2, "start": 3.0, "end": 5.25, "text": "សូមស្វាគមន៍មកកាន់ Khmer Translator"},
    ]
    srt = build_srt_content(segments)
    assert "1\n00:00:00,500 --> 00:00:02,750\nសួស្តីបងប្អូនទាំងអស់គ្នា" in srt
    assert "2\n00:00:03,000 --> 00:00:05,250\nសូមស្វាគមន៍មកកាន់ Khmer Translator" in srt

    # Test plain text
    txt = build_txt_content(segments, include_timestamps=True)
    assert "[00:00:00,500] សួស្តីបងប្អូនទាំងអស់គ្នា" in txt


# 11. Transcript edit and SRT export endpoints
def test_transcript_edit_and_export(client, sample_wav):
    with sample_wav.open("rb") as f:
        res_upload = client.post("/api/jobs", files={"video": ("test_export.wav", f, "audio/wav")})
    job_id = res_upload.json()["id"]

    try:
        # Edit transcript with Khmer Unicode text
        edited_segments = [
            {"id": 1, "start": 0.0, "end": 1.0, "text": "អរគុណច្រើនដែលបានប្រើប្រាស់ប្រព័ន្ធនេះ"}
        ]
        res_update = client.put(f"/api/jobs/{job_id}/transcript", json={"segments": edited_segments})
        assert res_update.status_code == 200
        assert res_update.json()["transcript"][0]["text"] == "អរគុណច្រើនដែលបានប្រើប្រាស់ប្រព័ន្ធនេះ"

        # Export SRT
        res_srt = client.get(f"/api/jobs/{job_id}/subtitles.srt")
        assert res_srt.status_code == 200
        assert "00:00:00,000 --> 00:00:01,000" in res_srt.text
        assert "អរគុណច្រើនដែលបានប្រើប្រាស់ប្រព័ន្ធនេះ" in res_srt.text

        # Export TXT
        res_txt = client.get(f"/api/jobs/{job_id}/transcript.txt")
        assert res_txt.status_code == 200
        assert "អរគុណច្រើនដែលបានប្រើប្រាស់ប្រព័ន្ធនេះ" in res_txt.text
    finally:
        client.delete(f"/api/jobs/{job_id}")


# 12. Safe cancellation test
def test_job_cancellation(client, sample_wav):
    with sample_wav.open("rb") as f:
        res_upload = client.post("/api/jobs", files={"video": ("test_cancel.wav", f, "audio/wav")})
    job_id = res_upload.json()["id"]

    try:
        res_cancel = client.post(f"/api/jobs/{job_id}/cancel")
        assert res_cancel.status_code == 200
        assert res_cancel.json()["status"] == "cancelled"
    finally:
        client.delete(f"/api/jobs/{job_id}")
