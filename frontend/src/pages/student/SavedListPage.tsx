import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  ArrowRight,
  ArrowUp,
  ArrowUpDown,
  Bookmark,
  FileText,
  GraduationCap,
  Heart,
  Layers,
  MapPin,
  Minus,
  Pencil,
  Sparkles,
  Trash2,
  X,
} from 'lucide-react'

import {
  comparePrograms,
  listSaved,
  startApplication,
  unsaveProgram,
  updateSaved,
} from '../../api/saved-lists'
import { getMyFollows, unfollowInstitution, type FollowedInstitution } from '../../api/events'
import { getMatches } from '../../api/matching'
import Badge from '../../components/ui/Badge'
import BandBadge from '../../components/ui/BandBadge'
import Breadcrumbs from '../../components/ui/Breadcrumbs'
import Button from '../../components/ui/Button'
import Card from '../../components/ui/Card'
import EmptyState from '../../components/ui/EmptyState'
import Modal from '../../components/ui/Modal'
import { SkeletonCard } from '../../components/ui/Skeleton'
import Tabs from '../../components/ui/Tabs'
import DualRing from './match/DualRing'
import RationalePopover from './match/RationalePopover'
import { showToast } from '../../stores/toast-store'
import { DEGREE_LABELS, DELIVERY_FORMAT_LABELS } from '../../utils/constants'
import { formatCurrency, formatDate, formatPercent } from '../../utils/format'
import usePageTitle from '../../hooks/usePageTitle'
import type {
  ComparisonResponse,
  MatchBand,
  MatchResultDual,
  SavedPriority,
  SavedProgram,
  SavedStatus,
} from '../../types'

// ── Spec 13 vocab ─────────────────────────────────────────────────────────
const PRIORITY_ORDER: SavedPriority[] = [
  'considering',
  'planning_to_apply',
  'applied',
  'dropped',
]
const PRIORITY_META: Record<SavedPriority, { label: string; chip: string }> = {
  // §10 — priority chips use cobalt/neutral/status tints, never gold.
  considering: { label: 'Considering', chip: 'bg-muted text-charcoal' },
  planning_to_apply: { label: 'Planning to apply', chip: 'bg-cobalt/10 text-cobalt' },
  applied: { label: 'Applied', chip: 'bg-success-soft text-success' },
  dropped: { label: 'Dropped', chip: 'bg-error-soft text-error' },
}

const STATUS_META: Record<
  SavedStatus,
  { label: string; variant: 'neutral' | 'info' | 'success' | 'warning' | 'danger' }
> = {
  considering: { label: 'Considering', variant: 'neutral' },
  application_started: { label: 'Application started', variant: 'info' },
  submitted: { label: 'Submitted', variant: 'info' },
  accepted: { label: 'Accepted', variant: 'success' },
  rejected: { label: 'Rejected', variant: 'danger' },
  waitlisted: { label: 'Waitlisted', variant: 'warning' },
  dropped: { label: 'Dropped', variant: 'neutral' },
}

const BAND_ORDER: MatchBand[] = ['reach', 'target', 'safer']
const BAND_BLURB: Record<MatchBand, string> = {
  reach: 'Ambitious — worth a shot',
  target: 'Strong, realistic fits',
  safer: 'High-confidence matches',
}

const VIEW_OPTIONS = [
  { value: 'tier', label: 'Grouped by tier' },
  { value: 'priority', label: 'Grouped by priority' },
  { value: 'flat', label: 'Flat list' },
] as const
type ViewMode = (typeof VIEW_OPTIONS)[number]['value']

const SORT_OPTIONS = [
  { value: 'match', label: 'Match score' },
  { value: 'date', label: 'Date added' },
  { value: 'deadline', label: 'Deadline' },
] as const
type SortKey = (typeof SORT_OPTIONS)[number]['value']

const MAX_COMPARE = 4 // Spec 13 §5

function toUnit(v: string | number | null | undefined): number {
  const n = typeof v === 'string' ? parseFloat(v) : v ?? 0
  if (!Number.isFinite(n)) return 0
  return Math.max(0, Math.min(1, n > 1 ? n / 100 : n))
}

