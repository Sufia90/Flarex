import type { ReactNode } from 'react'
import { Link } from 'react-router'
import { EvidenceStatusBadge } from '../../components/common/EvidenceStatusBadge'
import { useMissionRelevanceForExperiment } from '../../hooks/useMissionRelevance'
import { useInsightsForExperiment } from '../../hooks/useFireSafety'
import type { Experiment, Finding, Measurement } from '../../types/experiment'
import type { MissionRelevanceAssessment } from '../../types/mission-relevance'

function Missing() {
  return <span className="text-slate-500 italic">Not documented</span>
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="rounded-2xl border border-white/10 bg-[#0A1628] p-5 shadow-lg shadow-black/10">
      <h3 className="mb-4 text-sm font-bold text-cyan-400 uppercase tracking-widest flex items-center gap-2">
        <span className="w-1.5 h-1.5 rounded-full bg-cyan-500 shadow-[0_0_8px_#22d3ee]"></span>
        {title}
      </h3>
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
    <li className="rounded-xl border border-white/5 bg-[#040B14] p-4 hover:border-white/10 transition-colors">
      <p className="font-semibold text-white text-base">{m.parameter_name}</p>
      <p className="text-sm text-cyan-300 font-mono mt-1">
        {displayMeasurementValue(m.value)} {m.unit ? ` ${m.unit}` : ''}
      </p>
      <div className="mt-2 text-[11px] text-slate-400 flex flex-wrap gap-x-3 gap-y-1">
        <span>Kind: {m.measurement_kind ?? 'unknown'}</span>
        {m.measurement_method && <span>Method: {m.measurement_method}</span>}
        {m.sensor && <span>Sensor: {m.sensor}</span>}
        {m.time_point && <span>Time: {m.time_point}</span>}
      </div>
      <div className="mt-3 flex flex-wrap items-center gap-2 border-t border-white/5 pt-3">
        {m.verification_status ? <EvidenceStatusBadge status={m.verification_status} /> : null}
        {m.source_id ? <span className="text-[10px] uppercase tracking-wider text-slate-500 bg-white/5 px-2 py-1 rounded-md font-mono">Source: {m.source_id}</span> : null}
      </div>
    </li>
  )
}

function FindingRow({ f }: { f: Finding }) {
  return (
    <li className="rounded-xl border border-white/5 bg-[#040B14] p-4 hover:border-white/10 transition-colors">
      <p className="font-semibold text-white text-base mb-2">{f.title}</p>
      
      <div className="space-y-2 text-sm text-slate-300">
        <p><span className="text-slate-500 font-medium">Observation:</span> {f.observation ? f.observation : <Missing />}</p>
        <p><span className="text-slate-500 font-medium">Conclusion:</span> {f.conclusion ? f.conclusion : <Missing />}</p>
      </div>
      
      {f.supporting_evidence.length > 0 ? (
        <p className="mt-2 text-xs text-indigo-300 bg-indigo-500/10 p-2 rounded border border-indigo-500/20">Evidence: {f.supporting_evidence.join('; ')}</p>
      ) : null}
      {f.limitations.length > 0 ? (
        <p className="mt-2 text-xs text-orange-400/80 bg-orange-500/10 p-2 rounded border border-orange-500/20">Limitations: {f.limitations.join('; ')}</p>
      ) : null}
      
      <div className="mt-3 flex flex-wrap items-center gap-2 border-t border-white/5 pt-3">
        {f.fire_safety_relevance.map((c) => (
          <EvidenceStatusBadge key={c} status={c} />
        ))}
        {f.verification_status ? <EvidenceStatusBadge status={f.verification_status} /> : null}
        {f.source_id ? <span className="text-[10px] uppercase tracking-wider text-slate-500 bg-white/5 px-2 py-1 rounded-md font-mono">Source: {f.source_id}</span> : null}
      </div>
    </li>
  )
}

