import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '../api/client'
import { endpoints } from '../api/endpoints'
import { LoadingState } from '../components/feedback/LoadingState'
import { ErrorState } from '../components/feedback/ErrorState'

interface PredictionValue {
  value: number
  unit: string
  confidence_pct: number
  shown_as: string
}

interface NearestTest {
  test: string
  fuel_raw: string
  initial_o2: number | null
  final_o2: number | null
  final_co: number | null
  final_co2: number | null
}

interface PredictResponse {
  regime: string
  regime_basis: string
  predictions: Record<string, PredictionValue>
  explanation: {
    finding: string
    finding_source: string
    nearest_tests_above_19pct_o2: NearestTest[]
    nearest_tests_below_19pct_o2: NearestTest[]
    model: string
    metrics: Record<string, { mae: number; r2: number }>
  }
  warnings: string[]
}

interface ModelInfo {
  model: string
  materials: string[]
  forms: string[]
  targets: Record<string, { mae: number; r2: number }>
  regime_rule: string
  confidence_rule: string
  training_rows: number
  training_source: string
}

const TARGET_LABELS: Record<string, string> = {
  final_o2: 'Final O2',
  final_co: 'Final CO',
  final_co2: 'Final CO2',
}

function formatMetric(value: number): string {
  return value.toFixed(2)
}

function PredictionCard({ label, prediction }: { label: string; prediction: PredictionValue | undefined }) {
  return (
    <div className="rounded-xl border border-white/10 bg-[#040B14] p-4">
      <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">{label}</p>
      {prediction === undefined ? (
        <p className="text-sm text-slate-500 mt-3">Not returned by the model.</p>
      ) : (
        <div className="mt-3">
          <p className="text-2xl font-bold text-white">
            {prediction.value} <span className="text-sm font-medium text-slate-400">{prediction.unit}</span>
          </p>
          <div className="flex flex-wrap items-center gap-2 mt-3">
            <span className="text-[10px] font-bold uppercase tracking-wider text-cyan-300 bg-cyan-500/10 px-2 py-1 rounded-md border border-cyan-500/30">
              Predicted
            </span>
            <span className="text-xs text-slate-400">Confidence {prediction.confidence_pct}%</span>
          </div>
          {prediction.confidence_pct < 25 ? (
            <p className="text-xs text-orange-300 mt-3">
              Warning: low confidence. This prediction is unreliable.
            </p>
          ) : null}
        </div>
      )}
    </div>
  )
}

function NearestTestRow({ test }: { test: NearestTest }) {
  return (
    <li className="rounded-xl border border-white/5 bg-[#040B14] p-3">
      <p className="font-mono font-bold text-white text-sm">{test.test}</p>
      <p className="text-xs text-slate-400 mt-1">{test.fuel_raw}</p>
      <p className="text-xs text-slate-300 mt-2">
        Initial O2 {test.initial_o2 !== null ? `${test.initial_o2}%` : 'not documented'}
      </p>
      <div className="flex flex-wrap gap-x-4 gap-y-1 mt-1">
        {test.final_o2 !== null ? <span className="text-xs text-slate-400">Final O2 {test.final_o2}%</span> : null}
        {test.final_co !== null ? <span className="text-xs text-slate-400">Final CO {test.final_co} ppm</span> : null}
        {test.final_co2 !== null ? <span className="text-xs text-slate-400">Final CO2 {test.final_co2}%</span> : null}
      </div>
    </li>
  )
}

