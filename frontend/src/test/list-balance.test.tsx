// Feature #1 — application-list balance meter.
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { computeBalance } from '../pages/student/saved/listBalance'
import ListBalanceMeter from '../pages/student/saved/ListBalanceMeter'
import type { SavedProgram } from '../types'

const sp = (band: string | null): SavedProgram => ({ band_label: band } as SavedProgram)

describe('computeBalance', () => {
  it('counts bands and marks unscored', () => {
    const b = computeBalance([sp('reach'), sp('reach'), sp('target'), sp('safer'), sp(null)])
    expect(b).toMatchObject({ reach: 2, target: 1, safer: 1, unscored: 1, scored: 4 })
  })

  it('nudges to add a safer school when there are none', () => {
    const b = computeBalance([sp('reach'), sp('reach'), sp('target')])
    expect(b.nudge).toMatch(/no safer schools yet/i)
  })

  it('flags a reach-heavy list', () => {
    const b = computeBalance([sp('reach'), sp('reach'), sp('reach'), sp('safer')])
    expect(b.nudge).toMatch(/reach-heavy/i)
  })

  it('calls a balanced list balanced', () => {
    const b = computeBalance([sp('reach'), sp('target'), sp('safer')])
    expect(b.nudge).toMatch(/balanced spread/i)
  })

  it('stays silent below 3 scored programs', () => {
    expect(computeBalance([sp('reach'), sp('target')]).nudge).toBeNull()
  })
})

describe('ListBalanceMeter', () => {
  it('renders the band counts when something is scored', () => {
    render(<ListBalanceMeter programs={[sp('reach'), sp('target'), sp('safer')]} />)
    expect(screen.getByText(/1 reach · 1 target · 1 safer/)).toBeTruthy()
  })

  it('renders nothing when no program is scored', () => {
    const { container } = render(<ListBalanceMeter programs={[sp(null), sp(null)]} />)
    expect(container.firstChild).toBeNull()
  })
})
