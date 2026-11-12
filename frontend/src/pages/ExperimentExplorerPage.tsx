import { useState } from 'react'
import { useSearchParams } from 'react-router'
import { LoadingState } from '../components/feedback/LoadingState'
import { ErrorState } from '../components/feedback/ErrorState'
import { EmptyState } from '../components/feedback/EmptyState'
import { ExperimentFilters, emptyExperimentFilters, type ExperimentFilterValues } from '../features/experiments/ExperimentFilters'
import { ExperimentDetail } from '../features/experiments/ExperimentDetail'
import { useExperiment, useSearchExperiments } from '../hooks/useExperiments'

function ExperimentDetailView({ id, onClose }: { id: string; onClose: () => void }) {
  const q = useExperiment(id)
  if (q.isPending) return <LoadingState message="Loading experiment..." />
  if (q.isError || !q.data) return <ErrorState message="Could not load this experiment." onRetry={() => q.refetch()} />
  return (
    <div className="space-y-2">
      <button type="button" onClick={onClose} className="text-sm text-cyan-300 underline">Back to list</button>
      <ExperimentDetail experiment={q.data} />
    </div>
  )
}

export function ExperimentExplorerPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [draftFilters, setDraftFilters] = useState<ExperimentFilterValues>(emptyExperimentFilters)
  const [appliedFilters, setAppliedFilters] = useState<ExperimentFilterValues>(emptyExperimentFilters)
  const search = useSearchExperiments({ ...appliedFilters, page: 1, page_size: 20 })
  const selectedId = searchParams.get('id')
  const items = search.data?.items ?? []
  const isFiltered = Object.values(appliedFilters).some((v) => v !== '')

  function onSearch() {
    setAppliedFilters(draftFilters)
  }

  if (search.isPending) return <LoadingState message="Loading experiments..." />
  if (search.isError) return <ErrorState message="Could not load experiments." onRetry={() => search.refetch()} />
  return (
    <div className="space-y-4">
      <ExperimentFilters value={draftFilters} onChange={setDraftFilters} onSearch={onSearch} />
      {selectedId ? (
        <ExperimentDetailView id={selectedId} onClose={() => setSearchParams({})} />
      ) : items.length === 0 ? (
        <EmptyState
          title={isFiltered ? 'No experiments match these filters' : 'No experiments yet'}
          message={isFiltered ? 'Try different filters or clear them.' : 'No experiment records are loaded. Real NASA records will appear here when they are added.'}
        />
      ) : (
        <div>
          <p className="text-xs text-slate-400">Found {search.data?.total ?? 0} experiment(s).</p>
          <ul className="mt-2 space-y-1">
            {items.map((e) => (
              <li key={e.id}>
                <button type="button" onClick={() => setSearchParams({ id: e.id })} className="w-full rounded border border-slate-700 px-3 py-2 text-left text-sm text-white">
                  {e.name} <span className="text-xs text-slate-500">{e.nasa_investigation_id ?? e.id}{e.research_category ? ` · ${e.research_category}` : ''}</span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
