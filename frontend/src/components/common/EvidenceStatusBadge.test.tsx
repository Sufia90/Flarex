import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { EvidenceStatusBadge } from './EvidenceStatusBadge'

describe('EvidenceStatusBadge', () => {
  it('shows documented with its text', () => {
    render(<EvidenceStatusBadge status="documented" />)
    expect(screen.getByText('documented')).toBeInTheDocument()
  })

  it('shows underscores as spaces', () => {
    render(<EvidenceStatusBadge status="insufficient_evidence" />)
    expect(screen.getByText('insufficient evidence')).toBeInTheDocument()
  })

  it('uses a custom label when given', () => {
    render(<EvidenceStatusBadge status="potential" label="Maybe" />)
    expect(screen.getByText('Maybe')).toBeInTheDocument()
  })

  it('shows comparison statuses', () => {
    render(<EvidenceStatusBadge status="partially_comparable" />)
    expect(screen.getByText('partially comparable')).toBeInTheDocument()
  })
})
