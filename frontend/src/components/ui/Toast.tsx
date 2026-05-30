import { useToastStore, type ToastType } from '../../stores/toast-store'
import { X, CheckCircle, AlertTriangle, AlertCircle, Info } from 'lucide-react'
import clsx from 'clsx'

// Toast — Spec/02-design-system.md §11. Bottom-right stack, 16px gap, max 4
// visible, 360px wide. Brand status tokens; per-variant auto-dismiss lives in
// the store.

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

export default function ToastContainer() {
  const { toasts, removeToast } = useToastStore()

  if (toasts.length === 0) return null

  // Newest first; cap at 4 visible.
  const visible = [...toasts].slice(-4).reverse()

  return (
    <div className="fixed bottom-4 right-4 z-[100] flex flex-col gap-4 w-[min(360px,calc(100vw-2rem))] pb-safe">
      {visible.map(toast => (
        <div
          key={toast.id}
          role="status"
          aria-live="polite"
          className={clsx(
            'flex items-start gap-3 px-4 py-3 rounded-lg border border-border border-l-4 bg-card elev-raised animate-slide-in-right',
            ACCENT_MAP[toast.type]
          )}
        >
          <span className="mt-0.5 shrink-0">{ICON_MAP[toast.type]}</span>
          <p className="flex-1 text-sm text-foreground">{toast.message}</p>
          <button
            onClick={() => removeToast(toast.id)}
            aria-label="Dismiss"
            className="p-0.5 -mr-0.5 rounded hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
          >
            <X size={14} />
          </button>
        </div>
      ))}
    </div>
  )
}
