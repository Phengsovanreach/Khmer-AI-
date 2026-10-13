from __future__ import annotations
import asyncio
import json
import logging
import os
import platform
import shutil
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Query, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse, Response, StreamingResponse

from .auth import (
    register_user,
    login_user,
    get_user_by_token,
    revoke_session,
)
from .config import BASE_DIR, OUTPUT_DIR, UPLOAD_DIR, settings
from .diarization import diarize_and_profile_audio
from .dubbing import (
    generate_dubbed_audio_track,
    generate_speech_sample,
    get_available_khmer_voices,
    get_available_voices,
    get_default_voice_for_language,
    mix_audio_tracks,
    verify_audio_is_audible,
)
from .languages import (
    SUPPORTED_LANGUAGES,
    get_language_by_code,
    get_source_languages,
    get_supported_languages,
    get_target_languages,
    normalize_whisper_code,
)
from .schemas import (
    AppSettings,
    AuthResponse,
    AuthStatusResponse,
    CapabilitiesResponse,
    DictionaryEntry,
    DictionaryListResponse,
    DubbingRequest,
    HealthResponse,
    JobProgressResponse,
    JobResponse,
    LanguageInfo,
    LanguagesResponse,
    LoginRequest,
    ModelInfo,
    ModelsResponse,
    PreviewInfoResponse,
    ProjectUpdateRequest,
    ProofreadApplyRequest,
    ProofreadJobRequest,
    ProofreadJobResponse,
    ProofreadSampleRequest,
    ReadinessResponse,
    RegisterRequest,
    UserProfile,
    SegmentAudioSampleRequest,
    SpeakerMergeRequest,
    SpeakerProfile,
    SpeakerSplitRequest,
    SpeakerUpdateRequest,
    SubtitleInsertRequest,
    SubtitleMergeRequest,
    SubtitleSplitRequest,
    SystemDiagnosticsResponse,
    TranscriptSegment,
    TranscriptUpdateRequest,
    UploadChunkResponse,
    UploadCompleteRequest,
    UploadInitRequest,
    UploadInitResponse,
    UploadStatusResponse,
    VideoExportRequest,
    VoiceInfo,
)
from .khmer_nlp import dictionary_manager, khmer_proofreader, normalize_khmer_unicode
from .storage import (
    add_job_listener,
    delete_job,
    get_job,
    list_jobs,
    publish_job_update,
    remove_job_listener,
    safe_job,
    save_job,
    update_job,
)
from .transcription import (
    ALLOWED_EXTENSIONS,
    AVAILABLE_MODELS,
    build_srt_content,
    build_txt_content,
    build_vtt_content,
    extract_audio_stream,
    get_available_models,
    probe_media_file,
    render_video_with_subtitles,
    transcribe_media,
)
from .translation import translate_segments, translate_segments_to_khmer, translate_single_line

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    version="2.0.0",
    description="Multilingual AI Video Translation, Subtitle & Voice Dubbing Studio",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=r"^https://.*\.pages\.dev$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_current_user_optional(
    request: Request,
    authorization: str | None = Header(None),
) -> Optional[dict[str, Any]]:
    """Resolves authenticated user from Bearer Authorization header or HttpOnly auth_token cookie."""
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:].strip()
    elif authorization and authorization.strip():
        token = authorization.strip()
    if not token:
        token = request.cookies.get("auth_token")
    if not token:
        return None
    return get_user_by_token(token)


