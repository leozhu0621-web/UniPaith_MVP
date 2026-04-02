import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Megaphone, Plus, Send, Edit2, Trash2, BarChart3, Clock } from 'lucide-react'
import {
  getCampaigns, createCampaign, updateCampaign, deleteCampaign,
  sendCampaign, getCampaignMetrics, getSegments, getInstitutionPrograms,
} from '../../api/institutions'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Modal from '../../components/ui/Modal'
import Input from '../../components/ui/Input'
import Select from '../../components/ui/Select'
import Textarea from '../../components/ui/Textarea'
import Tabs from '../../components/ui/Tabs'
import EmptyState from '../../components/ui/EmptyState'
import Skeleton from '../../components/ui/Skeleton'
import InstitutionPageHeader from '../../components/institution/InstitutionPageHeader'
import { showToast } from '../../stores/toast-store'
import { formatDateTime, formatDate } from '../../utils/format'
import type { Campaign, CampaignMetrics, Segment, Program } from '../../types'

const CAMPAIGN_TYPES = [
  { value: 'email', label: 'Email' },
  { value: 'sms', label: 'SMS' },
  { value: 'in_app', label: 'In-App' },
]

const STATUS_BADGE: Record<string, 'neutral' | 'info' | 'success' | 'warning'> = {
  draft: 'neutral',
  scheduled: 'info',
  sent: 'success',
}

