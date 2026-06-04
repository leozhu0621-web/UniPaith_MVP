import { useState, useRef, useEffect, useId, cloneElement, isValidElement } from 'react'
import type { ReactNode, KeyboardEvent as ReactKeyboardEvent } from 'react'
import clsx from 'clsx'

interface DropdownItem {
  label: string
  onClick: () => void
  icon?: React.ReactNode
  variant?: 'default' | 'danger'
}

interface DropdownProps {
  /** The button that opens the menu. Menu-button ARIA + keyboard wiring is
   *  merged onto it (callers keep passing a plain <button>, e.g. an icon button
   *  with its own aria-label). */
  trigger: ReactNode
  items: DropdownItem[]
  align?: 'left' | 'right'
}

export default function Dropdown({ trigger, items, align = 'right' }: DropdownProps) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  const menuRef = useRef<HTMLDivElement>(null)
  const triggerRef = useRef<HTMLElement>(null)
  const menuId = useId()

  useEffect(() => {
    if (!open) return
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setOpen(false)
        triggerRef.current?.focus()
      }
    }
    document.addEventListener('mousedown', handler)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', handler)
      document.removeEventListener('keydown', onKey)
    }
  }, [open])

  // Focus the first item when the menu is opened by keyboard (ArrowDown).
  const focusFirstItem = () => {
    requestAnimationFrame(() => {
      menuRef.current?.querySelector<HTMLButtonElement>('[role="menuitem"]')?.focus()
    })
  }

  // ArrowUp/ArrowDown/Home/End roving across the menu items; Tab closes.
  const onMenuKeyDown = (e: ReactKeyboardEvent<HTMLDivElement>) => {
    const itemEls = Array.from(
      menuRef.current?.querySelectorAll<HTMLButtonElement>('[role="menuitem"]') ?? [],
    )
    if (itemEls.length === 0) return
    const currentIndex = itemEls.indexOf(document.activeElement as HTMLButtonElement)
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      itemEls[(currentIndex + 1 + itemEls.length) % itemEls.length].focus()
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      itemEls[(currentIndex - 1 + itemEls.length) % itemEls.length].focus()
    } else if (e.key === 'Home') {
      e.preventDefault()
      itemEls[0].focus()
    } else if (e.key === 'End') {
      e.preventDefault()
      itemEls[itemEls.length - 1].focus()
    } else if (e.key === 'Tab') {
      setOpen(false)
    }
  }

  // Merge menu-button semantics onto the caller's trigger element, preserving
  // its existing props (aria-label, className, etc.). Falls back to a wrapper
  // span only if a non-element trigger is ever passed.
  const triggerEl = isValidElement(trigger) ? (
    cloneElement(trigger as React.ReactElement<Record<string, unknown>>, {
      ref: triggerRef,
      'aria-haspopup': 'menu',
      'aria-expanded': open,
      'aria-controls': open ? menuId : undefined,
      onClick: (e: React.MouseEvent) => {
        ;(trigger as React.ReactElement<{ onClick?: (e: React.MouseEvent) => void }>).props.onClick?.(e)
        setOpen(o => !o)
      },
      onKeyDown: (e: ReactKeyboardEvent) => {
        ;(trigger as React.ReactElement<{ onKeyDown?: (e: ReactKeyboardEvent) => void }>).props.onKeyDown?.(e)
        if (e.key === 'ArrowDown') {
          e.preventDefault()
          setOpen(true)
          focusFirstItem()
        }
      },
    })
  ) : (
    <button
      ref={triggerRef as React.RefObject<HTMLButtonElement>}
      type="button"
      aria-haspopup="menu"
      aria-expanded={open}
      aria-controls={open ? menuId : undefined}
      onClick={() => setOpen(o => !o)}
      className="ui-btn inline-flex items-center"
    >
      {trigger}
    </button>
  )

  return (
    <div ref={ref} className="relative">
      {triggerEl}
      {open && (
        <div
          ref={menuRef}
          id={menuId}
          role="menu"
          onKeyDown={onMenuKeyDown}
          className={clsx(
            'absolute top-[calc(100%+4px)] w-48 bg-card border border-border rounded-lg elev-raised py-1 z-50 animate-slide-up-fade',
            align === 'right' ? 'right-0' : 'left-0'
          )}
        >
          {items.map((item, i) => (
            <button
              key={i}
              role="menuitem"
              tabIndex={-1}
              onClick={() => { item.onClick(); setOpen(false) }}
              className={clsx(
                'w-full text-left px-4 py-2 text-sm flex items-center gap-2 transition-colors',
                'focus-visible:outline-none focus-visible:bg-muted',
                item.variant === 'danger'
                  ? 'text-error hover:bg-error-soft/50 focus-visible:bg-error-soft/50'
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
