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
    <div className="rounded-lg bg-[#040B14] border border-white/5 p-4 mt-3">
      <p className="text-xs font-semibold text-cyan-400 uppercase tracking-wider mb-2">{title}</p>
      <ul className="list-disc space-y-1.5 pl-5 text-sm text-slate-300">
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
    <div className="space-y-4">
      {/* Header Info */}
      <div className="flex flex-wrap items-center gap-3 border-b border-white/5 pb-4 mb-4">
        <span className="text-lg font-bold text-white">{subjectLabel}</span>
        <span className="text-xs font-mono px-2 py-1 rounded bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">{mission} Mission</span>
        <div className="flex gap-2 ml-auto">
          <EvidenceStatusBadge status={data.relevance_level} />
          {data.evidence_status ? <EvidenceStatusBadge status={data.evidence_status} /> : null}
        </div>
      </div>

      <p className="text-sm text-slate-300 bg-white/5 p-3 rounded-lg border border-white/5">{data.explanation}</p>
      
      {/* Lists Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <StringList title="Relevant conditions" items={data.relevant_conditions} />
          <StringList title="Similarities" items={data.similarities} />
          <StringList title="Differences" items={data.differences} />
          <StringList title="Supporting evidence" items={data.supporting_evidence} />
        </div>
        <div>
          <StringList title="Transferability limitations" items={data.transferability_limitations} />
          <StringList title="Missing information" items={data.missing_information} />
          <StringList title="Source references" items={data.source_ids} />
          <StringList title="Limitations" items={data.limitations} />
        </div>
      </div>

      {/* Footer Info */}
      <div className="mt-4 pt-4 border-t border-white/10 space-y-2">
        {data.derived_from_experiment_ids.length > 0 ? (
          <p className="text-xs text-slate-400">
            <span className="font-semibold text-slate-300">Derived from experiments:</span> {data.derived_from_experiment_ids.join(', ')}
          </p>
        ) : null}
        
        <div className="p-4 rounded-lg bg-orange-500/5 border border-orange-500/10">
          <p className="text-xs text-orange-400/90 leading-relaxed">
            <strong className="text-orange-400 block mb-1">Important Note</strong>
            Microgravity findings are not automatically Moon or Mars evidence. Partial-gravity transferability may be unknown. A potential application requires further validation. Missing evidence does not mean the experiment is irrelevant.
          </p>
        </div>
        
        <p className="text-[11px] text-slate-500 italic mt-2">{data.methodology}</p>
      </div>
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
    <div className="space-y-6 rounded-2xl border border-white/10 bg-[#0A1628] p-6 shadow-lg shadow-black/20">
      
      {/* Mission Tabs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold text-white tracking-wide">Mission Context</h3>
          <p className="text-xs text-slate-400 mt-1">Select a mission to view relevant assessments.</p>
        </div>
        
        <div className="flex p-1 bg-[#040B14] rounded-lg border border-white/5 w-full sm:w-auto">
          {missions.map((m) => (
            <button 
              key={m} 
              type="button" 
              onClick={() => setMission(m)} 
              className={`flex-1 sm:flex-none rounded-md px-6 py-1.5 text-sm font-bold uppercase tracking-wider transition-all duration-300 ${
                mission === m 
                  ? 'bg-blue-500/20 text-blue-300 shadow-[0_0_10px_rgba(59,130,246,0.2)]' 
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              {m}
            </button>
          ))}
        </div>
      </div>

      {/* Content Area */}
      <div className="pt-4 border-t border-white/5 animate-in fade-in duration-500">
        {subjectType === 'hardware' ? (
          <HardwareRelevance id={subjectId} name={subjectName} mission={mission} />
        ) : (
          <ExperimentRelevance id={subjectId} name={subjectName} mission={mission} />
        )}
      </div>

    </div>
  )
}