import { create } from 'zustand'

interface UIState {
  sidebarCollapsed: boolean
  toggleSidebar: () => void
  activeModal: string | null
  openModal: (id: string) => void
  closeModal: () => void
  selectedProgramId: string | null
  selectedProgramName: string | null
  setSelectedProgram: (id: string | null, name?: string | null) => void
}

export const useUIStore = create<UIState>((set) => ({
  sidebarCollapsed: false,
  toggleSidebar: () => set(s => ({ sidebarCollapsed: !s.sidebarCollapsed })),
  activeModal: null,
  openModal: (id) => set({ activeModal: id }),
  closeModal: () => set({ activeModal: null }),
  selectedProgramId: null,
  selectedProgramName: null,
  setSelectedProgram: (id, name = null) => set({ selectedProgramId: id, selectedProgramName: name }),
}))
