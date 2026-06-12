// Connect API — Spec 20 (Student Stage 3a). The demand-side of the institution
// Outreach module: Updates feed, Events, Manage following, and Peers.
import apiClient from './client'
import { toArrayData } from './normalize'

// ── Types ──────────────────────────────────────────────────────────────────

export type FeedItemKind = 'post' | 'deadline' | 'program_change' | 'saved_search_alert'

export interface ConnectCta {
  type: string
  label: string
  target: string
}

export interface ConnectFeedItem {
  kind: FeedItemKind
  id: string
  date: string
  institution_id: string | null
  institution_name: string | null
  program_id: string | null
  program_name: string | null
  muted?: boolean
  pinned?: boolean
  // post
  title?: string
  body?: string
  media_urls?: (string | { url?: string })[]
  ctas?: ConnectCta[]
  // Spec 27 §5 — raw post id for per-object engagement tracking.
  post_id?: string
  // deadline
  deadline?: string
  days_until?: number
  // program_change
  change_summary?: string
  // Spec 2026-06-12 §6.2 — follow attribution ("because you follow X").
  follow_source?: 'saved' | 'application' | 'explicit' | null
  // saved_search_alert (Spec 2026-06-12 §5.4)
  saved_search_id?: string
  search_name?: string
  match_count?: number
  search_query?: { query?: string; chips?: unknown[]; filters?: Record<string, unknown>; sort?: string }
}

export interface ConnectFeed {
  items: ConnectFeedItem[]
  followed_count: number
  muted_count: number
  /** Spec 56 §4 — keyset cursor for the next page; null/absent on the last page. */
  next_cursor?: string | null
}

export type RsvpState = 'none' | 'rsvp' | 'waitlist' | 'attended'

export interface ConnectEvent {
  id: string
  institution_id: string
  institution_name: string
  program_id: string | null
  event_name: string
  event_type: string | null
  description: string | null
  location: string | null
  start_time: string
  end_time: string | null
  capacity: number | null
  going_count: number
  waitlist_count: number
  spots_left: number | null
  at_capacity: boolean
  rsvp_state: RsvpState
  recommended: boolean
  meeting_link: string | null
  meeting_link_reveals_at: string | null
  status?: string | null
}

export interface FollowDetail {
  institution_id: string
  name: string
  followed_at?: string | null
  country?: string | null
  city?: string | null
  logo_url?: string | null
  type?: string | null
  source: 'saved' | 'application' | 'explicit'
  muted: boolean
  program_count: number
  can_unfollow: boolean
}

export type ConnectionState = 'none' | 'requested' | 'incoming' | 'connected' | 'blocked'

export interface PeerCard {
  peer_id: string
  display_name: string
  shared_programs: { id: string; name: string }[]
  intended_major: string | null
  region: string | null
  bio: string | null
  connection_state: ConnectionState
}

export interface PeerVisibilityProfile {
  id: string
  display_name: string | null
  use_alias: boolean
  intended_major: string | null
  region: string | null
  bio: string | null
  share_targets: boolean
  visible: boolean
}

// ── Updates feed (§4) ────────────────────────────────────────────────────────

export const getConnectFeed = (
  rank: 'recent' | 'relevant' = 'recent',
  cursor?: string | null,
  opts?: { limit?: number; kinds?: string },
) =>
  apiClient
    .get('/connect/feed', {
      params: {
        tab: 'updates',
        rank,
        limit: opts?.limit ?? 50,
        ...(opts?.kinds ? { kinds: opts.kinds } : {}),
        ...(cursor ? { cursor } : {}),
      },
    })
    .then(r => r.data as ConnectFeed)

/** New-posts count since the last Updates visit (nav/tab badge). 0 when never visited. */
export const getUnseenCount = (since: string | null) =>
  since
    ? apiClient
        .get('/connect/feed/unseen-count', { params: { since } })
        .then(r => (r.data as { count: number }).count)
    : Promise.resolve(0)

// ── Events (§5) ──────────────────────────────────────────────────────────────

export const getConnectEvents = (scope: 'upcoming' | 'past' | 'mine' = 'upcoming') =>
  apiClient.get('/connect/events', { params: { scope } }).then(r => r.data as { events: ConnectEvent[]; scope: string })

// ── Manage following (§2) ─────────────────────────────────────────────────────

export const getFollowing = () =>
  apiClient.get('/connect/follows').then(r => toArrayData<FollowDetail>(r.data))

export const followInstitution = (institutionId: string) =>
  apiClient.post(`/connect/follows/${institutionId}`).then(r => r.data)

export const muteFollowing = (institutionId: string, muted: boolean) =>
  apiClient.patch(`/connect/follows/${institutionId}`, { muted }).then(r => r.data)

export const unfollowInstitution = (institutionId: string) =>
  apiClient.delete(`/connect/follows/${institutionId}`)

// ── Peers (§6) — opt-in, privacy-gated ────────────────────────────────────────

export const getPeersStatus = () =>
  apiClient.get('/connect/peers/status').then(r => r.data as { enabled: boolean; opted_in: boolean })

export const optInPeers = (optedIn: boolean) =>
  apiClient.post('/connect/peers/opt-in', { opted_in: optedIn }).then(r => r.data as { opted_in: boolean })

export const getMyPeerProfile = () =>
  apiClient.get('/connect/peers/me').then(r => r.data as PeerVisibilityProfile)

export const updateMyPeerProfile = (data: Partial<PeerVisibilityProfile>) =>
  apiClient.put('/connect/peers/me', data).then(r => r.data as PeerVisibilityProfile)

export const discoverPeers = (programId?: string) =>
  apiClient.get('/connect/peers', { params: programId ? { program_id: programId } : {} }).then(r => toArrayData<PeerCard>(r.data))

export const requestPeer = (peerId: string) =>
  apiClient.post(`/connect/peers/${peerId}/request`).then(r => r.data)

export const respondPeer = (peerId: string, accept: boolean) =>
  apiClient.post(`/connect/peers/${peerId}/respond`, { accept }).then(r => r.data)

export const blockPeer = (peerId: string) =>
  apiClient.post(`/connect/peers/${peerId}/block`).then(r => r.data)

export const reportPeer = (peerId: string, reason?: string, detail?: string) =>
  apiClient.post(`/connect/peers/${peerId}/report`, { reason, detail }).then(r => r.data)
