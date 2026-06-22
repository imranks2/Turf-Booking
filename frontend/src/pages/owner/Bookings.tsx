import { useOwnerBookings } from '@/hooks/useOwnerTurfs';
import { Table } from '@/components/ui/Table';
import { Badge } from '@/components/ui/Badge';
import { Spinner } from '@/components/ui/Spinner';
import { formatCurrency, formatDate } from '@/utils/formatters';
import { BOOKING_STATUS_LABELS } from '@/utils/constants';
import type { Booking } from '@/types';

export function OwnerBookings(): JSX.Element {
  const { data: bookings, isLoading } = useOwnerBookings();

  if (isLoading || !bookings) {
    return <Spinner label="Loading bookings..." />;
  }

  return (
    <div className="space-y-6 p-6">
      <h1 className="text-2xl font-bold text-gray-900">Bookings</h1>
      <Table<Booking>
        columns={[
          { header: 'Code', cell: (b) => `#${b.booking_code}` },
          { header: 'Date', cell: (b) => formatDate(b.booking_date) },
          { header: 'Slots', cell: (b) => b.slot_ids.length },
          { header: 'Amount', cell: (b) => formatCurrency(b.total_amount) },
          { header: 'Payout', cell: (b) => formatCurrency(b.owner_payout_amount) },
          {
            header: 'Status',
            cell: (b) => <Badge tone="blue">{BOOKING_STATUS_LABELS[b.status]}</Badge>,
          },
        ]}
        rows={bookings}
        rowKey={(b) => b.id}
        empty="No bookings yet"
      />
    </div>
  );
}
