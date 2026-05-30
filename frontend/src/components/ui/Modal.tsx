// Modal — Spec/02-design-system.md §6.
// Centered, blocks the rest of the UI. Three sizes (narrow / default /
// wide). Backdrop is rgba(10,20,40,0.45). Focus trap on open. ESC
// closes. First focusable element receives focus on open.

import { useEffect, useRef } from 'react'
import clsx from 'clsx'
import { X } from 'lucide-react'

export type ModalSize = 'sm' | 'narrow' | 'md' | 'default' | 'lg' | 'wide'

interface ModalProps {
  isOpen: boolean
  onClose: () => void
  title: string
  children: React.ReactNode
  size?: ModalSize
  /** Pinned-bottom action area (Cancel + primary). */
  footer?: React.ReactNode
  /** Prevent backdrop-click close (e.g., user has unsaved input). */
  disableBackdropClose?: boolean
  /** Optional id for the title for aria-labelledby. */
  titleId?: string
}

// Map both legacy + spec sizes to the same widths.
const SIZE_MAP: Record<ModalSize, string> = {
  sm: 'max-w-[640px]',     // legacy → narrow
  narrow: 'max-w-[640px]',
  md: 'max-w-[720px]',     // legacy → default
  default: 'max-w-[720px]',
  lg: 'max-w-[960px]',     // legacy → wide
  wide: 'max-w-[960px]',
}

export default function Modal({
  isOpen,
  onClose,
  title,
  children,
  size = 'default',
  footer,
  disableBackdropClose,
  titleId = 'modal-title',
}: ModalProps) {
  const containerRef = useRef<HTMLDivElement | null>(null)
  const previouslyFocusedRef = useRef<HTMLElement | null>(null)

  // ESC + focus trap + focus restore.
  useEffect(() => {
    if (!isOpen) return

    previouslyFocusedRef.current = document.activeElement as HTMLElement | null

    const focusFirst = () => {
      const root = containerRef.current
      if (!root) return
      const focusable = root.querySelectorAll<HTMLElement>(
        'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])',
      )
      focusable[0]?.focus()
    }
    const t = setTimeout(focusFirst, 0)

    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.stopPropagation()
        onClose()
        return
      }
      if (e.key !== 'Tab') return
      const root = containerRef.current
      if (!root) return
      const focusable = Array.from(
        root.querySelectorAll<HTMLElement>(
          'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])',
        ),
      ).filter(el => !el.hasAttribute('aria-hidden'))
      if (focusable.length === 0) return
      const first = focusable[0]
      const last = focusable[focusable.length - 1]
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault()
        last.focus()
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault()
        first.focus()
      }
    }

    document.addEventListener('keydown', handler)
    const prevOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'

    return () => {
      clearTimeout(t)
      document.removeEventListener('keydown', handler)
      document.body.style.overflow = prevOverflow
      previouslyFocusedRef.current?.focus?.()
    }
  }, [isOpen, onClose])

  if (!isOpen) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 animate-fade-in"
      role="presentation"
    >
      <div
        className="fixed inset-0"
        style={{ background: 'rgba(10, 20, 40, 0.45)' }}
        onClick={disableBackdropClose ? undefined : onClose}
        aria-hidden="true"
      />
      <div
        ref={containerRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        className={clsx(
          'relative w-full bg-card text-card-foreground rounded-[14px] elev-raised animate-scale-in',
          'flex flex-col max-h-[90vh]',
          SIZE_MAP[size],
        )}
      >
        <div className="flex items-start justify-between px-6 pt-5 pb-3 border-b border-border">
          <h2 id={titleId} className="text-[20px] leading-[1.3] font-bold text-foreground">
            {title}
          </h2>
          <button
            onClick={onClose}
            aria-label="Close dialog"
            className="-mt-1 -mr-2 p-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#FFD60A]"
          >
            <X size={18} />
          </button>
        </div>
        <div className="px-6 py-5 overflow-y-auto">{children}</div>
        {footer && (
          <div className="px-6 py-4 border-t border-border flex items-center justify-end gap-2 bg-background/40 rounded-b-[14px]">
            {footer}
          </div>
        )}
      </div>
    </div>
  )
}
