import { lazy, Suspense } from 'react'
import { Link } from 'react-router'
import { OverviewStats } from '../features/overview/OverviewStats'
import { LoadingState } from '../components/feedback/LoadingState'
import { ErrorState } from '../components/feedback/ErrorState'
import { EmptyState } from '../components/feedback/EmptyState'
import { ConnectionUnavailable } from '../components/feedback/ConnectionUnavailable'
import { useHealth } from '../hooks/useHealth'
import { useExperiments } from '../hooks/useExperiments'
import { useFireSafetySummary } from '../hooks/useFireSafety'
import { isApiError } from '../api/errors'

const CategoryBarChart = lazy(() =>
  import('../components/charts/CategoryBarChart').then((m) => ({ default: m.CategoryBarChart })),
)

export function OverviewPage() {
  const health = useHealth()
  const experiments = useExperiments()
  const summary = useFireSafetySummary()

  if (health.isPending || experiments.isPending || summary.isPending) {
    return <LoadingState message="Loading overview..." />
  }
  if (health.isError) {
    const e = health.error
    if (isApiError(e) && (e.kind === 'network' || e.kind === 'timeout')) {
      return <ConnectionUnavailable onRetry={() => health.refetch()} />
    }
    return <ErrorState message="Could not reach the backend." onRetry={() => health.refetch()} />
  }
  const failed = [experiments, summary].find((q) => q.isError)
  if (failed) {
    return <ErrorState message="Could not load overview data." onRetry={() => { experiments.refetch(); summary.refetch() }} />
  }
  const counts = {
    experiments: experiments.data?.total ?? 0,
    prevention: summary.data?.prevention_count ?? 0,
    detection: summary.data?.detection_count ?? 0,
    suppression: summary.data?.suppression_count ?? 0,
  }
  const hasRecords = counts.experiments > 0

  return (
    <div className="space-y-8 pb-12">
      {/* Top Status Bar */}
      <div className="flex items-center justify-between rounded-lg border border-cyan-500/20 bg-cyan-950/20 px-4 py-2">
        <p className="text-xs text-cyan-300/80 font-mono tracking-widest uppercase">
          System Status: <span className="text-cyan-400 font-bold">{health.data?.status ?? 'unknown'}</span> ({health.data?.service ?? ''})
        </p>
        <span className="flex h-2 w-2 rounded-full bg-cyan-400 shadow-[0_0_8px_#22d3ee]"></span>
      </div>

      {/* Main Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column (2/3 width) */}
        <div className="lg:col-span-2 space-y-6">
          <OverviewStats counts={counts} />

          {/* Central Interactive Viewer with Background Image */}
          <div className="relative overflow-hidden rounded-2xl border border-white/10 bg-[#0A1628] p-6 min-h-[350px] flex flex-col items-center justify-center group">
            
            {/* ছবির লিংক */}
            <div 
              className="absolute inset-0 opacity-30 group-hover:opacity-40 transition-opacity duration-700 bg-cover bg-center"
              style={{ backgroundImage: "url('https://www.nasa.gov/wp-content/uploads/2025/10/iss035e040444-0cf1d9.jpg')" }}
            ></div>
            
            {/* Overlay to make text readable */}
            <div className="absolute inset-0 bg-gradient-to-t from-[#0A1628] via-[#0A1628]/60 to-transparent"></div>

            {/* Background Glow Effect */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-cyan-500/10 rounded-full blur-3xl group-hover:bg-cyan-500/20 transition-all duration-700 pointer-events-none"></div>
            
            <div className="relative z-10 text-center space-y-4">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-cyan-950/80 backdrop-blur-sm border border-cyan-500/50 shadow-[0_0_20px_rgba(34,211,238,0.3)] mb-2">
                <svg className="w-8 h-8 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-white tracking-wide drop-shadow-lg">Combustion Research Visualization</h3>
              <p className="text-sm text-slate-300 max-w-md mx-auto drop-shadow-md">
                Explore the latest fire safety experiments and thermal dynamics. Interactive 3D viewer will be integrated here.
              </p>
              <Link to="/experiments" className="inline-block mt-4 px-6 py-2 rounded-full border border-cyan-500/50 bg-[#040B14]/50 backdrop-blur-sm text-cyan-300 text-sm font-medium hover:bg-cyan-500/20 transition-all shadow-[0_0_15px_rgba(34,211,238,0.2)]">
                Explore Experiments
              </Link>
            </div>
          </div>

          {/* Chart Section */}
          {hasRecords ? (
            <div className="rounded-2xl border border-white/10 bg-[#0A1628] p-6">
              <h2 className="text-sm font-semibold text-white mb-4 uppercase tracking-wider text-slate-300">Category Insights</h2>
              <Suspense fallback={<LoadingState message="Loading chart..." />}>
                <CategoryBarChart data={[{ name: 'Prevention', count: counts.prevention }, { name: 'Detection', count: counts.detection }, { name: 'Suppression', count: counts.suppression }]} title="Fire safety insights by category" />
              </Suspense>
            </div>
          ) : (
            <div className="rounded-2xl border border-white/10 bg-[#0A1628] p-6">
               <EmptyState title="No NASA research records loaded yet" message="The backend is connected, but no experiment records are loaded. Real NASA records will appear here when they are added." />
            </div>
          )}
        </div>

        {/* Right Column (1/3 width) */}
        <div className="space-y-6">
          <div className="rounded-2xl border border-white/10 bg-[#0A1628] p-6 h-full flex flex-col">
            <h2 className="text-sm font-semibold text-cyan-400 uppercase tracking-widest mb-6 border-b border-white/5 pb-4">Research Insights</h2>
            
            <div className="space-y-6 flex-1">
              {/* Evidence Standards Section */}
              <div>
                <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-3 flex items-center gap-2">
                  <svg className="w-4 h-4 text-cyan-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                  Evidence Standards
                </h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  All data presented in this explorer is derived from actual NASA combustion experiments. 
                </p>
                <ul className="mt-3 space-y-2">
                  <li className="flex items-start gap-2 text-xs text-slate-400">
                    <span className="w-1.5 h-1.5 rounded-full bg-cyan-500 mt-1 shrink-0"></span>
                    <span><strong className="text-slate-300">Verified:</strong> Data directly linked to source IDs.</span>
                  </li>
                  <li className="flex items-start gap-2 text-xs text-slate-400">
                    <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 mt-1 shrink-0"></span>
                    <span><strong className="text-slate-300">Derived:</strong> Interpretations based on documented data.</span>
                  </li>
                  <li className="flex items-start gap-2 text-xs text-slate-400">
                    <span className="w-1.5 h-1.5 rounded-full bg-orange-500 mt-1 shrink-0"></span>
                    <span><strong className="text-slate-300">Potential:</strong> Applications requiring further validation.</span>
                  </li>
                </ul>
              </div>

              {/* Quick Stats or Notes */}
              <div className="pt-4 border-t border-white/5">
                <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2 flex items-center gap-2">
                  <svg className="w-4 h-4 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                  Explorer Guide
                </h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Use the <strong className="text-cyan-300">Research Assistant</strong> in the sidebar to ask questions about specific combustion behaviors, or visit the <strong className="text-cyan-300">Compare</strong> page to analyze data side-by-side.
                </p>
              </div>
            </div>

            {/* Disclaimer Note */}
            <div className="pt-4 border-t border-white/10 mt-auto">
              <p className="text-[10px] text-slate-500 leading-relaxed text-justify">
                <strong className="text-slate-400">Note:</strong> Backend availability is not NASA data availability. Counts above come from the real API; zero means no records are loaded, not an error.
              </p>
            </div>
          </div>
        </div>

      </div>
    </div>
  )
}