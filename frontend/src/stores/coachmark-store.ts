import { create } from 'zustand'

// First-run coachmarks (Spec 81 §3.3). One-time tooltips that orient the user
// to the product's non-obvious signature components (DualRing, rationale, compare).
// Dismissal persists in localStorage. A queue ensures only ONE coachmark shows at
// a time (activeId = first-registered, still-unseen mark) so the UI never clutters.

const KEY = 'unipaith_coachmarks_seen'

function loadSeen(): Record<string, boolean> {
  try {
    return JSON.parse(localStorage.getItem(KEY) || '{}')
  } catch {
    return {}
  }
}

function firstUnseen(order: string[], seen: Record<string, boolean>): string | null {
  return order.find((id) => !seen[id]) ?? null
}

interface CoachmarkState {
  seen: Record<string, boolean>
  order: string[]
  activeId: string | null
  register: (id: string) => void
  unregister: (id: string) => void
  dismiss: (id: string) => void
}

export const useCoachmarkStore = create<CoachmarkState>((set) => ({
  seen: loadSeen(),
  order: [],
  activeId: null,
  register: (id) =>
    set((s) => {
      if (s.order.includes(id)) return s
      const order = [...s.order, id]
      return { order, activeId: firstUnseen(order, s.seen) }
    }),
  unregister: (id) =>
    set((s) => {
      const order = s.order.filter((x) => x !== id)
      return { order, activeId: firstUnseen(order, s.seen) }
    }),
  dismiss: (id) =>
    set((s) => {
      const seen = { ...s.seen, [id]: true }
      try {
        localStorage.setItem(KEY, JSON.stringify(seen))
      } catch {
        /* ignore quota/private-mode */
      }
      return { seen, activeId: firstUnseen(s.order, seen) }
    }),
}))
