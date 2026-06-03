import { CalendarClock, Inbox as InboxIcon, UserCheck } from 'lucide-react'
import Badge from '../../../components/ui/Badge'
import Skeleton from '../../../components/ui/Skeleton'
import { formatRelative } from '../../../utils/format'
import type { InstThreadFilter, InstThreadSummary, ReasonCode } from '../../../types'
import { REASON_CONFIG, REASON_OPTIONS, STATUS_CONFIG, formatDue, isOverdue } from './reasonCodes'

export interface InstInboxFilters {
  filter: InstThreadFilter
  reason: ReasonCode | 'all'
  program_id: string
  state: 'all' | 'open' | 'awaiting_student' | 'awaiting_us' | 'closed'
}

const FILTER_OPTIONS: { value: InstThreadFilter; label: string }[] = [
  { value: 'all', label: 'All' },
  { value: 'mine', label: 'Assigned to me' },
  { value: 'unassigned', label: 'Unassigned' },
]

const STATE_OPTIONS: { value: InstInboxFilters['state']; label: string }[] = [
  { value: 'all', label: 'All states' },
  { value: 'awaiting_us', label: 'We owe a reply' },
  { value: 'awaiting_student', label: 'Awaiting student' },
  { value: 'open', label: 'Open' },
  { value: 'closed', label: 'Closed' },
]

function selectCls() {
  return 'h-7 rounded-md border border-border bg-card px-2 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary'
}

function ThreadRow({
  thread,
  selected,
  onSelect,
}: {
  thread: InstThreadSummary
  selected: boolean
  onSelect: (id: string) => void
}) {
  const reason = thread.reason_label ? REASON_CONFIG[thread.reason_label] : null
  const ReasonIcon = reason?.icon
  const status = STATUS_CONFIG[thread.status]
  const StatusIcon = status?.icon
  const due = formatDue(thread.due_date)
  const overdue = isOverdue(thread)
  const muted = thread.status === 'awaiting_student' || thread.status === 'closed'

  return (
    <button
      onClick={() => onSelect(thread.id)}
      className={`w-full border-b border-border px-3 py-2.5 text-left transition-colors hover:bg-muted ${
        selected ? 'bg-muted' : ''
      } ${overdue ? 'border-l-2 border-l-warning bg-warning-soft/30' : ''} ${
        muted && !selected ? 'opacity-75' : ''
      }`}
    >
      <div className="flex items-center gap-2">
        {thread.unread_count > 0 && (
          <span
            className="flex h-4 min-w-4 shrink-0 items-center justify-center rounded-full bg-secondary px-1 text-[10px] font-semibold text-secondary-foreground"
            aria-label={`${thread.unread_count} unread`}
          >
            {thread.unread_count}
          </span>
        )}
        <p
          className={`flex-1 truncate text-sm ${
            thread.unread_count > 0 ? 'font-semibold text-foreground' : 'text-foreground'
          }`}
        >
          {thread.student.name}
        </p>
        <span className="shrink-0 text-[10px] text-muted-foreground">
          {formatRelative(thread.last_message_at)}
        </span>
      </div>
      <p className="mt-0.5 truncate text-[11px] text-secondary">
        {thread.program_name || 'General inquiry'}
        {thread.application_id ? ' · Application' : ''}
      </p>
      <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
        {reason && (
          <Badge variant={reason.variant} size="sm">
            {ReasonIcon && <ReasonIcon size={10} />}
            {reason.label}
          </Badge>
        )}
        {!reason && status && (
          <Badge variant={status.variant} size="sm">
            {StatusIcon && <StatusIcon size={10} />}
            {status.label}
          </Badge>
        )}
        {due && (
          <span
            className={`inline-flex items-center gap-1 text-[10px] ${
              overdue ? 'font-semibold text-warning' : 'text-muted-foreground'
            }`}
          >
            <CalendarClock size={10} /> {overdue ? 'Overdue' : 'Due'} {due}
          </span>
        )}
        {thread.assigned_to_name && (
          <span className="inline-flex items-center gap-1 text-[10px] text-muted-foreground">
            <UserCheck size={10} /> {thread.assigned_to_name}
          </span>
        )}
      </div>
    </button>
  )
}

export default function InboxThreadList({
  threads,
  loading,
  selectedId,
  onSelect,
  filters,
  onFilters,
  programOptions,
}: {
  threads: InstThreadSummary[]
  loading: boolean
  selectedId: string | null
  onSelect: (id: string) => void
  filters: InstInboxFilters
  onFilters: (f: InstInboxFilters) => void
  programOptions: { value: string; label: string }[]
}) {
  const unassignedCount = threads.filter(t => !t.assigned_to).length

  return (
    <div className="flex h-full flex-col">
      <div className="shrink-0 border-b border-border p-3">
        <h2 className="mb-2 text-sm font-semibold text-foreground">Inbox</h2>
        <div className="flex flex-wrap gap-1.5">
          <select
            className={selectCls()}
            value={filters.filter}
            onChange={e => onFilters({ ...filters, filter: e.target.value as InstThreadFilter })}
            aria-label="Assignment filter"
          >
            {FILTER_OPTIONS.map(o => (
              <option key={o.value} value={o.value}>
                {o.value === 'unassigned' && unassignedCount > 0
                  ? `${o.label} (${unassignedCount})`
                  : o.label}
              </option>
            ))}
          </select>
          <select
            className={selectCls()}
            value={filters.reason}
            onChange={e =>
              onFilters({ ...filters, reason: e.target.value as InstInboxFilters['reason'] })
            }
            aria-label="Reason code"
          >
            <option value="all">All reasons</option>
            {REASON_OPTIONS.map(o => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
          {programOptions.length > 1 && (
            <select
              className={selectCls()}
              value={filters.program_id}
              onChange={e => onFilters({ ...filters, program_id: e.target.value })}
              aria-label="Program"
            >
              {programOptions.map(o => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          )}
          <select
            className={selectCls()}
            value={filters.state}
            onChange={e =>
              onFilters({ ...filters, state: e.target.value as InstInboxFilters['state'] })
            }
            aria-label="Status"
          >
            {STATE_OPTIONS.map(o => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="space-y-3 p-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-16" />
            ))}
          </div>
        ) : threads.length === 0 ? (
          <div className="p-6 text-center">
            <InboxIcon size={28} className="mx-auto mb-2 text-muted-foreground/50" />
            <p className="text-sm text-muted-foreground">
              {filters.filter === 'unassigned'
                ? 'No unassigned conversations. Assign one to yourself to respond.'
                : 'No conversations yet. Messages from applicants and prospects land here.'}
            </p>
          </div>
        ) : (
          threads.map(t => (
            <ThreadRow key={t.id} thread={t} selected={selectedId === t.id} onSelect={onSelect} />
          ))
        )}
      </div>
    </div>
  )
}
