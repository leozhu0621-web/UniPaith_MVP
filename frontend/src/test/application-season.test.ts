// Feature #4 — application-season month grouping.
import { describe, it, expect } from 'vitest'
import { groupByMonth } from '../pages/student/calendar/seasonGroups'
import type { ConnectFeedItem } from '../api/connect'

const item = (id: string, deadline: string, days_until: number, program = 'P'): ConnectFeedItem =>
  ({ kind: 'deadline', id, date: deadline, deadline, days_until, program_name: program } as ConnectFeedItem)

describe('groupByMonth', () => {
  it('groups upcoming deadlines by month, ascending', () => {
    const groups = groupByMonth([
      item('a', '2026-10-15', 30),
      item('b', '2026-10-02', 17),
      item('c', '2026-11-20', 66),
    ])
    expect(groups.map(g => g.key)).toEqual(['2026-10', '2026-11'])
    expect(groups[0].count).toBe(2)
    expect(groups[0].soonest).toBe(17) // soonest of the two October items
  })

  it('drops past deadlines and non-deadline items', () => {
    const groups = groupByMonth([
      item('past', '2020-01-01', -100),
      { kind: 'post', id: 'p', date: '2026-10-01' } as ConnectFeedItem,
      item('ok', '2026-10-10', 25),
    ])
    expect(groups).toHaveLength(1)
    expect(groups[0].count).toBe(1)
  })

  it('caps at maxMonths', () => {
    const many = Array.from({ length: 9 }, (_, i) =>
      item(`m${i}`, `2026-${String(i + 1).padStart(2, '0')}-15`, (i + 1) * 30),
    )
    expect(groupByMonth(many, 6)).toHaveLength(6)
  })
})
