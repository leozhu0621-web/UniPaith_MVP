// Feature #2 — outcome-first discovery tiles.
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import OutcomeTiles, { OUTCOME_PRESETS } from '../pages/student/explore/discovery/OutcomeTiles'

describe('OUTCOME_PRESETS', () => {
  it('each preset sets a real ROI filter and a matching outcome sort', () => {
    const earning = OUTCOME_PRESETS.find(p => p.key === 'earning')!
    expect(earning.filters.min_median_salary).toBeGreaterThan(0)
    expect(earning.sort).toBe('salary_desc')

    const placement = OUTCOME_PRESETS.find(p => p.key === 'placement')!
    expect(placement.filters.min_employment_rate).toBeGreaterThan(0)
    expect(placement.sort).toBe('employment_desc')

    const value = OUTCOME_PRESETS.find(p => p.key === 'value')!
    expect(value.filters.max_tuition).toBeGreaterThan(0)
    expect(value.filters.min_median_salary).toBeGreaterThan(0)
  })
})

describe('OutcomeTiles', () => {
  it('renders all presets and fires onPick with the preset', () => {
    const onPick = vi.fn()
    render(<OutcomeTiles onPick={onPick} />)
    fireEvent.click(screen.getByText('High earning potential'))
    expect(onPick).toHaveBeenCalledWith(expect.objectContaining({ key: 'earning', sort: 'salary_desc' }))
    expect(screen.getByText('Strong job placement')).toBeTruthy()
    expect(screen.getByText('Low tuition, high salary')).toBeTruthy()
  })
})
