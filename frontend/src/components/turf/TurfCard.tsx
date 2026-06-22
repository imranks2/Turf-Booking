import { Link } from 'react-router-dom';
import type { TurfCard as TurfCardType } from '@/types';
import { Badge } from '@/components/ui/Badge';
import { AmenityTag } from '@/components/turf/AmenityTag';
import { formatCurrency } from '@/utils/formatters';
import { turfFallbackImage } from '@/utils/images';

export interface TurfCardProps {
  turf: TurfCardType;
}

export function TurfCard({ turf }: TurfCardProps): JSX.Element {
  const cover = turf.images[0] ?? turfFallbackImage(turf.id);
  return (
    <Link to={`/turfs/${turf.id}`} className="group block focus:outline-none">
      <article className="overflow-hidden rounded-2xl border border-gray-100 bg-white shadow-card transition-all duration-300 group-hover:-translate-y-1 group-hover:shadow-soft">
        <div className="relative h-44 w-full overflow-hidden bg-brand-950">
          <img
            src={cover}
            alt={turf.name}
            onError={(e) => {
              e.currentTarget.style.opacity = '0';
            }}
            className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
          />
          <div className="absolute inset-x-0 bottom-0 h-16 bg-gradient-to-t from-black/50 to-transparent" />
          {turf.min_price_per_hour !== null && (
            <span className="absolute bottom-3 left-3 rounded-full bg-white/95 px-3 py-1 text-sm font-semibold text-brand-700 shadow">
              {formatCurrency(turf.min_price_per_hour)}/hr
            </span>
          )}
          {turf.distance_km !== null && (
            <span className="absolute right-3 top-3 rounded-full bg-brand-950/70 px-2.5 py-1 text-xs font-medium text-white backdrop-blur">
              {turf.distance_km} km
            </span>
          )}
        </div>
        <div className="space-y-2 p-4">
          <h3 className="font-heading text-lg font-semibold text-gray-900">{turf.name}</h3>
          <p className="flex items-center gap-1 text-sm text-gray-500">
            <span className="text-brand-600">📍</span>
            {turf.address}, {turf.city}
          </p>
          <div className="flex flex-wrap gap-1 pt-1">
            {turf.sports.slice(0, 3).map((sport) => (
              <Badge key={sport.id} tone="green">
                {sport.sport_name}
              </Badge>
            ))}
          </div>
          <div className="flex flex-wrap gap-1">
            {turf.amenities.slice(0, 4).map((amenity) => (
              <AmenityTag key={amenity} amenity={amenity} />
            ))}
          </div>
        </div>
      </article>
    </Link>
  );
}
