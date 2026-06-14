import { useState, useMemo } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { PageContainer, PageHeader } from '../../components/student/density'
import {
  startOfMonth, endOfMonth, startOfWeek, endOfWeek, eachDayOfInterval,
  format, addMonths, subMonths, addWeeks, subWeeks, isSameDay, isToday, parseISO,
  setHours, setMinutes, differenceInMinutes, addMinutes, differenceInDays,
} from 'date-fns'
import {
  ChevronLeft, ChevronRight, Clock, FileText, Mic, Video,
  AlertTriangle, Plus, MapPin, Check, RotateCcw, Bell, Users, Wallet,
  Palette, Mail, ExternalLink, X as XIcon, CalendarClock,
} from 'lucide-react'
import {
  getCalendar, createReminder, createWorkBlock, patchCalendarItem,
  type CalendarItem, type CalendarItemType,
} from '../../api/calendar'
import { declineInterview, getMyInterviews } from '../../api/interviews'
import InterviewRespondPanel from './interviews/InterviewRespondPanel'
import type { Interview } from '../../types'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Modal from '../../components/ui/Modal'
import Input from '../../components/ui/Input'
import Select from '../../components/ui/Select'
import EmptyState from '../../components/ui/EmptyState'
import QueryError from '../../components/ui/QueryError'
import { SkeletonCard } from '../../components/ui/Skeleton'

type ViewMode = 'month' | 'week' | 'agenda'
type TypeBucket = 'all' | 'interviews' | 'deadlines' | 'events' | 'reminders' | 'work_blocks'
type DotColor = 'cobalt' | 'warning' | 'error' | 'slate'

// Spec 16 §4 + §9 — type → label / brand color / icon / filter bucket.
// Colors: cobalt (live interview, visits, info), warning (recorded/portfolio/
// audition windows), error (all deadlines), slate=text-mut (student-created).
// No gold on calendar items (§9: gold is the brand mark, not for time).
const TYPE_META: Record<CalendarItemType, { label: string; color: DotColor; icon: typeof Clock; bucket: TypeBucket }> = {
  interview_live: { label: 'Live interview', color: 'cobalt', icon: Video, bucket: 'interviews' },
  interview_recorded_window: { label: 'Recorded interview window', color: 'warning', icon: Mic, bucket: 'interviews' },
  interview_submission_deadline: { label: 'Interview submission due', color: 'warning', icon: Mic, bucket: 'interviews' },
  portfolio_review: { label: 'Portfolio review', color: 'warning', icon: Palette, bucket: 'interviews' },
  audition: { label: 'Audition', color: 'warning', icon: Mic, bucket: 'interviews' },
  campus_visit: { label: 'Campus visit', color: 'cobalt', icon: MapPin, bucket: 'events' },
  info_session: { label: 'Info session', color: 'cobalt', icon: Users, bucket: 'events' },
  submission_deadline: { label: 'Submission deadline', color: 'error', icon: FileText, bucket: 'deadlines' },
  document_deadline: { label: 'Document deadline', color: 'error', icon: FileText, bucket: 'deadlines' },
  recommendation_deadline: { label: 'Recommendation deadline', color: 'error', icon: Mail, bucket: 'deadlines' },
  deposit_deadline: { label: 'Deposit deadline', color: 'error', icon: Wallet, bucket: 'deadlines' },
  reminder: { label: 'Reminder', color: 'slate', icon: Bell, bucket: 'reminders' },
  work_block: { label: 'Work block', color: 'slate', icon: Clock, bucket: 'work_blocks' },
}

const DOT_BG: Record<DotColor, string> = {
  cobalt: 'bg-secondary', warning: 'bg-warning', error: 'bg-error', slate: 'bg-muted-foreground',
}
const ICON_TEXT: Record<DotColor, string> = {
  cobalt: 'text-secondary', warning: 'text-warning', error: 'text-error', slate: 'text-muted-foreground',
}
const ICON_SOFT_BG: Record<DotColor, string> = {
  cobalt: 'bg-secondary/10', warning: 'bg-warning-soft', error: 'bg-error-soft', slate: 'bg-muted',
}

const TYPE_BUCKETS: { value: TypeBucket; label: string }[] = [
  { value: 'all', label: 'All item types' },
  { value: 'interviews', label: 'Interviews' },
  { value: 'deadlines', label: 'Deadlines' },
  { value: 'events', label: 'Events' },
  { value: 'reminders', label: 'Reminders' },
  { value: 'work_blocks', label: 'Work blocks' },
]

const WORK_CATEGORIES = [
  { value: 'essay_draft', label: 'Essay drafting' },
  { value: 'interview_prep', label: 'Interview prep' },
  { value: 'research', label: 'Program research' },
  { value: 'general', label: 'General prep' },
]

