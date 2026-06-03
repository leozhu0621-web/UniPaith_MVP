import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Download } from 'lucide-react'
import { exportAuditCsv, getAuditEvent, getAuditLog } from '../../api/institutions'
import type { AuditLogParams } from '../../api/institutions'
import Card from '../../components/ui/Card'
import Select from '../../components/ui/Select'
import Input from '../../components/ui/Input'
import Button from '../../components/ui/Button'
import Table from '../../components/ui/Table'
import Sheet from '../../components/ui/Sheet'
import Skeleton from '../../components/ui/Skeleton'
import InstitutionPageHeader from '../../components/institution/InstitutionPageHeader'
import { showToast } from '../../stores/toast-store'
import { formatDateTime } from '../../utils/format'
import type { AuditEventDetail, AuditLogEntry } from '../../types'

// Spec 36 §2 — category taxonomy. ``batch_*`` is a single bucket; the audit
// log also captures messaging / team-invite events alongside the 13.
const CATEGORY_OPTIONS = [
  { value: '', label: 'All actions' },
  { value: 'status_change', label: 'Status change' },
  { value: 'decision_release', label: 'Decision release' },
  { value: 'reviewer_assigned', label: 'Reviewer assigned' },
  { value: 'checklist_change', label: 'Checklist change' },
  { value: 'document_replaced', label: 'Document replaced' },
  { value: 'waiver_override', label: 'Waiver / override' },
  { value: 'batch_action', label: 'Batch action' },
  { value: 'ai_generated', label: 'AI generated' },
  { value: 'consent_change', label: 'Consent change' },
  { value: 'data_export', label: 'Data export' },
  { value: 'data_deletion', label: 'Data deletion' },
  { value: 'fairness_signal_override', label: 'Fairness override' },
  { value: 'integrity_resolution', label: 'Integrity resolution' },
  { value: 'message', label: 'Messaging' },
  { value: 'team_invite', label: 'Team invite' },
]

const ENTITY_OPTIONS = [
  { value: '', label: 'All entities' },
  { value: 'application', label: 'Application' },
  { value: 'checklist_item', label: 'Checklist item' },
  { value: 'document', label: 'Document' },
  { value: 'review', label: 'Review' },
  { value: 'interview', label: 'Interview' },
  { value: 'offer', label: 'Offer' },
  { value: 'consent', label: 'Consent' },
  { value: 'segment', label: 'Segment' },
  { value: 'campaign', label: 'Campaign' },
  { value: 'conversation', label: 'Conversation' },
  { value: 'ai_artifact', label: 'AI artifact' },
  { value: 'team_invite', label: 'Team invite' },
]

// Spec 36 §9 — actor badge colours: system=gray · student=cobalt ·
// institution=body · AI=gold (gold shown as the marker dot to keep text
// contrast accessible).
const ROLE_BADGE: Record<string, string> = {
  system: 'bg-muted text-muted-foreground',
  student: 'bg-secondary/10 text-secondary',
  institution_admin: 'bg-muted text-foreground',
  ai_agent: 'bg-primary/15 text-foreground',
}
const ROLE_DOT: Record<string, string> = {
  system: 'bg-muted-foreground',
  student: 'bg-secondary',
  institution_admin: 'bg-foreground',
  ai_agent: 'bg-primary',
}
const ROLE_LABEL: Record<string, string> = {
  system: 'System',
  student: 'Student',
  institution_admin: 'Institution',
  ai_agent: 'AI',
}

const humanize = (s: string | null | undefined) => (s || '').replace(/[_.]/g, ' ').trim()
const isOverride = (e: AuditLogEntry) =>
  (e.category || '').endsWith('_override') || Boolean(e.reason)

function ActorBadge({ role, email }: { role: string | null; email: string | null }) {
  const r = role && ROLE_BADGE[role] ? role : 'system'
  const label = email || ROLE_LABEL[r]
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium ${ROLE_BADGE[r]}`}
    >
      <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${ROLE_DOT[r]}`} />
      <span className="max-w-[180px] truncate">{label}</span>
    </span>
  )
}

function Field({
  label,
  value,
  mono,
}: {
  label: string
  value: string | null | undefined
  mono?: boolean
}) {
  if (!value) return null
  return (
    <div>
      <p className="mb-0.5 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
        {label}
      </p>
      <p className={`break-words text-foreground ${mono ? 'font-mono text-xs' : ''}`}>{value}</p>
    </div>
  )
}