export function FlammabilityExplorerPage() {
  const [oxygen, setOxygen] = useState(21)
  const [airflow, setAirflow] = useState(10)
  const [material, setMaterial] = useState('PMMA')
  const [result, setResult] = useState<PredictResponse | null>(null)
  const [predicting, setPredicting] = useState(false)
  const [predictError, setPredictError] = useState<string | null>(null)
  const [retryCount, setRetryCount] = useState(0)

  const modelInfo = useQuery<ModelInfo, Error>({
    queryKey: ['flammability', 'model-info'],
    queryFn: ({ signal }) => apiClient.get<ModelInfo>(endpoints.flammability.modelInfo, { signal }),
  })

  useEffect(() => {
    const controller = new AbortController()
    setPredicting(true)
    setPredictError(null)
    const timer = setTimeout(() => {
      apiClient
        .post<PredictResponse>(
          endpoints.flammability.predict,
          { oxygen_pct: oxygen, airflow_cms: airflow, material, pressure_kpa: 101.3 },
          { signal: controller.signal },
        )
        .then((data) => {
          setResult(data)
          setPredicting(false)
        })
        .catch((err) => {
          if (err instanceof Error && err.name === 'AbortError') return
          setPredictError('Could not get a prediction. Check that the backend is running.')
          setPredicting(false)
        })
    }, 300)
    return () => {
      clearTimeout(timer)
      controller.abort()
    }
  }, [oxygen, airflow, material, retryCount])

  if (modelInfo.isPending) return <LoadingState message="Loading model info..." />
  if (modelInfo.isError) return <ErrorState message="Could not load model info." onRetry={() => modelInfo.refetch()} />

  const info = modelInfo.data
  const materials = info.materials.length > 0 ? info.materials : ['PMMA']
  const isBlue = result !== null && result.regime === 'blue flame'

  return (
    <div className="space-y-6 pb-12">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-2">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-wide flex items-center gap-2">
            <svg className="w-6 h-6 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z" />
            </svg>
            Flammability Explorer
          </h1>
          <p className="text-sm text-slate-400 mt-1 max-w-2xl">
            Set the conditions. A model trained on published microgravity combustion results predicts the flame-spread
            regime and the measured outcomes, with the experiments behind the prediction.
          </p>
        </div>
      </div>

      <div className="rounded-2xl border border-white/10 bg-[#0A1628] p-5 shadow-lg shadow-black/20">
        <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4">Experimental conditions</h2>
        <div className="grid gap-6 md:grid-cols-3">
          <div>
            <label htmlFor="oxygen-slider" className="flex items-center justify-between text-sm text-slate-300">
              <span>Oxygen concentration</span>
              <span className="font-mono font-bold text-cyan-300">{oxygen.toFixed(1)}%</span>
            </label>
            <input
              id="oxygen-slider"
              type="range"
              min={13}
              max={22}
              step={0.5}
              value={oxygen}
              onChange={(e) => setOxygen(Number(e.target.value))}
              className="w-full mt-3 accent-cyan-500"
            />
            <p className="text-xs text-slate-500 mt-2">
              Regime boundary at 19%. At or above 19% the model reports a sooty flame; below 19% a blue flame.
            </p>
          </div>
          <div>
            <label htmlFor="airflow-slider" className="flex items-center justify-between text-sm text-slate-300">
              <span>Flow velocity</span>
              <span className="font-mono font-bold text-cyan-300">{airflow} cm/s</span>
            </label>
            <input
              id="airflow-slider"
              type="range"
              min={0}
              max={40}
              step={1}
              value={airflow}
              onChange={(e) => setAirflow(Number(e.target.value))}
              className="w-full mt-3 accent-cyan-500"
            />
            <p className="text-xs text-slate-500 mt-2">
              Documented range for BASS-II is up to 40 cm/s.
            </p>
          </div>
          <div>
            <label htmlFor="material-select" className="block text-sm text-slate-300">
              Material
            </label>
            <select
              id="material-select"
              value={material}
              onChange={(e) => setMaterial(e.target.value)}
              className="w-full mt-3 rounded-lg border border-white/10 bg-[#040B14] px-3 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50"
            >
              {materials.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
            <p className="text-xs text-slate-500 mt-2">
              Pressure 101.3 kPa (fixed). The training data has no pressure variation, so pressure does not change the
              prediction.
            </p>
          </div>
        </div>
      </div>

      <div className="rounded-2xl border border-white/10 bg-[#0A1628] p-5 shadow-lg shadow-black/20">
        <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4">Predicted outcome</h2>
        {predictError !== null ? (
          <div className="rounded-xl border border-red-500/30 bg-red-950/30 p-4">
            <p className="text-sm text-red-200">{predictError}</p>
            <button
              type="button"
              onClick={() => setRetryCount((c) => c + 1)}
              className="mt-3 rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-sm font-medium text-slate-200 hover:bg-white/10"
            >
              Retry
            </button>
          </div>
        ) : result === null ? (
          <p className="text-sm text-slate-400">{predicting ? 'Predicting...' : 'Waiting for a prediction.'}</p>
        ) : (
          <div className="space-y-5">
            <div className={`rounded-xl border p-5 ${isBlue ? 'border-cyan-500/30 bg-cyan-950/20' : 'border-orange-500/30 bg-orange-950/20'}`}>
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Flame-spread regime</p>
              <p className={`text-3xl font-bold mt-2 capitalize ${isBlue ? 'text-cyan-300' : 'text-orange-300'}`}>
                {result.regime}
              </p>
              <p className="text-sm text-slate-300 mt-2">{result.regime_basis}</p>
              {predicting ? <p className="text-xs text-slate-500 mt-2">Updating prediction...</p> : null}
            </div>
            <div className="grid gap-4 md:grid-cols-3">
              {Object.keys(TARGET_LABELS).map((key) => (
                <PredictionCard key={key} label={TARGET_LABELS[key] ?? key} prediction={result.predictions[key]} />
              ))}
            </div>
          </div>
        )}
      </div>

      {result !== null ? (
        <div className="rounded-2xl border border-white/10 bg-[#0A1628] p-5 shadow-lg shadow-black/20">
          <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4">Why this prediction</h2>
          <p className="text-sm text-slate-300 p-3 bg-[#040B14] rounded-lg border border-white/5">
            {result.explanation.finding}
          </p>
          <p className="text-xs text-slate-500 mt-3">
            Finding source:{' '}
            <span className="font-mono text-cyan-300 bg-cyan-500/10 px-2 py-1 rounded border border-cyan-500/20">
              {result.explanation.finding_source}
            </span>
          </p>
          <div className="grid gap-4 md:grid-cols-2 mt-4">
            <div>
              <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                Nearest tests above 19% oxygen
              </h3>
              <ul className="space-y-2">
                {result.explanation.nearest_tests_above_19pct_o2.map((t) => (
                  <NearestTestRow key={t.test} test={t} />
                ))}
              </ul>
            </div>
            <div>
              <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                Nearest tests below 19% oxygen
              </h3>
              <ul className="space-y-2">
                {result.explanation.nearest_tests_below_19pct_o2.map((t) => (
                  <NearestTestRow key={t.test} test={t} />
                ))}
              </ul>
            </div>
          </div>
        </div>
      ) : null}

      {result !== null && result.warnings.length > 0 ? (
        <div className="rounded-2xl border border-orange-500/20 bg-orange-950/20 p-5">
          <h2 className="text-sm font-semibold text-orange-300 uppercase tracking-wider mb-3">Warnings</h2>
          <ul className="space-y-2">
            {result.warnings.map((w) => (
              <li key={w} className="text-sm text-orange-200/80">
                {w}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      <div className="rounded-2xl border border-white/10 bg-[#0A1628] p-5 shadow-lg shadow-black/20">
        <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-3">About this model</h2>
        <p className="text-sm text-slate-300">
          Rough estimate from {info.training_rows} BASS-II tests ({info.training_source}). It is not a precise
          prediction.
        </p>
        <p className="text-sm text-slate-400 mt-2">{info.regime_rule}</p>
        <div className="grid gap-3 md:grid-cols-3 mt-4">
          {Object.keys(TARGET_LABELS).map((key) => {
            const metric = info.targets[key]
            if (metric === undefined) return null
            return (
              <div key={key} className="rounded-xl border border-white/5 bg-[#040B14] p-3">
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">{TARGET_LABELS[key] ?? key}</p>
                <p className="text-sm text-slate-300 mt-2">
                  R2 {formatMetric(metric.r2)} · MAE {formatMetric(metric.mae)}
                </p>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
