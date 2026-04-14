import { create } from 'zustand'

export interface ChatMessage {
  id: string
  sender_type: 'student' | 'assistant'
  message_body: string
  sent_at: string
}

interface CounselorState {
  messages: ChatMessage[]
  isMinimized: boolean // when on other tabs, counselor can be hidden
  addMessage: (msg: ChatMessage) => void
  setMinimized: (v: boolean) => void
}

export const useCounselorStore = create<CounselorState>((set) => ({
  messages: [],
  isMinimized: false,
  addMessage: (msg) => set(state => ({ messages: [...state.messages, msg] })),
  setMinimized: (v) => set({ isMinimized: v }),
}))
