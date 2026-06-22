import { Link } from 'react-router-dom';
import { useMyBookings } from '@/hooks/useBookings';
import { BookingCard } from '@/components/booking/BookingCard';
import { Spinner } from '@/components/ui/Spinner';
import { Button } from '@/components/ui/Button';

export function MyBookings(): JSX.Element {
  const { data: bookings, isLoading, isError } = useMyBookings();

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <h1 className="mb-6 text-2xl font-bold text-gray-900">My bookings</h1>
      {isLoading && <Spinner label="Loading bookings..." />}
      {isError && <p className="text-sm text-red-500">Failed to load bookings.</p>}
      {bookings && bookings.length === 0 && (
        <div className="rounded-xl border border-dashed border-gray-300 p-10 text-center">
          <p className="mb-4 text-gray-500">You have no bookings yet.</p>
          <Link to="/">
            <Button>Find a turf</Button>
          </Link>
        </div>
      )}
      <div className="space-y-3">
        {bookings?.map((booking) => (
          <BookingCard key={booking.id} booking={booking} />
        ))}
      </div>
    </div>
  );
}
