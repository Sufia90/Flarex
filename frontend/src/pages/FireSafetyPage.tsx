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
  { value: 'all', label: 'All categories' },
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
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <StatCard label="Total insights" value={summary.data?.total_insights ?? 0} />
        <StatCard label="Documented" value={summary.data?.documented_count ?? 0} />
        <StatCard label="Potential" value={summary.data?.potential_count ?? 0} />
        <StatCard label="Experiments with evidence" value={summary.data?.experiments_with_evidence ?? 0} />
      </div>
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
      <div className="flex flex-wrap items-center gap-2">
        {tabs.map((t) => (
          <button key={t.value} type="button" onClick={() => setTab(t.value)} className={`rounded border px-3 py-1 text-sm ${tab === t.value ? 'border-cyan-600 bg-cyan-950 text-cyan-300' : 'border-slate-600 text-slate-300'}`}>
            {t.label}
          </button>
        ))}
        <label className="ml-2 text-xs text-slate-400">
          Evidence status
          <select className="ml-1 rounded border border-slate-600 bg-slate-800 px-2 py-1 text-sm text-white" value={evidenceStatus} onChange={(e) => setEvidenceStatus(e.target.value as FireSafetyEvidenceStatus | '')}>
            <option value="">All</option>
            <option value="documented">Documented</option>
            <option value="potential">Potential</option>
            <option value="unsupported">Unsupported</option>
            <option value="unknown">Unknown</option>
            <option value="insufficient_evidence">Insufficient evidence</option>
          </select>
        </label>
      </div>
      {experimentId ? <p className="text-xs text-slate-400">Filtered by experiment: {experimentId}</p> : null}
      {hardwareId ? <p className="text-xs text-slate-400">Filtered by hardware: {hardwareId}</p> : null}
      {items.length === 0 ? (
        <EmptyState title="No fire safety insights yet" message="No insights match the current filters. Real NASA records will produce insights here when they are added." />
      ) : (
        <div>
          <p className="text-xs text-slate-400">Found {insights.data?.total ?? 0} insight(s).</p>
          <div className="mt-2 space-y-3">
            {items.map((insight) => (
              <InsightCard key={insight.insight_id ?? `${insight.experiment_id}-${insight.category}`} insight={insight} />
            ))}
          </div>
        </div>
      )}
      {summary.data?.explanation ? <p className="text-xs text-slate-400">{summary.data.explanation}</p> : null}
    </div>
  )
}
