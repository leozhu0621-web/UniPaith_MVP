import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { listMyApplications } from '../../api/applications'
import { getMyRsvps } from '../../api/events'
import { getMyInterviews } from '../../api/interviews'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import EmptyState from '../../components/ui/EmptyState'
import { SkeletonCard } from '../../components/ui/Skeleton'
import { formatDate, formatDateTime } from '../../utils/format'
import { differenceInDays, parseISO, format } from 'date-fns'
import { Clock, FileText, CalendarDays, Mic, AlertTriangle } from 'lucide-react'

interface DeadlineItem {
  date: Date
  label: string
  sublabel?: string
  type: 'application' | 'event' | 'interview'
  link: string
}

export default function DeadlinesPage() {
  const navigate = useNavigate()

  const { data: applications, isLoading: appsLoading } = useQuery({
    queryKey: ['my-applications'],
    queryFn: listMyApplications,
  })

  const { data: rsvps, isLoading: rsvpsLoading } = useQuery({
    queryKey: ['my-rsvps'],
    queryFn: getMyRsvps,
  })

  const { data: interviews, isLoading: intLoading } = useQuery({
    queryKey: ['my-interviews'],
    queryFn: getMyInterviews,
  })

  const isLoading = appsLoading || rsvpsLoading || intLoading
  const now = new Date()

  const deadlines = useMemo(() => {
    const items: DeadlineItem[] = []

    ;(applications ?? []).forEach((a: any) => {
      if (a.program?.application_deadline) {
        const d = parseISO(a.program.application_deadline)
        if (d >= now) {
          items.push({
            date: d,
            label: `${a.program.program_name} deadline`,
            sublabel: a.status === 'draft' ? 'Application not submitted yet' : `Status: ${a.status.replace(/_/g, ' ')}`,
            type: 'application',
            link: `/s/applications/${a.id}`,
          })
        }
      }
    })

    ;(rsvps ?? []).forEach((r: any) => {
      if (r.event?.start_time) {
        const d = parseISO(r.event.start_time)
        if (d >= now) {
          items.push({
            date: d,
            label: r.event.event_name || 'Event',
            sublabel: r.event.location || r.event.event_type,
            type: 'event',
            link: '/s/calendar',
          })
        }
      }
    })

    ;(interviews ?? []).forEach((i: any) => {
      const time = i.confirmed_time || i.proposed_times?.[0]
      if (time) {
        const d = parseISO(time)
        if (d >= now) {
          items.push({
            date: d,
            label: `Interview — ${i.interview_type || 'Video'}`,
            sublabel: i.status === 'confirmed' ? 'Confirmed' : 'Pending confirmation',
            type: 'interview',
            link: '/s/calendar',
          })
        }
      }
    })

    items.sort((a, b) => a.date.getTime() - b.date.getTime())
    return items
  }, [applications, rsvps, interviews])

  // Group by month
  const grouped = useMemo(() => {
    const groups: Record<string, DeadlineItem[]> = {}
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
    const days = differenceInDays(date, now)
    if (days <= 3) return <Badge variant="danger">In {days === 0 ? 'Today' : days === 1 ? '1 day' : `${days} days`}</Badge>
    if (days <= 7) return <Badge variant="warning">In {days} days</Badge>
    if (days <= 30) return <Badge variant="info">In {Math.ceil(days / 7)} weeks</Badge>
    return <Badge variant="neutral">In {Math.ceil(days / 30)} months</Badge>
  }

  if (isLoading) return <div className="p-6 max-w-3xl mx-auto space-y-4">{Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} />)}</div>

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold">Deadline Tracker</h1>
          <p className="text-sm text-gray-500 mt-1">{deadlines.length} upcoming deadline{deadlines.length !== 1 ? 's' : ''}</p>
        </div>
      </div>

      {/* Urgent alert */}
      {deadlines.length > 0 && differenceInDays(deadlines[0].date, now) <= 7 && (
        <div className="flex items-start gap-3 bg-red-50 border border-red-200 rounded-lg px-4 py-3 mb-6">
          <AlertTriangle size={18} className="text-red-600 mt-0.5 flex-shrink-0" />
          <div>
            <p className="text-sm font-medium text-red-800">Urgent deadline approaching</p>
            <p className="text-sm text-red-700">{deadlines[0].label} — {formatDate(deadlines[0].date.toISOString())}</p>
          </div>
        </div>
      )}

      {deadlines.length === 0 ? (
        <EmptyState
          icon={<Clock size={48} />}
          title="No upcoming deadlines"
          description="Apply to programs or RSVP to events to see deadlines here."
          action={{ label: 'Discover Programs', onClick: () => navigate('/s/discover') }}
        />
      ) : (
        <div className="space-y-8">
          {Object.entries(grouped).map(([month, items]) => (
            <div key={month}>
              <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">{month}</h2>
              <div className="relative">
                {/* Timeline line */}
                <div className="absolute left-5 top-0 bottom-0 w-px bg-gray-200" />

                <div className="space-y-4">
                  {items.map((item, i) => {
                    const config = typeConfig[item.type]
                    const Icon = config.icon
                    return (
                      <div
                        key={i}
                        onClick={() => navigate(item.link)}
                        className="flex items-start gap-4 cursor-pointer group"
                      >
                        {/* Timeline dot */}
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
                            <div className="flex-shrink-0 ml-3">
                              {urgencyBadge(item.date)}
                            </div>
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
    </div>
  )
}
