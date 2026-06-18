// Application-season grouping (Discover review 2026-06-14 #4). Groups the
// student's upcoming program deadlines (the connect deadline feed) by calendar
// month so the cramped 3-row radar becomes a season overview. Pure + tested.
import type { ConnectFeedItem } from '../../../api/connect'

export interface MonthGroup {
  key: string // YYYY-MM
  label: string // e.g. "Oct 2026"
  items: ConnectFeedItem[]
  count: number
  /** soonest days_until in the group — drives the urgency tint. */
  soonest: number
}

/** Group upcoming (days_until >= 0) deadline items by month, ascending, capped
 *  at `maxMonths` (default 6). Items without a parseable deadline are skipped. */
export function groupByMonth(items: ConnectFeedItem[], maxMonths = 6): MonthGroup[] {
  const byKey = new Map<string, MonthGroup>()
  for (const it of items) {
    if (it.kind !== 'deadline') continue
    const iso = it.deadline
    if (!iso) continue
    const d = new Date(iso)
    if (Number.isNaN(d.getTime())) continue
    const days = it.days_until ?? Math.ceil((d.getTime() - Date.now()) / 86_400_000)
    if (days < 0) continue
    const key = `${d.getUTCFullYear()}-${String(d.getUTCMonth() + 1).padStart(2, '0')}`
    const label = d.toLocaleDateString('en-US', { month: 'short', year: 'numeric', timeZone: 'UTC' })
    let g = byKey.get(key)
    if (!g) {
      g = { key, label, items: [], count: 0, soonest: days }
      byKey.set(key, g)
    }
    g.items.push(it)
    g.count++
    if (days < g.soonest) g.soonest = days
  }
  return [...byKey.values()].sort((a, b) => a.key.localeCompare(b.key)).slice(0, maxMonths)
}
