from __future__ import annotations
from typing import Any
from pydantic import BaseModel, Field

class HealthResponse(BaseModel):
    status: str
    app: str
    version: str = "2.0.0"

class ReadinessResponse(BaseModel):
    status: str
    app: str
    version: str = "2.0.0"
    ffmpeg: bool
    ffprobe: bool
    faster_whisper: bool
    tts: bool
    storage_writable: bool
    active_jobs: int = 0
    checks: dict[str, bool] = {}

class SystemDiagnosticsResponse(BaseModel):
    app_name: str
    app_version: str
    environment: str
    platform: str
    python_version: str
    cpu_cores: int
    memory_total_mb: int
    memory_available_mb: int
    storage_free_mb: int
    ffmpeg_available: bool
    ffprobe_available: bool
    faster_whisper_available: bool
    tts_engine_available: bool
    default_whisper_model: str
    supported_languages_count: int
    concurrency_lock_active: bool
    sanitized_cors_origins: list[str]


class ModelInfo(BaseModel):
    id: str
    name: str
    download_size_mb: int
    estimated_ram_mb: int
    description: str
    is_default: bool = False

class ModelsResponse(BaseModel):
    models: list[ModelInfo]
    default_model: str


class LanguageInfo(BaseModel):
    code: str
    name: str
    native_name: str
    flag: str
    whisper_code: str | None = None
    default_voice: str | None = None
    asr_supported: bool = True
    translation_supported: bool = True
    tts_supported: bool = True


class LanguagesResponse(BaseModel):
    source_languages: list[LanguageInfo]
    target_languages: list[LanguageInfo]
    default_source_lang: str = "auto"
    default_target_lang: str = "km"


class TranscriptSegment(BaseModel):
    id: int
    start: float
    end: float
    text: str
    speaker_id: str | None = None
    confidence: float | None = None
    emotion: str | None = "neutral"
    emotion_confidence: float | None = None
    ssml_rate: str | None = None
    ssml_pitch: str | None = None
    ssml_volume: str | None = None


class SpeakerProfile(BaseModel):
    id: str | None = None
    speaker_id: str = "speaker_1"
    name: str = "Speaker 1"
    gender_presentation: str = "uncertain"
    age_impression: str = "adult"
    speaking_style: str = "conversational"
    speaking_speed: str = "normal"
    pitch_hz: float | None = None
    confidence: float = 0.8
    assigned_voice_id: str = "km-KH-PisethNeural"
    voice_id: str | None = None
    segment_count: int = 0
    total_duration: float = 0.0
    sample_dialogue: list[str] = []
    speech_rate: int = 0
    volume_boost: float = 1.0

    def model_post_init(self, __context: Any) -> None:
        if not self.id and self.speaker_id:
            self.id = self.speaker_id
        elif not self.speaker_id and self.id:
            self.speaker_id = self.id
        if not self.voice_id and self.assigned_voice_id:
            self.voice_id = self.assigned_voice_id


class TranscriptUpdateRequest(BaseModel):
    segments: list[TranscriptSegment] = Field(default_factory=list)
    transcript: list[TranscriptSegment] | None = None

    def model_post_init(self, __context: Any) -> None:
        if not self.segments and self.transcript:
            self.segments = self.transcript
        elif self.segments and not self.transcript:
            self.transcript = self.segments


class TranscriptionRequest(BaseModel):
    model: str = "tiny"
    language: str | None = None
    target_language: str = "km"
    auto_diarize: bool = True
    auto_translate: bool = False
    auto_dub: bool = False


class TranslationRequest(BaseModel):
    source_language: str | None = None
    target_language: str = "km"


class SpeakerUpdateRequest(BaseModel):
    speakers: list[SpeakerProfile]


class SpeakerMergeRequest(BaseModel):
    speaker_id_keep: str
    speaker_id_merge: str


class SpeakerSplitRequest(BaseModel):
    segment_ids: list[int]
    new_speaker_name: str | None = None


