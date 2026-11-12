import { useState } from 'react'
import { EvidenceStatusBadge } from '../../components/common/EvidenceStatusBadge'
import { LoadingState } from '../../components/feedback/LoadingState'
import { ErrorState } from '../../components/feedback/ErrorState'
import { useMissionRelevanceForExperiment, useMissionRelevanceForHardware } from '../../hooks/useMissionRelevance'
import type { MissionContext, MissionRelevanceAssessment } from '../../types/mission-relevance'

const missions: MissionContext[] = ['ISS', 'Moon', 'Mars']

function StringList({ title, items }: { title: string; items: string[] }) {
  if (items.length === 0) return null
  return (
    <div>
      <p className="text-xs text-slate-400">{title}</p>
      <ul className="mt-1 list-disc space-y-1 pl-5 text-sm text-slate-300">
        {items.map((item, i) => (
          <li key={i}>{item}</li>
        ))}
      </ul>
    </div>
  )
}

function AssessmentView({ subjectLabel, mission, pending, error, data, onRetry }: { subjectLabel: string; mission: MissionContext; pending: boolean; error: boolean; data: MissionRelevanceAssessment | undefined; onRetry: () => void }) {
  if (pending) return <LoadingState message="Loading assessment..." />
  if (error) return <ErrorState message="Could not load the mission relevance assessment." onRetry={onRetry} />
  if (!data) return <p className="text-sm text-slate-500">No assessment available.</p>
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <span className="font-semibold text-white">{subjectLabel} — {mission}</span>
        <EvidenceStatusBadge status={data.relevance_level} />
        {data.evidence_status ? <EvidenceStatusBadge status={data.evidence_status} /> : null}
      </div>
      <p className="text-sm text-slate-300">{data.explanation}</p>
      <StringList title="Relevant conditions" items={data.relevant_conditions} />
      <StringList title="Similarities" items={data.similarities} />
      <StringList title="Differences" items={data.differences} />
      <StringList title="Supporting evidence" items={data.supporting_evidence} />
      <StringList title="Transferability limitations" items={data.transferability_limitations} />
      <StringList title="Missing information" items={data.missing_information} />
      <StringList title="Source references" items={data.source_ids} />
      {data.derived_from_experiment_ids.length > 0 ? <p className="text-xs text-slate-400">Derived from experiments: {data.derived_from_experiment_ids.join(', ')}</p> : null}
      <StringList title="Limitations" items={data.limitations} />
      <p className="text-sm text-slate-300">Microgravity findings are not automatically Moon or Mars evidence. Partial-gravity transferability may be unknown. A potential application requires further validation. Missing evidence does not mean the experiment is irrelevant.</p>
      <p className="text-xs text-slate-500">{data.methodology}</p>
    </div>
  )
}

function ExperimentRelevance({ id, name, mission }: { id: string; name: string | null; mission: MissionContext }) {
  const q = useMissionRelevanceForExperiment(id, mission)
  return <AssessmentView subjectLabel={name ?? id} mission={mission} pending={q.isPending} error={q.isError} data={q.data} onRetry={() => q.refetch()} />
}

function HardwareRelevance({ id, name, mission }: { id: string; name: string | null; mission: MissionContext }) {
  const q = useMissionRelevanceForHardware(id, mission)
  return <AssessmentView subjectLabel={name ?? id} mission={mission} pending={q.isPending} error={q.isError} data={q.data} onRetry={() => q.refetch()} />
}

export function RelevancePanel({ subjectType, subjectId, subjectName, initialMission }: { subjectType: 'experiment' | 'hardware'; subjectId: string; subjectName: string | null; initialMission?: MissionContext }) {
  const [mission, setMission] = useState<MissionContext>(initialMission ?? 'ISS')
  return (
    <div className="space-y-4 rounded border border-slate-700 bg-slate-900 p-4">
      <div className="flex gap-2">
        {missions.map((m) => (
          <button key={m} type="button" onClick={() => setMission(m)} className={`rounded border px-3 py-1 text-sm ${mission === m ? 'border-cyan-600 bg-cyan-950 text-cyan-300' : 'border-slate-600 text-slate-300'}`}>
            {m}
          </button>
        ))}
      </div>
      {subjectType === 'hardware' ? (
        <HardwareRelevance id={subjectId} name={subjectName} mission={mission} />
      ) : (
        <ExperimentRelevance id={subjectId} name={subjectName} mission={mission} />
      )}
    </div>
  )
}
