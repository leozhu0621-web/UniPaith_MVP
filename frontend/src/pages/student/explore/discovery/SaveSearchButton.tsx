import { useEffect, useRef, useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Bell, BookmarkPlus, Check, X } from 'lucide-react'

import Button from '../../../../components/ui/Button'
import { showToast } from '../../../../stores/toast-store'
import { createSavedSearch } from '../../../../api/savedSearches'
import type { ConstraintChip, SearchFilters, SortOption } from '../../../../types/search'

// Spec 56 §6 — save the current search/filter set (named) from the Match UI.
// Captures the live Explore state (q + chips + filters + sort), which round-trips
// back via the same URL encoders. Optionally enables new-match alerts.

interface Props {
  query: string
  chips: ConstraintChip[]
  filters: SearchFilters
  sort: SortOption
}

function defaultName(chips: ConstraintChip[], query: string): string {
  const labels = chips.map(c => c.display).filter(Boolean)
  if (labels.length) return labels.slice(0, 3).join(' · ')
  if (query.trim()) return query.trim().slice(0, 60)
  return 'My search'
}

export default function SaveSearchButton({ query, chips, filters, sort }: Props) {
  const qc = useQueryClient()
  const [open, setOpen] = useState(false)
  const [name, setName] = useState('')
  const [alertEnabled, setAlertEnabled] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (open) {
      setName(defaultName(chips, query))
      // Defer focus until the popover is painted.
      requestAnimationFrame(() => inputRef.current?.focus())
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open])

  const createMut = useMutation({
    mutationFn: () =>
      createSavedSearch({
        name: name.trim() || defaultName(chips, query),
        entity_type: 'program',
        query: { query: query || null, chips, filters, sort },
        alert_enabled: alertEnabled,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['saved-searches'] })
      showToast(
        alertEnabled ? 'Search saved — we’ll alert you to new matches' : 'Search saved',
        'success',
      )
      setOpen(false)
      setAlertEnabled(false)
    },
    onError: (err: unknown) =>
      showToast((err as Error).message ?? 'Could not save this search', 'error'),
  })

  return (
    <div className="relative">
      <Button
        size="sm"
        variant="secondary"
        onClick={() => setOpen(o => !o)}
        aria-expanded={open}
        aria-haspopup="dialog"
      >
        <BookmarkPlus size={15} className="mr-1.5" />
        Save search
      </Button>

      {open && (
        <>
          {/* click-away */}
          <button
            type="button"
            aria-hidden
            tabIndex={-1}
            className="fixed inset-0 z-40 cursor-default"
            onClick={() => setOpen(false)}
          />
          <div
            role="dialog"
            aria-label="Save this search"
            className="absolute right-0 z-50 mt-2 w-72 rounded-xl border border-border bg-card p-4 elev-raised"
          >
            <div className="mb-2 flex items-center justify-between">
              <h3 className="text-sm font-semibold text-foreground">Save this search</h3>
              <button
                type="button"
                onClick={() => setOpen(false)}
                aria-label="Close"
                className="p-1 text-muted-foreground hover:text-foreground"
              >
                <X size={15} />
              </button>
            </div>
            <label className="block text-xs font-medium text-muted-foreground" htmlFor="saved-search-name">
              Name
            </label>
            <input
              id="saved-search-name"
              ref={inputRef}
              type="text"
              value={name}
              maxLength={120}
              onChange={e => setName(e.target.value)}
              onKeyDown={e => {
                if (e.key === 'Enter' && name.trim()) createMut.mutate()
                if (e.key === 'Escape') setOpen(false)
              }}
              className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground focus:border-secondary focus:outline-none focus:ring-2 focus:ring-ring"
            />
            <label className="mt-3 flex cursor-pointer items-start gap-2 text-sm text-foreground">
              <input
                type="checkbox"
                checked={alertEnabled}
                onChange={e => setAlertEnabled(e.target.checked)}
                className="mt-0.5 rounded border-border"
              />
              <span className="flex items-center gap-1.5">
                <Bell size={14} className="text-secondary" />
                Alert me to new matches
              </span>
            </label>
            <div className="mt-4 flex justify-end gap-2">
              <Button size="sm" variant="tertiary" onClick={() => setOpen(false)}>
                Cancel
              </Button>
              <Button
                size="sm"
                variant="secondary"
                loading={createMut.isPending}
                disabled={!name.trim()}
                onClick={() => createMut.mutate()}
              >
                <Check size={15} className="mr-1.5" />
                Save
              </Button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
