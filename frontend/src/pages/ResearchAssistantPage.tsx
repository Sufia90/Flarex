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
    <div className="space-y-6 pb-12">
      
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-2">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-wide flex items-center gap-2">
            <svg className="w-6 h-6 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
            Research Assistant
          </h1>
          <p className="text-sm text-slate-400 mt-1 max-w-2xl">
            Ask a question. The assistant searches only the loaded NASA records and shows the evidence behind the answer. It never invents answers.
          </p>
        </div>
      </div>

      {/* Search / Ask Container */}
      <div className="rounded-2xl border border-white/10 bg-[#0A1628] p-5 shadow-lg shadow-black/20">
        <form
          onSubmit={(e) => {
            e.preventDefault()
            ask(draft)
          }}
          className="flex flex-col sm:flex-row gap-3"
        >
          <div className="relative flex-1">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <svg className="h-5 w-5 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
            </div>
            <input
              className="w-full rounded-lg border border-white/10 bg-[#040B14] pl-10 pr-4 py-3 text-sm text-white focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 transition-all placeholder:text-slate-600"
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              placeholder="Ask about the loaded research (e.g., What did BASS study?)..."
            />
          </div>
          <div className="flex gap-2">
            <button 
              type="submit" 
              className="rounded-lg bg-cyan-600 px-6 py-3 text-sm font-bold text-white transition-all hover:bg-cyan-500 hover:shadow-[0_0_15px_rgba(34,211,238,0.4)]"
            >
              Ask
            </button>
            <button 
              type="button" 
              onClick={onClear} 
              className="rounded-lg border border-white/10 bg-white/5 px-6 py-3 text-sm font-medium text-slate-300 transition-all hover:bg-white/10 hover:text-white"
            >
              Clear
            </button>
          </div>
        </form>

        {/* Examples */}
        <div className="flex flex-wrap items-center gap-2 mt-4 pt-4 border-t border-white/5">
          <span className="text-[11px] font-medium text-slate-500 uppercase tracking-wider">Try:</span>
          {EXAMPLES.map((ex) => (
            <button 
              key={ex} 
              type="button" 
              onClick={() => ask(ex)} 
              className="rounded-full bg-cyan-500/10 border border-cyan-500/20 px-3 py-1 text-xs font-medium text-cyan-300 hover:bg-cyan-500/20 hover:border-cyan-500/40 transition-all"
            >
              {ex}
            </button>
          ))}
        </div>
      </div>

      {/* Content Area */}
      <div>
        {items.length === 0 ? (
          <div className="rounded-2xl border border-white/10 bg-[#0A1628] p-8">
            <EmptyState title="No records loaded yet" message="No experiment records are loaded. Real NASA records will appear here when they are added." />
          </div>
        ) : results === null ? (
          <div className="rounded-2xl border border-white/5 border-dashed bg-[#0A1628]/50 p-12 text-center">
            <svg className="w-12 h-12 text-slate-600 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
            <p className="text-sm text-slate-400">Type a question above, or click one of the examples to begin your research query.</p>
          </div>
        ) : results.length === 0 ? (
          <div className="rounded-2xl border border-orange-500/20 bg-orange-950/20 p-8">
             <div className="flex items-center gap-2 mb-2 text-orange-400 font-semibold">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
                Insufficient Evidence
             </div>
            <p className="text-sm text-orange-200/70">No loaded records match this question. Try different words, for example BASS, suppression, or oxygen.</p>
          </div>
        ) : (
          <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="flex items-center gap-2">
               <span className="text-cyan-400 font-bold bg-cyan-500/10 px-3 py-1 rounded-full border border-cyan-500/20 text-xs">
                  Found {results.length} experiment(s)
               </span>
               <span className="text-sm text-slate-400">for "{asked}"</span>
            </div>
            
            {results.map((r) => (
              <div key={r.experiment.id} className="rounded-2xl border border-white/10 bg-[#0A1628] overflow-hidden">
                
                {/* Result Header */}
                <div className="bg-white/5 px-5 py-4 border-b border-white/5 flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-3">
                    <Link className="font-bold text-lg text-white hover:text-cyan-300 transition-colors" to={`/experiments?id=${encodeURIComponent(r.experiment.id)}`}>
                      {r.experiment.name}
                    </Link>
                    <EvidenceStatusBadge status={r.experiment.data_quality.verification_status} />
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] text-slate-500 uppercase tracking-wider">Matched:</span>
                    <span className="text-xs font-mono text-cyan-300 bg-cyan-500/10 px-2 py-1 rounded border border-cyan-500/20">{r.matchedWords.join(', ')}</span>
                  </div>
                </div>

                {/* Result Body */}
                <div className="p-5">
                  {r.experiment.scientific_objective ? (
                    <p className="text-sm text-slate-300 mb-4 p-3 bg-[#040B14] rounded-lg border border-white/5">
                      <span className="text-cyan-400 font-semibold mb-1 block">Objective:</span> 
                      {r.experiment.scientific_objective}
                    </p>
                  ) : null}
                  
                  <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Matched Findings</h4>
                  {r.findings.length > 0 ? (
                    <ul className="space-y-3">
                      {r.findings.slice(0, 3).map((f) => (
                        <li key={f.id} className="rounded-xl border border-white/5 bg-[#040B14] p-4 hover:border-white/10 transition-colors">
                          <p className="font-semibold text-white text-base mb-1">{f.title}</p>
                          <p className="text-sm text-slate-300">{f.observation ? f.observation : 'Not documented'}</p>
                          <div className="mt-3 flex flex-wrap items-center gap-2 border-t border-white/5 pt-3">
                            {f.verification_status ? <EvidenceStatusBadge status={f.verification_status} /> : null}
                            {f.source_id ? <span className="text-[10px] uppercase tracking-wider text-slate-500 bg-white/5 px-2 py-1 rounded-md font-mono">Source: {f.source_id}</span> : null}
                          </div>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-sm text-slate-500 italic">No matching findings in this experiment.</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}