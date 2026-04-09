import { create } from 'zustand'

interface CompareItem {
  program_id: string
  program_name: string
  institution_name: string
  degree_type?: string
}

interface CompareState {
  items: CompareItem[]
  add: (item: CompareItem) => void
  remove: (programId: string) => void
  clear: () => void
  has: (programId: string) => boolean
}

export const useCompareStore = create<CompareState>((set, get) => ({
  items: [],
  add: (item) =>
    set(state => {
      if (state.items.length >= 5) return state
      if (state.items.some(i => i.program_id === item.program_id)) return state
      return { items: [...state.items, item] }
    }),
  remove: (programId) =>
    set(state => ({ items: state.items.filter(i => i.program_id !== programId) })),
  clear: () => set({ items: [] }),
  has: (programId) => get().items.some(i => i.program_id === programId),
}))
