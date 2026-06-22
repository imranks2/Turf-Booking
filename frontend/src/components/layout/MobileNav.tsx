import { NavLink } from 'react-router-dom';
import type { SidebarItem } from '@/components/layout/Sidebar';

export interface MobileNavProps {
  items: SidebarItem[];
}

export function MobileNav({ items }: MobileNavProps): JSX.Element {
  return (
    <nav className="flex gap-2 overflow-x-auto border-b border-gray-200 bg-white px-3 py-2 md:hidden">
      {items.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          end
          className={({ isActive }) =>
            `whitespace-nowrap rounded-full px-3 py-1.5 text-sm font-medium transition ${
              isActive ? 'bg-brand-50 text-brand-700' : 'text-gray-600 hover:bg-gray-100'
            }`
          }
        >
          {item.label}
        </NavLink>
      ))}
    </nav>
  );
}
