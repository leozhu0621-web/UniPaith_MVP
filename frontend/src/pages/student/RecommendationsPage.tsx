import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { listRecommendations, createRecommendation, updateRecommendation, deleteRecommendation, sendRecommendationRequest } from '../../api/recommendations'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import Modal from '../../components/ui/Modal'
import Input from '../../components/ui/Input'
import Textarea from '../../components/ui/Textarea'
import Select from '../../components/ui/Select'
import Badge from '../../components/ui/Badge'
import EmptyState from '../../components/ui/EmptyState'
import QueryError from '../../components/ui/QueryError'
import { SkeletonCard } from '../../components/ui/Skeleton'
import { showToast } from '../../stores/toast-store'
import { confirmDialog } from '../../stores/confirm-store'
import { daysUntil, DeadlinePill } from '../../utils/deadline'
import { UserCheck, Plus, Pencil, Trash2, Send, Mail, Check } from 'lucide-react'
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

/**
 * A request is "at risk" when the letter is still out (asked, not yet in) AND
 * its deadline lands within a week — or has already passed. A nudge is the
 * counselor move here, so these surface first.
 */
function isAtRisk(rec: RecommendationRequest): boolean {
  if (rec.status !== 'requested' && rec.status !== 'submitted') return false
  if (!rec.due_date) return false
  const days = daysUntil(rec.due_date)
  return days != null && days <= 7
}

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
    onError: () => showToast("We couldn't create the request. Please try again.", 'error'),
  })

  const updateMut = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => updateRecommendation(id, data),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['recommendations'] }); setShowModal(false); setEditItem(null); showToast('Updated', 'success') },
    onError: () => showToast("We couldn't save your changes. Please try again.", 'error'),
  })

  const deleteMut = useMutation({
    mutationFn: deleteRecommendation,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['recommendations'] }); showToast('Deleted', 'success') },
    onError: () => showToast("We couldn't delete the request. Please try again.", 'error'),
  })

  const sendMut = useMutation({
    mutationFn: sendRecommendationRequest,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['recommendations'] }); showToast('Request sent', 'success') },
    onError: () => showToast("We couldn't send the request. Please try again.", 'error'),
  })

  if (isLoading) return <div className="space-y-4">{Array.from({ length: 3 }).map((_, i) => <SkeletonCard key={i} />)}</div>
  if (isError) {
    const message = error instanceof Error ? error.message : undefined
    return (
      <QueryError
        title="We couldn't load your recommendation requests."
        detail={message}
        onRetry={() => queryClient.invalidateQueries({ queryKey: ['recommendations'] })}
      />
    )
  }

  const recs: RecommendationRequest[] = Array.isArray(recommendations)
    ? recommendations
    : Array.isArray((recommendations as any)?.items)
      ? (recommendations as any).items
      : []

  // Group by status (summary badges — counts only, original grouping)
  const byStatus = { draft: [] as RecommendationRequest[], requested: [] as RecommendationRequest[], submitted: [] as RecommendationRequest[], received: [] as RecommendationRequest[] }
  recs.forEach(r => {
    if (byStatus[r.status as keyof typeof byStatus]) {
      byStatus[r.status as keyof typeof byStatus].push(r)
    }
  })

  // At-risk requests come first (soonest / most-overdue first), then everything
  // else in the existing visual order. Stable: index keeps the original order.
  const sortedRecs = recs
    .map((rec, index) => ({ rec, index }))
    .sort((a, b) => {
      const aRisk = isAtRisk(a.rec)
      const bRisk = isAtRisk(b.rec)
      if (aRisk && bRisk) {
        const aDays = daysUntil(a.rec.due_date) ?? 0
        const bDays = daysUntil(b.rec.due_date) ?? 0
        if (aDays !== bDays) return aDays - bDays
        return a.index - b.index
      }
      if (aRisk !== bRisk) return aRisk ? -1 : 1
      return a.index - b.index
    })
    .map(({ rec }) => rec)

  return (
    <div>
      <div className="flex justify-end mb-4">
        <Button size="sm" onClick={() => { setEditItem(null); setShowModal(true) }}>
          <Plus size={14} className="mr-1" /> New request
        </Button>
      </div>

      {/* Summary badges */}
      {recs.length > 0 && (
        <div className="flex gap-3 mb-6">
          {Object.entries(byStatus).map(([status, items]) => {
            if (items.length === 0) return null
            const config = STATUS_CONFIG[status]
            return (
              <div key={status} className="flex items-center gap-2 px-3 py-1.5 bg-muted rounded-lg">
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
          title="No recommenders yet"
          action={{ label: 'Add a recommender', onClick: () => setShowModal(true) }}
        />
      ) : (
        <div className="space-y-3">
          {sortedRecs.map(rec => {
            const config = STATUS_CONFIG[rec.status] || STATUS_CONFIG.draft
            const atRisk = isAtRisk(rec)
            const days = rec.due_date ? daysUntil(rec.due_date) : null
            const isOut = rec.status === 'requested' || rec.status === 'submitted'
            return (
              <Card pad={false} key={rec.id} className={`p-4 ${atRisk ? 'border-warning/40' : ''}`}>
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 rounded-full bg-muted flex items-center justify-center flex-shrink-0">
                      <UserCheck size={18} className="text-muted-foreground" />
                    </div>
                    <div>
                      <p className="font-semibold text-sm">{rec.recommender_name}</p>
                      {rec.recommender_title && (
                        <p className="text-xs text-muted-foreground">{rec.recommender_title}{rec.recommender_institution ? ` at ${rec.recommender_institution}` : ''}</p>
                      )}
                      <div className="flex items-center gap-2 mt-1">
                        <Badge variant={config.variant as any} size="sm">{config.label}</Badge>
                        {rec.relationship && <span className="text-xs text-muted-foreground">{rec.relationship}</span>}
                      </div>
                      {rec.recommender_email && (
                        <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
                          <Mail size={10} /> {rec.recommender_email}
                        </p>
                      )}
                      {rec.due_date && (
                        <p className="text-xs mt-0.5 flex items-center gap-1.5">
                          <span className="text-muted-foreground">Due</span>
                          <DeadlinePill date={rec.due_date} days={days} />
                          {atRisk && (
                            <span className="text-xs font-medium text-warning">
                              {days != null && days < 0 ? 'Overdue' : 'Due soon'}
                            </span>
                          )}
                        </p>
                      )}
                      {rec.notes && <p className="text-xs text-muted-foreground mt-1 italic">"{rec.notes}"</p>}
                    </div>
                  </div>
                  <div className="flex gap-1">
                    {rec.status === 'draft' && (
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={async () => {
                          const ok = await confirmDialog({
                            title: 'Send this request?',
                            body: `This emails ${rec.recommender_name}${rec.recommender_email ? ` at ${rec.recommender_email}` : ''} a recommendation request.`,
                            confirmLabel: 'Send',
                          })
                          if (!ok) return
                          sendMut.mutate(rec.id)
                        }}
                        loading={sendMut.isPending}
                      >
                        <Send size={12} className="mr-1" /> Send
                      </Button>
                    )}
                    {isOut && (
                      <Button
                        size="sm"
                        variant="secondary"
                        aria-label={`Send a reminder to ${rec.recommender_name}`}
                        onClick={async () => {
                          const ok = await confirmDialog({
                            title: 'Send a reminder?',
                            body: `This emails ${rec.recommender_name}${rec.recommender_email ? ` at ${rec.recommender_email}` : ''} a reminder about their recommendation.`,
                            confirmLabel: 'Send reminder',
                          })
                          if (!ok) return
                          sendMut.mutate(rec.id)
                        }}
                        loading={sendMut.isPending}
                      >
                        <Send size={12} className="mr-1" /> Nudge
                      </Button>
                    )}
                    {isOut && (
                      <Button
                        size="sm"
                        variant="secondary"
                        aria-label={`Mark ${rec.recommender_name}'s letter received`}
                        onClick={async () => {
                          const ok = await confirmDialog({
                            title: 'Mark this letter received?',
                            body: `Confirm that ${rec.recommender_name}'s recommendation letter is in. This closes the loop and counts toward your readiness.`,
                            confirmLabel: 'Mark received',
                          })
                          if (!ok) return
                          updateMut.mutate({ id: rec.id, data: { status: 'received' } })
                        }}
                        loading={updateMut.isPending}
                      >
                        <Check size={12} className="mr-1" /> Mark received
                      </Button>
                    )}
                    <Button size="sm" variant="ghost" aria-label={`Edit request for ${rec.recommender_name}`} onClick={() => { setEditItem(rec); setShowModal(true) }}><Pencil size={12} /></Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      aria-label={`Delete request for ${rec.recommender_name}`}
                      onClick={async () => {
                        const ok = await confirmDialog({
                          title: 'Delete this request?',
                          body: `Remove the recommendation request for ${rec.recommender_name}? This can't be undone.`,
                          confirmLabel: 'Delete',
                          destructive: true,
                        })
                        if (!ok) return
                        deleteMut.mutate(rec.id)
                      }}
                    >
                      <Trash2 size={12} />
                    </Button>
                  </div>
                </div>
              </Card>
            )
          })}
        </div>
      )}

      {/* Create/Edit Modal */}
      <Modal isOpen={showModal} onClose={() => { setShowModal(false); setEditItem(null) }} title={editItem ? 'Edit request' : 'New request'}>
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
      <Input label="Recommender name" {...register('recommender_name')} required />
      <Input label="Email" type="email" {...register('recommender_email')} />
      <Input label="Title or position" {...register('recommender_title')} />
      <Input label="Institution" {...register('recommender_institution')} />
      <Select
        label="Relationship"
        placeholder="Select..."
        options={RELATIONSHIP_OPTIONS.map(r => ({ value: r, label: r }))}
        {...register('relationship')}
      />
      <Input label="Due date" type="date" {...register('due_date')} />
      <Textarea label="Notes" {...register('notes')} placeholder="Any special instructions or context..." />
      <Button type="submit" loading={loading} className="w-full">Save</Button>
    </form>
  )
}
