// Connect → Peers (Spec 20 §6). Opt-in, privacy-gated. Off by default; the
// opt-in explainer is the entire tab body until the student opts in. Peer cards
// never show scores or rings (§6.2 / §10). Behind connect_peers_enabled.
import { useState } from 'react'
import { confirmDialog } from '../../../stores/confirm-store'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Ban, Check, Flag, MapPin, ShieldCheck, UserPlus, Users } from 'lucide-react'
import {
  blockPeer, discoverPeers, getMyPeerProfile, getPeersStatus, optInPeers,
  reportPeer, requestPeer, respondPeer, updateMyPeerProfile,
  type PeerCard, type PeerVisibilityProfile,
} from '../../../api/connect'
import QueryError from '../../../components/ui/QueryError'
import Skeleton from '../../../components/ui/Skeleton'

export default function PeersTab() {
  const qc = useQueryClient()
  const { data: status, isLoading, isError, refetch } = useQuery({
    queryKey: ['peers-status'], queryFn: getPeersStatus, retry: false,
  })

  const [optInError, setOptInError] = useState<string | null>(null)
  const optInMut = useMutation({
    mutationFn: () => optInPeers(true),
    onSuccess: () => {
      setOptInError(null)
      qc.invalidateQueries({ queryKey: ['peers-status'] })
    },
    onError: () => setOptInError("Couldn't save your preference. Please try again."),
  })

  if (isLoading) return <Skeleton className="h-40 rounded-xl" />

  if (isError) return <QueryError onRetry={() => refetch()} />

  if (!status?.enabled) {
    return (
      <EmptyExplainer
        title="Peer connections coming soon"
      />
    )
  }

  if (!status.opted_in) {
    return (
      <div className="bg-card rounded-xl border border-border p-6 text-center max-w-md mx-auto">
        <div className="w-12 h-12 rounded-full bg-secondary/10 flex items-center justify-center mx-auto mb-3">
          <Users size={22} className="text-secondary" />
        </div>
        <h3 className="text-base font-semibold text-foreground mb-1">Connect with other applicants</h3>
        <p className="text-sm text-muted-foreground mb-2">
          Others can find you by shared programs and see only what you choose to share.
        </p>
        <ul className="text-xs text-muted-foreground text-left max-w-xs mx-auto mb-4 space-y-1">
          <li className="flex items-center gap-2"><ShieldCheck size={13} className="text-secondary" /> Your scores, GPA, and financials are never shared.</li>
          <li className="flex items-center gap-2"><ShieldCheck size={13} className="text-secondary" /> You choose your display name, major, region, and bio.</li>
          <li className="flex items-center gap-2"><ShieldCheck size={13} className="text-secondary" /> Revocable any time in Settings.</li>
        </ul>
        {optInError && (
          <p className="text-xs text-error mb-3">{optInError}</p>
        )}
        <button
          onClick={() => optInMut.mutate()}
          disabled={optInMut.isPending}
          className="px-5 py-2.5 bg-secondary text-secondary-foreground text-sm font-medium rounded-lg hover:brightness-95 transition-colors disabled:opacity-60"
        >
          Turn on Peers
        </button>
      </div>
    )
  }

  return <PeersDiscovery />
}

function EmptyExplainer({ title, body }: { title: string; body?: string }) {
  return (
    <div className="text-center py-12">
      <div className="w-12 h-12 rounded-full bg-muted flex items-center justify-center mx-auto mb-3">
        <Users size={20} className="text-muted-foreground" />
      </div>
      <p className="text-sm font-medium text-foreground mb-1">{title}</p>
      {body && <p className="text-xs text-muted-foreground max-w-sm mx-auto">{body}</p>}
    </div>
  )
}

