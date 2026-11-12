import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { OverviewStats } from './OverviewStats'

describe('OverviewStats', () => {
  it('shows all six counts', () => {
    render(
      <OverviewStats
        counts={{ experiments: 3, hardware: 2, relationships: 1, prevention: 4, detection: 0, suppression: 1 }}
      />,
    )
    expect(screen.getByText('Experiments')).toBeInTheDocument()
    expect(screen.getByText('3')).toBeInTheDocument()
    expect(screen.getByText('Hardware')).toBeInTheDocument()
    expect(screen.getByText('2')).toBeInTheDocument()
    expect(screen.getByText('Relationships')).toBeInTheDocument()
    expect(screen.getByText('4')).toBeInTheDocument()
    expect(screen.getByText('Prevention evidence')).toBeInTheDocument()
    expect(screen.getByText('Detection evidence')).toBeInTheDocument()
    expect(screen.getByText('Suppression evidence')).toBeInTheDocument()
    expect(screen.getAllByText('1')).toHaveLength(2)
    expect(screen.getByText('0')).toBeInTheDocument()
  })

  it('shows zero counts instead of hiding them', () => {
    render(
      <OverviewStats
        counts={{ experiments: 0, hardware: 0, relationships: 0, prevention: 0, detection: 0, suppression: 0 }}
      />,
    )
    expect(screen.getAllByText('0')).toHaveLength(6)
  })
})
