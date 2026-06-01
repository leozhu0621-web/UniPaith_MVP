import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Megaphone, Plus, Send, Edit2, Trash2, BarChart3, Link2, Copy, ExternalLink,
  Pause, Play, CalendarClock, Users, Upload, LayoutTemplate, CheckCircle,
} from 'lucide-react'
import {
  getCampaigns, deleteCampaign, sendCampaign, scheduleCampaign, pauseCampaign,
  resumeCampaign, completeCampaign, submitCampaignForApproval, approveCampaign,
  getCampaignMetrics, getSegments, getInstitutionPrograms, previewCampaignAudience,
  getCampaignLinks, createCampaignLink, deleteCampaignLink, getCampaignAttribution,
  getTemplates, getUploadedLists,
} from '../../api/institutions'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Modal from '../../components/ui/Modal'
import Input from '../../components/ui/Input'
import Select from '../../components/ui/Select'
import Tabs from '../../components/ui/Tabs'
import EmptyState from '../../components/ui/EmptyState'
import Skeleton from '../../components/ui/Skeleton'
import InstitutionPageHeader from '../../components/institution/InstitutionPageHeader'
import { showToast } from '../../stores/toast-store'
import { formatDateTime, formatDate } from '../../utils/format'
import type {
  AudiencePreview, Campaign, CampaignAttributionDetail, CampaignLink,
  CampaignMetrics, CampaignStatus, CommunicationTemplate, Program, Segment,
} from '../../types'
import CampaignEditorModal from './campaigns/CampaignEditorModal'
import AudienceManagerSheet from './campaigns/AudienceManagerSheet'
import {
  STATUS_BADGE, STATUS_LABELS, OBJECTIVE_LABELS, CTA_LABELS, CHANNEL_OPTIONS,
  ATTRIBUTION_LABELS,
} from './campaigns/constants'

const LIST_TABS = [
  { id: 'all', label: 'All' },
  { id: 'draft', label: 'Drafts' },
  { id: 'pending_approval', label: 'Pending' },
  { id: 'scheduled', label: 'Scheduled' },
  { id: 'active', label: 'Active' },
  { id: 'completed', label: 'Completed' },
]

function channelSummary(channels: string[]): string {
  if (!channels?.length) return '—'
  return channels
    .map(ch => CHANNEL_OPTIONS.find(c => c.value === ch)?.label ?? ch)
    .join(' + ')
}

