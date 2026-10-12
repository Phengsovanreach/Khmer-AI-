import React, { useState } from 'react';
import {
  Search,
  RotateCcw,
  Plus,
  Scissors,
  Merge,
  Trash2,
  AlertTriangle,
  Play,
  Save,
  Languages,
  Check,
  Copy,
  Clock,
  Sparkles,
  Users,
  Sliders,
  Replace,
  Type,
  Palette,
  Smile,
  Volume2,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Job, TranscriptSegment, SpeakerProfile, fmtTime, SubtitleStyling } from '../types';

interface SubtitleEditorProProps {
  job: Job;
  API: string;
  editedSegments: TranscriptSegment[];
  translationSegments: TranscriptSegment[];
  speakers?: SpeakerProfile[];
  targetLanguage?: string;
  onSegmentsChange: (segments: TranscriptSegment[]) => void;
  onTranslationChange: (translation: TranscriptSegment[]) => void;
  onSeekToTime?: (time: number) => void;
  currentTime?: number;
  onRefreshJob: () => Promise<void>;
  setNotice: (msg: string) => void;
  setError: (msg: string) => void;
  isDirty: boolean;
  onSaveNow: () => Promise<void>;
  onTranslate: () => Promise<void>;
  onStylingChange?: (styling: SubtitleStyling) => void;
}

