import { useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getOnboarding, getNextStep } from '../../api/students'
import { getMatches } from '../../api/matching'
import { useDeadlines } from '../../hooks/useDeadlines'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import ProgressBar from '../../components/ui/ProgressBar'
import Skeleton from '../../components/ui/Skeleton'
import {
  MessageSquare, Search, FileText, User,
  ArrowRight, ShieldCheck, AlertTriangle, Sparkles, Calendar, Zap,
} from 'lucide-react'
import { differenceInDays, parseISO } from 'date-fns'
import { formatDate } from '../../utils/format'
import type { Application } from '../../types'

type Priority = 'urgent' | 'soon' | 'on-track'
type SortKey = 'deadline' | 'readiness' | 'priority'

interface NextAction {
  appId: string
  programName: string
  institutionName: string
  action: string
  priority: Priority
  daysLeft: number | null
}

const PRIORITY_ORDER: Record<Priority, number> = { urgent: 0, soon: 1, 'on-track': 2 }

const PRIORITY_BADGE: Record<Priority, { variant: 'danger' | 'warning' | 'success'; label: string }> = {
  urgent:    { variant: 'danger',  label: 'Urgent' },
  soon:      { variant: 'warning', label: 'Soon' },
  'on-track': { variant: 'success', label: 'On Track' },
}

const STATUS_LABELS: Record<string, string> = {
  draft: 'Draft',
  submitted: 'Submitted',
  under_review: 'Under Review',
  interview: 'Interview',
  decision_made: 'Decision',
}

function deriveAction(app: Application): { action: string; daysLeft: number | null; priority: Priority } {
  const deadline = app.program?.application_deadline
  const daysLeft = deadline ? differenceInDays(parseISO(deadline), new Date()) : null

  const priority: Priority =
    daysLeft != null && daysLeft < 3 ? 'urgent' :
    daysLeft != null && daysLeft < 7 ? 'soon' : 'on-track'

  const deadlineSuffix = daysLeft != null && daysLeft >= 0 ? ` by ${formatDate(deadline)}` : ''

  if (app.status === 'draft') {
    const firstMissing = app.missing_items?.[0]
    if (firstMissing) {
      return { action: `Upload ${firstMissing}${deadlineSuffix}`, daysLeft, priority }
    }
    return { action: `Complete and submit${deadlineSuffix}`, daysLeft, priority }
  }

  if (app.status === 'submitted') {
    return { action: 'Awaiting review', daysLeft, priority: 'on-track' }
  }

  if (app.status === 'under_review') {
    return { action: 'Under review — check for updates', daysLeft, priority: 'on-track' }
  }

  if (app.status === 'interview') {
    return { action: 'Schedule interview', daysLeft, priority: daysLeft != null && daysLeft < 7 ? 'soon' : 'on-track' }
  }

  return { action: 'Review status', daysLeft, priority: 'on-track' }
}

function buildActions(apps: Application[]): NextAction[] {
  return apps
    .filter(a => a.status !== 'decision_made')
    .map(a => {
      const { action, daysLeft, priority } = deriveAction(a)
      return {
        appId: a.id,
        programName: a.program?.program_name || 'Program',
        institutionName: (a.program as any)?.institution_name || '',
        action,
        priority,
        daysLeft,
      }
    })
}

