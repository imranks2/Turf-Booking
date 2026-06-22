import { Navigate } from 'react-router-dom';
import type { ReactNode } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { Spinner } from '@/components/ui/Spinner';
import { Sidebar, type SidebarItem } from '@/components/layout/Sidebar';
import { MobileNav } from '@/components/layout/MobileNav';
import type { Role } from '@/types';

export interface RequireRoleProps {
  role: Role;
  sidebarTitle: string;
  items: SidebarItem[];
  children: ReactNode;
}

export function RequireRole({ role, sidebarTitle, items, children }: RequireRoleProps): JSX.Element {
  const { user, loading } = useAuth();

  if (loading) {
    return <Spinner label="Loading..." />;
  }
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  if (user.role !== role) {
    return <Navigate to="/" replace />;
  }

  return (
    <div className="min-h-[calc(100vh-57px)]">
      <MobileNav items={items} />
      <div className="flex">
        <Sidebar title={sidebarTitle} items={items} />
        <div className="flex-1 bg-gray-50">{children}</div>
      </div>
    </div>
  );
}
