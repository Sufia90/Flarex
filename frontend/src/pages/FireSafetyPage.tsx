import { lazy, Suspense, useState } from 'react'
import { useSearchParams } from 'react-router'
import { LoadingState } from '../components/feedback/LoadingState'
import { ErrorState } from '../components/feedback/ErrorState'
import { EmptyState } from '../components/feedback/EmptyState'
import { StatCard } from '../components/common/StatCard'
import { InsightCard } from '../features/fire-safety/InsightCard'
import { useFireSafetyInsights, useFireSafetySummary } from '../hooks/useFireSafety'
import type { FireSafetyCategory, FireSafetyEvidenceStatus } from '../types/fire-safety'

const CategoryBarChart = lazy(() =>
  import('../components/charts/CategoryBarChart').then((m) => ({ default: m.CategoryBarChart })),
)

type Tab = 'all' | FireSafetyCategory
const tabs: { value: Tab; label: string }[] = [
  { value: 'all', label: 'All Categories' },
  { value: 'prevention', label: 'Prevention' },
  { value: 'detection', label: 'Detection' },
  { value: 'suppression', label: 'Suppression' },
]

export function FireSafetyPage() {
  const [searchParams] = useSearchParams()
  const [tab, setTab] = useState<Tab>((searchParams.get('category') as Tab) ?? 'all')
  const [evidenceStatus, setEvidenceStatus] = useState<FireSafetyEvidenceStatus | ''>('')
  const experimentId = searchParams.get('experiment') ?? undefined
  const hardwareId = searchParams.get('hardware') ?? undefined
  const summary = useFireSafetySummary()
  const insights = useFireSafetyInsights({
    category: tab === 'all' ? undefined : tab,
    evidence_status: evidenceStatus === '' ? undefined : evidenceStatus,
    experiment_id: experimentId,
    hardware_id: hardwareId,
    page: 1,
    page_size: 20,
  })
  const items = insights.data?.items ?? []

  if (summary.isPending || insights.isPending) return <LoadingState message="Loading fire safety insights..." />
  if (summary.isError) return <ErrorState message="Could not load the fire safety summary." onRetry={() => summary.refetch()} />
  if (insights.isError) return <ErrorState message="Could not load fire safety insights." onRetry={() => insights.refetch()} />

  return (
    <div className="space-y-6 pb-12">
      
      {/* Header Section */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-2">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-wide">Fire Safety Insights</h1>
          <p className="text-sm text-slate-400 mt-1">Analyze prevention, detection, and suppression data from combustion experiments.</p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-red-500/10 border border-red-500/20">
           <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500"></span>
            </span>
          <span className="text-xs font-medium text-red-400 uppercase tracking-wider">Safety Module Active</span>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        {/* Note: Assuming StatCard is updated to the dark theme, if not it will inherit the default grid */}
        <StatCard label="Total insights" value={summary.data?.total_insights ?? 0} />
        <StatCard label="Documented" value={summary.data?.documented_count ?? 0} />
        <StatCard label="Potential" value={summary.data?.potential_count ?? 0} />
        <StatCard label="Experiments with evidence" value={summary.data?.experiments_with_evidence ?? 0} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column (Chart & Content) */}
        <div className="lg:col-span-2 space-y-6">
          {/* Chart Section */}
          <div className="rounded-2xl border border-white/10 bg-[#0A1628] p-6 shadow-lg shadow-black/20">
            <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4">Insights by Category</h2>
            <Suspense fallback={<LoadingState message="Loading chart..." />}>
              <CategoryBarChart
                data={[
                  { name: 'Prevention', count: summary.data?.prevention_count ?? 0 },
                  { name: 'Detection', count: summary.data?.detection_count ?? 0 },
                  { name: 'Suppression', count: summary.data?.suppression_count ?? 0 },
                ]}
                title="Insights by category"
              />
            </Suspense>
          </div>

          {/* Filters and Tabs Section */}
          <div className="rounded-2xl border border-white/10 bg-[#0A1628] p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            {/* Tabs */}
            <div className="flex flex-wrap items-center gap-2">
              {tabs.map((t) => (
                <button 
                  key={t.value} 
                  type="button" 
                  onClick={() => setTab(t.value)} 
                  className={`rounded-full px-4 py-1.5 text-sm transition-all duration-300 font-medium ${
                    tab === t.value 
                      ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/50 shadow-[0_0_10px_rgba(34,211,238,0.2)]' 
                      : 'bg-white/5 text-slate-400 border border-transparent hover:bg-white/10 hover:text-white'
                  }`}
                >
                  {t.label}
                </button>
              ))}
            </div>

            {/* Evidence Status Selector */}
            <div className="flex items-center gap-2">
              <label className="text-xs font-medium text-slate-400 uppercase tracking-wider whitespace-nowrap">
                Evidence
              </label>
              <select 
                className="rounded-lg border border-white/10 bg-[#040B14] px-3 py-1.5 text-sm text-white focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 transition-all appearance-none cursor-pointer" 
                value={evidenceStatus} 
                onChange={(e) => setEvidenceStatus(e.target.value as FireSafetyEvidenceStatus | '')}
              >
                <option value="">All Status</option>
                <option value="documented">Documented</option>
                <option value="potential">Potential</option>
                <option value="unsupported">Unsupported</option>
                <option value="unknown">Unknown</option>
                <option value="insufficient_evidence">Insufficient evidence</option>
              </select>
            </div>
          </div>

          {/* Active Filters Display */}
          {(experimentId || hardwareId) && (
            <div className="flex gap-2 text-xs">
              {experimentId && (
                <span className="px-3 py-1 rounded-full bg-cyan-950/50 border border-cyan-500/30 text-cyan-300">
                  Experiment: {experimentId}
                </span>
              )}
              {hardwareId && (
                <span className="px-3 py-1 rounded-full bg-cyan-950/50 border border-cyan-500/30 text-cyan-300">
                  Hardware: {hardwareId}
                </span>
              )}
            </div>
          )}

          {/* Insight Cards List */}
          {items.length === 0 ? (
            <div className="rounded-2xl border border-white/10 bg-[#0A1628] p-8">
              <EmptyState title="No fire safety insights yet" message="No insights match the current filters. Real NASA records will produce insights here when they are added." />
            </div>
          ) : (
            <div>
              <div className="flex items-center justify-between mb-3 px-1">
                <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">Results</p>
                <p className="text-xs text-slate-500">Found {insights.data?.total ?? 0} insight(s)</p>
              </div>
              <div className="space-y-4">
                {items.map((insight) => (
                  <InsightCard key={insight.insight_id ?? `${insight.experiment_id}-${insight.category}`} insight={insight} />
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right Column (Side Panel) */}
        <div className="space-y-6">
          <div className="rounded-2xl border border-white/10 bg-[#0A1628] p-6 h-full">
            <h3 className="text-sm font-semibold text-cyan-400 uppercase tracking-widest mb-4">Safety Protocol</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              This module categorizes combustion research into three critical fire safety phases. Ensure all data displayed is verified against official NASA sources.
            </p>
            
            <div className="mt-8 space-y-4">
               <div className="p-4 rounded-xl bg-green-500/5 border border-green-500/10">
                  <h4 className="text-green-400 font-medium text-sm mb-1">Prevention</h4>
                  <p className="text-xs text-slate-500">Materials & designs that resist ignition.</p>
               </div>
               <div className="p-4 rounded-xl bg-amber-500/5 border border-amber-500/10">
                  <h4 className="text-amber-400 font-medium text-sm mb-1">Detection</h4>
                  <p className="text-xs text-slate-500">Sensors and systems to identify fire early.</p>
               </div>
               <div className="p-4 rounded-xl bg-red-500/5 border border-red-500/10">
                  <h4 className="text-red-400 font-medium text-sm mb-1">Suppression</h4>
                  <p className="text-xs text-slate-500">Methods to extinguish or control combustion.</p>
               </div>
            </div>

            {summary.data?.explanation && (
              <div className="mt-8 pt-6 border-t border-white/10">
                <p className="text-[11px] text-slate-500 leading-relaxed">
                  <strong className="text-slate-400">Summary Note:</strong> {summary.data.explanation}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}