// Manage Following panel (Spec 20 §3). Lists followed institutions with
// mute / unfollow. Following is a user-controlled choice, so unfollow is
// always available — even with an active application at the institution.
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Bell, BellOff, GraduationCap } from 'lucide-react'
import { getFollowing, muteFollowing, unfollowInstitution, type FollowDetail } from '../../../api/connect'
import { confirmDialog } from '../../../stores/confirm-store'
import { showToast } from '../../../stores/toast-store'
import Sheet from '../../../components/ui/Sheet'
import Skeleton from '../../../components/ui/Skeleton'
import QueryError from '../../../components/ui/QueryError'

export default function ManageFollowingPanel({ onClose }: { onClose: () => void }) {
  const qc = useQueryClient()
  const { data: follows, isLoading, isError, refetch } = useQuery({
    queryKey: ['connect-follows'], queryFn: getFollowing, retry: false,
  })

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ['connect-follows'] })
    qc.invalidateQueries({ queryKey: ['connect-feed'] })
  }
  // Optimistic mute/unfollow (Ship D §4): patch the cached list so the row
  // responds instantly; roll back + toast on failure, reconcile on settle.
  const muteMut = useMutation({
    mutationFn: ({ id, muted }: { id: string; muted: boolean }) => muteFollowing(id, muted),
    onMutate: async ({ id, muted }) => {
      await qc.cancelQueries({ queryKey: ['connect-follows'] })
      const previous = qc.getQueryData<FollowDetail[]>(['connect-follows'])
      qc.setQueryData<FollowDetail[]>(['connect-follows'], old =>
        old?.map(f => (f.institution_id === id ? { ...f, muted } : f)))
      return { previous }
    },
    onError: (_err, _vars, ctx) => {
      if (ctx?.previous !== undefined) qc.setQueryData(['connect-follows'], ctx.previous)
      showToast("We couldn't update notifications for this school. Please try again.", 'error')
    },
    onSettled: invalidate,
  })
  const unfollowMut = useMutation({
    mutationFn: (id: string) => unfollowInstitution(id),
    onMutate: async (id) => {
      await qc.cancelQueries({ queryKey: ['connect-follows'] })
      const previous = qc.getQueryData<FollowDetail[]>(['connect-follows'])
      qc.setQueryData<FollowDetail[]>(['connect-follows'], old =>
        old?.filter(f => f.institution_id !== id))
      return { previous }
    },
    onError: (_err, _vars, ctx) => {
      if (ctx?.previous !== undefined) qc.setQueryData(['connect-follows'], ctx.previous)
      showToast("We couldn't unfollow this school. Please try again.", 'error')
    },
    onSettled: invalidate,
  })

  return (
    <Sheet isOpen onClose={onClose} title="Manage following" side="right">
      {isLoading ? (
        <div className="space-y-2">{[1, 2, 3].map(i => <Skeleton key={i} className="h-12 rounded-lg" />)}</div>
      ) : isError ? (
        // A failed fetch is not "not following anyone" — say so, with a retry.
        <QueryError detail="We couldn't load the schools you follow." onRetry={() => refetch()} />
      ) : (follows?.length ?? 0) === 0 ? (
        <p className="text-center text-sm text-muted-foreground py-8">You're not following any institutions yet.</p>
      ) : (
        <ul className="divide-y divide-border -mx-6">
          {follows!.map((f: FollowDetail) => (
            <li key={f.institution_id} className="flex items-center gap-3 px-6 py-3">
              <div className="w-8 h-8 rounded-md bg-secondary/10 flex items-center justify-center flex-shrink-0">
                <GraduationCap size={15} className="text-secondary" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-foreground truncate">{f.name}</p>
                <p className="text-[10px] text-muted-foreground">
                  {[f.city, f.country].filter(Boolean).join(', ') || `${f.program_count} program${f.program_count !== 1 ? 's' : ''}`}
                  {f.source === 'application' && ' · applying'}
                  {f.source === 'saved' && ' · saved'}
                </p>
              </div>
              <button
                onClick={() => muteMut.mutate({ id: f.institution_id, muted: !f.muted })}
                title={f.muted ? 'Unmute' : 'Mute'}
                className={`p-1.5 rounded-lg transition-colors ${f.muted ? 'text-muted-foreground bg-muted' : 'text-secondary hover:bg-secondary/5'}`}
              >
                {f.muted ? <BellOff size={15} /> : <Bell size={15} />}
              </button>
              <button
                onClick={async () => {
                  if (await confirmDialog({
                    title: 'Unfollow?',
                    body: "You'll stop seeing their updates.",
                    confirmLabel: 'Unfollow',
                    destructive: true,
                  })) {
                    unfollowMut.mutate(f.institution_id)
                  }
                }}
                className="text-xs font-medium text-muted-foreground hover:text-error transition-colors"
              >
                Unfollow
              </button>
            </li>
          ))}
        </ul>
      )}
    </Sheet>
  )
}
