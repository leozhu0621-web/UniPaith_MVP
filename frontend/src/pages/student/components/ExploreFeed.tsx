import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { searchPrograms } from '../../../api/programs'
import { listEvents, rsvpEvent, cancelRsvp, getMyRsvps } from '../../../api/events'
import { getFeaturedPromotions, getPublicPostsFeed } from '../../../api/institutions'
import { listSaved, saveProgram, unsaveProgram } from '../../../api/saved-lists'
import { formatCurrency } from '../../../utils/format'
import { DEGREE_LABELS } from '../../../utils/constants'
import type { ProgramSummary, Promotion, InstitutionPost } from '../../../types'
import {
  Search, Bookmark, BookmarkCheck, MapPin, Clock, DollarSign,
  Calendar, Users, Sparkles, GraduationCap, Megaphone,
  ChevronRight, Heart, ExternalLink, TrendingUp, Globe,
  Monitor, Briefcase, Wrench, Palette, BookOpen, Scale,
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
  const [interest, setInterest] = useState('all')
  const [searchQ, setSearchQ] = useState('')

  // --- Data fetching ---
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
          if (item.type === 'program') return <ProgramCard key={`p-${item.data.id}`} program={item.data} saved={savedIds.has(item.data.id)} onSave={() => toggleSave(item.data.id)} onView={() => navigate(`/s/programs/${item.data.id}`)} />
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

function ProgramCard({ program, saved, onSave, onView }: {
  program: ProgramSummary; saved: boolean; onSave: () => void; onView: () => void
}) {
  const degree = DEGREE_LABELS[program.degree_type] || program.degree_type
  return (
    <div className="bg-white rounded-xl border border-divider hover:shadow-md transition-shadow overflow-hidden">
      {/* Header bar — institution info */}
      <div className="flex items-center gap-3 px-4 pt-4 pb-2">
        <div className="w-10 h-10 rounded-lg bg-student-mist flex items-center justify-center flex-shrink-0">
          <GraduationCap size={18} className="text-student" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-student-ink truncate">{program.institution_name}</p>
          <p className="text-[10px] text-student-text flex items-center gap-1">
            <MapPin size={9} />
            {program.institution_city ? `${program.institution_city}, ` : ''}{program.institution_country}
          </p>
        </div>
        <button
          onClick={e => { e.stopPropagation(); onSave() }}
          className="p-1.5 rounded-lg hover:bg-student-mist transition-colors"
        >
          {saved
            ? <BookmarkCheck size={16} className="text-student" />
            : <Bookmark size={16} className="text-student-text" />
          }
        </button>
      </div>

      {/* Program body */}
      <div className="px-4 pb-4 cursor-pointer" onClick={onView}>
        <h3 className="text-base font-semibold text-student-ink mb-1">{program.program_name}</h3>
        <div className="flex flex-wrap gap-2 mb-3">
          <span className="px-2 py-0.5 text-[10px] font-medium rounded-full bg-gold-soft text-gold">{degree}</span>
          {program.delivery_format && (
            <span className="px-2 py-0.5 text-[10px] font-medium rounded-full bg-student-mist text-student">
              {program.delivery_format.replace(/_/g, ' ')}
            </span>
          )}
          {program.duration_months && (
            <span className="px-2 py-0.5 text-[10px] rounded-full bg-gray-100 text-gray-600 flex items-center gap-0.5">
              <Clock size={8} /> {program.duration_months}mo
            </span>
          )}
        </div>

        {/* Metrics row */}
        <div className="flex items-center gap-4 text-xs text-student-text">
          {program.tuition != null && (
            <span className="flex items-center gap-1">
              <DollarSign size={11} /> {formatCurrency(program.tuition)}/yr
            </span>
          )}
          {program.median_salary != null && (
            <span className="flex items-center gap-1">
              <TrendingUp size={11} /> {formatCurrency(program.median_salary)} avg salary
            </span>
          )}
          {program.employment_rate != null && (
            <span className="flex items-center gap-1">
              <Users size={11} /> {Math.round(program.employment_rate * 100)}% employed
            </span>
          )}
        </div>
      </div>

      {/* Action bar */}
      <div className="flex items-center border-t border-divider">
        <button onClick={onView} className="flex-1 flex items-center justify-center gap-1.5 py-2.5 text-xs font-medium text-student hover:bg-student-mist transition-colors">
          <ExternalLink size={12} /> View Details
        </button>
        <div className="w-px h-6 bg-divider" />
        <button onClick={onSave} className="flex-1 flex items-center justify-center gap-1.5 py-2.5 text-xs font-medium text-student-text hover:bg-student-mist transition-colors">
          {saved ? <BookmarkCheck size={12} className="text-student" /> : <Bookmark size={12} />}
          {saved ? 'Saved' : 'Save'}
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
