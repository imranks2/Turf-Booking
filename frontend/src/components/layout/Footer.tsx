import { Link } from 'react-router-dom';

export function Footer(): JSX.Element {
  return (
    <footer className="mt-16 border-t border-gray-200 bg-brand-950 text-white">
      <div className="mx-auto grid max-w-6xl grid-cols-2 gap-8 px-4 py-12 sm:px-6 md:grid-cols-4 lg:px-8">
        <div className="col-span-2 md:col-span-1">
          <span className="text-xl font-bold text-white">
            Turf<span className="text-lime-400">App</span>
          </span>
          <p className="mt-3 text-sm text-white/70">
            Book sports venues across cities. Transparent pricing, instant confirmation, no hidden
            charges.
          </p>
        </div>
        <FooterCol
          title="Play"
          links={[
            { label: 'Find turfs', to: '/' },
            { label: 'My bookings', to: '/bookings' },
            { label: 'Sign in', to: '/login' },
          ]}
        />
        <FooterCol
          title="For owners"
          links={[
            { label: 'List your turf', to: '/login' },
            { label: 'Owner dashboard', to: '/owner' },
          ]}
        />
        <FooterCol
          title="Company"
          links={[
            { label: 'About', to: '/' },
            { label: 'Contact', to: '/' },
            { label: 'Help', to: '/' },
          ]}
        />
      </div>
      <div className="border-t border-white/10">
        <div className="mx-auto max-w-6xl px-4 py-4 text-center text-xs text-white/60 sm:px-6 lg:px-8">
          © {new Date().getFullYear()} TurfApp. All rights reserved.
        </div>
      </div>
    </footer>
  );
}

function FooterCol({
  title,
  links,
}: {
  title: string;
  links: Array<{ label: string; to: string }>;
}): JSX.Element {
  return (
    <div>
      <h4 className="text-sm font-semibold text-white">{title}</h4>
      <ul className="mt-3 space-y-2 text-sm text-white/70">
        {links.map((link) => (
          <li key={link.label}>
            <Link to={link.to} className="transition hover:text-lime-400">
              {link.label}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