function PeersDiscovery() {
  const qc = useQueryClient()
  const [showSettings, setShowSettings] = useState(false)

  const { data: peers, isLoading, isError, refetch } = useQuery({
    queryKey: ['peers-discover'], queryFn: () => discoverPeers(), retry: false,
  })

  const invalidate = () => qc.invalidateQueries({ queryKey: ['peers-discover'] })
  const requestMut = useMutation({ mutationFn: (id: string) => requestPeer(id), onSuccess: invalidate })
  const respondMut = useMutation({ mutationFn: ({ id, accept }: { id: string; accept: boolean }) => respondPeer(id, accept), onSuccess: invalidate })
  const blockMut = useMutation({ mutationFn: (id: string) => blockPeer(id), onSuccess: invalidate })
  const reportMut = useMutation({ mutationFn: (id: string) => reportPeer(id, 'inappropriate'), onSuccess: invalidate })

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-xs text-muted-foreground">Applicants to programs you're considering.</p>
        <button
          onClick={() => setShowSettings(s => !s)}
          className="text-xs font-medium text-secondary hover:underline"
        >
          {showSettings ? 'Hide' : 'Visibility settings'}
        </button>
      </div>

      {showSettings && <VisibilityEditor onClose={() => setShowSettings(false)} />}

      {isLoading ? (
        <div className="grid sm:grid-cols-2 gap-3">
          {[1, 2].map(i => <Skeleton key={i} className="h-36 rounded-xl" />)}
        </div>
      ) : isError ? (
        <QueryError onRetry={() => refetch()} />
      ) : (peers?.length ?? 0) === 0 ? (
        <EmptyExplainer
          title="No peers yet for your programs"
        />
      ) : (
        <div className="stagger-list grid sm:grid-cols-2 gap-3">
          {peers!.map(p => (
            <PeerCardView
              key={p.peer_id}
              peer={p}
              busy={requestMut.isPending || respondMut.isPending}
              onRequest={() => requestMut.mutate(p.peer_id)}
              onAccept={() => respondMut.mutate({ id: p.peer_id, accept: true })}
              onBlock={async () => { if (await confirmDialog({ title: 'Block this peer?', body: "They won't be able to reach you.", confirmLabel: 'Block', destructive: true })) blockMut.mutate(p.peer_id) }}
              onReport={async () => { if (await confirmDialog({ title: 'Report this peer?', body: 'Our moderation team will review them.', confirmLabel: 'Report', destructive: true })) reportMut.mutate(p.peer_id) }}
            />
          ))}
        </div>
      )}
    </div>
  )
}

function PeerCardView({ peer, busy, onRequest, onAccept, onBlock, onReport }: {
  peer: PeerCard; busy?: boolean
  onRequest: () => void; onAccept: () => void; onBlock: () => void; onReport: () => void
}) {
  const initials = peer.display_name.split(' ').map(w => w[0]).slice(0, 2).join('').toUpperCase()
  return (
    <div className="bg-card rounded-xl border border-border p-4 flex flex-col">
      <div className="flex items-start gap-3">
        <div className="w-10 h-10 rounded-full bg-secondary/10 flex items-center justify-center flex-shrink-0 text-secondary text-sm font-semibold">
          {initials || '?'}
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold text-foreground truncate">{peer.display_name}</p>
          {peer.intended_major && <p className="text-xs text-muted-foreground truncate">{peer.intended_major}</p>}
          {peer.region && (
            <p className="text-[10px] text-muted-foreground flex items-center gap-0.5 mt-0.5">
              <MapPin size={9} /> {peer.region}
            </p>
          )}
        </div>
        <div className="flex items-center gap-1 flex-shrink-0">
          <button onClick={onReport} title="Report" className="text-muted-foreground hover:text-error p-1"><Flag size={13} /></button>
          <button onClick={onBlock} title="Block" className="text-muted-foreground hover:text-error p-1"><Ban size={13} /></button>
        </div>
      </div>

      {peer.bio && <p className="text-xs text-muted-foreground mt-2 line-clamp-2">{peer.bio}</p>}

      {peer.shared_programs.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-2">
          {peer.shared_programs.slice(0, 3).map(sp => (
            <span key={sp.id} className="px-2 py-0.5 text-[10px] rounded-full bg-muted text-muted-foreground">{sp.name}</span>
          ))}
        </div>
      )}

      <div className="mt-3 pt-3 border-t border-border">
        {peer.connection_state === 'connected' ? (
          <span className="inline-flex items-center gap-1 text-xs font-medium text-secondary"><Check size={13} /> Connected</span>
        ) : peer.connection_state === 'requested' ? (
          <span className="text-xs text-muted-foreground">Request sent</span>
        ) : peer.connection_state === 'incoming' ? (
          <button onClick={onAccept} disabled={busy} className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium rounded-lg bg-secondary text-secondary-foreground hover:brightness-95 transition-colors disabled:opacity-60">
            <Check size={13} /> Accept request
          </button>
        ) : (
          <button onClick={onRequest} disabled={busy} className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium rounded-lg border border-secondary text-secondary hover:bg-secondary/5 transition-colors disabled:opacity-60">
            <UserPlus size={13} /> Connect
          </button>
        )}
      </div>
    </div>
  )
}

