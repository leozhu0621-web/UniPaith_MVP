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
import CounselorSessionCard from './components/CounselorSessionCard'
import CounselorNudge from './components/CounselorNudge'
import { listSaved } from '../../api/saved-lists'
import {
  MessageSquare, Search, FileText, User,
  ArrowRight, AlertTriangle, Sparkles, Calendar, Zap,
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

  const { data: savedList } = useQuery({
    queryKey: ['saved'],
    queryFn: listSaved,
  })

  const applicationsList: Application[] = Array.isArray(applications) ? applications : []
  const matchCount = Array.isArray(matches) ? matches.length : 0
  const savedCount = Array.isArray(savedList) ? savedList.length : 0
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

  const journeyStage = completionPct < 30
    ? { label: 'Self-Discovery', color: 'text-purple-600', desc: 'Understanding who you are and what you want' }
    : completionPct < 60
      ? { label: 'Exploration', color: 'text-blue-600', desc: 'Discovering programs that fit your unique story' }
      : completionPct < 80
        ? { label: 'Refinement', color: 'text-amber-600', desc: 'Sharpening your preferences and building your narrative' }
        : appCount > 0
          ? { label: 'Application', color: 'text-emerald-600', desc: 'Bringing your best self to each program' }
          : { label: 'Ready to Apply', color: 'text-emerald-600', desc: 'Your profile is strong — time to take the next step' }

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-6">
      <div>
        <div className="flex items-center gap-2 mb-1">
          <Sparkles size={20} className="text-amber-500" />
          <span className={`text-xs font-semibold uppercase tracking-wider ${journeyStage.color}`}>{journeyStage.label} Phase</span>
        </div>
        <h1 className="text-2xl font-semibold text-stone-800">Your Journey Today</h1>
        <p className="text-sm text-gray-500 mt-1">{journeyStage.desc}</p>
      </div>

      {(matchesError || deadlinesError) && (
        <Card className="p-4 border-amber-200 bg-amber-50">
          <div className="flex items-start gap-2 text-amber-800">
            <AlertTriangle size={16} className="mt-0.5" />
            <p className="text-sm">Some data could not load. The page is still usable.</p>
          </div>
        </Card>
      )}

      {/* AI Counselor Session Card */}
      <CounselorSessionCard
        guidanceText={
          nextStep?.guidance_text
            ? nextStep.guidance_text
            : completionPct < 30
              ? "Welcome! I'm your private college counselor. Let's start by getting to know you — your goals, interests, and what kind of future excites you."
              : completionPct < 60
                ? "You're building a strong foundation. Let's explore what programs might be the right fit for who you are becoming."
                : completionPct < 80
                  ? "Your story is coming together. A few more details will help me find programs where you'll truly thrive."
                  : "Your profile is looking great. Ready to discover your best-fit programs?"
        }
        completionPct={completionPct}
        matchCount={matchCount}
        savedCount={savedCount}
        appCount={appCount}
      />

      {/* Journey flow nudge — adapts to student's stage */}
      {completionPct < 80 && (
        <CounselorNudge
          message={`Your story is ${completionPct}% complete. A few more details help me find programs where you truly belong.`}
          actionLabel="Continue your story"
          actionTo="/s/profile"
          counselorLink="/s/chat?prefill=What should I add to my profile next?"
        />
      )}
      {completionPct >= 80 && matchCount === 0 && (
        <CounselorNudge
          message="Your profile looks strong. Let me show you programs that match who you are."
          actionLabel="Explore programs"
          actionTo="/s/discover"
          variant="celebrate"
        />
      )}
      {matchCount > 0 && savedCount === 0 && (
        <CounselorNudge
          message={`I found ${matchCount} programs that could be great for you. Save the ones that resonate.`}
          actionLabel="View matches"
          actionTo="/s/discover"
          variant="suggestion"
        />
      )}
      {savedCount > 0 && appCount === 0 && (
        <CounselorNudge
          message={`You have ${savedCount} programs saved. Ready to take the next step?`}
          actionLabel="Start applying"
          actionTo="/s/applications"
          variant="celebrate"
          counselorLink="/s/chat?prefill=Which of my saved programs should I apply to first?"
        />
      )}
      {draftCount > 0 && (
        <CounselorNudge
          message={`You have ${draftCount} application${draftCount > 1 ? 's' : ''} in progress. Let me help you finish strong.`}
          actionLabel="Continue application"
          actionTo={`/s/applications/${applicationsList.find(a => a.status === 'draft')?.id || ''}`}
          variant="urgent"
          counselorLink="/s/chat?prefill=Help me with my application in progress"
        />
      )}

      {/* Self-Discovery Progress */}
      {completionPct < 100 && (
        <Card className="p-5">
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-center gap-2">
              <User size={18} className="text-stone-600" />
              <div>
                <h2 className="font-semibold text-stone-700">Your Story</h2>
                <p className="text-[10px] text-gray-400">The more I know, the better I can guide you</p>
              </div>
            </div>
            <Button size="sm" variant="secondary" onClick={() => navigate('/s/profile')}>
              Continue <ArrowRight size={14} className="ml-1" />
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
          <div className="text-center py-6">
            <p className="text-sm text-gray-500 mb-3">
              {savedCount > 0
                ? `You have ${savedCount} programs saved. When you're ready, start an application and your next steps will appear here.`
                : "Your next steps will appear here once you start exploring and applying to programs."}
            </p>
            <Button size="sm" variant="secondary" onClick={() => navigate(savedCount > 0 ? '/s/saved' : '/s/discover')}>
              {savedCount > 0 ? 'View saved programs' : 'Explore programs'} <ArrowRight size={14} className="ml-1" />
            </Button>
          </div>
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

      {/* Summary stats row — only show when there's meaningful data */}
      {(matchCount > 0 || appCount > 0 || deadlines.length > 0) && (
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
      )}

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
