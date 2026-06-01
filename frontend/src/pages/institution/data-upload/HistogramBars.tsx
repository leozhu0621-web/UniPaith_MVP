import type { DatasetHistogramColumn } from '../../../types'

// Spec 24 §5 — per-column histogram. Cobalt bars only (no gold; operational).
export default function HistogramBars({ col }: { col: DatasetHistogramColumn }) {
  const max = Math.max(1, ...col.top.map((t) => t.count))
  if (col.top.length === 0) {
    return <p className="text-xs text-muted-foreground italic">No values</p>
  }
  return (
    <div className="space-y-1">
      {col.top.map((t) => (
        <div key={t.value} className="flex items-center gap-2">
          <span className="w-28 shrink-0 truncate text-xs text-foreground" title={t.value}>
            {t.value || <span className="italic text-muted-foreground">(blank)</span>}
          </span>
          <div className="h-3 flex-1 rounded-sm bg-muted">
            <div
              className="h-3 rounded-sm bg-secondary"
              style={{ width: `${Math.round((t.count / max) * 100)}%` }}
            />
          </div>
          <span className="w-8 shrink-0 text-right text-xs tabular-nums text-muted-foreground">
            {t.count}
          </span>
        </div>
      ))}
      <p className="pt-0.5 text-[11px] text-muted-foreground">
        {col.distinct} distinct{col.null_count > 0 ? ` · ${col.null_count} blank` : ''}
      </p>
    </div>
  )
}