const WEEK_GRID_START_HOUR = 7
const WEEK_GRID_END_HOUR = 21 // 9 PM boundary
const WEEK_HOUR_PX = 44
const WEEK_GRID_HEIGHT = (WEEK_GRID_END_HOUR - WEEK_GRID_START_HOUR) * WEEK_HOUR_PX
const WEEK_GRID_MINUTES = (WEEK_GRID_END_HOUR - WEEK_GRID_START_HOUR) * 60
const DEADLINE_TYPES: CalendarItemType[] = [
  'submission_deadline', 'document_deadline', 'recommendation_deadline',
  'interview_submission_deadline', 'deposit_deadline',
]

const isOverdue = (i: CalendarItem) => i.status === 'overdue'
const isDone = (i: CalendarItem) => i.status === 'completed' || i.status === 'cancelled'

/** Compute the effective dot color for an item, applying urgency to deadlines. */
function itemColor(item: CalendarItem): DotColor {
  if (isOverdue(item)) return 'error'
  const base = TYPE_META[item.type].color
  if (base !== 'error') return base
  // deadline items: compute urgency from days until start_at
  const daysLeft = differenceInDays(parseISO(item.start_at), new Date())
  if (daysLeft < 0) return 'error'
  if (daysLeft <= 7) return 'error'
  if (daysLeft <= 30) return 'warning'
  return 'slate'
}
// A deadline-like item the student can mark complete (Spec 16 §5).
const completable = (i: CalendarItem) =>
  ['submission_deadline', 'document_deadline', 'recommendation_deadline',
   'interview_submission_deadline', 'deposit_deadline', 'reminder', 'work_block'].includes(i.type)

// datetime-local <-> ISO (UTC). Spec 16 §13: store UTC, render local.
const toISO = (local: string) => (local ? new Date(local).toISOString() : '')

