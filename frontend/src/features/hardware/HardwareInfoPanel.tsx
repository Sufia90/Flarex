import type { ReactNode } from 'react'
import { Link } from 'react-router'
import type { Experiment } from '../../types/experiment'
import type { Hardware } from '../../types/hardware'
import type { ExperimentHardwareRelationship } from '../../types/relationship'

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div>
      <p className="text-xs text-slate-400">{label}</p>
      <div className="mt-1 text-sm text-white">{children}</div>
    </div>
  )
}

function Missing() {
  return <span className="text-slate-500">Not documented</span>
}

export function HardwareInfoPanel({ hardware, experiments, relationships }: { hardware: Hardware; experiments: Experiment[]; relationships: ExperimentHardwareRelationship[] }) {
  const nameById = new Map(experiments.map((e) => [e.id, e.name]))
  return (
    <div className="space-y-4 rounded border border-slate-700 bg-slate-900 p-4">
      <div>
        <h2 className="text-lg font-semibold text-white">{hardware.name}</h2>
        <p className="text-sm text-slate-400">
          {hardware.acronym ? `${hardware.acronym} · ` : ''}{hardware.hardware_type}
          {hardware.facility_classification ? ` · ${hardware.facility_classification}` : ''}
        </p>
      </div>
      <Field label="Description">{hardware.description ? hardware.description : <Missing />}</Field>
      <Field label="Purpose">{hardware.purpose ? hardware.purpose : <Missing />}</Field>
      <Field label="Supported measurements">
        {hardware.supported_measurements.length > 0 ? (
          <ul className="list-disc pl-5">
            {hardware.supported_measurements.map((m) => (
              <li key={m}>{m}</li>
            ))}
          </ul>
        ) : (
          <Missing />
        )}
      </Field>
      <Field label="Parent hardware">{hardware.parent_hardware_id ? hardware.parent_hardware_id : <Missing />}</Field>
      <Field label="Limitations">{hardware.limitations ? hardware.limitations : <Missing />}</Field>
      <Field label="Source references">
        {hardware.source_ids.length > 0 ? hardware.source_ids.join(', ') : <Missing />}
      </Field>
      <Field label="Image references">
        {hardware.image_ids.length > 0 ? hardware.image_ids.join(', ') : <Missing />}
      </Field>
      <Field label="Diagram references">
        {hardware.diagram_ids.length > 0 ? hardware.diagram_ids.join(', ') : <Missing />}
      </Field>
      <div>
        <p className="text-xs text-slate-400">Related experiments</p>
        {relationships.length === 0 ? (
          <p className="mt-1 text-sm text-slate-500">No linked experiments yet.</p>
        ) : (
          <ul className="mt-1 space-y-1">
            {relationships.map((r) => (
              <li key={r.id} className="text-sm text-white">
                <Link className="text-cyan-300" to={`/experiments?id=${encodeURIComponent(r.experiment_id)}`}>
                  {nameById.get(r.experiment_id) ?? r.experiment_id}
                </Link>
                <span className="text-slate-400"> · {r.relationship_type}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
