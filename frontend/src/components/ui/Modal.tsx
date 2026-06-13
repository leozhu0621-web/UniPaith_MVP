import { useEffect, useRef } from 'react'
import clsx from 'clsx'
import { X } from 'lucide-react'
import { usePresence } from './usePresence'

// Modal — Spec/02-design-system.md §6 + Spec/02b §6.
// Ink-tinted backdrop; focus trap; ESC closes; first focusable receives focus;
// focus restored on close (at close START — the focus effect keys on isOpen,
// not on presence, so restoration is not delayed by the exit animation).
// On mobile (< sm) it docks as a bottom sheet. Exit animation via usePresence.

interface ModalProps {
  isOpen: boolean
  onClose: () => void
  title?: string
  children: React.ReactNode
  /** narrow (640) confirmations · default (720) forms · wide (960) editors. */
  size?: 'sm' | 'md' | 'lg'
  footer?: React.ReactNode
}

const SIZE_MAP = {
  sm: 'sm:max-w-[640px]',
  md: 'sm:max-w-[720px]',
  lg: 'sm:max-w-[960px]',
}

const FOCUSABLE =
  'a[href],button:not([disabled]),textarea,input,select,[tabindex]:not([tabindex="-1"])'

export default function Modal({ isOpen, onClose, title, children, size = 'md', footer }: ModalProps) {
  const panelRef = useRef<HTMLDivElement>(null)
  const previouslyFocused = useRef<HTMLElement | null>(null)
  const { mounted, closing } = usePresence(isOpen)

  // Keep the latest onClose in a ref so the focus-management effect can depend
  // ONLY on `isOpen`. Callers pass an inline arrow (`onClose={() => setOpen(false)}`)
  // whose identity changes every render; if that were an effect dependency, every
  // keystroke in a form-owning parent would re-run the effect and yank focus back
  // to the first field — making it impossible to type in any other field.
  const onCloseRef = useRef(onClose)
  onCloseRef.current = onClose

  useEffect(() => {
    if (!isOpen) return
    previouslyFocused.current = document.activeElement as HTMLElement
    document.body.style.overflow = 'hidden'

    // Prefer the first form field (command palettes / forms expect this),
    // else the first focusable, else the panel itself.
    const panel = panelRef.current
    const firstField = panel?.querySelector<HTMLElement>('input,textarea,select')
    const firstFocusable = panel?.querySelector<HTMLElement>(FOCUSABLE)
    ;(firstField ?? firstFocusable ?? panel)?.focus()

    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onCloseRef.current()
        return
      }
      if (e.key === 'Tab' && panel) {
        const items = Array.from(panel.querySelectorAll<HTMLElement>(FOCUSABLE)).filter(
          el => el.offsetParent !== null
        )
        if (items.length === 0) return
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
    // Depends ONLY on isOpen — onClose is read live via onCloseRef so a changing
    // callback identity (every keystroke in a form-owning parent) never re-runs
    // this effect and never resets focus. See test/modal-focus.test.tsx.
  }, [isOpen])

  if (!mounted) return null

  return (
    <div
      className={clsx(
        'fixed inset-0 z-50 flex items-end justify-center sm:items-center sm:p-4',
        closing && 'pointer-events-none'
      )}
      role="dialog"
      aria-modal="true"
      aria-label={title}
    >
      <div
        className={clsx('fixed inset-0 bg-scrim', closing ? 'animate-fade-out' : 'animate-fade-in')}
        onClick={onClose}
      />
      <div
        ref={panelRef}
        tabIndex={-1}
        className={clsx(
          'relative bg-card text-foreground w-full elev-raised outline-none',
          'rounded-t-2xl sm:rounded-xl',
          'max-h-[92vh] sm:max-h-[88vh] flex flex-col',
          closing
            ? 'animate-slide-down-fade sm:animate-scale-out'
            : 'animate-slide-up-fade sm:animate-scale-in',
          SIZE_MAP[size]
        )}
      >
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
        <div className="px-6 py-4 overflow-y-auto pb-safe">{children}</div>
        {footer && (
          <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-border shrink-0 pb-safe">
            {footer}
          </div>
        )}
      </div>
    </div>
  )
}
