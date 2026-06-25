// Lightweight recently-viewed program history (localStorage), surfaced in the
// global command palette + the "Pick up where you left off" hint so re-finding a
// program is one keystroke away.

import { useAuthStore } from '../stores/auth-store'

export interface RecentProgram {
  id: string
  program_name: string
  institution_name?: string | null
  institution_city?: string | null
  degree_type?: string | null
}

const LEGACY_KEY = 'unipaith_recent_programs'
const MAX = 6

// Per-user key. The recents were stored under a single global key, so on a shared
// browser a NEW account saw the PRIOR user's recently-viewed ("Pick up where you
// left off: Artificial Intelligence, Carnegie Mellon" on a fresh account). Scoping
// the key to the signed-in user id isolates each account; a logged-out reader gets
// an "anon" bucket that never bleeds into a real account.
function storageKey(): string {
  const uid = useAuthStore.getState().user?.id
  return uid ? `${LEGACY_KEY}:${uid}` : `${LEGACY_KEY}:anon`
}

export function getRecentPrograms(): RecentProgram[] {
  try {
    // One-time cleanup: drop the legacy global key so a prior user's list can
    // never be read by another account on this browser.
    if (localStorage.getItem(LEGACY_KEY) !== null) localStorage.removeItem(LEGACY_KEY)
    const arr = JSON.parse(localStorage.getItem(storageKey()) || '[]')
    return Array.isArray(arr) ? arr.filter((x) => x?.id && x?.program_name).slice(0, MAX) : []
  } catch {
    return []
  }
}

export function pushRecentProgram(p: Partial<RecentProgram> | null | undefined): void {
  if (!p?.id || !p.program_name) return
  try {
    const next: RecentProgram[] = [
      {
        id: p.id,
        program_name: p.program_name,
        institution_name: p.institution_name ?? null,
        institution_city: p.institution_city ?? null,
        degree_type: p.degree_type ?? null,
      },
      ...getRecentPrograms().filter((x) => x.id !== p.id),
    ].slice(0, MAX)
    localStorage.setItem(storageKey(), JSON.stringify(next))
  } catch {
    // storage unavailable (private mode / quota) — recents are best-effort.
  }
}
