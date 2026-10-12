import React, { useState, useRef, useEffect } from 'react';
import { HelpCircle, Info, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export type HelpTopicKey =
  | 'auto_detect'
  | 'diarization'
  | 'auto_voice'
  | 'emotion'
  | 'speech_separation'
  | 'preserve_soundtrack'
  | 'ducking'
  | 'khmer_dict'
  | 'subtitle_timing'
  | 'audio_mixing'
  | 'export_quality';

interface HelpDefinition {
  titleKhmer: string;
  titleEnglish: string;
  summaryKhmer: string;
  summaryEnglish: string;
  detailKhmer?: string;
  detailEnglish?: string;
  tip?: string;
}

export const HELP_TOPICS: Record<HelpTopicKey, HelpDefinition> = {
  auto_detect: {
    titleKhmer: 'ស្វែងរកភាសាដើមស្វ័យប្រវត្តិ (Auto Detect)',
    titleEnglish: 'Automatic Language Identification',
    summaryKhmer: 'AI Whisper នឹងស្តាប់សំឡេង 30 វិនាទីដំបូងដើម្បីកំណត់ភាសាដែលកំពុងនិយាយក្នុងវីដេអូដោយស្វ័យប្រវត្តិ។',
    summaryEnglish: 'Whisper samples the first 30 seconds of audio to automatically detect the spoken source language.',
    tip: 'ប្រសិនបើវីដេអូមានតន្ត្រីខ្លាំង សូមជ្រើសរើសភាសាជាក់លាក់ដើម្បីបង្កើនភាពត្រឹមត្រូវ។',
  },
  diarization: {
    titleKhmer: 'ការបែងចែកតួអង្គនិយាយ (Speaker Diarization)',
    titleEnglish: 'Speaker Diarization & Profiling',
    summaryKhmer: 'បច្ចេកវិទ្យាវិភាគ និងបំបែកថាអ្នកណាជាអ្នកនិយាយនៅពេលណា (Speaker 1, 2...) ដោយមិនច្រឡំសំឡេងគ្នា។',
    summaryEnglish: 'Identifies who spoke when, assigning stable speaker IDs across dialogue segments.',
    tip: 'អ្នកអាចកែសម្រួល ឬប្តូរតួអង្គក្នុងផ្ទាំង Characters Studio បានគ្រប់ពេល។',
  },
  auto_voice: {
    titleKhmer: 'ការជ្រើសរើសសំឡេងតួអង្គស្វ័យប្រវត្តិ (Automatic Voice Assignment)',
    titleEnglish: 'Smart Character Voice Mapping',
    summaryKhmer: 'កំណត់សំឡេង AI Neural (Piseth / Sreymom / Guy / Jenny) ឱ្យសមស្របតាមភេទ និងអាយុរបស់តួអង្គនីមួយៗ។',
    summaryEnglish: 'Automatically allocates distinct, natural neural voices based on estimated vocal traits and gender presentation.',
    tip: 'រក្សាសំឡេងតួអង្គឱ្យស្របគ្នាគ្រប់ឈុតឆាកក្នុងសាច់រឿងទាំងមូល។',
  },
  emotion: {
    titleKhmer: 'ការបញ្ចេញសំឡេងតាមអារម្មណ៍ (Emotion-Aware Dubbing)',
    titleEnglish: 'Emotion-Aware Speech Delivery',
    summaryKhmer: 'វិភាគអារម្មណ៍ក្នុងសាច់រឿង (រីករាយ, ខឹង, ស្រែក, កើតទុក្ខ) ហើយកែសម្រួលល្បឿន និងសម្លេង (Pitch) ឱ្យរស់រវើក។',
    summaryEnglish: 'Analyzes conversational context to dynamically adjust speech pitch, rate, and delivery styles where supported.',
  },
  speech_separation: {
    titleKhmer: 'ការញែកសំឡេងមនុស្ស និងតន្ត្រី (Speech Separation)',
    titleEnglish: 'Dialogue & Background Sound Separation',
    summaryKhmer: 'បំបែកសំឡេងសន្ទនារបស់មនុស្សចេញពីតន្ត្រីកំដរ និងសំឡេងវាយតប់ ដើម្បីកុំឱ្យបាត់បង់បរិយាកាសដើម។',
    summaryEnglish: 'Isolates spoken dialogue from the background audio bed so non-speech sounds remain intact.',
  },
  preserve_soundtrack: {
    titleKhmer: 'រក្សាតន្ត្រី និងសំឡេង Effects ដើម (Preserve Original Soundtrack)',
    titleEnglish: 'Original Soundtrack & SFX Preservation',
    summaryKhmer: 'ជំនួសតែសំឡេងនិយាយរបស់មនុស្សប៉ុណ្ណោះ! រក្សាតន្ត្រីកំដរ សំឡេងកណ្តាប់ដៃ ផ្ទុះ អាវុធ និងបរិស្ថានដើមឱ្យនៅដដែល។',
    summaryEnglish: 'Replaces spoken dialogue while preserving background music, fighting effects, impacts, and environmental ambience.',
    tip: 'បើកជាលំនាំដើម (ON by default) សម្រាប់គុណភាពកម្រិតភាពយន្ត។',
  },
  ducking: {
    titleKhmer: 'បន្ថយសំឡេងកំដរស្វ័យប្រវត្តិតាមចង្វាក់ (Background Ducking)',
    titleEnglish: 'Dynamic Sidechain Ducking',
    summaryKhmer: 'នៅពេលតួអង្គនិយាយ សំឡេងតន្ត្រីកំដរនឹងស្រកចុះបន្តិចដោយស្វ័យប្រវត្តិ ហើយត្រឡប់មកពេញវិញពេលស្ងាត់។',
    summaryEnglish: 'Smoothly attenuates background audio during active translated speech to guarantee crystal-clear vocal clarity.',
  },
  khmer_dict: {
    titleKhmer: 'វចនានុក្រមបញ្ចេញសំឡេងខ្មែរ (Khmer Pronunciation Dictionary)',
    titleEnglish: 'Khmer Pronunciation & Name Dictionary',
    summaryKhmer: 'កំណត់ការអានឈ្មោះមនុស្ស ទីកន្លែង និងពាក្យបច្ចេកទេសពិបាកៗ ដើម្បីកុំឱ្យ AI អានខុស។',
    summaryEnglish: 'Custom phonetics dictionary mapping difficult names, acronyms, and specialized terms to natural pronunciations.',
  },
  subtitle_timing: {
    titleKhmer: 'ការកំណត់ត្រាពេលវេលា Subtitles (Subtitle Timing Alignment)',
    titleEnglish: 'Subtitle & Speech Timestamp Sync',
    summaryKhmer: 'កែសម្រួលពេលវេលាចាប់ផ្តើម និងបញ្ចប់នៃឃ្លានីមួយៗឱ្យស៊ីចង្វាក់ជាមួយរូបភាពវីដេអូ។',
    summaryEnglish: 'Synchronizes start and end timestamps so translated subtitles and speech match the on-screen action.',
  },
  audio_mixing: {
    titleKhmer: 'ការលាយបញ្ចូលសំឡេងឆ្លាតវៃ (Intelligent Audio Mixing)',
    titleEnglish: 'Dual-Track Intelligent Mixing',
    summaryKhmer: 'លៃតម្រូវកម្រិតសំឡេងដើម (Soundtrack Volume) និងសំឡេងបកប្រែ (Dialogue Volume) ដោយមិនបែកសំឡេង (Zero Clipping)។',
    summaryEnglish: 'Balances dialogue volume and background audio levels with vocal formant frequency carving to prevent clipping.',
  },
  export_quality: {
    titleKhmer: 'គុណភាពវីដេអូពេល Export (Video Export & Burn-in)',
    titleEnglish: 'Video Rendering & Subtitle Burn-in',
    summaryKhmer: 'ដុត Subtitles អក្សរខ្មែរ និងផ្គុំសំឡេង Dubbing ចូលទៅក្នុងវីដេអូ MP4 កម្រិតច្បាស់ខ្ពស់។',
    summaryEnglish: 'Renders the final MP4 with hardsubbed Khmer Unicode subtitles and the newly mastered multilingual soundtrack.',
  },
};

interface ContextualHelpProps {
  topic: HelpTopicKey;
  size?: number;
  className?: string;
  lang?: 'km' | 'en';
}

export const ContextualHelp: React.FC<ContextualHelpProps> = ({
  topic,
  size = 15,
  className = '',
  lang = 'km',
}) => {
  const [open, setOpen] = useState(false);
  const def = HELP_TOPICS[topic];
  const popoverRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleOutsideClick = (e: MouseEvent) => {
      if (popoverRef.current && !popoverRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    if (open) {
      document.addEventListener('mousedown', handleOutsideClick);
    }
    return () => {
      document.removeEventListener('mousedown', handleOutsideClick);
    };
  }, [open]);

  if (!def) return null;

  return (
    <span
      ref={popoverRef}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        position: 'relative',
        verticalAlign: 'middle',
        marginLeft: 6,
      }}
      className={className}
    >
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation();
          setOpen(!open);
        }}
        aria-label={`Help about ${def.titleEnglish}`}
        style={{
          background: 'none',
          border: 'none',
          padding: 2,
          cursor: 'pointer',
          color: open ? 'var(--gold)' : 'var(--muted)',
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          borderRadius: '50%',
          transition: 'color 0.15s ease',
        }}
        title={lang === 'km' ? def.titleKhmer : def.titleEnglish}
      >
        <HelpCircle size={size} />
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: 4, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 4, scale: 0.95 }}
            transition={{ duration: 0.15 }}
            style={{
              position: 'absolute',
              top: '100%',
              left: '50%',
              transform: 'translateX(-50%)',
              zIndex: 1000,
              width: 280,
              maxWidth: '85vw',
              background: 'var(--panel)',
              border: '1px solid var(--gold)',
              borderRadius: 8,
              boxShadow: '0 10px 25px rgba(0,0,0,0.3)',
              padding: '12px 14px',
              color: 'var(--fg)',
              fontSize: 12,
              lineHeight: 1.5,
              marginTop: 6,
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                justifyContent: 'space-between',
                gap: 8,
                marginBottom: 6,
                borderBottom: '1px solid var(--line)',
                paddingBottom: 6,
              }}
            >
              <b style={{ color: 'var(--gold)', fontSize: 12.5 }}>
                {lang === 'km' ? def.titleKhmer : def.titleEnglish}
              </b>
              <button
                type="button"
                onClick={() => setOpen(false)}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--muted)',
                  cursor: 'pointer',
                  padding: 0,
                }}
              >
                <X size={13} />
              </button>
            </div>

            <p style={{ margin: '0 0 6px', color: 'var(--fg)' }}>
              {lang === 'km' ? def.summaryKhmer : def.summaryEnglish}
            </p>

            {def.tip && (
              <div
                style={{
                  background: 'rgba(217,168,76,0.1)',
                  borderLeft: '2px solid var(--gold)',
                  padding: '4px 8px',
                  borderRadius: 4,
                  fontSize: 11,
                  color: 'var(--fg)',
                }}
              >
                💡 {def.tip}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </span>
  );
};
