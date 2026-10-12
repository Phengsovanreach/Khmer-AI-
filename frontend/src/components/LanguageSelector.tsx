import React, { useState, useRef, useEffect } from 'react';
import { ArrowLeftRight, Check, ChevronDown, Globe, Search, Sparkles } from 'lucide-react';
import { LanguageInfo } from '../types';

interface LanguageSelectorProps {
  sourceLanguages?: LanguageInfo[];
  targetLanguages?: LanguageInfo[];
  selectedSource?: string;
  selectedTarget?: string;
  sourceLanguage?: string;
  targetLanguage?: string;
  onSourceChange: (code: string) => void;
  onTargetChange: (code: string) => void;
  disabled?: boolean;
  uiLang?: string;
  layout?: 'horizontal' | 'vertical';
}

export const LanguageSelector: React.FC<LanguageSelectorProps> = ({
  sourceLanguages,
  targetLanguages,
  selectedSource,
  selectedTarget,
  sourceLanguage,
  targetLanguage,
  onSourceChange,
  onTargetChange,
  disabled = false,
  uiLang = 'km',
  layout = 'vertical',
}) => {
  const isVertical = layout === 'vertical';
  const isKm = uiLang === 'km';
  const actualSource = selectedSource || sourceLanguage || 'auto';
  const actualTarget = selectedTarget || targetLanguage || 'km';

  const srcList = sourceLanguages && sourceLanguages.length > 0 ? sourceLanguages : [
    { code: 'auto', name: 'Auto Detect', native_name: 'ស្វ័យប្រវត្តិ', flag: '✨', asr_supported: true, translation_supported: true, tts_supported: false },
    { code: 'km', name: 'Khmer', native_name: 'ភាសាខ្មែរ', flag: '🇰🇭', asr_supported: true, translation_supported: true, tts_supported: true },
    { code: 'en', name: 'English', native_name: 'English', flag: '🇺🇸', asr_supported: true, translation_supported: true, tts_supported: true },
    { code: 'zh', name: 'Chinese', native_name: '中文', flag: '🇨🇳', asr_supported: true, translation_supported: true, tts_supported: true },
    { code: 'fr', name: 'French', native_name: 'Français', flag: '🇫🇷', asr_supported: true, translation_supported: true, tts_supported: true },
  ];
  const tgtList = targetLanguages && targetLanguages.length > 0 ? targetLanguages : [
    { code: 'km', name: 'Khmer', native_name: 'ភាសាខ្មែរ', flag: '🇰🇭', asr_supported: true, translation_supported: true, tts_supported: true },
    { code: 'en', name: 'English', native_name: 'English', flag: '🇺🇸', asr_supported: true, translation_supported: true, tts_supported: true },
    { code: 'zh', name: 'Chinese', native_name: '中文', flag: '🇨🇳', asr_supported: true, translation_supported: true, tts_supported: true },
    { code: 'fr', name: 'French', native_name: 'Français', flag: '🇫🇷', asr_supported: true, translation_supported: true, tts_supported: true },
  ];

  const [sourceOpen, setSourceOpen] = useState(false);
  const [targetOpen, setTargetOpen] = useState(false);
  const [sourceSearch, setSourceSearch] = useState('');
  const [targetSearch, setTargetSearch] = useState('');

  const sourceRef = useRef<HTMLDivElement>(null);
  const targetRef = useRef<HTMLDivElement>(null);

  // Close dropdowns on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (sourceRef.current && !sourceRef.current.contains(e.target as Node)) {
        setSourceOpen(false);
      }
      if (targetRef.current && !targetRef.current.contains(e.target as Node)) {
        setTargetOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const curSource = srcList.find((l) => l.code === actualSource) || {
    code: actualSource,
    name: actualSource === 'auto' ? 'Auto Detect' : actualSource,
    native_name: actualSource === 'auto' ? 'ស្វែងរកស្វ័យប្រវត្តិ' : actualSource,
    flag: actualSource === 'auto' ? '🌐' : '🌐',
    asr_supported: true,
    translation_supported: true,
    tts_supported: false,
  };

  const curTarget = tgtList.find((l) => l.code === actualTarget) || {
    code: actualTarget,
    name: actualTarget,
    native_name: actualTarget,
    flag: '🌐',
    asr_supported: true,
    translation_supported: true,
    tts_supported: true,
  };

  const filteredSources = srcList.filter(
    (l) =>
      l.name.toLowerCase().includes(sourceSearch.toLowerCase()) ||
      l.native_name.toLowerCase().includes(sourceSearch.toLowerCase()) ||
      l.code.toLowerCase().includes(sourceSearch.toLowerCase())
  );

  const filteredTargets = tgtList.filter(
    (l) =>
      l.name.toLowerCase().includes(targetSearch.toLowerCase()) ||
      l.native_name.toLowerCase().includes(targetSearch.toLowerCase()) ||
      l.code.toLowerCase().includes(targetSearch.toLowerCase())
  );

  const canSwap = actualSource !== 'auto' && actualSource !== actualTarget;

  const handleSwap = () => {
    if (!canSwap || disabled) return;
    const temp = actualSource;
    onSourceChange(actualTarget);
    onTargetChange(temp);
  };

  return (
    <div className="language-selector-root relative rounded-2xl bg-gradient-to-r from-emerald-950/70 via-slate-900/80 to-amber-950/60 p-3.5 border border-emerald-500/30 shadow-xl backdrop-blur-md w-full min-w-0 box-border">
      <div className={`flex ${isVertical ? 'flex-col gap-2' : 'flex-col md:flex-row items-stretch md:items-center justify-between gap-3'}`}>
        {/* Source Language Picker */}
        <div className="flex-1 relative w-full min-w-0" ref={sourceRef}>
          <label className="block text-xs font-semibold text-emerald-400/90 mb-1.5 flex items-center gap-1.5">
            <Globe className="w-3.5 h-3.5 text-emerald-400" />
            {isKm ? 'ភាសាដើម (Source Language)' : 'Source Language (Original Speech)'}
          </label>
          <button
            type="button"
            disabled={disabled}
            onClick={() => {
              setSourceOpen(!sourceOpen);
              setTargetOpen(false);
            }}
            className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl border bg-slate-950/80 transition-all text-left ${
              sourceOpen
                ? 'border-emerald-400 shadow-lg shadow-emerald-500/20'
                : 'border-slate-800 hover:border-emerald-500/40'
            } ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
          >
            <div className="flex items-center gap-2.5 truncate min-w-0">
              <span className="text-xl leading-none shrink-0">{curSource.flag}</span>
              <div className="truncate min-w-0">
                <div className="text-sm font-semibold text-slate-100 truncate">
                  {curSource.native_name}
                </div>
                <div className="text-xs text-slate-400 truncate">{curSource.name}</div>
              </div>
            </div>
            <ChevronDown
              className={`w-4 h-4 text-emerald-400 shrink-0 transition-transform ${
                sourceOpen ? 'rotate-180' : ''
              }`}
            />
          </button>

          {/* Source Dropdown Menu */}
          {sourceOpen && (
            <div className="absolute z-50 mt-1.5 w-full left-0 right-0 max-w-full rounded-xl bg-slate-900 border border-emerald-500/40 shadow-2xl overflow-hidden backdrop-blur-xl animate-in fade-in zoom-in-95 duration-150">
              <div className="p-2 border-b border-slate-800 bg-slate-950/60">
                <div className="relative">
                  <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
                  <input
                    type="text"
                    value={sourceSearch}
                    onChange={(e) => setSourceSearch(e.target.value)}
                    placeholder={isKm ? 'ស្វែងរកភាសា...' : 'Search language...'}
                    className="w-full pl-8 pr-3 py-1.5 text-xs rounded-lg bg-slate-800/80 border border-slate-700 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-400"
                    autoFocus
                  />
                </div>
              </div>
              <div className="max-h-60 overflow-y-auto p-1 divide-y divide-slate-800/50">
                {filteredSources.map((lang) => {
                  const isSelected = lang.code === actualSource;
                  return (
                    <button
                      key={lang.code}
                      type="button"
                      onClick={() => {
                        onSourceChange(lang.code);
                        setSourceOpen(false);
                        setSourceSearch('');
                      }}
                      className={`w-full flex items-center justify-between px-3 py-2 text-xs rounded-lg transition-colors ${
                        isSelected
                          ? 'bg-emerald-600/30 text-emerald-200 font-semibold'
                          : 'text-slate-300 hover:bg-slate-800/80'
                      }`}
                    >
                      <div className="flex items-center gap-2 truncate min-w-0">
                        <span className="text-base shrink-0">{lang.flag}</span>
                        <div className="truncate text-left min-w-0">
                          <div className="text-slate-100">{lang.native_name}</div>
                          <div className="text-[10px] text-slate-400">{lang.name}</div>
                        </div>
                      </div>
                      {isSelected && <Check className="w-3.5 h-3.5 text-emerald-400 shrink-0" />}
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* Swap Button & Divider */}
        {isVertical ? (
          <div className="flex items-center justify-center gap-2 my-0.5 shrink-0 w-full">
            <div className="h-px bg-slate-800/80 flex-1" />
            <button
              type="button"
              disabled={!canSwap || disabled}
              onClick={handleSwap}
              title={
                canSwap
                  ? isKm
                    ? 'ប្តូរភាសាដើម និងគោលដៅ'
                    : 'Swap Source & Target Languages'
                  : isKm
                  ? 'មិនអាចប្តូរបានទេ (Auto Detect)'
                  : 'Cannot swap Auto Detect'
              }
              className={`p-1.5 rounded-full border transition-all ${
                canSwap && !disabled
                  ? 'bg-emerald-600/20 border-amber-500/40 text-amber-300 hover:bg-emerald-600/40 hover:scale-105 active:scale-95 shadow-md shadow-emerald-950'
                  : 'bg-slate-800/40 border-slate-800 text-slate-600 cursor-not-allowed opacity-50'
              }`}
            >
              <ArrowLeftRight className="w-3.5 h-3.5" />
            </button>
            <div className="h-px bg-slate-800/80 flex-1" />
          </div>
        ) : (
          <div className="flex flex-row md:flex-col items-center justify-center gap-1 shrink-0 self-center">
            <button
              type="button"
              disabled={!canSwap || disabled}
              onClick={handleSwap}
              title={
                canSwap
                  ? isKm
                    ? 'ប្តូរភាសាដើម និងគោលដៅ'
                    : 'Swap Source & Target Languages'
                  : isKm
                  ? 'មិនអាចប្តូរបានទេ (Auto Detect)'
                  : 'Cannot swap Auto Detect'
              }
              className={`p-2.5 rounded-full border transition-all ${
                canSwap && !disabled
                  ? 'bg-emerald-600/20 border-amber-500/40 text-amber-300 hover:bg-emerald-600/40 hover:scale-105 active:scale-95 shadow-md shadow-emerald-950'
                  : 'bg-slate-800/40 border-slate-800 text-slate-600 cursor-not-allowed opacity-50'
              }`}
            >
              <ArrowLeftRight className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Target Language Picker */}
        <div className="flex-1 relative w-full min-w-0" ref={targetRef}>
          <label className="block text-xs font-semibold text-amber-400/90 mb-1.5 flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-amber-400" />
            {isKm ? 'ភាសាគោលដៅ (Target Translation & Dubbing)' : 'Target Language (Translation & Dubbing)'}
          </label>
          <button
            type="button"
            disabled={disabled}
            onClick={() => {
              setTargetOpen(!targetOpen);
              setSourceOpen(false);
            }}
            className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl border bg-slate-950/80 transition-all text-left ${
              targetOpen
                ? 'border-amber-400 shadow-lg shadow-amber-500/20'
                : 'border-slate-800 hover:border-amber-500/40'
            } ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
          >
            <div className="flex items-center gap-2.5 truncate min-w-0">
              <span className="text-xl leading-none shrink-0">{curTarget.flag}</span>
              <div className="truncate min-w-0">
                <div className="text-sm font-semibold text-slate-100 truncate">
                  {curTarget.native_name}
                </div>
                <div className="text-xs text-slate-400 truncate">{curTarget.name}</div>
              </div>
            </div>
            <ChevronDown
              className={`w-4 h-4 text-amber-400 shrink-0 transition-transform ${
                targetOpen ? 'rotate-180' : ''
              }`}
            />
          </button>

          {/* Target Dropdown Menu */}
          {targetOpen && (
            <div className="absolute z-50 mt-1.5 w-full left-0 right-0 max-w-full rounded-xl bg-slate-900 border border-amber-500/40 shadow-2xl overflow-hidden backdrop-blur-xl animate-in fade-in zoom-in-95 duration-150">
              <div className="p-2 border-b border-slate-800 bg-slate-950/60">
                <div className="relative">
                  <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
                  <input
                    type="text"
                    value={targetSearch}
                    onChange={(e) => setTargetSearch(e.target.value)}
                    placeholder={isKm ? 'ស្វែងរកភាសាគោលដៅ...' : 'Search target language...'}
                    className="w-full pl-8 pr-3 py-1.5 text-xs rounded-lg bg-slate-800/80 border border-slate-700 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-amber-400"
                    autoFocus
                  />
                </div>
              </div>
              <div className="max-h-60 overflow-y-auto p-1 divide-y divide-slate-800/50">
                {filteredTargets.map((lang) => {
                  const isSelected = lang.code === actualTarget;
                  return (
                    <button
                      key={lang.code}
                      type="button"
                      onClick={() => {
                        onTargetChange(lang.code);
                        setTargetOpen(false);
                        setTargetSearch('');
                      }}
                      className={`w-full flex items-center justify-between px-3 py-2 text-xs rounded-lg transition-colors ${
                        isSelected
                          ? 'bg-amber-600/30 text-amber-200 font-semibold'
                          : 'text-slate-300 hover:bg-slate-800/80'
                      }`}
                    >
                      <div className="flex items-center gap-2 truncate min-w-0">
                        <span className="text-base shrink-0">{lang.flag}</span>
                        <div className="truncate text-left min-w-0">
                          <div className="text-slate-100">{lang.native_name}</div>
                          <div className="text-[10px] text-slate-400">{lang.name}</div>
                        </div>
                      </div>
                      {isSelected && <Check className="w-3.5 h-3.5 text-amber-400 shrink-0" />}
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Direction summary banner */}
      <div className="mt-2.5 pt-2 border-t border-slate-800/60 flex flex-wrap items-center justify-between gap-2 text-[11px] text-slate-400">
        <div className="flex items-center gap-1.5 truncate">
          <span className="text-slate-500">{isKm ? 'ទិសដៅ:' : 'Direction:'}</span>
          <span className="font-semibold text-emerald-300 flex items-center gap-1 truncate">
            <span>{curSource.flag}</span> {curSource.name}
          </span>
          <span className="text-slate-500">➔</span>
          <span className="font-semibold text-amber-300 flex items-center gap-1 truncate">
            <span>{curTarget.flag}</span> {curTarget.name}
          </span>
        </div>
        <div className="flex items-center gap-1.5 text-[10px] text-slate-500 shrink-0">
          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-emerald-950/80 text-emerald-400 border border-emerald-800/40">
            ASR ✓
          </span>
          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-amber-950/80 text-amber-400 border border-amber-800/40">
            TTS ✓
          </span>
        </div>
      </div>
    </div>
  );
};
