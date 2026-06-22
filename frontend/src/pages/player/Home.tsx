import { useState } from 'react';
import { useDiscoverTurfs, useCities, useSports } from '@/hooks/useTurfs';
import { TurfCard } from '@/components/turf/TurfCard';
import { HeroSlider } from '@/components/turf/HeroSlider';
import { Footer } from '@/components/layout/Footer';
import { Spinner } from '@/components/ui/Spinner';
import { Button } from '@/components/ui/Button';
import { SPORT_CATEGORIES } from '@/utils/images';
import type { DiscoveryFilters } from '@/types';

const STEPS = [
  { icon: '🔍', title: 'Find a turf', text: 'Search by city, sport and price. Live availability.' },
  { icon: '📅', title: 'Pick your slot', text: 'Choose your time. We hold it while you pay.' },
  { icon: '⚡', title: 'Play instantly', text: 'Pay the advance, get instant confirmation on WhatsApp.' },
];

export function Home(): JSX.Element {
  const [draft, setDraft] = useState<DiscoveryFilters>({ page: 1, limit: 20 });
  const [filters, setFilters] = useState<DiscoveryFilters>({ page: 1, limit: 20 });

  const { data, isLoading, isError } = useDiscoverTurfs(filters);
  const { data: cities } = useCities();
  const { data: sports } = useSports();

  const applyFilters = (next: DiscoveryFilters): void => {
    setDraft(next);
    setFilters({ ...next, page: 1 });
  };

  const pickSport = (sport: string): void => {
    applyFilters({ ...draft, sport });
    document.getElementById('results')?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <div>
      <HeroSlider>
        <div className="grid grid-cols-1 gap-3 rounded-2xl bg-white p-3 shadow-card sm:grid-cols-[1fr_1fr_auto]">
          <select
            aria-label="City"
            className="rounded-xl border border-gray-200 px-4 py-3 text-sm text-gray-800 focus:ring-2 focus:ring-brand-500"
            value={draft.city ?? ''}
            onChange={(e) => setDraft((d) => ({ ...d, city: e.target.value || undefined }))}
          >
            <option value="">All cities</option>
            {cities?.map((city) => (
              <option key={city} value={city}>
                {city}
              </option>
            ))}
          </select>
          <select
            aria-label="Sport"
            className="rounded-xl border border-gray-200 px-4 py-3 text-sm text-gray-800 focus:ring-2 focus:ring-brand-500"
            value={draft.sport ?? ''}
            onChange={(e) => setDraft((d) => ({ ...d, sport: e.target.value || undefined }))}
          >
            <option value="">All sports</option>
            {sports?.map((sport) => (
              <option key={sport.name} value={sport.name}>
                {sport.name}
              </option>
            ))}
          </select>
          <Button size="lg" onClick={() => applyFilters(draft)}>
            Search turfs
          </Button>
        </div>
      </HeroSlider>

      {/* Sport categories */}
      <section className="mx-auto max-w-6xl px-4 py-12 sm:px-6 lg:px-8">
        <h2 className="mb-6 text-2xl font-bold text-gray-900">Play by sport</h2>
        <div className="grid grid-cols-3 gap-3 sm:grid-cols-6">
          {SPORT_CATEGORIES.map((cat) => (
            <button
              key={cat.name}
              type="button"
              onClick={() => pickSport(cat.name)}
              className="group relative aspect-square overflow-hidden rounded-2xl bg-brand-950 shadow-card"
            >
              <img
                src={cat.image}
                alt={cat.name}
                onError={(e) => {
                  e.currentTarget.style.opacity = '0';
                }}
                className="h-full w-full object-cover opacity-80 transition-transform duration-500 group-hover:scale-110"
              />
              <span className="absolute inset-0 flex items-end justify-center bg-gradient-to-t from-black/70 to-transparent p-2 text-sm font-semibold text-white">
                {cat.name}
              </span>
            </button>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section className="bg-brand-50/60 py-14">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
          <h2 className="mb-8 text-center text-2xl font-bold text-gray-900">How it works</h2>
          <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
            {STEPS.map((step, i) => (
              <div key={step.title} className="rounded-2xl bg-white p-6 text-center shadow-card">
                <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-gradient text-2xl shadow-soft">
                  {step.icon}
                </div>
                <span className="text-xs font-semibold uppercase tracking-wide text-brand-600">
                  Step {i + 1}
                </span>
                <h3 className="mt-1 text-lg font-semibold text-gray-900">{step.title}</h3>
                <p className="mt-2 text-sm text-gray-500">{step.text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Results */}
      <section id="results" className="mx-auto max-w-6xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">
              {filters.sport ? `${filters.sport} turfs` : 'Featured turfs'}
              {filters.city ? ` in ${filters.city}` : ''}
            </h2>
            {data && <p className="text-sm text-gray-500">{data.total} venue(s) available</p>}
          </div>
          <div className="flex items-center gap-2">
            <input
              type="number"
              min={0}
              placeholder="Min ₹"
              className="w-24 rounded-full border border-gray-200 px-4 py-2 text-sm"
              value={draft.price_min ?? ''}
              onChange={(e) =>
                setDraft((d) => ({ ...d, price_min: e.target.value ? Number(e.target.value) : undefined }))
              }
            />
            <input
              type="number"
              min={0}
              placeholder="Max ₹"
              className="w-24 rounded-full border border-gray-200 px-4 py-2 text-sm"
              value={draft.price_max ?? ''}
              onChange={(e) =>
                setDraft((d) => ({ ...d, price_max: e.target.value ? Number(e.target.value) : undefined }))
              }
            />
            <Button variant="secondary" size="sm" onClick={() => applyFilters(draft)}>
              Apply
            </Button>
          </div>
        </div>

        {isLoading && <Spinner label="Loading turfs..." />}
        {isError && <p className="text-sm text-red-500">Failed to load turfs. Please try again.</p>}
        {data && data.items.length === 0 && (
          <p className="py-12 text-center text-gray-500">No turfs match your filters.</p>
        )}

        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {data?.items.map((turf) => (
            <TurfCard key={turf.id} turf={turf} />
          ))}
        </div>
      </section>

      <Footer />
    </div>
  );
}
