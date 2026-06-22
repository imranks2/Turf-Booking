import { useQuery, type UseQueryResult } from '@tanstack/react-query';
import { api, unwrap } from '@/services/api';
import type {
  ApiEnvelope,
  DiscoveryFilters,
  DiscoveryResult,
  Slot,
  SportSummary,
  TurfDetail,
} from '@/types';

function buildParams(filters: DiscoveryFilters): Record<string, string | number> {
  const params: Record<string, string | number> = {};
  if (filters.city) params.city = filters.city;
  if (filters.sport) params.sport = filters.sport;
  if (filters.price_min !== undefined) params.price_min = filters.price_min;
  if (filters.price_max !== undefined) params.price_max = filters.price_max;
  if (filters.date) params.date = filters.date;
  params.page = filters.page ?? 1;
  params.limit = filters.limit ?? 20;
  return params;
}

export function useDiscoverTurfs(filters: DiscoveryFilters): UseQueryResult<DiscoveryResult> {
  return useQuery({
    queryKey: ['turfs', filters],
    queryFn: async () => {
      const response = await api.get<ApiEnvelope<DiscoveryResult>>('/turfs', {
        params: buildParams(filters),
      });
      return unwrap(response.data);
    },
  });
}

export function useTurfDetail(turfId: string | undefined): UseQueryResult<TurfDetail> {
  return useQuery({
    queryKey: ['turf', turfId],
    enabled: Boolean(turfId),
    queryFn: async () => {
      const response = await api.get<ApiEnvelope<TurfDetail>>(`/turfs/${turfId}`);
      return unwrap(response.data);
    },
  });
}

export function useTurfSlots(
  turfId: string | undefined,
  sportId: string | undefined,
  date: string,
): UseQueryResult<Slot[]> {
  return useQuery({
    queryKey: ['turf-slots', turfId, sportId, date],
    enabled: Boolean(turfId && sportId && date),
    queryFn: async () => {
      const response = await api.get<ApiEnvelope<Slot[]>>(`/turfs/${turfId}/slots`, {
        params: { sport_id: sportId, date },
      });
      return unwrap(response.data);
    },
  });
}

export function useSports(): UseQueryResult<SportSummary[]> {
  return useQuery({
    queryKey: ['sports'],
    queryFn: async () => {
      const response = await api.get<ApiEnvelope<SportSummary[]>>('/sports');
      return unwrap(response.data);
    },
  });
}

export function useCities(): UseQueryResult<string[]> {
  return useQuery({
    queryKey: ['cities'],
    queryFn: async () => {
      const response = await api.get<ApiEnvelope<string[]>>('/cities');
      return unwrap(response.data);
    },
  });
}
