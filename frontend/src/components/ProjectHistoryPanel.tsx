import React, { useState } from 'react';
import {
  Search,
  FolderOpen,
  Calendar,
  Clock,
  Subtitles,
  Film,
  AudioLines,
  Trash2,
  Edit2,
  Check,
  X,
  Play,
  ArrowUpDown,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Job, fmtTime, COPYRIGHT_TEXT } from '../types';
import { CambodianCulturalBackground } from './CambodianCulturalBackground';

interface ProjectHistoryPanelProps {
  jobs: Job[];
  active: Job | null;
  onSelectJob: (job: Job) => void;
  onRenameJob: (jobId: string, newName: string) => Promise<void>;
  onDeleteJob: (jobId: string) => Promise<void>;
  onOpenPreview: (job: Job) => void;
}

export const ProjectHistoryPanel: React.FC<ProjectHistoryPanelProps> = ({
  jobs,
  active,
  onSelectJob,
  onRenameJob,
  onDeleteJob,
  onOpenPreview,
}) => {
  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState<'date_desc' | 'date_asc' | 'duration'>('date_desc');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingName, setEditingName] = useState<string>('');

  // Delete modal confirmation state
  const [deleteTarget, setDeleteTarget] = useState<Job | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const startRename = (j: Job) => {
    setEditingId(j.id);
    setEditingName(j.name || j.filename.replace(/\.[^/.]+$/, ''));
  };

  const saveRename = async (jobId: string) => {
    if (editingName.trim()) {
      await onRenameJob(jobId, editingName.trim());
    }
    setEditingId(null);
  };

  // Filter & Sort
  const filtered = jobs
    .filter((j) => {
      const q = search.toLowerCase();
      const name = (j.name || '').toLowerCase();
      const fn = j.filename.toLowerCase();
      return name.includes(q) || fn.includes(q);
    })
    .sort((a, b) => {
      if (sortBy === 'duration') return (b.duration_seconds || 0) - (a.duration_seconds || 0);
      if (sortBy === 'date_asc') return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
    });

  return (
    <div style={{ marginTop: 10 }}>
      {/* Top Search & Filter Bar */}
      <div className="subtitle-pro-toolbar">
        <div className="subtitle-search-box">
          <Search size={14} style={{ color: 'var(--muted)' }} />
          <input
            type="text"
            className="subtitle-search-input"
            placeholder="ស្វែងរកតាមឈ្មោះគម្រោង ឬឯកសារ (Search projects)..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          {search && (
            <span style={{ fontSize: 10, color: 'var(--gold)' }}>
              {filtered.length} found
            </span>
          )}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 11, color: 'var(--muted)', display: 'flex', alignItems: 'center', gap: 4 }}>
            <ArrowUpDown size={12} /> តម្រៀបតាម:
          </span>
          <select
            className="config-select"
            style={{ padding: '4px 8px', fontSize: 11 }}
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
          >
            <option value="date_desc">ថ្មីបំផុតមុន (Newest First)</option>
            <option value="date_asc">ចាស់បំផុតមុន (Oldest First)</option>
            <option value="duration">ថិរវេលាវីដេអូ (Longest Duration)</option>
          </select>
        </div>
      </div>

      {/* Projects Grid */}
      {filtered.length === 0 ? (
        <CambodianCulturalBackground variant="empty-state" />
      ) : (
        <div className="project-history-grid">
          {filtered.map((j) => {
            const isActive = active?.id === j.id;
            const isEditing = editingId === j.id;
            const displayName = j.name || j.filename.replace(/\.[^/.]+$/, '');

            return (
              <motion.div
                layout
                key={j.id}
                className={`project-card ${isActive ? 'active' : ''}`}
                style={{
                  borderLeft: isActive ? '4px solid var(--gold)' : undefined,
                }}
              >
                {/* Header */}
                <div className="project-card-header">
                  {isEditing ? (
                    <div style={{ display: 'flex', alignItems: 'center', gap: 4, width: '100%' }}>
                      <input
                        type="text"
                        className="config-input"
                        value={editingName}
                        onChange={(e) => setEditingName(e.target.value)}
                        style={{ fontSize: 13, padding: '3px 6px', flex: 1 }}
                        autoFocus
                      />
                      <button className="icon-btn" onClick={() => saveRename(j.id)} title="Save name">
                        <Check size={14} style={{ color: 'var(--green)' }} />
                      </button>
                      <button className="icon-btn" onClick={() => setEditingId(null)} title="Cancel">
                        <X size={14} />
                      </button>
                    </div>
                  ) : (
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, flex: 1 }}>
                      <span className="project-card-title">{displayName}</span>
                      <button
                        className="icon-btn"
                        style={{ opacity: 0.6 }}
                        onClick={() => startRename(j)}
                        title="Rename Project"
                      >
                        <Edit2 size={12} />
                      </button>
                    </div>
                  )}

                  <span className={`badge-pill ${j.status === 'transcribed' ? 'success' : j.status === 'failed' ? 'danger' : 'warning'}`}>
                    {j.status}
                  </span>
                </div>

                {/* Meta details */}
                <div className="project-card-meta">
                  <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                    <Clock size={11} /> {fmtTime(j.duration_seconds)}
                  </span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                    <Subtitles size={11} /> {j.transcript.length} lines
                  </span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                    <Calendar size={11} /> {new Date(j.created_at).toLocaleDateString()}
                  </span>
                </div>

                {/* Feature Badges */}
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                  {j.has_rendered_video && (
                    <span className="tag tag-ready" style={{ fontSize: 9 }}>
                      <Film size={10} /> Rendered MP4
                    </span>
                  )}
                  {j.has_dubbed_audio && (
                    <span className="tag tag-ready" style={{ fontSize: 9, background: 'rgba(217, 181, 109, 0.14)', color: 'var(--gold)' }}>
                      <AudioLines size={10} /> Dubbed Track
                    </span>
                  )}
                </div>

                {/* Actions */}
                <div className="project-card-actions">
                  <button
                    className="primary-btn"
                    style={{ padding: '4px 10px', fontSize: 11, flex: 1 }}
                    onClick={() => onSelectJob(j)}
                  >
                    Open Workspace
                  </button>

                  <button
                    className="secondary-btn"
                    style={{ padding: '4px 8px', fontSize: 11 }}
                    onClick={() => onOpenPreview(j)}
                    title="Preview Video & Subtitles"
                  >
                    <Play size={12} /> Preview
                  </button>

                  <button
                    className="icon-btn"
                    style={{ color: '#ea8282' }}
                    onClick={() => setDeleteTarget(j)}
                    title="Delete Project"
                  >
                    <Trash2 size={13} />
                  </button>
                </div>
              </motion.div>
            );
          })}
        </div>
      )}

      {/* Delete Confirmation Modal */}
      <AnimatePresence>
        {deleteTarget && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="modal-overlay"
            onClick={() => setDeleteTarget(null)}
          >
            <motion.div
              initial={{ scale: 0.95, y: 10 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.95, y: 10 }}
              className="modal-box"
              style={{ maxWidth: 420 }}
              onClick={(e) => e.stopPropagation()}
            >
              <h3 style={{ margin: '0 0 10px', fontSize: 16, color: '#ea8282', display: 'flex', alignItems: 'center', gap: 8 }}>
                <Trash2 size={18} /> បញ្ជាក់ការលុបគម្រោង (Confirm Deletion)
              </h3>
              <p style={{ fontSize: 12, lineHeight: 1.6, color: 'var(--text)' }}>
                តើអ្នកពិតជាចង់លុបគម្រោង <b>"{deleteTarget.name || deleteTarget.filename}"</b> នេះមែនទេ?
                រាល់ Subtitle, Dubbing track, និងវីដេអូដែលបាន Export នឹងត្រូវលុបចេញពីប្រព័ន្ធ។
              </p>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 16 }}>
                <button className="secondary-btn" onClick={() => setDeleteTarget(null)}>
                  បោះបង់ (Cancel)
                </button>
                <button
                  className="primary-btn"
                  style={{ background: '#ea8282', color: '#fff' }}
                  disabled={isDeleting}
                  onClick={async () => {
                    setIsDeleting(true);
                    await onDeleteJob(deleteTarget.id);
                    setIsDeleting(false);
                    setDeleteTarget(null);
                  }}
                >
                  {isDeleting ? 'កំពុងលុប...' : 'លុបជាអចិន្ត្រៃយ៍ (Delete)'}
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <div style={{ marginTop: 24, display: 'flex', justifyContent: 'flex-end' }}>
        <span className="footer-copyright">{COPYRIGHT_TEXT}</span>
      </div>
    </div>
  );
};
