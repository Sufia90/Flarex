import { ComparisonPanel } from '../features/comparison/ComparisonPanel'
import { RankingPanel } from '../features/comparison/RankingPanel'

export function CompareRankPage() {
  return (
    <div className="space-y-6">
      <p className="text-sm text-slate-300">Compare experiments or measurements. Rankings use one documented criterion at a time and never invent weights or scores.</p>
      <ComparisonPanel />
      <RankingPanel />
    </div>
  )
}
