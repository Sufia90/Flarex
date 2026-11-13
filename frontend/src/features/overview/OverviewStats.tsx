import { StatCard } from '../../components/common/StatCard'

export interface OverviewCounts {
  experiments: number
  prevention: number
  detection: number
  suppression: number
}

export function OverviewStats({ counts }: { counts: OverviewCounts }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      
      {/* Experiments Card */}
      <div className="relative overflow-hidden rounded-xl border border-white/10 bg-[#0A1628] p-5 group hover:border-cyan-500/30 transition-all duration-300">
        <div className="absolute top-0 right-0 p-3 opacity-20 group-hover:opacity-40 transition-opacity">
          <svg className="w-12 h-12 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
          </svg>
        </div>
        <div className="relative z-10">
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">Experiments</p>
          <div className="flex items-baseline gap-2">
            <h3 className="text-3xl font-bold text-white group-hover:text-cyan-300 transition-colors">{counts.experiments}</h3>
          </div>
          <p className="text-[11px] text-slate-500 mt-2 flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-500/50"></span>
            Research records loaded
          </p>
        </div>
        <div className="absolute bottom-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-cyan-500/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
      </div>

      {/* Prevention Card */}
      <div className="relative overflow-hidden rounded-xl border border-white/10 bg-[#0A1628] p-5 group hover:border-green-500/30 transition-all duration-300">
        <div className="absolute top-0 right-0 p-3 opacity-20 group-hover:opacity-40 transition-opacity">
          <svg className="w-12 h-12 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
        </div>
        <div className="relative z-10">
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">Prevention</p>
          <div className="flex items-baseline gap-2">
            <h3 className="text-3xl font-bold text-white group-hover:text-green-300 transition-colors">{counts.prevention}</h3>
          </div>
          <p className="text-[11px] text-slate-500 mt-2 flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-green-500/50"></span>
            Fire safety evidence
          </p>
        </div>
        <div className="absolute bottom-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-green-500/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
      </div>

      {/* Detection Card */}
      <div className="relative overflow-hidden rounded-xl border border-white/10 bg-[#0A1628] p-5 group hover:border-amber-500/30 transition-all duration-300">
        <div className="absolute top-0 right-0 p-3 opacity-20 group-hover:opacity-40 transition-opacity">
          <svg className="w-12 h-12 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
          </svg>
        </div>
        <div className="relative z-10">
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">Detection</p>
          <div className="flex items-baseline gap-2">
            <h3 className="text-3xl font-bold text-white group-hover:text-amber-300 transition-colors">{counts.detection}</h3>
          </div>
          <p className="text-[11px] text-slate-500 mt-2 flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-500/50"></span>
            Fire safety evidence
          </p>
        </div>
        <div className="absolute bottom-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-amber-500/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
      </div>

      {/* Suppression Card */}
      <div className="relative overflow-hidden rounded-xl border border-white/10 bg-[#0A1628] p-5 group hover:border-red-500/30 transition-all duration-300">
        <div className="absolute top-0 right-0 p-3 opacity-20 group-hover:opacity-40 transition-opacity">
          <svg className="w-12 h-12 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z" />
          </svg>
        </div>
        <div className="relative z-10">
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">Suppression</p>
          <div className="flex items-baseline gap-2">
            <h3 className="text-3xl font-bold text-white group-hover:text-red-300 transition-colors">{counts.suppression}</h3>
          </div>
          <p className="text-[11px] text-slate-500 mt-2 flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-red-500/50"></span>
            Fire safety evidence
          </p>
        </div>
        <div className="absolute bottom-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-red-500/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
      </div>

    </div>
  )
}