import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { listEvents, rsvpEvent, cancelRsvp, getMyRsvps } from '../../../api/events'
import { getFeaturedPromotions, getPublicPostsFeed } from '../../../api/institutions'
import {
  Calendar, MapPin, Users, ChevronRight, Sparkles,
  Megaphone, GraduationCap, Globe, Heart, BookOpen,
  Monitor, Briefcase, Wrench, Palette, Scale,
} from 'lucide-react'
import type { Promotion, InstitutionPost } from '../../../types'

const INTEREST_FILTERS = [
  { key: 'all', label: 'All', icon: Globe },
  { key: 'cs', label: 'Computer Science', icon: Monitor },
  { key: 'biz', label: 'Business', icon: Briefcase },
  { key: 'eng', label: 'Engineering', icon: Wrench },
  { key: 'health', label: 'Health', icon: Heart },
  { key: 'arts', label: 'Arts & Design', icon: Palette },
  { key: 'edu', label: 'Education', icon: BookOpen },
  { key: 'law', label: 'Law', icon: Scale },
]

function formatEventDate(dateStr: string) {
  const d = new Date(dateStr)
  const month = d.toLocaleString('en-US', { month: 'short' })
  const day = d.getDate()
  const time = d.toLocaleString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true })
  return { month, day, time }
}

function daysUntil(dateStr: string) {
  const diff = Math.ceil((new Date(dateStr).getTime() - Date.now()) / 86400000)
  if (diff === 0) return 'Today'
  if (diff === 1) return 'Tomorrow'
  if (diff < 0) return 'Past'
  return `In ${diff} days`
}

