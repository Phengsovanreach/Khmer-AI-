import pytest
import subprocess
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app
from app.storage import save_job, get_job, delete_job
from app.languages import get_source_languages, get_target_languages, get_language_by_code
from app.translation import translate_single_line
from app.dubbing import get_available_voices
from app.diarization import diarize_and_profile_audio

client = TestClient(app)


def test_languages_endpoint():
    res = client.get("/api/languages")
    assert res.status_code == 200
    data = res.json()
    assert "source_languages" in data
    assert "target_languages" in data
    assert len(data["source_languages"]) >= 20
    assert len(data["target_languages"]) >= 19

    # Check auto detect is present in source languages
    assert any(l["code"] == "auto" for l in data["source_languages"])
    # Check Khmer, English, Chinese, Japanese, Korean, French, Spanish are present
    codes = [l["code"] for l in data["target_languages"]]
    for expected in ["km", "en", "zh", "ja", "ko", "vi", "fr", "es", "de"]:
        assert expected in codes
    assert "th" not in codes


def test_multilingual_voices_endpoint():
    # Test Khmer voices
    km_res = client.get("/api/dubbing/voices?target_language=km")
    assert km_res.status_code == 200
    km_data = km_res.json()
    assert len(km_data) >= 2
    assert any(v["id"] == "km-KH-PisethNeural" for v in km_data)

    # Test English voices
    en_res = client.get("/api/dubbing/voices?target_language=en")
    assert en_res.status_code == 200
    en_data = en_res.json()
    assert len(en_data) >= 4
    assert any("Guy" in v["name"] for v in en_data)

    # Test Chinese voices
    zh_res = client.get("/api/dubbing/voices?target_language=zh")
    assert zh_res.status_code == 200
    zh_data = zh_res.json()
    assert len(zh_data) >= 2


def test_speaker_management_api():
    job_id = "test-spk-mgmt-job"
    try:
        initial_job = {
            "id": job_id,
            "filename": "test.mp4",
            "name": "Speaker Test",
            "status": "transcribed",
            "stage": "completed",
            "progress": 100,
            "source_language": "en",
            "target_language": "km",
            "speakers": [
                {
                    "id": "speaker_1",
                    "speaker_id": "speaker_1",
                    "name": "Speaker 1",
                    "gender_presentation": "masculine",
                    "age_impression": "adult",
                    "speaking_style": "conversational",
                    "speaking_speed": "normal",
                    "confidence": 0.9,
                    "assigned_voice_id": "km-KH-PisethNeural",
                    "segment_count": 2,
                    "total_duration": 4.0,
                    "sample_dialogue": ["Hello"],
                },
                {
                    "id": "speaker_2",
                    "speaker_id": "speaker_2",
                    "name": "Speaker 2",
                    "gender_presentation": "feminine",
                    "age_impression": "adult",
                    "speaking_style": "conversational",
                    "speaking_speed": "normal",
                    "confidence": 0.85,
                    "assigned_voice_id": "km-KH-SreymomNeural",
                    "segment_count": 1,
                    "total_duration": 2.0,
                    "sample_dialogue": ["Hi there"],
                },
            ],
            "transcript": [
                {"id": 1, "start": 0.0, "end": 2.0, "text": "Hello", "speaker_id": "speaker_1"},
                {"id": 2, "start": 2.5, "end": 4.5, "text": "Hi there", "speaker_id": "speaker_2"},
                {"id": 3, "start": 5.0, "end": 7.0, "text": "How are you?", "speaker_id": "speaker_1"},
            ],
            "translation": [],
        }
        save_job(initial_job)

        # 1. Test updating speaker profile (rename)
        updated_speakers = [
            {**initial_job["speakers"][0], "name": "Prof. Oak"},
            initial_job["speakers"][1],
        ]
        put_res = client.put(f"/api/jobs/{job_id}/speakers", json={"speakers": updated_speakers})
        assert put_res.status_code == 200
        spks = put_res.json()["speakers"]
        assert spks[0]["name"] == "Prof. Oak"

        # 2. Test merging speaker_2 into speaker_1
        merge_res = client.post(
            f"/api/jobs/{job_id}/speakers/merge",
            json={"speaker_id_keep": "speaker_1", "speaker_id_merge": "speaker_2"},
        )
        assert merge_res.status_code == 200
        m_job = merge_res.json()
        assert len(m_job["speakers"]) == 1
        # Check all segments now belong to speaker_1
        assert all(s["speaker_id"] == "speaker_1" for s in m_job["transcript"])

        # 3. Test splitting segment 2 into a new speaker
        split_res = client.post(
            f"/api/jobs/{job_id}/speakers/split",
            json={"segment_ids": [2], "new_speaker_name": "Narrator"},
        )
        assert split_res.status_code == 200
        s_job = split_res.json()
        assert len(s_job["speakers"]) == 2
        narrator = next(s for s in s_job["speakers"] if s["name"] == "Narrator")
        assert narrator["speaker_id"] == "speaker_2"
        # Segment 2 should have speaker_2
        assert s_job["transcript"][1]["speaker_id"] == "speaker_2"

    finally:
        delete_job(job_id)


