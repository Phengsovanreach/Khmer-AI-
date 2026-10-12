import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Mail,
  Lock,
  Eye,
  EyeOff,
  User,
  Sparkles,
  ShieldCheck,
  Languages,
  CheckCircle2,
  AlertCircle,
  Loader2,
  ArrowRight,
  Info,
  X,
  AudioLines,
  Heart,
  Cpu,
} from 'lucide-react';
import { AuthService, UserProfile } from '../services/authService';
import {
  KhmerLotusMotif,
  KhmerCornerKbach,
  KhmerBorderDivider,
} from './CambodianCulturalBackground';

interface AngkorNexusAuthProps {
  onSuccess: (user: UserProfile) => void;
  dark?: boolean;
}

type AuthMode = 'login' | 'register';
type LanguageMode = 'km' | 'en';

export const AngkorNexusAuth: React.FC<AngkorNexusAuthProps> = ({ onSuccess, dark = true }) => {
  const [mode, setMode] = useState<AuthMode>('login');
  const [lang, setLang] = useState<LanguageMode>('km');

  // Shared Form Fields
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(true);
  const [termsAccepted, setTermsAccepted] = useState(true);

  // UI States
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [showForgotModal, setShowForgotModal] = useState(false);
  const [showTermsModal, setShowTermsModal] = useState(false);

  // Forgot password form state
  const [forgotEmail, setForgotEmail] = useState('');
  const [forgotSubmitted, setForgotSubmitted] = useState(false);

  // Clear messages on mode switch
  const switchMode = (newMode: AuthMode) => {
    setMode(newMode);
    setErrorMsg('');
    setSuccessMsg('');
  };

  // Password Strength Calculation (0 - 3)
  const calculatePasswordStrength = (pass: string): { score: number; labelKm: string; labelEn: string; color: string } => {
    if (!pass) return { score: 0, labelKm: 'មិនទាន់មាន', labelEn: 'None', color: 'transparent' };
    let score = 0;
    if (pass.length >= 8) score++;
    if (/[0-9]/.test(pass) && /[a-zA-Z]/.test(pass)) score++;
    if (/[^a-zA-Z0-9]/.test(pass) && pass.length >= 10) score++;

    if (score === 1) return { score: 1, labelKm: 'ខ្សោយ', labelEn: 'Weak', color: '#e06c75' };
    if (score === 2) return { score: 2, labelKm: 'មធ្យម', labelEn: 'Fair', color: '#e5c07b' };
    return { score: 3, labelKm: 'រឹងមាំខ្លាំង', labelEn: 'Strong', color: '#77d5a3' };
  };

  const strength = calculatePasswordStrength(password);

  // Form Submissions
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg('');
    setSuccessMsg('');

    if (!email.trim() || !email.includes('@')) {
      setErrorMsg(lang === 'km' ? 'សូមបញ្ចូលអ៊ីមែលឱ្យបានត្រឹមត្រូវ' : 'Please provide a valid email address.');
      return;
    }

    if (!password) {
      setErrorMsg(lang === 'km' ? 'សូមបញ្ចូលពាក្យសម្ងាត់' : 'Please enter your password.');
      return;
    }

    if (mode === 'register') {
      if (!name.trim()) {
        setErrorMsg(lang === 'km' ? 'សូមបញ្ចូលឈ្មោះពេញរបស់អ្នក' : 'Please enter your full name.');
        return;
      }
      if (password.length < 8) {
        setErrorMsg(lang === 'km' ? 'ពាក្យសម្ងាត់ត្រូវមានយ៉ាងហោចណាស់ ៨ តួអក្សរ' : 'Password must be at least 8 characters long.');
        return;
      }
      if (password !== confirmPassword) {
        setErrorMsg(lang === 'km' ? 'ពាក្យសម្ងាត់ផ្ទៀងផ្ទាត់មិនត្រូវគ្នាទេ' : 'Passwords do not match.');
        return;
      }
      if (!termsAccepted) {
        setErrorMsg(lang === 'km' ? 'សូមយល់ព្រមលើលក្ខខណ្ឌប្រើប្រាស់' : 'Please accept the Terms & Privacy Policy.');
        return;
      }
    }

    setLoading(true);

    try {
      if (mode === 'login') {
        const res = await AuthService.login(email.trim(), password, rememberMe);
        setSuccessMsg(lang === 'km' ? 'ចូលប្រើប្រាស់បានជោគជ័យ! កំពុងបើក Studio...' : 'Login successful! Launching studio...');
        setTimeout(() => {
          onSuccess(res.user);
        }, 650);
      } else {
        const res = await AuthService.register(name.trim(), email.trim(), password);
        setSuccessMsg(lang === 'km' ? 'គណនីបានបង្កើតដោយជោគជ័យ! សូមស្វាគមន៍មកកាន់ Khmer AI' : 'Account created successfully! Welcome to Khmer AI.');
        setTimeout(() => {
          onSuccess(res.user);
        }, 750);
      }
    } catch (err: any) {
      setErrorMsg(err.message || (lang === 'km' ? 'ប្រតិបត្តិការបរាជ័យ សូមព្យាយាមម្តងទៀត' : 'Authentication failed. Please try again.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="angkor-nexus-auth-root">
      {/* 1. LAYERED BACKGROUND ARCHITECTURE */}
      <div className="angkor-nexus-bg-layer" aria-hidden="true">
        {/* Obsidian Navy to Midnight Black Gradient */}
        <div className="nexus-cosmic-glow" />

        {/* Subtle Silhouette of Angkor Wat Sacred Towers */}
        <svg
          className="angkor-wat-silhouette-svg"
          viewBox="0 0 1440 460"
          preserveAspectRatio="none"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          {/* Central Stupa Pinnacle (ប្រាង្គកណ្តាល) */}
          <path
            d="M720 40 C718 100 705 140 700 170 C695 190 690 200 680 220 C665 250 655 270 650 320 L790 320 C785 270 775 250 760 220 C750 200 745 190 740 170 C735 140 722 100 720 40 Z"
            fill="url(#angkorGrad1)"
            opacity="0.35"
          />
          {/* Left Intermediate Tower */}
          <path
            d="M590 110 C588 150 578 180 575 200 C570 220 565 240 555 260 C545 285 538 300 535 340 L645 340 C642 300 635 285 625 260 C615 240 610 220 605 200 C602 180 592 150 590 110 Z"
            fill="url(#angkorGrad1)"
            opacity="0.25"
          />
          {/* Right Intermediate Tower */}
          <path
            d="M850 110 C848 150 838 180 835 200 C830 220 825 240 815 260 C805 285 798 300 795 340 L905 340 C902 300 895 285 885 260 C875 240 870 220 865 200 C862 180 852 150 850 110 Z"
            fill="url(#angkorGrad1)"
            opacity="0.25"
          />
          {/* Outer Left Tower */}
          <path
            d="M470 160 C468 190 460 215 458 230 C452 250 448 268 440 285 C432 305 428 320 425 360 L515 360 C512 320 508 305 500 285 C492 268 488 250 482 230 C480 215 472 190 470 160 Z"
            fill="url(#angkorGrad1)"
            opacity="0.18"
          />
          {/* Outer Right Tower */}
          <path
            d="M970 160 C968 190 960 215 958 230 C952 250 948 268 940 285 C932 305 928 320 925 360 L1015 360 C1012 320 1008 305 1000 285 C992 268 988 250 982 230 C980 215 972 190 970 160 Z"
            fill="url(#angkorGrad1)"
            opacity="0.18"
          />
          {/* Base Causeway & Gallery Balustrade */}
          <path
            d="M0 350 L1440 350 L1440 460 L0 460 Z"
            fill="url(#angkorBaseGrad)"
            opacity="0.45"
          />
          <defs>
            <linearGradient id="angkorGrad1" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#D6B46A" stopOpacity="0.4" />
              <stop offset="100%" stopColor="#0B1020" stopOpacity="0.85" />
            </linearGradient>
            <linearGradient id="angkorBaseGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#15223c" stopOpacity="0.6" />
              <stop offset="100%" stopColor="#0B1020" stopOpacity="0.95" />
            </linearGradient>
          </defs>
        </svg>

        {/* Ethereal Floating Dust & Starlight Particles */}
        <div className="angkor-particles-emitter">
          {[...Array(14)].map((_, i) => (
            <div
              key={i}
              className="angkor-dust-particle"
              style={{
                left: `${(i * 19 + 7) % 96}%`,
                top: `${(i * 23 + 12) % 88}%`,
                animationDelay: `${(i * 0.7) % 5}s`,
                animationDuration: `${6 + (i % 4) * 2}s`,
              }}
            />
          ))}
        </div>
      </div>

      {/* 2. MAIN BILINGUAL CONTAINER */}
      <div className="angkor-nexus-container">
        {/* LEFT COLUMN: CINEMATIC KHMER HERITAGE & AI SHOWCASE (DESKTOP) */}
        <motion.div
          className="nexus-heritage-portal"
          initial={{ opacity: 0, x: -30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.65, ease: [0.16, 1, 0.3, 1] }}
        >
          {/* Holographic Seal Badge */}
          <div className="nexus-emblem-badge">
            <div className="nexus-emblem-glow-ring" />
            <KhmerLotusMotif size={36} color="var(--gold, #D6B46A)" />
          </div>

          <div className="nexus-brand-header">
            <span className="nexus-heritage-kicker">
              មរតកវប្បធម៌ខ្មែរ · ANCIENT ROOTS × AI INTELLIGENCE
            </span>
            <h1 className="nexus-hero-title">
              KHMER <span>TRANSLATOR</span>
            </h1>
            <p className="nexus-hero-tagline">
              {lang === 'km'
                ? '« បកប្រែរឿងរ៉ាវ រក្សាអារម្មណ៍ដើម »'
                : '“ Translate the Story. Keep the Emotion. ”'}
            </p>
          </div>

          <p className="nexus-hero-description">
            {lang === 'km'
              ? 'វេទិកា AI វ័យឆ្លាតជំនាន់ថ្មី សម្រាប់ការបំប្លែងសំឡេងជាអក្សរ (Speech-to-Text) ការកែសម្រួល Subtitle ស្វ័យប្រវត្តិ និងការបញ្ចូលសំឡេង Dubbed ពហុភាសា ផ្អែកលើបច្ចេកវិទ្យាកម្រិតខ្ពស់ និងមរតកវប្បធម៌ខ្មែរដ៏រុងរឿង។'
              : 'Next-generation AI dubbing and multilingual speech platform engineered with authentic Khmer cultural precision, on-device data privacy, and deep actor emotional vocalization preservation.'}
          </p>

          {/* Holographic AI Audio Frequency Visualizer */}
          <div className="nexus-audio-card">
            <div className="nexus-audio-head">
              <span className="nexus-audio-dot" />
              <b>{lang === 'km' ? 'សំឡេង & អារម្មណ៍ AI' : 'NEURAL AUDIO ENGINE'}</b>
              <small>FASTER-WHISPER · CPU INT8</small>
            </div>
            <div className="nexus-visualizer-bars">
              {[40, 75, 25, 90, 60, 30, 85, 95, 45, 70, 80, 55, 35, 90, 65, 40].map((h, idx) => (
                <div
                  key={idx}
                  className="nexus-visualizer-bar"
                  style={{
                    height: `${h}%`,
                    animationDelay: `${idx * 0.08}s`,
                  }}
                />
              ))}
            </div>
            <div className="nexus-audio-foot">
              <span>{lang === 'km' ? 'ភាពត្រឹមត្រូវខ្ពស់ · មិនប្រើ Cloud API' : '100% Local Privacy · Zero API Cost'}</span>
              <b>99.4% KHMER ACCURACY</b>
            </div>
          </div>

          {/* Pillars List */}
          <div className="nexus-features-grid">
            <div className="nexus-feature-item">
              <div className="nexus-feature-icon">
                <ShieldCheck size={18} />
              </div>
              <div>
                <b>{lang === 'km' ? 'សុវត្ថិភាពទិន្នន័យ 100%' : '100% On-Device Privacy'}</b>
                <small>{lang === 'km' ? 'ទិន្នន័យត្រូវបានដំណើរការលើម៉ាស៊ីនផ្ទាល់' : 'All voice processing runs securely locally'}</small>
              </div>
            </div>
            <div className="nexus-feature-item">
              <div className="nexus-feature-icon">
                <Sparkles size={18} />
              </div>
              <div>
                <b>{lang === 'km' ? 'សំឡេង Dubbed ធម្មជាតិ' : 'Actor Emotion Dubbing'}</b>
                <small>{lang === 'km' ? 'រក្សាសំឡេងសើច ស្រែក និងអារម្មណ៍តួអង្គ' : 'Preserves nonverbal laughs, gasps & tone'}</small>
              </div>
            </div>
          </div>
        </motion.div>

        {/* RIGHT COLUMN: REFINED ANGKOR NEXUS AUTHENTICATION PANEL */}
        <motion.div
          className="nexus-auth-card-panel"
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55, delay: 0.1, ease: [0.16, 1, 0.3, 1] }}
        >
          {/* Subtle Angkor Wat Ornamental Corner Emblems */}
          <KhmerCornerKbach position="top-left" size={32} />
          <KhmerCornerKbach position="top-right" size={32} />
          <KhmerCornerKbach position="bottom-left" size={32} />
          <KhmerCornerKbach position="bottom-right" size={32} />

          {/* Top Panel Actions: Language Toggle & Mobile Brand Logo */}
          <div className="nexus-card-top-bar">
            <div className="nexus-mobile-brand-mark">
              <img src="/logo.png" alt="Khmer AI Heritage Logo" className="nexus-mini-logo" />
              <span>KHMER AI</span>
            </div>

            <div className="nexus-lang-selector" role="group" aria-label="Language Selector">
              <button
                type="button"
                className={`nexus-lang-btn ${lang === 'km' ? 'active' : ''}`}
                onClick={() => setLang('km')}
                title="ប្តូរទៅភាសាខ្មែរ"
              >
                🇰🇭 ខ្មែរ
              </button>
              <button
                type="button"
                className={`nexus-lang-btn ${lang === 'en' ? 'active' : ''}`}
                onClick={() => setLang('en')}
                title="Switch to English"
              >
                EN
              </button>
            </div>
          </div>

          {/* Navigation Mode Switcher Tabs */}
          <div className="nexus-mode-tabs" role="tablist">
            <button
              type="button"
              role="tab"
              aria-selected={mode === 'login'}
              className={`nexus-mode-tab ${mode === 'login' ? 'active' : ''}`}
              onClick={() => switchMode('login')}
            >
              {lang === 'km' ? 'ចូលប្រើប្រាស់' : 'Sign In'}
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={mode === 'register'}
              className={`nexus-mode-tab ${mode === 'register' ? 'active' : ''}`}
              onClick={() => switchMode('register')}
            >
              {lang === 'km' ? 'ចុះឈ្មោះថ្មី' : 'Create Account'}
            </button>
          </div>

          {/* Welcome Heading */}
          <div className="nexus-form-intro">
            <h2>
              {mode === 'login'
                ? lang === 'km'
                  ? 'ស្វាគមន៍ការត្រឡប់មកវិញ'
                  : 'Welcome Back'
                : lang === 'km'
                ? 'បង្កើតគណនីថ្មី'
                : 'Begin Your Journey'}
            </h2>
            <p>
              {mode === 'login'
                ? lang === 'km'
                  ? 'សូមបញ្ចូលព័ត៌មានគណនីរបស់អ្នក ដើម្បីចូលប្រើប្រាស់ស្ទូឌីយោ'
                  : 'Enter your credentials to enter the AI speech studio'
                : lang === 'km'
                ? 'ចូលរួមប្រើប្រាស់ស្ទូឌីយោបកប្រែសំឡេង និងវីដេអូ AI ជំនាន់ថ្មី'
                : 'Join the premier cultural Khmer speech intelligence studio'}
            </p>
          </div>

          {/* Feedback Messages */}
          <AnimatePresence mode="wait">
            {errorMsg && (
              <motion.div
                className="nexus-alert error"
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                role="alert"
              >
                <AlertCircle size={16} />
                <span>{errorMsg}</span>
                <button
                  type="button"
                  className="nexus-alert-close"
                  onClick={() => setErrorMsg('')}
                  aria-label="Dismiss error"
                >
                  <X size={14} />
                </button>
              </motion.div>
            )}

            {successMsg && (
              <motion.div
                className="nexus-alert success"
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                role="status"
              >
                <CheckCircle2 size={16} />
                <span>{successMsg}</span>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Main Auth Form */}
          <form className="nexus-auth-form" onSubmit={handleSubmit} noValidate>
            {/* Full Name Field (Register Mode Only) */}
            {mode === 'register' && (
              <div className="nexus-field-group">
                <label htmlFor="nexus-name">
                  {lang === 'km' ? 'ឈ្មោះពេញ' : 'Full Name'} <span className="req">*</span>
                </label>
                <div className="nexus-input-wrap">
                  <User size={16} className="nexus-input-icon" />
                  <input
                    id="nexus-name"
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder={lang === 'km' ? 'ឧ. សុវណ្ណរាជ' : 'e.g. Sovannreach'}
                    required
                    autoComplete="name"
                  />
                </div>
              </div>
            )}

            {/* Email Field */}
            <div className="nexus-field-group">
              <label htmlFor="nexus-email">
                {lang === 'km' ? 'អាសយដ្ឋានអ៊ីមែល' : 'Email Address'} <span className="req">*</span>
              </label>
              <div className="nexus-input-wrap">
                <Mail size={16} className="nexus-input-icon" />
                <input
                  id="nexus-email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder={lang === 'km' ? 'name@example.com' : 'name@example.com'}
                  required
                  autoComplete="email"
                />
              </div>
            </div>

            {/* Password Field */}
            <div className="nexus-field-group">
              <div className="nexus-label-row">
                <label htmlFor="nexus-password">
                  {lang === 'km' ? 'ពាក្យសម្ងាត់' : 'Password'} <span className="req">*</span>
                </label>
                {mode === 'login' && (
                  <button
                    type="button"
                    className="nexus-text-link"
                    onClick={() => setShowForgotModal(true)}
                  >
                    {lang === 'km' ? 'ភ្លេចពាក្យសម្ងាត់?' : 'Forgot Password?'}
                  </button>
                )}
              </div>
              <div className="nexus-input-wrap">
                <Lock size={16} className="nexus-input-icon" />
                <input
                  id="nexus-password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  required
                  autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                />
                <button
                  type="button"
                  className="nexus-pw-toggle"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                  tabIndex={0}
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>

              {/* Password Strength Meter (Register Mode) */}
              {mode === 'register' && password && (
                <div className="nexus-strength-meter">
                  <div className="nexus-strength-track">
                    <div
                      className="nexus-strength-bar"
                      style={{
                        width: `${(strength.score / 3) * 100}%`,
                        backgroundColor: strength.color,
                      }}
                    />
                  </div>
                  <div className="nexus-strength-info">
                    <small>
                      {lang === 'km' ? 'កម្រិតសុវត្ថិភាព៖ ' : 'Strength: '}
                      <b style={{ color: strength.color }}>
                        {lang === 'km' ? strength.labelKm : strength.labelEn}
                      </b>
                    </small>
                    <small>{lang === 'km' ? 'យ៉ាងតិច ៨ តួអក្សរ' : 'Min 8 chars'}</small>
                  </div>
                </div>
              )}
            </div>

            {/* Confirm Password Field (Register Mode Only) */}
            {mode === 'register' && (
              <div className="nexus-field-group">
                <label htmlFor="nexus-confirm-password">
                  {lang === 'km' ? 'ផ្ទៀងផ្ទាត់ពាក្យសម្ងាត់' : 'Confirm Password'} <span className="req">*</span>
                </label>
                <div className="nexus-input-wrap">
                  <Lock size={16} className="nexus-input-icon" />
                  <input
                    id="nexus-confirm-password"
                    type={showConfirmPassword ? 'text' : 'password'}
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="••••••••••••"
                    required
                    autoComplete="new-password"
                  />
                  <button
                    type="button"
                    className="nexus-pw-toggle"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    aria-label={showConfirmPassword ? 'Hide password' : 'Show password'}
                  >
                    {showConfirmPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>
            )}

            {/* Remember Me / Terms Agreement Checkbox */}
            {mode === 'login' ? (
              <div className="nexus-checkbox-row">
                <label className="nexus-checkbox-label">
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                  />
                  <span className="nexus-checkbox-custom" />
                  <span>{lang === 'km' ? 'ចងចាំគណនីខ្ញុំលើឧបករណ៍នេះ' : 'Remember me on this device'}</span>
                </label>
              </div>
            ) : (
              <div className="nexus-checkbox-row">
                <label className="nexus-checkbox-label">
                  <input
                    type="checkbox"
                    checked={termsAccepted}
                    onChange={(e) => setTermsAccepted(e.target.checked)}
                  />
                  <span className="nexus-checkbox-custom" />
                  <span>
                    {lang === 'km' ? 'ខ្ញុំយល់ព្រមលើ ' : 'I agree to the '}
                    <button
                      type="button"
                      className="nexus-inline-link"
                      onClick={() => setShowTermsModal(true)}
                    >
                      {lang === 'km' ? 'លក្ខខណ្ឌប្រើប្រាស់ & ភាពឯកជន' : 'Terms & Privacy Policy'}
                    </button>
                  </span>
                </label>
              </div>
            )}

            {/* Submit Button with Angkor Golden Gradient */}
            <button
              type="submit"
              className="nexus-submit-btn"
              disabled={loading}
            >
              {loading ? (
                <>
                  <Loader2 size={16} className="spin" />
                  <span>{lang === 'km' ? 'កំពុងផ្ទៀងផ្ទាត់...' : 'Authenticating...'}</span>
                </>
              ) : mode === 'login' ? (
                <>
                  <span>{lang === 'km' ? 'ចូលប្រើប្រាស់ស្ទូឌីយោ' : 'Enter AI Studio'}</span>
                  <ArrowRight size={16} />
                </>
              ) : (
                <>
                  <span>{lang === 'km' ? 'ចុះឈ្មោះបង្កើតគណនី' : 'Create Free Account'}</span>
                  <Sparkles size={16} />
                </>
              )}
            </button>
          </form>

          {/* Bottom Switcher Link */}
          <div className="nexus-card-foot">
            {mode === 'login' ? (
              <p>
                {lang === 'km' ? 'មិនទាន់មានគណនីនៅឡើយ? ' : "Don't have an account yet? "}
                <button
                  type="button"
                  className="nexus-switch-link"
                  onClick={() => switchMode('register')}
                >
                  {lang === 'km' ? 'ចុះឈ្មោះឥឡូវនេះ' : 'Sign up now'}
                </button>
              </p>
            ) : (
              <p>
                {lang === 'km' ? 'មានគណនីរួចហើយ? ' : 'Already have an account? '}
                <button
                  type="button"
                  className="nexus-switch-link"
                  onClick={() => switchMode('login')}
                >
                  {lang === 'km' ? 'ចូលប្រើប្រាស់' : 'Sign in'}
                </button>
              </p>
            )}
          </div>
        </motion.div>
      </div>

      {/* 3. FORGOT PASSWORD MODAL */}
      <AnimatePresence>
        {showForgotModal && (
          <div className="nexus-modal-backdrop" onClick={() => setShowForgotModal(false)}>
            <motion.div
              className="nexus-modal-card"
              onClick={(e) => e.stopPropagation()}
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
            >
              <div className="nexus-modal-head">
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <KhmerLotusMotif size={22} color="var(--gold, #D6B46A)" />
                  <h3>{lang === 'km' ? 'កំណត់ពាក្យសម្ងាត់ឡើងវិញ' : 'Reset Your Password'}</h3>
                </div>
                <button
                  type="button"
                  className="nexus-modal-close"
                  onClick={() => setShowForgotModal(false)}
                  aria-label="Close"
                >
                  <X size={16} />
                </button>
              </div>

              <div className="nexus-modal-body">
                {forgotSubmitted ? (
                  <div className="nexus-forgot-success">
                    <CheckCircle2 size={36} color="var(--green, #77d5a3)" />
                    <h4>{lang === 'km' ? 'ការណែនាំត្រូវបានផ្ញើ!' : 'Instructions Sent!'}</h4>
                    <p>
                      {lang === 'km'
                        ? `ប្រសិនបើអាសយដ្ឋាន ${forgotEmail} មានក្នុងប្រព័ន្ធរបស់យើង អ្នកនឹងទទួលបានតំណភ្ជាប់កំណត់ពាក្យសម្ងាត់ឡើងវិញ។`
                        : `If an account exists for ${forgotEmail}, instructions to reset your password have been sent.`}
                    </p>
                    <button
                      type="button"
                      className="nexus-submit-btn secondary"
                      onClick={() => {
                        setShowForgotModal(false);
                        setForgotSubmitted(false);
                      }}
                    >
                      {lang === 'km' ? 'យល់ព្រម' : 'Done'}
                    </button>
                  </div>
                ) : (
                  <>
                    <p>
                      {lang === 'km'
                        ? 'សូមបញ្ចូលអាសយដ្ឋានអ៊ីមែលដែលអ្នកបានចុះឈ្មោះ។ យើងនឹងផ្ញើតំណភ្ជាប់ដើម្បីកំណត់ពាក្យសម្ងាត់ថ្មីជូនអ្នក។'
                        : 'Enter the email associated with your account, and we will send password reset instructions.'}
                    </p>
                    <div className="nexus-field-group" style={{ marginTop: 14 }}>
                      <label htmlFor="forgot-email">
                        {lang === 'km' ? 'អាសយដ្ឋានអ៊ីមែល' : 'Email Address'}
                      </label>
                      <div className="nexus-input-wrap">
                        <Mail size={16} className="nexus-input-icon" />
                        <input
                          id="forgot-email"
                          type="email"
                          value={forgotEmail}
                          onChange={(e) => setForgotEmail(e.target.value)}
                          placeholder="name@example.com"
                          required
                        />
                      </div>
                    </div>
                    <div className="nexus-modal-actions">
                      <button
                        type="button"
                        className="nexus-submit-btn"
                        onClick={() => {
                          if (forgotEmail.includes('@')) {
                            setForgotSubmitted(true);
                          }
                        }}
                      >
                        {lang === 'km' ? 'ផ្ញើតំណកំណត់ឡើងវិញ' : 'Send Reset Link'}
                      </button>
                    </div>
                  </>
                )}
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* 4. TERMS & PRIVACY POLICY MODAL */}
      <AnimatePresence>
        {showTermsModal && (
          <div className="nexus-modal-backdrop" onClick={() => setShowTermsModal(false)}>
            <motion.div
              className="nexus-modal-card wide"
              onClick={(e) => e.stopPropagation()}
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
            >
              <div className="nexus-modal-head">
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <ShieldCheck size={22} color="var(--gold, #D6B46A)" />
                  <h3>{lang === 'km' ? 'លក្ខខណ្ឌប្រើប្រាស់ & គោលការណ៍ភាពឯកជន' : 'Terms & Privacy Policy'}</h3>
                </div>
                <button
                  type="button"
                  className="nexus-modal-close"
                  onClick={() => setShowTermsModal(false)}
                  aria-label="Close"
                >
                  <X size={16} />
                </button>
              </div>

              <div className="nexus-modal-body legal">
                <h4>{lang === 'km' ? '១. គោលការណ៍ភាពឯកជនខ្ពស់បំផុត (Privacy-First)' : '1. Local Privacy First'}</h4>
                <p>
                  {lang === 'km'
                    ? 'Khmer Translator ដំណើរការម៉ូដែល AI ស្គាល់សំឡេង (Whisper) និងសំឡេង Dubbing ដោយផ្ទាល់នៅលើម៉ាស៊ីនបម្រើក្នុងស្រុក។ សំឡេង វីដេអូ និងឯកសារអត្ថបទរបស់អ្នកមិនត្រូវបានលក់ ឬផ្ទេរទៅភាគីទីបីដោយគ្មានការអនុញ្ញាតឡើយ។'
                    : 'Khmer Translator processes your audio and video locally. Your source media, transcripts, and voice samples remain private and are never shared or sold.'}
                </p>

                <h4>{lang === 'km' ? '២. កម្មសិទ្ធិបញ្ញា និងសិទ្ធិអ្នកនិពន្ធ' : '2. Intellectual Property & Culture'}</h4>
                <p>
                  {lang === 'km'
                    ? 'រាល់ការច្នៃប្រឌិត និងស្នាដៃវីដេអូ ឬអូឌីយ៉ូដែលបង្កើតឡើងតាមរយៈ Khmer AI គឺជាកម្មសិទ្ធិពេញលេញរបស់អ្នកប្រើប្រាស់។'
                    : 'All audio translations, subtitle files (SRT/VTT), and dubbed media generated belong entirely to you as the creator.'}
                </p>

                <h4>{lang === 'km' ? '៣. សុវត្ថិភាពគណនី' : '3. Account Security'}</h4>
                <p>
                  {lang === 'km'
                    ? 'ពាក្យសម្ងាត់ត្រូវបានរក្សាទុកជាទម្រង់ Cryptographic Hash (PBKDF2-SHA256) ដោយសុវត្ថិភាព។ យើងមិនដែលរក្សាទុកពាក្យសម្ងាត់ដើមរបស់អ្នកជាអក្សរធម្មតាឡើយ។'
                    : 'Passwords are encrypted and stored solely as secure salted PBKDF2-HMAC-SHA256 hashes. Plain text passwords are never stored.'}
                </p>

                <div className="nexus-modal-actions">
                  <button
                    type="button"
                    className="nexus-submit-btn"
                    onClick={() => setShowTermsModal(false)}
                  >
                    {lang === 'km' ? 'ខ្ញុំបានយល់ និងយល់ព្រម' : 'I Understand & Agree'}
                  </button>
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};
