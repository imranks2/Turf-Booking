import { Link } from 'react-router-dom';
import { useOwnerAnalytics, useOwnerTurfs } from '@/hooks/useOwnerTurfs';
import { KpiCard } from '@/components/analytics/KpiCard';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Spinner } from '@/components/ui/Spinner';
import { formatCurrency } from '@/utils/formatters';

export function OwnerDashboard(): JSX.Element {
  const { data: analytics, isLoading } = useOwnerAnalytics();
  const { data: turfs } = useOwnerTurfs();

  if (isLoading || !analytics) {
    return <Spinner label="Loading dashboard..." />;
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <Link to="/owner/turfs/new">
          <Button>Add turf</Button>
        </Link>
      </div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard label="Active turfs" value={String(turfs?.filter((t) => t.is_active).length ?? 0)} />
        <KpiCard label="Bookings" value={String(analytics.total_bookings)} />
        <KpiCard label="Revenue" value={formatCurrency(analytics.total_revenue)} />
        <KpiCard label="Payouts" value={formatCurrency(analytics.total_owner_payouts)} />
      </div>
      <Card>
        <h3 className="mb-2 font-semibold text-gray-900">Quick links</h3>
        <div className="flex flex-wrap gap-3">
          <Link to="/owner/calendar">
            <Button variant="secondary">Manage calendar</Button>
          </Link>
          <Link to="/owner/bookings">
            <Button variant="secondary">View bookings</Button>
          </Link>
          <Link to="/owner/analytics">
            <Button variant="secondary">Full analytics</Button>
          </Link>
        </div>
      </Card>
    </div>
  );
}
