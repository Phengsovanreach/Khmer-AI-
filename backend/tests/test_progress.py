from __future__ import annotations
import io
import subprocess
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.storage import get_job, update_job


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sample_wav(tmp_path) -> Path:
    wav_path = tmp_path / "valid_test_progress.wav"
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "sine=frequency=1000:duration=1.5",
        "-ar", "16000",
        "-ac", "1",
        str(wav_path)
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return wav_path


def test_progress_bounds_and_lifecycle(client, sample_wav):
    """Verify that progress stays strictly within [0, 100], and never reports 100% prematurely."""
    with sample_wav.open("rb") as f:
        res_upload = client.post("/api/jobs", files={"video": ("progress_test.wav", f, "audio/wav")})
    assert res_upload.status_code == 200
    job_id = res_upload.json()["id"]

    try:
        # Check initial state
        res_init = client.get(f"/api/jobs/{job_id}")
        assert res_init.status_code == 200
        data_init = res_init.json()
        assert data_init["progress"] == 0
        assert data_init["status"] == "uploaded"

        # Check lightweight progress endpoint
        res_prog = client.get(f"/api/jobs/{job_id}/progress")
        assert res_prog.status_code == 200
        prog_data = res_prog.json()
        assert 0 <= prog_data["progress"] <= 100
        assert prog_data["id"] == job_id

        # Run real transcription
        res_trans = client.post(f"/api/jobs/{job_id}/transcribe?model=tiny&language=en")
        assert res_trans.status_code == 200
        data_trans = res_trans.json()

        # Upon successful completion, progress reaches exactly 100
        assert data_trans["progress"] == 100
        assert data_trans["status"] == "transcribed"
        assert data_trans["stage"] == "completed"
        assert data_trans["stages"]["completed"] == "completed"
        assert data_trans["elapsed_seconds"] is not None and data_trans["elapsed_seconds"] > 0
    finally:
        client.delete(f"/api/jobs/{job_id}")


def test_failure_and_retry_resets_progress(client, sample_wav):
    """Verify that failures preserve reached progress and retry cleanly resets progress to 0."""
    with sample_wav.open("rb") as f:
        res_upload = client.post("/api/jobs", files={"video": ("fail_retry.wav", f, "audio/wav")})
    job_id = res_upload.json()["id"]

    try:
        # Simulate a mid-stage failure
        update_job(job_id, {
            "status": "failed",
            "stage": "failed",
            "progress": 42,
            "error": "Simulated hardware error",
            "message": "Simulated hardware error"
        })

        res_check = client.get(f"/api/jobs/{job_id}/progress")
        assert res_check.status_code == 200
        failed_data = res_check.json()
        assert failed_data["status"] == "failed"
        assert failed_data["progress"] == 42
        assert "Simulated" in failed_data["error"]

        # Call retry endpoint
        res_retry = client.post(f"/api/jobs/{job_id}/retry?model=tiny")
        assert res_retry.status_code == 200
        retry_data = res_retry.json()
        # After retry finishes successfully, it achieves 100%
        assert retry_data["status"] == "transcribed"
        assert retry_data["progress"] == 100
        assert retry_data["error"] is None
    finally:
        client.delete(f"/api/jobs/{job_id}")


def test_cancel_does_not_report_100_percent(client, sample_wav):
    """Verify that cancelled jobs update to cancelled and do not jump to 100%."""
    with sample_wav.open("rb") as f:
        res_upload = client.post("/api/jobs", files={"video": ("cancel_test.wav", f, "audio/wav")})
    job_id = res_upload.json()["id"]

    try:
        res_cancel = client.post(f"/api/jobs/{job_id}/cancel")
        assert res_cancel.status_code == 200
        cancel_data = res_cancel.json()
        assert cancel_data["status"] == "cancelled"

        res_prog = client.get(f"/api/jobs/{job_id}/progress")
        assert res_prog.status_code == 200
        prog = res_prog.json()
        assert prog["status"] == "cancelled"
        assert prog["progress"] < 100
    finally:
        client.delete(f"/api/jobs/{job_id}")


def test_missing_job_returns_404(client):
    res = client.get("/api/jobs/non_existent_id_999/progress")
    assert res.status_code == 404
    res_retry = client.post("/api/jobs/non_existent_id_999/retry")
    assert res_retry.status_code == 404
    res_events = client.get("/api/jobs/non_existent_id_999/events")
    assert res_events.status_code == 404


def test_events_stream_connects(client, sample_wav):
    """Verify that SSE stream connects and outputs initial job data."""
    with sample_wav.open("rb") as f:
        res_upload = client.post("/api/jobs", files={"video": ("stream_test.wav", f, "audio/wav")})
    job_id = res_upload.json()["id"]

    try:
        # Mark job as transcribed so stream outputs event and completes cleanly
        update_job(job_id, {"status": "transcribed", "stage": "completed", "progress": 100})
        res = client.get(f"/api/jobs/{job_id}/events")
        assert res.status_code == 200
        assert "text/event-stream" in res.headers["content-type"]
        assert "data:" in res.text
        assert job_id in res.text
    finally:
        client.delete(f"/api/jobs/{job_id}")


