import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getOnboarding, getNextStep } from '../../api/students'
import { getMatches } from '../../api/matching'
import { listMyApplications } from '../../api/applications'
import { getMyRsvps } from '../../api/events'
import { getMyInterviews } from '../../api/interviews'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import ProgressBar from '../../components/ui/ProgressBar'
import Skeleton from '../../components/ui/Skeleton'
import { formatDate, formatScore } from '../../utils/format'
import { TIER_LABELS } from '../../utils/constants'
import {
  MessageSquare, Search, FileText, User, Clock,
  ArrowRight, Sparkles, CalendarDays, TrendingUp, ShieldCheck, AlertTriangle,
} from 'lucide-react'
import { parseISO, differenceInDays } from 'date-fns'
import type { MatchResult, Application } from '../../types'

interface Deadline {
  date: Date
  label: string
  type: 'application' | 'event' | 'interview'
  link: string
}

export default function DashboardPage() {
  const navigate = useNavigate()

  const { data: onboarding, isLoading: onbLoading } = useQuery({
    queryKey: ['onboarding'],
    queryFn: getOnboarding,
  })

  const { data: nextStep } = useQuery({
    queryKey: ['next-step'],
    queryFn: getNextStep,
  })

  const completionPct = onboarding?.completion_percentage ?? 0
  const showMatches = completionPct >= 80

  const { data: matches, isLoading: matchesLoading, isError: matchesError } = useQuery({
    queryKey: ['matches'],
    queryFn: () => getMatches(),
    enabled: showMatches,
  })

  const { data: applications, isLoading: appsLoading, isError: appsError } = useQuery({
    queryKey: ['my-applications'],
    queryFn: listMyApplications,
  })

  const { data: rsvps, isError: rsvpsError } = useQuery({
    queryKey: ['my-rsvps'],
    queryFn: getMyRsvps,
  })

  const { data: interviews, isError: interviewsError } = useQuery({
    queryKey: ['my-interviews'],
    queryFn: getMyInterviews,
  })

  const applicationsList: Application[] = Array.isArray(applications) ? applications : []
  const rsvpsList: any[] = Array.isArray(rsvps) ? rsvps : []
  const interviewsList: any[] = Array.isArray(interviews) ? interviews : []
  const matchesList: MatchResult[] = Array.isArray(matches) ? matches : []

  // Aggregate deadlines
  const now = new Date()
  const deadlines: Deadline[] = []

  applicationsList.forEach((a: Application) => {
    if (a.program?.application_deadline) {
      const d = parseISO(a.program.application_deadline)
      if (d >= now) {
        deadlines.push({
          date: d,
          label: `${a.program.program_name} deadline`,
          type: 'application',
          link: `/s/applications/${a.id}`,
        })
      }
    }
  })

  rsvpsList.forEach((r: any) => {
    if (r.event?.start_time) {
      const d = parseISO(r.event.start_time)
      if (d >= now) {
        deadlines.push({
          date: d,
          label: r.event.event_name || 'Event',
          type: 'event',
          link: '/s/calendar',
        })
      }
    }
  })

  interviewsList.forEach((i: any) => {
    const time = i.confirmed_time || i.proposed_times?.[0]
    if (time) {
      const d = parseISO(time)
      if (d >= now) {
        deadlines.push({
          date: d,
          label: 'Interview',
          type: 'interview',
          link: '/s/calendar',
        })
      }
    }
  })

  deadlines.sort((a, b) => a.date.getTime() - b.date.getTime())

  // Application status counts
  const statusCounts: Record<string, number> = {}
  applicationsList.forEach((a: Application) => {
    statusCounts[a.status] = (statusCounts[a.status] || 0) + 1
  })

  // Top matches
  const topMatches = matchesList
    .sort((a: MatchResult, b: MatchResult) => b.match_score - a.match_score)
    .slice(0, 3)

  const urgencyColor = (date: Date) => {
    const days = differenceInDays(date, now)
    if (days <= 7) return 'text-amber-700 bg-amber-50'
    if (days <= 30) return 'text-blue-700 bg-blue-50'
    return 'text-gray-700 bg-gray-100'
  }

  const urgencyLabel = (date: Date) => {
    const days = differenceInDays(date, now)
    if (days === 0) return 'Focus now'
    if (days === 1) return 'Focus tomorrow'
    if (days <= 7) return `Focus this week`
    if (days <= 30) return `Plan this month`
    return `Upcoming`
  }

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Today with your admissions counselor</h1>
          <p className="text-sm text-gray-500 mt-1">A calm brief of what matters now, what is next, and what can wait.</p>
        </div>
      </div>

      {(matchesError || appsError || rsvpsError || interviewsError) && (
        <Card className="p-4 border-amber-200 bg-amber-50">
          <div className="flex items-start gap-2 text-amber-800">
            <AlertTriangle size={16} className="mt-0.5" />
            <p className="text-sm">
              Some dashboard data could not load. The page is still usable and you can continue.
            </p>
          </div>
        </Card>
      )}

      {/* Counselor brief */}
      <Card className="p-5">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <ShieldCheck size={17} className="text-gray-700" />
              <h2 className="font-semibold text-gray-900">Counselor Brief</h2>
            </div>
            <p className="text-sm text-gray-700">
              {nextStep?.guidance_text
                ? `You are on track. The best step right now is: ${nextStep.guidance_text}`
                : 'You are in a stable place. Continue your current plan and we will refine it together.'}
            </p>
          </div>
          <Button size="sm" variant="secondary" onClick={() => navigate('/s/chat')}>
            Talk to counselor <ArrowRight size={14} className="ml-1" />
          </Button>
        </div>
      </Card>

      {/* Profile Completion + Next Step */}
      {completionPct < 100 && (
        <Card className="p-5">
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-center gap-2">
              <User size={18} className="text-gray-600" />
              <h2 className="font-semibold text-gray-900">Profile Completion</h2>
            </div>
            <Button size="sm" variant="secondary" onClick={() => navigate('/s/profile')}>
              Complete Profile <ArrowRight size={14} className="ml-1" />
            </Button>
          </div>
          {onbLoading ? (
            <Skeleton className="h-6" />
          ) : (
            <>
              <ProgressBar value={completionPct} label={`${completionPct}% complete`} />
              {completionPct < 80 && (
                <p className="text-sm text-blue-700 bg-blue-50 rounded-lg px-3 py-2 mt-3">
                  A bit more profile detail will improve recommendation confidence and reduce uncertainty.
                </p>
              )}
              {nextStep && (
                <div className="mt-3 text-sm text-gray-600">
                  <span className="font-medium">Next:</span> {nextStep.guidance_text || `Fill in your ${nextStep.section}`}
                </div>
              )}
            </>
          )}
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* AI Match Highlights */}
        <Card className="p-5">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Sparkles size={18} className="text-gray-600" />
              <h2 className="font-semibold text-gray-900">Top Matches</h2>
            </div>
            <button onClick={() => navigate('/s/discover')} className="text-sm text-gray-500 hover:text-gray-700 flex items-center gap-1">
              View all <ArrowRight size={14} />
            </button>
          </div>
          {!showMatches ? (
            <p className="text-sm text-gray-500">Complete your profile (80%+) to see AI matches.</p>
          ) : matchesLoading ? (
            <div className="space-y-3">{Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-16" />)}</div>
          ) : topMatches.length === 0 ? (
            <p className="text-sm text-gray-500">No matches yet — check back after processing.</p>
          ) : (
            <div className="space-y-3">
              {topMatches.map((m: MatchResult) => {
                const tierInfo = TIER_LABELS[m.match_tier]
                return (
                  <div
                    key={m.id}
                    onClick={() => navigate(`/s/schools/${m.program_id}`)}
                    className="flex items-center justify-between p-3 rounded-lg border border-gray-100 hover:bg-gray-50 cursor-pointer"
                  >
                    <div className="min-w-0">
                      <p className="text-sm font-medium truncate">{m.program?.program_name || 'Program'}</p>
                      <p className="text-xs text-gray-500 truncate">{m.program?.department || ''}</p>
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      <span className="text-sm font-bold">{formatScore(m.match_score)}</span>
                      {tierInfo && <Badge variant={tierInfo.color as any} size="sm">{tierInfo.label}</Badge>}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </Card>

        {/* Application Status Summary */}
        <Card className="p-5">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <FileText size={18} className="text-gray-600" />
              <h2 className="font-semibold text-gray-900">Applications</h2>
            </div>
            <button onClick={() => navigate('/s/applications')} className="text-sm text-gray-500 hover:text-gray-700 flex items-center gap-1">
              View all <ArrowRight size={14} />
            </button>
          </div>
          {appsLoading ? (
            <Skeleton className="h-20" />
          ) : applicationsList.length === 0 ? (
            <div className="text-center py-4">
              <p className="text-sm text-gray-500 mb-3">No applications yet</p>
              <Button size="sm" onClick={() => navigate('/s/discover')}>Discover Programs</Button>
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-3">
              {[
                { key: 'draft', label: 'Draft', icon: '📝' },
                { key: 'submitted', label: 'Submitted', icon: '📤' },
                { key: 'under_review', label: 'Under Review', icon: '🔍' },
                { key: 'decision_made', label: 'Decision', icon: '📋' },
              ].map(({ key, label, icon }) => (
                <div
                  key={key}
                  onClick={() => navigate('/s/applications')}
                  className="flex items-center gap-3 p-3 rounded-lg border border-gray-100 hover:bg-gray-50 cursor-pointer"
                >
                  <span className="text-lg">{icon}</span>
                  <div>
                    <p className="text-xl font-bold">{statusCounts[key] || 0}</p>
                    <p className="text-xs text-gray-500">{label}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Upcoming Deadlines */}
        <Card className="p-5">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Clock size={18} className="text-gray-600" />
              <h2 className="font-semibold text-gray-900">Upcoming Deadlines</h2>
            </div>
            <button onClick={() => navigate('/s/deadlines')} className="text-sm text-gray-500 hover:text-gray-700 flex items-center gap-1">
              Calendar <ArrowRight size={14} />
            </button>
          </div>
          {deadlines.length === 0 ? (
            <p className="text-sm text-gray-500">No upcoming deadlines</p>
          ) : (
            <div className="space-y-2">
              {deadlines.slice(0, 5).map((d, i) => (
                <div
                  key={i}
                  onClick={() => navigate(d.link)}
                  className="flex items-center justify-between p-3 rounded-lg border border-gray-100 hover:bg-gray-50 cursor-pointer"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <CalendarDays size={16} className="text-gray-400 flex-shrink-0" />
                    <div className="min-w-0">
                      <p className="text-sm font-medium truncate">{d.label}</p>
                      <p className="text-xs text-gray-500">{formatDate(d.date.toISOString())}</p>
                    </div>
                  </div>
                  <span className={`text-xs font-medium px-2 py-1 rounded-full flex-shrink-0 ${urgencyColor(d.date)}`}>
                    {urgencyLabel(d.date)}
                  </span>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Quick Actions */}
        <Card className="p-5">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp size={18} className="text-gray-600" />
            <h2 className="font-semibold text-gray-900">Quick Actions</h2>
          </div>
          <div className="grid grid-cols-2 gap-3">
            {completionPct < 100 && (
              <button
                onClick={() => navigate('/s/profile')}
                className="flex items-center gap-3 p-3 rounded-lg border border-gray-100 hover:bg-gray-50 text-left"
              >
                <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
                  <User size={16} className="text-blue-600" />
                </div>
                <span className="text-sm font-medium">Reduce profile uncertainty</span>
              </button>
            )}
            <button
              onClick={() => navigate('/s/discover')}
              className="flex items-center gap-3 p-3 rounded-lg border border-gray-100 hover:bg-gray-50 text-left"
            >
              <div className="w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center">
                <Search size={16} className="text-purple-600" />
              </div>
              <span className="text-sm font-medium">Explore fitting programs</span>
            </button>
            <button
              onClick={() => navigate('/s/chat')}
              className="flex items-center gap-3 p-3 rounded-lg border border-gray-100 hover:bg-gray-50 text-left"
            >
              <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center">
                <MessageSquare size={16} className="text-green-600" />
              </div>
              <span className="text-sm font-medium">Talk with your counselor</span>
            </button>
            {applicationsList.some((a: Application) => a.status === 'draft') && (
              <button
                onClick={() => {
                  const draft = applicationsList.find((a: Application) => a.status === 'draft')
                  if (draft) navigate(`/s/applications/${draft.id}`)
                }}
                className="flex items-center gap-3 p-3 rounded-lg border border-gray-100 hover:bg-gray-50 text-left"
              >
                <div className="w-8 h-8 rounded-full bg-amber-100 flex items-center justify-center">
                  <FileText size={16} className="text-amber-600" />
                </div>
                <span className="text-sm font-medium">Continue with calm checklist</span>
              </button>
            )}
          </div>
        </Card>
      </div>
    </div>
  )
}
