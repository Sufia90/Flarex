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
    <div className="space-y-4">
      <p className="text-sm text-slate-300">Mission relevance is qualitative: documented, potential, unsupported, unknown, or insufficient evidence. No numeric scores are used.</p>
      <div className="flex gap-2">
        <button type="button" onClick={() => changeSubjectType('experiment')} className={`rounded border px-3 py-1 text-sm ${subjectType === 'experiment' ? 'border-cyan-600 bg-cyan-950 text-cyan-300' : 'border-slate-600 text-slate-300'}`}>Experiment</button>
        <button type="button" onClick={() => changeSubjectType('hardware')} className={`rounded border px-3 py-1 text-sm ${subjectType === 'hardware' ? 'border-cyan-600 bg-cyan-950 text-cyan-300' : 'border-slate-600 text-slate-300'}`}>Hardware</button>
      </div>
      <label className="block text-xs text-slate-400">
        {subjectType === 'experiment' ? 'Experiment' : 'Hardware'}
        <select className="mt-1 w-full rounded border border-slate-600 bg-slate-800 px-2 py-1 text-sm text-white" value={subjectId} onChange={(e) => setSubjectId(e.target.value)}>
          <option value="">Select a record</option>
          {items.map((i) => (
            <option key={i.id} value={i.id}>{i.name}</option>
          ))}
        </select>
      </label>
      {subjectId ? (
        <RelevancePanel subjectType={subjectType} subjectId={subjectId} subjectName={subjectName} initialMission={initialMission} />
      ) : (
        <EmptyState title="Select a record" message="Choose an experiment or hardware record to see its mission relevance for ISS, Moon, and Mars." />
      )}
    </div>
  )
}
