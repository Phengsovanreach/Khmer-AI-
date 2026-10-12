# Khmer Translator 2.0 — AI Video Translation, Subtitle & Multilingual Dubbing Studio

A production-ready, on-premise AI video translation, professional subtitle editing, neural voice dubbing, video preview, and export platform tailored for low-resource environments (developed on Ubuntu Linux for systems with ~3.3 – 4 GiB RAM).

**Copyright Notice:**  
**© 2026 Phengsovanreach. All rights reserved.**

---

## 1. Core Principle & Audio Engineering Philosophy

> **Translate and replace human speech only. Preserve the original non-speech soundtrack as much as technically possible.**

- **Preserve Action & Fighting SFX:** Punches, kicks, impacts, weapon sounds, explosions, footsteps, wind, rain, and crowd ambience remain fully audible.
- **Dynamic Sidechain Ducking:** During active translated dialogue, original background audio smoothly ducks by 35% with an intelligent 1,400 Hz vocal formant notch filter (`equalizer=f=1400:t=q:w=1.0:g=-5`) ensuring vocal clarity without masking scene atmosphere.
- **Authentic Nonverbal Vocalizations:** Laughter, screams, gasps, and crying are sliced directly from the original actor's audio track with 30 ms micro-fades rather than synthesizing unnatural robotic text.
- **Anti-Cutoff Audio Fitting:** Automatically adjusts speech tempo (up to 1.25x `atempo`) and applies micro-fadeouts so last syllables and sentence endings are never clipped.
- **100% Local-First & Zero Ollama / GPU Requirement:** All models run via INT8 CPU quantization (`faster-whisper`), eliminating heavy GPU and Ollama dependencies.

---

## 2. Key Features

1. **Complete 15-Section Help Center & User Guide:**
   - Integrated directly into Settings and accessible anywhere via sidebar.
   - Searchable articles, expandable FAQs, troubleshooting guides, and system requirements.
   - One-click **Copy Diagnostic Information** (strictly sanitizes secrets and personal media).
2. **Interactive Onboarding Wizard:**
   - 5-step guided walkthrough for beginners.
   - Keyboard accessible (`Esc`, arrow keys), non-blocking, and persistent via localStorage.
3. **Contextual Help System:**
   - Integrated help tooltips next to complex settings (Auto Detect, Diarization, Auto Voice, Emotion Dubbing, Ducking, Khmer Dictionary, Export Quality).
4. **Speaker Diarization & Character Voice Studio:**
   - Detects distinct speakers (`Speaker 1`, `Speaker 2`) and tracks vocal continuity across scenes.
   - Verified natural voices: `PisethNeural` (Male) and `SreymomNeural` (Female) for Khmer; `Guy`, `Jenny`, `Aria` for English.
5. **Subtitle Editor Pro & Automated Khmer Proofreader:**
   - Dual-column editing with live click-to-seek synchronization.
   - Automated Khmer Unicode ligature engine fixing duplicate vowels, subscript ordering (ជើងអក្សរ), and punctuation.
   - Custom phonetic Pronunciation Dictionary for names and specialized terms.
6. **Synchronized Dual Video Preview Studio:**
   - Side-by-side frame-locked playback of original video vs. translated dubbed video.
   - Live audio selector: Original Audio, Dubbed Voice Only, or Mixed Soundtrack.
7. **Production Deployment Readiness:**
   - Built-in probes: `/api/health`, `/api/ready` (Kubernetes/systemd readiness), `/api/system/diagnostics`.
   - Comprehensive systemd, Caddy, Nginx, Docker, and GitHub Actions CI configurations.

---

## 3. Documentation Directory

Detailed guides are located in the `docs/` folder:
- 📖 [**Complete User Guide (docs/USER_GUIDE.md)**](file:///home/izen/Documents/khmer-translator-fullstack/khmer-translator/docs/USER_GUIDE.md) — Beginner and advanced workflows.
- 🚀 [**Production Deployment Guide (docs/DEPLOYMENT.md)**](file:///home/izen/Documents/khmer-translator-fullstack/khmer-translator/docs/DEPLOYMENT.md) — Systemd, Caddy, Docker, and storage retention.
- 🛠️ [**Troubleshooting Guide (docs/TROUBLESHOOTING.md)**](file:///home/izen/Documents/khmer-translator-fullstack/khmer-translator/docs/TROUBLESHOOTING.md) — Remediation for audio, video, text, and connectivity issues.

---

## 4. Hardware Requirements & Sizing

- **Operating System:** Ubuntu Linux 22.04+ / Debian 12 / Windows 10/11
- **Memory (RAM):** 3.3 GiB – 4 GiB minimum (tested on ASUS VivoBook X515MA)
- **Processor:** Dual-core CPU or higher (optimized for INT8 CPU quantization)
- **Disk Space:** ~5 GB for runtime, models, and virtual environment
- **Python:** Python 3.11+
- **Node.js:** Node.js 20+ and npm

Install system dependencies on Ubuntu:
```bash
sudo apt update && sudo apt install -y ffmpeg python3-venv python3-pip curl
```

---

## 5. Quick Start (Local Development)

### 1. Backend (FastAPI)
```bash
cd backend
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
- Health Probe: `http://127.0.0.1:8000/api/health`
- Readiness Probe: `http://127.0.0.1:8000/api/ready`
- System Diagnostics: `http://127.0.0.1:8000/api/system/diagnostics`

### 2. Frontend (React + TypeScript + Vite)
In a separate terminal:
```bash
cd frontend
npm install
npm run dev
```
Open your browser at `http://localhost:5173`.

---

## 6. Production Deployment Overview

### Pattern A: Systemd Service + Caddy Reverse Proxy (Recommended)
Compile the frontend and run FastAPI as a background service:
```bash
# Build frontend
cd frontend && npm run build

# Start backend via systemd
sudo systemctl enable --now khmer-translator.service
```

### Pattern B: Docker Compose
```bash
docker compose up -d --build
```

---

## 7. Automated Testing & Verification

Run all backend automated unit and integration tests:
```bash
cd backend
.venv/bin/pytest tests/ -v
```
Result: **58 passed tests** covering audio preservation, speech fitting, Khmer Unicode ligatures, multilingual translation, API endpoints, and production readiness.

Run frontend typecheck and production build:
```bash
cd frontend
npm run build
```
Result: **Zero TypeScript errors**, production bundle compiled cleanly in `dist/`.

---

## 8. Copyright & License

**© 2026 Phengsovanreach. All rights reserved.**

All original code, audio processing pipelines, and designs in the Khmer Translator project are copyrighted by Phengsovanreach.
