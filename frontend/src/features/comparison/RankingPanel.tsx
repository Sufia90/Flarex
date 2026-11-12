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
    <div className="space-y-4 rounded border border-slate-700 bg-slate-900 p-4">
      <h3 className="text-base font-semibold text-white">Evidence-based ranking</h3>
      <p className="text-sm text-slate-300">This ranking measures one documented criterion at a time. It does not say which experiment is best or safest overall, and it uses no weights or combined score.</p>
      <label className="block text-xs text-slate-400">
        Ranking criterion
        <select className="mt-1 w-full rounded border border-slate-600 bg-slate-800 px-2 py-1 text-sm text-white" value={criterion} onChange={(e) => changeCriterion(e.target.value as RankingCriterion)}>
          {criteria.map((c) => (
            <option key={c.value} value={c.value}>{c.label}</option>
          ))}
        </select>
      </label>
      {criterionInfo ? <p className="text-sm text-slate-300">{criterionInfo.description}</p> : null}
      <div className="flex gap-2">
        <button type="button" onClick={() => setMode('all')} className={`rounded border px-3 py-1 text-sm ${mode === 'all' ? 'border-cyan-600 bg-cyan-950 text-cyan-300' : 'border-slate-600 text-slate-300'}`}>All eligible records</button>
        <button type="button" onClick={() => setMode('selected')} className={`rounded border px-3 py-1 text-sm ${mode === 'selected' ? 'border-cyan-600 bg-cyan-950 text-cyan-300' : 'border-slate-600 text-slate-300'}`}>Selected records</button>
      </div>
      {mode === 'selected' ? (
        items.length === 0 ? (
          <EmptyState title="No records to rank" message="No records are loaded yet." />
        ) : (
          <ul className="max-h-64 space-y-1 overflow-auto">
            {items.map((item) => (
              <li key={item.id}>
                <label className="flex items-center gap-2 text-sm text-white">
                  <input type="checkbox" checked={selected.includes(item.id)} onChange={() => toggle(item.id)} />
                  {item.label}
                  <span className="text-xs text-slate-500">{item.id}</span>
                </label>
              </li>
            ))}
          </ul>
        )
      ) : null}
      <label className="block text-xs text-slate-400">
        Result limit
        <input className="mt-1 w-24 rounded border border-slate-600 bg-slate-800 px-2 py-1 text-sm text-white" type="number" min={1} max={50} value={limit} onChange={(e) => setLimit(Number(e.target.value))} />
      </label>
      <button type="button" disabled={createRanking.isPending || (mode === 'selected' && selected.length === 0)} onClick={submit} className="rounded bg-cyan-600 px-3 py-1 text-sm text-white disabled:opacity-50">
        Rank
      </button>
      {createRanking.isPending ? <LoadingState message="Ranking..." /> : null}
      {error ? <ErrorState message={error} onRetry={submit} /> : null}
      {result ? (
        <div className="space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-semibold text-white">{result.title}</span>
            <EvidenceStatusBadge status={result.status} />
          </div>
          <p className="text-sm text-slate-300">{result.question}</p>
          <p className="text-sm text-slate-300">{result.metric_name}: {result.metric_description}</p>
          {result.status === 'insufficient_evidence' ? (
            <p className="text-sm text-slate-400">Insufficient evidence to rank. {result.explanation}</p>
          ) : result.items.length === 0 ? (
            <EmptyState title="No ranked items" message="No items had enough evidence to rank." />
          ) : (
            <ol className="space-y-2">
              {result.items.map((item) => (
                <li key={item.item_id} className="rounded border border-slate-700 p-3">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-semibold text-white">Rank {item.rank === null ? '—' : item.rank}</span>
                    <span className="text-sm text-white">{item.item_name ?? item.item_id}</span>
                    <span className="text-xs text-slate-400">
                      {item.metric_value}{item.metric_max !== null && item.metric_max !== undefined ? ` / ${item.metric_max}` : ''}
                    </span>
                  </div>
                  {item.rank === null ? <p className="mt-1 text-xs text-slate-400">Not ranked — insufficient evidence.</p> : null}
                  <p className="mt-1 text-xs text-slate-400">{item.explanation}</p>
                  <div className="mt-1 flex flex-wrap gap-2">
                    {item.data_completeness ? <EvidenceStatusBadge status={item.data_completeness} /> : null}
                    {item.verification_status ? <EvidenceStatusBadge status={item.verification_status} /> : null}
                    <span className="text-xs text-slate-400">Evidence records: {item.evidence_ids.length}</span>
                  </div>
                  {item.limitations.length > 0 ? <p className="mt-1 text-xs text-slate-400">Limitations: {item.limitations.join('; ')}</p> : null}
                </li>
              ))}
            </ol>
          )}
          <p className="text-sm text-slate-300">{result.explanation}</p>
          {result.source_ids.length > 0 ? <p className="text-xs text-slate-400">Sources: {result.source_ids.join(', ')}</p> : null}
          {result.limitations.length > 0 ? <p className="text-xs text-slate-400">Limitations: {result.limitations.join('; ')}</p> : null}
          <p className="text-xs text-slate-400">{result.methodology}</p>
        </div>
      ) : null}
    </div>
  )
}
