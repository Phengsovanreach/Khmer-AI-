from __future__ import annotations
import math
import subprocess
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.storage import delete_job


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sample_media(tmp_path) -> Path:
    wav_path = tmp_path / "chunked_sample.wav"
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "sine=frequency=800:duration=2.0",
        "-ar", "16000",
        "-ac", "1",
        str(wav_path)
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return wav_path


def test_chunked_upload_full_flow(client, sample_media):
    data = sample_media.read_bytes()
    file_size = len(data)
    chunk_size = math.ceil(file_size / 3)
    total_chunks = math.ceil(file_size / chunk_size)

    # 1. Init
    init_res = client.post("/api/upload/init", json={
        "filename": "chunked_sample.wav",
        "file_size": file_size,
        "chunk_size": chunk_size,
        "total_chunks": total_chunks,
        "source_language": "en",
        "target_language": "km",
        "name": "Test Chunked Project",
    })
    assert init_res.status_code == 200, init_res.text
    init_data = init_res.json()
    upload_id = init_data["upload_id"]
    assert init_data["total_chunks"] == total_chunks

    # 2. Upload chunks in loop
    for idx in range(total_chunks):
        chunk_slice = data[idx * chunk_size : (idx + 1) * chunk_size]
        res = client.post(
            "/api/upload/chunk",
            data={"upload_id": upload_id, "chunk_index": idx},
            files={"chunk": (f"chunk_{idx}.part", chunk_slice, "application/octet-stream")},
        )
        assert res.status_code == 200, res.text
        chunk_res = res.json()
        assert idx in chunk_res["uploaded_chunks"]

    # 3. Check status
    status_res = client.get(f"/api/upload/status/{upload_id}")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert len(status_data["uploaded_chunks"]) == total_chunks
    assert status_data["uploaded_bytes"] == file_size

    # 4. Complete
    comp_res = client.post("/api/upload/complete", data={"upload_id": upload_id})
    assert comp_res.status_code == 200, comp_res.text
    job_data = comp_res.json()
    assert job_data["status"] == "uploaded"
    assert job_data["duration_seconds"] > 1.0
    assert job_data["name"] == "Test Chunked Project"

    # Cleanup
    delete_job(job_data["id"])


def test_chunked_upload_resume_and_cancel(client, sample_media):
    data = sample_media.read_bytes()
    file_size = len(data)
    chunk_size = math.ceil(file_size / 3)
    total_chunks = math.ceil(file_size / chunk_size)

    init_res = client.post("/api/upload/init", json={
        "filename": "resumable.wav",
        "file_size": file_size,
        "chunk_size": chunk_size,
        "total_chunks": total_chunks,
    })
    assert init_res.status_code == 200
    upload_id = init_res.json()["upload_id"]

    # Upload only chunk 0
    chunk_0 = data[0:chunk_size]
    res_0 = client.post(
        "/api/upload/chunk",
        data={"upload_id": upload_id, "chunk_index": 0},
        files={"chunk": ("chunk_0.part", chunk_0, "application/octet-stream")},
    )
    assert res_0.status_code == 200

    # Query status (resuming query)
    status_res = client.get(f"/api/upload/status/{upload_id}")
    assert status_res.status_code == 200
    assert status_res.json()["uploaded_chunks"] == [0]

    # Cancel upload session
    del_res = client.delete(f"/api/upload/{upload_id}")
    assert del_res.status_code == 200
    assert del_res.json()["upload_id"] == upload_id

    # Confirm session is deleted
    status_after = client.get(f"/api/upload/status/{upload_id}")
    assert status_after.status_code == 404


def test_direct_upload_endpoint(client, sample_media):
    with sample_media.open("rb") as f:
        res = client.post("/api/upload", files={"file": ("direct_test.wav", f, "audio/wav")})
    assert res.status_code == 200
    job = res.json()
    assert job["filename"] == "direct_test.wav"
    delete_job(job["id"])


def test_upload_validation_errors(client):
    # Invalid extension
    bad_ext = client.post("/api/upload/init", json={
        "filename": "malware.exe",
        "file_size": 1024,
        "total_chunks": 1,
    })
    assert bad_ext.status_code == 400
    assert "Unsupported media extension" in bad_ext.json()["detail"]

    # Zero file size
    zero_size = client.post("/api/upload/init", json={
        "filename": "empty.mp4",
        "file_size": 0,
        "total_chunks": 1,
    })
    assert zero_size.status_code == 400


def test_upload_duration_exceeding_2_hours_rejected(client, tmp_path, monkeypatch):
    """Verifies that uploaded videos exceeding 2 hours (7200s) are rejected with a clear 400 error."""
    import app.main as main_mod

    # Mock ffprobe to return a video duration of 7201 seconds (over 2 hours)
    def mock_probe_media_file(path):
        return {
            "duration": 7201.0,
            "has_audio": True,
            "has_video": True,
            "size": 1024,
            "format_name": "mov,mp4,m4a,3gp,3g2,mj2",
        }

    monkeypatch.setattr(main_mod, "probe_media_file", mock_probe_media_file)

    test_file = tmp_path / "long_video.mp4"
    test_file.write_bytes(b"dummy video content")

    with test_file.open("rb") as f:
        res = client.post("/api/upload", files={"file": ("long_video.mp4", f, "video/mp4")})

    assert res.status_code == 400
    assert "2 ម៉ោង" in res.json()["detail"] or "7200" in res.json()["detail"]

