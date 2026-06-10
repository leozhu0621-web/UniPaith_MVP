// Connect → Updates (Spec 20 §4). Reverse-chronological or relevance-ranked
// feed of posts + deadline reminders + program changes from followed institutions.
// Infinite scroll via keyset cursor (Spec 56 §4) + a "new since last visit" pill.
import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useInfiniteQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowUp, Loader2, Search } from 'lucide-react'
import { getConnectFeed, muteFollowing, type ConnectFeedItem } from '../../../api/connect'
import { createReminder } from '../../../api/calendar'
import FeedItemCard from './ConnectCards'
import QueryError from '../../../components/ui/QueryError'

const SEEN_KEY = 'unipaith_connect_last_seen'

export default function UpdatesTab() {
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [rank, setRank] = useState<'recent' | 'relevant'>('recent')
  const [pillDismissed, setPillDismissed] = useState(false)
  const topRef = useRef<HTMLDivElement | null>(null)
  const sentinelRef = useRef<HTMLDivElement | null>(null)
  // Captured once at mount — the newest item date the user saw last visit.
  const lastSeenRef = useRef<string>(
    (() => {
      try {
        return localStorage.getItem(SEEN_KEY) ?? ''
      } catch {
        return ''
      }
    })(),
  )

  const {
    data,
    isLoading,
    isError,
    refetch,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useInfiniteQuery({
    queryKey: ['connect-feed', rank],
    queryFn: ({ pageParam }) => getConnectFeed(rank, pageParam),
    initialPageParam: undefined as string | undefined,
    getNextPageParam: last => last.next_cursor ?? undefined,
    retry: false,
  })

  const muteMut = useMutation({
    mutationFn: (institutionId: string) => muteFollowing(institutionId, true),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['connect-feed'] })
      qc.invalidateQueries({ queryKey: ['connect-follows'] })
    },
  })

  const onViewProgram = (programId: string) => navigate(`/s/programs/${programId}`)
  const onStartApplication = (programId: string) => navigate(`/s/programs/${programId}?apply=1`)
  const onRsvpEvent = () => navigate('/s/posts?tab=events')
  const onRequestInfo = (programId: string) => navigate(`/s/messages?program=${programId}`)

  const onAddToCalendar = async (item: ConnectFeedItem) => {
    if (!item.deadline) return
    try {
      await createReminder({
        title: `${item.program_name || 'Program'} — application deadline`,
        start_at: new Date(item.deadline).toISOString(),
        notes: `From ${item.institution_name} (added from Connect)`,
      })
      qc.invalidateQueries({ queryKey: ['calendar'] })
    } catch {
      /* non-fatal — the reminder is a convenience */
    }
  }

  const items = useMemo(() => data?.pages.flatMap(p => p.items) ?? [], [data])
  const followedCount = data?.pages[0]?.followed_count ?? 0

  // "New since your last visit" — items newer than the date recorded last visit.
  const newCount = useMemo(() => {
    const since = lastSeenRef.current
    if (!since) return 0
    return items.filter(it => it.date && it.date > since).length
  }, [items])

  // Record this visit's newest item date so the next visit compares against it.
  useEffect(() => {
    if (!items.length) return
    const newest = items.reduce((m, it) => (it.date > m ? it.date : m), items[0].date)
    try {
      localStorage.setItem(SEEN_KEY, newest)
    } catch {
      /* ignore */
    }
  }, [items])

  // Infinite-scroll sentinel (Spec 56 §4).
  useEffect(() => {
    const el = sentinelRef.current
    if (!el || !hasNextPage) return
    const obs = new IntersectionObserver(
      entries => {
        if (entries[0]?.isIntersecting && hasNextPage && !isFetchingNextPage) fetchNextPage()
      },
      { rootMargin: '320px' },
    )
    obs.observe(el)
    return () => obs.disconnect()
  }, [hasNextPage, isFetchingNextPage, fetchNextPage])

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map(i => <div key={i} className="h-32 bg-card rounded-xl border border-border animate-pulse" />)}
      </div>
    )
  }

  if (isError) {
    return <QueryError onRetry={() => refetch()} />
  }

  // No follows (Spec 20 §9)
  if (followedCount === 0) {
    return (
      <div className="text-center py-14">
        <h3 className="text-base font-semibold text-foreground mb-1">Follow a program to see updates here.</h3>
        <p className="text-sm text-muted-foreground mb-5 max-w-sm mx-auto">
          Saving a program follows its institution — their updates, deadlines, and events land here.
        </p>
        <button
          onClick={() => navigate('/s/explore')}
          className="inline-flex items-center gap-2 px-5 py-2.5 bg-secondary text-secondary-foreground text-sm font-medium rounded-lg hover:brightness-95 transition-colors"
        >
          <Search size={16} /> Find programs
        </button>
      </div>
    )
  }

  const scrollToTop = () => {
    setPillDismissed(true)
    topRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  return (
    <div className="space-y-4">
      <div ref={topRef} />

      {newCount > 0 && !pillDismissed && (
        <div className="flex justify-center">
          <button
            onClick={scrollToTop}
            className="ui-btn inline-flex items-center gap-1.5 rounded-full bg-secondary px-3.5 py-1.5 text-xs font-semibold text-secondary-foreground elev-subtle hover:brightness-95 transition"
          >
            <ArrowUp size={13} /> {newCount} new since your last visit
          </button>
        </div>
      )}

      <div className="flex items-center justify-end">
        <div className="inline-flex rounded-full bg-muted p-0.5">
          {(['recent', 'relevant'] as const).map(r => (
            <button
              key={r}
              onClick={() => setRank(r)}
              className={`px-3 py-1 text-xs font-medium rounded-full transition-colors ${
                rank === r ? 'bg-card text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              {r === 'recent' ? 'Recent' : 'Most relevant'}
            </button>
          ))}
        </div>
      </div>

      {items.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-sm text-muted-foreground">
            You're following {followedCount} institution{followedCount !== 1 ? 's' : ''}. New updates will appear here.
          </p>
        </div>
      ) : (
        <>
          <div className="space-y-3">
            {items.map(item => (
              <FeedItemCard
                key={item.id}
                item={item}
                onViewProgram={onViewProgram}
                onAddToCalendar={onAddToCalendar}
                onStartApplication={onStartApplication}
                onRsvpEvent={onRsvpEvent}
                onRequestInfo={onRequestInfo}
                onMute={item.kind === 'post' ? (id => muteMut.mutate(id)) : undefined}
              />
            ))}
          </div>

          {/* Infinite-scroll sentinel + loading indicator (Spec 56 §4). */}
          <div ref={sentinelRef} className="h-8 flex items-center justify-center">
            {isFetchingNextPage && <Loader2 size={16} className="animate-spin text-muted-foreground" />}
          </div>
        </>
      )}
    </div>
  )
}