export default function CalendarPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [searchParams, setSearchParams] = useSearchParams()

  const viewParam = searchParams.get('view') as ViewMode | null
  const isMobile = typeof window !== 'undefined' && window.matchMedia('(max-width: 1023px)').matches
  const [view, setView] = useState<ViewMode>(viewParam ?? (isMobile ? 'agenda' : 'month'))
  const [currentMonth, setCurrentMonth] = useState(new Date())
  const [currentWeek, setCurrentWeek] = useState(new Date())
  const [selectedDay, setSelectedDay] = useState<Date | null>(null)
  const [appFilter, setAppFilter] = useState<string>('all')
  const [typeFilter, setTypeFilter] = useState<TypeBucket>('all')
  const [showReminder, setShowReminder] = useState(false)
  const [showWorkBlock, setShowWorkBlock] = useState(false)
  const [detailItem, setDetailItem] = useState<CalendarItem | null>(null)

  // Fetch a wide window once; navigate/filter client-side (smooth, no refetch).
  const range = useMemo(() => {
    const from = subMonths(new Date(), 6)
    const to = addMonths(new Date(), 18)
    return { from: from.toISOString(), to: to.toISOString() }
  }, [])

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['calendar', range.from, range.to],
    queryFn: () => getCalendar(range),
  })
  // Drop items we can't safely render: an unknown type (no TYPE_META entry) or a
  // missing/invalid start_at would throw deep in the grid. Skip them rather than
  // crash the whole timeline.
  const items: CalendarItem[] = useMemo(
    () =>
      (data ?? []).filter(
        i => !!TYPE_META[i.type] && !!i.start_at && !isNaN(parseISO(i.start_at).getTime()),
      ),
    [data],
  )

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['calendar'] })

  const patchMut = useMutation({
    mutationFn: ({ id, body }: { id: string; body: Parameters<typeof patchCalendarItem>[1] }) =>
      patchCalendarItem(id, body),
    onSuccess: updated => {
      invalidate()
      setDetailItem(prev => (prev && prev.id === updated.id ? updated : prev))
    },
  })

  const declineMut = useMutation({
    mutationFn: (interviewId: string) => declineInterview(interviewId),
    onSuccess: () => {
      invalidate()
      setDetailItem(null)
    },
  })

  // Applications present in the timeline → filter options.
  const appOptions = useMemo(() => {
    const map = new Map<string, string>()
    items.forEach(i => {
      if (i.application_id) map.set(i.application_id, i.institution_name || i.subtitle || 'Application')
    })
    return [{ value: 'all', label: 'All applications' },
      ...Array.from(map, ([value, label]) => ({ value, label }))]
  }, [items])

  const switchView = (v: ViewMode) => {
    setView(v)
    setSelectedDay(null)
    setSearchParams({ view: v })
  }

  const filtered = useMemo(() => items.filter(i => {
    if (appFilter !== 'all' && i.application_id !== appFilter) return false
    if (typeFilter !== 'all' && TYPE_META[i.type]?.bucket !== typeFilter) return false
    return true
  }), [items, appFilter, typeFilter])

  const overdueCount = filtered.filter(isOverdue).length
  const hasActiveFilter = appFilter !== 'all' || typeFilter !== 'all'
  const clearFilters = () => { setAppFilter('all'); setTypeFilter('all') }

  // ── Loading ──
  if (isLoading) {
    return (
      <PageContainer className="space-y-4">
        {Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} />)}
      </PageContainer>
    )
  }

  // ── Error ── distinguish a failed fetch from an empty (but successful) timeline.
  if (isError) {
    return (
      <PageContainer>
        <QueryError detail="We couldn't load your timeline." onRetry={() => refetch()} />
      </PageContainer>
    )
  }

  // Month grid scaffold
  const monthStart = startOfMonth(currentMonth)
  const days = eachDayOfInterval({ start: monthStart, end: endOfMonth(currentMonth) })
  const startDow = monthStart.getDay()
  const padDays = startDow === 0 ? 6 : startDow - 1

  // Week scaffold
  const weekStart = startOfWeek(currentWeek, { weekStartsOn: 1 })
  const weekEnd = endOfWeek(currentWeek, { weekStartsOn: 1 })
  const weekDays = eachDayOfInterval({ start: weekStart, end: weekEnd })

  const itemsOn = (day: Date) => filtered.filter(i => isSameDay(parseISO(i.start_at), day))

  return (
    <PageContainer>
      {/* Room header — consistent with the other My Space rooms (eyebrow = surface). */}
      <PageHeader
        eyebrow="My Space"
        title="Calendar"
        count={filtered.length}
        sub="Your admissions timeline — deadlines, interviews, reminders, and work blocks"
        actions={
          <>
            <Button size="sm" variant="secondary" onClick={() => setShowReminder(true)}>
              <Plus size={14} className="mr-1" /> Add reminder
            </Button>
            <Button size="sm" variant="secondary" onClick={() => setShowWorkBlock(true)}>
              <Plus size={14} className="mr-1" /> Add work block
            </Button>
          </>
        }
      />

      {/* Controls: view switcher + filters */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <div className="inline-flex items-center gap-1 bg-muted rounded-lg p-0.5">
          {(['month', 'week', 'agenda'] as ViewMode[]).map(v => (
            <button
              key={v}
              onClick={() => switchView(v)}
              className={`px-3 py-1.5 text-sm rounded-md transition-colors capitalize ${
                view === v ? 'bg-card text-foreground shadow-sm font-semibold' : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              {v}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2">
          <div className="w-44">
            <Select value={appFilter} onChange={e => setAppFilter(e.target.value)} options={appOptions} />
          </div>
          <div className="w-40">
            <Select value={typeFilter} onChange={e => setTypeFilter(e.target.value as TypeBucket)} options={TYPE_BUCKETS} />
          </div>
        </div>
      </div>

      {/* Overdue banner (Spec 16 §7 — highlight in red across all views) */}
      {overdueCount > 0 && (
        <div className="flex items-center gap-2.5 bg-error-soft rounded-lg px-4 py-2.5 mb-4">
          <AlertTriangle size={16} className="text-error flex-shrink-0" />
          <p className="text-sm text-error font-medium">
            {overdueCount} item{overdueCount !== 1 ? 's' : ''} overdue
          </p>
        </div>
      )}

      {/* Smart empty state — replaces the blank month/week/agenda grids when
          there's nothing to show, so the room never reads as abandoned. */}
      {filtered.length === 0 ? (
        <div className="animate-fade-in">
          <EmptyState
            icon={<CalendarClock size={40} />}
            title={hasActiveFilter ? 'Nothing matches these filters' : 'Your calendar is clear'}
            description={
              hasActiveFilter
                ? 'No items match the current filters. Clear them to see your full timeline.'
                : 'Deadlines and interviews land here as you save and apply to programs. Add a reminder or block off study time to get a head start.'
            }
            action={
              hasActiveFilter
                ? { label: 'Clear filters', onClick: clearFilters }
                : { label: 'Add a reminder', onClick: () => setShowReminder(true) }
            }
          />
        </div>
      ) : (
      <>
      {/* ── MONTH ── */}
      {view === 'month' && (
        <>
          <div className="flex items-center justify-end gap-3 mb-4">
            <button onClick={() => setCurrentMonth(m => subMonths(m, 1))} className="p-1.5 hover:bg-muted rounded transition-colors" aria-label="Previous month"><ChevronLeft size={18} /></button>
            <span className="text-sm font-semibold w-36 text-center text-foreground">{format(currentMonth, 'MMMM yyyy')}</span>
            <button onClick={() => setCurrentMonth(m => addMonths(m, 1))} className="p-1.5 hover:bg-muted rounded transition-colors" aria-label="Next month"><ChevronRight size={18} /></button>
          </div>
          <div className="grid grid-cols-7 gap-px bg-muted rounded-lg overflow-hidden border border-border">
            {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map(d => (
              <div key={d} className="bg-background py-2 text-center text-xs font-semibold text-muted-foreground">{d}</div>
            ))}
            {Array.from({ length: padDays }).map((_, i) => <div key={`pad-${i}`} className="bg-card min-h-[92px]" />)}
            {days.map(day => {
              const dayItems = itemsOn(day)
              const today = isToday(day)
              const selected = selectedDay && isSameDay(selectedDay, day)
              return (
                <button
                  key={day.toISOString()}
                  onClick={() => setSelectedDay(day)}
                  className={`bg-card min-h-[92px] p-1.5 text-left align-top hover:bg-background transition-colors ${selected ? 'ring-2 ring-inset ring-secondary' : ''}`}
                >
                  <span className={`inline-block text-xs ${today ? 'font-bold text-secondary border-b-2 border-secondary' : 'text-muted-foreground'}`}>
                    {format(day, 'd')}
                  </span>
                  <div className="mt-1 space-y-0.5">
                    {dayItems.slice(0, 3).map(i => {
                      const c = itemColor(i)
                      return (
                        <div key={i.id} className={`flex items-center gap-1 ${isDone(i) ? 'opacity-50' : ''}`}>
                          <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${DOT_BG[c]}`} />
                          <span className={`text-[10px] truncate ${isDone(i) ? 'line-through text-muted-foreground' : 'text-foreground'}`}>{i.title}</span>
                        </div>
                      )
                    })}
                    {dayItems.length > 3 && <div className="text-[10px] text-muted-foreground pl-2.5">+{dayItems.length - 3} more</div>}
                  </div>
                </button>
              )
            })}
          </div>
          {/* Day detail panel (Spec 16 §3 — click date → day detail) */}
          {selectedDay && (
            <div className="mt-5">
              <div className="flex items-center justify-between mb-2">
                <h2 className="text-h3 text-foreground">{format(selectedDay, 'EEEE, MMMM d')}</h2>
                <button onClick={() => setSelectedDay(null)} className="text-muted-foreground hover:text-foreground p-1" aria-label="Close day"><XIcon size={16} /></button>
              </div>
              <DayList items={itemsOn(selectedDay)} onOpen={setDetailItem} />
            </div>
          )}
        </>
      )}

      {/* ── WEEK (Spec 16 §3: hour grid 7am–9pm) ── */}
      {view === 'week' && (
        <>
          <div className="flex items-center justify-end gap-3 mb-4">
            <button onClick={() => setCurrentWeek(w => subWeeks(w, 1))} className="p-1.5 hover:bg-muted rounded transition-colors" aria-label="Previous week"><ChevronLeft size={18} /></button>
            <span className="text-sm font-semibold text-center text-foreground">{format(weekStart, 'MMM d')} — {format(weekEnd, 'MMM d, yyyy')}</span>
            <button onClick={() => setCurrentWeek(w => addWeeks(w, 1))} className="p-1.5 hover:bg-muted rounded transition-colors" aria-label="Next week"><ChevronRight size={18} /></button>
          </div>
          <WeekHourGrid weekDays={weekDays} itemsOn={itemsOn} onOpen={setDetailItem} />
        </>
      )}

      {/* ── AGENDA ── */}
      {view === 'agenda' && (
        <AgendaView items={filtered} hasActiveFilter={hasActiveFilter} onClearFilters={clearFilters} onOpen={setDetailItem} onDiscover={() => navigate('/s/explore')} />
      )}
      </>
      )}

      {/* Item detail + actions */}
      <ItemDetailModal
        item={detailItem}
        onClose={() => setDetailItem(null)}
        onNavigate={link => { setDetailItem(null); navigate(link) }}
        onPatch={(id, body) => patchMut.mutate({ id, body })}
        onDecline={id => declineMut.mutate(id)}
        patching={patchMut.isPending || declineMut.isPending}
      />

      <ReminderModal
        open={showReminder}
        apps={appOptions}
        onClose={() => setShowReminder(false)}
        onCreated={() => { setShowReminder(false); invalidate() }}
      />
      <WorkBlockModal
        open={showWorkBlock}
        apps={appOptions}
        onClose={() => setShowWorkBlock(false)}
        onCreated={() => { setShowWorkBlock(false); invalidate() }}
      />
    </PageContainer>
  )
}