function MissionRow({ experimentId, mission, pending, error, data }: { experimentId: string; mission: string; pending: boolean; error: boolean; data: MissionRelevanceAssessment | undefined }) {
  if (pending) return <div className="p-3 rounded-xl bg-[#040B14] border border-white/5 text-sm text-slate-400 animate-pulse">{mission}: Loading...</div>
  if (error || !data) return <div className="p-3 rounded-xl bg-[#040B14] border border-white/5 text-sm text-red-400">{mission}: Could not load assessment.</div>
  
  return (
    <div className="rounded-xl border border-white/5 bg-[#040B14] p-4 flex flex-col sm:flex-row sm:items-start justify-between gap-3 hover:border-blue-500/30 transition-colors">
      <div className="flex-1">
        <div className="flex items-center gap-2 mb-1">
          <span className="font-semibold text-white">{mission} Mission</span>
          <EvidenceStatusBadge status={data.relevance_level} />
        </div>
        <p className="text-sm text-slate-300">{data.explanation}</p>
        {data.transferability_limitations.length > 0 ? (
          <p className="mt-2 text-[11px] text-orange-400/80">Transferability limits: {data.transferability_limitations.join('; ')}</p>
        ) : null}
      </div>
      <Link 
        className="whitespace-nowrap inline-flex items-center gap-1 text-xs font-semibold text-blue-400 hover:text-blue-300 bg-blue-500/10 px-3 py-1.5 rounded-lg border border-blue-500/20 transition-all" 
        to={`/mission-relevance?subject=experiment&id=${encodeURIComponent(experimentId)}&mission=${mission}`}
      >
        Open assessment
        <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" /></svg>
      </Link>
    </div>
  )
}

