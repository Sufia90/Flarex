const tones: Record<string, string> = {
  documented: 'border-emerald-600 bg-emerald-950 text-emerald-300',
  confirmed: 'border-emerald-600 bg-emerald-950 text-emerald-300',
  complete: 'border-emerald-600 bg-emerald-950 text-emerald-300',
  comparable: 'border-emerald-600 bg-emerald-950 text-emerald-300',
  potential: 'border-amber-600 bg-amber-950 text-amber-300',
  partially_documented: 'border-amber-600 bg-amber-950 text-amber-300',
  partially_complete: 'border-amber-600 bg-amber-950 text-amber-300',
  partially_comparable: 'border-amber-600 bg-amber-950 text-amber-300',
  unsupported: 'border-red-600 bg-red-950 text-red-300',
  not_comparable: 'border-red-600 bg-red-950 text-red-300',
  verification_failed: 'border-red-600 bg-red-950 text-red-300',
  unknown: 'border-slate-600 bg-slate-800 text-slate-300',
  unverified: 'border-slate-600 bg-slate-800 text-slate-300',
  not_yet_verified: 'border-slate-600 bg-slate-800 text-slate-300',
  insufficient_evidence: 'border-slate-600 bg-slate-800 text-slate-300',
  insufficient_data: 'border-slate-600 bg-slate-800 text-slate-300',
  incomplete: 'border-slate-600 bg-slate-800 text-slate-300',
}

function pretty(status: string) {
  return status.replace(/_/g, ' ')
}

export function EvidenceStatusBadge({ status, label }: { status: string; label?: string }) {
  const tone = tones[status] ?? 'border-slate-600 bg-slate-800 text-slate-300'
  return (
    <span className={`inline-block rounded border px-2 py-0.5 text-xs ${tone}`}>
      {label ?? pretty(status)}
    </span>
  )
}
