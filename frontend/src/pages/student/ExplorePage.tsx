import { useState, useEffect, useCallback } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { searchPrograms, nlpSearch } from '../../api/programs'
import { searchInstitutions, getInstitutionSchools, getSchoolPrograms } from '../../api/institutions'
import { listSaved, saveProgram, unsaveProgram } from '../../api/saved-lists'
import { useCompareStore } from '../../stores/compare-store'
import UniversityCard from './explore/cards/UniversityCard'
import SchoolCard from './explore/cards/SchoolCard'
import ProgramCard from './explore/cards/ProgramCard'
import InterestPills from './explore/shared/InterestPills'
import {
  Search, X, Loader2, Sparkles, ChevronRight, Building2, GraduationCap, ChevronLeft,
} from 'lucide-react'
import type { ProgramSummary, SchoolSummary, MatchResult } from '../../types'

interface NlpResult {
  filters_applied: Record<string, any>
  results: { items: ProgramSummary[]; total: number }
  interpretation: string
}

// Drill-down state
type DrillLevel = 0 | 1 | 2 // 0=universities, 1=schools, 2=programs
interface SelectedUniversity { id: string; name: string }
interface SelectedSchool { id: string; name: string; institutionId: string; institutionName: string }

export default function ExplorePage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const queryClient = useQueryClient()
  const compareStore = useCompareStore()

  // Drill-down state
  const [level, setLevel] = useState<DrillLevel>(0)
  const [selectedUni, setSelectedUni] = useState<SelectedUniversity | null>(null)
  const [selectedSchool, setSelectedSchool] = useState<SelectedSchool | null>(null)

  // Search state
  const [q, setQ] = useState(searchParams.get('q') || '')
  const [isSearching, setIsSearching] = useState(false)
  const [nlpResult, setNlpResult] = useState<NlpResult | null>(null)

  // ─── Queries ───

  // Level 0: Universities — keep cached across drill levels
  const { data: universities, isLoading: uniLoading } = useQuery({
    queryKey: ['explore-universities'],
    queryFn: () => searchInstitutions({ page_size: 50 }),
    staleTime: 5 * 60 * 1000,
  })

  // Level 1: Schools within a university
  const { data: schools, isLoading: schoolsLoading } = useQuery({
    queryKey: ['explore-schools', selectedUni?.id],
    queryFn: () => getInstitutionSchools(selectedUni!.id),
    enabled: level === 1 && !!selectedUni,
  })

  // Level 2: Programs within a school
  const { data: programs, isLoading: programsLoading } = useQuery({
    queryKey: ['explore-programs', selectedSchool?.institutionId, selectedSchool?.id],
    queryFn: () => getSchoolPrograms(selectedSchool!.institutionId, selectedSchool!.id),
    enabled: level === 2 && !!selectedSchool,
  })

  // Search mode: flat program search
  const { data: searchResults, isLoading: searchLoading } = useQuery({
    queryKey: ['explore-search', q],
    queryFn: () => searchPrograms({ q: q || undefined, page_size: 21 }),
    enabled: isSearching && q.length >= 2 && !nlpResult,
  })

  // Saved programs
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

  // ─── Navigation ───

  // Reset scroll whenever drill level changes
  useEffect(() => {
    const t = setTimeout(() => document.querySelector('main')?.scrollTo({ top: 0, behavior: 'instant' }), 50)
    return () => clearTimeout(t)
  }, [level])

  const drillToSchools = useCallback((uni: { id: string; name: string }) => {
    setSelectedUni(uni)
    setLevel(1)
    // scroll reset handled by useEffect on level
  }, [])

  const drillToPrograms = useCallback((school: SchoolSummary) => {
    setSelectedSchool({
      id: school.id,
      name: school.name,
      institutionId: school.institution_id,
      institutionName: selectedUni?.name || '',
    })
    setLevel(2)
    // scroll reset handled by useEffect on level
  }, [selectedUni])

  const goBack = useCallback(() => {
    if (level === 2) { setLevel(1); setSelectedSchool(null) }
    else if (level === 1) { setLevel(0); setSelectedUni(null) }
    // scroll reset handled by useEffect on level
  }, [level])

  const goToLevel = useCallback((target: DrillLevel) => {
    setLevel(target)
    if (target === 0) { setSelectedUni(null); setSelectedSchool(null) }
    if (target === 1) { setSelectedSchool(null) }
    // scroll reset handled by useEffect on level
  }, [])

  // Search handling
  const handleSearch = () => {
    if (q.trim().length >= 3) {
      setIsSearching(true)
      nlpMut.mutate(q.trim())
    }
  }

  const clearSearch = () => {
    setQ('')
    setIsSearching(false)
    setNlpResult(null)
  }

  const exitSearch = () => {
    setIsSearching(false)
    setNlpResult(null)
  }

  // ─── Data ───

  const uniList: any[] = universities?.items ?? []
  const schoolList: SchoolSummary[] = Array.isArray(schools) ? schools : []
  const programList: ProgramSummary[] = Array.isArray(programs) ? programs : []
  const searchProgramList: ProgramSummary[] = nlpResult
    ? (nlpResult.results?.items ?? [])
    : (searchResults?.items ?? [])

  // ─── Render ───

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Search bar */}
      <div className="relative mb-4">
        <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-student-text" />
        <input
          type="text"
          value={q}
          onChange={e => { setQ(e.target.value); if (!e.target.value.trim()) clearSearch() }}
          onKeyDown={e => { if (e.key === 'Enter') handleSearch() }}
          onFocus={() => { if (q.length >= 2) setIsSearching(true) }}
          placeholder="Search universities, schools, or programs..."
          className="w-full pl-10 pr-24 py-3 bg-white border border-stone rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-student"
        />
        <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
          {q && <button onClick={clearSearch} className="p-1 text-student-text hover:text-student-ink"><X size={14} /></button>}
          <button
            onClick={handleSearch}
            disabled={q.trim().length < 3 || nlpMut.isPending}
            className="px-3 py-1.5 bg-student text-white text-xs font-medium rounded-lg hover:bg-student-hover disabled:opacity-40 transition-colors"
          >
            {nlpMut.isPending ? <Loader2 size={12} className="animate-spin" /> : 'Search'}
          </button>
        </div>
      </div>

      {/* NLP interpretation chips */}
      {nlpResult && isSearching && (
        <div className="mb-4 space-y-2">
          <div className="flex items-center gap-2 px-3 py-2 bg-gold-soft rounded-lg border border-gold/20">
            <Sparkles size={12} className="text-gold flex-shrink-0" />
            <p className="text-xs text-student-ink flex-1">{nlpResult.interpretation}</p>
            <button onClick={exitSearch} className="text-xs text-student-text hover:text-student-ink">Back to browse</button>
          </div>
        </div>
      )}

      {/* ── SEARCH MODE: Flat program results ── */}
      {isSearching && (
        <>
          {(searchLoading || nlpMut.isPending) ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[1, 2, 3].map(i => <div key={i} className="h-72 bg-white rounded-xl border border-divider animate-pulse" />)}
            </div>
          ) : searchProgramList.length === 0 ? (
            <div className="text-center py-16 bg-white rounded-xl border border-divider">
              <Search size={32} className="mx-auto text-stone mb-3" />
              <p className="text-sm text-student-ink font-medium mb-1">No results found</p>
              <p className="text-xs text-student-text">Try a different search term.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {searchProgramList.map(p => (
                <ProgramCard
                  key={p.id}
                  program={p}
                  saved={savedIds.has(p.id)}
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

      {/* ── BROWSE MODE: Drill-down with slide animation ── */}
      {!isSearching && (
        <>
          {/* Breadcrumb */}
          <div className="flex items-center gap-1.5 mb-4 text-sm">
            <button
              onClick={() => goToLevel(0)}
              className={`flex items-center gap-1 px-2 py-1 rounded-md transition-colors ${
                level === 0 ? 'text-student-ink font-semibold' : 'text-student-text hover:text-student-ink hover:bg-student-mist'
              }`}
            >
              <Building2 size={14} />
              Universities
            </button>
            {level >= 1 && selectedUni && (
              <>
                <ChevronRight size={14} className="text-student-text/40" />
                <button
                  onClick={() => goToLevel(1)}
                  className={`px-2 py-1 rounded-md transition-colors ${
                    level === 1 ? 'text-student-ink font-semibold' : 'text-student-text hover:text-student-ink hover:bg-student-mist'
                  }`}
                >
                  {selectedUni.name}
                </button>
              </>
            )}
            {level >= 2 && selectedSchool && (
              <>
                <ChevronRight size={14} className="text-student-text/40" />
                <span className="text-student-ink font-semibold px-2 py-1">{selectedSchool.name}</span>
              </>
            )}
          </div>

          {/* Slide container */}
          <div className="overflow-hidden">
            <div
              className="flex transition-transform duration-300 ease-in-out"
              style={{ transform: `translateX(-${level * 100}%)` }}
            >
              {/* ─── Level 0: Universities ─── */}
              <div className="w-full flex-shrink-0 min-h-[200px]">
                {uniLoading ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {[1, 2, 3].map(i => <div key={i} className="h-80 bg-white rounded-xl border border-divider animate-pulse" />)}
                  </div>
                ) : uniList.length === 0 ? (
                  <div className="text-center py-16 bg-white rounded-xl border border-divider">
                    <Building2 size={32} className="mx-auto text-stone mb-3" />
                    <p className="text-sm text-student-ink font-medium mb-1">No universities yet</p>
                    <p className="text-xs text-student-text">Universities will appear here as they join the platform.</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {uniList.map((inst: any) => (
                      <UniversityCard
                        key={inst.id}
                        institution={inst}
                        onClick={() => drillToSchools({ id: inst.id, name: inst.name })}
                      />
                    ))}
                  </div>
                )}
              </div>

              {/* ─── Level 1: Schools ─── */}
              <div className="w-full flex-shrink-0 min-h-[200px]">
                {level >= 1 && (
                  <>
                    {/* Back button */}
                    <button
                      onClick={goBack}
                      className="flex items-center gap-1.5 text-sm text-student-text hover:text-student-ink mb-4 transition-colors"
                    >
                      <ChevronLeft size={16} />
                      Back to Universities
                    </button>

                    {schoolsLoading ? (
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {[1, 2, 3].map(i => <div key={i} className="h-72 bg-white rounded-xl border border-divider animate-pulse" />)}
                      </div>
                    ) : schoolList.length === 0 ? (
                      <div className="text-center py-16 bg-white rounded-xl border border-divider">
                        <GraduationCap size={32} className="mx-auto text-stone mb-3" />
                        <p className="text-sm text-student-ink font-medium mb-1">No schools found</p>
                        <p className="text-xs text-student-text">This university hasn't organized programs into schools yet.</p>
                      </div>
                    ) : (
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {schoolList.map((school: SchoolSummary) => (
                          <SchoolCard
                            key={school.id}
                            school={school}
                            institutionName={selectedUni?.name || ''}
                            onClick={() => drillToPrograms(school)}
                          />
                        ))}
                      </div>
                    )}
                  </>
                )}
              </div>

              {/* ─── Level 2: Programs ─── */}
              <div className="w-full flex-shrink-0 min-h-[200px]">
                {level >= 2 && (
                  <>
                    <button
                      onClick={goBack}
                      className="flex items-center gap-1.5 text-sm text-student-text hover:text-student-ink mb-4 transition-colors"
                    >
                      <ChevronLeft size={16} />
                      Back to {selectedUni?.name || 'Schools'}
                    </button>

                    {programsLoading ? (
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {[1, 2, 3].map(i => <div key={i} className="h-64 bg-white rounded-xl border border-divider animate-pulse" />)}
                      </div>
                    ) : programList.length === 0 ? (
                      <div className="text-center py-16 bg-white rounded-xl border border-divider">
                        <GraduationCap size={32} className="mx-auto text-stone mb-3" />
                        <p className="text-sm text-student-ink font-medium mb-1">No programs found</p>
                      </div>
                    ) : (
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {programList.map((p: ProgramSummary) => (
                          <ProgramCard
                            key={p.id}
                            program={p}
                            saved={savedIds.has(p.id)}
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
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