function DiffBox({ title, value }: { title: string; value: Record<string, unknown> | null }) {
  if (!value || Object.keys(value).length === 0) return null
  return (
    <div className="flex-1 min-w-0">
      <p className="mb-1 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
        {title}
      </p>
      <pre className="overflow-x-auto rounded-md bg-muted p-2 font-mono text-xs text-foreground">
        {JSON.stringify(value, null, 2)}
      </pre>
    </div>
  )
}

function EventDetail({ e }: { e: AuditEventDetail }) {
  return (
    <div className="space-y-5 text-sm">
      <div className="flex flex-wrap items-center gap-2">
        <ActorBadge role={e.actor_role} email={e.actor_email} />
        <span className="font-medium text-foreground">{humanize(e.action)}</span>
      </div>
      <Field label="When" value={formatDateTime(e.occurred_at || e.created_at)} />
      <Field label="Category" value={humanize(e.category)} />
      <Field label="Entity" value={`${humanize(e.entity_type)}${e.entity_id ? ` · ${e.entity_id}` : ''}`} />
      {e.application_id && <Field label="Application" value={e.application_id} mono />}

      {e.reason && (
        <div className="rounded-md bg-warning-soft p-3">
          <p className="mb-1 text-[11px] font-semibold uppercase tracking-wider text-warning">
            Override reason
          </p>
          <p className="text-foreground">{e.reason}</p>
        </div>
      )}

      {(e.old_value || e.new_value) && (
        <div className="flex flex-col gap-3 sm:flex-row">
          <DiffBox title="Before" value={e.old_value} />
          <DiffBox title="After" value={e.new_value} />
        </div>
      )}

      {e.description && <Field label="Detail" value={e.description} />}
      {e.metadata_json && Object.keys(e.metadata_json).length > 0 && (
        <Field label="Metadata" value={JSON.stringify(e.metadata_json)} mono />
      )}

      {(e.ip_address || e.user_agent) && (
        <div className="space-y-0.5 border-t border-border pt-3 text-xs text-muted-foreground">
          {e.ip_address && <p>IP · {e.ip_address}</p>}
          {e.user_agent && <p className="truncate">{e.user_agent}</p>}
        </div>
      )}
    </div>
  )
}