def get_current_user(
    current_user: Optional[dict[str, Any]] = Depends(get_current_user_optional),
) -> dict[str, Any]:
    """Strict dependency requiring authenticated user; raises HTTP 401 if missing or invalid."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required / តម្រូវឲ្យចូលប្រើប្រាស់ជាមុនសិន",
        )
    return current_user


def check_job_access(job: dict[str, Any], user: Optional[dict[str, Any]]) -> None:
    """Enforces account data isolation. If a job has a user_id, only the owner can access it."""
    job_user_id = job.get("user_id")
    if job_user_id:
        if not user or user.get("id") != job_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You do not have permission to access this project / គ្មានសិទ្ធិចូលប្រើប្រាស់គម្រោងនេះទេ",
            )


@app.middleware("http")
async def enforce_job_data_isolation(request: Request, call_next):
    """
    Security Middleware enforcing multi-tenant account data isolation.
    Guarantees private job resources cannot be inspected, modified, or deleted across accounts.
    Allows HTTP OPTIONS CORS preflight requests to pass through immediately.
    """
    if request.method == "OPTIONS":
        return await call_next(request)

    path = request.url.path
    job_id = None
    if path.startswith("/api/jobs/"):
        sub = path[len("/api/jobs/"):]
        candidate = sub.split("/")[0]
        if candidate and candidate != "import-url":
            job_id = candidate
    elif path.startswith("/api/transcription/jobs/"):
        sub = path[len("/api/transcription/jobs/"):]
        candidate = sub.split("/")[0]
        if candidate:
            job_id = candidate

    if job_id:
        job = get_job(job_id)
        if job and job.get("user_id"):
            token = None
            auth_header = request.headers.get("authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header[7:].strip()
            elif auth_header and auth_header.strip():
                token = auth_header.strip()
            if not token:
                token = request.cookies.get("auth_token")

            user = get_user_by_token(token) if token else None
            if not user or user["id"] != job["user_id"]:
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={
                        "detail": "Forbidden: You do not have permission to access this project / គ្មានសិទ្ធិចូលប្រើប្រាស់គម្រោងនេះទេ"
                    },
                )

    return await call_next(request)


# Concurrency limiter to prevent CPU/RAM exhaustion on low-memory systems (3.3 GiB RAM)
TRANSCRIPTION_SEMAPHORE = asyncio.Semaphore(1)
ACTIVE_CANCELLATIONS: set[str] = set()


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def get_system_memory_info() -> tuple[int, int]:
    """Returns (total_mb, available_mb) using procfs or standard os sysconf."""
    try:
        meminfo_path = Path("/proc/meminfo")
        if meminfo_path.exists():
            mem = {}
            for line in meminfo_path.read_text().splitlines():
                parts = line.split(":")
                if len(parts) == 2:
                    key = parts[0].strip()
                    val = parts[1].strip().split()[0]
                    mem[key] = int(val)
            total_mb = mem.get("MemTotal", 0) // 1024
            avail_mb = mem.get("MemAvailable", mem.get("MemFree", 0)) // 1024
            return total_mb, avail_mb
    except Exception:
        pass
    try:
        page_size = os.sysconf("SC_PAGE_SIZE")
        total_pages = os.sysconf("SC_PHYS_PAGES")
        avail_pages = os.sysconf("SC_AVPHYS_PAGES")
        total_mb = (page_size * total_pages) // (1024 * 1024)
        avail_mb = (page_size * avail_pages) // (1024 * 1024)
        return total_mb, avail_mb
    except Exception:
        return 4096, 2048


def get_disk_free_mb(path: Path) -> int:
    try:
        st = os.statvfs(path)
        return (st.f_bavail * st.f_frsize) // (1024 * 1024)
    except Exception:
        return 10240


@app.get("/health", response_model=HealthResponse)
def health_root():
    """Lightweight root health probe for Render health check path and UptimeRobot."""
    return HealthResponse(status="ok", app=settings.app_name, version=settings.app_version)


@app.get("/api/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="ok", app=settings.app_name, version=settings.app_version)



@app.get("/api/ready", response_model=ReadinessResponse)
async def ready(response: Response):
    """Production readiness probe for Kubernetes, Docker, or systemd."""
    ffmpeg_ok = command_exists("ffmpeg")
    ffprobe_ok = command_exists("ffprobe")
    try:
        import faster_whisper  # noqa: F401
        whisper_ok = True
    except Exception:
        whisper_ok = False

    try:
        import edge_tts  # noqa: F401
        tts_ok = True
    except Exception:
        tts_ok = False

    # Check directory writability
    storage_writable = False
    try:
        test_file = UPLOAD_DIR / f".readiness_test_{uuid.uuid4().hex}"
        test_file.write_text("ok")
        test_file.unlink(missing_ok=True)
        storage_writable = True
    except Exception:
        storage_writable = False

    active_count = len([j for j in list_jobs() if j.get("status") in ("processing", "uploading", "transcribing", "dubbing", "exporting")])
    checks = {
        "ffmpeg": ffmpeg_ok,
        "ffprobe": ffprobe_ok,
        "faster_whisper": whisper_ok,
        "tts": tts_ok,
        "storage_writable": storage_writable,
    }

    is_ready = ffmpeg_ok and ffprobe_ok and storage_writable
    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return ReadinessResponse(
        status="ready" if is_ready else "degraded",
        app=settings.app_name,
        version=settings.app_version,
        ffmpeg=ffmpeg_ok,
        ffprobe=ffprobe_ok,
        faster_whisper=whisper_ok,
        tts=tts_ok,
        storage_writable=storage_writable,
        active_jobs=active_count,
        checks=checks,
    )


# =============================================================================
# ANGKOR NEXUS AUTHENTICATION ENDPOINTS
# =============================================================================

@app.post("/api/auth/register", response_model=AuthResponse)
async def api_register(req: RegisterRequest, request: Request, response: Response):
    """Register a new user account with Argon2id hashed password, set HttpOnly cookie, and create session."""
    if not req.terms_accepted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="សូមយល់ព្រមលើលក្ខខណ្ឌប្រើប្រាស់ / You must agree to the Terms and Privacy Policy",
        )
    try:
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        user_dict, token = register_user(
            req.name, req.email, req.password, client_ip=client_ip, user_agent=user_agent
        )
        is_https = request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https"
        response.set_cookie(
            key="auth_token",
            value=token,
            max_age=30 * 86400,
            httponly=True,
            secure=is_https,
            samesite="none" if is_https else "lax",
            path="/",
        )
        return AuthResponse(
            success=True,
            user=UserProfile(**user_dict),
            token=token,
            message="គណនីត្រូវបានបង្កើតដោយជោគជ័យ / Account created successfully",
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        logger.error("Registration error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ការចុះឈ្មោះបរាជ័យ សូមព្យាយាមម្តងទៀត / Registration failed. Please try again.",
        )


@app.post("/api/auth/login", response_model=AuthResponse)
async def api_login(req: LoginRequest, request: Request, response: Response):
    """Authenticate existing user credentials via Argon2id, create session, and issue secure cookie."""
    try:
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        user_dict, token = login_user(
            req.email,
            req.password,
            remember_me=req.remember_me,
            client_ip=client_ip,
            user_agent=user_agent,
        )
        is_https = request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https"
        max_age = 30 * 86400 if req.remember_me else 86400
        response.set_cookie(
            key="auth_token",
            value=token,
            max_age=max_age,
            httponly=True,
            secure=is_https,
            samesite="none" if is_https else "lax",
            path="/",
        )
        return AuthResponse(
            success=True,
            user=UserProfile(**user_dict),
            token=token,
            message="ចូលប្រើប្រាស់បានជោគជ័យ / Logged in successfully",
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    except Exception as exc:
        logger.error("Login error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ការផ្ទៀងផ្ទាត់បរាជ័យ / Authentication failed.",
        )


@app.get("/api/auth/me", response_model=AuthStatusResponse)
async def api_get_me(request: Request, authorization: str | None = Header(None)):
    """Retrieve current authenticated user profile from Bearer token or HttpOnly cookie."""
    user_dict = get_current_user_optional(request, authorization)
    if not user_dict:
        return AuthStatusResponse(authenticated=False, user=None)
    return AuthStatusResponse(authenticated=True, user=UserProfile(**user_dict))


@app.post("/api/auth/logout")
async def api_logout(request: Request, response: Response, authorization: str | None = Header(None)):
    """Revoke session token and clear authentication cookie upon user logout."""
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:].strip()
    elif authorization and authorization.strip():
        token = authorization.strip()
    if not token:
        token = request.cookies.get("auth_token")
    if token:
        revoke_session(token)
    is_https = request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https"
    response.delete_cookie(key="auth_token", path="/", samesite="none" if is_https else "lax", secure=is_https)
    return {"success": True, "message": "បានចាកចេញដោយជោគជ័យ / Logged out successfully"}



@app.get("/api/system/diagnostics", response_model=SystemDiagnosticsResponse)
async def system_diagnostics():
    """Returns safe, sanitized diagnostic information for user troubleshooting without secrets."""
    total_mem, avail_mem = get_system_memory_info()
    free_disk = get_disk_free_mb(UPLOAD_DIR)

    try:
        import faster_whisper  # noqa: F401
        whisper_ok = True
    except Exception:
        whisper_ok = False

    try:
        import edge_tts  # noqa: F401
        tts_ok = True
    except Exception:
        tts_ok = False

    sanitized_cors = [str(o) for o in (settings.cors_origins if isinstance(settings.cors_origins, list) else settings.cors_origins.split(","))]
    active_count = len([j for j in list_jobs() if j.get("status") in ("processing", "uploading", "transcribing", "dubbing", "exporting")])

    return SystemDiagnosticsResponse(
        app_name=settings.app_name,
        app_version=settings.app_version,
        environment=settings.environment,
        platform=f"{platform.system()} {platform.release()} ({platform.machine()})",
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        cpu_cores=os.cpu_count() or 1,
        memory_total_mb=total_mem,
        memory_available_mb=avail_mem,
        storage_free_mb=free_disk,
        ffmpeg_available=command_exists("ffmpeg"),
        ffprobe_available=command_exists("ffprobe"),
        faster_whisper_available=whisper_ok,
        tts_engine_available=tts_ok,
        default_whisper_model=settings.default_whisper_model,
        supported_languages_count=len(SUPPORTED_LANGUAGES),
        concurrency_lock_active=active_count > 0,
        sanitized_cors_origins=sanitized_cors,
    )


@app.get("/api/languages", response_model=LanguagesResponse)
async def get_all_languages():
    """Returns curated supported multilingual source and target languages."""
    return LanguagesResponse(
        source_languages=[LanguageInfo(**l) for l in get_source_languages()],
        target_languages=[LanguageInfo(**l) for l in get_target_languages()],
        default_source_lang="auto",
        default_target_lang="km",
    )


@app.get("/api/capabilities", response_model=CapabilitiesResponse)
async def capabilities():
    try:
        import faster_whisper  # noqa: F401
        whisper_installed = True
    except Exception:
        whisper_installed = False

    voices = [VoiceInfo(**v) for v in get_available_khmer_voices()]

    return CapabilitiesResponse(
        ffmpeg=command_exists("ffmpeg"),
        ffprobe=command_exists("ffprobe"),
        faster_whisper=whisper_installed,
        default_model=settings.default_whisper_model,
        available_models=[m["id"] for m in AVAILABLE_MODELS],
        ollama=False,
        ollama_model="",
        ollama_models=[],
        tts=True,
        available_voices=voices,
        supported_languages_count=len(SUPPORTED_LANGUAGES),
        url_import=command_exists("yt-dlp"),
    )


@app.get("/api/transcription/models", response_model=ModelsResponse)
def get_transcription_models():
    models = [ModelInfo(**m) for m in get_available_models()]
    return ModelsResponse(models=models, default_model=settings.default_whisper_model)


async def _save_upload_and_validate(video: UploadFile) -> tuple[str, str, Path, float]:
    """Helper to stream upload, validate extension and media with ffprobe."""
    original_name = video.filename or "media.mp4"
    ext = Path(original_name).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported media extension: '{ext or '(none)'}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    job_id = uuid.uuid4().hex[:12]
    target_path = UPLOAD_DIR / f"{job_id}{ext}"
    max_bytes = settings.max_upload_mb * 1024 * 1024
    written = 0

    try:
        with target_path.open("wb") as out:
            while chunk := await video.read(1024 * 1024):  # 1MB chunks
                written += len(chunk)
                if written > max_bytes:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File exceeds maximum upload limit of {settings.max_upload_mb} MB.",
                    )
                out.write(chunk)
    except HTTPException:
        target_path.unlink(missing_ok=True)
        raise
    except Exception as exc:
        target_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving uploaded file: {exc}",
        ) from exc

    if written == 0:
        target_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    # Validate media integrity with ffprobe
    try:
        probe_info = await asyncio.to_thread(probe_media_file, target_path)
        duration = float(probe_info.get("duration", 0.0))
        if duration > 7200.0:
            target_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="វីដេអូមានរយៈពេលលើសពី 2 ម៉ោង (120 នាទី)។ Video duration exceeds the maximum limit of 2 hours (7200 seconds).",
            )
    except HTTPException:
        raise
    except Exception as exc:
        target_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Media validation failed: {exc}",
        )

    return job_id, original_name, target_path, duration


CHUNK_UPLOAD_DIR = (UPLOAD_DIR / ".chunks").resolve()
CHUNK_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
_CHUNK_METADATA_LOCK = threading.Lock()


def _clean_expired_upload_sessions(max_age_seconds: int = 86400) -> None:
    """Purges incomplete upload directories older than 24 hours."""
    now = time.time()
    try:
        for p in CHUNK_UPLOAD_DIR.iterdir():
            if p.is_dir():
                try:
                    if (now - p.stat().st_mtime) > max_age_seconds:
                        shutil.rmtree(p, ignore_errors=True)
                except Exception:
                    pass
    except Exception:
        pass


@app.post("/api/upload/init", response_model=UploadInitResponse)
async def init_chunked_upload(req: UploadInitRequest):
    """Initializes a resumable chunked media upload session."""
    original_name = req.filename or "media.mp4"
    ext = Path(original_name).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported media extension: '{ext or '(none)'}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    max_bytes = settings.max_upload_mb * 1024 * 1024
    if req.file_size <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size must be greater than 0 bytes.",
        )
    if req.file_size > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum upload limit of {settings.max_upload_mb} MB.",
        )

    free_mb = get_disk_free_mb(UPLOAD_DIR)
    needed_mb = (req.file_size / (1024 * 1024)) + 50
    if free_mb < needed_mb:
        raise HTTPException(
            status_code=status.HTTP_507_INSUFFICIENT_STORAGE,
            detail=f"Insufficient server storage space. Free: {free_mb} MB, Required: {int(needed_mb)} MB.",
        )

    _clean_expired_upload_sessions()

    upload_id = uuid.uuid4().hex[:16]
    session_dir = CHUNK_UPLOAD_DIR / upload_id
    session_dir.mkdir(parents=True, exist_ok=True)

    metadata = {
        "upload_id": upload_id,
        "filename": original_name,
        "file_size": req.file_size,
        "chunk_size": req.chunk_size,
        "total_chunks": req.total_chunks,
        "source_language": req.source_language or "auto",
        "target_language": req.target_language or "km",
        "name": req.name,
        "uploaded_chunks": [],
        "uploaded_bytes": 0,
        "created_at": utcnow(),
        "status": "in_progress",
    }
    meta_path = session_dir / "metadata.json"
    meta_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    expires_at = datetime.fromtimestamp(time.time() + 86400, timezone.utc).isoformat()
    return UploadInitResponse(
        upload_id=upload_id,
        filename=original_name,
        file_size=req.file_size,
        chunk_size=req.chunk_size,
        total_chunks=req.total_chunks,
        uploaded_chunks=[],
        expires_at=expires_at,
    )


@app.post("/api/upload/chunk", response_model=UploadChunkResponse)
async def upload_media_chunk(
    upload_id: str = Form(...),
    chunk_index: int = Form(...),
    chunk: UploadFile = File(...),
):
    """Receives and securely stores an individual chunk part for an active upload session."""
    session_dir = CHUNK_UPLOAD_DIR / upload_id
    meta_path = session_dir / "metadata.json"
    if not meta_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Upload session '{upload_id}' not found or has expired.",
        )

    try:
        metadata = json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to read upload session state.",
        ) from exc

    if chunk_index < 0 or chunk_index >= metadata["total_chunks"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid chunk index {chunk_index}. Total expected chunks: {metadata['total_chunks']}.",
        )

    part_file = session_dir / f"chunk_{chunk_index:05d}.part"
    chunk_bytes = await chunk.read()
    if not chunk_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Chunk {chunk_index} is empty.",
        )

    part_file.write_bytes(chunk_bytes)

    with _CHUNK_METADATA_LOCK:
        # Recalculate uploaded chunks and bytes based on physical part files
        part_files = sorted(session_dir.glob("chunk_*.part"))
        uploaded_indices = []
        total_written = 0
        for pf in part_files:
            try:
                idx = int(pf.stem.split("_")[1])
                uploaded_indices.append(idx)
                total_written += pf.stat().st_size
            except (ValueError, IndexError):
                continue

        metadata["uploaded_chunks"] = sorted(set(uploaded_indices))
        metadata["uploaded_bytes"] = total_written
        metadata["updated_at"] = utcnow()
        meta_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    return UploadChunkResponse(
        upload_id=upload_id,
        chunk_index=chunk_index,
        uploaded_chunks=metadata["uploaded_chunks"],
        uploaded_bytes=metadata["uploaded_bytes"],
        total_chunks=metadata["total_chunks"],
        file_size=metadata["file_size"],
        is_complete=(len(metadata["uploaded_chunks"]) == metadata["total_chunks"]),
    )


@app.get("/api/upload/status/{upload_id}", response_model=UploadStatusResponse)
async def get_upload_status(upload_id: str):
    """Retrieves current chunk progress for resumable uploads without double counting."""
    session_dir = CHUNK_UPLOAD_DIR / upload_id
    meta_path = session_dir / "metadata.json"
    if not meta_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Upload session '{upload_id}' not found.",
        )

    try:
        metadata = json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to read upload session state.",
        ) from exc

    # Confirm actual part files
    part_files = sorted(session_dir.glob("chunk_*.part"))
    uploaded_indices = []
    total_written = 0
    for pf in part_files:
        try:
            idx = int(pf.stem.split("_")[1])
            uploaded_indices.append(idx)
            total_written += pf.stat().st_size
        except (ValueError, IndexError):
            continue

    return UploadStatusResponse(
        upload_id=upload_id,
        filename=metadata["filename"],
        file_size=metadata["file_size"],
        chunk_size=metadata["chunk_size"],
        total_chunks=metadata["total_chunks"],
        uploaded_chunks=sorted(set(uploaded_indices)),
        uploaded_bytes=total_written,
        status=metadata.get("status", "in_progress"),
    )


@app.post("/api/upload/complete", response_model=JobResponse)
async def complete_chunked_upload(
    request: Request,
    authorization: str | None = Header(None),
    upload_id: str | None = None,
    source_language: str | None = None,
    target_language: str | None = None,
    name: str | None = None,
):
    """Assembles received chunks, validates media with ffprobe, and initializes the translation job."""
    current_user = get_current_user_optional(request, authorization)
    
    eff_upload_id = upload_id
    eff_src = source_language
    eff_tgt = target_language
    eff_name = name

    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            body = await request.json()
            if isinstance(body, dict):
                eff_upload_id = eff_upload_id or body.get("upload_id")
                eff_src = eff_src or body.get("source_language")
                eff_tgt = eff_tgt or body.get("target_language")
                eff_name = eff_name or body.get("name")
        except Exception:
            pass
    else:
        try:
            form = await request.form()
            eff_upload_id = eff_upload_id or form.get("upload_id")
            eff_src = eff_src or form.get("source_language")
            eff_tgt = eff_tgt or form.get("target_language")
            eff_name = eff_name or form.get("name")
        except Exception:
            try:
                body = await request.json()
                if isinstance(body, dict):
                    eff_upload_id = eff_upload_id or body.get("upload_id")
                    eff_src = eff_src or body.get("source_language")
                    eff_tgt = eff_tgt or body.get("target_language")
                    eff_name = eff_name or body.get("name")
            except Exception:
                pass

    if not eff_upload_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing upload_id parameter.",
        )

    session_dir = CHUNK_UPLOAD_DIR / eff_upload_id
    meta_path = session_dir / "metadata.json"
    if not meta_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Upload session '{eff_upload_id}' not found or already completed.",
        )

    metadata = json.loads(meta_path.read_text(encoding="utf-8"))
    total_chunks = metadata["total_chunks"]
    original_name = metadata["filename"]
    ext = Path(original_name).suffix.lower()

    # Verify all parts exist
    for idx in range(total_chunks):
        expected_part = session_dir / f"chunk_{idx:05d}.part"
        if not expected_part.exists():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing chunk index {idx} of {total_chunks}. Please upload missing chunks before completing.",
            )

    job_id = uuid.uuid4().hex[:12]
    target_path = UPLOAD_DIR / f"{job_id}{ext}"

    try:
        with target_path.open("wb") as out:
            for idx in range(total_chunks):
                part_file = session_dir / f"chunk_{idx:05d}.part"
                with part_file.open("rb") as src:
                    shutil.copyfileobj(src, out)
    except Exception as exc:
        target_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error assembling chunked upload: {exc}",
        ) from exc

    # Validate media with ffprobe
    try:
        probe_info = await asyncio.to_thread(probe_media_file, target_path)
        duration = float(probe_info.get("duration", 0.0))
        if duration > 7200.0:
            target_path.unlink(missing_ok=True)
            shutil.rmtree(session_dir, ignore_errors=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="វីដេអូមានរយៈពេលលើសពី 2 ម៉ោង (120 នាទី)។ Video duration exceeds the maximum limit of 2 hours (7200 seconds).",
            )
    except HTTPException:
        raise
    except Exception as exc:
        target_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Media validation failed for assembled file: {exc}",
        ) from exc

    # Clean up upload session
    shutil.rmtree(session_dir, ignore_errors=True)

    eff_src = eff_src or metadata.get("source_language") or "auto"
    eff_tgt = eff_tgt or metadata.get("target_language") or "km"
    eff_name = eff_name or metadata.get("name") or Path(original_name).stem

    job = {
        "id": job_id,
        "user_id": current_user["id"] if current_user else None,
        "filename": original_name,
        "name": (eff_name.strip() if eff_name and eff_name.strip() else Path(original_name).stem),
        "status": "uploaded",
        "stage": "queued",
        "progress": 0,
        "message": "ឯកសារបាន Upload និងផ្គុំដោយជោគជ័យ។ រួចរាល់សម្រាប់ Transcribe។",
        "created_at": utcnow(),
        "duration_seconds": duration,
        "source_language": eff_src,
        "target_language": eff_tgt,
        "speakers": [],
        "transcript": [],
        "translation": [],
        "error": None,
        "stages": {},
        "path": str(target_path),
        "voice_settings": {},
        "subtitle_styling": {},
    }
    save_job(job)
    return safe_job(job)


@app.delete("/api/upload/{upload_id}")
async def cancel_chunked_upload(upload_id: str):
    """Cancels and purges all partial chunks for an active upload session."""
    session_dir = CHUNK_UPLOAD_DIR / upload_id
    if session_dir.exists():
        shutil.rmtree(session_dir, ignore_errors=True)
    return {"message": "Upload session cancelled and cleaned up.", "upload_id": upload_id}


@app.post("/api/upload", response_model=JobResponse)
async def upload_direct_media(
    request: Request,
    authorization: str | None = Header(None),
    video: UploadFile | None = File(None),
    file: UploadFile | None = File(None),
    source_language: str = Form(default="auto"),
    target_language: str = Form(default="km"),
    name: str | None = Form(default=None),
):
    """Unified direct upload endpoint compatible with both 'video' and 'file' multipart fields."""
    current_user = get_current_user_optional(request, authorization)
    media_file = video or file
    if not media_file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No media file provided in request. Expecting 'video' or 'file' multipart field.",
        )
    job_id, original_name, target_path, duration = await _save_upload_and_validate(media_file)

    job = {
        "id": job_id,
        "user_id": current_user["id"] if current_user else None,
        "filename": original_name,
        "name": (name.strip() if name and name.strip() else Path(original_name).stem),
        "status": "uploaded",
        "stage": "queued",
        "progress": 0,
        "message": "ឯកសារបាន Upload ដោយជោគជ័យ។ រួចរាល់សម្រាប់ Transcribe។",
        "created_at": utcnow(),
        "duration_seconds": duration,
        "source_language": source_language or "auto",
        "target_language": target_language or "km",
        "speakers": [],
        "transcript": [],
        "translation": [],
        "error": None,
        "stages": {},
        "path": str(target_path),
        "voice_settings": {},
        "subtitle_styling": {},
    }
    save_job(job)
    return safe_job(job)


@app.post("/api/jobs", response_model=JobResponse)
async def create_job(
    request: Request,
    authorization: str | None = Header(None),
    video: UploadFile | None = File(None),
    file: UploadFile | None = File(None),
    media: UploadFile | None = File(None),
    source_language: str = Form(default="auto"),
    target_language: str = Form(default="km"),
    name: str | None = Form(default=None),
):
    current_user = get_current_user_optional(request, authorization)
    upload_file = video or file or media
    if not upload_file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing media file. Please provide a file in field 'video', 'file', or 'media'.",
        )
    job_id, original_name, target_path, duration = await _save_upload_and_validate(upload_file)

    job = {
        "id": job_id,
        "user_id": current_user["id"] if current_user else None,
        "filename": original_name,
        "name": (name.strip() if name and name.strip() else Path(original_name).stem),
        "status": "uploaded",
        "stage": "queued",
        "progress": 0,
        "message": "ឯកសារបាន Upload ដោយជោគជ័យ។ រួចរាល់សម្រាប់ Transcribe។",
        "created_at": utcnow(),
        "duration_seconds": duration,
        "source_language": source_language or "auto",
        "target_language": target_language or "km",
        "speakers": [],
        "transcript": [],
        "translation": [],
        "error": None,
        "stages": {},
        "path": str(target_path),
        "voice_settings": {},
        "subtitle_styling": {},
    }
    save_job(job)
    return safe_job(job)


@app.post("/api/jobs/import-url", response_model=JobResponse)
async def import_media_from_url(request: Request, authorization: str | None = Header(None)):
    """
    Safely imports media from a valid URL.
    Supports both JSON payloads and Form-encoded data, direct media links (.mp4, .webm, .wav, etc.) and supported platforms via yt-dlp where permitted.
    """
    content_type = request.headers.get("content-type", "").lower()
    raw_url: str = ""
    source_language: str = "auto"
    target_language: str = "km"

    if "application/json" in content_type:
        try:
            body = await request.json()
            raw_url = str(body.get("url", ""))
            source_language = str(body.get("source_language", "auto"))
            target_language = str(body.get("target_language", "km"))
        except Exception:
            pass
    else:
        try:
            form = await request.form()
            raw_url = str(form.get("url", ""))
            source_language = str(form.get("source_language", "auto"))
            target_language = str(form.get("target_language", "km"))
        except Exception:
            pass

    clean_url = raw_url.strip()
    if not clean_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL is required. សូមបញ្ចូលតំណភ្ជាប់វីដេអូ ឬ URL មេឌៀ។",
        )
    if not (clean_url.startswith("http://") or clean_url.startswith("https://")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid URL scheme. Only HTTP and HTTPS URLs are permitted.",
        )

    job_id = uuid.uuid4().hex[:12]
    out_media_file = UPLOAD_DIR / f"{job_id}.mp4"

    # Strategy 1: Check if it is a direct media file
    is_direct_media = any(clean_url.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS)

    if is_direct_media or not command_exists("yt-dlp"):
        try:
            async with httpx.AsyncClient(timeout=45.0, follow_redirects=True) as client:
                resp = await client.get(clean_url)
                if resp.status_code != 200:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Failed to fetch media from URL (HTTP {resp.status_code}).",
                    )
                content = resp.content
                if len(content) > settings.max_upload_mb * 1024 * 1024:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"Media from URL exceeds {settings.max_upload_mb} MB limit.",
                    )
                out_media_file.write_bytes(content)
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Direct URL download failed: {exc}. Please upload the video file directly.",
            )
    else:
        # Strategy 2: yt-dlp with safe constraints
        cmd = [
            "yt-dlp",
            "--no-playlist",
            "--max-filesize", f"{settings.max_upload_mb}M",
            "-f", "bestvideo[ext=mp4][height<=720]+bestaudio[ext=m4a]/best[ext=mp4][height<=720]/best[height<=720]/best",
            "-o", str(out_media_file),
            clean_url,
        ]
        try:
            proc = await asyncio.to_thread(
                subprocess.run, cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=120
            )
            if proc.returncode != 0 or not out_media_file.exists():
                err = proc.stderr[-300:] if proc.stderr else "Unknown error"
                raise RuntimeError(err)
        except Exception as exc:
            out_media_file.unlink(missing_ok=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Platform URL import failed or is restricted: {str(exc)[:150]}. "
                    "Please download the video to your computer and upload it directly."
                ),
            )

    # Validate downloaded media with ffprobe
    try:
        probe_info = await asyncio.to_thread(probe_media_file, out_media_file)
        duration = float(probe_info.get("duration", 0.0))
    except Exception as exc:
        out_media_file.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Imported media validation failed: {exc}",
        )

    current_user = get_current_user_optional(request, authorization)
    job = {
        "id": job_id,
        "user_id": current_user["id"] if current_user else None,
        "filename": Path(clean_url.split("?")[0]).name or f"{job_id}.mp4",
        "name": f"Imported Video ({job_id})",
        "status": "uploaded",
        "stage": "queued",
        "progress": 0,
        "message": "វីដេអូត្រូវបានទាញយក និងត្រួតពិនិត្យដោយជោគជ័យ។",
        "created_at": utcnow(),
        "duration_seconds": duration,
        "source_language": source_language or "auto",
        "target_language": target_language or "km",
        "speakers": [],
        "transcript": [],
        "translation": [],
        "error": None,
        "stages": {},
        "path": str(out_media_file),
        "voice_settings": {},
        "subtitle_styling": {},
    }
    save_job(job)
    return safe_job(job)


@app.get("/api/jobs")
async def get_all_jobs(request: Request, authorization: str | None = Header(None)):
    current_user = get_current_user_optional(request, authorization)
    if current_user:
        jobs = list_jobs(user_id=current_user["id"], include_unowned=False)
    else:
        jobs = [j for j in list_jobs() if not j.get("user_id")]
    return [safe_job(j) for j in jobs]


@app.get("/api/jobs/{job_id}", response_model=JobResponse)
async def get_job_by_id(job_id: str, request: Request, authorization: str | None = Header(None)):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    current_user = get_current_user_optional(request, authorization)
    check_job_access(job, current_user)
    return safe_job(job)


@app.delete("/api/jobs/{job_id}")
async def remove_job(job_id: str, request: Request, authorization: str | None = Header(None)):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    current_user = get_current_user_optional(request, authorization)
    check_job_access(job, current_user)
    success = delete_job(job_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return {"status": "deleted", "id": job_id}


async def _execute_transcription(
    job: dict[str, Any],
    model_id: str,
    language: str | None,
    target_language: str | None = None,
    auto_diarize: bool = True,
    auto_translate: bool = False,
    auto_dub: bool = False,
    vad_filter: bool = True,
) -> dict[str, Any]:
    job_id = job["id"]
    file_path = Path(job["path"])
    target_lang = target_language or job.get("target_language") or "km"

    if not file_path.exists():
        update_job(
            job_id,
            {
                "status": "failed",
                "stage": "failed",
                "progress": 0,
                "message": "Media file is missing from server storage. Please re-upload.",
                "error": "Media file is missing from server storage. Please re-upload.",
            },
            persist_disk=True,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Media file is missing from server storage. Please re-upload.",
        )

    start_time = time.time()
    last_update_time = [0.0]

    def set_progress(
        stage: str,
        progress: int,
        message: str,
        processed_duration: float | None = None,
        total_duration: float | None = None,
        persist: bool = False,
    ):
        elapsed = round(time.time() - start_time, 1)
        eta = None
        if processed_duration and total_duration and processed_duration > 2.0 and total_duration > processed_duration and elapsed > 0.5:
            rate = processed_duration / elapsed
            if rate > 0.05:
                eta = round((total_duration - processed_duration) / rate, 1)

        # Stage completion is strictly sequential and verified:
        validating_done = progress >= 10 or stage in ("extracting_audio", "transcribing", "detecting_speakers", "generating_subtitles", "completed")
        extracting_done = progress >= 15 or stage in ("transcribing", "detecting_speakers", "generating_subtitles", "completed")
        transcribing_done = progress >= 85 or stage in ("detecting_speakers", "generating_subtitles", "completed")
        detecting_done = progress >= 92 or stage in ("generating_subtitles", "completed")
        generating_done = progress >= 98 or stage == "completed" or progress >= 100

        # Prerequisite safeguard: if progress reaches 100% or stage is completed, all prerequisites resolve to completed
        if progress >= 100 or stage == "completed":
            validating_done = True
            extracting_done = True
            transcribing_done = True
            detecting_done = True
            generating_done = True

        stage_statuses = {
            "validating": "completed" if validating_done else "active" if stage == "validating" else "pending",
            "extracting_audio": "completed" if extracting_done else "active" if stage == "extracting_audio" else "pending",
            "transcribing": "completed" if transcribing_done else "active" if stage == "transcribing" else "pending",
            "detecting_speakers": "completed" if detecting_done else "active" if stage == "detecting_speakers" else "pending",
            "generating_subtitles": "completed" if generating_done else "active" if stage == "generating_subtitles" else "pending",
            "completed": "completed" if (progress >= 100 or stage == "completed") else "pending",
        }

        updates = {
            "status": stage if progress < 100 else "transcribed",
            "stage": stage,
            "progress": min(max(int(progress), 0), 100),
            "message": message,
            "elapsed_seconds": elapsed,
            "eta_seconds": eta,
            "processed_duration": round(processed_duration, 2) if processed_duration is not None else None,
            "duration_seconds": round(total_duration, 2) if total_duration is not None else job.get("duration_seconds"),
            "stages": stage_statuses,
            "error": None,
        }
        return update_job(job_id, updates, persist_disk=persist)

    # Stage 1: Validating
    set_progress("validating", 5, "ផ្ទៀងផ្ទាត់ឯកសារមេឌៀ (Validating media format with FFprobe)...", persist=True)

    wav_path = UPLOAD_DIR / f"{job_id}_clean.wav"

    async with TRANSCRIPTION_SEMAPHORE:
        if job_id in ACTIVE_CANCELLATIONS:
            ACTIVE_CANCELLATIONS.discard(job_id)
            updated = update_job(
                job_id,
                {
                    "status": "cancelled",
                    "stage": "cancelled",
                    "message": "ដំណើរការត្រូវបានបោះបង់ដោយអ្នកប្រើប្រាស់ (Cancelled by user)",
                },
                persist_disk=True,
            )
            return safe_job(updated or job)

        try:
            # Media validation with FFprobe
            probe_info = await asyncio.to_thread(probe_media_file, file_path)
            total_duration = float(probe_info.get("duration", 0.0)) or float(job.get("duration_seconds", 0.0) or 0.0)

            if job_id in ACTIVE_CANCELLATIONS:
                ACTIVE_CANCELLATIONS.discard(job_id)
                updated = update_job(job_id, {"status": "cancelled", "stage": "cancelled", "message": "Cancelled by user"}, persist_disk=True)
                return safe_job(updated or job)

            # Stage 2: Audio extraction via FFmpeg
            set_progress(
                "extracting_audio",
                10,
                "ទាញយក និងសម្រួលសំឡេងជា 16kHz Mono (Extracting audio with FFmpeg)...",
                total_duration=total_duration,
                persist=True,
            )
            try:
                extracted_wav = await asyncio.to_thread(extract_audio_stream, file_path, wav_path)
                transcribe_input = extracted_wav
            except Exception as extract_err:
                logger.warning("FFmpeg extraction fallback: using original %s: %s", file_path, extract_err)
                transcribe_input = file_path

            if job_id in ACTIVE_CANCELLATIONS:
                ACTIVE_CANCELLATIONS.discard(job_id)
                updated = update_job(job_id, {"status": "cancelled", "stage": "cancelled", "message": "Cancelled by user"}, persist_disk=True)
                return safe_job(updated or job)

            # Mark Step 2 completed and transition strictly sequentially to Step 3
            set_progress(
                "transcribing",
                15,
                f"ការបំប្លែងសំឡេងរួចរាល់។ ចាប់ផ្តើមស្គាល់សំឡេងដោយ Faster-Whisper ({model_id})...",
                total_duration=total_duration,
                persist=True,
            )

            def on_segment(current_end: float, dur: float, seg_dict: dict[str, Any]):
                nonlocal total_duration
                d = dur if dur > 0 else total_duration
                if d <= 0:
                    d = max(current_end, 1.0)
                total_duration = d
                ratio = min(current_end / d, 1.0)
                calc_progress = 15 + int(ratio * 70)  # Range 15% -> 85%
                now = time.time()
                if now - last_update_time[0] >= 0.3 or calc_progress >= 85:
                    last_update_time[0] = now
                    msg = f"ស្គាល់សំឡេង: {current_end:.1f}s / {d:.1f}s ({int(ratio * 100)}%)"
                    set_progress("transcribing", calc_progress, msg, processed_duration=current_end, total_duration=d, persist=False)

            def check_cancelled() -> bool:
                return job_id in ACTIVE_CANCELLATIONS

            whisper_lang = normalize_whisper_code(language)
            result = await asyncio.to_thread(
                transcribe_media,
                file_path=transcribe_input,
                model_id=model_id,
                language=whisper_lang,
                device=settings.whisper_device,
                compute_type=settings.whisper_compute_type,
                vad_filter=vad_filter,
                progress_callback=on_segment,
                cancel_check=check_cancelled,
            )

            segments = result.get("segments", [])
            detected_src_lang = result.get("source_language")

            # Stage 4: Multi-speaker Diarization & Character Profiling
            speaker_profiles: list[dict[str, Any]] = []
            if auto_diarize and wav_path.exists() and len(segments) > 0:
                set_progress(
                    "detecting_speakers",
                    88,
                    "វិភាគសំឡេង និងកំណត់អត្តសញ្ញាណតួអង្គនិយាយ (Detecting speakers & voice profiles)...",
                    total_duration=total_duration,
                    persist=True,
                )
                try:
                    updated_segs, profiles = await asyncio.to_thread(
                        diarize_and_profile_audio,
                        wav_path=wav_path,
                        segments=segments,
                        target_language=target_lang,
                    )
                    segments = updated_segs
                    speaker_profiles = profiles
                except Exception as diarize_err:
                    logger.warning("Speaker diarization fallback: %s", diarize_err)
                    speaker_profiles = [
                        {
                            "id": "speaker_1",
                            "speaker_id": "speaker_1",
                            "name": "Speaker 1",
                            "gender_presentation": "adult",
                            "age_impression": "adult",
                            "speaking_style": "conversational",
                            "speaking_speed": "normal",
                            "confidence": 0.85,
                            "assigned_voice_id": "km-KH-PisethNeural",
                            "segment_count": len(segments),
                            "total_duration": total_duration,
                            "sample_dialogue": [s["text"] for s in segments[:3]],
                        }
                    ]
                    for s in segments:
                        s["speaker_id"] = "speaker_1"

            # Optional Auto-Translation
            translated_segments: list[dict[str, Any]] = []
            if (auto_translate or auto_dub) and len(segments) > 0:
                set_progress("translating", 93, f"បកប្រែជាភាសា {target_lang}...", total_duration=total_duration, persist=True)
                try:
                    translated_segments = await translate_segments(
                        segments,
                        source_lang=detected_src_lang or language or "auto",
                        target_lang=target_lang,
                    )
                    # Context-Aware Khmer Proofreading & Unicode Normalization Pipeline
                    if target_lang == "km" and translated_segments:
                        set_progress("translating", 95, "កំពុងផ្ទៀងផ្ទាត់អក្ខរាវិរុទ្ធ និងវេយ្យាករណ៍ភាសាខ្មែរ (Khmer Proofreading)...", total_duration=total_duration, persist=True)
                        try:
                            proof_out = khmer_proofreader.proofread_segments(
                                translated_segments,
                                source_segments=segments,
                                auto_apply_high_confidence=True,
                            )
                            for s, r in zip(translated_segments, proof_out["results"]):
                                if r.get("applied_automatically"):
                                    s["text"] = r["suggested_khmer"]
                        except Exception as p_err:
                            logger.warning("Auto proofreading failed: %s", p_err)
                except Exception as t_err:
                    logger.warning("Auto translation failed: %s", t_err)

            # Optional Auto-Dubbing
            has_dubbed_audio = False
            dubbed_audio_url = None
            if auto_dub and len(segments) > 0:
                dub_segments = translated_segments if translated_segments else segments
                set_progress("dubbing", 96, f"កំពុងបង្កើតសំឡេង AI Dubbing ស្វ័យប្រវត្តិ ({target_lang})...", total_duration=total_duration, persist=True)
                try:
                    out_dubbed = OUTPUT_DIR / f"{job_id}_dubbed.mp3"
                    raw_dubbed = OUTPUT_DIR / f"{job_id}_raw_dubbed.mp3"
                    spk_voices = {p["speaker_id"]: p["assigned_voice_id"] for p in speaker_profiles if p.get("speaker_id") and p.get("assigned_voice_id")}
                    spk_rates = {p["speaker_id"]: p.get("speech_rate", 0) for p in speaker_profiles if p.get("speaker_id")}
                    default_voice = get_default_voice_for_language(target_lang or "km")
                    primary_voice = (
                        speaker_profiles[0]["assigned_voice_id"]
                        if (speaker_profiles and speaker_profiles[0].get("assigned_voice_id"))
                        else default_voice
                    )

                    await generate_dubbed_audio_track(
                        segments=dub_segments,
                        output_audio_path=raw_dubbed,
                        voice_id=primary_voice,
                        speaker_voices=spk_voices,
                        speaker_rates=spk_rates,
                        total_duration=float(total_duration or 10.0),
                        original_media_path=wav_path,
                        preserve_nonverbal=True,
                    )

                    if wav_path.exists():
                        await asyncio.to_thread(
                            mix_audio_tracks,
                            original_audio_path=wav_path,
                            dubbed_audio_path=raw_dubbed,
                            output_mixed_path=out_dubbed,
                            voice_volume=1.0,
                            original_volume=0.85,
                            preserve_soundtrack=True,
                            ducking_intensity=0.35,
                        )
                        raw_dubbed.unlink(missing_ok=True)
                    else:
                        if raw_dubbed.exists():
                            shutil.move(str(raw_dubbed), str(out_dubbed))

                    if out_dubbed.exists() and verify_audio_is_audible(out_dubbed):
                        has_dubbed_audio = True
                        dubbed_audio_url = f"/api/jobs/{job_id}/dubbed-audio"
                except Exception as d_err:
                    logger.warning("Auto-dubbing failed: %s", d_err)

            # Stage 5: Subtitle generation
            set_progress(
                "generating_subtitles",
                98,
                "បង្កើត និងរក្សាទុកឯកសារ Subtitle SRT & Plain Text...",
                total_duration=total_duration,
                persist=True,
            )

            srt_content = build_srt_content(segments)
            txt_content = build_txt_content(segments, include_timestamps=True)
            vtt_content = build_vtt_content(segments)
            srt_path = OUTPUT_DIR / f"{job_id}.srt"
            txt_path = OUTPUT_DIR / f"{job_id}.txt"
            vtt_path = OUTPUT_DIR / f"{job_id}.vtt"
            srt_path.write_text(srt_content, encoding="utf-8")
            txt_path.write_text(txt_content, encoding="utf-8")
            vtt_path.write_text(vtt_content, encoding="utf-8")

            # Stage 6: Completed
            final_duration = result.get("duration") or total_duration
            completed_job = update_job(
                job_id,
                {
                    "status": "transcribed",
                    "stage": "completed",
                    "progress": 100,
                    "message": "ដំណើរការស្គាល់សំឡេងបានជោគជ័យពេញលេញ (100%)",
                    "transcript": segments,
                    "translation": translated_segments,
                    "speakers": speaker_profiles,
                    "source_language": language or detected_src_lang or "auto",
                    "detected_source_language": detected_src_lang,
                    "target_language": target_lang,
                    "model_used": result.get("model_used"),
                    "duration_seconds": round(float(final_duration), 2) if final_duration else None,
                    "processed_duration": round(float(final_duration), 2) if final_duration else None,
                    "elapsed_seconds": round(time.time() - start_time, 1),
                    "eta_seconds": 0.0,
                    "output_srt_path": str(srt_path),
                    "output_txt_path": str(txt_path),
                    "has_dubbed_audio": has_dubbed_audio,
                    "dubbed_audio_url": dubbed_audio_url,
                    "error": None,
                    "stages": {
                        "validating": "completed",
                        "extracting_audio": "completed",
                        "transcribing": "completed",
                        "detecting_speakers": "completed",
                        "generating_subtitles": "completed",
                        "completed": "completed",
                    },
                },
                persist_disk=True,
            )
            return safe_job(completed_job or job)

        except InterruptedError:
            ACTIVE_CANCELLATIONS.discard(job_id)
            updated = update_job(
                job_id,
                {
                    "status": "cancelled",
                    "stage": "cancelled",
                    "message": "ដំណើរការត្រូវបានបោះបង់ដោយអ្នកប្រើប្រាស់ (Cancelled by user)",
                },
                persist_disk=True,
            )
            return safe_job(updated or job)
        except Exception as exc:
            logger.error("Job %s execution failed: %s", job_id, exc)
            ACTIVE_CANCELLATIONS.discard(job_id)
            failed_job = update_job(
                job_id,
                {
                    "status": "failed",
                    "stage": "failed",
                    "message": f"Processing failed: {exc}",
                    "error": str(exc),
                    "stages": {"failed": "failed"},
                },
                persist_disk=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Speech recognition failed: {exc}",
            ) from exc


@app.post("/api/jobs/{job_id}/transcribe", response_model=JobResponse)
async def transcribe_job(
    job_id: str,
    model: str = Query(default="tiny"),
    language: str | None = Query(default=None),
    target_language: str = Query(default="km"),
    auto_diarize: bool = Query(default=True),
    auto_translate: bool = Query(default=False),
    auto_dub: bool = Query(default=False),
):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    ACTIVE_CANCELLATIONS.discard(job_id)
    return await _execute_transcription(
        job,
        model_id=model,
        language=language or job.get("source_language"),
        target_language=target_language or job.get("target_language"),
        auto_diarize=auto_diarize,
        auto_translate=auto_translate or auto_dub,
        auto_dub=auto_dub,
    )


@app.post("/api/jobs/{job_id}/diarize", response_model=JobResponse)
async def diarize_job(job_id: str):
    """Manually triggers or re-runs speaker diarization and voice profiling."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    segments = job.get("transcript", [])
    if not segments:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Transcribe the media before detecting speakers.")

    wav_path = UPLOAD_DIR / f"{job_id}_clean.wav"
    if not wav_path.exists():
        media_path = _find_job_media_path(job_id, job)
        await asyncio.to_thread(extract_audio_stream, media_path, wav_path)

    target_lang = job.get("target_language", "km")
    updated_segs, profiles = await asyncio.to_thread(
        diarize_and_profile_audio,
        wav_path=wav_path,
        segments=segments,
        target_language=target_lang,
    )

    # Sync speaker_id to translation segments if available
    trans_segs = list(job.get("translation", []))
    for idx, t_seg in enumerate(trans_segs):
        if idx < len(updated_segs):
            t_seg["speaker_id"] = updated_segs[idx].get("speaker_id")

    updated = update_job(
        job_id,
        {
            "transcript": updated_segs,
            "translation": trans_segs,
            "speakers": profiles,
            "updated_at": utcnow(),
        },
        persist_disk=True,
    )
    return safe_job(updated or job)


