import { describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen } from '@testing-library/react'
import { RelevancePanel } from './RelevancePanel'

const mockAssessment = vi.hoisted(() => ({
  assessment_id: 'mr-exp-001-ISS',
  subject_type: 'experiment',
  subject_id: 'exp-001',
  subject_name: 'FLEX',
  mission: 'ISS',
  relevance_level: 'documented',
  relevant_conditions: ['Microgravity'],
  similarities: ['Flame behavior in microgravity.'],
  differences: ['Gravity level differs.'],
  supporting_evidence: ['FLEX tests in microgravity.'],
  transferability_limitations: ['Partial gravity not tested.'],
  missing_information: [],
  source_ids: ['src-001'],
  evidence_status: 'unverified',
  derived_from_experiment_ids: [],
  explanation: 'Documented relevance for ISS.',
  limitations: ['One investigation only.'],
  methodology: 'Test methodology.',
}))

vi.mock('../../hooks/useMissionRelevance', () => ({
  useMissionRelevanceForExperiment: () => ({ data: mockAssessment, isPending: false, isError: false, refetch: vi.fn() }),
  useMissionRelevanceForHardware: () => ({ data: undefined, isPending: false, isError: false, refetch: vi.fn() }),
}))

describe('RelevancePanel', () => {
  it('shows the assessment level and explanation', () => {
    render(<RelevancePanel subjectType="experiment" subjectId="exp-001" subjectName="FLEX" initialMission="ISS" />)
    expect(screen.getByText('documented')).toBeInTheDocument()
    expect(screen.getByText('Documented relevance for ISS.')).toBeInTheDocument()
  })

  it('shows the microgravity note', () => {
    render(<RelevancePanel subjectType="experiment" subjectId="exp-001" subjectName="FLEX" initialMission="ISS" />)
    expect(screen.getByText(/Microgravity findings are not automatically/)).toBeInTheDocument()
  })

  it('makes the Moon button active when clicked', () => {
    render(<RelevancePanel subjectType="experiment" subjectId="exp-001" subjectName="FLEX" initialMission="ISS" />)
    fireEvent.click(screen.getByRole('button', { name: 'Moon' }))
    expect(screen.getByRole('button', { name: 'Moon' })).toHaveClass('border-cyan-600')
  })

  it('renders the hardware branch for a hardware subject', () => {
    render(<RelevancePanel subjectType="hardware" subjectId="hw-001" subjectName="CIR" initialMission="ISS" />)
    expect(screen.getByText('No assessment available.')).toBeInTheDocument()
  })
})
