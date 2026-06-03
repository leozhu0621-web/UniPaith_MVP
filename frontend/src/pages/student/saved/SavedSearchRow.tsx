import { Bell, BellOff, Play, Search, Trash2 } from 'lucide-react'

import Button from '../../../components/ui/Button'
import type { SavedSearch } from '../../../api/savedSearches'

// Spec 56 §6 — one saved search: what it searches, its last match count, an
// alert toggle, and run / open / delete actions.

function querySummary(s: SavedSearch): string[] {
  const labels = (s.query?.chips ?? []).map(c => c.display).filter(Boolean)
  const filterCount = s.query?.filters ? Object.keys(s.query.filters).length : 0
  const parts = labels.slice(0, 4)
  if (filterCount > 0) parts.push(`+${filterCount} filter${filterCount === 1 ? '' : 's'}`)
  if (parts.length === 0 && s.query?.query) parts.push(`“${s.query.query}”`)
  return parts
}

function AlertToggle({
  enabled,
  pending,
  onToggle,
}: {
  enabled: boolean
  pending: boolean
  onToggle: () => void
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={enabled}
      aria-label={enabled ? 'Disable new-match alerts' : 'Enable new-match alerts'}
      disabled={pending}
      onClick={onToggle}
      className={`inline-flex items-center gap-1.5 rounded-pill border px-2.5 py-1 text-xs font-semibold transition-colors disabled:opacity-60 ${
        enabled
          ? 'border-secondary/40 bg-secondary/10 text-secondary'
          : 'border-border bg-card text-muted-foreground hover:bg-muted'
      }`}
    >
      {enabled ? <Bell size={13} /> : <BellOff size={13} />}
      {enabled ? 'Alerts on' : 'Alerts off'}
    </button>
  )
}

export default function SavedSearchRow({
  search,
  onToggleAlert,
  onRun,
  onOpen,
  onDelete,
  togglePending,
  runPending,
  deletePending,
}: {
  search: SavedSearch
  onToggleAlert: () => void
  onRun: () => void
  onOpen: () => void
  onDelete: () => void
  togglePending: boolean
  runPending: boolean
  deletePending: boolean
}) {
  const summary = querySummary(search)
  const count = search.last_match_count

  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <h3 className="truncate text-base font-semibold text-foreground">{search.name}</h3>
          <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
            {summary.length > 0 ? (
              summary.map(part => (
                <span
                  key={part}
                  className="rounded-pill bg-muted px-2 py-0.5 text-[11px] font-medium text-muted-foreground"
                >
                  {part}
                </span>
              ))
            ) : (
              <span className="text-[11px] text-muted-foreground">All programs</span>
            )}
          </div>
          <p className="mt-2 text-xs text-muted-foreground">
            {count != null && search.last_run_at
              ? `${count} match${count === 1 ? '' : 'es'} at last run`
              : 'Not run yet'}
          </p>
        </div>

        <AlertToggle enabled={search.alert_enabled} pending={togglePending} onToggle={onToggleAlert} />
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-2 border-t border-border pt-3">
        <Button size="sm" variant="secondary" onClick={onOpen}>
          <Search size={14} className="mr-1.5" />
          Open in Match
        </Button>
        <Button size="sm" variant="tertiary" loading={runPending} onClick={onRun}>
          <Play size={14} className="mr-1.5" />
          Run now
        </Button>
        <button
          type="button"
          onClick={onDelete}
          disabled={deletePending}
          aria-label="Delete saved search"
          className="ml-auto inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium text-muted-foreground hover:bg-warning-soft hover:text-warning disabled:opacity-60"
        >
          <Trash2 size={14} />
          Delete
        </button>
      </div>
    </div>
  )
}
