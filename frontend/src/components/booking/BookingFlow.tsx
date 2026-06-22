import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/Button';
import { PriceBreakdown } from '@/components/booking/PriceBreakdown';
import { useCreateBooking } from '@/hooks/useBookings';
import { useAuth } from '@/hooks/useAuth';
import { openCheckout } from '@/services/razorpay';
import type { TurfSportView } from '@/types';

export interface BookingFlowProps {
  turfName: string;
  turfSport: TurfSportView;
  selectedSlotIds: string[];
  hours: number;
}

const RAZORPAY_KEY = import.meta.env.VITE_RAZORPAY_KEY_ID ?? '';

export function BookingFlow({
  turfName,
  turfSport,
  selectedSlotIds,
  hours,
}: BookingFlowProps): JSX.Element {
  const { user } = useAuth();
  const navigate = useNavigate();
  const createBooking = useCreateBooking();
  const [error, setError] = useState<string | null>(null);

  const handleBook = async (): Promise<void> => {
    setError(null);
    try {
      const booking = await createBooking.mutateAsync({
        turf_sport_id: turfSport.id,
        slot_ids: selectedSlotIds,
      });
      await openCheckout({
        key: RAZORPAY_KEY,
        amount: booking.amount,
        currency: 'INR',
        name: turfName,
        description: `${turfSport.sport_name} • ${hours} hr`,
        order_id: booking.razorpay_order_id,
        prefill: { email: user?.email, contact: user?.phone },
        theme: { color: '#059669' },
        handler: () => navigate(`/bookings/${booking.booking_id}`),
        modal: { ondismiss: () => navigate(`/bookings/${booking.booking_id}`) },
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start booking');
    }
  };

  return (
    <div className="space-y-3">
      <PriceBreakdown
        pricePerHour={turfSport.price_per_hour}
        advanceDepositPercentage={turfSport.advance_deposit_percentage}
        hours={hours}
      />
      {error && <p className="text-sm text-red-500">{error}</p>}
      {user ? (
        <Button
          className="w-full"
          size="lg"
          disabled={selectedSlotIds.length === 0}
          loading={createBooking.isPending}
          onClick={() => void handleBook()}
        >
          {selectedSlotIds.length === 0 ? 'Select slots to book' : 'Proceed to pay'}
        </Button>
      ) : (
        <Link to="/login" className="block">
          <Button className="w-full" size="lg" variant="secondary">
            Sign in to book
          </Button>
        </Link>
      )}
    </div>
  );
}
