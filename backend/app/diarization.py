from __future__ import annotations
import logging
import math
import wave
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


def extract_pcm_samples(wav_path: Path) -> tuple[np.ndarray, int]:
    """Reads 16-bit mono or stereo PCM audio into float32 array in [-1.0, 1.0]."""
    with wave.open(str(wav_path), "rb") as wf:
        n_channels = wf.getnchannels()
        sr = wf.getframerate()
        n_frames = wf.getnframes()
        raw = wf.readframes(n_frames)
        samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
        if n_channels > 1:
            samples = samples.reshape(-1, n_channels).mean(axis=1)
        return samples, sr


def _estimate_frame_f0(frame: np.ndarray, sr: int = 16000) -> float:
    """Estimates fundamental frequency (F0) using normalized autocorrelation."""
    frame = frame - np.mean(frame)
    energy = np.sum(frame**2)
    if energy < 1e-4:
        return 0.0

    corr = np.correlate(frame, frame, mode="full")
    corr = corr[len(corr) // 2 :]
    if corr[0] <= 0:
        return 0.0
    norm_corr = corr / corr[0]

    # Human voice pitch search range: 75 Hz to 380 Hz
    min_lag = int(sr / 380)
    max_lag = int(sr / 75)
    if max_lag >= len(norm_corr):
        max_lag = len(norm_corr) - 1
    if min_lag >= max_lag:
        return 0.0

    peak_lag = min_lag + int(np.argmax(norm_corr[min_lag:max_lag]))
    peak_val = norm_corr[peak_lag]

    # Threshold for voiced frame
    if peak_val > 0.35 and peak_lag > 0:
        return float(sr / peak_lag)
    return 0.0


def extract_segment_features(samples: np.ndarray, sr: int = 16000) -> dict[str, Any]:
    """Computes acoustic features for a dialogue segment."""
    if len(samples) < 512:
        return {
            "f0_median": 150.0,
            "f0_std": 0.0,
            "spectral_centroid": 1500.0,
            "energy": 0.01,
            "zcr": 0.05,
            "feature_vector": np.zeros(20, dtype=np.float32),
        }

    frame_size = int(sr * 0.03)  # 30ms
    hop_size = int(sr * 0.015)   # 15ms
    n_frames = max(1, (len(samples) - frame_size) // hop_size)

    f0_list: list[float] = []
    centroids: list[float] = []
    energies: list[float] = []
    zcrs: list[float] = []

    # Frequency bins for FFT
    freqs = np.fft.rfftfreq(frame_size, 1.0 / sr)

    # 16-band Mel filterbank weights
    n_mels = 16
    mel_min = 1127.0 * math.log(1.0 + 80.0 / 700.0)
    mel_max = 1127.0 * math.log(1.0 + (sr / 2.0) / 700.0)
    mel_pts = np.linspace(mel_min, mel_max, n_mels + 2)
    hz_pts = 700.0 * (np.exp(mel_pts / 1127.0) - 1.0)
    bin_pts = np.floor((frame_size + 1) * hz_pts / sr).astype(int)

    fbank = np.zeros((n_mels, len(freqs)), dtype=np.float32)
    for m in range(1, n_mels + 1):
        left = max(0, bin_pts[m - 1])
        center = max(left + 1, bin_pts[m])
        right = min(len(freqs) - 1, max(center + 1, bin_pts[m + 1]))
        for k in range(left, center):
            if center > left:
                fbank[m - 1, k] = (k - bin_pts[m - 1]) / (bin_pts[m] - bin_pts[m - 1])
        for k in range(center, right):
            if right > center:
                fbank[m - 1, k] = (bin_pts[m + 1] - k) / (bin_pts[m + 1] - bin_pts[m])

    mel_energies = np.zeros(n_mels, dtype=np.float32)

    # Sub-sample frames evenly for rapid feature extraction on long segments
    max_sample_frames = 48
    if n_frames > max_sample_frames:
        frame_indices = list(range(0, n_frames, max(1, n_frames // max_sample_frames)))[:max_sample_frames]
    else:
        frame_indices = list(range(n_frames))

    processed_frames = 0
    for i in frame_indices:
        st = i * hop_size
        frame = samples[st : st + frame_size]
        if len(frame) < frame_size:
            break

        f0 = _estimate_frame_f0(frame, sr)
        if f0 > 0:
            f0_list.append(f0)

        # RMS Energy
        eng = float(np.sqrt(np.mean(frame**2)))
        energies.append(eng)

        # Zero crossing rate
        zcr = float(np.mean(np.abs(np.diff(np.sign(frame)))) / 2.0)
        zcrs.append(zcr)

        # FFT & Spectral Centroid
        mag = np.abs(np.fft.rfft(frame * np.hanning(len(frame))))
        mag_sum = np.sum(mag)
        if mag_sum > 1e-6:
            centroids.append(float(np.sum(freqs * mag) / mag_sum))
            mel_energies += np.dot(fbank, mag)
        processed_frames += 1

    f0_med = float(np.median(f0_list)) if f0_list else 150.0
    f0_std = float(np.std(f0_list)) if len(f0_list) > 1 else 10.0
    cent_mean = float(np.mean(centroids)) if centroids else 1500.0
    eng_mean = float(np.mean(energies)) if energies else 0.05
    zcr_mean = float(np.mean(zcrs)) if zcrs else 0.05

    # Normalize mel energies
    if processed_frames > 0:
        mel_energies /= processed_frames
    mel_norm = mel_energies / (np.linalg.norm(mel_energies) + 1e-6)

    # Compose acoustically weighted 20-dim feature vector
    feat_vec = np.zeros(20, dtype=np.float32)
    feat_vec[0] = 2.5 * ((f0_med - 150.0) / 100.0)      # High-weight pitch fundamental
    feat_vec[1] = 1.0 * (f0_std / 50.0)
    feat_vec[2] = 1.5 * ((cent_mean - 1500.0) / 800.0)   # Timbre brightness
    feat_vec[3] = 1.0 * zcr_mean
    feat_vec[4:20] = mel_norm * 0.8                      # Mel spectral envelope

    return {
        "f0_median": round(f0_med, 1),
        "f0_std": round(f0_std, 1),
        "spectral_centroid": round(cent_mean, 1),
        "energy": round(eng_mean, 4),
        "zcr": round(zcr_mean, 4),
        "feature_vector": feat_vec,
    }


def _cluster_feature_vectors(
    vectors: list[np.ndarray], max_speakers: int = 5, distance_threshold: float = 0.65
) -> list[int]:
    """
    Performs agglomerative clustering with normalized Euclidean distance.
    Returns cluster index (0, 1, 2...) for each vector.
    """
    n = len(vectors)
    if n == 0:
        return []
    if n == 1:
        return [0]

    # Initial singleton clusters
    clusters = [[i] for i in range(n)]

    def cluster_distance(c1: list[int], c2: list[int]) -> float:
        total_dist = 0.0
        count = 0
        for i in c1:
            for j in c2:
                d = float(np.linalg.norm(vectors[i] - vectors[j]))
                total_dist += d
                count += 1
        return total_dist / max(1, count)

    while len(clusters) > 1 and len(clusters) > max_speakers:
        min_d = float("inf")
        best_pair = (0, 1)
        for i in range(len(clusters)):
            for j in range(i + 1, len(clusters)):
                d = cluster_distance(clusters[i], clusters[j])
                if d < min_d:
                    min_d = d
                    best_pair = (i, j)
        i, j = best_pair
        clusters[i].extend(clusters[j])
        clusters.pop(j)

    # Continue merging while distance < threshold and len > 1
    while len(clusters) > 1:
        min_d = float("inf")
        best_pair = (0, 1)
        for i in range(len(clusters)):
            for j in range(i + 1, len(clusters)):
                d = cluster_distance(clusters[i], clusters[j])
                if d < min_d:
                    min_d = d
                    best_pair = (i, j)
        if min_d > distance_threshold:
            break
        i, j = best_pair
        clusters[i].extend(clusters[j])
        clusters.pop(j)

    # Sort clusters by size (largest cluster = Speaker 1)
    clusters.sort(key=lambda c: len(c), reverse=True)

    labels = [-1] * n
    for c_idx, cluster in enumerate(clusters):
        for idx in cluster:
            labels[idx] = c_idx

    return labels


def diarize_and_profile_audio(
    wav_path: Path,
    segments: list[dict[str, Any]],
    target_language: str = "km",
    available_voices: list[dict[str, Any]] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Performs speaker diarization and builds character voice profiles.
    Returns:
      1) updated_segments with assigned speaker_id and confidence
      2) speaker_profiles list
    """
    if not segments:
        return [], []

    samples, sr = extract_pcm_samples(wav_path)
    total_audio_len = len(samples)

    # Extract acoustic features per segment
    features_list: list[dict[str, Any]] = []
    for seg in segments:
        st = max(0, int(float(seg.get("start", 0.0)) * sr))
        en = min(total_audio_len, int(float(seg.get("end", 0.0)) * sr))
        if en > st:
            seg_samples = samples[st:en]
        else:
            seg_samples = np.zeros(512, dtype=np.float32)

        feat = extract_segment_features(seg_samples, sr=sr)
        features_list.append(feat)

    vectors = [f["feature_vector"] for f in features_list]
    cluster_labels = _cluster_feature_vectors(vectors, max_speakers=6, distance_threshold=0.38)

    # Group segments by speaker label
    speakers_data: dict[int, list[int]] = {}
    for idx, label in enumerate(cluster_labels):
        speakers_data.setdefault(label, []).append(idx)

    # Find available voices for target language
    from .dubbing import get_available_voices
    target_voices = available_voices or get_available_voices(target_language)
    male_voices = [v["id"] for v in target_voices if v.get("gender") == "Male"]
    female_voices = [v["id"] for v in target_voices if v.get("gender") == "Female"]
    all_voice_ids = [v["id"] for v in target_voices]

    male_ptr = 0
    female_ptr = 0

    speaker_profiles: list[dict[str, Any]] = []
    label_to_speaker_id: dict[int, str] = {}
    used_voices: set[str] = set()

    for label, seg_indices in sorted(speakers_data.items(), key=lambda item: item[0]):
        spk_num = label + 1
        speaker_id = f"speaker_{spk_num}"
        label_to_speaker_id[label] = speaker_id

        # Aggregate acoustic stats
        pitches = [features_list[i]["f0_median"] for i in seg_indices if features_list[i]["f0_median"] > 60]
        avg_pitch = float(np.mean(pitches)) if pitches else 150.0
        centroids = [features_list[i]["spectral_centroid"] for i in seg_indices]
        avg_centroid = float(np.mean(centroids)) if centroids else 1500.0

        # Dialogue text duration & speed estimation
        total_dur = sum(
            max(0.1, float(segments[i].get("end", 0.0)) - float(segments[i].get("start", 0.0)))
            for i in seg_indices
        )
        total_chars = sum(len(str(segments[i].get("text", ""))) for i in seg_indices)
        chars_per_sec = total_chars / max(0.5, total_dur)

        # Voice presentation estimation
        if avg_pitch < 165.0:
            gender_presentation = "masculine"
            confidence_gender = 0.88 if avg_pitch < 145.0 else 0.72
        elif avg_pitch > 185.0:
            gender_presentation = "feminine"
            confidence_gender = 0.88 if avg_pitch > 200.0 else 0.72
        else:
            gender_presentation = "uncertain"
            confidence_gender = 0.60

        # Age impression estimation
        if avg_pitch > 260.0 or (avg_pitch > 230.0 and avg_centroid > 2400.0):
            age_impression = "childlike"
        elif avg_pitch > 210.0 and chars_per_sec > 4.5:
            age_impression = "young_adult"
        elif avg_pitch < 110.0 or (avg_pitch < 130.0 and chars_per_sec < 2.5):
            age_impression = "mature"
        else:
            age_impression = "adult"

        # Speaking speed
        if chars_per_sec > 4.8:
            speaking_speed = "fast"
        elif chars_per_sec < 2.2:
            speaking_speed = "slow"
        else:
            speaking_speed = "normal"

        # Speaking style
        if chars_per_sec > 4.5:
            speaking_style = "energetic"
        elif chars_per_sec < 2.5:
            speaking_style = "calm"
        else:
            speaking_style = "conversational"

        # Distinct voice allocation across multiple speakers
        # Prioritize unused voices matching estimated gender presentation
        if gender_presentation == "masculine":
            pref_pool = [v for v in male_voices if v not in used_voices]
            if not pref_pool:
                pref_pool = [v for v in male_voices] or [v for v in female_voices if v not in used_voices] or all_voice_ids
        elif gender_presentation == "feminine":
            pref_pool = [v for v in female_voices if v not in used_voices]
            if not pref_pool:
                pref_pool = [v for v in female_voices] or [v for v in male_voices if v not in used_voices] or all_voice_ids
        else:
            pref_pool = [v for v in all_voice_ids if v not in used_voices] or all_voice_ids

        assigned_voice = pref_pool[0] if pref_pool else (male_voices[0] if male_voices else "km-KH-PisethNeural")
        
        # Calculate distinct speech rate adjustment if same voice had to be reused
        spk_rate_adj = 0
        if assigned_voice in used_voices:
            # Shift rate slightly for character differentiation
            rate_offsets = [8, -8, 14, -12]
            reuse_idx = sum(1 for p in speaker_profiles if p.get("assigned_voice_id") == assigned_voice)
            spk_rate_adj = rate_offsets[reuse_idx % len(rate_offsets)]
        elif age_impression == "childlike":
            spk_rate_adj = 8
        elif age_impression == "mature":
            spk_rate_adj = -5

        used_voices.add(assigned_voice)

        # Sample dialogue texts
        sample_texts = [
            str(segments[i].get("text", "")).strip()
            for i in seg_indices
            if str(segments[i].get("text", "")).strip()
        ][:3]

        profile = {
            "id": speaker_id,
            "speaker_id": speaker_id,
            "name": f"Speaker {spk_num}",
            "gender_presentation": gender_presentation,
            "age_impression": age_impression,
            "speaking_style": speaking_style,
            "speaking_speed": speaking_speed,
            "pitch_hz": round(avg_pitch, 1),
            "confidence": round(confidence_gender, 2),
            "assigned_voice_id": assigned_voice,
            "voice_id": assigned_voice,
            "segment_count": len(seg_indices),
            "total_duration": round(total_dur, 2),
            "sample_dialogue": sample_texts,
            "speech_rate": spk_rate_adj,
            "volume_boost": 1.0,
        }
        speaker_profiles.append(profile)

    # Assign speaker_id to each segment
    updated_segments: list[dict[str, Any]] = []
    for idx, seg in enumerate(segments):
        c_label = cluster_labels[idx]
        spk_id = label_to_speaker_id.get(c_label, "speaker_1")
        seg_copy = dict(seg)
        seg_copy["speaker_id"] = spk_id
        seg_copy["confidence"] = round(float(speaker_profiles[c_label]["confidence"]), 2) if c_label < len(speaker_profiles) else 0.85
        updated_segments.append(seg_copy)

    # Perform story-aware dialogue context emotion detection
    from .emotion import analyze_dialogue_emotions
    emotion_enriched_segments = analyze_dialogue_emotions(updated_segments, acoustic_features=features_list)

    return emotion_enriched_segments, speaker_profiles
