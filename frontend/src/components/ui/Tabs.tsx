// Tabs — Spec/02-design-system.md §7 (Top nav active = 2px primary
// underline) and the general sub-tab pattern. Active label: --text,
// weight 700, 2px bottom border --primary (the one gold accent).
// Counts use a neutral pill.

import clsx from 'clsx'

interface Tab {
  id: string
  label: string
  count?: number
  disabled?: boolean
}

interface TabsProps {
  tabs: Tab[]
  activeTab: string
  onChange: (tabId: string) => void
  className?: string
}

export default function Tabs({ tabs, activeTab, onChange, className }: TabsProps) {
  return (
    <div
      role="tablist"
      className={clsx('flex border-b border-border overflow-x-auto scrollbar-none', className)}
    >
      {tabs.map(tab => {
        const isActive = activeTab === tab.id
        return (
          <button
            key={tab.id}
            role="tab"
            type="button"
            aria-selected={isActive}
            aria-controls={`tabpanel-${tab.id}`}
            id={`tab-${tab.id}`}
            disabled={tab.disabled}
            onClick={() => !tab.disabled && onChange(tab.id)}
            className={clsx(
              'relative px-4 py-2.5 text-[13px] font-bold whitespace-nowrap motion-base transition-colors',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#FFD60A] rounded-t-md',
              isActive
                ? 'text-foreground'
                : 'text-muted-foreground hover:text-foreground',
              tab.disabled && 'opacity-40 cursor-not-allowed',
            )}
          >
            <span className="flex items-center gap-1.5">
              {tab.label}
              {tab.count != null && (
                <span
                  className={clsx(
                    'px-1.5 py-0.5 text-[11px] rounded-full tabular-nums font-bold',
                    isActive
                      ? 'bg-[#FFD60A] text-[#2A2724] dark:bg-[#F2C800] dark:text-[#0A1428]'
                      : 'bg-muted text-muted-foreground',
                  )}
                >
                  {tab.count}
                </span>
              )}
            </span>
            {isActive && (
              <span
                aria-hidden="true"
                className="absolute left-2 right-2 -bottom-[1px] h-0.5 rounded-full bg-[#FFD60A] dark:bg-[#F2C800]"
              />
            )}
          </button>
        )
      })}
    </div>
  )
}
