import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import WeekRibbon from '../pages/student/myspace/home/WeekRibbon'

const iso = (d: number) => new Date(Date.now() - d * 86_400_000).toISOString()

describe('WeekRibbon', () => {
  it('shows only non-zero segments', () => {
    render(<WeekRibbon saved={[{ added_at: iso(1) }] as any} runs={[]} apps={[{ submitted_at: iso(2) }] as any} />)
    expect(screen.getByText(/1 saved/)).toBeTruthy()
    expect(screen.getByText(/1 submitted/)).toBeTruthy()
    expect(screen.queryByText(/reviewed/)).toBeNull()
  })
  it('shows the smart-empty prompt on a quiet week', () => {
    render(<WeekRibbon saved={[]} runs={[]} apps={[]} />)
    expect(screen.getByText(/quiet week/i)).toBeTruthy()
  })
})
