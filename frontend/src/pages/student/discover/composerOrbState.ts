/**
 * Derive the composer orb's live state from the conversation's existing state.
 *
 * The persistent orb at the composer gives Uni a "living presence" so the
 * orb's states are reachable in normal use (chat-tab spec §1). Pure + isolated
 * so it can be unit-tested without rendering. Priority order (first match wins):
 *   responding > thinking > celebrating > listening > idle
 */
import type { OrbState } from '../../../components/student/UniOrb'

export function deriveComposerOrbState(s: {
  /** A reply is actively streaming over SSE. */
  streaming: boolean
  /** Text accumulated so far for the streaming reply. */
  streamText: string
  /** A non-streaming turn is in flight (awaiting the reply). */
  pending: boolean
  /** The student's current composer draft. */
  draft: string
  /** A transient milestone flash (e.g. matches just unlocked). */
  celebrating: boolean
}): OrbState {
  if (s.streaming && s.streamText) return 'responding'
  if (s.pending || (s.streaming && !s.streamText)) return 'thinking'
  if (s.celebrating) return 'celebrating'
  if (s.draft.trim()) return 'listening'
  return 'idle'
}
