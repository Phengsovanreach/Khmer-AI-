export const COPYRIGHT_YEAR = '2026';
export const COPYRIGHT_OWNER = 'Phengsovanreach';
export const COPYRIGHT_TEXT = `© ${COPYRIGHT_YEAR} ${COPYRIGHT_OWNER}. All rights reserved.`;

export const TELEGRAM_SUPPORT = {
  displayName: 'Telegram Support',
  username: '@NeonCipher200',
  url: 'https://t.me/NeonCipher200',
  buttonLabel: 'Contact Us on Telegram',
  messageKhmer: 'ត្រូវការជំនួយជាមួយ Khmer Translator? ទំនាក់ទំនងមកកាន់ពួកយើងតាម Telegram។',
  messageEnglish: 'Need help with Khmer Translator? Contact us on Telegram.',
};

export interface LanguageInfo {
  code: string;
  name: string;
  native_name: string;
  flag: string;
  whisper_code?: string | null;
  default_voice?: string | null;
  asr_supported: boolean;
  translation_supported: boolean;
  tts_supported: boolean;
}

export interface LanguagesResponse {
  source_languages: LanguageInfo[];
  target_languages: LanguageInfo[];
  default_source_lang: string;
  default_target_lang: string;
}

export interface SpeakerProfile {
  id: string;
  speaker_id: string;
  name: string;
  gender_presentation: 'masculine' | 'feminine' | 'uncertain' | string;
  age_impression: 'childlike' | 'young_adult' | 'adult' | 'mature' | 'elderly' | 'uncertain' | string;
  speaking_style: string;
  speaking_speed: string;
  pitch_hz?: number | null;
  confidence: number;
  assigned_voice_id: string;
  voice_id?: string | null;
  segment_count: number;
  total_duration: number;
  sample_dialogue: string[];
  speech_rate?: number;
  volume_boost?: number;
}

export interface TranscriptSegment {
  id: number;
  start: number;
  end: number;
  text: string;
  speaker_id?: string | null;
  confidence?: number | null;
  emotion?: string | null;
  emotion_confidence?: number | null;
  ssml_rate?: string | null;
  ssml_pitch?: string | null;
  ssml_volume?: string | null;
}

export interface SubtitleStyling {
  font_size?: number;
  font_family?: string;
  primary_color?: string;
  outline_color?: string;
  background_opacity?: number;
  position?: 'bottom' | 'top' | 'middle';
}

export interface Job {
  id: string;
  name?: string;
  filename: string;
  status: string;
  stage?: string | null;
  progress?: number;
  message?: string | null;
  created_at: string;
  updated_at?: string;
  duration_seconds: number | null;
  processed_duration?: number | null;
  elapsed_seconds?: number | null;
  eta_seconds?: number | null;
  model_used?: string | null;
  source_language?: string | null;
  detected_source_language?: string | null;
  target_language: string;
  speakers: SpeakerProfile[];
  transcript: TranscriptSegment[];
  translation: TranscriptSegment[];
  error: string | null;
  stages?: Record<string, string>;
  has_rendered_video?: boolean;
  rendered_video_url?: string | null;
  has_dubbed_audio?: boolean;
  dubbed_audio_url?: string | null;
  voice_settings?: Record<string, any>;
  subtitle_styling?: SubtitleStyling;
}

export interface VoiceInfo {
  id: string;
  name: string;
  gender: string;
  language: string;
  locale?: string;
  description?: string;
  recommended: boolean;
  age_impression?: string;
}

export interface AppSettings {
  ui_language: string;
  default_model: string;
  default_source_lang: string;
  default_target_lang: string;
  default_tts_voice: string;
  subtitle_font_size: string;
  theme?: string;
  reduced_motion?: boolean;
  cultural_background_mode?: 'subtle' | 'vibrant' | 'minimal' | 'disabled';
  show_celestial_angel?: boolean;
}

export interface PipelineStageConfig {
  id: string;
  nameKhmer: string;
  nameEnglish: string;
  description: string;
  supported: boolean;
}

