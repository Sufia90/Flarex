import type { ReactNode } from 'react'
import { Link } from 'react-router'
import { EvidenceStatusBadge } from '../../components/common/EvidenceStatusBadge'
import { useHardware } from '../../hooks/useHardware'
import { useRelationshipsByExperiment } from '../../hooks/useRelationships'
import { useMissionRelevanceForExperiment } from '../../hooks/useMissionRelevance'
import { useInsightsForExperiment } from '../../hooks/useFireSafety'
import type { Experiment, Finding, Measurement } from '../../types/experiment'
import type { MissionRelevanceAssessment } from '../../types/mission-relevance'

function Missing() {
  return <span className="text-slate-500">Not documented</span>
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="rounded border border-slate-700 bg-slate-900 p-4">
      <h3 className="mb-3 text-base font-semibold text-white">{title}</h3>
      {children}
    </section>
  )
}

function displayMeasurementValue(value: boolean | number | string | null) {
  if (value === null) return 'Not measured'
  if (typeof value === 'boolean') return value ? 'Yes' : 'No'
  return String(value)
}

function MeasurementRow({ m }: { m: Measurement }) {
  return (
    <li className="rounded border border-slate-700 p-3">
      <p className="font-semibold text-white">{m.parameter_name}</p>
      <p className="text-sm text-slate-300">
        Value: {displayMeasurementValue(m.value)}
        {m.unit ? ` ${m.unit}` : ''}
      </p>
      <p className="text-xs text-slate-400">
        {m.measurement_kind ? `Kind: ${m.measurement_kind}` : 'Kind: unknown'}
        {m.measurement_method ? ` · Method: ${m.measurement_method}` : ''}
        {m.sensor ? ` · Sensor: ${m.sensor}` : ''}
        {m.time_point ? ` · Time: ${m.time_point}` : ''}
      </p>
      <div className="mt-1 flex flex-wrap items-center gap-2">
        {m.verification_status ? <EvidenceStatusBadge status={m.verification_status} /> : null}
        {m.source_id ? <span className="text-xs text-slate-400">Source: {m.source_id}</span> : null}
      </div>
    </li>
  )
}

function FindingRow({ f }: { f: Finding }) {
  return (
    <li className="rounded border border-slate-700 p-3">
      <p className="font-semibold text-white">{f.title}</p>
      <p className="mt-1 text-sm text-slate-300">Observation: {f.observation ? f.observation : 'Not documented'}</p>
      <p className="mt-1 text-sm text-slate-300">Conclusion: {f.conclusion ? f.conclusion : 'Not documented'}</p>
      {f.supporting_evidence.length > 0 ? <p className="mt-1 text-xs text-slate-400">Evidence: {f.supporting_evidence.join('; ')}</p> : null}
      {f.limitations.length > 0 ? <p className="mt-1 text-xs text-slate-400">Limitations: {f.limitations.join('; ')}</p> : null}
      <div className="mt-1 flex flex-wrap items-center gap-2">
        {f.fire_safety_relevance.map((c) => (
          <EvidenceStatusBadge key={c} status={c} />
        ))}
        {f.verification_status ? <EvidenceStatusBadge status={f.verification_status} /> : null}
        {f.source_id ? <span className="text-xs text-slate-400">Source: {f.source_id}</span> : null}
      </div>
    </li>
  )
}

function MissionRow({ experimentId, mission, pending, error, data }: { experimentId: string; mission: string; pending: boolean; error: boolean; data: MissionRelevanceAssessment | undefined }) {
  if (pending) return <p className="text-sm text-slate-400">{mission}: loading...</p>
  if (error || !data) return <p className="text-sm text-slate-400">{mission}: could not load assessment.</p>
  return (
    <div className="rounded border border-slate-700 p-3">
      <div className="flex items-center gap-2">
        <span className="font-semibold text-white">{mission}</span>
        <EvidenceStatusBadge status={data.relevance_level} />
      </div>
      <p className="mt-1 text-sm text-slate-300">{data.explanation}</p>
      {data.transferability_limitations.length > 0 ? <p className="mt-1 text-xs text-slate-400">Transferability limits: {data.transferability_limitations.join('; ')}</p> : null}
      <Link className="text-xs text-cyan-300" to={`/mission-relevance?subject=experiment&id=${encodeURIComponent(experimentId)}&mission=${mission}`}>
        Open mission assessment
      </Link>
    </div>
  )
}

