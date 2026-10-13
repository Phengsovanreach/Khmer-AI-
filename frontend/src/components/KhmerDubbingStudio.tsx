import React, { useState, useEffect } from 'react';
import {
  AudioLines,
  Volume2,
  VolumeX,
  Play,
  Pause,
  Download,
  Sparkles,
  Sliders,
  CheckCircle2,
  Loader2,
  FileAudio,
  Users,
} from 'lucide-react';
import { motion } from 'framer-motion';
import { Job, VoiceInfo, SpeakerProfile } from '../types';
import { AuthService } from '../services/authService';

interface KhmerDubbingStudioProps {
  job: Job;
  API: string;
  voices: VoiceInfo[];
  targetLanguage?: string;
  speakers?: SpeakerProfile[];
  onRefreshJob: () => Promise<void>;
  setNotice: (msg: string) => void;
  setError: (msg: string) => void;
}

export const KhmerDubbingStudio: React.FC<KhmerDubbingStudioProps> = ({
  job,
  API,
  voices,
  targetLanguage = 'km',
  speakers = [],
  onRefreshJob,
  setNotice,
  setError,
}) => {
  const [selectedVoice, setSelectedVoice] = useState<string>(
    voices[0]?.id || 'km-KH-PisethNeural'
  );
  const [voiceVolume, setVoiceVolume] = useState<number>(1.0);
  const [originalVolume, setOriginalVolume] = useState<number>(0.2);
  const [mixOriginal, setMixOriginal] = useState<boolean>(true);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);

  // Sample playback state
  const [isPlayingSample, setIsPlayingSample] = useState<boolean>(false);
  const [sampleAudio, setSampleAudio] = useState<HTMLAudioElement | null>(null);

  // Sync default voice when voices prop changes
  useEffect(() => {
    if (voices.length > 0 && !voices.some((v) => v.id === selectedVoice)) {
      setSelectedVoice(voices[0].id);
    }
  }, [voices]);

  // Play Sample Audio
  const handlePlaySample = async (voiceId: string) => {
    if (sampleAudio) {
      sampleAudio.pause();
      setIsPlayingSample(false);
    }
    try {
      const audioUrl = `${API}/api/dubbing/sample`;
      const formData = new FormData();
      formData.append('voice_id', voiceId);

      const res = await fetch(audioUrl, {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) throw new Error('Could not fetch voice sample');
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      setSampleAudio(audio);
      setIsPlayingSample(true);
      audio.onended = () => setIsPlayingSample(false);
      audio.onerror = () => setIsPlayingSample(false);
      await audio.play();
    } catch (err: any) {
      setError(`បរាជ័យក្នុងការចាក់សំឡេងគំរូ: ${err.message || err}`);
      setIsPlayingSample(false);
    }
  };

  // Generate Dubbing with multi-speaker voice mappings
  const handleGenerateDubbing = async () => {
    setIsGenerating(true);
    try {
      const speakerVoices: Record<string, string> = {};
      const speakerRates: Record<string, number> = {};
      (job.speakers || speakers).forEach((spk) => {
        if (spk.speaker_id && spk.assigned_voice_id) {
          speakerVoices[spk.speaker_id] = spk.assigned_voice_id;
        }
        if (spk.speaker_id && spk.speech_rate) {
          speakerRates[spk.speaker_id] = spk.speech_rate;
        }
      });

      const authHeaders = AuthService.getAuthHeaders();
      const res = await fetch(`${API}/api/jobs/${job.id}/dub`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...authHeaders,
        },
        credentials: 'include',
        body: JSON.stringify({
          voice_id: selectedVoice,
          target_language: targetLanguage,
          speaker_voices: speakerVoices,
          speaker_rates: speakerRates,
          voice_volume: voiceVolume,
          original_volume: originalVolume,
          mix_original: mixOriginal,
        }),
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Dubbing generation failed');
      }

      await onRefreshJob();
      setNotice('ការបង្កើតសំឡេង AI Dubbing ទទួលបានជោគជ័យ!');
    } catch (err: any) {
      const errMsg = err?.message || String(err);
      if (errMsg.includes('Failed to fetch')) {
        setError(`កំហុសក្នុងការបង្កើត Dubbing: មិនអាចភ្ជាប់ទៅកាន់ម៉ាស៊ីនបម្រើ API (${API}) បានទេ។ សូមពិនិត្យមើលថាតើ Render Backend កំពុងដំណើរការ ឬរង់ចាំ cold start រួចចុចសាកល្បងម្តងទៀត។`);
      } else {
        setError(`កំហុសក្នុងការបង្កើត Dubbing: ${errMsg}`);
      }
    } finally {
      setIsGenerating(false);
    }
  };

  const hasSpeakers = (job.speakers && job.speakers.length > 0) || speakers.length > 0;
  const currentSpeakers = job.speakers && job.speakers.length > 0 ? job.speakers : speakers;

  return (
    <div className="space-y-4">
      {/* Studio Header Card */}
      <div className="p-4 rounded-2xl bg-gradient-to-r from-emerald-950/70 via-slate-900/80 to-amber-950/60 border border-emerald-500/30 backdrop-blur-md shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-amber-500/20 text-amber-300 border border-amber-500/30">
              <AudioLines className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                ស្ទូឌីយោបញ្ចេញសំឡេង AI (Neural Voice Dubbing Studio)
                <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-950 text-amber-300 border border-amber-700/50">
                  Target: {targetLanguage.toUpperCase()}
                </span>
              </h3>
              <p className="text-xs text-slate-400">
                សំយោគសំឡេងនិយាយ Neural TTS គុណភាពខ្ពស់ ដាក់តាម Timeline នៃ Subtitles
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={handleGenerateDubbing}
            disabled={isGenerating || (!job.translation?.length && !job.transcript?.length)}
            className={`px-4 py-2.5 rounded-xl text-xs font-bold transition-all shadow-lg flex items-center gap-2 ${
              isGenerating
                ? 'bg-amber-600/50 text-amber-200 cursor-wait'
                : 'bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 shadow-amber-950/50 hover:scale-105 active:scale-95'
            }`}
          >
            {isGenerating ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                កំពុងបង្កើតសំឡេង...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                បង្កើតសំឡេង AI Dubbing
              </>
            )}
          </button>
        </div>
      </div>

      {/* Multi-Speaker Status Banner */}
      {hasSpeakers && (
        <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center justify-between text-xs text-slate-300">
          <div className="flex items-center gap-2">
            <Users className="w-4 h-4 text-emerald-400" />
            <span>
              រកឃើញ <b>{currentSpeakers.length}</b> តួអង្គ (Speakers)។ ប្រព័ន្ធនឹងសំយោគសំឡេងតាមតួអង្គនីមួយៗដោយស្វ័យប្រវត្តិ។
            </span>
          </div>
          <span className="text-[10px] text-amber-400 font-semibold bg-amber-950/60 px-2 py-0.5 rounded border border-amber-800/40">
            Multi-Speaker Mode
          </span>
        </div>
      )}

      {/* Controls & Voices Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Left Column: Voice Picker */}
        <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-3">
          <h4 className="text-xs font-bold text-slate-200 flex items-center gap-2">
            <Sparkles className="w-3.5 h-3.5 text-amber-400" />
            សំឡេងដើមលំនាំដើម (Default Language Voice)
          </h4>

          <div className="space-y-2">
            {voices.map((v) => {
              const isSelected = selectedVoice === v.id;
              return (
                <div
                  key={v.id}
                  onClick={() => setSelectedVoice(v.id)}
                  className={`p-3 rounded-xl border transition-all cursor-pointer flex items-center justify-between gap-3 ${
                    isSelected
                      ? 'border-amber-400/80 bg-amber-950/30 shadow-md shadow-amber-950/20'
                      : 'border-slate-800 bg-slate-950/60 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center gap-2.5 truncate">
                    <div
                      className={`w-3 h-3 rounded-full border ${
                        isSelected ? 'bg-amber-400 border-amber-300' : 'border-slate-600'
                      }`}
                    />
                    <div className="truncate">
                      <div className="text-xs font-bold text-slate-100 truncate flex items-center gap-1.5">
                        {v.name}
                        {v.recommended && (
                          <span className="text-[10px] px-1.5 py-0.2 rounded bg-amber-500/20 text-amber-300 font-normal">
                            ★ ណែនាំ
                          </span>
                        )}
                      </div>
                      <div className="text-[10px] text-slate-400">
                        {v.gender} • {v.language || targetLanguage}
                      </div>
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      handlePlaySample(v.id);
                    }}
                    className={`px-2.5 py-1 text-xs rounded-lg border font-semibold flex items-center gap-1 transition-colors ${
                      isPlayingSample
                        ? 'bg-amber-500 text-slate-950 border-amber-400'
                        : 'bg-slate-800 text-amber-300 border-slate-700 hover:bg-slate-700'
                    }`}
                  >
                    <Play className="w-3 h-3 fill-current" /> ស្តាប់គំរូ
                  </button>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Column: Audio Ducking & Volume Controls */}
        <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
          <h4 className="text-xs font-bold text-slate-200 flex items-center gap-2">
            <Sliders className="w-3.5 h-3.5 text-emerald-400" />
            ការលាយសំឡេង និងសម្រួលកម្រិត (Audio Ducking)
          </h4>

          {/* Voice Volume */}
          <div>
            <div className="flex justify-between text-xs text-slate-300 mb-1.5">
              <span>កម្រិតសំឡេង AI Dubbed (Voice):</span>
              <span className="font-mono text-amber-400">{Math.round(voiceVolume * 100)}%</span>
            </div>
            <input
              type="range"
              min="0"
              max="2.0"
              step="0.05"
              value={voiceVolume}
              onChange={(e) => setVoiceVolume(parseFloat(e.target.value))}
              className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-amber-500"
            />
          </div>

          {/* Original Background Volume */}
          <div>
            <div className="flex justify-between text-xs text-slate-300 mb-1.5">
              <span>សំឡេងដើមនៃវីដេអូ (Background Media):</span>
              <span className="font-mono text-emerald-400">{Math.round(originalVolume * 100)}%</span>
            </div>
            <input
              type="range"
              min="0"
              max="1.0"
              step="0.05"
              value={originalVolume}
              onChange={(e) => setOriginalVolume(parseFloat(e.target.value))}
              className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-emerald-500"
            />
          </div>

          {/* Mix Toggle */}
          <div className="pt-2 border-t border-slate-800 flex items-center justify-between">
            <label className="text-xs text-slate-300 cursor-pointer flex items-center gap-2">
              <input
                type="checkbox"
                checked={mixOriginal}
                onChange={(e) => setMixOriginal(e.target.checked)}
                className="w-4 h-4 rounded text-amber-500 focus:ring-0 bg-slate-900 border-slate-700"
              />
              រក្សាទុកសំឡេងដើមនៃវីដេអូជាផ្ទៃខាងក្រោយ (Keep Background Audio)
            </label>
          </div>

          {/* Dubbed Audio Output Preview */}
          {job.has_dubbed_audio && job.dubbed_audio_url && (
            <div className="mt-3 p-3 rounded-xl bg-emerald-950/40 border border-emerald-500/40 space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-xs text-emerald-300">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <span>សំឡេង Dubbed រួចរាល់សម្រាប់ចាក់ ឬទាញយក</span>
                </div>
                <a
                  href={job.dubbed_audio_url.startsWith('http') ? job.dubbed_audio_url : `${API}${job.dubbed_audio_url}`}
                  download={`${job.id}_dubbed.mp3`}
                  className="px-2.5 py-1 text-xs font-semibold rounded-lg bg-emerald-600 text-white hover:bg-emerald-500 flex items-center gap-1 shadow-sm"
                >
                  <Download className="w-3.5 h-3.5" /> MP3
                </a>
              </div>
              <audio
                controls
                className="w-full h-8 rounded"
                src={job.dubbed_audio_url.startsWith('http') ? job.dubbed_audio_url : `${API}${job.dubbed_audio_url}`}
                preload="metadata"
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
