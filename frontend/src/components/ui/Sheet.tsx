// Sheet — Spec/02-design-system.md §6.
// Right-side panel. Use for: editing a record in context without losing
// the list (profile section, message reply, scheduling interview).
// 480px desktop, full-width on mobile with safe-area top inset.

import { useEffect, useRef } from 'react'
import clsx from 'clsx'
import { X } from 'lucide-react'

interface SheetProps {
  isOpen: boolean
  onClose: () => void
  title: string
  children: React.ReactNode
  footer?: React.ReactNode
  /** Desktop width — defaults to 480px. */
  width?: 'sm' | 'md' | 'lg'
  side?: 'right' | 'left'
  titleId?: string
}

const WIDTH_CLASSES = {
  sm: 'md:max-w-[400px]',
  md: 'md:max-w-[480px]',
  lg: 'md:max-w-[640px]',
}

export default function Sheet({
  isOpen,
  onClose,
  title,
  children,
  footer,
  width = 'md',
  side = 'right',
  titleId = 'sheet-title',
}: SheetProps) {
  const containerRef = useRef<HTMLDivElement | null>(null)
  const previouslyFocusedRef = useRef<HTMLElement | null>(null)

  useEffect(() => {
    if (!isOpen) return
    previouslyFocusedRef.current = document.activeElement as HTMLElement | null

    const t = setTimeout(() => {
      const root = containerRef.current
      const focusable = root?.querySelector<HTMLElement>(
        'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])',
      )
      focusable?.focus()
    }, 0)

    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.stopPropagation()
        onClose()
      }
    }
    document.addEventListener('keydown', handler)
    const prev = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      clearTimeout(t)
      document.removeEventListener('keydown', handler)
      document.body.style.overflow = prev
      previouslyFocusedRef.current?.focus?.()
    }
  }, [isOpen, onClose])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50">
      <div
        className="fixed inset-0 animate-fade-in"
        style={{ background: 'rgba(10, 20, 40, 0.45)' }}
        onClick={onClose}
        aria-hidden="true"
      />
      <div
        ref={containerRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        className={clsx(
          'fixed top-0 bottom-0 w-full bg-card text-card-foreground elev-raised flex flex-col pt-safe',
          side === 'right'
            ? 'right-0 border-l border-border animate-sheet-side-in'
            : 'left-0 border-r border-border',
          WIDTH_CLASSES[width],
        )}
      >
        <div className="flex items-start justify-between px-6 pt-5 pb-3 border-b border-border">
          <h2 id={titleId} className="text-[20px] leading-[1.3] font-bold text-foreground">
            {title}
          </h2>
          <button
            onClick={onClose}
            aria-label="Close panel"
            className="-mt-1 -mr-2 p-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#FFD60A]"
          >
            <X size={18} />
          </button>
        </div>
        <div className="flex-1 px-6 py-5 overflow-y-auto">{children}</div>
        {footer && (
          <div className="px-6 py-4 border-t border-border flex items-center justify-end gap-2 pb-safe">
            {footer}
          </div>
        )}
      </div>
    </div>
  )
}
