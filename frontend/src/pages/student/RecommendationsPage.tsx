import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { listRecommendations, createRecommendation, updateRecommendation, deleteRecommendation, sendRecommendationRequest } from '../../api/recommendations'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import Modal from '../../components/ui/Modal'
import Input from '../../components/ui/Input'
import Textarea from '../../components/ui/Textarea'
import Badge from '../../components/ui/Badge'
import EmptyState from '../../components/ui/EmptyState'
import { SkeletonCard } from '../../components/ui/Skeleton'
import { showToast } from '../../stores/toast-store'
import { formatDate } from '../../utils/format'
import { UserCheck, Plus, Pencil, Trash2, Send, Mail } from 'lucide-react'
import type { RecommendationRequest } from '../../types'

const STATUS_CONFIG: Record<string, { label: string; variant: string }> = {
  draft: { label: 'Draft', variant: 'neutral' },
  requested: { label: 'Requested', variant: 'info' },
  submitted: { label: 'Submitted', variant: 'warning' },
  received: { label: 'Received', variant: 'success' },
}

const RELATIONSHIP_OPTIONS = [
  'Professor', 'Academic Advisor', 'Research Supervisor',
  'Employer', 'Mentor', 'Colleague', 'Other',
]

export default function RecommendationsPage() {
  const queryClient = useQueryClient()
  const [showModal, setShowModal] = useState(false)
  const [editItem, setEditItem] = useState<RecommendationRequest | null>(null)

  const { data: recommendations, isLoading, isError, error } = useQuery({
    queryKey: ['recommendations'],
    queryFn: listRecommendations,
  })

  const createMut = useMutation({
    mutationFn: createRecommendation,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['recommendations'] }); setShowModal(false); showToast('Recommendation request created', 'success') },
  })

  const updateMut = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => updateRecommendation(id, data),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['recommendations'] }); setShowModal(false); setEditItem(null); showToast('Updated', 'success') },
  })

  const deleteMut = useMutation({
    mutationFn: deleteRecommendation,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['recommendations'] }); showToast('Deleted', 'success') },
  })

  const sendMut = useMutation({
    mutationFn: sendRecommendationRequest,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['recommendations'] }); showToast('Request sent', 'success') },
  })

  if (isLoading) return <div className="p-6 max-w-3xl mx-auto space-y-4">{Array.from({ length: 3 }).map((_, i) => <SkeletonCard key={i} />)}</div>
  if (isError) {
    const message = error instanceof Error ? error.message : 'Failed to load recommendation requests.'
    return (
      <div className="p-6 max-w-3xl mx-auto">
        <Card className="p-5">
          <h1 className="text-xl font-semibold mb-2">Recommendation Letters</h1>
          <p className="text-sm text-red-600">{message}</p>
          <Button size="sm" className="mt-4" onClick={() => queryClient.invalidateQueries({ queryKey: ['recommendations'] })}>
            Retry
          </Button>
        </Card>
      </div>
    )
  }

  const recs: RecommendationRequest[] = Array.isArray(recommendations)
    ? recommendations
    : Array.isArray((recommendations as any)?.items)
      ? (recommendations as any).items
      : []

  // Group by status
  const byStatus = { draft: [] as RecommendationRequest[], requested: [] as RecommendationRequest[], submitted: [] as RecommendationRequest[], received: [] as RecommendationRequest[] }
  recs.forEach(r => {
    if (byStatus[r.status as keyof typeof byStatus]) {
      byStatus[r.status as keyof typeof byStatus].push(r)
    }
  })

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold">Recommendation Letters</h1>
          <p className="text-sm text-gray-500 mt-1">Track recommendation requests from your recommenders.</p>
        </div>
        <Button size="sm" onClick={() => { setEditItem(null); setShowModal(true) }}>
          <Plus size={14} className="mr-1" /> New Request
        </Button>
      </div>

      {/* Summary badges */}
      {recs.length > 0 && (
        <div className="flex gap-3 mb-6">
          {Object.entries(byStatus).map(([status, items]) => {
            if (items.length === 0) return null
            const config = STATUS_CONFIG[status]
            return (
              <div key={status} className="flex items-center gap-2 px-3 py-1.5 bg-gray-50 rounded-lg">
                <Badge variant={config.variant as any} size="sm">{config.label}</Badge>
                <span className="text-sm font-medium">{items.length}</span>
              </div>
            )
          })}
        </div>
      )}

      {recs.length === 0 ? (
        <EmptyState
          icon={<UserCheck size={48} />}
          title="You can add recommenders when you're ready"
          description="Track recommendation letter requests here."
          action={{ label: 'Add Recommender', onClick: () => setShowModal(true) }}
        />
      ) : (
        <div className="space-y-3">
          {recs.map(rec => {
            const config = STATUS_CONFIG[rec.status] || STATUS_CONFIG.draft
            return (
              <Card key={rec.id} className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center flex-shrink-0">
                      <UserCheck size={18} className="text-gray-500" />
                    </div>
                    <div>
                      <p className="font-semibold text-sm">{rec.recommender_name}</p>
                      {rec.recommender_title && (
                        <p className="text-xs text-gray-500">{rec.recommender_title}{rec.recommender_institution ? ` at ${rec.recommender_institution}` : ''}</p>
                      )}
                      <div className="flex items-center gap-2 mt-1">
                        <Badge variant={config.variant as any} size="sm">{config.label}</Badge>
                        {rec.relationship && <span className="text-xs text-gray-400">{rec.relationship}</span>}
                      </div>
                      {rec.recommender_email && (
                        <p className="text-xs text-gray-400 mt-1 flex items-center gap-1">
                          <Mail size={10} /> {rec.recommender_email}
                        </p>
                      )}
                      {rec.due_date && (
                        <p className="text-xs text-gray-400 mt-0.5">Due: {formatDate(rec.due_date)}</p>
                      )}
                      {rec.notes && <p className="text-xs text-gray-500 mt-1 italic">"{rec.notes}"</p>}
                    </div>
                  </div>
                  <div className="flex gap-1">
                    {rec.status === 'draft' && (
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={() => sendMut.mutate(rec.id)}
                        loading={sendMut.isPending}
                      >
                        <Send size={12} className="mr-1" /> Send
                      </Button>
                    )}
                    <Button size="sm" variant="ghost" onClick={() => { setEditItem(rec); setShowModal(true) }}><Pencil size={12} /></Button>
                    <Button size="sm" variant="ghost" onClick={() => deleteMut.mutate(rec.id)}><Trash2 size={12} /></Button>
                  </div>
                </div>
              </Card>
            )
          })}
        </div>
      )}

      {/* Create/Edit Modal */}
      <Modal isOpen={showModal} onClose={() => { setShowModal(false); setEditItem(null) }} title={editItem ? 'Edit Recommendation Request' : 'New Recommendation Request'}>
        <RecommendationForm
          defaultValues={editItem}
          onSubmit={data => {
            if (editItem) {
              updateMut.mutate({ id: editItem.id, data })
            } else {
              createMut.mutate(data)
            }
          }}
          loading={createMut.isPending || updateMut.isPending}
        />
      </Modal>
    </div>
  )
}

