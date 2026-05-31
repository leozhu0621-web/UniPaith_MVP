import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  listSaved,
  listSavedTagSuggestions,
  unsaveProgram,
  patchSavedProgram,
  startApplicationFromSaved,
} from '../../api/saved-lists'
import { getMyFollows } from '../../api/events'
import ProgramCard from './explore/cards/ProgramCard'
import Button from '../../components/ui/Button'
import Modal from '../../components/ui/Modal'
import Badge from '../../components/ui/Badge'
import EmptyState from '../../components/ui/EmptyState'
import BandBadge from '../../components/ui/BandBadge'
import { SkeletonCard } from '../../components/ui/Skeleton'
import { showToast } from '../../stores/toast-store'
import { MAX_COMPARE, useCompareStore } from '../../stores/compare-store'
import usePageTitle from '../../hooks/usePageTitle'
import {
  Bookmark,
  ChevronDown,
  FileText,
  GraduationCap,
  MapPin,
  Pencil,
  Plus,
  X,
} from 'lucide-react'
import type {
  MatchBand,
  MatchResult,
  ProgramSummary,
  SavedPriority,
  SavedProgram,
  SavedStatus,
} from '../../types'

type Tab = 'programs' | 'schools'
type ViewMode = 'tier' | 'priority' | 'flat'
type SortKey = 'match_score' | 'date_added' | 'deadline'
type FilterKey = 'all' | SavedPriority

const PRIORITY_CONFIG: Record<SavedPriority, { label: string; color: string }> = {
  considering: { label: 'Considering', color: 'bg-muted text-charcoal' },
  planning_to_apply: { label: 'Planning to apply', color: 'bg-cobalt/10 text-cobalt' },
  applied: { label: 'Applied', color: 'bg-success-soft text-success' },
  dropped: { label: 'Dropped', color: 'bg-error-soft text-error' },
}
const PRIORITY_ORDER: SavedPriority[] = [
  'considering',
  'planning_to_apply',
  'applied',
  'dropped',
]

const STATUS_LABELS: Record<SavedStatus, string> = {
  considering: 'Considering',
  application_started: 'Application started',
  submitted: 'Submitted',
  accepted: 'Accepted',
  rejected: 'Rejected',
  waitlisted: 'Waitlisted',
  dropped: 'Dropped',
}

const BAND_ORDER: MatchBand[] = ['reach', 'target', 'safer']
const BAND_EYEBROW: Record<MatchBand, string> = {
  reach: 'Reach',
  target: 'Target',
  safer: 'Safer',
}

function bandToTier(band?: MatchBand | null): number {
  if (band === 'reach') return 1
  if (band === 'target') return 2
  if (band === 'safer') return 3
  return 0
}

function programSummaryOf(sp: SavedProgram): ProgramSummary {
  const p = sp.program
  if (p) return p
  return {
    id: sp.program_id,
    institution_id: '',
    program_name: sp.program_name ?? 'Program',
    degree_type: 'masters',
    institution_name: sp.institution_name ?? '',
    institution_country: '',
  } as ProgramSummary
}

function matchOf(sp: SavedProgram): MatchResult | undefined {
  if (sp.fitness_score == null) return undefined
  const tier = bandToTier(sp.band_label)
  return {
    id: sp.id,
    student_id: '',
    program_id: sp.program_id,
    match_score: sp.fitness_score,
    match_tier: tier || 2,
    score_breakdown: null,
    reasoning_text: null,
    model_version: null,
    computed_at: sp.added_at,
    is_stale: false,
  }
}

function sortPrograms(list: SavedProgram[], sortKey: SortKey): SavedProgram[] {
  return [...list].sort((a, b) => {
    if (sortKey === 'match_score') {
      const sa = a.fitness_score ?? -1
      const sb = b.fitness_score ?? -1
      return sb - sa
    }
    if (sortKey === 'deadline') {
      const da = a.program?.application_deadline ?? '9999'
      const db = b.program?.application_deadline ?? '9999'
      return da.localeCompare(db)
    }
    return new Date(b.added_at).getTime() - new Date(a.added_at).getTime()
  })
}

