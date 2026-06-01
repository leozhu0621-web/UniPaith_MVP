import { ChevronDown } from 'lucide-react'
import Badge from '../../../components/ui/Badge'
import Skeleton from '../../../components/ui/Skeleton'
import { formatRelative } from '../../../utils/format'
import type { InstInboxThreadSummary, InstReasonCode } from '../../../types'
import { ACTION_CONFIG, formatDue } from '../../student/inbox/actionLabels'
import { REASON_CONFIG, statusLabel } from './reasonCodes'

export type InstListFilters = {
  filter: 'mine' | 'unassigned' | 'all'
  reason: InstReasonCode | 'all'
  program_id: string
}

const FILTER_TABS: { id: InstListFilters['filter']; label: string }[] = [
  { id: 'mine', label: 'Mine' },
  { id: 'unassigned', label: 'Unassigned' },
  { id: 'all', label: 'All' },
]

function selectCls() {
  return 'h-8 rounded-md border border-border bg-card px-2 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-cobalt'
}

export default function InstInboxList({
  threads,
  loading,
  selectedId,
  onSelect,
  filters,
  onFilters,
  programOptions,
  unassignedCount,
}: {
  threads: InstInboxThreadSummary[]
  loading: boolean
  selectedId: string | null
  onSelect: (id: string) => void
  filters: InstListFilters
  onFilters: (f: InstListFilters) => void
  programOptions: { value: string; label: string }[]
  unassignedCount: number
}) {
  return (
    <div className="flex h-full w-80 shrink-0 flex-col border-r border-border bg-card">
      <div className="border-b border-border px-3 py-3">
        <p className="text-eyebrow uppercase text-cobalt font-semibold">Inbox</p>
        <div className="mt-2 flex gap-1">
          {FILTER_TABS.map(tab => (
            <button
              key={tab.id}
              type="button"
              onClick={() => onFilters({ ...filters, filter: tab.id })}
              className={`rounded-md px-2 py-1 text-xs font-medium transition-colors ${
                filters.filter === tab.id
                  ? 'bg-cobalt text-white'
                  : 'text-muted-foreground hover:bg-muted'
              }`}
            >
              {tab.label}
              {tab.id === 'unassigned' && unassignedCount > 0 && (
                <span className="ml-1 rounded-full bg-warning/20 px-1.5 text-[10px] text-warning">
                  {unassignedCount}
                </span>
              )}
            </button>
          ))}
        </div>
        <div className="mt-2 flex gap-2">
          <div className="relative flex-1">
            <select
              className={`${selectCls()} w-full appearance-none pr-6`}
              value={filters.reason}
              onChange={e => onFilters({ ...filters, reason: e.target.value as InstListFilters['reason'] })}
              aria-label="Reason filter"
            >
              <option value="all">All reasons</option>
              {Object.entries(REASON_CONFIG).map(([code, cfg]) => (
                <option key={code} value={code}>
                  {cfg.label}
                </option>
              ))}
            </select>
            <ChevronDown size={12} className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground" />
          </div>
          <div className="relative flex-1">
            <select
              className={`${selectCls()} w-full appearance-none pr-6`}
              value={filters.program_id}
              onChange={e => onFilters({ ...filters, program_id: e.target.value })}
              aria-label="Program filter"
            >
              <option value="all">All programs</option>
              {programOptions.map(o => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
            <ChevronDown size={12} className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground" />
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="space-y-2 p-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-16" />
            ))}
          </div>
        ) : threads.length === 0 ? (
          <p className="px-4 py-10 text-center text-sm text-muted-foreground">
            Messages from applicants and prospects land here.
          </p>
        ) : (
          threads.map(t => {
            const action = t.action_label ? ACTION_CONFIG[t.action_label] : null
            const ActionIcon = action?.icon
            const due = formatDue(t.due_date)
            const overdue =
              t.status === 'awaiting_us' && t.due_date && new Date(t.due_date) < new Date()
            return (
              <button
                key={t.id}
                type="button"
                onClick={() => onSelect(t.id)}
                className={`w-full border-b border-divider px-3 py-2.5 text-left transition-colors hover:bg-muted ${
                  selectedId === t.id ? 'bg-muted' : ''
                } ${overdue ? 'border-l-2 border-l-warning bg-warning/5' : ''}`}
              >
                <div className="flex items-center gap-2">
                  {t.unread_count > 0 && (
                    <span className="h-2 w-2 shrink-0 rounded-full bg-cobalt" aria-label="Unread" />
                  )}
                  <p className="flex-1 truncate text-sm font-medium text-foreground">
                    {t.student_ref.name}
                  </p>
                  <span className="text-[10px] text-muted-foreground">
                    {formatRelative(t.last_message_at)}
                  </span>
                </div>
                <p className="mt-0.5 truncate text-[11px] text-muted-foreground">
                  {t.program_ref?.name || t.subject || 'Inquiry'}
                </p>
                <div className="mt-1 flex flex-wrap items-center gap-1">
                  {action && (
                    <Badge variant={action.variant} size="sm">
                      {ActionIcon && <ActionIcon size={10} />}
                      {action.label}
                    </Badge>
                  )}
                  <span className="text-[10px] text-muted-foreground">{statusLabel(t.status)}</span>
                  {due && (
                    <span className="text-[10px] text-muted-foreground">Due {due}</span>
                  )}
                </div>
              </button>
            )
          })
        )}
      </div>
    </div>
  )
}
