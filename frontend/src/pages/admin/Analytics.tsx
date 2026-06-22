import { useAdminAnalytics } from '@/hooks/useAdmin';
import { KpiCard } from '@/components/analytics/KpiCard';
import { RevenueChart } from '@/components/analytics/RevenueChart';
import { Spinner } from '@/components/ui/Spinner';
import { formatCurrency } from '@/utils/formatters';

export function AdminAnalyticsPage(): JSX.Element {
  const { data, isLoading } = useAdminAnalytics();

  if (isLoading || !data) {
    return <Spinner label="Loading analytics..." />;
  }

  return (
    <div className="space-y-6 p-6">
      <h1 className="text-2xl font-bold text-gray-900">Platform analytics</h1>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <KpiCard label="Total bookings" value={String(data.total_bookings)} />
        <KpiCard label="Gross revenue" value={formatCurrency(data.total_revenue)} />
        <KpiCard label="Platform fees" value={formatCurrency(data.total_platform_fees)} />
        <KpiCard label="Owner payouts" value={formatCurrency(data.total_owner_payouts)} />
        <KpiCard label="Active owners" value={String(data.active_owners)} />
        <KpiCard label="Active players" value={String(data.active_players)} />
      </div>
      <RevenueChart
        title="Platform fees over time"
        data={data.time_series}
        xKey="date"
        series={[{ key: 'platform_fees', color: '#2563eb', label: 'Platform fees' }]}
      />
    </div>
  );
}
