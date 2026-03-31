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
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [open])

  return (
    <div ref={ref} className="relative">
      <div onClick={() => setOpen(o => !o)}>{trigger}</div>
      {open && (
        <div
          className={clsx(
            'absolute top-full mt-1 w-48 bg-white border border-gray-200 rounded-lg shadow-lg py-1 z-50',
            align === 'right' ? 'right-0' : 'left-0'
          )}
        >
          {items.map((item, i) => (
            <button
              key={i}
              onClick={() => { item.onClick(); setOpen(false) }}
              className={clsx(
                'w-full text-left px-4 py-2 text-sm flex items-center gap-2',
                item.variant === 'danger'
                  ? 'text-red-600 hover:bg-red-50'
                  : 'text-gray-700 hover:bg-gray-50'
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
