import { NavLink, Outlet } from 'react-router'

const navItems = [
  { to: '/', label: 'Overview', icon: 'M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z' },
  { to: '/experiments', label: 'Experiment Explorer', icon: 'M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z' },
  { to: '/compare', label: 'Compare & Rank', icon: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z' },
  { to: '/fire-safety', label: 'Fire Safety Insights', icon: 'M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z' },
  { to: '/mission-relevance', label: 'Mission Relevance', icon: 'M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z' },
  { to: '/research-assistant', label: 'Research Assistant', icon: 'M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z' },
]

export function AppLayout() {
  return (
    <div className="flex min-h-screen bg-[#040B14] text-white font-sans selection:bg-cyan-500/30">
      
      {/* Sidebar Navigation */}
      <aside className="w-64 flex-shrink-0 border-r border-white/5 bg-[#07111F] flex flex-col hidden md:flex sticky top-0 h-screen">
        {/* Logo Area */}
        <div className="h-20 flex items-center px-6 border-b border-white/5 bg-gradient-to-r from-cyan-950/30 to-transparent">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded bg-cyan-500/20 border border-cyan-500/50 flex items-center justify-center shadow-[0_0_10px_rgba(34,211,238,0.2)]">
               <span className="text-cyan-400 font-bold text-lg">F</span>
            </div>
            <div>
              <h1 className="text-sm font-bold text-white tracking-wide leading-tight">FLAREX</h1>
              <p className="text-[10px] text-cyan-400/70 uppercase tracking-widest font-mono">Combustion Explorer</p>
            </div>
          </div>
        </div>

        {/* Nav Links */}
        <nav className="flex-1 overflow-y-auto py-6 px-3 space-y-1">
          <p className="px-3 text-[10px] font-semibold text-slate-500 uppercase tracking-widest mb-2 mt-2">Research Modules</p>
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-200 group relative overflow-hidden ${
                  isActive 
                    ? 'bg-cyan-500/10 text-cyan-300 font-medium' 
                    : 'text-slate-400 hover:bg-white/5 hover:text-white'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  {/* Active Indicator Line */}
                  {isActive && (
                    <span className="absolute left-0 top-0 bottom-0 w-1 bg-cyan-400 shadow-[0_0_10px_#22d3ee] rounded-r-md"></span>
                  )}
                  <svg className={`w-5 h-5 ${isActive ? 'text-cyan-400' : 'text-slate-500 group-hover:text-slate-300'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d={item.icon} />
                  </svg>
                  <span>{item.label}</span>
                </>
              )}
            </NavLink>
          ))}
        </nav>

        {/* Bottom Status */}
        <div className="p-4 border-t border-white/5 bg-[#050D17]">
          <div className="flex items-center gap-3 px-3 py-2 rounded-lg bg-white/5 border border-white/5">
            <span className="relative flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-green-500"></span>
            </span>
            <div className="text-xs">
              <p className="text-slate-300 font-medium">System Online</p>
              <p className="text-slate-500 text-[10px]">API Connected</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Header */}
        <header className="h-16 md:h-20 border-b border-white/5 bg-[#040B14]/80 backdrop-blur-md sticky top-0 z-10 px-4 md:px-8 flex items-center justify-between">
          <div>
            <h2 className="text-base md:text-lg font-semibold text-white tracking-wide">NASA Combustion Research Explorer</h2>
            <p className="text-xs text-slate-500 hidden sm:block mt-0.5">Explore · Compare · Understand · Apply</p>
          </div>
          
          {/* Top Right Actions */}
          <div className="flex items-center gap-4">
             <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/10 text-xs text-slate-300">
               <svg className="w-4 h-4 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
               <span>Search...</span>
             </div>
             {/* সার্কেলটি এখান থেকে ডিলিট করা হয়েছে */}
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 p-4 md:p-8 overflow-x-hidden">
          <div className="max-w-7xl mx-auto">
            <Outlet />
          </div>
        </main>
      </div>
      
    </div>
  )
}