export default function CommunityTab() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [interest, setInterest] = useState('all')

  const { data: events, isLoading: eventsLoading } = useQuery({
    queryKey: ['community-events'],
    queryFn: () => listEvents({ limit: 12 }),
    retry: false,
  })

  const { data: rsvps } = useQuery({
    queryKey: ['my-rsvps'],
    queryFn: getMyRsvps,
    retry: false,
  })

  const { data: promotions, isLoading: promosLoading } = useQuery({
    queryKey: ['featured-promotions'],
    queryFn: () => getFeaturedPromotions(),
    retry: false,
  })

  const { data: posts, isLoading: postsLoading } = useQuery({
    queryKey: ['posts-feed'],
    queryFn: () => getPublicPostsFeed(15),
    retry: false,
  })

  const rsvpSet = new Set((rsvps as any[] ?? []).map((r: any) => r.event_id))

  const rsvpMut = useMutation({
    mutationFn: (eventId: string) => rsvpSet.has(eventId) ? cancelRsvp(eventId) : rsvpEvent(eventId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['community-events'] })
      queryClient.invalidateQueries({ queryKey: ['my-rsvps'] })
    },
  })

  const eventsList: any[] = Array.isArray(events) ? events : []
  const promosList: Promotion[] = Array.isArray(promotions) ? promotions : []
  const postsList: InstitutionPost[] = Array.isArray(posts) ? posts : []

  const hasData = eventsList.length > 0 || promosList.length > 0 || postsList.length > 0

  return (
    <div className="space-y-8">
      {/* Interest filter pills */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1">
        {INTEREST_FILTERS.map(f => (
          <button
            key={f.key}
            onClick={() => setInterest(f.key)}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-full whitespace-nowrap transition-colors ${
              interest === f.key
                ? 'bg-student text-white'
                : 'bg-student-mist text-student-text hover:bg-student-moss'
            }`}
          >
            <f.icon size={12} />
            {f.label}
          </button>
        ))}
      </div>

      {!hasData && !eventsLoading && !promosLoading && !postsLoading && (
        <div className="text-center py-16">
          <GraduationCap size={48} className="mx-auto text-stone mb-4" />
          <h3 className="text-lg font-medium text-student-ink mb-2">Community is growing</h3>
          <p className="text-sm text-student-text max-w-md mx-auto">
            Schools are joining UniPaith and creating events, sharing updates, and featuring their programs.
            Check back soon — or explore programs in Browse & Search.
          </p>
        </div>
      )}

      {/* Upcoming Events */}
      {eventsList.length > 0 && (
        <section>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-lg font-semibold text-student-ink flex items-center gap-2">
              <Calendar size={18} className="text-student" /> Upcoming Events
            </h2>
            <span className="text-xs text-student-text">{eventsList.length} events</span>
          </div>
          <div className="flex gap-4 overflow-x-auto pb-2">
            {eventsList.slice(0, 8).map((evt: any) => {
              const { month, day, time } = formatEventDate(evt.start_time)
              const isRsvped = rsvpSet.has(evt.id)
              const spotsLeft = evt.capacity ? Math.max(0, evt.capacity - (evt.rsvp_count || 0)) : null
              return (
                <div
                  key={evt.id}
                  className="flex-shrink-0 w-72 bg-white rounded-xl border border-stone p-4 hover:shadow-md transition-shadow"
                >
                  <div className="flex gap-3 mb-3">
                    <div className="w-12 h-14 bg-student-mist rounded-lg flex flex-col items-center justify-center flex-shrink-0">
                      <span className="text-[10px] font-semibold text-student uppercase">{month}</span>
                      <span className="text-lg font-bold text-student-ink">{day}</span>
                    </div>
                    <div className="min-w-0 flex-1">
                      <h3 className="text-sm font-semibold text-student-ink truncate">{evt.event_name}</h3>
                      <p className="text-xs text-student-text truncate">{evt.institution_name || 'School Event'}</p>
                      {evt.event_type && (
                        <span className="inline-block mt-1 px-2 py-0.5 text-[10px] font-medium rounded-full bg-gold-soft text-gold">
                          {evt.event_type.replace(/_/g, ' ')}
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-3 text-xs text-student-text mb-3">
                    <span className="flex items-center gap-1">
                      <Calendar size={10} /> {time}
                    </span>
                    {evt.location && (
                      <span className="flex items-center gap-1 truncate">
                        <MapPin size={10} /> {evt.location}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center justify-between">
                    {spotsLeft !== null && (
                      <span className="text-[10px] text-student-text">
                        <Users size={10} className="inline mr-1" />
                        {spotsLeft > 0 ? `${spotsLeft} spots left` : 'Full'}
                      </span>
                    )}
                    <button
                      onClick={() => rsvpMut.mutate(evt.id)}
                      disabled={rsvpMut.isPending}
                      className={`ml-auto px-3 py-1 text-xs font-medium rounded-lg transition-colors ${
                        isRsvped
                          ? 'bg-student-mist text-student border border-student'
                          : 'bg-student text-white hover:bg-student-hover'
                      }`}
                    >
                      {isRsvped ? 'Cancel RSVP' : 'RSVP'}
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        </section>
      )}

      {/* Featured Programs / Promotions */}
      {promosList.length > 0 && (
        <section>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-lg font-semibold text-student-ink flex items-center gap-2">
              <Sparkles size={18} className="text-gold" /> Featured Programs
            </h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {promosList.slice(0, 6).map((promo: Promotion) => (
              <div
                key={promo.id}
                onClick={() => promo.program_id && navigate(`/s/programs/${promo.program_id}`)}
                className="bg-white rounded-xl border border-stone p-4 hover:shadow-md transition-shadow cursor-pointer"
              >
                <div className="flex items-start justify-between mb-2">
                  <span className="px-2 py-0.5 text-[10px] font-medium rounded-full bg-gold-soft text-gold">
                    <Megaphone size={10} className="inline mr-1" />Featured
                  </span>
                  {promo.ends_at && (
                    <span className="text-[10px] text-student-text">{daysUntil(promo.ends_at)}</span>
                  )}
                </div>
                <h3 className="text-sm font-semibold text-student-ink mb-1">{promo.title}</h3>
                {promo.description && (
                  <p className="text-xs text-student-text line-clamp-2 mb-2">{promo.description}</p>
                )}
                <div className="flex items-center justify-between">
                  <span className="text-xs text-student-text">{(promo as any).institution_name || ''}</span>
                  <ChevronRight size={14} className="text-student" />
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* School Updates / Posts Feed */}
      {postsList.length > 0 && (
        <section>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-lg font-semibold text-student-ink flex items-center gap-2">
              <Megaphone size={18} className="text-student" /> School Updates
            </h2>
          </div>
          <div className="space-y-3">
            {postsList.slice(0, 10).map((post: InstitutionPost) => (
              <div
                key={post.id}
                className="bg-white rounded-xl border border-stone p-4 hover:shadow-sm transition-shadow"
              >
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 bg-student-mist rounded-full flex items-center justify-center flex-shrink-0">
                    <GraduationCap size={18} className="text-student" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-semibold text-student-ink">
                        {post.institution_name || 'School'}
                      </span>
                      <span className="text-[10px] text-student-text">
                        {new Date(post.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                      </span>
                    </div>
                    <h3 className="text-sm font-medium text-student-ink mb-1">{post.title}</h3>
                    <p className="text-xs text-student-text line-clamp-3">{post.body}</p>
                    {post.media_urls && post.media_urls.length > 0 && (
                      <div className="mt-2 flex gap-2">
                        {post.media_urls.slice(0, 3).map((m: any, i: number) => (
                          <div key={i} className="w-16 h-16 rounded-lg bg-student-mist overflow-hidden">
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
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  )
}
