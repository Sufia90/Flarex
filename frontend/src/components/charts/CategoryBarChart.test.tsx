import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { CategoryBarChart } from './CategoryBarChart'

describe('CategoryBarChart', () => {
  it('shows an empty message when there is no data', () => {
    render(<CategoryBarChart data={[]} title="Fire safety" />)
    expect(screen.getByText('No data to chart yet.')).toBeInTheDocument()
  })

  it('shows the title when data exists', () => {
    render(
      <CategoryBarChart
        data={[
          { name: 'Prevention', count: 2 },
          { name: 'Detection', count: 0 },
        ]}
        title="Fire safety"
      />,
    )
    expect(screen.getByText('Fire safety')).toBeInTheDocument()
  })
})
