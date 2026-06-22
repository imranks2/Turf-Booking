import { useState } from 'react';
import { useAdminUsers, useSetUserStatus } from '@/hooks/useAdmin';
import { Table } from '@/components/ui/Table';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Spinner } from '@/components/ui/Spinner';
import type { AdminUser } from '@/types';

export function AdminUsers(): JSX.Element {
  const [q, setQ] = useState('');
  const [role, setRole] = useState('');
  const { data, isLoading } = useAdminUsers({ q: q || undefined, role: role || undefined });
  const setStatus = useSetUserStatus();

  return (
    <div className="space-y-6 p-6">
      <h1 className="text-2xl font-bold text-gray-900">Users</h1>

      <div className="flex flex-wrap items-end gap-3">
        <Input id="q" label="Search" placeholder="email or phone" value={q} onChange={(e) => setQ(e.target.value)} />
        <div className="flex flex-col gap-1">
          <label className="text-sm font-medium text-gray-700" htmlFor="role">
            Role
          </label>
          <select
            id="role"
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm"
            value={role}
            onChange={(e) => setRole(e.target.value)}
          >
            <option value="">All</option>
            <option value="turf_owner">Turf owners</option>
            <option value="player">Players</option>
            <option value="saas_admin">Admins</option>
          </select>
        </div>
      </div>

      {isLoading || !data ? (
        <Spinner label="Loading users..." />
      ) : (
        <Table<AdminUser>
          columns={[
            { header: 'Name', cell: (u) => u.name ?? '—' },
            { header: 'Email', cell: (u) => u.email },
            { header: 'Phone', cell: (u) => u.phone },
            { header: 'Role', cell: (u) => <Badge tone="gray">{u.role}</Badge> },
            {
              header: 'Status',
              cell: (u) => (
                <Badge tone={u.is_active ? 'green' : 'red'}>{u.is_active ? 'Active' : 'Inactive'}</Badge>
              ),
            },
            {
              header: 'Actions',
              cell: (u) =>
                u.is_active ? (
                  <Button
                    size="sm"
                    variant="danger"
                    loading={setStatus.isPending}
                    onClick={() => setStatus.mutate({ userId: u.id, action: 'suspend' })}
                  >
                    Suspend
                  </Button>
                ) : (
                  <Button
                    size="sm"
                    loading={setStatus.isPending}
                    onClick={() => setStatus.mutate({ userId: u.id, action: 'approve' })}
                  >
                    Approve
                  </Button>
                ),
            },
          ]}
          rows={data.items}
          rowKey={(u) => u.id}
          empty="No users found"
        />
      )}
    </div>
  );
}
