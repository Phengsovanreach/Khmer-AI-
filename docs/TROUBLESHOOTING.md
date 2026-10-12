# KHMER TRANSLATOR 2.0 — TROUBLESHOOTING GUIDE

This guide provides practical diagnoses, root causes, and step-by-step remediation procedures for common issues encountered during local development, video processing, and production deployment.

---

## 1. Audio & Dubbing Issues

### Issue 1.1: Dubbed Video Has No Sound
- **Symptom:** The exported or previewed video plays video frames, but no translated dialogue is audible.
- **Root Causes:**
  1. The `Dialogue Volume` slider was inadvertently set to 0%.
  2. Edge TTS synthesis failed due to temporary network unavailability during the dubbing job.
  3. The target language has no valid neural voice allocated.
- **Resolution:**
  1. Open the **Preview** tab or click **Export Video**. Verify that `Dialogue Volume` is set to 100% (1.0).
  2. Check backend service logs (`journalctl -u khmer-translator -n 50`) for TTS network timeouts.
  3. Re-run dubbing by clicking **Regenerate Dubbing** in the **Workspace** tab.

---

### Issue 1.2: Original Music, Fighting Sounds, or Action SFX Disappeared
- **Symptom:** Translated speech plays, but the background fighting sounds, punches, kicks, or background score are silent.
- **Root Causes:**
  1. The `Preserve Original Soundtrack` option was turned OFF.
  2. `Soundtrack Volume` was set to 0.
- **Resolution:**
  1. In the **Preview** or **Export** drawer, ensure **"Preserve Original Soundtrack & SFX"** is toggled **ON**.
  2. Confirm `Soundtrack Volume` is set between 75% and 85%.
  3. Re-export the video. The FFmpeg engine will apply dynamic sidechain compression (`sidechaincompress`) and vocal formant notch filtering (`equalizer=f=1400:t=q:w=1.0:g=-5`), preserving fighting effects.

---

### Issue 1.3: Syllables or Sentence Endings Cut Off Abruptly
- **Symptom:** The last syllable or final word of a translated subtitle is clipped.
- **Root Causes:**
  1. The translated sentence is significantly longer than the original speaker's time window.
- **Resolution:**
  1. The system automatically applies pitch-neutral tempo adjustment (up to 1.25x `atempo`) and smooth 40 ms micro-fadeouts.
  2. For extreme discrepancies, open **Subtitles** tab and edit the Khmer sentence to be more concise, or slightly extend the segment's `End Time`.

---

### Issue 1.4: Laughter, Screams, or Grunts Sound Like Robotic Words
- **Symptom:** Actor laughing or gasping causes TTS to pronounce bracketed text like "[laughter]".
- **Root Causes:**
  1. Nonverbal preservation was disabled.
- **Resolution:**
  1. Ensure **Preserve Nonverbal Expressions** is enabled.
  2. The pipeline's `is_nonverbal_sound_segment()` detects non-lexical cues (`[laughter]`, `*gasp*`, `(screaming)`, `ha ha`, `hmm`) and automatically extracts authentic actor audio slices with 30 ms micro-fades directly from the source video.

---

## 2. Translation & Khmer Text Issues

### Issue 2.1: Khmer Unicode Ligatures or Subscripts Look Broken
- **Symptom:** Subscript consonants (ជើងអក្សរ) display as dotted circles or broken symbols.
- **Root Causes:**
  1. Incorrect Unicode ordering in original transcription text (e.g., duplicated vowels or incorrect placement of Coeng U+17D2).
- **Resolution:**
  1. Navigate to the **Proofreading** tab.
  2. Click **"Run Automated Khmer Proofreader"**.
  3. The built-in ligature engine (`normalize_khmer_unicode()`) automatically corrects Unicode ordering, deduplicates vowel signs, and inserts appropriate punctuation spaces.

---

