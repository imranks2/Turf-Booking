import { Link } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { Button } from '@/components/ui/Button';

export function TopNav(): JSX.Element {
  const { user, logout } = useAuth();

  return (
    <header className="sticky top-0 z-20 border-b border-gray-200/70 bg-white/80 backdrop-blur-md">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3 sm:px-6 lg:px-8">
        <Link to="/" className="flex items-center gap-2 text-xl font-bold text-gray-900">
          <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-brand-gradient text-white shadow-soft">
            ⚽
          </span>
          Turf<span className="-ml-1 text-brand-600">App</span>
        </Link>
        <nav className="flex items-center gap-2 text-sm sm:gap-4">
          {user ? (
            <>
              {user.role === 'turf_owner' && (
                <Link to="/owner" className="font-medium text-gray-600 hover:text-brand-600">
                  Owner
                </Link>
              )}
              {user.role === 'saas_admin' && (
                <Link to="/admin" className="font-medium text-gray-600 hover:text-brand-600">
                  Admin
                </Link>
              )}
              {user.role === 'player' && (
                <Link to="/bookings" className="font-medium text-gray-600 hover:text-brand-600">
                  My bookings
                </Link>
              )}
              <span className="hidden text-gray-500 sm:inline">{user.email}</span>
              <Button variant="ghost" size="sm" onClick={() => void logout()}>
                Logout
              </Button>
            </>
          ) : (
            <Link to="/login">
              <Button size="sm">Sign in</Button>
            </Link>
          )}
        </nav>
      </div>
    </header>
  );
}
