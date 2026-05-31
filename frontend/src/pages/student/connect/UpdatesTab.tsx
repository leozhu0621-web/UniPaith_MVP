// Connect → Updates (Spec 20 §4). Reverse-chronological or relevance-ranked
// feed of posts + deadline reminders + program changes from followed institutions.
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Search } from 'lucide-react'
import { getConnectFeed, muteFollowing, type ConnectFeedItem } from '../../../api/connect'
import { createReminder } from '../../../api/calendar'
import FeedItemCard from './ConnectCards'

export default function UpdatesTab() {
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [rank, setRank] = useState<'recent' | 'relevant'>('recent')

  const { data, isLoading } = useQuery({
    queryKey: ['connect-feed', rank],
    queryFn: () => getConnectFeed(rank),
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

  const items = data?.items ?? []
  const followedCount = data?.followed_count ?? 0

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map(i => <div key={i} className="h-32 bg-white rounded-xl border border-divider animate-pulse" />)}
      </div>
    )
  }

  // No follows (Spec 20 §9)
  if (followedCount === 0) {
    return (
      <div className="text-center py-14">
        <h3 className="text-base font-semibold text-student-ink mb-1">Follow a program to see updates here.</h3>
        <p className="text-sm text-student-text mb-5 max-w-sm mx-auto">
          Saving a program follows its institution automatically — their updates, deadlines, and events land here.
        </p>
        <button
          onClick={() => navigate('/s/explore')}
          className="inline-flex items-center gap-2 px-5 py-2.5 bg-cobalt text-white text-sm font-medium rounded-lg hover:bg-cobalt-dark transition-colors"
        >
          <Search size={16} /> Find programs
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-end">
        <div className="inline-flex rounded-full bg-student-mist p-0.5">
          {(['recent', 'relevant'] as const).map(r => (
            <button
              key={r}
              onClick={() => setRank(r)}
              className={`px-3 py-1 text-xs font-medium rounded-full transition-colors ${
                rank === r ? 'bg-white text-student-ink shadow-sm' : 'text-student-text'
              }`}
            >
              {r === 'recent' ? 'Recent' : 'Most relevant'}
            </button>
          ))}
        </div>
      </div>

      {items.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-sm text-student-text">
            You're following {followedCount} institution{followedCount !== 1 ? 's' : ''}. New updates will appear here.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {items.map(item => (
            <FeedItemCard
              key={item.id}
              item={item}
              onViewProgram={onViewProgram}
              onAddToCalendar={onAddToCalendar}
              onMute={item.kind === 'post' ? (id => muteMut.mutate(id)) : undefined}
            />
          ))}
        </div>
      )}
    </div>
  )
}
