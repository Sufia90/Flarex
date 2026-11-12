import { describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen } from '@testing-library/react'
import { RankingPanel } from './RankingPanel'

const mockResult = vi.hoisted(() => ({
  ranking_id: 'rank-001',
  criterion: 'experiment_documentation_completeness',
  title: 'Experiments by documentation completeness',
  question: 'Which experiments are best documented?',
  methodology: 'Test methodology.',
  metric_name: 'Documentation signals',
  metric_description: 'Number of documentation fields present.',
  metric_max: 9,
  status: 'ranked',
  eligible_item_ids: ['exp-001', 'exp-002'],
  items: [
    { rank: 1, item_id: 'exp-001', item_name: 'FLEX', metric_value: 7, metric_max: 9, metric_breakdown: {}, evidence_ids: ['exp-001'], data_completeness: 'complete', verification_status: 'unverified', explanation: 'Seven of nine signals present.', limitations: [] },
    { rank: 1, item_id: 'exp-002', item_name: 'Saffire', metric_value: 7, metric_max: 9, metric_breakdown: {}, evidence_ids: ['exp-002'], data_completeness: 'complete', verification_status: 'unverified', explanation: 'Seven of nine signals present.', limitations: [] },
    { rank: null, item_id: 'exp-003', item_name: 'Empty', metric_value: 0, metric_max: 9, metric_breakdown: {}, evidence_ids: [], data_completeness: 'incomplete', verification_status: 'unverified', explanation: 'No signals present.', limitations: ['No documentation.'] },
  ],
  source_ids: [],
  explanation: 'Two items tie at rank 1.',
  limitations: [],
}))

vi.mock('../../hooks/useExperiments', () => ({
  useExperiments: () => ({
    data: { total: 2, page: 1, page_size: 20, total_pages: 1, items: [{ id: 'exp-001', name: 'FLEX' }, { id: 'exp-002', name: 'Saffire' }] },
    isPending: false,
    isError: false,
  }),
}))

vi.mock('../../hooks/useHardware', () => ({
  useHardware: () => ({
    data: { total: 0, page: 1, page_size: 20, total_pages: 0, items: [] },
    isPending: false,
    isError: false,
  }),
}))

vi.mock('../../hooks/useRankings', () => ({
  useCreateRanking: () => ({ mutateAsync: vi.fn().mockResolvedValue(mockResult), isPending: false }),
}))

describe('RankingPanel', () => {
  it('shows the criterion description', () => {
    render(<RankingPanel />)
    expect(screen.getByText('Ranks experiments by how many documentation fields are present.')).toBeInTheDocument()
  })

  it('shows equal ranks and unranked items after ranking', async () => {
    render(<RankingPanel />)
    fireEvent.click(screen.getByRole('button', { name: 'Rank' }))
    const rankOnes = await screen.findAllByText('Rank 1')
    expect(rankOnes).toHaveLength(2)
    expect(screen.getByText('Not ranked — insufficient evidence.')).toBeInTheDocument()
  })

  it('keeps Rank disabled in selected mode with no selection', () => {
    render(<RankingPanel />)
    fireEvent.click(screen.getByRole('button', { name: 'Selected records' }))
    expect(screen.getByRole('button', { name: 'Rank' })).toBeDisabled()
  })
})
