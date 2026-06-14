import type { Application, SavedProgram, WorkshopFeedbackRun } from '../../../../types'

export interface WeekInputs {
  saved: Pick<SavedProgram, 'added_at'>[]
  runs: Pick<WorkshopFeedbackRun, 'created_at'>[]
  apps: Pick<Application, 'submitted_at'>[]
}

export interface WeekCounts {
  saved: number
  reviewed: number
  submitted: number
  total: number
}

const WEEK_MS = 7 * 86_400_000

function within7d(iso: string | null | undefined): boolean {
  if (!iso) return false
  const t = new Date(iso).getTime()
  if (!Number.isFinite(t)) return false
  const delta = Date.now() - t
  return delta >= 0 && delta <= WEEK_MS
}

/** Count last-7-day activity from the three timestamped sources the home
 *  already fetches (Spec 2026-06-14 §Modules.2c). */
export function countThisWeek({ saved, runs, apps }: WeekInputs): WeekCounts {
  const s = saved.filter(x => within7d(x.added_at)).length
  const r = runs.filter(x => within7d(x.created_at)).length
  const sub = apps.filter(x => within7d(x.submitted_at)).length
  return { saved: s, reviewed: r, submitted: sub, total: s + r + sub }
}
