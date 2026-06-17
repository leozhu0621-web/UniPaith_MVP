import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Inbox, MessageSquare, CheckCircle2, Clock, User, UserPlus } from 'lucide-react'
import QueryError from '../../components/ui/QueryError'
import { getInquiries, updateInquiry, getTemplates } from '../../api/institutions'
import { getTeam } from '../../api/settings'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Select from '../../components/ui/Select'
import Modal from '../../components/ui/Modal'
import Textarea from '../../components/ui/Textarea'
import Tabs from '../../components/ui/Tabs'
import EmptyState from '../../components/ui/EmptyState'
import Skeleton from '../../components/ui/Skeleton'
import InstitutionPageHeader from '../../components/institution/InstitutionPageHeader'
import { showToast } from '../../stores/toast-store'
import { formatDateTime } from '../../utils/format'
import type { Inquiry } from '../../types'

// Spec 31 §7 — an inquiry left unanswered ≥ 4h is flagged for SLA visibility.
const FOUR_HOURS_MS = 4 * 60 * 60 * 1000
function isOverdue(inq: Inquiry): boolean {
  if (inq.status !== 'new' && inq.status !== 'in_progress') return false
  return Date.now() - new Date(inq.created_at).getTime() >= FOUR_HOURS_MS
}

const STATUS_BADGE: Record<string, 'neutral' | 'info' | 'success' | 'warning'> = {
  new: 'warning',
  in_progress: 'info',
  responded: 'success',
  closed: 'neutral',
}

