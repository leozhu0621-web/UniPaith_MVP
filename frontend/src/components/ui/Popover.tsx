import { useEffect, useId, useRef, useState } from 'react'
import clsx from 'clsx'
import { usePresence } from './usePresence'

// Popover — Spec/02-design-system.md §6.
// Compact, anchored to a trigger. Opens on click/tap (not hover) so it has a
// touch equivalent (Spec/02b §4). Max-width 320px, 16px padding, raised surface.

const FOCUSABLE =
  'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'

interface PopoverProps {
  trigger: React.ReactNode
  children: React.ReactNode | ((close: () => void) => React.ReactNode)
  align?: 'start' | 'center' | 'end'
  side?: 'top' | 'bottom'
  className?: string
  contentClassName?: string
}

export default function Popover({
  trigger,
  children,
  align = 'start',
  side = 'bottom',
  className,
  contentClassName,
}: PopoverProps) {
  const [open, setOpen] = useState(false)
  const wrapRef = useRef<HTMLDivElement>(null)
  const panelRef = useRef<HTMLDivElement>(null)
  const triggerRef = useRef<HTMLButtonElement>(null)
  const id = useId()
  // Keep the panel mounted briefly after close so it can animate out.
  const { mounted, closing } = usePresence(open)

  useEffect(() => {
    if (!open) return
    const onDocClick = (e: MouseEvent) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) setOpen(false)
    }
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') { setOpen(false); return }
      // Trap Tab within the open dialog so keyboard focus can't escape behind it.
      if (e.key === 'Tab') {
        const panel = panelRef.current
        if (!panel) return
        const f = Array.from(panel.querySelectorAll<HTMLElement>(FOCUSABLE)).filter(el => el.offsetParent !== null)
        if (!f.length) { e.preventDefault(); return }
        const first = f[0]
        const last = f[f.length - 1]
        const ae = document.activeElement
        if (e.shiftKey && (ae === first || ae === panel)) { e.preventDefault(); last.focus() }
        else if (!e.shiftKey && ae === last) { e.preventDefault(); first.focus() }
      }
    }
    document.addEventListener('mousedown', onDocClick)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onDocClick)
      document.removeEventListener('keydown', onKey)
    }
  }, [open])

  // Move focus into the panel on open; return it to the trigger on close — but
  // only when focus would otherwise be lost (the user didn't click elsewhere).
  useEffect(() => {
    if (!open) return
    const panel = panelRef.current
    const target = panel?.querySelector<HTMLElement>(FOCUSABLE) ?? panel
    target?.focus()
    return () => {
      const ae = document.activeElement
      if (!ae || ae === document.body || panelRef.current?.contains(ae)) {
        triggerRef.current?.focus()
      }
    }
  }, [open])

  const close = () => setOpen(false)

  return (
    <div ref={wrapRef} className={clsx('relative inline-flex', className)}>
      <button
        ref={triggerRef}
        type="button"
        aria-expanded={open}
        aria-controls={id}
        onClick={() => setOpen(v => !v)}
        className="inline-flex"
      >
        {trigger}
      </button>
      {mounted && (
        <div
          ref={panelRef}
          id={id}
          role="dialog"
          tabIndex={-1}
          className={clsx(
            'absolute z-50 w-[min(320px,calc(100vw-2rem))] rounded-lg border border-border bg-card text-foreground elev-raised p-4',
            closing ? 'animate-slide-down-fade pointer-events-none' : 'animate-slide-up-fade',
            side === 'bottom' ? 'top-[calc(100%+8px)]' : 'bottom-[calc(100%+8px)]',
            align === 'start' && 'left-0',
            align === 'center' && 'left-1/2 -translate-x-1/2',
            align === 'end' && 'right-0',
            contentClassName
          )}
        >
          {typeof children === 'function' ? children(close) : children}
        </div>
      )}
    </div>
  )
}
