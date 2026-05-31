// Manage Following panel (Spec 20 §3). Lists followed institutions with
// mute / unfollow. Unfollow is blocked while an active application exists —
// the panel shows why (Spec 20 §2).
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Bell, BellOff, GraduationCap, Lock, X } from 'lucide-react'
import { getFollowing, muteFollowing, unfollowInstitution, type FollowDetail } from '../../../api/connect'

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
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 px-4 bg-charcoal/40" onClick={onClose}>
      <div className="bg-white rounded-2xl max-w-md w-full max-h-[70vh] overflow-y-auto shadow-xl" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between p-4 border-b border-divider sticky top-0 bg-white">
          <h2 className="text-sm font-semibold text-student-ink">Manage following</h2>
          <button onClick={onClose} className="text-student-text hover:text-student-ink p-1"><X size={18} /></button>
        </div>

        {isLoading ? (
          <div className="p-4 space-y-2">{[1, 2, 3].map(i => <div key={i} className="h-12 bg-student-mist rounded-lg animate-pulse" />)}</div>
        ) : (follows?.length ?? 0) === 0 ? (
          <p className="p-6 text-center text-sm text-student-text">You're not following any institutions yet.</p>
        ) : (
          <ul className="divide-y divide-divider">
            {follows!.map((f: FollowDetail) => (
              <li key={f.institution_id} className="flex items-center gap-3 p-3">
                <div className="w-8 h-8 rounded-md bg-cobalt/10 flex items-center justify-center flex-shrink-0">
                  <GraduationCap size={15} className="text-cobalt" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-student-ink truncate">{f.name}</p>
                  <p className="text-[10px] text-student-text">
                    {[f.city, f.country].filter(Boolean).join(', ') || `${f.program_count} program${f.program_count !== 1 ? 's' : ''}`}
                    {f.source === 'application' && ' · applying'}
                    {f.source === 'saved' && ' · saved'}
                  </p>
                </div>
                <button
                  onClick={() => muteMut.mutate({ id: f.institution_id, muted: !f.muted })}
                  title={f.muted ? 'Unmute' : 'Mute'}
                  className={`p-1.5 rounded-lg transition-colors ${f.muted ? 'text-student-text bg-student-mist' : 'text-cobalt hover:bg-cobalt/5'}`}
                >
                  {f.muted ? <BellOff size={15} /> : <Bell size={15} />}
                </button>
                {f.can_unfollow ? (
                  <button
                    onClick={() => unfollowMut.mutate(f.institution_id)}
                    className="text-xs font-medium text-student-text hover:text-error transition-colors"
                  >
                    Unfollow
                  </button>
                ) : (
                  <span
                    title="You have an active application here. Withdraw it to unfollow."
                    className="inline-flex items-center gap-1 text-[10px] text-student-text"
                  >
                    <Lock size={11} /> Applying
                  </span>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
