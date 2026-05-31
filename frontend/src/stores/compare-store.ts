import { create } from 'zustand'
import { addToCompare, getCompareSet, removeFromCompare } from '../api/search'
import type { CompareItemDTO } from '../types/search'

// Spec 10 §8 — global compare tray, server-persisted so the set accumulates
// across sessions/devices. Capped at 4. The store keeps an optimistic local
// copy and reconciles with the server on every mutation.
export const MAX_COMPARE = 4

interface CompareItem {
  program_id: string
  program_name: string
  institution_name: string
  degree_type?: string
}

interface CompareState {
  items: CompareItem[]
  hydrated: boolean
  /** True briefly after an add was rejected because the set is full. */
  rejectedFull: boolean
  hydrate: () => Promise<void>
  add: (item: CompareItem) => void
  remove: (programId: string) => void
  clear: () => void
  has: (programId: string) => boolean
  isFull: () => boolean
}

const fromDTO = (i: CompareItemDTO): CompareItem => ({
  program_id: i.program_id,
  program_name: i.program_name,
  institution_name: i.institution_name,
  degree_type: i.degree_type ?? undefined,
})

export const useCompareStore = create<CompareState>((set, get) => ({
  items: [],
  hydrated: false,
  rejectedFull: false,

  hydrate: async () => {
    try {
      const res = await getCompareSet()
      set({ items: res.items.map(fromDTO), hydrated: true })
    } catch {
      // Unauthed or offline — keep whatever is local; mark hydrated so we
      // don't loop. The compare tray only mounts in the authed shell.
      set({ hydrated: true })
    }
  },

  add: (item) => {
    const state = get()
    if (state.has(item.program_id)) return
    if (state.items.length >= MAX_COMPARE) {
      set({ rejectedFull: true })
      setTimeout(() => set({ rejectedFull: false }), 2500)
      return
    }
    // Optimistic — reconcile with the server's authoritative set on return.
    set({ items: [...state.items, item], rejectedFull: false })
    addToCompare(item.program_id)
      .then(res => set({ items: res.items.map(fromDTO) }))
      .catch(() => get().hydrate())
  },

  remove: (programId) => {
    set(state => ({ items: state.items.filter(i => i.program_id !== programId) }))
    removeFromCompare(programId)
      .then(res => set({ items: res.items.map(fromDTO) }))
      .catch(() => get().hydrate())
  },

  clear: () => {
    const ids = get().items.map(i => i.program_id)
    set({ items: [] })
    ids.forEach(id => {
      removeFromCompare(id).catch(() => {})
    })
  },

  has: (programId) => get().items.some(i => i.program_id === programId),
  isFull: () => get().items.length >= MAX_COMPARE,
}))
