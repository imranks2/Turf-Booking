import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useBooking, useCancelBooking } from '@/hooks/useBookings';
import { Card } from '@/components/ui/Card';
import { Spinner } from '@/components/ui/Spinner';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { formatCurrency, formatDate } from '@/utils/formatters';

export function BookingConfirm(): JSX.Element {
  const { bookingId } = useParams<{ bookingId: string }>();
  const { data: booking, isLoading } = useBooking(bookingId, true);
  const cancelBooking = useCancelBooking();
  const [cancelMessage, setCancelMessage] = useState<string | null>(null);

  if (isLoading || !booking) {
    return <Spinner label="Loading booking..." />;
  }

  const isConfirmed = booking.status === 'confirmed';
  const isPending = booking.status === 'pending_payment';
  const isCancelled = booking.status === 'cancelled';

  const handleCancel = async (): Promise<void> => {
    if (!bookingId || !window.confirm('Cancel this booking? Refund depends on time to kickoff.')) {
      return;
    }
    const result = await cancelBooking.mutateAsync({ bookingId, reason: 'player_cancelled' });
    setCancelMessage(
      result.refund_amount > 0
        ? `Cancelled. Refund of ${formatCurrency(result.refund_amount)} (${result.refund_percentage}%) is being processed.`
        : 'Cancelled. No refund applies per the cancellation policy.',
    );
  };

  return (
    <div className="mx-auto max-w-lg px-4 py-10">
      <Card className="text-center">
        {isPending && (
          <>
            <Spinner label="Confirming your payment..." />
            <p className="text-sm text-gray-500">
              This can take a few seconds. We are waiting for payment confirmation.
            </p>
          </>
        )}

        {isConfirmed && (
          <div className="space-y-3">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-brand-100 text-2xl">
              ✅
            </div>
            <h1 className="text-xl font-bold text-gray-900">Booking confirmed!</h1>
            <p className="text-gray-600">
              Booking code <span className="font-semibold">#{booking.booking_code}</span>
            </p>
            <p className="text-sm text-gray-500">{formatDate(booking.booking_date)}</p>
            <p className="text-sm text-gray-500">
              Paid advance: {formatCurrency(booking.advance_deposit_amount)}
            </p>
          </div>
        )}

        {isCancelled && (
          <div className="space-y-2">
            <Badge tone="red">Cancelled</Badge>
            <p className="text-sm text-gray-600">
              {cancelMessage ?? 'This booking has been cancelled.'}
            </p>
            {booking.refund_amount ? (
              <p className="text-sm text-gray-500">
                Refund: {formatCurrency(booking.refund_amount)} ({booking.refund_status})
              </p>
            ) : null}
          </div>
        )}

        {!isPending && !isConfirmed && !isCancelled && (
          <div className="space-y-2">
            <Badge tone="red">Payment not completed</Badge>
            <p className="text-sm text-gray-600">
              Your booking could not be confirmed. Please try again.
            </p>
          </div>
        )}

        {isConfirmed && (
          <div className="mt-4">
            {cancelMessage ? (
              <p className="text-sm text-brand-700">{cancelMessage}</p>
            ) : (
              <Button
                variant="danger"
                loading={cancelBooking.isPending}
                onClick={() => void handleCancel()}
              >
                Cancel booking
              </Button>
            )}
          </div>
        )}

        <div className="mt-6 flex justify-center gap-3">
          <Link to="/bookings">
            <Button variant="secondary">My bookings</Button>
          </Link>
          <Link to="/">
            <Button>Find more turfs</Button>
          </Link>
        </div>
      </Card>
    </div>
  );
}
