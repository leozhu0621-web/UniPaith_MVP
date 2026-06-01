import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Megaphone, Plus, Send, Edit2, Trash2, BarChart3, Clock, Users, Link2, Copy,
  ExternalLink, Sparkles, Pause, FileText, LayoutTemplate,
} from 'lucide-react'
import {
  getCampaigns, createCampaign, updateCampaign, deleteCampaign, sendCampaign,
  getCampaignMetrics, getSegments, getInstitutionPrograms, previewCampaignAudience,
  previewSegmentAudience, getCampaignLinks, createCampaignLink, deleteCampaignLink,
  getCampaignAttribution, getTemplates, draftCampaignCopy, getInstitution,
} from '../../api/institutions'
import type { CampaignAudiencePreview } from '../../api/institutions'
import {
  CAMPAIGN_OBJECTIVES, CAMPAIGN_CHANNELS, DESTINATION_TYPES, CTA_TYPES,
  STATUS_BADGE, statusLabel, channelLabel, LIST_TABS, PERSONALIZATION_VARS,
} from './campaigns/campaignConstants'
import { draftCampaignCopy as localDraftCampaignCopy } from './campaigns/draftCampaignCopy'
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
import type {
  Campaign, CampaignAttributionDetail, CampaignLink, CampaignMetrics,
  CommunicationTemplate, Segment, Program, Institution,
} from '../../types'

