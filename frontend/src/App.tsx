import React, { useEffect, useRef, useState } from 'react';
import {
  Activity,
  ArrowLeft,
  AudioLines,
  Check,
  CheckCircle2,
  ChevronDown,
  CircleHelp,
  Clapperboard,
  Clock3,
  CloudUpload,
  Copy,
  Download,
  AlertCircle,
  Ban,
  BookOpen,
  Clock,
  Eye,
  EyeOff,
  FileAudio,
  FileCheck2,
  FileDown,
  FileText,
  FileVideo,
  Film,
  FolderOpen,
  Gauge,
  Hourglass,
  Languages,
  LayoutDashboard,
  Loader2,
  Maximize2,
  Menu,
  Moon,
  Music,
  Pause,
  Play,
  Plus,
  RefreshCw,
  RotateCcw,
  Save,
  Settings2,
  ShieldCheck,
  Sliders,
  Sparkles,
  StopCircle,
  Subtitles,
  Sun,
  LogOut,
  Trash2,
  Users,
  Video,
  Volume2,
  VolumeX,
  WandSparkles,
  X,
} from 'lucide-react';
import { AnimatePresence, motion } from 'framer-motion';

import { AngkorNexusAuth } from './components/AngkorNexusAuth';
import { AuthService, AuthUser } from './services/authService';
import { SubtitleEditorPro } from './components/SubtitleEditorPro';
import { KhmerDubbingStudio } from './components/KhmerDubbingStudio';
import { ProjectHistoryPanel } from './components/ProjectHistoryPanel';
import { SmartSettingsPanel } from './components/SmartSettingsPanel';
import { LanguageSelector } from './components/LanguageSelector';
import { CharacterVoiceStudio } from './components/CharacterVoiceStudio';
import { DualVideoPreviewStudio } from './components/DualVideoPreviewStudio';
import { KhmerProofreadingStudio } from './components/KhmerProofreadingStudio';
import { PronunciationDictionaryStudio } from './components/PronunciationDictionaryStudio';
import { HelpCenterStudio } from './components/HelpCenterStudio';
import { InteractiveOnboardingWizard } from './components/InteractiveOnboardingWizard';
import { ContextualHelp } from './components/ContextualHelp';
import { MediaUploadController, UploadProgressInfo } from './services/mediaUploadService';
import { MediaUploadProgressCard } from './components/MediaUploadProgressCard';
import {
  CambodianCulturalBackground,
  KhmerLotusMotif,
  KhmerCornerKbach,
  KhmerBorderDivider,
} from './components/CambodianCulturalBackground';
import { AnimatedDevata } from './components/AnimatedDevata';
import { FloatingKhmerAIAgent } from './components/FloatingKhmerAIAgent';
import {
  AppSettings,
  Caps,
  Job,
  ModelInfo,
  PipelineStageConfig,
  PIPELINE_STAGES,
  TranscriptSegment,
  VoiceInfo,
  LanguagesResponse,
  LanguageInfo,
  SpeakerProfile,
  fmtDurationDetailed,
  fmtFileSize,
  fmtTime,
  COPYRIGHT_YEAR,
  COPYRIGHT_OWNER,
  COPYRIGHT_TEXT,
} from './types';

export {
  COPYRIGHT_YEAR,
  COPYRIGHT_OWNER,
  COPYRIGHT_TEXT,
  PIPELINE_STAGES,
  fmtTime,
  fmtDurationDetailed,
  fmtFileSize,
};
export type {
  TranscriptSegment,
  Job,
  VoiceInfo,
  AppSettings,
  ModelInfo,
  Caps,
  PipelineStageConfig,
};

export const getApiBase = (): string => {
  const custom = typeof window !== 'undefined' ? localStorage.getItem('khmer_ai_api_url') : null;
  if (custom && custom.trim()) {
    return custom.trim().replace(/\/+$/, '');
  }
  if (import.meta.env.VITE_API_URL && import.meta.env.VITE_API_URL.trim()) {
    return import.meta.env.VITE_API_URL.trim().replace(/\/+$/, '');
  }
  const isHttps = typeof window !== 'undefined' && window.location.protocol === 'https:';
  if (isHttps) {
    return 'https://khmer-ai-1ktp.onrender.com';
  }
  return 'http://127.0.0.1:8000';
};

let API = getApiBase();

export const authFetch = async (url: string, init: RequestInit = {}): Promise<Response> => {
  const token = AuthService.getToken();
  const headers = new Headers(init.headers || {});
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  return fetch(url, {
    ...init,
    headers,
    credentials: 'include',
  });
};

export const formatErrorMessage = (err: unknown, defaultFallback: string = 'ដំណើរការមិនបានជោគជ័យ'): string => {
  if (!err) return defaultFallback;
  const raw = err instanceof Error ? err.message : String(err);
  if (
    raw.toLowerCase().includes('failed to fetch') ||
    raw.toLowerCase().includes('networkerror') ||
    raw.toLowerCase().includes('load failed') ||
    raw.includes('net::ERR')
  ) {
    return 'មិនអាចភ្ជាប់ទៅកាន់ម៉ាស៊ីនបម្រើ Cloud Backend បានទេ (ម៉ាស៊ីនបម្រើកំពុងចាប់ផ្ដើមដំណើរការឡើងវិញ Cold Start ឬបញ្ហាអ៊ីនធឺណិត)។ សូមរង់ចាំបន្តិច ហើយសាកល្បងម្ដងទៀត។';
  }
  return raw;
};

const SUPPORTED_EXTS = [
  '.mp4', '.mkv', '.mov', '.avi', '.webm', '.m4v',
  '.mp3', '.wav', '.m4a', '.flac', '.ogg', '.aac', '.opus'
];

const LANGUAGE_OPTIONS = [
  { code: 'auto', label: 'ស្វ័យប្រវត្តិ (Auto Detect)' },
  { code: 'km', label: 'ភាសាខ្មែរ (Khmer)' },
  { code: 'en', label: 'ភាសាអង់គ្លេស (English)' },
  { code: 'zh', label: 'ភាសាចិន (Chinese)' },
  { code: 'fr', label: 'ភាសាបារាំង (French)' },
  { code: 'ja', label: 'ភាសាជប៉ុន (Japanese)' },
  { code: 'ko', label: 'ភាសាកូរ៉េ (Korean)' },
  { code: 'de', label: 'ភាសាអាល្លឺម៉ង់ (German)' },
  { code: 'es', label: 'ភាសាអេស្ប៉ាញ (Spanish)' },
];


// Motion animation variants
const pageMotionVariants = {
  initial: { opacity: 0, y: 10 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.22, ease: [0.25, 0.1, 0.25, 1] } },
  exit: { opacity: 0, y: -8, transition: { duration: 0.16, ease: [0.25, 0.1, 0.25, 1] } },
};

const statsContainerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.06,
    },
  },
};

interface ProcessingProgressPanelProps {
  job: Job;
  busy: boolean;
  onCancel: (jobId: string) => void;
  onRetry: (jobId: string) => void;
}

export const ProcessingProgressPanel: React.FC<ProcessingProgressPanelProps> = ({
  job,
  busy,
  onCancel,
  onRetry,
}) => {
  const isProcessing =
    ['validating', 'extracting_audio', 'transcribing', 'generating_subtitles', 'translating', 'queued'].includes(job.status) ||
    busy;
  const isFailed = job.status === 'failed' || !!job.error;
  const isCancelled = job.status === 'cancelled';
  const isDone = job.status === 'transcribed' || job.status === 'completed' || (job.progress === 100 && !isFailed);

  const pct = Math.min(Math.max(job.progress ?? (isDone ? 100 : 0), 0), 100);

  // Determine stage status for each pipeline step with strict sequential resolution and 100% completion safeguard
  const getStageStatus = (stageId: string, supported: boolean): 'completed' | 'active' | 'pending' | 'unsupported' => {
    if (!supported) return 'unsupported';

    // Safeguard 1: If overall pipeline reached 100% or is completed, auto-resolve all prerequisite stages to 'completed'
    if (isDone || pct >= 100) {
      if (stageId === 'translating') {
        return job.translation && job.translation.length > 0 ? 'completed' : 'pending';
      }
      if (stageId === 'exporting') {
        return job.has_rendered_video ? 'completed' : 'pending';
      }
      return 'completed';
    }

    // Step order index in pipeline
    const STAGE_ORDER = ['validating', 'extracting_audio', 'transcribing', 'detecting_speakers', 'generating_subtitles', 'translating', 'exporting'];
    const currentStageIdx = STAGE_ORDER.indexOf(job.stage || job.status || '');
    const thisStageIdx = STAGE_ORDER.indexOf(stageId);

    // Safeguard 2: If backend reports stage explicitly, check prerequisite sequential rule
    if (job.stages && job.stages[stageId]) {
      const explicitStatus = job.stages[stageId];
      // If a subsequent stage is already active or completed, earlier stage MUST be completed
      if (currentStageIdx > thisStageIdx && thisStageIdx !== -1) {
        return 'completed';
      }
      return explicitStatus as any;
    }

    if (isFailed || isCancelled) {
      if (job.stage === stageId) return 'active';
    }

    // Safeguard 3: If current execution stage has moved ahead, previous steps are completed
    if (currentStageIdx > thisStageIdx && thisStageIdx !== -1) {
      return 'completed';
    }

    if (stageId === 'validating') return pct >= 10 || currentStageIdx > 0 ? 'completed' : isProcessing ? 'active' : 'pending';
    if (stageId === 'extracting_audio') return pct >= 15 || currentStageIdx > 1 ? 'completed' : (job.stage === 'extracting_audio' || (pct >= 5 && isProcessing)) ? 'active' : 'pending';
    if (stageId === 'transcribing') return pct >= 88 || currentStageIdx > 2 ? 'completed' : (job.stage === 'transcribing' || (pct >= 15 && isProcessing)) ? 'active' : 'pending';
    if (stageId === 'detecting_speakers') return pct >= 95 || currentStageIdx > 3 ? 'completed' : (job.stage === 'detecting_speakers' || pct >= 88) ? 'active' : 'pending';
    if (stageId === 'generating_subtitles') return pct >= 98 || isDone ? 'completed' : (job.stage === 'generating_subtitles' || pct >= 95) ? 'active' : 'pending';
    if (stageId === 'translating') return job.status === 'translating' ? 'active' : job.translation?.length ? 'completed' : 'pending';
    if (stageId === 'exporting') return job.has_rendered_video ? 'completed' : (job.stage === 'exporting' ? 'active' : 'pending');
    return 'pending';
  };

  const getStageDisplayTitle = () => {
    if (isFailed) return 'ដំណើរការបរាជ័យ (Processing Failed)';
    if (isCancelled) return 'ដំណើរការត្រូវបានបោះបង់ (Processing Cancelled)';
    if (isDone) return 'ដំណើរការបានជោគជ័យពេញលេញ (100% Completed)';
    switch (job.stage || job.status) {
      case 'validating':
        return 'កំពុងផ្ទៀងផ្ទាត់ឯកសារ (Validating Media)...';
      case 'extracting_audio':
        return 'កំពុងទាញយកសំឡេង (Extracting Audio 16kHz)...';
      case 'transcribing':
        return 'កំពុងស្គាល់សំឡេង (Speech Recognition in Progress)...';
      case 'generating_subtitles':
        return 'កំពុងបង្កើត Subtitles SRT & TXT...';
      case 'translating':
        return 'កំពុងបកប្រែជាភាសាខ្មែរ (Khmer Translation)...';
      case 'exporting':
        return 'កំពុងដំណើរការ Burn-in Subtitles ចូលក្នុងវីដេអូ (FFmpeg Export)...';
      default:
        return 'កំពុងរៀបចំដំណើរការ (Queued)...';
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: -6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.22 }}
      className="progress-panel"
    >
      {/* Header with Title and Control Buttons */}
      <div className="progress-header">
        <div className="progress-header-left">
          <div className={`progress-step-badge ${isFailed ? 'failed' : isCancelled ? 'cancelled' : isDone ? 'completed' : ''}`}>
            {isDone ? (
              <CheckCircle2 size={13} />
            ) : isFailed ? (
              <AlertCircle size={13} />
            ) : isCancelled ? (
              <Ban size={13} />
            ) : (
              <Loader2 size={13} className="spin" />
            )}
            <span>{getStageDisplayTitle()}</span>
          </div>
          <span style={{ fontSize: 11, color: 'var(--muted)', fontWeight: 500 }}>
            {job.filename}
          </span>
        </div>

        {/* Action Controls: Cancel or Retry */}
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          {isProcessing && !isDone && !isFailed && !isCancelled && (
            <motion.button
              whileTap={{ scale: 0.96 }}
              className="secondary-btn"
              style={{ color: '#ea8282', borderColor: '#ea828244' }}
              onClick={() => onCancel(job.id)}
              title="Cancel processing immediately"
            >
              <StopCircle size={14} /> បោះបង់ (Cancel)
            </motion.button>
          )}

          {(isFailed || isCancelled) && (
            <motion.button
              whileTap={{ scale: 0.96 }}
              className="primary-btn"
              onClick={() => onRetry(job.id)}
              title="Retry processing from stage 1"
            >
              <RotateCcw size={14} /> ព្យាយាមម្តងទៀត (Retry)
            </motion.button>
          )}
        </div>
      </div>

      {/* Hero Percentage and Time Meta */}
      <div className="progress-hero">
        <div className={`progress-percent-large ${isFailed ? 'failed' : isCancelled ? 'cancelled' : isDone ? 'completed' : ''}`}>
          {pct}%
        </div>

        <div className="progress-meta-row">
          {job.elapsed_seconds != null && job.elapsed_seconds > 0 && (
            <span className="progress-meta-pill">
              <Clock size={12} style={{ color: 'var(--gold)' }} />
              រយៈពេលដំណើរការ: <b>{job.elapsed_seconds.toFixed(1)}s</b>
            </span>
          )}

          {job.eta_seconds != null && job.eta_seconds > 0 && isProcessing && (
            <span className="progress-meta-pill" style={{ color: 'var(--gold2)' }}>
              <Hourglass size={12} />
              នៅសល់ប្រហែល: <b>~{job.eta_seconds >= 60 ? `${Math.floor(job.eta_seconds / 60)}m ${Math.round(job.eta_seconds % 60)}s` : `${Math.round(job.eta_seconds)}s`}</b>
            </span>
          )}

          {job.processed_duration != null && job.duration_seconds != null && job.duration_seconds > 0 && (
            <span className="progress-meta-pill">
              <FileAudio size={12} style={{ color: 'var(--green)' }} />
              សំឡេង: <b>{job.processed_duration.toFixed(1)}s / {job.duration_seconds.toFixed(1)}s</b>
            </span>
          )}
        </div>
      </div>

      {/* Animated Horizontal Progress Bar */}
      <div className="progress-track" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}>
        <div
          className={`progress-fill ${isFailed ? 'failed' : isCancelled ? 'cancelled' : isDone ? 'completed' : ''}`}
          style={{ width: `${pct}%` }}
        />
      </div>

      {/* Real-time Message Banner */}
      {job.message && (
        <div className="progress-message-banner">
          <span style={{ color: isFailed ? '#ea8282' : isDone ? 'var(--green)' : 'var(--text)', fontWeight: 500 }}>
            {job.message}
          </span>
          <span style={{ fontSize: 10, color: 'var(--muted)' }}>
            Faster-Whisper ({job.model_used || 'tiny'})
          </span>
        </div>
      )}

      {/* Error Banner when Failed */}
      {isFailed && job.error && (
        <div className="alert error" style={{ margin: '0 0 16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <AlertCircle size={15} />
            <span>កំហុសបច្ចេកទេស: {job.error}</span>
          </div>
          <button className="primary-btn" style={{ padding: '4px 10px', fontSize: 10 }} onClick={() => onRetry(job.id)}>
            <RotateCcw size={12} /> Retry Now
          </button>
        </div>
      )}

      {/* Pipeline Stages Stepper Grid (6 Actual Stages) */}
      <div className="pipeline-stepper-grid">
        {PIPELINE_STAGES.map((stg, idx) => {
          const status = getStageStatus(stg.id, stg.supported);
          return (
            <div key={stg.id} className={`stepper-card ${status}`}>
              <div className="stepper-card-top">
                <div className="stepper-card-title">
                  {status === 'completed' ? (
                    <CheckCircle2 size={15} style={{ color: 'var(--green)' }} />
                  ) : status === 'active' ? (
                    <Loader2 size={15} className="spin" style={{ color: 'var(--gold)' }} />
                  ) : status === 'unsupported' ? (
                    <Ban size={15} style={{ color: 'var(--muted)' }} />
                  ) : (
                    <span style={{ width: 15, height: 15, borderRadius: '50%', background: 'var(--line)', display: 'grid', placeItems: 'center', fontSize: 9, color: 'var(--muted)' }}>
                      {idx + 1}
                    </span>
                  )}
                  <span>{stg.nameKhmer}</span>
                </div>
                <span className={`tag ${status === 'completed' ? 'tag-ready' : status === 'active' ? 'tag-ready' : ''}`}>
                  {status === 'completed'
                    ? 'រួចរាល់ (Done)'
                    : status === 'active'
                    ? 'កំពុងដំណើរការ'
                    : status === 'unsupported'
                    ? 'មិនទាន់គាំទ្រ'
                    : 'រង់ចាំ (Pending)'}
                </span>
              </div>
              <p className="stepper-card-desc">{stg.description}</p>
            </div>
          );
        })}
      </div>
    </motion.div>
  );
};

