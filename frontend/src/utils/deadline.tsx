// Canonical deadline-urgency rendering, shared across every room.
//
// One source of truth for the days-left → tone escalation so the same deadline
// never renders amber in one room and red in another. Thresholds (Spec 18 §8):
//   <= 7  days → 'error'   (red / text-destructive)
//   <= 21 days → 'warning' (amber / text-warning)
//   else        → 'normal' (text-foreground)
// `--destructive` and `--error` resolve to the same value in both light and
// dark; we standardize on `text-destructive` so the token matches app-wide.
import { format, parseISO, differenceInCalendarDays } from 'date-fns'

/** Compact near-term date for a deadline pill — "Mar 5", no year. */
function shortDate(iso: string): string {
  return format(parseISO(iso), 'MMM d')
}

/** Days from today to an ISO date. Date-only strings ("2026-03-05") are parsed
 *  as LOCAL midnight and compared by calendar day, so a deadline never reads a
 *  day early/late in negative-UTC timezones (native `new Date` parses date-only
 *  as UTC midnight). Strings carrying a time keep the original instant math. */
export function daysUntil(iso?: string | null): number | null {
  if (!iso) return null
  if (/^\d{4}-\d{2}-\d{2}$/.test(iso)) {
    return differenceInCalendarDays(parseISO(iso), new Date())
  }
  return Math.ceil((new Date(iso).getTime() - Date.now()) / 86400000)
}

/** Deadline color escalation: normal → warning → error. */
export type DeadlineTone = 'normal' | 'warning' | 'error'
export function deadlineTone(days?: number | null): DeadlineTone {
  if (days == null) return 'normal'
  if (days <= 7) return 'error'
  if (days <= 21) return 'warning'
  return 'normal'
}

export const DEADLINE_TONE_CLASS: Record<DeadlineTone, string> = {
  normal: 'text-foreground',
  warning: 'text-warning',
  error: 'text-destructive',
}

/**
 * Compact, inline, display-only deadline pill — a colored short date whose tone
 * escalates as the deadline nears. NOT a control (no click / decision). Renders
 * nothing when there's no date; a muted "Overdue" when the date has passed.
 */
export function DeadlinePill({
  date,
  days,
  className = '',
}: {
  date?: string | null
  days?: number | null
  className?: string
}) {
  const left = days != null ? days : daysUntil(date)
  if (!date && left == null) return null

  // Overdue → muted past styling, not an alarm color.
  if (left != null && left < 0) {
    return (
      <span className={`text-xs text-muted-foreground line-through ${className}`}>
        {date ? shortDate(date) : 'Overdue'}
      </span>
    )
  }

  const tone = deadlineTone(left)
  return (
    <span className={`text-xs font-medium ${DEADLINE_TONE_CLASS[tone]} ${className}`}>
      {date ? shortDate(date) : `${left}d left`}
    </span>
  )
}
