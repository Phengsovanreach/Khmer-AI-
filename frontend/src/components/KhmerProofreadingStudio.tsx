import React, { useState, useEffect } from 'react';
import {
  AlertCircle,
  BookOpen,
  Check,
  CheckCheck,
  CheckCircle2,
  ChevronDown,
  Clock,
  Edit3,
  FileCheck2,
  Filter,
  History,
  Languages,
  Loader2,
  RefreshCw,
  RotateCcw,
  Sparkles,
  Undo2,
  Volume2,
  Wand2,
  X,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Job, ProofreadJobResponse, SegmentProofreadResult, TranscriptSegment } from '../types';

interface KhmerProofreadingStudioProps {
  job: Job | null;
  API: string;
  onRefreshJob: () => Promise<void>;
  setNotice: (msg: string) => void;
  setError: (msg: string) => void;
}

export const KhmerProofreadingStudio: React.FC<KhmerProofreadingStudioProps> = ({
  job,
  API,
  onRefreshJob,
  setNotice,
  setError,
}) => {
  const [style, setStyle] = useState<'conversational' | 'formal' | 'narrative'>('conversational');
  const [isLoading, setIsLoading] = useState(false);
  const [isApplying, setIsApplying] = useState(false);
  const [proofResults, setProofResults] = useState<SegmentProofreadResult[]>([]);
  const [summary, setSummary] = useState<ProofreadJobResponse['summary'] | null>(null);

  // Filter state
  const [activeFilter, setActiveFilter] = useState<'all' | 'issues_only' | 'spelling' | 'grammar' | 'terminology' | 'number_format'>('all');

  // History state for Undo / Redo
  const [historyStack, setHistoryStack] = useState<SegmentProofreadResult[][]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);

  // Audio audition state
  const [playingSegmentId, setPlayingSegmentId] = useState<number | null>(null);
  const [editingSegmentId, setEditingSegmentId] = useState<number | null>(null);
  const [editingText, setEditingText] = useState('');

  // Initial scan on mount or when job translation changes
  const runProofreadScan = async (autoApply = false) => {
    if (!job?.id) return;
    setIsLoading(true);
    try {
      const res = await fetch(`${API}/api/jobs/${job.id}/proofread`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          style,
          auto_apply_high_confidence: autoApply,
        }),
      });
      const data: ProofreadJobResponse = await res.json();
      if (!res.ok) throw new Error((data as any).detail || 'Proofreading failed');

      setProofResults(data.results);
      setSummary(data.summary);

      // Initialize history stack
      setHistoryStack([data.results]);
      setHistoryIndex(0);

      if (autoApply) {
        setNotice(`បានអនុវត្តការកែតម្រូវស្វ័យប្រវត្តិចំនួន ${data.summary.auto_applied_count} ឃ្លាដោយជោគជ័យ!`);
        await onRefreshJob();
      } else {
        setNotice(`បានស្កេនពិនិត្យចប់សព្វគ្រប់: រកឃើញចំណុចកែលម្អចំនួន ${data.total_issues} កន្លែង។`);
      }
    } catch (err: any) {
      setError(err.message || 'Proofreading scan failed');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (job?.translation && job.translation.length > 0 && proofResults.length === 0) {
      void runProofreadScan(false);
    }
  }, [job?.id, job?.translation?.length]);

  // Update history state
  const pushState = (newResults: SegmentProofreadResult[]) => {
    const nextStack = historyStack.slice(0, historyIndex + 1);
    nextStack.push(newResults);
    setHistoryStack(nextStack);
    setHistoryIndex(nextStack.length - 1);
    setProofResults(newResults);
  };

  const handleUndo = () => {
    if (historyIndex > 0) {
      const targetIdx = historyIndex - 1;
      setHistoryIndex(targetIdx);
      setProofResults(historyStack[targetIdx]);
    }
  };

  const handleRedo = () => {
    if (historyIndex < historyStack.length - 1) {
      const targetIdx = historyIndex + 1;
      setHistoryIndex(targetIdx);
      setProofResults(historyStack[targetIdx]);
    }
  };

  // Accept a single segment's suggestion
  const handleAcceptSegment = (segId: number) => {
    const updated = proofResults.map((item) => {
      if (item.segment_id === segId) {
        return {
          ...item,
          initial_translation: item.suggested_khmer,
          issues: [],
          applied_automatically: true,
        };
      }
      return item;
    });
    pushState(updated);
  };

  // Reject a single segment's suggestion
  const handleRejectSegment = (segId: number) => {
    const updated = proofResults.map((item) => {
      if (item.segment_id === segId) {
        return {
          ...item,
          suggested_khmer: item.initial_translation,
          issues: [],
          applied_automatically: false,
        };
      }
      return item;
    });
    pushState(updated);
  };

  // Start inline editing
  const handleStartEdit = (item: SegmentProofreadResult) => {
    setEditingSegmentId(item.segment_id);
    setEditingText(item.suggested_khmer || item.initial_translation);
  };

  // Save manual inline edit
  const handleSaveEdit = (segId: number) => {
    const updated = proofResults.map((item) => {
      if (item.segment_id === segId) {
        return {
          ...item,
          initial_translation: editingText,
          suggested_khmer: editingText,
          issues: [],
          applied_automatically: true,
        };
      }
      return item;
    });
    pushState(updated);
    setEditingSegmentId(null);
  };

  // Accept all high confidence suggestions
  const handleAcceptAllHighConfidence = () => {
    let count = 0;
    const updated = proofResults.map((item) => {
      if (item.confidence >= 0.85 && item.suggested_khmer !== item.initial_translation) {
        count++;
        return {
          ...item,
          initial_translation: item.suggested_khmer,
          issues: [],
          applied_automatically: true,
        };
      }
      return item;
    });
    pushState(updated);
    setNotice(`បានយល់ព្រមទទួលយកការកែតម្រូវដែលមានទំនុកចិត្តខ្ពស់ចំនួន ${count} ឃ្លា។`);
  };

  // Save reviewed translation back to Job
  const handleApplyAllChangesToJob = async () => {
    if (!job?.id) return;
    setIsApplying(true);
    try {
      const payloadSegments: TranscriptSegment[] = proofResults.map((r) => ({
        id: r.segment_id,
        start: r.start,
        end: r.end,
        text: r.initial_translation,
        speaker_id: r.speaker_id,
      }));

      const res = await fetch(`${API}/api/jobs/${job.id}/proofread-apply`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ applied_segments: payloadSegments }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to save proofread changes');

      await onRefreshJob();
      setNotice('បានរក្សាទុកអត្ថបទដែលបានផ្ទៀងផ្ទាត់ចូលក្នុងគម្រោងដោយជោគជ័យ!');
    } catch (err: any) {
      setError(err.message || 'Failed to apply proofread changes');
    } finally {
      setIsApplying(false);
    }
  };

  // Audition dialogue line audio
  const handlePlayAudio = async (text: string, segId: number) => {
    if (!text.trim() || playingSegmentId === segId) return;
    setPlayingSegmentId(segId);
    try {
      const res = await fetch(`${API}/api/dubbing/segment-sample`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text,
          voice_id: 'km-KH-PisethNeural',
          emotion: 'neutral',
        }),
      });
      if (!res.ok) throw new Error('Audio sample generation failed');
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audio.onended = () => {
        setPlayingSegmentId(null);
        URL.revokeObjectURL(url);
      };
      audio.onerror = () => {
        setPlayingSegmentId(null);
        URL.revokeObjectURL(url);
      };
      await audio.play();
    } catch (err) {
      setPlayingSegmentId(null);
    }
  };

  // Filtered segments
  const filteredList = proofResults.filter((item) => {
    if (activeFilter === 'all') return true;
    if (activeFilter === 'issues_only') return item.issues.length > 0;
    return item.issues.some((i) => i.type === activeFilter);
  });

  if (!job) {
    return (
      <div className="proofread-studio-root">
        <div className="empty-state" style={{ padding: 48, textAlign: 'center' }}>
          <div className="empty-art">
            <FileCheck2 size={28} />
          </div>
          <h3>មិនទាន់មានគម្រោងសកម្មសម្រាប់ផ្ទៀងផ្ទាត់នៅឡើយទេ</h3>
          <p>សូមជ្រើសរើស ឬបញ្ចូលវីដេអូ ដើម្បីចាប់ផ្ដើមត្រួតពិនិត្យអក្ខរាវិរុទ្ធ និងវេយ្យាករណ៍ខ្មែរ។</p>
        </div>
      </div>
    );
  }

  return (
    <div className="proofread-studio-root">
      {/* Studio Header */}
      <div className="proofread-header-card">
        <div className="proofread-header-top">
          <div className="proofread-brand-info">
            <div className="proofread-icon-box">
              <FileCheck2 size={24} />
            </div>
            <div>
              <h3>Khmer Text-Quality & Proofreading Studio Pro</h3>
              <p>ប្រព័ន្ធផ្ទៀងផ្ទាត់អក្ខរាវិរុទ្ធ វេយ្យាករណ៍ និងពាក្យបច្ចេកទេសភាសាខ្មែរតាមបរិបទសាច់រឿង</p>
            </div>
          </div>

          {/* Action Toolbar */}
          <div className="proofread-top-actions">
            <div className="proofread-style-select">
              <span className="text-xs text-muted">កម្រិតភាសា:</span>
              <select
                value={style}
                onChange={(e) => setStyle(e.target.value as any)}
                className="config-select"
                style={{ padding: '6px 12px', fontSize: 12 }}
              >
                <option value="conversational">សន្ទនាទូទៅ (Conversational)</option>
                <option value="formal">ផ្លូវការ (Formal)</option>
                <option value="narrative">និទានរឿង (Narrative)</option>
              </select>
            </div>

            <button
              type="button"
              className="secondary-btn"
              onClick={() => runProofreadScan(false)}
              disabled={isLoading}
            >
              {isLoading ? <Loader2 size={14} className="spin" /> : <RefreshCw size={14} />}
              <span>ស្កេនឡើងវិញ (Rescan)</span>
            </button>

            <button
              type="button"
              className="primary-btn"
              onClick={handleApplyAllChangesToJob}
              disabled={isApplying || proofResults.length === 0}
            >
              {isApplying ? <Loader2 size={14} className="spin" /> : <CheckCheck size={14} />}
              <span>រក្សាទុកចូលក្នុងវីដេអូ (Save to Video)</span>
            </button>
          </div>
        </div>

        {/* Summary Metric Pills */}
        {summary && (
          <div className="proofread-metrics-bar">
            <div className="metric-pill">
              <span>សរុបទាំងអស់:</span>
              <b>{summary.total_segments} ឃ្លា</b>
            </div>
            <div className={`metric-pill ${summary.total_issues > 0 ? 'warning' : 'success'}`}>
              <AlertCircle size={13} />
              <span>ចំណុចកែលម្អ:</span>
              <b>{summary.total_issues} កន្លែង</b>
            </div>
            {summary.spelling_issues > 0 && (
              <div className="metric-pill info">
                <span>អក្ខរាវិរុទ្ធ:</span>
                <b>{summary.spelling_issues}</b>
              </div>
            )}
            {summary.grammar_issues > 0 && (
              <div className="metric-pill info">
                <span>វេយ្យាករណ៍:</span>
                <b>{summary.grammar_issues}</b>
              </div>
            )}
            {summary.terminology_issues > 0 && (
              <div className="metric-pill gold">
                <span>បច្ចេកសព្ទ:</span>
                <b>{summary.terminology_issues}</b>
              </div>
            )}
            {summary.number_issues > 0 && (
              <div className="metric-pill info">
                <span>លេខ-កាលបរិច្ឆេទ:</span>
                <b>{summary.number_issues}</b>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Control Bar: Filters & Batch Operations */}
      <div className="proofread-control-bar">
        {/* Category Filter Tabs */}
        <div className="proofread-filters">
          <button
            type="button"
            className={`filter-tab ${activeFilter === 'all' ? 'active' : ''}`}
            onClick={() => setActiveFilter('all')}
          >
            ទាំងអស់ ({proofResults.length})
          </button>
          <button
            type="button"
            className={`filter-tab ${activeFilter === 'issues_only' ? 'active' : ''}`}
            onClick={() => setActiveFilter('issues_only')}
          >
            មានបញ្ហា ({proofResults.filter((r) => r.issues.length > 0).length})
          </button>
          <button
            type="button"
            className={`filter-tab ${activeFilter === 'spelling' ? 'active' : ''}`}
            onClick={() => setActiveFilter('spelling')}
          >
            អក្ខរាវិរុទ្ធ
          </button>
          <button
            type="button"
            className={`filter-tab ${activeFilter === 'grammar' ? 'active' : ''}`}
            onClick={() => setActiveFilter('grammar')}
          >
            វេយ្យាករណ៍
          </button>
          <button
            type="button"
            className={`filter-tab ${activeFilter === 'terminology' ? 'active' : ''}`}
            onClick={() => setActiveFilter('terminology')}
          >
            បច្ចេកសព្ទ
          </button>
        </div>

        {/* Undo, Redo & Batch Accept */}
        <div className="proofread-batch-actions">
          <button
            type="button"
            className="icon-btn-sm"
            onClick={handleUndo}
            disabled={historyIndex <= 0}
            title="Undo"
          >
            <Undo2 size={14} />
          </button>
          <button
            type="button"
            className="icon-btn-sm"
            onClick={handleRedo}
            disabled={historyIndex >= historyStack.length - 1}
            title="Redo"
          >
            <RotateCcw size={14} />
          </button>
          <button
            type="button"
            className="secondary-btn"
            style={{ fontSize: 12, padding: '6px 14px' }}
            onClick={handleAcceptAllHighConfidence}
          >
            <Wand2 size={13} style={{ color: 'var(--gold)' }} />
            <span>យល់ព្រមយកការកែតម្រូវទាំងអស់ (Accept All)</span>
          </button>
        </div>
      </div>

      {/* Segments Review List */}
      <div className="proofread-segments-container">
        {filteredList.length === 0 ? (
          <div className="proofread-empty-card">
            <CheckCircle2 size={40} style={{ color: 'var(--green)', marginBottom: 12 }} />
            <h4>អត្ថបទមានភាពត្រឹមត្រូវពេញលេញ!</h4>
            <p>មិនមានកំហុសអក្ខរាវិរុទ្ធ ឬវេយ្យាករណ៍នៅក្នុងជម្រើសចម្រាញ់នេះទេ។</p>
          </div>
        ) : (
          filteredList.map((item) => {
            const hasIssues = item.issues.length > 0;
            const isEditing = editingSegmentId === item.segment_id;
            const isPlaying = playingSegmentId === item.segment_id;

            return (
              <motion.div
                key={item.segment_id}
                layout
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                className={`proofread-segment-card ${hasIssues ? 'has-issue' : 'clean'}`}
              >
                {/* Segment Meta Head */}
                <div className="segment-card-meta">
                  <div className="segment-meta-left">
                    <span className="segment-id-pill">#{item.segment_id}</span>
                    <span className="segment-time-pill">
                      <Clock size={11} /> {item.start.toFixed(1)}s - {item.end.toFixed(1)}s
                    </span>
                    {item.speaker_id && (
                      <span className="segment-speaker-pill">
                        {item.speaker_id.replace('_', ' ')}
                      </span>
                    )}
                  </div>

                  <div className="segment-meta-right">
                    {hasIssues ? (
                      <span className="segment-confidence-pill warning">
                        <AlertCircle size={12} />
                        រកឃើញ {item.issues.length} បញ្ហា (ទំនុកចិត្ត {Math.round(item.confidence * 100)}%)
                      </span>
                    ) : (
                      <span className="segment-confidence-pill success">
                        <CheckCircle2 size={12} /> ត្រឹមត្រូវល្អ
                      </span>
                    )}

                    <button
                      type="button"
                      className="icon-btn-sm"
                      onClick={() => handlePlayAudio(item.suggested_khmer || item.initial_translation, item.segment_id)}
                      title="Audition spoken line"
                    >
                      {isPlaying ? <Loader2 size={13} className="spin" /> : <Volume2 size={13} />}
                    </button>
                  </div>
                </div>

                {/* 3-Column / Responsive Comparison Grid */}
                <div className="proofread-comparison-grid">
                  {/* Column 1: Original Source */}
                  <div className="comparison-col source-col">
                    <div className="col-label">អត្ថបទប្រភពដើម (Source Speech)</div>
                    <div className="col-content text-source">
                      {item.original_source || '—'}
                    </div>
                  </div>

                  {/* Column 2: Initial Translation */}
                  <div className="comparison-col initial-col">
                    <div className="col-label">ការបកប្រែដំបូង (Initial Translation)</div>
                    <div className="col-content text-initial">
                      {item.initial_translation}
                    </div>
                  </div>

                  {/* Column 3: Suggested Corrected Khmer */}
                  <div className="comparison-col suggested-col">
                    <div className="col-label">
                      <Sparkles size={11} style={{ color: 'var(--gold)' }} />
                      ការកែសម្រួលណែនាំ (Suggested Khmer)
                    </div>

                    {isEditing ? (
                      <div className="inline-edit-box">
                        <textarea
                          value={editingText}
                          onChange={(e) => setEditingText(e.target.value)}
                          className="inline-edit-textarea"
                          rows={2}
                          autoFocus
                        />
                        <div className="inline-edit-actions">
                          <button
                            type="button"
                            className="primary-btn"
                            style={{ padding: '4px 10px', fontSize: 11 }}
                            onClick={() => handleSaveEdit(item.segment_id)}
                          >
                            <Check size={12} /> រក្សាទុក
                          </button>
                          <button
                            type="button"
                            className="secondary-btn"
                            style={{ padding: '4px 10px', fontSize: 11 }}
                            onClick={() => setEditingSegmentId(null)}
                          >
                            <X size={12} /> បោះបង់
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="col-content text-suggested">
                        {item.diffs && item.diffs.length > 0 ? (
                          item.diffs.map((d, dIdx) => {
                            if (d.op === 'equal') {
                              return <span key={dIdx}>{d.text}</span>;
                            }
                            if (d.op === 'delete') {
                              return (
                                <del key={dIdx} className="diff-del">
                                  {d.text}
                                </del>
                              );
                            }
                            if (d.op === 'insert' || d.op === 'replace') {
                              return (
                                <mark key={dIdx} className="diff-ins">
                                  {d.text}
                                </mark>
                              );
                            }
                            return <span key={dIdx}>{d.text}</span>;
                          })
                        ) : (
                          item.suggested_khmer
                        )}
                      </div>
                    )}
                  </div>
                </div>

                {/* Explanation of Issues Detected */}
                {hasIssues && (
                  <div className="issues-explanation-list">
                    {item.issues.map((issue, idx) => (
                      <div key={idx} className="issue-item">
                        <span className={`issue-tag ${issue.type}`}>{issue.type}</span>
                        <span className="issue-reason">{issue.reason}</span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Card Action Buttons: Accept / Reject / Edit */}
                <div className="segment-card-footer">
                  <div className="segment-actions-left">
                    <button
                      type="button"
                      className="text-btn"
                      onClick={() => handleStartEdit(item)}
                    >
                      <Edit3 size={13} />
                      <span>កែសម្រួលដោយដៃ (Manual Edit)</span>
                    </button>
                  </div>

                  <div className="segment-actions-right">
                    <button
                      type="button"
                      className="secondary-btn"
                      style={{ padding: '6px 14px', fontSize: 12 }}
                      onClick={() => handleRejectSegment(item.segment_id)}
                    >
                      <X size={13} />
                      <span>បដិសេធ (Keep Initial)</span>
                    </button>
                    <button
                      type="button"
                      className="primary-btn"
                      style={{ padding: '6px 14px', fontSize: 12 }}
                      onClick={() => handleAcceptSegment(item.segment_id)}
                    >
                      <Check size={13} />
                      <span>យល់ព្រម (Accept Suggestion)</span>
                    </button>
                  </div>
                </div>
              </motion.div>
            );
          })
        )}
      </div>
    </div>
  );
};
