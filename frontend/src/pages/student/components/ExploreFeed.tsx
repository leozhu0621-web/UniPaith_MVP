import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { searchPrograms } from '../../../api/programs'
import { getMatches } from '../../../api/matching'
import { getOnboarding } from '../../../api/students'
import { listEvents, rsvpEvent, cancelRsvp, getMyRsvps } from '../../../api/events'
import { getFeaturedPromotions, getPublicPostsFeed } from '../../../api/institutions'
import { listSaved, saveProgram, unsaveProgram } from '../../../api/saved-lists'
import { useCompareStore } from '../../../stores/compare-store'
import { formatCurrency } from '../../../utils/format'
import { DEGREE_LABELS } from '../../../utils/constants'
import type { ProgramSummary, MatchResult, Promotion, InstitutionPost } from '../../../types'
import {
  Search, Bookmark, BookmarkCheck, MapPin, Clock, DollarSign,
  Calendar, Users, Sparkles, GraduationCap, Megaphone,
  ChevronRight, TrendingUp, Globe, ArrowRightLeft,
  Monitor, Briefcase, Wrench, Heart, Palette, BookOpen, Scale, MessageSquare,
} from 'lucide-react'

// --- Types for unified feed ---
type FeedItem =
  | { type: 'program'; data: ProgramSummary }
  | { type: 'event'; data: any }
  | { type: 'post'; data: InstitutionPost }
  | { type: 'promo'; data: Promotion }

const INTEREST_PILLS = [
  { key: 'all', label: 'For You', icon: Sparkles },
  { key: 'Computer Science', label: 'CS & Tech', icon: Monitor },
  { key: 'Business', label: 'Business', icon: Briefcase },
  { key: 'Engineering', label: 'Engineering', icon: Wrench },
  { key: 'Health', label: 'Health', icon: Heart },
  { key: 'Arts', label: 'Arts & Design', icon: Palette },
  { key: 'Education', label: 'Education', icon: BookOpen },
  { key: 'Law', label: 'Law', icon: Scale },
]

