import subprocess
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.storage import delete_job, get_job, update_job
from app.config import OUTPUT_DIR, UPLOAD_DIR

client = TestClient(app)


def create_test_wav(filepath: Path, duration: float = 1.0):
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"sine=frequency=440:duration={duration}",
        "-ar", "16000", "-ac", "1",
        str(filepath),
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)


def test_preview_info_and_media_streaming(tmp_path):
    wav_path = tmp_path / "preview_sample.wav"
    create_test_wav(wav_path, duration=1.2)

    with open(wav_path, "rb") as f:
        res = client.post("/api/jobs", files={"video": ("preview_sample.wav", f, "audio/wav")})
    assert res.status_code == 200
    job_id = res.json()["id"]

    try:
        # Check media stream
        media_res = client.get(f"/api/jobs/{job_id}/media")
        assert media_res.status_code == 200
        assert "audio/wav" in media_res.headers.get("content-type", "")
        assert len(media_res.content) > 0

        # Check Range request support (HTTP 206)
        range_res = client.get(f"/api/jobs/{job_id}/media", headers={"Range": "bytes=0-99"})
        assert range_res.status_code == 206
        assert len(range_res.content) == 100

        # Check preview-info endpoint
        info_res = client.get(f"/api/jobs/{job_id}/preview-info")
        assert info_res.status_code == 200
        info = info_res.json()
        assert info["job_id"] == job_id
        assert info["has_media_file"] is True
        assert info["has_rendered_video"] is False
        assert info["rendered_video_url"] is None
        assert info["duration_seconds"] is not None

        # Rendered video endpoint should return 404 before export
        rendered_res = client.get(f"/api/jobs/{job_id}/rendered-video")
        assert rendered_res.status_code == 404
    finally:
        delete_job(job_id)


def test_vtt_subtitle_export(tmp_path):
    wav_path = tmp_path / "vtt_sample.wav"
    create_test_wav(wav_path, duration=1.0)

    with open(wav_path, "rb") as f:
        res = client.post("/api/jobs", files={"video": ("vtt_sample.wav", f, "audio/wav")})
    assert res.status_code == 200
    job_id = res.json()["id"]

    try:
        # Adding transcript segments
        update_job(job_id, {
            "transcript": [
                {"id": 1, "start": 0.0, "end": 0.5, "text": "Hello world"},
                {"id": 2, "start": 0.5, "end": 1.0, "text": "Khmer test"},
            ],
            "translation": [
                {"id": 1, "start": 0.0, "end": 0.5, "text": "សួស្តីពិភពលោក"},
                {"id": 2, "start": 0.5, "end": 1.0, "text": "តេស្តភាសាខ្មែរ"},
            ],
        })

        # Test source VTT
        vtt_src = client.get(f"/api/jobs/{job_id}/subtitles.vtt?translated=false")
        assert vtt_src.status_code == 200
        assert "text/vtt" in vtt_src.headers.get("content-type", "")
        assert "WEBVTT" in vtt_src.text
        assert "00:00:00.000 --> 00:00:00.500" in vtt_src.text
        assert "Hello world" in vtt_src.text

        # Test Khmer translation VTT
        vtt_km = client.get(f"/api/jobs/{job_id}/subtitles.vtt?translated=true")
        assert vtt_km.status_code == 200
        assert "WEBVTT" in vtt_km.text
        assert "សួស្តីពិភពលោក" in vtt_km.text
    finally:
        delete_job(job_id)


def test_export_rendered_video_and_download(tmp_path):
    wav_path = tmp_path / "render_sample.wav"
    create_test_wav(wav_path, duration=1.0)

    with open(wav_path, "rb") as f:
        res = client.post("/api/jobs", files={"video": ("render_sample.wav", f, "audio/wav")})
    assert res.status_code == 200
    job_id = res.json()["id"]

    try:
        # Populate translation
        update_job(job_id, {
            "status": "transcribed",
            "transcript": [{"id": 1, "start": 0.0, "end": 0.9, "text": "Test speech"}],
            "translation": [{"id": 1, "start": 0.0, "end": 0.9, "text": "សាកល្បងភាសាខ្មែរ"}],
        })

        # Trigger video export with burned subtitles
        export_res = client.post(f"/api/jobs/{job_id}/export-video", json={
            "subtitle_source": "translation",
            "font_size": 22,
            "burn_subtitles": True,
            "include_dubbed_audio": False,
            "audio_mode": "original",
        })
        assert export_res.status_code == 200
        job_data = export_res.json()
        assert job_data["has_rendered_video"] is True
        assert job_data["rendered_video_url"] == f"/api/jobs/{job_id}/rendered-video"

        # Now GET rendered-video should succeed
        video_res = client.get(f"/api/jobs/{job_id}/rendered-video")
        assert video_res.status_code == 200
        assert "video/mp4" in video_res.headers.get("content-type", "")
        assert len(video_res.content) > 0

        # With download=true query param
        dl_res = client.get(f"/api/jobs/{job_id}/rendered-video?download=true")
        assert dl_res.status_code == 200
        assert "attachment" in dl_res.headers.get("content-disposition", "")
        assert ".mp4" in dl_res.headers.get("content-disposition", "")

        # Preview-info should now show has_rendered_video=True
        info_res = client.get(f"/api/jobs/{job_id}/preview-info")
        assert info_res.status_code == 200
        assert info_res.json()["has_rendered_video"] is True
        assert info_res.json()["rendered_video_size_bytes"] is not None
        assert info_res.json()["rendered_video_size_bytes"] > 0
    finally:
        delete_job(job_id)


def test_path_traversal_protection():
    # Attempting to access arbitrary system paths via job_id
    bad_id = "../../../../etc/passwd"
    res = client.get(f"/api/jobs/{bad_id}/media")
    assert res.status_code in (400, 404)