### Issue 2.2: Proper Names or Technical Terms Mispronounced
- **Symptom:** Foreign names or specialized terms are misread by the neural speech engine.
- **Resolution:**
  1. Navigate to the **Dictionary** tab.
  2. Enter the source term and the intended phonetic Khmer spelling.
  3. Click **Add Term**. All subsequent translation and dubbing jobs will substitute the phonetic pronunciation automatically.

---

## 3. Video Processing & Import Issues

### Issue 3.1: Video Upload Fails with "Unsupported Format"
- **Symptom:** File is rejected immediately upon upload.
- **Root Causes:**
  1. File exceeds 2,048 MB (2 GB).
  2. Media file is corrupted or contains no readable audio stream.
- **Resolution:**
  1. Verify the file using FFprobe:
     ```bash
     ffprobe -v error -show_entries format=duration,size -of default=noprint_wrappers=1 your_file.mp4
     ```
  2. If the video codec is proprietary, remux to standard MP4:
     ```bash
     ffmpeg -i input_file.mov -c:v libx264 -c:a aac output_file.mp4
     ```

---

### Issue 3.2: Processing Appears Stuck at "Transcribing"
- **Symptom:** Progress bar stays at 25% or 40% for an unusually long time.
- **Root Causes:**
  1. A large Whisper model (`small` or `medium`) was selected on a low-CPU / low-RAM machine.
  2. CPU starvation caused by another heavy background task.
- **Resolution:**
  1. On systems with 4 GB RAM (e.g. ASUS VivoBook X515MA), always use model `tiny` (`DEFAULT_WHISPER_MODEL="tiny"`).
  2. Check running processes on the server:
     ```bash
     top -b -n 1 | head -n 20
     ```

---

## 4. Production Deployment & Connectivity Issues

### Issue 4.1: Browser Displays "CORS Error" or Cannot Reach Backend
- **Symptom:** `Access to fetch at 'https://api.yourdomain.com' from origin 'https://yourdomain.com' has been blocked by CORS policy`.
- **Root Causes:**
  1. The frontend domain is not listed in `CORS_ORIGINS` in `backend/.env`.
- **Resolution:**
  1. In `backend/.env`, update:
     ```bash
     CORS_ORIGINS="https://yourdomain.com,https://api.yourdomain.com"
     ```
  2. Restart the backend service:
     ```bash
     sudo systemctl restart khmer-translator.service
     ```

---

### Issue 4.2: Readiness Probe Returns HTTP 503
- **Symptom:** `GET /api/ready` returns HTTP 503 Service Unavailable.
- **Root Causes:**
  1. FFmpeg or FFprobe is missing from the system path.
  2. `uploads/` or `outputs/` directory is not writable by the service user.
- **Resolution:**
  1. Query the readiness endpoint for check details:
     ```bash
     curl -s http://127.0.0.1:8000/api/ready | jq .
     ```
  2. If `storage_writable` is `false`, fix directory permissions:
     ```bash
     sudo chown -R www-data:www-data /opt/khmer-translator/backend/uploads /opt/khmer-translator/backend/outputs
     sudo chmod -R 775 /opt/khmer-translator/backend/uploads /opt/khmer-translator/backend/outputs
     ```
  3. If `ffmpeg` is `false`, install FFmpeg:
     ```bash
     sudo apt-get install -y ffmpeg
     ```

---

## 5. Generating a Diagnostic Report for Support

When filing an issue, generate a clean diagnostic report that contains no private user videos, passwords, or secrets:

1. In the web interface: Open **Settings & Models** -> **មជ្ឈមណ្ឌលជំនួយ ១៥ ផ្នែក (Help & Support Center)** -> Click **"Copy Diagnostic Information"**.
2. Or via terminal:
   ```bash
   curl -s http://127.0.0.1:8000/api/system/diagnostics | jq .
   ```
3. Attach this output to your bug report for immediate support.

---
*© 2026 Phengsovanreach. All rights reserved.*
