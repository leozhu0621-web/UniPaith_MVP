import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getMyRsvps } from '../../api/events'
import { getMyInterviews } from '../../api/interviews'
import { listMyApplications } from '../../api/applications'
import Card from '../../components/ui/Card'
import { formatDateTime } from '../../utils/format'
import {
  startOfMonth, endOfMonth, eachDayOfInterval, format, addMonths, subMonths,
  isSameDay, isToday, parseISO,
} from 'date-fns'
import { ChevronLeft, ChevronRight } from 'lucide-react'

interface CalendarEvent {
  date: Date
  title: string
  type: 'event' | 'deadline' | 'interview'
}

export default function CalendarPage() {
  const [currentMonth, setCurrentMonth] = useState(new Date())

  const { data: rsvps } = useQuery({ queryKey: ['my-rsvps'], queryFn: getMyRsvps })
  const { data: interviews } = useQuery({ queryKey: ['my-interviews'], queryFn: getMyInterviews })
  const { data: applications } = useQuery({ queryKey: ['my-applications'], queryFn: listMyApplications })

  const events = useMemo(() => {
    const items: CalendarEvent[] = []
    // RSVPs → events
    ;(rsvps ?? []).forEach((r: any) => {
      if (r.event?.start_time) items.push({ date: parseISO(r.event.start_time), title: r.event.event_name || 'Event', type: 'event' })
    })
    // Interviews
    ;(interviews ?? []).forEach((i: any) => {
      const time = i.confirmed_time || i.proposed_times?.[0]
      if (time) items.push({ date: parseISO(time), title: `Interview`, type: 'interview' })
    })
    // Application deadlines
    ;(applications ?? []).forEach((a: any) => {
      if (a.program?.application_deadline) {
        items.push({ date: parseISO(a.program.application_deadline), title: `${a.program.program_name} deadline`, type: 'deadline' })
      }
    })
    return items
  }, [rsvps, interviews, applications])

  const monthStart = startOfMonth(currentMonth)
  const monthEnd = endOfMonth(currentMonth)
  const days = eachDayOfInterval({ start: monthStart, end: monthEnd })

  // Pad start to align with Monday
  const startDay = monthStart.getDay()
  const padDays = startDay === 0 ? 6 : startDay - 1

  const upcomingEvents = events
    .filter(e => e.date >= new Date())
    .sort((a, b) => a.date.getTime() - b.date.getTime())
    .slice(0, 10)

  const typeIcon: Record<string, string> = { event: '🎤', deadline: '📅', interview: '🎙' }
  const typeColor: Record<string, string> = { event: 'bg-blue-400', deadline: 'bg-red-400', interview: 'bg-purple-400' }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold">Calendar</h1>
        <div className="flex items-center gap-3">
          <button onClick={() => setCurrentMonth(m => subMonths(m, 1))} className="p-1 hover:bg-gray-100 rounded"><ChevronLeft size={18} /></button>
          <span className="text-sm font-medium w-32 text-center">{format(currentMonth, 'MMMM yyyy')}</span>
          <button onClick={() => setCurrentMonth(m => addMonths(m, 1))} className="p-1 hover:bg-gray-100 rounded"><ChevronRight size={18} /></button>
        </div>
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
          const dayEvents = events.filter(e => isSameDay(e.date, day))
          return (
            <div key={day.toISOString()} className={`bg-white min-h-[80px] p-1 ${isToday(day) ? 'ring-2 ring-inset ring-gray-900' : ''}`}>
              <span className={`text-xs ${isToday(day) ? 'font-bold' : 'text-gray-600'}`}>{format(day, 'd')}</span>
              <div className="mt-1 space-y-0.5">
                {dayEvents.slice(0, 2).map((e, i) => (
                  <div key={i} className={`text-[10px] px-1 py-0.5 rounded truncate text-white ${typeColor[e.type]}`}>
                    {e.title}
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
      {upcomingEvents.length === 0 ? (
        <p className="text-sm text-gray-500">No upcoming events</p>
      ) : (
        <div className="space-y-2">
          {upcomingEvents.map((e, i) => (
            <Card key={i} className="p-3 flex items-center gap-3">
              <span className="text-lg">{typeIcon[e.type]}</span>
              <div>
                <p className="text-sm font-medium">{e.title}</p>
                <p className="text-xs text-gray-500">{formatDateTime(e.date.toISOString())}</p>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
