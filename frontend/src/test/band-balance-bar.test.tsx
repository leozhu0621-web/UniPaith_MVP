import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import BandBalanceBar, { balanceNudge } from '../components/student/BandBalanceBar'

describe('BandBalanceBar', () => {
  it('renders a segment per non-zero band, sized proportionally', () => {
    const { container } = render(<BandBalanceBar reach={2} target={3} safer={1} />)
    const track = container.querySelector('[role="img"]')!
    const segments = Array.from(track.children) as HTMLElement[]
    expect(segments).toHaveLength(3)
    // total = 6 → reach 2/6, target 3/6, safer 1/6
    expect(segments[0].style.width).toBe(`${(2 / 6) * 100}%`)
    expect(segments[1].style.width).toBe(`${(3 / 6) * 100}%`)
    expect(segments[2].style.width).toBe(`${(1 / 6) * 100}%`)
  })

  it('reuses the BandBadge color family for each segment', () => {
    const { container } = render(<BandBalanceBar reach={1} target={1} safer={1} />)
    const segments = Array.from(container.querySelector('[role="img"]')!.children) as HTMLElement[]
    expect(segments[0].className).toContain('bg-secondary') // reach = cobalt
    expect(segments[1].className).toContain('bg-success') // target = green
    expect(segments[2].className).toContain('bg-muted-foreground') // safer = neutral
  })

  it('drops a band with zero count from the bar', () => {
    const { container } = render(<BandBalanceBar reach={2} target={0} safer={1} />)
    expect(Array.from(container.querySelector('[role="img"]')!.children)).toHaveLength(2)
  })

  it('summarizes the counts for screen readers', () => {
    render(<BandBalanceBar reach={2} target={3} safer={1} />)
    expect(screen.getByRole('img', { name: '2 reach, 3 target, 1 safer' })).toBeTruthy()
  })

  it('renders nothing when the total is zero', () => {
    const { container } = render(<BandBalanceBar reach={0} target={0} safer={0} />)
    expect(container.firstChild).toBeNull()
  })
})

describe('balanceNudge', () => {
  it('nudges to add a safer option when there are reaches but none safer', () => {
    expect(balanceNudge({ reach: 2, target: 1, safer: 0 })).toBe(
      'Add a safer option to balance your list.',
    )
  })

  it('flags a single-band list as too narrow', () => {
    expect(balanceNudge({ reach: 0, target: 3, safer: 0 })).toBe(
      'Your list is all target — consider a wider range.',
    )
  })

  it('prefers the missing-safer nudge over the single-band nudge for all-reach', () => {
    expect(balanceNudge({ reach: 4, target: 0, safer: 0 })).toBe(
      'Add a safer option to balance your list.',
    )
  })

  it('says nothing when the spread is reasonable', () => {
    expect(balanceNudge({ reach: 1, target: 1, safer: 1 })).toBeNull()
  })

  it('says nothing when only safer programs exist (no reach to balance)', () => {
    // Single band, but the missing-safer rule cannot fire — falls to the
    // all-one-band rule.
    expect(balanceNudge({ reach: 0, target: 0, safer: 2 })).toBe(
      'Your list is all safer — consider a wider range.',
    )
  })

  it('says nothing when the total is zero', () => {
    expect(balanceNudge({ reach: 0, target: 0, safer: 0 })).toBeNull()
  })
})
