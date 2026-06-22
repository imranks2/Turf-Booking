import { useState } from 'react';
import { useAdminPayouts, useRetryPayout } from '@/hooks/useAdmin';
import { Table } from '@/components/ui/Table';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Spinner } from '@/components/ui/Spinner';
import { formatCurrency } from '@/utils/formatters';
import type { Payout } from '@/types';

const STATUS_TONE: Record<string, 'green' | 'amber' | 'red' | 'gray'> = {
  processed: 'green',
  pending: 'amber',
  failed: 'red',
};

export function AdminPayouts(): JSX.Element {
  const [status, setStatus] = useState('');
  const { data, isLoading } = useAdminPayouts(status || undefined);
  const retry = useRetryPayout();

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Payouts</h1>
        <select
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm"
          value={status}
          onChange={(e) => setStatus(e.target.value)}
        >
          <option value="">All</option>
          <option value="pending">Pending</option>
          <option value="processed">Processed</option>
          <option value="failed">Failed</option>
        </select>
      </div>

      {isLoading || !data ? (
        <Spinner label="Loading payouts..." />
      ) : (
        <Table<Payout>
          columns={[
            { header: 'Booking', cell: (p) => p.booking_id.slice(0, 8) },
            { header: 'Amount', cell: (p) => formatCurrency(p.amount) },
            {
              header: 'Status',
              cell: (p) => <Badge tone={STATUS_TONE[p.status] ?? 'gray'}>{p.status}</Badge>,
            },
            { header: 'Transfer', cell: (p) => p.razorpay_transfer_id ?? '—' },
            {
              header: 'Actions',
              cell: (p) =>
                p.status === 'failed' || p.status === 'pending' ? (
                  <Button size="sm" variant="secondary" loading={retry.isPending} onClick={() => retry.mutate(p.id)}>
                    Retry
                  </Button>
                ) : null,
            },
          ]}
          rows={data.items}
          rowKey={(p) => p.id}
          empty="No payouts"
        />
      )}
    </div>
  );
}
