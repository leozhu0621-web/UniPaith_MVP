import { describe, expect, it } from 'vitest'
import { countThisWeek, type WeekInputs } from '../pages/student/myspace/home/weekActivity'

const iso = (daysAgo: number) => new Date(Date.now() - daysAgo * 86_400_000).toISOString()

describe('countThisWeek', () => {
  it('counts only items within the last 7 days', () => {
    const inputs: WeekInputs = {
      saved: [{ added_at: iso(2) }, { added_at: iso(10) }] as any,
      runs: [{ created_at: iso(1) }] as any,
      apps: [{ submitted_at: iso(3) }, { submitted_at: null }, { submitted_at: iso(30) }] as any,
    }
    expect(countThisWeek(inputs)).toEqual({ saved: 1, reviewed: 1, submitted: 1, total: 3 })
  })

  it('is all-zero for an empty week', () => {
    expect(countThisWeek({ saved: [], runs: [], apps: [] })).toEqual({ saved: 0, reviewed: 0, submitted: 0, total: 0 })
  })
})
