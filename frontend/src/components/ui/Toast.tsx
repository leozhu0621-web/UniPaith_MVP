// Toast — Spec/02-design-system.md §11.
// Bottom-right stack. 16px gap, max 4 visible, 360px wide. Auto-dismiss
// 5s success/info, 8s warning, sticky error. Anatomy: icon + title +
// optional body + optional action link + dismiss X. Uses ARIA live
// region for screen readers.

import { useToastStore, type ToastType } from '../../stores/toast-store'
import { X, CheckCircle, AlertTriangle, AlertCircle, Info } from 'lucide-react'
import clsx from 'clsx'

const ICON_MAP: Record<ToastType, React.ReactNode> = {
  success: <CheckCircle size={18} className="text-[#1F6B2E] dark:text-[#6FCB95]" />,
  error: <AlertCircle size={18} className="text-[#B5321F] dark:text-[#FF8470]" />,
  warning: <AlertTriangle size={18} className="text-[#B8741D] dark:text-[#F0B964]" />,
  info: <Info size={18} className="text-[#2A6BD4] dark:text-[#6FA0E8]" />,
}

const BG_MAP: Record<ToastType, string> = {
  success: 'bg-card border-[#1F6B2E]/30 dark:border-[#6FCB95]/30',
  error: 'bg-card border-[#B5321F]/30 dark:border-[#FF8470]/30',
  warning: 'bg-card border-[#B8741D]/30 dark:border-[#F0B964]/30',
  info: 'bg-card border-[#2A6BD4]/30 dark:border-[#6FA0E8]/30',
}

export default function ToastContainer() {
  const { toasts, removeToast } = useToastStore()

  if (toasts.length === 0) return null

  // Per spec, max 4 visible; surplus stays in queue.
  const visible = toasts.slice(0, 4)

  return (
    <div
      aria-live="polite"
      aria-atomic="false"
      className="fixed bottom-4 right-4 z-[100] flex flex-col gap-3 w-[360px] max-w-[calc(100vw-2rem)] pb-safe"
    >
      {visible.map(toast => (
        <div
          key={toast.id}
          role={toast.type === 'error' ? 'alert' : 'status'}
          className={clsx(
            'flex items-start gap-3 px-4 py-3 rounded-[14px] border elev-raised animate-slide-up-fade',
            BG_MAP[toast.type],
          )}
        >
          <span className="mt-0.5 flex-shrink-0">{ICON_MAP[toast.type]}</span>
          <p className="flex-1 text-base text-foreground leading-snug">{toast.message}</p>
          <button
            onClick={() => removeToast(toast.id)}
            aria-label="Dismiss notification"
            className="flex-shrink-0 -mr-1 -mt-1 p-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#FFD60A]"
          >
            <X size={14} />
          </button>
        </div>
      ))}
    </div>
  )
}
