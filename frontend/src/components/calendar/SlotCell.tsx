import type { Slot } from '@/types';
import { formatSlotRange } from '@/utils/formatters';

export interface SlotCellProps {
  slot: Slot;
  selected: boolean;
  isLocked: boolean;
  onToggle: (slotId: string) => void;
}

const STATUS_CLASSES: Record<Slot['status'], string> = {
  available: 'border-gray-300 bg-white text-gray-800 hover:border-brand-500',
  booked: 'border-red-200 bg-red-50 text-red-700',
  blocked: 'border-gray-200 bg-gray-100 text-gray-500',
  maintenance: 'border-amber-200 bg-amber-50 text-amber-700',
};

export function SlotCell({ slot, selected, isLocked, onToggle }: SlotCellProps): JSX.Element {
  const disabled = slot.status !== 'available' || isLocked;
  const base = selected
    ? 'border-brand-600 bg-brand-50 text-brand-700 ring-2 ring-brand-500'
    : STATUS_CLASSES[slot.status];

  return (
    <button
      type="button"
      disabled={disabled}
      onClick={() => onToggle(slot.id)}
      className={`rounded-lg border px-2 py-2 text-sm font-medium transition disabled:cursor-not-allowed disabled:opacity-60 ${base}`}
    >
      {formatSlotRange(slot.start_time, slot.end_time)}
      {isLocked && slot.status === 'available' && <span className="ml-1 text-xs">🔒</span>}
    </button>
  );
}
