import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ClipboardCheck, Search } from 'lucide-react'
import { getInstitutionPrograms } from '../../api/institutions'
import { getApplicationsByProgram } from '../../api/applications-admin'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Select from '../../components/ui/Select'
import Input from '../../components/ui/Input'
import Skeleton from '../../components/ui/Skeleton'
import EmptyState from '../../components/ui/EmptyState'
import { formatDate, formatScore } from '../../utils/format'
import { STATUS_COLORS } from '../../utils/constants'
import type { Program, Application } from '../../types'

export default function ReviewQueuePage() {
  const navigate = useNavigate()
  const [selectedProgram, setSelectedProgram] = useState('')
  const [search, setSearch] = useState('')

  const programsQ = useQuery({ queryKey: ['institution-programs'], queryFn: getInstitutionPrograms })
  const programs: Program[] = programsQ.data ?? []

  const appsQ = useQuery({
    queryKey: ['review-queue-apps', selectedProgram],
    queryFn: () => getApplicationsByProgram(selectedProgram),
    enabled: !!selectedProgram,
  })
  const applications: Application[] = appsQ.data ?? []

  const reviewableApps = applications.filter(
    a => a.status === 'submitted' || a.status === 'under_review'
  )

  const filtered = reviewableApps.filter(
    a => !search || a.student_id.toLowerCase().includes(search.toLowerCase())
  )

  // Simple heuristic: if match_score exists, it's been partially reviewed; if decision, it's fully reviewed
  const pendingReview = filtered.filter(a => !a.decision)
  const reviewed = filtered.filter(a => !!a.decision)

  const programOptions = programs.map(p => ({ value: p.id, label: p.program_name }))

  const AppRow = ({ app }: { app: Application }) => (
    <div
      onClick={() => navigate(`/i/pipeline/${app.id}`)}
      className="flex items-center gap-4 p-3 border-b border-gray-100 hover:bg-gray-50 cursor-pointer"
    >
      <input type="checkbox" className="rounded border-gray-300" onClick={e => e.stopPropagation()} />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-900 truncate">{app.student_id.slice(0, 12)}...</p>
        <p className="text-xs text-gray-500">{app.program?.program_name ?? 'Program'}</p>
      </div>
      <div className="text-sm text-gray-600">
        {app.match_score != null ? formatScore(app.match_score / 100) : '\u2014'}
      </div>
      <Badge variant={(STATUS_COLORS[app.status] as any) ?? 'neutral'}>
        {app.status.replace('_', ' ')}
      </Badge>
      <div className="text-xs text-gray-400 w-24 text-right">{formatDate(app.submitted_at)}</div>
    </div>
  )

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Review Queue</h1>
      </div>

      <div className="flex items-center gap-4">
        <Select
          options={programOptions}
          placeholder="Select Program"
          value={selectedProgram}
          onChange={e => setSelectedProgram(e.target.value)}
          className="w-64"
        />
        <div className="relative flex-1 max-w-xs">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <Input
            placeholder="Search..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
      </div>

      {!selectedProgram ? (
        <EmptyState
          icon={<ClipboardCheck size={40} />}
          title="Select a program"
          description="Choose a program to see its review queue."
        />
      ) : appsQ.isLoading ? (
        <div className="space-y-2">{Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-14" />)}</div>
      ) : (
        <div className="space-y-6">
          {/* Pending */}
          <Card>
            <div className="px-4 py-3 border-b border-gray-200">
              <h3 className="text-sm font-semibold text-gray-900">
                Pending Review <span className="text-gray-400 font-normal">({pendingReview.length})</span>
              </h3>
            </div>
            {pendingReview.length === 0 ? (
              <p className="text-sm text-gray-500 text-center py-6">No pending reviews</p>
            ) : (
              pendingReview.map(app => <AppRow key={app.id} app={app} />)
            )}
          </Card>

          {/* Reviewed */}
          <Card>
            <div className="px-4 py-3 border-b border-gray-200">
              <h3 className="text-sm font-semibold text-gray-900">
                Reviewed <span className="text-gray-400 font-normal">({reviewed.length})</span>
              </h3>
            </div>
            {reviewed.length === 0 ? (
              <p className="text-sm text-gray-500 text-center py-6">No reviewed applications</p>
            ) : (
              reviewed.map(app => <AppRow key={app.id} app={app} />)
            )}
          </Card>
        </div>
      )}
    </div>
  )
}