export default function CampaignsPage({ embedded = false }: { embedded?: boolean }) {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState('all')
  const [editorOpen, setEditorOpen] = useState(false)
  const [editTarget, setEditTarget] = useState<Campaign | null>(null)
  const [audienceSheetOpen, setAudienceSheetOpen] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<Campaign | null>(null)
  const [sendTarget, setSendTarget] = useState<Campaign | null>(null)
  const [sendPreview, setSendPreview] = useState<AudiencePreview | null>(null)
  const [previewLoading, setPreviewLoading] = useState(false)
  const [metricsTarget, setMetricsTarget] = useState<Campaign | null>(null)
  const [linksTarget, setLinksTarget] = useState<string | null>(null)
  const [showLinksModal, setShowLinksModal] = useState(false)
  const [showAttribution, setShowAttribution] = useState(false)
  const [newLinkDest, setNewLinkDest] = useState('program')
  const [newLinkDestId, setNewLinkDestId] = useState('')
  const [newLinkLabel, setNewLinkLabel] = useState('')
  const [newLinkCustomUrl, setNewLinkCustomUrl] = useState('')

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
  const listsQ = useQuery({ queryKey: ['uploaded-lists'], queryFn: getUploadedLists })
  const templatesQ = useQuery({
    queryKey: ['templates', 'custom'],
    queryFn: () => getTemplates('custom'),
  })
  const templates: CommunicationTemplate[] = Array.isArray(templatesQ.data) ? templatesQ.data : []

  const metricsQ = useQuery({
    queryKey: ['campaign-metrics', metricsTarget?.id],
    queryFn: () => getCampaignMetrics(metricsTarget!.id),
    enabled: !!metricsTarget,
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

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['campaigns'] })

  const deleteMut = useMutation({
    mutationFn: deleteCampaign,
    onSuccess: () => { invalidate(); showToast('Campaign deleted', 'success'); setDeleteTarget(null) },
    onError: () => showToast('Failed to delete campaign', 'error'),
  })

  const actionMut = useMutation({
    mutationFn: async ({ id, action }: { id: string; action: string }) => {
      const map: Record<string, (x: string) => Promise<Campaign>> = {
        send: sendCampaign,
        schedule: scheduleCampaign,
        pause: pauseCampaign,
        resume: resumeCampaign,
        complete: completeCampaign,
        'submit-approval': submitCampaignForApproval,
        approve: approveCampaign,
      }
      const fn = map[action]
      if (!fn) throw new Error('Unknown action')
      return fn(id)
    },
    onSuccess: () => { invalidate(); showToast('Campaign updated', 'success'); setSendTarget(null); setSendPreview(null) },
    onError: (e: unknown) => {
      const msg = e instanceof Error ? e.message : ''
      showToast(
        msg.includes('0 recipients') ? '0 recipients after filtering. Adjust your audience.' : 'Action failed',
        'error',
      )
    },
  })

  const createLinkMut = useMutation({
    mutationFn: (p: { campaignId: string; payload: { destination_type: string; destination_id?: string; custom_url?: string; label?: string } }) =>
      createCampaignLink(p.campaignId, p.payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['campaign-links'] })
      showToast('Trackable link created', 'success')
      setNewLinkLabel(''); setNewLinkDestId(''); setNewLinkCustomUrl('')
    },
  })

  const deleteLinkMut = useMutation({
    mutationFn: (p: { campaignId: string; linkId: string }) => deleteCampaignLink(p.campaignId, p.linkId),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['campaign-links'] }); showToast('Link removed', 'success') },
  })

  const openSend = async (c: Campaign) => {
    setSendTarget(c)
    setSendPreview(null)
    setPreviewLoading(true)
    try {
      setSendPreview(await previewCampaignAudience(c.id))
    } catch {
      setSendPreview({ deduped_count: 0, sample: [], suppressed_count: 0, platform_count: 0, uploaded_count: 0, consent_excluded_count: 0 })
    } finally {
      setPreviewLoading(false)
    }
  }

  const canEdit = (s: CampaignStatus) => ['draft', 'pending_approval', 'scheduled', 'paused'].includes(s)
  const canSend = (s: CampaignStatus) => ['draft', 'scheduled', 'paused'].includes(s)
  const isExternal = (c: Campaign) => c.channels?.includes('external_email')

  const rootClass = embedded ? 'space-y-4' : 'p-6 space-y-4'

  return (
    <div className={rootClass}>
      <InstitutionPageHeader
        title="Campaigns"
        description="Plan, launch, and measure outbound outreach with trackable links and attribution."
        actions={(
          <div className="flex flex-wrap items-center gap-2">
            <Button variant="tertiary" size="sm" onClick={() => setAudienceSheetOpen(true)} className="gap-1.5">
              <Upload size={15} /> Lists & suppression
            </Button>
            <Link to="/i/templates">
              <Button variant="tertiary" size="sm" className="gap-1.5">
                <LayoutTemplate size={15} /> Templates
              </Button>
            </Link>
            <Button variant="secondary" onClick={() => { setEditTarget(null); setEditorOpen(true) }} className="gap-1.5">
              <Plus size={16} /> New campaign
            </Button>
          </div>
        )}
      />

      {campaigns.length > 0 && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {[
            { label: 'Total', value: campaigns.length },
            { label: 'Draft', value: campaigns.filter(c => c.status === 'draft').length },
            { label: 'Scheduled', value: campaigns.filter(c => c.status === 'scheduled').length },
            { label: 'Active', value: campaigns.filter(c => c.status === 'active').length },
          ].map(s => (
            <Card key={s.label} className="p-3">
              <p className="text-xs text-muted-foreground">{s.label}</p>
              <p className="text-xl font-semibold text-foreground tabular-nums">{s.value}</p>
            </Card>
          ))}
        </div>
      )}

      <Tabs tabs={LIST_TABS} activeTab={activeTab} onChange={setActiveTab} />

      {campaignsQ.isLoading ? (
        <div className="grid gap-4 md:grid-cols-2">{Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-44" />)}</div>
      ) : campaigns.length === 0 ? (
        <EmptyState
          icon={<Megaphone size={40} className="text-cobalt" />}
          title="No campaigns yet"
          description="Plan your first outreach."
          action={{ label: 'New campaign', onClick: () => { setEditTarget(null); setEditorOpen(true) } }}
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {campaigns.map(c => {
            const st = c.status
            const audienceN = c.audience?.deduped_count ?? null
            return (
              <Card key={c.id} className="p-4 border-border flex flex-col">
                <div className="flex items-start justify-between gap-2 mb-2">
                  <h3 className="font-semibold text-foreground leading-snug">{c.name}</h3>
                  <Badge variant={STATUS_BADGE[st] ?? 'neutral'}>{STATUS_LABELS[st]}</Badge>
                </div>
                <div className="flex flex-wrap gap-1.5 mb-2">
                  {c.objective && <Badge variant="neutral">{OBJECTIVE_LABELS[c.objective] ?? c.objective}</Badge>}
                  <Badge variant="info">{channelSummary(c.channels)}</Badge>
                  {audienceN != null && (
                    <Badge variant={audienceN === 0 ? 'warning' : 'info'}>
                      <Users size={11} className="inline mr-0.5" />
                      {audienceN} recipients
                    </Badge>
                  )}
                </div>
                <div className="text-sm text-muted-foreground space-y-0.5 flex-1">
                  {c.subject && <p className="truncate">Subject: {c.subject}</p>}
                  {c.cta_type && <p className="text-xs">CTA: {CTA_LABELS[c.cta_type] ?? c.cta_type}</p>}
                  {c.scheduled_at && <p className="text-xs">Scheduled {formatDateTime(c.scheduled_at)}</p>}
                  {c.sent_at && <p className="text-xs">Sent {formatDateTime(c.sent_at)}</p>}
                  <p className="text-xs">Created {formatDate(c.created_at)}</p>
                </div>
                <div className="flex flex-wrap gap-1.5 mt-3 pt-3 border-t border-border">
                  {canEdit(st) && (
                    <Button variant="ghost" size="sm" className="gap-1" onClick={() => { setEditTarget(c); setEditorOpen(true) }}>
                      <Edit2 size={14} /> Edit
                    </Button>
                  )}
                  {canSend(st) && (
                    <Button variant="secondary" size="sm" className="gap-1" onClick={() => openSend(c)}>
                      <Send size={14} /> {c.scheduled_at && new Date(c.scheduled_at) > new Date() ? 'Schedule' : 'Send'}
                    </Button>
                  )}
                  {st === 'scheduled' && (
                    <Button variant="ghost" size="sm" className="gap-1 text-success" onClick={() => actionMut.mutate({ id: c.id, action: 'pause' })}>
                      <Pause size={14} /> Pause
                    </Button>
                  )}
                  {st === 'paused' && (
                    <Button variant="ghost" size="sm" className="gap-1 text-success" onClick={() => actionMut.mutate({ id: c.id, action: 'resume' })}>
                      <Play size={14} /> Resume
                    </Button>
                  )}
                  {st === 'pending_approval' && c.requires_approval && (
                    <Button variant="ghost" size="sm" className="gap-1 text-cobalt" onClick={() => actionMut.mutate({ id: c.id, action: 'approve' })}>
                      <CheckCircle size={14} /> Approve
                    </Button>
                  )}
                  {st === 'draft' && c.requires_approval && (
                    <Button variant="ghost" size="sm" className="gap-1" onClick={() => actionMut.mutate({ id: c.id, action: 'submit-approval' })}>
                      Submit for approval
                    </Button>
                  )}
                  {st === 'active' && (
                    <Button variant="ghost" size="sm" className="gap-1 text-success" onClick={() => actionMut.mutate({ id: c.id, action: 'complete' })}>
                      Mark completed
                    </Button>
                  )}
                  <Button variant="ghost" size="sm" className="gap-1" onClick={() => { setLinksTarget(c.id); setShowLinksModal(true) }}>
                    <Link2 size={14} /> Links
                  </Button>
                  {['active', 'completed'].includes(st) && (
                    <>
                      <Button variant="ghost" size="sm" className="gap-1" onClick={() => setMetricsTarget(c)}>
                        <BarChart3 size={14} /> Metrics
                      </Button>
                      <Button variant="ghost" size="sm" className="gap-1 text-cobalt" onClick={() => { setLinksTarget(c.id); setShowAttribution(true) }}>
                        <ExternalLink size={14} /> Attribution
                      </Button>
                    </>
                  )}
                  {!['active', 'completed'].includes(st) && (
                    <Button variant="ghost" size="sm" className="gap-1 text-destructive" onClick={() => setDeleteTarget(c)}>
                      <Trash2 size={14} /> Delete
                    </Button>
                  )}
                </div>
              </Card>
            )
          })}
        </div>
      )}

      <CampaignEditorModal
        isOpen={editorOpen}
        onClose={() => { setEditorOpen(false); setEditTarget(null) }}
        editTarget={editTarget}
        programs={programs}
        segments={segments}
        uploadedLists={listsQ.data ?? []}
        templates={templates}
        onSaved={invalidate}
      />

      <AudienceManagerSheet isOpen={audienceSheetOpen} onClose={() => setAudienceSheetOpen(false)} />

      <Modal isOpen={!!deleteTarget} onClose={() => setDeleteTarget(null)} title="Delete campaign">
        <p className="text-sm text-muted-foreground mb-4">
          Delete <strong className="text-foreground">{deleteTarget?.name}</strong>? This cannot be undone.
        </p>
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={() => setDeleteTarget(null)}>Cancel</Button>
          <Button variant="destructive" loading={deleteMut.isPending} onClick={() => deleteTarget && deleteMut.mutate(deleteTarget.id)}>
            Delete
          </Button>
        </div>
      </Modal>

      <Modal
        isOpen={!!sendTarget}
        onClose={() => { setSendTarget(null); setSendPreview(null) }}
        title={sendTarget?.scheduled_at && new Date(sendTarget.scheduled_at) > new Date() ? 'Schedule campaign' : 'Send campaign'}
      >
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground">
            {sendTarget?.scheduled_at && new Date(sendTarget.scheduled_at) > new Date() ? 'Schedule' : 'Send'}{' '}
            <strong className="text-foreground">{sendTarget?.name}</strong> to the filtered audience.
          </p>
          <div className="bg-muted rounded-lg p-4 text-center">
            {previewLoading ? (
              <p className="text-sm animate-pulse">Calculating audience…</p>
            ) : (
              <>
                <p className="text-3xl font-bold text-foreground tabular-nums">{sendPreview?.deduped_count ?? 0}</p>
                <p className="text-sm text-muted-foreground">recipients after dedup & filtering</p>
              </>
            )}
          </div>
          {sendPreview && sendPreview.deduped_count === 0 && !previewLoading && (
            <p className="text-xs text-amber-800 bg-amber-50 border border-amber-100 rounded-lg px-3 py-2">
              0 recipients after filtering. Adjust your audience.
            </p>
          )}
          {sendPreview && sendPreview.sample.length > 0 && (
            <div className="border border-border rounded-lg overflow-hidden text-xs">
              <p className="px-3 py-2 bg-muted font-medium text-muted-foreground">Sample (up to 10)</p>
              <table className="w-full">
                <tbody>
                  {sendPreview.sample.map((row, i) => (
                    <tr key={i} className="border-t border-border">
                      <td className="px-3 py-1.5">{row.name ?? '—'}</td>
                      <td className="px-3 py-1.5 text-muted-foreground">{row.email ?? '—'}</td>
                      <td className="px-3 py-1.5 text-muted-foreground">{row.source}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {actionMut.isPending && (
            <div>
              <p className="text-xs text-muted-foreground mb-1 flex items-center gap-1"><CalendarClock size={12} /> Send in progress</p>
              <div className="h-2 bg-muted rounded-full overflow-hidden"><div className="h-full bg-cobalt animate-pulse w-full" /></div>
            </div>
          )}
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => { setSendTarget(null); setSendPreview(null) }}>Cancel</Button>
            <Button
              variant="secondary"
              className="gap-2"
              loading={actionMut.isPending}
              disabled={previewLoading || (sendPreview?.deduped_count ?? 0) === 0}
              onClick={() => sendTarget && actionMut.mutate({
                id: sendTarget.id,
                action: sendTarget.scheduled_at && new Date(sendTarget.scheduled_at) > new Date() ? 'schedule' : 'send',
              })}
            >
              <Send size={14} />
              {actionMut.isPending ? 'Sending…' : `Send to ${sendPreview?.deduped_count ?? 0}`}
            </Button>
          </div>
        </div>
      </Modal>

      <Modal isOpen={!!metricsTarget} onClose={() => setMetricsTarget(null)} title="Campaign metrics" size="md">
        {metricsQ.isLoading ? <Skeleton className="h-32" /> : !metrics ? (
          <p className="text-sm text-muted-foreground text-center py-6">No metrics yet.</p>
        ) : (
          <div className="space-y-4">
            {metricsTarget && !isExternal(metricsTarget) && (
              <p className="text-xs text-muted-foreground bg-muted rounded-lg px-3 py-2">
                Opens apply to external email only; internal messaging tracks delivery and clicks.
              </p>
            )}
            <div className="grid grid-cols-2 gap-3 text-center">
              {[
                { label: 'Sent', value: metrics.sent },
                { label: 'Delivered', value: metrics.delivered },
                { label: 'Opens', value: metrics.opens },
                { label: 'Clicks', value: metrics.clicks },
              ].map(m => (
                <div key={m.label} className="bg-muted rounded-lg p-3">
                  <p className="text-xl font-bold tabular-nums">{m.value}</p>
                  <p className="text-xs text-muted-foreground">{m.label}</p>
                </div>
              ))}
            </div>
            {metrics.conversions && Object.keys(metrics.conversions).length > 0 && (
              <div>
                <p className="text-xs font-medium text-muted-foreground uppercase mb-2">Conversions</p>
                <div className="grid grid-cols-2 gap-2">
                  {Object.entries(metrics.conversions).map(([k, v]) => (
                    <div key={k} className="flex justify-between text-sm border-b border-border py-1">
                      <span>{ATTRIBUTION_LABELS[k] ?? k}</span>
                      <span className="font-medium tabular-nums">{v}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </Modal>

      <Modal isOpen={showLinksModal} onClose={() => { setShowLinksModal(false); setLinksTarget(null) }} title="Trackable links">
        <div className="space-y-4">
          <div className="border border-border rounded-lg p-3 space-y-3">
            <p className="text-sm font-medium">Generate link</p>
            <div className="grid grid-cols-2 gap-2">
              <Select label="Destination" options={[
                { value: 'program', label: 'Program' },
                { value: 'institution', label: 'Institution' },
                { value: 'event', label: 'Event' },
                { value: 'custom', label: 'Custom URL' },
              ]} value={newLinkDest} onChange={e => setNewLinkDest(e.target.value)} />
              {newLinkDest === 'custom' ? (
                <Input label="URL" value={newLinkCustomUrl} onChange={e => setNewLinkCustomUrl(e.target.value)} />
              ) : (
                <Select label="Target" options={[{ value: '', label: 'Select…' }, ...programs.map(p => ({ value: p.id, label: p.program_name }))]} value={newLinkDestId} onChange={e => setNewLinkDestId(e.target.value)} />
              )}
            </div>
            <Input label="Label" value={newLinkLabel} onChange={e => setNewLinkLabel(e.target.value)} />
            <Button variant="secondary" size="sm" loading={createLinkMut.isPending} onClick={() => {
              if (!linksTarget) return
              const payload: { destination_type: string; destination_id?: string; custom_url?: string; label?: string } = {
                destination_type: newLinkDest,
                label: newLinkLabel || undefined,
              }
              if (newLinkDest === 'custom') {
                if (!newLinkCustomUrl.trim()) { showToast('URL required', 'warning'); return }
                payload.custom_url = newLinkCustomUrl
              } else if (newLinkDestId) payload.destination_id = newLinkDestId
              createLinkMut.mutate({ campaignId: linksTarget, payload })
            }}>Generate link</Button>
          </div>
          {linksQ.isLoading ? <Skeleton className="h-16" /> : links.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-4">No links yet.</p>
          ) : links.map(lnk => (
            <div key={lnk.id} className="flex gap-2 border border-border rounded-lg p-3">
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium truncate">{lnk.label || lnk.destination_name || lnk.destination_type}</p>
                <p className="text-xs text-muted-foreground truncate">{lnk.trackable_url}</p>
                <p className="text-xs text-muted-foreground">{lnk.click_count} clicks</p>
              </div>
              <Button variant="ghost" size="sm" onClick={() => lnk.trackable_url && navigator.clipboard.writeText(lnk.trackable_url).then(() => showToast('Copied', 'success'))}>
                <Copy size={14} />
              </Button>
              <Button variant="ghost" size="sm" className="text-destructive" onClick={() => linksTarget && deleteLinkMut.mutate({ campaignId: linksTarget, linkId: lnk.id })}>
                <Trash2 size={14} />
              </Button>
            </div>
          ))}
        </div>
      </Modal>

      <Modal isOpen={showAttribution} onClose={() => { setShowAttribution(false); setLinksTarget(null) }} title="Attribution" size="lg">
        {attributionQ.isLoading ? <Skeleton className="h-40" /> : !attribution ? (
          <p className="text-sm text-muted-foreground text-center py-6">No attribution data.</p>
        ) : (
          <div className="space-y-4">
            <p className="text-center text-sm text-muted-foreground">{attribution.campaign_name}</p>
            <div className="grid grid-cols-4 gap-2 text-center text-sm">
              {[
                { label: 'Recipients', v: attribution.recipients },
                { label: 'Delivered', v: attribution.delivered },
                { label: 'Opened', v: attribution.opened },
                { label: 'Clicked', v: attribution.clicked },
              ].map(x => (
                <div key={x.label} className="bg-muted rounded-lg p-2">
                  <p className="font-bold tabular-nums">{x.v}</p>
                  <p className="text-xs text-muted-foreground">{x.label}</p>
                </div>
              ))}
            </div>
            <div className="grid grid-cols-3 gap-2">
              {[
                { label: 'Views', v: attribution.views },
                { label: 'Saves', v: attribution.saves },
                { label: 'RSVPs', v: attribution.rsvps },
                { label: 'Info', v: attribution.request_infos },
                { label: 'Apps', v: attribution.applications },
              ].map(x => (
                <div key={x.label} className="border border-border rounded-lg p-2 text-center">
                  <p className="text-lg font-bold tabular-nums">{x.v}</p>
                  <p className="text-xs text-muted-foreground">{x.label}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