class JobResponse(BaseModel):
    id: str
    filename: str
    name: str | None = None
    status: str
    stage: str | None = None
    progress: int = 0
    message: str | None = None
    created_at: str
    updated_at: str | None = None
    duration_seconds: float | None = None
    processed_duration: float | None = None
    elapsed_seconds: float | None = None
    eta_seconds: float | None = None
    model_used: str | None = None
    source_language: str | None = None
    detected_source_language: str | None = None
    target_language: str = "km"
    speakers: list[SpeakerProfile] = []
    transcript: list[TranscriptSegment] = []
    translation: list[TranscriptSegment] = []
    error: str | None = None
    stages: dict[str, str] = Field(default_factory=dict)
    has_rendered_video: bool = False
    rendered_video_url: str | None = None
    has_dubbed_audio: bool = False
    dubbed_audio_url: str | None = None
    voice_settings: dict[str, Any] = Field(default_factory=dict)
    subtitle_styling: dict[str, Any] = Field(default_factory=dict)


class JobProgressResponse(BaseModel):
    id: str
    status: str
    stage: str | None = None
    progress: int = 0
    message: str | None = None
    elapsed_seconds: float | None = None
    eta_seconds: float | None = None
    processed_duration: float | None = None
    total_duration: float | None = None
    error: str | None = None
    stages: dict[str, str] = Field(default_factory=dict)


class ProjectUpdateRequest(BaseModel):
    name: str | None = None
    source_language: str | None = None
    target_language: str | None = None
    speakers: list[SpeakerProfile] | None = None
    voice_settings: dict[str, Any] | None = None
    subtitle_styling: dict[str, Any] | None = None


class SubtitleSplitRequest(BaseModel):
    segment_id: int
    split_time: float
    text_part1: str
    text_part2: str
    target: str = "transcript"


class SubtitleMergeRequest(BaseModel):
    segment_id_1: int
    segment_id_2: int
    target: str = "transcript"


class SubtitleInsertRequest(BaseModel):
    after_segment_id: int | None = None
    segment: TranscriptSegment
    target: str = "transcript"


class VoiceInfo(BaseModel):
    id: str
    name: str
    gender: str
    language: str
    recommended: bool = False
    age_impression: str = "adult"


class VoiceSampleRequest(BaseModel):
    voice_id: str = "km-KH-PisethNeural"
    text: str | None = None
    rate: int = 0


class DubbingRequest(BaseModel):
    voice_id: str = "km-KH-PisethNeural"
    target_language: str = "km"
    speaker_voices: dict[str, str] = Field(default_factory=dict)
    speaker_rates: dict[str, int] = Field(default_factory=dict)
    voice_volume: float = 1.0
    original_volume: float = 0.85
    mix_original: bool = True
    preserve_soundtrack: bool = True
    ducking_intensity: float = 0.35
    preserve_nonverbal: bool = True


class SegmentAudioSampleRequest(BaseModel):
    text: str
    voice_id: str = "km-KH-PisethNeural"
    emotion: str = "neutral"
    rate: int = 0


class VideoExportRequest(BaseModel):
    subtitle_source: str = "auto"
    font_size: int = 22
    font_family: str = "Noto Sans Khmer"
    burn_subtitles: bool = True
    include_dubbed_audio: bool = True
    audio_mode: str = "mixed"  # "mixed" | "dubbed" | "original"
    target_language: str = "km"
    voice_volume: float = 1.0
    original_volume: float = 0.85
    mix_original: bool = True
    preserve_soundtrack: bool = True
    ducking_intensity: float = 0.35
    preserve_nonverbal: bool = True


class PreviewInfoResponse(BaseModel):
    job_id: str
    filename: str
    name: str | None = None
    is_video: bool
    duration_seconds: float | None = None
    width: int | None = None
    height: int | None = None
    has_media_file: bool = False
    media_url: str
    source_language: str | None = None
    target_language: str = "km"
    has_transcript: bool = False
    has_translation: bool = False
    speakers_count: int = 0
    has_rendered_video: bool = False
    rendered_video_url: str | None = None
    has_dubbed_audio: bool = False
    dubbed_audio_url: str | None = None
    rendered_video_size_bytes: int | None = None
    rendered_video_duration: float | None = None
    srt_source_url: str
    srt_khmer_url: str
    vtt_source_url: str
    vtt_khmer_url: str
    txt_source_url: str
    txt_khmer_url: str


class AppSettings(BaseModel):
    ui_language: str = "km"
    default_model: str = "tiny"
    default_source_lang: str = "auto"
    default_target_lang: str = "km"
    default_tts_voice: str = "km-KH-PisethNeural"
    subtitle_font_size: str = "medium"
    subtitle_position: str = "bottom"
    theme: str = "dark"
    reduced_motion: bool = False
    cultural_background_mode: str = "subtle"
    show_celestial_angel: bool = True


