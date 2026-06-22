import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseMutationResult,
  type UseQueryResult,
} from '@tanstack/react-query';
import { api, unwrap } from '@/services/api';
import type { ApiEnvelope, Booking, OwnerAnalytics, OwnerTurf, Payout, Slot } from '@/types';

export interface TurfFormInput {
  name: string;
  address: string;
  city: string;
  description?: string;
  amenities: string[];
  operating_hours: Record<string, { open: string; close: string }>;
}

export function useOwnerTurfs(): UseQueryResult<OwnerTurf[]> {
  return useQuery({
    queryKey: ['owner-turfs'],
    queryFn: async () => {
      const response = await api.get<ApiEnvelope<OwnerTurf[]>>('/owner/turfs');
      return unwrap(response.data);
    },
  });
}

export function useCreateTurf(): UseMutationResult<OwnerTurf, unknown, TurfFormInput> {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (input: TurfFormInput) => {
      const response = await api.post<ApiEnvelope<OwnerTurf>>('/owner/turfs', input);
      return unwrap(response.data);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['owner-turfs'] });
    },
  });
}

export function useOwnerAnalytics(from?: string, to?: string): UseQueryResult<OwnerAnalytics> {
  return useQuery({
    queryKey: ['owner-analytics', from, to],
    queryFn: async () => {
      const response = await api.get<ApiEnvelope<OwnerAnalytics>>('/owner/analytics', {
        params: { from, to },
      });
      return unwrap(response.data);
    },
  });
}

export function useOwnerBookings(turfId?: string, status?: string): UseQueryResult<Booking[]> {
  return useQuery({
    queryKey: ['owner-bookings', turfId, status],
    queryFn: async () => {
      const response = await api.get<ApiEnvelope<Booking[]>>('/owner/bookings', {
        params: { turf_id: turfId, status },
      });
      return unwrap(response.data);
    },
  });
}

export function useOwnerPayouts(): UseQueryResult<{ items: Payout[]; total: number }> {
  return useQuery({
    queryKey: ['owner-payouts'],
    queryFn: async () => {
      const response = await api.get<ApiEnvelope<{ items: Payout[]; total: number }>>('/owner/payouts');
      return unwrap(response.data);
    },
  });
}

export function useOwnerSlots(
  turfId: string | undefined,
  sportId: string | undefined,
  date: string,
): UseQueryResult<Slot[]> {
  return useQuery({
    queryKey: ['owner-slots', turfId, sportId, date],
    enabled: Boolean(turfId && sportId && date),
    queryFn: async () => {
      const response = await api.get<ApiEnvelope<Slot[]>>('/owner/slots', {
        params: { turf_id: turfId, sport_id: sportId, date },
      });
      return unwrap(response.data);
    },
  });
}

export function useBlockSlots(): UseMutationResult<
  { blocked: number },
  unknown,
  { turf_sport_id: string; slot_date: string; start_time: string; end_time: string; reason: string }
> {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (input) => {
      const response = await api.post<ApiEnvelope<{ blocked: number }>>('/owner/slots/block', input);
      return unwrap(response.data);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['owner-slots'] });
    },
  });
}

export function useGenerateSlots(): UseMutationResult<
  { created: number },
  unknown,
  { turf_sport_id: string; days: number }
> {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (input) => {
      const response = await api.post<ApiEnvelope<{ created: number }>>('/owner/slots/generate', input);
      return unwrap(response.data);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['owner-slots'] });
    },
  });
}
