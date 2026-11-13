import { useState } from 'react'
import { EvidenceStatusBadge } from '../../components/common/EvidenceStatusBadge'
import { LoadingState } from '../../components/feedback/LoadingState'
import { ErrorState } from '../../components/feedback/ErrorState'
import { EmptyState } from '../../components/feedback/EmptyState'
import { useExperiments } from '../../hooks/useExperiments'
import { useCompareExperiments, useCompareMeasurements } from '../../hooks/useComparisons'
import type { ExperimentComparison, MeasurementComparison, ParameterComparison } from '../../types/comparison'

type ComparisonType = 'experiments' | 'measurements'
type ComparisonResult = ExperimentComparison | MeasurementComparison

function ParameterRows({ parameters }: { parameters: ParameterComparison[] }) {
  if (parameters.length === 0) return <p className="text-sm text-slate-500">No parameters compared.</p>
  return (
    <ul className="space-y-3 mt-4">
      {parameters.map((p) => (
        <li key={p.parameter_name} className="rounded-xl border border-white/5 bg-[#040B14] p-4">
          <div className="flex flex-wrap items-center gap-3 mb-2">
            <span className="font-semibold text-cyan-300">{p.parameter_name}</span>
            <EvidenceStatusBadge status={p.status} />
            <span className="text-[10px] uppercase tracking-wider text-slate-500 bg-white/5 px-2 py-1 rounded-md">{p.category}</span>
          </div>
          <p className="text-sm text-slate-300 mb-3">{p.reason}</p>
          <ul className="space-y-1.5 text-xs text-slate-400">
            {p.values.map((v) => (
              <li key={v.item_id} className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-slate-600"></span>
                <span className="text-slate-300">{v.item_id}:</span> 
                {v.value === null ? <span className="text-red-400">Not measured</span> : <span className="text-white font-mono">{String(v.value)} {v.unit}</span>}
                {v.missing_reason ? <span className="text-slate-500 italic">({v.missing_reason})</span> : ''}
              </li>
            ))}
          </ul>
          {p.conditions_note ? <p className="mt-3 text-xs text-slate-500 border-t border-white/5 pt-2">{p.conditions_note}</p> : null}
        </li>
      ))}
    </ul>
  )
}

function ListBlock({ title, items }: { title: string; items: string[] }) {
  if (items.length === 0) return null
  return (
    <div className="mt-4">
      <p className="text-xs font-semibold text-cyan-400 uppercase tracking-wider mb-2">{title}</p>
      <ul className="list-disc space-y-1 pl-5 text-sm text-slate-300">
        {items.map((i) => (
          <li key={i}>{i}</li>
        ))}
      </ul>
    </div>
  )
}

