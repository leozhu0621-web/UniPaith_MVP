import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getMatches, logEngagement } from '../../api/matching'
import { searchPrograms, nlpSearch } from '../../api/programs'
import { getOnboarding } from '../../api/students'
import Badge from '../../components/ui/Badge'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import Skeleton from '../../components/ui/Skeleton'
import { listSaved, saveProgram, unsaveProgram } from '../../api/saved-lists'
import { useCompareStore } from '../../stores/compare-store'
import { Search, SlidersHorizontal, X, ChevronDown, MessageSquare, Sparkles, Loader2, Pencil, Monitor, Briefcase, Wrench, Heart, Palette, BookOpen, Scale, Users, Bookmark, BookmarkCheck, MapPin, Clock, BarChart3, ExternalLink, ArrowRightLeft } from 'lucide-react'
import { formatCurrency, formatScore } from '../../utils/format'
import { DEGREE_LABELS, TIER_LABELS } from '../../utils/constants'
import type { MatchResult, PaginatedResponse, ProgramSummary } from '../../types'

interface NlpFiltersApplied {
  country?: string
  degree_type?: string
  min_tuition?: number
  max_tuition?: number
  [key: string]: unknown
}

interface NlpSearchResult {
  filters_applied: NlpFiltersApplied
  results: PaginatedResponse<ProgramSummary>
  interpretation: string
}

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

const GENRE_TILES: { key: string; label: string; icon: typeof Monitor; query: string }[] = [
  { key: 'cs', label: 'Computer Science', icon: Monitor, query: 'Computer Science' },
  { key: 'biz', label: 'Business', icon: Briefcase, query: 'Business' },
  { key: 'eng', label: 'Engineering', icon: Wrench, query: 'Engineering' },
  { key: 'health', label: 'Health Sciences', icon: Heart, query: 'Health Sciences' },
  { key: 'arts', label: 'Arts & Design', icon: Palette, query: 'Arts Design' },
  { key: 'edu', label: 'Education', icon: BookOpen, query: 'Education' },
  { key: 'law', label: 'Law', icon: Scale, query: 'Law' },
  { key: 'social', label: 'Social Sciences', icon: Users, query: 'Social Sciences' },
]

const DEGREE_OPTIONS = [
  { value: 'masters', label: 'M.S.' },
  { value: 'phd', label: 'Ph.D.' },
  { value: 'bachelors', label: 'B.S.' },
  { value: 'certificate', label: 'Certificate' },
  { value: 'diploma', label: 'Diploma' },
]

