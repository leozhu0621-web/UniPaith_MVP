import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  listSaved,
  listSavedTagSuggestions,
  unsaveProgram,
  patchSavedProgram,
  startApplicationFromSaved,
} from '../../api/saved-lists'
import { listSavedSearches } from '../../api/savedSearches'
import { qk } from '../../api/queryKeys'
import { getMyFollows, unfollowInstitution } from '../../api/events'
import SavedSearchesPanel from './saved/SavedSearchesPanel'
import Button from '../../components/ui/Button'
import EmptyState from '../../components/ui/EmptyState'
import QueryError from '../../components/ui/QueryError'
import { PageContainer, PageHeader } from '../../components/student/density'
import BandBadge from '../../components/ui/BandBadge'
import { SkeletonCard } from '../../components/ui/Skeleton'
import { showToast } from '../../stores/toast-store'
import { MAX_COMPARE, useCompareStore } from '../../stores/compare-store'
import usePageTitle from '../../hooks/usePageTitle'
import { Bookmark, GraduationCap } from 'lucide-react'
import type { MatchBand, SavedPriority, SavedProgram } from '../../types'
import SavedProgramRow, { PRIORITY_CONFIG, PRIORITY_ORDER } from './saved/SavedProgramRow'
import SavedSchoolCard from './saved/SavedSchoolCard'
import { programSummaryOf, sortSavedPrograms, type SortKey } from './saved/savedUtils'

type Tab = 'programs' | 'schools' | 'searches'
type ViewMode = 'tier' | 'priority' | 'flat'
type FilterKey = 'all' | SavedPriority

const BAND_ORDER: MatchBand[] = ['reach', 'target', 'safer']
const BAND_EYEBROW: Record<MatchBand, string> = {
  reach: 'Reach',
  target: 'Target',
  safer: 'Safer',
}

