import type { Slot } from '@/types';
import { SlotCell } from '@/components/calendar/SlotCell';

export interface CalendarGridProps {
  slots: Slot[];
  selectedIds: Set<string>;
  lockedIds: Set<string>;
  onToggle: (slotId: string) => void;
}

export function CalendarGrid({ slots, selectedIds, lockedIds, onToggle }: CalendarGridProps): JSX.Element {
  if (slots.length === 0) {
    return <p className="py-6 text-center text-sm text-gray-500">No available slots for this day.</p>;
  }
  return (
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-4">
      {slots.map((slot) => (
        <SlotCell
          key={slot.id}
          slot={slot}
          selected={selectedIds.has(slot.id)}
          isLocked={lockedIds.has(slot.id)}
          onToggle={onToggle}
        />
      ))}
    </div>
  );
}
