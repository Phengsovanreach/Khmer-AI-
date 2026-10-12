# KHMER TRANSLATOR 2.0 — COMPLETE USER GUIDE

Welcome to **Khmer Translator 2.0**, an advanced, on-premise AI speech recognition, multilingual video translation, and neural dubbing workstation with original soundtrack and sound effect preservation.

---

## Table of Contents
1. [Overview & Core Philosophy](#1-overview--core-philosophy)
2. [Quick Start (3-Minute Guide)](#2-quick-start-3-minute-guide)
3. [Step 1: Importing Your Video](#3-step-1-importing-your-video)
4. [Step 2: Language Selection](#4-step-2-language-selection)
5. [Step 3: Speaker Diarization & Neural Voices](#5-step-3-speaker-diarization--neural-voices)
6. [Step 4: Original Soundtrack & Action Sound Preservation](#6-step-4-original-soundtrack--action-sound-preservation)
7. [Step 5: Subtitle Editing & Khmer Proofreading](#7-step-5-subtitle-editing--khmer-proofreading)
8. [Step 6: Dual Video Preview Studio & Video Export](#8-step-6-dual-video-preview-studio--video-export)
9. [Keyboard Shortcuts](#9-keyboard-shortcuts)
10. [FAQ & Help Center](#10-faq--help-center)

---

## 1. Overview & Core Philosophy

Khmer Translator operates on one fundamental audio engineering principle:

> **Translate and replace human speech only. Preserve the original non-speech soundtrack as much as technically possible.**

### Key Highlights
- **100% Local-First Processing:** Videos and audio streams are processed on your local server. No private video content is ever transmitted to third-party cloud analytics or data harvesters.
- **Low-Resource Architecture:** Optimized specifically for hardware with 3.3 to 4 GiB of system RAM (e.g., ASUS VivoBook X515MA) using INT8 CPU quantization.
- **Zero Ollama / Heavy GPU Requirement:** All translation, subtitle processing, and audio mixing run with zero heavy GPU dependencies.
- **Full Cultural Elegance:** Includes an authentic Khmer cultural theme with Angkor Wat motifs, lotus patterns, and Devata animations.

---

## 2. Quick Start (3-Minute Guide)

For first-time users, the default workflow is designed to be completely automatic:

1. Open **Workspace** tab.
2. Drag and drop your video file (`.mp4`, `.mkv`, `.webm`, etc.).
3. Leave **Source Language** on `🌐 Auto Detect` (or select the specific source language).
4. Set **Target Language** to `🇰🇭 ភាសាខ្មែរ (Khmer)` (or your desired target language).
5. Ensure **Preserve Original Soundtrack & SFX** is toggled **ON** (default).
6. Click **"Transcribe & Auto-Dub"**.
7. Once finished, preview the result in **Dual Video Preview Studio** and click **Export Video**.

---

## 3. Step 1: Importing Your Video

### Supported Formats
- **Video Containers:** MP4, MKV, MOV, WebM, AVI, M4V (Codecs: H.264, H.265/HEVC, VP9, AV1).
- **Audio Files:** MP3, WAV, M4A, FLAC, OGG, AAC, OPUS.
- **File Size Limit:** Up to 2,048 MB (2 GB) per file.

### How to Import
- **Drag & Drop:** Simply drag your file over the upload dropzone.
- **File Browser:** Click "Browse Media File" to select a file from your file manager.
- **URL Import (if yt-dlp installed):** Paste a direct video URL and click "Download & Import".

### Media Validation
Before processing begins, the system automatically runs an FFprobe integrity inspection to verify audio streams, sample rates, channels, and duration. If an invalid or corrupted file is uploaded, a clear diagnostic message is displayed.

---

## 4. Step 2: Language Selection

Khmer Translator supports 12+ international languages:
- 🇰🇭 **Khmer (`km`)** — Default target with full Khmer Unicode ligature support
- 🇺🇸 **English (`en`)**
- 🇨🇳 **Chinese Simplified (`zh`)**
- 🇯🇵 **Japanese (`ja`)**
- 🇰🇷 **Korean (`ko`)**
- 🇻🇳 **Vietnamese (`vi`)**
- 🇫🇷 **French (`fr`)**
- 🇪🇸 **Spanish (`es`)**
- 🇩🇪 **German (`de`)**
- 🇮🇩 **Indonesian (`id`)**
- 🇱🇦 **Lao (`lo`)**
- 🇲🇲 **Burmese (`my`)**

### Automatic Language Detection
When `Auto Detect` is selected, Whisper analyzes the first 30 seconds of speech to automatically determine the spoken language. If your clip has heavy background music during the opening seconds, explicitly selecting the source language is recommended.

---

## 5. Step 3: Speaker Diarization & Neural Voices

### Automatic Character Profiling
During processing, the speech engine groups dialogue by acoustic characteristics and assigns consistent speaker labels (`Speaker 1`, `Speaker 2`, etc.).

### Verified Curated Voices
- **Khmer (km-KH):**
  - `PisethNeural` — Natural masculine voice with authoritative and conversational delivery.
  - `SreymomNeural` — Warm feminine voice with expressive storytelling cadence.
- **English (en-US):**
  - `GuyNeural` — Natural adult male.
  - `JennyNeural` — Natural adult female.
  - `AriaNeural` — Expressive young female.

### Editing Character Profiles
Navigate to the **Characters** tab to:
- Rename character labels (e.g., change `Speaker 1` to `Dara`, `Speaker 2` to `Bopha`).
- Reassign target voices.
- Merge duplicate speaker IDs into a single character.
- Split falsely grouped dialogue segments.

---

## 6. Step 4: Original Soundtrack & Action Sound Preservation

Traditional video dubbing tools often silence the original audio track completely or apply aggressive filters that destroy background music, punches, kicks, and environmental sounds. Khmer Translator uses an intelligent audio strategy:

1. **Speech-Aware Separation:** Spoken dialogue is isolated from the sound bed.
2. **Authentic Nonverbal Preservation:** Laughter, screams, gasps, and crying are sliced directly from the original actor's audio track with 30 ms micro-fades. Edge TTS is never instructed to speak literal text like "[laughter]".
3. **Dynamic Sidechain Ducking:** During active translated dialogue, the original background audio is smoothly attenuated by 35% with a 35 ms attack and 300 ms release curve.
4. **Speech Formant EQ:** A -5 dB parametric notch filter at 1,400 Hz is applied to the background track, carving out frequency space for crystal-clear vocal clarity.
5. **Full Restoration During Pauses:** When characters stop speaking, the background soundtrack returns to 100% volume immediately.

---

## 7. Step 5: Subtitle Editing & Khmer Proofreading

### Subtitle Editor Pro
Under the **Subtitles** tab:
- Click any subtitle line to edit text.
- Adjust start and end timestamps down to the millisecond.
- Insert, delete, split, or merge subtitle segments.
- Download `.SRT`, `.VTT`, or `.TXT` transcript files.

### Khmer Proofreader & Ligature Engine
Under the **Proofreading** tab:
- Automatically fixes duplicated vowels, broken subscripts (ជើងអក្សរ), and punctuation marks.
- Expands digits and percentages into formal Khmer spoken words for natural dubbing pronunciation.

### Pronunciation Dictionary
Under the **Dictionary** tab:
- Add difficult proper names, historical titles, and specialized technical terms.
- Specify exact phonetic pronunciation in Khmer Unicode.

---

## 8. Step 6: Dual Video Preview Studio & Video Export

### Side-by-Side Dual Video Studio
Navigate to the **Preview** tab:
- **Synchronous Scrubbing:** Seeking in either player locks the other player down to the frame.
- **Audio Stream Selector:**
  - `Original Audio` — Listen to the source video audio only.
  - `Dubbed Audio Only` — Listen strictly to the translated neural dialogue.
  - `Mixed Soundtrack` — Listen to the combined audio with sidechain ducking.
- **Volume Controls:** Independent sliders for Dialogue Volume and Soundtrack Volume.

### Video Export
1. Click **Export Video** in the Preview studio or open the **Export** tab.
2. Configure settings:
   - **Burn Subtitles into Video (Hardsub):** Yes / No.
   - **Subtitle Font Size:** Small (18px), Medium (22px), Large (26px).
   - **Preserve Original Soundtrack:** ON (recommended).
   - **Original Volume:** Default 85%.
   - **Dialogue Volume:** Default 100%.
   - **Preserve Nonverbal Expressions:** ON.
3. Click **Start Render**.
4. Once completed, click **Download Completed MP4**.

---

## 9. Keyboard Shortcuts

| Shortcut | Action |
| :--- | :--- |
| `Space` | Play / Pause video playback |
| `Left Arrow` | Seek backward 2 seconds |
| `Right Arrow` | Seek forward 2 seconds |
| `Escape` | Close modals and dialogs |
| `Ctrl + S` / `Cmd + S` | Save subtitle edits |

---

## 10. FAQ & Help Center

To access full documentation, troubleshooting matrices, and diagnostic reporting inside the application:
1. Open the **Settings & Models** tab in the sidebar.
2. Click **មជ្ឈមណ្ឌលជំនួយ ១៥ ផ្នែក (Help & Support Center)**.
3. Use the search bar to locate solutions for audio, dubbing, translation, or rendering issues.
4. Click **Copy Diagnostic Information** to generate a sanitized diagnostic report when seeking technical support.

### Official Telegram Support
- **Display Name:** Telegram Support
- **Username:** `@NeonCipher200`
- **Direct Contact:** [https://t.me/NeonCipher200](https://t.me/NeonCipher200)
- **Message:** *Need help with Khmer Translator? Contact us on Telegram.*

---
*© 2026 Phengsovanreach. All rights reserved.*
