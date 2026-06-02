import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Bell } from 'lucide-react'

import EmptyState from '../../../components/ui/EmptyState'
import { SkeletonCard } from '../../../components/ui/Skeleton'
import { showToast } from '../../../stores/toast-store'
import {
  deleteSavedSearch,
  listSavedSearches,
  runSavedSearch,
  updateSavedSearch,
  type SavedSearch,
} from '../../../api/savedSearches'
import { encodeChipsParam } from '../explore/discovery/chipUtils'
import { encodeFiltersParam } from '../explore/discovery/filterUtils'
import SavedSearchRow from './SavedSearchRow'

// Spec 56 §6 — the Saved-searches tab: list, toggle alerts (optimistic), run now,
// delete, and re-open a saved search in Match by restoring its exact URL state.

export default function SavedSearchesPanel() {
  const navigate = useNavigate()
  const qc = useQueryClient()

  const { data: searches = [], isLoading } = useQuery({
    queryKey: ['saved-searches'],
    queryFn: listSavedSearches,
  })

  const toggleMut = useMutation({
    mutationFn: ({ id, alert_enabled }: { id: string; alert_enabled: boolean }) =>
      updateSavedSearch(id, { alert_enabled }),
    onMutate: async ({ id, alert_enabled }) => {
      await qc.cancelQueries({ queryKey: ['saved-searches'] })
      const prev = qc.getQueryData<SavedSearch[]>(['saved-searches'])
      qc.setQueryData<SavedSearch[]>(['saved-searches'], old =>
        (old ?? []).map(s => (s.id === id ? { ...s, alert_enabled } : s)),
      )
      return { prev }
    },
    onError: (_err, _vars, ctx) => {
      if (ctx?.prev) qc.setQueryData(['saved-searches'], ctx.prev)
      showToast('Could not update alerts', 'error')
    },
    onSuccess: (_data, vars) =>
      showToast(vars.alert_enabled ? 'Alerts on for this search' : 'Alerts off', 'success'),
    onSettled: () => qc.invalidateQueries({ queryKey: ['saved-searches'] }),
  })

  const runMut = useMutation({
    mutationFn: runSavedSearch,
    onSuccess: res => {
      qc.invalidateQueries({ queryKey: ['saved-searches'] })
      showToast(`${res.count} program${res.count === 1 ? '' : 's'} match this search`, 'success')
    },
    onError: () => showToast('Could not run that search', 'error'),
  })

  const deleteMut = useMutation({
    mutationFn: deleteSavedSearch,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['saved-searches'] })
      showToast('Saved search removed', 'success')
    },
    onError: () => showToast('Could not delete that search', 'error'),
  })

  const openInMatch = (s: SavedSearch) => {
    const p = new URLSearchParams()
    const q = s.query?.query
    if (q && q.trim()) p.set('q', q.trim())
    if (s.query?.chips && s.query.chips.length) p.set('chips', encodeChipsParam(s.query.chips))
    if (s.query?.filters && Object.keys(s.query.filters).length)
      p.set('filters', encodeFiltersParam(s.query.filters))
    if (s.query?.sort && s.query.sort !== 'relevance') p.set('sort', s.query.sort)
    navigate(`/s/explore?${p.toString()}`)
  }

  if (isLoading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 2 }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    )
  }

  if (searches.length === 0) {
    return (
      <EmptyState
        icon={<Bell size={48} />}
        title="No saved searches yet"
        description="Run a search in Match, then “Save search” to keep it here — turn on alerts and we’ll tell you when new programs match."
        action={{ label: 'Open Match →', onClick: () => navigate('/s/explore') }}
      />
    )
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">
        Saved searches keep your filters in one tap. Turn on alerts and we’ll notify you when new
        programs match — consent-aware, never more than a few a day.
      </p>
      {searches.map(s => (
        <SavedSearchRow
          key={s.id}
          search={s}
          onToggleAlert={() => toggleMut.mutate({ id: s.id, alert_enabled: !s.alert_enabled })}
          onRun={() => runMut.mutate(s.id)}
          onOpen={() => openInMatch(s)}
          onDelete={() => deleteMut.mutate(s.id)}
          togglePending={toggleMut.isPending && toggleMut.variables?.id === s.id}
          runPending={runMut.isPending && runMut.variables === s.id}
          deletePending={deleteMut.isPending && deleteMut.variables === s.id}
        />
      ))}
    </div>
  )
}
