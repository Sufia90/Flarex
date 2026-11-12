import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { HardwareViewport } from './HardwareViewport'
import type { Hardware } from '../../types/hardware'

const hardware: Hardware = {
  id: 'hw-001',
  schema_version: '1.0',
  created_at: '2026-11-12T00:00:00',
  updated_at: '2026-11-12T00:00:00',
  status: 'active',
  name: 'Combustion Integrated Rack',
  acronym: 'CIR',
  hardware_type: 'facility',
  description: null,
  purpose: null,
  facility_classification: null,
  parent_hardware_id: null,
  component_ids: [],
  image_ids: [],
  diagram_ids: [],
  supported_measurements: [],
  related_experiment_ids: [],
  source_ids: [],
  limitations: null,
  data_quality: {
    completeness: 'not_yet_verified',
    verification_status: 'unverified',
    missing_fields: [],
    notes: '',
  },
}

describe('HardwareViewport', () => {
  it('shows the WebGL fallback when WebGL is unavailable', () => {
    render(<HardwareViewport hardware={hardware} onSelect={() => {}} />)
    expect(screen.getByText('3D view unavailable')).toBeInTheDocument()
    expect(screen.getByText(/could not start WebGL/)).toBeInTheDocument()
  })

  it('shows the fallback even with no hardware selected', () => {
    render(<HardwareViewport hardware={null} onSelect={() => {}} />)
    expect(screen.getByText('3D view unavailable')).toBeInTheDocument()
  })
})
