import { useAnnounceStore } from '../stores/announce-store'

/**
 * Returns a stable `announce(message)` function that posts to the app-wide
 * polite ARIA live region (rendered once in StudentLayout via <LiveAnnouncer/>).
 * Spec 80 §4. Call after optimistic mutations so screen-reader users hear the
 * result, e.g. `announce('Saved to your list')`.
 */
export function useAnnounce(): (message: string) => void {
  return useAnnounceStore((s) => s.announce)
}
