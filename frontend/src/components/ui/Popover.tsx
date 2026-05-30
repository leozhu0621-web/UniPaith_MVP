import { useEffect, useId, useRef, useState } from 'react'
import clsx from 'clsx'

// Popover — Spec/02-design-system.md §6.
// Compact, anchored to a trigger. Opens on click/tap (not hover) so it has a
// touch equivalent (Spec/02b §4). Max-width 320px, 16px padding, raised surface.

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
  const id = useId()

  useEffect(() => {
    if (!open) return
    const onDocClick = (e: MouseEvent) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) setOpen(false)
    }
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false)
    }
    document.addEventListener('mousedown', onDocClick)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onDocClick)
      document.removeEventListener('keydown', onKey)
    }
  }, [open])

  const close = () => setOpen(false)

  return (
    <div ref={wrapRef} className={clsx('relative inline-flex', className)}>
      <button
        type="button"
        aria-expanded={open}
        aria-controls={id}
        onClick={() => setOpen(v => !v)}
        className="inline-flex"
      >
        {trigger}
      </button>
      {open && (
        <div
          id={id}
          role="dialog"
          className={clsx(
            'absolute z-50 w-[min(320px,calc(100vw-2rem))] rounded-lg border border-border bg-card text-foreground elev-raised p-4',
            'animate-slide-up-fade',
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
