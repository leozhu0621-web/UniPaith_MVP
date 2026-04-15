import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { searchPrograms, nlpSearch } from '../../api/programs'
import { searchInstitutions } from '../../api/institutions'
import { getMatches } from '../../api/matching'
import { getOnboarding } from '../../api/students'
import { listSaved, saveProgram, unsaveProgram } from '../../api/saved-lists'
import { useCompareStore } from '../../stores/compare-store'
import ProgramCard from './explore/cards/ProgramCard'
import SchoolCard from './explore/cards/SchoolCard'
import InterestPills from './explore/shared/InterestPills'
import {
  Search, X, Loader2, Sparkles, GraduationCap, Building2,
} from 'lucide-react'
import type { ProgramSummary, MatchResult } from '../../types'

interface NlpResult {
  filters_applied: Record<string, any>
  results: { items: ProgramSummary[]; total: number }
  interpretation: string
}

type Tab = 'programs' | 'schools'

const COUNTRY_OPTIONS = ['United States', 'United Kingdom', 'Canada', 'Australia', 'Germany', 'Netherlands', 'France', 'Singapore', 'Japan', 'South Korea']
const DEGREE_OPTIONS = [{ v: 'masters', l: 'Masters' }, { v: 'phd', l: 'PhD' }, { v: 'bachelors', l: 'Bachelors' }, { v: 'certificate', l: 'Certificate' }]
const FORMAT_OPTIONS = [{ v: 'in_person', l: 'On Campus' }, { v: 'hybrid', l: 'Hybrid' }, { v: 'online', l: 'Online' }]
const CAMPUS_OPTIONS = [{ v: 'urban', l: 'Urban' }, { v: 'suburban', l: 'Suburban' }, { v: 'rural', l: 'Rural' }]
const DURATION_OPTIONS = [{ v: '12', l: '≤ 1yr' }, { v: '24', l: '≤ 2yr' }, { v: '36', l: '≤ 3yr' }, { v: '48', l: '≤ 4yr' }]
const SORT_OPTIONS = [{ v: 'relevance', l: 'Relevance' }, { v: 'tuition_asc', l: 'Tuition: Low→High' }, { v: 'tuition_desc', l: 'Tuition: High→Low' }, { v: 'salary_desc', l: 'Salary: Highest' }, { v: 'employment_desc', l: 'Employment: Highest' }, { v: 'deadline', l: 'Deadline: Soonest' }]

