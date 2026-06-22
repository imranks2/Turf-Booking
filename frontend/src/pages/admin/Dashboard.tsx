import { Link } from 'react-router-dom';
import { useAdminAnalytics } from '@/hooks/useAdmin';
import { KpiCard } from '@/components/analytics/KpiCard';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Spinner } from '@/components/ui/Spinner';
import { formatCurrency } from '@/utils/formatters';

export function AdminDashboard(): JSX.Element {
  const { data, isLoading } = useAdminAnalytics();

  if (isLoading || !data) {
    return <Spinner label="Loading dashboard..." />;
  }

  return (
    <div className="space-y-6 p-6">
      <h1 className="text-2xl font-bold text-gray-900">Admin dashboard</h1>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard label="Active owners" value={String(data.active_owners)} />
        <KpiCard label="Active players" value={String(data.active_players)} />
        <KpiCard label="Bookings" value={String(data.total_bookings)} />
        <KpiCard label="Platform fees" value={formatCurrency(data.total_platform_fees)} />
      </div>
      <Card>
        <h3 className="mb-2 font-semibold text-gray-900">Manage</h3>
        <div className="flex flex-wrap gap-3">
          <Link to="/admin/users">
            <Button variant="secondary">Users</Button>
          </Link>
          <Link to="/admin/payouts">
            <Button variant="secondary">Payouts</Button>
          </Link>
          <Link to="/admin/analytics">
            <Button variant="secondary">Analytics</Button>
          </Link>
        </div>
      </Card>
    </div>
  );
}