export default function AuditLogPage() {
  const [category, setCategory] = useState('')
  const [entity, setEntity] = useState('')
  const [actorId, setActorId] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [page, setPage] = useState(0)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [exporting, setExporting] = useState(false)
  const pageSize = 50

  const params: AuditLogParams = {
    category: category || undefined,
    entity_type: entity || undefined,
    actor_id: actorId || undefined,
    date_from: dateFrom || undefined,
    date_to: dateTo || undefined,
  }

  const auditQ = useQuery({
    queryKey: ['audit-log', params, page],
    queryFn: () => getAuditLog({ ...params, limit: pageSize, offset: page * pageSize }),
  })
  const entries: AuditLogEntry[] = auditQ.data?.items ?? []
  const total = auditQ.data?.total ?? 0

  // Actor dropdown derived from loaded rows (keeps the current selection present).
  const actorOptions = useMemo(() => {
    const seen = new Map<string, string>()
    for (const e of entries) {
      if (e.actor_user_id) {
        seen.set(e.actor_user_id, e.actor_email || ROLE_LABEL[e.actor_role || 'system'] || 'Actor')
      }
    }
    if (actorId && !seen.has(actorId)) seen.set(actorId, 'Selected actor')
    return [{ value: '', label: 'All actors' }, ...[...seen].map(([v, l]) => ({ value: v, label: l }))]
  }, [entries, actorId])

  const detailQ = useQuery({
    queryKey: ['audit-event', selectedId],
    queryFn: () => getAuditEvent(selectedId as string),
    enabled: !!selectedId,
  })

  const hasFilters = category || entity || actorId || dateFrom || dateTo
  const clearFilters = () => {
    setCategory('')
    setEntity('')
    setActorId('')
    setDateFrom('')
    setDateTo('')
    setPage(0)
  }

  const handleExport = async () => {
    setExporting(true)
    try {
      const blob = await exportAuditCsv(params)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'unipaith-audit-log.csv'
      a.click()
      URL.revokeObjectURL(url)
      showToast('Audit log exported', 'success')
    } catch {
      showToast('Export failed. Try again.', 'error')
    } finally {
      setExporting(false)
    }
  }

  const columns = [
    {
      key: 'occurred_at',
      label: 'Timestamp',
      render: (r: AuditLogEntry) => (
        <span className="whitespace-nowrap text-muted-foreground">
          {formatDateTime(r.occurred_at || r.created_at)}
        </span>
      ),
    },
    {
      key: 'actor',
      label: 'Actor',
      render: (r: AuditLogEntry) => <ActorBadge role={r.actor_role} email={r.actor_email} />,
    },
    {
      key: 'action',
      label: 'Action',
      render: (r: AuditLogEntry) => (
        <div className="flex flex-col">
          <span className="font-medium text-foreground">{humanize(r.action)}</span>
          {r.category && r.category !== r.action && (
            <span className="text-[11px] text-muted-foreground">{humanize(r.category)}</span>
          )}
        </div>
      ),
    },
    {
      key: 'entity',
      label: 'Entity',
      render: (r: AuditLogEntry) => (
        <span className="text-muted-foreground">
          {humanize(r.entity_type)}
          {r.entity_id ? <span className="text-muted-foreground/70"> · {r.entity_id.slice(0, 16)}</span> : null}
        </span>
      ),
    },
  ]

  const totalPages = Math.max(1, Math.ceil(total / pageSize))

  return (
    <div className="space-y-4 p-6">
      <InstitutionPageHeader
        title="Audit log"
        description="Who did what, when — the complete, append-only trail for compliance, fairness audits, and incident review."
      />

      {/* Filters (Spec 36 §4) */}
      <Card className="p-4">
        <div className="flex flex-wrap items-end gap-3">
          <Select
            label="Action"
            options={CATEGORY_OPTIONS}
            value={category}
            onChange={e => {
              setCategory(e.target.value)
              setPage(0)
            }}
          />
          <Select
            label="Entity"
            options={ENTITY_OPTIONS}
            value={entity}
            onChange={e => {
              setEntity(e.target.value)
              setPage(0)
            }}
          />
          <Select
            label="Actor"
            options={actorOptions}
            value={actorId}
            onChange={e => {
              setActorId(e.target.value)
              setPage(0)
            }}
          />
          <Input
            label="From"
            type="date"
            value={dateFrom}
            onChange={e => {
              setDateFrom(e.target.value)
              setPage(0)
            }}
          />
          <Input
            label="To"
            type="date"
            value={dateTo}
            onChange={e => {
              setDateTo(e.target.value)
              setPage(0)
            }}
          />
          {hasFilters && (
            <Button variant="ghost" size="sm" onClick={clearFilters}>
              Clear
            </Button>
          )}
          <div className="ml-auto flex items-center gap-3">
            <span className="text-xs text-muted-foreground">{total} events</span>
            <Button variant="tertiary" size="sm" onClick={handleExport} loading={exporting}>
              <Download size={14} /> Export CSV
            </Button>
          </div>
        </div>
      </Card>

      <Table
        columns={columns}
        data={entries}
        isLoading={auditQ.isLoading}
        emptyMessage="No events match your filters."
        onRowClick={(r: AuditLogEntry) => setSelectedId(r.id)}
        rowClassName={(r: AuditLogEntry) =>
          isOverride(r) ? 'bg-warning-soft hover:bg-warning-soft' : undefined
        }
      />

      {total > pageSize && (
        <div className="flex items-center justify-between pt-1">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setPage(p => Math.max(0, p - 1))}
            disabled={page === 0}
          >
            Previous
          </Button>
          <span className="text-xs text-muted-foreground">
            Page {page + 1} of {totalPages}
          </span>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setPage(p => p + 1)}
            disabled={(page + 1) * pageSize >= total}
          >
            Next
          </Button>
        </div>
      )}

      {/* Detail panel (Spec 36 §4 — before/after diff + reason) */}
      <Sheet isOpen={!!selectedId} onClose={() => setSelectedId(null)} title="Audit event">
        {detailQ.isLoading ? (
          <div className="space-y-3">
            <Skeleton className="h-6 w-2/3" />
            <Skeleton className="h-20 w-full" />
            <Skeleton className="h-20 w-full" />
          </div>
        ) : detailQ.data ? (
          <EventDetail e={detailQ.data} />
        ) : (
          <p className="text-sm text-muted-foreground">Couldn't load this event.</p>
        )}
      </Sheet>
    </div>
  )
}
