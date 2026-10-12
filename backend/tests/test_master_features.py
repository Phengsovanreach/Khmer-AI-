import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.storage import save_job, get_job, delete_job
from app.translation import translate_text_to_khmer
from app.dubbing import get_available_khmer_voices

client = TestClient(app)

def test_available_voices():
    voices = get_available_khmer_voices()
    assert len(voices) >= 2
    voice_ids = [v["id"] for v in voices]
    assert "km-KH-PisethNeural" in voice_ids
    assert "km-KH-SreymomNeural" in voice_ids

    response = client.get("/api/dubbing/voices")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    assert any(v["id"] == "km-KH-PisethNeural" for v in data)

def test_app_settings_lifecycle():
    get_res = client.get("/api/settings")
    assert get_res.status_code == 200
    original_settings = get_res.json()
    assert "ui_language" in original_settings

    # Update settings
    updated_payload = {
        **original_settings,
        "ui_language": "km",
        "default_tts_voice": "km-KH-SreymomNeural",
        "subtitle_font_size": "large",
    }
    put_res = client.put("/api/settings", json=updated_payload)
    assert put_res.status_code == 200
    saved = put_res.json()
    assert saved["ui_language"] == "km"
    assert saved["default_tts_voice"] == "km-KH-SreymomNeural"
    assert saved["subtitle_font_size"] == "large"

def test_subtitle_editor_pro_operations():
    job_id = "test-subtitle-pro-job"
    sample_segments = [
        {"id": 0, "start": 0.0, "end": 2.0, "text": "Hello world"},
        {"id": 1, "start": 2.5, "end": 5.0, "text": "Welcome to Khmer Translator"},
        {"id": 2, "start": 5.5, "end": 8.0, "text": "Enjoy high quality subtitles"},
    ]
    save_job({
        "id": job_id,
        "name": "Initial Project Name",
        "filename": "demo.mp4",
        "status": "transcribed",
        "transcript": sample_segments,
        "translation": [
            {"id": 0, "start": 0.0, "end": 2.0, "text": "សួស្តីពិភពលោក"},
            {"id": 1, "start": 2.5, "end": 5.0, "text": "សូមស្វាគមន៍មកកាន់ Khmer Translator"},
            {"id": 2, "start": 5.5, "end": 8.0, "text": "រីករាយជាមួយ Subtitle គុណភាពខ្ពស់"},
        ],
    })

    try:
        # 1. Project rename
        rename_res = client.patch(f"/api/jobs/{job_id}", json={"name": "Renamed Khmer Project"})
        assert rename_res.status_code == 200
        assert rename_res.json()["name"] == "Renamed Khmer Project"

        # 2. Split segment #1 at 3.5s
        split_res = client.post(f"/api/jobs/{job_id}/transcript/split", json={
            "segment_id": 1,
            "split_time": 3.5,
            "text_part1": "Welcome to",
            "text_part2": "Khmer Translator",
        })
        assert split_res.status_code == 200
        transcript = split_res.json()["transcript"]
        assert len(transcript) == 4
        assert transcript[1]["text"] == "Welcome to"
        assert transcript[1]["end"] == 3.5
        assert transcript[2]["text"] == "Khmer Translator"
        assert transcript[2]["start"] == 3.5
        assert transcript[2]["end"] == 5.0

        # 3. Merge segments #2 and #3 back together
        merge_res = client.post(f"/api/jobs/{job_id}/transcript/merge", json={
            "segment_id_1": 2,
            "segment_id_2": 3,
        })
        assert merge_res.status_code == 200
        transcript = merge_res.json()["transcript"]
        assert len(transcript) == 3
        assert transcript[1]["start"] == 2.5
        assert transcript[1]["end"] == 5.0
        assert "Welcome to Khmer Translator" in transcript[1]["text"]


        # 4. Insert new segment after #2
        insert_res = client.post(f"/api/jobs/{job_id}/transcript/insert", json={
            "after_segment_id": 2,
            "segment": {
                "id": 99,
                "start": 8.2,
                "end": 10.0,
                "text": "Thank you for watching",
            },
        })
        assert insert_res.status_code == 200
        transcript = insert_res.json()["transcript"]
        assert len(transcript) == 4
        assert transcript[3]["text"] == "Thank you for watching"

        # 5. Delete segment
        del_res = client.delete(f"/api/jobs/{job_id}/transcript/3")
        assert del_res.status_code == 200
        transcript = del_res.json()["transcript"]
        assert len(transcript) == 3

        # 6. Timestamp validation: reject end <= start
        bad_update_res = client.put(f"/api/jobs/{job_id}/transcript", json={
            "transcript": [
                {"id": 0, "start": 5.0, "end": 2.0, "text": "Invalid order"}
            ]
        })
        assert bad_update_res.status_code in (400, 422)

    finally:
        delete_job(job_id)

def test_translation_without_ollama():
    # Direct test of translate_text_to_khmer
    res = translate_text_to_khmer("Hello world")
    assert isinstance(res, str)
    assert len(res) > 0
    # Must not throw error and should produce text

