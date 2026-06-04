import { useMemo, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Calendar, Plus, MoreHorizontal } from 'lucide-react'
import { getInstitutionPrograms } from '../../api/institutions'
import {
  getInstitutionInterviews,
  completeInterview,
  cancelInterview,
  markInterviewNoShow,
} from '../../api/interviews-admin'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Tabs from '../../components/ui/Tabs'
import Select from '../../components/ui/Select'
import EmptyState from '../../components/ui/EmptyState'
import Skeleton from '../../components/ui/Skeleton'
import Dropdown from '../../components/ui/Dropdown'
import QueryError from '../../components/ui/QueryError'
import InstitutionPageHeader from '../../components/institution/InstitutionPageHeader'
import { showToast } from '../../stores/toast-store'
import { confirmDialog } from '../../stores/confirm-store'
import { formatDateTime } from '../../utils/format'
import { STATUS_COLORS, INTERVIEW_TYPES, INTERVIEW_TYPE_LABELS } from '../../utils/constants'
import type { Interview, Program } from '../../types'
import ProposeInterviewModal from './interviews/ProposeInterviewModal'
import ScoreInterviewModal from './interviews/ScoreInterviewModal'
import RescheduleInterviewModal from './interviews/RescheduleInterviewModal'

type BadgeVariant = 'neutral' | 'info' | 'success' | 'warning' | 'danger'

const REC_LABELS: Record<string, string> = {
  recommend: 'Recommend',
  neutral: 'Neutral',
  not_recommend: 'Do not recommend',
}

