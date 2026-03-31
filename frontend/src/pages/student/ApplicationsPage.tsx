import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { listMyApplications } from '../../api/applications'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Tabs from '../../components/ui/Tabs'
import EmptyState from '../../components/ui/EmptyState'
import { SkeletonCard } from '../../components/ui/Skeleton'
import { formatDate, formatScore } from '../../utils/format'
import { toBadgeVariant } from '../../utils/constants'
import { FileText } from 'lucide-react'
import type { Application } from '../../types'

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

  const filtered = filter === 'all'
    ? (applications ?? [])
    : (applications ?? []).filter((a: Application) => a.status === filter)

  if (isLoading) return <div className="p-6 space-y-4">{Array.from({ length: 3 }).map((_, i) => <SkeletonCard key={i} />)}</div>

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <h1 className="text-2xl font-semibold mb-4">My Applications</h1>

      <Tabs tabs={FILTER_TABS} activeTab={filter} onChange={setFilter} />

      <div className="mt-4 space-y-3">
        {filtered.length === 0 ? (
          <EmptyState
            icon={<FileText size={48} />}
            title="No applications yet"
            description="Discover programs to get started."
            action={{ label: 'Discover', onClick: () => navigate('/s/discover') }}
          />
        ) : (
          filtered.map((app: Application) => (
            <Card
              key={app.id}
              onClick={() => navigate(`/s/applications/${app.id}`)}
              className="p-4"
            >
              <div className="flex justify-between items-start">
                <div>
                  <p className="font-semibold text-sm">{app.program?.program_name || 'Program'}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge variant={toBadgeVariant(app.status)}>
                      {app.status.replace(/_/g, ' ')}
                    </Badge>
                    {app.match_score != null && (
                      <span className="text-xs text-gray-500">Match: {formatScore(app.match_score)}</span>
                    )}
                  </div>
                  {app.submitted_at && (
                    <p className="text-xs text-gray-400 mt-1">Submitted: {formatDate(app.submitted_at)}</p>
                  )}
                  {app.decision && (
                    <Badge variant={toBadgeVariant(app.decision)} className="mt-1">
                      {app.decision}
                    </Badge>
                  )}
                </div>
                <span className="text-xs text-gray-400">{app.status === 'draft' ? 'Continue' : 'View'} →</span>
              </div>
            </Card>
          ))
        )}
      </div>
    </div>
  )
}
