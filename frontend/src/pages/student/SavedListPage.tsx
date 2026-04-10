import { useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { listSaved, unsaveProgram, updateSavedNotes, comparePrograms } from '../../api/saved-lists'
import { listMyApplications, createApplication } from '../../api/applications'
import { getMatches } from '../../api/matching'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import Modal from '../../components/ui/Modal'
import Badge from '../../components/ui/Badge'
import EmptyState from '../../components/ui/EmptyState'
import { SkeletonCard } from '../../components/ui/Skeleton'
import { showToast } from '../../stores/toast-store'
import { formatCurrency, formatDate, formatPercent, formatScore } from '../../utils/format'
import { DEGREE_LABELS, TIER_LABELS, STATUS_COLORS } from '../../utils/constants'
import { Heart, Trash2, Pencil, BarChart3, ArrowUp, ArrowDown, Minus, ArrowUpDown, Filter, FileText, ChevronDown } from 'lucide-react'
import type { SavedProgram, ComparisonResponse, MatchResult, Application } from '../../types'

type Priority = 'considering' | 'planning' | 'applied' | 'dropped'

const PRIORITY_CONFIG: Record<Priority, { label: string; color: string }> = {
  considering: { label: 'Considering', color: 'bg-gray-100 text-gray-700' },
  planning: { label: 'Planning', color: 'bg-sky-100 text-sky-800' },
  applied: { label: 'Applied', color: 'bg-emerald-100 text-emerald-800' },
  dropped: { label: 'Dropped', color: 'bg-rose-100 text-rose-800' },
}
const PRIORITY_ORDER: Priority[] = ['considering', 'planning', 'applied', 'dropped']

type SortKey = 'date_added' | 'match_score' | 'deadline'
const SORT_OPTIONS: { value: SortKey; label: string }[] = [
  { value: 'date_added', label: 'Date Added' },
  { value: 'match_score', label: 'Match Score' },
  { value: 'deadline', label: 'Deadline' },
]

const TIER_GROUP_LABELS: Record<number, string> = { 1: 'Reach', 2: 'Target', 3: 'Safer' }
const TIER_GROUP_ORDER = [1, 2, 3, 0] // 0 = unmatched

export default function SavedListPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [editingNotes, setEditingNotes] = useState<{ id: string; notes: string } | null>(null)
  const [comparison, setComparison] = useState<ComparisonResponse | null>(null)
  const [priorities, setPriorities] = useState<Record<string, Priority>>({})
  const [filterPriority, setFilterPriority] = useState<Priority | 'all'>('all')
  const [sortKey, setSortKey] = useState<SortKey>('date_added')
  const [groupByTier, setGroupByTier] = useState(true)

  const { data: saved, isLoading } = useQuery({ queryKey: ['saved'], queryFn: listSaved })
  const { data: matches } = useQuery({ queryKey: ['matches'], queryFn: () => getMatches() })
  const { data: applications } = useQuery({ queryKey: ['my-applications'], queryFn: listMyApplications })

  const removeMut = useMutation({
    mutationFn: unsaveProgram,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['saved'] }); showToast('Removed', 'success') },
  })
  const notesMut = useMutation({
    mutationFn: ({ id, notes }: { id: string; notes: string }) => updateSavedNotes(id, notes),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['saved'] }); setEditingNotes(null); showToast('Notes updated', 'success') },
  })
  const compareMut = useMutation({
    mutationFn: (ids: string[]) => comparePrograms(ids),
    onSuccess: (data) => setComparison(data),
  })
  const applyMut = useMutation({
    mutationFn: createApplication,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['my-applications'] })
      showToast('Application started', 'success')
      navigate(`/s/applications/${data.id}`)
    },
  })

  const matchLookup = useMemo(() => {
    const map: Record<string, MatchResult> = {}
    const list: MatchResult[] = Array.isArray(matches) ? matches : []
    list.forEach(m => { map[m.program_id] = m })
    return map
  }, [matches])

  const appLookup = useMemo(() => {
    const map: Record<string, Application> = {}
    const list: Application[] = Array.isArray(applications) ? applications : []
    list.forEach(a => { map[a.program_id] = a })
    return map
  }, [applications])

  const programs: SavedProgram[] = useMemo(() => Array.isArray(saved) ? saved : [], [saved])

  const getPriority = (programId: string): Priority => priorities[programId] ?? 'considering'
  const setProgramPriority = (programId: string, p: Priority) => setPriorities(prev => ({ ...prev, [programId]: p }))

  const filtered = useMemo(() => {
    let list = programs
    if (filterPriority !== 'all') {
      list = list.filter(sp => getPriority(sp.program_id) === filterPriority)
    }
    return [...list].sort((a, b) => {
      if (sortKey === 'match_score') {
        const sa = matchLookup[a.program_id]?.match_score ?? -1
        const sb = matchLookup[b.program_id]?.match_score ?? -1
        return sb - sa
      }
      if (sortKey === 'deadline') {
        const da = a.program?.application_deadline ?? '9999'
        const db = b.program?.application_deadline ?? '9999'
        return da.localeCompare(db)
      }
      return new Date(b.added_at).getTime() - new Date(a.added_at).getTime()
    })
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [programs, filterPriority, sortKey, matchLookup, priorities])

  const grouped = useMemo(() => {
    if (!groupByTier) return null
    const groups: Record<number, SavedProgram[]> = { 1: [], 2: [], 3: [], 0: [] }
    filtered.forEach(sp => {
      const tier = matchLookup[sp.program_id]?.match_tier ?? 0
      groups[tier].push(sp)
    })
    return groups
  }, [filtered, groupByTier, matchLookup])

  const priorityCounts = useMemo(() => {
    const counts: Record<string, number> = { all: programs.length }
    PRIORITY_ORDER.forEach(p => { counts[p] = 0 })
    programs.forEach(sp => { counts[getPriority(sp.program_id)]++ })
    return counts
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [programs, priorities])

  const toggle = (id: string) => {
    const next = new Set(selected)
    if (next.has(id)) next.delete(id); else next.add(id)
    setSelected(next)
  }

  const bestValue = (values: (number | null | undefined)[], higher = true) => {
    const nums = values.filter((v): v is number => v != null)
    if (nums.length === 0) return null
    return higher ? Math.max(...nums) : Math.min(...nums)
  }
  const ValueIndicator = ({ value, best }: { value: number | null | undefined; best: number | null }) => {
    if (value == null || best == null) return <Minus size={12} className="text-gray-300" />
    if (value === best) return <ArrowUp size={12} className="text-green-500" />
    return <ArrowDown size={12} className="text-red-500" />
  }

  if (isLoading) return <div className="p-6 space-y-4">{Array.from({ length: 3 }).map((_, i) => <SkeletonCard key={i} />)}</div>

  const renderCard = (sp: SavedProgram) => {
    const matchInfo = matchLookup[sp.program_id]
    const tierInfo = matchInfo ? TIER_LABELS[matchInfo.match_tier] : null
    const app = appLookup[sp.program_id]
    const priority = getPriority(sp.program_id)
    const isDropped = priority === 'dropped'

    return (
      <Card key={sp.id} className={`p-4 ${isDropped ? 'opacity-60' : ''}`}>
        <div className="flex items-start gap-3">
          <input
            type="checkbox"
            checked={selected.has(sp.program_id)}
            onChange={() => toggle(sp.program_id)}
            className="mt-1"
          />
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0">
                <p className={`font-semibold text-sm cursor-pointer hover:underline ${isDropped ? 'line-through text-gray-400' : ''}`} onClick={() => navigate(`/s/programs/${sp.program_id}`)}>
                  {sp.program_name || sp.program?.program_name || 'Program'}
                </p>
                <p className="text-xs text-gray-500">{sp.institution_name || sp.program?.institution_name}</p>
              </div>
              <div className="flex items-center gap-2 flex-shrink-0">
                {matchInfo && tierInfo && (
                  <>
                    <span className="text-sm font-bold">{formatScore(matchInfo.match_score)}</span>
                    <Badge variant={tierInfo.color as any} size="sm">{tierInfo.label}</Badge>
                  </>
                )}
              </div>
            </div>

            <div className="flex flex-wrap gap-x-4 gap-y-1 mt-1 text-xs text-gray-400">
              {sp.program?.tuition != null && <span>Tuition: {formatCurrency(sp.program.tuition)}</span>}
              {sp.program?.application_deadline && <span>Deadline: {formatDate(sp.program.application_deadline)}</span>}
            </div>

            <div className="flex flex-wrap items-center gap-2 mt-2">
              <div className="relative inline-block">
                <select
                  value={priority}
                  onChange={e => setProgramPriority(sp.program_id, e.target.value as Priority)}
                  className={`appearance-none text-xs font-medium rounded-full pl-2.5 pr-6 py-0.5 border-0 cursor-pointer ${PRIORITY_CONFIG[priority].color}`}
                >
                  {PRIORITY_ORDER.map(p => (
                    <option key={p} value={p}>{PRIORITY_CONFIG[p].label}</option>
                  ))}
                </select>
                <ChevronDown size={10} className="absolute right-1.5 top-1/2 -translate-y-1/2 pointer-events-none text-gray-400" />
              </div>

              {app && (
                <Badge variant={(STATUS_COLORS[app.status] ?? 'neutral') as any} size="sm">
                  {app.status.replace(/_/g, ' ')}
                </Badge>
              )}

              {!app && priority !== 'dropped' && (
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => applyMut.mutate(sp.program_id)}
                  loading={applyMut.isPending}
                  className="text-xs"
                >
                  <FileText size={12} className="mr-1" />
                  Start Application
                </Button>
              )}
            </div>

            {sp.notes && <p className="text-xs text-gray-600 mt-1 italic">"{sp.notes}"</p>}
          </div>

          <div className="flex gap-1 flex-shrink-0">
            <Button size="sm" variant="ghost" onClick={() => setEditingNotes({ id: sp.program_id, notes: sp.notes || '' })}><Pencil size={12} /></Button>
            <Button size="sm" variant="ghost" onClick={() => removeMut.mutate(sp.program_id)}><Trash2 size={12} /></Button>
          </div>
        </div>
      </Card>
    )
  }

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-semibold">Saved Programs</h1>
        {selected.size >= 2 && (
          <Button size="sm" variant="secondary" onClick={() => compareMut.mutate(Array.from(selected))} loading={compareMut.isPending}>
            <BarChart3 size={14} className="mr-1" /> Compare ({selected.size})
          </Button>
        )}
      </div>

      {programs.length === 0 ? (
        <EmptyState
          icon={<Heart size={48} />}
          title="Programs you save will appear here"
          description="Browse Discover to find programs that interest you."
          action={{ label: 'Discover Programs', onClick: () => navigate('/s/discover') }}
        />
      ) : (
        <>
          <div className="flex flex-wrap items-center gap-3 mb-4">
            <div className="flex items-center gap-1">
              <Filter size={14} className="text-gray-400 mr-1" />
              {(['all', ...PRIORITY_ORDER] as const).map(p => (
                <button
                  key={p}
                  onClick={() => setFilterPriority(p)}
                  className={`text-xs px-2.5 py-1 rounded-full font-medium transition-colors ${
                    filterPriority === p
                      ? 'bg-stone-800 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {p === 'all' ? 'All' : PRIORITY_CONFIG[p].label} ({priorityCounts[p] ?? 0})
                </button>
              ))}
            </div>

            <div className="flex items-center gap-2 ml-auto">
              <div className="flex items-center gap-1 text-xs text-gray-500">
                <ArrowUpDown size={12} />
                <select
                  value={sortKey}
                  onChange={e => setSortKey(e.target.value as SortKey)}
                  className="text-xs border-0 bg-transparent cursor-pointer text-gray-600 font-medium"
                >
                  {SORT_OPTIONS.map(o => (
                    <option key={o.value} value={o.value}>{o.label}</option>
                  ))}
                </select>
              </div>

              <button
                onClick={() => setGroupByTier(!groupByTier)}
                className={`text-xs px-2.5 py-1 rounded font-medium transition-colors ${
                  groupByTier ? 'bg-stone-800 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                Group by Tier
              </button>
            </div>
          </div>

          {grouped ? (
            <div className="space-y-6">
              {TIER_GROUP_ORDER.map(tier => {
                const items = grouped[tier]
                if (!items || items.length === 0) return null
                const label = tier === 0 ? 'Unmatched' : TIER_GROUP_LABELS[tier]
                return (
                  <div key={tier}>
                    <div className="flex items-center gap-2 mb-2">
                      <h2 className="text-sm font-semibold text-gray-700">{label}</h2>
                      <span className="text-xs text-gray-400">({items.length})</span>
                    </div>
                    <div className="space-y-3">
                      {items.map(renderCard)}
                    </div>
                  </div>
                )
              })}
            </div>
          ) : (
            <div className="space-y-3">
              {filtered.map(renderCard)}
            </div>
          )}
        </>
      )}

      {/* Edit notes modal */}
      <Modal isOpen={!!editingNotes} onClose={() => setEditingNotes(null)} title="Edit Notes">
        {editingNotes && (
          <div className="space-y-3">
            <textarea
              value={editingNotes.notes}
              onChange={e => setEditingNotes({ ...editingNotes, notes: e.target.value })}
              className="w-full border rounded px-3 py-2 text-sm min-h-[100px]"
              placeholder="Your notes about this program..."
            />
            <Button onClick={() => notesMut.mutate({ id: editingNotes.id, notes: editingNotes.notes })} loading={notesMut.isPending} className="w-full">Save</Button>
          </div>
        )}
      </Modal>

      {/* Comparison modal */}
      <Modal isOpen={!!comparison} onClose={() => setComparison(null)} title="Program Comparison" size="lg">
        {comparison && (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2 px-2 text-gray-500 font-medium">Feature</th>
                  {comparison.programs.map(p => (
                    <th key={p.id} className="text-left py-2 px-2 font-semibold">{p.program_name}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                <tr className="border-b">
                  <td className="py-2 px-2 text-gray-500">Institution</td>
                  {comparison.programs.map(p => (
                    <td key={p.id} className="py-2 px-2">{p.institution_name}</td>
                  ))}
                </tr>
                <tr className="border-b">
                  <td className="py-2 px-2 text-gray-500">Country</td>
                  {comparison.programs.map(p => (
                    <td key={p.id} className="py-2 px-2">{p.institution_country}</td>
                  ))}
                </tr>
                <tr className="border-b">
                  <td className="py-2 px-2 text-gray-500">Degree</td>
                  {comparison.programs.map(p => (
                    <td key={p.id} className="py-2 px-2">
                      <Badge variant="info" size="sm">{DEGREE_LABELS[p.degree_type] || p.degree_type}</Badge>
                    </td>
                  ))}
                </tr>
                {(() => {
                  const scores = comparison.programs.map(p => matchLookup[p.id]?.match_score)
                  const best = bestValue(scores, true)
                  return (
                    <tr className="border-b bg-gray-50">
                      <td className="py-2 px-2 text-gray-500 font-medium">Match Score</td>
                      {comparison.programs.map((p, i) => {
                        const m = matchLookup[p.id]
                        const ti = m ? TIER_LABELS[m.match_tier] : null
                        return (
                          <td key={p.id} className="py-2 px-2">
                            {m ? (
                              <div className="flex items-center gap-2">
                                <span className="font-bold">{formatScore(m.match_score)}</span>
                                {ti && <Badge variant={ti.color as any} size="sm">{ti.label}</Badge>}
                                <ValueIndicator value={scores[i]} best={best} />
                              </div>
                            ) : '\u2014'}
                          </td>
                        )
                      })}
                    </tr>
                  )
                })()}
                {(() => {
                  const tuitions = comparison.programs.map(p => (p as any).tuition)
                  const best = bestValue(tuitions, false)
                  return (
                    <tr className="border-b">
                      <td className="py-2 px-2 text-gray-500">Tuition</td>
                      {comparison.programs.map((p, i) => (
                        <td key={p.id} className="py-2 px-2">
                          <div className="flex items-center gap-2">
                            <span>{formatCurrency((p as any).tuition)}</span>
                            <ValueIndicator value={tuitions[i]} best={best} />
                          </div>
                        </td>
                      ))}
                    </tr>
                  )
                })()}
                {(() => {
                  const rates = comparison.programs.map(p => (p as any).acceptance_rate)
                  const best = bestValue(rates, true)
                  return (
                    <tr className="border-b">
                      <td className="py-2 px-2 text-gray-500">Acceptance Rate</td>
                      {comparison.programs.map((p, i) => (
                        <td key={p.id} className="py-2 px-2">
                          <div className="flex items-center gap-2">
                            <span>{formatPercent((p as any).acceptance_rate, 1)}</span>
                            <ValueIndicator value={rates[i]} best={best} />
                          </div>
                        </td>
                      ))}
                    </tr>
                  )
                })()}
                <tr className="border-b">
                  <td className="py-2 px-2 text-gray-500">Deadline</td>
                  {comparison.programs.map(p => (
                    <td key={p.id} className="py-2 px-2">{formatDate(p.application_deadline)}</td>
                  ))}
                </tr>
                <tr className="border-b">
                  <td className="py-2 px-2 text-gray-500">Duration</td>
                  {comparison.programs.map(p => (
                    <td key={p.id} className="py-2 px-2">{(p as any).duration_months ? `${(p as any).duration_months} months` : '\u2014'}</td>
                  ))}
                </tr>
              </tbody>
            </table>
          </div>
        )}
      </Modal>
    </div>
  )
}
