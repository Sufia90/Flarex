import { EvidenceStatusBadge } from '../../components/common/EvidenceStatusBadge'
import type { FireSafetyInsight } from '../../types/fire-safety'

function EvidenceList({ title, items, note }: { title: string; items: string[]; note?: string }) {
  if (items.length === 0) return null
  return (
    <div>
      <p className="text-xs font-semibold text-slate-300">{title}</p>
      {note ? <p className="text-xs text-slate-500">{note}</p> : null}
      <ul className="mt-1 list-disc space-y-1 pl-5 text-sm text-slate-300">
        {items.map((item, i) => (
          <li key={i}>{item}</li>
        ))}
      </ul>
    </div>
  )
}

export function InsightCard({ insight }: { insight: FireSafetyInsight }) {
  return (
    <article className="space-y-3 rounded border border-slate-700 bg-slate-900 p-4">
      <div className="flex flex-wrap items-center gap-2">
        <EvidenceStatusBadge status={insight.category} />
        <EvidenceStatusBadge status={insight.evidence_status} />
        {insight.verification_status ? <EvidenceStatusBadge status={insight.verification_status} /> : null}
        {insight.derived ? <span className="text-xs text-slate-400">Derived from linked experiments</span> : null}
      </div>
      <p className="text-sm text-white">{insight.experiment_name ?? insight.experiment_id ?? 'Unknown experiment'}</p>
      <EvidenceList title="NASA-documented evidence" items={insight.documented_evidence} />
      <EvidenceList title="Derived interpretation" items={insight.derived_interpretation} />
      <EvidenceList title="Potential applications" items={insight.potential_applications} note="Potential applications are not experimentally proven results." />
      {insight.finding_ids.length > 0 ? <p className="text-xs text-slate-400">Supporting findings: {insight.finding_ids.join(', ')}</p> : null}
      {insight.source_ids.length > 0 ? <p className="text-xs text-slate-400">Sources: {insight.source_ids.join(', ')}</p> : null}
      {insight.limitations.length > 0 ? <p className="text-xs text-slate-400">Limitations: {insight.limitations.join('; ')}</p> : null}
      {insight.missing_information.length > 0 ? <p className="text-xs text-slate-400">Missing information: {insight.missing_information.join('; ')}</p> : null}
      <p className="text-sm text-slate-300">{insight.explanation}</p>
      <p className="text-xs text-slate-500">{insight.methodology}</p>
    </article>
  )
}
