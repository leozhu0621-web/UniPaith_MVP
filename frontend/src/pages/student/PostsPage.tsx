import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getStudentFeed } from '../../api/students'
import { listSaved } from '../../api/saved-lists'
import { rsvpEvent, cancelRsvp, getMyRsvps } from '../../api/events'
import EventCard from './explore/cards/EventCard'
import PostCard from './explore/cards/PostCard'
import { Rss, Search, GraduationCap } from 'lucide-react'

export default function PostsPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [selectedSchool, setSelectedSchool] = useState<string | null>(null)

  const { data: feed, isLoading } = useQuery({
    queryKey: ['student-feed'],
    queryFn: () => getStudentFeed(50),
    retry: false,
  })

  useQuery({ queryKey: ['saved-programs'], queryFn: listSaved, retry: false })
  const { data: rsvps } = useQuery({ queryKey: ['my-rsvps'], queryFn: getMyRsvps, retry: false })

  const rsvpSet = new Set((rsvps as any[] ?? []).map((r: any) => r.event_id))
  const rsvpMut = useMutation({
    mutationFn: (eventId: string) => rsvpSet.has(eventId) ? cancelRsvp(eventId) : rsvpEvent(eventId),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['student-feed'] }); queryClient.invalidateQueries({ queryKey: ['my-rsvps'] }) },
  })

  const items: any[] = feed?.items ?? []
  const followedCount: number = feed?.followed_count ?? 0

  // Derive school list from feed items
  const schools = (() => {
    const map = new Map<string, { id: string; name: string; count: number; lastDate: string }>()
    for (const item of items) {
      const id = item.institution_id
      const name = item.institution_name
      if (!id || !name) continue
      const existing = map.get(id)
      if (existing) {
        existing.count++
        if (item.date > existing.lastDate) existing.lastDate = item.date
      } else {
        map.set(id, { id, name, count: 1, lastDate: item.date || '' })
      }
    }
    return Array.from(map.values()).sort((a, b) => b.lastDate.localeCompare(a.lastDate))
  })()

  // Filter items by selected school
  const filteredItems = selectedSchool
    ? items.filter(i => i.institution_id === selectedSchool)
    : items

  // Loading
  if (isLoading) {
    return (
      <div className="flex h-full">
        <aside className="w-52 border-r border-divider bg-white p-4 hidden lg:block">
          {[1, 2, 3].map(i => <div key={i} className="h-14 bg-student-mist rounded-lg mb-2 animate-pulse" />)}
        </aside>
        <div className="flex-1 p-6">
          <div className="max-w-2xl mx-auto space-y-4">
            {[1, 2, 3].map(i => <div key={i} className="h-32 bg-white rounded-xl border border-divider animate-pulse" />)}
          </div>
        </div>
      </div>
    )
  }

  // Empty state — no followed schools
  if (followedCount === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center max-w-md px-6">
          <div className="w-16 h-16 rounded-full bg-student-mist flex items-center justify-center mx-auto mb-4">
            <Rss size={28} className="text-student" />
          </div>
          <h2 className="text-lg font-semibold text-student-ink mb-2">Your feed is empty</h2>
          <p className="text-sm text-student-text mb-6">
            When you save programs in Explore, you'll automatically follow those schools. Their events, updates, and announcements will appear here.
          </p>
          <button
            onClick={() => navigate('/s/explore')}
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-student text-white text-sm font-medium rounded-xl hover:bg-student-hover transition-colors"
          >
            <Search size={16} /> Explore Programs
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-full">
      {/* Left: School panel (~200px, narrow) */}
      <aside className="w-52 flex-shrink-0 border-r border-divider bg-white overflow-y-auto hidden lg:block">
        <div className="p-3">
          <p className="text-[10px] font-semibold text-student-text uppercase tracking-wider px-2 mb-2">
            Your Schools ({schools.length})
          </p>

          {/* All button */}
          <button
            onClick={() => setSelectedSchool(null)}
            className={`w-full text-left px-3 py-2 rounded-lg text-xs font-medium mb-1 transition-colors ${
              !selectedSchool ? 'bg-student-mist text-student-ink' : 'text-student-text hover:bg-student-mist'
            }`}
          >
            All Updates
          </button>

          {/* School list */}
          {schools.map(s => {
            const isActive = selectedSchool === s.id
            const hasNew = s.lastDate && new Date(s.lastDate) > new Date(Date.now() - 86400000 * 2)
            return (
              <button
                key={s.id}
                onClick={() => setSelectedSchool(isActive ? null : s.id)}
                className={`w-full text-left px-3 py-2.5 rounded-lg mb-0.5 transition-colors ${
                  isActive ? 'bg-student-mist' : 'hover:bg-student-mist/50'
                }`}
              >
                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 rounded-md bg-school-mist flex items-center justify-center flex-shrink-0">
                    <GraduationCap size={13} className="text-school" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-1">
                      {hasNew && <span className="w-1.5 h-1.5 rounded-full bg-student flex-shrink-0" />}
                      <p className="text-xs font-medium text-student-ink truncate">{s.name}</p>
                    </div>
                    <p className="text-[10px] text-student-text">{s.count} update{s.count !== 1 ? 's' : ''}</p>
                  </div>
                </div>
              </button>
            )
          })}
        </div>
      </aside>

      {/* Right: Feed (flex-1, takes most space) */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-2xl mx-auto px-6 py-6 space-y-4">
          {selectedSchool && (
            <div className="flex items-center gap-2 pb-3 border-b border-divider">
              <GraduationCap size={14} className="text-school" />
              <span className="text-sm font-medium text-student-ink">
                {schools.find(s => s.id === selectedSchool)?.name || 'School'}
              </span>
              <button onClick={() => setSelectedSchool(null)} className="text-xs text-student-text hover:text-student-ink ml-auto">
                Show all
              </button>
            </div>
          )}

          {filteredItems.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-sm text-student-text">No updates from this school yet.</p>
            </div>
          ) : (
            filteredItems.map((item: any) => {
              if (item.type === 'event') {
                return <EventCard key={`ev-${item.id}`} event={item} isRsvped={rsvpSet.has(item.id)} onRsvp={() => rsvpMut.mutate(item.id)} />
              }
              if (item.type === 'post') {
                return (
                  <PostCard
                    key={`post-${item.id}`}
                    post={{
                      id: item.id, institution_id: item.institution_id, author_id: null,
                      title: item.title, body: item.body || '', media_urls: item.media_urls,
                      pinned: false, tagged_program_ids: null, tagged_intake: null,
                      status: 'published', created_at: item.date, updated_at: item.date,
                      institution_name: item.institution_name,
                    } as any}
                  />
                )
              }
              return null
            })
          )}
        </div>
      </div>
    </div>
  )
}
