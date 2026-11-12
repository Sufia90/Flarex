import { describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen } from '@testing-library/react'
import { ExperimentFilters, emptyExperimentFilters } from './ExperimentFilters'

describe('ExperimentFilters', () => {
  it('shows the current query value in the first text field', () => {
    const { container } = render(
      <ExperimentFilters value={{ ...emptyExperimentFilters, query: 'FLEX' }} onChange={() => {}} onSearch={() => {}} />,
    )
    const input = container.querySelector('input')
    expect(input).toHaveValue('FLEX')
  })

  it('calls onChange when the query changes', () => {
    const onChange = vi.fn()
    const { container } = render(
      <ExperimentFilters value={emptyExperimentFilters} onChange={onChange} onSearch={() => {}} />,
    )
    const input = container.querySelector('input')
    fireEvent.change(input!, { target: { value: 'Saffire' } })
    expect(onChange).toHaveBeenCalledWith({ ...emptyExperimentFilters, query: 'Saffire' })
  })

  it('calls onSearch when Search is clicked', () => {
    const onSearch = vi.fn()
    render(<ExperimentFilters value={emptyExperimentFilters} onChange={() => {}} onSearch={onSearch} />)
    fireEvent.click(screen.getByRole('button', { name: 'Search' }))
    expect(onSearch).toHaveBeenCalledTimes(1)
  })

  it('clears all filters when Clear is clicked', () => {
    const onChange = vi.fn()
    render(
      <ExperimentFilters value={{ ...emptyExperimentFilters, query: 'FLEX' }} onChange={onChange} onSearch={() => {}} />,
    )
    fireEvent.click(screen.getByRole('button', { name: 'Clear' }))
    expect(onChange).toHaveBeenCalledWith(emptyExperimentFilters)
  })
})
