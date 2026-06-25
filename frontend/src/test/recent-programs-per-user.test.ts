// recentPrograms used a single global localStorage key, so on a shared browser a
// NEW account saw the PRIOR user's recently-viewed ("Pick up where you left off:
// Artificial Intelligence, Carnegie Mellon" on a fresh account). These pin the
// per-user isolation + legacy-key cleanup.
import { describe, it, expect, beforeEach } from 'vitest'
import { useAuthStore } from '../stores/auth-store'
import { getRecentPrograms, pushRecentProgram } from '../lib/recentPrograms'

function setUser(id: string | null) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  useAuthStore.setState({ user: id ? ({ id } as any) : null })
}

describe('recentPrograms — per-user isolation', () => {
  beforeEach(() => localStorage.clear())

  it("does not leak one account's recents to another on the same browser", () => {
    setUser('user-A')
    pushRecentProgram({
      id: 'p1',
      program_name: 'Artificial Intelligence',
      institution_name: 'Carnegie Mellon',
    })
    expect(getRecentPrograms().map(r => r.id)).toEqual(['p1'])

    // A different account signs in on the same browser → sees nothing.
    setUser('user-B')
    expect(getRecentPrograms()).toEqual([])

    // Back to A → A's recents are still there (isolated, not lost).
    setUser('user-A')
    expect(getRecentPrograms().map(r => r.id)).toEqual(['p1'])
  })

  it('drops the legacy global key so pre-fix data can never be read by any account', () => {
    localStorage.setItem(
      'unipaith_recent_programs',
      JSON.stringify([{ id: 'old', program_name: 'Leftover' }]),
    )
    setUser('user-C')
    expect(getRecentPrograms()).toEqual([])
    expect(localStorage.getItem('unipaith_recent_programs')).toBeNull()
  })
})
