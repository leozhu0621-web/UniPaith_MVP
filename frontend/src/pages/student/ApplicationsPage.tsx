import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { listMyApplications } from '../../api/applications'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Tabs from '../../components/ui/Tabs'
import EmptyState from '../../components/ui/EmptyState'
import { SkeletonCard } from '../../components/ui/Skeleton'
import { formatDate } from '../../utils/format'
import { STATUS_COLORS } from '../../utils/constants'
import { FileText, Target, TrendingUp, Shield } from 'lucide-react'
import CounselorNudge from './components/CounselorNudge'
import type { Application } from '../../types'

function classifyApp(matchScore: number | null): { label: string; color: string; icon: typeof Target } {
  if (matchScore == null) return { label: 'Unrated', color: 'text-gray-400 bg-gray-50', icon: Target }
  if (matchScore >= 75) return { label: 'Target', color: 'text-emerald-700 bg-emerald-50', icon: Target }
  if (matchScore >= 50) return { label: 'Good Fit', color: 'text-blue-700 bg-blue-50', icon: TrendingUp }
  return { label: 'Reach', color: 'text-amber-700 bg-amber-50', icon: Shield }
}

const FILTER_TABS = [
  { id: 'all', label: 'All' },
  { id: 'draft', label: 'Draft' },
  { id: 'submitted', label: 'Submitted' },
  { id: 'under_review', label: 'Under Review' },
  { id: 'decision_made', label: 'Decision' },
]

export default function ApplicationsPage() {
  const navigate = useNavigate()
  const [filter, setFilter] = useState('all')

  const { data: applications, isLoading } = useQuery({
    queryKey: ['my-applications'],
    queryFn: listMyApplications,
  })
  const applicationsList: Application[] = Array.isArray(applications) ? applications : []

  const filtered = filter === 'all'
    ? applicationsList
    : applicationsList.filter((a: Application) => a.status === filter)

  if (isLoading) return <div className="p-6 space-y-4">{Array.from({ length: 3 }).map((_, i) => <SkeletonCard key={i} />)}</div>

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <h1 className="text-2xl font-semibold mb-4">My Applications</h1>

      {applicationsList.length === 0 && (
        <div className="mb-4">
          <CounselorNudge
            message="Your counselor can help you decide which programs to apply to first based on your profile and goals."
            actionLabel="Ask counselor"
            actionTo="/s/chat?prefill=Which programs should I apply to first based on my profile?"
          />
        </div>
      )}

      <Tabs tabs={FILTER_TABS} activeTab={filter} onChange={setFilter} />

      <div className="mt-4 space-y-3">
        {filtered.length === 0 ? (
          <EmptyState
            icon={<FileText size={48} />}
            title="Your applications will appear here"
            description="Save programs you're interested in, then start applications when you're ready."
            action={{ label: 'Explore programs', onClick: () => navigate('/s/explore') }}
          />
        ) : (
          filtered.map((app: Application) => {
            const cls = classifyApp(app.match_score)
            const deadline = app.program?.application_deadline
            const daysLeft = deadline ? Math.ceil((new Date(deadline).getTime() - Date.now()) / 86400000) : null
            return (
              <Card
                key={app.id}
                onClick={() => navigate(`/s/applications/${app.id}`)}
                className="p-4 hover:shadow-sm transition-shadow"
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="font-semibold text-sm text-student-ink truncate">{app.program?.program_name || 'Program'}</p>
                      <span className={`px-2 py-0.5 text-[10px] font-medium rounded-full ${cls.color}`}>{cls.label}</span>
                    </div>
                    {(app.program as any)?.institution_name && (
                      <p className="text-xs text-student-text mt-0.5">{(app.program as any).institution_name}</p>
                    )}
                    <div className="flex items-center gap-2 mt-1.5">
                      <Badge variant={(STATUS_COLORS[app.status] || 'neutral') as any}>
                        {app.status.replace(/_/g, ' ')}
                      </Badge>
                      {app.decision && (
                        <Badge variant={(STATUS_COLORS[app.decision] || 'neutral') as any}>
                          {app.decision}
                        </Badge>
                      )}
                      {daysLeft != null && daysLeft >= 0 && daysLeft <= 30 && app.status === 'draft' && (
                        <span className={`text-[10px] font-medium ${daysLeft <= 7 ? 'text-red-600' : 'text-amber-600'}`}>
                          {daysLeft === 0 ? 'Due today' : `${daysLeft}d left`}
                        </span>
                      )}
                    </div>
                    {app.submitted_at && (
                      <p className="text-xs text-gray-400 mt-1">Submitted {formatDate(app.submitted_at)}</p>
                    )}
                  </div>
                  <span className="text-xs text-student-text flex-shrink-0">{app.status === 'draft' ? 'Continue →' : 'View →'}</span>
                </div>
              </Card>
            )
          })
        )}
      </div>
    </div>
  )
}
