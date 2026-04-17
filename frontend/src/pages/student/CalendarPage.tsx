import { useState, useMemo } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useDeadlines } from '../../hooks/useDeadlines'
import { confirmInterview } from '../../api/interviews'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Modal from '../../components/ui/Modal'
import Input from '../../components/ui/Input'
import Select from '../../components/ui/Select'
import EmptyState from '../../components/ui/EmptyState'
import { SkeletonCard } from '../../components/ui/Skeleton'
import { formatDate, formatDateTime } from '../../utils/format'
import {
  startOfMonth, endOfMonth, startOfWeek, endOfWeek, eachDayOfInterval,
  format, addMonths, subMonths, addWeeks, subWeeks,
  isSameDay, isToday, differenceInDays,
} from 'date-fns'
import {
  ChevronLeft, ChevronRight, Clock, FileText, CalendarDays, Mic,
  AlertTriangle, Plus, Video, Phone, MapPin, Check, X as XIcon,
} from 'lucide-react'

type ViewMode = 'month' | 'week' | 'agenda'
type ItemType = 'all' | 'event' | 'application' | 'interview' | 'work_block'

interface CalendarItem {
  date: Date
  label: string
  sublabel?: string
  type: string
  link: string
  meta?: any
}

interface WorkBlock {
  id: string
  title: string
  date: Date
  duration_minutes: number
  linked_app_id?: string
  category: 'essay_draft' | 'interview_prep' | 'general' | 'research'
}

const TYPE_OPTIONS: { value: ItemType; label: string }[] = [
  { value: 'all', label: 'All Types' },
  { value: 'event', label: 'Events' },
  { value: 'application', label: 'Deadlines' },
  { value: 'interview', label: 'Interviews' },
  { value: 'work_block', label: 'Work Blocks' },
]

const WORK_CATEGORIES = [
  { value: 'essay_draft', label: 'Essay Drafting' },
  { value: 'interview_prep', label: 'Interview Prep' },
  { value: 'research', label: 'Program Research' },
  { value: 'general', label: 'General Prep' },
]

