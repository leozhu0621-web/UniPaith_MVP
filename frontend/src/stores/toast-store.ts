import { create } from 'zustand'

export type ToastType = 'success' | 'error' | 'warning' | 'info'

export interface Toast {
  id: string
  message: string
  type: ToastType
}

interface ToastState {
  toasts: Toast[]
  addToast: (message: string, type?: ToastType) => void
  removeToast: (id: string) => void
}

let nextId = 0

// Per-variant auto-dismiss (Spec/02 §11): 5s success/info, 8s warning,
// sticky for error (manual close only).
const DISMISS_MS: Record<ToastType, number | null> = {
  success: 5000,
  info: 5000,
  warning: 8000,
  error: null,
}

export const useToastStore = create<ToastState>((set) => ({
  toasts: [],

  addToast: (message, type = 'info') => {
    const id = String(++nextId)
    set(s => ({ toasts: [...s.toasts, { id, message, type }] }))
    const ms = DISMISS_MS[type]
    if (ms != null) {
      setTimeout(() => {
        set(s => ({ toasts: s.toasts.filter(t => t.id !== id) }))
      }, ms)
    }
  },

  removeToast: (id) => {
    set(s => ({ toasts: s.toasts.filter(t => t.id !== id) }))
  },
}))

export const showToast = (message: string, type?: ToastType) => {
  useToastStore.getState().addToast(message, type)
}
