/**
 * MediaUploadProgressCard Component
 * 
 * Displays real-time dynamic internet-based media upload metrics:
 * - Real-time progress percentage (0 - 100%)
 * - Actual uploaded bytes / total bytes (MB / GB)
 * - Dynamic upload transfer speed (KB/s / MB/s)
 * - Dynamic ETA based on rolling window transfer measurements
 * - Smooth animated progress bar with Khmer gold styling
 * - Full controls: Pause, Resume, and Cancel
 * 
 * © 2026 Phengsovanreach. All rights reserved.
 */

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  CloudUpload,
  Pause,
  Play,
  X,
  RotateCcw,
  AlertTriangle,
  CheckCircle2,
  Loader2,
  HardDrive,
  Gauge,
  Clock,
  Activity,
  FileVideo,
} from 'lucide-react';
import { UploadProgressInfo } from '../services/mediaUploadService';

interface MediaUploadProgressCardProps {
  progress: UploadProgressInfo;
  filename: string;
  onPause: () => void;
  onResume: () => void;
  onCancel: () => void;
  onRetry?: () => void;
}

export const MediaUploadProgressCard: React.FC<MediaUploadProgressCardProps> = ({
  progress,
  filename,
  onPause,
  onResume,
  onCancel,
  onRetry,
}) => {
  const isUploading = progress.phase === 'uploading';
  const isPaused = progress.phase === 'paused';
  const isProcessing = progress.phase === 'processing';
  const isCompleted = progress.phase === 'completed';
  const isFailed = progress.phase === 'failed';
  const isPreparing = progress.phase === 'preparing';

  const getStatusBadge = () => {
    switch (progress.phase) {
      case 'uploading':
        return (
          <span className="upload-badge uploading">
            <span className="live-dot" /> Uploading (កំពុង Upload)
          </span>
        );
      case 'paused':
        return (
          <span className="upload-badge paused">
            <Pause size={11} /> Paused (បានផ្អាក)
          </span>
        );
      case 'processing':
        return (
          <span className="upload-badge processing">
            <Loader2 size={11} className="spin" /> Assembling (កំពុងផ្ទៀងផ្ទាត់)
          </span>
        );
      case 'completed':
        return (
          <span className="upload-badge completed">
            <CheckCircle2 size={11} /> Completed (ជោគជ័យ)
          </span>
        );
      case 'failed':
        return (
          <span className="upload-badge failed">
            <AlertTriangle size={11} /> Failed (បរាជ័យ)
          </span>
        );
      default:
        return (
          <span className="upload-badge preparing">
            <Loader2 size={11} className="spin" /> Preparing (រៀបចំ)
          </span>
        );
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 8, scale: 0.99 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -8, scale: 0.99 }}
      transition={{ duration: 0.22 }}
      className="media-upload-card"
    >
      {/* Header with Title and Status */}
      <div className="upload-card-header">
        <div className="upload-card-title-group">
          <div className="upload-card-icon">
            {isProcessing ? (
              <Loader2 size={22} className="spin" />
            ) : isCompleted ? (
              <CheckCircle2 size={22} />
            ) : (
              <CloudUpload size={22} />
            )}
          </div>
          <div>
            <h3 className="upload-main-title">
              {progress.statusKhmer || 'កំពុង Upload ឯកសារមេឌៀទៅកាន់ម៉ាស៊ីនបម្រើ...'}
            </h3>
            <div className="upload-file-meta">
              <FileVideo size={13} style={{ color: 'var(--gold)' }} />
              <b className="upload-filename-text" title={filename}>
                {filename}
              </b>
              <span className="upload-meta-dot">•</span>
              <span>{progress.formattedTotal}</span>
              {progress.totalChunks > 1 && (
                <>
                  <span className="upload-meta-dot">•</span>
                  <span>
                    Chunk {Math.min(progress.currentChunk, progress.totalChunks)} /{' '}
                    {progress.totalChunks}
                  </span>
                </>
              )}
            </div>
          </div>
        </div>

        <div className="upload-badge-wrapper">{getStatusBadge()}</div>
      </div>

      {/* Slow Connection / Unstable Warning */}
      <AnimatePresence>
        {progress.isSlow && isUploading && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="upload-slow-banner"
          >
            <AlertTriangle size={14} />
            <span>
              ល្បឿនអ៊ីនធឺណិតកំពុងយឺត ឬមានការប្រែប្រួល។ ប្រព័ន្ធ Chunked ធានាមិនបាត់បង់ទិន្នន័យឡើយ (Connection is slow; automatic chunk retry active).
            </span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Progress Bar with Floating Value */}
      <div className="upload-progress-section">
        <div className="upload-progress-label-row">
          <span className="upload-progress-percent">
            {progress.progressPercent.toFixed(1)}%
          </span>
          <span className="upload-bytes-counter">
            {progress.formattedUploaded} / {progress.formattedTotal}
          </span>
        </div>

        <div className="upload-progress-bar-track" role="progressbar" aria-valuenow={progress.progressPercent} aria-valuemin={0} aria-valuemax={100}>
          <motion.div
            className={`upload-progress-bar-fill ${progress.phase}`}
            animate={{ width: `${Math.min(100, Math.max(0, progress.progressPercent))}%` }}
            transition={{ ease: 'easeOut', duration: 0.2 }}
          />
        </div>
      </div>

      {/* Real-time 4-Metrics Grid */}
      <div className="upload-metrics-grid">
        {/* Metric 1: Progress */}
        <div className="upload-metric-box">
          <div className="metric-box-head">
            <Activity size={13} className="metric-icon gold" />
            <span>Progress (វឌ្ឍនភាព)</span>
          </div>
          <div className="metric-box-val">{progress.progressPercent.toFixed(0)}%</div>
          <small className="metric-box-sub">
            {isProcessing ? 'Verifying on server' : 'Transferred to server'}
          </small>
        </div>

        {/* Metric 2: Uploaded Size */}
        <div className="upload-metric-box">
          <div className="metric-box-head">
            <HardDrive size={13} className="metric-icon green" />
            <span>Uploaded (ទំហំបានបញ្ជូន)</span>
          </div>
          <div className="metric-box-val">{progress.formattedUploaded}</div>
          <small className="metric-box-sub">Of {progress.formattedTotal} total</small>
        </div>

        {/* Metric 3: Real Upload Speed */}
        <div className="upload-metric-box">
          <div className="metric-box-head">
            <Gauge size={13} className="metric-icon gold" />
            <span>Speed (ល្បឿនពិត)</span>
          </div>
          <div className="metric-box-val">{progress.formattedSpeed}</div>
          <small className="metric-box-sub">Measured transferred rate</small>
        </div>

        {/* Metric 4: Estimated Remaining Time (ETA) */}
        <div className="upload-metric-box">
          <div className="metric-box-head">
            <Clock size={13} className="metric-icon blue" />
            <span>Remaining (ពេលនៅសល់)</span>
          </div>
          <div className="metric-box-val eta" title={progress.formattedEta}>
            {progress.formattedEta.replace(/\(.*?\)/g, '').trim()}
          </div>
          <small className="metric-box-sub">Based on dynamic speed</small>
        </div>
      </div>

      {/* Error Message if Failed */}
      {isFailed && progress.error && (
        <div className="upload-error-box">
          <AlertTriangle size={15} style={{ flexShrink: 0 }} />
          <span>{progress.error}</span>
        </div>
      )}

      {/* Action Controls: Pause, Resume, Cancel, Retry */}
      <div className="upload-controls-row">
        <div className="upload-status-subtext">
          {isUploading && (
            <span>🚀 Dynamic chunk pipeline active (5 MB chunks with auto-resume)</span>
          )}
          {isPaused && (
            <span>⏸️ Upload is paused. Click Resume to continue from the last chunk.</span>
          )}
          {isProcessing && (
            <span>⚙️ Assembling media chunks and validating with FFprobe...</span>
          )}
          {isCompleted && (
            <span>✅ Upload successfully verified! Initializing transcription...</span>
          )}
          {isFailed && (
            <span>⚠️ An error occurred during upload. You can retry safely.</span>
          )}
        </div>

        <div className="upload-action-buttons">
          {/* Pause / Resume Controls */}
          {isUploading && (
            <button
              type="button"
              className="upload-action-btn pause"
              onClick={onPause}
              title="Pause upload"
            >
              <Pause size={14} /> ផ្អាក (Pause)
            </button>
          )}

          {isPaused && (
            <button
              type="button"
              className="upload-action-btn resume"
              onClick={onResume}
              title="Resume upload"
            >
              <Play size={14} /> បន្ត (Resume)
            </button>
          )}

          {/* Retry Control */}
          {isFailed && onRetry && (
            <button
              type="button"
              className="upload-action-btn retry"
              onClick={onRetry}
              title="Retry upload"
            >
              <RotateCcw size={14} /> ព្យាយាមម្តងទៀត (Retry)
            </button>
          )}

          {/* Cancel Control */}
          {(isUploading || isPaused || isPreparing || isFailed) && (
            <button
              type="button"
              className="upload-action-btn cancel"
              onClick={onCancel}
              title="Cancel and clean up upload"
            >
              <X size={14} /> បោះបង់ (Cancel)
            </button>
          )}
        </div>
      </div>
    </motion.div>
  );
};
