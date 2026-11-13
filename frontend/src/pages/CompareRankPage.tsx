import { ComparisonPanel } from '../features/comparison/ComparisonPanel'
import { RankingPanel } from '../features/comparison/RankingPanel'

export function CompareRankPage() {
  return (
    <div className="space-y-8 pb-12">
      
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-2 border-b border-white/10 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-wide">Compare & Rank</h1>
          <p className="text-sm text-slate-400 mt-1 max-w-2xl">
            Analyze experiments and measurements side-by-side. Our ranking engine strictly uses documented criteria and never generates fake weights or scores.
          </p>
        </div>
        
        {/* Info Badge */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-cyan-500/10 border border-cyan-500/20 whitespace-nowrap">
           <svg className="w-4 h-4 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
             <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
           </svg>
          <span className="text-xs font-medium text-cyan-400 uppercase tracking-wider">Evidence-Based Only</span>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="grid grid-cols-1 gap-8">
        
        {/* Comparison Section Container */}
        <div className="rounded-2xl border border-white/10 bg-[#0A1628] p-6 shadow-lg shadow-black/20">
          <ComparisonPanel />
        </div>

        {/* Ranking Section Container */}
        <div className="rounded-2xl border border-white/10 bg-[#0A1628] p-6 shadow-lg shadow-black/20">
          <RankingPanel />
        </div>

      </div>
    </div>
  )
}