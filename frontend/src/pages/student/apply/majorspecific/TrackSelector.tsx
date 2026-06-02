// Spec 43 — track chooser. Chips for the tracks the student has started or that
// were inferred from their major (Spec 43 §1); a dropdown adds any of the
// remaining 15. Selected = cobalt; started tracks show their fit score; inferred
// (not-yet-started) tracks carry a subtle "suggested" affordance.
import clsx from 'clsx'

import type { TrackSchema } from '../../../../types/majorSpecific'

import { trackLabel } from './constants'

export default function TrackSelector({
  catalog,
  activeKeys,
  suggestedKeys,
  fitScores,
  selected,
  onSelect,
}: {
  catalog: TrackSchema[]
  activeKeys: string[]
  suggestedKeys: string[]
  fitScores: Record<string, number>
  selected: string
  onSelect: (trackKey: string) => void
}) {
  const labelOf = (k: string) => trackLabel(k, catalog.find(t => t.track_key === k)?.label)
  // Union of started ∪ suggested, started first, preserving order.
  const shown: string[] = []
  for (const k of [...activeKeys, ...suggestedKeys]) {
    if (!shown.includes(k)) shown.push(k)
  }
  const remaining = catalog.map(t => t.track_key).filter(k => !shown.includes(k))
  const activeSet = new Set(activeKeys)

  return (
    <div className="flex flex-wrap items-center gap-2">
      {shown.map(k => {
        const isSel = k === selected
        const started = activeSet.has(k)
        return (
          <button
            key={k}
            type="button"
            onClick={() => onSelect(k)}
            className={clsx(
              'inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-sm transition-colors',
              isSel
                ? 'border-secondary bg-secondary text-secondary-foreground'
                : 'border-border bg-background text-foreground hover:border-secondary/60',
            )}
          >
            {labelOf(k)}
            {started && fitScores[k] != null ? (
              <span
                className={clsx(
                  'rounded-full px-1.5 text-xs tabular-nums',
                  isSel ? 'bg-secondary-foreground/20' : 'bg-muted text-muted-foreground',
                )}
              >
                {fitScores[k]}
              </span>
            ) : !started ? (
              <span
                className={clsx(
                  'rounded-full px-1.5 text-[10px] uppercase',
                  isSel ? 'bg-secondary-foreground/20' : 'bg-muted text-muted-foreground',
                )}
              >
                suggested
              </span>
            ) : null}
          </button>
        )
      })}

      {remaining.length > 0 && (
        <select
          value=""
          onChange={e => e.target.value && onSelect(e.target.value)}
          className="rounded-full border border-dashed border-border bg-background px-3 py-1.5 text-sm text-muted-foreground focus:border-secondary focus:outline-none"
          aria-label="Add another track"
        >
          <option value="">+ Add track…</option>
          {remaining.map(k => (
            <option key={k} value={k}>
              {labelOf(k)}
            </option>
          ))}
        </select>
      )}
    </div>
  )
}
