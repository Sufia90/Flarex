import { useState } from 'react'
import { EvidenceStatusBadge } from '../../components/common/EvidenceStatusBadge'
import { LoadingState } from '../../components/feedback/LoadingState'
import { ErrorState } from '../../components/feedback/ErrorState'
import { EmptyState } from '../../components/feedback/EmptyState'
import { useExperiments } from '../../hooks/useExperiments'
import { useHardware } from '../../hooks/useHardware'
import { useCreateRanking } from '../../hooks/useRankings'
import type { RankingCriterion, RankingResult } from '../../types/ranking'

const criteria: { value: RankingCriterion; label: string; description: string }[] = [
  { value: 'hardware_experiment_associations', label: 'Hardware by documented experiment associations', description: 'Ranks hardware by how many experiments are documented as using it.' },
  { value: 'experiment_documentation_completeness', label: 'Experiments by documentation completeness', description: 'Ranks experiments by how many documentation fields are present.' },
  { value: 'experiment_measurement_coverage', label: 'Experiments by measurement coverage', description: 'Ranks experiments by how many measurements are documented.' },
]

export function RankingPanel() {
  const [criterion, setCriterion] = useState<RankingCriterion>('experiment_documentation_completeness')
  const [mode, setMode] = useState<'all' | 'selected'>('all')
  const [selected, setSelected] = useState<string[]>([])
  const [limit, setLimit] = useState(10)
  const [result, setResult] = useState<RankingResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const experiments = useExperiments()
  const hardware = useHardware()
  const createRanking = useCreateRanking()
  const isHardwareCriterion = criterion === 'hardware_experiment_associations'
  const items = isHardwareCriterion
    ? (hardware.data?.items ?? []).map((h) => ({ id: h.id, label: h.name }))
    : (experiments.data?.items ?? []).map((e) => ({ id: e.id, label: e.name }))
  const criterionInfo = criteria.find((c) => c.value === criterion)

  function toggle(id: string) {
    if (selected.includes(id)) {
      setSelected(selected.filter((s) => s !== id))
    } else {
      setSelected([...selected, id])
    }
  }

  async function submit() {
    setError(null)
    setResult(null)
    try {
      setResult(await createRanking.mutateAsync({ criterion, item_ids: mode === 'selected' ? selected : null, limit }))
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Ranking failed.')
    }
  }

  function changeCriterion(next: RankingCriterion) {
    setCriterion(next)
    setSelected([])
    setResult(null)
    setError(null)
  }

  if (experiments.isPending || hardware.isPending) return <LoadingState message="Loading records..." />
  
  return (
    <div className="space-y-6">
      <div className="border-b border-white/10 pb-4">
        <h3 className="text-lg font-semibold text-white tracking-wide flex items-center gap-2">
          <svg className="w-5 h-5 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>
          Evidence-based Ranking
        </h3>
        <p className="text-sm text-slate-400 mt-2">
          This ranking measures <strong className="text-cyan-300">one documented criterion at a time</strong>. It does not say which experiment is best overall, and uses no weights or combined score.
        </p>
      </div>

      {/* Controls Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 bg-[#040B14] p-5 rounded-xl border border-white/5">
        
        {/* Left Col: Criterion */}
        <div className="space-y-4">
          <label className="block">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 block">Ranking Criterion</span>
            <select 
              className="w-full rounded-lg border border-white/10 bg-[#0A1628] px-3 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 transition-all appearance-none cursor-pointer" 
              value={criterion} 
              onChange={(e) => changeCriterion(e.target.value as RankingCriterion)}
            >
              {criteria.map((c) => (
                <option key={c.value} value={c.value}>{c.label}</option>
              ))}
            </select>
          </label>
          {criterionInfo ? <p className="text-xs text-slate-400 leading-relaxed bg-white/5 p-3 rounded-lg border border-white/5">{criterionInfo.description}</p> : null}
        </div>

        {/* Right Col: Options */}
        <div className="space-y-4">
          <div>
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 block">Target Records</span>
            <div className="flex p-1 bg-[#0A1628] rounded-lg border border-white/10">
              <button type="button" onClick={() => setMode('all')} className={`flex-1 rounded-md px-3 py-1.5 text-xs font-medium transition-all ${mode === 'all' ? 'bg-cyan-500/20 text-cyan-300' : 'text-slate-400 hover:text-white'}`}>All Eligible</button>
              <button type="button" onClick={() => setMode('selected')} className={`flex-1 rounded-md px-3 py-1.5 text-xs font-medium transition-all ${mode === 'selected' ? 'bg-cyan-500/20 text-cyan-300' : 'text-slate-400 hover:text-white'}`}>Select Manually</button>
            </div>
          </div>
          
          <label className="block">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 block">Result Limit</span>
            <input className="w-24 rounded-lg border border-white/10 bg-[#0A1628] px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 transition-all" type="number" min={1} max={50} value={limit} onChange={(e) => setLimit(Number(e.target.value))} />
          </label>
        </div>
      </div>

      {/* Manual Selection List */}
      {mode === 'selected' ? (
        <div className="mt-4">
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">Select Records to Rank</p>
          {items.length === 0 ? (
            <EmptyState title="No records to rank" message="No records are loaded yet." />
          ) : (
            <ul className="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-64 overflow-auto p-1 custom-scrollbar">
              {items.map((item) => (
                <li key={item.id}>
                  <label className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-all ${selected.includes(item.id) ? 'bg-cyan-500/10 border-cyan-500/30' : 'bg-[#040B14] border-white/5 hover:border-white/20'}`}>
                    <input type="checkbox" checked={selected.includes(item.id)} onChange={() => toggle(item.id)} className="w-4 h-4 rounded border-white/20 bg-[#040B14] text-cyan-500 focus:ring-cyan-500 focus:ring-offset-[#040B14]" />
                    <div>
                      <span className="block text-sm font-medium text-white">{item.label}</span>
                      <span className="block text-[10px] text-slate-500 font-mono mt-0.5">{item.id}</span>
                    </div>
                  </label>
                </li>
              ))}
            </ul>
          )}
        </div>
      ) : null}

      <button type="button" disabled={createRanking.isPending || (mode === 'selected' && selected.length === 0)} onClick={submit} className="w-full sm:w-auto rounded-lg bg-cyan-600 px-8 py-2.5 text-sm font-bold text-white transition-all hover:bg-cyan-500 hover:shadow-[0_0_15px_rgba(34,211,238,0.4)] disabled:opacity-50 disabled:hover:bg-cyan-600 disabled:hover:shadow-none">
        Generate Ranking
      </button>

      {createRanking.isPending ? <LoadingState message="Ranking..." /> : null}
      {error ? <ErrorState message={error} onRetry={submit} /> : null}

      {/* Results Area */}
      {result ? (
        <div className="mt-8 rounded-xl bg-[#040B14] border border-white/5 p-5">
          <div className="flex flex-wrap items-center gap-3 mb-4 border-b border-white/5 pb-4">
            <h4 className="text-white font-semibold text-lg">{result.title}</h4>
            <EvidenceStatusBadge status={result.status} />
          </div>
          
          <p className="text-sm text-slate-300 mb-2"><span className="text-slate-500">Question:</span> {result.question}</p>
          <p className="text-sm text-slate-300 mb-4"><span className="text-cyan-400 font-medium">{result.metric_name}:</span> {result.metric_description}</p>
          
          {result.status === 'insufficient_evidence' ? (
            <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/20">
              <p className="text-sm text-red-400 font-medium">Insufficient evidence to rank.</p>
              <p className="text-xs text-slate-400 mt-1">{result.explanation}</p>
            </div>
          ) : result.items.length === 0 ? (
            <EmptyState title="No ranked items" message="No items had enough evidence to rank." />
          ) : (
            <ol className="space-y-3">
              {result.items.map((item) => (
                <li key={item.item_id} className="relative overflow-hidden rounded-xl border border-white/5 bg-[#0A1628] p-4 hover:border-cyan-500/30 transition-all">
                  <div className="flex flex-wrap items-center gap-3 mb-2">
                    <span className="flex items-center justify-center w-8 h-8 rounded-full bg-cyan-500/10 text-cyan-400 font-bold text-sm border border-cyan-500/20">
                      {item.rank === null ? '—' : item.rank}
                    </span>
                    <span className="text-base font-semibold text-white">{item.item_name ?? item.item_id}</span>
                    <span className="ml-auto text-sm font-mono text-cyan-300 bg-cyan-500/10 px-3 py-1 rounded-md border border-cyan-500/20">
                      {item.metric_value}{item.metric_max !== null && item.metric_max !== undefined ? ` / ${item.metric_max}` : ''}
                    </span>
                  </div>
                  {item.rank === null ? <p className="mt-1 text-xs text-red-400">Not ranked — insufficient evidence.</p> : null}
                  <p className="mt-2 text-sm text-slate-400">{item.explanation}</p>
                  <div className="mt-3 flex flex-wrap items-center gap-2">
                    {item.data_completeness ? <EvidenceStatusBadge status={item.data_completeness} /> : null}
                    {item.verification_status ? <EvidenceStatusBadge status={item.verification_status} /> : null}
                    <span className="text-[10px] uppercase tracking-wider text-slate-500 bg-white/5 px-2 py-1 rounded-md">Evidence records: {item.evidence_ids.length}</span>
                  </div>
                  {item.limitations.length > 0 ? <p className="mt-2 text-xs text-orange-400/80">Limitations: {item.limitations.join('; ')}</p> : null}
                </li>
              ))}
            </ol>
          )}
          
          <div className="mt-6 pt-4 border-t border-white/5">
            <p className="text-sm text-slate-300 mb-2">{result.explanation}</p>
            {result.source_ids.length > 0 ? <p className="text-xs text-slate-500 mb-1">Sources: {result.source_ids.join(', ')}</p> : null}
            {result.limitations.length > 0 ? <p className="text-xs text-orange-400/70 mb-1">Limitations: {result.limitations.join('; ')}</p> : null}
            <p className="text-xs text-slate-500 italic mt-2">{result.methodology}</p>
          </div>
        </div>
      ) : null}
    </div>
  )
}