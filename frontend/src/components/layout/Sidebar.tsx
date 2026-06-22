import { NavLink } from 'react-router-dom';

export interface SidebarItem {
  to: string;
  label: string;
}

export interface SidebarProps {
  title: string;
  items: SidebarItem[];
}

export function Sidebar({ title, items }: SidebarProps): JSX.Element {
  return (
    <aside className="hidden w-56 shrink-0 border-r border-gray-200 bg-white md:block">
      <div className="px-4 py-4 text-sm font-semibold uppercase tracking-wide text-gray-400">
        {title}
      </div>
      <nav className="flex flex-col gap-1 px-2">
        {items.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end
            className={({ isActive }) =>
              `rounded-lg px-3 py-2 text-sm font-medium transition ${
                isActive ? 'bg-brand-50 text-brand-700' : 'text-gray-600 hover:bg-gray-100'
              }`
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