export default function CampaignsPage() {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState('all')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showMetricsModal, setShowMetricsModal] = useState(false)
  const [editTarget, setEditTarget] = useState<Campaign | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<Campaign | null>(null)
  const [metricsTarget, setMetricsTarget] = useState<string | null>(null)

  // Form state
  const [campaignName, setCampaignName] = useState('')
  const [campaignType, setCampaignType] = useState('email')
  const [subject, setSubject] = useState('')
  const [body, setBody] = useState('')
  const [programId, setProgramId] = useState('')
  const [segmentId, setSegmentId] = useState('')
  const [scheduledAt, setScheduledAt] = useState('')

  const tabs = [
    { id: 'all', label: 'All' },
    { id: 'draft', label: 'Drafts' },
    { id: 'scheduled', label: 'Scheduled' },
    { id: 'sent', label: 'Sent' },
  ]

  const statusFilter = activeTab === 'all' ? undefined : activeTab
  const campaignsQ = useQuery({
    queryKey: ['campaigns', statusFilter],
    queryFn: () => getCampaigns(statusFilter),
  })
  const campaigns: Campaign[] = Array.isArray(campaignsQ.data) ? campaignsQ.data : []

  const programsQ = useQuery({ queryKey: ['institution-programs'], queryFn: getInstitutionPrograms })
  const programs: Program[] = Array.isArray(programsQ.data) ? programsQ.data : []

  const segmentsQ = useQuery({ queryKey: ['segments'], queryFn: getSegments })
  const segments: Segment[] = Array.isArray(segmentsQ.data) ? segmentsQ.data : []

  const metricsQ = useQuery({
    queryKey: ['campaign-metrics', metricsTarget],
    queryFn: () => getCampaignMetrics(metricsTarget!),
    enabled: !!metricsTarget && showMetricsModal,
  })
  const metrics: CampaignMetrics | undefined = metricsQ.data

  const programOptions = [{ value: '', label: 'None' }, ...programs.map(p => ({ value: p.id, label: p.program_name }))]
  const segmentOptions = [{ value: '', label: 'None' }, ...segments.map(s => ({ value: s.id, label: s.segment_name }))]

  const resetForm = () => {
    setCampaignName('')
    setCampaignType('email')
    setSubject('')
    setBody('')
    setProgramId('')
    setSegmentId('')
    setScheduledAt('')
    setEditTarget(null)
  }

  const openCreate = () => { resetForm(); setShowCreateModal(true) }
  const openEdit = (c: Campaign) => {
    setEditTarget(c)
    setCampaignName(c.campaign_name)
    setCampaignType(c.campaign_type ?? 'email')
    setSubject(c.message_subject ?? '')
    setBody(c.message_body ?? '')
    setProgramId(c.program_id ?? '')
    setSegmentId(c.segment_id ?? '')
    setScheduledAt(c.scheduled_send_at ? c.scheduled_send_at.slice(0, 16) : '')
    setShowCreateModal(true)
  }

  const createMut = useMutation({
    mutationFn: createCampaign,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['campaigns'] })
      showToast('Campaign created', 'success')
      setShowCreateModal(false)
      resetForm()
    },
    onError: () => showToast('Failed to create campaign', 'error'),
  })

  const updateMut = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: any }) => updateCampaign(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['campaigns'] })
      showToast('Campaign updated', 'success')
      setShowCreateModal(false)
      resetForm()
    },
    onError: () => showToast('Failed to update campaign', 'error'),
  })

  const deleteMut = useMutation({
    mutationFn: deleteCampaign,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['campaigns'] })
      showToast('Campaign deleted', 'success')
      setDeleteTarget(null)
    },
    onError: () => showToast('Failed to delete campaign', 'error'),
  })

  const sendMut = useMutation({
    mutationFn: sendCampaign,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['campaigns'] })
      showToast('Campaign sent!', 'success')
    },
    onError: () => showToast('Failed to send campaign', 'error'),
  })

  const handleSubmit = () => {
    if (!campaignName.trim()) { showToast('Name is required', 'warning'); return }
    const payload = {
      campaign_name: campaignName,
      campaign_type: campaignType,
      message_subject: subject || undefined,
      message_body: body || undefined,
      program_id: programId || null,
      segment_id: segmentId || null,
      scheduled_send_at: scheduledAt ? new Date(scheduledAt).toISOString() : null,
    }

    if (editTarget) {
      updateMut.mutate({ id: editTarget.id, payload })
    } else {
      createMut.mutate(payload)
    }
  }

  return (
    <div className="p-6 space-y-4">
      <InstitutionPageHeader
        title="Outreach Campaigns"
        description="Plan and monitor student outreach from draft to delivery."
        actions={(
          <Button onClick={openCreate} className="flex items-center gap-2">
            <Plus size={16} /> New Campaign
          </Button>
        )}
      />

      <Card className="p-3">
        <p className="text-xs text-gray-500">Operational cue</p>
        <p className="text-sm text-gray-700">
          Draft campaigns should be attached to a segment before sending so outcomes can be compared by audience.
        </p>
      </Card>

      {campaigns.length > 0 && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <Card className="p-3">
            <p className="text-xs text-gray-500">Total</p>
            <p className="text-xl font-semibold text-gray-900">{campaigns.length}</p>
          </Card>
          <Card className="p-3">
            <p className="text-xs text-gray-500">Draft</p>
            <p className="text-xl font-semibold text-gray-900">{campaigns.filter(c => (c.status ?? 'draft') === 'draft').length}</p>
          </Card>
          <Card className="p-3">
            <p className="text-xs text-gray-500">Scheduled</p>
            <p className="text-xl font-semibold text-gray-900">{campaigns.filter(c => c.status === 'scheduled').length}</p>
          </Card>
          <Card className="p-3">
            <p className="text-xs text-gray-500">Sent</p>
            <p className="text-xl font-semibold text-gray-900">{campaigns.filter(c => c.status === 'sent').length}</p>
          </Card>
        </div>
      )}

      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

      {campaignsQ.isLoading ? (
        <div className="grid grid-cols-2 gap-4">{Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-40" />)}</div>
      ) : campaigns.length === 0 ? (
        <EmptyState
          icon={<Megaphone size={40} />}
          title="No campaigns"
          description="Create targeted outreach campaigns to engage prospective students."
          action={{ label: 'New Campaign', onClick: openCreate }}
        />
      ) : (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
          {campaigns.map(c => {
            const prog = programs.find(p => p.id === c.program_id)
            const seg = segments.find(s => s.id === c.segment_id)
            return (
              <Card key={c.id} className="p-4">
                <div className="flex items-start justify-between mb-2">
                  <h3 className="font-semibold text-gray-900">{c.campaign_name}</h3>
                  <Badge variant={STATUS_BADGE[c.status ?? 'draft'] ?? 'neutral'}>{c.status ?? 'draft'}</Badge>
                </div>
                <Badge variant="info" className="mb-3">{c.campaign_type ?? 'email'}</Badge>
                <div className="space-y-1 text-sm text-gray-600">
                  {c.message_subject && <p className="truncate">Subject: {c.message_subject}</p>}
                  {prog && <p className="text-xs text-gray-400">Program: {prog.program_name}</p>}
                  {seg && <p className="text-xs text-gray-400">Segment: {seg.segment_name}</p>}
                  {c.scheduled_send_at && (
                    <div className="flex items-center gap-1 text-xs text-gray-400">
                      <Clock size={12} /> Scheduled: {formatDateTime(c.scheduled_send_at)}
                    </div>
                  )}
                  {c.sent_at && (
                    <p className="text-xs text-gray-400">Sent: {formatDateTime(c.sent_at)}</p>
                  )}
                  <p className="text-xs text-gray-400">Created {formatDate(c.created_at)}</p>
                </div>
                <div className="flex gap-2 mt-3">
                  {c.status !== 'sent' && (
                    <>
                      <Button variant="ghost" size="sm" onClick={() => openEdit(c)} className="flex items-center gap-1">
                        <Edit2 size={14} /> Edit
                      </Button>
                      <Button variant="ghost" size="sm" onClick={() => sendMut.mutate(c.id)} disabled={sendMut.isPending}
                        className="flex items-center gap-1 text-green-600">
                        <Send size={14} /> Send
                      </Button>
                    </>
                  )}
                  {c.status === 'sent' && (
                    <Button variant="ghost" size="sm" onClick={() => { setMetricsTarget(c.id); setShowMetricsModal(true) }}
                      className="flex items-center gap-1">
                      <BarChart3 size={14} /> Metrics
                    </Button>
                  )}
                  {c.status !== 'sent' && (
                    <Button variant="ghost" size="sm" onClick={() => setDeleteTarget(c)}
                      className="flex items-center gap-1 text-red-600">
                      <Trash2 size={14} /> Delete
                    </Button>
                  )}
                </div>
              </Card>
            )
          })}
        </div>
      )}

      {/* Create/Edit Modal */}
      <Modal isOpen={showCreateModal} onClose={() => { setShowCreateModal(false); resetForm() }} title={editTarget ? 'Edit Campaign' : 'New Campaign'}>
        <div className="space-y-4">
          <Input label="Campaign Name *" value={campaignName} onChange={e => setCampaignName(e.target.value)} />
          <Select label="Type" options={CAMPAIGN_TYPES} value={campaignType} onChange={e => setCampaignType(e.target.value)} />
          <Input label="Subject" value={subject} onChange={e => setSubject(e.target.value)} placeholder="Message subject" />
          <Textarea label="Message Body" value={body} onChange={e => setBody(e.target.value)} rows={4} placeholder="Write your outreach message..." />
          <Select label="Program" options={programOptions} value={programId} onChange={e => setProgramId(e.target.value)} />
          <Select label="Segment" options={segmentOptions} value={segmentId} onChange={e => setSegmentId(e.target.value)} />
          <Input label="Schedule Send" type="datetime-local" value={scheduledAt} onChange={e => setScheduledAt(e.target.value)} />
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => { setShowCreateModal(false); resetForm() }}>Cancel</Button>
            <Button onClick={handleSubmit} disabled={createMut.isPending || updateMut.isPending}>
              {(createMut.isPending || updateMut.isPending) ? 'Saving...' : 'Save'}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Delete Confirmation */}
      <Modal isOpen={!!deleteTarget} onClose={() => setDeleteTarget(null)} title="Delete Campaign">
        <p className="text-sm text-gray-600 mb-4">
          Are you sure you want to delete <strong>{deleteTarget?.campaign_name}</strong>? This action cannot be undone.
        </p>
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={() => setDeleteTarget(null)}>Cancel</Button>
          <Button
            variant="danger"
            onClick={() => deleteTarget && deleteMut.mutate(deleteTarget.id)}
            disabled={deleteMut.isPending}
          >
            {deleteMut.isPending ? 'Deleting...' : 'Delete'}
          </Button>
        </div>
      </Modal>

      {/* Metrics Modal */}
      <Modal isOpen={showMetricsModal} onClose={() => { setShowMetricsModal(false); setMetricsTarget(null) }} title="Campaign Metrics">
        {metricsQ.isLoading ? (
          <div className="space-y-3">{Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-8" />)}</div>
        ) : !metrics ? (
          <p className="text-sm text-gray-500 text-center py-4">No metrics available.</p>
        ) : (
          <div className="space-y-4">
            <div className="text-center mb-4">
              <p className="text-3xl font-bold text-gray-900">{metrics.total_recipients}</p>
              <p className="text-sm text-gray-500">Total Recipients</p>
            </div>
            {[
              { label: 'Delivered', value: metrics.delivered, color: 'bg-blue-500' },
              { label: 'Opened', value: metrics.opened, color: 'bg-green-500' },
              { label: 'Clicked', value: metrics.clicked, color: 'bg-amber-500' },
              { label: 'Responded', value: metrics.responded, color: 'bg-purple-500' },
            ].map(m => (
              <div key={m.label}>
                <div className="flex items-center justify-between text-sm mb-1">
                  <span className="text-gray-700">{m.label}</span>
                  <span className="font-medium text-gray-900">
                    {m.value} {metrics.total_recipients > 0 && `(${Math.round(m.value / metrics.total_recipients * 100)}%)`}
                  </span>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-2">
                  <div
                    className={`${m.color} rounded-full h-2 transition-all`}
                    style={{ width: metrics.total_recipients > 0 ? `${(m.value / metrics.total_recipients) * 100}%` : '0%' }}
                  />
                </div>
              </div>
            ))}
          </div>
        )}
      </Modal>
    </div>
  )
}
