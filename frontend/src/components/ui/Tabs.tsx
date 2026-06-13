import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import clsx from 'clsx'

// Tabs — Spec/02 §10 + Spec/02b §3.3. On mobile this scrolls horizontally as a
// segmented control with scroll-into-view on selection; selection stays
// deep-linkable (consumer writes ?tab=). `sticky` pins the strip to the top of
// the scroll container on mobile, matching §3.3's pinned behavior.
// UX overhaul §2: ONE sliding underline (transform/width transition on the
// motion tokens) replaces the per-tab jumping border.
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
  const [indicator, setIndicator] = useState({ left: 0, width: 0 })

  // Measure the active tab and slide the underline to it. offsetLeft/-Width are
  // relative to the strip (the positioned ancestor), so the indicator tracks
  // correctly inside the horizontal scroller. Re-measures on selection, on tab
  // list changes, and on resize/font-scale changes (ResizeObserver, guarded for
  // environments without it, e.g. jsdom).
  useLayoutEffect(() => {
    const measure = () => {
      const node = activeRef.current
      if (!node) return
      const { offsetLeft: left, offsetWidth: width } = node
      setIndicator(prev => (prev.left === left && prev.width === width ? prev : { left, width }))
    }
    measure()
    if (typeof ResizeObserver === 'undefined') return
    const ro = new ResizeObserver(measure)
    if (stripRef.current) ro.observe(stripRef.current)
    return () => ro.disconnect()
  }, [activeTab, tabs])

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
        'relative flex border-b border-border overflow-x-auto no-scrollbar flex-nowrap',
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
              'ui-btn shrink-0 px-4 py-2.5 text-sm font-semibold transition-colors border-b-2 border-transparent -mb-px whitespace-nowrap',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded-t-md',
              active ? 'text-foreground' : 'text-muted-foreground hover:text-foreground'
            )}
          >
            {tab.label}
            {tab.count != null && (
              <span
                className={clsx(
                  'ml-1.5 px-1.5 py-0.5 text-xs rounded-pill',
                  active ? 'bg-secondary/10 text-secondary' : 'bg-muted text-muted-foreground'
                )}
              >
                {tab.count}
              </span>
            )}
          </button>
        )
      })}
      <span
        aria-hidden="true"
        className="absolute bottom-0 left-0 h-0.5 bg-secondary"
        style={{
          width: indicator.width,
          transform: `translateX(${indicator.left}px)`,
          transition:
            'transform var(--dur-base) var(--ease-out), width var(--dur-base) var(--ease-out)',
        }}
      />
    </div>
  )
}

/**
 * Keyed tab-panel wrapper (UX overhaul §2) — remounts on tab change so the
 * 160ms fade/rise entrance replays. Wrap the panel a consumer renders below
 * the strip: `<TabPanel activeTab={tab}>{content}</TabPanel>`.
 */
export function TabPanel({
  activeTab,
  className,
  children,
}: {
  activeTab: string
  className?: string
  children: ReactNode
}) {
  return (
    <div key={activeTab} className={clsx('animate-tab-panel-in', className)}>
      {children}
    </div>
  )
}