@app.put("/api/jobs/{job_id}/speakers", response_model=JobResponse)
def update_speakers(job_id: str, payload: SpeakerUpdateRequest):
    """Updates editable character names, assigned voices, and profiles."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    updated = update_job(
        job_id,
        {"speakers": [s.model_dump() for s in payload.speakers], "updated_at": utcnow()},
        persist_disk=True,
    )
    return safe_job(updated or job)


@app.post("/api/jobs/{job_id}/speakers/merge", response_model=JobResponse)
def merge_speakers_endpoint(job_id: str, payload: SpeakerMergeRequest):
    """Merges two speaker profiles together and reassigns dialogue segments."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    keep_id = payload.speaker_id_keep
    merge_id = payload.speaker_id_merge

    transcript = list(job.get("transcript", []))
    for s in transcript:
        if s.get("speaker_id") == merge_id:
            s["speaker_id"] = keep_id

    translation = list(job.get("translation", []))
    for s in translation:
        if s.get("speaker_id") == merge_id:
            s["speaker_id"] = keep_id

    # Filter out merged speaker from profiles and update count
    profiles = [p for p in job.get("speakers", []) if p.get("speaker_id") != merge_id]
    for p in profiles:
        if p.get("speaker_id") == keep_id:
            p["segment_count"] = sum(1 for s in transcript if s.get("speaker_id") == keep_id)

    updated = update_job(
        job_id,
        {
            "transcript": transcript,
            "translation": translation,
            "speakers": profiles,
            "updated_at": utcnow(),
        },
        persist_disk=True,
    )
    return safe_job(updated or job)