interface VideoPreviewStudioProps {
  active: Job | null;
  API: string;
  onBackToEditor: () => void;
  onRefreshJob: () => Promise<void>;
  busy: boolean;
  setNotice: (msg: string) => void;
  setError: (msg: string) => void;
}

export const VideoPreviewStudio: React.FC<VideoPreviewStudioProps> = ({
  active,
  API,
  onBackToEditor,
  onRefreshJob,
  busy,
  setNotice,
  setError,
}) => {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);

  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const [isMuted, setIsMuted] = useState(false);
  const [playbackRate, setPlaybackRate] = useState(1);

  // Preview Mode: 'live_overlay' (uses original video + live subtitles) vs 'rendered' (uses rendered MP4)
  const [previewMode, setPreviewMode] = useState<'live_overlay' | 'rendered'>(
    active?.has_rendered_video ? 'rendered' : 'live_overlay'
  );

  // Subtitle Settings
  const [showSubtitles, setShowSubtitles] = useState(true);
  const [fontSize, setFontSize] = useState<'small' | 'medium' | 'large'>('medium');
  const [position, setPosition] = useState<'bottom' | 'center' | 'top'>('bottom');
  const [comparisonMode, setComparisonMode] = useState<'khmer_only' | 'dual'>('khmer_only');

  // Audio Mode for export: 'dubbed' (replace original voice) | 'mixed' (ducking) | 'original'
  const [audioMode, setAudioMode] = useState<'dubbed' | 'mixed' | 'original'>('dubbed');
  // Live Preview Audio selection: 'dubbed' (plays dubbed track in sync) | 'original'
  const [liveAudioTrack, setLiveAudioTrack] = useState<'dubbed' | 'original'>(
    active?.has_dubbed_audio ? 'dubbed' : 'original'
  );
  const dubbedAudioRef = useRef<HTMLAudioElement | null>(null);

  const [showSettings, setShowSettings] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [videoError, setVideoError] = useState<string | null>(null);
  const [isLoadingVideo, setIsLoadingVideo] = useState(false);

  // Sync mode if active changes
  useEffect(() => {
    if (active?.has_rendered_video) {
      setPreviewMode('rendered');
    } else {
      setPreviewMode('live_overlay');
    }
    setCurrentTime(0);
    setIsPlaying(false);
    setVideoError(null);
  }, [active?.id, active?.has_rendered_video]);

  // Handle Play/Pause
  const togglePlay = () => {
    if (!videoRef.current) return;
    if (videoRef.current.paused) {
      videoRef.current.play().catch(() => {});
    } else {
      videoRef.current.pause();
    }
  };

  // Handle Seek
  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const time = parseFloat(e.target.value);
    setCurrentTime(time);
    if (videoRef.current) {
      videoRef.current.currentTime = time;
    }
    if (dubbedAudioRef.current) {
      dubbedAudioRef.current.currentTime = time;
    }
  };

  // Restart Preview
  const handleRestart = () => {
    if (!videoRef.current) return;
    videoRef.current.currentTime = 0;
    setCurrentTime(0);
    if (dubbedAudioRef.current) {
      dubbedAudioRef.current.currentTime = 0;
    }
    videoRef.current.play().catch(() => {});
  };

  // Volume & Mute
  const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseFloat(e.target.value);
    setVolume(val);
    if (videoRef.current) {
      videoRef.current.volume = val;
      videoRef.current.muted = val === 0;
      setIsMuted(val === 0);
    }
    if (dubbedAudioRef.current) {
      dubbedAudioRef.current.volume = val;
      dubbedAudioRef.current.muted = val === 0;
    }
  };

  const toggleMute = () => {
    if (!videoRef.current) return;
    const nextMuted = !isMuted;
    videoRef.current.muted = nextMuted;
    if (dubbedAudioRef.current) {
      dubbedAudioRef.current.muted = nextMuted;
    }
    setIsMuted(nextMuted);
  };

  // Playback Rate
  const handleSpeedChange = (rate: number) => {
    setPlaybackRate(rate);
    if (videoRef.current) {
      videoRef.current.playbackRate = rate;
    }
  };

  // Fullscreen
  const toggleFullscreen = () => {
    if (!containerRef.current) return;
    if (!document.fullscreenElement) {
      containerRef.current.requestFullscreen().catch(() => {});
    } else {
      document.exitFullscreen().catch(() => {});
    }
  };

  // Export Final Video (FFmpeg hardsub)
  const handleExportVideo = async () => {
    if (!active) return;
    setIsExporting(true);
    try {
      const res = await authFetch(`${API}/api/jobs/${active.id}/export-video`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          subtitle_source: active.translation?.length ? 'translation' : 'transcript',
          font_size: fontSize === 'small' ? 18 : fontSize === 'large' ? 26 : 22,
          burn_subtitles: true,
          include_dubbed_audio: audioMode !== 'original',
          audio_mode: audioMode,
          voice_volume: 1.0,
          original_volume: audioMode === 'mixed' ? 0.25 : 0.0,
          preserve_soundtrack: audioMode === 'mixed',
        }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Video rendering failed');
      }

      await onRefreshJob();
      setPreviewMode('rendered');
      setNotice('វីដេអូត្រូវបាន Export និងបញ្ចូល Subtitles រួចរាល់ដោយជោគជ័យ! អ្នកអាចទាញយក (Download) បានឥឡូវនេះ។');
    } catch (err: any) {
      setError(`បរាជ័យក្នុងការ Export វីដេអូ: ${err.message || err}`);
    } finally {
      setIsExporting(false);
    }
  };

  if (!active) {
    return (
      <div className="preview-studio-panel">
        <div className="empty-state">
          <Film size={36} style={{ color: 'var(--gold)', marginBottom: 12 }} />
          <h3>No Project Selected for Preview</h3>
          <p>សូមជ្រើសរើស ឬ Upload វីដេអូមួយនៅក្នុង Workspace ដើម្បីចាប់ផ្តើម Preview និង Export។</p>
          <button className="primary-btn" onClick={onBackToEditor}>
            <ArrowLeft size={16} /> Go to Workspace
          </button>
        </div>
      </div>
    );
  }

  // Active Subtitle Segment
  const transcriptList = active.transcript || [];
  const translationList = active.translation || [];
  const hasTranslation = translationList.length > 0;

  const activeIdx = transcriptList.findIndex(
    (s) => currentTime >= s.start && currentTime <= s.end
  );

  const activeSourceText = activeIdx >= 0 ? transcriptList[activeIdx]?.text : '';
  const activeKhmerText = activeIdx >= 0
    ? (hasTranslation ? translationList[activeIdx]?.text : activeSourceText)
    : '';

  const mediaSrc = previewMode === 'rendered'
    ? `${API}/api/jobs/${active.id}/rendered-video`
    : `${API}/api/jobs/${active.id}/media`;

  const isAudioFile = ['.mp3', '.wav', '.m4a', '.flac', '.ogg', '.aac', '.opus'].some((ext) =>
    active.filename.toLowerCase().endsWith(ext)
  );

  return (
    <div className="preview-studio-panel">
      {/* Top Bar */}
      <div className="preview-top-bar">
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <button className="secondary-btn" onClick={onBackToEditor} title="Back to Editor">
            <ArrowLeft size={15} /> Back to Editor
          </button>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <b style={{ fontSize: 15 }}>{active.filename}</b>
              <span className={`badge-pill ${active.has_rendered_video ? 'success' : 'warning'}`}>
                {active.has_rendered_video ? 'Rendered MP4 Ready' : 'Live Subtitle Overlay'}
              </span>
            </div>
            <small style={{ color: 'var(--muted)', fontSize: 11 }}>
              Duration: {fmtTime(duration || active.duration_seconds)} · {transcriptList.length} subtitle segments
            </small>
          </div>
        </div>

        {/* Mode Switcher */}
        <div className="preview-mode-tabs">
          <button
            className={`preview-mode-btn ${previewMode === 'live_overlay' ? 'active' : ''}`}
            onClick={() => {
              setPreviewMode('live_overlay');
              if (videoRef.current) videoRef.current.muted = isMuted;
            }}
          >
            <Subtitles size={14} /> Live Subtitles Preview
          </button>
          {active.has_dubbed_audio && (
            <button
              className={`preview-mode-btn ${previewMode === 'live_overlay' && liveAudioTrack === 'dubbed' ? 'active' : ''}`}
              onClick={() => {
                setPreviewMode('live_overlay');
                setLiveAudioTrack((prev) => (prev === 'dubbed' ? 'original' : 'dubbed'));
                setNotice(liveAudioTrack === 'dubbed' ? 'ប្ដូរទៅសំឡេងដើម (Original)' : 'ប្ដូរទៅសំឡេងបកប្រែ AI Dubbed (Target Voice)');
              }}
              title="Toggle target-language dubbed voice preview on video"
              style={{
                borderColor: liveAudioTrack === 'dubbed' ? 'var(--gold)' : undefined,
                color: liveAudioTrack === 'dubbed' ? 'var(--gold)' : undefined,
              }}
            >
              <Volume2 size={14} /> {liveAudioTrack === 'dubbed' ? 'AI Dubbed Voice (ON)' : 'AI Dubbed Voice (OFF)'}
            </button>
          )}
          <button
            className={`preview-mode-btn ${previewMode === 'rendered' ? 'active' : ''} ${!active.has_rendered_video ? 'disabled' : ''}`}
            onClick={() => {
              if (active.has_rendered_video) {
                setPreviewMode('rendered');
              } else {
                setNotice('វីដេអូមិនទាន់បាន Export នៅឡើយទេ។ សូមចុច "Export Final Video" ខាងក្រោមដើម្បី Render។');
              }
            }}
            title={active.has_rendered_video ? 'Play Rendered Video' : 'Please export video first'}
          >
            <Film size={14} /> Rendered Video (Hardsub)
          </button>
        </div>

        {/* Quick Toolbar */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <button
            className={`player-icon-btn ${showSettings ? 'active' : ''}`}
            onClick={() => setShowSettings(!showSettings)}
            title="Subtitle Display Settings"
          >
            <Sliders size={14} /> Settings
          </button>
          <button
            className="player-icon-btn"
            onClick={async () => {
              await onRefreshJob();
              setNotice('បាន Refresh ទិន្នន័យ Preview រួចរាល់!');
            }}
            title="Regenerate / Reload Preview"
          >
            <RefreshCw size={14} /> Reload
          </button>
        </div>
      </div>

      {/* Video Screen Container */}
      <div className="video-screen-wrapper" ref={containerRef}>
        <div className="video-screen" onClick={togglePlay}>
          {videoError ? (
            <div style={{ textAlign: 'center', padding: 24, color: '#ff9b9b' }}>
              <AlertCircle size={32} style={{ marginBottom: 10 }} />
              <p style={{ margin: 0, fontWeight: 600 }}>{videoError}</p>
              <button
                className="secondary-btn"
                style={{ marginTop: 12 }}
                onClick={(e) => {
                  e.stopPropagation();
                  setVideoError(null);
                  if (videoRef.current) {
                    videoRef.current.load();
                  }
                }}
              >
                <RefreshCw size={14} /> Retry Loading
              </button>
            </div>
          ) : (
            <>
              <video
                ref={videoRef}
                src={mediaSrc}
                className="video-element"
                playsInline
                preload="metadata"
                muted={previewMode === 'live_overlay' && liveAudioTrack === 'dubbed' ? true : isMuted}
                onTimeUpdate={() => {
                  const t = videoRef.current?.currentTime || 0;
                  setCurrentTime(t);
                  if (dubbedAudioRef.current && Math.abs(dubbedAudioRef.current.currentTime - t) > 0.25) {
                    dubbedAudioRef.current.currentTime = t;
                  }
                }}
                onLoadedMetadata={() => {
                  setDuration(videoRef.current?.duration || active.duration_seconds || 0);
                  setIsLoadingVideo(false);
                }}
                onPlay={() => {
                  setIsPlaying(true);
                  if (dubbedAudioRef.current && previewMode === 'live_overlay' && liveAudioTrack === 'dubbed') {
                    dubbedAudioRef.current.play().catch(() => {});
                  }
                }}
                onPause={() => {
                  setIsPlaying(false);
                  if (dubbedAudioRef.current) dubbedAudioRef.current.pause();
                }}
                onWaiting={() => setIsLoadingVideo(true)}
                onPlaying={() => {
                  setIsLoadingVideo(false);
                  if (dubbedAudioRef.current && previewMode === 'live_overlay' && liveAudioTrack === 'dubbed') {
                    dubbedAudioRef.current.play().catch(() => {});
                  }
                }}
                onError={() => {
                  setVideoError('Cannot stream media. File might be missing or corrupted.');
                  setIsLoadingVideo(false);
                }}
              />

              {active.has_dubbed_audio && active.dubbed_audio_url && (
                <audio
                  ref={dubbedAudioRef}
                  src={active.dubbed_audio_url.startsWith('http') ? active.dubbed_audio_url : `${API}${active.dubbed_audio_url}`}
                  preload="auto"
                />
              )}

              {/* Audio-only art if no video stream */}
              {isAudioFile && (
                <div className="audio-screen-art" style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}>
                  <AudioLines size={48} style={{ color: 'var(--gold)', opacity: 0.8 }} />
                  <p style={{ color: 'var(--text)', fontSize: 14, fontWeight: 600, margin: 0 }}>
                    {active.filename}
                  </p>
                  <p style={{ color: 'var(--muted)', fontSize: 11, margin: 0 }}>
                    Audio Track Playback · Synchronized Subtitle Canvas
                  </p>
                </div>
              )}

              {/* Loading Indicator */}
              {isLoadingVideo && (
                <div style={{ position: 'absolute', inset: 0, background: 'rgba(0,0,0,0.45)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Loader2 size={36} className="spin" style={{ color: 'var(--gold)' }} />
                </div>
              )}

              {/* Synchronized Subtitle Overlay (Only in live_overlay mode) */}
              {previewMode === 'live_overlay' && showSubtitles && (activeKhmerText || activeSourceText) && (
                <div className={`subtitle-overlay pos-${position} size-${fontSize}`}>
                  <div className="subtitle-bubble">
                    {comparisonMode === 'dual' && hasTranslation && activeSourceText && (
                      <div className="subtitle-source-line">{activeSourceText}</div>
                    )}
                    <div className="subtitle-khmer-line">{activeKhmerText || activeSourceText}</div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Custom Controls Bar */}
      <div className="player-controls-bar">
        {/* Timeline Slider */}
        <div className="timeline-track-row">
          <span className="timeline-time-badge">{fmtTime(currentTime)}</span>
          <input
            type="range"
            min={0}
            max={duration || active.duration_seconds || 1}
            step={0.05}
            value={currentTime}
            onChange={handleSeek}
            className="timeline-input"
            aria-label="Timeline scrubbing"
          />
          <span className="timeline-time-badge">{fmtTime(duration || active.duration_seconds)}</span>
        </div>

        {/* Buttons Row */}
        <div className="controls-actions-row">
          <div className="controls-group-left">
            <button
              className="player-icon-btn primary"
              onClick={togglePlay}
              title={isPlaying ? 'Pause' : 'Play'}
              aria-label={isPlaying ? 'Pause' : 'Play'}
            >
              {isPlaying ? <Pause size={15} /> : <Play size={15} />}
              <span>{isPlaying ? 'Pause' : 'Play'}</span>
            </button>

            <button className="player-icon-btn" onClick={handleRestart} title="Restart Preview (00:00)">
              <RotateCcw size={14} /> Restart
            </button>

            {previewMode === 'live_overlay' && (
              <button
                className={`player-icon-btn ${showSubtitles ? 'active' : ''}`}
                onClick={() => setShowSubtitles(!showSubtitles)}
                title="Toggle Subtitle Visibility"
              >
                {showSubtitles ? <Eye size={14} /> : <EyeOff size={14} />}
                <span>{showSubtitles ? 'Subtitles ON' : 'Subtitles OFF'}</span>
              </button>
            )}

            {/* Volume Control */}
            <button className="player-icon-btn" onClick={toggleMute} title={isMuted ? 'Unmute' : 'Mute'}>
              {isMuted ? <VolumeX size={14} /> : <Volume2 size={14} />}
            </button>
            <input
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={isMuted ? 0 : volume}
              onChange={handleVolumeChange}
              className="volume-slider"
              aria-label="Volume control"
            />
          </div>

          <div className="controls-group-right">
            {/* Speed Selector */}
            <select
              className="speed-select"
              value={playbackRate}
              onChange={(e) => handleSpeedChange(parseFloat(e.target.value))}
              aria-label="Playback speed"
            >
              <option value="0.5">0.5x</option>
              <option value="0.75">0.75x</option>
              <option value="1">1.0x Normal</option>
              <option value="1.25">1.25x</option>
              <option value="1.5">1.5x</option>
              <option value="2">2.0x</option>
            </select>

            <button className="player-icon-btn" onClick={toggleFullscreen} title="Fullscreen">
              <Maximize2 size={14} /> Fullscreen
            </button>
          </div>
        </div>
      </div>

      {/* Subtitle Settings Drawer */}
      <AnimatePresence>
        {showSettings && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="preview-settings-drawer"
          >
            <div className="preview-setting-item">
              <span className="preview-setting-label">Font Size (ទំហំអក្សរ)</span>
              <div className="preview-setting-pills">
                {(['small', 'medium', 'large'] as const).map((s) => (
                  <button
                    key={s}
                    className={`preview-pill-btn ${fontSize === s ? 'active' : ''}`}
                    onClick={() => setFontSize(s)}
                  >
                    {s.charAt(0).toUpperCase() + s.slice(1)}
                  </button>
                ))}
              </div>
            </div>

            <div className="preview-setting-item">
              <span className="preview-setting-label">Subtitle Position (ទីតាំង)</span>
              <div className="preview-setting-pills">
                {(['bottom', 'center', 'top'] as const).map((p) => (
                  <button
                    key={p}
                    className={`preview-pill-btn ${position === p ? 'active' : ''}`}
                    onClick={() => setPosition(p)}
                  >
                    {p.charAt(0).toUpperCase() + p.slice(1)}
                  </button>
                ))}
              </div>
            </div>

            <div className="preview-setting-item">
              <span className="preview-setting-label">Comparison Display (ការប្រៀបធៀប)</span>
              <div className="preview-setting-pills">
                <button
                  className={`preview-pill-btn ${comparisonMode === 'khmer_only' ? 'active' : ''}`}
                  onClick={() => setComparisonMode('khmer_only')}
                >
                  Khmer Only
                </button>
                <button
                  className={`preview-pill-btn ${comparisonMode === 'dual' ? 'active' : ''}`}
                  onClick={() => setComparisonMode('dual')}
                >
                  Dual (Source + Khmer)
                </button>
              </div>
            </div>

            <div className="preview-setting-item">
              <span className="preview-setting-label">Audio Dubbing Mode (ជម្រើសសំឡេង)</span>
              <div className="preview-setting-pills">
                <button
                  className={`preview-pill-btn ${audioMode === 'dubbed' ? 'active' : ''}`}
                  onClick={() => setAudioMode('dubbed')}
                  title="Replace original speech completely with target-language AI voice"
                >
                  Replace Voice (សំឡេងបកប្រែសុទ្ធ)
                </button>
                <button
                  className={`preview-pill-btn ${audioMode === 'mixed' ? 'active' : ''}`}
                  onClick={() => setAudioMode('mixed')}
                  title="Intelligent ducking: keep background sound effects/music with translated voice"
                >
                  Keep BG Audio (លាយសំឡេងផ្ទៃខាងក្រោយ)
                </button>
                <button
                  className={`preview-pill-btn ${audioMode === 'original' ? 'active' : ''}`}
                  onClick={() => setAudioMode('original')}
                  title="Keep original unaltered audio track"
                >
                  Original (សំឡេងដើម)
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Action & Download Section */}
      <div className="export-action-section">
        <div className="export-action-info">
          <b style={{ fontSize: 14 }}>
            {active.has_rendered_video ? 'Rendered Output Video Ready' : 'Export & Download Subtitles'}
          </b>
          <small style={{ color: 'var(--muted)', fontSize: 11 }}>
            {active.has_rendered_video
              ? 'វីដេអូ MP4 ត្រូវបានដុតបញ្ចូល Subtitles (Hardsub) រួចរាល់។ អ្នកអាចទាញយកវីដេអូ ឬឯកសារ Subtitle ខាងក្រោម។'
              : 'អ្នកអាចទាញយក Subtitle (SRT, VTT, TXT) ភ្លាមៗ ឬ Export ដើម្បីដុតបញ្ចូល Subtitles ចូលក្នុងវីដេអូ MP4។'}
          </small>
        </div>

        <div className="export-action-buttons">
          {/* Export Video Button */}
          <motion.button
            whileTap={{ scale: 0.98 }}
            className="primary-btn"
            disabled={isExporting || busy || (!transcriptList.length && !translationList.length)}
            onClick={handleExportVideo}
            style={{
              background: 'linear-gradient(135deg, #e5c783 0%, #b38a3f 100%)',
              color: '#080f1d',
              fontWeight: 700,
            }}
          >
            {isExporting ? <Loader2 size={15} className="spin" /> : <Film size={15} />}
            {isExporting ? 'Exporting Video (FFmpeg)...' : active.has_rendered_video ? 'Re-export Final Video' : 'Export Final Video (MP4)'}
          </motion.button>

          {/* Download Rendered Video */}
          {active.has_rendered_video ? (
            <a
              className="primary-btn link-btn"
              href={`${API}/api/jobs/${active.id}/rendered-video?download=true`}
              download
            >
              <Download size={15} /> Download Final Video (.mp4)
            </a>
          ) : (
            <button
              className="secondary-btn"
              disabled
              title="Please click 'Export Final Video' first to render the MP4."
            >
              <Download size={15} /> Download Final Video (Export First)
            </button>
          )}

          {/* Subtitle Downloads */}
          <a
            className="secondary-btn link-btn"
            href={`${API}/api/jobs/${active.id}/subtitles.srt?translated=true`}
            download
            title="Download SubRip Subtitles (.srt)"
          >
            <Download size={14} /> .SRT
          </a>

          <a
            className="secondary-btn link-btn"
            href={`${API}/api/jobs/${active.id}/subtitles.vtt?translated=true`}
            download
            title="Download WebVTT Subtitles (.vtt)"
          >
            <Download size={14} /> .VTT
          </a>

          <a
            className="secondary-btn link-btn"
            href={`${API}/api/jobs/${active.id}/transcript.txt?translated=true`}
            download
            title="Download Plain Text Transcript (.txt)"
          >
            <FileText size={14} /> .TXT
          </a>
        </div>
      </div>
    </div>
  );
};

export default function App() {
  const [dark, setDark] = useState(() => {
    const saved = localStorage.getItem('khmer_translator_theme');
    if (saved) return saved === 'dark';
    return true;
  });

  const [currentUser, setCurrentUser] = useState<AuthUser | null>(() => AuthService.getCachedUser());
  const [isAuthChecking, setIsAuthChecking] = useState<boolean>(true);
  const [apiBaseUrl, setApiBaseUrl] = useState<string>(getApiBase);
  API = apiBaseUrl;

  const [customApiInput, setCustomApiInput] = useState<string>(() => {
    return localStorage.getItem('khmer_ai_api_url') || (apiBaseUrl.startsWith('http://127.0.0.1') ? '' : apiBaseUrl);
  });
  const isHttps = typeof window !== 'undefined' && window.location.protocol === 'https:';
  const isLocalApi = apiBaseUrl.startsWith('http://127.0.0.1') || apiBaseUrl.startsWith('http://localhost');
  const needsBackendUrl = isHttps && isLocalApi;

  const handleSaveCustomApi = async (url: string) => {
    const clean = url.trim().replace(/\/+$/, '');
    if (!clean) return;
    localStorage.setItem('khmer_ai_api_url', clean);
    setApiBaseUrl(clean);
    API = clean;
    setNotice('បានរក្សាទុក និងភ្ជាប់ទៅកាន់ Backend Server ដោយជោគជ័យ!');
    await loadState();
  };

  useEffect(() => {
    AuthService.verifySession().then((user) => {
      setCurrentUser(user);
      setIsAuthChecking(false);
    });
  }, [apiBaseUrl]);

  useEffect(() => {
    localStorage.setItem('khmer_translator_theme', dark ? 'dark' : 'light');
    document.documentElement.classList.toggle('dark', dark);
    document.documentElement.classList.toggle('light', !dark);
  }, [dark]);

  const [section, setSection] = useState<'Workspace' | 'Overview' | 'Subtitles' | 'Characters' | 'Proofreading' | 'Dictionary' | 'Preview' | 'Export' | 'Settings'>('Workspace');
  const [workflowMode, setWorkflowMode] = useState<'beginner' | 'advanced'>(() => {
    return (localStorage.getItem('khmer_translator_workflow_mode') as 'beginner' | 'advanced') || 'beginner';
  });

  const handleSetWorkflowMode = (mode: 'beginner' | 'advanced') => {
    setWorkflowMode(mode);
    localStorage.setItem('khmer_translator_workflow_mode', mode);
  };

  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [active, setActive] = useState<Job | null>(null);
  const [caps, setCaps] = useState<Caps | null>(null);
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>('tiny');
  const [selectedLanguage, setSelectedLanguage] = useState<string>('auto');
  const [selectedSourceLang, setSelectedSourceLang] = useState<string>('auto');
  const [selectedTargetLang, setSelectedTargetLang] = useState<string>('km');
  const [languagesData, setLanguagesData] = useState<LanguagesResponse | null>(null);
  const [importUrl, setImportUrl] = useState<string>('');
  const [showUrlImport, setShowUrlImport] = useState<boolean>(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [editedSegments, setEditedSegments] = useState<TranscriptSegment[]>([]);
  const [activeSegmentIndex, setActiveSegmentIndex] = useState<number | null>(null);
  const [isDirty, setIsDirty] = useState(false);
  const [copied, setCopied] = useState(false);
  const [busy, setBusy] = useState(false);
  const [statusStage, setStatusStage] = useState('');
  const [notice, setNotice] = useState('');
  const [error, setError] = useState('');
  const [drag, setDrag] = useState(false);
  const [showHelp, setShowHelp] = useState(false);
  const [showOnboarding, setShowOnboarding] = useState(false);

  const fileRef = useRef<HTMLInputElement>(null);
  const [uploadProgress, setUploadProgress] = useState<UploadProgressInfo | null>(null);
  const uploadControllerRef = useRef<MediaUploadController | null>(null);
  const [voices, setVoices] = useState<VoiceInfo[]>([]);
  const [translationSegments, setTranslationSegments] = useState<TranscriptSegment[]>([]);
  const [saveStatus, setSaveStatus] = useState<'saved' | 'saving' | 'error' | 'idle'>('saved');
  const [appSettings, setAppSettings] = useState<AppSettings>({
    ui_language: 'km',
    default_model: 'tiny',
    default_source_lang: 'auto',
    default_target_lang: 'km',
    default_tts_voice: 'km-KH-PisethNeural',
    subtitle_font_size: 'medium',
  });
  const autoSaveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Sync edited segments, translations, and languages whenever active job changes
  useEffect(() => {
    if (active) {
      setEditedSegments([...(active.transcript || [])]);
      setTranslationSegments([...(active.translation || [])]);
      if (active.source_language) setSelectedSourceLang(active.source_language);
      if (active.target_language) setSelectedTargetLang(active.target_language);
      setIsDirty(false);
      setSaveStatus('saved');
    } else {
      setEditedSegments([]);
      setTranslationSegments([]);
      setIsDirty(false);
      setSaveStatus('saved');
    }
  }, [active?.id, active?.transcript, active?.translation, active?.source_language, active?.target_language]);

  // Debounced Auto-Save
  useEffect(() => {
    if (!isDirty || !active) return;
    setSaveStatus('saving');
    if (autoSaveTimerRef.current) clearTimeout(autoSaveTimerRef.current);

    autoSaveTimerRef.current = setTimeout(async () => {
      try {
        const res = await authFetch(`${API}/api/jobs/${active.id}/transcript`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ transcript: editedSegments }),
        });
        if (!res.ok) throw new Error('Auto-save failed');
        const data = await res.json();
        setActive(data);
        setIsDirty(false);
        setSaveStatus('saved');
      } catch {
        setSaveStatus('error');
      }
    }, 1500);

    return () => {
      if (autoSaveTimerRef.current) clearTimeout(autoSaveTimerRef.current);
    };
  }, [editedSegments, isDirty, active?.id]);

  const activeJobIdRef = useRef<string | null>(null);
  useEffect(() => {
    activeJobIdRef.current = active?.id || null;
  }, [active?.id]);

  // Load backend state with resilient cold-start detection and non-collapsing settled calls
  const loadState = async (retryCount = 0) => {
    try {
      const results = await Promise.allSettled([
        authFetch(`${API}/api/jobs`),
        authFetch(`${API}/api/capabilities`),
        authFetch(`${API}/api/transcription/models`),
        authFetch(`${API}/api/dubbing/voices`),
        authFetch(`${API}/api/settings`),
        authFetch(`${API}/api/languages`),
      ]);

      const [resJobs, resCaps, resModels, resVoices, resSettings, resLangs] = results.map((r) =>
        r.status === 'fulfilled' ? r.value : null
      );

      // Detect potential Render Free Tier cold-start (all initial calls rejected or non-200)
      const allFailed = results.every((r) => r.status === 'rejected' || (r.status === 'fulfilled' && !r.value?.ok));
      if (allFailed && retryCount < 3) {
        setNotice('🔄 ម៉ាស៊ីនបម្រើ Cloud Backend កំពុងចាប់ផ្ដើមដំណើរការឡើងវិញ (Server is waking up)... សូមរង់ចាំបន្តិច');
        setTimeout(() => {
          void loadState(retryCount + 1);
        }, 2500);
        return;
      }

      if (resJobs && resJobs.ok) {
        const jobsData: Job[] = await resJobs.json();
        setJobs(jobsData);
        const currentTargetId = activeJobIdRef.current;
        if (currentTargetId) {
          const fresh = jobsData.find((j: Job) => j.id === currentTargetId);
          if (fresh) {
            setActive(fresh);
          }
          // Do NOT reset to jobsData[0] if activeJobId exists but is pending or fresh
        } else if (jobsData.length > 0) {
          setActive(jobsData[0]);
        }
      }
      if (resCaps && resCaps.ok) {
        const capsData = await resCaps.json();
        setCaps(capsData);
        if (capsData.default_model) setSelectedModel(capsData.default_model);
      }
      if (resModels && resModels.ok) {
        const modelsData = await resModels.json();
        setModels(modelsData.models || []);
      }
      if (resVoices && resVoices.ok) {
        const voicesData = await resVoices.json();
        setVoices(voicesData || []);
      }
      if (resSettings && resSettings.ok) {
        const settingsData = await resSettings.json();
        setAppSettings(settingsData);
      }
      if (resLangs && resLangs.ok) {
        const langsData = await resLangs.json();
        setLanguagesData(langsData);
      }
    } catch {
      const isLocal = API.includes('localhost') || API.includes('127.0.0.1');
      const msg = isLocal
        ? 'មិនអាចភ្ជាប់ទៅកាន់ FastAPI Backend (Local) បានទេ។ សូមពិនិត្យថាតើ Backend កំពុងដំណើរការនៅ port 8000 ដែរឬទេ។'
        : 'មិនអាចភ្ជាប់ទៅកាន់ម៉ាស៊ីនបម្រើ Cloud Backend បានទេ។ ម៉ាស៊ីនបម្រើអាចនឹងកំពុងចាប់ផ្ដើមដំណើរការឡើងវិញ (Cold Start) សូមព្យាយាមម្ដងទៀត។';
      setError(msg);
    }
  };

  const handleRenameProject = async (jobId: string, newName: string) => {
    try {
      const res = await authFetch(`${API}/api/jobs/${jobId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newName }),
      });
      if (!res.ok) throw new Error('Rename failed');
      const updated = await res.json();
      if (active?.id === jobId) setActive(updated);
      await loadState();
      setNotice('បានប្តូរឈ្មោះគម្រោងដោយជោគជ័យ');
    } catch (err: any) {
      setError(`បរាជ័យក្នុងការប្តូរឈ្មោះ: ${err.message || err}`);
    }
  };

  const handleSaveSettings = async (newSettings: AppSettings) => {
    const res = await authFetch(`${API}/api/settings`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newSettings),
    });
    if (!res.ok) throw new Error('Failed to save settings');
    const saved = await res.json();
    setAppSettings(saved);
  };

  const runTranslation = async (jobId: string, srcLang?: string, tgtLang?: string) => {
    setBusy(true);
    setError('');
    const src = srcLang || selectedSourceLang || 'auto';
    const tgt = tgtLang || selectedTargetLang || 'km';
    setNotice(`កំពុងបកប្រែ (${src} → ${tgt}) តាមប្រព័ន្ធ Universal Translation (Zero Ollama)...`);
    try {
      const res = await authFetch(`${API}/api/jobs/${jobId}/translate?source_language=${encodeURIComponent(src)}&target_language=${encodeURIComponent(tgt)}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'បរាជ័យក្នុងការបកប្រែ');
      setActive(data);
      setTranslationSegments(data.translation || []);
      setNotice(`ការបកប្រែជាភាសា ${tgt} បានជោគជ័យពេញលេញ (100%)!`);
    } catch (err: any) {
      setError(formatErrorMessage(err, 'បរាជ័យក្នុងការបកប្រែ'));
    } finally {
      setBusy(false);
    }
  };

  const handleUpdateSpeakers = async (updatedSpeakers: SpeakerProfile[]) => {
    if (!active) return;
    try {
      const res = await authFetch(`${API}/api/jobs/${active.id}/speakers`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ speakers: updatedSpeakers }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to update speakers');
      setActive(data);
      setNotice('បានរក្សាទុកទម្រង់តួអង្គ (Character Profiles) ដោយជោគជ័យ');
    } catch (err: any) {
      setError(err.message || 'បរាជ័យក្នុងការកែប្រែតួអង្គ');
    }
  };

  const handleMergeSpeakers = async (keepSpeakerId: string, mergeSpeakerId: string) => {
    if (!active) return;
    try {
      const res = await authFetch(`${API}/api/jobs/${active.id}/speakers/merge`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ keep_speaker_id: keepSpeakerId, merge_speaker_id: mergeSpeakerId }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to merge speakers');
      setActive(data);
      setEditedSegments([...(data.transcript || [])]);
      setTranslationSegments([...(data.translation || [])]);
      setNotice('បានបញ្ចូលតួអង្គ (Merge Characters) ដោយជោគជ័យ');
    } catch (err: any) {
      setError(err.message || 'បរាជ័យក្នុងការបញ្ចូលតួអង្គ');
    }
  };

  const handleSplitSpeaker = async (speakerId: string, segmentIds: number[], newSpeakerName?: string) => {
    if (!active) return;
    try {
      const res = await authFetch(`${API}/api/jobs/${active.id}/speakers/split`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ speaker_id: speakerId, segment_ids: segmentIds, new_speaker_name: newSpeakerName }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to split speaker');
      setActive(data);
      setEditedSegments([...(data.transcript || [])]);
      setTranslationSegments([...(data.translation || [])]);
      setNotice('បានបំបែកតួអង្គថ្មី (Split Character) ដោយជោគជ័យ');
    } catch (err: any) {
      setError(err.message || 'បរាជ័យក្នុងការបំបែកតួអង្គ');
    }
  };

  const handleImportUrl = async () => {
    if (!importUrl.trim()) return;
    setBusy(true);
    setError('');
    setStatusStage('កំពុងទាញយកវីដេអូពី URL (Safe Media Downloader)...');
    try {
      const res = await authFetch(`${API}/api/jobs/import-url`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url: importUrl.trim(),
          source_language: selectedSourceLang,
          target_language: selectedTargetLang,
          auto_diarize: true,
          auto_translate: true,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'បរាជ័យក្នុងការ Import ពី URL');
      setActive(data);
      setImportUrl('');
      setShowUrlImport(false);
      await loadState();
      setNotice('បាន Import វីដេអូពី URL ដោយជោគជ័យ! កំពុងចាប់ផ្តើមបកប្រែ...');
      await runTranscription(
        data.id,
        selectedModel,
        selectedSourceLang,
        selectedTargetLang,
        true,
        true,
        workflowMode === 'beginner'
      );
    } catch (err: any) {
      setError(err.message || 'បរាជ័យក្នុងការ Import ពី URL');
    } finally {
      setBusy(false);
      setStatusStage('');
    }
  };

  useEffect(() => {
    void loadState();
    const pollIntervalMs = busy || active?.status === 'transcribing' ? 2500 : 6000;
    const interval = setInterval(() => void loadState(), pollIntervalMs);
    return () => clearInterval(interval);
  }, [active?.id, active?.status, busy]);


  // Real-time EventSource (SSE) + resilient polling for active job processing
  useEffect(() => {
    const currentJobId = active?.id;
    if (!currentJobId) return;
    const isTerminal = ['transcribed', 'completed', 'failed', 'cancelled'].includes(active.status);
    if (isTerminal) return;

    let isMounted = true;
    let es: EventSource | null = null;
    let pollInterval: ReturnType<typeof setInterval> | null = null;

    try {
      es = new EventSource(`${API}/api/jobs/${currentJobId}/events`);
      es.onmessage = (event) => {
        if (!isMounted) return;
        try {
          const freshJob: Job = JSON.parse(event.data);
          setActive((prev) => (prev?.id === freshJob.id ? { ...prev, ...freshJob } : prev));
          if (['transcribed', 'completed', 'failed', 'cancelled'].includes(freshJob.status)) {
            es?.close();
            void loadState();
          }
        } catch (err) {
          console.error('SSE JSON error:', err);
        }
      };
      es.onerror = () => {
        if (es) {
          es.close();
          es = null;
        }
        if (!pollInterval && isMounted) {
          pollInterval = setInterval(async () => {
            try {
              const res = await authFetch(`${API}/api/jobs/${currentJobId}`);
              if (res.status === 404) {
                if (pollInterval) {
                  clearInterval(pollInterval);
                  pollInterval = null;
                }
                if (isMounted) {
                  setActive((prev) => (prev?.id === currentJobId ? null : prev));
                  setNotice('គម្រោងពីមុនផុតកំណត់ ឬមិនមាននៅលើម៉ាស៊ីនបម្រើទៀតទេ (Job expired or not found)');
                }
                return;
              }
              if (res.ok) {
                const freshJob: Job = await res.json();
                if (isMounted) {
                  setActive((prev) => (prev?.id === freshJob.id ? { ...prev, ...freshJob } : prev));
                  if (['transcribed', 'completed', 'failed', 'cancelled'].includes(freshJob.status)) {
                    if (pollInterval) clearInterval(pollInterval);
                    void loadState();
                  }
                }
              }
            } catch {
              // ignore
            }
          }, 1000);
        }
      };
    } catch {
      pollInterval = setInterval(async () => {
        try {
          const res = await authFetch(`${API}/api/jobs/${currentJobId}`);
          if (res.status === 404) {
            if (pollInterval) clearInterval(pollInterval);
            if (isMounted) {
              setActive((prev) => (prev?.id === currentJobId ? null : prev));
            }
            void loadState();
            return;
          }
          if (res.ok) {
            const freshJob: Job = await res.json();
            if (isMounted) {
              setActive((prev) => (prev?.id === freshJob.id ? { ...prev, ...freshJob } : prev));
              if (['transcribed', 'completed', 'failed', 'cancelled'].includes(freshJob.status)) {
                if (pollInterval) clearInterval(pollInterval);
                void loadState();
              }
            }
          }
        } catch {
          // ignore
        }
      }, 1000);
    }

    return () => {
      isMounted = false;
      if (es) es.close();
      if (pollInterval) clearInterval(pollInterval);
    };
  }, [active?.id, active?.status]);

  const handleCancelJob = async (jobId: string) => {
    try {
      setBusy(true);
      const res = await authFetch(`${API}/api/jobs/${jobId}/cancel`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        if (data.job) setActive(data.job);
        setNotice('បានបោះបង់ដំណើរការដោយជោគជ័យ (Job cancelled)');
        await loadState();
      }
    } catch {
      setError('មិនអាចបោះបង់ការងារបានទេ');
    } finally {
      setBusy(false);
    }
  };

  const handleRetryJob = async (jobId: string) => {
    try {
      setBusy(true);
      setError('');
      setNotice('កំពុងចាប់ផ្តើមដំណើរការឡើងវិញ...');
      const res = await authFetch(`${API}/api/jobs/${jobId}/retry?model=${encodeURIComponent(selectedModel)}`, {
        method: 'POST',
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'ការចាប់ផ្តើមឡើងវិញបរាជ័យ');
      setActive(data);
      await loadState();
      setNotice('ការចាប់ផ្តើមឡើងវិញបានជោគជ័យពេញលេញ!');
    } catch (err) {
      setError(formatErrorMessage(err, 'ការចាប់ផ្តើមឡើងវិញបរាជ័យ'));
    } finally {
      setBusy(false);
    }
  };

  // File selection & validation
  const handleFileSelect = (file: File | undefined) => {
    if (!file) return;
    setError('');
    setNotice('');

    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!SUPPORTED_EXTS.includes(ext)) {
      setError(`ទម្រង់ឯកសារមិនគាំទ្រ: "${ext}"។ គាំទ្រតែ: ${SUPPORTED_EXTS.join(', ')}`);
      return;
    }

    if (file.size > 4096 * 1024 * 1024) {
      setError('ឯកសារធំជាងទំហំកំណត់ 4096 MB (4 GB)។ សូមជ្រើសរើសឯកសារតូចជាងនេះ។');
      return;
    }

    if (uploadProgress && ['uploading', 'paused'].includes(uploadProgress.phase)) {
      if (uploadControllerRef.current) {
        uploadControllerRef.current.cancel();
        uploadControllerRef.current = null;
      }
      setUploadProgress(null);
    }

    setSelectedFile(file);
    setSection('Workspace');
    setNotice(`បានជ្រើសរើសឯកសារ: ${file.name} (${fmtFileSize(file.size)})`);
  };

  // Upload Controls: Pause, Resume, Cancel, Retry
  const handlePauseUpload = () => {
    if (uploadControllerRef.current) {
      uploadControllerRef.current.pause();
      setBusy(false);
    }
  };

  const handleResumeUpload = async () => {
    if (!uploadControllerRef.current) return;
    setBusy(true);
    setError('');
    setStatusStage('កំពុង Upload ឯកសារមេឌៀទៅកាន់ម៉ាស៊ីនបម្រើ...');
    try {
      const completedJob = await uploadControllerRef.current.resume();
      if (completedJob) {
        setActive(completedJob);
        setSelectedFile(null);
        setUploadProgress(null);
        uploadControllerRef.current = null;
        await loadState();

        const isBeginner = workflowMode === 'beginner';
        await runTranscription(
          completedJob.id,
          selectedModel,
          selectedSourceLang,
          selectedTargetLang,
          true,
          true,
          isBeginner
        );
      }
    } catch (err: any) {
      setError(formatErrorMessage(err, 'ការបន្ត Upload បរាជ័យ'));
    } finally {
      setBusy(false);
      setStatusStage('');
    }
  };

  const handleCancelUpload = async () => {
    if (uploadControllerRef.current) {
      await uploadControllerRef.current.cancel();
      uploadControllerRef.current = null;
    }
    setUploadProgress(null);
    setBusy(false);
    setStatusStage('');
    setNotice('ការ Upload ត្រូវបានបោះបង់ និងសម្អាតរួចរាល់ (Upload cancelled)');
  };

  const handleRetryUpload = () => {
    if (uploadControllerRef.current && uploadProgress?.phase === 'failed') {
      handleResumeUpload();
    } else if (selectedFile) {
      if (workflowMode === 'beginner') {
        handleBeginnerTranslateAndDub();
      } else {
        handleUploadAndTranscribe();
      }
    }
  };

  // Upload and Transcribe workflow
  const handleUploadAndTranscribe = async () => {
    if (!selectedFile) return;
    setBusy(true);
    setError('');
    setStatusStage('កំពុង Upload ឯកសារមេឌៀទៅកាន់ម៉ាស៊ីនបម្រើ...');

    const controller = new MediaUploadController(selectedFile, {
      apiBase: API,
      sourceLang: selectedSourceLang,
      targetLang: selectedTargetLang,
      onProgress: (info) => {
        setUploadProgress(info);
      },
    });
    uploadControllerRef.current = controller;

    try {
      const uploadedJob = await controller.start();
      if (!uploadedJob) {
        // Paused or cancelled
        return;
      }

      setActive(uploadedJob);
      setSelectedFile(null);
      setUploadProgress(null);
      uploadControllerRef.current = null;
      await loadState();

      try {
        await runTranscription(uploadedJob.id, selectedModel, selectedSourceLang, selectedTargetLang, true, true, false);
      } catch (transcribeErr: any) {
        // Preserve uploaded job so the user never has to re-upload the file
        setError(`ការ Upload វីដេអូបានជោគជ័យ ១០០% ប៉ុន្តែការស្គាល់សំឡេងមានបញ្ហា: ${transcribeErr.message || transcribeErr}។ ឯកសារត្រូវបានរក្សាទុកនៅលើ Server រួចហើយ អ្នកអាចចុចប៊ូតុង "សាកល្បងម្ដងទៀត" ដោយមិនបាច់ Upload ឡើងវិញទេ។`);
      }
    } catch (err) {
      setError(formatErrorMessage(err, 'ដំណើរការបរាជ័យ'));
    } finally {
      setBusy(false);
      setStatusStage('');
    }
  };

  const runTranscription = async (
    jobId: string,
    model: string,
    srcLang: string,
    tgtLang: string = 'km',
    autoDiarize = true,
    autoTranslate = true,
    autoDub = false
  ) => {
    setBusy(true);
    setError('');
    setStatusStage(autoDub ? 'កំពុងដំណើរការបកប្រែ និងបង្កើតសំឡេង AI Dubbing ស្វ័យប្រវត្តិ...' : `កំពុងដំណើរការស្គាល់សំឡេងដោយ Faster-Whisper (គំរូ ${model})...`);

    try {
      const params = new URLSearchParams({
        model,
        source_language: srcLang || 'auto',
        target_language: tgtLang || 'km',
        auto_diarize: autoDiarize ? 'true' : 'false',
        auto_translate: autoTranslate ? 'true' : 'false',
        auto_dub: autoDub ? 'true' : 'false',
      });
      const res = await authFetch(`${API}/api/jobs/${jobId}/transcribe?${params.toString()}`, {
        method: 'POST',
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'ការស្គាល់សំឡេងបរាជ័យ');
      }
      setActive(data);
      await loadState();
      if (autoDub) {
        setNotice('ការបកប្រែ និងបង្កើតសំឡេង AI Dubbed បានជោគជ័យពេញលេញ! អ្នកអាចស្ដាប់ និង Preview ភ្លាមៗ។');
        setSection('Preview');
      } else {
        setNotice('ការស្គាល់សំឡេង និងការវិភាគសំឡេងតួអង្គបានជោគជ័យពេញលេញ!');
      }
    } catch (err) {
      setError(formatErrorMessage(err, 'ការស្គាល់សំឡេងបរាជ័យ'));
    } finally {
      setBusy(false);
      setStatusStage('');
    }
  };

  // Beginner Mode: 1-Click Unified Translate & Dub Pipeline
  const handleBeginnerTranslateAndDub = async () => {
    if (busy) return;
    if (selectedFile) {
      setBusy(true);
      setError('');
      setStatusStage('កំពុង Upload ឯកសារមេឌៀទៅកាន់ម៉ាស៊ីនបម្រើ...');

      const controller = new MediaUploadController(selectedFile, {
        apiBase: API,
        sourceLang: selectedSourceLang,
        targetLang: selectedTargetLang,
        onProgress: (info) => {
          setUploadProgress(info);
        },
      });
      uploadControllerRef.current = controller;

      try {
        const uploadedJob = await controller.start();
        if (!uploadedJob) {
          // Paused or cancelled
          return;
        }

        setActive(uploadedJob);
        setSelectedFile(null);
        setUploadProgress(null);
        uploadControllerRef.current = null;
        await loadState();

        try {
          await runTranscription(uploadedJob.id, selectedModel, selectedSourceLang, selectedTargetLang, true, true, true);
        } catch (transcribeErr: any) {
          // Preserve uploaded job so the user never has to re-upload the file
          setError(`ការ Upload វីដេអូបានជោគជ័យ ១០០% ប៉ុន្តែការបកប្រែ/បញ្ចូលសំឡេងមានបញ្ហា: ${transcribeErr.message || transcribeErr}។ ឯកសារត្រូវបានរក្សាទុកនៅលើ Server រួចហើយ អ្នកអាចចុចប៊ូតុង "សាកល្បងម្ដងទៀត" ដោយមិនបាច់ Upload ឡើងវិញទេ។`);
        }
      } catch (err: any) {
        setError(formatErrorMessage(err, 'ការ Upload បរាជ័យ'));
      } finally {
        setBusy(false);
        setStatusStage('');
      }
    } else if (active) {
      await runTranscription(active.id, selectedModel, selectedSourceLang, selectedTargetLang, true, true, true);
    } else {
      setError('សូមជ្រើសរើស ឬ Upload វីដេអូមួយជាមុនសិន។');
    }
  };


  // Save edited transcript segments
  const saveEditedTranscript = async () => {
    if (!active) return;
    setBusy(true);
    setError('');
    try {
      const res = await authFetch(`${API}/api/jobs/${active.id}/transcript`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ segments: editedSegments }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'រក្សាទុកមិនបានជោគជ័យ');
      setActive(data);
      setIsDirty(false);
      setNotice('បានរក្សាទុកការកែសម្រួលដោយជោគជ័យ');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'បរាជ័យក្នុងការរក្សាទុក');
    } finally {
      setBusy(false);
    }
  };

  const handleSegmentTextChange = (index: number, newText: string) => {
    const updated = [...editedSegments];
    updated[index] = { ...updated[index], text: newText };
    setEditedSegments(updated);
    setIsDirty(true);
  };

  const handleRemoveSegment = (index: number) => {
    const updated = editedSegments.filter((_, idx) => idx !== index);
    setEditedSegments(updated);
    setIsDirty(true);
  };

  const handleAddSegment = () => {
    const lastSeg = editedSegments[editedSegments.length - 1];
    const newStart = lastSeg ? lastSeg.end : 0;
    const newEnd = newStart + 3.0;
    const newSeg: TranscriptSegment = {
      id: editedSegments.length + 1,
      start: newStart,
      end: newEnd,
      text: '',
    };
    setEditedSegments([...editedSegments, newSeg]);
    setIsDirty(true);
  };

  const handleCopyTranscript = async () => {
    if (!editedSegments.length) return;
    const fullText = editedSegments
      .map((s) => `[${fmtTime(s.start)} --> ${fmtTime(s.end)}] ${s.text}`)
      .join('\n');
    try {
      await navigator.clipboard.writeText(fullText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
      setNotice('បានចម្លងអត្ថបទទាំងអស់ទៅកាន់ Clipboard!');
    } catch {
      setError('មិនអាចចម្លងអត្ថបទបានទេ។');
    }
  };

  const handleDeleteJob = async (jobId: string) => {
    if (!confirm('តើអ្នកពិតជាចង់លុបគម្រោងនេះមែនទេ?')) return;
    try {
      const res = await authFetch(`${API}/api/jobs/${jobId}`, { method: 'DELETE' });
      if (res.ok) {
        if (active?.id === jobId) {
          setActive(null);
          setSelectedFile(null);
        }
        await loadState();
        setNotice('បានលុបគម្រោងរួចរាល់');
      }
    } catch {
      setError('មិនអាចលុបគម្រោងបានទេ');
    }
  };

  const handleNewProject = () => {
    setActive(null);
    setSelectedFile(null);
    setNotice('');
    setError('');
    setSection('Workspace');
  };

  const totalMediaDuration = jobs.reduce((acc, j) => acc + (j.duration_seconds || 0), 0);
  const activeIsVideo = selectedFile
    ? selectedFile.type.startsWith('video') || ['.mp4', '.mkv', '.mov', '.avi', '.webm'].some((e) => selectedFile.name.endsWith(e))
    : active?.filename
    ? ['.mp4', '.mkv', '.mov', '.avi', '.webm'].some((e) => active.filename.endsWith(e))
    : false;

  if (isAuthChecking) {
    return (
      <div className={dark ? 'app dark' : 'app light'} style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', background: '#0B1020', color: '#D6B46A' }}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16 }}>
          <img src="/logo.png" alt="Khmer Heritage" style={{ width: 64, height: 64, filter: 'drop-shadow(0 0 16px rgba(214,180,106,0.5))' }} />
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.95rem', fontWeight: 600, letterSpacing: '0.05em' }}>
            <span className="live-dot" /> កំពុងផ្ទៀងផ្ទាត់គណនី ANGKOR NEXUS...
          </div>
        </div>
      </div>
    );
  }

  if (!currentUser) {
    return (
      <AngkorNexusAuth
        dark={dark}
        onSuccess={(user) => {
          setCurrentUser(user);
          void loadState();
        }}
      />
    );
  }

  return (
    <div className={dark ? 'app dark' : 'app light'}>
      {/* Authentic Cambodian Cultural Ambient Backdrop */}
      <CambodianCulturalBackground
        variant="ambient"
        mode={appSettings.cultural_background_mode || 'subtle'}
        dark={dark}
      />

      {/* Mobile Backdrop for Navigation Drawer */}
      {mobileMenuOpen && (
        <div
          className="mobile-backdrop"
          onClick={() => setMobileMenuOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Sidebar with animated active indicators */}
      <aside className={`sidebar ${mobileMenuOpen ? 'mobile-open' : ''}`}>
        <div className="brand">
          <div className="brand-mark-img">
            <img src="/logo.png" alt="Khmer Cultural Heritage Logo" className="brand-logo" />
          </div>
          <div>
            <b>KHMER<span> TRANSLATOR</span></b>
            <small style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <KhmerLotusMotif size={10} /> មរតកវប្បធម៌ខ្មែរ · SPEECH AI
            </small>
          </div>
          <button
            className="icon-btn mobile-menu"
            aria-label="Toggle mobile menu"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? <X size={18} /> : <Menu size={18} />}
          </button>
        </div>

        <div className="workspace-pill">
          <div className="workspace-icon">
            <Sparkles size={16} />
          </div>
          <div>
            <b>Local Workspace</b>
            <small>Ubuntu · 3.3 GiB RAM</small>
          </div>
          <ChevronDown size={15} />
        </div>

        <div style={{ padding: '0 12px 10px 12px' }}>
          <div className="workflow-mode-tabs" style={{ width: '100%', justifyContent: 'center' }}>
            <button
              type="button"
              className={`workflow-mode-tab ${workflowMode === 'beginner' ? 'active' : ''}`}
              style={{ flex: 1, justifyContent: 'center' }}
              onClick={() => handleSetWorkflowMode('beginner')}
              title="Beginner Mode (សាមញ្ញ)"
            >
              <Sparkles size={12} /> Beginner
            </button>
            <button
              type="button"
              className={`workflow-mode-tab ${workflowMode === 'advanced' ? 'active' : ''}`}
              style={{ flex: 1, justifyContent: 'center' }}
              onClick={() => handleSetWorkflowMode('advanced')}
              title="Advanced Studio (កម្រិតខ្ពស់)"
            >
              <Sliders size={12} /> Advanced
            </button>
          </div>
        </div>

        <p className="nav-label">NAVIGATION</p>
        <nav>
          {[
            [LayoutDashboard, 'Overview'],
            [Clapperboard, 'Workspace'],
            [Subtitles, 'Subtitles'],
            [Users, 'Characters'],
            [FileCheck2, 'Proofreading'],
            [BookOpen, 'Dictionary'],
            [Film, 'Preview'],
            [FolderOpen, 'Export'],
          ].map(([Icon, name]: any) => {
            const isSelected = section === name;
            return (
              <button
                key={name}
                className={`nav-item ${isSelected ? 'selected' : ''}`}
                onClick={() => {
                  setSection(name as any);
                  setMobileMenuOpen(false);
                }}
              >
                {isSelected && (
                  <motion.div
                    layoutId="activeNavIndicator"
                    className="nav-indicator"
                    transition={{ type: 'spring', stiffness: 380, damping: 30 }}
                  />
                )}
                <Icon size={18} />
                <span>{name}</span>
                {name === 'Workspace' && active && <span className="nav-dot" />}
              </button>
            );
          })}
        </nav>

        <p className="nav-label tools-label">SYSTEM & HELP</p>
        <nav>
          <button
            className={`nav-item ${section === 'Settings' ? 'selected' : ''}`}
            onClick={() => {
              setSection('Settings');
              setMobileMenuOpen(false);
            }}
          >
            {section === 'Settings' && (
              <motion.div
                layoutId="activeNavIndicator"
                className="nav-indicator"
                transition={{ type: 'spring', stiffness: 380, damping: 30 }}
              />
            )}
            <Settings2 size={18} />
            <span>Settings & Models</span>
          </button>
          <button
            className="nav-item"
            onClick={() => {
              setShowHelp(true);
              setMobileMenuOpen(false);
            }}
          >
            <CircleHelp size={18} />
            <span>Help Guide</span>
          </button>
        </nav>

        {/* Animated Khmer Celestial Angel (Devata) on Sidebar */}
        <AnimatedDevata
          show={appSettings.show_celestial_angel !== false}
          reducedMotion={appSettings.reduced_motion}
          dark={dark}
          variant="sidebar"
        />

        <div className="sidebar-bottom">
          <div className="local-card">
            <div className="local-top">
              <span className="live-dot" /> LOCAL SPEECH ENGINE <ShieldCheck size={15} />
            </div>
            <b>{caps?.faster_whisper ? 'faster-whisper Active' : 'faster-whisper Offline'}</b>
            <small>
              {caps?.faster_whisper
                ? `Model: ${selectedModel} (CPU int8)`
                : 'Install faster-whisper in backend venv.'}
            </small>
            <div className="local-line">
              <span style={{ width: caps?.faster_whisper ? '100%' : '15%' }} />
            </div>
          </div>

          <div className="profile" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%', padding: '10px 12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, minWidth: 0 }}>
              <div style={{
                width: 34,
                height: 34,
                borderRadius: '50%',
                background: 'linear-gradient(135deg, #D6B46A, #927044)',
                color: '#0B1020',
                fontWeight: 700,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '0.88rem',
                flexShrink: 0,
                boxShadow: '0 0 10px rgba(214,180,106,0.3)'
              }}>
                {currentUser?.full_name?.charAt(0)?.toUpperCase() || 'U'}
              </div>
              <div style={{ minWidth: 0 }}>
                <b style={{ display: 'block', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap', maxWidth: 110, fontSize: '0.85rem' }}>
                  {currentUser?.full_name || 'Khmer AI'}
                </b>
                <small style={{ display: 'block', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap', maxWidth: 110, opacity: 0.7, fontSize: '0.72rem' }}>
                  {currentUser?.email || COPYRIGHT_OWNER}
                </small>
              </div>
            </div>
            <button
              className="icon-btn"
              onClick={() => {
                AuthService.logout();
                setCurrentUser(null);
                setJobs([]);
                setActive(null);
              }}
              title="ចាកចេញ (Sign Out)"
              aria-label="Sign Out"
              style={{ color: '#D6B46A', padding: 6, flexShrink: 0 }}
            >
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Container */}
      <main className="main">
        <header className="topbar">
          <div className="topbar-left">
            <button
              className="icon-btn mobile-menu"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              aria-label="Toggle navigation menu"
            >
              <Menu size={18} />
            </button>

            <div className="breadcrumbs">
              <span>Projects</span> <span>/</span> <b>{section}</b>
              {active && (
                <>
                  <span>/</span>
                  <span className="breadcrumb-project-title" title={active.name || active.filename}>
                    {active.name || active.filename}
                  </span>
                  {saveStatus === 'saving' && (
                    <span className="autosave-badge autosave-saving">
                      <Loader2 size={11} className="spin" /> រក្សាទុក...
                    </span>
                  )}
                  {saveStatus === 'saved' && (
                    <span className="autosave-badge autosave-saved">
                      <CheckCircle2 size={11} /> បានរក្សាទុក
                    </span>
                  )}
                  {saveStatus === 'error' && (
                    <span className="autosave-badge autosave-error">
                      <AlertCircle size={11} /> បរាជ័យរក្សាទុក
                    </span>
                  )}
                </>
              )}
            </div>
          </div>

          <div className="top-actions">
            {/* Workflow Mode Switcher */}
            <div className="workflow-mode-tabs" role="tablist" aria-label="Workflow Mode">
              <button
                type="button"
                className={`workflow-mode-tab ${workflowMode === 'beginner' ? 'active' : ''}`}
                onClick={() => handleSetWorkflowMode('beginner')}
                title="Beginner Mode: 1-Click Translate & Dub"
              >
                <Sparkles size={13} />
                <span className="tab-full-label">Beginner Mode (សាមញ្ញ)</span>
                <span className="tab-short-label">Beginner</span>
              </button>
              <button
                type="button"
                className={`workflow-mode-tab ${workflowMode === 'advanced' ? 'active' : ''}`}
                onClick={() => handleSetWorkflowMode('advanced')}
                title="Advanced Studio: Per-speaker voice overrides, timing, studio"
              >
                <Sliders size={13} />
                <span className="tab-full-label">Advanced Studio (កម្រិតខ្ពស់)</span>
                <span className="tab-short-label">Advanced</span>
              </button>
            </div>

            <span className="local-badge">
              <span className="live-dot" /> <span className="local-badge-text">100% Local</span>
            </span>
            <button
              className="icon-btn"
              onClick={() => setDark(!dark)}
              aria-label="Toggle theme"
              title="Toggle theme"
            >
              {dark ? <Sun size={18} /> : <Moon size={18} />}
            </button>
            <button
              className="help-btn"
              onClick={() => setShowHelp(true)}
              aria-label="Open help guide"
            >
              <CircleHelp size={17} />
              <span>Help</span>
            </button>
          </div>
        </header>

        <div className="content">
          <div className="page-heading">
            <div>
              <div className="eyebrow">
                <Sparkles size={14} /> LOCAL AI SPEECH WORKSPACE
              </div>
              <h1>
                Khmer & Multi-language Speech, <em>Reimagined.</em>
              </h1>
              <p>
                បម្លែងសំឡេងក្នុងវីដេអូនិងអូឌីយ៉ូទៅជាអត្ថបទ (Speech-to-Text) និងបង្កើត Subtitle SRT ត្រឹមត្រូវតាមស្ដង់ដារ ដោយមិនពឹងលើ Cloud ឬ Paid API។
              </p>
            </div>
            <motion.button
              whileTap={{ scale: 0.97 }}
              className="primary-btn"
              onClick={handleNewProject}
              disabled={busy}
            >
              <Plus size={18} /> New transcription
            </motion.button>
            <input
              ref={fileRef}
              type="file"
              accept="video/*,audio/*,.mp4,.mkv,.mov,.avi,.webm,.m4v,.mp3,.wav,.m4a,.flac,.ogg,.aac,.opus"
              hidden
              onChange={(e) => {
                handleFileSelect(e.target.files?.[0]);
                e.currentTarget.value = '';
              }}
            />
          </div>

          {/* Production Backend URL Connection Banner if on HTTPS but pointing to localhost */}
          {needsBackendUrl && (
            <motion.div
              initial={{ opacity: 0, y: -6 }}
              animate={{ opacity: 1, y: 0 }}
              style={{
                background: 'linear-gradient(135deg, rgba(214,180,106,0.18), rgba(17,26,46,0.95))',
                border: '1px solid rgba(214,180,106,0.5)',
                borderRadius: 12,
                padding: '14px 18px',
                marginBottom: 20,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: 14,
                flexWrap: 'wrap',
                boxShadow: '0 4px 20px rgba(0,0,0,0.4)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, minWidth: 260, flex: 1 }}>
                <AlertCircle size={22} style={{ color: '#D6B46A', flexShrink: 0 }} />
                <div>
                  <b style={{ color: '#D6B46A', fontSize: 13, display: 'block' }}>
                    ទាមទារភ្ជាប់ Backend Server សម្រាប់ Cloudflare / Phone
                  </b>
                  <p style={{ margin: '4px 0 0', color: 'var(--text-secondary)', fontSize: 11, lineHeight: 1.5 }}>
                    ដើម្បី Upload វីដេអូ និងបកប្រែលើទូរស័ព្ទដៃ សូមបញ្ចូល Render API URL របស់អ្នក (ឧទាហរណ៍៖ <code>https://khmer-ai.onrender.com</code>)។
                  </p>
                </div>
              </div>
              <div style={{ display: 'flex', gap: 8, alignItems: 'center', width: '100%', maxWidth: 460 }}>
                <input
                  type="url"
                  placeholder="https://your-service.onrender.com"
                  value={customApiInput}
                  onChange={(e) => setCustomApiInput(e.target.value)}
                  style={{
                    flex: 1,
                    padding: '9px 12px',
                    borderRadius: 8,
                    border: '1px solid #D6B46A',
                    background: '#0B1020',
                    color: '#fff',
                    fontSize: 12,
                    outline: 'none',
                  }}
                />
                <button
                  type="button"
                  className="primary-btn"
                  style={{ padding: '9px 16px', fontSize: 11, whiteSpace: 'nowrap' }}
                  onClick={() => handleSaveCustomApi(customApiInput)}
                >
                  <Check size={14} /> ភ្ជាប់ (Connect)
                </button>
              </div>
            </motion.div>
          )}

          {/* Animated Notice & Error Alerts */}
          <AnimatePresence>
            {(notice || error || busy) && (
              <motion.div
                initial={{ opacity: 0, y: -8, scale: 0.98 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -8, scale: 0.98 }}
                transition={{ duration: 0.18 }}
                className={error ? 'alert error' : 'alert'}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  {busy ? (
                    <span className="audio-wave-loader">
                      <span className="wave-bar" />
                      <span className="wave-bar" />
                      <span className="wave-bar" />
                      <span className="wave-bar" />
                    </span>
                  ) : (
                    <CheckCircle2 size={16} />
                  )}
                  <span>{error || statusStage || notice}</span>
                </div>
                <button
                  onClick={() => { setError(''); setNotice(''); }}
                  aria-label="Dismiss alert"
                >
                  <X size={15} />
                </button>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Staggered Metrics Bar */}
          <motion.section
            className="stats-grid"
            variants={statsContainerVariants}
            initial="hidden"
            animate="visible"
          >
            <Stat
              icon={<Clapperboard />}
              label="TOTAL PROJECTS"
              value={String(jobs.length).padStart(2, '0')}
              note="In local workspace"
            />
            <Stat
              icon={<Clock3 />}
              label="TOTAL MEDIA TIME"
              value={fmtTime(totalMediaDuration)}
              note="All processed media"
            />
            <Stat
              icon={<Languages />}
              label="SOURCE LANGUAGE"
              value={active?.source_language ? active.source_language.toUpperCase() : selectedLanguage === 'auto' ? 'Auto' : selectedLanguage.toUpperCase()}
              note="Detected or selected"
            />
            <Stat
              icon={<Gauge />}
              label="WHISPER ENGINE"
              value={caps?.faster_whisper ? 'Ready' : 'Offline'}
              note={`Model: ${selectedModel} (int8)`}
              status={!!caps?.faster_whisper}
            />
          </motion.section>

          {/* SECTION TRANSITIONS */}
          <AnimatePresence mode="wait">
            {section === 'Workspace' && (
              <motion.div
                key="workspace-view"
                variants={pageMotionVariants}
                initial="initial"
                animate="animate"
                exit="exit"
              >
                <div className="section-head">
                  <div>
                    <h2>
                      {workflowMode === 'beginner'
                        ? '1-Click Multilingual AI Video Translate & Dub'
                        : 'Speech transcription workspace'}
                    </h2>
                    <p>
                      {workflowMode === 'beginner'
                        ? 'បកប្រែ និងបញ្ចូលសំឡេង Dubbed ស្វ័យប្រវត្តិតាមរយៈ 1-Click ងាយស្រួលបំផុតសម្រាប់អ្នកចាប់ផ្ដើម'
                        : 'ជ្រើសរើសឯកសារអូឌីយ៉ូ ឬវីដេអូ ដើម្បីចាប់ផ្ដើមស្គាល់សំឡេង។'}
                    </p>
                  </div>
                  <div className="section-head-actions" style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                    <div className="workflow-mode-tabs" role="tablist">
                      <button
                        type="button"
                        className={`workflow-mode-tab ${workflowMode === 'beginner' ? 'active' : ''}`}
                        onClick={() => handleSetWorkflowMode('beginner')}
                      >
                        <Sparkles size={13} /> Beginner
                      </button>
                      <button
                        type="button"
                        className={`workflow-mode-tab ${workflowMode === 'advanced' ? 'active' : ''}`}
                        onClick={() => handleSetWorkflowMode('advanced')}
                      >
                        <Sliders size={13} /> Advanced
                      </button>
                    </div>
                    <button className="text-btn" onClick={() => void loadState()}>
                      Refresh <Activity size={15} />
                    </button>
                  </div>
                </div>

                {workflowMode === 'beginner' ? (
                  /* ========================================================
                     BEGINNER MODE (1-Click Unified Dubbing Pipeline)
                     ======================================================== */
                  <div className="beginner-card">
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                        <div style={{ width: 44, height: 44, borderRadius: 12, background: 'rgba(217, 181, 109, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--gold)' }}>
                          <WandSparkles size={24} />
                        </div>
                        <div>
                          <h3 style={{ margin: 0, fontSize: 17, fontWeight: 700 }}>
                            Automatic Translate & Dubbing Pipeline
                          </h3>
                          <p style={{ margin: '3px 0 0', fontSize: 12, color: 'var(--muted)' }}>
                            ដំណើរការបកប្រែ + បែងចែកតួអង្គ + ចាត់ចែងសំឡេង + បញ្ចូលសំឡេង Dubbed ក្នុងជំហានតែមួយ
                          </p>
                        </div>
                      </div>
                      <span className="beginner-step-badge" style={{ padding: '6px 14px', background: 'rgba(217, 181, 109, 0.12)', borderRadius: 20 }}>
                        <CheckCircle2 size={13} /> Fully Automated Pipeline
                      </span>
                    </div>

                    <div className="beginner-steps-grid">
                      {/* STEP 1: VIDEO SELECTION */}
                      <div className="beginner-step-card">
                        <div className="beginner-step-badge">
                          <Video size={14} /> ជំហានទី ១: ជ្រើសរើសវីដេអូ (Select Video)
                        </div>

                        {uploadProgress ? (
                          <MediaUploadProgressCard
                            progress={uploadProgress}
                            filename={selectedFile?.name || active?.filename || 'Media File'}
                            onPause={handlePauseUpload}
                            onResume={handleResumeUpload}
                            onCancel={handleCancelUpload}
                            onRetry={handleRetryUpload}
                          />
                        ) : selectedFile ? (
                          <div className="file-preview" style={{ margin: 0 }}>
                            <div className="file-preview-icon">
                              {selectedFile.type.startsWith('video') ? <FileVideo size={20} /> : <FileAudio size={20} />}
                            </div>
                            <div className="file-preview-info">
                              <b>{selectedFile.name}</b>
                              <small>{fmtFileSize(selectedFile.size)} · រួចរាល់សម្រាប់ Upload</small>
                            </div>
                            <button
                              className="icon-btn-sm"
                              onClick={() => setSelectedFile(null)}
                              title="Remove file"
                            >
                              <X size={14} />
                            </button>
                          </div>
                        ) : active ? (
                          <div className="file-preview" style={{ margin: 0 }}>
                            <div className="file-preview-icon">
                              <FileVideo size={20} />
                            </div>
                            <div className="file-preview-info">
                              <b>{active.filename}</b>
                              <small>គម្រោងសកម្ម · {fmtDurationDetailed(active.duration_seconds)}</small>
                            </div>
                            <button
                              className="secondary-btn"
                              style={{ padding: '4px 8px', fontSize: 11 }}
                              onClick={() => fileRef.current?.click()}
                            >
                              ប្តូរឯកសារ
                            </button>
                          </div>
                        ) : (
                          <motion.button
                            animate={{ scale: drag ? 1.015 : 1 }}
                            className={`dropzone ${drag ? 'dragging' : ''}`}
                            style={{ padding: '24px 16px', margin: 0 }}
                            onClick={() => fileRef.current?.click()}
                            onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
                            onDragLeave={() => setDrag(false)}
                            onDrop={(e) => {
                              e.preventDefault();
                              setDrag(false);
                              handleFileSelect(e.dataTransfer.files?.[0]);
                            }}
                            disabled={busy}
                          >
                            <CloudUpload size={24} style={{ color: 'var(--gold)', margin: '0 auto 8px' }} />
                            <b>ជ្រើសរើស ឬទម្លាក់វីដេអូនៅទីនេះ</b>
                            <span style={{ fontSize: 11 }}>MP4, MKV, MOV, WEBM, MP3 · រយៈពេលរហូតដល់ 2 ម៉ោង (120 នាទី) · Max 4 GB</span>
                          </motion.button>
                        )}
                      </div>

                      {/* STEP 2: LANGUAGES */}
                      <div className="beginner-step-card">
                        <div className="beginner-step-badge">
                          <Languages size={14} /> ជំហានទី ២: ជ្រើសរើសភាសា (Languages)
                        </div>
                        <LanguageSelector
                          sourceLanguage={selectedSourceLang}
                          targetLanguage={selectedTargetLang}
                          sourceLanguages={languagesData?.source_languages}
                          targetLanguages={languagesData?.target_languages}
                          onSourceChange={setSelectedSourceLang}
                          onTargetChange={setSelectedTargetLang}
                          disabled={busy}
                          layout="vertical"
                        />
                      </div>

                      {/* STEP 3: AUTOMATIC SMART FEATURES */}
                      <div className="beginner-step-card">
                        <div className="beginner-step-badge">
                          <ShieldCheck size={14} /> ជំហានទី ៣: ប្រព័ន្ធស្វ័យប្រវត្តិ (Smart Automation)
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 10, background: 'var(--panel)', padding: '10px 12px', borderRadius: 8, border: '1px solid var(--line)' }}>
                            <Users size={16} style={{ color: 'var(--gold)', flexShrink: 0 }} />
                            <div style={{ fontSize: 12 }}>
                              <b style={{ display: 'block', color: 'var(--text)' }}>Smart Multi-Speaker Assignment</b>
                              <span style={{ color: 'var(--muted)', fontSize: 11 }}>កំណត់សំឡេងតួអង្គដាច់ដោយឡែកដោយស្វ័យប្រវត្តិ</span>
                            </div>
                            <Check size={16} style={{ color: 'var(--green)', marginLeft: 'auto' }} />
                          </div>

                          <div style={{ display: 'flex', alignItems: 'center', gap: 10, background: 'var(--panel)', padding: '10px 12px', borderRadius: 8, border: '1px solid var(--line)' }}>
                            <Sparkles size={16} style={{ color: 'var(--gold)', flexShrink: 0 }} />
                            <div style={{ fontSize: 12 }}>
                              <b style={{ display: 'block', color: 'var(--text)' }}>Emotion-Aware Modulation</b>
                              <span style={{ color: 'var(--muted)', fontSize: 11 }}>កែតម្រូវចង្វាក់ កម្ពស់ និងល្បឿនតាមអារម្មណ៍សាច់រឿង</span>
                            </div>
                            <Check size={16} style={{ color: 'var(--green)', marginLeft: 'auto' }} />
                          </div>

                          <div style={{ display: 'flex', alignItems: 'center', gap: 10, background: 'var(--panel)', padding: '10px 12px', borderRadius: 8, border: '1px solid var(--line)' }}>
                            <Volume2 size={16} style={{ color: 'var(--gold)', flexShrink: 0 }} />
                            <div style={{ fontSize: 12 }}>
                              <b style={{ display: 'block', color: 'var(--text)' }}>Verified Audio Stream Output</b>
                              <span style={{ color: 'var(--muted)', fontSize: 11 }}>ធានាថាវីដេអូចុងក្រោយមានសំឡេង Dubbed ច្បាស់លាស់ 100%</span>
                            </div>
                            <Check size={16} style={{ color: 'var(--green)', marginLeft: 'auto' }} />
                          </div>

                          <div style={{ display: 'flex', alignItems: 'center', gap: 10, background: 'var(--panel)', padding: '10px 12px', borderRadius: 8, border: '1px solid var(--line)' }}>
                            <FileCheck2 size={16} style={{ color: 'var(--gold)', flexShrink: 0 }} />
                            <div style={{ fontSize: 12 }}>
                              <b style={{ display: 'block', color: 'var(--text)' }}>Contextual Khmer Proofreading</b>
                              <span style={{ color: 'var(--muted)', fontSize: 11 }}>ត្រួតពិនិត្យអក្ខរាវិរុទ្ធ វេយ្យាករណ៍ និងពាក្យបច្ចេកទេសស្វ័យប្រវត្តិ</span>
                            </div>
                            <Check size={16} style={{ color: 'var(--green)', marginLeft: 'auto' }} />
                          </div>

                          <div style={{ display: 'flex', alignItems: 'center', gap: 10, background: 'var(--panel)', padding: '10px 12px', borderRadius: 8, border: '1px solid var(--line)' }}>
                            <Music size={16} style={{ color: 'var(--gold)', flexShrink: 0 }} />
                            <div style={{ fontSize: 12 }}>
                              <b style={{ display: 'block', color: 'var(--text)' }}>Preserve Original Soundtrack & SFX</b>
                              <span style={{ color: 'var(--muted)', fontSize: 11 }}>រក្សាភ្លេង សំឡេងកាប់ចាក់ប្រយុទ្ធ ការសើច យំ និងបរិយាកាសដើម 100%</span>
                            </div>
                            <Check size={16} style={{ color: 'var(--green)', marginLeft: 'auto' }} />
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* REAL-TIME PROGRESS PANEL IF PROCESSING OR ACTIVE */}
                    {active && (busy || ['validating', 'extracting_audio', 'transcribing', 'generating_subtitles', 'translating', 'queued'].includes(active.status)) && (
                      <div style={{ marginTop: 20 }}>
                        <ProcessingProgressPanel
                          job={active}
                          busy={busy}
                          onCancel={handleCancelJob}
                          onRetry={handleRetryJob}
                        />
                      </div>
                    )}

                    {/* BEGINNER ACTIONS BAR */}
                    <div className="beginner-actions-bar">
                      <div>
                        {active?.has_dubbed_audio && !busy ? (
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--green)', fontSize: 13, fontWeight: 600 }}>
                            <CheckCircle2 size={16} />
                            <span>វីដេអូ Dubbed បានបង្កើតរួចរាល់ហើយ! អ្នកអាចទស្សនា ឬទាញយកភ្លាមៗ។</span>
                          </div>
                        ) : (
                          <div style={{ color: 'var(--muted)', fontSize: 12 }}>
                            ចុចប៊ូតុងខាងស្ដាំ ដើម្បីបកប្រែ និងបញ្ចូលសំឡេង Dubbed ដោយស្វ័យប្រវត្តិតាម 1-Click
                          </div>
                        )}
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
                        {active?.has_dubbed_audio && !busy && (
                          <button
                            type="button"
                            className="secondary-btn"
                            style={{ padding: '12px 20px', fontSize: 14 }}
                            onClick={() => setSection('Preview')}
                          >
                            <Film size={16} />
                            <span>បើកមើល Dual Video Preview</span>
                          </button>
                        )}

                        <motion.button
                          whileTap={{ scale: 0.98 }}
                          type="button"
                          className="beginner-primary-action"
                          disabled={busy || (!selectedFile && !active)}
                          onClick={handleBeginnerTranslateAndDub}
                        >
                          {busy ? (
                            <>
                              <Loader2 size={18} className="spin" />
                              <span>កំពុងដំណើរការបកប្រែ និង Dubbing...</span>
                            </>
                          ) : (
                            <>
                              <WandSparkles size={18} />
                              <span>បកប្រែ និងបង្កើតសំឡេង Dubbed ស្វ័យប្រវត្តិ (Translate & Dub)</span>
                            </>
                          )}
                        </motion.button>
                      </div>
                    </div>
                  </div>
                ) : (
                  <>
                    {/* Cambodian Cultural Showcase & Welcome Hero */}
                    {!active && (
                      <CambodianCulturalBackground
                        variant="hero"
                        mode={appSettings.cultural_background_mode || 'subtle'}
                        dark={dark}
                        onNewProject={() => fileRef.current?.click()}
                        onExploreHistory={() => setSection('Overview')}
                      />
                    )}

                    <div className="work-grid">
                  {/* Upload & Model Selection Panel */}
                  <section className="panel import-panel">
                    <div className="panel-title">
                      <div className="title-icon">
                        <CloudUpload size={19} />
                      </div>
                      <div>
                        <h3>Step 1: Multilingual AI Video Import</h3>
                        <p>ជ្រើសរើសវីដេអូ ឬ URL និងកំណត់ភាសាប្រភព/គោលដៅ</p>
                      </div>
                      <span className="step">01</span>
                    </div>

                    {/* Import Source Switcher: Upload File vs URL */}
                    <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
                      <button
                        type="button"
                        className={`preview-pill-btn ${!showUrlImport ? 'active' : ''}`}
                        onClick={() => setShowUrlImport(false)}
                      >
                        <CloudUpload size={13} /> ឯកសារក្នុងម៉ាស៊ីន (File Upload)
                      </button>
                      <button
                        type="button"
                        className={`preview-pill-btn ${showUrlImport ? 'active' : ''}`}
                        onClick={() => setShowUrlImport(true)}
                      >
                        <Video size={13} /> នាំចូលពី URL (Media Link)
                      </button>
                    </div>

                    {!showUrlImport ? (
                      <>
                        {uploadProgress ? (
                          <MediaUploadProgressCard
                            progress={uploadProgress}
                            filename={selectedFile?.name || active?.filename || 'Media File'}
                            onPause={handlePauseUpload}
                            onResume={handleResumeUpload}
                            onCancel={handleCancelUpload}
                            onRetry={handleRetryUpload}
                          />
                        ) : (
                          <>
                            <motion.button
                              animate={{ scale: drag ? 1.015 : 1 }}
                              className={`dropzone ${drag ? 'dragging' : ''}`}
                              onClick={() => fileRef.current?.click()}
                              onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
                              onDragLeave={() => setDrag(false)}
                              onDrop={(e) => {
                                e.preventDefault();
                                setDrag(false);
                                handleFileSelect(e.dataTransfer.files?.[0]);
                              }}
                              disabled={busy}
                            >
                              <div className="upload-symbol">
                                <CloudUpload size={26} />
                              </div>
                              <b>{busy ? 'កំពុងដំណើរការ...' : 'ទម្លាក់ឯកសារ ឬចុចដើម្បីជ្រើសរើស'}</b>
                              <span>or <u>browse audio/video</u> from your device</span>
                              <small>MP4, MKV, MOV, WEBM, MP3, WAV, M4A, FLAC, OGG · Resumable Chunked Upload · Max 4 GB</small>
                            </motion.button>

                            {/* Selected File Details & Uploaded Job Recovery Card */}
                            <AnimatePresence>
                              {!selectedFile && active && (active.status === 'failed' || active.status === 'uploaded' || !active.transcript?.length) && (
                                <motion.div
                                  initial={{ opacity: 0, y: 6 }}
                                  animate={{ opacity: 1, y: 0 }}
                                  exit={{ opacity: 0, y: -6 }}
                                  className="file-preview"
                                  style={{ borderColor: 'var(--accent)', background: 'rgba(235, 94, 40, 0.06)', marginTop: 12 }}
                                >
                                  <div className="file-preview-icon">
                                    <FileVideo size={20} color="var(--accent)" />
                                  </div>
                                  <div className="file-preview-info">
                                    <b>{active.filename || active.name || active.id}</b>
                                    <small style={{ color: active.status === 'failed' ? '#e03131' : 'var(--muted)' }}>
                                      {active.status === 'failed'
                                        ? '⚠️ ការដំណើរការមិនទាន់ជោគជ័យ (ឯកសារបានរក្សាទុកលើ Server រួចហើយ)'
                                        : '✅ វីដេអូបាន Upload ជោគជ័យ (រួចរាល់សម្រាប់ដំណើរការ)'}
                                    </small>
                                  </div>
                                  <div className="file-preview-actions" style={{ display: 'flex', alignItems: 'center', gap: 8, marginLeft: 'auto' }}>
                                    <button
                                      type="button"
                                      className="primary-btn"
                                      style={{ padding: '6px 14px', fontSize: 12, borderRadius: 6 }}
                                      disabled={busy}
                                      onClick={() => runTranscription(active.id, selectedModel, selectedSourceLang, selectedTargetLang, true, true, false)}
                                    >
                                      <WandSparkles size={14} /> 🔄 សាកល្បងម្ដងទៀត (Retry)
                                    </button>
                                  </div>
                                </motion.div>
                              )}

                              {selectedFile && (
                                <motion.div
                                  initial={{ opacity: 0, y: 6 }}
                                  animate={{ opacity: 1, y: 0 }}
                                  exit={{ opacity: 0, y: -6 }}
                                  className="file-preview"
                                >
                                  <div className="file-preview-icon">
                                    {selectedFile.type.startsWith('video') ? <FileVideo size={20} /> : <FileAudio size={20} />}
                                  </div>
                                  <div className="file-preview-info">
                                    <b>{selectedFile.name}</b>
                                    <small>{fmtFileSize(selectedFile.size)} · {selectedFile.type || 'Media File'}</small>
                                  </div>
                                  <div className="file-preview-actions" style={{ display: 'flex', alignItems: 'center', gap: 8, marginLeft: 'auto' }}>
                                    <button
                                      type="button"
                                      className="primary-btn"
                                      style={{ padding: '6px 14px', fontSize: 12, borderRadius: 6 }}
                                      disabled={busy}
                                      onClick={handleUploadAndTranscribe}
                                    >
                                      <WandSparkles size={14} /> Upload & Process
                                    </button>
                                    <button
                                      className="icon-btn"
                                      onClick={() => setSelectedFile(null)}
                                      title="Remove file"
                                      aria-label="Remove selected file"
                                      disabled={busy}
                                    >
                                      <X size={15} />
                                    </button>
                                  </div>
                                </motion.div>
                              )}
                            </AnimatePresence>
                          </>
                        )}
                      </>
                    ) : (
                      <div style={{ background: 'var(--panel2)', border: '1px solid var(--line)', borderRadius: 10, padding: 14, display: 'flex', flexDirection: 'column', gap: 10 }}>
                        <label style={{ fontSize: 11, fontWeight: 600, color: 'var(--text)', display: 'flex', alignItems: 'center', gap: 6 }}>
                          <Video size={14} style={{ color: 'var(--gold)' }} />
                          <span>Video or Media URL</span>
                        </label>
                        <input
                          type="url"
                          placeholder="https://example.com/video.mp4 ឬ YouTube / Bilibili / Media link"
                          value={importUrl}
                          onChange={(e) => setImportUrl(e.target.value)}
                          disabled={busy}
                          style={{
                            background: 'var(--panel)',
                            border: '1px solid var(--line)',
                            borderRadius: 8,
                            padding: '10px 12px',
                            color: 'var(--text)',
                            fontSize: 12,
                            outline: 'none',
                            width: '100%',
                          }}
                        />
                        <small style={{ color: 'var(--muted)', fontSize: 10, lineHeight: 1.5 }}>
                          គាំទ្រតំណភ្ជាប់ផ្ទាល់ (Direct MP4/WebM) និងវេទិកាដែលអនុញ្ញាតដោយ yt-dlp។ ដំណើរការទាញយកមានសុវត្ថិភាពខ្ពស់ និងមិនប៉ះពាល់ដល់ប្រព័ន្ធ។
                        </small>
                      </div>
                    )}

                    {/* Multilingual Source & Target Language Selector Component */}
                    <LanguageSelector
                      sourceLanguage={selectedSourceLang}
                      targetLanguage={selectedTargetLang}
                      sourceLanguages={languagesData?.source_languages}
                      targetLanguages={languagesData?.target_languages}
                      onSourceChange={setSelectedSourceLang}
                      onTargetChange={setSelectedTargetLang}
                      disabled={busy}
                    />

                    {/* Whisper Model Configuration */}
                    <div className="config-group" style={{ gridTemplateColumns: '1fr', marginTop: 8 }}>
                      <div className="config-field">
                        <label className="config-label">Speech Recognition Engine (Faster-Whisper)</label>
                        <select
                          className="config-select"
                          value={selectedModel}
                          onChange={(e) => setSelectedModel(e.target.value)}
                          disabled={busy}
                        >
                          {models.length > 0 ? (
                            models.map((m) => (
                              <option key={m.id} value={m.id}>
                                {m.name} (~{m.estimated_ram_mb}MB RAM)
                              </option>
                            ))
                          ) : (
                            <>
                              <option value="tiny">Tiny (Recommended · ~390MB RAM)</option>
                              <option value="base">Base (~500MB RAM)</option>
                            </>
                          )}
                        </select>
                      </div>
                    </div>

                    {/* Action Bar */}
                    <div className="action-bar" style={{ marginTop: 14 }}>
                      {!showUrlImport ? (
                        <motion.button
                          whileTap={{ scale: 0.98 }}
                          className="primary-btn"
                          disabled={busy || !selectedFile}
                          onClick={handleUploadAndTranscribe}
                          style={{ width: '100%', justifyContent: 'center' }}
                        >
                          <WandSparkles size={16} /> ចាប់ផ្តើមបកប្រែវីដេអូ (Process & Transcribe)
                        </motion.button>
                      ) : (
                        <motion.button
                          whileTap={{ scale: 0.98 }}
                          className="primary-btn"
                          disabled={busy || !importUrl.trim()}
                          onClick={handleImportUrl}
                          style={{ width: '100%', justifyContent: 'center' }}
                        >
                          <Download size={16} /> ទាញយក & បកប្រែវីដេអូពី URL (Import & Process)
                        </motion.button>
                      )}
                    </div>

                    <div className="hint">
                      <ShieldCheck size={14} /> ការទទួលស្គាល់សំឡេងនិងការបកប្រែដំណើរការដោយសុវត្ថិភាព 100% Free & Open-Source (Zero Ollama)。
                    </div>
                  </section>

                  {/* Pipeline Status Panel */}
                  <section className="panel pipeline-panel">
                    <div className="panel-title">
                      <div className="title-icon gold">
                        <WandSparkles size={19} />
                      </div>
                      <div>
                        <h3>Step 2: Processing Pipeline</h3>
                        <p>លំហូរដំណើរការស្គាល់សំឡេងនិង Subtitles</p>
                      </div>
                      <span className="step">02</span>
                    </div>

                    <div className="pipeline">
                      {[
                        {
                          n: '01',
                          title: 'Media Validation & Audio Extraction',
                          desc: 'FFmpeg/FFprobe validates streams and codecs',
                          ok: !!caps?.ffprobe,
                          tag: caps?.ffprobe ? 'READY' : 'SETUP',
                        },
                        {
                          n: '02',
                          title: 'Local Speech Recognition',
                          desc: `faster-whisper CPU (${selectedModel}, int8)`,
                          ok: !!caps?.faster_whisper,
                          tag: caps?.faster_whisper ? 'READY' : 'SETUP',
                        },
                        {
                          n: '03',
                          title: 'Timestamped Subtitle Generation',
                          desc: 'Accurate SRT & plain text segments',
                          ok: !!(active && active.transcript.length > 0),
                          tag: active && active.transcript.length > 0 ? 'COMPLETED' : 'STANDBY',
                        },
                        {
                          n: '04',
                          title: 'Optional Khmer Translation',
                          desc: 'Translate recognized text with local AI',
                          ok: !!caps?.ollama,
                          tag: caps?.ollama ? 'READY' : 'OPTIONAL',
                        },
                      ].map((x) => (
                        <div className="pipeline-row" key={x.n}>
                          <div className={`pipeline-number ${x.ok ? 'done' : ''}`}>
                            {x.ok ? <CheckCircle2 size={16} /> : x.n}
                          </div>
                          <div className="pipeline-copy">
                            <b>{x.title}</b>
                            <small>{x.desc}</small>
                          </div>
                          <span className={`tag ${x.ok ? 'tag-ready' : ''}`}>{x.tag}</span>
                        </div>
                      ))}
                    </div>

                    <div className="pipeline-foot">
                      <span className="live-dot" /> Concurrency limited to 1 job to conserve RAM
                    </div>
                  </section>
                </div>

                {/* Active Project & Transcript Editor */}
                <div className="section-head recent-head">
                  <div>
                    <h2>{active ? 'Active Project & Transcript Editor' : 'Recent Projects'}</h2>
                    <p>{active ? active.filename : 'បញ្ជីគម្រោងដែលបានស្គាល់សំឡេងថ្មីៗ'}</p>
                  </div>
                  {active && (
                    <button className="text-btn" onClick={handleNewProject}>
                      All projects <ChevronDown size={15} />
                    </button>
                  )}
                </div>

                {/* Real-Time Processing Progress Panel */}
                {active && (
                  <ProcessingProgressPanel
                    job={active}
                    busy={busy}
                    onCancel={handleCancelJob}
                    onRetry={handleRetryJob}
                  />
                )}

                {active ? (
                  <motion.section
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="panel project-detail"
                  >
                    <div className="detail-head">
                      <div className="file-icon">
                        {activeIsVideo ? <FileVideo size={22} /> : <FileAudio size={22} />}
                      </div>
                      <div className="detail-name">
                        <b>{active.filename}</b>
                        <small>
                          ID: {active.id} · {fmtDurationDetailed(active.duration_seconds)} duration · Language: {active.source_language || 'auto'} · Model: {active.model_used || selectedModel}
                        </small>
                      </div>
                      <span className={`badge-pill ${active.status === 'transcribed' ? 'success' : active.status === 'error' || active.status === 'failed' ? 'danger' : 'warning'}`}>
                        {active.status}
                      </span>
                    </div>

                    {/* Action Toolbar */}
                    <div className="detail-actions">
                      {['validating', 'extracting_audio', 'transcribing', 'generating_subtitles', 'translating', 'queued'].includes(active.status) || busy ? (
                        <motion.button
                          whileTap={{ scale: 0.98 }}
                          className="secondary-btn"
                          style={{ color: '#ea8282', borderColor: '#ea828244' }}
                          onClick={() => handleCancelJob(active.id)}
                        >
                          <StopCircle size={15} /> Cancel Processing
                        </motion.button>
                      ) : active.status === 'failed' || active.status === 'cancelled' ? (
                        <motion.button
                          whileTap={{ scale: 0.98 }}
                          className="primary-btn"
                          onClick={() => handleRetryJob(active.id)}
                        >
                          <RotateCcw size={15} /> Retry Processing
                        </motion.button>
                      ) : (
                        <motion.button
                          whileTap={{ scale: 0.98 }}
                          className="secondary-btn"
                          disabled={busy}
                          onClick={() => runTranscription(active.id, selectedModel, selectedLanguage)}
                        >
                          <RefreshCw size={15} /> Re-transcribe
                        </motion.button>
                      )}

                      {isDirty && (
                        <motion.button
                          whileTap={{ scale: 0.98 }}
                          className="primary-btn"
                          disabled={busy}
                          onClick={saveEditedTranscript}
                        >
                          <Save size={15} /> Save Edits
                        </motion.button>
                      )}

                      <motion.button
                        whileTap={{ scale: 0.98 }}
                        className="secondary-btn"
                        disabled={busy || !editedSegments.length}
                        onClick={handleCopyTranscript}
                      >
                        {copied ? <Check size={15} /> : <Copy size={15} />}
                        {copied ? 'បានចម្លង!' : 'Copy Transcript'}
                      </motion.button>

                      <motion.button
                        whileTap={{ scale: 0.98 }}
                        className="primary-btn"
                        style={{
                          background: 'linear-gradient(135deg, #e5c783 0%, #b38a3f 100%)',
                          color: '#080f1d',
                          fontWeight: 700,
                        }}
                        onClick={() => setSection('Preview')}
                        title="Preview video with subtitles before export"
                      >
                        <Film size={15} /> Preview & Export
                      </motion.button>

                      {editedSegments.length > 0 && (
                        <a
                          className="secondary-btn link-btn"
                          href={`${API}/api/jobs/${active.id}/subtitles.srt`}
                          download
                        >
                          <Download size={15} /> Export SRT
                        </a>
                      )}

                      {editedSegments.length > 0 && (
                        <a
                          className="secondary-btn link-btn"
                          href={`${API}/api/jobs/${active.id}/transcript.txt`}
                          download
                        >
                          <FileText size={15} /> Export TXT
                        </a>
                      )}

                      {caps?.ollama && (
                        <motion.button
                          whileTap={{ scale: 0.98 }}
                          className="secondary-btn"
                          disabled={busy || !editedSegments.length}
                          onClick={() => runTranslation(active.id)}
                        >
                          <Languages size={15} /> Translate to Khmer
                        </motion.button>
                      )}

                      <motion.button
                        whileTap={{ scale: 0.98 }}
                        className="secondary-btn"
                        style={{ color: '#ea8282' }}
                        onClick={() => handleDeleteJob(active.id)}
                        title="Delete project"
                        aria-label="Delete project"
                      >
                        <Trash2 size={15} /> Delete
                      </motion.button>
                    </div>

                    {/* Transcript Segments Interactive Editor with AnimatePresence */}
                    <div className="subtitle-list">
                      <div className="subtitle-heading">
                        <b>Transcript Segments ({editedSegments.length})</b>
                        <div className="toolbar-group">
                          <button className="text-btn" onClick={handleAddSegment}>
                            <Plus size={14} /> Add segment
                          </button>
                        </div>
                      </div>

                      {editedSegments.length === 0 ? (
                        active?.status === 'transcribing' || busy ? (
                          <div style={{ textAlign: 'center', padding: '36px 16px', background: 'var(--panel2)', borderRadius: 9, border: '1px solid var(--line)' }}>
                            <div className="audio-wave-anim" style={{ justifyContent: 'center', marginBottom: 14 }}>
                              {[0.4, 0.9, 0.6, 1.0, 0.5, 0.8, 0.3].map((h, i) => (
                                <motion.span
                                  key={i}
                                  animate={{ scaleY: [0.3, h, 0.3] }}
                                  transition={{ duration: 0.9, repeat: Infinity, delay: i * 0.12 }}
                                  style={{
                                    display: 'inline-block',
                                    width: 4,
                                    height: 24,
                                    background: 'var(--gold)',
                                    borderRadius: 2,
                                    margin: '0 2.5px'
                                  }}
                                />
                              ))}
                            </div>
                            <p style={{ margin: '0 0 6px', fontSize: 14, color: 'var(--gold)', fontWeight: 600 }}>
                              កំពុងដំណើរការស្គាល់សំឡេង (AI Transcription in progress)...
                            </p>
                            <p style={{ margin: 0, fontSize: 12, color: 'var(--muted)' }}>
                              Faster-Whisper កំពុងបំលែងសំឡេងជាអត្ថបទតាមពេលវេលាជាក់ស្តែង។ សូមរង់ចាំបន្តិច...
                            </p>
                          </div>
                        ) : (
                          <div style={{ textAlign: 'center', padding: '24px 16px', background: 'var(--panel2)', borderRadius: 9, border: '1px dashed var(--line)' }}>
                            <p style={{ margin: '0 0 8px', fontSize: 13, color: 'var(--text)', fontWeight: 600 }}>
                              មិនទាន់មាន Segment អត្ថបទនៅឡើយទេ
                            </p>
                            <p style={{ margin: '0 0 16px', fontSize: 11, color: 'var(--muted)', maxWidth: 460, marginInline: 'auto', lineHeight: 1.6 }}>
                              ប្រសិនបើឯកសារជាបទចម្រៀង (Song) ឬមានតន្ត្រីរំខាន ប្រព័ន្ធបានបន្ថែមមុខងារបិទ Noise Filter ដោយស្វ័យប្រវត្តិដើម្បីចាប់យកសំឡេងច្រៀង។ សូមចុចប៊ូតុងខាងក្រោមដើម្បី Transcribe ឡើងវិញ។
                            </p>
                            <div style={{ display: 'flex', gap: 10, justifyContent: 'center', flexWrap: 'wrap' }}>
                              <motion.button
                                whileTap={{ scale: 0.98 }}
                                className="primary-btn"
                                disabled={busy}
                                onClick={() => runTranscription(active.id, selectedModel, selectedLanguage)}
                              >
                                <RefreshCw size={15} /> ចុច Re-transcribe ឡើងវិញ
                              </motion.button>
                              <button className="secondary-btn" onClick={handleAddSegment}>
                                <Plus size={15} /> បន្ថែម Segment ដោយដៃ
                              </button>
                            </div>
                          </div>
                        )
                      ) : (
                        <div className="editor-container">
                          <AnimatePresence>
                            {editedSegments.map((seg, idx) => (
                              <motion.div
                                layout
                                initial={{ opacity: 0, y: 8 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, scale: 0.96 }}
                                transition={{ duration: 0.18 }}
                                className={`segment-item ${activeSegmentIndex === idx ? 'active-highlight' : ''}`}
                                key={seg.id || idx}
                              >
                                <div className="segment-meta">
                                  <span className="segment-time-badge">
                                    {fmtTime(seg.start)} → {fmtTime(seg.end)}
                                  </span>
                                  <span style={{ fontSize: 10, color: 'var(--muted)' }}>#{idx + 1}</span>
                                  <button
                                    className="segment-del-btn"
                                    onClick={() => handleRemoveSegment(idx)}
                                    title="Remove segment"
                                    aria-label={`Remove segment ${idx + 1}`}
                                  >
                                    <Trash2 size={14} />
                                  </button>
                                </div>
                                <textarea
                                  className="segment-input"
                                  value={seg.text}
                                  onFocus={() => setActiveSegmentIndex(idx)}
                                  onBlur={() => setActiveSegmentIndex(null)}
                                  onChange={(e) => handleSegmentTextChange(idx, e.target.value)}
                                  placeholder="Recognized speech text..."
                                  rows={2}
                                />
                                {active.translation?.[idx] && (
                                  <div style={{ fontSize: 11, color: 'var(--green)', padding: '2px 4px' }}>
                                    <b>Khmer:</b> {active.translation[idx].text}
                                  </div>
                                )}
                              </motion.div>
                            ))}
                          </AnimatePresence>
                        </div>
                      )}
                    </div>
                  </motion.section>
                ) : jobs.length === 0 ? (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.98 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="empty-state"
                  >
                    <div className="empty-art">
                      <FileVideo size={30} />
                      <AudioLines size={21} />
                    </div>
                    <h3>Your next transcription starts here</h3>
                    <p>ជ្រើសរើសឯកសារអូឌីយ៉ូ ឬវីដេអូដើម្បីចាប់ផ្តើមស្គាល់សំឡេងជាលើកដំបូង។</p>
                    <button className="secondary-btn" onClick={() => fileRef.current?.click()}>
                      <Plus size={16} /> Choose media file
                    </button>
                  </motion.div>
                ) : (
                  <div className="jobs-list">
                    <AnimatePresence>
                      {jobs.map((j) => (
                        <motion.div
                          layout
                          initial={{ opacity: 0, y: 6 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, scale: 0.96 }}
                          key={j.id}
                          className="job-row"
                          style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 12 }}
                          onClick={() => setActive(j)}
                        >
                          <div className="file-icon">
                            {['.mp4', '.mkv', '.mov', '.avi', '.webm'].some((e) => j.filename.endsWith(e)) ? (
                              <FileVideo size={20} />
                            ) : (
                              <FileAudio size={20} />
                            )}
                          </div>
                          <div className="job-copy">
                            <b>{j.filename}</b>
                            <small>
                              {new Date(j.created_at).toLocaleString()} · {fmtDurationDetailed(j.duration_seconds)} · {j.transcript.length} segments
                            </small>
                          </div>
                          <span className={`status ${j.status === 'transcribed' ? 'complete' : j.status === 'error' ? 'bad' : ''}`}>
                            {j.status}
                          </span>
                          <button
                            className="icon-btn"
                            onClick={(e) => {
                              e.stopPropagation();
                              void handleDeleteJob(j.id);
                            }}
                            title="Delete project"
                            aria-label={`Delete project ${j.filename}`}
                          >
                            <Trash2 size={14} />
                          </button>
                          <Play size={16} />
                        </motion.div>
                      ))}
                    </AnimatePresence>
                  </div>
                )}

                    {active && (editedSegments.length > 0 || (active.translation && active.translation.length > 0)) && (
                      <KhmerDubbingStudio
                        job={active}
                        API={API}
                        voices={voices}
                        onRefreshJob={loadState}
                        setNotice={setNotice}
                        setError={setError}
                      />
                    )}
                  </>
                )}
              </motion.div>
            )}



            {/* SUBTITLES TAB */}
            {section === 'Subtitles' && (
              <motion.section
                key="subtitles-view"
                variants={pageMotionVariants}
                initial="initial"
                animate="animate"
                exit="exit"
                className="panel"
                style={{ marginTop: 20 }}
              >
                <div className="panel-title">
                  <div className="title-icon gold">
                    <Subtitles size={20} />
                  </div>
                  <div>
                    <h3>Subtitle & Transcript Studio Pro</h3>
                    <p>ពិនិត្យនិងកែសម្រួល Subtitles, Split, Merge, និងបកប្រែជាភាសាខ្មែរ</p>
                  </div>
                </div>

                {active ? (
                  <SubtitleEditorPro
                    job={active}
                    API={API}
                    editedSegments={editedSegments}
                    translationSegments={translationSegments}
                    speakers={active.speakers || []}
                    targetLanguage={active.target_language || selectedTargetLang}
                    onSegmentsChange={(newSegs) => {
                      setEditedSegments(newSegs);
                      setIsDirty(true);
                    }}
                    onTranslationChange={(newTrans) => {
                      setTranslationSegments(newTrans);
                      setIsDirty(true);
                    }}
                    onSeekToTime={(_t) => {
                      setSection('Preview');
                    }}
                    onRefreshJob={loadState}
                    setNotice={setNotice}
                    setError={setError}
                    isDirty={isDirty}
                    onSaveNow={saveEditedTranscript}
                    onTranslate={() => runTranslation(active.id, selectedSourceLang, selectedTargetLang)}
                  />
                ) : (
                  <div className="empty-state">
                    <Subtitles size={32} style={{ color: 'var(--gold)', marginBottom: 10 }} />
                    <h3>No project selected</h3>
                    <p>សូមបើកគម្រោងមួយនៅក្នុង Workspace ដើម្បីកែសម្រួល Subtitles។</p>
                    <motion.button
                      whileTap={{ scale: 0.98 }}
                      className="primary-btn"
                      onClick={() => setSection('Workspace')}
                    >
                      Go to Workspace
                    </motion.button>
                  </div>
                )}
              </motion.section>
            )}

            {/* CHARACTERS TAB */}
            {section === 'Characters' && (
              <motion.section
                key="characters-view"
                variants={pageMotionVariants}
                initial="initial"
                animate="animate"
                exit="exit"
                className="panel"
                style={{ marginTop: 20 }}
              >
                <div className="panel-title">
                  <div className="title-icon gold">
                    <Users size={20} />
                  </div>
                  <div>
                    <h3>Character Voice Studio</h3>
                    <p>គ្រប់គ្រងតួអង្គដែលបានរកឃើញដោយស្វ័យប្រវត្តិ កែតម្រូវសម្លេងអាយុ/ភេទ និងជ្រើសរើសសំឡេង TTS សម្រាប់ភាសា {active?.target_language || selectedTargetLang}</p>
                  </div>
                </div>

                {active ? (
                  <CharacterVoiceStudio
                    job={active}
                    speakers={active.speakers || []}
                    targetLanguage={active.target_language || selectedTargetLang}
                    API={API}
                    onUpdateSpeakers={handleUpdateSpeakers}
                    onMergeSpeakers={handleMergeSpeakers}
                    onSplitSpeaker={handleSplitSpeaker}
                    onRefreshJob={loadState}
                    setNotice={setNotice}
                    setError={setError}
                  />
                ) : (
                  <div className="empty-state">
                    <Users size={32} style={{ color: 'var(--gold)', marginBottom: 10 }} />
                    <h3>No project selected</h3>
                    <p>សូមបើកគម្រោងមួយនៅក្នុង Workspace ដើម្បីគ្រប់គ្រងតួអង្គ និងកំណត់សំឡេង Voice Studio។</p>
                    <motion.button
                      whileTap={{ scale: 0.98 }}
                      className="primary-btn"
                      onClick={() => setSection('Workspace')}
                    >
                      Go to Workspace
                    </motion.button>
                  </div>
                )}
              </motion.section>
            )}

            {/* OVERVIEW TAB */}
            {section === 'Overview' && (
              <motion.section
                key="overview-view"
                variants={pageMotionVariants}
                initial="initial"
                animate="animate"
                exit="exit"
                className="panel"
                style={{ marginTop: 20 }}
              >
                <div className="panel-title">
                  <div className="title-icon">
                    <LayoutDashboard size={20} />
                  </div>
                  <div>
                    <h3>Project History & Overview</h3>
                    <p>ប្រវត្តិគម្រោងបកប្រែវីដេអូ ស្វែងរក តម្រៀប និងគ្រប់គ្រងឯកសារ</p>
                  </div>
                </div>

                <ProjectHistoryPanel
                  jobs={jobs}
                  active={active}
                  onSelectJob={(j) => {
                    setActive(j);
                    setSection('Workspace');
                  }}
                  onRenameJob={handleRenameProject}
                  onDeleteJob={handleDeleteJob}
                  onOpenPreview={(j) => {
                    setActive(j);
                    setSection('Preview');
                  }}
                />
              </motion.section>
            )}

            {/* PREVIEW TAB */}
            {section === 'Preview' && (
              <motion.section
                key="preview-view"
                variants={pageMotionVariants}
                initial="initial"
                animate="animate"
                exit="exit"
              >
                <DualVideoPreviewStudio
                  active={active}
                  API={API}
                  onBackToEditor={() => setSection('Workspace')}
                  onRefreshJob={async () => {
                    await loadState();
                  }}
                  busy={busy}
                  setNotice={setNotice}
                  setError={setError}
                />
              </motion.section>
            )}

            {/* EXPORT TAB */}
            {section === 'Export' && (
              <motion.section
                key="export-view"
                variants={pageMotionVariants}
                initial="initial"
                animate="animate"
                exit="exit"
                className="panel"
                style={{ marginTop: 20 }}
              >
                <div className="panel-title">
                  <div className="title-icon gold">
                    <FolderOpen size={20} />
                  </div>
                  <div>
                    <h3>Subtitle & Video Exports</h3>
                    <p>ទាញយកឯកសារ SRT, VTT, TXT និងវីដេអូ MP4 សម្រាប់គម្រោងទាំងអស់</p>
                  </div>
                </div>

                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Project</th>
                        <th>Languages</th>
                        <th>Target Subtitles</th>
                        <th>Source Subtitles</th>
                        <th>Dubbed Speech</th>
                        <th>Video Render</th>
                      </tr>
                    </thead>
                    <tbody>
                      {jobs.filter((j) => j.transcript.length > 0).length === 0 ? (
                        <tr>
                          <td colSpan={6} style={{ textAlign: 'center', color: 'var(--muted)' }}>
                            មិនទាន់មានគម្រោងណាដែលមានអត្ថបទរួចរាល់សម្រាប់ Export នៅឡើយទេ។
                          </td>
                        </tr>
                      ) : (
                        jobs
                          .filter((j) => j.transcript.length > 0)
                          .map((j) => (
                            <tr key={j.id}>
                              <td>
                                <b>{j.filename}</b>
                                <div style={{ fontSize: 10, color: 'var(--muted)' }}>{j.transcript.length} segments</div>
                              </td>
                              <td>
                                <span className="lang-badge ready">
                                  {j.source_language || 'auto'} → {j.target_language || 'km'}
                                </span>
                              </td>
                              <td>
                                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                                  <a className="text-btn" href={`${API}/api/jobs/${j.id}/subtitles.srt?lang=target`} download>
                                    <Download size={13} /> .SRT
                                  </a>
                                  <a className="text-btn" href={`${API}/api/jobs/${j.id}/subtitles.vtt?lang=target`} download>
                                    <Download size={13} /> .VTT
                                  </a>
                                  <a className="text-btn" href={`${API}/api/jobs/${j.id}/transcript.txt?lang=target`} download>
                                    <Download size={13} /> .TXT
                                  </a>
                                </div>
                              </td>
                              <td>
                                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                                  <a className="text-btn" style={{ color: 'var(--muted)' }} href={`${API}/api/jobs/${j.id}/subtitles.srt?lang=source`} download>
                                    <Download size={13} /> .SRT
                                  </a>
                                  <a className="text-btn" style={{ color: 'var(--muted)' }} href={`${API}/api/jobs/${j.id}/subtitles.vtt?lang=source`} download>
                                    <Download size={13} /> .VTT
                                  </a>
                                </div>
                              </td>
                              <td>
                                {j.has_dubbed_audio ? (
                                  <a
                                    className="text-btn"
                                    style={{ color: 'var(--gold)', fontWeight: 600 }}
                                    href={`${API}/api/jobs/${j.id}/dubbed-audio?download=true`}
                                    download
                                  >
                                    <AudioLines size={14} /> Download .MP3
                                  </a>
                                ) : (
                                  <span style={{ fontSize: 11, color: 'var(--muted)' }}>—</span>
                                )}
                              </td>
                              <td>
                                {j.has_rendered_video ? (
                                  <a
                                    className="text-btn"
                                    style={{ color: 'var(--green)', fontWeight: 600 }}
                                    href={`${API}/api/jobs/${j.id}/rendered-video?download=true`}
                                    download
                                  >
                                    <Download size={14} /> Download .MP4
                                  </a>
                                ) : (
                                  <button
                                    className="text-btn"
                                    style={{ color: 'var(--gold)' }}
                                    onClick={() => {
                                      setActive(j);
                                      setSection('Preview');
                                    }}
                                  >
                                    <Film size={14} /> Preview / Render
                                  </button>
                                )}
                              </td>
                            </tr>
                          ))
                      )}
                    </tbody>
                  </table>
                </div>
              </motion.section>
            )}

            {/* KHMER PROOFREADING TAB */}
            {section === 'Proofreading' && (
              <motion.section
                key="proofread-view"
                variants={pageMotionVariants}
                initial="initial"
                animate="animate"
                exit="exit"
                style={{ marginTop: 20 }}
              >
                <KhmerProofreadingStudio
                  job={active}
                  API={API}
                  onRefreshJob={async () => {
                    await loadState();
                  }}
                  setNotice={setNotice}
                  setError={setError}
                />
              </motion.section>
            )}

            {/* PRONUNCIATION DICTIONARY TAB */}
            {section === 'Dictionary' && (
              <motion.section
                key="dictionary-view"
                variants={pageMotionVariants}
                initial="initial"
                animate="animate"
                exit="exit"
                style={{ marginTop: 20 }}
              >
                <PronunciationDictionaryStudio
                  API={API}
                  setNotice={setNotice}
                  setError={setError}
                />
              </motion.section>
            )}

            {/* SETTINGS TAB */}
            {section === 'Settings' && (
              <motion.section
                key="settings-view"
                variants={pageMotionVariants}
                initial="initial"
                animate="animate"
                exit="exit"
                className="panel"
                style={{ marginTop: 20 }}
              >
                <SmartSettingsPanel
                  settings={appSettings}
                  onSaveSettings={handleSaveSettings}
                  caps={caps}
                  API={API}
                  setNotice={setNotice}
                  setError={setError}
                  onOpenOnboarding={() => setShowOnboarding(true)}
                />
              </motion.section>
            )}

          </AnimatePresence>

          {/* Semantic Footer with Visible, Elegant Copyright Notice */}
          <footer className="app-footer">
            <div className="footer-left">
              <span className="footer-brand">
                <img src="/logo.png" alt="Logo" className="footer-logo" />
                KHMER TRANSLATOR <i>•</i> LOCAL AI SPEECH WORKSPACE
              </span>
              <span className="footer-sub">
                Free & Open-Source Speech Recognition · Low-Resource Ubuntu Architecture
              </span>
            </div>
            <div className="footer-copyright" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <KhmerLotusMotif size={14} />
              <span>{COPYRIGHT_TEXT}</span>
            </div>
          </footer>
        </div>
      </main>

      {/* Animated Help & About Modal */}
      <AnimatePresence>
        {showHelp && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="modal-overlay"
            style={{
              position: 'fixed',
              inset: 0,
              background: 'rgba(5, 4, 10, 0.82)',
              backdropFilter: 'blur(8px)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 9998,
              padding: 16,
            }}
            onClick={() => setShowHelp(false)}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 10 }}
              transition={{ duration: 0.2, ease: [0.25, 0.1, 0.25, 1] }}
              className="modal-box"
              style={{
                maxWidth: 960,
                width: '95vw',
                maxHeight: '90vh',
                overflowY: 'auto',
                background: 'var(--panel)',
                border: '1px solid var(--gold)',
                borderRadius: 14,
                padding: '20px 24px',
                boxShadow: '0 25px 60px rgba(0,0,0,0.6)',
              }}
              onClick={(e) => e.stopPropagation()}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  marginBottom: 10,
                  borderBottom: '1px solid var(--line)',
                  paddingBottom: 10,
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <img src="/logo.png" alt="Emblem" style={{ width: 28, height: 28, objectFit: 'contain' }} />
                  <div>
                    <h3 style={{ margin: 0, fontSize: 16 }}>
                      សៀវភៅណែនាំ & មជ្ឈមណ្ឌលជំនួយ (Help & Support Center)
                    </h3>
                    <small style={{ color: 'var(--gold)' }}>Khmer Translator 2.0 · Production Edition</small>
                  </div>
                </div>
                <button
                  className="icon-btn"
                  onClick={() => setShowHelp(false)}
                  aria-label="Close guide modal"
                >
                  <X size={18} />
                </button>
              </div>

              <HelpCenterStudio
                API={API}
                onOpenOnboarding={() => {
                  setShowHelp(false);
                  setShowOnboarding(true);
                }}
                setNotice={setNotice}
                setError={setError}
              />
            </motion.div>
          </motion.div>
        )}

        <InteractiveOnboardingWizard
          isOpen={showOnboarding}
          onClose={() => setShowOnboarding(false)}
          onNavigateToWorkspace={() => setSection('Workspace')}
        />

        <FloatingKhmerAIAgent API_BASE={API} />
      </AnimatePresence>
    </div>
  );
}

function Stat({
  icon,
  label,
  value,
  note,
  status,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  note: string;
  status?: boolean;
}) {
  const statCardVariants = {
    hidden: { opacity: 0, y: 10 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.28, ease: 'easeOut' } },
  };

  return (
    <motion.div
      variants={statCardVariants}
      className="stat-card"
    >
      <div className="stat-top">
        <span>{label}</span>
        <div className="stat-icon">{icon}</div>
      </div>
      <div className="stat-value">
        {value}
        {status !== undefined && <span className={`status-light ${status ? 'on' : ''}`} />}
      </div>
      <div className="stat-note">{note}</div>
    </motion.div>
  );
}
