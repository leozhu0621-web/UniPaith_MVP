import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { listSaved, unsaveProgram, updateSavedNotes, comparePrograms } from '../../api/saved-lists'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import Modal from '../../components/ui/Modal'
import EmptyState from '../../components/ui/EmptyState'
import { SkeletonCard } from '../../components/ui/Skeleton'
import { showToast } from '../../stores/toast-store'
import { formatCurrency, formatDate } from '../../utils/format'
import { Heart, Trash2, Pencil, BarChart3 } from 'lucide-react'
import type { SavedProgram, ComparisonResponse } from '../../types'

export default function SavedListPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [editingNotes, setEditingNotes] = useState<{ id: string; notes: string } | null>(null)
  const [comparison, setComparison] = useState<ComparisonResponse | null>(null)

  const { data: saved, isLoading } = useQuery({ queryKey: ['saved'], queryFn: listSaved })
  const removeMut = useMutation({ mutationFn: unsaveProgram, onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['saved'] }); showToast('Removed', 'success') } })
  const notesMut = useMutation({ mutationFn: ({ id, notes }: { id: string; notes: string }) => updateSavedNotes(id, notes), onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['saved'] }); setEditingNotes(null); showToast('Notes updated', 'success') } })
  const compareMut = useMutation({ mutationFn: (ids: string[]) => comparePrograms(ids), onSuccess: (data) => setComparison(data) })

  const toggle = (id: string) => {
    const next = new Set(selected)
    next.has(id) ? next.delete(id) : next.add(id)
    setSelected(next)
  }

  if (isLoading) return <div className="p-6 space-y-4">{Array.from({ length: 3 }).map((_, i) => <SkeletonCard key={i} />)}</div>

  const programs: SavedProgram[] = saved ?? []

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
          title="No saved programs"
          description="Save programs from Discover to compare them here."
          action={{ label: 'Discover Programs', onClick: () => navigate('/s/discover') }}
        />
      ) : (
        <div className="space-y-3">
          {programs.map(sp => (
            <Card key={sp.id} className="p-4">
              <div className="flex items-start gap-3">
                <input
                  type="checkbox"
                  checked={selected.has(sp.program_id)}
                  onChange={() => toggle(sp.program_id)}
                  className="mt-1"
                />
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-sm cursor-pointer hover:underline" onClick={() => navigate(`/s/schools/${sp.program_id}`)}>
                    {sp.program?.program_name || 'Program'}
                  </p>
                  <p className="text-xs text-gray-500">{sp.program?.institution_name}</p>
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
          ))}
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

      {/* Comparison modal */}
      <Modal isOpen={!!comparison} onClose={() => setComparison(null)} title="Program Comparison" size="lg">
        {comparison && (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2 px-2">Feature</th>
                  {comparison.programs.map(p => (
                    <th key={p.id} className="text-left py-2 px-2">{p.program_name}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {['degree_type', 'institution_name', 'institution_country', 'tuition', 'application_deadline'].map(key => (
                  <tr key={key} className="border-b">
                    <td className="py-2 px-2 text-gray-500 capitalize">{key.replace(/_/g, ' ')}</td>
                    {comparison.programs.map(p => (
                      <td key={p.id} className="py-2 px-2">{String((p as any)[key] ?? '—')}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Modal>
    </div>
  )
}
