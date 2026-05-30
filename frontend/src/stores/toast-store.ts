// Toast store — Spec/02-design-system.md §11.
// Auto-dismiss: 5s success/info, 8s warning, sticky error (manual only).

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

const DURATION_MS: Record<ToastType, number> = {
  success: 5000,
  info: 5000,
  warning: 8000,
  error: 0, // sticky — manual close only
}

let nextId = 0

export const useToastStore = create<ToastState>((set) => ({
  toasts: [],

  addToast: (message, type = 'info') => {
    const id = String(++nextId)
    set(s => ({ toasts: [...s.toasts, { id, message, type }] }))
    const ms = DURATION_MS[type]
    if (ms > 0) {
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
