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
  /** When set, the MiniCounselorPanel picks this up, sends it as a student
   *  message, and clears it. Used by in-page CTAs like "Ask about this program"
   *  to open the chat and send a pre-filled prompt. */
  pendingPrompt: string | null
  addMessage: (msg: ChatMessage) => void
  setMinimized: (v: boolean) => void
  askQuestion: (prompt: string) => void
  clearPendingPrompt: () => void
}

export const useCounselorStore = create<CounselorState>((set) => ({
  messages: [],
  isMinimized: false,
  pendingPrompt: null,
  addMessage: (msg) => set(state => ({ messages: [...state.messages, msg] })),
  setMinimized: (v) => set({ isMinimized: v }),
  askQuestion: (prompt) => set({ pendingPrompt: prompt, isMinimized: false }),
  clearPendingPrompt: () => set({ pendingPrompt: null }),
}))
