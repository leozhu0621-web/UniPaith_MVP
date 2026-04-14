import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { searchPrograms, nlpSearch } from '../../api/programs'
import { getMatches } from '../../api/matching'
import { getOnboarding } from '../../api/students'
import { listEvents, rsvpEvent, cancelRsvp, getMyRsvps } from '../../api/events'
import { getFeaturedPromotions, getPublicPostsFeed } from '../../api/institutions'
import { listSaved, saveProgram, unsaveProgram } from '../../api/saved-lists'
import { useCompareStore } from '../../stores/compare-store'
import ProgramCard from './explore/cards/ProgramCard'
import EventCard from './explore/cards/EventCard'
import PostCard from './explore/cards/PostCard'
import PromoCard from './explore/cards/PromoCard'
import InterestPills from './explore/shared/InterestPills'
import Button from '../../components/ui/Button'
import {
  Search, Sparkles, X, Loader2, Bookmark,
} from 'lucide-react'
import type { ProgramSummary, MatchResult, Promotion, InstitutionPost } from '../../types'

// NLP result type
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

  // Search state
  const [q, setQ] = useState(searchParams.get('q') || '')
  const [interest, setInterest] = useState('all')
  const [nlpResult, setNlpResult] = useState<NlpResult | null>(null)
  const [showSavedOnly, setShowSavedOnly] = useState(false)

  // Data loading
  const { data: onboarding } = useQuery({ queryKey: ['onboarding'], queryFn: getOnboarding })
  const profileReady = (onboarding?.completion_percentage ?? 0) >= 80

  const { data: matchData } = useQuery({
    queryKey: ['matches'], queryFn: () => getMatches(), enabled: profileReady, retry: false,
  })
  const matchMap = new Map<string, MatchResult>()
  if (Array.isArray(matchData)) (matchData as MatchResult[]).forEach(m => matchMap.set(m.program_id, m))

  const { data: programs, isLoading: programsLoading } = useQuery({
    queryKey: ['explore-programs', interest, showSavedOnly],
    queryFn: () => searchPrograms({
      q: interest === 'all' ? undefined : interest,
      page_size: 12,
      sort_by: 'relevance',
    }),
    enabled: !nlpResult,
  })

  const { data: events } = useQuery({ queryKey: ['explore-events'], queryFn: () => listEvents({ limit: 4 }), retry: false })
  const { data: promotions } = useQuery({ queryKey: ['explore-promos'], queryFn: () => getFeaturedPromotions(), retry: false })
  const { data: posts } = useQuery({ queryKey: ['explore-posts'], queryFn: () => getPublicPostsFeed(6), retry: false })
  const { data: rsvps } = useQuery({ queryKey: ['my-rsvps'], queryFn: getMyRsvps, retry: false })
  const { data: savedData } = useQuery({ queryKey: ['saved-programs'], queryFn: listSaved, retry: false })

  const [savedIds, setSavedIds] = useState<Set<string>>(new Set())
  useEffect(() => { if (savedData) setSavedIds(new Set(savedData.map((s: any) => String(s.program_id)))) }, [savedData])

  const rsvpSet = new Set((rsvps as any[] ?? []).map((r: any) => r.event_id))
  const rsvpMut = useMutation({
    mutationFn: (eventId: string) => rsvpSet.has(eventId) ? cancelRsvp(eventId) : rsvpEvent(eventId),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['explore-events'] }); queryClient.invalidateQueries({ queryKey: ['my-rsvps'] }) },
  })

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

  const handleSearch = () => {
    const trimmed = q.trim()
    if (trimmed.length >= 5) {
      nlpMut.mutate(trimmed)
    }
  }

  const clearSearch = () => {
    setQ('')
    setNlpResult(null)
  }

  // Data
  const displayPrograms: ProgramSummary[] = nlpResult
    ? (nlpResult.results?.items ?? [])
    : (Array.isArray(programs?.items) ? programs.items : [])
  const filteredPrograms = showSavedOnly
    ? displayPrograms.filter(p => savedIds.has(p.id))
    : displayPrograms
  const eventList: any[] = Array.isArray(events) ? events : []
  const promoList: Promotion[] = Array.isArray(promotions) ? promotions : []
  const postList: InstitutionPost[] = Array.isArray(posts) ? posts : []
  const savedCount = savedIds.size

  return (
    <div className="p-6 max-w-3xl mx-auto">
      {/* Header */}
      <h1 className="text-2xl font-semibold text-student-ink mb-1">Explore</h1>
      <p className="text-sm text-student-text mb-5">Discover programs, schools, and opportunities from around the world.</p>

      {/* NLP Search Bar */}
      <div className="relative mb-4">
        <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-student-text" />
        <input
          type="text"
          value={q}
          onChange={e => { setQ(e.target.value); if (!e.target.value.trim()) clearSearch() }}
          onKeyDown={e => { if (e.key === 'Enter') handleSearch() }}
          placeholder="Try: 'Affordable CS masters in Canada' or 'Business programs with high employment rate'"
          className="w-full pl-10 pr-20 py-3 bg-white border border-stone rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-student"
        />
        <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
          {q && (
            <button onClick={clearSearch} className="p-1 text-student-text hover:text-student-ink">
              <X size={14} />
            </button>
          )}
          <button
            onClick={handleSearch}
            disabled={q.trim().length < 5 || nlpMut.isPending}
            className="px-3 py-1.5 bg-student text-white text-xs font-medium rounded-lg hover:bg-student-hover disabled:opacity-40 transition-colors"
          >
            {nlpMut.isPending ? <Loader2 size={12} className="animate-spin" /> : 'Search'}
          </button>
        </div>
      </div>

      {/* NLP interpretation + editable constraint chips */}
      {nlpResult && (
        <div className="mb-4 space-y-2">
          <div className="flex items-center gap-2 px-3 py-2 bg-gold-soft rounded-lg border border-gold/20">
            <Sparkles size={12} className="text-gold flex-shrink-0" />
            <p className="text-xs text-student-ink flex-1">{nlpResult.interpretation}</p>
            <button onClick={clearSearch} className="text-xs text-student-text hover:text-student-ink">Clear</button>
          </div>
          {/* Editable constraint chips from NLP filters */}
          {Object.keys(nlpResult.filters_applied || {}).length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {Object.entries(nlpResult.filters_applied).map(([key, val]) => {
                if (!val) return null
                const label = key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
                const display = typeof val === 'number' ? `$${val.toLocaleString()}` : String(val)
                return (
                  <span key={key} className="inline-flex items-center gap-1 px-2.5 py-1 text-xs rounded-full bg-student-mist text-student-ink">
                    <span className="text-student-text">{label}:</span> {display}
                    <button
                      onClick={() => {
                        const updated = { ...nlpResult.filters_applied }
                        delete updated[key]
                        setNlpResult({ ...nlpResult, filters_applied: updated })
                      }}
                      className="ml-0.5 text-student-text hover:text-student-ink"
                    >
                      <X size={10} />
                    </button>
                  </span>
                )
              })}
            </div>
          )}
        </div>
      )}

      {/* Interest pills + Saved toggle */}
      {!nlpResult && (
        <div className="flex items-center gap-3 mb-5">
          <div className="flex-1 overflow-x-auto">
            <InterestPills active={interest} onChange={setInterest} />
          </div>
          <button
            onClick={() => setShowSavedOnly(!showSavedOnly)}
            className={`flex items-center gap-1 px-3 py-1.5 text-xs font-medium rounded-full whitespace-nowrap transition-colors flex-shrink-0 ${
              showSavedOnly
                ? 'bg-student text-white'
                : 'bg-white border border-stone text-student-text hover:border-student'
            }`}
          >
            <Bookmark size={11} />
            Saved ({savedCount})
          </button>
        </div>
      )}

      {/* === Unified Feed === */}
      <div className="space-y-4">

        {/* Featured promotions (top of feed when no search) */}
        {!nlpResult && promoList.length > 0 && (
          <div className="space-y-3">
            {promoList.slice(0, 2).map(p => (
              <PromoCard key={p.id} promo={p} onView={() => p.program_id && navigate(`/s/programs/${p.program_id}`)} />
            ))}
          </div>
        )}

        {/* Programs */}
        {(programsLoading || nlpMut.isPending) ? (
          <div className="space-y-4">
            {[1, 2, 3].map(i => (
              <div key={i} className="bg-white rounded-xl border border-divider p-6 animate-pulse">
                <div className="h-24 bg-student-mist rounded-lg mb-3" />
                <div className="h-4 bg-student-mist rounded w-2/3 mb-2" />
                <div className="h-3 bg-student-mist rounded w-1/3" />
              </div>
            ))}
          </div>
        ) : filteredPrograms.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-xl border border-divider">
            <Search size={32} className="mx-auto text-stone mb-3" />
            <p className="text-sm text-student-ink font-medium mb-1">
              {showSavedOnly ? 'No saved programs yet' : 'No programs found'}
            </p>
            <p className="text-xs text-student-text mb-3">
              {showSavedOnly
                ? 'Save programs from the feed to build your shortlist.'
                : 'Try a different search or interest category.'}
            </p>
            {showSavedOnly && (
              <Button size="sm" variant="secondary" onClick={() => setShowSavedOnly(false)}>
                Browse all programs
              </Button>
            )}
          </div>
        ) : (
          <>
            {/* First batch of programs */}
            {filteredPrograms.slice(0, 3).map(p => (
              <ProgramCard
                key={p.id}
                program={p}
                saved={savedIds.has(p.id)}
                match={matchMap.get(p.id)}
                comparing={compareStore.has(p.id)}
                onSave={() => toggleSave(p.id)}
                onCompare={() => compareStore.has(p.id) ? compareStore.remove(p.id) : compareStore.add({ program_id: p.id, program_name: p.program_name, institution_name: p.institution_name, degree_type: p.degree_type })}
                onAskCounselor={() => navigate(`/s?prefill=${encodeURIComponent(`Tell me about ${p.program_name} at ${p.institution_name}. Is it a good fit for me?`)}`)}
                onView={() => navigate(`/s/programs/${p.id}`)}
              />
            ))}

            {/* Events injected after first 3 programs */}
            {!nlpResult && eventList.length > 0 && (
              <div className="space-y-3">
                <p className="text-xs font-semibold text-student-text uppercase tracking-wider px-1">Upcoming Events</p>
                {eventList.slice(0, 2).map(ev => (
                  <EventCard key={ev.id} event={ev} isRsvped={rsvpSet.has(ev.id)} onRsvp={() => rsvpMut.mutate(ev.id)} />
                ))}
              </div>
            )}

            {/* More programs */}
            {filteredPrograms.slice(3, 6).map(p => (
              <ProgramCard
                key={p.id}
                program={p}
                saved={savedIds.has(p.id)}
                match={matchMap.get(p.id)}
                comparing={compareStore.has(p.id)}
                onSave={() => toggleSave(p.id)}
                onCompare={() => compareStore.has(p.id) ? compareStore.remove(p.id) : compareStore.add({ program_id: p.id, program_name: p.program_name, institution_name: p.institution_name, degree_type: p.degree_type })}
                onAskCounselor={() => navigate(`/s?prefill=${encodeURIComponent(`Tell me about ${p.program_name} at ${p.institution_name}. Is it a good fit for me?`)}`)}
                onView={() => navigate(`/s/programs/${p.id}`)}
              />
            ))}

            {/* School posts injected mid-feed */}
            {!nlpResult && postList.length > 0 && (
              <div className="space-y-3">
                <p className="text-xs font-semibold text-student-text uppercase tracking-wider px-1">School Updates</p>
                {postList.slice(0, 2).map(post => (
                  <PostCard key={post.id} post={post} />
                ))}
              </div>
            )}

            {/* Remaining programs */}
            {filteredPrograms.slice(6).map(p => (
              <ProgramCard
                key={p.id}
                program={p}
                saved={savedIds.has(p.id)}
                match={matchMap.get(p.id)}
                comparing={compareStore.has(p.id)}
                onSave={() => toggleSave(p.id)}
                onCompare={() => compareStore.has(p.id) ? compareStore.remove(p.id) : compareStore.add({ program_id: p.id, program_name: p.program_name, institution_name: p.institution_name, degree_type: p.degree_type })}
                onAskCounselor={() => navigate(`/s?prefill=${encodeURIComponent(`Tell me about ${p.program_name} at ${p.institution_name}. Is it a good fit for me?`)}`)}
                onView={() => navigate(`/s/programs/${p.id}`)}
              />
            ))}

            {/* More events at bottom */}
            {!nlpResult && eventList.length > 2 && (
              <div className="space-y-3">
                {eventList.slice(2).map(ev => (
                  <EventCard key={ev.id} event={ev} isRsvped={rsvpSet.has(ev.id)} onRsvp={() => rsvpMut.mutate(ev.id)} />
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
