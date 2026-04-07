import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getOnboarding, getNextStep } from '../../api/students'
import { getMatches } from '../../api/matching'
import { useDeadlines } from '../../hooks/useDeadlines'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import ProgressBar from '../../components/ui/ProgressBar'
import Skeleton from '../../components/ui/Skeleton'
import {
  MessageSquare, Search, FileText, User,
  ArrowRight, ShieldCheck, AlertTriangle, Sparkles, Calendar,
} from 'lucide-react'
import { differenceInDays } from 'date-fns'
import { formatDate } from '../../utils/format'
import type { Application } from '../../types'

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

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Today with your admissions counselor</h1>
        <p className="text-sm text-stone-500 mt-1">What matters now, what is next, and what can wait.</p>
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
              <ShieldCheck size={17} className="text-stone-700" />
              <h2 className="font-semibold text-stone-800">Counselor Brief</h2>
            </div>
            <p className="text-sm text-stone-700">
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
              <User size={18} className="text-stone-600" />
              <h2 className="font-semibold text-stone-800">Profile Completion</h2>
            </div>
            <Button size="sm" variant="secondary" onClick={() => navigate('/s/profile')}>
              Complete Profile <ArrowRight size={14} className="ml-1" />
            </Button>
          </div>
          {onbLoading ? (
            <Skeleton className="h-6" />
          ) : (
            <>
              <p className="text-sm text-stone-600 mb-2">
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

      {/* Summary stats row */}
      <div className="grid grid-cols-3 gap-4">
        <Card className="p-4 text-center cursor-pointer hover:bg-stone-50" onClick={() => navigate('/s/discover')}>
          <Sparkles size={20} className="mx-auto text-purple-500 mb-1" />
          <p className="text-2xl font-bold">{matchCount}</p>
          <p className="text-xs text-stone-500">AI Matches</p>
        </Card>
        <Card className="p-4 text-center cursor-pointer hover:bg-stone-50" onClick={() => navigate('/s/applications')}>
          <FileText size={20} className="mx-auto text-blue-500 mb-1" />
          <p className="text-2xl font-bold">{appCount}</p>
          <p className="text-xs text-stone-500">Applications</p>
        </Card>
        <Card className="p-4 text-center cursor-pointer hover:bg-stone-50" onClick={() => navigate('/s/calendar')}>
          <Calendar size={20} className="mx-auto text-amber-500 mb-1" />
          <p className="text-2xl font-bold">{deadlines.length}</p>
          <p className="text-xs text-stone-500">Deadlines</p>
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
        <h2 className="font-semibold text-stone-800 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-2 gap-3">
          {completionPct < 100 && (
            <button
              onClick={() => navigate('/s/profile')}
              className="flex items-center gap-3 p-3 rounded-lg border border-stone-100 hover:bg-stone-50 text-left"
            >
              <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
                <User size={16} className="text-blue-600" />
              </div>
              <span className="text-sm font-medium">Complete profile</span>
            </button>
          )}
          <button
            onClick={() => navigate('/s/discover')}
            className="flex items-center gap-3 p-3 rounded-lg border border-stone-100 hover:bg-stone-50 text-left"
          >
            <div className="w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center">
              <Search size={16} className="text-purple-600" />
            </div>
            <span className="text-sm font-medium">Explore programs</span>
          </button>
          <button
            onClick={() => navigate('/s/chat')}
            className="flex items-center gap-3 p-3 rounded-lg border border-stone-100 hover:bg-stone-50 text-left"
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
              className="flex items-center gap-3 p-3 rounded-lg border border-stone-100 hover:bg-stone-50 text-left"
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
