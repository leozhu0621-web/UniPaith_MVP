import { useEffect, useState } from 'react'
import { useToastStore, type Toast, type ToastType } from '../../stores/toast-store'
import { X, CheckCircle, AlertTriangle, AlertCircle, Info } from 'lucide-react'
import clsx from 'clsx'
import { usePresence } from './usePresence'

// Toast — Spec/02-design-system.md §11. Bottom-right stack, 16px gap, max 4
// visible, 360px wide. Brand status tokens; per-variant auto-dismiss lives in
// the store. Exit animation via usePresence: the container holds just-departed
// toasts for one exit beat (slide/fade out) before dropping them — the store's
// dismiss timing is untouched.

const ICON_MAP: Record<ToastType, React.ReactNode> = {
  success: <CheckCircle size={18} className="text-success" />,
  error: <AlertCircle size={18} className="text-error" />,
  warning: <AlertTriangle size={18} className="text-warning" />,
  info: <Info size={18} className="text-secondary" />,
}

const ACCENT_MAP: Record<ToastType, string> = {
  success: 'border-l-success',
  error: 'border-l-error',
  warning: 'border-l-warning',
  info: 'border-l-secondary',
}

function ToastItem({
  toast,
  present,
  onExited,
  onDismiss,
}: {
  toast: Toast
  present: boolean
  onExited: (id: string) => void
  onDismiss: () => void
}) {
  const { mounted, closing } = usePresence(present)

  // Once the exit window has elapsed, tell the container to drop this entry.
  useEffect(() => {
    if (!present && !mounted) onExited(toast.id)
  }, [present, mounted, onExited, toast.id])

  if (!mounted) return null

  return (
    <div
      role="status"
      aria-live="polite"
      className={clsx(
        'flex items-start gap-3 px-4 py-3 rounded-lg border border-border border-l-4 bg-card elev-raised',
        closing ? 'animate-slide-out-right pointer-events-none' : 'animate-slide-in-right',
        ACCENT_MAP[toast.type]
      )}
    >
      <span className="mt-0.5 shrink-0">{ICON_MAP[toast.type]}</span>
      <p className="flex-1 text-sm text-foreground">{toast.message}</p>
      <button
        onClick={onDismiss}
        aria-label="Dismiss"
        className="p-0.5 -mr-0.5 rounded hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
      >
        <X size={14} />
      </button>
    </div>
  )
}

export default function ToastContainer() {
  const { toasts, removeToast } = useToastStore()
  // Every toast we have rendered, in arrival order. Entries outlive the store
  // list by one exit animation; ToastItem reports back when fully gone.
  const [buffer, setBuffer] = useState<Toast[]>([])

  useEffect(() => {
    setBuffer(prev => {
      const known = new Set(prev.map(t => t.id))
      const additions = toasts.filter(t => !known.has(t.id))
      return additions.length ? [...prev, ...additions] : prev
    })
  }, [toasts])

  if (buffer.length === 0 && toasts.length === 0) return null

  // Newest first; cap at 4 visible (same window as before — older toasts exit
  // when a fifth arrives, and re-entering the window is handled by the store).
  const visibleIds = new Set(toasts.slice(-4).map(t => t.id))
  const inStore = new Set(toasts.map(t => t.id))
  // Render only the capped window plus toasts that have left the store and are
  // playing their exit beat — store entries beyond the cap stay hidden (as the
  // old slice(-4) did) until they re-enter the window.
  const rendered = [...buffer].reverse().filter(t => visibleIds.has(t.id) || !inStore.has(t.id))

  return (
    // Below lg the stack clears the fixed 56px mobile bottom tab bar (+ safe
    // area); at lg+ there is no tab bar, so it sits at the normal offset.
    <div className="fixed right-4 z-[100] flex flex-col gap-4 w-[min(360px,calc(100vw-2rem))] bottom-[calc(56px+env(safe-area-inset-bottom)+0.5rem)] lg:bottom-4 lg:pb-safe">
      {rendered.map(toast => (
        <ToastItem
          key={toast.id}
          toast={toast}
          present={visibleIds.has(toast.id)}
          onExited={id => setBuffer(prev => prev.filter(t => t.id !== id))}
          onDismiss={() => removeToast(toast.id)}
        />
      ))}
    </div>
  )
}
