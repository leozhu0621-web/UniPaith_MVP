import { useState } from 'react'
import { Bell, CalendarClock, ChevronDown, MessageSquare } from 'lucide-react'
import Badge from '../../../components/ui/Badge'
import Skeleton from '../../../components/ui/Skeleton'
import { formatRelative } from '../../../utils/format'
import type { InboxThreadSummary } from '../../../types'
import { ACTION_CONFIG, formatDue, threadEyebrow } from './actionLabels'

export interface InboxFilters {
  type: 'all' | 'human' | 'system'
  state: 'all' | 'needs_reply' | 'requested' | 'completed' | 'status_update_only'
  application_id: string
  sort: 'urgent' | 'recent' | 'action_required'
}

const STATE_OPTIONS: { value: InboxFilters['state']; label: string }[] = [
  { value: 'all', label: 'All states' },
  { value: 'needs_reply', label: 'Needs reply' },
  { value: 'requested', label: 'Requested' },
  { value: 'status_update_only', label: 'Status only' },
  { value: 'completed', label: 'Completed' },
]

const SORT_OPTIONS: { value: InboxFilters['sort']; label: string }[] = [
  { value: 'urgent', label: 'Most urgent' },
  { value: 'recent', label: 'Most recent' },
  { value: 'action_required', label: 'Most action-required' },
]

function selectCls() {
  return 'h-7 rounded-md border border-border bg-card px-2 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary'
}

function ThreadRow({
  thread,
  selected,
  onSelect,
}: {
  thread: InboxThreadSummary
  selected: boolean
  onSelect: (id: string) => void
}) {
  const action = thread.action_label ? ACTION_CONFIG[thread.action_label] : null
  const due = formatDue(thread.due_date)
  const ActionIcon = action?.icon
  return (
    <button
      onClick={() => onSelect(thread.id)}
      className={`w-full border-b border-border px-3 py-2.5 text-left transition-colors hover:bg-muted ${
        selected ? 'bg-muted' : ''
      }`}
    >
      <div className="flex items-center gap-2">
        {thread.unread && <span className="h-2 w-2 shrink-0 rounded-full bg-secondary" aria-label="Unread" />}
        <p className={`flex-1 truncate text-sm ${thread.unread ? 'font-semibold text-foreground' : 'text-foreground'}`}>
          {thread.subject || 'Conversation'}
        </p>
        <span className="shrink-0 text-[10px] text-muted-foreground">{formatRelative(thread.last_message_at)}</span>
      </div>
      <p className="mt-0.5 truncate text-[11px] text-secondary">{threadEyebrow(thread)}</p>
      <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
        {action && (
          <Badge variant={action.variant} size="sm">
            {ActionIcon && <ActionIcon size={10} />}
            {action.label}
          </Badge>
        )}
        {due && (
          <span className="inline-flex items-center gap-1 text-[10px] text-muted-foreground">
            <CalendarClock size={10} /> Due {due}
          </span>
        )}
      </div>
    </button>
  )
}

export default function InboxList({
  threads,
  loading,
  selectedId,
  onSelect,
  filters,
  onFilters,
  appOptions,
}: {
  threads: InboxThreadSummary[]
  loading: boolean
  selectedId: string | null
  onSelect: (id: string) => void
  filters: InboxFilters
  onFilters: (f: InboxFilters) => void
  appOptions: { value: string; label: string }[]
}) {
  const [systemOpen, setSystemOpen] = useState(true)

  // When showing "all", split human vs system into a collapsible group (§4.2).
  const human = threads.filter(t => t.type === 'human')
  const system = threads.filter(t => t.type === 'system')
  const splitView = filters.type === 'all' && system.length > 0 && human.length > 0

  return (
    <div className="flex h-full flex-col">
      {/* Header + filters */}
      <div className="shrink-0 border-b border-border p-3">
        <h2 className="mb-2 text-sm font-semibold text-foreground">Inbox</h2>
        <div className="flex flex-wrap gap-1.5">
          <select
            className={selectCls()}
            value={filters.type}
            onChange={e => onFilters({ ...filters, type: e.target.value as InboxFilters['type'] })}
            aria-label="Message type"
          >
            <option value="all">All messages</option>
            <option value="human">Human</option>
            <option value="system">System</option>
          </select>
          <select
            className={selectCls()}
            value={filters.state}
            onChange={e => onFilters({ ...filters, state: e.target.value as InboxFilters['state'] })}
            aria-label="Action state"
          >
            {STATE_OPTIONS.map(o => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>
          {appOptions.length > 1 && (
            <select
              className={selectCls()}
              value={filters.application_id}
              onChange={e => onFilters({ ...filters, application_id: e.target.value })}
              aria-label="Application"
            >
              {appOptions.map(o => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          )}
          <select
            className={selectCls()}
            value={filters.sort}
            onChange={e => onFilters({ ...filters, sort: e.target.value as InboxFilters['sort'] })}
            aria-label="Sort"
          >
            {SORT_OPTIONS.map(o => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>
        </div>
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="space-y-3 p-3">
            {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-16" />)}
          </div>
        ) : threads.length === 0 ? (
          <div className="p-6 text-center">
            <MessageSquare size={28} className="mx-auto mb-2 text-muted-foreground/50" />
            <p className="text-sm text-muted-foreground">
              No conversations yet. Schools will reach out as you start applications.
            </p>
          </div>
        ) : splitView ? (
          <>
            {human.map(t => (
              <ThreadRow key={t.id} thread={t} selected={selectedId === t.id} onSelect={onSelect} />
            ))}
            {/* System messages — visually separated + collapsible (§4.2) */}
            <button
              onClick={() => setSystemOpen(o => !o)}
              className="flex w-full items-center gap-1.5 bg-muted/40 px-3 py-1.5 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground"
            >
              <Bell size={11} />
              System &amp; notifications ({system.length})
              <ChevronDown size={12} className={`ml-auto transition-transform ${systemOpen ? '' : '-rotate-90'}`} />
            </button>
            {systemOpen &&
              system.map(t => (
                <div key={t.id} className="bg-muted/20">
                  <ThreadRow thread={t} selected={selectedId === t.id} onSelect={onSelect} />
                </div>
              ))}
          </>
        ) : (
          threads.map(t => (
            <ThreadRow key={t.id} thread={t} selected={selectedId === t.id} onSelect={onSelect} />
          ))
        )}
      </div>
    </div>
  )
}
