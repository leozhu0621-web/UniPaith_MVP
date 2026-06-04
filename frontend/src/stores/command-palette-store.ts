import { create } from 'zustand'

// Shared open/close state for the global ⌘K command palette, so a single modal
// can be driven from triggers anywhere in the layout (desktop + mobile).
interface PaletteState {
  open: boolean
  setOpen: (open: boolean) => void
  toggle: () => void
}

export const useCommandPalette = create<PaletteState>((set) => ({
  open: false,
  setOpen: (open) => set({ open }),
  toggle: () => set((s) => ({ open: !s.open })),
}))