function EditableChip({
  label,
  value,
  onRemove,
  options,
  onSelect,
  isNlp,
}: {
  label: string
  value: string
  onRemove: () => void
  options?: { value: string; label: string }[]
  onSelect?: (v: string) => void
  isNlp: boolean
}) {
  const [editing, setEditing] = useState(false)
  const bg = isNlp ? 'bg-purple-100 text-purple-800' : 'bg-stone-100 text-stone-700'

  if (editing && options && onSelect) {
    return (
      <span className={`inline-flex items-center gap-1 px-1 py-0.5 text-xs rounded-full ${bg}`}>
        <select
          autoFocus
          className="bg-transparent text-xs outline-none cursor-pointer pr-1"
          value=""
          onChange={e => { onSelect(e.target.value); setEditing(false) }}
          onBlur={() => setEditing(false)}
        >
          <option value="" disabled>{label}</option>
          {options.map(o => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
      </span>
    )
  }

  return (
    <span className={`inline-flex items-center gap-1 px-3 py-1 text-xs rounded-full ${bg}`}>
      {value}
      {options && (
        <button onClick={() => setEditing(true)} className="opacity-60 hover:opacity-100">
          <Pencil size={10} />
        </button>
      )}
      <button onClick={onRemove}><X size={12} /></button>
    </span>
  )
}

export default function DiscoverPage() {
  const navigate = useNavigate()
  const [q, setQ] = useState('')
  const [page, setPage] = useState(1)
  const [showFilters, setShowFilters] = useState(false)
  const [sortBy, setSortBy] = useState('relevance')

  // Filter state
  const [country, setCountry] = useState('')
  const [degreeType, setDegreeType] = useState('')
  const [minTuition, setMinTuition] = useState('')
  const [maxTuition, setMaxTuition] = useState('')

  // Compare
  const compareStore = useCompareStore()

  // Saved programs
  const [savedIds, setSavedIds] = useState<Set<string>>(new Set())
  const { data: savedData } = useQuery({
    queryKey: ['saved-programs'],
    queryFn: listSaved,
    retry: false,
  })
  useEffect(() => {
    if (savedData) {
      setSavedIds(new Set(savedData.map((s: any) => String(s.program_id))))
    }
  }, [savedData])
  const queryClient = useQueryClient()
  const toggleSave = async (programId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    try {
      if (savedIds.has(programId)) {
        await unsaveProgram(programId)
        setSavedIds(prev => { const n = new Set(prev); n.delete(programId); return n })
      } else {
        await saveProgram(programId)
        setSavedIds(prev => new Set(prev).add(programId))
      }
      queryClient.invalidateQueries({ queryKey: ['saved-programs'] })
    } catch { /* ignore */ }
  }

  // NLP search state
  const [nlpResult, setNlpResult] = useState<NlpSearchResult | null>(null)

  const nlpMutation = useMutation({
    mutationFn: nlpSearch,
    onSuccess: (data: NlpSearchResult) => {
      setNlpResult(data)
      const f = data.filters_applied
      if (f.country) setCountry(f.country)
      if (f.degree_type) setDegreeType(f.degree_type)
      if (f.min_tuition != null) setMinTuition(String(f.min_tuition))
      if (f.max_tuition != null) setMaxTuition(String(f.max_tuition))
      setPage(1)
    },
    onError: () => { setNlpResult(null) },
  })

  const handleNlpSearch = () => {
    if (q.trim().length >= 5) nlpMutation.mutate(q.trim())
  }

  const handleManualFilterChange = <T,>(setter: (v: T) => void, value: T) => {
    setter(value)
    setNlpResult(null)
    setPage(1)
  }

  const { data: onboarding } = useQuery({ queryKey: ['onboarding'], queryFn: getOnboarding })
  const showMatches = (onboarding?.completion_percentage ?? 0) >= 80

  const { data: matches, isLoading: matchesLoading } = useQuery({
    queryKey: ['matches'],
    queryFn: () => getMatches(),
    enabled: showMatches,
  })

  const { data: browseData, isLoading: browseLoading } = useQuery({
    queryKey: ['programs', { q, page, sortBy, country, degreeType, minTuition, maxTuition }],
    queryFn: () => searchPrograms({
      q: q || undefined,
      page,
      page_size: 12,
      country: country || undefined,
      degree_type: degreeType || undefined,
      min_tuition: minTuition ? Number(minTuition) : undefined,
      max_tuition: maxTuition ? Number(maxTuition) : undefined,
      sort_by: sortBy !== 'relevance' ? sortBy : undefined,
    }),
  })

  const matchesByTier: Record<number, MatchResult[]> = { 3: [], 2: [], 1: [] }
  const matchesList: MatchResult[] = Array.isArray(matches) ? matches : []
  matchesList.forEach((m: MatchResult) => {
    if (matchesByTier[m.match_tier]) matchesByTier[m.match_tier].push(m)
  })

  const handleCardClick = (programId: string) => {
    logEngagement(programId, 'viewed_program', 1).catch(() => {})
    navigate(`/s/programs/${programId}`)
  }

  const resetFilters = () => {
    setCountry('')
    setDegreeType('')
    setMinTuition('')
    setMaxTuition('')
    setNlpResult(null)
    setPage(1)
  }

  const activeFilterCount = [country, degreeType, minTuition, maxTuition].filter(Boolean).length

  // Use NLP results when available, otherwise fall back to browse results
  const displayData = nlpResult ? nlpResult.results : browseData
  const programs: ProgramSummary[] = Array.isArray(displayData?.items) ? displayData.items : []
  const isLoading = nlpMutation.isPending || browseLoading

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <h1 className="text-2xl font-semibold mb-2">Discover Programs</h1>

      {!showMatches && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg px-4 py-3 mb-6 text-sm text-blue-800">
          Complete your profile (80%+) to see AI-powered matches.{' '}
          <button onClick={() => navigate('/s/profile')} className="font-medium underline">Complete profile</button>
        </div>
      )}

      <div className="flex items-center justify-between mb-6">
        <p className="text-sm text-gray-500">Need help choosing? Your counselor can guide you.</p>
        <Button size="sm" variant="secondary" onClick={() => navigate('/s/chat')}>
          <MessageSquare size={14} className="mr-1" /> Ask Counselor
        </Button>
      </div>

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

      {/* Genre Tiles */}
      <div className="flex gap-2 overflow-x-auto pb-2 mb-4">
        {GENRE_TILES.map(tile => {
          const active = q === tile.query
          return (
            <button
              key={tile.key}
              onClick={() => {
                if (active) {
                  setQ('')
                } else {
                  setQ(tile.query)
                  setNlpResult(null)
                }
                setPage(1)
              }}
              className={`flex-shrink-0 flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-colors ${
                active
                  ? 'bg-stone-700 text-white shadow-sm'
                  : 'bg-white border border-gray-200 text-stone-600 hover:bg-stone-50'
              }`}
            >
              <tile.icon size={16} />
              {tile.label}
            </button>
          )
        })}
      </div>

      <h2 className="text-lg font-medium mb-3">Browse All Programs</h2>

      {/* Search + Filter Bar */}
      <div className="flex gap-3 mb-4">
        <div className="relative flex-1">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text" value={q}
            onChange={e => { setQ(e.target.value); setPage(1) }}
            onKeyDown={e => { if (e.key === 'Enter') handleNlpSearch() }}
            placeholder="Try: &quot;CS programs in California under $30k&quot;"
            className="w-full pl-9 pr-20 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-slate-700"
          />
          <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1.5">
            {nlpMutation.isPending ? (
              <Loader2 size={16} className="text-purple-500 animate-spin" />
            ) : (
              <button
                onClick={handleNlpSearch}
                disabled={q.trim().length < 5}
                className="text-purple-500 hover:text-purple-700 disabled:text-gray-300 transition-colors"
                title="AI-powered search"
              >
                <Sparkles size={16} />
              </button>
            )}
          </div>
        </div>
        <button
          onClick={() => setShowFilters(!showFilters)}
          className={`flex items-center gap-2 px-4 py-2 text-sm border rounded-lg hover:bg-gray-50 ${
            activeFilterCount > 0 ? 'border-brand-slate-700 text-brand-slate-700' : 'border-gray-300 text-gray-600'
          }`}
        >
          <SlidersHorizontal size={16} />
          Filters
          {activeFilterCount > 0 && (
            <span className="bg-brand-slate-700 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">{activeFilterCount}</span>
          )}
        </button>
        <div className="relative">
          <select
            value={sortBy}
            onChange={e => setSortBy(e.target.value)}
            className="appearance-none px-4 py-2 pr-8 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-slate-700 bg-white"
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
              <button onClick={resetFilters} className="text-xs text-gray-500 hover:text-brand-slate-600">Clear all</button>
            )}
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div>
              <label className="text-xs text-gray-500 mb-1 block">Country</label>
              <select
                value={country}
                onChange={e => handleManualFilterChange(setCountry, e.target.value)}
                className="w-full text-sm border border-gray-300 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-brand-slate-700"
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
                onChange={e => handleManualFilterChange(setDegreeType, e.target.value)}
                className="w-full text-sm border border-gray-300 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-brand-slate-700"
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
                onChange={e => handleManualFilterChange(setMinTuition, e.target.value)}
                placeholder="0"
                className="w-full text-sm border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand-slate-700"
              />
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">Max Tuition ($)</label>
              <input
                type="number"
                value={maxTuition}
                onChange={e => handleManualFilterChange(setMaxTuition, e.target.value)}
                placeholder="Any"
                className="w-full text-sm border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand-slate-700"
              />
            </div>
          </div>
        </div>
      )}

      {/* NLP Interpretation */}
      {nlpResult && (
        <div className="flex items-center gap-2 mb-3 text-xs text-purple-700 bg-purple-50 border border-purple-100 rounded-lg px-3 py-2">
          <Sparkles size={14} className="flex-shrink-0" />
          <span>AI understood: {nlpResult.interpretation}</span>
          <button onClick={resetFilters} className="ml-auto text-purple-400 hover:text-purple-600"><X size={14} /></button>
        </div>
      )}

      {/* Editable Constraint Chips */}
      {(activeFilterCount > 0 || sortBy !== 'relevance') && (
        <div className="flex flex-wrap gap-2 mb-4">
          {country && (
            <EditableChip
              label="Country"
              value={country}
              isNlp={!!nlpResult}
              options={COUNTRY_OPTIONS.map(c => ({ value: c, label: c }))}
              onSelect={v => handleManualFilterChange(setCountry, v)}
              onRemove={() => { setCountry(''); setNlpResult(null); setPage(1) }}
            />
          )}
          {degreeType && (
            <EditableChip
              label="Degree"
              value={DEGREE_LABELS[degreeType] || degreeType}
              isNlp={!!nlpResult}
              options={DEGREE_OPTIONS}
              onSelect={v => handleManualFilterChange(setDegreeType, v)}
              onRemove={() => { setDegreeType(''); setNlpResult(null); setPage(1) }}
            />
          )}
          {minTuition && (
            <EditableChip
              label="Min Budget"
              value={`Min: $${Number(minTuition).toLocaleString()}`}
              isNlp={!!nlpResult}
              onRemove={() => { setMinTuition(''); setNlpResult(null); setPage(1) }}
            />
          )}
          {maxTuition && (
            <EditableChip
              label="Max Budget"
              value={`Max: $${Number(maxTuition).toLocaleString()}`}
              isNlp={!!nlpResult}
              onRemove={() => { setMaxTuition(''); setNlpResult(null); setPage(1) }}
            />
          )}
          {sortBy !== 'relevance' && (
            <EditableChip
              label="Sort"
              value={SORT_OPTIONS.find(s => s.value === sortBy)?.label || sortBy}
              isNlp={false}
              options={SORT_OPTIONS.filter(s => s.value !== 'relevance')}
              onSelect={v => handleManualFilterChange(setSortBy, v)}
              onRemove={() => { setSortBy('relevance'); setPage(1) }}
            />
          )}
        </div>
      )}

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-28" />)}
        </div>
      ) : programs.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-500 mb-2">No programs match yet — try adjusting your search.</p>
          {activeFilterCount > 0 && (
            <Button size="sm" variant="secondary" onClick={resetFilters}>Clear Filters</Button>
          )}
        </div>
      ) : (
        <>
          <p className="text-xs text-gray-500 mb-3">{displayData?.total ?? 0} programs found</p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {programs.map((p: ProgramSummary) => (
              <Card key={p.id} onClick={() => handleCardClick(p.id)} className="p-4 hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0 flex-1">
                    <p className="font-semibold text-sm text-stone-700 truncate">{p.program_name}</p>
                    <p className="text-xs text-gray-500 mt-0.5">
                      {p.institution_name}
                      {(p.institution_city || p.institution_country) && (
                        <span className="text-gray-400">
                          {' \u2014 '}{[p.institution_city, p.institution_country].filter(Boolean).join(', ')}
                        </span>
                      )}
                    </p>
                  </div>
                  <button
                    onClick={(e) => toggleSave(p.id, e)}
                    className={`p-1 rounded transition-colors ${savedIds.has(p.id) ? 'text-amber-500' : 'text-gray-300 hover:text-amber-500'}`}
                    title={savedIds.has(p.id) ? 'Saved' : 'Save'}
                  >
                    {savedIds.has(p.id) ? <BookmarkCheck size={16} /> : <Bookmark size={16} />}
                  </button>
                </div>

                <div className="flex items-center gap-2 mt-2">
                  <Badge variant="info" size="sm">{DEGREE_LABELS[p.degree_type] || p.degree_type}</Badge>
                  {p.tuition != null && (
                    <span className="text-xs text-gray-500">{formatCurrency(p.tuition)}/yr</span>
                  )}
                </div>

                <div className="flex flex-wrap gap-x-3 gap-y-1 mt-2">
                  {p.duration_months && (
                    <span className="inline-flex items-center gap-1 text-[11px] text-gray-500">
                      <Clock size={10} className="text-gray-400" />{p.duration_months} mo
                    </span>
                  )}
                  {p.delivery_format && (
                    <span className="inline-flex items-center gap-1 text-[11px] text-gray-500">
                      <Monitor size={10} className="text-gray-400" />{p.delivery_format.replace(/_/g, ' ')}
                    </span>
                  )}
                  {p.acceptance_rate != null && (
                    <span className="inline-flex items-center gap-1 text-[11px] text-gray-500">
                      <BarChart3 size={10} className="text-gray-400" />{(p.acceptance_rate * 100).toFixed(0)}% accept
                    </span>
                  )}
                  {p.application_deadline && (
                    <span className="inline-flex items-center gap-1 text-[11px] text-gray-500">
                      <MapPin size={10} className="text-gray-400" />
                      {new Date(p.application_deadline).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                    </span>
                  )}
                </div>

                <div className="flex items-center justify-end gap-2 mt-3 pt-2 border-t border-gray-100">
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      if (compareStore.has(p.id)) {
                        compareStore.remove(p.id)
                      } else {
                        compareStore.add({
                          program_id: p.id,
                          program_name: p.program_name,
                          institution_name: p.institution_name,
                          degree_type: p.degree_type,
                        })
                      }
                    }}
                    className={`inline-flex items-center gap-1 text-xs ${compareStore.has(p.id) ? 'text-purple-600' : 'text-stone-400 hover:text-stone-600'}`}
                  >
                    <ArrowRightLeft size={10} />
                    {compareStore.has(p.id) ? 'In compare' : 'Compare'}
                  </button>
                  <button
                    onClick={(e) => { e.stopPropagation(); navigate(`/s/programs/${p.id}`) }}
                    className="inline-flex items-center gap-1 text-xs text-stone-500 hover:text-stone-700"
                  >
                    Details <ExternalLink size={10} />
                  </button>
                </div>
              </Card>
            ))}
          </div>

          {/* Pagination */}
          {displayData && displayData.total_pages > 1 && (
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
                Page {page} of {displayData.total_pages}
              </span>
              <Button
                size="sm"
                variant="secondary"
                disabled={page >= displayData.total_pages}
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