export default function SavedListPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const compareStore = useCompareStore()

  const [tab, setTab] = useState<Tab>('programs')
  const [viewMode, setViewMode] = useState<ViewMode>('tier')
  const [sortKey, setSortKey] = useState<SortKey>('match_score')
  const [filterKey, setFilterKey] = useState<FilterKey>('all')
  const [editingNotes, setEditingNotes] = useState<{ id: string; notes: string } | null>(null)
  const [editingTags, setEditingTags] = useState<{ id: string; tags: string[]; input: string } | null>(
    null,
  )
  const [bulkBusy, setBulkBusy] = useState(false)

  const { data: saved, isLoading } = useQuery({ queryKey: ['saved'], queryFn: listSaved })
  const { data: tagSuggestions = [] } = useQuery({
    queryKey: ['saved-tags'],
    queryFn: listSavedTagSuggestions,
  })
  const { data: follows = [] } = useQuery({ queryKey: ['my-follows'], queryFn: getMyFollows })

  usePageTitle('Saved')

  const programs: SavedProgram[] = useMemo(() => (Array.isArray(saved) ? saved : []), [saved])

  const removeMut = useMutation({
    mutationFn: unsaveProgram,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['saved'] })
      queryClient.invalidateQueries({ queryKey: ['saved-tags'] })
      showToast('Removed from your shortlist', 'success')
    },
  })

  const patchMut = useMutation({
    mutationFn: ({
      programId,
      body,
    }: {
      programId: string
      body: { priority?: SavedPriority; notes?: string; tags?: string[] }
    }) => patchSavedProgram(programId, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['saved'] })
      queryClient.invalidateQueries({ queryKey: ['saved-tags'] })
    },
  })

  const startAppMut = useMutation({
    mutationFn: startApplicationFromSaved,
    onSuccess: data => {
      queryClient.invalidateQueries({ queryKey: ['saved'] })
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
    }
    return sortPrograms(list, sortKey)
  }, [programs, filterKey, sortKey])

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

  const renderProgramRow = (sp: SavedProgram) => {
    const prog = programSummaryOf(sp)
    const match = matchOf(sp)
    const isDropped = sp.priority === 'dropped'
    const inCompare = compareStore.has(sp.program_id)
    const canStart =
      sp.status === 'considering' && sp.priority !== 'dropped' && sp.priority !== 'applied'

    return (
      <div
        key={sp.id}
        className={`relative ${isDropped ? 'opacity-70' : ''}`}
      >
        <div className="absolute left-3 top-4 z-10 flex flex-col gap-2">
          <input
            type="checkbox"
            checked={inCompare}
            onChange={() => toggleCompare(sp)}
            disabled={bulkBusy}
            aria-label={`Add ${prog.program_name} to compare`}
            className="rounded border-stone"
          />
        </div>
        <div className="pl-8">
          <div className="flex flex-wrap items-center gap-2 mb-2">
            <div className="relative inline-block">
              <select
                value={sp.priority}
                onChange={e =>
                  patchMut.mutate({
                    programId: sp.program_id,
                    body: { priority: e.target.value as SavedPriority },
                  })
                }
                disabled={patchMut.isPending}
                className={`appearance-none text-xs font-medium rounded-full pl-2.5 pr-6 py-0.5 border-0 cursor-pointer ${PRIORITY_CONFIG[sp.priority].color}`}
              >
                {PRIORITY_ORDER.map(p => (
                  <option key={p} value={p}>
                    {PRIORITY_CONFIG[p].label}
                  </option>
                ))}
              </select>
              <ChevronDown
                size={10}
                className="absolute right-1.5 top-1/2 -translate-y-1/2 pointer-events-none text-slate/60"
              />
            </div>
            <Badge variant="neutral" size="sm">
              {STATUS_LABELS[sp.status] ?? sp.status}
            </Badge>
            {sp.tags.map(tag => (
              <span
                key={tag}
                className="text-[10px] px-2 py-0.5 rounded-full bg-muted text-slate border border-stone/50"
              >
                {tag}
              </span>
            ))}
            <button
              type="button"
              onClick={() =>
                setEditingTags({ id: sp.program_id, tags: [...sp.tags], input: '' })
              }
              className="text-[10px] text-cobalt font-medium hover:underline inline-flex items-center gap-0.5"
            >
              <Plus size={10} /> Add tag
            </button>
            {canStart && (
              <Button
                size="sm"
                variant="secondary"
                onClick={() => startAppMut.mutate(sp.program_id)}
                loading={startAppMut.isPending}
                className="text-xs"
              >
                <FileText size={12} className="mr-1" />
                Start application →
              </Button>
            )}
            <Button
              size="sm"
              variant="ghost"
              onClick={() => setEditingNotes({ id: sp.program_id, notes: sp.notes || '' })}
              className="text-xs"
            >
              <Pencil size={12} className="mr-1" />
              {sp.notes ? 'Notes' : '+ Add notes'}
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => removeMut.mutate(sp.program_id)}
              loading={removeMut.isPending}
              className="text-xs text-error"
            >
              Remove
            </Button>
          </div>
          {sp.notes && (
            <p className="text-xs text-slate mb-2 italic line-clamp-2">&ldquo;{sp.notes}&rdquo;</p>
          )}
          <ProgramCard
            program={prog}
            saved
            match={match}
            comparing={inCompare}
            onSave={() => removeMut.mutate(sp.program_id)}
            onCompare={() => toggleCompare(sp)}
            onView={() => navigate(`/s/programs/${sp.program_id}`)}
          />
        </div>
      </div>
    )
  }

  const renderTierSection = (band: MatchBand, items: SavedProgram[]) => {
    if (items.length === 0) return null
    return (
      <section key={band} className="space-y-4">
        <div className="flex items-center gap-2 border-b border-divider pb-2">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
            {BAND_EYEBROW[band]}
          </span>
          <BandBadge band={band} size="sm" />
          <span className="text-xs text-slate/60">({items.length})</span>
        </div>
        <div className="space-y-6">{items.map(renderProgramRow)}</div>
      </section>
    )
  }

  if (isLoading) {
    return (
      <div className="p-6 max-w-5xl mx-auto space-y-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    )
  }

  return (
    <div className="p-6 max-w-5xl mx-auto pb-28">
      <header className="mb-6">
        <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground mb-1">
          Saved
        </p>
        <h1 className="text-2xl font-semibold text-foreground">Your shortlist</h1>
      </header>

      <div className="flex gap-1 border-b border-divider mb-5">
        <button
          type="button"
          onClick={() => setTab('programs')}
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
          onClick={() => setTab('schools')}
          className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
            tab === 'schools'
              ? 'border-secondary text-secondary'
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          Schools ({follows.length})
        </button>
      </div>

      {tab === 'schools' ? (
        follows.length === 0 ? (
          <EmptyState
            icon={<GraduationCap size={48} />}
            title="No saved schools yet"
            description="Follow a school from its profile to bookmark it here."
            action={{ label: 'Open Match →', onClick: () => navigate('/s/explore') }}
          />
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {follows.map(f => (
              <button
                key={f.institution_id}
                type="button"
                onClick={() => navigate(`/s/institutions/${f.institution_id}`)}
                className="text-left bg-white rounded-lg border border-stone hover:shadow-md transition-all p-4 flex gap-3"
              >
                <div className="w-10 h-10 rounded-lg bg-muted border border-stone/60 flex items-center justify-center flex-shrink-0">
                  <GraduationCap size={18} className="text-cobalt" />
                </div>
                <div className="min-w-0">
                  <p className="font-semibold text-sm text-charcoal truncate">{f.name}</p>
                  <p className="text-xs text-slate flex items-center gap-1 mt-0.5">
                    <MapPin size={10} /> Saved school
                  </p>
                </div>
              </button>
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
          <div className="flex flex-wrap items-center gap-3 mb-5">
            <label className="flex items-center gap-1.5 text-xs text-slate">
              View
              <select
                value={viewMode}
                onChange={e => setViewMode(e.target.value as ViewMode)}
                className="text-xs font-medium border border-divider rounded-md px-2 py-1 bg-card"
              >
                <option value="tier">Grouped by tier</option>
                <option value="priority">Grouped by priority</option>
                <option value="flat">Flat list</option>
              </select>
            </label>
            <label className="flex items-center gap-1.5 text-xs text-slate">
              Sort
              <select
                value={sortKey}
                onChange={e => setSortKey(e.target.value as SortKey)}
                className="text-xs font-medium border border-divider rounded-md px-2 py-1 bg-card"
              >
                <option value="match_score">Match score</option>
                <option value="date_added">Date added</option>
                <option value="deadline">Deadline</option>
              </select>
            </label>
            <label className="flex items-center gap-1.5 text-xs text-slate">
              Filter
              <select
                value={filterKey}
                onChange={e => setFilterKey(e.target.value as FilterKey)}
                className="text-xs font-medium border border-divider rounded-md px-2 py-1 bg-card"
              >
                <option value="all">All ({priorityCounts.all})</option>
                {PRIORITY_ORDER.map(p => (
                  <option key={p} value={p}>
                    {PRIORITY_CONFIG[p].label} ({priorityCounts[p] ?? 0})
                  </option>
                ))}
              </select>
            </label>
          </div>

          {viewMode === 'tier' && (
            <div className="space-y-8">
              {BAND_ORDER.map(b => renderTierSection(b, tierGroups.groups[b]))}
              {tierGroups.unmatched.length > 0 && (
                <section className="space-y-4">
                  <div className="flex items-center gap-2 border-b border-divider pb-2">
                    <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                      Unmatched
                    </span>
                    <span className="text-xs text-slate/60">({tierGroups.unmatched.length})</span>
                  </div>
                  <div className="space-y-6">{tierGroups.unmatched.map(renderProgramRow)}</div>
                </section>
              )}
            </div>
          )}

          {viewMode === 'priority' && (
            <div className="space-y-8">
              {PRIORITY_ORDER.map(p => {
                const items = priorityGroups[p]
                if (items.length === 0) return null
                return (
                  <section key={p} className="space-y-4">
                    <div className="flex items-center gap-2 border-b border-divider pb-2">
                      <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                        {PRIORITY_CONFIG[p].label}
                      </span>
                      <span className="text-xs text-slate/60">({items.length})</span>
                    </div>
                    <div className="space-y-6">{items.map(renderProgramRow)}</div>
                  </section>
                )
              })}
            </div>
          )}

          {viewMode === 'flat' && (
            <div className="space-y-6">{filtered.map(renderProgramRow)}</div>
          )}
        </>
      )}

      {tab === 'programs' && compareStore.items.length >= 1 && (
        <div className="fixed inset-x-0 bottom-[calc(56px+env(safe-area-inset-bottom))] lg:bottom-0 z-30 flex justify-center px-4 pb-3 pointer-events-none">
          <div className="pointer-events-auto bg-card border border-border elev-raised rounded-xl px-4 py-3 flex items-center gap-3 max-w-lg w-full">
            <span className="text-xs text-muted-foreground flex-1">
              {compareStore.items.length} selected
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

      <Modal isOpen={!!editingNotes} onClose={() => setEditingNotes(null)} title="Notes">
        {editingNotes && (
          <div className="space-y-3">
            <textarea
              value={editingNotes.notes}
              onChange={e => setEditingNotes({ ...editingNotes, notes: e.target.value })}
              className="w-full border border-divider rounded-lg px-3 py-2 text-sm min-h-[100px] focus:outline-none focus:ring-2 focus:ring-ring"
              placeholder="Why I saved this, things to verify…"
            />
            <Button
              variant="secondary"
              onClick={() => {
                patchMut.mutate(
                  { programId: editingNotes.id, body: { notes: editingNotes.notes } },
                  { onSuccess: () => setEditingNotes(null) },
                )
              }}
              loading={patchMut.isPending}
              className="w-full"
            >
              Save notes
            </Button>
          </div>
        )}
      </Modal>

      <Modal isOpen={!!editingTags} onClose={() => setEditingTags(null)} title="Tags">
        {editingTags && (
          <div className="space-y-3">
            <div className="flex flex-wrap gap-1.5">
              {editingTags.tags.map(tag => (
                <span
                  key={tag}
                  className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-muted"
                >
                  {tag}
                  <button
                    type="button"
                    onClick={() =>
                      setEditingTags({
                        ...editingTags,
                        tags: editingTags.tags.filter(t => t !== tag),
                      })
                    }
                  >
                    <X size={10} />
                  </button>
                </span>
              ))}
            </div>
            <input
              list="saved-tag-suggestions"
              value={editingTags.input}
              onChange={e => setEditingTags({ ...editingTags, input: e.target.value })}
              onKeyDown={e => {
                if (e.key === 'Enter' && editingTags.input.trim()) {
                  e.preventDefault()
                  const t = editingTags.input.trim()
                  if (!editingTags.tags.includes(t)) {
                    setEditingTags({
                      ...editingTags,
                      tags: [...editingTags.tags, t],
                      input: '',
                    })
                  }
                }
              }}
              className="w-full border border-divider rounded-lg px-3 py-2 text-sm"
              placeholder="Add a tag…"
            />
            <datalist id="saved-tag-suggestions">
              {allTags.map(t => (
                <option key={t} value={t} />
              ))}
            </datalist>
            <Button
              variant="secondary"
              onClick={() => {
                let tags = [...editingTags.tags]
                if (editingTags.input.trim() && !tags.includes(editingTags.input.trim())) {
                  tags = [...tags, editingTags.input.trim()]
                }
                patchMut.mutate(
                  { programId: editingTags.id, body: { tags } },
                  { onSuccess: () => setEditingTags(null) },
                )
              }}
              loading={patchMut.isPending}
              className="w-full"
            >
              Save tags
            </Button>
          </div>
        )}
      </Modal>
    </div>
  )
}
