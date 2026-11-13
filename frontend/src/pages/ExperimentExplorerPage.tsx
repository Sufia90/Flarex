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
    <div className="space-y-4 animate-in fade-in slide-in-from-right-4 duration-300">
      <button 
        type="button" 
        onClick={onClose} 
        className="inline-flex items-center gap-2 text-sm font-medium text-cyan-400 hover:text-cyan-300 transition-colors bg-cyan-500/10 px-3 py-1.5 rounded-lg border border-cyan-500/20"
      >
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>
        Back to list
      </button>
      <div className="rounded-2xl border border-white/10 bg-[#0A1628] p-1 overflow-hidden shadow-lg shadow-black/20">
        <ExperimentDetail experiment={q.data} />
      </div>
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
    <div className="space-y-6 pb-12">
      
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-2">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-wide">Experiment Explorer</h1>
          <p className="text-sm text-slate-400 mt-1 max-w-2xl">
            Search and analyze NASA combustion experiments. Filter by name, fuel, or research category.
          </p>
        </div>
      </div>

      {/* Search Bar Container */}
      <div className="rounded-2xl border border-white/10 bg-[#0A1628] p-4 shadow-lg shadow-black/20">
        <form
          onSubmit={(e) => {
            e.preventDefault()
            onSearch()
          }}
          className="flex flex-col sm:flex-row gap-3"
        >
          <div className="relative flex-1">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <svg className="h-5 w-5 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <input
              className="w-full rounded-lg border border-white/10 bg-[#040B14] pl-10 pr-4 py-3 text-sm text-white focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 transition-all placeholder:text-slate-600"
              value={draftQuery}
              onChange={(e) => setDraftQuery(e.target.value)}
              placeholder="Search experiments by name, fuel, or category..."
            />
          </div>
          <div className="flex gap-2">
            <button 
              type="submit" 
              className="rounded-lg bg-cyan-600 px-6 py-3 text-sm font-bold text-white transition-all hover:bg-cyan-500 hover:shadow-[0_0_15px_rgba(34,211,238,0.4)]"
            >
              Search
            </button>
            <button 
              type="button" 
              onClick={onClear} 
              className="rounded-lg border border-white/10 bg-white/5 px-6 py-3 text-sm font-medium text-slate-300 transition-all hover:bg-white/10 hover:text-white"
            >
              Clear
            </button>
          </div>
        </form>
      </div>

      {/* Content Area */}
      <div className="mt-6">
        {selectedId ? (
          <ExperimentDetailView id={selectedId} onClose={() => setSearchParams({})} />
        ) : items.length === 0 ? (
          <div className="rounded-2xl border border-white/10 bg-[#0A1628] p-8">
            <EmptyState
              title={appliedQuery !== '' ? 'No experiments match your search' : 'No experiments yet'}
              message={appliedQuery !== '' ? 'Try a different search query.' : 'No experiment records are loaded. Real NASA records will appear here when they are added.'}
            />
          </div>
        ) : (
          <div>
            <div className="flex items-center justify-between mb-4 px-1">
              <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">Search Results</p>
              <p className="text-xs text-cyan-400 bg-cyan-500/10 px-3 py-1 rounded-full border border-cyan-500/20">
                Found {search.data?.total ?? 0} experiment(s)
              </p>
            </div>
            
            <ul className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {items.map((e) => (
                <li key={e.id}>
                  <button 
                    type="button" 
                    onClick={() => setSearchParams({ id: e.id })} 
                    className="w-full group flex flex-col items-start rounded-xl border border-white/10 bg-[#0A1628] p-4 text-left transition-all duration-300 hover:border-cyan-500/40 hover:bg-cyan-950/20 hover:shadow-[0_0_15px_rgba(34,211,238,0.1)]"
                  >
                    <span className="text-base font-semibold text-white group-hover:text-cyan-300 transition-colors">
                      {e.name}
                    </span>
                    <div className="flex items-center gap-2 mt-2">
                      <span className="text-[10px] uppercase tracking-wider text-slate-400 bg-white/5 px-2 py-1 rounded-md font-mono">
                        {e.nasa_investigation_id ?? e.id}
                      </span>
                      {e.research_category && (
                        <span className="text-[10px] uppercase tracking-wider text-cyan-400/80 bg-cyan-500/10 px-2 py-1 rounded-md">
                          {e.research_category}
                        </span>
                      )}
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

    </div>
  )
}