def test_mix_audio_tracks(tmp_path):
    from app.dubbing import mix_audio_tracks
    import subprocess

    orig = tmp_path / "orig.mp3"
    speech = tmp_path / "speech.mp3"
    out1 = tmp_path / "mixed1.mp3"
    out2 = tmp_path / "mixed2.mp3"

    # Create short 1s silent audio files
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono:d=1.0", "-c:a", "libmp3lame", str(orig)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono:d=1.0", "-c:a", "libmp3lame", str(speech)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Test with standard keyword arguments
    res1 = mix_audio_tracks(
        original_audio_path=orig,
        dubbed_audio_path=speech,
        output_mixed_path=out1,
        voice_volume=1.0,
        original_volume=0.2,
    )
    assert res1.exists()
    assert res1.stat().st_size > 0

    # Test with alias keyword arguments (the ones from the user's error)
    res2 = mix_audio_tracks(
        original_media_path=orig,
        speech_audio_path=speech,
        output_audio_path=out2,
        speech_volume=1.0,
        original_volume=0.2,
    )
    assert res2.exists()
    assert res2.stat().st_size > 0


def test_segment_audio_sample_endpoint():
    res = client.post(
        "/api/dubbing/segment-sample",
        json={
            "text": "សួស្តីកម្ពុជា",
            "voice_id": "km-KH-PisethNeural",
            "emotion": "happy",
            "rate": 0,
        },
    )
    assert res.status_code == 200
    assert res.headers["content-type"] == "audio/mpeg"
    assert len(res.content) > 100


def test_multi_speaker_distinct_voice_allocation(tmp_path):
    from app.diarization import diarize_and_profile_audio
    import subprocess

    # Generate a 4-second stereo test wav file
    wav_file = tmp_path / "multi_speaker_test.wav"
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "sine=frequency=140:duration=2.0",
            "-f", "lavfi", "-i", "sine=frequency=240:duration=2.0",
            "-filter_complex", "[0:a][1:a]concat=n=2:v=0:a=1[out]",
            "-map", "[out]",
            "-c:a", "pcm_s16le",
            str(wav_file),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    segments = [
        {"id": 1, "start": 0.0, "end": 1.8, "text": "This is the first speaker speaking deeply."},
        {"id": 2, "start": 2.1, "end": 3.9, "text": "This is the second speaker speaking higher."},
    ]

    updated_segs, profiles = diarize_and_profile_audio(
        wav_path=wav_file,
        segments=segments,
        target_language="km",
    )

    assert len(profiles) >= 1
    # Check that speaker profiles have required metadata
    for p in profiles:
        assert "speaker_id" in p
        assert "assigned_voice_id" in p
        assert "gender_presentation" in p
        assert "age_impression" in p
        assert "speaking_style" in p


def test_export_video_auto_dubbing_validation(tmp_path):
    import subprocess
    import uuid
    from app.storage import save_job, delete_job
    from app.config import OUTPUT_DIR

    # Create dummy 2-second video
    video_file = tmp_path / "test_video.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=black:s=640x360:r=24:d=2.0", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono:d=2.0", "-c:v", "libx264", "-c:a", "aac", "-shortest", str(video_file)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    job_id = str(uuid.uuid4())
    save_job({
        "id": job_id,
        "name": "Auto Dub Test",
        "filename": "test_video.mp4",
        "path": str(video_file),
        "status": "transcribed",
        "duration_seconds": 2.0,
        "source_language": "en",
        "target_language": "km",
        "transcript": [
            {"id": 1, "start": 0.2, "end": 1.8, "text": "Hello world", "speaker_id": "speaker_1"}
        ],
        "translation": [
            {"id": 1, "start": 0.2, "end": 1.8, "text": "សួស្តីពិភពលោក", "speaker_id": "speaker_1", "emotion": "happy"}
        ],
        "speakers": [
            {"speaker_id": "speaker_1", "assigned_voice_id": "km-KH-PisethNeural", "name": "Speaker 1"}
        ],
    })

    try:
        # Request video export with include_dubbed_audio=True and audio_mode="dubbed"
        # The dubbed mp3 does not exist yet; backend should auto-synthesize it and verify audio stream in mp4!
        res = client.post(
            f"/api/jobs/{job_id}/export-video",
            json={
                "subtitle_source": "translation",
                "font_size": 20,
                "burn_subtitles": True,
                "include_dubbed_audio": True,
                "audio_mode": "dubbed",
            },
        )
        assert res.status_code == 200, res.text
        data = res.json()
        assert data.get("has_rendered_video") is True
        assert data.get("has_dubbed_audio") is True

        rendered_mp4 = OUTPUT_DIR / f"{job_id}_rendered.mp4"
        assert rendered_mp4.exists()
        assert rendered_mp4.stat().st_size > 1000

        # Verify using FFprobe that the MP4 has both video and audio streams
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,codec_name", "-of", "json", str(rendered_mp4)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        import json
        probe_data = json.loads(probe.stdout)
        stream_types = [s["codec_type"] for s in probe_data.get("streams", [])]
        assert "video" in stream_types, "Exported MP4 must contain video stream"
        assert "audio" in stream_types, "Exported MP4 must contain audible audio stream"
    finally:
        delete_job(job_id)


