import { useEffect, useRef } from 'react'
import clsx from 'clsx'

// Tabs — Spec/02 §10 + Spec/02b §3.3. On mobile this scrolls horizontally as a
// segmented control with scroll-into-view on selection; selection stays
// deep-linkable (consumer writes ?tab=). `sticky` pins the strip to the top of
// the scroll container on mobile, matching §3.3's pinned behavior.
interface Tab {
  id: string
  label: string
  count?: number
}

interface TabsProps {
  tabs: Tab[]
  activeTab: string
  onChange: (tabId: string) => void
  /** Pin to top of scroll container — recommended for mobile per Spec/02b §3.3. */
  sticky?: boolean
}

export default function Tabs({ tabs, activeTab, onChange, sticky }: TabsProps) {
  const stripRef = useRef<HTMLDivElement>(null)
  const activeRef = useRef<HTMLButtonElement>(null)

  // Scroll the active tab into view on selection — matches §3.3's
  // "snap to first item on tap" behavior. Only triggers when the
  // active tab is partially outside the visible strip.
  useEffect(() => {
    const strip = stripRef.current
    const node = activeRef.current
    if (!strip || !node) return
    const stripRect = strip.getBoundingClientRect()
    const nodeRect = node.getBoundingClientRect()
    const partiallyHidden = nodeRect.left < stripRect.left || nodeRect.right > stripRect.right
    if (partiallyHidden) {
      node.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' })
    }
  }, [activeTab])

  return (
    <div
      ref={stripRef}
      role="tablist"
      className={clsx(
        'flex border-b border-border overflow-x-auto no-scrollbar flex-nowrap',
        sticky && 'sticky top-0 z-20 bg-background',
      )}
    >
      {tabs.map(tab => {
        const active = activeTab === tab.id
        return (
          <button
            key={tab.id}
            ref={active ? activeRef : undefined}
            role="tab"
            aria-selected={active}
            onClick={() => onChange(tab.id)}
            className={clsx(
              'ui-btn shrink-0 px-4 py-2.5 text-sm font-semibold transition-colors border-b-2 -mb-px whitespace-nowrap',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded-t-md',
              active
                ? 'border-secondary text-foreground'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            )}
          >
            {tab.label}
            {tab.count != null && (
              <span
                className={clsx(
                  'ml-1.5 px-1.5 py-0.5 text-xs rounded-pill',
                  active ? 'bg-cobalt/10 text-cobalt' : 'bg-muted text-muted-foreground'
                )}
              >
                {tab.count}
              </span>
            )}
          </button>
        )
      })}
    </div>
  )
}
