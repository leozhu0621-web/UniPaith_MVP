import { parseISO } from 'date-fns'
import type { CalendarItem, CalendarItemType } from '../../../api/calendar'

// Date-only deadlines (application / document / recommendation / interview-
// submission / deposit) have no real time — the backend stores them end-of-day
// UTC (23:59Z, see calendar_service._eod). Parsing that instant into LOCAL time
// lands them on the NEXT calendar day for any positive-UTC-offset viewer (e.g.
// the founder's UTC+8 sees 07:59 the next morning), so a "due Nov 1" deadline
// would show under Nov 2 on the month/week/agenda — a day late on a deadline
// surface (Calendar review 2026-06-21 #1). Bucket these by their UTC calendar
// date so they land on the intended day for every viewer; timed items (events,
// reminders, work blocks) keep their real local instant.
export const DEADLINE_TYPES: readonly CalendarItemType[] = [
  'submission_deadline',
  'document_deadline',
  'recommendation_deadline',
  'interview_submission_deadline',
  'deposit_deadline',
]

const DEADLINE_TYPE_SET: ReadonlySet<string> = new Set(DEADLINE_TYPES)

export function isDeadlineType(type: CalendarItemType): boolean {
  return DEADLINE_TYPE_SET.has(type)
}

/** The calendar day an item belongs on. Date-only deadlines bucket by their UTC
 *  date (timezone-stable); everything else by its real local instant. */
export function itemDay(item: Pick<CalendarItem, 'type' | 'start_at'>): Date {
  const d = parseISO(item.start_at)
  if (isDeadlineType(item.type)) {
    // Local midnight of the UTC y/m/d → isSameDay()/format() bucket it on the
    // intended calendar date regardless of the viewer's timezone.
    return new Date(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate())
  }
  return d
}
