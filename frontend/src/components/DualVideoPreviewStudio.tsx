import React, { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Play,
  Pause,
  RotateCcw,
  Volume2,
  VolumeX,
  Maximize,
  Minimize,
  Settings,
  Film,
  Download,
  ArrowLeft,
  Subtitles,
  Columns,
  Eye,
  EyeOff,
  Sliders,
  Check,
  Loader2,
  RefreshCw,
  Sparkles,
  FileText,
  Clock,
  Layers,
  Split,
  ChevronDown,
  Volume1,
  ShieldCheck,
} from 'lucide-react';
import { Job, TranscriptSegment, fmtTime } from '../types';

interface DualVideoPreviewStudioProps {
  active: Job | null;
  API: string;
  onBackToEditor: () => void;
  onRefreshJob: () => Promise<void>;
  busy: boolean;
  setNotice: (msg: string) => void;
  setError: (msg: string) => void;
}

type PreviewLayoutMode = 'side_by_side' | 'original_only' | 'translated_only' | 'split_ab';
type AudioMode = 'original' | 'dubbed' | 'both';

export const DualVideoPreviewStudio: React.FC<DualVideoPreviewStudioProps> = ({
  active,
  API,
  onBackToEditor,
  onRefreshJob,
  busy,
  setNotice,
  setError,
}) => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const origVideoRef = useRef<HTMLVideoElement | null>(null);
  const transVideoRef = useRef<HTMLVideoElement | null>(null);
  const dubbedAudioRef = useRef<HTMLAudioElement | null>(null);

  // Sync state
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [playbackRate, setPlaybackRate] = useState(1);
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Layout mode
  const [layoutMode, setLayoutMode] = useState<PreviewLayoutMode>('side_by_side');
  const [abSplitPercent, setAbSplitPercent] = useState(50); // For A/B slider

  // Audio configuration
  const [audioMode, setAudioMode] = useState<AudioMode>('both');
  const [origVolume, setOrigVolume] = useState(1.0);
  const [transVolume, setTransVolume] = useState(1.0);
  const [isOrigMuted, setIsOrigMuted] = useState(false);
  const [isTransMuted, setIsTransMuted] = useState(false);
  const [preserveSoundtrack, setPreserveSoundtrack] = useState(true);
  const [soundtrackVolume, setSoundtrackVolume] = useState(0.85);
  const [dialogueVolume, setDialogueVolume] = useState(1.0);
  const [preserveNonverbal, setPreserveNonverbal] = useState(true);

  // Subtitle settings
  const [showOrigSubtitles, setShowOrigSubtitles] = useState(true);
  const [showTransSubtitles, setShowTransSubtitles] = useState(true);
  const [fontSize, setFontSize] = useState<'small' | 'medium' | 'large'>('medium');
  const [subtitlePosition, setSubtitlePosition] = useState<'bottom' | 'center' | 'top'>('bottom');

  // Drawer / modals
  const [showSettingsDrawer, setShowSettingsDrawer] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [showDownloadDropdown, setShowDownloadDropdown] = useState(false);

  // Error tracking
  const [origVideoError, setOrigVideoError] = useState<string | null>(null);
  const [transVideoError, setTransVideoError] = useState<string | null>(null);

  // Determine media URLs
  const originalMediaUrl = active ? `${API}/api/jobs/${active.id}/media` : '';
  const renderedVideoUrl = active?.has_rendered_video ? `${API}/api/jobs/${active.id}/rendered-video` : '';
  const dubbedAudioUrl = active?.has_dubbed_audio ? `${API}/api/jobs/${active.id}/dubbed-audio` : '';

  // Has rendered video versus live overlay
  const hasRendered = Boolean(active?.has_rendered_video);
  const hasDubbedAudio = Boolean(active?.has_dubbed_audio);

  // In live preview mode for translated panel, we use original media with live target overlays
  const translatedPanelMediaUrl = hasRendered ? renderedVideoUrl : originalMediaUrl;

  // Transcript lists
  const transcriptList: TranscriptSegment[] = active?.transcript || [];
  const translationList: TranscriptSegment[] = active?.translation || [];

  // Active segments for timestamp
  const activeOrigSeg = transcriptList.find((s) => currentTime >= s.start && currentTime <= s.end);
  const activeTransSeg = translationList.find((s) => currentTime >= s.start && currentTime <= s.end);

  // Synchronized Play/Pause
  const togglePlay = useCallback(() => {
    const nextPlay = !isPlaying;
    setIsPlaying(nextPlay);

    if (nextPlay) {
      if (origVideoRef.current && origVideoRef.current.paused) {
        origVideoRef.current.play().catch(() => {});
      }
      if (transVideoRef.current && transVideoRef.current.paused) {
        transVideoRef.current.play().catch(() => {});
      }
      if (!hasRendered && hasDubbedAudio && dubbedAudioRef.current && dubbedAudioRef.current.paused) {
        dubbedAudioRef.current.play().catch(() => {});
      }
    } else {
      if (origVideoRef.current && !origVideoRef.current.paused) {
        origVideoRef.current.pause();
      }
      if (transVideoRef.current && !transVideoRef.current.paused) {
        transVideoRef.current.pause();
      }
      if (dubbedAudioRef.current && !dubbedAudioRef.current.paused) {
        dubbedAudioRef.current.pause();
      }
    }
  }, [isPlaying, hasRendered, hasDubbedAudio]);

  // Handle master seek
  const handleSeek = (targetTime: number) => {
    setCurrentTime(targetTime);
    if (origVideoRef.current) {
      origVideoRef.current.currentTime = targetTime;
    }
    if (transVideoRef.current) {
      transVideoRef.current.currentTime = targetTime;
    }
    if (dubbedAudioRef.current) {
      dubbedAudioRef.current.currentTime = targetTime;
    }
  };

  // Restart both
  const handleRestart = () => {
    handleSeek(0);
    if (!isPlaying) {
      togglePlay();
    }
  };

  // Sync timeupdate from primary video
  const handlePrimaryTimeUpdate = (e: React.SyntheticEvent<HTMLVideoElement>) => {
    const time = e.currentTarget.currentTime;
    setCurrentTime(time);

    // Sync secondary player if drift > 0.2s
    if (transVideoRef.current && Math.abs(transVideoRef.current.currentTime - time) > 0.25) {
      transVideoRef.current.currentTime = time;
    }
    if (dubbedAudioRef.current && Math.abs(dubbedAudioRef.current.currentTime - time) > 0.25) {
      dubbedAudioRef.current.currentTime = time;
    }
  };

  // Sync secondary timeupdate if user directly interacted with translated video
  const handleSecondaryTimeUpdate = (e: React.SyntheticEvent<HTMLVideoElement>) => {
    const time = e.currentTarget.currentTime;
    if (layoutMode === 'translated_only') {
      setCurrentTime(time);
      if (dubbedAudioRef.current && Math.abs(dubbedAudioRef.current.currentTime - time) > 0.25) {
        dubbedAudioRef.current.currentTime = time;
      }
      if (origVideoRef.current && Math.abs(origVideoRef.current.currentTime - time) > 0.25) {
        origVideoRef.current.currentTime = time;
      }
    }
  };

  // Update audio volumes based on audio mode and active layout
  useEffect(() => {
    if (origVideoRef.current) {
      origVideoRef.current.muted = isOrigMuted || audioMode === 'dubbed';
      origVideoRef.current.volume = isOrigMuted || audioMode === 'dubbed' ? 0 : origVolume;
    }
    if (transVideoRef.current) {
      // If translated video is rendered MP4, it has dubbed audio embedded
      if (hasRendered) {
        transVideoRef.current.muted = isTransMuted || audioMode === 'original';
        transVideoRef.current.volume = isTransMuted || audioMode === 'original' ? 0 : transVolume;
      } else if (layoutMode === 'translated_only') {
        // In translated_only mode, Panel 1 (original video) is unmounted!
        if (hasDubbedAudio) {
          // Dubbed voice is output via dubbedAudioRef; keep transVideo as background audio if soundtrack preserved
          transVideoRef.current.muted = !preserveSoundtrack || isTransMuted || audioMode === 'dubbed';
          transVideoRef.current.volume = isTransMuted || audioMode === 'dubbed' ? 0 : soundtrackVolume;
        } else {
          // No separate dubbed audio: transVideo MUST be unmuted so user hears audio with translated subtitles
          transVideoRef.current.muted = isTransMuted;
          transVideoRef.current.volume = isTransMuted ? 0 : transVolume;
        }
      } else {
        // In side-by-side or split mode, origVideo is active and plays soundtrack to avoid echoing
        transVideoRef.current.muted = true;
      }
    }
    if (dubbedAudioRef.current) {
      dubbedAudioRef.current.muted = isTransMuted || audioMode === 'original';
      dubbedAudioRef.current.volume = isTransMuted || audioMode === 'original' ? 0 : dialogueVolume;
    }
  }, [
    audioMode,
    origVolume,
    transVolume,
    soundtrackVolume,
    dialogueVolume,
    preserveSoundtrack,
    isOrigMuted,
    isTransMuted,
    hasRendered,
    hasDubbedAudio,
    layoutMode,
  ]);

  // Update playback rate
  const handleSpeedChange = (rate: number) => {
    setPlaybackRate(rate);
    if (origVideoRef.current) origVideoRef.current.playbackRate = rate;
    if (transVideoRef.current) transVideoRef.current.playbackRate = rate;
    if (dubbedAudioRef.current) dubbedAudioRef.current.playbackRate = rate;
  };

  // Fullscreen toggle
  const toggleFullscreen = () => {
    if (!containerRef.current) return;
    if (!document.fullscreenElement) {
      containerRef.current.requestFullscreen().then(() => setIsFullscreen(true)).catch(() => {});
    } else {
      document.exitFullscreen().then(() => setIsFullscreen(false)).catch(() => {});
    }
  };

  // Export / Render Final Video (Hardsub)
  const handleExportVideo = async () => {
    if (!active) return;
    setIsExporting(true);
    try {
      const res = await fetch(`${API}/api/jobs/${active.id}/export-video`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          subtitle_source: active.translation?.length ? 'translation' : 'transcript',
          font_size: fontSize === 'small' ? 18 : fontSize === 'large' ? 26 : 22,
          burn_subtitles: true,
          include_dubbed_audio: audioMode !== 'original',
          audio_mode: audioMode === 'original' ? 'original' : (preserveSoundtrack ? 'mixed' : 'dubbed'),
          preserve_soundtrack: preserveSoundtrack,
          original_volume: soundtrackVolume,
          voice_volume: dialogueVolume,
          preserve_nonverbal: preserveNonverbal,
          ducking_intensity: 0.35,
        }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Video rendering failed');
      }

      await onRefreshJob();
      setNotice('វីដេអូ MP4 ត្រូវបាន Render និងដុតបញ្ចូល Subtitles ដោយជោគជ័យ! Dual Preview ឥឡូវនេះបង្ហាញ Rendered Output ពិតប្រាកដ។');
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
          <p>សូមជ្រើសរើស ឬ Upload វីដេអូមួយនៅក្នុង Workspace ដើម្បីចាប់ផ្តើម Dual Video Preview។</p>
          <button className="primary-btn" onClick={onBackToEditor}>
            <ArrowLeft size={16} /> Go to Workspace
          </button>
        </div>
      </div>
    );
  }

  // Format timestamp helper
  const formatTimecode = (sec: number) => {
    const s = Math.max(0, sec);
    const m = Math.floor(s / 60);
    const remS = Math.floor(s % 60);
    const ms = Math.floor((s % 1) * 1000);
    return `${String(m).padStart(2, '0')}:${String(remS).padStart(2, '0')}.${String(ms).padStart(3, '0')}`;
  };

  return (
    <div className="preview-studio-panel" ref={containerRef} style={{ maxWidth: '100%' }}>
      {/* Top Header Bar */}
      <div className="preview-top-bar" style={{ gap: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
          <button className="secondary-btn" onClick={onBackToEditor} title="Back to Editor">
            <ArrowLeft size={15} /> Back to Editor
          </button>

          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
              <b style={{ fontSize: 16, color: 'var(--text)' }}>{active.filename}</b>
              {hasRendered ? (
                <span className="badge-pill success" style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                  <Check size={12} /> Rendered MP4 Ready
                </span>
              ) : (
                <span className="badge-pill warning" style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                  <Sparkles size={12} /> Live Sync Preview (Awaiting Final Render)
                </span>
              )}
            </div>
            <div style={{ color: 'var(--muted)', fontSize: 12, marginTop: 2 }}>
              <span>Time: <b>{formatTimecode(currentTime)}</b> / {fmtTime(duration || active.duration_seconds || 0)}</span>
              <span style={{ margin: '0 8px' }}>•</span>
              <span>{active.source_language || 'Source'} → <b>{active.target_language.toUpperCase()}</b></span>
            </div>
          </div>
        </div>

        {/* Layout Switcher Buttons */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
          <div className="preview-mode-tabs" title="Switch Dual Preview Layout">
            <button
              className={`preview-mode-btn ${layoutMode === 'side_by_side' ? 'active' : ''}`}
              onClick={() => setLayoutMode('side_by_side')}
              title="Side-by-Side Dual Display"
            >
              <Columns size={14} /> Side-by-Side
            </button>
            <button
              className={`preview-mode-btn ${layoutMode === 'split_ab' ? 'active' : ''}`}
              onClick={() => setLayoutMode('split_ab')}
              title="A/B Split Screen Comparison"
            >
              <Split size={14} /> A/B Split
            </button>
            <button
              className={`preview-mode-btn ${layoutMode === 'original_only' ? 'active' : ''}`}
              onClick={() => setLayoutMode('original_only')}
              title="Original Video Only"
            >
              Original Only
            </button>
            <button
              className={`preview-mode-btn ${layoutMode === 'translated_only' ? 'active' : ''}`}
              onClick={() => setLayoutMode('translated_only')}
              title="Translated Video Only"
            >
              Translated Only
            </button>
          </div>

          {/* Quick Refresh */}
          <button
            className="player-icon-btn"
            onClick={async () => {
              await onRefreshJob();
              setNotice('បាន Refresh ស្ថានភាព Preview ដោយជោគជ័យ!');
            }}
            title="Refresh Preview Data"
          >
            <RefreshCw size={15} />
          </button>

          {/* Subtitle Settings Drawer Toggle */}
          <button
            className={`player-icon-btn ${showSettingsDrawer ? 'active' : ''}`}
            onClick={() => setShowSettingsDrawer(!showSettingsDrawer)}
            title="Preview & Subtitle Settings"
          >
            <Settings size={15} />
          </button>
        </div>
      </div>

      {/* Synchronized Dual Video Workspace */}
      <div
        className="dual-video-workspace"
        style={{
          display: 'grid',
          gridTemplateColumns:
            layoutMode === 'side_by_side'
              ? 'repeat(auto-fit, minmax(min(100%, 360px), 1fr))'
              : '1fr',
          gap: 16,
          marginBottom: 16,
          position: 'relative',
        }}
      >
        {/* ================= PANEL 1: ORIGINAL VIDEO ================= */}
        {(layoutMode === 'side_by_side' || layoutMode === 'original_only' || layoutMode === 'split_ab') && (
          <div className="dual-player-card">
            {/* Panel Title Bar */}
            <div className="dual-player-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span
                  style={{
                    fontSize: 11,
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em',
                    padding: '3px 8px',
                    borderRadius: 5,
                    background: 'rgba(59, 130, 246, 0.2)',
                    color: '#60a5fa',
                    border: '1px solid rgba(59, 130, 246, 0.3)',
                  }}
                >
                  Original Video
                </span>
                <span style={{ fontSize: 12, color: 'var(--muted)' }}>
                  Lang: {active.source_language || 'Auto'}
                </span>
              </div>

              {/* Subtitle Toggle */}
              <button
                type="button"
                className={`player-icon-btn ${showOrigSubtitles ? 'active' : ''}`}
                style={{ width: 28, height: 28 }}
                onClick={() => setShowOrigSubtitles(!showOrigSubtitles)}
                title="Toggle Original Subtitles"
              >
                {showOrigSubtitles ? <Subtitles size={13} /> : <EyeOff size={13} />}
              </button>
            </div>

            {/* Screen Container */}
            <div
              className="video-screen"
              style={{
                position: 'relative',
                aspectRatio: '16/9',
                background: '#000',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer',
              }}
              onClick={togglePlay}
            >
              <video
                ref={origVideoRef}
                src={originalMediaUrl}
                className="video-element"
                playsInline
                onLoadedMetadata={(e) => {
                  setDuration(e.currentTarget.duration);
                  setOrigVideoError(null);
                }}
                onTimeUpdate={handlePrimaryTimeUpdate}
                onError={() => setOrigVideoError('Failed to load original media file.')}
              />

              {/* Subtitle Overlay */}
              {showOrigSubtitles && activeOrigSeg && (
                <div className={`subtitle-overlay pos-${subtitlePosition}`}>
                  <div className={`subtitle-bubble size-${fontSize}`}>
                    <span className="subtitle-text" style={{ color: '#f1f5f9' }}>
                      {activeOrigSeg.text}
                    </span>
                    {activeOrigSeg.speaker_id && (
                      <div style={{ fontSize: 10, color: '#93c5fd', marginTop: 4 }}>
                        {activeOrigSeg.speaker_id}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Error overlay if any */}
              {origVideoError && (
                <div style={{ position: 'absolute', inset: 0, background: 'rgba(0,0,0,0.85)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#f87171', padding: 20, textAlign: 'center', fontSize: 13 }}>
                  {origVideoError}
                </div>
              )}
            </div>

            {/* Panel Quick Status */}
            <div className="dual-player-footer">
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Clock size={12} />
                <span>Timestamp: <b>{formatTimecode(currentTime)}</b></span>
              </div>
              <div>{transcriptList.length} original lines</div>
            </div>
          </div>
        )}

        {/* ================= PANEL 2: TRANSLATED VIDEO ================= */}
        {(layoutMode === 'side_by_side' || layoutMode === 'translated_only' || layoutMode === 'split_ab') && (
          <div className={`dual-player-card ${hasRendered ? 'rendered' : ''}`}>
            {/* Panel Title Bar */}
            <div className="dual-player-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span
                  style={{
                    fontSize: 11,
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em',
                    padding: '3px 8px',
                    borderRadius: 5,
                    background: hasRendered
                      ? 'rgba(34, 197, 94, 0.2)'
                      : 'rgba(217, 181, 109, 0.2)',
                    color: hasRendered ? '#4ade80' : 'var(--gold)',
                    border: hasRendered
                      ? '1px solid rgba(34, 197, 94, 0.3)'
                      : '1px solid rgba(217, 181, 109, 0.3)',
                  }}
                >
                  {hasRendered ? 'Translated Video (Rendered MP4)' : 'Translated Video (Live Overlay Preview)'}
                </span>
                <span style={{ fontSize: 12, color: 'var(--muted)' }}>
                  Lang: <b>{active.target_language.toUpperCase()}</b>
                </span>
              </div>

              {/* Subtitle Toggle */}
              {!hasRendered && (
                <button
                  type="button"
                  className={`player-icon-btn ${showTransSubtitles ? 'active' : ''}`}
                  style={{ width: 28, height: 28 }}
                  onClick={() => setShowTransSubtitles(!showTransSubtitles)}
                  title="Toggle Translated Subtitles"
                >
                  {showTransSubtitles ? <Subtitles size={13} /> : <EyeOff size={13} />}
                </button>
              )}
            </div>

            {/* Screen Container */}
            <div
              className="video-screen"
              style={{
                position: 'relative',
                aspectRatio: '16/9',
                background: '#000',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer',
              }}
              onClick={togglePlay}
            >
              <video
                ref={transVideoRef}
                src={translatedPanelMediaUrl}
                className="video-element"
                playsInline
                onTimeUpdate={handleSecondaryTimeUpdate}
                onError={() => setTransVideoError('Rendered video file not ready or missing.')}
              />

              {/* Live Subtitle Overlay (Only active when NOT hardsub rendered) */}
              {!hasRendered && showTransSubtitles && (activeTransSeg || activeOrigSeg) && (
                <div className={`subtitle-overlay pos-${subtitlePosition}`}>
                  <div className={`subtitle-bubble size-${fontSize}`} style={{ border: '1px solid rgba(217, 181, 109, 0.6)' }}>
                    <span className="subtitle-text" style={{ color: '#fed7aa', fontWeight: 600 }}>
                      {activeTransSeg ? activeTransSeg.text : activeOrigSeg?.text}
                    </span>
                    {(activeTransSeg?.speaker_id || activeTransSeg?.emotion) && (
                      <div style={{ display: 'flex', gap: 6, justifyContent: 'center', fontSize: 10, marginTop: 4 }}>
                        {activeTransSeg.speaker_id && (
                          <span style={{ color: 'var(--gold)' }}>{activeTransSeg.speaker_id}</span>
                        )}
                        {activeTransSeg.emotion && (
                          <span style={{ color: '#38bdf8', fontStyle: 'italic' }}>
                            [{activeTransSeg.emotion}]
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Hidden Audio Element for Live Dubbed Audio (if live preview mode) */}
              {!hasRendered && hasDubbedAudio && (
                <audio ref={dubbedAudioRef} src={dubbedAudioUrl} preload="auto" />
              )}

              {/* Error overlay if any */}
              {transVideoError && (
                <div style={{ position: 'absolute', inset: 0, background: 'rgba(0,0,0,0.85)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#f87171', padding: 20, textAlign: 'center', fontSize: 13 }}>
                  {transVideoError}
                </div>
              )}
            </div>

            {/* Panel Quick Status */}
            <div className="dual-player-footer">
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Clock size={12} />
                <span>Timestamp: <b>{formatTimecode(currentTime)}</b></span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                {hasRendered ? (
                  <span style={{ color: '#4ade80' }}>● Final Output Verified</span>
                ) : (
                  <span style={{ color: 'var(--gold)' }}>● Live Generated Audio & Text</span>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Synchronized Shared Timeline & Playback Controller */}
      <div
        className="unified-playback-controls"
        style={{
          background: 'var(--card)',
          border: '1px solid var(--line)',
          borderRadius: 12,
          padding: '16px 20px',
          boxShadow: '0 6px 24px rgba(0, 0, 0, 0.3)',
          display: 'flex',
          flexDirection: 'column',
          gap: 14,
        }}
      >
        {/* Scrub Bar Slider */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ fontSize: 12, fontFamily: 'var(--font-display, monospace)', fontVariantNumeric: 'tabular-nums', fontWeight: 600, color: 'var(--gold)', minWidth: 65 }}>
            {formatTimecode(currentTime)}
          </span>
          <input
            type="range"
            min={0}
            max={duration || active.duration_seconds || 100}
            step={0.05}
            value={currentTime}
            onChange={(e) => handleSeek(parseFloat(e.target.value))}
            style={{
              flex: 1,
              accentColor: 'var(--gold)',
              cursor: 'pointer',
              height: 6,
              borderRadius: 3,
            }}
          />
          <span style={{ fontSize: 12, fontFamily: 'var(--font-display, monospace)', fontVariantNumeric: 'tabular-nums', fontWeight: 600, color: 'var(--muted)', minWidth: 65, textAlign: 'right' }}>
            {fmtTime(duration || active.duration_seconds || 0)}
          </span>
        </div>

        {/* Playback Action Buttons & Audio Track Selector */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
          {/* Left: Play/Pause/Restart/Speed */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
            {/* Play/Pause Button */}
            <motion.button
              whileTap={{ scale: 0.95 }}
              onClick={togglePlay}
              className="primary-btn"
              style={{
                width: 44,
                height: 44,
                borderRadius: '50%',
                padding: 0,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                background: isPlaying
                  ? 'linear-gradient(135deg, #e5c783 0%, #b38a3f 100%)'
                  : 'linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)',
                color: isPlaying ? '#080f1d' : '#ffffff',
                boxShadow: '0 4px 14px rgba(0,0,0,0.4)',
              }}
              title={isPlaying ? 'Pause Both (Space)' : 'Play Both (Space)'}
            >
              {isPlaying ? <Pause size={20} /> : <Play size={20} style={{ marginLeft: 2 }} />}
            </motion.button>

            {/* Restart Button */}
            <button
              className="player-icon-btn"
              onClick={handleRestart}
              title="Restart from 00:00"
            >
              <RotateCcw size={16} />
            </button>

            {/* Playback Speed Pills */}
            <div className="preview-setting-pills" style={{ marginLeft: 6 }}>
              {[0.75, 1, 1.25, 1.5].map((speed) => (
                <button
                  key={speed}
                  className={`preview-pill-btn ${playbackRate === speed ? 'active' : ''}`}
                  onClick={() => handleSpeedChange(speed)}
                  style={{ fontSize: 11, padding: '4px 8px' }}
                >
                  {speed}x
                </button>
              ))}
            </div>
          </div>

          {/* Center: Audio Track Switcher */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
            <span style={{ fontSize: 12, color: 'var(--muted)', fontWeight: 600 }}>Audio Track:</span>
            <div className="preview-mode-tabs">
              <button
                className={`preview-mode-btn ${audioMode === 'both' ? 'active' : ''}`}
                onClick={() => setAudioMode('both')}
                title="Play both original and dubbed audio"
              >
                <Layers size={13} /> Both
              </button>
              <button
                className={`preview-mode-btn ${audioMode === 'original' ? 'active' : ''}`}
                onClick={() => setAudioMode('original')}
                title="Play original audio only"
              >
                Original Audio
              </button>
              <button
                className={`preview-mode-btn ${audioMode === 'dubbed' ? 'active' : ''}`}
                onClick={() => setAudioMode('dubbed')}
                title="Play dubbed target audio only"
              >
                Dubbed Audio
              </button>
            </div>

            {/* Independent Volume Controls */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, background: 'rgba(0,0,0,0.25)', padding: '4px 10px', borderRadius: 8, border: '1px solid var(--line)' }}>
              <button
                type="button"
                onClick={() => setIsOrigMuted(!isOrigMuted)}
                title="Mute / Unmute Original"
                style={{ background: 'none', border: 'none', color: isOrigMuted ? 'var(--muted)' : '#60a5fa', cursor: 'pointer', padding: 0 }}
              >
                {isOrigMuted ? <VolumeX size={15} /> : <Volume1 size={15} />}
              </button>
              <input
                type="range"
                min={0}
                max={1}
                step={0.05}
                value={isOrigMuted ? 0 : origVolume}
                onChange={(e) => {
                  setOrigVolume(parseFloat(e.target.value));
                  setIsOrigMuted(false);
                }}
                title={`Original Volume: ${Math.round(origVolume * 100)}%`}
                style={{ width: 60, accentColor: '#3b82f6', height: 4 }}
              />

              <div style={{ width: 1, height: 16, background: 'var(--line)', margin: '0 4px' }} />

              <button
                type="button"
                onClick={() => setIsTransMuted(!isTransMuted)}
                title="Mute / Unmute Dubbed"
                style={{ background: 'none', border: 'none', color: isTransMuted ? 'var(--muted)' : 'var(--gold)', cursor: 'pointer', padding: 0 }}
              >
                {isTransMuted ? <VolumeX size={15} /> : <Volume2 size={15} />}
              </button>
              <input
                type="range"
                min={0}
                max={1}
                step={0.05}
                value={isTransMuted ? 0 : transVolume}
                onChange={(e) => {
                  setTransVolume(parseFloat(e.target.value));
                  setIsTransMuted(false);
                }}
                title={`Dubbed Volume: ${Math.round(transVolume * 100)}%`}
                style={{ width: 60, accentColor: 'var(--gold)', height: 4 }}
              />
            </div>
          </div>

          {/* Right: Fullscreen & Settings */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <button
              className="player-icon-btn"
              onClick={toggleFullscreen}
              title={isFullscreen ? 'Exit Fullscreen' : 'Enter Fullscreen'}
            >
              {isFullscreen ? <Minimize size={16} /> : <Maximize size={16} />}
            </button>
          </div>
        </div>
      </div>

      {/* Settings Drawer (Subtitle Appearance & Comparisons) */}
      <AnimatePresence>
        {showSettingsDrawer && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="preview-settings-drawer"
            style={{ marginTop: 14, overflow: 'hidden' }}
          >
            <div className="preview-setting-item">
              <span className="preview-setting-label">Subtitle Font Size</span>
              <div className="preview-setting-pills">
                {(['small', 'medium', 'large'] as const).map((s) => (
                  <button
                    key={s}
                    className={`preview-pill-btn ${fontSize === s ? 'active' : ''}`}
                    onClick={() => setFontSize(s)}
                  >
                    {s.toUpperCase()}
                  </button>
                ))}
              </div>
            </div>

            <div className="preview-setting-item">
              <span className="preview-setting-label">Subtitle Position</span>
              <div className="preview-setting-pills">
                {(['bottom', 'center', 'top'] as const).map((p) => (
                  <button
                    key={p}
                    className={`preview-pill-btn ${subtitlePosition === p ? 'active' : ''}`}
                    onClick={() => setSubtitlePosition(p)}
                  >
                    {p.toUpperCase()}
                  </button>
                ))}
              </div>
            </div>

            <div className="preview-setting-item">
              <span className="preview-setting-label">A/B Comparison Split</span>
              <input
                type="range"
                min={10}
                max={90}
                value={abSplitPercent}
                onChange={(e) => setAbSplitPercent(parseInt(e.target.value, 10))}
                style={{ width: 120, accentColor: 'var(--gold)' }}
              />
              <span style={{ fontSize: 12, color: 'var(--muted)', width: 40 }}>{abSplitPercent}%</span>
            </div>

            <div className="preview-setting-item" style={{ borderTop: '1px solid var(--line)', paddingTop: 10, marginTop: 6 }}>
              <span className="preview-setting-label" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <ShieldCheck size={14} style={{ color: 'var(--green)' }} />
                Preserve Soundtrack & SFX
              </span>
              <button
                type="button"
                className={`preview-pill-btn ${preserveSoundtrack ? 'active' : ''}`}
                onClick={() => setPreserveSoundtrack(!preserveSoundtrack)}
                style={{
                  background: preserveSoundtrack ? 'rgba(16, 185, 129, 0.2)' : undefined,
                  color: preserveSoundtrack ? 'var(--green)' : undefined,
                  borderColor: preserveSoundtrack ? 'var(--green)' : undefined,
                  fontWeight: 700,
                }}
              >
                {preserveSoundtrack ? 'ON (Preserving Music & Fighting SFX)' : 'OFF (Mute Original)'}
              </button>
            </div>

            <div className="preview-setting-item">
              <span className="preview-setting-label">Soundtrack Volume (Music & Action)</span>
              <input
                type="range"
                min={0}
                max={1.5}
                step={0.05}
                value={soundtrackVolume}
                onChange={(e) => setSoundtrackVolume(parseFloat(e.target.value))}
                style={{ width: 120, accentColor: 'var(--gold)' }}
              />
              <span style={{ fontSize: 12, color: 'var(--muted)', width: 40 }}>{Math.round(soundtrackVolume * 100)}%</span>
            </div>

            <div className="preview-setting-item">
              <span className="preview-setting-label">Dialogue Volume (Translated Voice)</span>
              <input
                type="range"
                min={0}
                max={1.5}
                step={0.05}
                value={dialogueVolume}
                onChange={(e) => setDialogueVolume(parseFloat(e.target.value))}
                style={{ width: 120, accentColor: 'var(--green)' }}
              />
              <span style={{ fontSize: 12, color: 'var(--muted)', width: 40 }}>{Math.round(dialogueVolume * 100)}%</span>
            </div>

            <div className="preview-setting-item">
              <span className="preview-setting-label">Preserve Nonverbal Audio</span>
              <button
                type="button"
                className={`preview-pill-btn ${preserveNonverbal ? 'active' : ''}`}
                onClick={() => setPreserveNonverbal(!preserveNonverbal)}
                title="Preserve authentic actor laughter, screams, gasps, and fighting sounds"
              >
                {preserveNonverbal ? 'ON (Real Laughter & Gasps)' : 'OFF'}
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Export & Render Action Bottom Bar */}
      <div
        className="export-action-section"
        style={{
          marginTop: 20,
          padding: '20px 24px',
          background: 'var(--card)',
          borderRadius: 12,
          border: '1px solid var(--line)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: 16,
        }}
      >
        <div className="export-action-info" style={{ maxWidth: 600 }}>
          <b style={{ fontSize: 15, display: 'block', marginBottom: 4, color: 'var(--text)' }}>
            {hasRendered ? 'Final Video Rendered and Verified' : 'Render Translated Video with Hardsub Subtitles'}
          </b>
          <p style={{ color: 'var(--muted)', fontSize: 12, margin: 0, lineHeight: 1.5 }}>
            {hasRendered
              ? 'វីដេអូ MP4 ត្រូវបានដុតបញ្ចូល Subtitles (Hardsub) និងបញ្ចូលសម្លេង Dubbed រួចរាល់។ អ្នកអាចទាញយក (Download) ឯកសារខាងក្រោម។'
              : 'ចុច "Render Final Video (MP4)" ដើម្បីបញ្ជា FFmpeg ដុតបញ្ចូល Subtitles និងលាយសម្លេង Dubbed ចូលក្នុងវីដេអូទិន្នផលចុងក្រោយ។'}
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
          {/* Render Final Video Button */}
          <motion.button
            whileTap={{ scale: 0.98 }}
            className="primary-btn"
            disabled={isExporting || busy || (!transcriptList.length && !translationList.length)}
            onClick={handleExportVideo}
            style={{
              background: 'linear-gradient(135deg, #e5c783 0%, #b38a3f 100%)',
              color: '#080f1d',
              fontWeight: 700,
              padding: '10px 18px',
              fontSize: 13,
            }}
          >
            {isExporting ? <Loader2 size={16} className="spin" /> : <Film size={16} />}
            {isExporting
              ? 'Rendering Video (FFmpeg)...'
              : hasRendered
              ? 'Re-render Final Video (MP4)'
              : 'Render Final Video (MP4)'}
          </motion.button>

          {/* Download Rendered MP4 */}
          {hasRendered ? (
            <a
              className="primary-btn link-btn"
              href={`${API}/api/jobs/${active.id}/rendered-video?download=true`}
              download
              style={{
                background: 'linear-gradient(135deg, #22c55e 0%, #16a34a 100%)',
                color: '#ffffff',
                fontWeight: 700,
                padding: '10px 18px',
                fontSize: 13,
              }}
            >
              <Download size={16} /> Download Final Video (.mp4)
            </a>
          ) : (
            <button
              className="secondary-btn"
              disabled
              title="សូមចុច Render Final Video ជាមុនសិន ដើម្បីទាញយក MP4"
              style={{ opacity: 0.5, cursor: 'not-allowed' }}
            >
              <Download size={16} /> Download Final Video (Awaiting Render)
            </button>
          )}

          {/* Subtitles Download Dropdown */}
          <div style={{ position: 'relative' }}>
            <button
              className="secondary-btn"
              onClick={() => setShowDownloadDropdown(!showDownloadDropdown)}
              style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '10px 14px' }}
            >
              <FileText size={15} /> Export Subtitles <ChevronDown size={14} />
            </button>

            {showDownloadDropdown && (
              <div
                style={{
                  position: 'absolute',
                  right: 0,
                  bottom: '100%',
                  marginBottom: 8,
                  background: 'var(--panel)',
                  border: '1px solid var(--line)',
                  borderRadius: 8,
                  padding: 6,
                  boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
                  zIndex: 40,
                  minWidth: 180,
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 4,
                }}
              >
                <a
                  className="dropdown-link-btn"
                  href={`${API}/api/jobs/${active.id}/subtitles.srt?lang=target`}
                  download
                  onClick={() => setShowDownloadDropdown(false)}
                >
                  Download Target Subtitles (.srt)
                </a>
                <a
                  className="dropdown-link-btn"
                  href={`${API}/api/jobs/${active.id}/subtitles.vtt?lang=target`}
                  download
                  onClick={() => setShowDownloadDropdown(false)}
                >
                  Download Target Subtitles (.vtt)
                </a>
                <a
                  className="dropdown-link-btn"
                  href={`${API}/api/jobs/${active.id}/transcript.txt?lang=target`}
                  download
                  onClick={() => setShowDownloadDropdown(false)}
                >
                  Download Target Transcript (.txt)
                </a>
                <div style={{ height: 1, background: 'var(--line)', margin: '4px 0' }} />
                <a
                  className="dropdown-link-btn"
                  href={`${API}/api/jobs/${active.id}/subtitles.srt?lang=source`}
                  download
                  onClick={() => setShowDownloadDropdown(false)}
                >
                  Download Source Subtitles (.srt)
                </a>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
