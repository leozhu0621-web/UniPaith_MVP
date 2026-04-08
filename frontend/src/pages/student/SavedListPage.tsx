import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { listSaved, unsaveProgram, updateSavedNotes, comparePrograms } from '../../api/saved-lists'
import { getMatches } from '../../api/matching'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import Modal from '../../components/ui/Modal'
import Badge from '../../components/ui/Badge'
import EmptyState from '../../components/ui/EmptyState'
import { SkeletonCard } from '../../components/ui/Skeleton'
import { showToast } from '../../stores/toast-store'
import { formatCurrency, formatDate, formatPercent, formatScore } from '../../utils/format'
import { DEGREE_LABELS, TIER_LABELS } from '../../utils/constants'
import { Heart, Trash2, Pencil, BarChart3, ArrowUp, ArrowDown, Minus } from 'lucide-react'
import type { SavedProgram, ComparisonResponse, MatchResult } from '../../types'

export default function SavedListPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [editingNotes, setEditingNotes] = useState<{ id: string; notes: string } | null>(null)
  const [comparison, setComparison] = useState<ComparisonResponse | null>(null)

  const { data: saved, isLoading } = useQuery({ queryKey: ['saved'], queryFn: listSaved })
  const { data: matches } = useQuery({ queryKey: ['matches'], queryFn: () => getMatches() })

  const removeMut = useMutation({ mutationFn: unsaveProgram, onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['saved'] }); showToast('Removed', 'success') } })
  const notesMut = useMutation({ mutationFn: ({ id, notes }: { id: string; notes: string }) => updateSavedNotes(id, notes), onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['saved'] }); setEditingNotes(null); showToast('Notes updated', 'success') } })
  const compareMut = useMutation({ mutationFn: (ids: string[]) => comparePrograms(ids), onSuccess: (data) => setComparison(data) })

  // Build match score lookup
  const matchLookup: Record<string, MatchResult> = {}
  const matchesList: MatchResult[] = Array.isArray(matches) ? matches : []
  matchesList.forEach((m: MatchResult) => { matchLookup[m.program_id] = m })

  const toggle = (id: string) => {
    const next = new Set(selected)
    if (next.has(id)) { next.delete(id) } else { next.add(id) }
    setSelected(next)
  }

  if (isLoading) return <div className="p-6 space-y-4">{Array.from({ length: 3 }).map((_, i) => <SkeletonCard key={i} />)}</div>

  const programs: SavedProgram[] = Array.isArray(saved) ? saved : []

  // Comparison helper: find best/worst in a numeric column
  const bestValue = (values: (number | null | undefined)[], higher = true) => {
    const nums = values.filter((v): v is number => v != null)
    if (nums.length === 0) return null
    return higher ? Math.max(...nums) : Math.min(...nums)
  }

  const ValueIndicator = ({ value, best, lower }: { value: number | null | undefined; best: number | null; lower?: boolean }) => {
    if (value == null || best == null) return <Minus size={12} className="text-gray-300" />
    if (value === best) return <ArrowUp size={12} className={lower ? 'text-green-500' : 'text-green-500'} />
    return <ArrowDown size={12} className={lower ? 'text-red-500' : 'text-red-500'} />
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
        <div className="space-y-3">
          {programs.map(sp => {
            const matchInfo = matchLookup[sp.program_id]
            const tierInfo = matchInfo ? TIER_LABELS[matchInfo.match_tier] : null
            return (
              <Card key={sp.id} className="p-4">
                <div className="flex items-start gap-3">
                  <input
                    type="checkbox"
                    checked={selected.has(sp.program_id)}
                    onChange={() => toggle(sp.program_id)}
                    className="mt-1"
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="font-semibold text-sm cursor-pointer hover:underline" onClick={() => navigate(`/s/programs/${sp.program_id}`)}>
                          {sp.program?.program_name || 'Program'}
                        </p>
                        <p className="text-xs text-gray-500">{sp.program?.institution_name}</p>
                      </div>
                      {matchInfo && tierInfo && (
                        <div className="flex items-center gap-2 flex-shrink-0">
                          <span className="text-sm font-bold">{formatScore(matchInfo.match_score)}</span>
                          <Badge variant={tierInfo.color as any} size="sm">{tierInfo.label}</Badge>
                        </div>
                      )}
                    </div>
                    <div className="flex gap-4 mt-1 text-xs text-gray-400">
                      {sp.program?.tuition != null && <span>Tuition: {formatCurrency(sp.program.tuition)}</span>}
                      {sp.program?.application_deadline && <span>Deadline: {formatDate(sp.program.application_deadline)}</span>}
                    </div>
                    {sp.notes && <p className="text-xs text-gray-600 mt-1 italic">"{sp.notes}"</p>}
                  </div>
                  <div className="flex gap-1">
                    <Button size="sm" variant="ghost" onClick={() => setEditingNotes({ id: sp.program_id, notes: sp.notes || '' })}><Pencil size={12} /></Button>
                    <Button size="sm" variant="ghost" onClick={() => removeMut.mutate(sp.program_id)}><Trash2 size={12} /></Button>
                  </div>
                </div>
              </Card>
            )
          })}
        </div>
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

      {/* Enhanced Comparison modal */}
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
                {/* Institution */}
                <tr className="border-b">
                  <td className="py-2 px-2 text-gray-500">Institution</td>
                  {comparison.programs.map(p => (
                    <td key={p.id} className="py-2 px-2">{p.institution_name}</td>
                  ))}
                </tr>

                {/* Country */}
                <tr className="border-b">
                  <td className="py-2 px-2 text-gray-500">Country</td>
                  {comparison.programs.map(p => (
                    <td key={p.id} className="py-2 px-2">{p.institution_country}</td>
                  ))}
                </tr>

                {/* Degree */}
                <tr className="border-b">
                  <td className="py-2 px-2 text-gray-500">Degree</td>
                  {comparison.programs.map(p => (
                    <td key={p.id} className="py-2 px-2">
                      <Badge variant="info" size="sm">{DEGREE_LABELS[p.degree_type] || p.degree_type}</Badge>
                    </td>
                  ))}
                </tr>

                {/* Match Score */}
                {(() => {
                  const scores = comparison.programs.map(p => matchLookup[p.id]?.match_score)
                  const best = bestValue(scores, true)
                  return (
                    <tr className="border-b bg-gray-50">
                      <td className="py-2 px-2 text-gray-500 font-medium">Match Score</td>
                      {comparison.programs.map((p, i) => {
                        const m = matchLookup[p.id]
                        const tierInfo = m ? TIER_LABELS[m.match_tier] : null
                        return (
                          <td key={p.id} className="py-2 px-2">
                            {m ? (
                              <div className="flex items-center gap-2">
                                <span className="font-bold">{formatScore(m.match_score)}</span>
                                {tierInfo && <Badge variant={tierInfo.color as any} size="sm">{tierInfo.label}</Badge>}
                                <ValueIndicator value={scores[i]} best={best} />
                              </div>
                            ) : '—'}
                          </td>
                        )
                      })}
                    </tr>
                  )
                })()}

                {/* Tuition */}
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
                            <ValueIndicator value={tuitions[i]} best={best} lower />
                          </div>
                        </td>
                      ))}
                    </tr>
                  )
                })()}

                {/* Acceptance Rate */}
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

                {/* Deadline */}
                <tr className="border-b">
                  <td className="py-2 px-2 text-gray-500">Deadline</td>
                  {comparison.programs.map(p => (
                    <td key={p.id} className="py-2 px-2">{formatDate(p.application_deadline)}</td>
                  ))}
                </tr>

                {/* Duration */}
                <tr className="border-b">
                  <td className="py-2 px-2 text-gray-500">Duration</td>
                  {comparison.programs.map(p => (
                    <td key={p.id} className="py-2 px-2">{(p as any).duration_months ? `${(p as any).duration_months} months` : '—'}</td>
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