function VisibilityEditor({ onClose }: { onClose: () => void }) {
  const qc = useQueryClient()
  const { data: profile } = useQuery({ queryKey: ['peer-profile'], queryFn: getMyPeerProfile, retry: false })
  const [form, setForm] = useState<Partial<PeerVisibilityProfile>>({})
  const merged = { ...profile, ...form } as PeerVisibilityProfile

  const saveMut = useMutation({
    mutationFn: () => updateMyPeerProfile(form),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['peer-profile'] })
      qc.invalidateQueries({ queryKey: ['peers-discover'] })
      onClose()
    },
  })

  const set = (k: keyof PeerVisibilityProfile, v: string | boolean | null) =>
    setForm(f => ({ ...f, [k]: v }))

  if (!profile) return <Skeleton className="h-40 rounded-xl" />

  return (
    <div className="bg-card rounded-xl border border-border p-4 space-y-3">
      <p className="text-xs font-semibold text-foreground">What other applicants see</p>
      <div className="grid sm:grid-cols-2 gap-3">
        <Field label="Display name">
          <input className="w-full rounded-lg border border-border px-3 py-1.5 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-secondary focus:border-secondary" value={merged.display_name ?? ''} onChange={e => set('display_name', e.target.value)} placeholder="Your name or an alias" />
        </Field>
        <Field label="Intended major">
          <input className="w-full rounded-lg border border-border px-3 py-1.5 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-secondary focus:border-secondary" value={merged.intended_major ?? ''} onChange={e => set('intended_major', e.target.value)} placeholder="e.g. Computer Science" />
        </Field>
        <Field label="Region (country / region only)">
          <input className="w-full rounded-lg border border-border px-3 py-1.5 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-secondary focus:border-secondary" value={merged.region ?? ''} onChange={e => set('region', e.target.value)} placeholder="e.g. California, USA" />
        </Field>
        <Field label="Short bio">
          <input className="w-full rounded-lg border border-border px-3 py-1.5 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-secondary focus:border-secondary" value={merged.bio ?? ''} onChange={e => set('bio', e.target.value)} placeholder="One line about you" />
        </Field>
      </div>
      <div className="flex flex-wrap gap-4 pt-1">
        <Toggle label="Discoverable" checked={merged.visible} onChange={v => set('visible', v)} />
        <Toggle label="Show my target programs" checked={merged.share_targets} onChange={v => set('share_targets', v)} />
      </div>
      <div className="flex items-center gap-2 pt-1">
        <button onClick={() => saveMut.mutate()} disabled={saveMut.isPending} className="px-4 py-1.5 text-xs font-medium rounded-lg bg-secondary text-secondary-foreground hover:brightness-95 disabled:opacity-60">Save</button>
        <button onClick={onClose} className="px-4 py-1.5 text-xs font-medium rounded-lg text-muted-foreground hover:text-foreground">Cancel</button>
      </div>
    </div>
  )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider">{label}</span>
      <div className="mt-1">{children}</div>
    </label>
  )
}

function Toggle({ label, checked, onChange }: { label: string; checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <button onClick={() => onChange(!checked)} className="flex items-center gap-2 text-xs text-muted-foreground">
      <span className={`w-9 h-5 rounded-full transition-colors flex items-center px-0.5 ${checked ? 'bg-secondary' : 'bg-muted/40'}`}>
        <span className={`w-4 h-4 rounded-full bg-card transition-transform ${checked ? 'translate-x-4' : ''}`} />
      </span>
      {label}
    </button>
  )
}
