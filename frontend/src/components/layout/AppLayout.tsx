import { NavLink, Outlet } from 'react-router'

const navItems = [
  { to: '/', label: 'Overview' },
  { to: '/experiments', label: 'Experiment Explorer' },
  { to: '/hardware', label: 'Hardware Explorer' },
  { to: '/compare', label: 'Compare & Rank' },
  { to: '/fire-safety', label: 'Fire Safety Insights' },
  { to: '/mission-relevance', label: 'Mission Relevance' },
  { to: '/research-assistant', label: 'Research Assistant' },
]

export function AppLayout() {
  return (
    <div className="min-h-screen bg-[#07111F] text-white">
      <header className="border-b border-white/10 px-6 py-4">
        <h1 className="text-lg font-bold text-[#28D7F2]">NASA Combustion Research Explorer</h1>
        <p className="text-sm text-white/70">Explore · Compare · Understand · Apply</p>
      </header>
      <nav className="flex flex-wrap gap-1 border-b border-white/10 px-6 py-2" aria-label="Sections">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) =>
              `rounded-md px-3 py-2 text-sm ${isActive ? 'bg-[#28D7F2] font-semibold text-[#07111F]' : 'text-white/80 hover:bg-white/10'}`
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
      <main className="mx-auto max-w-6xl px-6 py-6">
        <Outlet />
      </main>
    </div>
  )
}
