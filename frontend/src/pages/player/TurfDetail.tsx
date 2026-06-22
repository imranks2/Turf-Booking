import { useMemo, useState } from 'react';
import { useParams } from 'react-router-dom';
import { useTurfDetail, useTurfSlots } from '@/hooks/useTurfs';
import { Spinner } from '@/components/ui/Spinner';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { AmenityTag } from '@/components/turf/AmenityTag';
import { CalendarGrid } from '@/components/calendar/CalendarGrid';
import { BookingFlow } from '@/components/booking/BookingFlow';
import { Footer } from '@/components/layout/Footer';
import { formatCurrency, toISODate } from '@/utils/formatters';
import { turfFallbackImage } from '@/utils/images';

const WEEKDAY_ORDER = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'];

function slotHours(start: string, end: string): number {
  const [sh, sm] = start.split(':').map(Number);
  const [eh, em] = end.split(':').map(Number);
  return (eh * 60 + em - (sh * 60 + sm)) / 60;
}

export function TurfDetail(): JSX.Element {
  const { turfId } = useParams<{ turfId: string }>();
  const { data: turf, isLoading } = useTurfDetail(turfId);
  const [sportId, setSportId] = useState<string>('');
  const [date, setDate] = useState<string>(toISODate(new Date()));
  const [selected, setSelected] = useState<Set<string>>(new Set());

  const activeSportId = sportId || turf?.sports[0]?.sport_id || '';
  const { data: slots, isLoading: slotsLoading } = useTurfSlots(turfId, activeSportId, date);

  const activeSport = turf?.sports.find((s) => s.sport_id === activeSportId) ?? turf?.sports[0];

  const totalHours = useMemo(() => {
    if (!slots) return 0;
    return slots
      .filter((s) => selected.has(s.id))
      .reduce((sum, s) => sum + slotHours(s.start_time, s.end_time), 0);
  }, [slots, selected]);

  if (isLoading || !turf) {
    return <Spinner label="Loading turf..." />;
  }

  const toggleSlot = (slotId: string): void => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(slotId)) {
        next.delete(slotId);
      } else {
        next.add(slotId);
      }
      return next;
    });
  };

  const resetSelection = (updater: () => void): void => {
    setSelected(new Set());
    updater();
  };

  return (
    <>
    <div className="mx-auto max-w-5xl px-4 py-8">
      <div className="mb-6 h-64 w-full overflow-hidden rounded-2xl bg-brand-950 shadow-card">
        <img
          src={turf.images[0] ?? turfFallbackImage(turf.id)}
          alt={turf.name}
          onError={(e) => {
            e.currentTarget.style.opacity = '0';
          }}
          className="h-full w-full object-cover"
        />
      </div>

      <div className="mb-6 flex flex-col gap-2">
        <h1 className="text-2xl font-bold text-gray-900">{turf.name}</h1>
        <p className="text-gray-500">
          {turf.address}, {turf.city}
        </p>
        {turf.description && <p className="text-sm text-gray-600">{turf.description}</p>}
        <div className="flex flex-wrap gap-1 pt-2">
          {turf.amenities.map((amenity) => (
            <AmenityTag key={amenity} amenity={amenity} />
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <div className="mb-4 flex flex-wrap items-center gap-3">
            <select
              className="rounded-lg border border-gray-300 px-3 py-2 text-sm"
              value={activeSportId}
              onChange={(e) => resetSelection(() => setSportId(e.target.value))}
            >
              {turf.sports.map((sport) => (
                <option key={sport.sport_id} value={sport.sport_id}>
                  {sport.sport_name} — {formatCurrency(sport.price_per_hour)}/hr
                </option>
              ))}
            </select>
            <input
              type="date"
              className="rounded-lg border border-gray-300 px-3 py-2 text-sm"
              value={date}
              min={toISODate(new Date())}
              onChange={(e) => resetSelection(() => setDate(e.target.value))}
            />
          </div>

          {slotsLoading ? (
            <Spinner label="Loading slots..." />
          ) : (
            <CalendarGrid
              slots={slots ?? []}
              selectedIds={selected}
              lockedIds={new Set()}
              onToggle={toggleSlot}
            />
          )}
        </Card>

        <div className="space-y-4">
          {activeSport && (
            <BookingFlow
              turfName={turf.name}
              turfSport={activeSport}
              selectedSlotIds={[...selected]}
              hours={totalHours}
            />
          )}

          <Card>
            <h2 className="mb-3 font-semibold text-gray-900">Operating hours</h2>
            <ul className="space-y-1 text-sm text-gray-600">
              {WEEKDAY_ORDER.map((day) => {
                const hours = turf.operating_hours[day];
                return (
                  <li key={day} className="flex justify-between">
                    <span className="uppercase">{day}</span>
                    {hours ? (
                      <span>
                        {hours.open} – {hours.close}
                      </span>
                    ) : (
                      <Badge tone="red">Closed</Badge>
                    )}
                  </li>
                );
              })}
            </ul>
          </Card>
        </div>
      </div>
    </div>
    <Footer />
    </>
  );
}
