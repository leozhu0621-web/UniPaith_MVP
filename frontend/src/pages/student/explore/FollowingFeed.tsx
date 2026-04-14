import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getStudentFeed } from '../../../api/students'
import { rsvpEvent, cancelRsvp, getMyRsvps } from '../../../api/events'
import EventCard from './cards/EventCard'
import PostCard from './cards/PostCard'
import { Rss, Search, GraduationCap } from 'lucide-react'

export default function FollowingFeed() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data: feed, isLoading } = useQuery({
    queryKey: ['student-feed'],
    queryFn: () => getStudentFeed(30),
    retry: false,
  })

  const { data: rsvps } = useQuery({
    queryKey: ['my-rsvps'],
    queryFn: getMyRsvps,
    retry: false,
  })

  const rsvpSet = new Set((rsvps as any[] ?? []).map((r: any) => r.event_id))

  const rsvpMut = useMutation({
    mutationFn: (eventId: string) => rsvpSet.has(eventId) ? cancelRsvp(eventId) : rsvpEvent(eventId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['student-feed'] })
      queryClient.invalidateQueries({ queryKey: ['my-rsvps'] })
    },
  })

  const items: any[] = feed?.items ?? []
  const followedCount: number = feed?.followed_count ?? 0

  // Loading state
  if (isLoading) {
    return (
      <div className="max-w-2xl mx-auto space-y-4">
        {[1, 2, 3].map(i => (
          <div key={i} className="bg-white rounded-xl border border-divider p-6 animate-pulse">
            <div className="h-4 bg-student-mist rounded w-1/3 mb-3" />
            <div className="h-3 bg-student-mist rounded w-2/3 mb-2" />
            <div className="h-3 bg-student-mist rounded w-1/2" />
          </div>
        ))}
      </div>
    )
  }

  // Empty state — no followed schools
  if (followedCount === 0) {
    return (
      <div className="max-w-2xl mx-auto text-center py-16">
        <div className="w-16 h-16 rounded-full bg-student-mist flex items-center justify-center mx-auto mb-4">
          <Rss size={28} className="text-student" />
        </div>
        <h3 className="text-lg font-semibold text-student-ink mb-2">Your feed is empty</h3>
        <p className="text-sm text-student-text max-w-md mx-auto mb-6">
          When you save programs, you'll automatically follow those schools. Their events, updates, and announcements will appear here — like a personalized news feed.
        </p>
        <button
          onClick={() => navigate('/s/explore?tab=discover')}
          className="inline-flex items-center gap-2 px-5 py-2.5 bg-student text-white text-sm font-medium rounded-xl hover:bg-student-hover transition-colors"
        >
          <Search size={16} /> Discover Programs
        </button>
      </div>
    )
  }

  // Feed with content
  return (
    <div className="max-w-2xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-2 mb-4 pb-3 border-b border-divider">
        <Rss size={16} className="text-student" />
        <span className="text-sm font-medium text-student-ink">Updates from {followedCount} school{followedCount !== 1 ? 's' : ''} you follow</span>
      </div>

      {items.length === 0 ? (
        <div className="text-center py-12">
          <GraduationCap size={32} className="mx-auto text-stone mb-3" />
          <p className="text-sm text-student-text">No updates yet from schools you follow. Check back soon.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {items.map((item: any) => {
            if (item.type === 'event') {
              return (
                <EventCard
                  key={`ev-${item.id}`}
                  event={item}
                  isRsvped={rsvpSet.has(item.id)}
                  onRsvp={() => rsvpMut.mutate(item.id)}
                />
              )
            }
            if (item.type === 'post') {
              return (
                <PostCard
                  key={`post-${item.id}`}
                  post={{
                    id: item.id,
                    institution_id: item.institution_id,
                    author_id: null,
                    title: item.title,
                    body: item.body || '',
                    media_urls: item.media_urls,
                    pinned: false,
                    tagged_program_ids: null,
                    tagged_intake: null,
                    status: 'published',
                    created_at: item.date,
                    updated_at: item.date,
                    institution_name: item.institution_name,
                  } as any}
                />
              )
            }
            return null
          })}
        </div>
      )}
    </div>
  )
}
