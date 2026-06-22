import { useEffect, useState } from 'react';
import {
  useBlockSlots,
  useGenerateSlots,
  useOwnerSlots,
  useOwnerTurfs,
} from '@/hooks/useOwnerTurfs';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Spinner } from '@/components/ui/Spinner';
import { CalendarGrid } from '@/components/calendar/CalendarGrid';
import { toISODate } from '@/utils/formatters';

const BLOCK_REASONS = ['offline_walkin', 'maintenance', 'private_event', 'other'];

export function OwnerCalendar(): JSX.Element {
  const { data: turfs } = useOwnerTurfs();
  const [turfId, setTurfId] = useState<string>('');
  const [sportId, setSportId] = useState<string>('');
  const [date, setDate] = useState<string>(toISODate(new Date()));
  const [reason, setReason] = useState<string>('maintenance');
  const [selected, setSelected] = useState<Set<string>>(new Set());

  const turf = turfs?.find((t) => t.id === turfId) ?? turfs?.[0];
  const activeTurfId = turfId || turf?.id || '';
  const activeSportId = sportId || turf?.sports[0]?.sport_id || '';
  const turfSport = turf?.sports.find((s) => s.sport_id === activeSportId) ?? turf?.sports[0];

  const { data: slots, isLoading } = useOwnerSlots(activeTurfId, activeSportId, date);
  const generateSlots = useGenerateSlots();
  const blockSlots = useBlockSlots();

  useEffect(() => {
    setSelected(new Set());
  }, [activeTurfId, activeSportId, date]);

  const toggle = (slotId: string): void => {
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(slotId) ? next.delete(slotId) : next.add(slotId);
      return next;
    });
  };

  const handleGenerate = async (): Promise<void> => {
    if (turfSport) {
      await generateSlots.mutateAsync({ turf_sport_id: turfSport.id, days: 14 });
    }
  };

  const handleBlock = async (): Promise<void> => {
    if (!turfSport || !slots) return;
    const chosen = slots.filter((s) => selected.has(s.id));
    if (chosen.length === 0) return;
    const starts = chosen.map((s) => s.start_time).sort();
    const ends = chosen.map((s) => s.end_time).sort();
    await blockSlots.mutateAsync({
      turf_sport_id: turfSport.id,
      slot_date: date,
      start_time: starts[0].slice(0, 5),
      end_time: ends[ends.length - 1].slice(0, 5),
      reason,
    });
    setSelected(new Set());
  };

  return (
    <div className="space-y-6 p-6">
      <h1 className="text-2xl font-bold text-gray-900">Calendar</h1>

      <Card>
        <div className="flex flex-wrap items-center gap-3">
          <select
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm"
            value={activeTurfId}
            onChange={(e) => {
              setTurfId(e.target.value);
              setSportId('');
            }}
          >
            {turfs?.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>
          <select
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm"
            value={activeSportId}
            onChange={(e) => setSportId(e.target.value)}
          >
            {turf?.sports.map((s) => (
              <option key={s.sport_id} value={s.sport_id}>
                {s.sport_name}
              </option>
            ))}
          </select>
          <input
            type="date"
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm"
            value={date}
            onChange={(e) => setDate(e.target.value)}
          />
          <Button variant="secondary" loading={generateSlots.isPending} onClick={() => void handleGenerate()}>
            Generate 14 days
          </Button>
        </div>
      </Card>

      <Card>
        {isLoading ? (
          <Spinner label="Loading slots..." />
        ) : (
          <CalendarGrid slots={slots ?? []} selectedIds={selected} lockedIds={new Set()} onToggle={toggle} />
        )}

        <div className="mt-4 flex flex-wrap items-center gap-3 border-t border-gray-100 pt-4">
          <select
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
          >
            {BLOCK_REASONS.map((r) => (
              <option key={r} value={r}>
                {r.replace(/_/g, ' ')}
              </option>
            ))}
          </select>
          <Button
            variant="danger"
            disabled={selected.size === 0}
            loading={blockSlots.isPending}
            onClick={() => void handleBlock()}
          >
            Block {selected.size > 0 ? `${selected.size} slot(s)` : 'selected'}
          </Button>
        </div>
      </Card>
    </div>
  );
}