export default function SavedListPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  usePageTitle('Saved')

  const [tab, setTab] = useState<'programs' | 'schools'>('programs')
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [editing, setEditing] = useState<{ programId: string; notes: string; tags: string[] } | null>(
    null
  )
  const [comparison, setComparison] = useState<ComparisonResponse | null>(null)
  const [rationaleFor, setRationaleFor] = useState<string | null>(null)
  const [view, setView] = useState<ViewMode>('tier')
  const [sortKey, setSortKey] = useState<SortKey>('match')
  const [filter, setFilter] = useState<SavedPriority | 'all'>('all')

  const { data: saved, isLoading } = useQuery({ queryKey: ['saved'], queryFn: listSaved })
  const { data: follows } = useQuery({ queryKey: ['my-follows'], queryFn: getMyFollows })
  const { data: matches } = useQuery({ queryKey: ['matches'], queryFn: () => getMatches() })

  const removeMut = useMutation({
    mutationFn: unsaveProgram,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['saved'] })
      showToast('Removed from your shortlist', 'success')
    },
  })
  const patchMut = useMutation({
    mutationFn: ({ programId, ...patch }: { programId: string } & Parameters<typeof updateSaved>[1]) =>
      updateSaved(programId, patch),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['saved'] }),
  })
  const compareMut = useMutation({
    mutationFn: (ids: string[]) => comparePrograms(ids),
    onSuccess: data => setComparison(data),
  })
  const startAppMut = useMutation({
    mutationFn: (programId: string) => startApplication(programId),
    onSuccess: data => {
      queryClient.invalidateQueries({ queryKey: ['saved'] })
      queryClient.invalidateQueries({ queryKey: ['my-applications'] })
      showToast(data.created ? 'Application started' : 'Opening your application', 'success')
      navigate(`/s/applications/${data.app_id}`)
    },
  })
  const unfollowMut = useMutation({
    mutationFn: unfollowInstitution,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['my-follows'] })
      showToast('Unfollowed', 'success')
    },
  })

  const matchLookup = useMemo(() => {
    const map: Record<string, MatchResultDual> = {}
    ;(Array.isArray(matches) ? matches : []).forEach(m => {
      map[m.program_id] = m
    })
    return map
  }, [matches])

  const programs: SavedProgram[] = useMemo(() => (Array.isArray(saved) ? saved : []), [saved])
  const schools: FollowedInstitution[] = useMemo(
    () => (Array.isArray(follows) ? follows : []),
    [follows]
  )

  const bandOf = (sp: SavedProgram): MatchBand | null =>
    sp.band_label ?? matchLookup[sp.program_id]?.band_label ?? null
  const fitnessOf = (sp: SavedProgram): number =>
    toUnit(sp.fitness_score ?? matchLookup[sp.program_id]?.fitness_score)
  const confidenceOf = (sp: SavedProgram): number =>
    toUnit(sp.confidence_score ?? matchLookup[sp.program_id]?.confidence_score)

  // Every tag the student has used — powers the autocomplete (Spec 13 §4.3).
  const tagDictionary = useMemo(() => {
    const set = new Set<string>()
    programs.forEach(sp => (sp.tags ?? []).forEach(t => set.add(t)))
    return Array.from(set).sort()
  }, [programs])

  const priorityCounts = useMemo(() => {
    const counts: Record<string, number> = { all: programs.length }
    PRIORITY_ORDER.forEach(p => (counts[p] = 0))
    programs.forEach(sp => (counts[sp.priority] = (counts[sp.priority] ?? 0) + 1))
    return counts
  }, [programs])

  const visible = useMemo(() => {
    let list = programs
    if (filter !== 'all') list = list.filter(sp => sp.priority === filter)
    return [...list].sort((a, b) => {
      if (sortKey === 'match') return fitnessOf(b) - fitnessOf(a)
      if (sortKey === 'deadline') {
        const da = a.application_deadline ?? a.program?.application_deadline ?? '9999'
        const db = b.application_deadline ?? b.program?.application_deadline ?? '9999'
        return da.localeCompare(db)
      }
      return new Date(b.added_at).getTime() - new Date(a.added_at).getTime()
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [programs, filter, sortKey, matchLookup])

  type Group = { key: string; label: string; band?: MatchBand; blurb?: string; items: SavedProgram[] }
  const groups: Group[] = useMemo(() => {
    if (view === 'flat') return [{ key: 'all', label: '', items: visible }]
    if (view === 'priority') {
      return PRIORITY_ORDER.map(p => ({
        key: p,
        label: PRIORITY_META[p].label,
        items: visible.filter(sp => sp.priority === p),
      })).filter(g => g.items.length > 0)
    }
    // tier (default)
    const out: Group[] = BAND_ORDER.map(band => ({
      key: band,
      label: band[0].toUpperCase() + band.slice(1),
      band,
      blurb: BAND_BLURB[band],
      items: visible.filter(sp => bandOf(sp) === band),
    }))
    const unbanded = visible.filter(sp => bandOf(sp) == null)
    if (unbanded.length) out.push({ key: 'unbanded', label: 'Not yet matched', items: unbanded })
    return out.filter(g => g.items.length > 0)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [visible, view, matchLookup])

  const toggleSelect = (programId: string) => {
    setSelected(prev => {
      const next = new Set(prev)
      if (next.has(programId)) {
        next.delete(programId)
      } else if (next.size >= MAX_COMPARE) {
        showToast(`You can compare up to ${MAX_COMPARE} programs`, 'info')
        return prev
      } else {
        next.add(programId)
      }
      return next
    })
  }

  if (isLoading) {
    return (
      <div className="p-6 max-w-4xl mx-auto space-y-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    )
  }

  return (
    <div className="p-6 max-w-4xl mx-auto pb-28">
      <Breadcrumbs className="mb-3" items={[{ label: 'Profile', to: '/s/profile' }, { label: 'Saved' }]} />

      {/* ── Header — eyebrow + H1 (Spec 13 §2 / §13) ── */}
      <header className="mb-5">
        <p className="text-eyebrow uppercase tracking-[0.22em] text-cobalt font-semibold">Saved</p>
        <h1 className="text-h2 font-bold text-charcoal mt-1">Your shortlist</h1>
        <p className="text-sm text-slate mt-1">
          Curate the programs and schools you're considering, then turn them into applications.
        </p>
      </header>

      <Tabs
        tabs={[
          { id: 'programs', label: 'Programs', count: programs.length },
          { id: 'schools', label: 'Schools', count: schools.length },
        ]}
        activeTab={tab}
        onChange={id => setTab(id as 'programs' | 'schools')}
      />

      {tab === 'programs' ? (
        <div className="mt-5">
          {programs.length === 0 ? (
            <EmptyState
              icon={<Heart size={48} />}
              title="Your shortlist is empty"
              description="Save programs from Match or Discovery to see them here."
              action={{ label: 'Open Match →', onClick: () => navigate('/s/explore') }}
            />
          ) : (
            <>
              {/* ── Controls: View · Sort · Filter ── */}
              <div className="flex flex-wrap items-center gap-x-4 gap-y-3 mb-5">
                <label className="inline-flex items-center gap-1.5 text-xs text-slate">
                  <Layers size={13} className="text-slate/60" />
                  <span className="sr-only">View</span>
                  <select
                    value={view}
                    onChange={e => setView(e.target.value as ViewMode)}
                    className="text-xs font-semibold bg-transparent border border-stone rounded-md pl-2 pr-6 py-1 cursor-pointer text-charcoal focus:outline-none focus:ring-2 focus:ring-cobalt/40"
                  >
                    {VIEW_OPTIONS.map(o => (
                      <option key={o.value} value={o.value}>
                        {o.label}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="inline-flex items-center gap-1.5 text-xs text-slate">
                  <ArrowUpDown size={13} className="text-slate/60" />
                  <span className="sr-only">Sort</span>
                  <select
                    value={sortKey}
                    onChange={e => setSortKey(e.target.value as SortKey)}
                    className="text-xs font-semibold bg-transparent border border-stone rounded-md pl-2 pr-6 py-1 cursor-pointer text-charcoal focus:outline-none focus:ring-2 focus:ring-cobalt/40"
                  >
                    {SORT_OPTIONS.map(o => (
                      <option key={o.value} value={o.value}>
                        {o.label}
                      </option>
                    ))}
                  </select>
                </label>

                <div className="flex items-center gap-1 ml-auto flex-wrap">
                  {(['all', ...PRIORITY_ORDER] as const).map(p => (
                    <button
                      key={p}
                      onClick={() => setFilter(p)}
                      className={`text-xs px-2.5 py-1 rounded-pill font-medium transition-colors ${
                        filter === p
                          ? 'bg-charcoal text-white'
                          : 'bg-muted text-slate hover:bg-stone/40'
                      }`}
                    >
                      {p === 'all' ? 'All' : PRIORITY_META[p].label} ({priorityCounts[p] ?? 0})
                    </button>
                  ))}
                </div>
              </div>

              {/* ── Grouped rows ── */}
              {groups.length === 0 ? (
                <p className="text-sm text-slate py-8 text-center">No programs match this filter.</p>
              ) : (
                <div className="space-y-7">
                  {groups.map(g => (
                    <section key={g.key}>
                      {g.label && (
                        <div className="flex items-center gap-2.5 mb-3">
                          {g.band ? (
                            <BandBadge band={g.band} size="md" />
                          ) : (
                            <p className="text-eyebrow uppercase tracking-[0.18em] font-semibold text-slate">
                              {g.label}
                            </p>
                          )}
                          <span className="text-xs text-slate/60">{g.items.length}</span>
                          {g.blurb && <span className="text-xs text-slate/50">· {g.blurb}</span>}
                        </div>
                      )}
                      <div className="space-y-3">
                        {g.items.map(sp => (
                          <SavedProgramRow
                            key={sp.id}
                            sp={sp}
                            band={bandOf(sp)}
                            fitness={fitnessOf(sp)}
                            confidence={confidenceOf(sp)}
                            selected={selected.has(sp.program_id)}
                            onToggleSelect={() => toggleSelect(sp.program_id)}
                            onPriority={priority => patchMut.mutate({ programId: sp.program_id, priority })}
                            onEdit={() =>
                              setEditing({
                                programId: sp.program_id,
                                notes: sp.notes ?? '',
                                tags: sp.tags ?? [],
                              })
                            }
                            onRemove={() => removeMut.mutate(sp.program_id)}
                            onStartApp={() => startAppMut.mutate(sp.program_id)}
                            startingApp={startAppMut.isPending && startAppMut.variables === sp.program_id}
                            onRationale={() => setRationaleFor(sp.program_id)}
                            onView={() => navigate(`/s/programs/${sp.program_id}`)}
                          />
                        ))}
                      </div>
                    </section>
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      ) : (
        // ── Schools tab (Spec 13 §3.2) ──
        <div className="mt-5">
          {schools.length === 0 ? (
            <EmptyState
              icon={<GraduationCap size={48} />}
              title="No schools followed yet"
              description="Follow a school from its page to keep it on your shortlist and in your Connect feed."
              action={{ label: 'Browse schools →', onClick: () => navigate('/s/explore?tab=schools') }}
            />
          ) : (
            <div className="grid gap-3 sm:grid-cols-2">
              {schools.map(s => (
                <SavedSchoolCard
                  key={s.institution_id}
                  school={s}
                  onView={() => navigate(`/s/institutions/${s.institution_id}`)}
                  onUnfollow={() => unfollowMut.mutate(s.institution_id)}
                  unfollowing={unfollowMut.isPending && unfollowMut.variables === s.institution_id}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── Compare tray (sticky) — Spec 13 §5 ── */}
      {tab === 'programs' && selected.size > 0 && (
        <div className="fixed bottom-0 inset-x-0 z-30 bg-card/95 backdrop-blur border-t border-border shadow-[0_-2px_12px_rgba(10,20,40,0.06)]">
          <div className="max-w-4xl mx-auto px-6 py-3 flex items-center gap-3">
            <span className="text-sm text-slate">
              <span className="font-semibold text-charcoal">{selected.size}</span> selected
              <span className="text-slate/50"> · up to {MAX_COMPARE}</span>
            </span>
            <button
              onClick={() => setSelected(new Set())}
              className="text-xs text-slate hover:text-charcoal underline-offset-2 hover:underline"
            >
              Clear
            </button>
            <div className="ml-auto flex items-center gap-2">
              {selected.size < 2 && (
                <span className="text-xs text-slate/60">Select at least 2 to compare</span>
              )}
              <Button
                size="sm"
                variant="secondary"
                disabled={selected.size < 2}
                loading={compareMut.isPending}
                onClick={() => compareMut.mutate(Array.from(selected))}
              >
                Compare selected ({selected.size}) <ArrowRight size={14} className="ml-1" />
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* ── Notes & tags editor (mounted only while open) ── */}
      {editing && (
        <NotesTagsModal
          key={editing.programId}
          initialNotes={editing.notes}
          initialTags={editing.tags}
          tagDictionary={tagDictionary}
          saving={patchMut.isPending}
          onClose={() => setEditing(null)}
          onSave={(notes, tags) =>
            patchMut.mutate(
              { programId: editing.programId, notes, tags },
              { onSuccess: () => setEditing(null) }
            )
          }
        />
      )}

      {/* ── Comparison modal ── */}
      <CompareModal comparison={comparison} onClose={() => setComparison(null)} />

      {/* ── "Why this match" rationale popover ── */}
      {rationaleFor && (
        <RationalePopover
          programId={rationaleFor}
          fitnessBreakdown={matchLookup[rationaleFor]?.fitness_breakdown}
          confidenceBreakdown={matchLookup[rationaleFor]?.confidence_breakdown}
          confidenceScore={toUnit(matchLookup[rationaleFor]?.confidence_score)}
          cachedRationale={matchLookup[rationaleFor]?.rationale_text}
          onClose={() => setRationaleFor(null)}
        />
      )}
    </div>
  )
}

// ───────────────────────────────────────────────────────────────────────────
// Saved program row — full program + curation controls (Spec 13 §3.1).
// ───────────────────────────────────────────────────────────────────────────
function SavedProgramRow({
  sp,
  band,
  fitness,
  confidence,
  selected,
  onToggleSelect,
  onPriority,
  onEdit,
  onRemove,
  onStartApp,
  startingApp,
  onRationale,
  onView,
}: {
  sp: SavedProgram
  band: MatchBand | null
  fitness: number
  confidence: number
  selected: boolean
  onToggleSelect: () => void
  onPriority: (p: SavedPriority) => void
  onEdit: () => void
  onRemove: () => void
  onStartApp: () => void
  startingApp: boolean
  onRationale: () => void
  onView: () => void
}) {
  const dropped = sp.priority === 'dropped'
  const status = STATUS_META[sp.status] ?? STATUS_META.considering
  const degree = sp.degree_type ? DEGREE_LABELS[sp.degree_type] ?? sp.degree_type : null
  const deadline = sp.application_deadline ?? sp.program?.application_deadline ?? null
  const tuition = sp.tuition ?? sp.program?.tuition ?? null
  const city = sp.institution_city ?? sp.program?.institution_city ?? null
  const country = sp.institution_country ?? sp.program?.institution_country ?? null
  const hasApp = sp.status !== 'considering' && sp.status !== 'dropped'
  const hasScore = fitness > 0 || confidence > 0

  return (
    <Card className={`p-4 ${dropped ? 'opacity-60' : ''}`}>
      <div className="flex items-start gap-3">
        <input
          type="checkbox"
          checked={selected}
          onChange={onToggleSelect}
          className="mt-1.5 h-4 w-4 accent-cobalt cursor-pointer"
          aria-label="Add to compare"
        />

        {hasScore && (
          <button onClick={onRationale} className="shrink-0 mt-0.5" aria-label="Why this match">
            <DualRing fitness={fitness} confidence={confidence} size={56} compact />
          </button>
        )}

        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <div className="min-w-0">
              <button onClick={onView} className="text-left">
                <h3
                  className={`text-[15px] font-bold leading-tight hover:text-cobalt transition-colors ${
                    dropped ? 'line-through text-slate/60' : 'text-charcoal'
                  }`}
                >
                  {sp.program_name ?? sp.program?.program_name ?? 'Program'}
                </h3>
              </button>
              <p className="text-xs text-slate mt-0.5 truncate">
                {sp.institution_name ?? sp.program?.institution_name}
                {(city || country) && (
                  <span className="text-slate/60">
                    {' · '}
                    <MapPin size={9} className="inline -mt-0.5" /> {[city, country].filter(Boolean).join(', ')}
                  </span>
                )}
              </p>
            </div>
            <div className="flex items-center gap-1.5 shrink-0">
              {band && <BandBadge band={band} />}
              <Badge variant={status.variant} size="sm">
                {status.label}
              </Badge>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-1.5 text-xs text-slate/70">
            {degree && (
              <span className="px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider rounded bg-muted text-charcoal border border-stone/50">
                {degree}
              </span>
            )}
            {tuition != null && <span>{formatCurrency(tuition)}/yr</span>}
            {deadline && <span>Due {formatDate(deadline)}</span>}
          </div>

          {/* Tags */}
          {sp.tags && sp.tags.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {sp.tags.map(t => (
                <span
                  key={t}
                  className="px-2 py-0.5 text-[10px] rounded-pill bg-cobalt/8 text-cobalt border border-cobalt/15"
                >
                  {t}
                </span>
              ))}
            </div>
          )}

          {/* Notes */}
          {sp.notes && <p className="text-xs text-slate mt-2 italic">“{sp.notes}”</p>}

          {/* Controls row */}
          <div className="flex flex-wrap items-center gap-2 mt-3">
            <select
              value={sp.priority}
              onChange={e => onPriority(e.target.value as SavedPriority)}
              className={`appearance-none text-xs font-semibold rounded-pill pl-2.5 pr-6 py-1 border-0 cursor-pointer focus:outline-none focus:ring-2 focus:ring-cobalt/40 ${PRIORITY_META[sp.priority].chip}`}
              aria-label="Priority"
            >
              {PRIORITY_ORDER.map(p => (
                <option key={p} value={p}>
                  {PRIORITY_META[p].label}
                </option>
              ))}
            </select>

            {hasScore && (
              <button
                onClick={onRationale}
                className="inline-flex items-center gap-1 text-xs font-semibold text-cobalt hover:underline"
              >
                <Sparkles size={12} /> Why this match
              </button>
            )}

            {!hasApp && !dropped && (
              <Button size="sm" variant="secondary" onClick={onStartApp} loading={startingApp} className="text-xs">
                <FileText size={12} className="mr-1" /> Start application
              </Button>
            )}

            <div className="ml-auto flex items-center gap-0.5">
              <button
                onClick={onEdit}
                className="p-1.5 rounded-md text-slate hover:text-cobalt hover:bg-muted transition-colors"
                aria-label="Edit notes & tags"
              >
                <Pencil size={13} />
              </button>
              <button
                onClick={onRemove}
                className="p-1.5 rounded-md text-slate hover:text-error hover:bg-error-soft/40 transition-colors"
                aria-label="Remove"
              >
                <Trash2 size={13} />
              </button>
            </div>
          </div>
        </div>
      </div>
    </Card>
  )
}

// ───────────────────────────────────────────────────────────────────────────
// Saved school card — editorial duotone, institution-level (Spec 13 §3.2).
// ───────────────────────────────────────────────────────────────────────────
function SavedSchoolCard({
  school,
  onView,
  onUnfollow,
  unfollowing,
}: {
  school: FollowedInstitution
  onView: () => void
  onUnfollow: () => void
  unfollowing: boolean
}) {
  const location = [school.city, school.country].filter(Boolean).join(', ')
  return (
    <Card className="p-4 flex items-start gap-3">
      <div className="w-11 h-11 rounded-lg bg-cobalt/10 flex items-center justify-center shrink-0 overflow-hidden">
        {school.logo_url ? (
          <img src={school.logo_url} alt="" className="w-full h-full object-contain" />
        ) : (
          <GraduationCap size={20} className="text-cobalt" />
        )}
      </div>
      <div className="flex-1 min-w-0">
        <button onClick={onView} className="text-left">
          <h3 className="text-[15px] font-bold text-charcoal leading-tight hover:text-cobalt transition-colors truncate">
            {school.name}
          </h3>
        </button>
        <p className="text-xs text-slate mt-0.5 flex items-center gap-1 flex-wrap">
          {location && (
            <>
              <MapPin size={10} /> {location}
            </>
          )}
          {school.program_count != null && (
            <span className="text-slate/60">
              {location ? ' · ' : ''}
              {school.program_count} program{school.program_count === 1 ? '' : 's'}
            </span>
          )}
        </p>
        <div className="flex items-center gap-3 mt-3">
          <button
            onClick={onView}
            className="inline-flex items-center gap-1 text-xs font-semibold text-cobalt hover:underline"
          >
            View school <ArrowRight size={12} />
          </button>
          <button
            onClick={onUnfollow}
            disabled={unfollowing}
            className="inline-flex items-center gap-1 text-xs text-slate hover:text-error transition-colors disabled:opacity-50"
          >
            <Bookmark size={12} /> Unfollow
          </button>
        </div>
      </div>
    </Card>
  )
}

// ───────────────────────────────────────────────────────────────────────────
// Notes & tags editor (Spec 13 §4.3).
// ───────────────────────────────────────────────────────────────────────────
function NotesTagsModal({
  initialNotes,
  initialTags,
  tagDictionary,
  saving,
  onClose,
  onSave,
}: {
  initialNotes: string
  initialTags: string[]
  tagDictionary: string[]
  saving: boolean
  onClose: () => void
  onSave: (notes: string, tags: string[]) => void
}) {
  const [notes, setNotes] = useState(initialNotes)
  const [tags, setTags] = useState<string[]>(initialTags)
  const [draft, setDraft] = useState('')

  const addTag = (raw: string) => {
    const t = raw.trim()
    if (!t) return
    if (!tags.some(x => x.toLowerCase() === t.toLowerCase())) setTags([...tags, t])
    setDraft('')
  }
  const suggestions = tagDictionary.filter(
    t => !tags.some(x => x.toLowerCase() === t.toLowerCase())
  )

  return (
    <Modal isOpen onClose={onClose} title="Notes & tags">
      <div className="space-y-4">
        <div>
          <label className="text-xs font-semibold text-charcoal block mb-1.5">Notes</label>
          <textarea
            value={notes}
            onChange={e => setNotes(e.target.value)}
            className="w-full border border-stone rounded-md px-3 py-2 text-sm min-h-[96px] focus:outline-none focus:ring-2 focus:ring-cobalt/40"
            placeholder="Why I saved this · things to verify…"
          />
        </div>

        <div>
          <label className="text-xs font-semibold text-charcoal block mb-1.5">Tags</label>
          <div className="flex flex-wrap gap-1.5 mb-2">
            {tags.map(t => (
              <span
                key={t}
                className="inline-flex items-center gap-1 px-2 py-0.5 text-xs rounded-pill bg-cobalt/10 text-cobalt"
              >
                {t}
                <button onClick={() => setTags(tags.filter(x => x !== t))} aria-label={`Remove ${t}`}>
                  <X size={11} />
                </button>
              </span>
            ))}
          </div>
          <input
            value={draft}
            onChange={e => setDraft(e.target.value)}
            onKeyDown={e => {
              if (e.key === 'Enter' || e.key === ',') {
                e.preventDefault()
                addTag(draft)
              }
            }}
            list="saved-tag-suggestions"
            placeholder="Add a tag and press Enter"
            className="w-full border border-stone rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-cobalt/40"
          />
          <datalist id="saved-tag-suggestions">
            {suggestions.map(t => (
              <option key={t} value={t} />
            ))}
          </datalist>
        </div>

        <Button onClick={() => onSave(notes, tags)} loading={saving} className="w-full">
          Save
        </Button>
      </div>
    </Modal>
  )
}

// ───────────────────────────────────────────────────────────────────────────
// Compare modal — side-by-side with dual scores + best-value markers (§5).
// ───────────────────────────────────────────────────────────────────────────
function CompareModal({
  comparison,
  onClose,
}: {
  comparison: ComparisonResponse | null
  onClose: () => void
}) {
  const progs = comparison?.programs ?? []

  const best = (vals: (number | null | undefined)[], higher = true): number | null => {
    const nums = vals.filter((v): v is number => v != null && Number.isFinite(v))
    if (!nums.length) return null
    return higher ? Math.max(...nums) : Math.min(...nums)
  }
  const Marker = ({ v, b }: { v: number | null | undefined; b: number | null }) =>
    v == null || b == null ? (
      <Minus size={11} className="text-slate/30" />
    ) : v === b ? (
      <ArrowUp size={11} className="text-success" />
    ) : (
      <span className="inline-block w-[11px]" />
    )

  const fitness = progs.map(p => (p.fitness_score != null ? Number(p.fitness_score) : null))
  const confidence = progs.map(p => (p.confidence_score != null ? Number(p.confidence_score) : null))
  const tuitions = progs.map(p => p.tuition ?? null)
  const rates = progs.map(p => p.acceptance_rate ?? null)
  const bestFit = best(fitness, true)
  const bestConf = best(confidence, true)
  const bestTuition = best(tuitions, false)
  const bestRate = best(rates, true)

  const cell = 'py-2.5 px-3 align-top'
  const rowLabel = 'py-2.5 px-3 text-slate font-medium whitespace-nowrap'

  return (
    <Modal isOpen={!!comparison} onClose={onClose} title="Compare programs" size="lg">
      {progs.length < 2 ? (
        <p className="text-sm text-slate py-6 text-center">Select at least 2 programs to compare.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left py-2.5 px-3 text-slate font-medium">Dimension</th>
                {progs.map(p => (
                  <th key={p.id} className="text-left py-2.5 px-3 font-bold text-charcoal min-w-[140px]">
                    {p.program_name}
                    <span className="block text-xs font-normal text-slate">{p.institution_name}</span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-divider bg-muted/40">
                <td className={rowLabel}>Fitness</td>
                {progs.map((p, i) => (
                  <td key={p.id} className={cell}>
                    <span className="inline-flex items-center gap-1.5">
                      <span className="font-bold">
                        {fitness[i] != null ? `${Math.round(toUnit(fitness[i]) * 100)}%` : '—'}
                      </span>
                      <Marker v={fitness[i]} b={bestFit} />
                    </span>
                  </td>
                ))}
              </tr>
              <tr className="border-b border-divider bg-muted/40">
                <td className={rowLabel}>Confidence</td>
                {progs.map((p, i) => (
                  <td key={p.id} className={cell}>
                    <span className="inline-flex items-center gap-1.5">
                      <span className="font-bold">
                        {confidence[i] != null ? `${Math.round(toUnit(confidence[i]) * 100)}%` : '—'}
                      </span>
                      <Marker v={confidence[i]} b={bestConf} />
                    </span>
                  </td>
                ))}
              </tr>
              <tr className="border-b border-divider">
                <td className={rowLabel}>Band</td>
                {progs.map(p => (
                  <td key={p.id} className={cell}>
                    {p.band_label ? <BandBadge band={p.band_label} /> : '—'}
                  </td>
                ))}
              </tr>
              <tr className="border-b border-divider">
                <td className={rowLabel}>Degree</td>
                {progs.map(p => (
                  <td key={p.id} className={cell}>
                    {p.degree_type ? DEGREE_LABELS[p.degree_type] ?? p.degree_type : '—'}
                  </td>
                ))}
              </tr>
              <tr className="border-b border-divider">
                <td className={rowLabel}>Format</td>
                {progs.map(p => (
                  <td key={p.id} className={cell}>
                    {p.delivery_format ? DELIVERY_FORMAT_LABELS[p.delivery_format] ?? p.delivery_format : '—'}
                    {p.duration_months ? ` · ${p.duration_months} mo` : ''}
                  </td>
                ))}
              </tr>
              <tr className="border-b border-divider">
                <td className={rowLabel}>Location</td>
                {progs.map(p => (
                  <td key={p.id} className={cell}>
                    {[p.institution_city, p.institution_country].filter(Boolean).join(', ') || '—'}
                  </td>
                ))}
              </tr>
              <tr className="border-b border-divider">
                <td className={rowLabel}>Tuition</td>
                {progs.map((p, i) => (
                  <td key={p.id} className={cell}>
                    <span className="inline-flex items-center gap-1.5">
                      {formatCurrency(p.tuition)}
                      <Marker v={tuitions[i]} b={bestTuition} />
                    </span>
                  </td>
                ))}
              </tr>
              <tr className="border-b border-divider">
                <td className={rowLabel}>Acceptance</td>
                {progs.map((p, i) => (
                  <td key={p.id} className={cell}>
                    <span className="inline-flex items-center gap-1.5">
                      {p.acceptance_rate != null ? formatPercent(p.acceptance_rate, 1) : '—'}
                      <Marker v={rates[i]} b={bestRate} />
                    </span>
                  </td>
                ))}
              </tr>
              <tr>
                <td className={rowLabel}>Deadline</td>
                {progs.map(p => (
                  <td key={p.id} className={cell}>
                    {p.application_deadline ? formatDate(p.application_deadline) : '—'}
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
      )}
    </Modal>
  )
}