export const PIPELINE_STAGES: PipelineStageConfig[] = [
  {
    id: 'validating',
    nameKhmer: 'ផ្ទៀងផ្ទាត់ឯកសារមេឌៀ',
    nameEnglish: 'Media Validation (FFprobe)',
    description: 'ពិនិត្យ Container, Codec, Channels និង Duration',
    supported: true,
  },
  {
    id: 'extracting_audio',
    nameKhmer: 'ទាញយក និងសម្រួលសំឡេង',
    nameEnglish: 'Audio Extraction (FFmpeg 16kHz)',
    description: 'បំប្លែងជា PCM 16kHz Mono សម្រាប់ Whisper',
    supported: true,
  },
  {
    id: 'transcribing',
    nameKhmer: 'ស្គាល់សំឡេង AI Faster-Whisper',
    nameEnglish: 'Speech Recognition (INT8 CPU)',
    description: 'ស្គាល់សំឡេង និងកំណត់ត្រាពេលវេលា Segment',
    supported: true,
  },
  {
    id: 'detecting_speakers',
    nameKhmer: 'វិភាគសំឡេង និងកំណត់តួអង្គ (Diarization)',
    nameEnglish: 'Speaker Diarization & Profiling',
    description: 'កំណត់អត្តសញ្ញាណ Speaker 1, 2... ភេទ អាយុ និងសំឡេង',
    supported: true,
  },
  {
    id: 'generating_subtitles',
    nameKhmer: 'បង្កើតឯកសារ Subtitles SRT & TXT',
    nameEnglish: 'Subtitle Generation',
    description: 'បង្កើត SubRip (.srt), WebVTT (.vtt) និង Plain Text',
    supported: true,
  },
  {
    id: 'translating',
    nameKhmer: 'បកប្រែពហុភាសា (Multilingual Translation)',
    nameEnglish: 'Neural Translation (Zero Ollama)',
    description: 'បកប្រែ Subtitles ទៅជាភាសាគោលដៅជ្រើសរើស',
    supported: true,
  },
  {
    id: 'dubbing',
    nameKhmer: 'បង្កើតសំឡេងនិយាយ AI Dubbing',
    nameEnglish: 'AI Neural Voice Dubbing',
    description: 'សំយោគសំឡេងតាមតួអង្គ និងរៀបចំលើ Timeline',
    supported: true,
  },
  {
    id: 'exporting',
    nameKhmer: 'Video Rendering & Subtitle Burn-in',
    nameEnglish: 'Video Export (FFmpeg Hardsub)',
    description: 'បញ្ចូល Subtitles & Dubbed Audio ទៅក្នុងវីដេអូ MP4',
    supported: true,
  },
];

export interface ModelInfo {
  id: string;
  name: string;
  download_size_mb: number;
  estimated_ram_mb: number;
  description: string;
  is_default: boolean;
}

export interface Caps {
  ffmpeg: boolean;
  ffprobe: boolean;
  faster_whisper: boolean;
  default_model: string;
  available_models: string[];
  ollama: boolean;
  ollama_model: string;
  ollama_models: string[];
  tts: boolean;
  url_import: boolean;
  supported_languages_count?: number;
}

export const fmtTime = (n: number | null | undefined): string => {
  if (n == null || isNaN(n) || n < 0) return '00:00';
  const m = Math.floor(n / 60);
  const s = Math.floor(n % 60);
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
};

export const fmtDurationDetailed = (seconds: number | null | undefined): string => {
  if (seconds == null || isNaN(seconds)) return '—';
  const ms = Math.floor(seconds * 1000);
  const totalSec = Math.floor(ms / 1000);
  const m = Math.floor(totalSec / 60);
  const s = totalSec % 60;
  const milli = ms % 1000;
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}.${String(Math.floor(milli / 100))}`;
};

export const fmtFileSize = (bytes: number): string => {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

export interface DictionaryEntry {
  term: string;
  replacement: string;
  category: string;
  notes?: string;
  case_sensitive?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface ProofreadIssue {
  type: string;
  original: string;
  replacement: string;
  reason: string;
  confidence: number;
}

export interface ProofreadDiff {
  op: 'equal' | 'delete' | 'insert' | 'replace';
  text: string;
  old_text?: string;
  new_text?: string;
}

export interface SegmentProofreadResult {
  segment_id: number;
  original_source: string;
  initial_translation: string;
  suggested_khmer: string;
  issues: ProofreadIssue[];
  diffs: ProofreadDiff[];
  confidence: number;
  start: number;
  end: number;
  speaker_id?: string;
  applied_automatically?: boolean;
}

export interface ProofreadJobResponse {
  results: SegmentProofreadResult[];
  summary: {
    total_segments: number;
    segments_with_issues: number;
    total_issues: number;
    auto_applied_count: number;
    spelling_issues: number;
    grammar_issues: number;
    terminology_issues: number;
    number_issues: number;
    diacritic_issues: number;
  };
  total_issues: number;
}

