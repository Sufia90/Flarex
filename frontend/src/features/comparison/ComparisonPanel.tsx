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
    <ul className="space-y-2">
      {parameters.map((p) => (
        <li key={p.parameter_name} className="rounded border border-slate-700 p-3">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-semibold text-white">{p.parameter_name}</span>
            <EvidenceStatusBadge status={p.status} />
            <span className="text-xs text-slate-400">{p.category}</span>
          </div>
          <p className="mt-1 text-sm text-slate-300">{p.reason}</p>
          <ul className="mt-1 space-y-1 text-xs text-slate-400">
            {p.values.map((v) => (
              <li key={v.item_id}>
                {v.item_id}: {v.value === null ? 'Not measured' : String(v.value)}{v.unit ? ` ${v.unit}` : ''}
                {v.missing_reason ? ` (${v.missing_reason})` : ''}
              </li>
            ))}
          </ul>
          {p.conditions_note ? <p className="mt-1 text-xs text-slate-400">{p.conditions_note}</p> : null}
        </li>
      ))}
    </ul>
  )
}

function ListBlock({ title, items }: { title: string; items: string[] }) {
  if (items.length === 0) return null
  return (
    <div>
      <p className="text-xs text-slate-400">{title}</p>
      <ul className="mt-1 list-disc space-y-1 pl-5 text-sm text-slate-300">
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
  const items =
    kind === 'experiments'
      ? experimentItems.map((e) => ({ id: e.id, label: e.name }))
      : measurementItems
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
    <div className="space-y-4 rounded border border-slate-700 bg-slate-900 p-4">
      <h3 className="text-base font-semibold text-white">Compare</h3>
      <div className="flex gap-2">
        <button type="button" onClick={() => changeKind('experiments')} className={`rounded border px-3 py-1 text-sm ${kind === 'experiments' ? 'border-cyan-600 bg-cyan-950 text-cyan-300' : 'border-slate-600 text-slate-300'}`}>Experiments</button>
        <button type="button" onClick={() => changeKind('measurements')} className={`rounded border px-3 py-1 text-sm ${kind === 'measurements' ? 'border-cyan-600 bg-cyan-950 text-cyan-300' : 'border-slate-600 text-slate-300'}`}>Measurements</button>
      </div>
      {items.length === 0 ? (
        <EmptyState title="No records to compare" message="No records are loaded yet. Comparison needs at least 2 records." />
      ) : (
        <div>
          <p className="text-xs text-slate-400">Select 2 to 10 items. Selected: {selected.length}</p>
          <ul className="mt-2 max-h-64 space-y-1 overflow-auto">
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
          <button type="button" disabled={selected.length < 2 || pending} onClick={submit} className="mt-3 rounded bg-cyan-600 px-3 py-1 text-sm text-white disabled:opacity-50">
            Compare selected
          </button>
        </div>
      )}
      {pending ? <LoadingState message="Comparing..." /> : null}
      {error ? <ErrorState message={error} onRetry={submit} /> : null}
      {result ? (
        <div className="space-y-3">
          <p className="text-sm text-slate-300">Comparison: {result.comparison_id ?? 'n/a'} · {result.category}</p>
          <p className="text-sm text-slate-300">{result.explanation}</p>
          {'parameters' in result ? <ParameterRows parameters={result.parameters} /> : null}
          {'conditions' in result && result.conditions.length > 0 ? (
            <div>
              <p className="text-xs text-slate-400">Conditions</p>
              <ul className="mt-1 space-y-1 text-sm text-slate-300">
                {result.conditions.map((c) => (
                  <li key={c.condition_name}>{c.condition_name}: {c.status} — {c.reason}</li>
                ))}
              </ul>
            </div>
          ) : null}
          <ListBlock title="Similarities" items={result.similarities} />
          <ListBlock title="Differences" items={result.differences} />
          <ListBlock title="Missing information" items={result.missing_information} />
          {'incompatible_items' in result ? <ListBlock title="Incompatible items" items={result.incompatible_items} /> : null}
          <ListBlock title="Source references" items={result.source_ids} />
          <ListBlock title="Limitations" items={result.limitations} />
          <p className="text-xs text-slate-400">{result.methodology}</p>
        </div>
      ) : null}
    </div>
  )
}
