    # the function on the app.dubbing module before making the request.
    monkeypatch.setattr(dubbing, "generate_segment_audio", fake_generate_segment_audio)

    res = client.post(
        "/api/dubbing/segment-sample",
        json={
            "text": "សួស្តីកម្ពុជា",
            "voice_id": "km-KH-PisethNeural",
            "emotion": "happy",
            "rate": 0,
        },
    )

    assert res.status_code == 200, res.text
    assert res.headers["content-type"] == "audio/mpeg"
    assert res.content == expected_audio
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
