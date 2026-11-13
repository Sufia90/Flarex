import { EvidenceStatusBadge } from '../../components/common/EvidenceStatusBadge'
import type { FireSafetyInsight } from '../../types/fire-safety'

function EvidenceList({ title, items, note }: { title: string; items: string[]; note?: string }) {
  if (items.length === 0) return null
  return (
    <div className="rounded-lg bg-[#040B14] border border-white/5 p-3 mt-3">
      <p className="text-xs font-semibold text-cyan-400 mb-1">{title}</p>
      {note ? <p className="text-[10px] text-orange-400/80 italic mb-2">{note}</p> : null}
      <ul className="list-disc space-y-1 pl-5 text-sm text-slate-300">
        {items.map((item, i) => (
          <li key={i}>{item}</li>
        ))}
      </ul>
    </div>
  )
}

export function InsightCard({ insight }: { insight: FireSafetyInsight }) {
  return (
    <article className="space-y-3 rounded-xl border border-white/10 bg-[#0A1628] p-5 hover:border-cyan-500/30 transition-all duration-300 shadow-lg shadow-black/10">
      
      {/* Header Badges */}
      <div className="flex flex-wrap items-center gap-2 mb-2">
        <EvidenceStatusBadge status={insight.category} />
        <EvidenceStatusBadge status={insight.evidence_status} />
        {insight.verification_status ? <EvidenceStatusBadge status={insight.verification_status} /> : null}
        {insight.derived ? <span className="text-xs text-cyan-400/70 font-medium ml-1">Derived from linked experiments</span> : null}
      </div>

      {/* Title */}
      <p className="text-lg font-bold text-white tracking-wide">
        {insight.experiment_name ?? insight.experiment_id ?? 'Unknown experiment'}
      </p>

      {/* Evidence Sections */}
      <div className="space-y-2">
        <EvidenceList title="NASA-documented evidence" items={insight.documented_evidence} />
        <EvidenceList title="Derived interpretation" items={insight.derived_interpretation} />
        <EvidenceList title="Potential applications" items={insight.potential_applications} note="Potential applications are not experimentally proven results." />
      </div>

      {/* Footer Info (IDs, Limits) */}
      <div className="pt-3 border-t border-white/5 space-y-1">
        {insight.finding_ids.length > 0 ? <p className="text-xs text-slate-400">Supporting findings: {insight.finding_ids.join(', ')}</p> : null}
        {insight.source_ids.length > 0 ? <p className="text-xs text-slate-400">Sources: {insight.source_ids.join(', ')}</p> : null}
        {insight.limitations.length > 0 ? <p className="text-xs text-orange-400/70">Limitations: {insight.limitations.join('; ')}</p> : null}
        {insight.missing_information.length > 0 ? <p className="text-xs text-red-400/70">Missing information: {insight.missing_information.join('; ')}</p> : null}
      </div>

      {/* Explanation & Methodology */}
      {insight.explanation && (
        <p className="text-sm text-slate-300 mt-2 bg-white/5 p-2 rounded border border-white/5">{insight.explanation}</p>
      )}
      {insight.methodology && (
        <p className="text-[11px] text-slate-500 mt-1">{insight.methodology}</p>
      )}
    </article>
  )
}