import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Sparkles, Sun, Compass, Play, CloudUpload, ArrowRight } from 'lucide-react';

export interface CambodianCulturalBackgroundProps {
  variant?: 'ambient' | 'hero' | 'empty-state' | 'banner';
  mode?: 'subtle' | 'vibrant' | 'minimal' | 'disabled';
  dark?: boolean;
  className?: string;
  onNewProject?: () => void;
  onExploreHistory?: () => void;
  children?: React.ReactNode;
}

export const KhmerLotusMotif: React.FC<{ size?: number; color?: string; className?: string }> = ({
  size = 32,
  color = 'var(--gold, #d9b56d)',
  className = '',
}) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 48 48"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={`khmer-lotus-icon ${className}`}
    aria-hidden="true"
  >
    {/* Central Lotus Bud Pinnacle */}
    <path
      d="M24 4C24 4 21 14 21 21C21 26 22.5 28 24 30C25.5 28 27 26 27 21C27 14 24 4 24 4Z"
      fill={color}
      fillOpacity="0.88"
    />
    {/* Inner Left Petal */}
    <path
      d="M21 18C18 19.5 14 23 15 28C15.8 32 19 33 22 32.5C21 29 21 24 21 18Z"
      fill={color}
      fillOpacity="0.75"
    />
    {/* Inner Right Petal */}
    <path
      d="M27 18C30 19.5 34 23 33 28C32.2 32 29 33 26 32.5C27 29 27 24 27 18Z"
      fill={color}
      fillOpacity="0.75"
    />
    {/* Outer Left Calyx Wing */}
    <path
      d="M17 26C13 28 8 32 10 37C11.5 40.5 16 40 19 38C17 34 17 30 17 26Z"
      fill={color}
      fillOpacity="0.5"
    />
    {/* Outer Right Calyx Wing */}
    <path
      d="M31 26C35 28 40 32 38 37C36.5 40.5 32 40 29 38C31 34 31 30 31 26Z"
      fill={color}
      fillOpacity="0.5"
    />
    {/* Lotus Base Pedestal (ថ្នាក់ផ្កាឈូក) */}
    <path
      d="M12 40C16 38.5 20 39.5 24 40.5C28 39.5 32 38.5 36 40C33 43 27 44 24 44C21 44 15 43 12 40Z"
      fill={color}
      fillOpacity="0.9"
    />
    {/* Center Jewel Accent */}
    <circle cx="24" cy="27" r="2" fill="#fff" fillOpacity="0.7" />
  </svg>
);

/**
 * Traditional Khmer Ornamental Corner Flourish (ក្បាច់ផ្ញីទេស / Kbach Phni Tes)
 * Inspired by Angkorian stone carvings framing entryways.
 */
export const KhmerCornerKbach: React.FC<{
  position?: 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right';
  size?: number;
  color?: string;
}> = ({ position = 'top-left', size = 44, color = 'var(--gold, #d9b56d)' }) => {
  const rotation = {
    'top-left': '0',
    'top-right': 'scale(-1, 1)',
    'bottom-left': 'scale(1, -1)',
    'bottom-right': 'scale(-1, -1)',
  }[position];

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      style={{ transform: rotation }}
      className="khmer-corner-ornament"
      aria-hidden="true"
    >
      <path
        d="M3 3H36C36 3 24 9 18 16C12 23 8 36 8 36V61"
        stroke={color}
        strokeWidth="1.5"
        strokeLinecap="round"
      />
      <path
        d="M3 10C16 10 24 16 28 26C31 34 32 48 32 48"
        stroke={color}
        strokeWidth="1"
        strokeDasharray="2 3"
        strokeOpacity="0.6"
      />
      <path
        d="M12 12C12 12 18 7 24 8C27 8.5 28 11 26 13C24 15 19 15 17 19C15 23 16 27 12 28C9 28.5 8 26 9 23C10 19 12 12 12 12Z"
        fill={color}
        fillOpacity="0.45"
      />
      <circle cx="5" cy="5" r="2.5" fill={color} />
      <circle cx="36" cy="3" r="1.5" fill={color} />
      <circle cx="3" cy="36" r="1.5" fill={color} />
    </svg>
  );
};

/**
 * Traditional Khmer Ornamental Border Divider with Central Lotus Diamond
 */