export default function SavedListPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const compareStore = useCompareStore()
  const [searchParams, setSearchParams] = useSearchParams()

  const tabParam = searchParams.get('tab')
  const [tab, setTab] = useState<Tab>(
    tabParam === 'schools' || tabParam === 'searches' ? tabParam : 'programs',
  )
  const selectTab = (t: Tab) => {
    setTab(t)
    const p = new URLSearchParams(searchParams)
    if (t === 'programs') p.delete('tab')
    else p.set('tab', t)
    setSearchParams(p, { replace: true })
  }
  const [viewMode, setViewMode] = useState<ViewMode>('tier')
  const [sortKey, setSortKey] = useState<SortKey>('fitness_score')
  const [filterKey, setFilterKey] = useState<FilterKey>('all')
  const [showDropped, setShowDropped] = useState(false)
  const [bulkBusy, setBulkBusy] = useState(false)

  const { data: saved, isLoading, isError, refetch } = useQuery({
    queryKey: qk.savedPrograms(),
    queryFn: listSaved,
    retry: 1,
  })
  const { data: tagSuggestions = [] } = useQuery({
    queryKey: ['saved-tags'],
    queryFn: listSavedTagSuggestions,
  })
  const { data: follows = [] } = useQuery({ queryKey: ['my-follows'], queryFn: getMyFollows })
  const { data: savedSearches = [] } = useQuery({
    queryKey: ['saved-searches'],
    queryFn: listSavedSearches,
  })

  usePageTitle('Saved')

  useEffect(() => {
    if (!compareStore.hydrated) compareStore.hydrate()
  }, [compareStore])

  const programs: SavedProgram[] = useMemo(() => (Array.isArray(saved) ? saved : []), [saved])

  const removeMut = useMutation({
    mutationFn: unsaveProgram,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: qk.savedPrograms() })
      queryClient.invalidateQueries({ queryKey: ['saved-tags'] })
      showToast('Removed from your shortlist', 'success')
    },
    onError: (err: unknown) =>
      showToast((err as Error).message ?? 'Could not remove this program', 'error'),
  })

  const patchMut = useMutation({
    mutationFn: ({
      programId,
      body,
    }: {
      programId: string
      body: { priority?: SavedPriority; notes?: string; tags?: string[] }
    }) => patchSavedProgram(programId, body),
    onSuccess: (_data, vars) => {
      queryClient.invalidateQueries({ queryKey: qk.savedPrograms() })
      queryClient.invalidateQueries({ queryKey: ['saved-tags'] })
      if (vars.body.priority) showToast('Priority updated', 'success')
      if (vars.body.notes !== undefined) showToast('Notes saved', 'success')
      if (vars.body.tags) showToast('Tags updated', 'success')
    },
    onError: (err: unknown) =>
      showToast((err as Error).message ?? 'Could not update saved program', 'error'),
  })

  const unfollowMut = useMutation({
    mutationFn: unfollowInstitution,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['my-follows'] })
      showToast('School removed from saved list', 'success')
    },
  })

  const startAppMut = useMutation({
    mutationFn: startApplicationFromSaved,
    onSuccess: data => {
      queryClient.invalidateQueries({ queryKey: qk.savedPrograms() })
      queryClient.invalidateQueries({ queryKey: ['my-applications'] })
      showToast('Application started', 'success')
      navigate(`/s/applications/${data.app_id}`)
    },
    onError: (err: unknown) =>
      showToast((err as Error).message ?? 'Could not start application', 'error'),
  })

  const filtered = useMemo(() => {
    let list = programs
    if (filterKey !== 'all') {
      list = list.filter(sp => sp.priority === filterKey)
    } else if (!showDropped) {
      list = list.filter(sp => sp.priority !== 'dropped')
    }
    return sortSavedPrograms(list, sortKey)
  }, [programs, filterKey, sortKey, showDropped])

  const tierGroups = useMemo(() => {
    const groups: Record<MatchBand, SavedProgram[]> = { reach: [], target: [], safer: [] }
    const unmatched: SavedProgram[] = []
    for (const sp of filtered) {
      const band = sp.band_label
      if (band && band in groups) groups[band as MatchBand].push(sp)
      else unmatched.push(sp)
    }
    return { groups, unmatched }
  }, [filtered])

  const priorityGroups = useMemo(() => {
    const groups: Record<SavedPriority, SavedProgram[]> = {
      considering: [],
      planning_to_apply: [],
      applied: [],
      dropped: [],
    }
    for (const sp of filtered) groups[sp.priority].push(sp)
    return groups
  }, [filtered])

  const priorityCounts = useMemo(() => {
    const counts: Record<string, number> = { all: programs.length }
    PRIORITY_ORDER.forEach(p => {
      counts[p] = programs.filter(sp => sp.priority === p).length
    })
    return counts
  }, [programs])

  const allTags = useMemo(() => {
    const set = new Set<string>(tagSuggestions)
    programs.forEach(sp => sp.tags?.forEach(t => set.add(t)))
    return Array.from(set).sort()
  }, [programs, tagSuggestions])

  const toggleCompare = (sp: SavedProgram) => {
    const prog = programSummaryOf(sp)
    if (compareStore.has(sp.program_id)) {
      compareStore.remove(sp.program_id)
      return
    }
    if (compareStore.isFull()) {
      showToast(`You can compare up to ${MAX_COMPARE} programs. Remove one to add another.`, 'warning')
      return
    }
    compareStore.add({
      program_id: sp.program_id,
      program_name: prog.program_name,
      institution_name: prog.institution_name ?? sp.institution_name ?? '',
      degree_type: prog.degree_type,
    })
  }

  const runCompareSelected = () => {
    if (compareStore.items.length < 2) {
      showToast('Select at least 2 programs to compare.', 'info')
      return
    }
    setBulkBusy(true)
    compareStore.requestCompareRun()
    setTimeout(() => setBulkBusy(false), 800)
  }

  const renderRow = (sp: SavedProgram) => (
    <SavedProgramRow
      key={sp.id}
      item={sp}
      comparing={compareStore.has(sp.program_id)}
      compareDisabled={bulkBusy}
      onToggleCompare={() => toggleCompare(sp)}
      onPriorityChange={priority =>
        patchMut.mutate({ programId: sp.program_id, body: { priority } })
      }
      onRemove={() => removeMut.mutate(sp.program_id)}
      onStartApplication={() => startAppMut.mutate(sp.program_id)}
      onSaveNotes={notes => patchMut.mutate({ programId: sp.program_id, body: { notes } })}
      onSaveTags={tags => patchMut.mutate({ programId: sp.program_id, body: { tags } })}
      onView={() => navigate(`/s/programs/${sp.program_id}`)}
      tagSuggestions={allTags}
      priorityPending={patchMut.isPending}
      startAppPending={startAppMut.isPending}
      removePending={removeMut.isPending}
    />
  )

  const renderTierSection = (band: MatchBand, items: SavedProgram[]) => {
    if (items.length === 0) return null
    return (
      <section key={band} className="space-y-4">
        <div className="flex items-center gap-2 border-b border-border pb-2">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
            {BAND_EYEBROW[band]}
          </span>
          <BandBadge band={band} size="sm" />
          <span className="text-xs text-muted-foreground">({items.length})</span>
        </div>
        <div className="stagger-list space-y-4">{items.map(renderRow)}</div>
      </section>
    )
  }

  if (isLoading) {
    return (
      <PageContainer className="space-y-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </PageContainer>
    )
  }

  if (isError && programs.length === 0) {
    return (
      <PageContainer>
        <QueryError detail="We couldn't load your saved list." onRetry={() => refetch()} />
      </PageContainer>
    )
  }

  return (
    <PageContainer className="pb-28">
      {/* Room header — consistent with the other My Space rooms (eyebrow = surface). */}
      <PageHeader
        eyebrow="My Space"
        title="Your shortlist"
        sub="Curate programs you are serious about, then compare and start applications when you are ready."
      />

      {/* Hidden on lg+ where the My Space rail's Saved group lists these views
          (Spec 2026-06-15 §A follow-up); kept below lg where the rail collapses
          to flat pills. */}
      <div className="lg:hidden flex gap-1 border-b border-border mb-5">
        <button
          type="button"
          onClick={() => selectTab('programs')}
          className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
            tab === 'programs'
              ? 'border-secondary text-secondary'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          Programs ({programs.length})
        </button>
        <button
          type="button"
          onClick={() => selectTab('schools')}
          className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
            tab === 'schools'
              ? 'border-secondary text-secondary'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          Schools ({follows.length})
        </button>
        <button
          type="button"
          onClick={() => selectTab('searches')}
          className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
            tab === 'searches'
              ? 'border-secondary text-secondary'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          Searches ({savedSearches.length})
        </button>
      </div>

      {tab === 'searches' ? (
        <SavedSearchesPanel />
      ) : tab === 'schools' ? (
        follows.length === 0 ? (
          <EmptyState
            icon={<GraduationCap size={48} />}
            title="No saved schools yet"
            description="Follow a school from its profile to bookmark it here."
            action={{ label: 'Open Match →', onClick: () => navigate('/s/explore') }}
          />
        ) : (
          <div className="stagger-list grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {follows.map(f => (
              <SavedSchoolCard
                key={f.institution_id}
                school={f}
                onOpen={() => navigate(`/s/institutions/${f.institution_id}`)}
                onUnfollow={() => unfollowMut.mutate(f.institution_id)}
                unfollowing={unfollowMut.isPending}
              />
            ))}
          </div>
        )
      ) : programs.length === 0 ? (
        <EmptyState
          icon={<Bookmark size={48} />}
          title="Your shortlist is empty"
          description="Save programs from Match or Discovery to see them here."
          action={{ label: 'Open Match →', onClick: () => navigate('/s/explore') }}
        />
      ) : (
        <>
          {isError && (
            <p className="text-sm text-warning mb-4 rounded-lg border border-warning/30 bg-warning-soft px-3 py-2">
              We could not refresh your list. Showing the last saved copy if available.
            </p>
          )}

          <div className="flex flex-wrap items-center gap-3 mb-5 p-3 rounded-xl border border-border bg-muted/20">
            <label className="flex items-center gap-1.5 text-xs text-muted-foreground">
              View
              <select
                value={viewMode}
                onChange={e => setViewMode(e.target.value as ViewMode)}
                className="text-xs font-medium border border-border rounded-md px-2 py-1 bg-card text-foreground"
              >
                <option value="tier">Grouped by tier</option>
                <option value="priority">Grouped by priority</option>
                <option value="flat">Flat list</option>
              </select>
            </label>
            <label className="flex items-center gap-1.5 text-xs text-muted-foreground">
              Sort
              <select
                value={sortKey}
                onChange={e => setSortKey(e.target.value as SortKey)}
                className="text-xs font-medium border border-border rounded-md px-2 py-1 bg-card text-foreground"
              >
                <option value="fitness_score">Fitness score</option>
                <option value="date_added">Date added</option>
                <option value="deadline">Deadline</option>
              </select>
            </label>
            <label className="flex items-center gap-1.5 text-xs text-muted-foreground">
              Filter
              <select
                value={filterKey}
                onChange={e => setFilterKey(e.target.value as FilterKey)}
                className="text-xs font-medium border border-border rounded-md px-2 py-1 bg-card text-foreground"
              >
                <option value="all">All ({priorityCounts.all})</option>
                {PRIORITY_ORDER.map(p => (
                  <option key={p} value={p}>
                    {PRIORITY_CONFIG[p].label} ({priorityCounts[p] ?? 0})
                  </option>
                ))}
              </select>
            </label>
            {filterKey === 'all' && (priorityCounts.dropped ?? 0) > 0 && (
              <label className="flex items-center gap-1.5 text-xs text-muted-foreground cursor-pointer">
                <input
                  type="checkbox"
                  checked={showDropped}
                  onChange={e => setShowDropped(e.target.checked)}
                  className="rounded border-border"
                />
                Show dropped ({priorityCounts.dropped})
              </label>
            )}
          </div>

          {filtered.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-8">
              No programs match this filter. Try showing dropped items or clearing the filter.
            </p>
          ) : viewMode === 'tier' ? (
            <div className="space-y-8">
              {BAND_ORDER.map(b => renderTierSection(b, tierGroups.groups[b]))}
              {tierGroups.unmatched.length > 0 && (
                <section className="space-y-4">
                  <div className="flex items-center gap-2 border-b border-border pb-2">
                    <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                      Unmatched
                    </span>
                    <span className="text-xs text-muted-foreground">
                      ({tierGroups.unmatched.length})
                    </span>
                  </div>
                  <div className="stagger-list space-y-4">{tierGroups.unmatched.map(renderRow)}</div>
                </section>
              )}
            </div>
          ) : viewMode === 'priority' ? (
            <div className="space-y-8">
              {PRIORITY_ORDER.map(p => {
                const items = priorityGroups[p]
                if (items.length === 0) return null
                return (
                  <section key={p} className="space-y-4">
                    <div className="flex items-center gap-2 border-b border-border pb-2">
                      <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                        {PRIORITY_CONFIG[p].label}
                      </span>
                      <span className="text-xs text-muted-foreground">({items.length})</span>
                    </div>
                    <div className="stagger-list space-y-4">{items.map(renderRow)}</div>
                  </section>
                )
              })}
            </div>
          ) : (
            <div className="stagger-list space-y-4">{filtered.map(renderRow)}</div>
          )}
        </>
      )}

      {tab === 'programs' && compareStore.items.length >= 1 && (
        <div className="fixed inset-x-0 bottom-[calc(56px+env(safe-area-inset-bottom))] lg:bottom-0 z-30 flex justify-center px-4 pb-3 pointer-events-none">
          <div className="pointer-events-auto bg-card border border-border elev-raised rounded-xl px-4 py-3 flex items-center gap-3 max-w-lg w-full">
            <span className="text-xs text-muted-foreground flex-1">
              {compareStore.items.length} selected for compare
            </span>
            <Button
              size="sm"
              variant="secondary"
              disabled={compareStore.items.length < 2 || bulkBusy}
              loading={bulkBusy}
              onClick={runCompareSelected}
            >
              Compare selected ({compareStore.items.length}) →
            </Button>
          </div>
        </div>
      )}
    </PageContainer>
  )
}