function RecommendationForm({ defaultValues, onSubmit, loading }: { defaultValues: any; onSubmit: (d: any) => void; loading: boolean }) {
  const { register, handleSubmit } = useForm({
    defaultValues: {
      recommender_name: defaultValues?.recommender_name || '',
      recommender_email: defaultValues?.recommender_email || '',
      recommender_title: defaultValues?.recommender_title || '',
      recommender_institution: defaultValues?.recommender_institution || '',
      relationship: defaultValues?.relationship || '',
      due_date: defaultValues?.due_date?.slice(0, 10) || '',
      notes: defaultValues?.notes || '',
    },
  })

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-3">
      <Input label="Recommender Name" {...register('recommender_name')} required />
      <Input label="Email" type="email" {...register('recommender_email')} />
      <Input label="Title / Position" {...register('recommender_title')} />
      <Input label="Institution / Organization" {...register('recommender_institution')} />
      <div>
        <label className="text-sm text-brand-slate-600 mb-1 block">Relationship</label>
        <select {...register('relationship')} className="w-full text-sm border border-gray-300 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-brand-slate-700">
          <option value="">Select...</option>
          {RELATIONSHIP_OPTIONS.map(r => (
            <option key={r} value={r}>{r}</option>
          ))}
        </select>
      </div>
      <Input label="Due Date" type="date" {...register('due_date')} />
      <Textarea label="Notes" {...register('notes')} placeholder="Any special instructions or context..." />
      <Button type="submit" loading={loading} className="w-full">Save</Button>
    </form>
  )
}
