import { describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen } from '@testing-library/react'
import { ComparisonPanel } from './ComparisonPanel'

vi.mock('../../hooks/useExperiments', () => {
  function experiment(id: string, name: string) {
    return {
      id,
      schema_version: '1.0',
      created_at: '2026-11-12T00:00:00',
      updated_at: '2026-11-12T00:00:00',
      status: 'active',
      nasa_investigation_id: null,
      name,
      acronym: null,
      description: null,
      scientific_objective: null,
      research_category: null,
      combustion_type: null,
      fuel_material: null,
      sample_geometry: null,
      sample_dimensions: null,
      hardware_ids: [],
      related_investigation_ids: [],
      conditions: {
        fuel_material: null,
        oxygen_concentration: null,
        oxygen_unit: null,
        oxygen_basis: null,
        ambient_pressure: null,
        pressure_unit: null,
        temperature: null,
        temperature_unit: null,
        airflow_velocity: null,
        airflow_unit: null,
        airflow_direction: null,
        gravity_condition: null,
        sample_geometry: null,
        sample_dimensions: null,
        other_conditions: {},
      },
      measurements: [],
      findings: [],
      limitations: [],
      source_ids: [],
      media_ids: [],
      mission_applicability: [],
      transferability_note: null,
      fire_safety_relevance: [],
      data_quality: { completeness: 'not_yet_verified', verification_status: 'unverified', missing_fields: [], notes: '' },
    }
  }
  return {
    useExperiments: () => ({
      data: { total: 2, page: 1, page_size: 20, total_pages: 1, items: [experiment('exp-001', 'FLEX'), experiment('exp-002', 'Saffire')] },
      isPending: false,
      isError: false,
    }),
  }
})

vi.mock('../../hooks/useHardware', () => ({
  useHardware: () => ({
    data: { total: 0, page: 1, page_size: 20, total_pages: 0, items: [] },
    isPending: false,
    isError: false,
  }),
}))

vi.mock('../../hooks/useComparisons', () => ({
  useCompareExperiments: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useCompareHardware: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useCompareMeasurements: () => ({ mutateAsync: vi.fn(), isPending: false }),
}))

describe('ComparisonPanel', () => {
  it('lists experiments to compare', () => {
    render(<ComparisonPanel />)
    expect(screen.getByText('FLEX')).toBeInTheDocument()
    expect(screen.getByText('Saffire')).toBeInTheDocument()
    expect(screen.getByText(/Selected: 0/)).toBeInTheDocument()
  })

  it('enables Compare after two items are selected', () => {
    render(<ComparisonPanel />)
    fireEvent.click(screen.getByText('FLEX'))
    fireEvent.click(screen.getByText('Saffire'))
    expect(screen.getByText(/Selected: 2/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Compare selected' })).not.toBeDisabled()
  })

  it('keeps Compare disabled with fewer than two items', () => {
    render(<ComparisonPanel />)
    expect(screen.getByRole('button', { name: 'Compare selected' })).toBeDisabled()
  })

  it('shows an empty state for hardware when no hardware is loaded', () => {
    render(<ComparisonPanel />)
    fireEvent.click(screen.getByRole('button', { name: 'Hardware' }))
    expect(screen.getByText('No records to compare')).toBeInTheDocument()
  })
})
