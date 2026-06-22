import { useOwnerAnalytics } from '@/hooks/useOwnerTurfs';
import { KpiCard } from '@/components/analytics/KpiCard';
import { RevenueChart } from '@/components/analytics/RevenueChart';
import { Table } from '@/components/ui/Table';
import { Card } from '@/components/ui/Card';
import { Spinner } from '@/components/ui/Spinner';
import { formatCurrency } from '@/utils/formatters';
import type { SportBreakdown } from '@/types';

export function OwnerAnalytics(): JSX.Element {
  const { data, isLoading } = useOwnerAnalytics();

  if (isLoading || !data) {
    return <Spinner label="Loading analytics..." />;
  }

  return (
    <div className="space-y-6 p-6">
      <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard label="Bookings" value={String(data.total_bookings)} />
        <KpiCard label="Revenue" value={formatCurrency(data.total_revenue)} />
        <KpiCard label="Platform fees" value={formatCurrency(data.total_platform_fees)} />
        <KpiCard label="Your payouts" value={formatCurrency(data.total_owner_payouts)} />
      </div>

      <RevenueChart
        title="Revenue over time"
        data={data.time_series}
        xKey="date"
        series={[{ key: 'revenue', color: '#059669', label: 'Revenue' }]}
      />

      <Card>
        <h3 className="mb-4 font-semibold text-gray-900">By sport</h3>
        <Table<SportBreakdown>
          columns={[
            { header: 'Sport', cell: (r) => r.sport },
            { header: 'Bookings', cell: (r) => r.bookings },
            { header: 'Revenue', cell: (r) => formatCurrency(r.revenue) },
          ]}
          rows={data.by_sport}
          rowKey={(r) => r.sport}
          empty="No bookings yet"
        />
      </Card>
    </div>
  );
}
