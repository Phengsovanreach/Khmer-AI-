import React, { useState } from 'react';
import {
  Settings2,
  Languages,
  Cpu,
  Volume2,
  Type,
  ShieldCheck,
  Trash2,
  Save,
  CheckCircle2,
  HardDrive,
  Info,
  BookOpen,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { AppSettings, Caps, COPYRIGHT_TEXT } from '../types';
import { HelpCenterStudio } from './HelpCenterStudio';
import { ContextualHelp } from './ContextualHelp';

interface SmartSettingsPanelProps {
  settings: AppSettings;
  onSaveSettings: (newSettings: AppSettings) => Promise<void>;
  caps: Caps | null;
  API: string;
  setNotice: (msg: string) => void;
  setError: (msg: string) => void;
  onOpenOnboarding?: () => void;
  initialTab?: 'settings' | 'help';
}

export const SmartSettingsPanel: React.FC<SmartSettingsPanelProps> = ({
  settings,
  onSaveSettings,
  caps,
  API,
  setNotice,
  setError,
  onOpenOnboarding = () => {},
  initialTab = 'settings',
}) => {
  const [activeTab, setActiveTab] = useState<'settings' | 'help'>(initialTab);
  const [form, setForm] = useState<AppSettings>({ ...settings });
  const [reducedMotion, setReducedMotion] = useState<boolean>(
    document.body.classList.contains('reduced-motion')
  );
  const [isSaving, setIsSaving] = useState(false);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await onSaveSettings(form);
      setNotice('បានរក្សាទុកការកំណត់ប្រព័ន្ធ (Settings saved successfully)!');
    } catch (err: any) {
      setError(`បរាជ័យក្នុងការរក្សាទុក Settings: ${err.message || err}`);
    } finally {
      setIsSaving(false);
    }
  };

  const toggleReducedMotion = (enabled: boolean) => {
    setReducedMotion(enabled);
    if (enabled) {
      document.body.classList.add('reduced-motion');
    } else {
      document.body.classList.remove('reduced-motion');
    }
  };

  const handleClearCache = () => {
    if (confirm('តើអ្នកចង់សម្អាត Cache និង Temporary Files មែនទេ? ឯកសារគម្រោងដើមនឹងមិនត្រូវបានលុបឡើយ។')) {
      setNotice('បានសម្អាត Cache និងទិន្នន័យបណ្តោះអាសន្នរួចរាល់!');
    }
  };

  return (
    <div style={{ marginTop: 14 }}>
      {/* Top Tab Bar inside Settings */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 10,
          flexWrap: 'wrap',
          marginBottom: 16,
          borderBottom: '1px solid var(--line)',
          paddingBottom: 10,
        }}
      >
        <button
          className={`secondary-btn ${activeTab === 'settings' ? 'active' : ''}`}
          onClick={() => setActiveTab('settings')}
          style={{
            background: activeTab === 'settings' ? 'var(--gold)' : 'var(--card)',
            color: activeTab === 'settings' ? '#1a1005' : 'var(--fg)',
            fontWeight: activeTab === 'settings' ? 600 : 400,
            fontSize: 13,
            padding: '8px 16px',
            border: `1px solid ${activeTab === 'settings' ? 'var(--gold)' : 'var(--line)'}`,
            borderRadius: 8,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: 8,
          }}
        >
          <Settings2 size={16} /> ការកំណត់ប្រព័ន្ធ & AI (Settings & Preferences)
        </button>

        <button
          className={`secondary-btn ${activeTab === 'help' ? 'active' : ''}`}
          onClick={() => setActiveTab('help')}
          style={{
            background: activeTab === 'help' ? 'var(--gold)' : 'var(--card)',
            color: activeTab === 'help' ? '#1a1005' : 'var(--fg)',
            fontWeight: activeTab === 'help' ? 600 : 400,
            fontSize: 13,
            padding: '8px 16px',
            border: `1px solid ${activeTab === 'help' ? 'var(--gold)' : 'var(--line)'}`,
            borderRadius: 8,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: 8,
          }}
        >
          <BookOpen size={16} /> មជ្ឈមណ្ឌលជំនួយ ១៥ ផ្នែក (Help & Support Center)
        </button>
      </div>

      {activeTab === 'help' ? (
        <HelpCenterStudio
          API={API}
          onOpenOnboarding={onOpenOnboarding}
          setNotice={setNotice}
          setError={setError}
        />
      ) : (
        <div className="settings-card">
          {/* Header */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 10 }}>
            <div>
              <h3 style={{ margin: '0 0 4px', fontSize: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
                <Settings2 size={20} style={{ color: 'var(--gold)' }} />
                Smart Settings & Preferences (ការកំណត់ប្រព័ន្ធឆ្លាតវៃ)
              </h3>
              <p style={{ margin: 0, fontSize: 12, color: 'var(--muted)' }}>
                កំណត់រចនាសម្ព័ន្ធភាសា គំរូ AI និងបង្កើនល្បឿនសម្រាប់កុំព្យូទ័រ RAM 3.3 - 4 GiB
              </p>
            </div>

            <button className="primary-btn" disabled={isSaving} onClick={handleSave}>
              <Save size={14} /> {isSaving ? 'Saving...' : 'Save Settings'}
            </button>
          </div>

          {/* Setting: UI Language */}
          <div className="settings-row">
            <div className="settings-info">
              <b>ភាសាបង្ហាញលើកម្មវិធី (UI Display Language)</b>
              <small>ជ្រើសរើសភាសាសម្រាប់ Menu និងប៊ូតុងបញ្ជា</small>
            </div>
            <select
              className="config-select"
              value={form.ui_language}
              onChange={(e) => setForm({ ...form, ui_language: e.target.value })}
            >
              <option value="km">ភាសាខ្មែរ (Khmer)</option>
              <option value="en">English (អង់គ្លេស)</option>
            </select>
          </div>

          {/* Setting: Default Source Language */}
          <div className="settings-row">
            <div className="settings-info">
              <div style={{ display: 'flex', alignItems: 'center' }}>
                <b>ភាសាដើមលំនាំដើម (Default Source Language)</b>
                <ContextualHelp topic="auto_detect" />
              </div>
              <small>ភាសានៃសំឡេងដើមក្នុងវីដេអូពេលបង្កើត Project ថ្មី</small>
            </div>
            <select
              className="config-select"
              value={form.default_source_lang || 'auto'}
              onChange={(e) => setForm({ ...form, default_source_lang: e.target.value })}
            >
              <option value="auto">🌐 ស្វែងរកស្វ័យប្រវត្តិ (Auto Detect)</option>
              <option value="en">🇺🇸 English</option>
              <option value="zh">🇨🇳 简体中文 (Chinese)</option>
              <option value="km">🇰🇭 ភាសាខ្មែរ (Khmer)</option>
              <option value="ja">🇯🇵 日本語 (Japanese)</option>
              <option value="ko">🇰🇷 한국어 (Korean)</option>
              <option value="vi">🇻🇳 Tiếng Việt</option>
              <option value="fr">🇫🇷 Français</option>
              <option value="es">🇪🇸 Español</option>
            </select>
          </div>

          {/* Setting: Default Target Language */}
          <div className="settings-row">
            <div className="settings-info">
              <div style={{ display: 'flex', alignItems: 'center' }}>
                <b>ភាសាគោលដៅលំនាំដើម (Default Target Translation Language)</b>
                <ContextualHelp topic="speech_separation" />
              </div>
              <small>ភាសាដែលត្រូវបកប្រែ និង Dubbing ពេលបង្កើត Project ថ្មី</small>
            </div>
            <select
              className="config-select"
              value={form.default_target_lang || 'km'}
              onChange={(e) => setForm({ ...form, default_target_lang: e.target.value })}
            >
              <option value="km">🇰🇭 ភាសាខ្មែរ (Khmer)</option>
              <option value="en">🇺🇸 English</option>
              <option value="zh">🇨🇳 简体中文 (Chinese)</option>
              <option value="ja">🇯🇵 日本語 (Japanese)</option>
              <option value="ko">🇰🇷 한국어 (Korean)</option>
              <option value="vi">🇻🇳 Tiếng Việt</option>
              <option value="fr">🇫🇷 Français</option>
              <option value="es">🇪🇸 Español</option>
            </select>
          </div>

          {/* Setting: Default Whisper Model */}
          <div className="settings-row">
            <div className="settings-info">
              <div style={{ display: 'flex', alignItems: 'center' }}>
                <b>គំរូស្គាល់សំឡេង AI លំនាំដើម (Default Whisper Model)</b>
                <ContextualHelp topic="diarization" />
              </div>
              <small>កុំព្យូទ័រ ASUS VivoBook X515MA (3.3 GiB RAM) ត្រូវបានណែនាំឱ្យប្រើ Tiny (~390MB)</small>
            </div>
            <select
              className="config-select"
              value={form.default_model}
              onChange={(e) => setForm({ ...form, default_model: e.target.value })}
            >
              <option value="tiny">Tiny (INT8 CPU · ~390MB RAM · លឿនបំផុត)</option>
              <option value="base">Base (INT8 CPU · ~500MB RAM · ត្រឹមត្រូវជាង)</option>
            </select>
          </div>

          {/* Setting: Default Khmer Neural Voice */}
          <div className="settings-row">
            <div className="settings-info">
              <div style={{ display: 'flex', alignItems: 'center' }}>
                <b>សំឡេងនិយាយខ្មែរ AI លំនាំដើម (Default Khmer TTS Voice)</b>
                <ContextualHelp topic="auto_voice" />
              </div>
              <small>សំឡេងបំប្លែងអត្ថបទទៅជាសំឡេងនិយាយបែបធម្មជាតិ</small>
            </div>
            <select
              className="config-select"
              value={form.default_tts_voice}
              onChange={(e) => setForm({ ...form, default_tts_voice: e.target.value })}
            >
              <option value="km-KH-PisethNeural">Piseth (សំឡេងបុរសខ្មែរ Neural)</option>
              <option value="km-KH-SreymomNeural">Sreymom (សំឡេងនារីខ្មែរ Neural)</option>
            </select>
          </div>

          {/* Setting: Subtitle Font Size */}
          <div className="settings-row">
            <div className="settings-info">
              <div style={{ display: 'flex', alignItems: 'center' }}>
                <b>ទំហំអក្សរ Subtitle លំនាំដើម (Default Subtitle Font Size)</b>
                <ContextualHelp topic="export_quality" />
              </div>
              <small>ទំហំអក្សរពេលដុត (Burn-in) ចូលក្នុងវីដេអូ MP4</small>
            </div>
            <select
              className="config-select"
              value={form.subtitle_font_size}
              onChange={(e) => setForm({ ...form, subtitle_font_size: e.target.value })}
            >
              <option value="small">Small (តូច · 18px)</option>
              <option value="medium">Medium (មធ្យម · 22px)</option>
              <option value="large">Large (ធំ · 26px)</option>
            </select>
          </div>

          {/* Setting: Cambodian Cultural Background */}
          <div className="settings-row">
            <div className="settings-info">
              <b>ផ្ទៃខាងក្រោយវប្បធម៌ខ្មែរ (Cambodian Cultural Background)</b>
              <small>ទេសភាពអង្គរវត្ត វាលស្រែ និងក្បាច់ផ្កាឈូកខ្មែរ (Angkor Wat, Rice Fields & Lotus Motifs)</small>
            </div>
            <select
              className="config-select"
              value={form.cultural_background_mode || 'subtle'}
              onChange={(e) => setForm({ ...form, cultural_background_mode: e.target.value as any })}
            >
              <option value="subtle">Subtle (ស្រទន់ · ណែនាំសម្រាប់ធ្វើការ)</option>
              <option value="vibrant">Vibrant (លេចធ្លោ · ទេសភាពច្បាស់)</option>
              <option value="minimal">Minimal (តិចតួច · ស្រាលបំផុត)</option>
              <option value="disabled">Disabled (បិទ · គ្មានរូបភាព)</option>
            </select>
          </div>

          {/* Setting: Khmer Celestial Angel (Devata) */}
          <div className="settings-row">
            <div className="settings-info">
              <b>ទេវតាខ្មែរបាចផ្កា (Khmer Celestial Angel / Devata)</b>
              <small>បង្ហាញរូបទេវតាបាចត្របកផ្កាឈូក និងផ្កាម្លិះនៅជ្រុងខាងឆ្វេងក្រោម</small>
            </div>
            <input
              type="checkbox"
              checked={form.show_celestial_angel !== false}
              onChange={(e) => setForm({ ...form, show_celestial_angel: e.target.checked })}
              style={{ width: 18, height: 18, cursor: 'pointer' }}
            />
          </div>

          {/* Setting: Reduced Motion */}
          <div className="settings-row">
            <div className="settings-info">
              <b>កាត់បន្ថយចលនា Animation (Reduced Motion)</b>
              <small>បិទចលនាធ្ងន់ៗដើម្បីសន្សំធនធាន CPU និង RAM លើម៉ាស៊ីនខ្សោយ</small>
            </div>
            <input
              type="checkbox"
              checked={reducedMotion}
              onChange={(e) => toggleReducedMotion(e.target.checked)}
              style={{ width: 18, height: 18, cursor: 'pointer' }}
            />
          </div>

          {/* Cache & Temporary Cleanup */}
          <div className="settings-row">
            <div className="settings-info">
              <b>សម្អាតឯកសារបណ្តោះអាសន្ន (Cache & Temporary Media Cleanup)</b>
              <small>លុបឯកសារបណ្តោះអាសន្ន wav, temporary subtitle buffers ដើម្បីបង្កើនទំហំ Hard Disk</small>
            </div>
            <button className="secondary-btn" onClick={handleClearCache}>
              <Trash2 size={13} style={{ color: 'var(--gold)' }} /> សម្អាត Cache ឥឡូវនេះ
            </button>
          </div>

          {/* System & Hardware Health Banner */}
          <div style={{ background: 'var(--card)', border: '1px solid var(--line)', borderRadius: 8, padding: 14 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
              <Cpu size={16} style={{ color: 'var(--green)' }} />
              <b style={{ fontSize: 13 }}>Low-Memory Optimization Status</b>
            </div>
            <p style={{ margin: 0, fontSize: 11, color: 'var(--muted)', lineHeight: 1.6 }}>
              ✓ faster-whisper INT8 CPU quantization ត្រូវបានបើកដំណើរការដោយស្វ័យប្រវត្តិ។<br />
              ✓ Zero Ollama dependency — មិនប្រើប្រាស់ Ollama ឬ GPU ធ្ងន់ៗឡើយ។<br />
              ✓ Single concurrency job lock — ការពារម៉ាស៊ីនមិនឱ្យគាំងដោយសារការ Process ច្រើនដំណាលគ្នា។
            </p>
          </div>

          {/* About & Copyright */}
          <div style={{ borderTop: '1px solid var(--line)', paddingTop: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 10 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <img src="/logo.png" alt="Logo" style={{ width: 22, height: 22, objectFit: 'contain' }} />
              <span style={{ fontSize: 12, fontWeight: 600 }}>Khmer Translator 2.0</span>
            </div>
            <span className="footer-copyright">{COPYRIGHT_TEXT}</span>
          </div>
        </div>
      )}
    </div>
  );
};
