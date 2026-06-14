import { Sparkles } from 'lucide-react'
import { countThisWeek, type WeekInputs } from './weekActivity'

/** "This week · N saved · N reviewed · N submitted" — only non-zero segments;
 *  a smart-empty prompt on a quiet week (Spec 2026-06-14 §Modules.2c). */
export default function WeekRibbon(inputs: WeekInputs) {
  const c = countThisWeek(inputs)
  const segments: string[] = []
  if (c.saved) segments.push(`${c.saved} saved`)
  if (c.reviewed) segments.push(`${c.reviewed} reviewed`)
  if (c.submitted) segments.push(`${c.submitted} submitted`)

  return (
    <div className="flex items-center gap-2 rounded-md bg-muted/50 px-3 py-2">
      <Sparkles size={13} className="shrink-0 text-secondary" aria-hidden />
      {c.total === 0 ? (
        <p className="text-xs text-muted-foreground">A quiet week so far — pick one thing below to move forward.</p>
      ) : (
        <p className="text-xs text-foreground">
          <span className="font-semibold">This week</span>
          <span className="text-muted-foreground"> · {segments.join(' · ')}</span>
        </p>
      )}
    </div>
  )
}