function humanize(status: string): string {
  return status.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

export default function InterviewsPage({ embedded = false }: { embedded?: boolean }) {
  const [activeTab, setActiveTab] = useState('upcoming')
  const [programFilter, setProgramFilter] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  const [showPropose, setShowPropose] = useState(false)
  const [scoreTarget, setScoreTarget] = useState<Interview | null>(null)
  const [rescheduleTarget, setRescheduleTarget] = useState<Interview | null>(null)

  const qc = useQueryClient()

  const interviewsQ = useQuery({
    queryKey: ['institution-interviews'],
    queryFn: () => getInstitutionInterviews(),
  })
  const interviews: Interview[] = useMemo(
    () => (Array.isArray(interviewsQ.data) ? interviewsQ.data : []),
    [interviewsQ.data],
  )

  const programsQ = useQuery({ queryKey: ['institution-programs'], queryFn: getInstitutionPrograms })
  const programs: Program[] = Array.isArray(programsQ.data) ? programsQ.data : []

  const invalidate = () => qc.invalidateQueries({ queryKey: ['institution-interviews'] })

  const completeMut = useMutation({
    mutationFn: completeInterview,
    onSuccess: () => {
      invalidate()
      showToast('Interview marked complete', 'success')
    },
    onError: () => showToast('Failed to complete', 'error'),
  })
  const cancelMut = useMutation({
    mutationFn: cancelInterview,
    onSuccess: () => {
      invalidate()
      showToast('Interview cancelled', 'success')
    },
    onError: () => showToast('Failed to cancel', 'error'),
  })
  const noShowMut = useMutation({
    mutationFn: markInterviewNoShow,
    onSuccess: () => {
      invalidate()
      showToast('Marked as no-show', 'success')
    },
    onError: () => showToast('Failed to update', 'error'),
  })

  const confirmedCount = interviews.filter(i => i.status === 'confirmed').length
  const awaitingCount = interviews.filter(i => i.status === 'proposed').length
  const completedCount = interviews.filter(i => i.status === 'completed').length

  const tabs = [
    { id: 'upcoming', label: 'Upcoming' },
    { id: 'completed', label: 'Completed' },
    { id: 'all', label: 'All' },
  ]

  const filtered = useMemo(() => {
    return interviews.filter(i => {
      if (activeTab === 'upcoming' && !['proposed', 'confirmed'].includes(i.status)) return false
      if (activeTab === 'completed' && i.status !== 'completed') return false
      if (programFilter && i.program?.id !== programFilter) return false
      if (typeFilter && i.interview_type !== typeFilter) return false
      return true
    })
  }, [interviews, activeTab, programFilter, typeFilter])

  const programOptions = [
    { value: '', label: 'All programs' },
    ...programs.map(p => ({ value: p.id, label: p.program_name })),
  ]
  const typeOptions = [{ value: '', label: 'All types' }, ...INTERVIEW_TYPES]

  const statusBadge = (iv: Interview) => {
    if (iv.async_expired) return <Badge variant="danger">No submission received</Badge>
    if (iv.status === 'proposed') return <Badge variant="warning">Awaiting student</Badge>
    const variant = (STATUS_COLORS[iv.status] as BadgeVariant) ?? 'neutral'
    return <Badge variant={variant}>{humanize(iv.status)}</Badge>
  }

  const scheduledLabel = (iv: Interview) => {
    if (iv.scheduled_at || iv.confirmed_time) return formatDateTime(iv.scheduled_at ?? iv.confirmed_time)
    if (iv.async_window_end) return `By ${formatDateTime(iv.async_window_end)}`
    if (iv.proposed_times?.length) return `${iv.proposed_times.length} proposed`
    return '—'
  }

  const rowActions = (iv: Interview) => {
    const scoreable = !['proposed', 'cancelled'].includes(iv.status)
    const completable = ['proposed', 'confirmed'].includes(iv.status)
    const cancellable = !['completed', 'cancelled'].includes(iv.status)
    const noshowable = ['proposed', 'confirmed'].includes(iv.status) || iv.async_expired

    const confirmNoShow = async () => {
      const ok = await confirmDialog({
        title: 'Mark as no-show?',
        body: 'This records that the applicant did not attend and closes out the interview.',
        confirmLabel: 'Mark no-show',
        destructive: true,
      })
      if (!ok) return
      noShowMut.mutate(iv.id)
    }
    const confirmCancel = async () => {
      const ok = await confirmDialog({
        title: 'Cancel interview?',
        body: 'This cancels the interview for the applicant and cannot be undone.',
        confirmLabel: 'Cancel interview',
        destructive: true,
      })
      if (!ok) return
      cancelMut.mutate(iv.id)
    }

    const menu: { label: string; onClick: () => void; variant?: 'default' | 'danger' }[] = []
    if (completable && scoreable) menu.push({ label: 'Mark complete', onClick: () => completeMut.mutate(iv.id) })
    if (cancellable) menu.push({ label: 'Reschedule', onClick: () => setRescheduleTarget(iv) })
    if (noshowable) menu.push({ label: 'Mark no-show', onClick: confirmNoShow })
    if (cancellable) menu.push({ label: 'Cancel interview', onClick: confirmCancel, variant: 'danger' })

    return (
      <div className="flex items-center justify-end gap-1">
        {scoreable ? (
          <Button size="sm" variant="ghost" className="text-secondary" onClick={() => setScoreTarget(iv)}>
            Score
          </Button>
        ) : completable ? (
          <Button size="sm" variant="ghost" onClick={() => completeMut.mutate(iv.id)}>
            Complete
          </Button>
        ) : null}
        {menu.length > 0 && (
          <Dropdown
            trigger={
              <button
                className="p-1.5 rounded-md hover:bg-muted text-muted-foreground transition-colors"
                aria-label="More actions"
              >
                <MoreHorizontal size={16} />
              </button>
            }
            items={menu}
          />
        )}
      </div>
    )
  }

  const body = (
    <>
      {!embedded && (
        <InstitutionPageHeader
          title="Interviews"
          description="Propose, schedule, score, and complete admissions interviews."
          actions={
            <Button variant="secondary" onClick={() => setShowPropose(true)} className="flex items-center gap-2">
              <Plus size={16} /> Propose interview
            </Button>
          }
        />
      )}

      {/* KPI row (§4) */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <Card className="p-3">
          <p className="text-xs text-muted-foreground">Confirmed</p>
          <p className="text-xl font-semibold text-success">{confirmedCount}</p>
        </Card>
        <Card className="p-3">
          <p className="text-xs text-muted-foreground">Awaiting student</p>
          <p className="text-xl font-semibold text-warning">{awaitingCount}</p>
        </Card>
        <Card className="p-3">
          <p className="text-xs text-muted-foreground">Completed</p>
          <p className="text-xl font-semibold text-foreground">{completedCount}</p>
        </Card>
      </div>

      {/* Tabs + filters */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />
        <div className="flex items-center gap-2">
          <Select
            options={programOptions}
            value={programFilter}
            onChange={e => setProgramFilter(e.target.value)}
            uiSize="sm"
            aria-label="Filter by program"
          />
          <Select
            options={typeOptions}
            value={typeFilter}
            onChange={e => setTypeFilter(e.target.value)}
            uiSize="sm"
            aria-label="Filter by type"
          />
          {embedded && (
            <Button variant="secondary" size="sm" onClick={() => setShowPropose(true)} className="flex items-center gap-1 whitespace-nowrap">
              <Plus size={14} /> Propose
            </Button>
          )}
        </div>
      </div>

      {/* Table */}
      <Card>
        {interviewsQ.isLoading ? (
          <div className="p-4 space-y-2">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-12" />
            ))}
          </div>
        ) : interviewsQ.isError ? (
          <QueryError variant="inline" detail="We couldn't load your interviews." onRetry={() => interviewsQ.refetch()} />
        ) : filtered.length === 0 ? (
          <EmptyState
            icon={<Calendar size={40} />}
            title={interviews.length === 0 ? 'No interviews scheduled.' : 'No interviews match these filters.'}
            description={
              interviews.length === 0
                ? 'Propose an interview to an applicant to get started.'
                : 'Try a different tab, program, or type.'
            }
            action={interviews.length === 0 ? { label: 'Propose interview', onClick: () => setShowPropose(true) } : undefined}
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left text-xs text-muted-foreground">
                  <th className="px-4 py-2.5 font-medium">Applicant</th>
                  <th className="px-4 py-2.5 font-medium">Program</th>
                  <th className="px-4 py-2.5 font-medium">Type</th>
                  <th className="px-4 py-2.5 font-medium">Status</th>
                  <th className="px-4 py-2.5 font-medium">Scheduled</th>
                  <th className="px-4 py-2.5 font-medium text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {filtered.map(iv => (
                  <tr key={iv.id} className="hover:bg-muted/40 transition-colors">
                    <td className="px-4 py-3 text-foreground font-medium">{iv.applicant?.name || 'Applicant'}</td>
                    <td className="px-4 py-3 text-muted-foreground">{iv.program?.name || '—'}</td>
                    <td className="px-4 py-3">
                      <Badge variant="info">{INTERVIEW_TYPE_LABELS[iv.interview_type] || iv.interview_type}</Badge>
                    </td>
                    <td className="px-4 py-3">
                      {statusBadge(iv)}
                      {iv.recommendation && (
                        <span className="block text-xs text-muted-foreground mt-1">
                          {REC_LABELS[iv.recommendation] || iv.recommendation}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-muted-foreground whitespace-nowrap">{scheduledLabel(iv)}</td>
                    <td className="px-4 py-3">{rowActions(iv)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <ProposeInterviewModal
        isOpen={showPropose}
        onClose={() => setShowPropose(false)}
        onProposed={invalidate}
        programs={programs}
      />
      <ScoreInterviewModal
        isOpen={scoreTarget !== null}
        onClose={() => setScoreTarget(null)}
        onScored={invalidate}
        interview={scoreTarget}
      />
      <RescheduleInterviewModal
        isOpen={rescheduleTarget !== null}
        onClose={() => setRescheduleTarget(null)}
        onRescheduled={invalidate}
        interview={rescheduleTarget}
      />
    </>
  )

  if (embedded) return <div className="space-y-4">{body}</div>
  return <div className="p-6 space-y-4">{body}</div>
}
