import React, { useState, useEffect } from 'react';
import {
  Clapperboard,
  Sparkles,
  Languages,
  Users,
  Music,
  Film,
  ArrowRight,
  ArrowLeft,
  CheckCircle2,
  X,
  Volume2,
  FileCheck2,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { COPYRIGHT_TEXT } from '../types';

interface OnboardingWizardProps {
  isOpen: boolean;
  onClose: () => void;
  onNavigateToWorkspace?: () => void;
}

interface StepData {
  id: number;
  icon: any;
  titleKhmer: string;
  titleEnglish: string;
  badge: string;
  descriptionKhmer: string;
  descriptionEnglish: string;
  keyPoints: { icon: string; km: string; en: string }[];
  illustrationGradient: string;
}

const STEPS: StepData[] = [
  {
    id: 1,
    icon: Sparkles,
    badge: 'ស្វាគមន៍ / WELCOME',
    titleKhmer: 'សូមស្វាគមន៍មកកាន់ Khmer Translator 2.0',
    titleEnglish: 'Welcome to Khmer Translator 2.0',
    descriptionKhmer:
      'ប្រព័ន្ធបកប្រែវីដេអូ និងបញ្ចូលសំឡេងនិយាយឆ្លាតវៃពហុភាសា ដែលដំណើរការលើកុំព្យូទ័ររបស់អ្នកផ្ទាល់ (100% Local AI Speech Engine) ដោយមិនទាមទារ Ollama ឬ GPU ធ្ងន់ៗឡើយ។',
    descriptionEnglish:
      'A professional multilingual AI video translation, dubbing, and subtitle studio running on your local machine with zero heavy GPU or Ollama dependencies.',
    keyPoints: [
      { icon: '🛡️', km: 'សុវត្ថិភាពឯកជនភាព ១០០% (Local-First): វីដេអូមិនត្រូវបានបញ្ជូនទៅ Server ខាងក្រៅឡើយ', en: '100% Local privacy: media files stay on your machine' },
      { icon: '⚡', km: 'រចនាឡើងយ៉ាងពិសេសសម្រាប់កុំព្យូទ័រ RAM 3.3 - 4 GiB (INT8 CPU Quantization)', en: 'Optimized for low-memory CPU hardware (3.3 - 4 GiB RAM)' },
      { icon: '🇰🇭', km: 'រចនាបថវប្បធម៌ខ្មែរ ប្រណីត ស្រទន់ និងគាំទ្រភាសាខ្មែរពេញលេញ', en: 'Authentic Khmer cultural design with full Unicode support' },
    ],
    illustrationGradient: 'linear-gradient(135deg, rgba(217,168,76,0.2) 0%, rgba(30,22,54,0.4) 100%)',
  },
  {
    id: 2,
    icon: Clapperboard,
    badge: 'ជំហានទី ១ / STEP 1',
    titleKhmer: 'នាំចូលវីដេអូ និងជ្រើសរើសភាសា',
    titleEnglish: 'Import Video & Select Languages',
    descriptionKhmer:
      'ទម្លាក់ឯកសារវីដេអូ ឬអូឌីយ៉ូរបស់អ្នកចូលទៅក្នុងកម្មវិធី។ ប្រព័ន្ធគាំទ្រគ្រប់ទម្រង់ទូទៅរួមមាន MP4, MKV, MOV, WebM, MP3, និង WAV។',
    descriptionEnglish:
      'Drag and drop your media file. Supports MP4, MKV, MOV, WebM, MP3, WAV, and high-definition video containers up to 2 GB.',
    keyPoints: [
      { icon: '🌐', km: 'Auto Detect Language: AI Whisper ស្វែងរកភាសាដើមក្នុងវីដេអូដោយស្វ័យប្រវត្តិ', en: 'Auto Detect Language: Whisper detects the spoken language' },
      { icon: '🎯', km: 'ភាសាគោលដៅ៖ អាចបកប្រែជាភាសាខ្មែរ (Khmer), អង់គ្លេស, ចិន, ជប៉ុន, កូរ៉េ និង ១២+ ភាសាទៀត', en: 'Target Language: Translate into Khmer, English, Chinese, etc.' },
      { icon: '🚀', km: 'Beginner Mode៖ ចុច "Transcribe" តែមួយឃ្លីក ប្រព័ន្ធដំណើរការគ្រប់ដំណាក់កាលស្វ័យប្រវត្តិ', en: 'Beginner Mode: One-click workflow from upload to export' },
    ],
    illustrationGradient: 'linear-gradient(135deg, rgba(74,144,226,0.2) 0%, rgba(20,30,50,0.4) 100%)',
  },
  {
    id: 3,
    icon: Users,
    badge: 'ជំហានទី ២ / STEP 2',
    titleKhmer: 'បែងចែកតួអង្គ និងកំណត់សំឡេង AI',
    titleEnglish: 'Speaker Diarization & Character Voices',
    descriptionKhmer:
      'កម្មវិធីនឹងស្តាប់ និងវិភាគថាតើមានមនុស្សប៉ុន្មាននាក់កំពុងនិយាយក្នុងវីដេអូ ហើយបែងចែកជា Speaker 1, 2... ដោយស្វ័យប្រវត្តិ។',
    descriptionEnglish:
      'The engine automatically detects distinct speakers, tracks character continuity across scenes, and maps suitable neural voices.',
    keyPoints: [
      { icon: '🎙️', km: 'សំឡេងខ្មែរ Neural ធម្មជាតិ៖ Piseth (ពិសិដ្ឋ) និង Sreymom (ស្រីមុំ)', en: 'Natural Khmer Neural Voices: Piseth (Male) & Sreymom (Female)' },
      { icon: '🎭', km: 'កែសម្រួលតួអង្គក្នុង Characters Studio៖ ប្តូរសំឡេង កម្រិតល្បឿន និងស្ទីលនិយាយបានតាមចិត្ត', en: 'Editable Character Profiles: Adjust pitch, rate, and assignment' },
      { icon: '✨', km: 'Emotion Delivery៖ បញ្ចេញសំឡេងតាមអារម្មណ៍តួអង្គ (រីករាយ, ខឹង, កើតទុក្ខ)', en: 'Emotion Delivery: Expressive style adaptation' },
    ],
    illustrationGradient: 'linear-gradient(135deg, rgba(46,204,113,0.2) 0%, rgba(20,40,30,0.4) 100%)',
  },
  {
    id: 4,
    icon: Music,
    badge: 'ជំហានទី ៣ / STEP 3',
    titleKhmer: 'រក្សាតន្ត្រី សំឡេងវាយតប់ និង SFX ដើម',
    titleEnglish: 'Preserve Original Soundtrack & Action SFX',
    descriptionKhmer:
      'គោលការណ៍ស្នូល៖ ជំនួសតែសំឡេងនិយាយរបស់មនុស្សប៉ុណ្ណោះ! តន្ត្រីកំដរ សំឡេងកណ្តាប់ដៃ អាវុធ ការផ្ទុះ និងបរិស្ថានដើមត្រូវបានរក្សាទុក ១០០%។',
    descriptionEnglish:
      'Core principle: Translate human speech only! Background music, punches, kicks, explosions, and environmental audio are strictly preserved.',
    keyPoints: [
      { icon: '🥊', km: 'Fighting & Action SFX៖ សំឡេងវាយតប់មិនត្រូវបានលុបបំបាត់ឡើយ ទោះជាតួអង្គកំពុងនិយាយក៏ដោយ', en: 'Action Sound Effects: Punches and weapon sounds stay fully audible' },
      { icon: '😂', km: 'Nonverbal Preservation៖ សំឡេងសើច ស្រែក និងយំរបស់តួអង្គពិតត្រូវបានកាត់យកមកប្រើផ្ទាល់', en: 'Nonverbal Vocalizations: Authentic actor laughs and gasps preserved' },
      { icon: '🎛️', km: 'Sidechain Ducking & Vocal Formant EQ៖ សំឡេងបកប្រែឮច្បាស់ត្រចៀកដោយមិនបែកសំឡេង', en: 'Dynamic Sidechain Ducking: Crystal-clear vocal clarity' },
    ],
    illustrationGradient: 'linear-gradient(135deg, rgba(231,76,60,0.2) 0%, rgba(40,20,20,0.4) 100%)',
  },
  {
    id: 5,
    icon: Film,
    badge: 'ជំហានទី ៤ / STEP 4',
    titleKhmer: 'Dual Video Preview & Export វីដេអូសម្រេច',
    titleEnglish: 'Dual Video Preview & Final Video Export',
    descriptionKhmer:
      'ផ្ទៀងផ្ទាត់វីដេអូដើម និងវីដេអូបានបកប្រែរួចក្នុងស្ទូឌីយោ Preview ទន្ទឹមគ្នា មុនពេលទាញយកឯកសារ MP4 ឬ Subtitle SRT/VTT។',
    descriptionEnglish:
      'Compare original and dubbed versions side-by-side in Dual Video Preview Studio before exporting the completed video or subtitle files.',
    keyPoints: [
      { icon: '📺', km: 'Side-by-Side Playback៖ ចុច Play ម្តង វីដេអូទាំងពីររត់ស្របគ្នា down to millisecond', en: 'Synchronized dual playback with independent audio track selectors' },
      { icon: '✏️', km: 'Subtitle Editor Pro & Proofreading៖ កែសម្រួលអក្ខរាវិរុទ្ធខ្មែរ និងវចនានុក្រមសូរសព្ទ', en: 'Subtitle Editor Pro & Khmer Proofreader with live dictionary' },
      { icon: '🎬', km: 'Export MP4 (Hardsubbed)៖ ដុត Subtitles និងសំឡេង Dubbing ចូលវីដេអូកម្រិតច្បាស់', en: 'Export MP4: Render video with burned-in subtitles and mixed audio' },
    ],
    illustrationGradient: 'linear-gradient(135deg, rgba(155,89,182,0.2) 0%, rgba(30,20,40,0.4) 100%)',
  },
];

export const InteractiveOnboardingWizard: React.FC<OnboardingWizardProps> = ({
  isOpen,
  onClose,
  onNavigateToWorkspace,
}) => {
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;
      if (e.key === 'Escape') {
        handleFinish();
      } else if (e.key === 'ArrowRight' && currentStep < STEPS.length - 1) {
        setCurrentStep((prev) => prev + 1);
      } else if (e.key === 'ArrowLeft' && currentStep > 0) {
        setCurrentStep((prev) => prev - 1);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, currentStep]);

  if (!isOpen) return null;

  const step = STEPS[currentStep];
  const StepIcon = step.icon;

  const handleFinish = () => {
    try {
      localStorage.setItem('khmer_translator_onboarding_completed', 'true');
    } catch (_) {}
    onClose();
  };

  const handleFinishAndStart = () => {
    handleFinish();
    if (onNavigateToWorkspace) {
      onNavigateToWorkspace();
    }
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="modal-overlay"
        style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(5, 4, 10, 0.78)',
          backdropFilter: 'blur(8px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 9999,
          padding: 16,
        }}
        onClick={handleFinish}
      >
        <motion.div
          initial={{ opacity: 0, scale: 0.94, y: 14 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.94, y: 14 }}
          transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
          className="onboarding-box"
          style={{
            background: 'var(--panel)',
            border: '1px solid var(--gold)',
            borderRadius: 14,
            maxWidth: 620,
            width: '100%',
            overflow: 'hidden',
            boxShadow: '0 25px 60px rgba(0,0,0,0.5)',
            display: 'flex',
            flexDirection: 'column',
          }}
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header Banner */}
          <div
            style={{
              padding: '18px 22px 14px',
              borderBottom: '1px solid var(--line)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              background: step.illustrationGradient,
              position: 'relative',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <div
                style={{
                  width: 40,
                  height: 40,
                  borderRadius: 10,
                  background: 'var(--gold)',
                  color: '#1a1005',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: '0 4px 12px rgba(217,168,76,0.35)',
                }}
              >
                <StepIcon size={22} />
              </div>
              <div>
                <span
                  style={{
                    fontSize: 10.5,
                    fontWeight: 700,
                    letterSpacing: 1,
                    color: 'var(--gold)',
                    textTransform: 'uppercase',
                  }}
                >
                  {step.badge} · {currentStep + 1} នៃ {STEPS.length}
                </span>
                <h3 style={{ margin: 0, fontSize: 16, color: 'var(--fg)' }}>
                  {step.titleKhmer}
                </h3>
              </div>
            </div>

            <button
              onClick={handleFinish}
              aria-label="Skip onboarding"
              style={{
                background: 'rgba(0,0,0,0.2)',
                border: '1px solid var(--line)',
                color: 'var(--muted)',
                borderRadius: '50%',
                width: 30,
                height: 30,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer',
              }}
            >
              <X size={15} />
            </button>
          </div>

          {/* Body Content */}
          <div style={{ padding: '20px 22px', flex: 1 }}>
            <p
              style={{
                margin: '0 0 16px',
                fontSize: 13.5,
                lineHeight: 1.6,
                color: 'var(--fg)',
              }}
            >
              {step.descriptionKhmer}
            </p>

            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: 10,
                marginBottom: 16,
              }}
            >
              {step.keyPoints.map((pt, idx) => (
                <div
                  key={idx}
                  style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: 10,
                    padding: '8px 12px',
                    borderRadius: 8,
                    background: 'var(--card)',
                    border: '1px solid var(--line)',
                    fontSize: 12.5,
                    lineHeight: 1.5,
                  }}
                >
                  <span style={{ fontSize: 16, flexShrink: 0 }}>{pt.icon}</span>
                  <div>
                    <div style={{ color: 'var(--fg)', fontWeight: 500 }}>
                      {pt.km}
                    </div>
                    <div style={{ fontSize: 11, color: 'var(--muted)', marginTop: 2 }}>
                      {pt.en}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Progress Dots */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 8,
                margin: '16px 0 6px',
              }}
            >
              {STEPS.map((_, idx) => (
                <button
                  key={idx}
                  onClick={() => setCurrentStep(idx)}
                  style={{
                    width: currentStep === idx ? 24 : 8,
                    height: 8,
                    borderRadius: 4,
                    background: currentStep === idx ? 'var(--gold)' : 'var(--line)',
                    border: 'none',
                    padding: 0,
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                  }}
                  aria-label={`Jump to step ${idx + 1}`}
                />
              ))}
            </div>
          </div>

          {/* Footer Controls */}
          <div
            style={{
              padding: '12px 22px 16px',
              borderTop: '1px solid var(--line)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: 10,
              background: 'rgba(0,0,0,0.1)',
            }}
          >
            <button
              onClick={handleFinish}
              style={{
                background: 'none',
                border: 'none',
                color: 'var(--muted)',
                fontSize: 12,
                cursor: 'pointer',
                padding: '6px 10px',
              }}
            >
              រំលង (Skip Tutorial)
            </button>

            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              {currentStep > 0 && (
                <button
                  className="secondary-btn"
                  onClick={() => setCurrentStep((prev) => prev - 1)}
                  style={{ fontSize: 12, padding: '7px 14px' }}
                >
                  <ArrowLeft size={14} /> ត្រឡប់ក្រោយ (Back)
                </button>
              )}

              {currentStep < STEPS.length - 1 ? (
                <button
                  className="primary-btn"
                  onClick={() => setCurrentStep((prev) => prev + 1)}
                  style={{ fontSize: 12, padding: '7px 16px' }}
                >
                  បន្ទាប់ (Next) <ArrowRight size={14} />
                </button>
              ) : (
                <button
                  className="primary-btn"
                  onClick={handleFinishAndStart}
                  style={{
                    fontSize: 12,
                    padding: '7px 18px',
                    background: 'var(--gold)',
                    color: '#1a1005',
                    fontWeight: 600,
                  }}
                >
                  <CheckCircle2 size={15} /> ចាប់ផ្តើមបកប្រែ (Start Translating)
                </button>
              )}
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};
