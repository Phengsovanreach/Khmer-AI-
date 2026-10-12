from __future__ import annotations
import json
import logging
import threading
from pathlib import Path
from typing import Any
from .config import JOBS_FILE, UPLOAD_DIR, OUTPUT_DIR

logger = logging.getLogger(__name__)

_STORAGE_LOCK = threading.Lock()
_JOBS: dict[str, dict[str, Any]] = {}


def _load_from_disk() -> dict[str, dict[str, Any]]:
    if not JOBS_FILE.exists():
        return {}
    try:
        data = json.loads(JOBS_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except Exception as exc:
        logger.error("Failed to read jobs file %s: %s", JOBS_FILE, exc)
    return {}


def _save_to_disk() -> None:
    try:
        temp_file = JOBS_FILE.with_suffix(".tmp")
        temp_file.write_text(json.dumps(_JOBS, indent=2, ensure_ascii=False), encoding="utf-8")
        temp_file.replace(JOBS_FILE)
    except Exception as exc:
        logger.error("Failed to write jobs to %s: %s", JOBS_FILE, exc)


# Initialize memory from disk
with _STORAGE_LOCK:
    _JOBS = _load_from_disk()


import asyncio
from collections import defaultdict

_SUBSCRIBERS_LOCK = threading.Lock()
_SUBSCRIBERS: dict[str, set[asyncio.Queue]] = defaultdict(set)


def safe_job(job: dict[str, Any]) -> dict[str, Any]:
    """Strip local filesystem paths and internal state before returning to client."""
    cleaned = {k: v for k, v in job.items() if k not in ("path", "output_srt_path", "output_txt_path", "temp_wav_path", "rendered_video_path", "dubbed_audio_path")}
    job_id = cleaned.get("id", "")
    rendered_file = OUTPUT_DIR / f"{job_id}_rendered.mp4"
    has_rendered = rendered_file.exists() and rendered_file.stat().st_size > 0
    cleaned["has_rendered_video"] = has_rendered
    cleaned["rendered_video_url"] = f"/api/jobs/{job_id}/rendered-video" if has_rendered else None

    dubbed_file = OUTPUT_DIR / f"{job_id}_dubbed.mp3"
    has_dubbed = dubbed_file.exists() and dubbed_file.stat().st_size > 0
    cleaned["has_dubbed_audio"] = has_dubbed
    cleaned["dubbed_audio_url"] = f"/api/jobs/{job_id}/dubbed-audio" if has_dubbed else None

    if "name" not in cleaned or not cleaned["name"]:
        filename = cleaned.get("filename", "Project")
        cleaned["name"] = Path(filename).stem

    if "created_at" not in cleaned or not cleaned["created_at"]:
        from datetime import datetime, timezone
        cleaned["created_at"] = datetime.now(timezone.utc).isoformat()
    if "updated_at" not in cleaned or not cleaned["updated_at"]:
        cleaned["updated_at"] = cleaned.get("created_at")

    if "voice_settings" not in cleaned or not isinstance(cleaned["voice_settings"], dict):
        cleaned["voice_settings"] = {}

    if "target_language" not in cleaned or not cleaned["target_language"]:
        cleaned["target_language"] = "km"
    if "speakers" not in cleaned or not isinstance(cleaned["speakers"], list):
        cleaned["speakers"] = []
    if "subtitle_styling" not in cleaned or not isinstance(cleaned["subtitle_styling"], dict):
        cleaned["subtitle_styling"] = {}

    status = cleaned.get("status", "queued")
    if "progress" not in cleaned or cleaned["progress"] is None:
        cleaned["progress"] = 100 if status in ("transcribed", "completed", "translated") else 0
    if "stage" not in cleaned or cleaned["stage"] is None:
        cleaned["stage"] = "completed" if status in ("transcribed", "completed", "translated") else status
    if "stages" not in cleaned or not isinstance(cleaned["stages"], dict):
        cleaned["stages"] = {}

    cleaned["user_id"] = job.get("user_id")

    return cleaned


def add_job_listener(job_id: str, queue: asyncio.Queue) -> None:
    with _SUBSCRIBERS_LOCK:
        _SUBSCRIBERS[job_id].add(queue)


def remove_job_listener(job_id: str, queue: asyncio.Queue) -> None:
    with _SUBSCRIBERS_LOCK:
        if job_id in _SUBSCRIBERS:
            _SUBSCRIBERS[job_id].discard(queue)
            if not _SUBSCRIBERS[job_id]:
                _SUBSCRIBERS.pop(job_id, None)


def publish_job_update(job_id: str, job_data: dict[str, Any]) -> None:
    with _SUBSCRIBERS_LOCK:
        queues = list(_SUBSCRIBERS.get(job_id, set()))
    for q in queues:
        try:
            q.put_nowait(safe_job(job_data))
        except Exception:
            pass


def get_job(job_id: str) -> dict[str, Any] | None:
    with _STORAGE_LOCK:
        job = _JOBS.get(job_id)
        if not job:
            disk_jobs = _load_from_disk()
            if job_id in disk_jobs:
                _JOBS[job_id] = disk_jobs[job_id]
                job = _JOBS.get(job_id)
        return dict(job) if job else None


def list_jobs(user_id: str | None = None, include_unowned: bool = False) -> list[dict[str, Any]]:
    with _STORAGE_LOCK:
        disk_jobs = _load_from_disk()
        for k, v in disk_jobs.items():
            if k not in _JOBS:
                _JOBS[k] = v
        jobs = list(_JOBS.values())

    if user_id is not None:
        if include_unowned:
            jobs = [j for j in jobs if j.get("user_id") == user_id or not j.get("user_id")]
        else:
            jobs = [j for j in jobs if j.get("user_id") == user_id]

    return sorted(jobs, key=lambda j: j.get("created_at", ""), reverse=True)


def save_job(job: dict[str, Any]) -> None:
    with _STORAGE_LOCK:
        _JOBS[job["id"]] = dict(job)
        _save_to_disk()
    publish_job_update(job["id"], job)


def update_job(job_id: str, updates: dict[str, Any], persist_disk: bool = True) -> dict[str, Any] | None:
    with _STORAGE_LOCK:
        job = _JOBS.get(job_id)
        if not job:
            return None
        job.update(updates)
        _JOBS[job_id] = job
        if persist_disk:
            _save_to_disk()
        result = dict(job)
    publish_job_update(job_id, result)
    return result


def delete_job(job_id: str) -> bool:
    with _STORAGE_LOCK:
        job = _JOBS.pop(job_id, None)
        if not job:
            return False
        _save_to_disk()

    # Clean up associated files
    for key in ("path", "output_srt_path", "output_txt_path", "temp_wav_path", "rendered_video_path"):
        if key in job and job[key]:
            Path(job[key]).unlink(missing_ok=True)
    (OUTPUT_DIR / f"{job_id}_rendered.mp4").unlink(missing_ok=True)
    (OUTPUT_DIR / f"{job_id}_dubbed.mp3").unlink(missing_ok=True)
    (OUTPUT_DIR / f"{job_id}-km.srt").unlink(missing_ok=True)
    (OUTPUT_DIR / f"{job_id}-source.srt").unlink(missing_ok=True)
    (OUTPUT_DIR / f"{job_id}-km.vtt").unlink(missing_ok=True)
    (OUTPUT_DIR / f"{job_id}-source.vtt").unlink(missing_ok=True)

    return True