export default function CalendarPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [searchParams, setSearchParams] = useSearchParams()
  const initialView = (searchParams.get('view') as ViewMode) || 'month'
  const [view, setView] = useState<ViewMode>(initialView)
  const [currentMonth, setCurrentMonth] = useState(new Date())
  const [currentWeek, setCurrentWeek] = useState(new Date())
  const [typeFilter, setTypeFilter] = useState<ItemType>('all')
  const [showWorkBlockModal, setShowWorkBlockModal] = useState(false)
  const [workBlocks, setWorkBlocks] = useState<WorkBlock[]>([])
  const [wbForm, setWbForm] = useState({ title: '', date: '', duration: '60', category: 'general' })
  const { deadlines, isLoading, interviews } = useDeadlines()
  const interviewList: any[] = Array.isArray(interviews) ? interviews : []

  const confirmMut = useMutation({
    mutationFn: ({ id, time }: { id: string; time: string }) => confirmInterview(id, time),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['my-interviews'] }),
  })

  const switchView = (v: ViewMode) => {
    setView(v)
    setSearchParams(v === 'month' ? {} : { view: v })
  }

  // Build a lookup from interview time to raw interview object for agenda meta
  const interviewMetaLookup = useMemo(() => {
    const map = new Map<string, any>()
    interviewList.forEach(iv => {
      const time = iv.confirmed_time || iv.proposed_times?.[0]
      if (time) map.set(time, iv)
    })
    return map
  }, [interviewList])

  const allItems: CalendarItem[] = useMemo(() => {
    // deadlines already includes interviews from useDeadlines — enrich with meta
    const items: CalendarItem[] = deadlines.map(d => {
      if (d.type === 'interview') {
        // Find the matching raw interview for confirm/decline actions
        const meta = interviewMetaLookup.get(d.date.toISOString()) ?? null
        return { ...d, meta }
      }
      return d
    })
    workBlocks.forEach(wb => {
      items.push({
        date: wb.date,
        label: wb.title,
        sublabel: `${wb.duration_minutes} min — ${wb.category.replace(/_/g, ' ')}`,
        type: 'work_block' as const,
        link: wb.linked_app_id ? `/s/applications/${wb.linked_app_id}` : '/s/calendar',
      })
    })
    items.sort((a, b) => a.date.getTime() - b.date.getTime())
    return items
  }, [deadlines, interviewMetaLookup, workBlocks])

  const filtered = typeFilter === 'all' ? allItems : allItems.filter(i => i.type === typeFilter)

  const typeColor: Record<string, string> = {
    event: 'bg-blue-400', application: 'bg-red-400',
    interview: 'bg-purple-400', work_block: 'bg-emerald-400',
  }
  const typeConfig: Record<string, { icon: typeof FileText; color: string; bg: string }> = {
    application: { icon: FileText, color: 'text-blue-600', bg: 'bg-blue-100' },
    event: { icon: CalendarDays, color: 'text-purple-600', bg: 'bg-purple-100' },
    interview: { icon: Mic, color: 'text-amber-600', bg: 'bg-amber-100' },
    work_block: { icon: Clock, color: 'text-emerald-600', bg: 'bg-emerald-100' },
  }

  const urgencyBadge = (date: Date) => {
    const d = differenceInDays(date, new Date())
    if (d < 0) return <Badge variant="danger">Past</Badge>
    if (d === 0) return <Badge variant="warning">Today</Badge>
    if (d <= 7) return <Badge variant="warning">{d}d</Badge>
    if (d <= 30) return <Badge variant="info">This month</Badge>
    return <Badge variant="neutral">Upcoming</Badge>
  }

  const handleAddWorkBlock = () => {
    if (!wbForm.title || !wbForm.date) return
    const wb: WorkBlock = {
      id: `wb-${Date.now()}`,
      title: wbForm.title,
      date: new Date(wbForm.date),
      duration_minutes: Number(wbForm.duration) || 60,
      category: wbForm.category as WorkBlock['category'],
    }
    setWorkBlocks(prev => [...prev, wb])
    setShowWorkBlockModal(false)
    setWbForm({ title: '', date: '', duration: '60', category: 'general' })
  }

  // Week view data
  const weekStart = startOfWeek(currentWeek, { weekStartsOn: 1 })
  const weekEnd = endOfWeek(currentWeek, { weekStartsOn: 1 })
  const weekDays = eachDayOfInterval({ start: weekStart, end: weekEnd })

  // Month view data
  const monthStart = startOfMonth(currentMonth)
  const monthEnd = endOfMonth(currentMonth)
  const days = eachDayOfInterval({ start: monthStart, end: monthEnd })
  const startDay = monthStart.getDay()
  const padDays = startDay === 0 ? 6 : startDay - 1

  // Agenda grouped
  const grouped = useMemo(() => {
    const groups: Record<string, CalendarItem[]> = {}
    filtered.forEach(d => {
      const key = format(d.date, 'MMMM yyyy')
      if (!groups[key]) groups[key] = []
      groups[key].push(d)
    })
    return groups
  }, [filtered])

  if (isLoading) return <div className="p-6 max-w-4xl mx-auto space-y-4">{Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} />)}</div>

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-2xl font-semibold">Calendar</h1>
          <p className="text-sm text-gray-500 mt-1">{filtered.length} item{filtered.length !== 1 ? 's' : ''}</p>
        </div>
        <div className="flex items-center gap-2">
          <Button size="sm" variant="secondary" onClick={() => setShowWorkBlockModal(true)}>
            <Plus size={14} className="mr-1" /> Work Block
          </Button>
          <div className="flex items-center gap-1 bg-gray-100 rounded-lg p-0.5">
            {(['month', 'week', 'agenda'] as ViewMode[]).map(v => (
              <button
                key={v}
                onClick={() => switchView(v)}
                className={`px-3 py-1.5 text-sm rounded-md transition-colors capitalize ${view === v ? 'bg-white text-stone-700 shadow-sm' : 'text-gray-500 hover:text-stone-600'}`}
              >
                {v}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-2 mb-4">
        {TYPE_OPTIONS.map(opt => (
          <button
            key={opt.value}
            onClick={() => setTypeFilter(opt.value)}
            className={`px-3 py-1 text-xs rounded-full transition-colors ${typeFilter === opt.value ? 'bg-stone-700 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
          >
            {opt.label}
          </button>
        ))}
      </div>

      {/* Focus banner */}
      {filtered.length > 0 && differenceInDays(filtered[0].date, new Date()) >= 0 && differenceInDays(filtered[0].date, new Date()) <= 3 && (
        <div className="flex items-start gap-3 bg-amber-50 border border-amber-200 rounded-lg px-4 py-3 mb-4">
          <AlertTriangle size={18} className="text-amber-600 mt-0.5 flex-shrink-0" />
          <div>
            <p className="text-sm font-medium text-amber-800">Coming up</p>
            <p className="text-sm text-amber-700">{filtered[0].label} — {formatDate(filtered[0].date.toISOString())}</p>
          </div>
        </div>
      )}

      {/* Month View */}
      {view === 'month' && (
        <>
          <div className="flex items-center justify-end gap-3 mb-4">
            <button onClick={() => setCurrentMonth(m => subMonths(m, 1))} className="p-1 hover:bg-gray-100 rounded"><ChevronLeft size={18} /></button>
            <span className="text-sm font-medium w-32 text-center">{format(currentMonth, 'MMMM yyyy')}</span>
            <button onClick={() => setCurrentMonth(m => addMonths(m, 1))} className="p-1 hover:bg-gray-100 rounded"><ChevronRight size={18} /></button>
          </div>
          <div className="grid grid-cols-7 gap-px bg-gray-200 rounded-lg overflow-hidden mb-6">
            {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map(d => (
              <div key={d} className="bg-gray-50 py-2 text-center text-xs font-medium text-gray-500">{d}</div>
            ))}
            {Array.from({ length: padDays }).map((_, i) => <div key={`pad-${i}`} className="bg-white min-h-[80px]" />)}
            {days.map(day => {
              const dayEvents = filtered.filter(e => isSameDay(e.date, day))
              return (
                <div key={day.toISOString()} className={`bg-white min-h-[80px] p-1 ${isToday(day) ? 'ring-2 ring-inset ring-stone-700' : ''}`}>
                  <span className={`text-xs ${isToday(day) ? 'font-bold' : 'text-gray-600'}`}>{format(day, 'd')}</span>
                  <div className="mt-1 space-y-0.5">
                    {dayEvents.slice(0, 2).map((e, i) => (
                      <div key={i} className={`text-[10px] px-1 py-0.5 rounded truncate text-white ${typeColor[e.type]}`}>{e.label}</div>
                    ))}
                    {dayEvents.length > 2 && <div className="text-[10px] text-gray-400">+{dayEvents.length - 2}</div>}
                  </div>
                </div>
              )
            })}
          </div>
        </>
      )}

      {/* Week View */}
      {view === 'week' && (
        <>
          <div className="flex items-center justify-end gap-3 mb-4">
            <button onClick={() => setCurrentWeek(w => subWeeks(w, 1))} className="p-1 hover:bg-gray-100 rounded"><ChevronLeft size={18} /></button>
            <span className="text-sm font-medium text-center">{format(weekStart, 'MMM d')} — {format(weekEnd, 'MMM d, yyyy')}</span>
            <button onClick={() => setCurrentWeek(w => addWeeks(w, 1))} className="p-1 hover:bg-gray-100 rounded"><ChevronRight size={18} /></button>
          </div>
          <div className="grid grid-cols-7 gap-3 mb-6">
            {weekDays.map(day => {
              const dayEvents = filtered.filter(e => isSameDay(e.date, day))
              return (
                <div key={day.toISOString()} className={`rounded-lg border p-2 min-h-[200px] ${isToday(day) ? 'border-stone-700 bg-stone-50' : 'border-gray-200'}`}>
                  <p className={`text-xs font-medium mb-2 ${isToday(day) ? 'text-stone-700' : 'text-gray-500'}`}>
                    {format(day, 'EEE d')}
                  </p>
                  <div className="space-y-1.5">
                    {dayEvents.map((e, i) => {
                      const cfg = typeConfig[e.type] || typeConfig.application
                      return (
                        <div key={i} onClick={() => navigate(e.link)} className="cursor-pointer">
                          <div className={`${cfg.bg} rounded p-1.5`}>
                            <p className="text-[10px] font-medium text-stone-700 truncate">{e.label}</p>
                            {e.sublabel && <p className="text-[9px] text-gray-500 truncate">{e.sublabel}</p>}
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )
            })}
          </div>
        </>
      )}

      {/* Agenda View */}
      {view === 'agenda' && (
        <>
          {filtered.length === 0 ? (
            <EmptyState
              icon={<Clock size={48} />}
              title="Nothing scheduled"
              description="Deadlines and events will appear here as you apply."
              action={{ label: 'Discover Programs', onClick: () => navigate('/s/explore') }}
            />
          ) : (
            <div className="space-y-8">
              {Object.entries(grouped).map(([month, items]) => (
                <div key={month}>
                  <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">{month}</h2>
                  <div className="relative">
                    <div className="absolute left-5 top-0 bottom-0 w-px bg-gray-200" />
                    <div className="space-y-4">
                      {items.map((item, i) => {
                        const config = typeConfig[item.type] || typeConfig.application
                        const Icon = config.icon
                        const isInterview = item.type === 'interview' && item.meta
                        return (
                          <div key={i} className="flex items-start gap-4 group">
                            <div className={`w-10 h-10 rounded-full ${config.bg} flex items-center justify-center flex-shrink-0 z-10`}>
                              <Icon size={18} className={config.color} />
                            </div>
                            <Card className="flex-1 p-4 group-hover:bg-gray-50">
                              <div className="flex items-start justify-between">
                                <div className="min-w-0 cursor-pointer" onClick={() => navigate(item.link)}>
                                  <p className="text-sm font-medium">{item.label}</p>
                                  {item.sublabel && <p className="text-xs text-gray-500 mt-0.5">{item.sublabel}</p>}
                                  <p className="text-xs text-gray-400 mt-1">{formatDateTime(item.date.toISOString())}</p>
                                </div>
                                <div className="flex-shrink-0 ml-3">{urgencyBadge(item.date)}</div>
                              </div>
                              {isInterview && (
                                <div className="mt-3 pt-3 border-t border-gray-100">
                                  <div className="flex items-center gap-3 text-xs text-gray-500 mb-2">
                                    {item.meta.interview_type === 'video' && <span className="flex items-center gap-1"><Video size={12} /> Video</span>}
                                    {item.meta.interview_type === 'phone' && <span className="flex items-center gap-1"><Phone size={12} /> Phone</span>}
                                    {item.meta.interview_type === 'in_person' && <span className="flex items-center gap-1"><MapPin size={12} /> In Person</span>}
                                    {item.meta.location_or_link && <span>{item.meta.location_or_link}</span>}
                                  </div>
                                  {item.meta.status === 'invited' && (
                                    <div className="flex gap-2">
                                      <Button size="sm" onClick={() => confirmMut.mutate({ id: item.meta.id, time: item.meta.proposed_times?.[0] ?? '' })}>
                                        <Check size={12} className="mr-1" /> Accept
                                      </Button>
                                      <Button size="sm" variant="secondary">Tentative</Button>
                                      <Button size="sm" variant="danger"><XIcon size={12} className="mr-1" /> Decline</Button>
                                    </div>
                                  )}
                                  {item.meta.status === 'confirmed' && <Badge variant="success">Confirmed</Badge>}
                                </div>
                              )}
                            </Card>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {/* Work Block Modal */}
      <Modal isOpen={showWorkBlockModal} onClose={() => setShowWorkBlockModal(false)} title="Add Work Block">
        <div className="space-y-3">
          <Input label="Title" value={wbForm.title} onChange={e => setWbForm(f => ({ ...f, title: e.target.value }))} placeholder="e.g. Draft MIT essay" />
          <Input label="Date & Time" type="datetime-local" value={wbForm.date} onChange={e => setWbForm(f => ({ ...f, date: e.target.value }))} />
          <Input label="Duration (minutes)" type="number" value={wbForm.duration} onChange={e => setWbForm(f => ({ ...f, duration: e.target.value }))} />
          <Select label="Category" options={WORK_CATEGORIES} value={wbForm.category} onChange={e => setWbForm(f => ({ ...f, category: e.target.value }))} />
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="ghost" onClick={() => setShowWorkBlockModal(false)}>Cancel</Button>
            <Button onClick={handleAddWorkBlock} disabled={!wbForm.title || !wbForm.date}>Add Block</Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
