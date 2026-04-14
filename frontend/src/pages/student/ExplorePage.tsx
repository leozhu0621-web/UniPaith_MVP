import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { searchPrograms, nlpSearch } from '../../api/programs'
import { getProfile } from '../../api/students'
import { getMatches } from '../../api/matching'
import { getOnboarding } from '../../api/students'
import { listSaved, saveProgram, unsaveProgram } from '../../api/saved-lists'
import { useCompareStore } from '../../stores/compare-store'
import { useAuthStore } from '../../stores/auth-store'
import ProgramCard from './explore/cards/ProgramCard'
import InterestPills from './explore/shared/InterestPills'
import Avatar from '../../components/ui/Avatar'
import {
  Search, X, Loader2, Sparkles, SlidersHorizontal,
  MapPin, Pencil, MessageSquare,
} from 'lucide-react'
import type { ProgramSummary, MatchResult } from '../../types'

interface NlpResult {
  filters_applied: Record<string, any>
  results: { items: ProgramSummary[]; total: number; page: number; page_size: number; total_pages: number }
  interpretation: string
}

export default function ExplorePage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const queryClient = useQueryClient()
  const compareStore = useCompareStore()
  const user = useAuthStore(s => s.user)

  const [q, setQ] = useState(searchParams.get('q') || '')
  const [interest, setInterest] = useState('all')
  const [nlpResult, setNlpResult] = useState<NlpResult | null>(null)
  const [showFilters, setShowFilters] = useState(false)

  // Filter state
  const [country, setCountry] = useState('')
  const [degreeType, setDegreeType] = useState('')
  const [maxTuition, setMaxTuition] = useState('')
  const [deliveryFormat, setDeliveryFormat] = useState('')
  const [campusSetting, setCampusSetting] = useState('')
  const [maxDuration, setMaxDuration] = useState('')
  const [sortBy, setSortBy] = useState('relevance')

  // Data
  const { data: profile } = useQuery({ queryKey: ['profile'], queryFn: getProfile, retry: false })
  const { data: onboarding } = useQuery({ queryKey: ['onboarding'], queryFn: getOnboarding })
  const profileReady = (onboarding?.completion_percentage ?? 0) >= 80

  const { data: matchData } = useQuery({ queryKey: ['matches'], queryFn: () => getMatches(), enabled: profileReady, retry: false })
  const matchMap = new Map<string, MatchResult>()
  if (Array.isArray(matchData)) (matchData as MatchResult[]).forEach(m => matchMap.set(m.program_id, m))

  const { data: programs, isLoading: programsLoading } = useQuery({
    queryKey: ['explore-programs', interest, country, degreeType, maxTuition, deliveryFormat, campusSetting, maxDuration, sortBy],
    queryFn: () => searchPrograms({
      q: interest === 'all' ? undefined : interest,
      page_size: 20,
      country: country || undefined,
      degree_type: degreeType || undefined,
      max_tuition: maxTuition ? Number(maxTuition) : undefined,
      delivery_format: deliveryFormat || undefined,
      campus_setting: campusSetting || undefined,
      max_duration_months: maxDuration ? Number(maxDuration) : undefined,
      sort_by: sortBy !== 'relevance' ? sortBy : undefined,
    }),
    enabled: !nlpResult,
  })

  const { data: savedData } = useQuery({ queryKey: ['saved-programs'], queryFn: listSaved, retry: false })
  const [savedIds, setSavedIds] = useState<Set<string>>(new Set())
  useEffect(() => { if (savedData) setSavedIds(new Set(savedData.map((s: any) => String(s.program_id)))) }, [savedData])

  const nlpMut = useMutation({
    mutationFn: nlpSearch,
    onSuccess: (data: NlpResult) => setNlpResult(data),
    onError: () => setNlpResult(null),
  })

  const toggleSave = async (programId: string) => {
    try {
      if (savedIds.has(programId)) { await unsaveProgram(programId); setSavedIds(prev => { const n = new Set(prev); n.delete(programId); return n }) }
      else { await saveProgram(programId); setSavedIds(prev => new Set(prev).add(programId)) }
      queryClient.invalidateQueries({ queryKey: ['saved-programs'] })
    } catch { /* */ }
  }

  const handleSearch = () => { if (q.trim().length >= 5) nlpMut.mutate(q.trim()) }
  const clearSearch = () => { setQ(''); setNlpResult(null) }

  const displayPrograms: ProgramSummary[] = nlpResult
    ? (nlpResult.results?.items ?? [])
    : (Array.isArray(programs?.items) ? programs.items : [])

  const COUNTRY_OPTIONS = ['United States', 'United Kingdom', 'Canada', 'Australia', 'Germany', 'Netherlands', 'France', 'Singapore', 'Japan', 'South Korea']
  const DEGREE_OPTIONS = [{ v: 'masters', l: 'Masters' }, { v: 'phd', l: 'PhD' }, { v: 'bachelors', l: 'Bachelors' }, { v: 'certificate', l: 'Certificate' }]
  const FORMAT_OPTIONS = [{ v: 'on_campus', l: 'On Campus' }, { v: 'hybrid', l: 'Hybrid' }, { v: 'online', l: 'Online' }]
  const CAMPUS_OPTIONS = [{ v: 'urban', l: 'Urban' }, { v: 'suburban', l: 'Suburban' }, { v: 'rural', l: 'Rural' }]
  const SORT_OPTIONS = [{ v: 'relevance', l: 'Relevance' }, { v: 'tuition_asc', l: 'Tuition: Low-High' }, { v: 'salary_desc', l: 'Salary: Highest' }, { v: 'employment_desc', l: 'Employment: Highest' }, { v: 'deadline', l: 'Deadline: Soonest' }]

  return (
    <div className="flex h-full">
      {/* Left: Mini Profile (~200px, narrow) */}
      <aside className="w-52 flex-shrink-0 border-r border-divider bg-white overflow-y-auto hidden lg:block">
        <div className="p-4">
          <div className="text-center mb-4">
            <Avatar name={user?.email || '?'} size="lg" />
            <p className="text-sm font-semibold text-student-ink mt-2">{profile?.first_name || user?.email?.split('@')[0] || 'Student'} {profile?.last_name || ''}</p>
            {profile?.goals_text && (
              <p className="text-[10px] text-student-text mt-1 line-clamp-2">{profile.goals_text}</p>
            )}
          </div>

          {/* Functional info — what they're looking for */}
          <div className="space-y-2 text-xs">
            {profile?.preferences?.preferred_degree_level && (
              <div className="flex items-center gap-1.5 text-student-text">
                <span className="text-student-ink font-medium capitalize">{profile.preferences.preferred_degree_level}</span>
              </div>
            )}
            {profile?.preferences?.preferred_countries?.length > 0 && (
              <div className="flex items-center gap-1.5 text-student-text">
                <MapPin size={11} />
                <span>{profile.preferences.preferred_countries.slice(0, 3).join(', ')}</span>
              </div>
            )}
            {profile?.nationality && (
              <div className="text-student-text">From: {profile.country_of_residence || profile.nationality}</div>
            )}
          </div>

          <div className="mt-4 pt-4 border-t border-divider space-y-1.5">
            <button onClick={() => navigate('/s/profile')} className="w-full flex items-center gap-2 px-2.5 py-1.5 text-xs text-student-text hover:text-student-ink hover:bg-student-mist rounded-lg transition-colors">
              <Pencil size={12} /> Edit Profile
            </button>
            <button onClick={() => navigate('/s?prefill=Help me find programs')} className="w-full flex items-center gap-2 px-2.5 py-1.5 text-xs text-student-text hover:text-student-ink hover:bg-student-mist rounded-lg transition-colors">
              <MessageSquare size={12} /> Ask Counselor
            </button>
          </div>
        </div>
      </aside>

      {/* Right: Database (flex-1) */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-6 max-w-4xl mx-auto">
          {/* NLP Search bar */}
          <div className="relative mb-4">
            <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-student-text" />
            <input
              type="text"
              value={q}
              onChange={e => { setQ(e.target.value); if (!e.target.value.trim()) clearSearch() }}
              onKeyDown={e => { if (e.key === 'Enter') handleSearch() }}
              placeholder="Try: 'Affordable CS masters in Canada with internships'"
              className="w-full pl-10 pr-24 py-3 bg-white border border-stone rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-student"
            />
            <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
              {q && <button onClick={clearSearch} className="p-1 text-student-text hover:text-student-ink"><X size={14} /></button>}
              <button onClick={handleSearch} disabled={q.trim().length < 5 || nlpMut.isPending} className="px-3 py-1.5 bg-student text-white text-xs font-medium rounded-lg hover:bg-student-hover disabled:opacity-40 transition-colors">
                {nlpMut.isPending ? <Loader2 size={12} className="animate-spin" /> : 'Search'}
              </button>
            </div>
          </div>

          {/* NLP interpretation */}
          {nlpResult && (
            <div className="mb-4 space-y-2">
              <div className="flex items-center gap-2 px-3 py-2 bg-gold-soft rounded-lg border border-gold/20">
                <Sparkles size={12} className="text-gold flex-shrink-0" />
                <p className="text-xs text-student-ink flex-1">{nlpResult.interpretation}</p>
                <button onClick={clearSearch} className="text-xs text-student-text hover:text-student-ink">Clear</button>
              </div>
              {Object.keys(nlpResult.filters_applied || {}).length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {Object.entries(nlpResult.filters_applied).filter(([_, v]) => v).map(([key, val]) => (
                    <span key={key} className="inline-flex items-center gap-1 px-2.5 py-1 text-xs rounded-full bg-student-mist text-student-ink">
                      <span className="text-student-text">{key.replace(/_/g, ' ')}:</span> {typeof val === 'number' ? `$${val.toLocaleString()}` : String(val)}
                      <button onClick={() => { const u = { ...nlpResult.filters_applied }; delete u[key]; setNlpResult({ ...nlpResult, filters_applied: u }) }} className="ml-0.5 text-student-text hover:text-student-ink"><X size={10} /></button>
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Interest pills */}
          {!nlpResult && (
            <div className="mb-4">
              <InterestPills active={interest} onChange={setInterest} />
            </div>
          )}

          {/* Filter toggle + sort */}
          <div className="flex items-center gap-3 mb-4">
            <button onClick={() => setShowFilters(!showFilters)} className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border transition-colors ${showFilters ? 'bg-student text-white border-student' : 'bg-white border-stone text-student-text hover:border-student'}`}>
              <SlidersHorizontal size={12} /> Filters
            </button>
            <select value={sortBy} onChange={e => setSortBy(e.target.value)} className="text-xs border border-stone rounded-lg px-2 py-1.5 bg-white text-student-text">
              {SORT_OPTIONS.map(o => <option key={o.v} value={o.v}>{o.l}</option>)}
            </select>
          </div>

          {/* Expanded filters */}
          {showFilters && (
            <div className="mb-5 p-4 bg-white border border-divider rounded-xl grid grid-cols-2 md:grid-cols-3 gap-3">
              <div>
                <label className="text-[10px] font-medium text-student-text mb-1 block">Country</label>
                <select value={country} onChange={e => setCountry(e.target.value)} className="w-full text-xs border border-stone rounded-lg px-2 py-1.5">
                  <option value="">Any</option>
                  {COUNTRY_OPTIONS.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
              <div>
                <label className="text-[10px] font-medium text-student-text mb-1 block">Degree</label>
                <select value={degreeType} onChange={e => setDegreeType(e.target.value)} className="w-full text-xs border border-stone rounded-lg px-2 py-1.5">
                  <option value="">Any</option>
                  {DEGREE_OPTIONS.map(o => <option key={o.v} value={o.v}>{o.l}</option>)}
                </select>
              </div>
              <div>
                <label className="text-[10px] font-medium text-student-text mb-1 block">Max Tuition</label>
                <input type="number" value={maxTuition} onChange={e => setMaxTuition(e.target.value)} placeholder="e.g. 50000" className="w-full text-xs border border-stone rounded-lg px-2 py-1.5" />
              </div>
              <div>
                <label className="text-[10px] font-medium text-student-text mb-1 block">Format</label>
                <select value={deliveryFormat} onChange={e => setDeliveryFormat(e.target.value)} className="w-full text-xs border border-stone rounded-lg px-2 py-1.5">
                  <option value="">Any</option>
                  {FORMAT_OPTIONS.map(o => <option key={o.v} value={o.v}>{o.l}</option>)}
                </select>
              </div>
              <div>
                <label className="text-[10px] font-medium text-student-text mb-1 block">Campus</label>
                <select value={campusSetting} onChange={e => setCampusSetting(e.target.value)} className="w-full text-xs border border-stone rounded-lg px-2 py-1.5">
                  <option value="">Any</option>
                  {CAMPUS_OPTIONS.map(o => <option key={o.v} value={o.v}>{o.l}</option>)}
                </select>
              </div>
              <div>
                <label className="text-[10px] font-medium text-student-text mb-1 block">Max Duration</label>
                <select value={maxDuration} onChange={e => setMaxDuration(e.target.value)} className="w-full text-xs border border-stone rounded-lg px-2 py-1.5">
                  <option value="">Any</option>
                  <option value="12">1 year</option>
                  <option value="24">2 years</option>
                  <option value="36">3 years</option>
                  <option value="48">4 years</option>
                </select>
              </div>
            </div>
          )}

          {/* Program cards */}
          {(programsLoading || nlpMut.isPending) ? (
            <div className="space-y-4">
              {[1, 2, 3].map(i => <div key={i} className="h-48 bg-white rounded-xl border border-divider animate-pulse" />)}
            </div>
          ) : displayPrograms.length === 0 ? (
            <div className="text-center py-16 bg-white rounded-xl border border-divider">
              <Search size={32} className="mx-auto text-stone mb-3" />
              <p className="text-sm text-student-ink font-medium mb-1">No programs found</p>
              <p className="text-xs text-student-text">Try adjusting your search or filters.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {displayPrograms.map(p => (
                <ProgramCard
                  key={p.id}
                  program={p}
                  saved={savedIds.has(p.id)}
                  match={matchMap.get(p.id)}
                  comparing={compareStore.has(p.id)}
                  onSave={() => toggleSave(p.id)}
                  onCompare={() => compareStore.has(p.id) ? compareStore.remove(p.id) : compareStore.add({ program_id: p.id, program_name: p.program_name, institution_name: p.institution_name, degree_type: p.degree_type })}
                  onAskCounselor={() => navigate(`/s?prefill=${encodeURIComponent(`Tell me about ${p.program_name} at ${p.institution_name}. Is it a good fit?`)}`)}
                  onView={() => navigate(`/s/programs/${p.id}`)}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
