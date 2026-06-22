import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCreateTurf, type TurfFormInput } from '@/hooks/useOwnerTurfs';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { COMMON_AMENITIES } from '@/utils/constants';

const WEEKDAYS = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'];

interface DayState {
  enabled: boolean;
  open: string;
  close: string;
}

export function TurfForm(): JSX.Element {
  const navigate = useNavigate();
  const createTurf = useCreateTurf();
  const [error, setError] = useState<string | null>(null);
  const [amenities, setAmenities] = useState<Set<string>>(new Set());
  const [days, setDays] = useState<Record<string, DayState>>(
    Object.fromEntries(WEEKDAYS.map((d) => [d, { enabled: true, open: '06:00', close: '23:00' }])),
  );

  const toggleAmenity = (amenity: string): void => {
    setAmenities((prev) => {
      const next = new Set(prev);
      next.has(amenity) ? next.delete(amenity) : next.add(amenity);
      return next;
    });
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    setError(null);
    const form = new FormData(event.currentTarget);
    const operating_hours: TurfFormInput['operating_hours'] = {};
    for (const day of WEEKDAYS) {
      const state = days[day];
      if (state.enabled) {
        operating_hours[day] = { open: state.open, close: state.close };
      }
    }
    if (Object.keys(operating_hours).length === 0) {
      setError('Select at least one open day');
      return;
    }
    try {
      await createTurf.mutateAsync({
        name: String(form.get('name')),
        address: String(form.get('address')),
        city: String(form.get('city')),
        description: String(form.get('description') || ''),
        amenities: [...amenities],
        operating_hours,
      });
      navigate('/owner/turfs');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create turf');
    }
  };

  return (
    <div className="mx-auto max-w-2xl p-6">
      <h1 className="mb-6 text-2xl font-bold text-gray-900">Add turf</h1>
      <form className="space-y-4" onSubmit={(e) => void handleSubmit(e)}>
        <Card className="space-y-4">
          <Input id="name" name="name" label="Turf name" required />
          <Input id="address" name="address" label="Address" required />
          <Input id="city" name="city" label="City" required />
          <Input id="description" name="description" label="Description" />
        </Card>

        <Card>
          <h3 className="mb-3 font-semibold text-gray-900">Amenities</h3>
          <div className="flex flex-wrap gap-2">
            {COMMON_AMENITIES.map((amenity) => (
              <button
                type="button"
                key={amenity}
                onClick={() => toggleAmenity(amenity)}
                className={`rounded-full border px-3 py-1 text-sm capitalize ${
                  amenities.has(amenity)
                    ? 'border-brand-500 bg-brand-50 text-brand-700'
                    : 'border-gray-300 text-gray-600'
                }`}
              >
                {amenity.replace(/_/g, ' ')}
              </button>
            ))}
          </div>
        </Card>

        <Card>
          <h3 className="mb-3 font-semibold text-gray-900">Operating hours</h3>
          <div className="space-y-2">
            {WEEKDAYS.map((day) => (
              <div key={day} className="flex items-center gap-3">
                <label className="flex w-20 items-center gap-2 text-sm uppercase">
                  <input
                    type="checkbox"
                    checked={days[day].enabled}
                    onChange={(e) =>
                      setDays((prev) => ({ ...prev, [day]: { ...prev[day], enabled: e.target.checked } }))
                    }
                  />
                  {day}
                </label>
                <input
                  type="time"
                  value={days[day].open}
                  disabled={!days[day].enabled}
                  onChange={(e) =>
                    setDays((prev) => ({ ...prev, [day]: { ...prev[day], open: e.target.value } }))
                  }
                  className="rounded-lg border border-gray-300 px-2 py-1 text-sm disabled:opacity-50"
                />
                <span className="text-gray-400">to</span>
                <input
                  type="time"
                  value={days[day].close}
                  disabled={!days[day].enabled}
                  onChange={(e) =>
                    setDays((prev) => ({ ...prev, [day]: { ...prev[day], close: e.target.value } }))
                  }
                  className="rounded-lg border border-gray-300 px-2 py-1 text-sm disabled:opacity-50"
                />
              </div>
            ))}
          </div>
        </Card>

        {error && <p className="text-sm text-red-500">{error}</p>}
        <Button type="submit" loading={createTurf.isPending}>
          Create turf
        </Button>
      </form>
    </div>
  );
}