// ── Week hour grid (Spec 16 §3: 7am–9pm) ─────────────────────────────────
function weekItemLayout(item: CalendarItem, day: Date): { top: number; height: number } | 'allday' | null {
  const start = parseISO(item.start_at)
  if (!isSameDay(start, day)) return null

  const gridStart = setMinutes(setHours(day, WEEK_GRID_START_HOUR), 0)
  const defaultEnd = item.end_at
    ? parseISO(item.end_at)
    : addMinutes(start, item.type === 'work_block' ? 60 : DEADLINE_TYPES.includes(item.type) ? 30 : 45)

  const startMins = differenceInMinutes(start, gridStart)
  const endMins = differenceInMinutes(defaultEnd, gridStart)

  // Deadlines stored as end-of-day UTC often fall outside the visible grid in local time.
  if (DEADLINE_TYPES.includes(item.type) && (startMins >= WEEK_GRID_MINUTES || startMins < 0)) {
    return 'allday'
  }
  if (startMins >= WEEK_GRID_MINUTES || endMins <= 0) return 'allday'

  const clampedStart = Math.max(0, startMins)
  const clampedEnd = Math.min(WEEK_GRID_MINUTES, Math.max(endMins, clampedStart + 30))
  const top = (clampedStart / WEEK_GRID_MINUTES) * WEEK_GRID_HEIGHT
  const height = Math.max(22, ((clampedEnd - clampedStart) / WEEK_GRID_MINUTES) * WEEK_GRID_HEIGHT)
  return { top, height }
}

