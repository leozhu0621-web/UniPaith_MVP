import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ScrollText, User, Clock, Filter } from 'lucide-react'
import { getAuditLog } from '../../api/institutions'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Select from '../../components/ui/Select'
import Input from '../../components/ui/Input'
import Button from '../../components/ui/Button'
import Skeleton from '../../components/ui/Skeleton'
import EmptyState from '../../components/ui/EmptyState'
import InstitutionPageHeader from '../../components/institution/InstitutionPageHeader'
import { formatDateTime } from '../../utils/format'
import type { AuditLogEntry } from '../../types'

const ACTION_BADGE: Record<string, 'info' | 'success' | 'warning' | 'neutral'> = {
  status_change: 'info',
  decision_release: 'success',
  reviewer_assigned: 'neutral',
  checklist_change: 'warning',
  document_replaced: 'warning',
  waiver_override: 'warning',
  batch_status_update: 'info',
  batch_decision: 'success',
  batch_assign: 'neutral',
  batch_request_items: 'warning',
}

const ACTION_OPTIONS = [
  { value: '', label: 'All Actions' },
  { value: 'status_change', label: 'Status Change' },
  { value: 'decision_release', label: 'Decision Release' },
  { value: 'reviewer_assigned', label: 'Reviewer Assigned' },
  { value: 'checklist_change', label: 'Checklist Change' },
  { value: 'document_replaced', label: 'Document Replaced' },
  { value: 'waiver_override', label: 'Waiver / Override' },
  { value: 'batch_status_update', label: 'Batch Status Update' },
  { value: 'batch_decision', label: 'Batch Decision' },
]

const ENTITY_OPTIONS = [
  { value: '', label: 'All Entities' },
  { value: 'application', label: 'Application' },
  { value: 'checklist', label: 'Checklist' },
  { value: 'document', label: 'Document' },
  { value: 'review', label: 'Review' },
  { value: 'interview', label: 'Interview' },
]

export default function AuditLogPage() {
  const [actionFilter, setActionFilter] = useState('')
  const [entityFilter, setEntityFilter] = useState('')
  const [appIdFilter, setAppIdFilter] = useState('')
  const [page, setPage] = useState(0)
  const pageSize = 50

  const auditQ = useQuery({
    queryKey: ['audit-log', actionFilter, entityFilter, appIdFilter, page],
    queryFn: () => getAuditLog({
      action: actionFilter || undefined,
      entity_type: entityFilter || undefined,
      application_id: appIdFilter || undefined,
      limit: pageSize,
      offset: page * pageSize,
    }),
  })

  const entries: AuditLogEntry[] = auditQ.data?.items ?? []
  const total = auditQ.data?.total ?? 0

  return (
    <div className="p-6 space-y-4">
      <InstitutionPageHeader
        title="Audit Log"
        description="Who changed what, when — complete trail for admissions pipeline actions."
      />

      {/* Filters */}
      <Card className="p-4">
        <div className="flex items-center gap-3">
          <Filter size={16} className="text-gray-400" />
          <Select
            label=""
            options={ACTION_OPTIONS}
            value={actionFilter}
            onChange={e => { setActionFilter(e.target.value); setPage(0) }}
          />
          <Select
            label=""
            options={ENTITY_OPTIONS}
            value={entityFilter}
            onChange={e => { setEntityFilter(e.target.value); setPage(0) }}
          />
          <Input
            label=""
            value={appIdFilter}
            onChange={e => { setAppIdFilter(e.target.value); setPage(0) }}
            placeholder="Application ID..."
            className="max-w-[250px]"
          />
          {(actionFilter || entityFilter || appIdFilter) && (
            <Button variant="ghost" size="sm" onClick={() => { setActionFilter(''); setEntityFilter(''); setAppIdFilter(''); setPage(0) }}>
              Clear
            </Button>
          )}
          <span className="ml-auto text-xs text-gray-400">{total} entries</span>
        </div>
      </Card>

      {/* Log Entries */}
      {auditQ.isLoading ? (
        <div className="space-y-2">{Array.from({ length: 8 }).map((_, i) => <Skeleton key={i} className="h-16" />)}</div>
      ) : entries.length === 0 ? (
        <EmptyState
          icon={<ScrollText size={40} />}
          title="No audit entries"
          description="Actions in the admissions pipeline will be recorded here automatically."
        />
      ) : (
        <div className="space-y-1">
          {entries.map(entry => (
            <Card key={entry.id} className="p-3">
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <Badge variant={ACTION_BADGE[entry.action] ?? 'neutral'}>
                      {entry.action.replace(/_/g, ' ')}
                    </Badge>
                    <Badge variant="neutral">{entry.entity_type}</Badge>
                    {entry.description && (
                      <span className="text-sm text-gray-700">{entry.description}</span>
                    )}
                  </div>
                  <div className="flex items-center gap-4 text-xs text-gray-400">
                    {entry.actor_email && (
                      <span className="flex items-center gap-1"><User size={11} /> {entry.actor_email}</span>
                    )}
                    <span className="flex items-center gap-1"><Clock size={11} /> {formatDateTime(entry.created_at)}</span>
                    {entry.application_id && (
                      <span className="font-mono text-gray-300">app:{entry.application_id.slice(0, 8)}</span>
                    )}
                  </div>
                  {(entry.old_value || entry.new_value) && (
                    <div className="flex items-center gap-2 mt-1 text-xs">
                      {entry.old_value && (
                        <span className="text-red-400 bg-red-50 px-1.5 py-0.5 rounded font-mono">
                          {JSON.stringify(entry.old_value)}
                        </span>
                      )}
                      {entry.old_value && entry.new_value && <span className="text-gray-300">&rarr;</span>}
                      {entry.new_value && (
                        <span className="text-green-600 bg-green-50 px-1.5 py-0.5 rounded font-mono">
                          {JSON.stringify(entry.new_value)}
                        </span>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </Card>
          ))}

          {/* Pagination */}
          {total > pageSize && (
            <div className="flex items-center justify-between pt-3">
              <Button variant="ghost" size="sm" onClick={() => setPage(p => Math.max(0, p - 1))} disabled={page === 0}>
                Previous
              </Button>
              <span className="text-xs text-gray-500">
                Page {page + 1} of {Math.ceil(total / pageSize)}
              </span>
              <Button variant="ghost" size="sm" onClick={() => setPage(p => p + 1)} disabled={(page + 1) * pageSize >= total}>
                Next
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
