import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseMutationResult,
  type UseQueryResult,
} from '@tanstack/react-query';
import { api, unwrap } from '@/services/api';
import type { ApiEnvelope, Booking, BookingCreateResponse } from '@/types';

export interface CreateBookingInput {
  turf_sport_id: string;
  slot_ids: string[];
}

export interface CancelResult {
  booking_id: string;
  status: string;
  refund_amount: number;
  refund_percentage: number;
  refund_status: string;
}

export function useCreateBooking(): UseMutationResult<
  BookingCreateResponse,
  unknown,
  CreateBookingInput
> {
  return useMutation({
    mutationFn: async (input: CreateBookingInput) => {
      const response = await api.post<ApiEnvelope<BookingCreateResponse>>('/bookings', input);
      return unwrap(response.data);
    },
  });
}

export function useMyBookings(): UseQueryResult<Booking[]> {
  return useQuery({
    queryKey: ['my-bookings'],
    queryFn: async () => {
      const response = await api.get<ApiEnvelope<Booking[]>>('/bookings');
      return unwrap(response.data);
    },
  });
}

export function useBooking(bookingId: string | undefined, pollUntilConfirmed = false): UseQueryResult<Booking> {
  return useQuery({
    queryKey: ['booking', bookingId],
    enabled: Boolean(bookingId),
    refetchInterval: (query) => {
      if (!pollUntilConfirmed) {
        return false;
      }
      const status = query.state.data?.status;
      return status === 'confirmed' || status === 'cancelled' ? false : 2000;
    },
    queryFn: async () => {
      const response = await api.get<ApiEnvelope<Booking>>(`/bookings/${bookingId}`);
      return unwrap(response.data);
    },
  });
}

export function useCancelBooking(): UseMutationResult<
  CancelResult,
  unknown,
  { bookingId: string; reason?: string }
> {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ bookingId, reason }) => {
      const response = await api.post<ApiEnvelope<CancelResult>>(`/bookings/${bookingId}/cancel`, {
        reason,
      });
      return unwrap(response.data);
    },
    onSuccess: (_data, variables) => {
      void queryClient.invalidateQueries({ queryKey: ['my-bookings'] });
      void queryClient.invalidateQueries({ queryKey: ['booking', variables.bookingId] });
    },
  });
}