export function ExperimentDetail({ experiment }: { experiment: Experiment }) {
  const iss = useMissionRelevanceForExperiment(experiment.id, 'ISS')
  const moon = useMissionRelevanceForExperiment(experiment.id, 'Moon')
  const mars = useMissionRelevanceForExperiment(experiment.id, 'Mars')
  const insights = useInsightsForExperiment(experiment.id)
  const c = experiment.conditions
  
  return (
    <div className="space-y-6 p-2">
      
      {/* Overview Section */}
      <Section title="Experiment Overview">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
          <div className="flex-1">
            <p className="text-2xl font-bold text-white tracking-wide">{experiment.name}</p>
            <p className="mt-2 text-sm text-slate-300 leading-relaxed">{experiment.description ? experiment.description : <Missing />}</p>
            <div className="mt-4 p-3 rounded-lg bg-white/5 border border-white/5">
              <p className="text-sm text-slate-300"><span className="font-semibold text-cyan-400">Objective:</span> {experiment.scientific_objective ? experiment.scientific_objective : <Missing />}</p>
            </div>
          </div>
          
          <div className="flex flex-wrap gap-2 md:flex-col md:items-end md:max-w-[200px]">
             {experiment.mission_applicability.map((m) => (
              <EvidenceStatusBadge key={m} status={m} />
            ))}
            {experiment.fire_safety_relevance.map((f) => (
              <EvidenceStatusBadge key={f} status={f} />
            ))}
            <EvidenceStatusBadge status={experiment.data_quality.verification_status} />
          </div>
        </div>
        
        <div className="mt-5 pt-4 border-t border-white/10 flex flex-wrap gap-2">
          <span className="text-[10px] uppercase tracking-wider text-slate-400 bg-white/5 px-2.5 py-1 rounded-md font-mono">ID: {experiment.id}</span>
          {experiment.nasa_investigation_id && <span className="text-[10px] uppercase tracking-wider text-cyan-400/80 bg-cyan-500/10 px-2.5 py-1 rounded-md font-mono border border-cyan-500/20">NASA ID: {experiment.nasa_investigation_id}</span>}
          {experiment.acronym && <span className="text-[10px] uppercase tracking-wider text-slate-400 bg-white/5 px-2.5 py-1 rounded-md font-mono">{experiment.acronym}</span>}
          {experiment.research_category && <span className="text-[10px] uppercase tracking-wider text-indigo-400/80 bg-indigo-500/10 px-2.5 py-1 rounded-md border border-indigo-500/20">Category: {experiment.research_category}</span>}
          {experiment.combustion_type && <span className="text-[10px] uppercase tracking-wider text-orange-400/80 bg-orange-500/10 px-2.5 py-1 rounded-md border border-orange-500/20">{experiment.combustion_type}</span>}
        </div>
      </Section>

      {/* Conditions Section */}
      <Section title="Experimental Conditions">
        {!c ? (
          <Missing />
        ) : (
          <dl className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            <div className="bg-[#040B14] p-3 rounded-lg border border-white/5"><dt className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Fuel</dt><dd className="text-sm font-medium text-white">{c.fuel_material ?? experiment.fuel_material ?? <Missing />}</dd></div>
            <div className="bg-[#040B14] p-3 rounded-lg border border-white/5"><dt className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Oxygen</dt><dd className="text-sm font-medium text-white">{c.oxygen_concentration === null || c.oxygen_concentration === undefined ? <Missing /> : `${c.oxygen_concentration}${c.oxygen_unit ? ` ${c.oxygen_unit}` : ''}${c.oxygen_basis ? ` (${c.oxygen_basis})` : ''}`}</dd></div>
            <div className="bg-[#040B14] p-3 rounded-lg border border-white/5"><dt className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Pressure</dt><dd className="text-sm font-medium text-white">{c.ambient_pressure === null || c.ambient_pressure === undefined ? <Missing /> : `${c.ambient_pressure}${c.pressure_unit ? ` ${c.pressure_unit}` : ''}`}</dd></div>
            <div className="bg-[#040B14] p-3 rounded-lg border border-white/5"><dt className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Temperature</dt><dd className="text-sm font-medium text-white">{c.temperature === null || c.temperature === undefined ? <Missing /> : `${c.temperature}${c.temperature_unit ? ` ${c.temperature_unit}` : ''}`}</dd></div>
            <div className="bg-[#040B14] p-3 rounded-lg border border-white/5"><dt className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Airflow</dt><dd className="text-sm font-medium text-white">{c.airflow_velocity === null || c.airflow_velocity === undefined ? <Missing /> : `${c.airflow_velocity}${c.airflow_unit ? ` ${c.airflow_unit}` : ''}${c.airflow_direction ? ` (${c.airflow_direction})` : ''}`}</dd></div>
            <div className="bg-[#040B14] p-3 rounded-lg border border-white/5"><dt className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Gravity</dt><dd className="text-sm font-medium text-white">{c.gravity_condition ? c.gravity_condition : <Missing />}</dd></div>
            <div className="bg-[#040B14] p-3 rounded-lg border border-white/5"><dt className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Sample Geometry</dt><dd className="text-sm font-medium text-white">{c.sample_geometry ?? experiment.sample_geometry ?? <Missing />}</dd></div>
            <div className="bg-[#040B14] p-3 rounded-lg border border-white/5"><dt className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Sample Dimensions</dt><dd className="text-sm font-medium text-white">{c.sample_dimensions ?? experiment.sample_dimensions ?? <Missing />}</dd></div>
          </dl>
        )}
        {c && c.other_conditions && Object.keys(c.other_conditions).length > 0 ? (
          <div className="mt-3 pt-3 border-t border-white/10">
            <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-2">Other Conditions</p>
            <ul className="space-y-1 text-sm text-slate-300">
              {Object.entries(c.other_conditions).map(([k, v]) => (
                <li key={k} className="flex gap-2"><span className="text-slate-500">{k}:</span> <span className="font-mono text-cyan-300">{String(v)}</span></li>
              ))}
            </ul>
          </div>
        ) : null}
      </Section>

      {/* Measurements Section */}
      <Section title="Measurements">
        {experiment.measurements.length === 0 ? (
          <p className="text-sm text-slate-500 italic">No measurements documented yet.</p>
        ) : (
          <ul className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {experiment.measurements.map((m) => (
              <MeasurementRow key={m.id} m={m} />
            ))}
          </ul>
        )}
      </Section>

      {/* Findings Section */}
      <Section title="Findings">
        {experiment.findings.length === 0 ? (
          <p className="text-sm text-slate-500 italic">No findings documented yet.</p>
        ) : (
          <ul className="space-y-3">
            {experiment.findings.map((f) => (
              <FindingRow key={f.id} f={f} />
            ))}
          </ul>
        )}
      </Section>

      {/* Mission Relevance Section */}
      <Section title="Mission Relevance">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
          <MissionRow experimentId={experiment.id} mission="ISS" pending={iss.isPending} error={iss.isError} data={iss.data} />
          <MissionRow experimentId={experiment.id} mission="Moon" pending={moon.isPending} error={moon.isError} data={moon.data} />
          <MissionRow experimentId={experiment.id} mission="Mars" pending={mars.isPending} error={mars.isError} data={mars.data} />
        </div>
      </Section>

      {/* Fire Safety Relevance Section */}
      <Section title="Fire Safety Relevance">
        {insights.isPending ? (
          <p className="text-sm text-slate-400 animate-pulse">Loading insights...</p>
        ) : (insights.data ?? []).length === 0 ? (
          <p className="text-sm text-slate-500 italic">No fire safety insights for this experiment yet.</p>
        ) : (
          <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {(insights.data ?? []).map((i) => (
              <li key={i.insight_id} className="flex flex-wrap items-center gap-2 rounded-lg border border-white/5 bg-[#040B14] p-3 text-sm text-white hover:border-white/10 transition-colors">
                <EvidenceStatusBadge status={i.category} />
                <EvidenceStatusBadge status={i.evidence_status} />
                <span className="text-slate-500 text-xs ml-auto">{i.experiment_name ?? i.experiment_id ?? ''}</span>
              </li>
            ))}
          </ul>
        )}
      </Section>
      
    </div>
  )
}