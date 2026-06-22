import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from '@/contexts/AuthContext';
import { SocketProvider } from '@/contexts/SocketContext';
import { TopNav } from '@/components/layout/TopNav';
import { RequireRole } from '@/components/layout/RequireRole';
import { Home } from '@/pages/player/Home';
import { TurfDetail } from '@/pages/player/TurfDetail';
import { BookingConfirm } from '@/pages/player/BookingConfirm';
import { MyBookings } from '@/pages/player/MyBookings';
import { Login } from '@/pages/Login';
import { OwnerDashboard } from '@/pages/owner/Dashboard';
import { OwnerTurfs } from '@/pages/owner/Turfs';
import { TurfForm } from '@/pages/owner/TurfForm';
import { OwnerCalendar } from '@/pages/owner/Calendar';
import { OwnerBookings } from '@/pages/owner/Bookings';
import { OwnerAnalytics } from '@/pages/owner/Analytics';
import { AdminDashboard } from '@/pages/admin/Dashboard';
import { AdminUsers } from '@/pages/admin/Users';
import { AdminPayouts } from '@/pages/admin/Payouts';
import { AdminAnalyticsPage } from '@/pages/admin/Analytics';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 30_000, retry: 1, refetchOnWindowFocus: false },
  },
});

const OWNER_NAV = [
  { to: '/owner', label: 'Dashboard' },
  { to: '/owner/turfs', label: 'Turfs' },
  { to: '/owner/calendar', label: 'Calendar' },
  { to: '/owner/bookings', label: 'Bookings' },
  { to: '/owner/analytics', label: 'Analytics' },
];

const ADMIN_NAV = [
  { to: '/admin', label: 'Dashboard' },
  { to: '/admin/users', label: 'Users' },
  { to: '/admin/payouts', label: 'Payouts' },
  { to: '/admin/analytics', label: 'Analytics' },
];

function ownerRoute(element: JSX.Element): JSX.Element {
  return (
    <RequireRole role="turf_owner" sidebarTitle="Owner" items={OWNER_NAV}>
      {element}
    </RequireRole>
  );
}

function adminRoute(element: JSX.Element): JSX.Element {
  return (
    <RequireRole role="saas_admin" sidebarTitle="Admin" items={ADMIN_NAV}>
      {element}
    </RequireRole>
  );
}

export function App(): JSX.Element {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <SocketProvider>
          <BrowserRouter>
            <TopNav />
            <main>
              <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/login" element={<Login />} />
                <Route path="/turfs/:turfId" element={<TurfDetail />} />
                <Route path="/bookings" element={<MyBookings />} />
                <Route path="/bookings/:bookingId" element={<BookingConfirm />} />

                <Route path="/owner" element={ownerRoute(<OwnerDashboard />)} />
                <Route path="/owner/turfs" element={ownerRoute(<OwnerTurfs />)} />
                <Route path="/owner/turfs/new" element={ownerRoute(<TurfForm />)} />
                <Route path="/owner/calendar" element={ownerRoute(<OwnerCalendar />)} />
                <Route path="/owner/bookings" element={ownerRoute(<OwnerBookings />)} />
                <Route path="/owner/analytics" element={ownerRoute(<OwnerAnalytics />)} />

                <Route path="/admin" element={adminRoute(<AdminDashboard />)} />
                <Route path="/admin/users" element={adminRoute(<AdminUsers />)} />
                <Route path="/admin/payouts" element={adminRoute(<AdminPayouts />)} />
                <Route path="/admin/analytics" element={adminRoute(<AdminAnalyticsPage />)} />

                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </main>
          </BrowserRouter>
        </SocketProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
}
