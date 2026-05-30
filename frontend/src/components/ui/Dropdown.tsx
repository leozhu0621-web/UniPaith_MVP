import { useState, useRef, useEffect } from 'react'
import clsx from 'clsx'

interface DropdownItem {
  label: string
  onClick: () => void
  icon?: React.ReactNode
  variant?: 'default' | 'danger'
}

interface DropdownProps {
  trigger: React.ReactNode
  items: DropdownItem[]
  align?: 'left' | 'right'
}

export default function Dropdown({ trigger, items, align = 'right' }: DropdownProps) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', handler)
      document.removeEventListener('keydown', onKey)
    }
  }, [open])

  return (
    <div ref={ref} className="relative">
      <div onClick={() => setOpen(o => !o)}>{trigger}</div>
      {open && (
        <div
          role="menu"
          className={clsx(
            'absolute top-[calc(100%+4px)] w-48 bg-card border border-border rounded-lg elev-raised py-1 z-50 animate-slide-up-fade',
            align === 'right' ? 'right-0' : 'left-0'
          )}
        >
          {items.map((item, i) => (
            <button
              key={i}
              role="menuitem"
              onClick={() => { item.onClick(); setOpen(false) }}
              className={clsx(
                'w-full text-left px-4 py-2 text-sm flex items-center gap-2 transition-colors',
                item.variant === 'danger'
                  ? 'text-error hover:bg-error-soft/50'
                  : 'text-foreground hover:bg-muted'
              )}
            >
              {item.icon}
              {item.label}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