@app.post("/api/jobs/{job_id}/speakers/split", response_model=JobResponse)
def split_speaker_endpoint(job_id: str, payload: SpeakerSplitRequest):
    """Splits selected segments into a new speaker."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    existing_speakers = list(job.get("speakers", []))
    new_spk_num = len(existing_speakers) + 1
    new_spk_id = f"speaker_{new_spk_num}"
    new_name = payload.new_speaker_name or f"Speaker {new_spk_num}"

    target_ids = set(payload.segment_ids)
    transcript = list(job.get("transcript", []))
    for s in transcript:
        if s.get("id") in target_ids:
            s["speaker_id"] = new_spk_id

    translation = list(job.get("translation", []))
    for s in translation:
        if s.get("id") in target_ids:
            s["speaker_id"] = new_spk_id

    new_profile = {
        "id": new_spk_id,
        "speaker_id": new_spk_id,
        "name": new_name,
        "gender_presentation": "adult",
        "age_impression": "adult",
        "speaking_style": "conversational",
        "speaking_speed": "normal",
        "confidence": 0.85,
        "assigned_voice_id": "km-KH-PisethNeural",
        "segment_count": len(target_ids),
        "total_duration": 0.0,
        "sample_dialogue": [s["text"] for s in transcript if s.get("speaker_id") == new_spk_id][:3],
    }
    existing_speakers.append(new_profile)

    updated = update_job(
        job_id,
        {
            "transcript": transcript,
            "translation": translation,
            "speakers": existing_speakers,
            "updated_at": utcnow(),
        },
        persist_disk=True,
    )
    return safe_job(updated or job)


@app.get("/api/transcription/jobs/{job_id}", response_model=JobResponse)
def get_transcription_job(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return safe_job(job)


@app.get("/api/transcription/jobs/{job_id}/result")
def get_transcription_result(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return {
        "id": job["id"],
        "status": job["status"],
        "source_language": job.get("source_language"),
        "target_language": job.get("target_language"),
        "model_used": job.get("model_used"),
        "duration_seconds": job.get("duration_seconds"),
        "transcript": job.get("transcript", []),
        "translation": job.get("translation", []),
        "speakers": job.get("speakers", []),
        "error": job.get("error"),
    }


@app.get("/api/jobs/{job_id}/progress", response_model=JobProgressResponse)
async def get_job_progress(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    safe = safe_job(job)
    return {
        "id": safe["id"],
        "status": safe.get("status", "queued"),
        "stage": safe.get("stage"),
        "progress": safe.get("progress", 0),
        "message": safe.get("message"),
        "elapsed_seconds": safe.get("elapsed_seconds"),
        "eta_seconds": safe.get("eta_seconds"),
        "processed_duration": safe.get("processed_duration"),
        "total_duration": safe.get("duration_seconds"),
        "error": safe.get("error"),
        "stages": safe.get("stages", {}),
    }


@app.get("/api/jobs/{job_id}/events")
async def job_events_stream(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    async def event_generator():
        queue: asyncio.Queue = asyncio.Queue(maxsize=50)
        add_job_listener(job_id, queue)
        try:
            current = get_job(job_id)
            if current:
                yield f"data: {json.dumps(safe_job(current), ensure_ascii=False)}\n\n"
                if current.get("status") in ("transcribed", "completed", "failed", "cancelled"):
                    return

            while True:
                try:
                    data = await asyncio.wait_for(queue.get(), timeout=10.0)
                    yield f"data: {json.dumps(safe_job(data), ensure_ascii=False)}\n\n"
                    if data.get("status") in ("transcribed", "completed", "failed", "cancelled"):
                        break
                except asyncio.TimeoutError:
                    yield ": ping\n\n"
                    refreshed = get_job(job_id)
                    if refreshed and refreshed.get("status") in ("transcribed", "completed", "failed", "cancelled"):
                        yield f"data: {json.dumps(safe_job(refreshed), ensure_ascii=False)}\n\n"
                        break
        finally:
            remove_job_listener(job_id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@app.post("/api/jobs/{job_id}/retry", response_model=JobResponse)
async def retry_job_endpoint(job_id: str, model: str = Query(default="tiny")):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    ACTIVE_CANCELLATIONS.discard(job_id)
    updated = update_job(
        job_id,
        {
            "status": "queued",
            "stage": "queued",
            "progress": 0,
            "message": "រៀបចំចាប់ផ្តើមដំណើរការឡើងវិញ (Retrying job)...",
            "error": None,
            "elapsed_seconds": 0.0,
            "eta_seconds": None,
            "processed_duration": 0.0,
            "stages": {},
        },
        persist_disk=True,
    )
    return await _execute_transcription(
        updated or job,
        model_id=model,
        language=job.get("source_language"),
        target_language=job.get("target_language"),
    )


@app.post("/api/jobs/{job_id}/cancel")
@app.post("/api/transcription/jobs/{job_id}/cancel")
async def cancel_transcription_job(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    ACTIVE_CANCELLATIONS.add(job_id)
    updated = update_job(
        job_id,
        {
            "status": "cancelled",
            "stage": "cancelled",
            "message": "ដំណើរការត្រូវបានបោះបង់ដោយអ្នកប្រើប្រាស់ (Cancelled by user)",
        },
        persist_disk=True,
    )
    return {"status": "cancelled", "job": safe_job(updated or job)}


@app.patch("/api/jobs/{job_id}", response_model=JobResponse)
async def update_project_metadata(job_id: str, payload: ProjectUpdateRequest):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    updates: dict[str, Any] = {"updated_at": utcnow()}
    if payload.name is not None:
        updates["name"] = payload.name.strip()
    if payload.source_language is not None:
        updates["source_language"] = payload.source_language
    if payload.target_language is not None:
        updates["target_language"] = payload.target_language
    if payload.speakers is not None:
        updates["speakers"] = [s.model_dump() for s in payload.speakers]
    if payload.voice_settings is not None:
        current_voice = dict(job.get("voice_settings", {}))
        current_voice.update(payload.voice_settings)
        updates["voice_settings"] = current_voice
    if payload.subtitle_styling is not None:
        current_style = dict(job.get("subtitle_styling", {}))
        current_style.update(payload.subtitle_styling)
        updates["subtitle_styling"] = current_style

    updated = update_job(job_id, updates)
    return safe_job(updated or job)


@app.put("/api/jobs/{job_id}/transcript", response_model=JobResponse)
def update_transcript(job_id: str, payload: TranscriptUpdateRequest, target: str = Query(default="transcript")):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    key = "translation" if target == "translation" else "transcript"
    existing_segs = {s.get("id"): s for s in job.get(key, [])}

    validated = []
    for idx, s in enumerate(payload.segments, start=1):
        if s.start < 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Segment #{idx} start time cannot be negative.")
        if s.end <= s.start:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Segment #{idx} end time must be greater than start time.")

        prev = existing_segs.get(s.id, {})
        entry: dict[str, Any] = {
            "id": idx,
            "start": round(float(s.start), 3),
            "end": round(float(s.end), 3),
            "text": str(s.text).strip(),
        }
        spk = s.speaker_id or prev.get("speaker_id")
        if spk:
            entry["speaker_id"] = spk
        conf = s.confidence if s.confidence is not None else prev.get("confidence")
        if conf is not None:
            entry["confidence"] = conf
        validated.append(entry)

    updated = update_job(job_id, {key: validated, "updated_at": utcnow()})
    return safe_job(updated or job)


@app.post("/api/jobs/{job_id}/transcript/split", response_model=JobResponse)
def split_transcript_segment(job_id: str, payload: SubtitleSplitRequest):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    key = "translation" if payload.target == "translation" else "transcript"
    segments = list(job.get(key, []))

    idx = next((i for i, s in enumerate(segments) if s.get("id") == payload.segment_id), None)
    if idx is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Segment #{payload.segment_id} not found")

    target_seg = segments[idx]
    orig_start = float(target_seg.get("start", 0.0))
    orig_end = float(target_seg.get("end", 0.0))
    spk_id = target_seg.get("speaker_id")

    if not (orig_start < payload.split_time < orig_end):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Split timestamp ({payload.split_time:.2f}s) must be strictly between start ({orig_start:.2f}s) and end ({orig_end:.2f}s).",
        )

    part1 = {"id": 0, "start": orig_start, "end": round(payload.split_time, 3), "text": payload.text_part1.strip()}
    part2 = {"id": 0, "start": round(payload.split_time, 3), "end": orig_end, "text": payload.text_part2.strip()}
    if spk_id:
        part1["speaker_id"] = spk_id
        part2["speaker_id"] = spk_id

    new_segments = segments[:idx] + [part1, part2] + segments[idx + 1:]
    for i, s in enumerate(new_segments, start=1):
        s["id"] = i

    updated = update_job(job_id, {key: new_segments, "updated_at": utcnow()})
    return safe_job(updated or job)


@app.post("/api/jobs/{job_id}/transcript/merge", response_model=JobResponse)
def merge_transcript_segments(job_id: str, payload: SubtitleMergeRequest):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    key = "translation" if payload.target == "translation" else "transcript"
    segments = list(job.get(key, []))

    idx1 = next((i for i, s in enumerate(segments) if s.get("id") == payload.segment_id_1), None)
    idx2 = next((i for i, s in enumerate(segments) if s.get("id") == payload.segment_id_2), None)

    if idx1 is None or idx2 is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="One or both segments not found")

    first_idx, second_idx = sorted([idx1, idx2])
    seg1 = segments[first_idx]
    seg2 = segments[second_idx]

    merged_text = f"{seg1.get('text', '').strip()} {seg2.get('text', '').strip()}".strip()
    merged_seg = {
        "id": 0,
        "start": min(float(seg1.get("start", 0.0)), float(seg2.get("start", 0.0))),
        "end": max(float(seg1.get("end", 0.0)), float(seg2.get("end", 0.0))),
        "text": merged_text,
    }
    if seg1.get("speaker_id"):
        merged_seg["speaker_id"] = seg1.get("speaker_id")

    new_segments = [s for i, s in enumerate(segments) if i not in (first_idx, second_idx)]
    new_segments.insert(first_idx, merged_seg)
    new_segments.sort(key=lambda s: s.get("start", 0.0))
    for i, s in enumerate(new_segments, start=1):
        s["id"] = i

    updated = update_job(job_id, {key: new_segments, "updated_at": utcnow()})
    return safe_job(updated or job)


@app.post("/api/jobs/{job_id}/transcript/insert", response_model=JobResponse)
def insert_transcript_segment(job_id: str, payload: SubtitleInsertRequest):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    key = "translation" if payload.target == "translation" else "transcript"
    segments = list(job.get(key, []))

    new_seg: dict[str, Any] = {
        "id": 0,
        "start": round(float(payload.segment.start), 3),
        "end": round(float(payload.segment.end), 3),
        "text": payload.segment.text.strip(),
    }
    if payload.segment.speaker_id:
        new_seg["speaker_id"] = payload.segment.speaker_id

    if payload.after_segment_id is not None:
        idx = next((i for i, s in enumerate(segments) if s.get("id") == payload.after_segment_id), None)
        if idx is not None:
            segments.insert(idx + 1, new_seg)
        else:
            segments.append(new_seg)
    else:
        segments.append(new_seg)

    segments.sort(key=lambda s: s.get("start", 0.0))
    for i, s in enumerate(segments, start=1):
        s["id"] = i

    updated = update_job(job_id, {key: segments, "updated_at": utcnow()})
    return safe_job(updated or job)


@app.delete("/api/jobs/{job_id}/transcript/{segment_id}", response_model=JobResponse)
def delete_transcript_segment(job_id: str, segment_id: int, target: str = Query(default="transcript")):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    key = "translation" if target == "translation" else "transcript"
    segments = [s for s in job.get(key, []) if s.get("id") != segment_id]
    for i, s in enumerate(segments, start=1):
        s["id"] = i

    updated = update_job(job_id, {key: segments, "updated_at": utcnow()})
    return safe_job(updated or job)


@app.post("/api/jobs/{job_id}/translate", response_model=JobResponse)
async def translate_job_endpoint(
    job_id: str,
    source_language: str | None = Query(default=None),
    target_language: str | None = Query(default=None),
):
    """
    Translates transcript segments into the specified target language.
    Does NOT require Ollama or paid APIs.
    """
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if not job.get("transcript"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transcribe the media before translating it.",
        )

    src_lang = source_language or job.get("source_language") or "auto"
    tgt_lang = target_language or job.get("target_language") or "km"

    current_stages = dict(job.get("stages", {}))
    current_stages["translating"] = "active"
    update_job(job_id, {
        "status": "translating",
        "stage": "translating",
        "progress": 70,
        "message": f"កំពុងបកប្រែ Subtitles ទៅជា {tgt_lang}...",
        "stages": current_stages,
    })

    try:
        translated_segments = await translate_segments(
            job["transcript"],
            source_lang=src_lang,
            target_lang=tgt_lang,
        )

        # Auto-synthesize dubbed audio track so preview and export immediately have sound
        has_dubbed_audio = False
        dubbed_audio_url = None
        try:
            target_voice = get_default_voice_for_language(tgt_lang)
            out_dubbed = OUTPUT_DIR / f"{job_id}_dubbed.mp3"
            raw_dubbed = OUTPUT_DIR / f"{job_id}_raw_dubbed.mp3"
            media_path = _find_job_media_path(job_id, job)
            speaker_voices = {}
            speaker_rates = {}
            for spk in job.get("speakers", []):
                spk_id = spk.get("speaker_id")
                if spk_id and spk.get("assigned_voice_id"):
                    speaker_voices[spk_id] = spk["assigned_voice_id"]
                if spk_id and spk.get("speech_rate"):
                    speaker_rates[spk_id] = spk["speech_rate"]

            await generate_dubbed_audio_track(
                segments=translated_segments,
                output_audio_path=raw_dubbed,
                voice_id=target_voice,
                speaker_voices=speaker_voices,
                speaker_rates=speaker_rates,
                total_duration=float(job.get("duration_seconds", 10.0) or 10.0),
                original_media_path=media_path,
                preserve_nonverbal=True,
            )

            if media_path and media_path.exists():
                await asyncio.to_thread(
                    mix_audio_tracks,
                    original_audio_path=media_path,
                    dubbed_audio_path=raw_dubbed,
                    output_mixed_path=out_dubbed,
                    voice_volume=1.0,
                    original_volume=0.85,
                    preserve_soundtrack=True,
                    ducking_intensity=0.35,
                )
                raw_dubbed.unlink(missing_ok=True)
            else:
                if raw_dubbed.exists():
                    shutil.move(str(raw_dubbed), str(out_dubbed))

            if out_dubbed.exists() and verify_audio_is_audible(out_dubbed):
                has_dubbed_audio = True
                dubbed_audio_url = f"/api/jobs/{job_id}/dubbed-audio"
        except Exception as dub_err:
            logger.warning("Auto-synthesis of dubbed audio during translation failed or skipped: %s", dub_err)

        current_stages["translating"] = "completed"
        current_stages["generating_subtitles"] = "completed"
        updated = update_job(job_id, {
            "status": "translated",
            "stage": "completed",
            "progress": 100,
            "message": f"ការបកប្រែជាភាសា {tgt_lang} បានជោគជ័យពេញលេញ!",
            "translation": translated_segments,
            "target_language": tgt_lang,
            "has_dubbed_audio": has_dubbed_audio,
            "dubbed_audio_url": dubbed_audio_url,
            "stages": current_stages,
            "updated_at": utcnow(),
        })
        return safe_job(updated or job)
    except Exception as exc:
        logger.error("Translation failed for job %s: %s", job_id, exc)
        current_stages["translating"] = "failed"
        update_job(job_id, {
            "status": "failed",
            "stage": "failed",
            "message": f"Translation failed: {exc}",
            "error": f"Translation failed: {exc}",
            "stages": current_stages,
        })
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Translation failed: {exc}")


@app.get("/api/jobs/{job_id}/subtitles.srt")
def export_srt_file(
    job_id: str,
    translated: bool = Query(default=False),
    lang: str | None = Query(default=None),
):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    if lang == "source":
        use_translated = False
    elif lang == "target":
        use_translated = True
    else:
        use_translated = bool(translated)

    segments = job.get("translation") if use_translated else job.get("transcript")
    if not segments:
        segments = job.get("transcript", [])
    if not segments:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No subtitle segments available to export. Transcribe the media first.",
        )

    content = build_srt_content(segments)
    suffix = job.get("target_language", "target") if use_translated else "source"
    out_file = OUTPUT_DIR / f"{job_id}-{suffix}.srt"
    out_file.write_text(content, encoding="utf-8")

    filename = f"{Path(job['filename']).stem}-{suffix}.srt"
    return FileResponse(
        out_file,
        media_type="application/x-subrip; charset=utf-8",
        filename=filename,
    )


@app.get("/api/jobs/{job_id}/subtitles.vtt")
def export_vtt_file(
    job_id: str,
    translated: bool = Query(default=False),
    lang: str | None = Query(default=None),
):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    if lang == "source":
        use_translated = False
    elif lang == "target":
        use_translated = True
    else:
        use_translated = bool(translated)

    segments = job.get("translation") if use_translated else job.get("transcript")
    if not segments:
        segments = job.get("transcript", [])
    if not segments:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No subtitle segments available to export.",
        )

    content = build_vtt_content(segments)
    suffix = job.get("target_language", "target") if use_translated else "source"
    out_file = OUTPUT_DIR / f"{job_id}-{suffix}.vtt"
    out_file.write_text(content, encoding="utf-8")

    filename = f"{Path(job['filename']).stem}-{suffix}.vtt"
    return FileResponse(
        out_file,
        media_type="text/vtt; charset=utf-8",
        filename=filename,
    )


@app.get("/api/jobs/{job_id}/transcript.txt")
def export_txt_file(
    job_id: str,
    translated: bool = Query(default=False),
    lang: str | None = Query(default=None),
    timestamps: bool = Query(default=True),
):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    if lang == "source":
        use_translated = False
    elif lang == "target":
        use_translated = True
    else:
        use_translated = bool(translated)
    segments = job.get("translation") if use_translated else job.get("transcript")
    if not segments:
        segments = job.get("transcript", [])
    if not segments:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No transcript text available to export.",
        )

    content = build_txt_content(segments, include_timestamps=timestamps)
    suffix = job.get("target_language", "target") if use_translated else "source"
    out_file = OUTPUT_DIR / f"{job_id}-{suffix}.txt"
    out_file.write_text(content, encoding="utf-8")

    filename = f"{Path(job['filename']).stem}-{suffix}.txt"
    return FileResponse(
        out_file,
        media_type="text/plain; charset=utf-8",
        filename=filename,
    )


def _find_job_media_path(job_id: str, job: dict[str, Any] | None = None) -> Path:
    """
    Safely locates the media file associated with a job across development
    and production deployments without path traversal vulnerabilities.
    """
    if not job_id or not all(c.isalnum() or c in "-_" for c in job_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid job ID format")

    if job is None:
        job = get_job(job_id)

    upload_root = UPLOAD_DIR.resolve()
    output_root = OUTPUT_DIR.resolve()
    base_root = BASE_DIR.resolve()
    import tempfile
    temp_roots = [Path(tempfile.gettempdir()).resolve(), Path("/tmp").resolve()]

    def _is_safe_file(cand: Path) -> bool:
        try:
            cand_resolved = cand.resolve()
            if not cand_resolved.is_file() or not cand_resolved.exists() or cand_resolved.stat().st_size == 0:
                return False
            # Verify no path traversal outside allowed directories
            for allowed in [upload_root, output_root, base_root] + temp_roots:
                try:
                    cand_resolved.relative_to(allowed)
                    return True
                except ValueError:
                    continue
            return False
        except Exception:
            return False

    # 1. Check job's recorded path (both exact and re-anchored to current upload_root/base_root)
    if job and job.get("path"):
        raw_path = Path(job["path"])
        candidates = [
            raw_path,
            upload_root / raw_path.name,
            upload_root / f"{job_id}{raw_path.suffix}",
            base_root / raw_path,
        ]
        for cand in candidates:
            if _is_safe_file(cand):
                return cand.resolve()

    # 2. Check original filename recorded on job
    if job and job.get("filename"):
        fn_path = Path(job["filename"])
        candidates = [
            upload_root / fn_path.name,
            upload_root / f"{job_id}{fn_path.suffix.lower()}",
            upload_root / f"{job_id}_{fn_path.name}",
        ]
        for cand in candidates:
            if _is_safe_file(cand):
                return cand.resolve()

    # 3. Check standard allowed extensions matching job_id in UPLOAD_DIR
    for ext in ALLOWED_EXTENSIONS:
        cand = upload_root / f"{job_id}{ext}"
        if _is_safe_file(cand):
            return cand.resolve()

    # 4. Glob check in UPLOAD_DIR for files matching job_id
    try:
        for cand in upload_root.glob(f"{job_id}.*"):
            if cand.suffix.lower() in ALLOWED_EXTENSIONS and _is_safe_file(cand):
                return cand.resolve()
        for cand in upload_root.glob(f"{job_id}_*"):
            if cand.suffix.lower() in ALLOWED_EXTENSIONS and _is_safe_file(cand):
                return cand.resolve()
    except Exception:
        pass

    # 5. Check clean WAV audio file
    clean_wav = upload_root / f"{job_id}_clean.wav"
    if _is_safe_file(clean_wav):
        return clean_wav.resolve()

    # 6. Check rendered or intermediate files in OUTPUT_DIR
    for cand in [output_root / f"{job_id}_rendered.mp4", output_root / f"{job_id}.mp4"]:
        if _is_safe_file(cand):
            return cand.resolve()

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media file not found for this job")


def _guess_media_type(path: Path) -> str:
    ext = path.suffix.lower()
    mapping = {
        ".mp4": "video/mp4",
        ".webm": "video/webm",
        ".mov": "video/quicktime",
        ".mkv": "video/x-matroska",
        ".m4v": "video/x-m4v",
        ".avi": "video/x-msvideo",
        ".wav": "audio/wav",
        ".mp3": "audio/mpeg",
        ".m4a": "audio/mp4",
        ".aac": "audio/aac",
        ".ogg": "audio/ogg",
        ".flac": "audio/flac",
        ".opus": "audio/opus",
    }
    return mapping.get(ext, "application/octet-stream")


@app.get("/api/jobs/{job_id}/media")
async def stream_media_file(job_id: str):
    """Streams original uploaded audio/video file with HTTP Range support for scrub preview."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    file_path = _find_job_media_path(job_id, job)
    media_type = _guess_media_type(file_path)
    return FileResponse(file_path, media_type=media_type)


