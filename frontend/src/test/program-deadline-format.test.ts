// Program-card deadline countdown consistency (deadline-math sweep 2026-06-21).
// deadlineInfo() used to compute "Xd left" with date-fns differenceInDays, which
// TRUNCATES — so a 2.5-day deadline read "2d left" on a card while the rest of the
// app (Applications, Calendar, DeadlinePill) used the canonical daysUntil (ceil)
// and said 3. Now it uses daysUntil, so the whole app agrees.
import { describe, it, expect } from 'vitest'
import { deadlineInfo } from '../pages/student/explore/cards/programFormat'

const inDays = (d: number) => new Date(Date.now() + d * 86_400_000).toISOString()

describe('deadlineInfo — canonical daysUntil countdown', () => {
  it('ceils partial days like the rest of the app (2.5d → "3d left", not "2d")', () => {
    const info = deadlineInfo(inDays(2.5))!
    expect(info.text).toBe('3d left')
    expect(info.urgent).toBe(true)
    expect(info.closed).toBe(false)
  })

  it('marks a past deadline closed (date shown, not urgent)', () => {
    const info = deadlineInfo(inDays(-3))!
    expect(info.closed).toBe(true)
    expect(info.urgent).toBe(false)
  })

  it('shows the date (not a relative pill) beyond 30 days', () => {
    const info = deadlineInfo(inDays(45))!
    expect(info.closed).toBe(false)
    expect(info.urgent).toBe(false)
    expect(info.text).not.toMatch(/left/)
  })

  it('returns null when there is no deadline', () => {
    expect(deadlineInfo(null)).toBeNull()
  })
})
