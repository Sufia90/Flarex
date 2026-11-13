import { useState } from 'react'
import { Link } from 'react-router'
import { LoadingState } from '../components/feedback/LoadingState'
import { ErrorState } from '../components/feedback/ErrorState'
import { EmptyState } from '../components/feedback/EmptyState'
import { EvidenceStatusBadge } from '../components/common/EvidenceStatusBadge'
import { useExperiments } from '../hooks/useExperiments'
import type { Experiment, Finding } from '../types/experiment'

const STOP_WORDS = new Set([
  'what', 'which', 'when', 'where', 'how', 'does', 'did', 'do', 'is', 'are', 'was', 'were',
  'can', 'could', 'would', 'should', 'has', 'have', 'had', 'the', 'and', 'for', 'with',
  'about', 'from', 'that', 'this', 'there', 'here', 'tell', 'show', 'list', 'give', 'find',
  'study', 'studied', 'studies', 'experiment', 'experiments', 'research', 'nasa', 'its', 'into',
  'over', 'under', 'between', 'among', 'any', 'all', 'more', 'most', 'other', 'some', 'than', 'then',
])

function keywords(question: string): string[] {
  const words = question
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, ' ')
    .split(/\s+/)
    .filter((w) => w.length > 2 && !STOP_WORDS.has(w))
  return [...new Set(words)]
}

function experimentText(e: Experiment): string {
  const parts: string[] = [
    e.name,
    e.description ?? '',
    e.scientific_objective ?? '',
    e.research_category ?? '',
    e.combustion_type ?? '',
    e.fuel_material ?? '',
    ...(e.mission_applicability ?? []),
    ...(e.fire_safety_relevance ?? []),
  ]
  const c = e.conditions
  if (c) {
    if (c.fuel_material) parts.push(`fuel ${c.fuel_material}`)
    if (c.oxygen_concentration !== null && c.oxygen_concentration !== undefined) parts.push('oxygen')
    if (c.ambient_pressure !== null && c.ambient_pressure !== undefined) parts.push('pressure')
    if (c.airflow_velocity !== null && c.airflow_velocity !== undefined) parts.push('airflow')
    if (c.gravity_condition) parts.push(`gravity ${c.gravity_condition}`)
    if (c.other_conditions) {
      for (const [k, v] of Object.entries(c.other_conditions)) parts.push(`${k} ${String(v)}`)
    }
  }
  for (const f of e.findings) parts.push(f.title, f.observation ?? '', f.conclusion ?? '')
  for (const m of e.measurements) parts.push(m.parameter_name)
  return parts.join(' ').toLowerCase()
}

type Match = {
  experiment: Experiment
  score: number
  matchedWords: string[]
  findings: Finding[]
}

function findMatches(experiments: Experiment[], question: string): Match[] {
  const words = keywords(question)
  if (words.length === 0) return []
  const matches: Match[] = []
  for (const e of experiments) {
    const text = experimentText(e)
    const matchedWords = words.filter((w) => text.includes(w))
    if (matchedWords.length === 0) continue
    const findings = e.findings.filter((f) => {
      const findingText = `${f.title} ${f.observation ?? ''} ${f.conclusion ?? ''}`.toLowerCase()
      return matchedWords.some((w) => findingText.includes(w))
    })
    matches.push({ experiment: e, score: matchedWords.length, matchedWords, findings })
  }
  matches.sort((a, b) => b.score - a.score)
  return matches
}

const EXAMPLES = ['BASS', 'suppression', 'oxygen']

export function ResearchAssistantPage() {
  const experiments = useExperiments()
  const [draft, setDraft] = useState('')
  const [asked, setAsked] = useState<string | null>(null)
  const [results, setResults] = useState<Match[] | null>(null)

  function ask(question: string) {
    const q = question.trim()
    if (q === '') return
    setDraft(q)
    setAsked(q)
    setResults(findMatches(experiments.data?.items ?? [], q))
  }

  function onClear() {
    setDraft('')
    setAsked(null)
    setResults(null)
  }

  if (experiments.isPending) return <LoadingState message="Loading records..." />
  if (experiments.isError) return <ErrorState message="Could not load experiments." onRetry={() => experiments.refetch()} />
  const items = experiments.data?.items ?? []
  return (
    <section className="space-y-4">
      <h2 className="text-xl font-bold">Research Assistant</h2>
      <p className="text-sm text-slate-300">Ask a question. The assistant searches only the loaded NASA records and shows the evidence behind the answer. It never invents answers.</p>
      <form
        onSubmit={(e) => {
          e.preventDefault()
          ask(draft)
        }}
        className="flex gap-2"
      >
        <input
          className="w-full rounded border border-slate-600 bg-slate-800 px-3 py-2 text-sm text-white"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="Ask about the loaded research..."
        />
        <button type="submit" className="rounded bg-cyan-600 px-3 py-2 text-sm text-white">Ask</button>
        <button type="button" onClick={onClear} className="rounded border border-slate-600 px-3 py-2 text-sm text-slate-300">Clear</button>
      </form>
      <div className="flex flex-wrap gap-2">
        <span className="text-xs text-slate-400">Try:</span>
        {EXAMPLES.map((ex) => (
          <button key={ex} type="button" onClick={() => ask(ex)} className="rounded border border-slate-600 px-3 py-1 text-sm text-slate-300">{ex}</button>
        ))}
      </div>
      {items.length === 0 ? (
        <EmptyState title="No records loaded yet" message="No experiment records are loaded. Real NASA records will appear here when they are added." />
      ) : results === null ? (
        <p className="text-sm text-slate-400">Type a question above, or try one of the examples.</p>
      ) : results.length === 0 ? (
        <EmptyState title="Insufficient evidence" message="No loaded records match this question. Try different words, for example BASS, suppression, or oxygen." />
      ) : (
        <div className="space-y-3">
          <p className="text-sm text-slate-300">Evidence found in {results.length} experiment(s) for "{asked}".</p>
          {results.map((r) => (
            <div key={r.experiment.id} className="space-y-2 rounded border border-slate-700 bg-slate-900 p-4">
              <div className="flex flex-wrap items-center gap-2">
                <Link className="font-semibold text-cyan-300" to={`/experiments?id=${encodeURIComponent(r.experiment.id)}`}>
                  {r.experiment.name}
                </Link>
                <EvidenceStatusBadge status={r.experiment.data_quality.verification_status} />
              </div>
              <p className="text-xs text-slate-400">Matched words: {r.matchedWords.join(', ')}</p>
              {r.experiment.scientific_objective ? <p className="text-sm text-slate-300">{r.experiment.scientific_objective}</p> : null}
              {r.findings.length > 0 ? (
                <ul className="space-y-2">
                  {r.findings.slice(0, 3).map((f) => (
                    <li key={f.id} className="rounded border border-slate-700 p-3">
                      <p className="font-semibold text-white">{f.title}</p>
                      <p className="mt-1 text-sm text-slate-300">{f.observation ? f.observation : 'Not documented'}</p>
                      <div className="mt-1 flex flex-wrap items-center gap-2">
                        {f.verification_status ? <EvidenceStatusBadge status={f.verification_status} /> : null}
                        {f.source_id ? <span className="text-xs text-slate-400">Source: {f.source_id}</span> : null}
                      </div>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-slate-500">No matching findings in this experiment.</p>
              )}
            </div>
          ))}
        </div>
      )}
    </section>
  )
}