@app.get("/api/jobs/{job_id}/preview-info", response_model=PreviewInfoResponse)
async def get_preview_info(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    has_media = False
    is_video = False
    width = None
    height = None
    duration = job.get("duration_seconds")

    try:
        media_path = _find_job_media_path(job_id, job)
        has_media = media_path.exists()
        probe = await asyncio.to_thread(probe_media_file, media_path)
        duration = float(probe.get("duration", 0.0)) or duration
        is_video = media_path.suffix.lower() in {".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"}
    except Exception:
        pass

    rendered_file = (OUTPUT_DIR / f"{job_id}_rendered.mp4").resolve()
    has_rendered = rendered_file.exists() and rendered_file.stat().st_size > 0
    rendered_size = rendered_file.stat().st_size if has_rendered else None
    rendered_duration = None

    if has_rendered:
        try:
            r_probe = await asyncio.to_thread(probe_media_file, rendered_file)
            rendered_duration = float(r_probe.get("duration", 0.0))
        except Exception:
            rendered_duration = duration

    dubbed_file = (OUTPUT_DIR / f"{job_id}_dubbed.mp3").resolve()
    has_dubbed = dubbed_file.exists() and dubbed_file.stat().st_size > 0

    return PreviewInfoResponse(
        job_id=job_id,
        filename=job.get("filename", "media"),
        name=job.get("name"),
        is_video=is_video,
        duration_seconds=duration,
        width=width,
        height=height,
        has_media_file=has_media,
        media_url=f"/api/jobs/{job_id}/media",
        source_language=job.get("source_language"),
        target_language=job.get("target_language", "km"),
        has_transcript=len(job.get("transcript", [])) > 0,
        has_translation=len(job.get("translation", [])) > 0,
        speakers_count=len(job.get("speakers", [])),
        has_rendered_video=has_rendered,
        rendered_video_url=f"/api/jobs/{job_id}/rendered-video" if has_rendered else None,
        has_dubbed_audio=has_dubbed,
        dubbed_audio_url=f"/api/jobs/{job_id}/dubbed-audio" if has_dubbed else None,
        rendered_video_size_bytes=rendered_size,
        rendered_video_duration=rendered_duration,
        srt_source_url=f"/api/jobs/{job_id}/subtitles.srt?lang=source",
        srt_khmer_url=f"/api/jobs/{job_id}/subtitles.srt?lang=target",
        vtt_source_url=f"/api/jobs/{job_id}/subtitles.vtt?lang=source",
        vtt_khmer_url=f"/api/jobs/{job_id}/subtitles.vtt?lang=target",
        txt_source_url=f"/api/jobs/{job_id}/transcript.txt?lang=source",
        txt_khmer_url=f"/api/jobs/{job_id}/transcript.txt?lang=target",
    )


@app.post("/api/jobs/{job_id}/export-video", response_model=JobResponse)
async def export_rendered_video(job_id: str, payload: VideoExportRequest = VideoExportRequest()):
    """
    Renders the final video with burned-in (hardsubbed) subtitles and optional dubbed audio track using FFmpeg.
    """
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    # Select subtitles: prioritize translation if available, otherwise transcript
    if payload.subtitle_source == "translation" and job.get("translation"):
        segments = job["translation"]
    elif payload.subtitle_source == "transcript" and job.get("transcript"):
        segments = job["transcript"]
    elif job.get("translation"):
        segments = job["translation"]
    elif job.get("transcript"):
        segments = job["transcript"]
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No transcript or translation available to burn into video. Transcribe the media first.",
        )

    media_path = _find_job_media_path(job_id, job)

    # Check for dubbed audio if requested
    dubbed_audio_path = None
    should_include_dub = payload.include_dubbed_audio and payload.audio_mode != "original"
    if should_include_dub:
        candidate_audio = (OUTPUT_DIR / f"{job_id}_dubbed.mp3").resolve()
        # If candidate audio does not exist, is empty, or is silent, auto-synthesize on-demand!
        is_candidate_valid = candidate_audio.exists() and candidate_audio.stat().st_size > 500 and verify_audio_is_audible(candidate_audio)
        if not is_candidate_valid:
            logger.info("Dubbed audio track missing or inaudible for job %s. Auto-generating before export...", job_id)
            speaker_voices = {}
            speaker_rates = {}
            for spk in job.get("speakers", []):
                spk_id = spk.get("speaker_id")
                if spk_id:
                    if spk.get("assigned_voice_id"):
                        speaker_voices[spk_id] = spk["assigned_voice_id"]
                    if spk.get("speech_rate"):
                        speaker_rates[spk_id] = spk["speech_rate"]

            target_lang = job.get("target_language") or "km"
            default_voice = get_default_voice_for_language(target_lang)
            chosen_voice = job.get("voice_settings", {}).get("voice_id") or default_voice

            # Speech audio MUST be synthesized from translated text, not original transcript
            dub_segments = job.get("translation") or segments

            raw_dubbed = OUTPUT_DIR / f"{job_id}_raw_dubbed.mp3"
            try:
                await generate_dubbed_audio_track(
                    segments=dub_segments,
                    output_audio_path=raw_dubbed,
                    voice_id=chosen_voice,
                    speaker_voices=speaker_voices,
                    speaker_rates=speaker_rates,
                    total_duration=float(job.get("duration_seconds", 10.0) or 10.0),
                    original_media_path=media_path,
                    preserve_nonverbal=getattr(payload, "preserve_nonverbal", True),
                )

                if payload.audio_mode == "mixed" and media_path and media_path.exists():
                    await asyncio.to_thread(
                        mix_audio_tracks,
                        original_audio_path=media_path,
                        dubbed_audio_path=raw_dubbed,
                        output_mixed_path=candidate_audio,
                        voice_volume=payload.voice_volume,
                        original_volume=payload.original_volume,
                        preserve_soundtrack=payload.preserve_soundtrack,
                        ducking_intensity=payload.ducking_intensity,
                    )
                    raw_dubbed.unlink(missing_ok=True)
                else:
                    if raw_dubbed.exists():
                        shutil.move(str(raw_dubbed), str(candidate_audio))
            except Exception as gen_err:
                logger.error("Dubbed audio generation failed during export: %s", gen_err)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Dubbed audio generation failed: {gen_err}",
                )

        if candidate_audio.exists() and candidate_audio.stat().st_size > 0 and verify_audio_is_audible(candidate_audio):
            dubbed_audio_path = candidate_audio
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate or locate valid audible dubbed audio track for export.",
            )

    # Prepare SRT file for FFmpeg libass subtitles filter
    srt_content = build_srt_content(segments)
    srt_file = OUTPUT_DIR / f"{job_id}-burnin.srt"
    srt_file.write_text(srt_content, encoding="utf-8")

    out_rendered_mp4 = OUTPUT_DIR / f"{job_id}_rendered.mp4"

    current_stages = dict(job.get("stages", {}))
    current_stages["exporting"] = "active"
    update_job(
        job_id,
        {
            "stage": "exporting",
            "progress": 92,
            "message": "កំពុងដំណើរការ Burn-in Subtitles & Audio ចូលក្នុងវីដេអូដោយ FFmpeg...",
            "stages": current_stages,
        },
        persist_disk=True,
    )

    try:
        render_res = await asyncio.to_thread(
            render_video_with_subtitles,
            input_media_path=media_path,
            subtitles_srt_path=srt_file,
            output_mp4_path=out_rendered_mp4,
            font_size=payload.font_size,
            audio_track_path=dubbed_audio_path,
        )

        current_stages["exporting"] = "completed"
        current_stages["completed"] = "completed"
        updated = update_job(
            job_id,
            {
                "status": "transcribed",
                "stage": "completed",
                "progress": 100,
                "message": "វីដេអូត្រូវបាន Render និងបញ្ចូល Subtitles & Dubbed Audio រួចរាល់ដោយជោគជ័យ!",
                "rendered_video_path": str(out_rendered_mp4),
                "has_rendered_video": True,
                "has_dubbed_audio": dubbed_audio_path is not None,
                "rendered_video_size_bytes": render_res.get("size_bytes"),
                "rendered_video_duration": render_res.get("duration"),
                "stages": current_stages,
            },
            persist_disk=True,
        )
        return safe_job(updated or job)
    except Exception as exc:
        logger.error("Video export failed for job %s: %s", job_id, exc)
        current_stages["exporting"] = "failed"
        update_job(
            job_id,
            {
                "stage": "failed",
                "message": f"Video export failed: {exc}",
                "error": f"Video export failed: {exc}",
                "stages": current_stages,
            },
            persist_disk=True,
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Video export failed: {exc}")


@app.get("/api/jobs/{job_id}/rendered-video")
async def get_rendered_video(job_id: str, download: bool = Query(default=False)):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    rendered_path = (OUTPUT_DIR / f"{job_id}_rendered.mp4").resolve()
    if not rendered_path.exists() or rendered_path.stat().st_size == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rendered video not found. Please click 'Export Final Video' first to render.",
        )

    filename = f"{Path(job.get('filename', 'video')).stem}_subtitled.mp4"
    return FileResponse(
        rendered_path,
        media_type="video/mp4",
        filename=filename,
        content_disposition_type="attachment" if download else "inline",
    )


