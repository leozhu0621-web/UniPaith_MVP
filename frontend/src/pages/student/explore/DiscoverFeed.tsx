import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { searchPrograms } from '../../../api/programs'
import { getMatches } from '../../../api/matching'
import { getOnboarding } from '../../../api/students'
import { listEvents, rsvpEvent, cancelRsvp, getMyRsvps } from '../../../api/events'
import { getFeaturedPromotions } from '../../../api/institutions'
import { listSaved, saveProgram, unsaveProgram } from '../../../api/saved-lists'
import { useCompareStore } from '../../../stores/compare-store'
import ProgramCard from './cards/ProgramCard'
import EventCard from './cards/EventCard'
import PromoCard from './cards/PromoCard'
import InterestPills from './shared/InterestPills'
import FeedSection from './shared/FeedSection'
import { Search, Globe, Sparkles, Calendar } from 'lucide-react'
import type { ProgramSummary, MatchResult, Promotion } from '../../../types'

export default function DiscoverFeed() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const compareStore = useCompareStore()
  const [interest, setInterest] = useState('all')
  const [searchQ, setSearchQ] = useState('')

  // Data
  const { data: onboarding } = useQuery({ queryKey: ['onboarding'], queryFn: getOnboarding })
  const profileReady = (onboarding?.completion_percentage ?? 0) >= 80

  const { data: matchData } = useQuery({
    queryKey: ['matches'],
    queryFn: () => getMatches(),
    enabled: profileReady,
    retry: false,
  })
  const matchMap = new Map<string, MatchResult>()
  if (Array.isArray(matchData)) (matchData as MatchResult[]).forEach(m => matchMap.set(m.program_id, m))

  const { data: programs } = useQuery({
    queryKey: ['discover-programs', interest],
    queryFn: () => searchPrograms({ q: interest === 'all' ? undefined : interest, page_size: 8, sort_by: 'relevance' }),
  })

  const { data: events } = useQuery({ queryKey: ['discover-events'], queryFn: () => listEvents({ limit: 4 }), retry: false })
  const { data: promotions } = useQuery({ queryKey: ['discover-promos'], queryFn: () => getFeaturedPromotions(), retry: false })
  const { data: rsvps } = useQuery({ queryKey: ['my-rsvps'], queryFn: getMyRsvps, retry: false })
  const { data: savedData } = useQuery({ queryKey: ['saved-programs'], queryFn: listSaved, retry: false })

  const [savedIds, setSavedIds] = useState<Set<string>>(new Set())
  useEffect(() => { if (savedData) setSavedIds(new Set(savedData.map((s: any) => String(s.program_id)))) }, [savedData])

  const rsvpSet = new Set((rsvps as any[] ?? []).map((r: any) => r.event_id))
  const rsvpMut = useMutation({
    mutationFn: (eventId: string) => rsvpSet.has(eventId) ? cancelRsvp(eventId) : rsvpEvent(eventId),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['discover-events'] }); queryClient.invalidateQueries({ queryKey: ['my-rsvps'] }) },
  })

  const toggleSave = async (programId: string) => {
    try {
      if (savedIds.has(programId)) { await unsaveProgram(programId); setSavedIds(prev => { const n = new Set(prev); n.delete(programId); return n }) }
      else { await saveProgram(programId); setSavedIds(prev => new Set(prev).add(programId)) }
      queryClient.invalidateQueries({ queryKey: ['saved-programs'] })
    } catch { /* */ }
  }

  const programList: ProgramSummary[] = Array.isArray(programs?.items) ? programs.items : []
  const eventList: any[] = Array.isArray(events) ? events : []
  const promoList: Promotion[] = Array.isArray(promotions) ? promotions : []

  return (
    <div className="max-w-2xl mx-auto">
      {/* Search bar */}
      <div className="relative mb-4">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-student-text" />
        <input
          type="text"
          value={searchQ}
          onChange={e => setSearchQ(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter' && searchQ.trim()) navigate(`/s/explore?tab=search&q=${encodeURIComponent(searchQ.trim())}`) }}
          placeholder="Search programs, schools, events..."
          className="w-full pl-10 pr-4 py-2.5 bg-white border border-stone rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-student"
        />
      </div>

      {/* Interest pills */}
      <div className="mb-5">
        <InterestPills active={interest} onChange={setInterest} />
      </div>

      {/* Featured promotions */}
      {promoList.length > 0 && (
        <FeedSection icon={Sparkles} title="Featured" count={promoList.length}>
          <div className="space-y-3">
            {promoList.slice(0, 2).map(p => (
              <PromoCard key={p.id} promo={p} onView={() => p.program_id && navigate(`/s/programs/${p.program_id}`)} />
            ))}
          </div>
        </FeedSection>
      )}

      {/* Upcoming events */}
      {eventList.length > 0 && (
        <FeedSection icon={Calendar} title="Upcoming Events" count={eventList.length}>
          <div className="space-y-3">
            {eventList.slice(0, 3).map(ev => (
              <EventCard key={ev.id} event={ev} isRsvped={rsvpSet.has(ev.id)} onRsvp={() => rsvpMut.mutate(ev.id)} />
            ))}
          </div>
        </FeedSection>
      )}

      {/* Programs */}
      <FeedSection icon={Globe} title="Programs" count={programList.length}>
        {programList.length === 0 ? (
          <p className="text-sm text-student-text py-6 text-center">No programs found. Try a different interest.</p>
        ) : (
          <div className="space-y-4">
            {programList.map(p => (
              <ProgramCard
                key={p.id}
                program={p}
                saved={savedIds.has(p.id)}
                match={matchMap.get(p.id)}
                comparing={compareStore.has(p.id)}
                onSave={() => toggleSave(p.id)}
                onCompare={() => { if (compareStore.has(p.id)) { compareStore.remove(p.id) } else { compareStore.add({ program_id: p.id, program_name: p.program_name, institution_name: p.institution_name, degree_type: p.degree_type }) } }}
                onAskCounselor={() => navigate(`/s?prefill=${encodeURIComponent(`Tell me about ${p.program_name} at ${p.institution_name}. Is it a good fit for me?`)}`)}
                onView={() => navigate(`/s/programs/${p.id}`)}
              />
            ))}
          </div>
        )}
      </FeedSection>
    </div>
  )
}
