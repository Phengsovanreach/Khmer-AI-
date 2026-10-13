import React, { useState, useEffect } from 'react';
import {
  BookOpen,
  Check,
  Edit2,
  FileText,
  Loader2,
  Plus,
  RefreshCw,
  Search,
  Sparkles,
  Tag,
  Trash2,
  Volume2,
  X,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { DictionaryEntry } from '../types';

interface PronunciationDictionaryStudioProps {
  API: string;
  setNotice: (msg: string) => void;
  setError: (msg: string) => void;
}

export const PronunciationDictionaryStudio: React.FC<PronunciationDictionaryStudioProps> = ({
  API,
  setNotice,
  setError,
}) => {
  const [entries, setEntries] = useState<DictionaryEntry[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(search);
    }, 200);
    return () => clearTimeout(timer);
  }, [search]);

  // Form modal state
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingEntry, setEditingEntry] = useState<DictionaryEntry | null>(null);
  const [formTerm, setFormTerm] = useState('');
  const [formReplacement, setFormReplacement] = useState('');
  const [formCategory, setFormCategory] = useState('tech');
  const [formNotes, setFormNotes] = useState('');
  const [formCaseSensitive, setFormCaseSensitive] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  // Audio preview state
  const [playingTerm, setPlayingTerm] = useState<string | null>(null);

  const fetchEntries = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API}/api/dictionary`);
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to load dictionary');
      setEntries(data.entries || []);
    } catch (err: any) {
      setError(err.message || 'Failed to load dictionary');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void fetchEntries();
  }, []);

  const handleOpenAdd = () => {
    setEditingEntry(null);
    setFormTerm('');
    setFormReplacement('');
    setFormCategory('tech');
    setFormNotes('');
    setFormCaseSensitive(false);
    setShowAddModal(true);
  };

  const handleOpenEdit = (entry: DictionaryEntry) => {
    setEditingEntry(entry);
    setFormTerm(entry.term);
    setFormReplacement(entry.replacement);
    setFormCategory(entry.category || 'general');
    setFormNotes(entry.notes || '');
    setFormCaseSensitive(Boolean(entry.case_sensitive));
    setShowAddModal(true);
  };

  const handleSaveEntry = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formTerm.trim() || !formReplacement.trim()) {
      setError('សូមបំពេញពាក្យដើម និងពាក្យខ្មែរជំនួសឱ្យបានត្រឹមត្រូវ។');
      return;
    }

    setIsSaving(true);
    try {
      const res = await fetch(`${API}/api/dictionary`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          term: formTerm.trim(),
          replacement: formReplacement.trim(),
          category: formCategory,
          notes: formNotes.trim(),
          case_sensitive: formCaseSensitive,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Save failed');

      setNotice(`បានរក្សាទុកពាក្យ "${data.term}" ក្នុងវចនានុក្រមដោយជោគជ័យ!`);
      setShowAddModal(false);
      await fetchEntries();
    } catch (err: any) {
      setError(err.message || 'Failed to save entry');
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeleteEntry = async (term: string) => {
    if (!window.confirm(`តើអ្នកពិតជាចង់លុបពាក្យ "${term}" ចេញពីវចនានុក្រមមែនទេ?`)) return;

    try {
      const res = await fetch(`${API}/api/dictionary/${encodeURIComponent(term)}`, {
        method: 'DELETE',
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Delete failed');

      setNotice(`បានលុបពាក្យ "${term}" រួចរាល់។`);
      await fetchEntries();
    } catch (err: any) {
      setError(err.message || 'Failed to delete entry');
    }
  };

  const handlePlayAudio = async (replacement: string, term: string) => {
    if (!replacement.trim() || playingTerm === term) return;
    setPlayingTerm(term);
    try {
      const res = await fetch(`${API}/api/dubbing/segment-sample`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: replacement,
          voice_id: 'km-KH-PisethNeural',
          emotion: 'neutral',
        }),
      });
      if (!res.ok) throw new Error('Audio generation failed');
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audio.onended = () => {
        setPlayingTerm(null);
        URL.revokeObjectURL(url);
      };
      audio.onerror = () => {
        setPlayingTerm(null);
        URL.revokeObjectURL(url);
      };
      await audio.play();
    } catch (err) {
      setPlayingTerm(null);
    }
  };

  // Filter entries
  const query = debouncedSearch.trim().toLowerCase();
  const filteredEntries = entries.filter((e) => {
    const matchSearch =
      !query ||
      e.term.toLowerCase().includes(query) ||
      e.replacement.toLowerCase().includes(query) ||
      (e.notes && e.notes.toLowerCase().includes(query));

    const matchCategory = selectedCategory === 'all' || e.category === selectedCategory;
    return matchSearch && matchCategory;
  });

  return (
    <div className="dictionary-studio-root">
      {/* Header */}
      <div className="proofread-header-card">
        <div className="proofread-header-top">
          <div className="proofread-brand-info">
            <div className="proofread-icon-box gold">
              <BookOpen size={24} />
            </div>
            <div>
              <h3>Custom Pronunciation & Terminology Dictionary</h3>
              <p>គ្រប់គ្រងពាក្យបច្ចេកទេស ឈ្មោះតួអង្គ និងការបញ្ចេញសំឡេងខ្មែរតាមតម្រូវការ</p>
            </div>
          </div>

          <div className="proofread-top-actions">
            <button
              type="button"
              className="secondary-btn"
              onClick={fetchEntries}
              disabled={isLoading}
            >
              {isLoading ? <Loader2 size={14} className="spin" /> : <RefreshCw size={14} />}
              <span>ផ្ទុកឡើងវិញ</span>
            </button>
            <button
              type="button"
              className="primary-btn"
              onClick={handleOpenAdd}
            >
              <Plus size={15} />
              <span>បន្ថែមពាក្យថ្មី (Add Term)</span>
            </button>
          </div>
        </div>
      </div>

      {/* Search & Category Filter */}
      <div className="dictionary-filter-bar">
        <div className="search-input-wrapper">
          <Search size={15} className="search-icon" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="ស្វែងរកពាក្យដើម ពាក្យខ្មែរ ឬកំណត់ចំណាំ..."
            className="search-input"
          />
          {search && (
            <button type="button" className="clear-btn" onClick={() => setSearch('')}>
              <X size={13} />
            </button>
          )}
        </div>

        <div className="category-chips">
          {['all', 'tech', 'media', 'brand', 'culture', 'spelling', 'courtesy', 'general'].map((cat) => (
            <button
              key={cat}
              type="button"
              className={`category-chip ${selectedCategory === cat ? 'active' : ''}`}
              onClick={() => setSelectedCategory(cat)}
            >
              {cat.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* Dictionary Entries Grid */}
      <div className="dictionary-grid">
        {filteredEntries.length === 0 ? (
          <div className="proofread-empty-card" style={{ gridColumn: '1 / -1' }}>
            <BookOpen size={36} style={{ color: 'var(--muted)', marginBottom: 12 }} />
            <h4>រកមិនឃើញពាក្យក្នុងវចនានុក្រមទេ</h4>
            <p>សូមព្យាយាមស្វែងរកពាក្យផ្សេង ឬចុច "បន្ថែមពាក្យថ្មី" ដើម្បីបង្កើត override ផ្ទាល់ខ្លួន។</p>
          </div>
        ) : (
          filteredEntries.map((item) => {
            const isPlaying = playingTerm === item.term;

            return (
              <motion.div
                key={item.term}
                layout
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                className="dict-card"
              >
                <div className="dict-card-top">
                  <span className={`dict-category-badge ${item.category}`}>
                    <Tag size={10} /> {item.category || 'general'}
                  </span>
                  <div className="dict-actions">
                    <button
                      type="button"
                      className="icon-btn-sm"
                      onClick={() => handlePlayAudio(item.replacement, item.term)}
                      title="Audition spoken pronunciation"
                    >
                      {isPlaying ? <Loader2 size={13} className="spin" /> : <Volume2 size={13} />}
                    </button>
                    <button
                      type="button"
                      className="icon-btn-sm"
                      onClick={() => handleOpenEdit(item)}
                      title="Edit term"
                    >
                      <Edit2 size={13} />
                    </button>
                    <button
                      type="button"
                      className="icon-btn-sm danger"
                      onClick={() => handleDeleteEntry(item.term)}
                      title="Delete term"
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>
                </div>

                <div className="dict-terms-row">
                  <div className="dict-original-term">
                    <span className="dict-label">ពាក្យដើម (Original):</span>
                    <b>{item.term}</b>
                  </div>
                  <span className="dict-arrow">➔</span>
                  <div className="dict-replacement-term">
                    <span className="dict-label">ពាក្យខ្មែរ (Pronounced):</span>
                    <b style={{ color: 'var(--gold)' }}>{item.replacement}</b>
                  </div>
                </div>

                {item.notes && (
                  <div className="dict-notes">
                    <span className="text-xs text-muted">{item.notes}</span>
                  </div>
                )}
              </motion.div>
            );
          })
        )}
      </div>

      {/* Add / Edit Term Modal */}
      <AnimatePresence>
        {showAddModal && (
          <div className="modal-backdrop" onClick={() => setShowAddModal(false)}>
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 10 }}
              className="modal-content"
              style={{ maxWidth: 480 }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="modal-header">
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <div className="title-icon gold" style={{ width: 32, height: 32 }}>
                    <BookOpen size={16} />
                  </div>
                  <b>{editingEntry ? 'កែសម្រួលពាក្យវចនានុក្រម' : 'បន្ថែមពាក្យថ្មីក្នុងវចនានុក្រម'}</b>
                </div>
                <button
                  type="button"
                  className="icon-btn-sm"
                  onClick={() => setShowAddModal(false)}
                >
                  <X size={15} />
                </button>
              </div>

              <form onSubmit={handleSaveEntry} className="modal-form">
                <div className="form-field">
                  <label>ពាក្យដើម ឬពាក្យបរទេស (Original Term):</label>
                  <input
                    type="text"
                    required
                    value={formTerm}
                    onChange={(e) => setFormTerm(e.target.value)}
                    placeholder="ឧទាហរណ៍: AI, Video, YouTube, Character..."
                    className="config-input"
                  />
                </div>

                <div className="form-field">
                  <label>ពាក្យខ្មែរត្រឹមត្រូវ ឬសំឡេងបញ្ចេញ (Khmer Replacement):</label>
                  <input
                    type="text"
                    required
                    value={formReplacement}
                    onChange={(e) => setFormReplacement(e.target.value)}
                    placeholder="ឧទាហរណ៍: បញ្ញាសិប្បនិម្មិត, វីដេអូ, យូធូប..."
                    className="config-input"
                  />
                </div>

                <div className="form-grid-2">
                  <div className="form-field">
                    <label>ប្រភេទពាក្យ (Category):</label>
                    <select
                      value={formCategory}
                      onChange={(e) => setFormCategory(e.target.value)}
                      className="config-select"
                    >
                      <option value="tech">បច្ចេកវិទ្យា (Technology)</option>
                      <option value="media">ប្រព័ន្ធផ្សព្វផ្សាយ (Media)</option>
                      <option value="brand">ម៉ាកយីហោ (Brand / Platform)</option>
                      <option value="culture">វប្បធម៌-ភូមិសាស្ត្រ (Culture)</option>
                      <option value="spelling">អក្ខរាវិរុទ្ធ (Spelling)</option>
                      <option value="courtesy">ការគួរសម (Courtesy)</option>
                      <option value="general">ទូទៅ (General)</option>
                    </select>
                  </div>

                  <div className="form-field" style={{ display: 'flex', alignItems: 'center', marginTop: 24 }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: 12 }}>
                      <input
                        type="checkbox"
                        checked={formCaseSensitive}
                        onChange={(e) => setFormCaseSensitive(e.target.checked)}
                      />
                      <span>Case Sensitive (ប្រកាន់តួអក្សរ)</span>
                    </label>
                  </div>
                </div>

                <div className="form-field">
                  <label>កំណត់ចំណាំ / បរិបទ (Notes - Optional):</label>
                  <input
                    type="text"
                    value={formNotes}
                    onChange={(e) => setFormNotes(e.target.value)}
                    placeholder="បញ្ជាក់ពីអត្ថន័យ ឬតួអង្គដែលត្រូវប្រើ..."
                    className="config-input"
                  />
                </div>

                <div className="modal-actions">
                  <button
                    type="button"
                    className="secondary-btn"
                    onClick={() => setShowAddModal(false)}
                  >
                    បោះបង់
                  </button>
                  <button
                    type="submit"
                    className="primary-btn"
                    disabled={isSaving}
                  >
                    {isSaving ? <Loader2 size={15} className="spin" /> : <Check size={15} />}
                    <span>{editingEntry ? 'ធ្វើបច្ចុប្បន្នភាព' : 'រក្សាទុក'}</span>
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};