# =========================================================================
# MULTILINGUAL AI VOICE DUBBING ENDPOINTS
# =========================================================================

@app.get("/api/dubbing/voices", response_model=list[VoiceInfo])
async def list_available_voices(language: str | None = Query(default=None), target_language: str | None = Query(default=None)):
    """
    Lists available verified Neural TTS voices for the requested language.
    Defaults to Khmer voices if no language is specified.
    """
    lang = language or target_language
    voices = get_available_voices(lang)
    return [VoiceInfo(**v) for v in voices]


@app.post("/api/dubbing/sample")
async def sample_voice_audio(
    voice_id: str = Form(default="km-KH-PisethNeural"),
    text: str | None = Form(default=None),
):
    """Generates an immediate audio preview sample for any selected neural voice."""
    sample_dir = OUTPUT_DIR / "voice_samples"
    sample_dir.mkdir(parents=True, exist_ok=True)
    sample_file = sample_dir / f"sample_{voice_id}.mp3"

    try:
        sample_bytes = await generate_speech_sample(text=text, voice_id=voice_id)
        sample_file.write_bytes(sample_bytes)
        return FileResponse(sample_file, media_type="audio/mpeg", filename=f"{voice_id}_sample.mp3")
    except Exception as exc:
        logger.error("Failed to generate voice sample for %s: %s", voice_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate voice sample: {exc}",
        )


