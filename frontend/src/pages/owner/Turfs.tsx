import { Link } from 'react-router-dom';
import { useOwnerTurfs } from '@/hooks/useOwnerTurfs';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Spinner } from '@/components/ui/Spinner';
import { formatCurrency } from '@/utils/formatters';

export function OwnerTurfs(): JSX.Element {
  const { data: turfs, isLoading } = useOwnerTurfs();

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">My turfs</h1>
        <Link to="/owner/turfs/new">
          <Button>Add turf</Button>
        </Link>
      </div>

      {isLoading && <Spinner label="Loading turfs..." />}
      {turfs && turfs.length === 0 && (
        <p className="text-gray-500">No turfs yet. Add your first turf to start accepting bookings.</p>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {turfs?.map((turf) => (
          <Card key={turf.id}>
            <div className="flex items-start justify-between">
              <h3 className="font-semibold text-gray-900">{turf.name}</h3>
              <Badge tone={turf.is_active ? 'green' : 'gray'}>
                {turf.is_active ? 'Active' : 'Inactive'}
              </Badge>
            </div>
            <p className="text-sm text-gray-500">
              {turf.address}, {turf.city}
            </p>
            <p className="mt-2 text-sm text-gray-600">
              {turf.sports.length} sport(s) • from {formatCurrency(turf.min_price_per_hour)}
            </p>
          </Card>
        ))}
      </div>
    </div>
  );
}