function WeekHourGrid({ weekDays, itemsOn, onOpen }: {
  weekDays: Date[]
  itemsOn: (day: Date) => CalendarItem[]
  onOpen: (i: CalendarItem) => void
}) {
  const hourLabels = Array.from(
    { length: WEEK_GRID_END_HOUR - WEEK_GRID_START_HOUR },
    (_, i) => WEEK_GRID_START_HOUR + i,
  )
  const hasAllDay = weekDays.some(day =>
    itemsOn(day).some(i => weekItemLayout(i, day) === 'allday'),
  )

  return (
    <div className="overflow-x-auto rounded-lg border border-border bg-card">
      <div className="min-w-[720px]">
        {/* Day headers */}
        <div className="grid grid-cols-[48px_repeat(7,1fr)] border-b border-border bg-background">
          <div />
          {weekDays.map(day => {
            const today = isToday(day)
            return (
              <div key={day.toISOString()} className={`py-2 text-center text-xs font-semibold ${today ? 'text-secondary' : 'text-muted-foreground'}`}>
                <span className={today ? 'border-b-2 border-secondary pb-0.5' : ''}>{format(day, 'EEE d')}</span>
              </div>
            )
          })}
        </div>

        {/* All-day / deadline strip */}
        {hasAllDay && (
          <div className="grid grid-cols-[48px_repeat(7,1fr)] border-b border-border min-h-[36px]">
            <div className="text-[10px] text-muted-foreground px-1 py-1 flex items-start justify-end">All day</div>
            {weekDays.map(day => (
              <div key={`allday-${day.toISOString()}`} className="border-l border-border p-0.5 space-y-0.5">
                {itemsOn(day).filter(i => weekItemLayout(i, day) === 'allday').map(i => {
                  const c = itemColor(i)
                  return (
                    <button
                      key={i.id}
                      onClick={() => onOpen(i)}
                      className={`w-full text-left rounded px-1 py-0.5 text-[10px] truncate hover:brightness-95 ${ICON_SOFT_BG[c]} ${isDone(i) ? 'opacity-50 line-through' : ''} text-foreground`}
                    >
                      {i.title}
                    </button>
                  )
                })}
              </div>
            ))}
          </div>
        )}

        {/* Hour grid */}
        <div className="grid grid-cols-[48px_repeat(7,1fr)]">
          <div className="relative" style={{ height: WEEK_GRID_HEIGHT }}>
            {hourLabels.map(h => (
              <div
                key={h}
                className="absolute right-1 -translate-y-1/2 text-[10px] text-muted-foreground tabular-nums"
                style={{ top: (h - WEEK_GRID_START_HOUR) * WEEK_HOUR_PX }}
              >
                {format(setMinutes(setHours(new Date(), h), 0), 'ha')}
              </div>
            ))}
          </div>
          {weekDays.map(day => {
            const today = isToday(day)
            const timed = itemsOn(day)
              .map(i => ({ item: i, layout: weekItemLayout(i, day) }))
              .filter((x): x is { item: CalendarItem; layout: { top: number; height: number } } =>
                x.layout !== null && x.layout !== 'allday',
              )
            return (
              <div
                key={day.toISOString()}
                className={`relative border-l border-border ${today ? 'bg-secondary/[0.03]' : ''}`}
                style={{ height: WEEK_GRID_HEIGHT }}
              >
                {hourLabels.map(h => (
                  <div
                    key={h}
                    className="absolute inset-x-0 border-t border-border/60"
                    style={{ top: (h - WEEK_GRID_START_HOUR) * WEEK_HOUR_PX }}
                  />
                ))}
                {timed.map(({ item, layout }) => {
                  const c = itemColor(item)
                  return (
                    <button
                      key={item.id}
                      onClick={() => onOpen(item)}
                      style={{ top: layout.top, height: layout.height }}
                      className={`absolute left-0.5 right-0.5 z-10 overflow-hidden rounded px-1 py-0.5 text-left transition-colors hover:brightness-95 ${ICON_SOFT_BG[c]} ${isDone(item) ? 'opacity-50' : ''}`}
                    >
                      <p className={`text-[10px] font-medium leading-tight truncate ${isDone(item) ? 'line-through' : ''} text-foreground`}>
                        {item.title}
                      </p>
                      <p className="text-[9px] text-muted-foreground truncate">
                        {format(parseISO(item.start_at), 'h:mm a')}
                        {item.end_at ? ` – ${format(parseISO(item.end_at), 'h:mm a')}` : ''}
                      </p>
                    </button>
                  )
                })}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

// ── Agenda view ──────────────────────────────────────────────────────────
function AgendaView({ items, hasActiveFilter, onClearFilters, onOpen, onDiscover }: {
  items: CalendarItem[]
  hasActiveFilter: boolean
  onClearFilters: () => void
  onOpen: (i: CalendarItem) => void
  onDiscover: () => void
}) {
  const upcoming = items.filter(i => !isDone(i))
  const grouped = useMemo(() => {
    const g: Record<string, CalendarItem[]> = {}
    items.forEach(i => {
      const key = format(parseISO(i.start_at), 'EEEE, MMMM d, yyyy')
      ;(g[key] ||= []).push(i)
    })
    return g
  }, [items])

  if (items.length === 0) {
    return hasActiveFilter ? (
      <EmptyState
        icon={<CalendarClock size={48} />}
        title="No items match"
        description="No calendar items match the current filters."
        action={{ label: 'Clear filters?', onClick: onClearFilters }}
      />
    ) : (
      <EmptyState
        icon={<CalendarClock size={48} />}
        title="Your calendar is clear"
        description="Set a work block or RSVP to an event to get started."
        action={{ label: 'Discover programs', onClick: onDiscover }}
      />
    )
  }

  return (
    <div className="stagger-list space-y-7">
      {Object.entries(grouped).map(([day, dayItems]) => (
        <div key={day}>
          <h2 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2.5">{day}</h2>
          <div className="space-y-2">
            {dayItems.map(i => <AgendaRow key={i.id} item={i} onOpen={onOpen} />)}
          </div>
        </div>
      ))}
      <p className="text-xs text-muted-foreground pt-2">{upcoming.length} upcoming item{upcoming.length !== 1 ? 's' : ''}</p>
    </div>
  )
}

function AgendaRow({ item, onOpen }: { item: CalendarItem; onOpen: (i: CalendarItem) => void }) {
  const meta = TYPE_META[item.type]
  const c = itemColor(item)
  const Icon = meta.icon
  return (
    <button onClick={() => onOpen(item)} className="w-full text-left group">
      <Card pad={false} className="flex items-start gap-3 p-3.5 group-hover:shadow-raised transition-shadow">
        <div className={`w-9 h-9 rounded-full ${ICON_SOFT_BG[c]} flex items-center justify-center flex-shrink-0`}>
          <Icon size={17} className={ICON_TEXT[c]} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <p className={`text-sm font-medium text-foreground ${isDone(item) ? 'line-through opacity-60' : ''}`}>{item.title}</p>
            <StatusBadge item={item} />
          </div>
          <p className="text-xs text-muted-foreground mt-0.5">
            {format(parseISO(item.start_at), 'h:mm a')}
            {item.end_at ? ` – ${format(parseISO(item.end_at), 'h:mm a')}` : ''}
            {' · '}{meta.label}
          </p>
          {(item.subtitle || item.location || item.meeting_link) && (
            <p className="text-xs text-muted-foreground/80 mt-0.5 truncate flex items-center gap-1">
              {item.meeting_link && <Video size={11} />}
              {item.location && <MapPin size={11} />}
              {item.subtitle || item.location || item.meeting_link}
            </p>
          )}
        </div>
      </Card>
    </button>
  )
}

// Day list (month-view day panel) — compact rows.
function DayList({ items, onOpen }: { items: CalendarItem[]; onOpen: (i: CalendarItem) => void }) {
  if (items.length === 0) return <p className="text-sm text-muted-foreground py-4">Nothing scheduled this day.</p>
  return (
    <div className="space-y-2">
      {items.sort((a, b) => +parseISO(a.start_at) - +parseISO(b.start_at)).map(i => <AgendaRow key={i.id} item={i} onOpen={onOpen} />)}
    </div>
  )
}

function StatusBadge({ item }: { item: CalendarItem }) {
  if (item.status === 'overdue') return <Badge variant="danger"><AlertTriangle size={11} /> Overdue</Badge>
  if (item.status === 'completed') return <Badge variant="success"><Check size={11} /> Done</Badge>
  if (item.status === 'cancelled') return <Badge variant="neutral">Cancelled</Badge>
  return null
}

// ── Item detail + actions modal (Spec 16 §5) ──────────────────────────────
function ItemDetailModal({ item, onClose, onNavigate, onPatch, onDecline, patching }: {
  item: CalendarItem | null
  onClose: () => void
  onNavigate: (link: string) => void
  onPatch: (id: string, body: Parameters<typeof patchCalendarItem>[1]) => void
  onDecline: (interviewId: string) => void
  patching: boolean
}) {
  const [confirmUrl, setConfirmUrl] = useState('')
  const interviewsQ = useQuery({
    queryKey: ['interviews'],
    queryFn: getMyInterviews,
    enabled: !!item?.interview_id,
  })
  const interview: Interview | null = useMemo(() => {
    if (!item?.interview_id) return null
    const found = (interviewsQ.data ?? []).find(i => i.id === item.interview_id)
    if (found) return found
    // Fallback while interviews load — enough for slot labels from calendar payload.
    if (item.proposed_times?.length) {
      return {
        id: item.interview_id,
        application_id: item.application_id || '',
        applicant: { student_id: null, name: '' },
        program: { id: null, name: item.subtitle || '' },
        interviewer_id: null,
        interview_type: item.type === 'interview_recorded_window' ? 'recorded_async' : 'live',
        status: item.interview_status || 'proposed',
        async_expired: false,
        proposed_times: item.proposed_times,
        proposed_slots: item.proposed_times,
        confirmed_time: null,
        scheduled_at: null,
        duration_minutes: 30,
        location: item.location,
        meeting_link: item.meeting_link,
        location_or_link: item.meeting_link || item.location,
        async_window_end: null,
        recording_url: null,
        notes_to_student: item.notes,
        recommendation: null,
        scores: [],
        created_at: null,
      }
    }
    return null
  }, [interviewsQ.data, item])

  if (!item) return null
  const meta = TYPE_META[item.type]
  const c = itemColor(item)
  const Icon = meta.icon

  return (
    <Modal isOpen={!!item} onClose={onClose} title={item.title}>
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <div className={`w-9 h-9 rounded-full ${ICON_SOFT_BG[c]} flex items-center justify-center flex-shrink-0`}>
            <Icon size={18} className={ICON_TEXT[c]} />
          </div>
          <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">{meta.label}</p>
          <div className="ml-auto"><StatusBadge item={item} /></div>
        </div>

        <dl className="space-y-1.5 text-sm">
          <Row label="When">
            {format(parseISO(item.start_at), 'EEE, MMM d · h:mm a')}
            {item.end_at ? ` – ${format(parseISO(item.end_at), 'h:mm a')}` : ''}
          </Row>
          {item.subtitle && <Row label="Where">{item.subtitle}</Row>}
          {item.location && <Row label="Location">{item.location}</Row>}
          {item.meeting_link && (
            <Row label="Link">
              <a href={item.meeting_link} target="_blank" rel="noreferrer" className="text-secondary hover:underline inline-flex items-center gap-1">
                Join <ExternalLink size={12} />
              </a>
            </Row>
          )}
          {item.recommender_name && <Row label="Recommender">{item.recommender_name}</Row>}
          {item.notes && <Row label="Notes">{item.notes}</Row>}
          {item.confirmation_url && (
            <Row label="Confirmation">
              <a href={item.confirmation_url} target="_blank" rel="noreferrer" className="text-secondary hover:underline inline-flex items-center gap-1">
                View <ExternalLink size={12} />
              </a>
            </Row>
          )}
        </dl>

        {/* Attach off-platform confirmation (Spec 16 §5) */}
        {!item.confirmation_url && completable(item) && (
          <div className="flex items-end gap-2">
            <div className="flex-1">
              <Input
                label="Attach confirmation (link)"
                placeholder="https://…"
                value={confirmUrl}
                onChange={e => setConfirmUrl(e.target.value)}
              />
            </div>
            <Button size="sm" variant="secondary" disabled={!confirmUrl || patching}
              onClick={() => { onPatch(item.id, { confirmation_url: confirmUrl }); setConfirmUrl('') }}>
              Attach
            </Button>
          </div>
        )}

        {interview && item.interview_id && (
          <InterviewRespondPanel
            interview={interview}
            compact
            onUpdated={onClose}
          />
        )}

        {/* Actions */}
        <div className="flex flex-wrap gap-2 pt-1">
          {item.link && (
            <Button size="sm" variant="secondary" onClick={() => onNavigate(item.link!)}>
              <ExternalLink size={13} className="mr-1" /> Open application
            </Button>
          )}
          {completable(item) && !isDone(item) && !item.interview_id && (
            <Button size="sm" variant="secondary" disabled={patching}
              onClick={() => onPatch(item.id, { status: 'completed' })}>
              <Check size={13} className="mr-1" /> Mark complete
            </Button>
          )}
          {item.can_decline && item.interview_id && !isDone(item) && (
            <Button size="sm" variant="danger" disabled={patching}
              onClick={() => onDecline(item.interview_id!)}>
              <XIcon size={13} className="mr-1" /> Decline
            </Button>
          )}
          {item.status === 'completed' && (
            <Button size="sm" variant="ghost" disabled={patching}
              onClick={() => onPatch(item.id, { status: 'scheduled' })}>
              <RotateCcw size={13} className="mr-1" /> Reopen
            </Button>
          )}
        </div>
      </div>
    </Modal>
  )
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex gap-3">
      <dt className="text-muted-foreground w-24 flex-shrink-0">{label}</dt>
      <dd className="text-foreground min-w-0">{children}</dd>
    </div>
  )
}

// ── Create modals ──────────────────────────────────────────────────────────
function ReminderModal({ open, apps, onClose, onCreated }: {
  open: boolean
  apps: { value: string; label: string }[]
  onClose: () => void
  onCreated: () => void
}) {
  const [form, setForm] = useState({ title: '', start: '', notes: '', app: 'all' })
  const mut = useMutation({
    mutationFn: () => createReminder({
      title: form.title,
      start_at: toISO(form.start),
      notes: form.notes || null,
      application_id: form.app !== 'all' ? form.app : null,
    }),
    onSuccess: () => { setForm({ title: '', start: '', notes: '', app: 'all' }); onCreated() },
  })
  return (
    <Modal isOpen={open} onClose={onClose} title="Add reminder">
      <div className="space-y-3">
        <Input label="Title" placeholder="e.g. Email recommender" value={form.title} onChange={e => setForm(f => ({ ...f, title: e.target.value }))} />
        <Input label="Date & time" type="datetime-local" value={form.start} onChange={e => setForm(f => ({ ...f, start: e.target.value }))} />
        <Select label="Link to application (optional)" value={form.app} onChange={e => setForm(f => ({ ...f, app: e.target.value }))} options={apps} />
        <Input label="Notes (optional)" value={form.notes} onChange={e => setForm(f => ({ ...f, notes: e.target.value }))} />
        {mut.isError && <p className="text-xs text-error">Couldn’t save. Check the fields and try again.</p>}
        <div className="flex justify-end gap-2 pt-1">
          <Button variant="ghost" onClick={onClose}>Cancel</Button>
          <Button variant="secondary" onClick={() => mut.mutate()} disabled={!form.title || !form.start || mut.isPending}>
            {mut.isPending ? 'Saving…' : 'Add reminder'}
          </Button>
        </div>
      </div>
    </Modal>
  )
}

function WorkBlockModal({ open, apps, onClose, onCreated }: {
  open: boolean
  apps: { value: string; label: string }[]
  onClose: () => void
  onCreated: () => void
}) {
  const [form, setForm] = useState({ title: '', start: '', duration: '60', category: 'general', app: 'all' })
  const mut = useMutation({
    mutationFn: () => createWorkBlock({
      title: form.title,
      start_at: toISO(form.start),
      duration_minutes: Number(form.duration) || 60,
      category: form.category,
      application_id: form.app !== 'all' ? form.app : null,
    }),
    onSuccess: () => { setForm({ title: '', start: '', duration: '60', category: 'general', app: 'all' }); onCreated() },
  })
  return (
    <Modal isOpen={open} onClose={onClose} title="Add work block">
      <div className="space-y-3">
        <Input label="Title" placeholder="e.g. Draft Stanford essay" value={form.title} onChange={e => setForm(f => ({ ...f, title: e.target.value }))} />
        <Input label="Date & time" type="datetime-local" value={form.start} onChange={e => setForm(f => ({ ...f, start: e.target.value }))} />
        <Input label="Duration (minutes)" type="number" value={form.duration} onChange={e => setForm(f => ({ ...f, duration: e.target.value }))} />
        <Select label="Category" value={form.category} onChange={e => setForm(f => ({ ...f, category: e.target.value }))} options={WORK_CATEGORIES} />
        <Select label="Link to application (optional)" value={form.app} onChange={e => setForm(f => ({ ...f, app: e.target.value }))} options={apps} />
        {mut.isError && <p className="text-xs text-error">Couldn’t save. Check the fields and try again.</p>}
        <div className="flex justify-end gap-2 pt-1">
          <Button variant="ghost" onClick={onClose}>Cancel</Button>
          <Button variant="secondary" onClick={() => mut.mutate()} disabled={!form.title || !form.start || mut.isPending}>
            {mut.isPending ? 'Saving…' : 'Add work block'}
          </Button>
        </div>
      </div>
    </Modal>
  )
}
