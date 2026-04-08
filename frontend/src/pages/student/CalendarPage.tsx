import { useState, useMemo } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useDeadlines } from '../../hooks/useDeadlines'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import EmptyState from '../../components/ui/EmptyState'
import { SkeletonCard } from '../../components/ui/Skeleton'
import { formatDate, formatDateTime } from '../../utils/format'
import {
  startOfMonth, endOfMonth, eachDayOfInterval, format, addMonths, subMonths,
  isSameDay, isToday, differenceInDays,
} from 'date-fns'
import { ChevronLeft, ChevronRight, Clock, FileText, CalendarDays, Mic, AlertTriangle } from 'lucide-react'

type ViewMode = 'month' | 'agenda'

export default function CalendarPage() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const initialView = (searchParams.get('view') as ViewMode) || 'month'
  const [view, setView] = useState<ViewMode>(initialView)
  const [currentMonth, setCurrentMonth] = useState(new Date())
  const { deadlines, isLoading } = useDeadlines()

  const switchView = (v: ViewMode) => {
    setView(v)
    setSearchParams(v === 'month' ? {} : { view: v })
  }

  // --- Month view data ---
  const monthStart = startOfMonth(currentMonth)
  const monthEnd = endOfMonth(currentMonth)
  const days = eachDayOfInterval({ start: monthStart, end: monthEnd })
  const startDay = monthStart.getDay()
  const padDays = startDay === 0 ? 6 : startDay - 1

  const typeColor: Record<string, string> = { event: 'bg-blue-400', application: 'bg-red-400', interview: 'bg-purple-400' }
  const typeIcon: Record<string, string> = { event: '\uD83C\uDFA4', application: '\uD83D\uDCC5', interview: '\uD83C\uDF99' }

  // --- Agenda view data ---
  const grouped = useMemo(() => {
    const groups: Record<string, typeof deadlines> = {}
    deadlines.forEach(d => {
      const key = format(d.date, 'MMMM yyyy')
      if (!groups[key]) groups[key] = []
      groups[key].push(d)
    })
    return groups
  }, [deadlines])

  const typeConfig: Record<string, { icon: typeof FileText; color: string; bg: string }> = {
    application: { icon: FileText, color: 'text-blue-600', bg: 'bg-blue-100' },
    event: { icon: CalendarDays, color: 'text-purple-600', bg: 'bg-purple-100' },
    interview: { icon: Mic, color: 'text-amber-600', bg: 'bg-amber-100' },
  }

  const urgencyBadge = (date: Date) => {
    const now = new Date()
    const d = differenceInDays(date, now)
    if (d <= 7) return <Badge variant="warning">{d === 0 ? 'Focus now' : 'Focus this week'}</Badge>
    if (d <= 30) return <Badge variant="info">Plan this month</Badge>
    return <Badge variant="neutral">Upcoming</Badge>
  }

  if (isLoading) return <div className="p-6 max-w-4xl mx-auto space-y-4">{Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} />)}</div>

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold">Calendar</h1>
          <p className="text-sm text-gray-500 mt-1">{deadlines.length} upcoming item{deadlines.length !== 1 ? 's' : ''}</p>
        </div>
        <div className="flex items-center gap-1 bg-gray-100 rounded-lg p-0.5">
          <button
            onClick={() => switchView('month')}
            className={`px-3 py-1.5 text-sm rounded-md transition-colors ${view === 'month' ? 'bg-white text-brand-slate-700 shadow-sm' : 'text-gray-500 hover:text-brand-slate-600'}`}
          >
            Month
          </button>
          <button
            onClick={() => switchView('agenda')}
            className={`px-3 py-1.5 text-sm rounded-md transition-colors ${view === 'agenda' ? 'bg-white text-brand-slate-700 shadow-sm' : 'text-gray-500 hover:text-brand-slate-600'}`}
          >
            Timeline
          </button>
        </div>
      </div>

      {/* Focus this week banner */}
      {deadlines.length > 0 && differenceInDays(deadlines[0].date, new Date()) <= 7 && (
        <div className="flex items-start gap-3 bg-amber-50 border border-amber-200 rounded-lg px-4 py-3 mb-6">
          <AlertTriangle size={18} className="text-amber-600 mt-0.5 flex-shrink-0" />
          <div>
            <p className="text-sm font-medium text-amber-800">Focus this week</p>
            <p className="text-sm text-amber-700">{deadlines[0].label} — {formatDate(deadlines[0].date.toISOString())}</p>
            <button onClick={() => navigate(deadlines[0].link)} className="text-xs font-medium text-amber-800 underline mt-1">
              Open next action
            </button>
          </div>
        </div>
      )}

      {view === 'month' && (
        <>
          {/* Month navigation */}
          <div className="flex items-center justify-end gap-3 mb-4">
            <button onClick={() => setCurrentMonth(m => subMonths(m, 1))} className="p-1 hover:bg-gray-100 rounded"><ChevronLeft size={18} /></button>
            <span className="text-sm font-medium w-32 text-center">{format(currentMonth, 'MMMM yyyy')}</span>
            <button onClick={() => setCurrentMonth(m => addMonths(m, 1))} className="p-1 hover:bg-gray-100 rounded"><ChevronRight size={18} /></button>
          </div>

          {/* Calendar grid */}
          <div className="grid grid-cols-7 gap-px bg-gray-200 rounded-lg overflow-hidden mb-8">
            {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map(d => (
              <div key={d} className="bg-gray-50 py-2 text-center text-xs font-medium text-gray-500">{d}</div>
            ))}
            {Array.from({ length: padDays }).map((_, i) => (
              <div key={`pad-${i}`} className="bg-white min-h-[80px]" />
            ))}
            {days.map(day => {
              const dayEvents = deadlines.filter(e => isSameDay(e.date, day))
              return (
                <div key={day.toISOString()} className={`bg-white min-h-[80px] p-1 ${isToday(day) ? 'ring-2 ring-inset ring-brand-slate-700' : ''}`}>
                  <span className={`text-xs ${isToday(day) ? 'font-bold' : 'text-gray-600'}`}>{format(day, 'd')}</span>
                  <div className="mt-1 space-y-0.5">
                    {dayEvents.slice(0, 2).map((e, i) => (
                      <div key={i} className={`text-[10px] px-1 py-0.5 rounded truncate text-white ${typeColor[e.type]}`}>
                        {e.label}
                      </div>
                    ))}
                    {dayEvents.length > 2 && <div className="text-[10px] text-gray-400">+{dayEvents.length - 2} more</div>}
                  </div>
                </div>
              )
            })}
          </div>

          {/* Upcoming list */}
          <h2 className="text-lg font-medium mb-3">Upcoming</h2>
          {deadlines.length === 0 ? (
            <p className="text-sm text-gray-500">Your schedule is clear</p>
          ) : (
            <div className="space-y-2">
              {deadlines.slice(0, 10).map((e, i) => (
                <Card key={i} onClick={() => navigate(e.link)} className="p-3 flex items-center gap-3 cursor-pointer hover:bg-gray-50">
                  <span className="text-lg">{typeIcon[e.type]}</span>
                  <div>
                    <p className="text-sm font-medium">{e.label}</p>
                    <p className="text-xs text-gray-500">{formatDateTime(e.date.toISOString())}</p>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </>
      )}

      {view === 'agenda' && (
        <>
          {deadlines.length === 0 ? (
            <EmptyState
              icon={<Clock size={48} />}
              title="Nothing urgent — a calm moment to prepare"
              description="Deadlines and events will appear here as you apply."
              action={{ label: 'Discover Programs', onClick: () => navigate('/s/discover') }}
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
                        const config = typeConfig[item.type]
                        const Icon = config.icon
                        return (
                          <div key={i} onClick={() => navigate(item.link)} className="flex items-start gap-4 cursor-pointer group">
                            <div className={`w-10 h-10 rounded-full ${config.bg} flex items-center justify-center flex-shrink-0 z-10`}>
                              <Icon size={18} className={config.color} />
                            </div>
                            <Card className="flex-1 p-4 group-hover:bg-gray-50">
                              <div className="flex items-start justify-between">
                                <div className="min-w-0">
                                  <p className="text-sm font-medium">{item.label}</p>
                                  {item.sublabel && <p className="text-xs text-gray-500 mt-0.5">{item.sublabel}</p>}
                                  <p className="text-xs text-gray-400 mt-1">{formatDateTime(item.date.toISOString())}</p>
                                </div>
                                <div className="flex-shrink-0 ml-3">{urgencyBadge(item.date)}</div>
                              </div>
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
    </div>
  )
}
