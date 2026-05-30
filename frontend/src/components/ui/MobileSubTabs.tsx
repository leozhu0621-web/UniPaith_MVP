// MobileSubTabs — Spec/02b-design-system-mobile.md §3.3.
// Horizontally scrollable segmented control under the page title. Bound
// to ?tab= so deep links survive. When tabs > 4, this stays scrollable;
// the spec also allows a select fallback — kept simple here.

import clsx from 'clsx'

interface SubTab {
  id: string
  label: string
  count?: number
}

interface MobileSubTabsProps {
  tabs: SubTab[]
  activeTab: string
  onChange: (id: string) => void
  className?: string
}

export default function MobileSubTabs({ tabs, activeTab, onChange, className }: MobileSubTabsProps) {
  return (
    <div
      role="tablist"
      className={clsx('flex items-center gap-1.5 overflow-x-auto scrollbar-none -mx-4 px-4 py-2 lg:hidden', className)}
    >
      {tabs.map(t => {
        const isActive = activeTab === t.id
        return (
          <button
            key={t.id}
            role="tab"
            aria-selected={isActive}
            onClick={() => onChange(t.id)}
            className={clsx(
              'inline-flex items-center gap-1.5 flex-shrink-0 h-9 px-3 rounded-full text-[13px] font-bold whitespace-nowrap motion-fast transition-colors',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#FFD60A]',
              isActive
                ? 'bg-[#2A6BD4] text-[#FCFAF2] dark:bg-[#6FA0E8] dark:text-[#0A1428]'
                : 'bg-card border border-border text-foreground hover:bg-muted',
            )}
          >
            {t.label}
            {t.count != null && (
              <span
                className={clsx(
                  'tabular-nums px-1.5 rounded-full text-[11px]',
                  isActive
                    ? 'bg-[#FCFAF2]/20 text-[#FCFAF2] dark:bg-[#0A1428]/30 dark:text-[#0A1428]'
                    : 'bg-muted text-muted-foreground',
                )}
              >
                {t.count}
              </span>
            )}
          </button>
        )
      })}
    </div>
  )
}
