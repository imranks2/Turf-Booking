import { Link } from 'react-router-dom';
import type { Booking } from '@/types';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { formatCurrency, formatDate } from '@/utils/formatters';
import { BOOKING_STATUS_LABELS } from '@/utils/constants';

const STATUS_TONE: Record<Booking['status'], 'green' | 'amber' | 'red' | 'gray' | 'blue'> = {
  confirmed: 'green',
  pending_payment: 'amber',
  cancelled: 'red',
  completed: 'blue',
  no_show: 'gray',
};

export interface BookingCardProps {
  booking: Booking;
}

export function BookingCard({ booking }: BookingCardProps): JSX.Element {
  return (
    <Link to={`/bookings/${booking.id}`} className="block">
      <Card className="transition hover:shadow-md">
        <div className="flex items-start justify-between">
          <div>
            <p className="font-semibold text-gray-900">#{booking.booking_code}</p>
            <p className="text-sm text-gray-500">{formatDate(booking.booking_date)}</p>
          </div>
          <Badge tone={STATUS_TONE[booking.status]}>{BOOKING_STATUS_LABELS[booking.status]}</Badge>
        </div>
        <div className="mt-3 flex items-center justify-between text-sm">
          <span className="text-gray-500">{booking.slot_ids.length} slot(s)</span>
          <span className="font-medium text-gray-800">{formatCurrency(booking.total_amount)}</span>
        </div>
      </Card>
    </Link>
  );
}