export default function InquiriesPage({ embedded = false }: { embedded?: boolean }) {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState('all')
  const [selected, setSelected] = useState<Inquiry | null>(null)
  const [responseText, setResponseText] = useState('')

  const tabs = [
    { id: 'all', label: 'All' },
    { id: 'new', label: 'New' },
    { id: 'in_progress', label: 'In Progress' },
    { id: 'responded', label: 'Responded' },
    { id: 'closed', label: 'Closed' },
  ]

  const statusFilter = activeTab === 'all' ? undefined : activeTab
  const inquiriesQ = useQuery({
    queryKey: ['inquiries', statusFilter],
    queryFn: () => getInquiries(statusFilter),
  })
  const inquiries: Inquiry[] = Array.isArray(inquiriesQ.data) ? inquiriesQ.data : []

  const respondMut = useMutation({
    mutationFn: (p: { id: string; response_text: string }) =>
      updateInquiry(p.id, { response_text: p.response_text, status: 'responded' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inquiries'] })
      showToast('Response sent', 'success')
      setSelected(null)
      setResponseText('')
    },
    onError: () => showToast("We couldn't send the response. Please try again.", 'error'),
  })

  const statusMut = useMutation({
    mutationFn: (p: { id: string; status: string }) =>
      updateInquiry(p.id, { status: p.status }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inquiries'] })
      showToast('Status updated', 'success')
    },
    onError: () => showToast("We couldn't update the status. Please try again.", 'error'),
  })

  // Spec 31 §7 — response templates (Spec 25) + assign-to-staff.
  // Only fetched when a detail modal is open (their only consumer).
  const templatesQ = useQuery({ queryKey: ['inquiry-templates'], queryFn: () => getTemplates(), enabled: !!selected })
  const templates = Array.isArray(templatesQ.data) ? templatesQ.data : []
  const teamQ = useQuery({ queryKey: ['institution-team'], queryFn: getTeam, enabled: !!selected })
  // Only active members are real users assignable to an inquiry (pending invites are not).
  const assignableStaff = (Array.isArray(teamQ.data) ? teamQ.data : []).filter(m => m.status === 'active')
  const staffEmail = (id: string | null) =>
    id ? assignableStaff.find(m => m.id === id)?.email ?? null : null

  const assignMut = useMutation({
    mutationFn: (p: { id: string; assigned_to: string }) =>
      updateInquiry(p.id, { assigned_to: p.assigned_to }),
    onSuccess: (updated: Inquiry) => {
      queryClient.invalidateQueries({ queryKey: ['inquiries'] })
      showToast('Inquiry assigned', 'success')
      setSelected(updated)
    },
    onError: () => showToast('Failed to assign inquiry', 'error'),
  })

  const applyTemplate = (templateId: string) => {
    const t = templates.find(tpl => tpl.id === templateId)
    if (t) setResponseText(t.body)
  }

  const openDetail = (inq: Inquiry) => {
    setSelected(inq)
    setResponseText(inq.response_text || '')
  }

  const newCount = inquiries.filter(i => i.status === 'new').length

  const inner = (
    <div className="space-y-4">
      {!embedded && (
        <InstitutionPageHeader
          title="Inquiry Queue"
        />
      )}

      {inquiries.length > 0 && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <Card pad={false} className="p-3">
            <p className="text-xs text-muted-foreground">Total</p>
            <p className="text-xl font-semibold text-foreground">{inquiries.length}</p>
          </Card>
          <Card pad={false} className="p-3 border-warning-soft">
            <p className="text-xs text-warning">New</p>
            <p className="text-xl font-bold text-warning">{newCount}</p>
          </Card>
          <Card pad={false} className="p-3">
            <p className="text-xs text-muted-foreground">In Progress</p>
            <p className="text-xl font-semibold text-foreground">{inquiries.filter(i => i.status === 'in_progress').length}</p>
          </Card>
          <Card pad={false} className="p-3">
            <p className="text-xs text-muted-foreground">Responded</p>
            <p className="text-xl font-semibold text-foreground">{inquiries.filter(i => i.status === 'responded').length}</p>
          </Card>
        </div>
      )}

      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

      {inquiriesQ.isLoading ? (
        <div className="space-y-3">{Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-24" />)}</div>
      ) : inquiriesQ.isError ? (
        <QueryError variant="inline" detail="We couldn't load inquiries." onRetry={() => inquiriesQ.refetch()} />
      ) : inquiries.length === 0 ? (
        <EmptyState
          icon={<Inbox size={40} />}
          title="No inquiries"
          description="When students request info from your school or program pages, their inquiries will appear here."
        />
      ) : (
        <div className="space-y-2">
          {inquiries.map(inq => (
            <Card pad={false} key={inq.id} className="p-4 cursor-pointer hover:shadow-md transition-shadow" onClick={() => openDetail(inq)}>
              <div className="flex items-start justify-between mb-1">
                <div className="flex items-center gap-2">
                  <h3 className="font-semibold text-foreground text-sm">{inq.subject}</h3>
                  <Badge variant={STATUS_BADGE[inq.status] ?? 'neutral'}>{inq.status.replace('_', ' ')}</Badge>
                  {isOverdue(inq) && <Badge variant="warning">Unanswered ≥ 4h</Badge>}
                </div>
                {inq.program_name && <Badge variant="info">{inq.program_name}</Badge>}
              </div>
              <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground mt-1">
                <span className="flex items-center gap-1"><User size={12} /> {inq.student_name}</span>
                <span>{inq.student_email}</span>
                <span className="flex items-center gap-1"><Clock size={12} /> {formatDateTime(inq.created_at)}</span>
                {staffEmail(inq.assigned_to) && (
                  <span className="flex items-center gap-1 text-secondary"><UserPlus size={12} /> {staffEmail(inq.assigned_to)}</span>
                )}
              </div>
              <p className="text-sm text-muted-foreground mt-2 line-clamp-2">{inq.message}</p>
            </Card>
          ))}
        </div>
      )}

      {/* Detail / Respond Modal */}
      <Modal isOpen={!!selected} onClose={() => setSelected(null)} title={selected?.subject ?? ''}>
        {selected && (
          <div className="space-y-4">
            <div className="flex items-center gap-3 text-sm text-muted-foreground">
              <span className="flex items-center gap-1"><User size={14} /> {selected.student_name}</span>
              <span>{selected.student_email}</span>
              <Badge variant={STATUS_BADGE[selected.status]}>{selected.status.replace('_', ' ')}</Badge>
            </div>
            {selected.program_name && (
              <Badge variant="info">Program: {selected.program_name}</Badge>
            )}
            <Card pad={false} className="p-3 bg-muted">
              <p className="text-xs text-muted-foreground mb-1">Student's message</p>
              <p className="text-sm text-foreground whitespace-pre-wrap">{selected.message}</p>
            </Card>
            <p className="text-xs text-muted-foreground/70">Received: {formatDateTime(selected.created_at)}</p>

            {selected.response_text && selected.responded_at && (
              <Card pad={false} className="p-3 bg-success-soft border-success-soft">
                <p className="text-xs text-success mb-1 flex items-center gap-1"><CheckCircle2 size={12} /> Responded {formatDateTime(selected.responded_at)}</p>
                <p className="text-sm text-foreground whitespace-pre-wrap">{selected.response_text}</p>
              </Card>
            )}

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <Select
                label="Assign to staff"
                options={assignableStaff.map(m => ({ value: m.id, label: m.email }))}
                placeholder={assignableStaff.length ? 'Assign…' : 'No staff available'}
                value={selected.assigned_to ?? ''}
                onChange={e => e.target.value && assignMut.mutate({ id: selected.id, assigned_to: e.target.value })}
                disabled={!assignableStaff.length || assignMut.isPending}
              />
              <Select
                label="Insert response template"
                options={templates.map(t => ({ value: t.id, label: t.name }))}
                placeholder={templates.length ? 'Choose a template…' : 'No templates yet'}
                value=""
                onChange={e => { if (e.target.value) applyTemplate(e.target.value) }}
                disabled={!templates.length}
              />
            </div>

            <Textarea
              label="Your Response"
              value={responseText}
              onChange={e => setResponseText(e.target.value)}
              rows={4}
              placeholder="Type your response to the student..."
            />

            <div className="flex items-center justify-between">
              <div className="flex gap-2">
                {selected.status === 'new' && (
                  <Button variant="ghost" size="sm" onClick={() => statusMut.mutate({ id: selected.id, status: 'in_progress' })}>
                    Mark In Progress
                  </Button>
                )}
                {selected.status !== 'closed' && (
                  <Button variant="ghost" size="sm" onClick={() => statusMut.mutate({ id: selected.id, status: 'closed' })}>
                    Close
                  </Button>
                )}
              </div>
              <Button
                onClick={() => respondMut.mutate({ id: selected.id, response_text: responseText })}
                disabled={respondMut.isPending || !responseText.trim()}
                className="flex items-center gap-2"
              >
                <MessageSquare size={14} /> {respondMut.isPending ? 'Sending...' : 'Send Response'}
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )

  if (embedded) return inner
  return <div className="p-6">{inner}</div>
}
