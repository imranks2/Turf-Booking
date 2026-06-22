function unsplash(id: string, w: number): string {
  return `https://images.unsplash.com/photo-${id}?auto=format&fit=crop&w=${w}&q=70`;
}

export interface HeroSlide {
  id: string;
  image: string;
  eyebrow: string;
  title: string;
  subtitle: string;
}

export const HERO_SLIDES: HeroSlide[] = [
  {
    id: 'football',
    image: unsplash('1459865264687-595d652de67e', 1920),
    eyebrow: 'Football · 5s & 7s',
    title: 'Book your turf. Play your game.',
    subtitle: 'Floodlit pitches, instant booking, zero hidden charges.',
  },
  {
    id: 'cricket',
    image: unsplash('1540747913346-19e32dc3e97e', 1920),
    eyebrow: 'Box Cricket',
    title: 'Premium grounds, near you.',
    subtitle: 'Discover top-rated venues across 30+ cities.',
  },
  {
    id: 'night',
    image: unsplash('1551958219-acbc608c6377', 1920),
    eyebrow: 'Play anytime',
    title: 'Early mornings to late nights.',
    subtitle: 'Live availability, secure your slot in seconds.',
  },
];

export interface SportCategory {
  name: string;
  image: string;
}

export const SPORT_CATEGORIES: SportCategory[] = [
  { name: 'Football', image: unsplash('1517466787929-bc90951d0974', 600) },
  { name: 'Cricket', image: unsplash('1531415074968-036ba1b575da', 600) },
  { name: 'Badminton', image: unsplash('1626224583764-f87db24ac4ea', 600) },
  { name: 'Basketball', image: unsplash('1546519638-68e109498ffc', 600) },
  { name: 'Tennis', image: unsplash('1622279457486-62dcc4a431d6', 600) },
  { name: 'Futsal', image: unsplash('1574629810360-7efbbe195018', 600) },
];

const TURF_FALLBACKS = [
  unsplash('1459865264687-595d652de67e', 800),
  unsplash('1551958219-acbc608c6377', 800),
  unsplash('1574629810360-7efbbe195018', 800),
  unsplash('1431324155629-1a6deb1dec8d', 800),
];

export function turfFallbackImage(seed: string): string {
  let hash = 0;
  for (let i = 0; i < seed.length; i += 1) {
    hash = (hash * 31 + seed.charCodeAt(i)) >>> 0;
  }
  return TURF_FALLBACKS[hash % TURF_FALLBACKS.length];
}
