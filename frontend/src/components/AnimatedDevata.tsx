import React, { useMemo } from 'react';

export interface AnimatedDevataProps {
  show?: boolean;
  reducedMotion?: boolean;
  dark?: boolean;
  variant?: 'sidebar' | 'corner';
  className?: string;
}

interface PetalConfig {
  id: number;
  type: 'lotus' | 'jasmine';
  size: number;
  leftPercent: number;
  bottomPercent: number;
  tx: number;
  ty: number;
  rotate: number;
  duration: number;
  delay: number;
  opacity: number;
}

/**
 * AnimatedDevata
 * Traditional Khmer celestial angel (Devata/Apsara) gracefully scattering
 * lotus petals and jasmine blossoms on the sidebar.
 * © 2026 Phengsovanreach. All rights reserved.
 */
export const AnimatedDevata: React.FC<AnimatedDevataProps> = ({
  show = true,
  reducedMotion = false,
  dark = true,
  variant = 'sidebar',
  className = '',
}) => {
  // Pre-calculate randomized petal flight paths suited for sidebar dimensions
  const petals: PetalConfig[] = useMemo(() => {
    const list: PetalConfig[] = [];
    const count = variant === 'sidebar' ? 12 : 16;
    for (let i = 0; i < count; i++) {
      const isLotus = i % 2 === 0 || i % 5 === 0;
      // Trajectory drifting upward and gently across
      const tx = variant === 'sidebar' ? 40 + (i * 18) % 110 : 180 + (i * 27) % 360;
      const ty = variant === 'sidebar' ? -130 - (i * 22) % 180 : -240 - (i * 33) % 400;
      const rotate = 180 + (i * 67) % 720;
      const duration = variant === 'sidebar' ? 5.5 + (i * 0.6) % 3.5 : 6.5 + (i * 0.8) % 4.5;
      const delay = (i * 0.65) % 6;
      const size = isLotus
        ? (variant === 'sidebar' ? 10 + (i % 3) * 2 : 13 + (i % 4) * 2.5)
        : (variant === 'sidebar' ? 7 + (i % 3) * 1.5 : 9 + (i % 3) * 2);

      list.push({
        id: i,
        type: isLotus ? 'lotus' : 'jasmine',
        size,
        leftPercent: variant === 'sidebar' ? 24 + (i % 4) * 5 : 32 + (i % 5) * 4 - 8,
        bottomPercent: variant === 'sidebar' ? 58 + (i % 3) * 4 : 62 + (i % 4) * 3 - 6,
        tx,
        ty,
        rotate,
        duration,
        delay,
        opacity: isLotus ? 0.9 : 0.95,
      });
    }
    return list;
  }, [variant]);

  if (!show) {
    return null;
  }

  // 1. SIDEBAR VARIANT (Placed directly inside the sidebar as requested)
  if (variant === 'sidebar') {
    return (
      <div
        className={`sidebar-devata-card ${dark ? 'dark' : 'light'} ${reducedMotion ? 'reduced-motion' : ''} ${className}`}
        aria-hidden="true"
      >
        {/* Card Header with Khmer Lotus Motif */}
        <div className="sidebar-devata-head">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" className="head-lotus-icon">
            <path
              d="M12 2C12 2 9 8 9 12C9 15 10.5 17 12 18C13.5 17 15 15 15 12C15 8 12 2 12 2Z"
              fill="var(--gold, #d9b56d)"
            />
            <path
              d="M9 10C6 11.5 4 14 5 18C6 20 8.5 20.5 10 19C9.5 17 9 14 9 10Z"
              fill="var(--gold, #d9b56d)"
              fillOpacity="0.75"
            />
            <path
              d="M15 10C18 11.5 20 14 19 18C18 20 15.5 20.5 14 19C14.5 17 15 14 15 10Z"
              fill="var(--gold, #d9b56d)"
              fillOpacity="0.75"
            />
          </svg>
          <span>មរតកទេវតាខ្មែរ · DEVATA</span>
        </div>

        {/* Dedicated Devata Stage (Full Figure from Crown to Feet) */}
        <div className="devata-sidebar-stage">
          {/* Ambient Golden Aura Glow */}
          <div className="devata-sidebar-aura" />

          {/* Floating Petals within the stage */}
          {!reducedMotion && (
            <div className="devata-sidebar-petals">
              {petals.map((p) => (
                <div
                  key={p.id}
                  className={`devata-petal petal-${p.type}`}
                  style={{
                    left: `${p.leftPercent}%`,
                    bottom: `${p.bottomPercent}%`,
                    width: `${p.size}px`,
                    height: `${p.size}px`,
                    animationDuration: `${p.duration}s`,
                    animationDelay: `${p.delay}s`,
                    ['--petal-tx' as any]: `${p.tx}px`,
                    ['--petal-ty' as any]: `${p.ty}px`,
                    ['--petal-rot' as any]: `${p.rotate}deg`,
                    ['--petal-opacity' as any]: p.opacity,
                  }}
                >
                  {p.type === 'lotus' ? (
                    <svg viewBox="0 0 24 32" fill="none">
                      <path
                        d="M12 2C12 2 4 10 4 19C4 24.5 7.5 29 12 30C16.5 29 20 24.5 20 19C20 10 12 2 12 2Z"
                        fill="url(#lotusGradSidebar)"
                      />
                      <defs>
                        <linearGradient id="lotusGradSidebar" x1="12" y1="2" x2="12" y2="30" gradientUnits="userSpaceOnUse">
                          <stop stopColor="#ffc7d6" />
                          <stop offset="0.5" stopColor="#f484a0" />
                          <stop offset="1" stopColor="#d84872" />
                        </linearGradient>
                      </defs>
                    </svg>
                  ) : (
                    <svg viewBox="0 0 24 24" fill="none">
                      <circle cx="12" cy="6" r="4.5" fill="#ffffff" fillOpacity="0.95" />
                      <circle cx="17.7" cy="10.2" r="4.5" fill="#fdfbf7" fillOpacity="0.95" />
                      <circle cx="15.5" cy="17" r="4.5" fill="#fcf8f0" fillOpacity="0.95" />
                      <circle cx="8.5" cy="17" r="4.5" fill="#fdfbf7" fillOpacity="0.95" />
                      <circle cx="6.3" cy="10.2" r="4.5" fill="#ffffff" fillOpacity="0.95" />
                      <circle cx="12" cy="12" r="2.2" fill="#e5be6b" />
                    </svg>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Devata Celestial Figure */}
          <div className="devata-sidebar-figure">
            <picture>
              <source srcSet="/images/khmer-devata.webp" type="image/webp" />
              <img
                src="/images/khmer-devata.png"
                alt="Traditional Khmer Celestial Devata in sidebar"
                className="devata-sidebar-img"
                loading="eager"
              />
            </picture>
          </div>

          {/* Bottom Fade Gradient */}
          <div className="devata-sidebar-fade" />
        </div>
      </div>
    );
  }

  // 2. CORNER BACKDROP VARIANT (Alternative)
  return (
    <div
      className={`animated-devata-root ${dark ? 'dark' : 'light'} ${reducedMotion ? 'reduced-motion' : ''} ${className}`}
      aria-hidden="true"
    >
      <div className="devata-aura-glow" />
      {!reducedMotion && (
        <div className="devata-petals-emitter">
          {petals.map((p) => (
            <div
              key={p.id}
              className={`devata-petal petal-${p.type}`}
              style={{
                left: `${p.leftPercent}%`,
                bottom: `${p.bottomPercent}%`,
                width: `${p.size}px`,
                height: `${p.size}px`,
                animationDuration: `${p.duration}s`,
                animationDelay: `${p.delay}s`,
                ['--petal-tx' as any]: `${p.tx}px`,
                ['--petal-ty' as any]: `${p.ty}px`,
                ['--petal-rot' as any]: `${p.rotate}deg`,
                ['--petal-opacity' as any]: p.opacity,
              }}
            >
              {p.type === 'lotus' ? (
                <svg viewBox="0 0 24 32" fill="none">
                  <path
                    d="M12 2C12 2 4 10 4 19C4 24.5 7.5 29 12 30C16.5 29 20 24.5 20 19C20 10 12 2 12 2Z"
                    fill="url(#lotusGradCorner)"
                  />
                  <defs>
                    <linearGradient id="lotusGradCorner" x1="12" y1="2" x2="12" y2="30" gradientUnits="userSpaceOnUse">
                      <stop stopColor="#ffc7d6" />
                      <stop offset="0.5" stopColor="#f484a0" />
                      <stop offset="1" stopColor="#d84872" />
                    </linearGradient>
                  </defs>
                </svg>
              ) : (
                <svg viewBox="0 0 24 24" fill="none">
                  <circle cx="12" cy="6" r="4.5" fill="#ffffff" fillOpacity="0.95" />
                  <circle cx="17.7" cy="10.2" r="4.5" fill="#fdfbf7" fillOpacity="0.95" />
                  <circle cx="15.5" cy="17" r="4.5" fill="#fcf8f0" fillOpacity="0.95" />
                  <circle cx="8.5" cy="17" r="4.5" fill="#fdfbf7" fillOpacity="0.95" />
                  <circle cx="6.3" cy="10.2" r="4.5" fill="#ffffff" fillOpacity="0.95" />
                  <circle cx="12" cy="12" r="2.2" fill="#e5be6b" />
                </svg>
              )}
            </div>
          ))}
        </div>
      )}
      <div className="devata-figure-wrapper">
        <picture>
          <source srcSet="/images/khmer-devata.webp" type="image/webp" />
          <img
            src="/images/khmer-devata.png"
            alt="Traditional Khmer Celestial Devata"
            className="devata-figure-img"
            loading="eager"
          />
        </picture>
      </div>
      <div className="devata-bottom-fade" />
    </div>
  );
};
