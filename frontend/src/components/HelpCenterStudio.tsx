import React, { useState, useMemo } from 'react';
import {
  BookOpen,
  Search,
  CheckCircle2,
  Sparkles,
  Clapperboard,
  Languages,
  Users,
  Music,
  Film,
  FileCheck2,
  FolderOpen,
  AlertTriangle,
  HelpCircle,
  Cpu,
  ShieldCheck,
  LifeBuoy,
  Info,
  Copy,
  ChevronDown,
  ChevronRight,
  ExternalLink,
  Volume2,
  RefreshCw,
  X,
  Play,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { COPYRIGHT_TEXT, TELEGRAM_SUPPORT } from '../types';

export const TelegramIcon: React.FC<{ size?: number }> = ({ size = 18 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ flexShrink: 0 }}>
    <circle cx="12" cy="12" r="12" fill="#229ED9" />
    <path d="M17.5 7.2L5.8 11.7C5.0 12.0 5.0 12.5 5.7 12.7L8.7 13.6L15.6 9.3C15.9 9.1 16.2 9.2 16.0 9.4L10.4 14.4L10.2 17.5C10.5 17.5 10.6 17.4 10.8 17.2L12.5 15.6L16.0 18.2C16.6 18.5 17.1 18.3 17.3 17.6L19.2 8.5C19.4 7.6 18.9 7.2 17.5 7.2Z" fill="white" />
  </svg>
);

interface HelpCenterStudioProps {
  API: string;
  onOpenOnboarding: () => void;
  setNotice: (msg: string) => void;
  setError: (msg: string) => void;
}

interface ArticleSection {
  id: string;
  category: string;
  titleKhmer: string;
  titleEnglish: string;
  icon: any;
  contentKhmer: React.ReactNode;
  contentEnglish?: React.ReactNode;
  keywords: string[];
}

