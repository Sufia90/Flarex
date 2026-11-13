import { useState } from 'react'
import { useSearchParams } from 'react-router'
import { LoadingState } from '../components/feedback/LoadingState'
import { ErrorState } from '../components/feedback/ErrorState'
import { EmptyState } from '../components/feedback/EmptyState'
import { RelevancePanel } from '../features/mission-relevance/RelevancePanel'
import { useExperiments } from '../hooks/useExperiments'
import { useHardware } from '../hooks/useHardware'
import type { MissionContext } from '../types/mission-relevance'

export function MissionRelevancePage() {
  const [searchParams] = useSearchParams()
  const [subjectType, setSubjectType] = useState<'experiment' | 'hardware'>(
    searchParams.get('subject') === 'hardware' ? 'hardware' : 'experiment',
  )
  const [subjectId, setSubjectId] = useState(searchParams.get('id') ?? '')
  const initialMission = (searchParams.get('mission') as MissionContext) ?? 'ISS'
  const experiments = useExperiments()
  const hardware = useHardware()
  const items = subjectType === 'experiment' ? (experiments.data?.items ?? []) : (hardware.data?.items ?? [])
  const subjectName = items.find((i) => i.id === subjectId)?.name ?? null

  function changeSubjectType(next: 'experiment' | 'hardware') {
    setSubjectType(next)
    setSubjectId('')
  }

  if (experiments.isPending || hardware.isPending) return <LoadingState message="Loading records..." />
  if (experiments.isError || hardware.isError) return <ErrorState message="Could not load records." onRetry={() => { experiments.refetch(); hardware.refetch() }} />

  return (
    <div className="space-y-6 pb-12">
      
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-2 border-b border-white/10 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-wide">Mission Relevance</h1>
          <p className="text-sm text-slate-400 mt-1 max-w-2xl">
            Assess how documented experiments and hardware apply to ISS, Moon Base, and Mars Base missions. Relevance is qualitative and uses no numeric scores.
          </p>
        </div>
        
        {/* Info Badge */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-blue-500/10 border border-blue-500/20 whitespace-nowrap">
           <svg className="w-4 h-4 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
             <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
           </svg>
          <span className="text-xs font-medium text-blue-400 uppercase tracking-wider">Qualitative Analysis</span>
        </div>
      </div>

      {/* Selection Area Container */}
      <div className="rounded-2xl border border-white/10 bg-[#0A1628] p-5 shadow-lg shadow-black/20">
        
        {/* Subject Type Toggle */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-5">
          <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
            Select Subject Type
          </label>
          <div className="flex p-1 bg-[#040B14] rounded-lg border border-white/5 w-full sm:w-auto">
            <button 
              type="button" 
              onClick={() => changeSubjectType('experiment')} 
              className={`flex-1 sm:flex-none rounded-md px-6 py-1.5 text-sm font-medium transition-all ${subjectType === 'experiment' ? 'bg-cyan-500/20 text-cyan-300 shadow-sm' : 'text-slate-400 hover:text-white'}`}
            >
              Experiment
            </button>
            <button 
              type="button" 
              onClick={() => changeSubjectType('hardware')} 
              className={`flex-1 sm:flex-none rounded-md px-6 py-1.5 text-sm font-medium transition-all ${subjectType === 'hardware' ? 'bg-cyan-500/20 text-cyan-300 shadow-sm' : 'text-slate-400 hover:text-white'}`}
            >
              Hardware
            </button>
          </div>
        </div>

        {/* Record Selector */}
        <label className="block">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 block">
            {subjectType === 'experiment' ? 'Select Experiment Record' : 'Select Hardware Record'}
          </span>
          <div className="relative">
            <select 
              className="w-full rounded-lg border border-white/10 bg-[#040B14] px-4 py-3 text-sm text-white focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 transition-all appearance-none cursor-pointer" 
              value={subjectId} 
              onChange={(e) => setSubjectId(e.target.value)}
            >
              <option value="">— Choose a record to analyze —</option>
              {items.map((i) => (
                <option key={i.id} value={i.id}>{i.name}</option>
              ))}
            </select>
            {/* Custom Dropdown Arrow */}
            <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-slate-400">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
            </div>
          </div>
        </label>
      </div>

      {/* Content Area */}
      <div className="mt-6">
        {subjectId ? (
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
            <RelevancePanel subjectType={subjectType} subjectId={subjectId} subjectName={subjectName} initialMission={initialMission} />
          </div>
        ) : (
          <div className="rounded-2xl border border-white/10 bg-[#0A1628] p-8">
            <EmptyState 
              title="No record selected" 
              message="Choose an experiment or hardware record from the dropdown above to see its mission relevance analysis for ISS, Moon, and Mars." 
            />
          </div>
        )}
      </div>

    </div>
  )
}