export default function DashboardPage() {
  const navigate = useNavigate()
  const [sortKey, setSortKey] = useState<SortKey>('priority')

  const { data: onboarding, isLoading: onbLoading } = useQuery({
    queryKey: ['onboarding'],
    queryFn: getOnboarding,
  })

  const { data: nextStep } = useQuery({
    queryKey: ['next-step'],
    queryFn: getNextStep,
  })

  const completionPct = onboarding?.completion_percentage ?? 0

  const { data: matches, isError: matchesError } = useQuery({
    queryKey: ['matches'],
    queryFn: () => getMatches(),
    enabled: completionPct >= 80,
  })

  const { deadlines, isError: deadlinesError, applications } = useDeadlines()

  const applicationsList: Application[] = Array.isArray(applications) ? applications : []
  const matchCount = Array.isArray(matches) ? matches.length : 0
  const appCount = applicationsList.length
  const draftCount = applicationsList.filter(a => a.status === 'draft').length
  const nextDeadline = deadlines[0] ?? null
  const nextDeadlineDays = nextDeadline ? differenceInDays(nextDeadline.date, new Date()) : null

  const nextActions = useMemo(() => {
    const apps: Application[] = Array.isArray(applications) ? applications : []
    const actions = buildActions(apps)
    const sorted = [...actions]
    if (sortKey === 'priority') {
      sorted.sort((a, b) => PRIORITY_ORDER[a.priority] - PRIORITY_ORDER[b.priority])
    } else if (sortKey === 'deadline') {
      sorted.sort((a, b) => (a.daysLeft ?? 999) - (b.daysLeft ?? 999))
    } else {
      sorted.sort((a, b) => {
        const aDraft = a.action.startsWith('Complete') || a.action.startsWith('Upload') ? 0 : 1
        const bDraft = b.action.startsWith('Complete') || b.action.startsWith('Upload') ? 0 : 1
        return aDraft - bDraft || PRIORITY_ORDER[a.priority] - PRIORITY_ORDER[b.priority]
      })
    }
    return sorted
  }, [applications, sortKey])

  const statusCounts = useMemo(() => {
    const apps: Application[] = Array.isArray(applications) ? applications : []
    const counts: Record<string, number> = {}
    for (const a of apps) {
      counts[a.status] = (counts[a.status] || 0) + 1
    }
    return counts
  }, [applications])

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Today with your admissions counselor</h1>
        <p className="text-sm text-gray-500 mt-1">What matters now, what is next, and what can wait.</p>
      </div>

      {(matchesError || deadlinesError) && (
        <Card className="p-4 border-amber-200 bg-amber-50">
          <div className="flex items-start gap-2 text-amber-800">
            <AlertTriangle size={16} className="mt-0.5" />
            <p className="text-sm">Some data could not load. The page is still usable.</p>
          </div>
        </Card>
      )}

      {/* Counselor brief */}
      <Card className="p-5">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <ShieldCheck size={17} className="text-brand-slate-600" />
              <h2 className="font-semibold text-brand-slate-700">Counselor Brief</h2>
            </div>
            <p className="text-sm text-brand-slate-600">
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

      {/* Profile Completion */}
      {completionPct < 100 && (
        <Card className="p-5">
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-center gap-2">
              <User size={18} className="text-gray-600" />
              <h2 className="font-semibold text-brand-slate-700">Profile Completion</h2>
            </div>
            <Button size="sm" variant="secondary" onClick={() => navigate('/s/profile')}>
              Complete Profile <ArrowRight size={14} className="ml-1" />
            </Button>
          </div>
          {onbLoading ? (
            <Skeleton className="h-6" />
          ) : (
            <>
              <p className="text-sm text-gray-600 mb-2">
                {completionPct < 30 ? 'Getting started' : completionPct < 60 ? 'Building momentum' : completionPct < 80 ? 'Almost there' : 'Looking strong'}
              </p>
              <ProgressBar value={completionPct} />
              {completionPct < 80 && (
                <p className="text-sm text-sky-700 bg-sky-50 rounded-xl px-3 py-2 mt-3">
                  A few more details will help us find better fits for you.
                </p>
              )}
            </>
          )}
        </Card>
      )}

      {/* Next Actions */}
      <Card className="p-5">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-2">
            <Zap size={18} className="text-amber-500" />
            <h2 className="font-semibold text-brand-slate-700">Next Actions</h2>
          </div>
          <div className="flex gap-1">
            {(['priority', 'deadline', 'readiness'] as const).map(key => (
              <button
                key={key}
                onClick={() => setSortKey(key)}
                className={`px-2 py-0.5 text-xs rounded-full border transition-colors ${
                  sortKey === key
                    ? 'bg-stone-800 text-white border-stone-800'
                    : 'bg-white text-gray-500 border-gray-200 hover:bg-gray-50'
                }`}
              >
                {key.charAt(0).toUpperCase() + key.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {nextActions.length === 0 ? (
          <p className="text-sm text-gray-500 py-4 text-center">
            No active applications — start by saving programs you are interested in.
          </p>
        ) : (
          <div className="space-y-2">
            {nextActions.map(na => {
              const badge = PRIORITY_BADGE[na.priority]
              return (
                <button
                  key={na.appId}
                  onClick={() => navigate(`/s/applications/${na.appId}`)}
                  className="w-full text-left flex items-center gap-3 p-3 rounded-lg border border-gray-100 hover:bg-gray-50 transition-colors"
                >
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-stone-700 truncate">
                      {na.programName}
                    </p>
                    {na.institutionName && (
                      <p className="text-xs text-gray-500 truncate">{na.institutionName}</p>
                    )}
                    <p className="text-xs text-gray-600 mt-0.5">{na.action}</p>
                  </div>
                  <Badge variant={badge.variant} size="sm">{badge.label}</Badge>
                  <ArrowRight size={14} className="text-gray-400 shrink-0" />
                </button>
              )
            })}
          </div>
        )}

        {/* Portfolio summary badges */}
        {appCount > 0 && (
          <div className="flex flex-wrap gap-2 mt-4 pt-3 border-t border-gray-100">
            {Object.entries(STATUS_LABELS).map(([status, label]) => {
              const count = statusCounts[status]
              if (!count) return null
              return (
                <Badge key={status} variant="neutral" size="sm">
                  {label}: {count}
                </Badge>
              )
            })}
          </div>
        )}
      </Card>

      {/* Summary stats row */}
      <div className="grid grid-cols-3 gap-4">
        <Card className="p-4 text-center cursor-pointer hover:bg-gray-50" onClick={() => navigate('/s/discover')}>
          <Sparkles size={20} className="mx-auto text-purple-500 mb-1" />
          <p className="text-2xl font-bold">{matchCount}</p>
          <p className="text-xs text-gray-500">AI Matches</p>
        </Card>
        <Card className="p-4 text-center cursor-pointer hover:bg-gray-50" onClick={() => navigate('/s/applications')}>
          <FileText size={20} className="mx-auto text-blue-500 mb-1" />
          <p className="text-2xl font-bold">{appCount}</p>
          <p className="text-xs text-gray-500">Applications</p>
        </Card>
        <Card className="p-4 text-center cursor-pointer hover:bg-gray-50" onClick={() => navigate('/s/calendar')}>
          <Calendar size={20} className="mx-auto text-amber-500 mb-1" />
          <p className="text-2xl font-bold">{deadlines.length}</p>
          <p className="text-xs text-gray-500">Deadlines</p>
        </Card>
      </div>

      {/* Next deadline alert */}
      {nextDeadline && nextDeadlineDays != null && nextDeadlineDays <= 14 && (
        <Card className="p-4 border-amber-200 bg-amber-50 cursor-pointer hover:bg-amber-100" onClick={() => navigate(nextDeadline.link)}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-amber-900">{nextDeadline.label}</p>
              <p className="text-xs text-amber-700">{formatDate(nextDeadline.date.toISOString())} — {nextDeadlineDays === 0 ? 'Today' : `${nextDeadlineDays} days away`}</p>
            </div>
            <ArrowRight size={16} className="text-amber-600" />
          </div>
        </Card>
      )}

      {/* Quick Actions */}
      <Card className="p-5">
        <h2 className="font-semibold text-brand-slate-700 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-2 gap-3">
          {completionPct < 100 && (
            <button
              onClick={() => navigate('/s/profile')}
              className="flex items-center gap-3 p-3 rounded-lg border border-gray-100 hover:bg-gray-50 text-left"
            >
              <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
                <User size={16} className="text-blue-600" />
              </div>
              <span className="text-sm font-medium">Complete profile</span>
            </button>
          )}
          <button
            onClick={() => navigate('/s/discover')}
            className="flex items-center gap-3 p-3 rounded-lg border border-gray-100 hover:bg-gray-50 text-left"
          >
            <div className="w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center">
              <Search size={16} className="text-purple-600" />
            </div>
            <span className="text-sm font-medium">Explore programs</span>
          </button>
          <button
            onClick={() => navigate('/s/chat')}
            className="flex items-center gap-3 p-3 rounded-lg border border-gray-100 hover:bg-gray-50 text-left"
          >
            <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center">
              <MessageSquare size={16} className="text-green-600" />
            </div>
            <span className="text-sm font-medium">Talk with counselor</span>
          </button>
          {draftCount > 0 && (
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
              <span className="text-sm font-medium">Continue draft app</span>
            </button>
          )}
        </div>
      </Card>
    </div>
  )
}