@app.post("/api/dubbing/segment-sample")
async def sample_segment_audio(payload: SegmentAudioSampleRequest):
    """Generates on-demand speech sample for an individual dialogue line with story emotion."""
    try:
        from .dubbing import generate_segment_audio
        audio_bytes = await generate_segment_audio(
            text=payload.text,
            voice_id=payload.voice_id,
            emotion=payload.emotion,
            rate_pct=payload.rate,
        )
        return Response(content=audio_bytes, media_type="audio/mpeg")
    except Exception as exc:
        logger.error("Failed to generate segment audio sample: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate segment audio: {exc}",
        )


@app.post("/api/jobs/{job_id}/dub", response_model=JobResponse)
async def generate_dubbing_for_job(job_id: str, payload: DubbingRequest = DubbingRequest()):
    """
    Synthesizes dialogue segments into timed speech matching speaker profiles and aligns with video.
    """
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    segments = job.get("translation") or job.get("transcript")
    if not segments:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No transcript or translation available to dub. Translate or transcribe the media first.",
        )

    # Resolve and validate media_path prior to dubbing generation
    media_path: Path | None = None
    try:
        cand_path = _find_job_media_path(job_id, job)
        if cand_path.is_file() and cand_path.exists() and cand_path.stat().st_size > 0:
            media_path = cand_path
    except HTTPException:
        # Check if clean audio was cached as fallback
        cand_clean = (UPLOAD_DIR / f"{job_id}_clean.wav").resolve()
        if cand_clean.is_file() and cand_clean.exists() and cand_clean.stat().st_size > 0:
            media_path = cand_clean
            logger.info("Using clean WAV as media path fallback for job %s: %s", job_id, media_path)
    except Exception as exc:
        logger.warning("Error resolving media path for job %s: %s", job_id, exc)

    # If original mixing is requested but media file is missing, log warning
    if payload.mix_original and (media_path is None or not media_path.exists()):
        logger.warning(
            "Original media file is missing for job %s; dubbing will proceed without soundtrack mixing.",
            job_id,
        )

    # Build speaker voice lookup from job's speaker profiles if not in payload
    speaker_voices = dict(payload.speaker_voices)
    speaker_rates = dict(payload.speaker_rates)
    for spk in job.get("speakers", []):
        spk_id = spk.get("speaker_id")
        if spk_id:
            if spk_id not in speaker_voices and spk.get("assigned_voice_id"):
                speaker_voices[spk_id] = spk["assigned_voice_id"]
            if spk_id not in speaker_rates and spk.get("speech_rate"):
                speaker_rates[spk_id] = spk["speech_rate"]

    current_stages = dict(job.get("stages", {}))
    current_stages["dubbing"] = "active"
    update_job(
        job_id,
        {
            "stage": "dubbing",
            "progress": 60,
            "message": f"កំពុងបង្កើតសំឡេងនិយាយ AI ({payload.voice_id})...",
            "stages": current_stages,
        },
        persist_disk=True,
    )

    out_dubbed = OUTPUT_DIR / f"{job_id}_dubbed.mp3"
    raw_dubbed = OUTPUT_DIR / f"{job_id}_raw_dubbed.mp3"

    try:
        # Synthesize segments positioned accurately on the timeline
        await generate_dubbed_audio_track(
            segments=segments,
            output_audio_path=raw_dubbed,
            voice_id=payload.voice_id,
            speaker_voices=speaker_voices,
            speaker_rates=speaker_rates,
            total_duration=float(job.get("duration_seconds", 10.0) or 10.0),
            original_media_path=media_path,
            preserve_nonverbal=bool(payload.preserve_nonverbal and media_path and media_path.exists()),
        )

        if payload.mix_original and media_path and media_path.exists():
            update_job(
                job_id,
                {
                    "stage": "dubbing",
                    "progress": 85,
                    "message": "កំពុងលាយសំឡេង Dubbed ជាមួយសំឡេងដើមនៃវីដេអូ...",
                },
                persist_disk=True,
            )
            await asyncio.to_thread(
                mix_audio_tracks,
                original_audio_path=media_path,
                dubbed_audio_path=raw_dubbed,
                output_mixed_path=out_dubbed,
                voice_volume=payload.voice_volume,
                original_volume=payload.original_volume,
                preserve_soundtrack=payload.preserve_soundtrack,
                ducking_intensity=payload.ducking_intensity,
            )
            raw_dubbed.unlink(missing_ok=True)
        else:
            if raw_dubbed.exists():
                shutil.move(str(raw_dubbed), str(out_dubbed))

        if not out_dubbed.exists() or out_dubbed.stat().st_size < 500:
            raise RuntimeError("Generated dubbed audio track is empty or corrupted.")
        if not verify_audio_is_audible(out_dubbed):
            raise RuntimeError("Generated dubbed audio track is completely silent or inaudible.")

        current_stages["dubbing"] = "completed"
        updated = update_job(
            job_id,
            {
                "status": "transcribed",
                "stage": "completed",
                "progress": 100,
                "message": "ការបង្កើតសំឡេង Dubbed រួចរាល់ដោយជោគជ័យ!",
                "has_dubbed_audio": True,
                "dubbed_audio_url": f"/api/jobs/{job_id}/dubbed-audio",
                "voice_settings": payload.model_dump(),
                "stages": current_stages,
            },
            persist_disk=True,
        )
        return safe_job(updated or job)

    except Exception as exc:
        logger.error("Dubbing failed for job %s: %s", job_id, exc)
        current_stages["dubbing"] = "failed"
        update_job(
            job_id,
            {
                "stage": "failed",
                "message": f"Dubbing failed: {exc}",
                "error": str(exc),
                "stages": current_stages,
            },
            persist_disk=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Voice dubbing failed: {exc}",
        )


