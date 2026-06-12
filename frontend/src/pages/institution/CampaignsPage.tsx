import { useEffect, useState } from 'react'
import QueryError from '../../components/ui/QueryError'
import { useSearchParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Megaphone, Plus, Send, Edit2, Trash2, BarChart3, Clock, Users, Link2, Copy,
  ExternalLink, Pause, Play, CheckCircle2, CalendarClock, ShieldCheck, X, SlidersHorizontal,
} from 'lucide-react'
import {
  getCampaigns, deleteCampaign, sendCampaign, scheduleCampaign, pauseCampaign, resumeCampaign,
  completeCampaign, submitCampaignForApproval, approveCampaign, rejectCampaign,
  getCampaignMetrics, getSegments, getInstitutionPrograms, getUploadedLists, getTemplates,
  previewCampaignAudience, getCampaignLinks, createCampaignLink, deleteCampaignLink,
  getCampaignAttribution,
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
import type {
  Campaign, CampaignAttributionDetail, CampaignLink, CampaignMetrics, AudiencePreview,
  Segment, Program, UploadedList, CommunicationTemplate,
} from '../../types'
import CampaignEditorModal from './campaigns/CampaignEditorModal'
import AudienceManagerSheet from './campaigns/AudienceManagerSheet'
import {
  STATUS_BADGE, STATUS_LABELS, OBJECTIVE_LABELS, CTA_LABELS, ATTRIBUTION_LABELS,
} from './campaigns/constants'

const TABS = [
  { id: 'all', label: 'All' },
  { id: 'draft', label: 'Drafts' },
  { id: 'pending_approval', label: 'Pending' },
  { id: 'scheduled', label: 'Scheduled' },
  { id: 'active', label: 'Active' },
  { id: 'completed', label: 'Completed' },
]

export default function CampaignsPage() {
  const qc = useQueryClient()
  const [tab, setTab] = useState('all')
  const [showEditor, setShowEditor] = useState(false)
  const [editTarget, setEditTarget] = useState<Campaign | null>(null)
  const [seedSegmentId, setSeedSegmentId] = useState<string | undefined>(undefined)
  const [searchParams, setSearchParams] = useSearchParams()
  const [showAudienceMgr, setShowAudienceMgr] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<Campaign | null>(null)
  const [sendTarget, setSendTarget] = useState<Campaign | null>(null)
  const [rejectTarget, setRejectTarget] = useState<Campaign | null>(null)
  const [rejectComment, setRejectComment] = useState('')
  const [metricsTarget, setMetricsTarget] = useState<string | null>(null)
  const [linksTarget, setLinksTarget] = useState<string | null>(null)
  const [attrTarget, setAttrTarget] = useState<string | null>(null)
  const [newLinkDest, setNewLinkDest] = useState('program')
  const [newLinkDestId, setNewLinkDestId] = useState('')
  const [newLinkLabel, setNewLinkLabel] = useState('')
  const [newLinkUrl, setNewLinkUrl] = useState('')

  const statusFilter = tab === 'all' ? undefined : tab
  const campaignsQ = useQuery({ queryKey: ['campaigns', statusFilter], queryFn: () => getCampaigns(statusFilter) })
  const campaigns: Campaign[] = Array.isArray(campaignsQ.data) ? campaignsQ.data : []
  const allQ = useQuery({ queryKey: ['campaigns', undefined], queryFn: () => getCampaigns() })
  const allCampaigns: Campaign[] = Array.isArray(allQ.data) ? allQ.data : []

  const programs: Program[] = useQuery({ queryKey: ['institution-programs'], queryFn: getInstitutionPrograms }).data ?? []
  const segments: Segment[] = useQuery({ queryKey: ['segments'], queryFn: getSegments }).data ?? []
  const uploadedLists: UploadedList[] = useQuery({ queryKey: ['uploaded-lists'], queryFn: getUploadedLists }).data ?? []
  const templates: CommunicationTemplate[] = useQuery({ queryKey: ['comm-templates'], queryFn: () => getTemplates() }).data ?? []

  const refresh = () => qc.invalidateQueries({ queryKey: ['campaigns'] })

  const useLifecycle = (fn: (id: string) => Promise<Campaign>, msg: string) =>
    useMutation({
      mutationFn: fn,
      onSuccess: () => { refresh(); showToast(msg, 'success') },
      onError: (e: any) => showToast(e?.response?.data?.detail || 'Action failed', 'error'),
    })

  const sendMut = useLifecycle(sendCampaign, 'Campaign sent — now active')
  const scheduleMut = useLifecycle(scheduleCampaign, 'Campaign scheduled')
  const pauseMut = useLifecycle(pauseCampaign, 'Campaign paused')
  const resumeMut = useLifecycle(resumeCampaign, 'Campaign resumed')
  const completeMut = useLifecycle(completeCampaign, 'Campaign completed')
  const submitMut = useLifecycle(submitCampaignForApproval, 'Submitted for approval')
  const approveMut = useLifecycle(approveCampaign, 'Campaign approved')

  const deleteMut = useMutation({
    mutationFn: deleteCampaign,
    onSuccess: () => { refresh(); showToast('Campaign deleted', 'success'); setDeleteTarget(null) },
    onError: (e: any) => showToast(e?.response?.data?.detail || 'Could not delete', 'error'),
  })
  const rejectMut = useMutation({
    mutationFn: (id: string) => rejectCampaign(id, rejectComment.trim()),
    onSuccess: () => { refresh(); showToast('Campaign rejected', 'success'); setRejectTarget(null); setRejectComment('') },
    onError: () => showToast('Could not reject', 'error'),
  })

  // Send confirm — fetch audience preview
  const previewQ = useQuery<AudiencePreview>({
    queryKey: ['audience-preview', sendTarget?.id],
    queryFn: () => previewCampaignAudience(sendTarget!.id),
    enabled: !!sendTarget,
  })
  const preview = previewQ.data

  const metricsQ = useQuery<CampaignMetrics>({
    queryKey: ['campaign-metrics', metricsTarget],
    queryFn: () => getCampaignMetrics(metricsTarget!),
    enabled: !!metricsTarget,
  })
  const linksQ = useQuery<CampaignLink[]>({ queryKey: ['campaign-links', linksTarget], queryFn: () => getCampaignLinks(linksTarget!), enabled: !!linksTarget })
  const attrQ = useQuery<CampaignAttributionDetail>({ queryKey: ['campaign-attr', attrTarget], queryFn: () => getCampaignAttribution(attrTarget!), enabled: !!attrTarget })

  const createLinkMut = useMutation({
    mutationFn: (p: { id: string; payload: any }) => createCampaignLink(p.id, p.payload),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['campaign-links'] }); showToast('Link created', 'success'); setNewLinkLabel(''); setNewLinkDestId(''); setNewLinkUrl('') },
    onError: () => showToast("We couldn't create the link. Please try again.", 'error'),
  })
  const delLinkMut = useMutation({
    mutationFn: (p: { id: string; linkId: string }) => deleteCampaignLink(p.id, p.linkId),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['campaign-links'] }); showToast('Link removed', 'success') },
    onError: () => showToast("We couldn't remove the link. Please try again.", 'error'),
  })

  const copy = (t: string) => {
    navigator.clipboard.writeText(t)
      .then(() => showToast('Copied', 'success'))
      .catch(() => showToast("We couldn't copy to your clipboard.", 'error'))
  }
  const openEdit = (c: Campaign) => { setEditTarget(c); setShowEditor(true) }
  const openNew = () => { setEditTarget(null); setSeedSegmentId(undefined); setShowEditor(true) }

  // Deep link from Segments → "Use in campaign": open a new campaign editor
  // pre-seeded with the chosen segment, then strip the param (Spec 26 §3/§9).
  useEffect(() => {
    const seg = searchParams.get('segment')
    if (!seg) return
    setSeedSegmentId(seg)
    setEditTarget(null)
    setShowEditor(true)
    const next = new URLSearchParams(searchParams)
    next.delete('segment')
    setSearchParams(next, { replace: true })
  }, [searchParams, setSearchParams])

  const stat = (s: string) => allCampaigns.filter((c) => c.status === s).length

  return (
    <div className="p-6 space-y-4">
      <InstitutionPageHeader
        title="Campaigns"
        description="Plan, launch, and measure outreach across internal messaging and email."
        actions={
          <div className="flex items-center gap-2">
            <Button variant="tertiary" onClick={() => setShowAudienceMgr(true)} className="gap-2">
              <SlidersHorizontal size={16} /> Manage audience
            </Button>
            <Button variant="secondary" onClick={openNew} className="gap-2">
              <Plus size={16} /> New campaign
            </Button>
          </div>
        }
      />

      {allCampaigns.length > 0 && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {[
            { label: 'Total', value: allCampaigns.length },
            { label: 'Active', value: stat('active'), tone: 'text-success' },
            { label: 'Scheduled', value: stat('scheduled'), tone: 'text-accent' },
            { label: 'Completed', value: stat('completed') },
          ].map((s) => (
            <Card pad={false} key={s.label} className="p-3">
              <p className="text-xs text-muted-foreground">{s.label}</p>
              <p className={`text-xl font-semibold ${s.tone ?? 'text-foreground'}`}>{s.value}</p>
            </Card>
          ))}
        </div>
      )}

      <Tabs tabs={TABS} activeTab={tab} onChange={setTab} />

      {campaignsQ.isError ? (
        <QueryError detail="Couldn’t load campaigns." onRetry={() => campaignsQ.refetch()} />
      ) : campaignsQ.isLoading ? (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
          {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-44" />)}
        </div>
      ) : campaigns.length === 0 ? (
        <EmptyState
          icon={<Megaphone size={40} />}
          title={tab === 'all' ? 'No campaigns yet' : `No ${STATUS_LABELS[tab as keyof typeof STATUS_LABELS]?.toLowerCase() ?? ''} campaigns`}
          description="Plan your first outreach."
          action={{ label: 'New campaign', onClick: openNew }}
        />
      ) : (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
          {campaigns.map((c) => (
            <CampaignCard
              key={c.id}
              c={c}
              programs={programs}
              onEdit={() => openEdit(c)}
              onSend={() => setSendTarget(c)}
              onSchedule={() => scheduleMut.mutate(c.id)}
              onPause={() => pauseMut.mutate(c.id)}
              onResume={() => resumeMut.mutate(c.id)}
              onComplete={() => completeMut.mutate(c.id)}
              onSubmit={() => submitMut.mutate(c.id)}
              onApprove={() => approveMut.mutate(c.id)}
              onReject={() => setRejectTarget(c)}
              onDelete={() => setDeleteTarget(c)}
              onMetrics={() => setMetricsTarget(c.id)}
              onAttribution={() => setAttrTarget(c.id)}
              onLinks={() => setLinksTarget(c.id)}
            />
          ))}
        </div>
      )}

      <CampaignEditorModal
        isOpen={showEditor}
        onClose={() => { setShowEditor(false); setSeedSegmentId(undefined) }}
        editTarget={editTarget}
        initialSegmentId={seedSegmentId}
        programs={programs}
        segments={segments}
        uploadedLists={uploadedLists}
        templates={templates}
        onSaved={refresh}
      />
      <AudienceManagerSheet isOpen={showAudienceMgr} onClose={() => setShowAudienceMgr(false)} />

      {/* Send confirm */}
      <Modal isOpen={!!sendTarget} onClose={() => setSendTarget(null)} title="Send campaign" size="md">
        {sendTarget && (
          <div className="space-y-4">
            <p className="text-sm text-muted-foreground">
              You’re about to send <span className="font-semibold text-foreground">{sendTarget.name}</span> on{' '}
              {(sendTarget.channels || []).map((ch) => (ch === 'internal_messaging' ? 'Inbox' : 'Email')).join(' + ') || 'no channel'}.
            </p>
            <div className="rounded-lg border border-border bg-muted/40 p-4 text-center">
              {previewQ.isLoading ? (
                <p className="text-sm text-muted-foreground animate-pulse">Resolving audience…</p>
              ) : (
                <>
                  <p className="text-3xl font-bold text-accent">{preview?.deduped_count ?? 0}</p>
                  <p className="text-sm text-muted-foreground">deduped recipients</p>
                  <div className="mt-2 flex flex-wrap justify-center gap-2 text-xs text-muted-foreground">
                    {!!preview?.platform_count && <Badge variant="info">{preview.platform_count} platform</Badge>}
                    {!!preview?.uploaded_count && <Badge variant="neutral">{preview.uploaded_count} uploaded</Badge>}
                    {!!preview?.suppressed_count && <Badge variant="warning">{preview.suppressed_count} suppressed</Badge>}
                    {!!preview?.consent_excluded_count && <Badge variant="warning">{preview.consent_excluded_count} no consent</Badge>}
                  </div>
                </>
              )}
            </div>
            {preview && preview.deduped_count === 0 && (
              <p className="text-xs text-warning">0 recipients after filtering. Adjust your audience.</p>
            )}
            {preview && preview.sample.length > 0 && (
              <div className="rounded-lg border border-border divide-y divide-border max-h-44 overflow-y-auto">
                {preview.sample.map((p, i) => (
                  <div key={i} className="flex items-center justify-between px-3 py-1.5 text-[13px]">
                    <span className="text-foreground truncate">{p.name || p.email || '—'}</span>
                    <Badge variant={p.source === 'platform' ? 'info' : 'neutral'}>{p.source === 'platform' ? 'platform' : 'uploaded'}</Badge>
                  </div>
                ))}
              </div>
            )}
            <div className="flex justify-end gap-2">
              <Button variant="tertiary" onClick={() => setSendTarget(null)}>Cancel</Button>
              <Button
                variant="secondary"
                className="gap-2"
                disabled={sendMut.isPending || previewQ.isLoading || (preview?.deduped_count ?? 0) === 0}
                loading={sendMut.isPending}
                onClick={() => sendMut.mutate(sendTarget.id, { onSuccess: () => setSendTarget(null) })}
              >
                <Send size={14} /> Send to {preview?.deduped_count ?? 0}
              </Button>
            </div>
          </div>
        )}
      </Modal>

      {/* Reject */}
      <Modal isOpen={!!rejectTarget} onClose={() => setRejectTarget(null)} title="Reject campaign" size="md">
        <div className="space-y-4">
          <Textarea label="Reason" value={rejectComment} onChange={(e) => setRejectComment(e.target.value)} rows={3} placeholder="What needs to change before this can be sent?" />
          <div className="flex justify-end gap-2">
            <Button variant="tertiary" onClick={() => setRejectTarget(null)}>Cancel</Button>
            <Button variant="destructive" disabled={!rejectComment.trim() || rejectMut.isPending} loading={rejectMut.isPending} onClick={() => rejectTarget && rejectMut.mutate(rejectTarget.id)}>Reject</Button>
          </div>
        </div>
      </Modal>

      {/* Delete */}
      <Modal isOpen={!!deleteTarget} onClose={() => setDeleteTarget(null)} title="Delete campaign" size="sm">
        <p className="text-sm text-muted-foreground mb-4">
          Delete <span className="font-semibold text-foreground">{deleteTarget?.name}</span>? This cannot be undone.
        </p>
        <div className="flex justify-end gap-2">
          <Button variant="tertiary" onClick={() => setDeleteTarget(null)}>Cancel</Button>
          <Button variant="destructive" loading={deleteMut.isPending} onClick={() => deleteTarget && deleteMut.mutate(deleteTarget.id)}>Delete</Button>
        </div>
      </Modal>

      {/* Metrics */}
      <Modal isOpen={!!metricsTarget} onClose={() => setMetricsTarget(null)} title="Campaign metrics" size="md">
        <MetricsView metrics={metricsQ.data} loading={metricsQ.isLoading} />
      </Modal>

      {/* Attribution */}
      <Modal isOpen={!!attrTarget} onClose={() => setAttrTarget(null)} title="Attribution" size="lg">
        <AttributionView attr={attrQ.data} loading={attrQ.isLoading} />
      </Modal>

      {/* Links */}
      <Modal isOpen={!!linksTarget} onClose={() => setLinksTarget(null)} title="Trackable links" size="md">
        <div className="space-y-4">
          <div className="rounded-lg border border-border p-3 space-y-3">
            <p className="text-[13px] font-semibold text-foreground">Generate a link</p>
            <div className="grid grid-cols-2 gap-2">
              <Select
                label="Destination"
                options={[
                  { value: 'program', label: 'Program' },
                  { value: 'institution', label: 'Institution page' },
                  { value: 'event', label: 'Event' },
                  { value: 'custom', label: 'Custom URL' },
                ]}
                value={newLinkDest}
                onChange={(e) => setNewLinkDest(e.target.value)}
              />
              {newLinkDest === 'custom' ? (
                <Input label="URL" value={newLinkUrl} onChange={(e) => setNewLinkUrl(e.target.value)} placeholder="https://…" />
              ) : (
                <Select
                  label="Target"
                  options={[{ value: '', label: 'Select…' }, ...programs.map((p) => ({ value: p.id, label: p.program_name }))]}
                  value={newLinkDestId}
                  onChange={(e) => setNewLinkDestId(e.target.value)}
                />
              )}
            </div>
            <Input label="Label (optional)" value={newLinkLabel} onChange={(e) => setNewLinkLabel(e.target.value)} placeholder="CTA button" />
            <Button
              variant="secondary"
              size="sm"
              loading={createLinkMut.isPending}
              onClick={() => {
                if (!linksTarget) return
                const payload: any = { destination_type: newLinkDest, label: newLinkLabel || undefined }
                if (newLinkDest === 'custom') {
                  if (!newLinkUrl.trim()) return showToast('URL required', 'warning')
                  payload.custom_url = newLinkUrl
                } else if (newLinkDestId) payload.destination_id = newLinkDestId
                createLinkMut.mutate({ id: linksTarget, payload })
              }}
            >
              Generate link
            </Button>
          </div>
          {linksQ.isLoading ? (
            <Skeleton className="h-20" />
          ) : (linksQ.data ?? []).length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-3">No trackable links yet.</p>
          ) : (
            <div className="space-y-2">
              {(linksQ.data ?? []).map((l) => (
                <div key={l.id} className="rounded-lg border border-border p-3 flex items-center justify-between">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-foreground truncate">{l.label || l.destination_name || l.destination_type}</span>
                      <Badge variant="neutral">{l.destination_type}</Badge>
                    </div>
                    <p className="text-xs text-muted-foreground truncate mt-1">{l.trackable_url}</p>
                    <p className="text-xs text-muted-foreground mt-0.5">{l.click_count} clicks</p>
                  </div>
                  <div className="flex items-center gap-1 ml-2">
                    <Button variant="ghost" size="sm" onClick={() => l.trackable_url && copy(l.trackable_url)}><Copy size={14} /></Button>
                    <Button variant="ghost" size="sm" className="text-destructive" onClick={() => linksTarget && delLinkMut.mutate({ id: linksTarget, linkId: l.id })}><Trash2 size={14} /></Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </Modal>
    </div>
  )
}

// Compact ghost action button used across a card's control row.
function A(props: React.ComponentProps<typeof Button>) {
  return <Button variant="ghost" size="sm" className="gap-1" {...props} />
}

function CampaignCard({
  c, programs, onEdit, onSend, onSchedule, onPause, onResume, onComplete, onSubmit, onApprove, onReject, onDelete, onMetrics, onAttribution, onLinks,
}: {
  c: Campaign; programs: Program[]
  onEdit: () => void; onSend: () => void; onSchedule: () => void; onPause: () => void; onResume: () => void; onComplete: () => void
  onSubmit: () => void; onApprove: () => void; onReject: () => void; onDelete: () => void; onMetrics: () => void; onAttribution: () => void; onLinks: () => void
}) {
  const status = c.status || 'draft'
  const progNames = (c.associate_program_ids || []).map((id) => programs.find((p) => p.id === id)?.program_name).filter(Boolean)
  return (
    <Card pad={false} className="p-4 flex flex-col">
      <div className="flex items-start justify-between gap-2 mb-2">
        <h3 className="font-semibold text-foreground">{c.name}</h3>
        <Badge variant={STATUS_BADGE[status]}>{STATUS_LABELS[status]}</Badge>
      </div>
      <div className="flex flex-wrap items-center gap-1.5 mb-3">
        {c.objective && <Badge variant="neutral">{OBJECTIVE_LABELS[c.objective] ?? c.objective}</Badge>}
        {(c.channels || []).map((ch) => (
          <Badge key={ch} variant="info">{ch === 'internal_messaging' ? 'Inbox' : 'Email'}</Badge>
        ))}
        {c.cta_type && <Badge variant="neutral">{CTA_LABELS[c.cta_type] ?? c.cta_type}</Badge>}
      </div>

      <div className="space-y-1 text-sm text-muted-foreground flex-1">
        {c.subject && <p className="truncate">Subject: {c.subject}</p>}
        {progNames.length > 0 && <p className="text-xs truncate">Programs: {progNames.join(', ')}</p>}
        <div className="flex flex-wrap items-center gap-3 text-xs pt-1">
          {(c.audience?.deduped_count ?? null) !== null && (
            <span className="inline-flex items-center gap-1 text-accent font-medium">
              <Users size={12} /> ≈{c.audience?.deduped_count} recipients
            </span>
          )}
          {typeof c.sent_count === 'number' && c.sent_count > 0 && (
            <span className="inline-flex items-center gap-1"><Send size={12} /> {c.sent_count} sent</span>
          )}
          {c.scheduled_at && <span className="inline-flex items-center gap-1"><Clock size={12} /> {formatDateTime(c.scheduled_at)}</span>}
        </div>
        {status === 'draft' && c.rejection_comment && (
          <p className="mt-1 text-xs text-warning">Returned: {c.rejection_comment}</p>
        )}
        <p className="text-xs text-muted-foreground/70 pt-0.5">Created {formatDate(c.created_at)}</p>
      </div>

      <div className="flex flex-wrap gap-1 mt-3 pt-3 border-t border-border">
        {status === 'pending_approval' ? (
          <>
            <A onClick={onApprove} className="text-success"><ShieldCheck size={14} /> Approve</A>
            <A onClick={onReject} className="text-destructive"><X size={14} /> Reject</A>
            <A onClick={onLinks}><Link2 size={14} /> Links</A>
          </>
        ) : (
          <>
            {['draft', 'scheduled', 'paused'].includes(status) && (
              <A onClick={onEdit}><Edit2 size={14} /> Edit</A>
            )}
            {c.requires_approval && status === 'draft' && !c.approved_at && (
              <A onClick={onSubmit} className="text-accent"><ShieldCheck size={14} /> Submit</A>
            )}
            {['draft', 'scheduled'].includes(status) && (
              <Button variant="secondary" size="sm" className="gap-1" onClick={onSend}><Send size={14} /> Send</Button>
            )}
            {status === 'draft' && c.scheduled_at && (
              <A onClick={onSchedule} className="text-accent"><CalendarClock size={14} /> Schedule</A>
            )}
            {['active', 'scheduled'].includes(status) && (
              <A onClick={onPause}><Pause size={14} /> Pause</A>
            )}
            {status === 'paused' && <A onClick={onResume} className="text-success"><Play size={14} /> Resume</A>}
            {['active', 'paused'].includes(status) && (
              <A onClick={onComplete}><CheckCircle2 size={14} /> Complete</A>
            )}
            {['active', 'paused', 'completed'].includes(status) && (
              <>
                <A onClick={onMetrics}><BarChart3 size={14} /> Metrics</A>
                <A onClick={onAttribution} className="text-accent"><ExternalLink size={14} /> Attribution</A>
              </>
            )}
            <A onClick={onLinks}><Link2 size={14} /> Links</A>
            {!['active', 'completed'].includes(status) && (
              <A onClick={onDelete} className="text-destructive"><Trash2 size={14} /> Delete</A>
            )}
          </>
        )}
      </div>
    </Card>
  )
}

function MetricsView({ metrics, loading }: { metrics?: CampaignMetrics; loading: boolean }) {
  if (loading) return <div className="space-y-3">{Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-8" />)}</div>
  if (!metrics) return <p className="text-sm text-muted-foreground text-center py-4">No metrics yet.</p>
  const sent = metrics.sent || 0
  const pct = (v: number) => (sent > 0 ? Math.round((v / sent) * 100) : 0)
  const bars = [
    { label: 'Delivered', value: metrics.delivered, cls: 'bg-secondary' },
    { label: 'Opens (email)', value: metrics.opens, cls: 'bg-success' },
    { label: 'Clicks', value: metrics.clicks, cls: 'bg-accent' },
  ]
  const conv = Object.entries(metrics.conversions || {}).filter(([k]) => ATTRIBUTION_LABELS[k])
  return (
    <div className="space-y-4">
      <div className="text-center">
        <p className="text-3xl font-bold text-foreground">{sent}</p>
        <p className="text-sm text-muted-foreground">recipients</p>
      </div>
      {bars.map((b) => (
        <div key={b.label}>
          <div className="flex justify-between text-sm mb-1">
            <span className="text-muted-foreground">{b.label}</span>
            <span className="font-medium text-foreground">{b.value} ({pct(b.value)}%)</span>
          </div>
          <div className="w-full bg-muted rounded-full h-2">
            <div className={`${b.cls} rounded-full h-2 transition-all`} style={{ width: `${pct(b.value)}%` }} />
          </div>
        </div>
      ))}
      {conv.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-muted-foreground uppercase mb-2">Conversions</p>
          <div className="grid grid-cols-3 gap-2">
            {conv.map(([k, v]) => (
              <div key={k} className="bg-muted/60 rounded-lg p-2 text-center">
                <p className="text-lg font-bold text-foreground">{v}</p>
                <p className="text-xs text-muted-foreground">{ATTRIBUTION_LABELS[k]}</p>
              </div>
            ))}
          </div>
        </div>
      )}
      <div className="flex gap-2">
        <div className="flex-1 bg-muted/60 rounded-lg p-2 text-center">
          <p className="text-lg font-bold text-foreground">{metrics.unsubscribes}</p>
          <p className="text-xs text-muted-foreground">Unsubscribes</p>
        </div>
        <div className="flex-1 bg-muted/60 rounded-lg p-2 text-center">
          <p className="text-lg font-bold text-foreground">{metrics.bounces}</p>
          <p className="text-xs text-muted-foreground">Bounces</p>
        </div>
      </div>
    </div>
  )
}

function AttributionView({ attr, loading }: { attr?: CampaignAttributionDetail; loading: boolean }) {
  if (loading) return <div className="space-y-3">{Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-8" />)}</div>
  if (!attr) return <p className="text-sm text-muted-foreground text-center py-4">No attribution data.</p>
  const funnel = [
    { label: 'Recipients', value: attr.recipients },
    { label: 'Delivered', value: attr.delivered },
    { label: 'Opened', value: attr.opened },
    { label: 'Clicked', value: attr.clicked },
  ]
  const actions = [
    { label: 'Views', value: attr.views },
    { label: 'Saves', value: attr.saves },
    { label: 'RSVPs', value: attr.rsvps },
    { label: 'Info requests', value: attr.request_infos },
    { label: 'Applications', value: attr.applications },
  ]
  return (
    <div className="space-y-5">
      <div className="space-y-2">
        <p className="text-xs font-semibold text-muted-foreground uppercase">Engagement funnel</p>
        {funnel.map((s) => (
          <div key={s.label} className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">{s.label}</span>
            <span className="font-medium text-foreground">
              {s.value}{attr.recipients > 0 && <span className="text-muted-foreground/70 text-xs"> ({Math.round((s.value / attr.recipients) * 100)}%)</span>}
            </span>
          </div>
        ))}
      </div>
      <div className="space-y-2">
        <p className="text-xs font-semibold text-muted-foreground uppercase">Downstream actions</p>
        <div className="grid grid-cols-3 gap-2">
          {actions.map((a) => (
            <div key={a.label} className="bg-muted/60 rounded-lg p-2 text-center">
              <p className="text-lg font-bold text-foreground">{a.value}</p>
              <p className="text-xs text-muted-foreground">{a.label}</p>
            </div>
          ))}
        </div>
      </div>
      {attr.links.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-semibold text-muted-foreground uppercase">Per-link breakdown</p>
          <div className="border border-border rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-muted/60">
                <tr>
                  <th className="text-left px-3 py-2 font-medium text-muted-foreground">Link</th>
                  <th className="text-right px-3 py-2 font-medium text-muted-foreground">Clicks</th>
                  <th className="text-right px-3 py-2 font-medium text-muted-foreground">Views</th>
                  <th className="text-right px-3 py-2 font-medium text-muted-foreground">Saves</th>
                  <th className="text-right px-3 py-2 font-medium text-muted-foreground">Apps</th>
                </tr>
              </thead>
              <tbody>
                {attr.links.map((l) => (
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
  )
}
