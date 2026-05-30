// Popover — Spec/02-design-system.md §6.
// Compact, anchored to a trigger. Max 320px, 16px padding, surface bg,
// 1px border, elev-raised. Anchor to its trigger; click-outside or ESC
// closes. Mobile: opens on tap (not hover).

import { useEffect, useRef, useState, useId, useCallback } from 'react'
import clsx from 'clsx'

type Placement = 'bottom-start' | 'bottom-end' | 'top-start' | 'top-end'

interface PopoverProps {
  trigger: (props: { open: boolean; toggle: () => void; close: () => void }) => React.ReactNode
  children: React.ReactNode | ((props: { close: () => void }) => React.ReactNode)
  placement?: Placement
  className?: string
  /** Open the popover on hover-intent (desktop). Mobile always tap-only. */
  hoverIntent?: boolean
}

const PLACEMENT_CLASSES: Record<Placement, string> = {
  'bottom-start': 'top-full left-0 mt-2',
  'bottom-end': 'top-full right-0 mt-2',
  'top-start': 'bottom-full left-0 mb-2',
  'top-end': 'bottom-full right-0 mb-2',
}

export default function Popover({
  trigger,
  children,
  placement = 'bottom-start',
  className,
  hoverIntent = false,
}: PopoverProps) {
  const [open, setOpen] = useState(false)
  const rootRef = useRef<HTMLDivElement | null>(null)
  const panelId = useId()
  const hoverTimer = useRef<number | null>(null)

  const close = useCallback(() => setOpen(false), [])
  const toggle = useCallback(() => setOpen(o => !o), [])

  useEffect(() => {
    if (!open) return
    const handleClick = (e: MouseEvent) => {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false)
    }
    document.addEventListener('mousedown', handleClick)
    document.addEventListener('keydown', handleKey)
    return () => {
      document.removeEventListener('mousedown', handleClick)
      document.removeEventListener('keydown', handleKey)
    }
  }, [open])

  // Tap is always honored; hover-intent kicks in only on devices with a
  // fine pointer (desktop). Mobile users still tap (Spec/02b §4).
  const hoverProps =
    hoverIntent && typeof window !== 'undefined' && window.matchMedia?.('(hover: hover) and (pointer: fine)').matches
      ? {
          onMouseEnter: () => {
            if (hoverTimer.current) window.clearTimeout(hoverTimer.current)
            setOpen(true)
          },
          onMouseLeave: () => {
            hoverTimer.current = window.setTimeout(() => setOpen(false), 150)
          },
        }
      : {}

  return (
    <div ref={rootRef} className="relative inline-block" {...hoverProps}>
      <span aria-haspopup="dialog" aria-expanded={open} aria-controls={open ? panelId : undefined}>
        {trigger({ open, toggle, close })}
      </span>
      {open && (
        <div
          id={panelId}
          role="dialog"
          className={clsx(
            'absolute z-40 max-w-[320px] w-max bg-card text-card-foreground rounded-[14px] border border-border elev-raised p-4 animate-slide-up-fade',
            PLACEMENT_CLASSES[placement],
            className,
          )}
        >
          {typeof children === 'function' ? children({ close }) : children}
        </div>
      )}
    </div>
  )
}
