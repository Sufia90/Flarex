import { StatCard } from '../../components/common/StatCard'

export interface OverviewCounts {
  experiments: number
  hardware: number
  relationships: number
  prevention: number
  detection: number
  suppression: number
}

export function OverviewStats({ counts }: { counts: OverviewCounts }) {
  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-3">
      <StatCard label="Experiments" value={counts.experiments} subtext="Research records loaded" />
      <StatCard label="Hardware" value={counts.hardware} subtext="Hardware records loaded" />
      <StatCard label="Relationships" value={counts.relationships} subtext="Experiment-hardware links" />
      <StatCard label="Prevention evidence" value={counts.prevention} subtext="Fire safety insights" />
      <StatCard label="Detection evidence" value={counts.detection} subtext="Fire safety insights" />
      <StatCard label="Suppression evidence" value={counts.suppression} subtext="Fire safety insights" />
    </div>
  )
}
