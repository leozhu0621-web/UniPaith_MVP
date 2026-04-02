import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery } from '@tanstack/react-query'
import { chatStudentAssistant, getMatches, logEngagement } from '../../api/matching'
import { searchPrograms } from '../../api/programs'
import { getOnboarding } from '../../api/students'
import Badge from '../../components/ui/Badge'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import Skeleton from '../../components/ui/Skeleton'
import { Search, SlidersHorizontal, X, ChevronDown } from 'lucide-react'
import { formatCurrency, formatScore } from '../../utils/format'
import { DEGREE_LABELS, TIER_LABELS } from '../../utils/constants'
import type { MatchResult, ProgramSummary } from '../../types'

const SORT_OPTIONS = [
  { value: 'relevance', label: 'Relevance' },
  { value: 'tuition_asc', label: 'Tuition: Low → High' },
  { value: 'tuition_desc', label: 'Tuition: High → Low' },
  { value: 'deadline', label: 'Deadline: Soonest' },
]

const COUNTRY_OPTIONS = [
  'United States', 'United Kingdom', 'Canada', 'Australia',
  'Germany', 'Netherlands', 'France', 'Singapore', 'Japan', 'South Korea',
]

export default function DiscoverPage() {
  const navigate = useNavigate()
  const [q, setQ] = useState('')
  const [page, setPage] = useState(1)
  const [showFilters, setShowFilters] = useState(false)
  const [sortBy, setSortBy] = useState('relevance')
  const [assistantMessage, setAssistantMessage] = useState('')
  const [assistantReply, setAssistantReply] = useState<string | null>(null)

  // Filter state
  const [country, setCountry] = useState('')
  const [degreeType, setDegreeType] = useState('')
  const [minTuition, setMinTuition] = useState('')
  const [maxTuition, setMaxTuition] = useState('')

  const { data: onboarding } = useQuery({ queryKey: ['onboarding'], queryFn: getOnboarding })
  const showMatches = (onboarding?.completion_percentage ?? 0) >= 80

  const { data: matches, isLoading: matchesLoading } = useQuery({
    queryKey: ['matches'],
    queryFn: () => getMatches(),
    enabled: showMatches,
  })

  const { data: browseData, isLoading: browseLoading } = useQuery({
    queryKey: ['programs', { q, page, country, degreeType, minTuition, maxTuition }],
    queryFn: () => searchPrograms({
      q: q || undefined,
      page,
      page_size: 12,
      country: country || undefined,
      degree_type: degreeType || undefined,
      min_tuition: minTuition ? Number(minTuition) : undefined,
      max_tuition: maxTuition ? Number(maxTuition) : undefined,
    }),
  })

  const assistantMut = useMutation({
    mutationFn: (message: string) => chatStudentAssistant(message),
    onSuccess: (data: { reply: string }) => {
      setAssistantReply(data.reply)
    },
  })

  const matchesByTier: Record<number, MatchResult[]> = { 3: [], 2: [], 1: [] }
  const matchesList: MatchResult[] = Array.isArray(matches) ? matches : []
  matchesList.forEach((m: MatchResult) => {
    if (matchesByTier[m.match_tier]) matchesByTier[m.match_tier].push(m)
  })

  const handleCardClick = (programId: string) => {
    logEngagement(programId, 'viewed_program', 1).catch(() => {})
    navigate(`/s/schools/${programId}`)
  }

  const resetFilters = () => {
    setCountry('')
    setDegreeType('')
    setMinTuition('')
    setMaxTuition('')
    setPage(1)
  }

  const activeFilterCount = [country, degreeType, minTuition, maxTuition].filter(Boolean).length

  // Sort programs client-side
  const browseItems: ProgramSummary[] = Array.isArray(browseData?.items) ? browseData.items : []
  const programs = [...browseItems]
  if (sortBy === 'tuition_asc') programs.sort((a, b) => (a.tuition ?? Infinity) - (b.tuition ?? Infinity))
  else if (sortBy === 'tuition_desc') programs.sort((a, b) => (b.tuition ?? 0) - (a.tuition ?? 0))
  else if (sortBy === 'deadline') programs.sort((a, b) => {
    const da = a.application_deadline ? new Date(a.application_deadline).getTime() : Infinity
    const db = b.application_deadline ? new Date(b.application_deadline).getTime() : Infinity
    return da - db
  })

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <h1 className="text-2xl font-semibold mb-2">Discover Programs</h1>

      {!showMatches && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg px-4 py-3 mb-6 text-sm text-blue-800">
          Complete your profile (80%+) to see AI-powered matches.{' '}
          <button onClick={() => navigate('/s/profile')} className="font-medium underline">Complete profile</button>
        </div>
      )}

      <Card className="p-4 mb-6">
        <h2 className="text-lg font-medium mb-2">UniPaith AI Assistant (OpenAI)</h2>
        <p className="text-sm text-gray-500 mb-3">
          Ask for advice on program fit, profile gaps, and next steps.
        </p>
        <div className="flex gap-2">
          <input
            value={assistantMessage}
            onChange={e => setAssistantMessage(e.target.value)}
            placeholder="Ask: How can I improve my match quality for data science programs?"
            className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-900"
          />
          <Button
            onClick={() => assistantMut.mutate(assistantMessage)}
            disabled={assistantMut.isPending || !assistantMessage.trim()}
          >
            {assistantMut.isPending ? 'Thinking...' : 'Ask AI'}
          </Button>
        </div>
        {assistantReply && (
          <div className="mt-3 bg-gray-50 border border-gray-200 rounded-lg p-3">
            <p className="text-xs text-gray-500 mb-1">Assistant reply</p>
            <p className="text-sm text-gray-700 whitespace-pre-wrap">{assistantReply}</p>
          </div>
        )}
      </Card>

      {showMatches && (
        <div className="mb-8">
          <h2 className="text-lg font-medium mb-4">Your AI Matches</h2>
          {matchesLoading ? (
            <div className="flex gap-4">{Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-32 w-64" />)}</div>
          ) : matchesList.length === 0 ? (
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

      {/* Search + Filter Bar */}
      <div className="flex gap-3 mb-4">
        <div className="relative flex-1">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text" value={q} onChange={e => { setQ(e.target.value); setPage(1) }}
            placeholder="Search programs..."
            className="w-full pl-9 pr-4 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-900"
          />
        </div>
        <button
          onClick={() => setShowFilters(!showFilters)}
          className={`flex items-center gap-2 px-4 py-2 text-sm border rounded-lg hover:bg-gray-50 ${
            activeFilterCount > 0 ? 'border-gray-900 text-gray-900' : 'border-gray-300 text-gray-600'
          }`}
        >
          <SlidersHorizontal size={16} />
          Filters
          {activeFilterCount > 0 && (
            <span className="bg-gray-900 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">{activeFilterCount}</span>
          )}
        </button>
        <div className="relative">
          <select
            value={sortBy}
            onChange={e => setSortBy(e.target.value)}
            className="appearance-none px-4 py-2 pr-8 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-900 bg-white"
          >
            {SORT_OPTIONS.map(o => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>
          <ChevronDown size={14} className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
        </div>
      </div>

      {/* Filter Panel */}
      {showFilters && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium">Filters</h3>
            {activeFilterCount > 0 && (
              <button onClick={resetFilters} className="text-xs text-gray-500 hover:text-gray-700">Clear all</button>
            )}
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div>
              <label className="text-xs text-gray-500 mb-1 block">Country</label>
              <select
                value={country}
                onChange={e => { setCountry(e.target.value); setPage(1) }}
                className="w-full text-sm border border-gray-300 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-gray-900"
              >
                <option value="">All Countries</option>
                {COUNTRY_OPTIONS.map(c => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">Degree Type</label>
              <select
                value={degreeType}
                onChange={e => { setDegreeType(e.target.value); setPage(1) }}
                className="w-full text-sm border border-gray-300 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-gray-900"
              >
                <option value="">All Degrees</option>
                {Object.entries(DEGREE_LABELS).map(([v, l]) => (
                  <option key={v} value={v}>{l}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">Min Tuition ($)</label>
              <input
                type="number"
                value={minTuition}
                onChange={e => { setMinTuition(e.target.value); setPage(1) }}
                placeholder="0"
                className="w-full text-sm border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-gray-900"
              />
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">Max Tuition ($)</label>
              <input
                type="number"
                value={maxTuition}
                onChange={e => { setMaxTuition(e.target.value); setPage(1) }}
                placeholder="Any"
                className="w-full text-sm border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-gray-900"
              />
            </div>
          </div>
        </div>
      )}

      {/* Active Filter Chips */}
      {activeFilterCount > 0 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {country && (
            <span className="inline-flex items-center gap-1 px-3 py-1 text-xs bg-gray-100 rounded-full">
              {country}
              <button onClick={() => { setCountry(''); setPage(1) }}><X size={12} /></button>
            </span>
          )}
          {degreeType && (
            <span className="inline-flex items-center gap-1 px-3 py-1 text-xs bg-gray-100 rounded-full">
              {DEGREE_LABELS[degreeType] || degreeType}
              <button onClick={() => { setDegreeType(''); setPage(1) }}><X size={12} /></button>
            </span>
          )}
          {minTuition && (
            <span className="inline-flex items-center gap-1 px-3 py-1 text-xs bg-gray-100 rounded-full">
              Min: ${Number(minTuition).toLocaleString()}
              <button onClick={() => { setMinTuition(''); setPage(1) }}><X size={12} /></button>
            </span>
          )}
          {maxTuition && (
            <span className="inline-flex items-center gap-1 px-3 py-1 text-xs bg-gray-100 rounded-full">
              Max: ${Number(maxTuition).toLocaleString()}
              <button onClick={() => { setMaxTuition(''); setPage(1) }}><X size={12} /></button>
            </span>
          )}
        </div>
      )}

      {browseLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-28" />)}
        </div>
      ) : programs.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-500 mb-2">No programs found matching your criteria.</p>
          {activeFilterCount > 0 && (
            <Button size="sm" variant="secondary" onClick={resetFilters}>Clear Filters</Button>
          )}
        </div>
      ) : (
        <>
          <p className="text-xs text-gray-500 mb-3">{browseData?.total ?? 0} programs found</p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {programs.map((p: ProgramSummary) => (
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

          {/* Pagination */}
          {browseData && browseData.total_pages > 1 && (
            <div className="flex items-center justify-center gap-2 mt-6">
              <Button
                size="sm"
                variant="secondary"
                disabled={page === 1}
                onClick={() => setPage(p => p - 1)}
              >
                Previous
              </Button>
              <span className="text-sm text-gray-500">
                Page {page} of {browseData.total_pages}
              </span>
              <Button
                size="sm"
                variant="secondary"
                disabled={page >= browseData.total_pages}
                onClick={() => setPage(p => p + 1)}
              >
                Next
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
