import { useEffect, useRef } from 'react'
import clsx from 'clsx'
import { X } from 'lucide-react'

// Sheet — Spec/02-design-system.md §6 + Spec/02b §6.
// `right` (default): edits a record in context; 480px desktop, full-width mobile.
// `bottom`: the mobile default for filters, artifact rail, compare, day agenda —
// has a peek handle and slides up from the bottom.

interface SheetProps {
  isOpen: boolean
  onClose: () => void
  title?: string
  children: React.ReactNode
  side?: 'right' | 'bottom'
  footer?: React.ReactNode
  /** Width for right sheets. */
  widthClass?: string
}

const FOCUSABLE =
  'a[href],button:not([disabled]),textarea,input,select,[tabindex]:not([tabindex="-1"])'

export default function Sheet({
  isOpen,
  onClose,
  title,
  children,
  side = 'right',
  footer,
  widthClass = 'sm:max-w-[480px]',
}: SheetProps) {
  const panelRef = useRef<HTMLDivElement>(null)
  const previouslyFocused = useRef<HTMLElement | null>(null)

  useEffect(() => {
    if (!isOpen) return
    previouslyFocused.current = document.activeElement as HTMLElement
    document.body.style.overflow = 'hidden'
    const panel = panelRef.current
    const first = panel?.querySelector<HTMLElement>(FOCUSABLE)
    ;(first ?? panel)?.focus()

    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') return onClose()
      if (e.key === 'Tab' && panel) {
        const items = Array.from(panel.querySelectorAll<HTMLElement>(FOCUSABLE)).filter(
          el => el.offsetParent !== null
        )
        if (!items.length) return
        const firstEl = items[0]
        const lastEl = items[items.length - 1]
        if (e.shiftKey && document.activeElement === firstEl) {
          e.preventDefault()
          lastEl.focus()
        } else if (!e.shiftKey && document.activeElement === lastEl) {
          e.preventDefault()
          firstEl.focus()
        }
      }
    }
    document.addEventListener('keydown', handleKey)
    return () => {
      document.removeEventListener('keydown', handleKey)
      document.body.style.overflow = ''
      previouslyFocused.current?.focus?.()
    }
  }, [isOpen, onClose])

  if (!isOpen) return null

  const isBottom = side === 'bottom'

  return (
    <div
      className={clsx('fixed inset-0 z-50 flex', isBottom ? 'items-end' : 'justify-end')}
      role="dialog"
      aria-modal="true"
      aria-label={title}
    >
      <div className="fixed inset-0 bg-scrim" onClick={onClose} />
      <div
        ref={panelRef}
        tabIndex={-1}
        className={clsx(
          'relative bg-card text-foreground elev-raised outline-none flex flex-col',
          isBottom
            ? 'w-full max-h-[85vh] rounded-t-2xl animate-slide-up-fade pb-safe'
            : clsx('h-full w-full border-l border-border animate-slide-in-right', widthClass),
        )}
      >
        {isBottom && (
          <div className="flex justify-center pt-3 pb-1 shrink-0">
            <span className="h-1.5 w-10 rounded-full bg-border" />
          </div>
        )}
        {title && (
          <div className="flex items-center justify-between gap-4 px-6 py-4 border-b border-border shrink-0">
            <h2 className="text-h3 text-foreground">{title}</h2>
            <button
              onClick={onClose}
              aria-label="Close"
              className="ui-btn p-1.5 -mr-1.5 rounded-md text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
            >
              <X size={18} />
            </button>
          </div>
        )}
        <div className="px-6 py-4 overflow-y-auto flex-1">{children}</div>
        {footer && (
          <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-border shrink-0 pb-safe">
            {footer}
          </div>
        )}
      </div>
    </div>
  )
}
