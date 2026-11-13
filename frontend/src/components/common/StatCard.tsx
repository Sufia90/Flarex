export function StatCard({ label, value, subtext }: { label: string; value: number | string; subtext?: string }) {
  return (
    <div className="relative overflow-hidden rounded-xl border border-white/10 bg-[#0A1628] p-5 group hover:border-cyan-500/30 transition-all duration-300 shadow-lg shadow-black/20">
      {/* Subtle top-right glow on hover */}
      <div className="absolute top-0 right-0 w-16 h-16 bg-cyan-500/10 rounded-bl-full opacity-0 group-hover:opacity-100 transition-opacity blur-xl"></div>
      
      <div className="relative z-10">
        <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-1">{label}</p>
        <p className="text-3xl font-bold text-white group-hover:text-cyan-300 transition-colors">{value}</p>
        {subtext ? (
          <p className="mt-2 text-[11px] text-slate-500 flex items-center gap-1">
            <span className="w-1 h-1 rounded-full bg-slate-600"></span>
            {subtext}
          </p>
        ) : null}
      </div>
      
      {/* Bottom accent line */}
      <div className="absolute bottom-0 left-0 w-full h-[2px] bg-gradient-to-r from-transparent via-cyan-500/40 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
    </div>
  )
}