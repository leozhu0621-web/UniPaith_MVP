import { create } from 'zustand'

// Promise-based confirm (Spec 78 §6) — replaces native window.confirm with a
// styled, brand-voice dialog. Mirrors the toast-store pattern: drive it from
// anywhere via `confirmDialog({...})` and `await` the boolean result.

export interface ConfirmOptions {
  title: string
  body?: string
  confirmLabel?: string
  cancelLabel?: string
  /** Destructive actions get a danger-tone confirm button. */
  destructive?: boolean
}

interface PendingConfirm extends ConfirmOptions {
  id: number
  resolve: (ok: boolean) => void
}

interface ConfirmState {
  current: PendingConfirm | null
  request: (opts: ConfirmOptions) => Promise<boolean>
  settle: (ok: boolean) => void
}

let nextId = 0

export const useConfirmStore = create<ConfirmState>((set, get) => ({
  current: null,
  request: (opts) =>
    new Promise<boolean>((resolve) => {
      set({ current: { ...opts, id: ++nextId, resolve } })
    }),
  settle: (ok) => {
    const cur = get().current
    if (cur) {
      cur.resolve(ok)
      set({ current: null })
    }
  },
}))

/** Imperative helper: `if (await confirmDialog({ title: '…' })) { … }` */
export const confirmDialog = (opts: ConfirmOptions) =>
  useConfirmStore.getState().request(opts)
