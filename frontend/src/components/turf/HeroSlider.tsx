import { useEffect, useState, type ReactNode } from 'react';
import { HERO_SLIDES } from '@/utils/images';

export interface HeroSliderProps {
  children?: ReactNode;
}

export function HeroSlider({ children }: HeroSliderProps): JSX.Element {
  const [active, setActive] = useState(0);

  useEffect(() => {
    const timer = window.setInterval(() => {
      setActive((i) => (i + 1) % HERO_SLIDES.length);
    }, 5000);
    return () => window.clearInterval(timer);
  }, []);

  const slide = HERO_SLIDES[active];

  return (
    <section className="relative isolate overflow-hidden bg-brand-950">
      {HERO_SLIDES.map((s, i) => (
        <img
          key={s.id}
          src={s.image}
          alt=""
          aria-hidden
          onError={(e) => {
            e.currentTarget.style.opacity = '0';
          }}
          className={`absolute inset-0 h-full w-full object-cover transition-opacity duration-1000 ${
            i === active ? 'opacity-100' : 'opacity-0'
          }`}
        />
      ))}
      <div className="absolute inset-0 bg-hero-overlay" />

      <div className="relative mx-auto flex min-h-[460px] max-w-6xl flex-col justify-center px-4 py-16 sm:px-6 lg:px-8">
        <div key={slide.id} className="max-w-2xl animate-slide-up">
          <span className="inline-flex items-center rounded-full bg-white/15 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-lime-400 backdrop-blur">
            {slide.eyebrow}
          </span>
          <h1 className="mt-4 text-4xl font-bold leading-tight text-white text-balance sm:text-5xl">
            {slide.title}
          </h1>
          <p className="mt-3 text-lg text-white/85">{slide.subtitle}</p>
        </div>

        {children && <div className="mt-8 max-w-3xl animate-fade-in">{children}</div>}

        <div className="mt-8 flex gap-2">
          {HERO_SLIDES.map((s, i) => (
            <button
              key={s.id}
              type="button"
              aria-label={`Slide ${i + 1}`}
              onClick={() => setActive(i)}
              className={`h-1.5 rounded-full transition-all ${
                i === active ? 'w-8 bg-lime-400' : 'w-4 bg-white/40'
              }`}
            />
          ))}
        </div>
      </div>
    </section>
  );
}