export default function ExplorePage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const queryClient = useQueryClient()
  const compareStore = useCompareStore()

  const [tab, setTab] = useState<Tab>(searchParams.get('tab') === 'schools' ? 'schools' : 'programs')
  const [q, setQ] = useState(searchParams.get('q') || '')
  const [interest, setInterest] = useState('all')
  const [nlpResult, setNlpResult] = useState<NlpResult | null>(null)

  // Filters
  const [country, setCountry] = useState('')
  const [degreeType, setDegreeType] = useState('')
  const [minTuition, setMinTuition] = useState('')
  const [maxTuition, setMaxTuition] = useState('')
  const [deliveryFormat, setDeliveryFormat] = useState('')
  const [campusSetting, setCampusSetting] = useState('')
  const [maxDuration, setMaxDuration] = useState('')
  const [city, setCity] = useState('')
  const [sortBy, setSortBy] = useState('relevance')

  // Data
  const { data: onboarding } = useQuery({ queryKey: ['onboarding'], queryFn: getOnboarding })
  const profileReady = (onboarding?.completion_percentage ?? 0) >= 80

  const { data: matchData } = useQuery({ queryKey: ['matches'], queryFn: () => getMatches(), enabled: profileReady, retry: false })
  const matchMap = new Map<string, MatchResult>()
  if (Array.isArray(matchData)) (matchData as MatchResult[]).forEach(m => matchMap.set(m.program_id, m))

  // Programs query
  const { data: programs, isLoading: programsLoading } = useQuery({
    queryKey: ['explore-programs', interest, country, degreeType, minTuition, maxTuition, deliveryFormat, campusSetting, maxDuration, city, sortBy],
    queryFn: () => searchPrograms({
      q: interest === 'all' ? undefined : interest,
      page_size: 21,
      country: country || undefined,
      degree_type: degreeType || undefined,
      min_tuition: minTuition ? Number(minTuition) : undefined,
      max_tuition: maxTuition ? Number(maxTuition) : undefined,
      delivery_format: deliveryFormat || undefined,
      campus_setting: campusSetting || undefined,
      max_duration_months: maxDuration ? Number(maxDuration) : undefined,
      city: city || undefined,
      sort_by: sortBy !== 'relevance' ? sortBy : undefined,
    }),
    enabled: tab === 'programs' && !nlpResult,
  })

  // Schools query
  const { data: schools, isLoading: schoolsLoading } = useQuery({
    queryKey: ['explore-schools', q, country],
    queryFn: () => searchInstitutions({ q: q || undefined, country: country || undefined, page_size: 21 }),
    enabled: tab === 'schools',
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

  const handleSearch = () => { if (q.trim().length >= 5 && tab === 'programs') nlpMut.mutate(q.trim()) }
  const clearSearch = () => { setQ(''); setNlpResult(null) }

  const displayPrograms: ProgramSummary[] = nlpResult
    ? (nlpResult.results?.items ?? [])
    : (Array.isArray(programs?.items) ? programs.items : [])
  const schoolList: any[] = Array.isArray(schools?.items) ? schools.items : []

  const FilterSelect = ({ value, onChange, options, placeholder }: {
    value: string; onChange: (v: string) => void; options: { v: string; l: string }[]; placeholder: string
  }) => (
    <select value={value} onChange={e => onChange(e.target.value)} className="text-xs border border-stone rounded-lg px-2 py-1.5 bg-white text-student-text min-w-0">
      <option value="">{placeholder}</option>
      {options.map(o => <option key={o.v} value={o.v}>{o.l}</option>)}
    </select>
  )

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Search bar */}
      <div className="relative mb-4">
        <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-student-text" />
        <input
          type="text" value={q}
          onChange={e => { setQ(e.target.value); if (!e.target.value.trim()) clearSearch() }}
          onKeyDown={e => { if (e.key === 'Enter') handleSearch() }}
          placeholder={tab === 'programs' ? "Search programs: 'CS masters in Canada with internships'" : "Search schools by name..."}
          className="w-full pl-10 pr-24 py-3 bg-white border border-stone rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-student"
        />
        <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
          {q && <button onClick={clearSearch} className="p-1 text-student-text hover:text-student-ink"><X size={14} /></button>}
          {tab === 'programs' && (
            <button onClick={handleSearch} disabled={q.trim().length < 5 || nlpMut.isPending} className="px-3 py-1.5 bg-student text-white text-xs font-medium rounded-lg hover:bg-student-hover disabled:opacity-40 transition-colors">
              {nlpMut.isPending ? <Loader2 size={12} className="animate-spin" /> : 'Search'}
            </button>
          )}
        </div>
      </div>

      {/* NLP chips */}
      {nlpResult && (
        <div className="mb-4 space-y-2">
          <div className="flex items-center gap-2 px-3 py-2 bg-gold-soft rounded-lg border border-gold/20">
            <Sparkles size={12} className="text-gold flex-shrink-0" />
            <p className="text-xs text-student-ink flex-1">{nlpResult.interpretation}</p>
            <button onClick={clearSearch} className="text-xs text-student-text hover:text-student-ink">Clear</button>
          </div>
          {Object.keys(nlpResult.filters_applied || {}).length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {Object.entries(nlpResult.filters_applied).filter(([, v]) => v).map(([key, val]) => (
                <span key={key} className="inline-flex items-center gap-1 px-2.5 py-1 text-xs rounded-full bg-student-mist text-student-ink">
                  <span className="text-student-text">{key.replace(/_/g, ' ')}:</span> {typeof val === 'number' ? `$${val.toLocaleString()}` : String(val)}
                  <button onClick={() => { const u = { ...nlpResult.filters_applied }; delete u[key]; setNlpResult({ ...nlpResult, filters_applied: u }) }} className="ml-0.5 text-student-text hover:text-student-ink"><X size={10} /></button>
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tabs: Programs / Schools */}
      <div className="flex items-center gap-4 mb-4">
        <div className="flex bg-student-mist rounded-lg p-0.5">
          <button
            onClick={() => setTab('programs')}
            className={`flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
              tab === 'programs' ? 'bg-white shadow-sm text-student-ink' : 'text-student-text hover:text-student-ink'
            }`}
          >
            <GraduationCap size={14} /> Programs
          </button>
          <button
            onClick={() => setTab('schools')}
            className={`flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
              tab === 'schools' ? 'bg-white shadow-sm text-student-ink' : 'text-student-text hover:text-student-ink'
            }`}
          >
            <Building2 size={14} /> Schools
          </button>
        </div>
      </div>

      {/* Interest pills (programs only) */}
      {tab === 'programs' && !nlpResult && (
        <div className="mb-4">
          <InterestPills active={interest} onChange={setInterest} />
        </div>
      )}

      {/* Filters — always visible, compact row */}
      {tab === 'programs' && !nlpResult && (
        <div className="flex flex-wrap items-center gap-2 mb-5">
          <select value={country} onChange={e => setCountry(e.target.value)} className="text-xs border border-stone rounded-lg px-2 py-1.5 bg-white text-student-text">
            <option value="">Country</option>
            {COUNTRY_OPTIONS.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
          <FilterSelect value={degreeType} onChange={setDegreeType} options={DEGREE_OPTIONS} placeholder="Degree" />
          <input type="number" value={minTuition} onChange={e => setMinTuition(e.target.value)} placeholder="Min $" className="w-20 text-xs border border-stone rounded-lg px-2 py-1.5 bg-white text-student-text" />
          <input type="number" value={maxTuition} onChange={e => setMaxTuition(e.target.value)} placeholder="Max $" className="w-20 text-xs border border-stone rounded-lg px-2 py-1.5 bg-white text-student-text" />
          <FilterSelect value={deliveryFormat} onChange={setDeliveryFormat} options={FORMAT_OPTIONS} placeholder="Format" />
          <FilterSelect value={campusSetting} onChange={setCampusSetting} options={CAMPUS_OPTIONS} placeholder="Campus" />
          <FilterSelect value={maxDuration} onChange={setMaxDuration} options={DURATION_OPTIONS} placeholder="Duration" />
          <input type="text" value={city} onChange={e => setCity(e.target.value)} placeholder="City" className="w-24 text-xs border border-stone rounded-lg px-2 py-1.5 bg-white text-student-text" />
          <select value={sortBy} onChange={e => setSortBy(e.target.value)} className="text-xs border border-stone rounded-lg px-2 py-1.5 bg-white text-student-text">
            {SORT_OPTIONS.map(o => <option key={o.v} value={o.v}>{o.l}</option>)}
          </select>
        </div>
      )}

      {tab === 'schools' && (
        <div className="flex flex-wrap items-center gap-2 mb-5">
          <select value={country} onChange={e => setCountry(e.target.value)} className="text-xs border border-stone rounded-lg px-2 py-1.5 bg-white text-student-text">
            <option value="">Country</option>
            {COUNTRY_OPTIONS.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>
      )}

      {/* Content */}
      {tab === 'programs' && (
        <>
          {(programsLoading || nlpMut.isPending) ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[1, 2, 3].map(i => <div key={i} className="h-64 bg-white rounded-xl border border-divider animate-pulse" />)}
            </div>
          ) : displayPrograms.length === 0 ? (
            <div className="text-center py-16 bg-white rounded-xl border border-divider">
              <Search size={32} className="mx-auto text-stone mb-3" />
              <p className="text-sm text-student-ink font-medium mb-1">No programs found</p>
              <p className="text-xs text-student-text">Try adjusting your search or filters.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
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
        </>
      )}

      {tab === 'schools' && (
        <>
          {schoolsLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[1, 2, 3].map(i => <div key={i} className="h-56 bg-white rounded-xl border border-divider animate-pulse" />)}
            </div>
          ) : schoolList.length === 0 ? (
            <div className="text-center py-16 bg-white rounded-xl border border-divider">
              <Building2 size={32} className="mx-auto text-stone mb-3" />
              <p className="text-sm text-student-ink font-medium mb-1">No schools found</p>
              <p className="text-xs text-student-text">Try a different search or filter.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {schoolList.map((inst: any) => (
                <SchoolCard key={inst.id} institution={inst} />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )
}
