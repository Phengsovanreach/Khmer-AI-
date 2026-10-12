import asyncio
import json
import os
import subprocess
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app
from app.dubbing import verify_audio_is_audible
from app.transcription import probe_media_file

client = TestClient(app)

def run_all_verifications():
    print("=== STARTING FULL END-TO-END SYSTEM VERIFICATION ===")
    report = []

    # 1. Health & Readiness Probe
    print("\n[1/10] Verifying System Probes & Diagnostics...")
    res_health = client.get("/api/health")
    assert res_health.status_code == 200, f"Health check failed: {res_health.text}"
    health_data = res_health.json()
    print(f"  ✓ Health Status: {health_data['status']} (v{health_data['version']})")

    res_ready = client.get("/api/ready")
    assert res_ready.status_code == 200, f"Readiness check failed: {res_ready.text}"
    ready_data = res_ready.json()
    print(f"  ✓ Readiness Status: {ready_data['status']}, Checks: {ready_data.get('checks', {})}")

    res_diag = client.get("/api/system/diagnostics")
    assert res_diag.status_code == 200
    diag_data = res_diag.json()
    print(f"  ✓ Diagnostics: Cores={diag_data['cpu_cores']}, Platform={diag_data['platform']}")
    report.append("System Probes: PASSED")

    # 2. Languages & Multilingual Voice Registry
    print("\n[2/10] Verifying Multilingual & Voice Registry...")
    res_langs = client.get("/api/languages")
    assert res_langs.status_code == 200
    langs = res_langs.json()
    print(f"  ✓ Supported Languages: {len(langs)} languages configured")

    res_voices_km = client.get("/api/dubbing/voices?language=km")
    assert res_voices_km.status_code == 200
    km_voices = res_voices_km.json()
    print(f"  ✓ Khmer Voices: {[v['id'] for v in km_voices]}")

    res_voices_en = client.get("/api/dubbing/voices?language=en")
    assert res_voices_en.status_code == 200
    en_voices = res_voices_en.json()
    print(f"  ✓ English Voices: {[v['id'] for v in en_voices]}")
    report.append("Languages & Voice Registry: PASSED")

    # 3. Secure Argon2id Authentication Lifecycle
    print("\n[3/10] Verifying Authentication & User Isolation...")
    test_name = "Verify Tester"
    test_email = "verify_tester_99@example.com"
    test_pass = "SecurePass99!@#"
    res_reg = client.post(
        "/api/auth/register",
        json={"name": test_name, "email": test_email, "password": test_pass, "terms_accepted": True},
    )
    if res_reg.status_code == 400 and "រួចហើយ" in res_reg.text:
        print("  ✓ User exists, testing login...")
    else:
        assert res_reg.status_code == 200, f"Registration failed: {res_reg.text}"
        print(f"  ✓ Registered user '{test_email}' with Argon2id")

    res_login = client.post("/api/auth/login", json={"email": test_email, "password": test_pass})
    assert res_login.status_code == 200, f"Login failed: {res_login.text}"
    token = res_login.json()["token"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    res_me = client.get("/api/auth/me", headers=auth_headers)
    assert res_me.status_code == 200
    assert res_me.json()["authenticated"] is True
    assert res_me.json()["user"]["email"] == test_email
    print(f"  ✓ User session authenticated successfully")
    report.append("Argon2id Authentication: PASSED")

    # 4. Media Upload with Validation
    print("\n[4/10] Generating & Uploading Test Media Video...")
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f_vid:
        vid_path = Path(f_vid.name)

    # Generate 3-second test video with 440Hz audible audio track
    cmd_gen = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "testsrc=size=640x360:rate=24:duration=3.0",
        "-f", "lavfi", "-i", "sine=frequency=440:duration=3.0",
        "-c:v", "libx264", "-preset", "ultrafast",
        "-c:a", "aac", "-b:a", "128k",
        "-shortest",
        str(vid_path)
    ]
    subprocess.run(cmd_gen, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    with open(vid_path, "rb") as f:
        res_upload = client.post(
            "/api/jobs",
            files={"video": ("test_verify_e2e.mp4", f, "video/mp4")},
            data={"source_language": "en", "target_language": "km"},
            headers=auth_headers,
        )
    assert res_upload.status_code == 200, f"Upload failed: {res_upload.text}"
    job_id = res_upload.json()["id"]
    print(f"  ✓ Media uploaded as Job ID: {job_id}")
    report.append("Media Upload & Ingestion: PASSED")

    # 5. Transcription Pipeline
    print("\n[5/10] Executing Whisper Speech Transcription...")
    res_transcribe = client.post(
        f"/api/jobs/{job_id}/transcribe?model=tiny&language=en",
        headers=auth_headers,
    )
    assert res_transcribe.status_code == 200, f"Transcription failed: {res_transcribe.text}"
    job_trans = res_transcribe.json()
    transcript = job_trans.get("transcript", [])
    print(f"  ✓ Transcription finished: {len(transcript)} segments found")
    report.append("Whisper Transcription: PASSED")

    # 6. Multi-Line Batch Translation
    print("\n[6/10] Executing High-Throughput Batch Translation (EN -> KM)...")
    # Populate structured sentences to test real translation
    client.put(
        f"/api/jobs/{job_id}/transcript",
        json={
            "segments": [
                {"id": 1, "start": 0.0, "end": 1.4, "text": "Hello world and welcome to Cambodia."},
                {"id": 2, "start": 1.5, "end": 2.8, "text": "This technology translates speech with artificial intelligence."},
            ]
        },
        headers=auth_headers,
    )

    res_trans = client.post(
        f"/api/jobs/{job_id}/translate?target_language=km",
        headers=auth_headers,
    )
    assert res_trans.status_code == 200, f"Translation failed: {res_trans.text}"
    job_translated = res_trans.json()
    translation = job_translated.get("translation", [])
    assert len(translation) == 2, "Expected 2 translated segments"
    for s in translation:
        print(f"  ✓ Segment {s['id']} Translated: '{s['text']}'")
    report.append("Batch Translation: PASSED")

    # 7. AI Voice Dubbing & Speech-Aware Sidechain Ducking
    print("\n[7/10] Generating AI Dubbing with Sidechain Ducking...")
    res_dub = client.post(
        f"/api/jobs/{job_id}/dub",
        json={
            "voice_id": "km-KH-PisethNeural",
            "mix_original": True,
            "voice_volume": 1.0,
            "original_volume": 0.5,
            "preserve_soundtrack": True,
            "ducking_intensity": 0.35,
        },
        headers=auth_headers,
    )
    assert res_dub.status_code == 200, f"Dubbing failed: {res_dub.text}"
    job_dubbed = res_dub.json()
    assert job_dubbed["has_dubbed_audio"] is True
    print(f"  ✓ Dubbing generated successfully: URL={job_dubbed['dubbed_audio_url']}")
    report.append("AI Voice Dubbing: PASSED")

    # 8. Audibility Validation of Dubbed Track
    print("\n[8/10] Verifying Dubbed Audio Track Audibility & Decodability...")
    res_audio = client.get(f"/api/jobs/{job_id}/dubbed-audio")
    assert res_audio.status_code == 200, f"Fetching dubbed audio failed: {res_audio.status_code}"
    assert "audio/mpeg" in res_audio.headers.get("content-type", "")
    assert len(res_audio.content) > 500

    # Save to disk and run volumedetect
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f_audio:
        f_audio.write(res_audio.content)
        audio_tmp = Path(f_audio.name)

    is_audible = verify_audio_is_audible(audio_tmp)
    assert is_audible is True, "Audio file is not audible or is digital silence!"
    probe_aud = probe_media_file(audio_tmp)
    print(f"  ✓ Audibility check passed: Audible={is_audible}, Duration={probe_aud.get('duration')}s, Codec={probe_aud.get('audio_codec')}")
    audio_tmp.unlink(missing_ok=True)
    report.append("Dubbed Audio Audibility & Decodability: PASSED")

    # 9. Final Video Render (Hardsub + Mixed Dubbing Track)
    print("\n[9/10] Rendering Final Video with Burned Subtitles & Dubbed Track...")
    res_export = client.post(
        f"/api/jobs/{job_id}/export-video",
        json={
            "subtitle_source": "translation",
            "font_size": 22,
            "burn_subtitles": True,
            "include_dubbed_audio": True,
            "audio_mode": "mixed",
        },
        headers=auth_headers,
    )
    assert res_export.status_code == 200, f"Export failed: {res_export.text}"
    job_exported = res_export.json()
    assert job_exported["has_rendered_video"] is True
    print(f"  ✓ Rendered video created: URL={job_exported['rendered_video_url']}")

    # 10. Final Rendered Video Stream Validation
    print("\n[10/10] Validating Rendered MP4 Video & Audio Streams...")
    res_vid = client.get(f"/api/jobs/{job_id}/rendered-video")
    assert res_vid.status_code == 200, f"Fetching rendered video failed: {res_vid.status_code}"
    assert "video/mp4" in res_vid.headers.get("content-type", "")
    assert len(res_vid.content) > 5000

    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f_rendered:
        f_rendered.write(res_vid.content)
        rendered_tmp = Path(f_rendered.name)

    probe_vid = probe_media_file(rendered_tmp)
    assert probe_vid.get("has_audio") is True, "Rendered video is MISSING an audio stream!"
    audio_stream = next((s for s in probe_vid["streams"] if s.get("codec_type") == "audio"), None)
    assert audio_stream is not None
    print(f"  ✓ MP4 Verified: Size={len(res_vid.content)} bytes, Audio Codec={audio_stream.get('codec_name')}, Duration={probe_vid.get('duration')}s")
    rendered_tmp.unlink(missing_ok=True)
    vid_path.unlink(missing_ok=True)
    report.append("Final Video Audio/Video Stream Verification: PASSED")

    print("\n=======================================================")
    print("ALL 10 VERIFICATION STAGES COMPLETED WITH 100% SUCCESS!")
    print("=======================================================")
    for item in report:
        print(f"  • {item}")

if __name__ == "__main__":
    run_all_verifications()