export default function CampaignsPage({ embedded = false }: { embedded?: boolean }) {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState('all')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showTemplateModal, setShowTemplateModal] = useState(false)
  const [showMetricsModal, setShowMetricsModal] = useState(false)
  const [editTarget, setEditTarget] = useState<Campaign | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<Campaign | null>(null)
  const [metricsTarget, setMetricsTarget] = useState<string | null>(null)
  const [sendTarget, setSendTarget] = useState<Campaign | null>(null)
  const [sendPreview, setSendPreview] = useState<CampaignAudiencePreview | null>(null)
  const [audienceLoading, setAudienceLoading] = useState(false)
  const [linksTarget, setLinksTarget] = useState<string | null>(null)
  const [showLinksModal, setShowLinksModal] = useState(false)
  const [showAttribution, setShowAttribution] = useState(false)
  const [newLinkDest, setNewLinkDest] = useState('program')
  const [newLinkDestId, setNewLinkDestId] = useState('')
  const [newLinkLabel, setNewLinkLabel] = useState('')
  const [newLinkCustomUrl, setNewLinkCustomUrl] = useState('')
  const [drafting, setDrafting] = useState(false)
  const [editorAudienceCount, setEditorAudienceCount] = useState<number | null>(null)
  const [editorAudienceLoading, setEditorAudienceLoading] = useState(false)

  const [campaignName, setCampaignName] = useState('')
  const [campaignType, setCampaignType] = useState('in_app')
  const [objective, setObjective] = useState('general')
  const [ctaType, setCtaType] = useState('learn_more')
  const [subject, setSubject] = useState('')
  const [body, setBody] = useState('')
  const [programId, setProgramId] = useState('')
  const [segmentId, setSegmentId] = useState('')
  const [scheduledAt, setScheduledAt] = useState('')

  const statusFilter = activeTab === 'all' ? undefined : activeTab
  const campaignsQ = useQuery({
    queryKey: ['campaigns', statusFilter],
    queryFn: () => getCampaigns(statusFilter),
  })
  const campaigns: Campaign[] = Array.isArray(campaignsQ.data) ? campaignsQ.data : []

  const institutionQ = useQuery({ queryKey: ['institution-me'], queryFn: getInstitution })
  const institution: Institution | undefined = institutionQ.data

  const programsQ = useQuery({ queryKey: ['institution-programs'], queryFn: getInstitutionPrograms })
  const programs: Program[] = Array.isArray(programsQ.data) ? programsQ.data : []

  const segmentsQ = useQuery({ queryKey: ['segments'], queryFn: getSegments })
  const segments: Segment[] = Array.isArray(segmentsQ.data) ? segmentsQ.data : []

  const templatesQ = useQuery({
    queryKey: ['communication-templates'],
    queryFn: () => getTemplates(),
    enabled: showTemplateModal,
  })
  const templates: CommunicationTemplate[] = Array.isArray(templatesQ.data) ? templatesQ.data : []

  const metricsQ = useQuery({
    queryKey: ['campaign-metrics', metricsTarget],
    queryFn: () => getCampaignMetrics(metricsTarget!),
    enabled: !!metricsTarget && showMetricsModal,
  })
  const metrics: CampaignMetrics | undefined = metricsQ.data

  const linksQ = useQuery({
    queryKey: ['campaign-links', linksTarget],
    queryFn: () => getCampaignLinks(linksTarget!),
    enabled: !!linksTarget && showLinksModal,
  })
  const links: CampaignLink[] = Array.isArray(linksQ.data) ? linksQ.data : []

  const attributionQ = useQuery({
    queryKey: ['campaign-attribution', linksTarget],
    queryFn: () => getCampaignAttribution(linksTarget!),
    enabled: !!linksTarget && showAttribution,
  })
  const attribution: CampaignAttributionDetail | undefined = attributionQ.data

  useEffect(() => {
    if (!showCreateModal) return
    let cancelled = false
    const loadAudience = async () => {
      setEditorAudienceLoading(true)
      try {
        if (editTarget?.id) {
          const preview = await previewCampaignAudience(editTarget.id)
          if (!cancelled) setEditorAudienceCount(preview.audience_count)
        } else if (segmentId) {
          const preview = await previewSegmentAudience(segmentId)
          if (!cancelled) setEditorAudienceCount(preview.audience_count)
        } else {
          if (!cancelled) setEditorAudienceCount(null)
        }
      } catch {
        if (!cancelled) setEditorAudienceCount(0)
      } finally {
        if (!cancelled) setEditorAudienceLoading(false)
      }
    }
    void loadAudience()
    return () => { cancelled = true }
  }, [showCreateModal, editTarget?.id, segmentId])

  const createLinkMut = useMutation({
    mutationFn: (p: { campaignId: string; payload: { destination_type: string; destination_id?: string; custom_url?: string; label?: string } }) =>
      createCampaignLink(p.campaignId, p.payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['campaign-links'] })
      showToast('Link created', 'success')
      setNewLinkLabel('')
      setNewLinkDestId('')
      setNewLinkCustomUrl('')
    },
  })

  const deleteLinkMut = useMutation({
    mutationFn: (p: { campaignId: string; linkId: string }) => deleteCampaignLink(p.campaignId, p.linkId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['campaign-links'] })
      showToast('Link deleted', 'success')
    },
  })

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
    mutationFn: ({ id, payload }: { id: string; payload: Parameters<typeof updateCampaign>[1] }) =>
      updateCampaign(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['campaigns'] })
      showToast('Campaign updated', 'success')
      setShowCreateModal(false)
      resetForm()
    },
    onError: () => showToast('Failed to update campaign', 'error'),
  })

  const pauseMut = useMutation({
    mutationFn: (id: string) => updateCampaign(id, { status: 'paused' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['campaigns'] })
      showToast('Campaign paused', 'success')
    },
    onError: () => showToast('Failed to pause campaign', 'error'),
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
      showToast('Campaign sent', 'success')
      setSendTarget(null)
      setSendPreview(null)
    },
    onError: () => showToast('Failed to send campaign', 'error'),
  })

  const channelOptions = CAMPAIGN_CHANNELS.map(c => ({ value: c.value, label: c.label }))
  const objectiveOptions = CAMPAIGN_OBJECTIVES.map(o => ({ value: o.value, label: o.label }))
  const ctaOptions = CTA_TYPES.map(c => ({ value: c.value, label: c.label }))
  const programOptions = [{ value: '', label: 'None' }, ...programs.map(p => ({ value: p.id, label: p.program_name }))]
  const segmentOptions = [{ value: '', label: 'None' }, ...segments.map(s => ({ value: s.id, label: s.segment_name }))]
  const linkDestOptions = DESTINATION_TYPES.map(d => ({ value: d.value, label: d.label }))

  const resetForm = () => {
    setCampaignName('')
    setCampaignType('in_app')
    setObjective('general')
    setCtaType('learn_more')
    setSubject('')
    setBody('')
    setProgramId('')
    setSegmentId('')
    setScheduledAt('')
    setEditTarget(null)
    setEditorAudienceCount(null)
  }

  const openCreate = () => { resetForm(); setShowCreateModal(true) }

  const openEdit = (c: Campaign) => {
    setEditTarget(c)
    setCampaignName(c.campaign_name)
    setCampaignType(c.campaign_type ?? 'in_app')
    setObjective('general')
    setCtaType('learn_more')
    setSubject(c.message_subject ?? '')
    setBody(c.message_body ?? '')
    setProgramId(c.program_id ?? '')
    setSegmentId(c.segment_id ?? '')
    setScheduledAt(c.scheduled_send_at ? c.scheduled_send_at.slice(0, 16) : '')
    setShowCreateModal(true)
  }

  const applyTemplate = (tpl: CommunicationTemplate) => {
    setSubject(tpl.subject)
    setBody(tpl.body)
    if (tpl.program_id) setProgramId(tpl.program_id)
    setShowTemplateModal(false)
    setShowCreateModal(true)
    showToast(`Applied template "${tpl.name}"`, 'success')
  }

  const handleDraftWithAI = async () => {
    setDrafting(true)
    const prog = programs.find(p => p.id === programId)
    try {
      const result = await draftCampaignCopy({
        objective,
        cta_type: ctaType,
        campaign_name: campaignName || undefined,
        program_name: prog?.program_name,
      })
      setSubject(result.subject)
      setBody(result.body)
      showToast('Draft generated', 'success')
    } catch {
      const fallback = localDraftCampaignCopy({
        objective,
        ctaType,
        campaignName: campaignName || 'Outreach update',
        institutionName: institution?.name,
        programName: prog?.program_name,
      })
      setSubject(fallback.subject)
      setBody(fallback.body)
      showToast('Draft generated (offline)', 'success')
    } finally {
      setDrafting(false)
    }
  }

  const openSendConfirm = async (c: Campaign) => {
    setSendTarget(c)
    setSendPreview(null)
    setAudienceLoading(true)
    try {
      const preview = await previewCampaignAudience(c.id)
      setSendPreview(preview)
    } catch {
      setSendPreview({ campaign_id: c.id, audience_count: 0, sample: [] })
    } finally {
      setAudienceLoading(false)
    }
  }

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

  const handleCreateLink = () => {
    if (!linksTarget) return
    const payload: { destination_type: string; destination_id?: string; custom_url?: string; label?: string } = {
      destination_type: newLinkDest,
      label: newLinkLabel || undefined,
    }
    if (newLinkDest === 'custom') {
      if (!newLinkCustomUrl.trim()) { showToast('URL is required', 'warning'); return }
      payload.custom_url = newLinkCustomUrl
    } else if (newLinkDestId) {
      payload.destination_id = newLinkDestId
    }
    createLinkMut.mutate({ campaignId: linksTarget, payload })
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    showToast('Copied to clipboard', 'success')
  }

  const isTerminal = (status: string | null | undefined) => status === 'sent'
  const canMutate = (status: string | null | undefined) => !isTerminal(status)
  const canSend = (status: string | null | undefined) =>
    status === 'draft' || status === 'scheduled'

  const audienceCount = sendPreview?.audience_count ?? 0
  const selectedChannel = CAMPAIGN_CHANNELS.find(c => c.value === campaignType)

  const headerActions = (
    <div className="flex flex-wrap items-center gap-2">
      <Button
        variant="tertiary"
        onClick={() => { resetForm(); setShowTemplateModal(true) }}
        className="flex items-center gap-2"
      >
        <LayoutTemplate size={16} /> Start from template
      </Button>
      <Button variant="secondary" onClick={openCreate} className="flex items-center gap-2">
        <Plus size={16} /> New Campaign
      </Button>
    </div>
  )

  const content = (
    <div className="space-y-4">
      {embedded ? (
        <div className="flex flex-wrap items-center justify-between gap-3">
          <p className="text-sm text-muted-foreground">Plan and monitor student outreach from draft to delivery.</p>
          {headerActions}
        </div>
      ) : (
        <InstitutionPageHeader
          title="Outreach Campaigns"
          description="Plan and monitor student outreach from draft to delivery."
          actions={headerActions}
        />
      )}

      {campaigns.length > 0 && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <Card className="p-3 border border-border">
            <p className="text-xs text-muted-foreground">Total</p>
            <p className="text-xl font-semibold text-foreground">{campaigns.length}</p>
          </Card>
          <Card className="p-3 border border-border">
            <p className="text-xs text-muted-foreground">Draft</p>
            <p className="text-xl font-semibold text-foreground">
              {campaigns.filter(c => (c.status ?? 'draft') === 'draft').length}
            </p>
          </Card>
          <Card className="p-3 border border-border">
            <p className="text-xs text-muted-foreground">Scheduled</p>
            <p className="text-xl font-semibold text-foreground">
              {campaigns.filter(c => c.status === 'scheduled').length}
            </p>
          </Card>
          <Card className="p-3 border border-border">
            <p className="text-xs text-muted-foreground">Completed</p>
            <p className="text-xl font-semibold text-foreground">
              {campaigns.filter(c => c.status === 'sent').length}
            </p>
          </Card>
        </div>
      )}

      <Tabs tabs={[...LIST_TABS]} activeTab={activeTab} onChange={setActiveTab} />

      {campaignsQ.isLoading ? (
        <div className="grid grid-cols-2 gap-4">
          {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-40" />)}
        </div>
      ) : campaigns.length === 0 ? (
        <EmptyState
          icon={<Megaphone size={40} />}
          title="No campaigns yet"
          description="Plan your first outreach."
          action={{ label: 'New Campaign', onClick: openCreate }}
        />
      ) : (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
          {campaigns.map(c => {
            const prog = programs.find(p => p.id === c.program_id)
            const seg = segments.find(s => s.id === c.segment_id)
            const status = c.status ?? 'draft'
            return (
              <Card key={c.id} className="p-4 border border-border">
                <div className="flex items-start justify-between mb-2 gap-2">
                  <h3 className="font-semibold text-foreground">{c.campaign_name}</h3>
                  <Badge variant={STATUS_BADGE[status] ?? 'neutral'}>{statusLabel(status)}</Badge>
                </div>
                <div className="flex flex-wrap items-center gap-2 mb-3">
                  <Badge variant="info">{channelLabel(c.campaign_type)}</Badge>
                  {seg && <Badge variant="neutral">{seg.segment_name}</Badge>}
                  {status === 'paused' && <Badge variant="warning">Paused</Badge>}
                </div>
                <div className="space-y-1 text-sm text-muted-foreground">
                  {c.message_subject && <p className="truncate">Subject: {c.message_subject}</p>}
                  {prog && <p className="text-xs">Program: {prog.program_name}</p>}
                  {seg && <p className="text-xs">Segment: {seg.segment_name}</p>}
                  {c.scheduled_send_at && (
                    <div className="flex items-center gap-1 text-xs">
                      <Clock size={12} /> Scheduled: {formatDateTime(c.scheduled_send_at)}
                    </div>
                  )}
                  {c.sent_at && <p className="text-xs">Completed: {formatDateTime(c.sent_at)}</p>}
                  <p className="text-xs">Created {formatDate(c.created_at)}</p>
                </div>
                <div className="flex flex-wrap gap-2 mt-3">
                  {canMutate(status) && (
                    <Button variant="ghost" size="sm" onClick={() => openEdit(c)} className="flex items-center gap-1">
                      <Edit2 size={14} /> Edit
                    </Button>
                  )}
                  {canSend(status) && (
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => openSendConfirm(c)}
                      className="flex items-center gap-1"
                    >
                      <Send size={14} /> Send
                    </Button>
                  )}
                  {status === 'scheduled' && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => pauseMut.mutate(c.id)}
                      disabled={pauseMut.isPending}
                      className="flex items-center gap-1 text-success"
                    >
                      <Pause size={14} /> Pause
                    </Button>
                  )}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => { setLinksTarget(c.id); setShowLinksModal(true) }}
                    className="flex items-center gap-1"
                  >
                    <Link2 size={14} /> Links
                  </Button>
                  {isTerminal(status) && (
                    <>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => { setMetricsTarget(c.id); setShowMetricsModal(true) }}
                        className="flex items-center gap-1"
                      >
                        <BarChart3 size={14} /> Metrics
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => { setLinksTarget(c.id); setShowAttribution(true) }}
                        className="flex items-center gap-1"
                      >
                        <ExternalLink size={14} /> Attribution
                      </Button>
                    </>
                  )}
                  {canMutate(status) && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setDeleteTarget(c)}
                      className="flex items-center gap-1 text-destructive"
                    >
                      <Trash2 size={14} /> Delete
                    </Button>
                  )}
                </div>
              </Card>
            )
          })}
        </div>
      )}

      <Modal
        isOpen={showCreateModal}
        onClose={() => { setShowCreateModal(false); resetForm() }}
        title={editTarget ? 'Edit Campaign' : 'New Campaign'}
      >
        <div className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <Button
              variant="tertiary"
              size="sm"
              onClick={() => { setShowCreateModal(false); setShowTemplateModal(true) }}
              className="flex items-center gap-1"
            >
              <LayoutTemplate size={14} /> Start from template
            </Button>
            <Button
              variant="tertiary"
              size="sm"
              onClick={handleDraftWithAI}
              disabled={drafting}
              loading={drafting}
              className="flex items-center gap-1"
            >
              <Sparkles size={14} /> Draft with AI
            </Button>
          </div>

          <Input label="Campaign Name *" value={campaignName} onChange={e => setCampaignName(e.target.value)} />

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <Select label="Objective" options={objectiveOptions} value={objective} onChange={e => setObjective(e.target.value)} />
            <Select label="CTA type" options={ctaOptions} value={ctaType} onChange={e => setCtaType(e.target.value)} />
          </div>

          <Select label="Channel" options={channelOptions} value={campaignType} onChange={e => setCampaignType(e.target.value)} />
          {selectedChannel && (
            <p className="text-xs text-muted-foreground -mt-2">{selectedChannel.hint}</p>
          )}

          {(campaignType === 'email' || campaignType === 'both') && (
            <Input label="Subject" value={subject} onChange={e => setSubject(e.target.value)} placeholder="Message subject" />
          )}
          <Textarea
            label="Message Body"
            value={body}
            onChange={e => setBody(e.target.value)}
            rows={5}
            placeholder="Write your outreach message..."
          />

          {(campaignType === 'email' || campaignType === 'both') && (
            <div className="rounded-lg border border-border px-3 py-2">
              <p className="text-xs font-medium text-foreground mb-1">Personalization variables</p>
              <p className="text-xs text-muted-foreground">
                Use in subject or body: {PERSONALIZATION_VARS.join(', ')}
              </p>
              <p className="text-xs text-muted-foreground mt-1">Unsubscribe link is added automatically to external email.</p>
            </div>
          )}

          <Select label="Program" options={programOptions} value={programId} onChange={e => setProgramId(e.target.value)} />
          <Select label="Segment" options={segmentOptions} value={segmentId} onChange={e => setSegmentId(e.target.value)} />

          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center gap-1.5 rounded-full border border-border bg-muted px-3 py-1 text-xs font-medium text-foreground">
              <Users size={12} className="text-muted-foreground" />
              {editorAudienceLoading ? (
                'Calculating audience…'
              ) : editorAudienceCount === null ? (
                'Select a segment to preview audience'
              ) : (
                `${editorAudienceCount} recipient${editorAudienceCount === 1 ? '' : 's'} after filtering`
              )}
            </span>
            {editorAudienceCount === 0 && !editorAudienceLoading && segmentId && (
              <span className="text-xs text-muted-foreground">
                0 recipients after filtering. Adjust your audience.
              </span>
            )}
          </div>

          <Input label="Schedule send" type="datetime-local" value={scheduledAt} onChange={e => setScheduledAt(e.target.value)} />

          <div className="flex justify-end gap-2 pt-1">
            <Button variant="ghost" onClick={() => { setShowCreateModal(false); resetForm() }}>Cancel</Button>
            <Button variant="secondary" onClick={handleSubmit} disabled={createMut.isPending || updateMut.isPending}>
              {(createMut.isPending || updateMut.isPending) ? 'Saving…' : scheduledAt ? 'Schedule' : 'Save draft'}
            </Button>
          </div>
        </div>
      </Modal>

      <Modal isOpen={showTemplateModal} onClose={() => setShowTemplateModal(false)} title="Start from template">
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Pick a saved template to pre-fill subject and body, or manage templates on the templates page.
          </p>
          <Link
            to="/i/templates"
            className="inline-flex items-center gap-1 text-sm text-secondary underline-offset-4 hover:underline"
            onClick={() => setShowTemplateModal(false)}
          >
            <FileText size={14} /> Open template library
          </Link>
          {templatesQ.isLoading ? (
            <Skeleton className="h-24" />
          ) : templates.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-6">
              No templates yet.{' '}
              <Link to="/i/templates" className="text-secondary underline-offset-4 hover:underline" onClick={() => setShowTemplateModal(false)}>
                Create one in Templates
              </Link>
            </p>
          ) : (
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {templates.filter(t => t.is_active).map(tpl => (
                <button
                  key={tpl.id}
                  type="button"
                  onClick={() => applyTemplate(tpl)}
                  className="w-full text-left rounded-lg border border-border p-3 hover:bg-muted transition-colors"
                >
                  <p className="text-sm font-medium text-foreground">{tpl.name}</p>
                  <p className="text-xs text-muted-foreground truncate mt-0.5">{tpl.subject}</p>
                  {tpl.program_name && <p className="text-xs text-muted-foreground mt-1">{tpl.program_name}</p>}
                </button>
              ))}
            </div>
          )}
        </div>
      </Modal>

      <Modal isOpen={!!deleteTarget} onClose={() => setDeleteTarget(null)} title="Delete Campaign">
        <p className="text-sm text-muted-foreground mb-4">
          Are you sure you want to delete <strong className="text-foreground">{deleteTarget?.campaign_name}</strong>? This cannot be undone.
        </p>
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={() => setDeleteTarget(null)}>Cancel</Button>
          <Button variant="destructive" onClick={() => deleteTarget && deleteMut.mutate(deleteTarget.id)} disabled={deleteMut.isPending}>
            {deleteMut.isPending ? 'Deleting…' : 'Delete'}
          </Button>
        </div>
      </Modal>

      <Modal isOpen={showMetricsModal} onClose={() => { setShowMetricsModal(false); setMetricsTarget(null) }} title="Campaign Metrics">
        {metricsQ.isLoading ? (
          <div className="space-y-3">{Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-8" />)}</div>
        ) : !metrics ? (
          <p className="text-sm text-muted-foreground text-center py-4">No metrics available.</p>
        ) : (
          <div className="space-y-4">
            <div className="text-center mb-4">
              <p className="text-3xl font-bold text-foreground">{metrics.total_recipients}</p>
              <p className="text-sm text-muted-foreground">Total recipients</p>
            </div>
            {[
              { label: 'Delivered', value: metrics.delivered, bar: 'bg-cobalt' },
              { label: 'Opened', value: metrics.opened, bar: 'bg-secondary' },
              { label: 'Clicked', value: metrics.clicked, bar: 'bg-primary' },
              { label: 'Responded', value: metrics.responded, bar: 'bg-success' },
            ].map(m => (
              <div key={m.label}>
                <div className="flex items-center justify-between text-sm mb-1">
                  <span className="text-foreground">{m.label}</span>
                  <span className="font-medium text-foreground">
                    {m.value}
                    {metrics.total_recipients > 0 && ` (${Math.round(m.value / metrics.total_recipients * 100)}%)`}
                  </span>
                </div>
                <div className="w-full bg-muted rounded-full h-2">
                  <div
                    className={`${m.bar} rounded-full h-2 transition-all`}
                    style={{ width: metrics.total_recipients > 0 ? `${(m.value / metrics.total_recipients) * 100}%` : '0%' }}
                  />
                </div>
              </div>
            ))}
          </div>
        )}
      </Modal>

      <Modal isOpen={showLinksModal} onClose={() => { setShowLinksModal(false); setLinksTarget(null) }} title="Trackable Links">
        <div className="space-y-4">
          <div className="border border-border rounded-lg p-3 space-y-3">
            <p className="text-sm font-medium text-foreground">Generate new link</p>
            <div className="grid grid-cols-2 gap-2">
              <Select label="Destination" options={linkDestOptions} value={newLinkDest} onChange={e => setNewLinkDest(e.target.value)} />
              {newLinkDest === 'custom' ? (
                <Input label="URL" value={newLinkCustomUrl} onChange={e => setNewLinkCustomUrl(e.target.value)} placeholder="https://…" />
              ) : (
                <Select
                  label="Target"
                  options={[{ value: '', label: 'Select…' }, ...programs.map(p => ({ value: p.id, label: p.program_name }))]}
                  value={newLinkDestId}
                  onChange={e => setNewLinkDestId(e.target.value)}
                />
              )}
            </div>
            <Input label="Label (optional)" value={newLinkLabel} onChange={e => setNewLinkLabel(e.target.value)} placeholder="e.g. CTA button" />
            <Button size="sm" variant="secondary" onClick={handleCreateLink} disabled={createLinkMut.isPending}>
              {createLinkMut.isPending ? 'Creating…' : 'Generate link'}
            </Button>
          </div>

          {linksQ.isLoading ? (
            <Skeleton className="h-20" />
          ) : links.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-4">No trackable links yet.</p>
          ) : (
            <div className="space-y-2">
              {links.map(lnk => (
                <div key={lnk.id} className="border border-border rounded-lg p-3 flex items-center justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-foreground truncate">
                        {lnk.label || lnk.destination_name || lnk.destination_type}
                      </span>
                      <Badge variant="neutral">{lnk.destination_type}</Badge>
                    </div>
                    <p className="text-xs text-muted-foreground truncate mt-1">{lnk.trackable_url}</p>
                    <p className="text-xs text-muted-foreground mt-1">{lnk.click_count} clicks</p>
                  </div>
                  <div className="flex items-center gap-1 shrink-0">
                    <Button variant="ghost" size="sm" onClick={() => lnk.trackable_url && copyToClipboard(lnk.trackable_url)}>
                      <Copy size={14} />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => linksTarget && deleteLinkMut.mutate({ campaignId: linksTarget, linkId: lnk.id })}
                      className="text-destructive"
                    >
                      <Trash2 size={14} />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </Modal>

      <Modal isOpen={showAttribution} onClose={() => { setShowAttribution(false); setLinksTarget(null) }} title="Campaign Attribution">
        {attributionQ.isLoading ? (
          <div className="space-y-3">{Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-8" />)}</div>
        ) : !attribution ? (
          <p className="text-sm text-muted-foreground text-center py-4">No attribution data available.</p>
        ) : (
          <div className="space-y-5">
            <div className="text-center">
              <p className="text-sm text-muted-foreground">{attribution.campaign_name}</p>
            </div>
            <div className="space-y-2">
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Engagement funnel</p>
              {[
                { label: 'Recipients', value: attribution.recipients },
                { label: 'Delivered', value: attribution.delivered },
                { label: 'Opened', value: attribution.opened },
                { label: 'Clicked', value: attribution.clicked },
              ].map(s => (
                <div key={s.label} className="flex items-center justify-between text-sm">
                  <span className="text-foreground">{s.label}</span>
                  <span className="font-medium text-foreground">
                    {s.value}
                    {attribution.recipients > 0 && (
                      <span className="text-muted-foreground text-xs ml-1">
                        ({Math.round(s.value / attribution.recipients * 100)}%)
                      </span>
                    )}
                  </span>
                </div>
              ))}
            </div>
            <div className="space-y-2">
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Downstream actions</p>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { label: 'Views', value: attribution.views },
                  { label: 'Saves', value: attribution.saves },
                  { label: 'RSVPs', value: attribution.rsvps },
                  { label: 'Info requests', value: attribution.request_infos },
                  { label: 'Applications', value: attribution.applications },
                ].map(a => (
                  <div key={a.label} className="bg-muted rounded-lg p-2 text-center border border-border">
                    <p className="text-lg font-bold text-foreground">{a.value}</p>
                    <p className="text-xs text-muted-foreground">{a.label}</p>
                  </div>
                ))}
              </div>
            </div>
            {attribution.links.length > 0 && (
              <div className="space-y-2">
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Per-link breakdown</p>
                <div className="border border-border rounded-lg overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-muted">
                      <tr>
                        <th className="text-left px-3 py-2 font-medium text-muted-foreground">Link</th>
                        <th className="text-right px-3 py-2 font-medium text-muted-foreground">Clicks</th>
                        <th className="text-right px-3 py-2 font-medium text-muted-foreground">Views</th>
                        <th className="text-right px-3 py-2 font-medium text-muted-foreground">Saves</th>
                        <th className="text-right px-3 py-2 font-medium text-muted-foreground">Apps</th>
                      </tr>
                    </thead>
                    <tbody>
                      {attribution.links.map(l => (
                        <tr key={l.link_id} className="border-t border-border">
                          <td className="px-3 py-2 truncate max-w-[160px] text-foreground">{l.label || l.destination_name || '—'}</td>
                          <td className="text-right px-3 py-2 text-foreground">{l.clicks}</td>
                          <td className="text-right px-3 py-2 text-foreground">{l.views}</td>
                          <td className="text-right px-3 py-2 text-foreground">{l.saves}</td>
                          <td className="text-right px-3 py-2 text-foreground">{l.applications}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}
      </Modal>

      <Modal isOpen={!!sendTarget} onClose={() => { setSendTarget(null); setSendPreview(null) }} title="Send Campaign">
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground">
            You are about to send <strong className="text-foreground">{sendTarget?.campaign_name}</strong>.
          </p>
          {sendTarget?.segment_id && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Users size={14} />
              Segment:{' '}
              <strong className="text-foreground">
                {segments.find(s => s.id === sendTarget.segment_id)?.segment_name ?? 'Unknown'}
              </strong>
            </div>
          )}
          <div className="rounded-lg border border-border bg-muted p-4 text-center">
            {audienceLoading ? (
              <p className="text-sm text-muted-foreground animate-pulse">Calculating audience…</p>
            ) : (
              <>
                <p className="text-3xl font-bold text-foreground">{audienceCount}</p>
                <p className="text-sm text-muted-foreground">
                  {audienceCount === 1 ? 'recipient after filtering' : 'recipients after filtering'}
                </p>
              </>
            )}
          </div>
          {audienceCount === 0 && !audienceLoading && (
            <p className="text-xs text-muted-foreground">0 recipients after filtering. Adjust your audience.</p>
          )}
          {!audienceLoading && sendPreview && sendPreview.sample.length > 0 && (
            <div className="border border-border rounded-lg overflow-hidden">
              <p className="text-xs font-medium text-muted-foreground px-3 py-2 bg-muted border-b border-border">
                Sample recipients
              </p>
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left px-3 py-2 font-medium text-muted-foreground">Name</th>
                    <th className="text-left px-3 py-2 font-medium text-muted-foreground">Email</th>
                  </tr>
                </thead>
                <tbody>
                  {sendPreview.sample.map(row => (
                    <tr key={row.student_id} className="border-t border-border">
                      <td className="px-3 py-2 text-foreground">{row.first_name ?? '—'}</td>
                      <td className="px-3 py-2 text-muted-foreground truncate max-w-[200px]">{row.email ?? '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => { setSendTarget(null); setSendPreview(null) }}>Cancel</Button>
            <Button
              variant="secondary"
              onClick={() => sendTarget && sendMut.mutate(sendTarget.id)}
              disabled={sendMut.isPending || audienceLoading || audienceCount === 0}
              className="flex items-center gap-2"
            >
              <Send size={14} />
              {sendMut.isPending ? 'Sending…' : `Send to ${audienceCount} recipient${audienceCount === 1 ? '' : 's'}`}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )

  return embedded ? content : <div className="p-6">{content}</div>
}