@app.get("/api/jobs/{job_id}/dubbed-audio")
async def get_dubbed_audio(job_id: str, download: bool = Query(default=False)):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    dubbed_file = (OUTPUT_DIR / f"{job_id}_dubbed.mp3").resolve()
    if not dubbed_file.exists() or dubbed_file.stat().st_size == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dubbed audio not found. Please click 'Generate AI Dubbing' first.",
        )

    filename = f"{Path(job.get('filename', 'audio')).stem}_dubbed.mp3"
    return FileResponse(
        dubbed_file,
        media_type="audio/mpeg",
        filename=filename,
        content_disposition_type="attachment" if download else "inline",
    )


# =========================================================================
# SMART SETTINGS PERSISTENCE ENDPOINTS
# =========================================================================

SETTINGS_FILE = (BASE_DIR / "app_settings.json").resolve()
USER_SETTINGS_DIR = (BASE_DIR / "user_settings").resolve()
USER_SETTINGS_DIR.mkdir(parents=True, exist_ok=True)


@app.get("/api/settings", response_model=AppSettings)
async def get_app_settings(request: Request, authorization: str | None = Header(None)):
    current_user = get_current_user_optional(request, authorization)
    target_file = (USER_SETTINGS_DIR / f"{current_user['id']}_settings.json") if current_user else SETTINGS_FILE
    if target_file.exists():
        try:
            data = json.loads(target_file.read_text(encoding="utf-8"))
            return AppSettings(**data)
        except Exception as exc:
            logger.warning("Failed to load user settings, fallback: %s", exc)
    if SETTINGS_FILE.exists():
        try:
            data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            return AppSettings(**data)
        except Exception:
            pass
    return AppSettings()


@app.put("/api/settings", response_model=AppSettings)
async def update_app_settings(settings_payload: AppSettings, request: Request, authorization: str | None = Header(None)):
    current_user = get_current_user_optional(request, authorization)
    target_file = (USER_SETTINGS_DIR / f"{current_user['id']}_settings.json") if current_user else SETTINGS_FILE
    try:
        target_file.write_text(json.dumps(settings_payload.model_dump(), indent=2), encoding="utf-8")
        return settings_payload
    except Exception as exc:
        logger.error("Failed to save settings: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not persist settings: {exc}",
        )


# =========================================================================
# PRONUNCIATION & TERMINOLOGY DICTIONARY ENDPOINTS
# =========================================================================

@app.get("/api/dictionary", response_model=DictionaryListResponse)
async def list_dictionary_entries():
    """Returns all custom pronunciation and terminology dictionary entries."""
    entries = dictionary_manager.get_all()
    return DictionaryListResponse(entries=[DictionaryEntry(**e) for e in entries], total=len(entries))


@app.post("/api/dictionary", response_model=DictionaryEntry)
async def add_or_update_dictionary_entry(entry: DictionaryEntry):
    """Adds or updates a terminology or pronunciation override."""
    try:
        updated = dictionary_manager.add_or_update(
            term=entry.term,
            replacement=entry.replacement,
            category=entry.category,
            notes=entry.notes,
            case_sensitive=entry.case_sensitive,
        )
        return DictionaryEntry(**updated)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update dictionary entry: {exc}",
        )


@app.delete("/api/dictionary/{term}")
async def delete_dictionary_entry(term: str):
    """Deletes an entry from the terminology dictionary."""
    success = dictionary_manager.delete(term)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Term '{term}' not found in dictionary",
        )
    return {"status": "deleted", "term": term}


# =========================================================================
# KHMER PROOFREADING & GRAMMAR QUALITY PIPELINE ENDPOINTS
# =========================================================================

@app.post("/api/jobs/{job_id}/proofread", response_model=ProofreadJobResponse)
async def proofread_job_translation(job_id: str, payload: ProofreadJobRequest):
    """
    Analyzes and suggests spelling, vowel/diacritic, grammar, and terminology
    improvements for the job's translated subtitles.
    Optionally applies high-confidence improvements automatically.
    """
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    translation = job.get("translation") or []
    transcript = job.get("transcript") or []
    if not translation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job has no translation segments to proofread. Please translate first.",
        )

    proof_result = khmer_proofreader.proofread_segments(
        segments=translation,
        source_segments=transcript,
        context_story=payload.context_story or job.get("name") or "",
        style=payload.style,
        auto_apply_high_confidence=payload.auto_apply_high_confidence,
    )

    if payload.auto_apply_high_confidence and proof_result["summary"]["auto_applied_count"] > 0:
        updated_translation = []
        for orig, res in zip(translation, proof_result["results"]):
            item = dict(orig)
            if res.get("applied_automatically"):
                item["text"] = res["suggested_khmer"]
            updated_translation.append(item)

        # Update disk SRT/VTT/TXT files
        srt_content = build_srt_content(updated_translation)
        vtt_content = build_vtt_content(updated_translation)
        txt_content = build_txt_content(updated_translation)
        srt_p = OUTPUT_DIR / f"{job_id}_khmer.srt"
        vtt_p = OUTPUT_DIR / f"{job_id}_khmer.vtt"
        txt_p = OUTPUT_DIR / f"{job_id}_khmer.txt"
        srt_p.write_text(srt_content, encoding="utf-8")
        vtt_p.write_text(vtt_content, encoding="utf-8")
        txt_p.write_text(txt_content, encoding="utf-8")

        update_job(job_id, {"translation": updated_translation}, persist_disk=True)

    return ProofreadJobResponse(
        results=[SegmentProofreadResult(**r) for r in proof_result["results"]],
        summary=proof_result["summary"],
        total_issues=proof_result["total_issues"],
    )


@app.put("/api/jobs/{job_id}/proofread-apply", response_model=JobResponse)
async def apply_proofread_changes(job_id: str, payload: ProofreadApplyRequest):
    """
    Applies reviewed and accepted proofread segments to the job translation,
    regenerating SRT, VTT, and TXT subtitle files.
    """
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    new_segments = [s.model_dump() for s in payload.applied_segments]

    srt_content = build_srt_content(new_segments)
    vtt_content = build_vtt_content(new_segments)
    txt_content = build_txt_content(new_segments)
    srt_p = OUTPUT_DIR / f"{job_id}_khmer.srt"
    vtt_p = OUTPUT_DIR / f"{job_id}_khmer.vtt"
    txt_p = OUTPUT_DIR / f"{job_id}_khmer.txt"
    srt_p.write_text(srt_content, encoding="utf-8")
    vtt_p.write_text(vtt_content, encoding="utf-8")
    txt_p.write_text(txt_content, encoding="utf-8")

    updated = update_job(
        job_id,
        {"translation": new_segments, "has_dubbed_audio": False},
        persist_disk=True,
    )
    return safe_job(updated or job)


@app.post("/api/proofread-sample")
async def proofread_sample_text(payload: ProofreadSampleRequest):
    """Instant single-line proofreader for live editing and testing."""
    res = khmer_proofreader.proofread_text(
        text=payload.text,
        source_text=payload.source_text,
        style=payload.style,
    )
    return res


# ==============================================================================
# FRONTEND STATIC MOUNT (FOR ALL-IN-ONE PRODUCTION DEPLOYMENTS)
# ==============================================================================
FRONTEND_DIST = (BASE_DIR.parent / "frontend" / "dist").resolve()
if FRONTEND_DIST.exists() and (FRONTEND_DIST / "index.html").exists():
    from fastapi.staticfiles import StaticFiles

    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")

