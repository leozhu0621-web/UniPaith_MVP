import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDeadlines } from '../../hooks/useDeadlines'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import EmptyState from '../../components/ui/EmptyState'
import { SkeletonCard } from '../../components/ui/Skeleton'
import { formatDate, formatDateTime } from '../../utils/format'
import { differenceInDays, format } from 'date-fns'
import { Clock, FileText, CalendarDays, Mic, AlertTriangle } from 'lucide-react'

export default function DeadlinesPage() {
  const navigate = useNavigate()
  const { deadlines, isLoading } = useDeadlines()

  // Group by month
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
    const days = differenceInDays(date, now)
    if (days <= 7) return <Badge variant="warning">{days === 0 ? 'Focus now' : 'Focus this week'}</Badge>
    if (days <= 30) return <Badge variant="info">Plan this month</Badge>
    return <Badge variant="neutral">Upcoming</Badge>
  }

  if (isLoading) return <div className="p-6 max-w-3xl mx-auto space-y-4">{Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} />)}</div>

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold">Deadline Tracker</h1>
          <p className="text-sm text-gray-500 mt-1">{deadlines.length} timeline item{deadlines.length !== 1 ? 's' : ''} to guide your next steps</p>
        </div>
      </div>

      {/* Focus this week */}
      {deadlines.length > 0 && differenceInDays(deadlines[0].date, new Date()) <= 7 && (
        <div className="flex items-start gap-3 bg-amber-50 border border-amber-200 rounded-lg px-4 py-3 mb-6">
          <AlertTriangle size={18} className="text-amber-600 mt-0.5 flex-shrink-0" />
          <div>
            <p className="text-sm font-medium text-amber-800">Focus this week</p>
            <p className="text-sm text-amber-700">{deadlines[0].label} — {formatDate(deadlines[0].date.toISOString())}</p>
            <button
              onClick={() => navigate(deadlines[0].link)}
              className="text-xs font-medium text-amber-800 underline mt-1"
            >
              Open next action
            </button>
          </div>
        </div>
      )}

      {deadlines.length === 0 ? (
        <EmptyState
          icon={<Clock size={48} />}
          title="No upcoming deadlines"
          description="Apply to programs or RSVP to events to see deadlines here."
          action={{ label: 'Discover Programs', onClick: () => navigate('/s/explore') }}
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
