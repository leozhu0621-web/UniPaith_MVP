// Calendar timezone off-by-one (Calendar review 2026-06-21 #1). Date-only
// deadlines are stored end-of-day UTC (23:59Z); parsing that instant into LOCAL
// time lands them on the next day for any positive-UTC-offset viewer (the
// founder is UTC+8). itemDay() buckets deadline-type items by their UTC calendar
// date so they show on the intended day for everyone. This test is
// timezone-independent: it asserts itemDay's LOCAL y/m/d equals start_at's UTC
// y/m/d, which holds in any runner timezone because itemDay builds the Date from
// UTC components.
import { describe, it, expect } from 'vitest'
import { isSameDay, parseISO } from 'date-fns'
import { itemDay, isDeadlineType } from '../pages/student/calendar/itemDay'

const deadline = (start_at: string) => ({ type: 'submission_deadline' as const, start_at })
const workBlock = (start_at: string) => ({ type: 'work_block' as const, start_at })

describe('itemDay — timezone-stable deadline bucketing', () => {
  it('buckets an end-of-day-UTC deadline on its UTC calendar date (no off-by-one)', () => {
    // 23:59Z on Nov 1: a raw local parse would land Nov 2 for UTC+ viewers;
    // itemDay pins it to Nov 1 regardless of the viewer's timezone.
    const d = itemDay(deadline('2026-11-01T23:59:00Z'))
    expect(d.getFullYear()).toBe(2026)
    expect(d.getMonth()).toBe(10) // November (0-indexed)
    expect(d.getDate()).toBe(1)
    expect(isSameDay(d, new Date(2026, 10, 1))).toBe(true)
  })

  it('leaves timed items (events / reminders / work blocks) on their real instant', () => {
    const start = '2026-11-01T14:30:00Z'
    expect(itemDay(workBlock(start)).getTime()).toBe(parseISO(start).getTime())
  })

  it('isDeadlineType identifies the date-only deadline types', () => {
    expect(isDeadlineType('submission_deadline')).toBe(true)
    expect(isDeadlineType('deposit_deadline')).toBe(true)
    expect(isDeadlineType('work_block')).toBe(false)
    expect(isDeadlineType('reminder')).toBe(false)
  })
})