export const SubtitleEditorPro: React.FC<SubtitleEditorProProps> = ({
  job,
  API,
  editedSegments,
  translationSegments,
  speakers = [],
  targetLanguage = 'km',
  onSegmentsChange,
  onTranslationChange,
  onSeekToTime,
  currentTime = 0,
  onRefreshJob,
  setNotice,
  setError,
  isDirty,
  onSaveNow,
  onTranslate,
  onStylingChange,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [replaceQuery, setReplaceQuery] = useState('');
  const [showReplace, setShowReplace] = useState(false);
  const [showStyling, setShowStyling] = useState(false);
  const [copied, setCopied] = useState(false);

  // Undo / Redo history
  const [history, setHistory] = useState<TranscriptSegment[][]>([]);
  const [historyIdx, setHistoryIdx] = useState<number>(-1);

  // Split Modal State
  const [splitTarget, setSplitTarget] = useState<TranscriptSegment | null>(null);
  const [splitTime, setSplitTime] = useState<number>(0);
  const [splitText1, setSplitText1] = useState<string>('');
  const [splitText2, setSplitText2] = useState<string>('');
  const [isSplitting, setIsSplitting] = useState(false);

  // Line audio preview
  const [playingSegIdx, setPlayingSegIdx] = useState<number | null>(null);
  const currentAudioRef = React.useRef<HTMLAudioElement | null>(null);

  const handlePlayLineAudio = async (seg: TranscriptSegment, idx: number) => {
    const transSeg = translationSegments.find((t) => t.id === seg.id) || seg;
    const textToSpeak = transSeg.text?.trim() || seg.text?.trim();
    if (!textToSpeak) return;

    const spk = speakers.find((s) => s.speaker_id === seg.speaker_id);
    const voiceId = spk?.assigned_voice_id || 'km-KH-PisethNeural';
    const emotion = seg.emotion || 'neutral';
    const rate = spk?.speech_rate || 0;

    try {
      setPlayingSegIdx(idx);
      if (currentAudioRef.current) {
        currentAudioRef.current.pause();
      }
      const res = await fetch(`${API}/api/dubbing/segment-sample`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: textToSpeak,
          voice_id: voiceId,
          emotion: emotion,
          rate: rate,
        }),
      });
      if (!res.ok) throw new Error('Audio synthesis failed');
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      currentAudioRef.current = audio;
      audio.onended = () => {
        setPlayingSegIdx(null);
        URL.revokeObjectURL(url);
      };
      audio.onerror = () => {
        setPlayingSegIdx(null);
        URL.revokeObjectURL(url);
      };
      await audio.play();
    } catch (err: any) {
      setPlayingSegIdx(null);
      setError(`បរាជ័យក្នុងការចាក់សំឡេង AI Line: ${err.message || err}`);
    }
  };

  // Local styling state
  const [styling, setStyling] = useState<SubtitleStyling>(
    job.subtitle_styling || {
      font_size: 22,
      font_family: 'Noto Sans Khmer',
      primary_color: '#FFFFFF',
      outline_color: '#000000',
      position: 'bottom',
    }
  );

  const pushHistory = (newSegments: TranscriptSegment[]) => {
    const nextHistory = history.slice(0, historyIdx + 1);
    nextHistory.push([...newSegments]);
    setHistory(nextHistory);
    setHistoryIdx(nextHistory.length - 1);
    onSegmentsChange(newSegments);
  };

  const handleUndo = () => {
    if (historyIdx > 0) {
      const prev = history[historyIdx - 1];
      setHistoryIdx(historyIdx - 1);
      onSegmentsChange([...prev]);
      setNotice('បាន Undo ការកែប្រែ (Undone)');
    }
  };

  const handleRedo = () => {
    if (historyIdx < history.length - 1) {
      const next = history[historyIdx + 1];
      setHistoryIdx(historyIdx + 1);
      onSegmentsChange([...next]);
      setNotice('បាន Redo ការកែប្រែ (Redone)');
    }
  };

  // Filtered segments
  const filteredIndices = editedSegments
    .map((seg, idx) => {
      const transText = translationSegments[idx]?.text || '';
      const match =
        !searchQuery.trim() ||
        seg.text.toLowerCase().includes(searchQuery.toLowerCase()) ||
        transText.toLowerCase().includes(searchQuery.toLowerCase()) ||
        String(seg.speaker_id || '').toLowerCase().includes(searchQuery.toLowerCase());
      return match ? idx : -1;
    })
    .filter((idx) => idx !== -1);

  const handleSourceChange = (idx: number, newText: string) => {
    const updated = [...editedSegments];
    updated[idx] = { ...updated[idx], text: newText };
    pushHistory(updated);
  };

  const handleTranslationChange = (idx: number, newText: string) => {
    const updated = [...translationSegments];
    while (updated.length <= idx) {
      const sourceRef = editedSegments[updated.length];
      updated.push({
        id: updated.length + 1,
        start: sourceRef?.start || 0,
        end: sourceRef?.end || 1,
        text: '',
        speaker_id: sourceRef?.speaker_id,
      });
    }
    updated[idx] = { ...updated[idx], text: newText };
    onTranslationChange(updated);
  };

  const handleSpeakerChange = (idx: number, newSpeakerId: string) => {
    const updatedSources = [...editedSegments];
    updatedSources[idx] = { ...updatedSources[idx], speaker_id: newSpeakerId };
    pushHistory(updatedSources);

    if (translationSegments.length > idx) {
      const updatedTranslations = [...translationSegments];
      updatedTranslations[idx] = { ...updatedTranslations[idx], speaker_id: newSpeakerId };
      onTranslationChange(updatedTranslations);
    }
    setNotice(`បានប្តូរ Speaker សម្រាប់ Segment #${idx + 1}`);
  };

  const handleEmotionChange = (idx: number, newEmotion: string) => {
    const updatedSources = [...editedSegments];
    updatedSources[idx] = { ...updatedSources[idx], emotion: newEmotion };
    pushHistory(updatedSources);

    if (translationSegments.length > idx) {
      const updatedTranslations = [...translationSegments];
      updatedTranslations[idx] = { ...updatedTranslations[idx], emotion: newEmotion };
      onTranslationChange(updatedTranslations);
    }
    setNotice(`បានកំណត់ Emotion "${newEmotion}" សម្រាប់ Segment #${idx + 1}`);
  };

  const handleTimingChange = (idx: number, field: 'start' | 'end', val: number) => {
    const updated = [...editedSegments];
    updated[idx] = { ...updated[idx], [field]: Math.max(0, val) };
    pushHistory(updated);

    if (translationSegments.length > idx) {
      const updatedTrans = [...translationSegments];
      updatedTrans[idx] = { ...updatedTrans[idx], [field]: Math.max(0, val) };
      onTranslationChange(updatedTrans);
    }
  };

  const handleReplaceAll = () => {
    if (!searchQuery.trim()) return;
    let count = 0;
    const updatedSources = editedSegments.map((s) => {
      if (s.text.includes(searchQuery)) {
        count++;
        return { ...s, text: s.text.replaceAll(searchQuery, replaceQuery) };
      }
      return s;
    });

    const updatedTrans = translationSegments.map((s) => {
      if (s.text.includes(searchQuery)) {
        return { ...s, text: s.text.replaceAll(searchQuery, replaceQuery) };
      }
      return s;
    });

    pushHistory(updatedSources);
    onTranslationChange(updatedTrans);
    setNotice(`បាន Replace ចំនួន ${count} កន្លែង`);
  };

  const handleAddSegment = async () => {
    try {
      const last = editedSegments[editedSegments.length - 1];
      const start = last ? Math.round((last.end + 0.1) * 100) / 100 : 0.0;
      const end = Math.round((start + 2.0) * 100) / 100;
      const res = await fetch(`${API}/api/jobs/${job.id}/transcript/insert`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          segment: { id: 0, start, end, text: 'Subtitle ថ្មី...', speaker_id: speakers[0]?.speaker_id || 'speaker_1' },
          target: 'transcript',
        }),
      });
      if (!res.ok) throw new Error('Insert failed');
      await onRefreshJob();
      setNotice('បានបន្ថែម Subtitle Segment ថ្មី');
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleDeleteSegment = async (segId: number, idx: number) => {
    try {
      const res = await fetch(`${API}/api/jobs/${job.id}/transcript/${segId}`, {
        method: 'DELETE',
      });
      if (!res.ok) throw new Error('Delete failed');
      await onRefreshJob();
      setNotice(`បានលុប Segment #${idx + 1}`);
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleMergeWithNext = async (idx: number) => {
    if (idx >= editedSegments.length - 1) return;
    const s1 = editedSegments[idx];
    const s2 = editedSegments[idx + 1];
    try {
      const res = await fetch(`${API}/api/jobs/${job.id}/transcript/merge`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          segment_id_1: s1.id,
          segment_id_2: s2.id,
          target: 'transcript',
        }),
      });
      if (!res.ok) throw new Error('Merge failed');
      await onRefreshJob();
      setNotice(`បានបញ្ចូល Segment #${idx + 1} និង #${idx + 2} ចូលគ្នា`);
    } catch (err: any) {
      setError(err.message);
    }
  };

  const openSplitModal = (seg: TranscriptSegment) => {
    setSplitTarget(seg);
    const mid = Math.round(((seg.start + seg.end) / 2) * 100) / 100;
    setSplitTime(mid);
    const words = seg.text.split(' ');
    const half = Math.ceil(words.length / 2);
    setSplitText1(words.slice(0, half).join(' '));
    setSplitText2(words.slice(half).join(' '));
  };

  const handleSplitConfirm = async () => {
    if (!splitTarget) return;
    setIsSplitting(true);
    try {
      const res = await fetch(`${API}/api/jobs/${job.id}/transcript/split`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          segment_id: splitTarget.id,
          split_time: splitTime,
          text_part1: splitText1,
          text_part2: splitText2,
          target: 'transcript',
        }),
      });
      if (!res.ok) {
        const d = await res.json();
        throw new Error(d.detail || 'Split failed');
      }
      await onRefreshJob();
      setSplitTarget(null);
      setNotice('បានបំបែក Segment ដោយជោគជ័យ');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsSplitting(false);
    }
  };

  const handleCopyAll = () => {
    const text = editedSegments.map((s, i) => `${i + 1}\n${fmtTime(s.start)} --> ${fmtTime(s.end)}\n${s.text}`).join('\n\n');
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleUpdateStyling = (key: keyof SubtitleStyling, val: any) => {
    const next = { ...styling, [key]: val };
    setStyling(next);
    if (onStylingChange) {
      onStylingChange(next);
    }
  };

  return (
    <div className="subtitle-editor-pro space-y-3">
      {/* Top Pro Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-2.5 p-3 rounded-2xl bg-slate-900/90 border border-emerald-500/30 backdrop-blur-md">
        {/* Left: Search & Replace */}
        <div className="flex items-center gap-2 flex-1 min-w-[260px]">
          <div className="relative flex-1">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="ស្វែងរកអត្ថបទ ឬ Speaker..."
              className="w-full pl-8 pr-3 py-1.5 text-xs rounded-xl bg-slate-950/80 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-400"
            />
          </div>
          <button
            type="button"
            onClick={() => setShowReplace(!showReplace)}
            className={`p-1.5 rounded-lg border text-xs flex items-center gap-1 transition-colors ${
              showReplace
                ? 'bg-emerald-600/30 text-emerald-300 border-emerald-500/50'
                : 'bg-slate-800/80 text-slate-400 border-slate-700 hover:text-slate-200'
            }`}
            title="Search & Replace"
          >
            <Replace className="w-3.5 h-3.5" />
          </button>
          <button
            type="button"
            onClick={() => setShowStyling(!showStyling)}
            className={`p-1.5 rounded-lg border text-xs flex items-center gap-1 transition-colors ${
              showStyling
                ? 'bg-amber-600/30 text-amber-300 border-amber-500/50'
                : 'bg-slate-800/80 text-slate-400 border-slate-700 hover:text-slate-200'
            }`}
            title="Subtitle Typography & Styling"
          >
            <Palette className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Right: Actions */}
        <div className="flex items-center gap-1.5">
          <button
            type="button"
            onClick={handleUndo}
            disabled={historyIdx <= 0}
            className="p-1.5 rounded-lg bg-slate-800/80 border border-slate-700 text-slate-300 hover:text-white disabled:opacity-40"
            title="Undo"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>

          <button
            type="button"
            onClick={handleAddSegment}
            className="px-2.5 py-1.5 rounded-xl text-xs font-semibold bg-emerald-600/20 text-emerald-300 border border-emerald-500/40 hover:bg-emerald-600/30 flex items-center gap-1"
          >
            <Plus className="w-3.5 h-3.5" /> Add
          </button>

          <button
            type="button"
            onClick={onTranslate}
            className="px-2.5 py-1.5 rounded-xl text-xs font-semibold bg-amber-600/20 text-amber-300 border border-amber-500/40 hover:bg-amber-600/30 flex items-center gap-1"
          >
            <Languages className="w-3.5 h-3.5" /> Translate ({targetLanguage.toUpperCase()})
          </button>

          <button
            type="button"
            onClick={handleCopyAll}
            className="p-1.5 rounded-lg bg-slate-800/80 border border-slate-700 text-slate-300 hover:text-white"
            title="Copy all subtitles"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
          </button>

          {isDirty && (
            <button
              type="button"
              onClick={onSaveNow}
              className="px-3 py-1.5 rounded-xl text-xs font-bold bg-emerald-600 text-white hover:bg-emerald-500 shadow-md shadow-emerald-950 flex items-center gap-1 animate-pulse"
            >
              <Save className="w-3.5 h-3.5" /> Save
            </button>
          )}
        </div>
      </div>

      {/* Replace Drawer */}
      {showReplace && (
        <div className="flex items-center gap-2 p-2.5 rounded-xl bg-slate-950/80 border border-slate-800 animate-in fade-in duration-150">
          <input
            type="text"
            value={replaceQuery}
            onChange={(e) => setReplaceQuery(e.target.value)}
            placeholder="ពាក្យជំនួស (Replace with)..."
            className="flex-1 px-3 py-1 text-xs rounded-lg bg-slate-900 border border-slate-700 text-slate-100 focus:outline-none"
          />
          <button
            type="button"
            onClick={handleReplaceAll}
            className="px-3 py-1 text-xs font-semibold rounded-lg bg-emerald-600 text-white hover:bg-emerald-500"
          >
            Replace All
          </button>
        </div>
      )}

      {/* Subtitle Styling Drawer */}
      {showStyling && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 p-3 rounded-xl bg-slate-950/90 border border-amber-500/30 animate-in fade-in duration-150 text-xs text-slate-300">
          <div>
            <label className="block text-[10px] text-slate-400 mb-1">Font Size:</label>
            <select
              value={styling.font_size || 22}
              onChange={(e) => handleUpdateStyling('font_size', parseInt(e.target.value, 10))}
              className="w-full px-2 py-1 rounded bg-slate-900 border border-slate-700 text-slate-200"
            >
              <option value="18">Small (18px)</option>
              <option value="22">Medium (22px)</option>
              <option value="26">Large (26px)</option>
              <option value="30">Extra Large (30px)</option>
            </select>
          </div>
          <div>
            <label className="block text-[10px] text-slate-400 mb-1">Font Family:</label>
            <select
              value={styling.font_family || 'Noto Sans Khmer'}
              onChange={(e) => handleUpdateStyling('font_family', e.target.value)}
              className="w-full px-2 py-1 rounded bg-slate-900 border border-slate-700 text-slate-200"
            >
              <option value="Noto Sans Khmer">Noto Sans Khmer (អក្សរខ្មែរ)</option>
              <option value="Inter">Inter (English Body & UI)</option>
              <option value="Manrope">Manrope (Modern Heading)</option>
              <option value="Space Grotesk">Space Grotesk (AI Display)</option>
            </select>
          </div>
          <div>
            <label className="block text-[10px] text-slate-400 mb-1">Text Color:</label>
            <input
              type="color"
              value={styling.primary_color || '#FFFFFF'}
              onChange={(e) => handleUpdateStyling('primary_color', e.target.value)}
              className="w-full h-7 rounded bg-slate-900 border border-slate-700 cursor-pointer"
            />
          </div>
          <div>
            <label className="block text-[10px] text-slate-400 mb-1">Position:</label>
            <select
              value={styling.position || 'bottom'}
              onChange={(e) => handleUpdateStyling('position', e.target.value)}
              className="w-full px-2 py-1 rounded bg-slate-900 border border-slate-700 text-slate-200"
            >
              <option value="bottom">Bottom (ខាងក្រោម)</option>
              <option value="middle">Middle (កណ្ដាល)</option>
              <option value="top">Top (ខាងលើ)</option>
            </select>
          </div>
        </div>
      )}

      {/* Segments Dual-Column List */}
      <div className="space-y-2.5 max-h-[640px] overflow-y-auto pr-1">
        {filteredIndices.length === 0 ? (
          <div className="text-center py-12 text-xs text-slate-500 rounded-xl bg-slate-950/40 border border-slate-800">
            មិនមាន Subtitle Segment ណាត្រូវនឹងពាក្យស្វែងរកឡើយ។
          </div>
        ) : (
          filteredIndices.map((idx) => {
            const seg = editedSegments[idx];
            const transSeg = translationSegments[idx];
            const isPlayingThis = currentTime >= seg.start && currentTime <= seg.end;
            const isInvalidOrder = seg.start >= seg.end;

            return (
              <div
                key={seg.id || idx}
                className={`p-3 rounded-2xl border transition-all ${
                  isPlayingThis
                    ? 'border-amber-400/80 bg-gradient-to-r from-amber-950/30 to-slate-900/90 shadow-lg shadow-amber-500/10'
                    : 'border-slate-800/80 bg-slate-900/70 hover:border-emerald-500/30'
                }`}
              >
                {/* Meta Bar */}
                <div className="flex flex-wrap items-center justify-between gap-2 mb-2 pb-2 border-b border-slate-800/50">
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => onSeekToTime && onSeekToTime(seg.start)}
                      className="flex items-center gap-1 px-2 py-0.5 rounded-lg text-xs font-mono font-semibold bg-emerald-950/80 text-emerald-300 border border-emerald-800/40 hover:bg-emerald-900/80 transition-colors"
                      title="Click to jump playback to this timestamp"
                    >
                      <Play className="w-2.5 h-2.5 fill-current" />
                      {fmtTime(seg.start)} → {fmtTime(seg.end)}
                    </button>
                    <span className="text-[10px] text-slate-500 font-mono">#{idx + 1}</span>

                    {/* Speaker Selector Pill */}
                    {speakers.length > 0 && (
                      <div className="flex items-center gap-1">
                        <Users className="w-3 h-3 text-amber-400/80" />
                        <select
                          value={seg.speaker_id || speakers[0]?.speaker_id || 'speaker_1'}
                          onChange={(e) => handleSpeakerChange(idx, e.target.value)}
                          className="text-[10px] font-semibold px-2 py-0.5 rounded-md bg-slate-950 border border-slate-700 text-amber-300 focus:outline-none focus:border-amber-400 cursor-pointer"
                        >
                          {speakers.map((spk) => (
                            <option key={spk.speaker_id} value={spk.speaker_id}>
                              {spk.name}
                            </option>
                          ))}
                        </select>
                      </div>
                    )}

                    {/* Story-Aware Emotion Selector Pill */}
                    <div className="flex items-center gap-1" title="Story-Aware Emotion (Affects Dubbing Pitch, Rate & Style)">
                      <Smile className="w-3 h-3 text-sky-400" />
                      <select
                        value={seg.emotion || 'neutral'}
                        onChange={(e) => handleEmotionChange(idx, e.target.value)}
                        className="text-[10px] font-semibold px-2 py-0.5 rounded-md bg-slate-950 border border-slate-700 text-sky-300 focus:outline-none focus:border-sky-400 cursor-pointer"
                      >
                        <option value="neutral">😐 Neutral</option>
                        <option value="happy">😊 Happy</option>
                        <option value="sad">😢 Sad</option>
                        <option value="angry">😠 Angry</option>
                        <option value="excited">🤩 Excited</option>
                        <option value="afraid">😨 Afraid</option>
                        <option value="surprised">😲 Surprised</option>
                        <option value="worried">😟 Worried</option>
                        <option value="calm">😌 Calm</option>
                        <option value="whispering">🤫 Whispering</option>
                        <option value="serious">🧐 Serious</option>
                        <option value="sarcastic">😏 Sarcastic</option>
                      </select>
                    </div>

                    {/* Preview Line Voice Button */}
                    <button
                      type="button"
                      onClick={() => handlePlayLineAudio(seg, idx)}
                      disabled={playingSegIdx === idx}
                      className="flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-semibold bg-amber-950/80 text-amber-300 border border-amber-800/50 hover:bg-amber-900/80 transition-colors cursor-pointer"
                      title="Play Translated AI Dubbed Voice for this dialogue line"
                    >
                      <Volume2 className="w-3 h-3 text-amber-400" />
                      {playingSegIdx === idx ? 'Playing...' : 'Voice'}
                    </button>
                  </div>

                  {/* Timing Inputs & Actions */}
                  <div className="flex items-center gap-2 text-xs">
                    <div className="flex items-center gap-1 text-[11px] font-mono text-slate-400">
                      <span>S:</span>
                      <input
                        type="number"
                        step="0.1"
                        min="0"
                        value={seg.start}
                        onChange={(e) => handleTimingChange(idx, 'start', parseFloat(e.target.value) || 0)}
                        className="w-14 px-1.5 py-0.5 rounded bg-slate-950 border border-slate-800 text-slate-100 text-center"
                      />
                      <span>E:</span>
                      <input
                        type="number"
                        step="0.1"
                        min="0"
                        value={seg.end}
                        onChange={(e) => handleTimingChange(idx, 'end', parseFloat(e.target.value) || 0)}
                        className="w-14 px-1.5 py-0.5 rounded bg-slate-950 border border-slate-800 text-slate-100 text-center"
                      />
                    </div>

                    <div className="flex items-center gap-1">
                      <button
                        type="button"
                        onClick={() => openSplitModal(seg)}
                        title="Split subtitle"
                        className="p-1 rounded bg-slate-800/80 text-amber-300 hover:bg-slate-700"
                      >
                        <Scissors className="w-3.5 h-3.5" />
                      </button>

                      {idx < editedSegments.length - 1 && (
                        <button
                          type="button"
                          onClick={() => handleMergeWithNext(idx)}
                          title="Merge with next segment"
                          className="p-1 rounded bg-slate-800/80 text-emerald-300 hover:bg-slate-700"
                        >
                          <Merge className="w-3.5 h-3.5" />
                        </button>
                      )}

                      <button
                        type="button"
                        onClick={() => handleDeleteSegment(seg.id, idx)}
                        title="Delete segment"
                        className="p-1 rounded bg-rose-950/60 text-rose-400 hover:bg-rose-900/60 border border-rose-800/30"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                </div>

                {/* Validation Warnings */}
                {isInvalidOrder && (
                  <div className="mb-2 p-1.5 rounded-lg bg-rose-950/60 text-rose-300 text-xs border border-rose-800/40 flex items-center gap-1.5">
                    <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
                    កំហុសលំដាប់ពេលវេលា: End time ({seg.end}s) ត្រូវតែធំជាង Start time ({seg.start}s)!
                  </div>
                )}

                {/* Dual Column Text Areas */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                  <div>
                    <label className="block text-[10px] font-semibold text-slate-400 mb-1">
                      Original Speech (អត្ថបទដើម):
                    </label>
                    <textarea
                      rows={2}
                      value={seg.text}
                      onChange={(e) => handleSourceChange(idx, e.target.value)}
                      placeholder="Source recognized speech text..."
                      className="w-full p-2 text-[13px] font-sans rounded-xl bg-slate-950/80 border border-slate-800 text-slate-100 placeholder-slate-600 focus:outline-none focus:border-emerald-400 transition-colors leading-relaxed tracking-normal"
                    />
                  </div>

                  <div>
                    <label className="block text-[10px] font-semibold text-amber-300 mb-1">
                      {targetLanguage.toUpperCase()} Translation (អត្ថបទបកប្រែ):
                    </label>
                    <textarea
                      rows={2}
                      value={transSeg?.text || ''}
                      onChange={(e) => handleTranslationChange(idx, e.target.value)}
                      placeholder={`Target ${targetLanguage.toUpperCase()} translation...`}
                      className="w-full p-2.5 text-[13.5px] font-khmer rounded-xl bg-slate-950/80 border border-amber-900/40 text-slate-100 placeholder-slate-600 focus:outline-none focus:border-amber-400 transition-colors leading-relaxed tracking-normal"
                    />
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Split Modal Dialog */}
      <AnimatePresence>
        {splitTarget && (
          <div
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
            onClick={() => setSplitTarget(null)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="w-full max-w-md p-5 rounded-2xl bg-slate-900 border border-emerald-500/40 shadow-2xl text-xs space-y-3"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                <Scissors className="w-4 h-4 text-amber-400" />
                បំបែក Segment (Split Subtitle)
              </h3>
              <div className="text-[11px] text-slate-400">
                ពេលវេលា: <b>{splitTarget.start}s</b> → <b>{splitTarget.end}s</b>
              </div>

              <div>
                <label className="block text-[11px] text-slate-300 mb-1">
                  ចំណុចបំបែក (Split Timestamp): <b className="text-amber-400">{splitTime}s</b>
                </label>
                <input
                  type="range"
                  min={splitTarget.start + 0.1}
                  max={splitTarget.end - 0.1}
                  step="0.05"
                  value={splitTime}
                  onChange={(e) => setSplitTime(parseFloat(e.target.value))}
                  className="w-full accent-amber-500"
                />
              </div>

              <div>
                <label className="block text-[11px] text-slate-300 mb-1">ផ្នែកទី ១ (Part 1):</label>
                <textarea
                  rows={2}
                  value={splitText1}
                  onChange={(e) => setSplitText1(e.target.value)}
                  className="w-full p-2 rounded-lg bg-slate-950 border border-slate-700 text-slate-100 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-[11px] text-slate-300 mb-1">ផ្នែកទី ២ (Part 2):</label>
                <textarea
                  rows={2}
                  value={splitText2}
                  onChange={(e) => setSplitText2(e.target.value)}
                  className="w-full p-2 rounded-lg bg-slate-950 border border-slate-700 text-slate-100 focus:outline-none"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setSplitTarget(null)}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700"
                >
                  បោះបង់
                </button>
                <button
                  type="button"
                  disabled={isSplitting}
                  onClick={handleSplitConfirm}
                  className="px-3 py-1.5 rounded-lg bg-emerald-600 text-white font-semibold hover:bg-emerald-500"
                >
                  {isSplitting ? 'កំពុងបំបែក...' : 'បញ្ជាក់ការបំបែក'}
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};
