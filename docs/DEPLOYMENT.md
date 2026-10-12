# KHMER TRANSLATOR 2.0 — PRODUCTION DEPLOYMENT GUIDE

This document provides production deployment instructions for **Khmer Translator 2.0**, covering hardware requirements, environment configuration, systemd services, Docker containerization, reverse proxy setup, and operational health checks.

---

## 1. System Requirements & Hardware Sizing

Khmer Translator utilizes **faster-whisper INT8 CPU quantization** and **Microsoft Edge Neural TTS**, allowing it to run smoothly on cost-effective, low-resource hardware without requiring a dedicated GPU.

### Minimum Production Hardware
- **Operating System:** Ubuntu 22.04 LTS / 24.04 LTS, Debian 12, or RHEL 9 (64-bit Linux).
- **CPU:** 2 vCPUs (x86_64 or ARM64 with AVX / NEON support).
- **RAM:** 3.5 GiB – 4 GiB (Swappiness configured with a 2 GB swapfile recommended).
- **Disk Storage:** 20 GB SSD storage (10 GB for OS + dependencies; 10 GB for video uploads/outputs).
- **Network:** Outbound HTTPS access (TCP 443) for Edge Neural TTS synthesis.

### Recommended High-Throughput Hardware
- **CPU:** 4 – 8 vCPUs.
- **RAM:** 8 GiB – 16 GiB.
- **Disk Storage:** 50 GB NVMe SSD.

---

## 2. System Prerequisites & Dependencies

### Install System Packages
```bash
sudo apt-get update && sudo apt-get install -y \
    ffmpeg \
    curl \
    git \
    python3 \
    python3-venv \
    python3-pip \
    nodejs \
    npm
```

### Verify FFmpeg and FFprobe
Ensure FFmpeg is installed and accessible in the system `$PATH`:
```bash
ffmpeg -version
ffprobe -version
```

---

## 3. Environment Variables Configuration

Copy `.env.example` to `.env` in both backend and frontend roots:

### Backend `.env` (`/path/to/backend/.env`)
```bash
# Application Configuration
APP_NAME="Khmer Translator API"
APP_VERSION="2.0.0"
ENVIRONMENT="production"
LOG_LEVEL="INFO"

# Server Bind Address
HOST="127.0.0.1"
PORT=8000

# Media Directories
UPLOAD_DIR="uploads"
OUTPUT_DIR="outputs"
JOBS_FILE="jobs.json"
MAX_UPLOAD_MB=2048

# Speech Recognition Model (tiny, base, small, medium)
DEFAULT_WHISPER_MODEL="tiny"
WHISPER_DEVICE="cpu"
WHISPER_COMPUTE_TYPE="int8"

# Production Allowed CORS Origins (Comma-separated)
CORS_ORIGINS="https://translator.yourdomain.com,http://127.0.0.1:8000"
```

### Frontend `.env` (`/path/to/frontend/.env`)
```bash
# Production API Base URL
VITE_API_URL="https://translator.yourdomain.com"
```

---

## 4. Deployment Pattern A: Bare-Metal / Systemd + Caddy (Recommended)

This pattern provides the best performance and minimal RAM consumption (~350 MB idle).

### Step 1: Install and Build Backend
```bash
cd /opt/khmer-translator/backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 2: Build Frontend Production Assets
```bash
cd /opt/khmer-translator/frontend
npm install --production=false
npm run build
# Production assets will be compiled to /opt/khmer-translator/frontend/dist
```

### Step 3: Create Backend Systemd Service
Create `/etc/systemd/system/khmer-translator.service`:
```ini
[Unit]
Description=Khmer Translator 2.0 FastAPI Application
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/khmer-translator/backend
EnvironmentFile=/opt/khmer-translator/backend/.env
ExecStart=/opt/khmer-translator/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo chown -R www-data:www-data /opt/khmer-translator
sudo systemctl daemon-reload
sudo systemctl enable --now khmer-translator.service
sudo systemctl status khmer-translator.service
```

### Step 4: Configure Reverse Proxy (Caddy or Nginx)

#### Option 1: Caddyfile (`/etc/caddy/Caddyfile`)
Caddy automatically provisions free SSL/TLS certificates via Let's Encrypt:
```caddy
translator.yourdomain.com {
    # Serve static frontend production bundle
    root * /opt/khmer-translator/frontend/dist
    file_server

    # Reverse proxy API requests to FastAPI
    handle /api/* {
        reverse_proxy 127.0.0.1:8000
    }

    # SPA Fallback for client-side routing
    try_files {path} /index.html
}
```

Reload Caddy:
```bash
sudo systemctl reload caddy
```

#### Option 2: Nginx Configuration
```nginx
server {
    listen 80;
    server_name translator.yourdomain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name translator.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/translator.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/translator.yourdomain.com/privkey.pem;

    client_max_body_size 2048M;

    root /opt/khmer-translator/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 1800s;
        proxy_send_timeout 1800s;
    }
}
```

---

## 5. Deployment Pattern B: Docker & Docker Compose

For containerized deployments using Docker:

### Step 1: Start Containers
```bash
docker compose up -d --build
```

### Step 2: View Logs
```bash
docker compose logs -f
```

---

## 6. Health & Readiness Verification

Once deployed, verify application readiness using the built-in probes:

### 1. Health Probe
```bash
curl -f https://translator.yourdomain.com/api/health
# Response: {"status":"ok","app":"Khmer Translator API","version":"2.0.0"}
```

### 2. Readiness Probe
```bash
curl -f https://translator.yourdomain.com/api/ready
# Response: {"status":"ready","app":"Khmer Translator API","version":"2.0.0","ffmpeg":true,"ffprobe":true,"faster_whisper":true,"tts":true,"storage_writable":true,"active_jobs":0}
```

### 3. Sanitized System Diagnostics
```bash
curl -f https://translator.yourdomain.com/api/system/diagnostics
# Returns sanitized CPU, memory, storage free space, and hardware profile without secrets.
```

---

## 7. Storage Management & Backup

### Media Storage Retention
Media files are stored in `backend/uploads/` and `backend/outputs/`. To prevent unbounded disk consumption, configure a daily cron job to delete temporary media files older than 7 days:

```bash
# Add to crontab (crontab -e)
0 3 * * * find /opt/khmer-translator/backend/uploads/ -type f -mtime +7 -delete
0 3 * * * find /opt/khmer-translator/backend/outputs/ -type f -mtime +7 -delete
```

### Backing Up Configuration & Dictionary
To backup user settings and custom pronunciation entries:
```bash
tar -czvf khmer_translator_backup_$(date +%F).tar.gz \
    /opt/khmer-translator/backend/app_settings.json \
    /opt/khmer-translator/backend/pronunciation_dictionary.json \
    /opt/khmer-translator/backend/jobs.json
```

---

## 8. Rollback & Updates Procedure

To deploy an application update:
```bash
cd /opt/khmer-translator
git pull origin main

# Update backend
cd backend
source .venv/bin/activate
pip install -r requirements.txt

# Update frontend
cd ../frontend
npm install --production=false
npm run build

# Restart service
sudo systemctl restart khmer-translator.service
```

If an issue occurs, roll back using Git:
```bash
git reset --hard HEAD~1
sudo systemctl restart khmer-translator.service
```

---
*© 2026 Phengsovanreach. All rights reserved.*
