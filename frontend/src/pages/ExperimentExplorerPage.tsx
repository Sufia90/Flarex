import { useState } from 'react'
import { useSearchParams } from 'react-router'
import { LoadingState } from '../components/feedback/LoadingState'
import { ErrorState } from '../components/feedback/ErrorState'
import { EmptyState } from '../components/feedback/EmptyState'
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
  const [draftQuery, setDraftQuery] = useState('')
  const [appliedQuery, setAppliedQuery] = useState('')
  const search = useSearchExperiments({ query: appliedQuery, page: 1, page_size: 20 })
  const selectedId = searchParams.get('id')
  const items = search.data?.items ?? []

  function onSearch() {
    setAppliedQuery(draftQuery)
  }

  function onClear() {
    setDraftQuery('')
    setAppliedQuery('')
  }

  if (search.isPending) return <LoadingState message="Loading experiments..." />
  if (search.isError) return <ErrorState message="Could not load experiments." onRetry={() => search.refetch()} />
  return (
    <div className="space-y-4">
      <form
        onSubmit={(e) => {
          e.preventDefault()
          onSearch()
        }}
        className="flex gap-2"
      >
        <input
          className="w-full rounded border border-slate-600 bg-slate-800 px-3 py-2 text-sm text-white"
          value={draftQuery}
          onChange={(e) => setDraftQuery(e.target.value)}
          placeholder="Search experiments by name, fuel, or category..."
        />
        <button type="submit" className="rounded bg-cyan-600 px-3 py-2 text-sm text-white">Search</button>
        <button type="button" onClick={onClear} className="rounded border border-slate-600 px-3 py-2 text-sm text-slate-300">Clear</button>
      </form>
      {selectedId ? (
        <ExperimentDetailView id={selectedId} onClose={() => setSearchParams({})} />
      ) : items.length === 0 ? (
        <EmptyState
          title={appliedQuery !== '' ? 'No experiments match your search' : 'No experiments yet'}
          message={appliedQuery !== '' ? 'Try a different search.' : 'No experiment records are loaded. Real NASA records will appear here when they are added.'}
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