export function ExperimentDetail({ experiment }: { experiment: Experiment }) {
  const hardwareList = useHardware()
  const rels = useRelationshipsByExperiment(experiment.id)
  const iss = useMissionRelevanceForExperiment(experiment.id, 'ISS')
  const moon = useMissionRelevanceForExperiment(experiment.id, 'Moon')
  const mars = useMissionRelevanceForExperiment(experiment.id, 'Mars')
  const insights = useInsightsForExperiment(experiment.id)
  const hardwareById = new Map((hardwareList.data?.items ?? []).map((h) => [h.id, h.name]))
  const c = experiment.conditions
  return (
    <div className="space-y-4">
      <Section title="Overview">
        <p className="text-lg font-semibold text-white">{experiment.name}</p>
        <p className="mt-1 text-sm text-slate-300">{experiment.description ? experiment.description : 'Not documented'}</p>
        <p className="mt-2 text-sm text-slate-300">Objective: {experiment.scientific_objective ? experiment.scientific_objective : 'Not documented'}</p>
        <p className="mt-1 text-xs text-slate-400">
          ID: {experiment.id}
          {experiment.nasa_investigation_id ? ` · NASA ID: ${experiment.nasa_investigation_id}` : ''}
          {experiment.acronym ? ` · ${experiment.acronym}` : ''}
          {experiment.research_category ? ` · Category: ${experiment.research_category}` : ''}
          {experiment.combustion_type ? ` · ${experiment.combustion_type}` : ''}
        </p>
        <div className="mt-2 flex flex-wrap gap-2">
          {experiment.mission_applicability.map((m) => (
            <EvidenceStatusBadge key={m} status={m} />
          ))}
          {experiment.fire_safety_relevance.map((f) => (
            <EvidenceStatusBadge key={f} status={f} />
          ))}
          <EvidenceStatusBadge status={experiment.data_quality.verification_status} />
        </div>
      </Section>
      <Section title="Experimental conditions">
        {!c ? (
          <Missing />
        ) : (
          <dl className="grid grid-cols-1 gap-2 text-sm md:grid-cols-2">
            <div><dt className="text-xs text-slate-400">Fuel</dt><dd className="text-white">{c.fuel_material ?? experiment.fuel_material ?? <Missing />}</dd></div>
            <div><dt className="text-xs text-slate-400">Oxygen</dt><dd className="text-white">{c.oxygen_concentration === null || c.oxygen_concentration === undefined ? <Missing /> : `${c.oxygen_concentration}${c.oxygen_unit ? ` ${c.oxygen_unit}` : ''}${c.oxygen_basis ? ` (${c.oxygen_basis})` : ''}`}</dd></div>
            <div><dt className="text-xs text-slate-400">Pressure</dt><dd className="text-white">{c.ambient_pressure === null || c.ambient_pressure === undefined ? <Missing /> : `${c.ambient_pressure}${c.pressure_unit ? ` ${c.pressure_unit}` : ''}`}</dd></div>
            <div><dt className="text-xs text-slate-400">Temperature</dt><dd className="text-white">{c.temperature === null || c.temperature === undefined ? <Missing /> : `${c.temperature}${c.temperature_unit ? ` ${c.temperature_unit}` : ''}`}</dd></div>
            <div><dt className="text-xs text-slate-400">Airflow</dt><dd className="text-white">{c.airflow_velocity === null || c.airflow_velocity === undefined ? <Missing /> : `${c.airflow_velocity}${c.airflow_unit ? ` ${c.airflow_unit}` : ''}${c.airflow_direction ? ` (${c.airflow_direction})` : ''}`}</dd></div>
            <div><dt className="text-xs text-slate-400">Gravity condition</dt><dd className="text-white">{c.gravity_condition ? c.gravity_condition : <Missing />}</dd></div>
            <div><dt className="text-xs text-slate-400">Sample geometry</dt><dd className="text-white">{c.sample_geometry ?? experiment.sample_geometry ?? <Missing />}</dd></div>
            <div><dt className="text-xs text-slate-400">Sample dimensions</dt><dd className="text-white">{c.sample_dimensions ?? experiment.sample_dimensions ?? <Missing />}</dd></div>
          </dl>
        )}
        {c && c.other_conditions && Object.keys(c.other_conditions).length > 0 ? (
          <ul className="mt-2 space-y-1 text-sm text-slate-300">
            {Object.entries(c.other_conditions).map(([k, v]) => (
              <li key={k}>{k}: {String(v)}</li>
            ))}
          </ul>
        ) : null}
      </Section>
      <Section title="Measurements">
        {experiment.measurements.length === 0 ? (
          <p className="text-sm text-slate-500">No measurements documented yet.</p>
        ) : (
          <ul className="space-y-2">
            {experiment.measurements.map((m) => (
              <MeasurementRow key={m.id} m={m} />
            ))}
          </ul>
        )}
      </Section>
      <Section title="Findings">
        {experiment.findings.length === 0 ? (
          <p className="text-sm text-slate-500">No findings documented yet.</p>
        ) : (
          <ul className="space-y-2">
            {experiment.findings.map((f) => (
              <FindingRow key={f.id} f={f} />
            ))}
          </ul>
        )}
      </Section>
      <Section title="Hardware">
        {rels.isPending ? (
          <p className="text-sm text-slate-400">Loading relationships...</p>
        ) : (rels.data ?? []).length === 0 ? (
          <p className="text-sm text-slate-500">No linked hardware yet.</p>
        ) : (
          <ul className="space-y-1">
            {(rels.data ?? []).map((r) => (
              <li key={r.id} className="text-sm text-white">
                <Link className="text-cyan-300" to={`/hardware?id=${encodeURIComponent(r.hardware_id)}`}>
                  {hardwareById.get(r.hardware_id) ?? r.hardware_id}
                </Link>
                <span className="text-slate-400"> · {r.relationship_type}</span>
              </li>
            ))}
          </ul>
        )}
      </Section>
      <Section title="Mission relevance">
        <div className="space-y-2">
          <MissionRow experimentId={experiment.id} mission="ISS" pending={iss.isPending} error={iss.isError} data={iss.data} />
          <MissionRow experimentId={experiment.id} mission="Moon" pending={moon.isPending} error={moon.isError} data={moon.data} />
          <MissionRow experimentId={experiment.id} mission="Mars" pending={mars.isPending} error={mars.isError} data={mars.data} />
        </div>
      </Section>
      <Section title="Fire safety relevance">
        {insights.isPending ? (
          <p className="text-sm text-slate-400">Loading insights...</p>
        ) : (insights.data ?? []).length === 0 ? (
          <p className="text-sm text-slate-500">No fire safety insights for this experiment yet.</p>
        ) : (
          <ul className="space-y-2">
            {(insights.data ?? []).map((i) => (
              <li key={i.insight_id} className="flex flex-wrap items-center gap-2 rounded border border-slate-700 p-3 text-sm text-white">
                <EvidenceStatusBadge status={i.category} />
                <EvidenceStatusBadge status={i.evidence_status} />
                <span className="text-slate-400">{i.experiment_name ?? i.experiment_id ?? ''}</span>
              </li>
            ))}
          </ul>
        )}
      </Section>
    </div>
  )
}
