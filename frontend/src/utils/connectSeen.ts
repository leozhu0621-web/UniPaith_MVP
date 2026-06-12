// Tracks when the student last opened the Updates tab, for the nav/tab
// "new updates" badge (Spec 2026-06-12 §6.3). Distinct from
// 'unipaith_connect_last_seen' (newest ITEM date, drives the in-feed pill) —
// that key can hold a future deadline date by design, so it can't be the
// `since` for a posts-only server count.
const KEY = 'unipaith_connect_seen_at'

export function getConnectSeenAt(): string | null {
  try {
    return localStorage.getItem(KEY)
  } catch {
    return null
  }
}

export function markConnectSeen(): void {
  try {
    localStorage.setItem(KEY, new Date().toISOString())
  } catch {
    /* ignore */
  }
}
