import React, { useState } from 'react';
import {
  Users,
  Mic2,
  Volume2,
  Play,
  Square,
  Edit2,
  Check,
  Combine,
  Sparkles,
  Gauge,
  Sliders,
  AlertCircle,
  HelpCircle,
  ChevronDown,
} from 'lucide-react';
import { SpeakerProfile, VoiceInfo, TranscriptSegment, Job } from '../types';

interface CharacterVoiceStudioProps {
  job?: Job | null;
  speakers: SpeakerProfile[];
  availableVoices?: VoiceInfo[];
  targetLanguage: string;
  transcript?: TranscriptSegment[];
  translation?: TranscriptSegment[];
  API?: string;
  onUpdateSpeakers: (updated: SpeakerProfile[]) => void;
  onMergeSpeakers: (keepId: string, mergeId: string) => Promise<void>;
  onSplitSpeaker?: (speakerId: string, segmentIds: number[], newName?: string) => Promise<void>;
  onRefreshJob?: () => Promise<void>;
  setNotice?: (msg: string) => void;
  setError?: (msg: string) => void;
  disabled?: boolean;
  uiLang?: string;
}

export const CharacterVoiceStudio: React.FC<CharacterVoiceStudioProps> = ({
  job,
  speakers,
  availableVoices,
  targetLanguage,
  transcript,
  translation,
  API = '',
  onUpdateSpeakers,
  onMergeSpeakers,
  onSplitSpeaker,
  disabled = false,
  uiLang = 'km',
}) => {
  const isKm = uiLang === 'km';
  const [editingSpeakerId, setEditingSpeakerId] = useState<string | null>(null);
  const [editedName, setEditedName] = useState('');
  const [playingVoiceId, setPlayingVoiceId] = useState<string | null>(null);
  const [audioElement, setAudioElement] = useState<HTMLAudioElement | null>(null);
  const [mergeTarget, setMergeTarget] = useState<{ [key: string]: string }>({});
  const [voiceList, setVoiceList] = useState<VoiceInfo[]>(availableVoices || []);

  React.useEffect(() => {
    if (availableVoices && availableVoices.length > 0) {
      setVoiceList(availableVoices);
      return;
    }
    const apiBase = API || '';
    fetch(`${apiBase}/api/dubbing/voices?target_language=${encodeURIComponent(targetLanguage || 'km')}`)
      .then((r) => r.json())
      .then((data) => {
        if (Array.isArray(data)) setVoiceList(data);
      })
      .catch(() => {});
  }, [targetLanguage, availableVoices, API]);

  const handlePlayVoiceSample = async (voiceId: string) => {
    if (!voiceId) return;
    if (audioElement) {
      audioElement.pause();
      if (playingVoiceId === voiceId) {
        setPlayingVoiceId(null);
        return;
      }
    }

    setPlayingVoiceId(voiceId);
    try {
      const formData = new FormData();
      formData.append('voice_id', voiceId);
      const apiBase = API || '';
      const res = await fetch(`${apiBase}/api/dubbing/sample`, {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) throw new Error('Sample fetch failed');
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      setAudioElement(audio);
      audio.onended = () => setPlayingVoiceId(null);
      audio.onerror = () => setPlayingVoiceId(null);
      await audio.play();
    } catch (err) {
      console.error('Failed to preview voice sample', err);
      setPlayingVoiceId(null);
    }
  };

  const handleSaveName = (speakerId: string) => {
    if (!editedName.trim()) return;
    const updated = speakers.map((s) =>
      s.speaker_id === speakerId ? { ...s, name: editedName.trim() } : s
    );
    onUpdateSpeakers(updated);
    setEditingSpeakerId(null);
  };

  const handleVoiceChange = (speakerId: string, newVoiceId: string) => {
    const updated = speakers.map((s) =>
      s.speaker_id === speakerId
        ? { ...s, assigned_voice_id: newVoiceId, voice_id: newVoiceId }
        : s
    );
    onUpdateSpeakers(updated);
  };

  const handleRateChange = (speakerId: string, rate: number) => {
    const updated = speakers.map((s) =>
      s.speaker_id === speakerId ? { ...s, speech_rate: rate } : s
    );
    onUpdateSpeakers(updated);
  };

  const handleGenderChange = (speakerId: string, gender: string) => {
    const updated = speakers.map((s) =>
      s.speaker_id === speakerId ? { ...s, gender_presentation: gender } : s
    );
    onUpdateSpeakers(updated);
  };

  const handleAgeChange = (speakerId: string, age: string) => {
    const updated = speakers.map((s) =>
      s.speaker_id === speakerId ? { ...s, age_impression: age } : s
    );
    onUpdateSpeakers(updated);
  };

  const genderBadgeColor = (gender: string) => {
    switch (gender.toLowerCase()) {
      case 'masculine':
        return 'bg-blue-950/80 text-blue-300 border-blue-800/40';
      case 'feminine':
        return 'bg-pink-950/80 text-pink-300 border-pink-800/40';
      default:
        return 'bg-slate-800/80 text-slate-300 border-slate-700';
    }
  };

  const ageBadgeColor = (age: string) => {
    switch (age.toLowerCase()) {
      case 'childlike':
        return 'bg-amber-950/80 text-amber-300 border-amber-800/40';
      case 'young_adult':
        return 'bg-emerald-950/80 text-emerald-300 border-emerald-800/40';
      case 'mature':
      case 'elderly':
        return 'bg-purple-950/80 text-purple-300 border-purple-800/40';
      default:
        return 'bg-slate-800/80 text-slate-300 border-slate-700';
    }
  };

  if (!speakers || speakers.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-emerald-500/30 bg-slate-900/60 p-8 text-center backdrop-blur-md">
        <Users className="w-12 h-12 text-emerald-400/60 mx-auto mb-3 animate-pulse" />
        <h3 className="text-base font-semibold text-slate-200 mb-1">
          {isKm ? 'មិនទាន់មានទិន្នន័យតួអង្គ (No Speakers Detected)' : 'No Speakers Detected Yet'}
        </h3>
        <p className="text-xs text-slate-400 max-w-md mx-auto">
          {isKm
            ? 'ដំណើរការ Transcribe វីដេអូ ដើម្បីស្គាល់តួអង្គនិយាយ (Speaker Diarization) ដោយស្វ័យប្រវត្តិ។'
            : 'Transcribe the video to automatically detect characters, speech timestamps, and acoustic voice profiles.'}
        </p>
      </div>
    );
  }

  return (
    <div className="character-voice-studio space-y-4">
      {/* Studio Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-3.5 rounded-xl bg-slate-900/90 border border-emerald-500/30">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-lg bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
            <Users className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              {isKm ? 'ស្ទូឌីយោតួអង្គ និងសំឡេង (Character Voice Studio)' : 'Character Voice Studio'}
              <span className="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-950 text-emerald-300 border border-emerald-700/50">
                {speakers.length} {isKm ? 'តួអង្គ' : 'Characters'}
              </span>
            </h3>
            <p className="text-xs text-slate-400">
              {isKm
                ? 'កំណត់សំឡេង ភេទ អាយុ និងល្បឿននិយាយតាមតួអង្គនីមួយៗ'
                : 'Manage detected speakers, assign target-language neural voices, and calibrate speaking speed.'}
            </p>
          </div>
        </div>
      </div>

      {/* Speaker Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {speakers.map((spk, idx) => {
          const isEditing = editingSpeakerId === spk.speaker_id;
          const assignedVoice = voiceList.find(
            (v) => v.id === (spk.assigned_voice_id || spk.voice_id)
          ) || voiceList[0] || {
            id: spk.assigned_voice_id || 'NeuralVoice',
            name: spk.assigned_voice_id || 'Neural Voice',
            gender: 'Male',
            language: targetLanguage,
            recommended: true,
          };

          return (
            <div
              key={spk.speaker_id}
              className="rounded-2xl border border-slate-800 hover:border-emerald-500/40 bg-gradient-to-br from-slate-900/90 via-slate-950 to-slate-900/90 p-4 shadow-xl backdrop-blur-md transition-all hover:shadow-emerald-950/30 flex flex-col justify-between gap-3.5"
            >
              {/* Card Header */}
              <div>
                <div className="flex items-center justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2 flex-1 min-w-0">
                    <span className="px-2 py-0.5 rounded-md text-[10px] font-mono font-bold bg-slate-800 text-amber-300 border border-amber-500/30">
                      #{idx + 1}
                    </span>
                    {isEditing ? (
                      <div className="flex items-center gap-1 flex-1">
                        <input
                          type="text"
                          value={editedName}
                          onChange={(e) => setEditedName(e.target.value)}
                          className="px-2 py-1 text-xs rounded bg-slate-950 border border-emerald-400 text-slate-100 focus:outline-none w-full"
                          autoFocus
                          onKeyDown={(e) => e.key === 'Enter' && handleSaveName(spk.speaker_id)}
                        />
                        <button
                          type="button"
                          onClick={() => handleSaveName(spk.speaker_id)}
                          className="p-1 rounded bg-emerald-600 text-white hover:bg-emerald-500"
                        >
                          <Check className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    ) : (
                      <div className="flex items-center gap-1.5 flex-1 min-w-0">
                        <h4 className="text-sm font-bold text-slate-100 truncate">
                          {spk.name}
                        </h4>
                        <button
                          type="button"
                          disabled={disabled}
                          onClick={() => {
                            setEditingSpeakerId(spk.speaker_id);
                            setEditedName(spk.name);
                          }}
                          className="text-slate-500 hover:text-emerald-400 transition-colors p-0.5"
                          title={isKm ? 'កែប្រែឈ្មោះតួអង្គ' : 'Rename character'}
                        >
                          <Edit2 className="w-3 h-3" />
                        </button>
                      </div>
                    )}
                  </div>

                  {/* Confidence Pill */}
                  <span
                    className="text-[10px] px-2 py-0.5 rounded-full font-semibold bg-emerald-950/60 text-emerald-400 border border-emerald-800/40 shrink-0"
                    title={`Confidence: ${Math.round((spk.confidence || 0.85) * 100)}%`}
                  >
                    {Math.round((spk.confidence || 0.85) * 100)}% Match
                  </span>
                </div>

                {/* Profile Traits */}
                <div className="flex flex-wrap items-center gap-1.5 mb-3">
                  {/* Gender Selector Badge */}
                  <select
                    disabled={disabled}
                    value={spk.gender_presentation || 'uncertain'}
                    onChange={(e) => handleGenderChange(spk.speaker_id, e.target.value)}
                    className={`text-[10px] font-semibold px-2 py-0.5 rounded-md border focus:outline-none cursor-pointer ${genderBadgeColor(
                      spk.gender_presentation || 'uncertain'
                    )}`}
                  >
                    <option value="masculine">♂ Masculine (បុរស)</option>
                    <option value="feminine">♀ Feminine (នារី)</option>
                    <option value="uncertain">? Neutral / Uncertain</option>
                  </select>

                  {/* Age Selector Badge */}
                  <select
                    disabled={disabled}
                    value={spk.age_impression || 'adult'}
                    onChange={(e) => handleAgeChange(spk.speaker_id, e.target.value)}
                    className={`text-[10px] font-semibold px-2 py-0.5 rounded-md border focus:outline-none cursor-pointer ${ageBadgeColor(
                      spk.age_impression || 'adult'
                    )}`}
                  >
                    <option value="childlike">Childlike (កុមារ)</option>
                    <option value="young_adult">Young Adult (យុវវ័យ)</option>
                    <option value="adult">Adult (មនុស្សពេញវ័យ)</option>
                    <option value="mature">Mature / Elderly (វ័យចំណាស់)</option>
                  </select>

                  {/* Pitch / Hz trait */}
                  {spk.pitch_hz && (
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-slate-800/80 text-slate-300 border border-slate-700">
                      {Math.round(spk.pitch_hz)} Hz
                    </span>
                  )}

                  {/* Segment Count trait */}
                  <span className="text-[10px] px-2 py-0.5 rounded-md bg-slate-800/60 text-slate-400 border border-slate-700/50">
                    {spk.segment_count || 0} {isKm ? 'ឃ្លា' : 'lines'}
                  </span>
                </div>

                {/* Assigned Neural Voice Picker */}
                <div className="space-y-1.5 bg-slate-950/70 p-2.5 rounded-xl border border-slate-800">
                  <label className="text-[11px] font-semibold text-slate-300 flex items-center justify-between">
                    <span className="flex items-center gap-1.5 text-amber-300">
                      <Mic2 className="w-3.5 h-3.5" />
                      {isKm ? 'សំឡេងនិយាយកំណត់ (Assigned Neural Voice):' : 'Assigned Neural Voice:'}
                    </span>
                    <span className="text-[10px] text-slate-500 font-normal">
                      Target: {targetLanguage.toUpperCase()}
                    </span>
                  </label>
                  <div className="flex items-center gap-2">
                    <select
                      disabled={disabled}
                      value={spk.assigned_voice_id || spk.voice_id || ''}
                      onChange={(e) => handleVoiceChange(spk.speaker_id, e.target.value)}
                      className="flex-1 text-xs px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-slate-100 focus:outline-none focus:border-amber-400 cursor-pointer"
                    >
                      {voiceList.map((v) => (
                        <option key={v.id} value={v.id}>
                          {v.name} ({v.gender}) {v.recommended ? '★ Recommended' : ''}
                        </option>
                      ))}
                    </select>

                    {/* Preview Voice Button */}
                    <button
                      type="button"
                      disabled={disabled}
                      onClick={() => {
                        const vid = spk.assigned_voice_id || spk.voice_id || (voiceList[0]?.id || '');
                        if (vid) handlePlayVoiceSample(vid);
                      }}
                      title={isKm ? 'ស្តាប់សំឡេងគំរូ' : 'Preview voice sample'}
                      className={`p-2 rounded-lg border transition-all ${
                        playingVoiceId === (spk.assigned_voice_id || spk.voice_id)
                          ? 'bg-amber-500 text-slate-950 border-amber-400 animate-pulse'
                          : 'bg-slate-800 hover:bg-slate-700 text-amber-300 border-slate-700'
                      }`}
                    >
                      {playingVoiceId === (spk.assigned_voice_id || spk.voice_id) ? (
                        <Square className="w-3.5 h-3.5 fill-current" />
                      ) : (
                        <Play className="w-3.5 h-3.5 fill-current" />
                      )}
                    </button>
                  </div>
                </div>

                {/* Speech Rate Slider */}
                <div className="mt-2.5 px-2.5 py-2 rounded-xl bg-slate-950/40 border border-slate-800/80">
                  <div className="flex items-center justify-between text-[11px] text-slate-400 mb-1">
                    <span className="flex items-center gap-1">
                      <Gauge className="w-3 h-3 text-slate-500" />
                      {isKm ? 'ល្បឿននិយាយ (Speed):' : 'Speaking Rate:'}
                    </span>
                    <span className="font-mono text-emerald-400">
                      {(spk.speech_rate || 0) >= 0 ? `+${spk.speech_rate || 0}%` : `${spk.speech_rate || 0}%`}
                    </span>
                  </div>
                  <input
                    type="range"
                    min="-20"
                    max="30"
                    step="5"
                    value={spk.speech_rate || 0}
                    disabled={disabled}
                    onChange={(e) => handleRateChange(spk.speaker_id, parseInt(e.target.value, 10))}
                    className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-emerald-500"
                  />
                </div>

                {/* Sample Dialogue Snippet */}
                {spk.sample_dialogue && spk.sample_dialogue.length > 0 && (
                  <div className="mt-2.5 text-[11px] text-slate-400 bg-slate-950/60 p-2 rounded-lg border border-slate-800/60 line-clamp-2 italic">
                    "{spk.sample_dialogue[0]}"
                  </div>
                )}
              </div>

              {/* Character Tools: Merge */}
              {speakers.length > 1 && (
                <div className="pt-2 border-t border-slate-800/60 flex items-center justify-between gap-2 text-xs">
                  <span className="text-[10px] text-slate-500 flex items-center gap-1">
                    <Combine className="w-3 h-3 text-slate-500" />
                    {isKm ? 'ច្របាច់បញ្ចូល:' : 'Merge into:'}
                  </span>
                  <div className="flex items-center gap-1.5">
                    <select
                      disabled={disabled}
                      value={mergeTarget[spk.speaker_id] || ''}
                      onChange={(e) =>
                        setMergeTarget({ ...mergeTarget, [spk.speaker_id]: e.target.value })
                      }
                      className="text-[11px] px-2 py-1 rounded bg-slate-900 border border-slate-700 text-slate-200 focus:outline-none"
                    >
                      <option value="">{isKm ? 'ជ្រើសរើស...' : 'Select speaker...'}</option>
                      {speakers
                        .filter((other) => other.speaker_id !== spk.speaker_id)
                        .map((other) => (
                          <option key={other.speaker_id} value={other.speaker_id}>
                            {other.name}
                          </option>
                        ))}
                    </select>
                    <button
                      type="button"
                      disabled={disabled || !mergeTarget[spk.speaker_id]}
                      onClick={() => {
                        const targetId = mergeTarget[spk.speaker_id];
                        if (targetId) {
                          onMergeSpeakers(targetId, spk.speaker_id);
                        }
                      }}
                      className="px-2 py-1 text-[10px] font-semibold rounded bg-amber-600/20 text-amber-300 border border-amber-600/40 hover:bg-amber-600/40 disabled:opacity-40 transition-colors"
                    >
                      {isKm ? 'ច្របាច់' : 'Merge'}
                    </button>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
