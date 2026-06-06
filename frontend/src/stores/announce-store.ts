import { create } from 'zustand'

/**
 * Screen-reader announcement store (Spec 80 §4 — ARIA live regions).
 * A single polite live region lives in StudentLayout and reads `message`.
 * Components push messages via the `useAnnounce()` hook on optimistic actions
 * (save to list, RSVP, stage move) so assistive tech is told what changed.
 *
 * `nonce` forces a DOM text change even when the same message repeats, so the
 * live region re-announces (screen readers ignore identical consecutive text).
 */
interface AnnounceState {
  message: string
  nonce: number
  announce: (message: string) => void
}

export const useAnnounceStore = create<AnnounceState>((set) => ({
  message: '',
  nonce: 0,
  announce: (message) => set((s) => ({ message, nonce: s.nonce + 1 })),
}))
