import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Bell } from 'lucide-react'
import { confirmDialog } from '../../../stores/confirm-store'

import EmptyState from '../../../components/ui/EmptyState'
import QueryError from '../../../components/ui/QueryError'
import { SkeletonCard } from '../../../components/ui/Skeleton'
import { showToast } from '../../../stores/toast-store'
import {
  deleteSavedSearch,
  listSavedSearches,
  runSavedSearch,
  updateSavedSearch,
  type SavedSearch,
} from '../../../api/savedSearches'
import { exploreUrlFromSavedQuery } from '../explore/discovery/searchUrl'
import SavedSearchRow from './SavedSearchRow'

// Spec 56 §6 — the Saved-searches tab: list, toggle alerts (optimistic), run now,
// delete, and re-open a saved search in Match by restoring its exact URL state.

export default function SavedSearchesPanel() {
  const navigate = useNavigate()
  const qc = useQueryClient()

  const { data: searches = [], isLoading, isError, refetch } = useQuery({
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
      showToast("We couldn't update alerts. Please try again.", 'error')
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
    onError: () => showToast("We couldn't run that search. Please try again.", 'error'),
  })

  const deleteMut = useMutation({
    mutationFn: deleteSavedSearch,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['saved-searches'] })
      showToast('Saved search removed', 'success')
    },
    onError: () => showToast("We couldn't remove that search. Please try again.", 'error'),
  })

  const openInMatch = (s: SavedSearch) => navigate(exploreUrlFromSavedQuery(s.query))

  if (isLoading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 2 }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    )
  }

  if (isError) {
    // Don't misreport a failed load as "No saved searches yet" (data honesty).
    return <QueryError detail="We couldn't load your saved searches." onRetry={() => refetch()} />
  }

  if (searches.length === 0) {
    return (
      <EmptyState
        icon={<Bell size={48} />}
        title="No saved searches yet"
        action={{ label: 'Open Discover →', onClick: () => navigate('/s/explore') }}
      />
    )
  }

  return (
    <div className="space-y-4">
      {searches.map(s => (
        <SavedSearchRow
          key={s.id}
          search={s}
          onToggleAlert={() => toggleMut.mutate({ id: s.id, alert_enabled: !s.alert_enabled })}
          onRun={() => runMut.mutate(s.id)}
          onOpen={() => openInMatch(s)}
          onDelete={async () => {
            const ok = await confirmDialog({
              title: 'Delete this saved search and its alerts?',
              confirmLabel: 'Delete',
              destructive: true,
            })
            if (ok) deleteMut.mutate(s.id)
          }}
          togglePending={toggleMut.isPending && toggleMut.variables?.id === s.id}
          runPending={runMut.isPending && runMut.variables === s.id}
          deletePending={deleteMut.isPending && deleteMut.variables === s.id}
        />
      ))}
    </div>
  )
}
