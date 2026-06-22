import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseMutationResult,
  type UseQueryResult,
} from '@tanstack/react-query';
import { api, unwrap } from '@/services/api';
import type { AdminAnalytics, AdminUser, ApiEnvelope, Paginated, Payout } from '@/types';

export interface UserFilters {
  q?: string;
  role?: string;
  status?: string;
  page?: number;
}

export function useAdminUsers(filters: UserFilters): UseQueryResult<Paginated<AdminUser>> {
  return useQuery({
    queryKey: ['admin-users', filters],
    queryFn: async () => {
      const response = await api.get<ApiEnvelope<Paginated<AdminUser>>>('/admin/users', {
        params: { q: filters.q, role: filters.role, status: filters.status, page: filters.page ?? 1 },
      });
      return unwrap(response.data);
    },
  });
}

export function useSetUserStatus(): UseMutationResult<
  { id: string; is_active: boolean },
  unknown,
  { userId: string; action: 'approve' | 'suspend' }
> {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ userId, action }) => {
      const response = await api.patch<ApiEnvelope<{ id: string; is_active: boolean }>>(
        `/admin/users/${userId}/${action}`,
      );
      return unwrap(response.data);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['admin-users'] });
    },
  });
}

export function useAdminAnalytics(from?: string, to?: string): UseQueryResult<AdminAnalytics> {
  return useQuery({
    queryKey: ['admin-analytics', from, to],
    queryFn: async () => {
      const response = await api.get<ApiEnvelope<AdminAnalytics>>('/admin/analytics', {
        params: { from, to },
      });
      return unwrap(response.data);
    },
  });
}

export function useAdminPayouts(status?: string): UseQueryResult<Paginated<Payout>> {
  return useQuery({
    queryKey: ['admin-payouts', status],
    queryFn: async () => {
      const response = await api.get<ApiEnvelope<Paginated<Payout>>>('/admin/payouts', {
        params: { status },
      });
      return unwrap(response.data);
    },
  });
}

export function useRetryPayout(): UseMutationResult<{ id: string; status: string }, unknown, string> {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payoutId: string) => {
      const response = await api.post<ApiEnvelope<{ id: string; status: string }>>(
        `/admin/payouts/${payoutId}/retry`,
      );
      return unwrap(response.data);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['admin-payouts'] });
    },
  });
}
