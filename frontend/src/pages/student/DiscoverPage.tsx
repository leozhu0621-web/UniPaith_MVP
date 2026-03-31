import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getMatches, logEngagement } from '../../api/matching'
import { searchPrograms } from '../../api/programs'
import { getOnboarding } from '../../api/students'
import Badge from '../../components/ui/Badge'
import Card from '../../components/ui/Card'
import Skeleton from '../../components/ui/Skeleton'
import { Search } from 'lucide-react'
import { formatCurrency, formatScore } from '../../utils/format'
import { DEGREE_LABELS, TIER_LABELS } from '../../utils/constants'
import type { MatchResult, ProgramSummary } from '../../types'

export default function DiscoverPage() {
  const navigate = useNavigate()
  const [q, setQ] = useState('')
  const [page, setPage] = useState(1)

  const { data: onboarding } = useQuery({ queryKey: ['onboarding'], queryFn: getOnboarding })
  const showMatches = (onboarding?.completion_percentage ?? 0) >= 80

  const { data: matches, isLoading: matchesLoading } = useQuery({
    queryKey: ['matches'],
    queryFn: () => getMatches(),
    enabled: showMatches,
  })

  const { data: browseData, isLoading: browseLoading } = useQuery({
    queryKey: ['programs', { q, page }],
    queryFn: () => searchPrograms({ q: q || undefined, page, page_size: 12 }),
  })

  const matchesByTier: Record<number, MatchResult[]> = { 3: [], 2: [], 1: [] }
  ;(matches ?? []).forEach((m: MatchResult) => {
    if (matchesByTier[m.match_tier]) matchesByTier[m.match_tier].push(m)
  })

  const handleCardClick = (programId: string) => {
    logEngagement(programId, 'viewed_program', 1).catch(() => {})
    navigate(`/s/schools/${programId}`)
  }

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <h1 className="text-2xl font-semibold mb-2">Discover Programs</h1>

      {!showMatches && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg px-4 py-3 mb-6 text-sm text-blue-800">
          Complete your profile (80%+) to see AI-powered matches.{' '}
          <button onClick={() => navigate('/s/profile')} className="font-medium underline">Complete profile</button>
        </div>
      )}

      {showMatches && (
        <div className="mb-8">
          <h2 className="text-lg font-medium mb-4">Your AI Matches</h2>
          {matchesLoading ? (
            <div className="flex gap-4">{Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-32 w-64" />)}</div>
          ) : (matches ?? []).length === 0 ? (
            <p className="text-sm text-gray-500">No matches yet — check back after your profile is processed.</p>
          ) : (
            [3, 2, 1].map(tier => {
              const items = matchesByTier[tier]
              if (!items.length) return null
              const tierInfo = TIER_LABELS[tier]
              return (
                <div key={tier} className="mb-6">
                  <div className="flex items-center gap-2 mb-2">
                    <Badge variant={tierInfo.color as any}>{tierInfo.label}</Badge>
                    <span className="text-sm text-gray-500">({items.length} programs)</span>
                  </div>
                  <div className="flex gap-3 overflow-x-auto pb-2">
                    {items.sort((a, b) => b.match_score - a.match_score).map(m => (
                      <Card key={m.id} onClick={() => handleCardClick(m.program_id)} className="flex-shrink-0 w-64 p-4">
                        <p className="font-semibold text-sm truncate">{m.program?.program_name || 'Program'}</p>
                        <p className="text-xs text-gray-500 mt-1 truncate">{m.program?.department || ''}</p>
                        <div className="flex items-center justify-between mt-3">
                          <span className="text-lg font-bold">{formatScore(m.match_score)}</span>
                          <Badge variant={tierInfo.color as any} size="sm">{tierInfo.label}</Badge>
                        </div>
                        {m.program?.tuition != null && (
                          <p className="text-xs text-gray-400 mt-1">{formatCurrency(m.program.tuition)}</p>
                        )}
                      </Card>
                    ))}
                  </div>
                </div>
              )
            })
          )}
        </div>
      )}

      <h2 className="text-lg font-medium mb-3">Browse All Programs</h2>
      <div className="relative mb-4">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
        <input
          type="text" value={q} onChange={e => { setQ(e.target.value); setPage(1) }}
          placeholder="Search programs..."
          className="w-full pl-9 pr-4 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-900"
        />
      </div>

      {browseLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-28" />)}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {(browseData?.items ?? []).map((p: ProgramSummary) => (
            <Card key={p.id} onClick={() => handleCardClick(p.id)} className="p-4">
              <p className="font-semibold text-sm truncate">{p.program_name}</p>
              <p className="text-xs text-gray-500 mt-1">{p.institution_name} — {p.institution_country}</p>
              <div className="flex items-center gap-2 mt-2">
                <Badge variant="info" size="sm">{DEGREE_LABELS[p.degree_type] || p.degree_type}</Badge>
                {p.tuition != null && <span className="text-xs text-gray-500">{formatCurrency(p.tuition)}</span>}
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
