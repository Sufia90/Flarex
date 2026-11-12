import { lazy, Suspense } from 'react'
import { useSearchParams } from 'react-router'
import { LoadingState } from '../components/feedback/LoadingState'
import { ErrorState } from '../components/feedback/ErrorState'
import { EmptyState } from '../components/feedback/EmptyState'
import { HardwareInfoPanel } from '../features/hardware/HardwareInfoPanel'
import { useHardware } from '../hooks/useHardware'
import { useExperiments } from '../hooks/useExperiments'
import { useRelationshipsByHardware } from '../hooks/useRelationships'
import type { Experiment } from '../types/experiment'
import type { Hardware } from '../types/hardware'

const HardwareViewport = lazy(() => import('../features/hardware/HardwareViewport').then((m) => ({ default: m.HardwareViewport })))

function HardwareDetail({ hardware, experiments }: { hardware: Hardware; experiments: Experiment[] }) {
  const relationships = useRelationshipsByHardware(hardware.id)
  if (relationships.isPending) return <LoadingState message="Loading linked experiments..." />
  return <HardwareInfoPanel hardware={hardware} experiments={experiments} relationships={relationships.data ?? []} />
}

export function HardwareExplorerPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const hardware = useHardware()
  const experiments = useExperiments()
  const items = hardware.data?.items ?? []
  const selectedId = searchParams.get('id') ?? items[0]?.id ?? null
  const selected = items.find((h) => h.id === selectedId) ?? null

  if (hardware.isPending || experiments.isPending) return <LoadingState message="Loading hardware..." />
  if (hardware.isError) return <ErrorState message="Could not load hardware." onRetry={() => hardware.refetch()} />
  if (items.length === 0) return <EmptyState title="No hardware records yet" message="No hardware records are loaded. Real NASA hardware records will appear here when they are added." />
  return (
    <div className="grid gap-6 md:grid-cols-[280px_1fr]">
      <div>
        <h2 className="text-base font-semibold text-white">Hardware</h2>
        <ul className="mt-2 space-y-1">
          {items.map((h) => (
            <li key={h.id}>
              <button type="button" onClick={() => setSearchParams({ id: h.id })} className={`w-full rounded border px-3 py-2 text-left text-sm ${h.id === selected?.id ? 'border-cyan-600 bg-cyan-950 text-cyan-300' : 'border-slate-700 text-slate-300'}`}>
                {h.name} <span className="text-xs text-slate-500">{h.hardware_type}{h.acronym ? ` · ${h.acronym}` : ''}</span>
              </button>
            </li>
          ))}
        </ul>
      </div>
      <div className="space-y-4">
        {selected ? (
          <>
            <Suspense fallback={<LoadingState message="Loading 3D view..." />}>
              <HardwareViewport hardware={selected} onSelect={() => {}} />
            </Suspense>
            <HardwareDetail hardware={selected} experiments={experiments.data?.items ?? []} />
          </>
        ) : (
          <EmptyState title="Select a hardware record" message="Choose a hardware record from the list to see its illustrative 3D view and details." />
        )}
      </div>
    </div>
  )
}