export function ComparisonPanel() {
  const [kind, setKind] = useState<ComparisonType>('experiments')
  const [selected, setSelected] = useState<string[]>([])
  const [result, setResult] = useState<ComparisonResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const experiments = useExperiments()
  const compareExperiments = useCompareExperiments()
  const compareMeasurements = useCompareMeasurements()
  const experimentItems = experiments.data?.items ?? []
  const measurementItems = experimentItems.flatMap((e) =>
    e.measurements.map((m) => ({ id: m.id, label: `${e.name} — ${m.parameter_name}` })),
  )
  const items = kind === 'experiments' ? experimentItems.map((e) => ({ id: e.id, label: e.name })) : measurementItems
  const pending = compareExperiments.isPending || compareMeasurements.isPending

  function toggle(id: string) {
    setError(null)
    if (selected.includes(id)) {
      setSelected(selected.filter((s) => s !== id))
    } else if (selected.length < 10) {
      setSelected([...selected, id])
    }
  }

  async function submit() {
    setError(null)
    setResult(null)
    try {
      if (kind === 'experiments') {
        setResult(await compareExperiments.mutateAsync({ experiment_ids: selected, parameters: null, include_conditions: true }))
      } else {
        setResult(await compareMeasurements.mutateAsync({ measurement_ids: selected, parameter_names: null }))
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Comparison failed.')
    }
  }

  function changeKind(next: ComparisonType) {
    setKind(next)
    setSelected([])
    setResult(null)
    setError(null)
  }

  if (experiments.isPending) return <LoadingState message="Loading records..." />
  return (
    <div className="space-y-6">
      {/* Header and Tabs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/10 pb-4">
        <h3 className="text-lg font-semibold text-white tracking-wide">Data Comparison</h3>
        <div className="flex p-1 bg-[#040B14] rounded-lg border border-white/5">
          <button type="button" onClick={() => changeKind('experiments')} className={`rounded-md px-4 py-1.5 text-sm font-medium transition-all ${kind === 'experiments' ? 'bg-cyan-500/20 text-cyan-300 shadow-sm' : 'text-slate-400 hover:text-white'}`}>Experiments</button>
          <button type="button" onClick={() => changeKind('measurements')} className={`rounded-md px-4 py-1.5 text-sm font-medium transition-all ${kind === 'measurements' ? 'bg-cyan-500/20 text-cyan-300 shadow-sm' : 'text-slate-400 hover:text-white'}`}>Measurements</button>
        </div>
      </div>

      {/* Selection Area */}
      {items.length === 0 ? (
        <EmptyState title="No records to compare" message="No records are loaded yet. Comparison needs at least 2 records." />
      ) : (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">Select 2 to 10 items</p>
            <span className="px-2 py-1 rounded-md bg-cyan-500/10 text-cyan-400 text-xs font-bold border border-cyan-500/20">Selected: {selected.length}</span>
          </div>
          
          <ul className="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-64 overflow-auto p-1 custom-scrollbar">
            {items.map((item) => (
              <li key={item.id}>
                <label className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-all ${selected.includes(item.id) ? 'bg-cyan-500/10 border-cyan-500/30' : 'bg-[#040B14] border-white/5 hover:border-white/20'}`}>
                  <input type="checkbox" checked={selected.includes(item.id)} onChange={() => toggle(item.id)} className="mt-1 w-4 h-4 rounded border-white/20 bg-[#040B14] text-cyan-500 focus:ring-cyan-500 focus:ring-offset-[#040B14]" />
                  <div>
                    <span className="block text-sm font-medium text-white">{item.label}</span>
                    <span className="block text-[10px] text-slate-500 font-mono mt-0.5">{item.id}</span>
                  </div>
                </label>
              </li>
            ))}
          </ul>
          
          <button type="button" disabled={selected.length < 2 || pending} onClick={submit} className="w-full sm:w-auto rounded-lg bg-cyan-600 px-6 py-2.5 text-sm font-bold text-white transition-all hover:bg-cyan-500 hover:shadow-[0_0_15px_rgba(34,211,238,0.4)] disabled:opacity-50 disabled:hover:bg-cyan-600 disabled:hover:shadow-none">
            Compare Selected
          </button>
        </div>
      )}

      {pending ? <LoadingState message="Comparing..." /> : null}
      {error ? <ErrorState message={error} onRetry={submit} /> : null}

      {/* Results Area */}
      {result ? (
        <div className="mt-8 rounded-xl bg-[#040B14] border border-white/5 p-5">
          <div className="flex flex-wrap items-center gap-3 mb-4 border-b border-white/5 pb-4">
            <h4 className="text-white font-semibold">Comparison Result</h4>
            <span className="text-xs text-slate-500 font-mono">ID: {result.comparison_id ?? 'n/a'}</span>
            <EvidenceStatusBadge status={result.category} />
          </div>
          
          <p className="text-sm text-slate-300 mb-4">{result.explanation}</p>
          
          {'parameters' in result ? <ParameterRows parameters={result.parameters} /> : null}
          
          {'conditions' in result && result.conditions.length > 0 ? (
            <div className="mt-6">
              <p className="text-xs font-semibold text-cyan-400 uppercase tracking-wider mb-2">Conditions</p>
              <ul className="space-y-2 text-sm text-slate-300">
                {result.conditions.map((c) => (
                  <li key={c.condition_name} className="flex gap-2 items-center bg-white/5 p-2 rounded-md">
                    <span className="font-medium text-white">{c.condition_name}:</span> 
                    <EvidenceStatusBadge status={c.status} />
                    <span className="text-slate-400">— {c.reason}</span>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6">
            <div>
              <ListBlock title="Similarities" items={result.similarities} />
              <ListBlock title="Missing information" items={result.missing_information} />
            </div>
            <div>
              <ListBlock title="Differences" items={result.differences} />
              {'incompatible_items' in result ? <ListBlock title="Incompatible items" items={result.incompatible_items} /> : null}
            </div>
          </div>
          
          <div className="mt-6 pt-4 border-t border-white/5">
            <ListBlock title="Source references" items={result.source_ids} />
            <ListBlock title="Limitations" items={result.limitations} />
            <p className="text-xs text-slate-500 mt-4 italic">{result.methodology}</p>
          </div>
        </div>
      ) : null}
    </div>
  )
}