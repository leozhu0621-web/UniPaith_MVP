import { useAnnounceStore } from '../../stores/announce-store'

/**
 * App-wide polite ARIA live region (Spec 80 §4). Mounted once in StudentLayout.
 * Visually hidden; screen readers announce `message` whenever it changes.
 * Components push via the `useAnnounce()` hook. `key={nonce}` re-mounts the text
 * node so identical consecutive messages still re-announce.
 */
export default function LiveAnnouncer() {
  const message = useAnnounceStore((s) => s.message)
  const nonce = useAnnounceStore((s) => s.nonce)
  return (
    <div aria-live="polite" aria-atomic="true" className="sr-only">
      <span key={nonce}>{message}</span>
    </div>
  )
}
