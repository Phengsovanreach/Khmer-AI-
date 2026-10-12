import os
from pathlib import Path
from typing import Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Khmer Translator API"
    app_version: str = "2.0.0"
    environment: str = "development"
    log_level: str = "INFO"
    host: str = "0.0.0.0"
    port: int = 8000
    upload_dir: str = "uploads"
    output_dir: str = "outputs"
    jobs_file: str = "jobs.json"
    max_upload_mb: int = 2048
    default_whisper_model: str = "tiny"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"
    cors_origins: Union[list[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "https://khmer-ai-16c.pages.dev",
        "https://1a4828c3.khmer-ai-16c.pages.dev",
    ]
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3:8b"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[list[str], str]) -> list[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
BASE_DIR = Path(__file__).resolve().parents[1]
UPLOAD_DIR = (BASE_DIR / settings.upload_dir).resolve()
OUTPUT_DIR = (BASE_DIR / settings.output_dir).resolve()
JOBS_FILE = (BASE_DIR / settings.jobs_file).resolve()
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