export default function ExploreFeed() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const compareStore = useCompareStore()
  const [interest, setInterest] = useState('all')
  const [searchQ, setSearchQ] = useState('')

  // --- Data fetching ---
  const { data: onboarding } = useQuery({ queryKey: ['onboarding'], queryFn: getOnboarding })
  const profileReady = (onboarding?.completion_percentage ?? 0) >= 80

  const { data: matchData } = useQuery({
    queryKey: ['matches'],
    queryFn: () => getMatches(),
    enabled: profileReady,
    retry: false,
  })
  const matchMap = new Map<string, MatchResult>()
  if (Array.isArray(matchData)) {
    (matchData as MatchResult[]).forEach(m => matchMap.set(m.program_id, m))
  }

  const { data: programs } = useQuery({
    queryKey: ['explore-programs', interest],
    queryFn: () => searchPrograms({
      q: interest === 'all' ? undefined : interest,
      page_size: 8,
      sort_by: 'relevance',
    }),
  })

  const { data: events } = useQuery({
    queryKey: ['explore-events'],
    queryFn: () => listEvents({ limit: 6 }),
    retry: false,
  })

  const { data: promotions } = useQuery({
    queryKey: ['explore-promos'],
    queryFn: () => getFeaturedPromotions(),
    retry: false,
  })

  const { data: posts } = useQuery({
    queryKey: ['explore-posts'],
    queryFn: () => getPublicPostsFeed(10),
    retry: false,
  })

  const { data: rsvps } = useQuery({
    queryKey: ['my-rsvps'],
    queryFn: getMyRsvps,
    retry: false,
  })

  const { data: savedData } = useQuery({
    queryKey: ['saved-programs'],
    queryFn: listSaved,
    retry: false,
  })

  const [savedIds, setSavedIds] = useState<Set<string>>(new Set())
  useEffect(() => {
    if (savedData) setSavedIds(new Set(savedData.map((s: any) => String(s.program_id))))
  }, [savedData])

  const rsvpSet = new Set((rsvps as any[] ?? []).map((r: any) => r.event_id))

  const rsvpMut = useMutation({
    mutationFn: (eventId: string) => rsvpSet.has(eventId) ? cancelRsvp(eventId) : rsvpEvent(eventId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['explore-events'] })
      queryClient.invalidateQueries({ queryKey: ['my-rsvps'] })
    },
  })

  const toggleSave = async (programId: string) => {
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

  const programList: ProgramSummary[] = Array.isArray(programs?.items) ? programs.items : []
  const eventList: any[] = Array.isArray(events) ? events : []
  const promoList: Promotion[] = Array.isArray(promotions) ? promotions : []
  const postList: InstitutionPost[] = Array.isArray(posts) ? posts : []

  // --- Build unified feed ---
  const feed: FeedItem[] = []

  // Interleave: programs first 2, then events, then posts, then more programs, promos mixed in
  const pSlice1 = programList.slice(0, 3)
  const pSlice2 = programList.slice(3, 6)
  const pSlice3 = programList.slice(6)

  pSlice1.forEach(p => feed.push({ type: 'program', data: p }))
  if (eventList.length > 0) feed.push({ type: 'event', data: eventList[0] })
  if (promoList.length > 0) feed.push({ type: 'promo', data: promoList[0] })
  pSlice2.forEach(p => feed.push({ type: 'program', data: p }))
  postList.slice(0, 2).forEach(p => feed.push({ type: 'post', data: p }))
  if (eventList.length > 1) feed.push({ type: 'event', data: eventList[1] })
  pSlice3.forEach(p => feed.push({ type: 'program', data: p }))
  if (promoList.length > 1) feed.push({ type: 'promo', data: promoList[1] })
  postList.slice(2, 5).forEach(p => feed.push({ type: 'post', data: p }))
  eventList.slice(2).forEach(e => feed.push({ type: 'event', data: e }))

  return (
    <div className="max-w-2xl mx-auto">
      {/* Search bar */}
      <div className="relative mb-4">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-student-text" />
        <input
          type="text"
          value={searchQ}
          onChange={e => setSearchQ(e.target.value)}
          onKeyDown={e => {
            if (e.key === 'Enter' && searchQ.trim()) {
              navigate(`/s/explore?tab=search&q=${encodeURIComponent(searchQ.trim())}`)
            }
          }}
          placeholder="Search programs, schools, events..."
          className="w-full pl-10 pr-4 py-2.5 bg-white border border-stone rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-student"
        />
      </div>

      {/* Interest pills */}
      <div className="flex gap-2 overflow-x-auto pb-3 mb-4 scrollbar-hide">
        {INTEREST_PILLS.map(p => (
          <button
            key={p.key}
            onClick={() => setInterest(p.key)}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-full whitespace-nowrap transition-colors ${
              interest === p.key
                ? 'bg-student text-white'
                : 'bg-white border border-stone text-student-text hover:border-student hover:text-student-ink'
            }`}
          >
            <p.icon size={12} />
            {p.label}
          </button>
        ))}
      </div>

      {/* Feed */}
      <div className="space-y-4">
        {feed.length === 0 && (
          <div className="text-center py-16">
            <Globe size={40} className="mx-auto text-stone mb-3" />
            <p className="text-sm text-student-text">Explore programs and school content here.</p>
          </div>
        )}

        {feed.map((item) => {
          if (item.type === 'program') return <ProgramCard key={`p-${item.data.id}`} program={item.data} saved={savedIds.has(item.data.id)} match={matchMap.get(item.data.id)} comparing={compareStore.has(item.data.id)} onSave={() => toggleSave(item.data.id)} onCompare={() => { const p = item.data; compareStore.has(p.id) ? compareStore.remove(p.id) : compareStore.add({ program_id: p.id, program_name: p.program_name, institution_name: p.institution_name, degree_type: p.degree_type }) }} onAskCounselor={() => navigate(`/s?prefill=${encodeURIComponent(`Tell me about ${item.data.program_name} at ${item.data.institution_name}. Is it a good fit for me?`)}`)} onView={() => navigate(`/s/programs/${item.data.id}`)} />
          if (item.type === 'event') return <EventCard key={`e-${item.data.id}`} event={item.data} isRsvped={rsvpSet.has(item.data.id)} onRsvp={() => rsvpMut.mutate(item.data.id)} />
          if (item.type === 'post') return <PostCard key={`post-${item.data.id}`} post={item.data} />
          if (item.type === 'promo') return <PromoCard key={`promo-${item.data.id}`} promo={item.data} onView={() => item.data.program_id && navigate(`/s/programs/${item.data.program_id}`)} />
          return null
        })}
      </div>
    </div>
  )
}


// ===== Feed Card Components =====

// --- Fit label from match tier ---
function fitLabel(tier: number): { text: string; color: string; bg: string } {
  if (tier >= 3) return { text: 'Strong Fit', color: 'text-emerald-700', bg: 'bg-emerald-50 border-emerald-200' }
  if (tier >= 2) return { text: 'Good Fit', color: 'text-blue-700', bg: 'bg-blue-50 border-blue-200' }
  return { text: 'Reach', color: 'text-amber-700', bg: 'bg-amber-50 border-amber-200' }
}

// --- Gradient banners by degree type ---
const BANNER_GRADIENTS: Record<string, string> = {
  masters: 'from-student/90 to-student-hover/80',
  phd: 'from-indigo-600/90 to-indigo-800/80',
  bachelors: 'from-sky-500/90 to-sky-700/80',
  certificate: 'from-amber-500/90 to-amber-700/80',
  diploma: 'from-teal-500/90 to-teal-700/80',
}

function ProgramCard({ program, saved, match, comparing, onSave, onCompare, onAskCounselor, onView }: {
  program: ProgramSummary; saved: boolean; match?: MatchResult; comparing: boolean
  onSave: () => void; onCompare: () => void; onAskCounselor: () => void; onView: () => void
}) {
  const degree = DEGREE_LABELS[program.degree_type] || program.degree_type
  const gradient = BANNER_GRADIENTS[program.degree_type] || BANNER_GRADIENTS.masters
  const fit = match ? fitLabel(match.match_tier) : null
  const deadlineDate = program.application_deadline ? new Date(program.application_deadline) : null
  const daysLeft = deadlineDate ? Math.ceil((deadlineDate.getTime() - Date.now()) / 86400000) : null

  return (
    <div className="bg-white rounded-xl border border-divider hover:shadow-lg transition-all overflow-hidden group">
      {/* ===== Hero Banner ===== */}
      <div className={`relative bg-gradient-to-r ${gradient} px-5 pt-5 pb-4 cursor-pointer`} onClick={onView}>
        {/* Fit badge */}
        {fit && (
          <span className={`absolute top-3 right-3 px-2.5 py-1 text-[10px] font-bold rounded-full border ${fit.bg} ${fit.color}`}>
            {fit.text}
          </span>
        )}

        {/* Degree pill */}
        <span className="inline-block px-2.5 py-0.5 text-[10px] font-semibold rounded-full bg-white/20 text-white backdrop-blur-sm mb-3">
          {degree}
          {program.delivery_format && ` · ${program.delivery_format.replace(/_/g, ' ')}`}
          {program.duration_months && ` · ${program.duration_months}mo`}
        </span>

        {/* Program name */}
        <h3 className="text-lg font-bold text-white leading-tight mb-1">{program.program_name}</h3>

        {/* Institution row */}
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-md bg-white/20 backdrop-blur-sm flex items-center justify-center">
            <GraduationCap size={14} className="text-white" />
          </div>
          <div>
            <p className="text-sm font-medium text-white/95">{program.institution_name}</p>
            <p className="text-[10px] text-white/70 flex items-center gap-1">
              <MapPin size={8} />
              {program.institution_city ? `${program.institution_city}, ` : ''}{program.institution_country}
            </p>
          </div>
        </div>
      </div>

      {/* ===== Stats Grid ===== */}
      <div className="grid grid-cols-4 divide-x divide-divider border-b border-divider">
        <div className="px-3 py-2.5 text-center">
          <p className="text-[10px] text-student-text mb-0.5 flex items-center justify-center gap-0.5"><DollarSign size={9} /> Tuition</p>
          <p className="text-xs font-bold text-student-ink">
            {program.tuition != null ? formatCurrency(program.tuition) : '—'}
          </p>
        </div>
        <div className="px-3 py-2.5 text-center">
          <p className="text-[10px] text-student-text mb-0.5 flex items-center justify-center gap-0.5"><TrendingUp size={9} /> Salary</p>
          <p className="text-xs font-bold text-student-ink">
            {program.median_salary != null ? formatCurrency(program.median_salary) : '—'}
          </p>
        </div>
        <div className="px-3 py-2.5 text-center">
          <p className="text-[10px] text-student-text mb-0.5 flex items-center justify-center gap-0.5"><Users size={9} /> Employed</p>
          <p className="text-xs font-bold text-student-ink">
            {program.employment_rate != null ? `${Math.round(program.employment_rate * 100)}%` : '—'}
          </p>
        </div>
        <div className="px-3 py-2.5 text-center">
          <p className="text-[10px] text-student-text mb-0.5 flex items-center justify-center gap-0.5"><Clock size={9} /> Deadline</p>
          <p className={`text-xs font-bold ${daysLeft != null && daysLeft <= 14 ? 'text-red-600' : 'text-student-ink'}`}>
            {daysLeft != null && daysLeft >= 0 ? (daysLeft === 0 ? 'Today' : `${daysLeft}d`) : deadlineDate ? deadlineDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : '—'}
          </p>
        </div>
      </div>

      {/* ===== Action Bar — 3 actions ===== */}
      <div className="flex items-center divide-x divide-divider">
        <button
          onClick={e => { e.stopPropagation(); onSave() }}
          className={`flex-1 flex items-center justify-center gap-1.5 py-2.5 text-xs font-medium transition-colors ${
            saved ? 'text-student bg-student-mist' : 'text-student-text hover:bg-student-mist hover:text-student-ink'
          }`}
        >
          {saved ? <BookmarkCheck size={13} className="text-student" /> : <Bookmark size={13} />}
          {saved ? 'Saved' : 'Save'}
        </button>
        <button
          onClick={e => { e.stopPropagation(); onCompare() }}
          className={`flex-1 flex items-center justify-center gap-1.5 py-2.5 text-xs font-medium transition-colors ${
            comparing ? 'text-student bg-student-mist' : 'text-student-text hover:bg-student-mist hover:text-student-ink'
          }`}
        >
          <ArrowRightLeft size={13} />
          {comparing ? 'Comparing' : 'Compare'}
        </button>
        <button
          onClick={e => { e.stopPropagation(); onAskCounselor() }}
          className="flex-1 flex items-center justify-center gap-1.5 py-2.5 text-xs font-medium text-gold hover:bg-gold-soft transition-colors"
        >
          <MessageSquare size={13} />
          Ask Counselor
        </button>
      </div>
    </div>
  )
}

function EventCard({ event, isRsvped, onRsvp }: {
  event: any; isRsvped: boolean; onRsvp: () => void
}) {
  const d = new Date(event.start_time)
  const month = d.toLocaleString('en-US', { month: 'short' })
  const day = d.getDate()
  const time = d.toLocaleString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true })
  const spotsLeft = event.capacity ? Math.max(0, event.capacity - (event.rsvp_count || 0)) : null

  return (
    <div className="bg-white rounded-xl border border-divider hover:shadow-md transition-shadow overflow-hidden">
      <div className="flex items-center gap-2 px-4 pt-3 pb-1">
        <Calendar size={12} className="text-student" />
        <span className="text-[10px] font-semibold text-student uppercase tracking-wider">Event</span>
        {event.event_type && (
          <span className="px-2 py-0.5 text-[10px] rounded-full bg-gold-soft text-gold">
            {event.event_type.replace(/_/g, ' ')}
          </span>
        )}
      </div>
      <div className="flex gap-4 px-4 pb-4">
        {/* Date block */}
        <div className="w-14 h-16 bg-student-mist rounded-lg flex flex-col items-center justify-center flex-shrink-0">
          <span className="text-[10px] font-semibold text-student uppercase">{month}</span>
          <span className="text-xl font-bold text-student-ink">{day}</span>
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-semibold text-student-ink mb-0.5">{event.event_name}</h3>
          <p className="text-xs text-student-text mb-1">{event.institution_name || 'School Event'}</p>
          <div className="flex items-center gap-3 text-[10px] text-student-text">
            <span className="flex items-center gap-0.5"><Clock size={9} /> {time}</span>
            {event.location && <span className="flex items-center gap-0.5 truncate"><MapPin size={9} /> {event.location}</span>}
            {spotsLeft !== null && <span className="flex items-center gap-0.5"><Users size={9} /> {spotsLeft > 0 ? `${spotsLeft} spots` : 'Full'}</span>}
          </div>
        </div>
        <button
          onClick={onRsvp}
          className={`self-center px-4 py-1.5 text-xs font-medium rounded-lg transition-colors flex-shrink-0 ${
            isRsvped
              ? 'bg-student-mist text-student border border-student'
              : 'bg-student text-white hover:bg-student-hover'
          }`}
        >
          {isRsvped ? 'Going' : 'RSVP'}
        </button>
      </div>
    </div>
  )
}

function PostCard({ post }: { post: InstitutionPost }) {
  return (
    <div className="bg-white rounded-xl border border-divider hover:shadow-sm transition-shadow overflow-hidden">
      <div className="flex items-center gap-2 px-4 pt-3 pb-1">
        <Megaphone size={12} className="text-student" />
        <span className="text-[10px] font-semibold text-student uppercase tracking-wider">School Update</span>
        <span className="text-[10px] text-student-text ml-auto">
          {new Date(post.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
        </span>
      </div>
      <div className="px-4 pb-4">
        <div className="flex items-center gap-2 mb-2">
          <div className="w-8 h-8 rounded-full bg-student-mist flex items-center justify-center">
            <GraduationCap size={14} className="text-student" />
          </div>
          <span className="text-xs font-semibold text-student-ink">{(post as any).institution_name || 'School'}</span>
        </div>
        <h3 className="text-sm font-medium text-student-ink mb-1">{post.title}</h3>
        <p className="text-xs text-student-text line-clamp-3 leading-relaxed">{post.body}</p>
        {post.media_urls && post.media_urls.length > 0 && (
          <div className="mt-2 flex gap-2 overflow-x-auto">
            {post.media_urls.slice(0, 3).map((m: any, i: number) => (
              <div key={i} className="w-24 h-16 rounded-lg bg-student-mist overflow-hidden flex-shrink-0">
                <img
                  src={typeof m === 'string' ? m : m.url}
                  alt=""
                  className="w-full h-full object-cover"
                  onError={e => (e.currentTarget.style.display = 'none')}
                />
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function PromoCard({ promo, onView }: { promo: Promotion; onView: () => void }) {
  return (
    <div
      onClick={onView}
      className="bg-gradient-to-r from-gold-soft to-white rounded-xl border border-gold/20 hover:shadow-md transition-shadow overflow-hidden cursor-pointer"
    >
      <div className="flex items-center gap-2 px-4 pt-3 pb-1">
        <Sparkles size={12} className="text-gold" />
        <span className="text-[10px] font-semibold text-gold uppercase tracking-wider">Featured Program</span>
      </div>
      <div className="px-4 pb-4">
        <h3 className="text-sm font-semibold text-student-ink mb-1">{promo.title}</h3>
        {promo.description && (
          <p className="text-xs text-student-text line-clamp-2 mb-2">{promo.description}</p>
        )}
        <div className="flex items-center justify-between">
          <span className="text-[10px] text-student-text">{(promo as any).institution_name || ''}</span>
          <span className="text-xs text-gold font-medium flex items-center gap-1">
            Learn more <ChevronRight size={10} />
          </span>
        </div>
      </div>
    </div>
  )
}
