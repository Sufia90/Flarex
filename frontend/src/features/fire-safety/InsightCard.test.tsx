import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { InsightCard } from './InsightCard'
import type { FireSafetyInsight } from '../../types/fire-safety'

const documentedInsight: FireSafetyInsight = {
  insight_id: 'fs-exp-001-prevention',
  category: 'prevention',
  evidence_status: 'documented',
  experiment_id: 'exp-001',
  experiment_name: 'FLEX',
  hardware_ids: ['hw-001'],
  finding_ids: ['f-001'],
  source_ids: ['src-001'],
  documented_evidence: ['Flame size reduced after the method was applied.'],
  derived_interpretation: ['The method may reduce flame spread.'],
  potential_applications: ['Crew cabin fire prevention, requires further validation.'],
  limitations: ['One test only.'],
  missing_information: [],
  verification_status: 'unverified',
  derived: false,
  methodology: 'Test methodology.',
  explanation: 'Prevention evidence is documented for FLEX.',
}

const potentialInsight: FireSafetyInsight = {
  ...documentedInsight,
  insight_id: 'fs-exp-001-detection',
  category: 'detection',
  evidence_status: 'potential',
  documented_evidence: [],
  derived_interpretation: [],
  potential_applications: ['Smoke detection in microgravity, requires further validation.'],
  finding_ids: [],
  source_ids: [],
}

describe('InsightCard', () => {
  it('shows the three evidence sections separately', () => {
    render(<InsightCard insight={documentedInsight} />)
    expect(screen.getByText('NASA-documented evidence')).toBeInTheDocument()
    expect(screen.getByText('Flame size reduced after the method was applied.')).toBeInTheDocument()
    expect(screen.getByText('Derived interpretation')).toBeInTheDocument()
    expect(screen.getByText('Potential applications')).toBeInTheDocument()
    expect(screen.getByText('Potential applications are not experimentally proven results.')).toBeInTheDocument()
  })

  it('shows category and evidence status badges', () => {
    render(<InsightCard insight={documentedInsight} />)
    expect(screen.getByText('prevention')).toBeInTheDocument()
    expect(screen.getByText('documented')).toBeInTheDocument()
  })

  it('shows finding ids and source ids', () => {
    render(<InsightCard insight={documentedInsight} />)
    expect(screen.getByText(/Supporting findings: f-001/)).toBeInTheDocument()
    expect(screen.getByText(/Sources: src-001/)).toBeInTheDocument()
  })

  it('shows no documented-evidence section for a potential insight', () => {
    render(<InsightCard insight={potentialInsight} />)
    expect(screen.queryByText('NASA-documented evidence')).not.toBeInTheDocument()
    expect(screen.getByText('Smoke detection in microgravity, requires further validation.')).toBeInTheDocument()
  })
})
