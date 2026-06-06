// Manage Following panel (Spec 20 §3). Lists followed institutions with
// mute / unfollow. Unfollow is blocked while an active application exists —
// the panel shows why (Spec 20 §2).
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Bell, BellOff, GraduationCap, Lock } from 'lucide-react'
import { getFollowing, muteFollowing, unfollowInstitution, type FollowDetail } from '../../../api/connect'
import { confirmDialog } from '../../../stores/confirm-store'
import Sheet from '../../../components/ui/Sheet'

export default function ManageFollowingPanel({ onClose }: { onClose: () => void }) {
  const qc = useQueryClient()
  const { data: follows, isLoading } = useQuery({
    queryKey: ['connect-follows'], queryFn: getFollowing, retry: false,
  })

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ['connect-follows'] })
    qc.invalidateQueries({ queryKey: ['connect-feed'] })
  }
  const muteMut = useMutation({
    mutationFn: ({ id, muted }: { id: string; muted: boolean }) => muteFollowing(id, muted),
    onSuccess: invalidate,
  })
  const unfollowMut = useMutation({
    mutationFn: (id: string) => unfollowInstitution(id),
    onSuccess: invalidate,
  })

  return (
    <Sheet isOpen onClose={onClose} title="Manage following" side="right">
      {isLoading ? (
        <div className="space-y-2">{[1, 2, 3].map(i => <div key={i} className="h-12 bg-muted rounded-lg animate-pulse" />)}</div>
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
              {f.can_unfollow ? (
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
              ) : (
                <span
                  title="You have an active application here. Withdraw it to unfollow."
                  className="inline-flex items-center gap-1 text-[10px] text-muted-foreground"
                >
                  <Lock size={11} /> Applying
                </span>
              )}
            </li>
          ))}
        </ul>
      )}
    </Sheet>
  )
}
