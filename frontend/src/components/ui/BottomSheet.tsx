// BottomSheet — Spec/02b-design-system-mobile.md §6.
// Mobile-default for: filters, artifact rail, compare tray, event
// detail, day agenda, action menus. Drag-to-dismiss + backdrop tap.
// 360ms slide-in (--dur-slow / --ease-out). Respect prefers-reduced-motion.

import { useEffect, useRef, useState } from 'react'
import clsx from 'clsx'

interface BottomSheetProps {
  isOpen: boolean
  onClose: () => void
  title?: string
  children: React.ReactNode
  /** Peek handle when collapsed (used for the artifact rail). */
  peekHandle?: boolean
  className?: string
}

export default function BottomSheet({
  isOpen,
  onClose,
  title,
  children,
  peekHandle = true,
  className,
}: BottomSheetProps) {
  const sheetRef = useRef<HTMLDivElement | null>(null)
  const startY = useRef<number | null>(null)
  const [dragOffset, setDragOffset] = useState(0)

  useEffect(() => {
    if (!isOpen) return
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handler)
    const prev = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', handler)
      document.body.style.overflow = prev
      setDragOffset(0)
    }
  }, [isOpen, onClose])

  const onPointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
    startY.current = e.clientY
    ;(e.target as HTMLElement).setPointerCapture(e.pointerId)
  }
  const onPointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
    if (startY.current == null) return
    const delta = e.clientY - startY.current
    if (delta > 0) setDragOffset(delta)
  }
  const onPointerUp = (e: React.PointerEvent<HTMLDivElement>) => {
    if (startY.current == null) return
    if (dragOffset > 80) {
      onClose()
    } else {
      setDragOffset(0)
    }
    startY.current = null
    ;(e.target as HTMLElement).releasePointerCapture(e.pointerId)
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center">
      <div
        className="fixed inset-0 animate-fade-in"
        style={{ background: 'rgba(10, 20, 40, 0.45)' }}
        onClick={onClose}
        aria-hidden="true"
      />
      <div
        ref={sheetRef}
        role="dialog"
        aria-modal="true"
        aria-label={title}
        style={{ transform: `translateY(${dragOffset}px)` }}
        className={clsx(
          'relative w-full bg-card text-card-foreground rounded-t-[22px] elev-raised animate-sheet-in pb-safe',
          'max-h-[90vh] flex flex-col',
          className,
        )}
      >
        {peekHandle && (
          <div
            className="flex items-center justify-center pt-2 pb-1 cursor-grab active:cursor-grabbing touch-none"
            onPointerDown={onPointerDown}
            onPointerMove={onPointerMove}
            onPointerUp={onPointerUp}
            onPointerCancel={onPointerUp}
          >
            <span aria-hidden="true" className="h-1 w-10 rounded-full bg-border" />
          </div>
        )}
        {title && (
          <div className="px-5 pb-2 pt-1 border-b border-border">
            <h3 className="text-[18px] leading-[1.3] font-bold">{title}</h3>
          </div>
        )}
        <div className="flex-1 overflow-y-auto px-5 py-4">{children}</div>
      </div>
    </div>
  )
}
