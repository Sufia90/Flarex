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
    <div className="space-y-6">
      <p className="text-sm text-slate-300">Backend status: {health.data?.status ?? 'unknown'} ({health.data?.service ?? ''})</p>
      <OverviewStats counts={counts} />
      {hasRecords ? (
        <Suspense fallback={<LoadingState message="Loading chart..." />}>
          <CategoryBarChart data={[{ name: 'Prevention', count: counts.prevention }, { name: 'Detection', count: counts.detection }, { name: 'Suppression', count: counts.suppression }]} title="Fire safety insights by category" />
        </Suspense>
      ) : (
        <EmptyState title="No NASA research records loaded yet" message="The backend is connected, but no experiment records are loaded. Real NASA records will appear here when they are added." />
      )}
      <div>
        <h2 className="text-base font-semibold text-white">Sections</h2>
        <ul className="mt-2 space-y-1 text-sm">
          <li><Link className="text-cyan-300 underline" to="/experiments">Experiment Explorer</Link></li>
          <li><Link className="text-cyan-300 underline" to="/compare">Compare & Rank</Link></li>
          <li><Link className="text-cyan-300 underline" to="/fire-safety">Fire Safety Insights</Link></li>
          <li><Link className="text-cyan-300 underline" to="/mission-relevance">Mission Relevance</Link></li>
        </ul>
      </div>
      <p className="text-xs text-slate-400">Backend availability is not NASA data availability. Counts above come from the real API; zero means no records are loaded, not an error.</p>
    </div>
  )
}