class CapabilitiesResponse(BaseModel):
    ffmpeg: bool
    ffprobe: bool
    faster_whisper: bool
    default_model: str
    available_models: list[str]
    ollama: bool = False
    ollama_model: str = ""
    ollama_models: list[str] = []
    tts: bool = True
    available_voices: list[VoiceInfo] = []
    supported_languages_count: int = 21
    url_import: bool = False


# ---------------------------------------------------------------------------
# Pronunciation & Terminology Dictionary Schemas
# ---------------------------------------------------------------------------
class DictionaryEntry(BaseModel):
    term: str
    replacement: str
    category: str = "general"
    notes: str = ""
    case_sensitive: bool = False
    created_at: str | None = None
    updated_at: str | None = None


class DictionaryListResponse(BaseModel):
    entries: list[DictionaryEntry]
    total: int


# ---------------------------------------------------------------------------
# Khmer Proofreading & Grammar Quality Schemas
# ---------------------------------------------------------------------------
class ProofreadIssue(BaseModel):
    type: str  # "spelling" | "grammar" | "terminology" | "number_format" | "diacritic" | "courtesy"
    original: str
    replacement: str
    reason: str
    confidence: float


class ProofreadDiff(BaseModel):
    op: str  # "equal" | "delete" | "insert" | "replace"
    text: str
    old_text: str | None = None
    new_text: str | None = None


class SegmentProofreadResult(BaseModel):
    segment_id: int
    original_source: str
    initial_translation: str
    suggested_khmer: str
    issues: list[ProofreadIssue]
    diffs: list[ProofreadDiff]
    confidence: float
    start: float = 0.0
    end: float = 0.0
    speaker_id: str | None = None
    applied_automatically: bool = False


class ProofreadJobRequest(BaseModel):
    style: str = "conversational"  # "conversational" | "formal" | "narrative"
    context_story: str | None = None
    auto_apply_high_confidence: bool = False


class ProofreadJobResponse(BaseModel):
    results: list[SegmentProofreadResult]
    summary: dict[str, int]
    total_issues: int


class ProofreadApplyRequest(BaseModel):
    applied_segments: list[TranscriptSegment]


class ProofreadSampleRequest(BaseModel):
    text: str
    source_text: str = ""
    style: str = "conversational"


# =========================================================================
# CHUNKED & RESUMABLE MEDIA UPLOAD SCHEMAS
# =========================================================================

class UploadInitRequest(BaseModel):
    filename: str
    file_size: int
    chunk_size: int = 5 * 1024 * 1024  # default 5MB chunks
    total_chunks: int
    source_language: str = "auto"
    target_language: str = "km"
    name: str | None = None


class UploadInitResponse(BaseModel):
    upload_id: str
    filename: str
    file_size: int
    chunk_size: int
    total_chunks: int
    uploaded_chunks: list[int] = []
    expires_at: str


class UploadChunkResponse(BaseModel):
    upload_id: str
    chunk_index: int
    uploaded_chunks: list[int]
    uploaded_bytes: int
    total_chunks: int
    file_size: int
    is_complete: bool


class UploadStatusResponse(BaseModel):
    upload_id: str
    filename: str
    file_size: int
    chunk_size: int
    total_chunks: int
    uploaded_chunks: list[int]
    uploaded_bytes: int
    status: str  # "in_progress", "completed", "failed", "cancelled"


class UploadCompleteRequest(BaseModel):
    upload_id: str
    source_language: str = "auto"
    target_language: str = "km"
    name: str | None = None


class URLImportRequest(BaseModel):
    url: str
    source_language: str = "auto"
    target_language: str = "km"
    auto_diarize: bool = True
    auto_translate: bool = True
    auto_dub: bool = False


# =============================================================================
# ANGKOR NEXUS AUTHENTICATION SCHEMAS
# =============================================================================

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    terms_accepted: bool = True


class LoginRequest(BaseModel):
    email: str
    password: str
    remember_me: bool = False


class UserProfile(BaseModel):
    id: str
    name: str
    email: str
    created_at: str
    avatar_color: str
    status: str = "active"
    email_verified: bool = True
    updated_at: str | None = None
    last_login_at: str | None = None


class AuthResponse(BaseModel):
    success: bool = True
    user: UserProfile
    token: str
    message: str = ""


class AuthStatusResponse(BaseModel):
    authenticated: bool
    user: UserProfile | None = None



