import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  MessageSquare,
  Bug,
  X,
  Minimize2,
  Send,
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  Copy,
  Check,
  RefreshCw,
  Search,
  ExternalLink,
} from 'lucide-react';

interface FloatingKhmerAIAgentProps {
  API_BASE?: string;
}

interface ChatMessage {
  id: string;
  sender: 'user' | 'agent';
  text: string;
  timestamp: string;
  suggestions?: string[];
}

export const FloatingKhmerAIAgent: React.FC<FloatingKhmerAIAgentProps> = ({ API_BASE = '' }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<'ask' | 'bug'>('ask');

  // ASK Mode State
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'init',
      sender: 'agent',
      text: 'សួស្តី! ខ្ញុំជា **Khmer AI Agent** ជំនួយការឆ្លាតវៃរបស់អ្នក។ តើខ្ញុំអាចជួយអ្វីបានទាក់ទងនឹងការបកប្រែវីដេអូ ឬបញ្ចូលសំឡេង Dubbing ថ្ងៃនេះ?',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      suggestions: [
        'តើធ្វើដូចម្តេចដើម្បីបញ្ចូលសំឡេង dubbing?',
        'តើប្រព័ន្ធនេះឥតគិតថ្លៃពិតមែនទេ?',
        'តើមានសំឡេងភាសាខ្មែរអ្វីខ្លះ?',
      ],
    },
  ]);
  const [inputQuestion, setInputQuestion] = useState('');
  const [isAsking, setIsAsking] = useState(false);

  // Bug Mode State
  const [bugDescription, setBugDescription] = useState('');
  const [bugErrorText, setBugErrorText] = useState('');
  const [bugSeverity, setBugSeverity] = useState('WARNING');
  const [bugContact, setBugContact] = useState('');
  const [isSubmittingBug, setIsSubmittingBug] = useState(false);
  const [submittedBugId, setSubmittedBugId] = useState<string | null>(null);
  const [bugCopied, setBugCopied] = useState(false);

  // Bug Status Lookup
  const [lookupId, setLookupId] = useState('');
  const [lookupResult, setLookupResult] = useState<{ id: string; status: string; summary: string } | null>(null);
  const [isLookingUp, setIsLookingUp] = useState(false);
  const [lookupError, setLookupError] = useState('');

  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen && activeTab === 'ask') {
      chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isOpen, activeTab]);

  const handleSendQuestion = async (queryText?: string) => {
    const q = (queryText || inputQuestion).trim();
    if (!q || isAsking) return;

    const userMsg: ChatMessage = {
      id: `usr_${Date.now()}`,
      sender: 'user',
      text: q,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputQuestion('');
    setIsAsking(true);

    try {
      const res = await fetch(`${API_BASE}/api/agent/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: q }),
      });

      if (!res.ok) throw new Error('Network error');
      const data = await res.json();

      const agentMsg: ChatMessage = {
        id: `agt_${Date.now()}`,
        sender: 'agent',
        text: data.answer || 'សូមអភ័យទោស ខ្ញុំមិនអាចទាញយកចម្លើយបាននៅពេលនេះទេ។',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        suggestions: data.suggestions || [],
      };
      setMessages((prev) => [...prev, agentMsg]);
    } catch {
      // Offline fallback
      const fallbackMsg: ChatMessage = {
        id: `agt_${Date.now()}`,
        sender: 'agent',
        text: 'សូមស្វាគមន៍! Khmer Translator AI គាំទ្រការបំប្លែងសំឡេងវីដេអូជាអក្សរ (Whisper) និងបញ្ចូលសំឡេង Dubbing ភាសាខ្មែរ (Sreymom & Piseth) ដោយឥតគិតថ្លៃ ១០០% អចិន្ត្រៃយ៍។ ប្រសិនបើមានបញ្ហាបច្ចេកទេស សូមប្តូរទៅកាន់ **Bug Mode** ដើម្បីរាយការណ៍។',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        suggestions: ['តើមានសំឡេងភាសាខ្មែរអ្វីខ្លះ?', 'តើប្រព័ន្ធនេះឥតគិតថ្លៃពិតមែនទេ?'],
      };
      setMessages((prev) => [...prev, fallbackMsg]);
    } finally {
      setIsAsking(false);
    }
  };

  const handleSubmitBug = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!bugDescription.trim() || isSubmittingBug) return;

    setIsSubmittingBug(true);
    try {
      const res = await fetch(`${API_BASE}/api/bugs/report`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          description: bugDescription,
          error_text: bugErrorText || undefined,
          page_url: window.location.pathname,
          severity: bugSeverity,
          user_contact: bugContact || undefined,
        }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Failed to submit bug report');
      }

      const data = await res.json();
      setSubmittedBugId(data.incident_id);
      setBugDescription('');
      setBugErrorText('');
    } catch (err: any) {
      alert(err.message || 'Error submitting bug report');
    } finally {
      setIsSubmittingBug(false);
    }
  };

  const handleLookupStatus = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!lookupId.trim() || isLookingUp) return;

    setIsLookingUp(true);
    setLookupError('');
    setLookupResult(null);

    try {
      const res = await fetch(`${API_BASE}/api/bugs/status/${lookupId.trim()}`);
      if (!res.ok) {
        throw new Error('រកមិនឃើញលេខយោងរបាយការណ៍នេះទេ (Report not found)');
      }
      const data = await res.json();
      setLookupResult({
        id: data.incident_id,
        status: data.status,
        summary: data.summary,
      });
    } catch (err: any) {
      setLookupError(err.message || 'Error looking up report status');
    } finally {
      setIsLookingUp(false);
    }
  };

  const copyIncidentId = () => {
    if (submittedBugId) {
      navigator.clipboard.writeText(submittedBugId);
      setBugCopied(true);
      setTimeout(() => setBugCopied(false), 2000);
    }
  };

  return (
    <>
      {/* Floating Bottom-Right Launcher Button */}
      <div
        style={{
          position: 'fixed',
          bottom: '24px',
          right: '24px',
          zIndex: 9999,
          display: isOpen ? 'none' : 'block',
        }}
      >
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => setIsOpen(true)}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            padding: '12px 18px',
            background: 'linear-gradient(135deg, rgba(20, 24, 33, 0.95) 0%, rgba(30, 36, 50, 0.95) 100%)',
            border: '1px solid rgba(212, 175, 55, 0.45)',
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.45), 0 0 15px rgba(212, 175, 55, 0.25)',
            borderRadius: '9999px',
            color: '#f8fafc',
            cursor: 'pointer',
            backdropFilter: 'blur(12px)',
            fontWeight: 600,
            fontSize: '14px',
          }}
          aria-label="Open Khmer AI Assistant"
        >
          <div
            style={{
              position: 'relative',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '28px',
              height: '28px',
              borderRadius: '50%',
              background: 'linear-gradient(135deg, #d4af37 0%, #00d2ff 100%)',
              color: '#0f172a',
            }}
          >
            <Sparkles size={16} />
            <span
              style={{
                position: 'absolute',
                top: -1,
                right: -1,
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                backgroundColor: '#10b981',
                boxShadow: '0 0 6px #10b981',
              }}
            />
          </div>
          <span>AI ជំនួយការ (AI Agent)</span>
        </motion.button>
      </div>

      {/* Floating Assistant Panel */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            transition={{ duration: 0.22 }}
            style={{
              position: 'fixed',
              bottom: '24px',
              right: '24px',
              width: '390px',
              maxWidth: 'calc(100vw - 32px)',
              height: '580px',
              maxHeight: 'calc(100vh - 100px)',
              zIndex: 9999,
              display: 'flex',
              flexDirection: 'column',
              background: 'rgba(15, 23, 42, 0.94)',
              border: '1px solid rgba(212, 175, 55, 0.35)',
              borderRadius: '16px',
              boxShadow: '0 20px 50px rgba(0, 0, 0, 0.6), 0 0 25px rgba(212, 175, 55, 0.15)',
              backdropFilter: 'blur(20px)',
              overflow: 'hidden',
              fontFamily: 'inherit',
            }}
          >
            {/* Header */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '12px 16px',
                background: 'rgba(30, 41, 59, 0.7)',
                borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div
                  style={{
                    width: '32px',
                    height: '32px',
                    borderRadius: '8px',
                    background: 'linear-gradient(135deg, #d4af37 0%, #00d2ff 100%)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#0f172a',
                  }}
                >
                  <Sparkles size={18} />
                </div>
                <div>
                  <div style={{ fontWeight: 600, fontSize: '14px', color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    Khmer AI Agent
                    <span style={{ fontSize: '10px', padding: '1px 6px', borderRadius: '4px', background: 'rgba(16, 185, 129, 0.2)', color: '#10b981' }}>
                      អនឡាញ
                    </span>
                  </div>
                  <div style={{ fontSize: '11px', color: '#94a3b8' }}>
                    ជំនួយការឆ្លាតវៃ & ស្វ័យព្យាបាល ២៤/៧
                  </div>
                </div>
              </div>
              <div style={{ display: 'flex', gap: '4px' }}>
                <button
                  onClick={() => setIsOpen(false)}
                  style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', padding: '6px' }}
                  aria-label="Minimize widget"
                >
                  <Minimize2 size={16} />
                </button>
                <button
                  onClick={() => setIsOpen(false)}
                  style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', padding: '6px' }}
                  aria-label="Close widget"
                >
                  <X size={16} />
                </button>
              </div>
            </div>

            {/* Mode Switcher Tabs */}
            <div
              style={{
                display: 'flex',
                padding: '6px 12px',
                background: 'rgba(15, 23, 42, 0.6)',
                borderBottom: '1px solid rgba(255, 255, 255, 0.06)',
                gap: '8px',
              }}
            >
              <button
                onClick={() => setActiveTab('ask')}
                style={{
                  flex: 1,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '6px',
                  padding: '8px 12px',
                  borderRadius: '8px',
                  fontSize: '12px',
                  fontWeight: 600,
                  cursor: 'pointer',
                  border: 'none',
                  background: activeTab === 'ask' ? 'rgba(212, 175, 55, 0.15)' : 'transparent',
                  color: activeTab === 'ask' ? '#d4af37' : '#94a3b8',
                  transition: 'all 0.15s ease',
                }}
              >
                <MessageSquare size={14} />
                សួរនាំ (ASK)
              </button>
              <button
                onClick={() => setActiveTab('bug')}
                style={{
                  flex: 1,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '6px',
                  padding: '8px 12px',
                  borderRadius: '8px',
                  fontSize: '12px',
                  fontWeight: 600,
                  cursor: 'pointer',
                  border: 'none',
                  background: activeTab === 'bug' ? 'rgba(239, 68, 68, 0.15)' : 'transparent',
                  color: activeTab === 'bug' ? '#ef4444' : '#94a3b8',
                  transition: 'all 0.15s ease',
                }}
              >
                <Bug size={14} />
                រាយការណ៍បញ្ហា (Bug)
              </button>
            </div>

            {/* TAB 1: ASK MODE */}
            {activeTab === 'ask' && (
              <div style={{ display: 'flex', flexDirection: 'column', flex: 1, overflow: 'hidden' }}>
                {/* Messages View */}
                <div
                  style={{
                    flex: 1,
                    overflowY: 'auto',
                    padding: '16px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '12px',
                  }}
                >
                  {messages.map((m) => (
                    <div
                      key={m.id}
                      style={{
                        alignSelf: m.sender === 'user' ? 'flex-end' : 'flex-start',
                        maxWidth: '85%',
                      }}
                    >
                      <div
                        style={{
                          padding: '10px 14px',
                          borderRadius: '12px',
                          fontSize: '13px',
                          lineHeight: 1.5,
                          whiteSpace: 'pre-wrap',
                          background:
                            m.sender === 'user'
                              ? 'linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%)'
                              : 'rgba(30, 41, 59, 0.85)',
                          color: '#f8fafc',
                          border: m.sender === 'user' ? 'none' : '1px solid rgba(255, 255, 255, 0.08)',
                          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.2)',
                        }}
                      >
                        {m.text}
                      </div>

                      {/* Suggestions Chips */}
                      {m.suggestions && m.suggestions.length > 0 && (
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '8px' }}>
                          {m.suggestions.map((s, idx) => (
                            <button
                              key={idx}
                              onClick={() => handleSendQuestion(s)}
                              style={{
                                padding: '4px 8px',
                                fontSize: '11px',
                                borderRadius: '6px',
                                background: 'rgba(212, 175, 55, 0.1)',
                                border: '1px solid rgba(212, 175, 55, 0.3)',
                                color: '#e2e8f0',
                                cursor: 'pointer',
                              }}
                            >
                              {s}
                            </button>
                          ))}
                        </div>
                      )}
                      <div style={{ fontSize: '10px', color: '#64748b', marginTop: '3px', textAlign: m.sender === 'user' ? 'right' : 'left' }}>
                        {m.timestamp}
                      </div>
                    </div>
                  ))}
                  {isAsking && (
                    <div style={{ alignSelf: 'flex-start', color: '#94a3b8', fontSize: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <RefreshCw size={12} className="animate-spin" />
                      <span>កំពុងគិត...</span>
                    </div>
                  )}
                  <div ref={chatEndRef} />
                </div>

                {/* Input Field */}
                <div
                  style={{
                    padding: '10px 12px',
                    background: 'rgba(15, 23, 42, 0.8)',
                    borderTop: '1px solid rgba(255, 255, 255, 0.08)',
                    display: 'flex',
                    gap: '8px',
                  }}
                >
                  <input
                    type="text"
                    value={inputQuestion}
                    onChange={(e) => setInputQuestion(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSendQuestion()}
                    placeholder="សួរសំណួរអំពី Khmer Translator AI..."
                    style={{
                      flex: 1,
                      padding: '10px 14px',
                      background: 'rgba(30, 41, 59, 0.6)',
                      border: '1px solid rgba(255, 255, 255, 0.12)',
                      borderRadius: '8px',
                      color: '#f8fafc',
                      fontSize: '13px',
                      outline: 'none',
                    }}
                  />
                  <button
                    onClick={() => handleSendQuestion()}
                    disabled={!inputQuestion.trim() || isAsking}
                    style={{
                      padding: '0 14px',
                      background: 'linear-gradient(135deg, #d4af37 0%, #00d2ff 100%)',
                      border: 'none',
                      borderRadius: '8px',
                      color: '#0f172a',
                      cursor: inputQuestion.trim() ? 'pointer' : 'not-allowed',
                      opacity: inputQuestion.trim() ? 1 : 0.6,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    <Send size={16} />
                  </button>
                </div>
              </div>
            )}

            {/* TAB 2: BUG MODE */}
            {activeTab === 'bug' && (
              <div style={{ flex: 1, overflowY: 'auto', padding: '16px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
                {submittedBugId ? (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    style={{
                      padding: '16px',
                      background: 'rgba(16, 185, 129, 0.12)',
                      border: '1px solid rgba(16, 185, 129, 0.35)',
                      borderRadius: '12px',
                      textAlign: 'center',
                    }}
                  >
                    <CheckCircle2 size={36} color="#10b981" style={{ margin: '0 auto 8px' }} />
                    <h4 style={{ margin: '0 0 6px', fontSize: '15px', color: '#f8fafc' }}>
                      បានបញ្ជូនរបាយការណ៍ដោយជោគជ័យ!
                    </h4>
                    <p style={{ margin: '0 0 12px', fontSize: '12px', color: '#94a3b8' }}>
                      របាយការណ៍ត្រូវបានកត់ត្រា និងបញ្ជូនទៅកាន់ Telegram របស់ក្រុមវិស្វករ។
                    </p>

                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '8px',
                        background: 'rgba(0, 0, 0, 0.3)',
                        padding: '8px 12px',
                        borderRadius: '6px',
                        marginBottom: '14px',
                      }}
                    >
                      <span style={{ fontSize: '13px', fontWeight: 600, color: '#d4af37' }}>{submittedBugId}</span>
                      <button
                        onClick={copyIncidentId}
                        style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', padding: '2px' }}
                      >
                        {bugCopied ? <Check size={14} color="#10b981" /> : <Copy size={14} />}
                      </button>
                    </div>

                    <button
                      onClick={() => setSubmittedBugId(null)}
                      style={{
                        padding: '8px 16px',
                        background: 'rgba(255, 255, 255, 0.08)',
                        border: '1px solid rgba(255, 255, 255, 0.15)',
                        borderRadius: '6px',
                        color: '#f8fafc',
                        fontSize: '12px',
                        cursor: 'pointer',
                      }}
                    >
                      រាយការណ៍បញ្ហាផ្សេងទៀត
                    </button>
                  </motion.div>
                ) : (
                  <form onSubmit={handleSubmitBug} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    <div>
                      <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>
                        កម្រិតធ្ងន់ធ្ងរ (Severity):
                      </label>
                      <select
                        value={bugSeverity}
                        onChange={(e) => setBugSeverity(e.target.value)}
                        style={{
                          width: '100%',
                          padding: '8px 12px',
                          background: 'rgba(30, 41, 59, 0.7)',
                          border: '1px solid rgba(255, 255, 255, 0.12)',
                          borderRadius: '6px',
                          color: '#f8fafc',
                          fontSize: '12px',
                        }}
                      >
                        <option value="WARNING">មធ្យម (Normal / Warning)</option>
                        <option value="HIGH">បន្ទាន់ (High Priority)</option>
                        <option value="CRITICAL">ធ្ងន់ធ្ងរ (Critical Blocked)</option>
                        <option value="LOW">តិចតួច (Low / Cosmetic)</option>
                      </select>
                    </div>

                    <div>
                      <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>
                        ការរៀបរាប់ពីបញ្ហា (Description) <span style={{ color: '#ef4444' }}>*</span>:
                      </label>
                      <textarea
                        required
                        minLength={5}
                        rows={3}
                        value={bugDescription}
                        onChange={(e) => setBugDescription(e.target.value)}
                        placeholder="សូមរៀបរាប់ពីកំហុស ឬមុខងារដែលមិនដំណើរការ..."
                        style={{
                          width: '100%',
                          boxSizing: 'border-box',
                          padding: '8px 12px',
                          background: 'rgba(30, 41, 59, 0.7)',
                          border: '1px solid rgba(255, 255, 255, 0.12)',
                          borderRadius: '6px',
                          color: '#f8fafc',
                          fontSize: '12px',
                          resize: 'none',
                        }}
                      />
                    </div>

                    <div>
                      <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>
                        Error Log ឬសារកំហុស (Error Details - Optional):
                      </label>
                      <textarea
                        rows={2}
                        value={bugErrorText}
                        onChange={(e) => setBugErrorText(e.target.value)}
                        placeholder="បិទភ្ជាប់ (Paste) សារ Error ប្រសិនបើមាន..."
                        style={{
                          width: '100%',
                          boxSizing: 'border-box',
                          padding: '8px 12px',
                          background: 'rgba(30, 41, 59, 0.7)',
                          border: '1px solid rgba(255, 255, 255, 0.12)',
                          borderRadius: '6px',
                          color: '#f8fafc',
                          fontSize: '11px',
                          fontFamily: 'monospace',
                          resize: 'none',
                        }}
                      />
                    </div>

                    <div>
                      <label style={{ display: 'block', fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>
                        អ៊ីមែល ឬ Telegram ទំនាក់ទំនង (Optional Contact):
                      </label>
                      <input
                        type="text"
                        value={bugContact}
                        onChange={(e) => setBugContact(e.target.value)}
                        placeholder="@telegram_handle ឬ email@domain.com"
                        style={{
                          width: '100%',
                          boxSizing: 'border-box',
                          padding: '8px 12px',
                          background: 'rgba(30, 41, 59, 0.7)',
                          border: '1px solid rgba(255, 255, 255, 0.12)',
                          borderRadius: '6px',
                          color: '#f8fafc',
                          fontSize: '12px',
                        }}
                      />
                    </div>

                    <button
                      type="submit"
                      disabled={!bugDescription.trim() || isSubmittingBug}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '6px',
                        padding: '10px',
                        background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
                        border: 'none',
                        borderRadius: '6px',
                        color: '#fff',
                        fontWeight: 600,
                        fontSize: '13px',
                        cursor: bugDescription.trim() && !isSubmittingBug ? 'pointer' : 'not-allowed',
                        opacity: bugDescription.trim() && !isSubmittingBug ? 1 : 0.6,
                        marginTop: '4px',
                      }}
                    >
                      {isSubmittingBug ? (
                        <>
                          <RefreshCw size={14} className="animate-spin" />
                          កំពុងបញ្ជូន...
                        </>
                      ) : (
                        <>
                          <Send size={14} />
                          បញ្ជូនរបាយការណ៍បញ្ហា (Submit Bug)
                        </>
                      )}
                    </button>
                  </form>
                )}

                {/* Bug Status Lookup Section */}
                <div
                  style={{
                    marginTop: '12px',
                    paddingTop: '12px',
                    borderTop: '1px solid rgba(255, 255, 255, 0.08)',
                  }}
                >
                  <label style={{ display: 'block', fontSize: '11px', color: '#94a3b8', marginBottom: '6px' }}>
                    តាមដានស្ថានភាពបញ្ហា (Track Incident Status):
                  </label>
                  <form onSubmit={handleLookupStatus} style={{ display: 'flex', gap: '6px' }}>
                    <input
                      type="text"
                      placeholder="ឧ. BUG-1234ABCD"
                      value={lookupId}
                      onChange={(e) => setLookupId(e.target.value)}
                      style={{
                        flex: 1,
                        padding: '6px 10px',
                        background: 'rgba(30, 41, 59, 0.7)',
                        border: '1px solid rgba(255, 255, 255, 0.12)',
                        borderRadius: '6px',
                        color: '#f8fafc',
                        fontSize: '12px',
                      }}
                    />
                    <button
                      type="submit"
                      disabled={!lookupId.trim() || isLookingUp}
                      style={{
                        padding: '6px 12px',
                        background: 'rgba(255, 255, 255, 0.08)',
                        border: '1px solid rgba(255, 255, 255, 0.15)',
                        borderRadius: '6px',
                        color: '#f8fafc',
                        fontSize: '12px',
                        cursor: 'pointer',
                      }}
                    >
                      {isLookingUp ? <RefreshCw size={12} className="animate-spin" /> : <Search size={12} />}
                    </button>
                  </form>

                  {lookupError && (
                    <div style={{ color: '#ef4444', fontSize: '11px', marginTop: '6px' }}>
                      {lookupError}
                    </div>
                  )}

                  {lookupResult && (
                    <div
                      style={{
                        marginTop: '8px',
                        padding: '8px 10px',
                        borderRadius: '6px',
                        background: 'rgba(30, 41, 59, 0.8)',
                        fontSize: '11px',
                        borderLeft: '3px solid #d4af37',
                      }}
                    >
                      <div style={{ fontWeight: 600, color: '#f8fafc', display: 'flex', justifyContent: 'space-between' }}>
                        <span>{lookupResult.id}</span>
                        <span style={{ color: '#10b981' }}>{lookupResult.status}</span>
                      </div>
                      <div style={{ color: '#94a3b8', marginTop: '2px' }}>{lookupResult.summary}</div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};