export const KhmerBorderDivider: React.FC<{ className?: string; color?: string }> = ({
  className = '',
  color = 'var(--gold, #d9b56d)',
}) => (
  <div className={`khmer-border-divider ${className}`} aria-hidden="true">
    <span className="divider-line" />
    <svg width="60" height="16" viewBox="0 0 60 16" fill="none" className="divider-motif">
      <path d="M0 8H20" stroke={color} strokeWidth="1" strokeOpacity="0.6" />
      <path d="M40 8H60" stroke={color} strokeWidth="1" strokeOpacity="0.6" />
      {/* Center Diamond Jewel */}
      <path d="M30 2L35 8L30 14L25 8Z" fill={color} fillOpacity="0.85" />
      <circle cx="20" cy="8" r="1.5" fill={color} />
      <circle cx="40" cy="8" r="1.5" fill={color} />
    </svg>
    <span className="divider-line" />
  </div>
);

/**
 * CambodianCulturalBackground
 * Master component delivering the authentic Cambodian countryside, Angkor Wat,
 * rice paddies, and Khmer ornamental aesthetic.
 */
export const CambodianCulturalBackground: React.FC<CambodianCulturalBackgroundProps> = ({
  variant = 'ambient',
  mode = 'subtle',
  dark = true,
  className = '',
  onNewProject,
  onExploreHistory,
  children,
}) => {
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageError, setImageError] = useState(false);

  // If disabled via user settings, render children or nothing
  if (mode === 'disabled') {
    return children ? <>{children}</> : null;
  }

  // 1. AMBIENT BACKDROP VARIANT (Subtle background across the workspace)
  if (variant === 'ambient') {
    return (
      <div
        className={`cambodian-cultural-ambient mode-${mode} ${dark ? 'dark' : 'light'} ${className}`}
        aria-hidden="true"
      >
        {/* Layer 1: Optimally compressed WebP/JPG Landscape */}
        {!imageError && (
          <picture className="cambodian-art-picture">
            <source srcSet="/images/cambodia-cultural-bg.webp" type="image/webp" />
            <img
              src="/images/cambodia-cultural-bg.jpg"
              alt="Cambodian countryside sunrise with Angkor Wat and emerald rice paddies"
              className={`cambodian-art-img ${imageLoaded ? 'loaded' : ''}`}
              loading="eager"
              decoding="async"
              onLoad={() => setImageLoaded(true)}
              onError={() => setImageError(true)}
            />
          </picture>
        )}

        {/* Layer 2: Readability Overlay & Atmospheric Gradients */}
        <div className="cambodian-scenic-overlay" />
        <div className="cambodian-vignette-overlay" />

        {/* Layer 3: Architectural Khmer Corner Carving Linework */}
        <div className="cambodian-ambient-ornaments">
          <KhmerCornerKbach position="top-left" size={54} />
          <KhmerCornerKbach position="top-right" size={54} />
        </div>
      </div>
    );
  }

  // 2. HERO SHOWCASE VARIANT (Rich welcome card with framed landscape & traditional motifs)
  if (variant === 'hero') {
    return (
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, ease: 'easeOut' }}
        className={`cambodian-hero-showcase ${dark ? 'dark' : 'light'} ${className}`}
      >
        {/* Corner Ornaments */}
        <KhmerCornerKbach position="top-left" size={42} />
        <KhmerCornerKbach position="top-right" size={42} />
        <KhmerCornerKbach position="bottom-left" size={42} />
        <KhmerCornerKbach position="bottom-right" size={42} />

        {/* Visual Vista with Landscape Image */}
        <div className="cambodian-hero-vista">
          <picture>
            <source srcSet="/images/cambodia-cultural-bg.webp" type="image/webp" />
            <img
              src="/images/cambodia-cultural-bg.jpg"
              alt="Angkor Wat sunrise landscape"
              className="cambodian-hero-img"
              loading="eager"
            />
          </picture>
          <div className="hero-vista-gradient" />
          <div className="hero-vista-badge">
            <Sun size={13} className="hero-badge-sun" />
            <span>បេតិកភណ្ឌអង្គរវត្ត & ធម្មជាតិខ្មែរ · ANGKOR WAT SUNRISE</span>
          </div>
        </div>

        {/* Content Section with Authentic Cultural Framing */}
        <div className="cambodian-hero-content">
          <div className="hero-eyebrow">
            <KhmerLotusMotif size={22} />
            <span>KHMER AI TRANSLATOR & SPEECH PLATFORM</span>
            <span className="hero-tag">© 2026</span>
          </div>

          <h2 className="hero-title">
            ស្វាគមន៍មកកាន់ <em>Khmer Translator</em>
          </h2>
          <p className="hero-desc">
            កម្មវិធីឆ្លាតវៃសម្រាប់បម្លែងសំឡេង វីដេអូ បកប្រែជាភាសាខ្មែរ កែសម្រួល Subtitles
            និងបញ្ចូលសំឡេងនិយាយបែបធម្មជាតិ (AI Dubbing) ដោយរក្សាការសម្ងាត់ 100% លើកុំព្យូទ័ររបស់អ្នក។
          </p>

          <KhmerBorderDivider className="hero-divider" />

          {/* Highlights Grid */}
          <div className="hero-features-grid">
            <div className="hero-feature-item">
              <span className="feature-bullet gold" />
              <div>
                <b>Local Whisper Engine</b>
                <small>ល្បឿនលឿន សុវត្ថិភាពខ្ពស់ គ្មាន Cloud Fee</small>
              </div>
            </div>
            <div className="hero-feature-item">
              <span className="feature-bullet green" />
              <div>
                <b>Khmer AI Dubbing Studio</b>
                <small>សំឡេងប្រុស (Piseth) & ស្រី (Sreymom) ពិតៗ</small>
              </div>
            </div>
            <div className="hero-feature-item">
              <span className="feature-bullet bronze" />
              <div>
                <b>Subtitle Editor Pro</b>
                <small>Split, Merge, Timecode Sync & Live Preview</small>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="hero-actions">
            {onNewProject && (
              <button className="primary-btn hero-btn" onClick={onNewProject}>
                <CloudUpload size={16} /> ចាប់ផ្ដើមគម្រោងថ្មី (New Project)
              </button>
            )}
            {onExploreHistory && (
              <button className="secondary-btn hero-btn" onClick={onExploreHistory}>
                <Compass size={16} /> ប្រវត្តិគម្រោង (Project History)
              </button>
            )}
          </div>
        </div>
      </motion.div>
    );
  }

  // 3. EMPTY STATE / WELCOME CARD VARIANT
  if (variant === 'empty-state') {
    return (
      <div className={`cambodian-empty-card ${dark ? 'dark' : 'light'} ${className}`}>
        <KhmerCornerKbach position="top-left" size={36} />
        <KhmerCornerKbach position="top-right" size={36} />

        <div className="empty-vista-preview">
          <picture>
            <source srcSet="/images/cambodia-cultural-bg.webp" type="image/webp" />
            <img
              src="/images/cambodia-cultural-bg.jpg"
              alt="Angkor Wat and emerald rice fields"
              className="empty-vista-img"
              loading="lazy"
            />
          </picture>
          <div className="empty-vista-tint" />
          <div className="empty-lotus-center">
            <KhmerLotusMotif size={44} />
          </div>
        </div>

        <div className="empty-card-body">
          <h3>មិនទាន់មានគម្រោងដំណើរការនៅឡើយទេ</h3>
          <p>
            សូមជ្រើសរើស ឬទម្លាក់ឯកសារវីដេអូ/អូឌីយ៉ូ ដើម្បីចាប់ផ្ដើមបម្លែងសំឡេង
            និងបង្កើតអត្ថបទរត់រឿងជាភាសាខ្មែរ។
          </p>
          {onNewProject && (
            <button className="primary-btn" onClick={onNewProject}>
              <CloudUpload size={16} /> បង្កើតការបកប្រែថ្មី (New Translation)
            </button>
          )}
        </div>
      </div>
    );
  }

  // 4. BANNER VARIANT (Compact landscape header band)
  return (
    <div className={`cambodian-cultural-banner ${dark ? 'dark' : 'light'} ${className}`}>
      <picture>
        <source srcSet="/images/cambodia-cultural-bg.webp" type="image/webp" />
        <img
          src="/images/cambodia-cultural-bg.jpg"
          alt="Angkor Wat Landscape"
          className="banner-img"
          loading="lazy"
        />
      </picture>
      <div className="banner-overlay" />
      <div className="banner-content">
        <KhmerLotusMotif size={28} />
        <div>
          <h4>Khmer Cultural AI Translation Platform</h4>
          <small>© 2026 Phengsovanreach · Powered by Local Whisper & Khmer Neural Speech</small>
        </div>
      </div>
      {children}
    </div>
  );
};