def test_diarization_audio_processing(tmp_path):
    wav = tmp_path / "synthetic_dialogue.wav"
    # Create 4-second audio: 0-2s 130Hz male tone, 2-4s 220Hz female tone
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "sine=frequency=130:duration=2.0",
        "-f", "lavfi", "-i", "sine=frequency=220:duration=2.0",
        "-filter_complex", "[0:a][1:a]concat=n=2:v=0:a=1[out]",
        "-map", "[out]",
        "-ar", "16000", "-ac", "1",
        str(wav),
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    segments = [
        {"id": 1, "start": 0.2, "end": 1.8, "text": "Good morning everybody"},
        {"id": 2, "start": 2.2, "end": 3.8, "text": "Hello professor"},
    ]

    updated_segs, profiles = diarize_and_profile_audio(wav, segments, target_language="km")
    assert len(updated_segs) == 2
    assert "speaker_id" in updated_segs[0]
    assert "speaker_id" in updated_segs[1]
    # Check that the two segments are detected as distinct speakers
    assert updated_segs[0]["speaker_id"] != updated_segs[1]["speaker_id"]
    assert len(profiles) >= 2


def test_multilingual_translation_and_export():
    job_id = "test-multi-trans-job"
    try:
        job = {
            "id": job_id,
            "filename": "video.mp4",
            "name": "Translation Export Test",
            "status": "transcribed",
            "stage": "completed",
            "progress": 100,
            "source_language": "en",
            "target_language": "fr",
            "transcript": [
                {"id": 1, "start": 0.0, "end": 2.0, "text": "Good morning everyone", "speaker_id": "speaker_1"},
                {"id": 2, "start": 2.5, "end": 4.5, "text": "Welcome to the show", "speaker_id": "speaker_2"},
            ],
            "translation": [],
        }
        save_job(job)

        # Translate to French
        res = client.post(f"/api/jobs/{job_id}/translate?source_language=en&target_language=fr")
        assert res.status_code == 200
        data = res.json()
        assert len(data["translation"]) == 2
        assert data["target_language"] == "fr"
        # Verify speaker assignments preserved
        assert data["translation"][0]["speaker_id"] == "speaker_1"
        assert data["translation"][1]["speaker_id"] == "speaker_2"

        # Test exporting subtitles in target language
        srt_res = client.get(f"/api/jobs/{job_id}/subtitles.srt?lang=target")
        assert srt_res.status_code == 200
        assert "-->" in srt_res.text

        vtt_res = client.get(f"/api/jobs/{job_id}/subtitles.vtt?lang=target")
        assert vtt_res.status_code == 200
        assert "WEBVTT" in vtt_res.text

        # Test preview info
        prev_res = client.get(f"/api/jobs/{job_id}/preview-info")
        assert prev_res.status_code == 200
        prev_data = prev_res.json()
        assert prev_data["has_translation"] is True
        assert prev_data["target_language"] == "fr"
    finally:
        delete_job(job_id)


def test_story_aware_emotion_analysis():
    from app.emotion import analyze_dialogue_emotions, get_emotion_tts_adjustments

    # Sample dialogue with emotional turns
    segments = [
        {"id": 1, "start": 0.0, "end": 2.0, "text": "I can't believe we actually won the championship! Wow!", "speaker_id": "spk_1"},
        {"id": 2, "start": 2.5, "end": 4.5, "text": "This is terrible news, everything is lost and ruined.", "speaker_id": "spk_1"},
        {"id": 3, "start": 5.0, "end": 7.0, "text": "Be quiet! Don't let anyone hear us, speak softly.", "speaker_id": "spk_2"},
        {"id": 4, "start": 7.5, "end": 9.0, "text": "The meeting will start promptly at nine.", "speaker_id": "spk_2"},
        {"id": 5, "start": 25.0, "end": 28.0, "text": "The next morning, the report was submitted.", "speaker_id": "spk_2"},
    ]

    enriched = analyze_dialogue_emotions(segments)
    assert len(enriched) == 5

    # Segment 1 should be happy or excited
    assert enriched[0]["emotion"] in ["happy", "excited"]
    assert enriched[0]["emotion_confidence"] > 0.5
    assert enriched[0]["ssml_pitch"] is not None

    # Segment 2 should be sad or worried
    assert enriched[1]["emotion"] in ["sad", "worried"]

    # Segment 3 should be whispering
    assert enriched[2]["emotion"] == "whispering"

    # Segment 4 follows immediately from same speaker (<5s gap) -> retains conversational continuity (whispering)
    assert enriched[3]["emotion"] == "whispering"

    # Segment 5 is after a scene break (>15s gap) with factual tone -> resets to neutral
    assert enriched[4]["emotion"] in ["neutral", "calm", "serious"]


def test_emotion_tts_adjustments():
    from app.emotion import get_emotion_tts_adjustments

    rate, pitch, vol = get_emotion_tts_adjustments("excited", base_rate_pct=10)
    assert "+" in rate
    assert "+" in pitch

    rate_sad, pitch_sad, vol_sad = get_emotion_tts_adjustments("sad", base_rate_pct=0)
    assert "-" in rate_sad
    assert "-" in pitch_sad

    rate_whisp, pitch_whisp, vol_whisp = get_emotion_tts_adjustments("whispering", base_rate_pct=0)
    assert "-" in vol_whisp