export const HelpCenterStudio: React.FC<HelpCenterStudioProps> = ({
  API,
  onOpenOnboarding,
  setNotice,
  setError,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [activeSectionId, setActiveSectionId] = useState<string>('getting-started');
  const [expandedFaqIndex, setExpandedFaqIndex] = useState<number | null>(null);
  const [copiedDiag, setCopiedDiag] = useState(false);
  const [isCopying, setIsCopying] = useState(false);

  // Diagnostic Data Collector
  const handleCopyDiagnostics = async () => {
    setIsCopying(true);
    try {
      let diagData: any = null;
      try {
        const res = await fetch(`${API}/api/system/diagnostics`);
        if (res.ok) {
          diagData = await res.json();
        }
      } catch (_) {
        // Fallback to local client diagnostics if backend offline
      }

      const clientInfo = {
        app_name: 'Khmer Translator',
        app_version: '2.0.0',
        timestamp: new Date().toISOString(),
        user_agent: navigator.userAgent,
        screen_resolution: `${window.screen.width}x${window.screen.height}`,
        client_language: navigator.language,
        backend_api: API,
        backend_diagnostics: diagData || 'Backend unreachable',
        copyright: COPYRIGHT_TEXT,
      };

      const jsonStr = JSON.stringify(clientInfo, null, 2);
      await navigator.clipboard.writeText(jsonStr);
      setCopiedDiag(true);
      setNotice('បានចម្លងព័ត៌មានវិនិច្ឆ័យប្រព័ន្ធ (Diagnostics copied to clipboard)!');
      setTimeout(() => setCopiedDiag(false), 3000);
    } catch (err: any) {
      setError(`បរាជ័យក្នុងការចម្លង Diagnostics: ${err.message || err}`);
    } finally {
      setIsCopying(false);
    }
  };

  const categories = [
    { id: 'all', labelKhmer: 'ទាំងអស់ (All)' },
    { id: 'guides', labelKhmer: '📖 សៀវភៅណែនាំ (Guides)' },
    { id: 'audio', labelKhmer: '🎧 សំឡេង & តន្ត្រី (Audio & SFX)' },
    { id: 'subtitles', labelKhmer: '✏️ អត្ថបទ & បកប្រែ (Subtitles)' },
    { id: 'troubleshoot', labelKhmer: '🛠️ ដោះស្រាយបញ្ហា (Troubleshoot)' },
    { id: 'system', labelKhmer: '💻 ប្រព័ន្ធ & សុវត្ថិភាព (System)' },
  ];

  // 15 Comprehensive Sections
  const sections: ArticleSection[] = useMemo(
    () => [
      // 1. Getting Started
      {
        id: 'getting-started',
        category: 'guides',
        titleKhmer: '១. ចាប់ផ្តើមដំបូង (Getting Started)',
        titleEnglish: '1. Getting Started with Khmer Translator',
        icon: Sparkles,
        keywords: ['start', 'beginner', 'quick', 'intro', 'ចាប់ផ្តើម', 'ដំបូង', 'welcome'],
        contentKhmer: (
          <div>
            <p style={{ lineHeight: 1.7, fontSize: 13.5 }}>
              Khmer Translator គឺជាកម្មវិធីបកប្រែវីដេអូ និងបញ្ចូលសំឡេងនិយាយឆ្លាតវៃ (AI Dubbing)
              ដែលដំណើរការលើកុំព្យូទ័រផ្ទាល់ (Local AI) ដោយមិនទាមទារ Ollama ឬកាតក្រាហ្វិកថ្លៃៗឡើយ។
            </p>
            <div
              style={{
                background: 'rgba(217,168,76,0.08)',
                borderLeft: '3px solid var(--gold)',
                padding: '12px 14px',
                borderRadius: 6,
                margin: '14px 0',
              }}
            >
              <b style={{ color: 'var(--gold)', fontSize: 13 }}>💡 ដំណើរការរហ័សក្នុងរយៈពេល ៣ ជំហាន (Quick 3-Minute Start)៖</b>
              <ol style={{ margin: '8px 0 0', paddingLeft: 20, fontSize: 12.5, lineHeight: 1.7 }}>
                <li><b>ទម្លាក់វីដេអូ៖</b> ជ្រើសរើសឯកសារ MP4, MKV ឬ WebM ក្នុងផ្ទាំង Workspace។</li>
                <li><b>ជ្រើសរើសភាសា៖</b> ភាសាដើម (Auto Detect) និងភាសាគោលដៅ (ភាសាខ្មែរ km)។</li>
                <li><b>ចុច Translate & Dub៖</b> ប្រព័ន្ធដំណើរការស្វ័យប្រវត្តិតាំងពីស្គាល់សំឡេង បកប្រែ ដល់បញ្ចូលសំឡេងនិយាយ!</li>
              </ol>
            </div>
            <button
              className="secondary-btn"
              onClick={onOpenOnboarding}
              style={{ marginTop: 8, fontSize: 12 }}
            >
              <Play size={13} style={{ color: 'var(--gold)' }} /> បើកការណែនាំអន្តរកម្មឡើងវិញ (Launch Interactive Onboarding)
            </button>
          </div>
        ),
      },

      // 2. Step-by-Step User Guide
      {
        id: 'step-by-step',
        category: 'guides',
        titleKhmer: '២. ជំហានលម្អិតតាមលំដាប់ (Step-by-Step User Guide)',
        titleEnglish: '2. Complete End-to-End Workflow',
        icon: Clapperboard,
        keywords: ['step', 'guide', 'workflow', 'លំដាប់', 'ជំហាន', 'pipeline', 'stages'],
        contentKhmer: (
          <div>
            <p style={{ lineHeight: 1.7, fontSize: 13 }}>
              ដំណាក់កាលដំណើរការជាក់ស្តែងទាំង ៨ របស់ម៉ាស៊ីន (Real 8-Stage Processing Pipeline)៖
            </p>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 10, margin: '14px 0' }}>
              {[
                { stage: '1. Validating', desc: 'ពិនិត្យ Container, Codec និង Audio Stream ជាមួយ FFprobe' },
                { stage: '2. Audio Extraction', desc: 'ស្រង់សំឡេងជា 16kHz PCM Mono សម្រាប់ Whisper' },
                { stage: '3. Transcription', desc: 'AI Faster-Whisper (INT8 CPU) ស្គាល់សំឡេង និងកំណត់ត្រាពេលវេលា' },
                { stage: '4. Diarization', desc: 'វិភាគតួអង្គនិយាយ (Speaker 1, 2) និងបែងចែកភេទ/អាយុ' },
                { stage: '5. Subtitles', desc: 'បង្កើត SRT, WebVTT និងទម្រង់អត្ថបទដើម' },
                { stage: '6. Translation', desc: 'បកប្រែជាភាសាខ្មែរ ឬភាសាគោលដៅដោយរក្សាអត្ថន័យសាច់រឿង' },
                { stage: '7. Neural Dubbing', desc: 'សំយោគសំឡេង Piseth/Sreymom និងរៀបចំលើ Timeline' },
                { stage: '8. Sound Mixing & Export', desc: 'រក្សាតន្ត្រីកំដរ/SFX ជាមួយ Sidechain Ducking និង Render MP4' },
              ].map((s, idx) => (
                <div key={idx} style={{ background: 'var(--card)', border: '1px solid var(--line)', borderRadius: 8, padding: '10px 12px' }}>
                  <b style={{ color: 'var(--gold)', fontSize: 12.5 }}>{s.stage}</b>
                  <p style={{ margin: '4px 0 0', fontSize: 11.5, color: 'var(--muted)' }}>{s.desc}</p>
                </div>
              ))}
            </div>
          </div>
        ),
      },

      // 3. Video Import Guide
      {
        id: 'video-import',
        category: 'guides',
        titleKhmer: '៣. ការនាំចូលវីដេអូ និងទម្រង់ឯកសារ (Video Import Guide)',
        titleEnglish: '3. Supported Media Formats & Limits',
        icon: FolderOpen,
        keywords: ['import', 'upload', 'format', 'mp4', 'mkv', 'webm', 'size', 'ទំហំ', 'ទម្រង់'],
        contentKhmer: (
          <div>
            <ul style={{ lineHeight: 1.8, fontSize: 13, paddingLeft: 20 }}>
              <li><b>ទម្រង់វីដេអូដែលគាំទ្រ៖</b> MP4, MKV, MOV, WebM, AVI, M4V (H.264, H.265, VP9, AV1)</li>
              <li><b>ទម្រង់អូឌីយ៉ូដែលគាំទ្រ៖</b> MP3, WAV, M4A, FLAC, OGG, AAC, OPUS</li>
              <li><b>ទំហំឯកសារអតិបរមា៖</b> រហូតដល់ 2,048 MB (2 GB) ក្នុងមួយឯកសារ</li>
              <li><b>ការនាំចូលតាម URL៖</b> គាំទ្រការទាញយកពី YouTube និងប្រភពអនឡាញ (ប្រសិនបើមានដំឡើង yt-dlp)</li>
              <li><b>ការការពារឯកសារខូច៖</b> FFprobe នឹងផ្ទៀងផ្ទាត់ Audio Stream ជាមុន។ ប្រសិនបើឯកសារគ្មានសម្លេង កម្មវិធីនឹងជូនដំណឹងភ្លាមៗ</li>
            </ul>
          </div>
        ),
      },

      // 4. Translation and Language Settings
      {
        id: 'languages-translation',
        category: 'subtitles',
        titleKhmer: '៤. ការកំណត់ភាសា និងការបកប្រែ (Translation & Language Settings)',
        titleEnglish: '4. Multilingual Neural Translation Settings',
        icon: Languages,
        keywords: ['translate', 'language', 'khmer', 'english', 'chinese', 'nllb', 'ភាសា', 'បកប្រែ'],
        contentKhmer: (
          <div>
            <p style={{ lineHeight: 1.7, fontSize: 13 }}>
              ប្រព័ន្ធគាំទ្រភាសាពេញនិយមជាង ១២+ ជុំវិញពិភពលោក៖
            </p>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, margin: '10px 0 14px' }}>
              {[
                '🇰🇭 ភាសាខ្មែរ (km)', '🇺🇸 English (en)', '🇨🇳 简体中文 (zh)', '🇯🇵 日本語 (ja)',
                '🇰🇷 한국어 (ko)', '🇻🇳 Tiếng Việt (vi)', '🇫🇷 Français (fr)', '🇪🇸 Español (es)',
                '🇩🇪 Deutsch (de)', '🇮🇩 Bahasa Indonesia (id)', '🇱🇦 ພາສາລາວ (lo)', '🇲🇲 မြန်မာစာ (my)',
              ].map((lang, idx) => (
                <span key={idx} style={{ background: 'var(--card)', border: '1px solid var(--line)', padding: '4px 10px', borderRadius: 20, fontSize: 11.5 }}>
                  {lang}
                </span>
              ))}
            </div>
            <p style={{ fontSize: 12.5, color: 'var(--muted)', lineHeight: 1.6 }}>
              ✓ <b>Zero Ollama Requirement:</b> ប្រើប្រាស់គំរូបកប្រែឆ្លាតវៃដែលដំណើរការស្រាលលើ CPU ដោយមិនចាំបាច់មាន Ollama ឡើយ។<br />
              ✓ <b>Khmer Unicode Alignment:</b> ធានាការតម្រៀបស្រៈ ព្យញ្ជនៈ និងជើងអក្សរខ្មែរត្រឹមត្រូវ ១០០% តាមក្បួនវេយ្យាករណ៍។
            </p>
          </div>
        ),
      },

      // 5. AI Voice and Character Settings
      {
        id: 'voices-characters',
        category: 'audio',
        titleKhmer: '៥. ការកំណត់សំឡេង និងតួអង្គ (AI Voice & Characters)',
        titleEnglish: '5. Speaker Diarization & Neural Voices',
        icon: Users,
        keywords: ['voice', 'piseth', 'sreymom', 'speaker', 'character', 'diarization', 'តួអង្គ', 'សំឡេង'],
        contentKhmer: (
          <div>
            <p style={{ lineHeight: 1.7, fontSize: 13 }}>
              ការកំណត់សំឡេងតួអង្គត្រូវបានរៀបចំយ៉ាងផ្ចិតផ្ចង់ក្នុង <b>Characters Studio</b>៖
            </p>
            <ul style={{ lineHeight: 1.8, fontSize: 12.5, paddingLeft: 20 }}>
              <li><b>Piseth (ពិសិដ្ឋ Neural)៖</b> សំឡេងបុរសខ្មែរ ធម្មជាតិ ស័ក្តិសមសម្រាប់តួអង្គប្រុស និទានរឿង ឬព័ត៌មាន។</li>
              <li><b>Sreymom (ស្រីមុំ Neural)៖</b> សំឡេងនារីខ្មែរ ស្រទន់ រស់រវើក ស័ក្តិសមសម្រាប់តួអង្គស្រី។</li>
              <li><b>Guy, Jenny, Aria (English Neural)៖</b> សំឡេងអង់គ្លេសកម្រិតខ្ពស់សម្រាប់វីដេអូបកប្រែជាភាសាអង់គ្លេស។</li>
              <li><b>ការកែតម្រូវតួអង្គច្រឡំ៖</b> ប្រសិនបើ AI ច្រឡំតួអង្គ អ្នកអាចប្តូរ Voice Assignment ឬច្របាច់បញ្ចូលតួអង្គ (Merge Speakers) ក្នុងផ្ទាំង Characters Studio បាន។</li>
            </ul>
          </div>
        ),
      },

      // 6. Original Soundtrack Preservation
      {
        id: 'soundtrack-preservation',
        category: 'audio',
        titleKhmer: '៦. ការរក្សាតន្ត្រី និងសំឡេង Effects ដើម (Soundtrack Preservation)',
        titleEnglish: '6. Preserving Music, Action SFX & Ambience',
        icon: Music,
        keywords: ['soundtrack', 'music', 'sfx', 'fighting', 'effects', 'ducking', 'តន្ត្រី', 'វាយតប់'],
        contentKhmer: (
          <div>
            <div
              style={{
                background: 'rgba(46,204,113,0.08)',
                borderLeft: '3px solid var(--green)',
                padding: '12px 14px',
                borderRadius: 6,
                marginBottom: 14,
              }}
            >
              <b style={{ color: 'var(--green)', fontSize: 13 }}>
                🛡️ គោលការណ៍ស្នូល៖ ជំនួសតែសំឡេងនិយាយរបស់មនុស្សប៉ុណ្ណោះ!
              </b>
              <p style={{ margin: '6px 0 0', fontSize: 12.5, lineHeight: 1.6 }}>
                កម្មវិធីមិនលុបបំបាត់តន្ត្រីកំដរ សំឡេងកណ្តាប់ដៃ អាវុធ ផ្ទុះ ជើងដើរ ខ្យល់ ភ្លៀង ឬសំឡេងបរិស្ថានឡើយ។
              </p>
            </div>
            <ul style={{ lineHeight: 1.8, fontSize: 12.5, paddingLeft: 20 }}>
              <li><b>Dynamic Sidechain Ducking៖</b> នៅពេលតួអង្គនិយាយ សំឡេងកំដរស្រកចុះបន្តិច (Ducking Intensity 35%) ហើយត្រឡប់មកពេញ ១០០% វិញពេលស្ងាត់។</li>
              <li><b>Vocal Formant Notch Filter៖</b> កាត់បន្ថយប្រេកង់សំឡេង 1400Hz លើ Soundtrack ដើមដើម្បីឱ្យសំឡេងនិយាយថ្មីឮច្បាស់ត្រចៀក។</li>
              <li><b>Nonverbal Vocalization Preservation៖</b> សំឡេងសើច យំ ស្រែក ដកដង្ហើមធំរបស់តួអង្គពិតត្រូវបានកាត់យកមកប្រើដោយផ្ទាល់ មិនប្រើសំឡេង TTS រ៉ូបូតឡើយ។</li>
            </ul>
          </div>
        ),
      },

      // 7. Video Preview and Audio Playback
      {
        id: 'preview-playback',
        category: 'guides',
        titleKhmer: '៧. ការមើលវីដេអូទន្ទឹមគ្នា (Dual Video Preview Studio)',
        titleEnglish: '7. Synchronized Dual Video Comparison',
        icon: Film,
        keywords: ['preview', 'dual', 'side by side', 'player', 'sync', 'មើល', 'ប្រៀបធៀប'],
        contentKhmer: (
          <div>
            <p style={{ lineHeight: 1.7, fontSize: 13 }}>
              ស្ទូឌីយោ <b>Dual Video Preview</b> អនុញ្ញាតឱ្យអ្នកប្រៀបធៀបវីដេអូដើម និងវីដេអូដែលបានបញ្ចូលសំឡេងរួច៖
            </p>
            <ul style={{ lineHeight: 1.8, fontSize: 12.5, paddingLeft: 20 }}>
              <li><b>Synchronized Playback៖</b> ចុច Play, Pause ឬអូស Seek Bar វីដេអូទាំងសងខាងនឹងរត់ស្របគ្នាក្នុងកម្រិតមីលីវិនាទី។</li>
              <li><b>Audio Switcher៖</b> អាចស្តាប់តែសំឡេងដើម (Original Audio), ស្តាប់តែសំឡេង Dubbing ឬស្តាប់សំឡេងលាយបញ្ចូលគ្នា (Mixed Soundtrack)។</li>
              <li><b>Volume Sliders៖</b> លៃតម្រូវកម្រិតសំឡេងដើម (Soundtrack Volume) និងសំឡេងនិយាយ (Dialogue Volume) តាមចំណូលចិត្ត។</li>
            </ul>
          </div>
        ),
      },

      // 8. Subtitle and Spelling Correction
      {
        id: 'subtitles-proofreading',
        category: 'subtitles',
        titleKhmer: '៨. ការកែសម្រួល Subtitles និងអក្ខរាវិរុទ្ធ (Subtitles & Proofreading)',
        titleEnglish: '8. Subtitle Editor Pro & Khmer Proofreading',
        icon: FileCheck2,
        keywords: ['subtitle', 'srt', 'vtt', 'editor', 'proofread', 'dictionary', 'អក្សរ', 'កែសម្រួល', 'វចនានុក្រម'],
        contentKhmer: (
          <div>
            <ul style={{ lineHeight: 1.8, fontSize: 12.5, paddingLeft: 20 }}>
              <li><b>Subtitle Editor Pro៖</b> កែសម្រួលអត្ថបទ កំណត់ត្រាពេលវេលា (Start/End Timestamps) បំបែក (Split) ឬច្របាច់បញ្ចូលឃ្លា (Merge)។</li>
              <li><b>Khmer Grammar & Ligature Engine៖</b> ជួសជុលកំហុសស្រៈជាន់គ្នា ជើងអក្សរ និងសញ្ញាខណ្ឌ (។) ស្វ័យប្រវត្តិ។</li>
              <li><b>Pronunciation Dictionary៖</b> បន្ថែមពាក្យ ឬឈ្មោះមនុស្សពិបាកៗទៅក្នុងវចនានុក្រម ដើម្បីឱ្យ AI អានតាមសូរសព្ទត្រឹមត្រូវ។</li>
            </ul>
          </div>
        ),
      },

      // 9. Exporting Videos
      {
        id: 'exporting-videos',
        category: 'guides',
        titleKhmer: '៩. ការ Export វីដេអូសម្រេច (Exporting Videos)',
        titleEnglish: '9. Video Rendering & Download Options',
        icon: FolderOpen,
        keywords: ['export', 'render', 'download', 'hardsub', 'mp4', 'ទាញយក'],
        contentKhmer: (
          <div>
            <ul style={{ lineHeight: 1.8, fontSize: 12.5, paddingLeft: 20 }}>
              <li><b>Render Hardsubbed MP4៖</b> ដុត Subtitles អក្សរខ្មែរ និងបញ្ចូលសំឡេង Dubbing ចូលទៅក្នុងវីដេអូ MP4 កម្រិតច្បាស់ខ្ពស់។</li>
              <li><b>ទាញយក Subtitles ដាច់ដោយឡែក៖</b> អាចទាញយកឯកសារ SubRip (.SRT), WebVTT (.VTT) ឬ Plain Text (.TXT) សម្រាប់យកទៅប្រើប្រាស់បន្ត។</li>
              <li><b>ទាញយកសំឡេង Dubbed Audio (.WAV)៖</b> សម្រាប់យកទៅកាត់តក្នុង Adobe Premiere, DaVinci Resolve ឬ CapCut។</li>
            </ul>
          </div>
        ),
      },

      // 10. Troubleshooting Center
      {
        id: 'troubleshooting',
        category: 'troubleshoot',
        titleKhmer: '១០. មជ្ឈមណ្ឌលដោះស្រាយបញ្ហា (Troubleshooting Center)',
        titleEnglish: '10. Searchable Troubleshooting Matrix',
        icon: AlertTriangle,
        keywords: ['troubleshoot', 'error', 'fix', 'problem', 'silent', 'sound', 'កំហុស', 'ដោះស្រាយ'],
        contentKhmer: (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {[
              {
                title: '🎧 វីដេអូដែល Dubbed រួចគ្មានឮសំឡេងនិយាយ (No Dubbed Voice)',
                causes: 'TTS request ជួបបញ្ហា network, ឯកសារទទេ ឬកម្រិតសំឡេង Dialogue Volume ត្រូវបានទាញមក 0%។',
                fixes: 'ចូលទៅកាន់ Dual Video Preview Studio -> ពិនិត្យមើល Dialogue Volume Slider ថាលើសពី 80% ឬចុច Generate Dubbing ម្តងទៀត។',
              },
              {
                title: '🥊 តន្ត្រីកំដរ ឬសំឡេងវាយតប់បាត់បង់ (Music / SFX Disappeared)',
                causes: 'ជម្រើស "Preserve Original Soundtrack" ត្រូវបានបិទ (Disabled)។',
                fixes: 'បើកជម្រើស "Preserve Original Soundtrack" ឱ្យ ON នៅក្នុង Export Drawer ឬ Settings។ វានឹងបើក Sidechain Ducking ស្វ័យប្រវត្តិ។',
              },
              {
                title: '✂️ សំឡេងនិយាយដាច់ចុងប្រយោគ (Cut-off Sentence Endings)',
                causes: 'ឃ្លាបកប្រែវែងជាងពេលវេលាកំណត់ក្នុង Subtitle window។',
                fixes: 'ប្រព័ន្ធបច្ចុប្បន្នប្រើ pitch-neutral atempo និង micro-fadeouts ស្វ័យប្រវត្តិ។ ប្រសិនបើតឹងពេក សូមកែសម្រួលឃ្លាក្នុង Subtitle Editor ឱ្យខ្លីល្មម។',
              },
              {
                title: '🛑 Upload វីដេអូមិនដំណើរការ ឬរាយការណ៍ថា Unsupported Format',
                causes: 'ឯកសារវីដេអូមាន Codec មិនស្គាល់ ឬទំហំលើសពី 2 GB។',
                fixes: 'បំប្លែងឯកសារទៅជា Standard MP4 (H.264 / AAC) មុនពេល Upload ឬកាត់បន្ថយទំហំឯកសារ។',
              },
              {
                title: '💻 កម្មវិធីដើរយឺត ឬជាប់គាំង (Processing Stuck)',
                causes: 'កុំព្យូទ័រខ្វះខាត RAM ឬ CPU ដំណើរការលើសកម្រិត។',
                fixes: 'ជ្រើសរើសគំរូ Whisper Model "Tiny" ក្នុង Settings (ប្រើត្រឹម ~390MB RAM) និងបិទកម្មវិធីធ្ងន់ៗដទៃលើកុំព្យូទ័រ។',
              },
            ].map((issue, idx) => (
              <div key={idx} style={{ background: 'var(--card)', border: '1px solid var(--line)', borderRadius: 8, padding: 12 }}>
                <b style={{ color: 'var(--gold)', fontSize: 13 }}>{issue.title}</b>
                <div style={{ marginTop: 6, fontSize: 12, lineHeight: 1.6 }}>
                  <span style={{ color: 'var(--muted)' }}><b>មូលហេតុ៖</b> {issue.causes}</span><br />
                  <span style={{ color: 'var(--green)' }}><b>វិធីដោះស្រាយ៖</b> {issue.fixes}</span>
                </div>
              </div>
            ))}
          </div>
        ),
      },

      // 11. Frequently Asked Questions
      {
        id: 'faq',
        category: 'troubleshoot',
        titleKhmer: '១១. សំណួរដែលសួរញឹកញាប់ (Frequently Asked Questions)',
        titleEnglish: '11. Frequently Asked Questions (FAQ)',
        icon: HelpCircle,
        keywords: ['faq', 'questions', 'answers', 'សំណួរ', 'ចម្លើយ'],
        contentKhmer: (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {[
              {
                q: 'តើ Khmer Translator ទាមទារការតភ្ជាប់អ៊ីនធឺណិតគ្រប់ពេលទេ?',
                a: 'ការស្គាល់សំឡេង Whisper, ការបកប្រែ, ការកាត់ត Subtitle និងការ Mix សំឡេងដំណើរការលើកុំព្យូទ័រផ្ទាល់ (Offline)។ ការបង្កើតសំឡេង Neural TTS ត្រូវការអ៊ីនធឺណិតស្រាលដើម្បីទាញសំឡេង Edge Neural Voices ដែលមានគុណភាពខ្ពស់។',
              },
              {
                q: 'តើខ្ញុំអាចប្រើកម្មវិធីនេះលើកុំព្យូទ័រខ្សោយ (Low-End Laptop) បានទេ?',
                a: 'បានយ៉ាងស្រួល! កម្មវិធីត្រូវបាន optimize យ៉ាងពិសេសសម្រាប់ម៉ាស៊ីន ASUS VivoBook X515MA (RAM 3.3 - 4 GiB) ដោយប្រើ faster-whisper INT8 CPU quantization។',
              },
              {
                q: 'តើវីដេអូរបស់ខ្ញុំមានសុវត្ថិភាពទេ?',
                a: 'មានសុវត្ថិភាព ១០០%! វីដេអូ និងឯកសារសំឡេងទាំងអស់ត្រូវបានរក្សាទុកតែនៅលើកុំព្យូទ័ររបស់អ្នកផ្ទាល់ (Local Storage) ដោយមិនត្រូវបាន Upload ទៅកាន់ Cloud ខាងក្រៅឡើយ។',
              },
              {
                q: 'តើធ្វើដូចម្តេចប្រសិនបើឈ្មោះតួអង្គអានខុស?',
                a: 'ចូលទៅកាន់ផ្ទាំង Dictionary (វចនានុក្រមសូរសព្ទ) ហើយបញ្ចូលពាក្យដើម និងរបៀបអានជាភាសាខ្មែរ។ ប្រព័ន្ធនឹងកែសម្រួលដោយស្វ័យប្រវត្តិនូវរាល់ឃ្លាដែលមានពាក្យនោះ។',
              },
            ].map((faq, idx) => (
              <div
                key={idx}
                style={{
                  background: 'var(--card)',
                  border: '1px solid var(--line)',
                  borderRadius: 8,
                  overflow: 'hidden',
                }}
              >
                <button
                  type="button"
                  onClick={() => setExpandedFaqIndex(expandedFaqIndex === idx ? null : idx)}
                  style={{
                    width: '100%',
                    padding: '12px 14px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    background: 'none',
                    border: 'none',
                    color: 'var(--fg)',
                    textAlign: 'left',
                    fontWeight: 600,
                    fontSize: 13,
                    cursor: 'pointer',
                  }}
                >
                  <span>{faq.q}</span>
                  {expandedFaqIndex === idx ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                </button>
                <AnimatePresence>
                  {expandedFaqIndex === idx && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      style={{ padding: '0 14px 12px', fontSize: 12.5, color: 'var(--muted)', lineHeight: 1.6 }}
                    >
                      {faq.a}
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            ))}
          </div>
        ),
      },

      // 12. System Requirements
      {
        id: 'system-requirements',
        category: 'system',
        titleKhmer: '១២. តម្រូវការប្រព័ន្ធ និង Hardware (System Requirements)',
        titleEnglish: '12. Hardware & Software Requirements',
        icon: Cpu,
        keywords: ['system', 'requirements', 'hardware', 'ram', 'cpu', 'ubuntu', 'linux', 'specs'],
        contentKhmer: (
          <div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 12 }}>
              <div style={{ background: 'var(--card)', border: '1px solid var(--line)', borderRadius: 8, padding: 14 }}>
                <b style={{ color: 'var(--gold)', fontSize: 13 }}>តម្រូវការអប្បបរមា (Minimum)</b>
                <ul style={{ margin: '8px 0 0', paddingLeft: 18, fontSize: 12, lineHeight: 1.8 }}>
                  <li><b>CPU:</b> Intel Celeron / Core i3 (2 Cores)</li>
                  <li><b>RAM:</b> 3.3 GiB - 4 GiB</li>
                  <li><b>Storage:</b> 5 GB Free Hard Disk</li>
                  <li><b>OS:</b> Ubuntu Linux 22.04+ / Debian / Windows 10/11</li>
                  <li><b>Whisper Model:</b> Tiny (INT8 CPU Quantization)</li>
                </ul>
              </div>
              <div style={{ background: 'var(--card)', border: '1px solid var(--line)', borderRadius: 8, padding: 14 }}>
                <b style={{ color: 'var(--green)', fontSize: 13 }}>តម្រូវការណែនាំ (Recommended)</b>
                <ul style={{ margin: '8px 0 0', paddingLeft: 18, fontSize: 12, lineHeight: 1.8 }}>
                  <li><b>CPU:</b> Intel Core i5 / AMD Ryzen 5 (4+ Cores)</li>
                  <li><b>RAM:</b> 8 GiB - 16 GiB</li>
                  <li><b>Storage:</b> 20 GB SSD</li>
                  <li><b>Whisper Model:</b> Base ឬ Small</li>
                  <li><b>GPU:</b> Not required (ដំណើរការលើ CPU បានយ៉ាងរលូន)</li>
                </ul>
              </div>
            </div>
          </div>
        ),
      },

      // 13. Privacy and Security
      {
        id: 'privacy-security',
        category: 'system',
        titleKhmer: '១៣. ឯកជនភាព និងសុវត្ថិភាព (Privacy & Security)',
        titleEnglish: '13. Data Privacy & Local-First Security',
        icon: ShieldCheck,
        keywords: ['privacy', 'security', 'data', 'safe', 'local', 'សុវត្ថិភាព', 'ឯកជនភាព'],
        contentKhmer: (
          <div>
            <p style={{ lineHeight: 1.7, fontSize: 13 }}>
              Khmer Translator ត្រូវបានបង្កើតឡើងដោយប្រកាន់ខ្ជាប់គោលការណ៍ <b>Local-First Privacy</b>៖
            </p>
            <ul style={{ lineHeight: 1.8, fontSize: 12.5, paddingLeft: 20 }}>
              <li><b>Zero Cloud Telemetry៖</b> គ្មានការប្រមូលទិន្នន័យ គ្មាន Tracking និងគ្មាន Analytics ខាងក្រៅ។</li>
              <li><b>On-Premise Media Processing៖</b> វីដេអូ អូឌីយ៉ូ និង Subtitles ត្រូវបានរក្សាទុកតែលើម៉ាស៊ីនរបស់អ្នកប៉ុណ្ណោះ។</li>
              <li><b>Path Traversal Protection៖</b> ប្រព័ន្ធការពារការលួចទាញយកឯកសារប្រព័ន្ធតាមរយៈ API routes។</li>
              <li><b>Cache Cleanup៖</b> អ្នកអាចលុបឯកសារបណ្តោះអាសន្នទាំងអស់បានគ្រប់ពេលក្នុង Settings។</li>
            </ul>
          </div>
        ),
      },

      // 14. Contact and Support
      {
        id: 'contact-support',
        category: 'system',
        titleKhmer: '១៤. ទំនាក់ទំនង និងជំនួយបច្ចេកទេស (Contact & Support)',
        titleEnglish: '14. Community Support & Issue Reporting',
        icon: LifeBuoy,
        keywords: ['contact', 'support', 'help', 'telegram', 'neoncipher200', 'issues', 'ទំនាក់ទំនង'],
        contentKhmer: (
          <div>
            {/* Official Telegram Support Card */}
            <div
              style={{
                background: 'linear-gradient(135deg, rgba(34,158,217,0.12) 0%, rgba(217,168,76,0.1) 100%)',
                border: '1px solid rgba(34,158,217,0.4)',
                borderRadius: 10,
                padding: '16px 18px',
                marginBottom: 14,
                boxShadow: '0 4px 16px rgba(0,0,0,0.15)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12, marginBottom: 10 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <TelegramIcon size={34} />
                  <div>
                    <b style={{ fontSize: 14, color: 'var(--fg)', display: 'flex', alignItems: 'center', gap: 6 }}>
                      {TELEGRAM_SUPPORT.displayName}
                      <span style={{ fontSize: 12, color: '#229ED9', fontWeight: 600 }}>{TELEGRAM_SUPPORT.username}</span>
                    </b>
                    <small style={{ color: 'var(--muted)', fontSize: 11.5 }}>
                      ជំនួយផ្ទាល់ផ្លូវការ (Official Telegram Direct Support)
                    </small>
                  </div>
                </div>

                <a
                  href={TELEGRAM_SUPPORT.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="primary-btn"
                  style={{
                    textDecoration: 'none',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 8,
                    background: 'linear-gradient(135deg, #229ED9 0%, #1782b8 100%)',
                    color: '#ffffff',
                    fontWeight: 600,
                    fontSize: 12.5,
                    padding: '8px 16px',
                    borderRadius: 8,
                    boxShadow: '0 4px 12px rgba(34,158,217,0.3)',
                  }}
                >
                  <TelegramIcon size={16} />
                  <span>{TELEGRAM_SUPPORT.buttonLabel}</span>
                  <ExternalLink size={13} />
                </a>
              </div>

              <p style={{ margin: '0 0 4px', fontSize: 12.5, color: 'var(--fg)', lineHeight: 1.6 }}>
                💬 <b>{TELEGRAM_SUPPORT.messageKhmer}</b>
              </p>
              <p style={{ margin: 0, fontSize: 11.5, color: 'var(--muted)', lineHeight: 1.5 }}>
                {TELEGRAM_SUPPORT.messageEnglish}
              </p>
            </div>

            <p style={{ lineHeight: 1.7, fontSize: 13 }}>
              សម្រាប់ការរាយការណ៍កំហុស (Bug Reports) ឬស្នើសុំមុខងារថ្មី (Feature Requests)៖
            </p>
            <ul style={{ lineHeight: 1.8, fontSize: 12.5, paddingLeft: 20 }}>
              <li><b>ឯកសារណែនាំ៖</b> សូមអានឯកសារ <code>docs/USER_GUIDE.md</code> និង <code>docs/DEPLOYMENT.md</code> ក្នុងគម្រោង។</li>
              <li><b>របាយការណ៍វិនិច្ឆ័យ៖</b> ប្រើប្រាស់ប៊ូតុង "Copy Diagnostic Information" ខាងក្រោមដើម្បីភ្ជាប់ជាមួយបញ្ហារបស់អ្នកពេលផ្ញើសារតាម Telegram។</li>
              <li><b>រក្សាសិទ្ធិបញ្ញា៖</b> {COPYRIGHT_TEXT}</li>
            </ul>
          </div>
        ),
      },

      // 15. About Khmer Translator
      {
        id: 'about',
        category: 'system',
        titleKhmer: '១៥. អំពី Khmer Translator (About Khmer Translator)',
        titleEnglish: '15. Application Version & Architecture Diagnostics',
        icon: Info,
        keywords: ['about', 'version', 'diagnostics', 'copyright', 'អំពី', 'កំណែ'],
        contentKhmer: (
          <div>
            <div style={{ background: 'var(--card)', border: '1px solid var(--line)', borderRadius: 8, padding: 14 }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 10 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <img src="/logo.png" alt="Logo" style={{ width: 32, height: 32, objectFit: 'contain' }} />
                  <div>
                    <b style={{ fontSize: 14 }}>Khmer Translator 2.0</b>
                    <div style={{ fontSize: 11, color: 'var(--muted)' }}>Build: October 2026 · Production Edition</div>
                  </div>
                </div>

                <button
                  className="primary-btn"
                  onClick={handleCopyDiagnostics}
                  disabled={isCopying}
                  style={{ fontSize: 12, padding: '7px 14px' }}
                >
                  <Copy size={13} /> {copiedDiag ? 'បានចម្លងរួចរាល់!' : 'Copy Diagnostic Information'}
                </button>
              </div>

              <div style={{ borderTop: '1px solid var(--line)', marginTop: 12, paddingTop: 10, fontSize: 12, color: 'var(--muted)', lineHeight: 1.6 }}>
                <div><b>Architecture:</b> FastAPI (Python 3.14) · React + TypeScript + Vite · FFmpeg Sidechain Audio Engine</div>
                <div><b>AI Engines:</b> faster-whisper INT8 CPU · Microsoft Edge Neural TTS · Zero Ollama Dependency</div>
                <div style={{ marginTop: 6, color: 'var(--gold)' }}>{COPYRIGHT_TEXT}</div>
              </div>
            </div>
          </div>
        ),
      },
    ],
    [API, isCopying, copiedDiag, onOpenOnboarding]
  );

  // Filter sections by search and category
  const filteredSections = useMemo(() => {
    return sections.filter((s) => {
      const matchesCategory = selectedCategory === 'all' || s.category === selectedCategory;
      if (!matchesCategory) return false;

      if (!searchQuery.trim()) return true;

      const q = searchQuery.toLowerCase();
      const inTitleKhmer = s.titleKhmer.toLowerCase().includes(q);
      const inTitleEng = s.titleEnglish.toLowerCase().includes(q);
      const inKeywords = s.keywords.some((k) => k.toLowerCase().includes(q));
      return inTitleKhmer || inTitleEng || inKeywords;
    });
  }, [sections, selectedCategory, searchQuery]);

  return (
    <div style={{ marginTop: 14 }}>
      {/* Header Banner */}
      <div
        style={{
          background: 'linear-gradient(135deg, rgba(217,168,76,0.12) 0%, rgba(30,22,54,0.3) 100%)',
          border: '1px solid var(--gold)',
          borderRadius: 12,
          padding: '18px 20px',
          marginBottom: 16,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: 12,
        }}
      >
        <div>
          <h3 style={{ margin: '0 0 4px', fontSize: 17, display: 'flex', alignItems: 'center', gap: 8, color: 'var(--fg)' }}>
            <BookOpen size={20} style={{ color: 'var(--gold)' }} />
            មជ្ឈមណ្ឌលជំនួយ & សៀវភៅណែនាំ (Help & Support Center)
          </h3>
          <p style={{ margin: 0, fontSize: 12, color: 'var(--muted)' }}>
            ឯកសារណែនាំលម្អិត ១៥ ផ្នែក របៀបដោះស្រាយបញ្ហា និងព័ត៌មានវិនិច្ឆ័យប្រព័ន្ធ
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
          <a
            href={TELEGRAM_SUPPORT.url}
            target="_blank"
            rel="noopener noreferrer"
            className="secondary-btn"
            style={{
              textDecoration: 'none',
              display: 'inline-flex',
              alignItems: 'center',
              gap: 6,
              fontSize: 12,
              padding: '7px 13px',
              border: '1px solid rgba(34,158,217,0.5)',
              color: 'var(--fg)',
            }}
          >
            <TelegramIcon size={15} />
            <span>{TELEGRAM_SUPPORT.buttonLabel}</span>
            <ExternalLink size={12} />
          </a>
          <button
            className="secondary-btn"
            onClick={onOpenOnboarding}
            style={{ fontSize: 12, padding: '7px 14px' }}
          >
            <Play size={13} style={{ color: 'var(--gold)' }} /> ការណែនាំដំបូង (Onboarding Guide)
          </button>
          <button
            className="primary-btn"
            onClick={handleCopyDiagnostics}
            disabled={isCopying}
            style={{ fontSize: 12, padding: '7px 14px' }}
          >
            <Copy size={13} /> {copiedDiag ? 'Copied!' : 'Copy Diagnostics'}
          </button>
        </div>
      </div>

      {/* Search Bar & Category Filters */}
      <div style={{ marginBottom: 16, display: 'flex', flexDirection: 'column', gap: 10 }}>
        <div style={{ position: 'relative' }}>
          <Search
            size={16}
            style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--muted)' }}
          />
          <input
            type="text"
            className="config-input"
            placeholder="ស្វែងរកប្រធានបទជំនួយ (Search articles, troubleshooting, audio, subtitles...)"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{ paddingLeft: 36, width: '100%', boxSizing: 'border-box' }}
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              style={{
                position: 'absolute',
                right: 10,
                top: '50%',
                transform: 'translateY(-50%)',
                background: 'none',
                border: 'none',
                color: 'var(--muted)',
                cursor: 'pointer',
              }}
            >
              <X size={15} />
            </button>
          )}
        </div>

        {/* Category Pills */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
          {categories.map((c) => (
            <button
              key={c.id}
              onClick={() => setSelectedCategory(c.id)}
              style={{
                background: selectedCategory === c.id ? 'var(--gold)' : 'var(--card)',
                color: selectedCategory === c.id ? '#1a1005' : 'var(--fg)',
                border: `1px solid ${selectedCategory === c.id ? 'var(--gold)' : 'var(--line)'}`,
                padding: '5px 12px',
                borderRadius: 20,
                fontSize: 12,
                cursor: 'pointer',
                fontWeight: selectedCategory === c.id ? 600 : 400,
                transition: 'all 0.15s ease',
              }}
            >
              {c.labelKhmer}
            </button>
          ))}
        </div>
      </div>

      {/* Content Layout: Sidebar Nav + Main Article Display */}
      {filteredSections.length === 0 ? (
        <div
          style={{
            background: 'var(--card)',
            border: '1px solid var(--line)',
            borderRadius: 10,
            padding: '30px 20px',
            textAlign: 'center',
            color: 'var(--muted)',
          }}
        >
          <HelpCircle size={32} style={{ color: 'var(--gold)', marginBottom: 8 }} />
          <h4 style={{ margin: '0 0 6px', color: 'var(--fg)' }}>រកមិនឃើញលទ្ធផលស្វែងរកឡើយ (No Articles Found)</h4>
          <p style={{ margin: 0, fontSize: 12 }}>
            សូមព្យាយាមស្វែងរកពាក្យគន្លឹះដទៃដូចជា: "voice", "soundtrack", "troubleshoot", "whisper", "export"
          </p>
          <button
            className="secondary-btn"
            onClick={() => {
              setSearchQuery('');
              setSelectedCategory('all');
            }}
            style={{ marginTop: 12, fontSize: 12 }}
          >
            សម្អាតការស្វែងរក (Clear Search)
          </button>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 14 }}>
          {filteredSections.map((sec) => {
            const Icon = sec.icon;
            const isSelected = activeSectionId === sec.id;
            return (
              <motion.div
                key={sec.id}
                layout
                className="help-section-card"
                style={{
                  background: 'var(--panel)',
                  border: `1px solid ${isSelected ? 'var(--gold)' : 'var(--line)'}`,
                  borderRadius: 10,
                  padding: '16px 18px',
                  boxShadow: isSelected ? '0 4px 18px rgba(217,168,76,0.1)' : 'none',
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 10,
                    marginBottom: 10,
                    borderBottom: '1px solid var(--line)',
                    paddingBottom: 8,
                  }}
                >
                  <div
                    style={{
                      width: 32,
                      height: 32,
                      borderRadius: 8,
                      background: 'rgba(217,168,76,0.15)',
                      color: 'var(--gold)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    <Icon size={17} />
                  </div>
                  <div>
                    <h4 style={{ margin: 0, fontSize: 13.5, color: 'var(--fg)' }}>
                      {sec.titleKhmer}
                    </h4>
                    <span style={{ fontSize: 10.5, color: 'var(--muted)' }}>
                      {sec.titleEnglish}
                    </span>
                  </div>
                </div>

                <div style={{ color: 'var(--fg)' }}>{sec.contentKhmer}</div>
              </motion.div>
            );
          })}
        </div>
      )}
    </div>
  );
};
